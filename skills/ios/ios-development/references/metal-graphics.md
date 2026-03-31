# Metal & Heavy Graphics Reference

## Table of contents
1. Стек технологий — выбор фреймворка
2. Архитектура рендер-лупа
3. Triple buffering + in-flight кадры
4. TBDR-оптимизация (Apple GPU)
5. Снижение CPU-оверхеда: PSO, heaps, argument buffers
6. Indirect command buffers и GPU-driven rendering
7. Синхронизация: fence, event, semaphore
8. Metal 3 Fast Resource Loading (MTLIO)
9. Стриминг: ODR, Background Assets
10. Текстуры: форматы, компрессия, sparse
11. MetalFX — динамическое разрешение и апскейл
12. Профилирование: инструменты и метрики
13. Терморегуляция и adaptive quality
14. Memory management и jetsam
15. Производственный чеклист

---

## 1. Стек технологий — выбор фреймворка

| Стек | Сильные стороны | Ограничения | Когда использовать |
|---|---|---|---|
| **Metal** | Минимальный оверхед, максимальный контроль GPU, лучший профилировщик | Высокая стоимость инженерии, привязка к платформе | Игры, рендер-движки, CV/ML постпроцессинг |
| **MetalKit** | Упрощает MTKView/тайминг/загрузку ассетов | Скрывает часть деталей; для предела — уходить в чистый Metal | Обвязка окна/рендер-лупа, прототипы |
| **MPS** | Готовые оптимизированные kernels (фильтры/линалг/NN) | Не всегда гибко; ограничения форматов | Постпроцессинг, Computer Vision, ML-препроцесс |
| **MPSGraph** | Высокопроизводительные вычислительные графы | Не заменяет рендер; нужна интеграция | ML-инференс рядом с графикой |
| **SceneKit** | Быстрый старт 3D, сценграф/физика/анимации | Меньше контроля; статус deprecation под вопросом | 3D в приложениях, средние нагрузки |
| **Unity** | Кросс-платформа, скорость разработки | Оверхед движка; «последние проценты» труднее | Кросс-платформенные игры, time-to-market важен |
| **Unreal** | Высокая визуальная планка | На iOS часть режимов beta; тяжёлый аппетит | «Консольный» визуал, большая команда |
| **MoltenVK** | Портирование Vulkan-кода | Переводной слой: не 1-к-1 по производительности | Кросс-платформенные движки с Vulkan-target |

**Правило:** для максимальной производительности начинать с Metal, добавлять высокоуровневые слои только там, где это не разрушает производительность.

---

## 2. Архитектура рендер-лупа

Правильная архитектура разделяет три зоны:

```
┌─────────────────────┐
│  Поток симуляции    │  физика, анимации, gameplay-логика, подготовка данных
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Поток кодирования  │  формирование command buffers, энкодеров, биндинг ресурсов
└────────┬────────────┘
         │
┌────────▼────────────┐
│  MTKView / CADisplayLink │  подача команд, present drawable, ровный frame pacing
└─────────────────────┘
```

**Ключевые параметры MTKView:**
```swift
mtkView.preferredFramesPerSecond = 60  // или 120 для ProMotion
mtkView.framebufferOnly = true          // держать true если не читаете drawable
```

**ProMotion:** явно проектировать режимы — 120Hz (игровой) vs 60Hz (энергосберегающий). Адаптироваться к термальным условиям без микростаттеров.

---

## 3. Triple buffering + in-flight кадры

**Главная ошибка:** непреднамеренная синхронизация CPU↔GPU (CPU ждёт GPU).

**Паттерн:** ограничить число одновременных кадров семафором (2–3), динамические uniform/instance данные — в кольцевом буфере.

