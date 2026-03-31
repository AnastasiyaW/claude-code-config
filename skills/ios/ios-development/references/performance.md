# iOS Performance Reference

## Table of contents
1. Main thread rules
2. SwiftUI render optimization
3. Memory management
4. Launch time
5. List & scroll performance
6. Images
7. Instruments guide

---

## 1. Main thread rules

**Golden rule:** Heavy work off main thread. UI updates on main thread.

```swift
// Correct
func loadData() async {
    let result = await Task.detached(priority: .userInitiated) {
        // heavy computation off main thread
        return processLargeDataset()
    }.value
    
    // UI update must be on main thread
    await MainActor.run {
        self.items = result
    }
}

// Mark functions that update UI
@MainActor
func updateUI(with items: [Item]) {
    self.items = items
    self.isLoading = false
}
```

**Purple warning fix** — "Publishing changes from background thread":
```swift
// Bad
DispatchQueue.global().async {
    let data = fetchData()
    self.items = data  // ← purple warning
}

// Good
Task {
    let data = await fetchDataAsync()
    await MainActor.run { self.items = data }
}

// Or mark the whole ViewModel @MainActor
@MainActor
final class MyViewModel: ObservableObject { }
```

---

## 2. SwiftUI render optimization

SwiftUI re-renders a view whenever any `@State`/`@Published` it reads changes. Keep views small and reads minimal.

### Split large ViewModels
```swift
// Bad — any change re-renders everything
class BigViewModel: ObservableObject {
    @Published var title: String = ""
    @Published var items: [Item] = []
    @Published var isLoading: Bool = false
    @Published var searchText: String = ""
}

// Good — split concerns
class ItemListViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var isLoading: Bool = false
}

class SearchViewModel: ObservableObject {
    @Published var searchText: String = ""
    @Published var results: [Item] = []
}
```

### Equatable structs prevent re-renders
```swift
struct ProductRow: View, Equatable {
    let product: Product  // Product must be Equatable
    
    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.product.id == rhs.product.id && lhs.product.name == rhs.product.name
    }
}

// Wrap with .equatable() modifier
ForEach(products) { product in
    ProductRow(product: product).equatable()
}
```

### Avoid expensive work in body
```swift
// Bad — runs on every render
var body: some View {
    let sorted = items.sorted { $0.name < $1.name }  // expensive!
    List(sorted) { ItemRow(item: $0) }
}

// Good — pre-compute in ViewModel
// ViewModel
var sortedItems: [Item] { items.sorted { $0.name < $1.name } }

// View
var body: some View {
    List(vm.sortedItems) { ItemRow(item: $0) }
}
```

### Drawinggroup for complex shapes
```swift
// For many overlapping/complex views
ComplexGraphView()
    .drawingGroup()  // rasterizes to Metal texture
```

---

## 3. Memory management

### ARC & weak references
```swift
// Capture list in closures — prevent retain cycles
class DataService {
    var onUpdate: (() -> Void)?
    
    func start() {
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            self?.refresh()  // weak self — no retain cycle
        }
    }
}

// Combine
$searchText
    .sink { [weak self] text in
        self?.search(text)
    }
    .store(in: &cancellables)
```

### NSCache for image/data caching
```swift
final class ImageCache {
    static let shared = ImageCache()
    private let cache = NSCache<NSString, UIImage>()
    
    init() {
        cache.countLimit = 100
        cache.totalCostLimit = 50 * 1024 * 1024  // 50 MB
    }
    
    func set(_ image: UIImage, for key: String) {
        cache.setObject(image, forKey: key as NSString, cost: image.jpegData(compressionQuality: 1)?.count ?? 0)
    }
    
    func get(_ key: String) -> UIImage? {
        cache.object(forKey: key as NSString)
    }
}
```

### Memory warning
```swift
// UIKit
override func didReceiveMemoryWarning() {
    super.didReceiveMemoryWarning()
    ImageCache.shared.clearAll()
}

// SwiftUI
.onReceive(NotificationCenter.default.publisher(for: UIApplication.didReceiveMemoryWarningNotification)) { _ in
    ImageCache.shared.clearAll()
}
```

---

## 4. Launch time

**Target:** < 400ms (cold launch). Measured from app launch to first frame.

### Rules
- No heavy work in `AppDelegate.didFinishLaunchingWithOptions` or `@main App.init`
- Defer non-critical initialization
- Use lazy properties for expensive objects