```swift
import Metal
import MetalKit

final class TripleBufferedRenderer: NSObject, MTKViewDelegate {
    private let device: MTLDevice
    private let commandQueue: MTLCommandQueue
    private let pipelineState: MTLRenderPipelineState

    private let maxFramesInFlight = 3
    private let inFlightSemaphore: DispatchSemaphore
    private var frameIndex = 0

    private struct Uniforms {
        var timeSeconds: Float
        var pad0: Float = 0
        var pad1: Float = 0
        var pad2: Float = 0
    }

    private let uniformStride: Int
    private let uniformBuffer: MTLBuffer
    private let startTime = CACurrentMediaTime()

    init?(mtkView: MTKView) {
        guard let dev = MTLCreateSystemDefaultDevice(),
              let queue = dev.makeCommandQueue() else { return nil }
        device = dev
        commandQueue = queue
        inFlightSemaphore = DispatchSemaphore(value: maxFramesInFlight)

        mtkView.device = dev
        mtkView.colorPixelFormat = .bgra8Unorm
        mtkView.framebufferOnly = true
        mtkView.preferredFramesPerSecond = 60

        let library = dev.makeDefaultLibrary()
        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction = library?.makeFunction(name: "vb_vertex")
        desc.fragmentFunction = library?.makeFunction(name: "vb_fragment")
        desc.colorAttachments[0].pixelFormat = .bgra8Unorm
        pipelineState = try! dev.makeRenderPipelineState(descriptor: desc)

        uniformStride = (MemoryLayout<Uniforms>.stride + 255) & ~255
        uniformBuffer = dev.makeBuffer(length: uniformStride * maxFramesInFlight,
                                       options: .storageModeShared)!
        uniformBuffer.label = "Uniform Ring Buffer"
        super.init()
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        inFlightSemaphore.wait()
        frameIndex = (frameIndex + 1) % maxFramesInFlight
        let uboOffset = frameIndex * uniformStride

        // Обновляем только слот текущего кадра
        var u = Uniforms(timeSeconds: Float(CACurrentMediaTime() - startTime))
        uniformBuffer.contents().advanced(by: uboOffset)
            .copyMemory(from: &u, byteCount: MemoryLayout<Uniforms>.stride)

        guard let pass = view.currentRenderPassDescriptor,
              let drawable = view.currentDrawable,
              let cb = commandQueue.makeCommandBuffer() else {
            inFlightSemaphore.signal(); return
        }
        cb.label = "Frame \(frameIndex)"

        // Семафор освобождается когда GPU закончил — не раньше
        cb.addCompletedHandler { [weak self] _ in self?.inFlightSemaphore.signal() }

        let enc = cb.makeRenderCommandEncoder(descriptor: pass)!
        enc.setRenderPipelineState(pipelineState)
        enc.setVertexBuffer(uniformBuffer, offset: uboOffset, index: 0)
        enc.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        enc.endEncoding()

        cb.present(drawable)
        cb.commit()
    }
}
```

---

## 4. TBDR-оптимизация (Apple GPU)

Apple GPU используют **Tile-Based Deferred Rendering**. Это меняет «правила игры»:

**Что критично в TBDR:**
- **Load/Store actions** — избегать лишних `.load` и `.store`. Если attachment не нужен после прохода — `storeAction = .dontCare`.
- **Держать данные в тайле** — избегать offscreen-проходов, которые читают из предыдущего результата через fetch (вместо этого — memoryless attachments).
- **Overdraw дороже** — каждый фрагмент в tile обрабатывается полностью; сортировка front-to-back имеет значение.

```swift
// Правильные load/store actions
let passDesc = MTLRenderPassDescriptor()
passDesc.colorAttachments[0].loadAction  = .clear   // начало кадра
passDesc.colorAttachments[0].storeAction = .store   // нужен результат

// Transient depth buffer — не нужен снаружи прохода
passDesc.depthAttachment.loadAction  = .clear
passDesc.depthAttachment.storeAction = .dontCare    // экономит bandwidth

// Memoryless (только TBDR) — данные живут только в тайле
let depthDesc = MTLTextureDescriptor.texture2DDescriptor(
    pixelFormat: .depth32Float, width: w, height: h, mipmapped: false)
depthDesc.storageMode = .memoryless  // нет расходов на передачу в/из памяти
depthDesc.usage = [.renderTarget]
```

---

## 5. Снижение CPU-оверхеда: PSO, Heaps, Argument Buffers

### Pipeline State Objects — создать один раз, кешировать

```swift
// Создать при старте, хранить в словаре/кеше
final class PipelineCache {
    private var cache: [String: MTLRenderPipelineState] = [:]
    private let device: MTLDevice

    func pipeline(for key: String, descriptor: MTLRenderPipelineDescriptor) -> MTLRenderPipelineState? {
        if let cached = cache[key] { return cached }
        let state = try? device.makeRenderPipelineState(descriptor: descriptor)
        cache[key] = state
        return state
    }
}
```

### Resource Heaps — один аллокатор, меньше оверхеда

```swift
func migrateTexturesToHeap(device: MTLDevice,
                           commandQueue: MTLCommandQueue,
                           sourceTextures: [MTLTexture]) throws -> (MTLHeap, [MTLTexture]) {
    let heapDesc = MTLHeapDescriptor()
    heapDesc.storageMode = .private
    heapDesc.type = .automatic

    func alignUp(_ x: Int, _ a: Int) -> Int { (x + a - 1) & ~(a - 1) }

    var totalSize = 0
    let texDescs = sourceTextures.map { t -> MTLTextureDescriptor in
        let d = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: t.pixelFormat, width: t.width, height: t.height,
            mipmapped: t.mipmapLevelCount > 1)
        d.usage = t.usage
        d.storageMode = heapDesc.storageMode
        let s = device.heapTextureSizeAndAlign(descriptor: d)
        totalSize = alignUp(totalSize, s.align) + s.size
        return d
    }
    heapDesc.size = totalSize

    let heap = device.makeHeap(descriptor: heapDesc)!
    heap.label = "Texture Heap"

    let heapTextures = texDescs.enumerated().map { (i, d) -> MTLTexture in
        let t = heap.makeTexture(descriptor: d)!
        t.label = "HeapTex[\(i)]"
        return t
    }

    // Blit источников в heap (private)
    let cb = commandQueue.makeCommandBuffer()!
    let blit = cb.makeBlitCommandEncoder()!
    for (i, src) in sourceTextures.enumerated() {
        blit.copy(from: src, sourceSlice: 0, sourceLevel: 0,
                  sourceOrigin: .init(), sourceSize: .init(width: src.width, height: src.height, depth: 1),
                  to: heapTextures[i], destinationSlice: 0, destinationLevel: 0, destinationOrigin: .init())
    }
    blit.endEncoding()
    cb.commit()
    cb.waitUntilCompleted()

    return (heap, heapTextures)
}
```

**Aliasing:** для transient ресурсов — выделить heap под максимальный, переиспользовать между проходами (не пересекающиеся во времени). Снижает пики памяти.

### Argument Buffers — один биндинг вместо N setTexture/setBuffer

```swift
func makeMaterialArgumentBuffer(device: MTLDevice,
                                 fragmentFunction: MTLFunction,
                                 texture: MTLTexture,
                                 sampler: MTLSamplerState) -> MTLBuffer {
    let encoder = fragmentFunction.makeArgumentEncoder(bufferIndex: 1)
    let argBuffer = device.makeBuffer(length: encoder.encodedLength, options: .storageModeShared)!
    argBuffer.label = "Material ArgBuffer"

    encoder.setArgumentBuffer(argBuffer, offset: 0)
    encoder.setTexture(texture, index: 0)
    encoder.setSamplerState(sampler, index: 1)
    return argBuffer
}
```

```metal
struct MaterialArgs {
    texture2d<float> baseColor [[id(0)]];
    sampler          samp      [[id(1)]];
};

fragment float4 ab_fragment(VSOut in [[stage_in]],
                            constant MaterialArgs& m [[buffer(1)]]) {
    return m.baseColor.sample(m.samp, in.uv);
}
```

---

## 6. Indirect Command Buffers и GPU-driven rendering

Используется когда узкое место — CPU-подготовка draw-calls (много объектов/материалов).