```swift
@main
struct MyApp: App {
    // Bad — runs synchronously at launch
    // let database = Database()  // ← slow
    
    // Good — lazy
    var body: some Scene {
        WindowGroup {
            ContentView()
                .task {
                    // defer non-critical work
                    await AppSetup.initialize()
                }
        }
    }
}

// Services — lazy initialization
class ServiceLocator {
    static let shared = ServiceLocator()
    
    lazy var analytics: AnalyticsService = AnalyticsService()
    lazy var notifications: NotificationService = NotificationService()
    // Only created when first accessed
}
```

### Static linking over dynamic frameworks
Each dynamic framework adds ~5-10ms to launch. Minimize third-party SDK count.

---

## 5. List & scroll performance

```swift
// Use List or LazyVStack — never VStack for large data
// VStack materializes ALL views at once

// List (most performant for large datasets)
List(largeDataset) { item in
    ItemRow(item: item)
}

// LazyVStack for custom layouts
ScrollView {
    LazyVStack(spacing: 12) {
        ForEach(largeDataset) { item in
            ItemCard(item: item)
        }
    }
}

// Stable IDs — critical for diffing
ForEach(items, id: \.id) { ... }  // use actual ID, not \.self for value types

// Avoid complex views in rows — extract to separate structs
// Bad
List(items) { item in
    HStack {
        AsyncImage(url: item.imageURL) { ... }
        VStack {
            Text(item.name).font(.headline)
            Text(item.description).font(.subheadline)
            // more complex content...
        }
    }
}

// Good — extract row to its own view type
List(items) { item in
    ItemRow(item: item)  // SwiftUI optimizes at struct boundary
}
```

---

## 6. Images

### AsyncImage (simple cases)
```swift
AsyncImage(url: URL(string: product.imageURL)) { phase in
    switch phase {
    case .empty: ProgressView()
    case .success(let image): image.resizable().scaledToFill()
    case .failure: Image(systemName: "photo").foregroundColor(.gray)
    @unknown default: EmptyView()
    }
}
.frame(width: 80, height: 80)
.clipShape(RoundedRectangle(cornerRadius: 8))
```

### Custom image loader with caching
```swift
@Observable
final class ImageLoader {
    var image: UIImage?
    var state: LoadState = .idle
    private static let cache = NSCache<NSString, UIImage>()
    
    enum LoadState { case idle, loading, loaded, failed }
    
    func load(url: URL) async {
        let key = url.absoluteString as NSString
        if let cached = Self.cache.object(forKey: key) {
            image = cached
            state = .loaded
            return
        }
        
        state = .loading
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let img = UIImage(data: data) {
                Self.cache.setObject(img, forKey: key)
                image = img
                state = .loaded
            }
        } catch {
            state = .failed
        }
    }
}
```

### Downsampling large images
```swift
func downsample(imageAt url: URL, to pointSize: CGSize, scale: CGFloat = UIScreen.main.scale) -> UIImage? {
    let options: [CFString: Any] = [kCGImageSourceCreateThumbnailFromImageAlways: true,
                                    kCGImageSourceShouldCacheImmediately: true,
                                    kCGImageSourceCreateThumbnailWithTransform: true,
                                    kCGImageSourceThumbnailMaxPixelSize: max(pointSize.width, pointSize.height) * scale]
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else { return nil }
    return UIImage(cgImage: cgImage)
}
```

---

## 7. Instruments guide

### Which instrument to use

| Problem | Instrument |
|---|---|
| App is slow / laggy | Time Profiler |
| Memory leak or growing memory | Leaks + Allocations |
| Launch is slow | App Launch |
| Scroll is janky | Core Animation / SwiftUI |
| Battery drain | Energy Log |
| Network requests too slow | Network |

### Time Profiler workflow
1. Product → Profile → Time Profiler
2. Reproduce the slow action
3. Stop, zoom into the slow region
4. Look for heavy call stacks in main thread
5. Heaviest Stack Trace panel → find your code

### Memory Leaks workflow
1. Instruments → Leaks
2. Run app, navigate around, go back
3. Red "L" markers = leak
4. Click leak → see retain cycle in reference graph
5. Fix: add `[weak self]` to the cycle

### SwiftUI profiling
- Use Instruments → SwiftUI profiling template
- Look for "Body Invocations" — how often each View's body runs
- High count on simple views = too many re-renders
- Use `.equatable()` modifier or split ViewModel to fix