```swift
// ICB: создать один раз, хранить между кадрами
let icbDesc = MTLIndirectCommandBufferDescriptor()
icbDesc.commandTypes = .drawIndexed
icbDesc.inheritBuffers = false
icbDesc.maxVertexBufferBindCount = 4
icbDesc.maxFragmentBufferBindCount = 2

let icb = device.makeIndirectCommandBuffer(descriptor: icbDesc,
                                           maxCommandCount: maxObjects,
                                           options: [])!
icb.label = "Scene ICB"

// Encode на GPU через compute-шейдер (GPU-driven)
// CPU только запускает reset + encode compute pass
let resetBlitEnc = cb.makeBlitCommandEncoder()!
resetBlitEnc.resetCommandsInBuffer(icb, range: 0..<maxObjects)
resetBlitEnc.endEncoding()

// Compute pass генерирует команды
let comp = cb.makeComputeCommandEncoder()!
comp.setComputePipelineState(icbFillPipeline)
comp.setBuffer(instanceBuffer, offset: 0, index: 0)
comp.useResource(icb, usage: .write)
comp.dispatchThreads(MTLSize(width: maxObjects, height: 1, depth: 1),
                     threadsPerThreadgroup: MTLSize(width: 64, height: 1, depth: 1))
comp.endEncoding()

// Render pass исполняет ICB
let renderEnc = cb.makeRenderCommandEncoder(descriptor: passDesc)!
renderEnc.executeCommandsInBuffer(icb, range: 0..<maxObjects)
renderEnc.endEncoding()
```

**Трейдоффы ICB:**
- ✅ Меньше CPU-времени на draw-calls, выше throughput
- ⚠️ Дополнительная latency (compute → render синхронизация)
- ⚠️ Дебаг заметно сложнее

---

## 7. Синхронизация: fence, event, semaphore

```swift
// MTLFence — ordering между passes в одном command buffer
let fence = device.makeFence()!

let pass1 = cb.makeRenderCommandEncoder(descriptor: desc1)!
// ... работа ...
pass1.updateFence(fence, after: .fragment)
pass1.endEncoding()

let pass2 = cb.makeRenderCommandEncoder(descriptor: desc2)!
pass2.waitForFence(fence, before: .vertex)  // гарантирует порядок
// ... работа ...
pass2.endEncoding()

// MTLSharedEvent — синхронизация между command buffers и CPU
let event = device.makeSharedEvent()!

// В command buffer 1
cb1.encodeSignalEvent(event, value: 1)
cb1.commit()

// В command buffer 2 (может быть другая очередь)
cb2.encodeWaitForEvent(event, value: 1)
cb2.commit()

// CPU wait на событие
let listener = MTLSharedEventListener()
event.notify(listener, atValue: 1) {
    print("GPU done")
}
```

---

## 8. Metal 3 Fast Resource Loading (MTLIO)

Для загрузки ассетов асинхронно и параллельно с GPU-работой (iOS 16+, Metal 3).

```swift
final class FastTextureLoader {
    private let device: MTLDevice
    private let ioQueue: MTLIOCommandQueue

    init?(device: MTLDevice) {
        self.device = device
        let qDesc = MTLIOCommandQueueDescriptor()
        qDesc.type = .concurrent
        qDesc.priority = .normal
        guard let q = try? device.makeIOCommandQueue(descriptor: qDesc) else { return nil }
        ioQueue = q
    }

    func loadTexture(from url: URL, width: Int, height: Int) throws -> MTLTexture {
        let texDesc = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: .rgba8Unorm, width: width, height: height, mipmapped: false)
        texDesc.storageMode = .private
        texDesc.usage = .shaderRead

        let texture = device.makeTexture(descriptor: texDesc)!
        texture.label = url.lastPathComponent

        let fileHandle = try device.makeIOHandle(url: url)
        let ioCB = ioQueue.makeCommandBuffer()!
        ioCB.label = "Load \(url.lastPathComponent)"

        ioCB.load(texture,
                  slice: 0, level: 0,
                  size: MTLSize(width: width, height: height, depth: 1),
                  sourceBytesPerRow: width * 4,
                  sourceBytesPerImage: width * height * 4,
                  destinationOrigin: MTLOrigin(),
                  sourceHandle: fileHandle,
                  sourceHandleOffset: 0)

        // В продакшене: не waitUntilCompleted — синхронизировать через MTLSharedEvent
        // чтобы GPU-рендер начал после завершения IO без блокировки CPU
        ioCB.commit()
        ioCB.waitUntilCompleted()  // только для прогрева / offscreen загрузки

        return texture
    }
}
```

**В продакшене вместо `waitUntilCompleted`:**
```swift
// IO командный буфер сигналит event
ioCB.signalEvent(sharedEvent, value: frameToken)
ioCB.commit()

// Render command buffer ждёт event
renderCB.encodeWaitForEvent(sharedEvent, value: frameToken)
renderCB.commit()
```

---

## 9. Стриминг ассетов: ODR и Background Assets

| Механизм | Что делает | Когда |
|---|---|---|
| **On-Demand Resources** | Ассеты на App Store, система управляет кешем | Уровни, DLC, тяжёлые ресурсы (до 2 ГБ) |
| **Background Assets** | Фоновое скачивание до первого запуска / между сессиями | Большие паки, first-run experience |
| **URLSession background** | Фоновые HTTP-загрузки | Кастомный CDN, обновления контента |

```swift
// On-Demand Resources
let request = NSBundleResourceRequest(tags: ["level_2_textures"])
request.loadingPriority = NSBundleResourceRequestLoadingPriorityUrgent

request.beginAccessingResources { error in
    guard error == nil else { return }
    // ресурсы доступны в Bundle
    let url = Bundle.main.url(forResource: "level2_terrain", withExtension: "astc")!
    // загружаем через MTLIO или MTKTextureLoader
}
// Не забыть endAccessingResources() когда уровень выгружен
request.endAccessingResources()
```

---

## 10. Текстуры: форматы, компрессия, sparse

**Compressed formats для iOS:**
- **ASTC** — гибкий битрейт (от 0.89 до 8 bpp), лучшее соотношение качество/размер, поддерживается на A8+
- **ETC2** — совместимость с OpenGL ES
- **PVRTC** — устаревший, избегать в новых проектах

```swift
// Проверка поддержки семейства
let device = MTLCreateSystemDefaultDevice()!
let supportsASTC = device.supportsFamily(.apple2)  // ASTC с A8+

// MTKTextureLoader с компрессией
let loader = MTKTextureLoader(device: device)
let options: [MTKTextureLoader.Option: Any] = [
    .generateMipmaps: true,
    .SRGB: true,
    .textureStorageMode: MTLStorageMode.private.rawValue
]
let texture = try loader.newTexture(URL: url, options: options)
```

**Sparse textures** — для больших миров (виртуальные текстуры):
```swift
// Поддержка зависит от GPU family
if device.supportsFamily(.apple6) {
    let texDesc = MTLTextureDescriptor()
    texDesc.textureType = .type2D
    texDesc.pixelFormat = .rgba8Unorm
    texDesc.width = 16384
    texDesc.height = 16384
    texDesc.sparsePageSize = .size64x64  // маппинг по страницам
    texDesc.usage = .shaderRead
    let sparseTexture = device.makeTexture(descriptor: texDesc)!
    // Маппировать только нужные тайлы через mapIndirectBuffers
}
```

---

## 11. MetalFX — динамическое разрешение и апскейл

Вместо рендера в нативе → рендер в пониженном разрешении + апскейл через MetalFX.

```swift
import MetalFX

// Spatial upscaling (без истории кадров, меньше latency)
func makeSpatialScaler(device: MTLDevice,
                       inputWidth: Int, inputHeight: Int,
                       outputWidth: Int, outputHeight: Int,
                       colorFormat: MTLPixelFormat) -> MTXSpatialScaler? {
    let desc = MTXSpatialScalerDescriptor()
    desc.inputWidth = inputWidth
    desc.inputHeight = inputHeight
    desc.outputWidth = outputWidth
    desc.outputHeight = outputHeight
    desc.colorTextureFormat = colorFormat
    desc.outputTextureFormat = colorFormat
    return desc.makeScaler(device: device)
}

// Temporal upscaling (лучше качество, нужна motion vectors + depth)
func makeTemporalScaler(device: MTLDevice, desc: MTXTemporalScalerDescriptor) -> MTXTemporalScaler? {
    return desc.makeScaler(device: device)
}

// В рендер-лупе
func applyUpscale(scaler: MTXSpatialScaler,
                  commandBuffer: MTLCommandBuffer,
                  inputTexture: MTLTexture,
                  outputTexture: MTLTexture) {
    scaler.colorTexture = inputTexture
    scaler.outputTexture = outputTexture
    scaler.encode(commandBuffer: commandBuffer)
}
```

**Динамическое масштабирование разрешения:**
```swift
func adaptRenderResolution(thermalState: ProcessInfo.ThermalState,
                           nativeSize: CGSize) -> CGSize {
    let scale: Double = switch thermalState {
    case .nominal:  1.0
    case .fair:     0.85
    case .serious:  0.70
    case .critical: 0.55
    @unknown default: 0.70
    }
    return CGSize(width: nativeSize.width * scale, height: nativeSize.height * scale)
}
```

---

## 12. Профилирование: инструменты и метрики

### Какой инструмент использовать

| Проблема | Инструмент |
|---|---|
| Stalls CPU↔GPU, общий таймлайн | Metal System Trace (Instruments) |
| Разбор одного кадра по passes | GPU Frame Capture в Xcode |
| Bandwidth/шейдер-лимитеры live | Metal Performance HUD + GPU Counters |
| Память: footprint, heaps, leaks | Allocations + Metal Memory Viewer |
| Launch time | App Launch Instrument |

### Metal Performance HUD (быстрый мониторинг)
```swift
// Включить через environment variable или в коде
// Environment: MTL_HUD_ENABLED=1
// Или:
UserDefaults.standard.set(true, forKey: "MetalForceHudEnabled")
```

### GPU Counter Sample Buffers (программный сбор)
```swift
// Получить доступные наборы счётчиков
let sets = device.counterSets ?? []
guard let commonSet = sets.first(where: { $0.name == MTLCommonCounterSet.timestamp.rawValue }) else { return }

let sampleBufDesc = MTLCounterSampleBufferDescriptor()
sampleBufDesc.counterSet = commonSet
sampleBufDesc.storageMode = .shared
sampleBufDesc.sampleCount = 2

let sampleBuffer = try! device.makeCounterSampleBuffer(descriptor: sampleBufDesc)

// В encoder
renderEncoder.sampleCounters(sampleBuffer: sampleBuffer, sampleIndex: 0, barrier: false)
// ... рендер ...
renderEncoder.sampleCounters(sampleBuffer: sampleBuffer, sampleIndex: 1, barrier: false)

// Читать результаты
let data = try! sampleBuffer.resolveCounterRange(0..<2)
```

### Минимальный набор метрик для production

```swift
// Мониторинг GPU-памяти
func logMemoryBudget(device: MTLDevice) {
    let allocated = device.currentAllocatedSize      // текущий footprint
    let recommended = device.recommendedMaxWorkingSetSize  // рекомендуемый лимит
    let ratio = Double(allocated) / Double(recommended)
    if ratio > 0.8 { /* предупреждение */ }
}
```

**Метрики которые должны быть зафиксированы:**
- CPU frame time: среднее + p95/p99
- GPU frame time: среднее + p95/p99
- GPU busy vs idle (по Metal System Trace)
- currentAllocatedSize / recommendedMaxWorkingSetSize
- Bandwidth-лимитеры (по GPU counters)
- Наличие spikes/stutters (tail latency)

---

## 13. Терморегуляция и adaptive quality

```swift
import Foundation

final class ThermalManager {
    static let shared = ThermalManager()

    // Подписка на изменения теплового состояния
    private var observer: NSObjectProtocol?

    func startMonitoring(onStateChange: @escaping (ProcessInfo.ThermalState) -> Void) {
        observer = NotificationCenter.default.addObserver(
            forName: ProcessInfo.thermalStateDidChangeNotification,
            object: nil,
            queue: .main
        ) { _ in
            onStateChange(ProcessInfo.processInfo.thermalState)
        }
    }

    // Настройки качества по тепловому состоянию
    struct QualitySettings {
        var targetFPS: Int
        var shadowQuality: Float      // 0..1
        var renderScale: Float        // 0..1
        var particleCount: Int
        var aoEnabled: Bool
    }

    func qualityForThermalState(_ state: ProcessInfo.ThermalState) -> QualitySettings {
        switch state {
        case .nominal:
            return QualitySettings(targetFPS: 60, shadowQuality: 1.0,
                                   renderScale: 1.0, particleCount: 1000, aoEnabled: true)
        case .fair:
            return QualitySettings(targetFPS: 60, shadowQuality: 0.7,
                                   renderScale: 0.85, particleCount: 500, aoEnabled: true)
        case .serious:
            return QualitySettings(targetFPS: 30, shadowQuality: 0.4,
                                   renderScale: 0.7, particleCount: 200, aoEnabled: false)
        case .critical:
            return QualitySettings(targetFPS: 30, shadowQuality: 0.0,
                                   renderScale: 0.55, particleCount: 0, aoEnabled: false)
        @unknown default:
            return qualityForThermalState(.serious)
        }
    }
}
```

**Правило:** реагировать на `thermalState` до того, как наступит жёсткое троттлинг — проактивно, а не реактивно.

---

## 14. Memory management и jetsam

```swift
// Реакция на memory warning
NotificationCenter.default.addObserver(
    forName: UIApplication.didReceiveMemoryWarningNotification,
    object: nil, queue: .main
) { _ in
    // 1. Освободить текстурные кеши
    TextureCache.shared.evictAll()
    // 2. Снизить качество
    RenderSettings.shared.degradeQuality()
    // 3. Выгрузить неактивные уровни/ассеты
    AssetManager.shared.unloadInactiveAssets()
}

// Постоянный мониторинг (каждые N кадров)
func checkMemoryBudget() {
    let device = MTLCreateSystemDefaultDevice()!
    let used = device.currentAllocatedSize
    let limit = device.recommendedMaxWorkingSetSize

    if used > Int(Double(limit) * 0.9) {
        // Критическая зона — принудительное освобождение
        TextureCache.shared.evictLRU(bytesToFree: used - Int(Double(limit) * 0.7))
    }
}
```

**Jetsam анализ:** при крашах из-за OOM → в Xcode → Devices → Download Container → искать `JetsamEvent` отчёты. Показывают footprint всех процессов в момент терминации.

---

## 15. Производственный чеклист

### Рендер-пайплайн
- [ ] in-flight кадры ограничены семафором (2–3)
- [ ] Uniform/instance данные в кольцевом буфере
- [ ] PSO создаются один раз, кешируются (не в `draw()`)
- [ ] Шейдеры компилируются до первого кадра (нет PSO-компиляции в рантайме)
- [ ] framebufferOnly = true (если не нужно читать drawable)
- [ ] Load/Store actions оптимизированы (dontCare для transient)
- [ ] Depth buffer = .memoryless где возможно

### Память
- [ ] Бюджет задан: мониторинг currentAllocatedSize / recommendedMaxWorkingSetSize
- [ ] Heaps для наборов текстур уровня
- [ ] Aliasing для transient ресурсов между проходами
- [ ] Компрессия: ASTC для цветных текстур
- [ ] Обработчик memory warning освобождает кеши немедленно

### Adaptive quality
- [ ] 3+ режима качества (Low/Medium/High)
- [ ] Подписка на thermalStateDidChangeNotification
- [ ] MetalFX upscaler для среднего/низкого режима
- [ ] Динамическое масштабирование render scale

### Профилирование
- [ ] Эталонные сцены-бенчмарки зафиксированы
- [ ] Metal System Trace прогнан на устройстве
- [ ] GPU Frame Capture — нет очевидных пустых слотов
- [ ] p95/p99 frame time задокументированы
- [ ] GPU memory budget проверен через currentAllocatedSize

### Ресурсы
- [ ] ODR / Background Assets настроены для тяжёлых ассетов
- [ ] MTLIO используется для стриминга уровней (Metal 3)
- [ ] Синхронизация IO↔GPU через MTLSharedEvent (не waitUntilCompleted)

---

## Официальные источники

- Metal Best Practices: https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/
- TBDR: https://developer.apple.com/documentation/metal/tailor-your-apps-for-apple-gpus-and-tile-based-deferred-rendering
- Reducing memory footprint: https://developer.apple.com/documentation/metal/reducing-the-memory-footprint-of-metal-apps
- Metal Feature Set Tables: https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf
- Fast Resource Loading (MTLIO): https://developer.apple.com/videos/play/wwdc2022/10104/
- Argument Buffers: https://developer.apple.com/documentation/metal/improving-cpu-performance-by-using-argument-buffers
- MetalFX: https://developer.apple.com/documentation/metalfx
- Metal Tools: https://developer.apple.com/metal/tools/
- GPU Frame Capture: https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode
- GPU Counters: https://developer.apple.com/documentation/metal/gpu-counters-and-counter-sample-buffers
- On-Demand Resources: https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/On_Demand_Resources_Guide/
- Background Assets: https://developer.apple.com/documentation/BackgroundAssets
- Jetsam Reports: https://developer.apple.com/documentation/xcode/identifying-high-memory-use-with-jetsam-event-reports
