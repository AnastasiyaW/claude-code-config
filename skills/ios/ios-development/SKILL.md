---
name: ios-development
description: >
  Comprehensive iOS app development skill. Use this skill for ANY iOS-related task:
  writing Swift/SwiftUI/UIKit code, architecting apps, debugging crashes, setting up
  navigation, networking, data persistence, animations, performance optimization, App Store
  submission, Xcode configuration. Trigger when user mentions: iOS, Swift, SwiftUI, UIKit,
  Xcode, iPhone/iPad app, Combine, CoreData, SwiftData, MVVM, TCA, URLSession, async/await,
  @State/@Binding/@ObservableObject, NavigationStack, XCTest, TestFlight, provisioning profiles,
  or any Apple platform development. Always use this skill before writing iOS code or architecture.
---

# iOS Development Skill

## Quick orientation

Before anything else, identify:
1. **UI framework** → SwiftUI / UIKit / mixed?
2. **Architecture** → MVVM / TCA / VIPER / Clean / MVC?
3. **iOS target** → iOS 16 / 17 / 18? (affects API availability)
4. **Task type** → new feature / debug / refactor / architecture / performance / release?
5. **Graphics intensity** → стандартный UI / средняя 3D / тяжёлая графика / Metal?

Если задача связана с **Metal, GPU, рендерингом, шейдерами, TBDR, MetalFX, GPU profiling, frame pacing, PSO, heaps, ICB, MTLIO** → читать `references/metal-graphics.md` первым.

Then read the relevant reference file before writing code.

---

## Reference files — read when needed

| Topic | File | When to read |
|---|---|---|
| SwiftUI pipeline | `references/swiftui.md` | SwiftUI views, state, bindings, modifiers, animations |
| UIKit pipeline | `references/uikit.md` | UIViewController, Auto Layout, delegates, storyboards |
| Architecture | `references/architecture.md` | MVVM, TCA, VIPER, Clean, Coordinator |
| Networking | `references/networking.md` | URLSession, async/await, REST/GraphQL, auth |
| Data persistence | `references/data.md` | CoreData, SwiftData, UserDefaults, Keychain, FileManager |
| Navigation | `references/navigation.md` | NavigationStack, Coordinator, deep links, sheets |
| Performance | `references/performance.md` | Instruments, memory, launch time, rendering |
| **Metal & Heavy Graphics** | `references/metal-graphics.md` | Metal, GPU рендер, TBDR, PSO/heaps/argument buffers, ICB, MTLIO, MetalFX, терморегуляция, профилирование GPU |

---

## iOS version matrix (API availability)

| Feature | Min iOS |
|---|---|
| SwiftUI | iOS 13 |
| `async/await` | iOS 15 |
| NavigationStack | iOS 16 |
| SwiftData | iOS 17 |
| `@Observable` macro | iOS 17 |
| RippleEffect, ScrollView phases | iOS 18 |

Always check target before using newer APIs. Use `#available` guards for backward compatibility:
```swift
if #available(iOS 17, *) {
    // SwiftData or @Observable
} else {
    // fallback
}
```

---

## Core Swift patterns (always apply)

### Concurrency — async/await first
```swift
// Prefer this
func loadUser() async throws -> User {
    let data = try await URLSession.shared.data(from: url).0
    return try JSONDecoder().decode(User.self, from: data)
}

// Call site
Task {
    do {
        user = try await loadUser()
    } catch {
        errorMessage = error.localizedDescription
    }
}
```

### Error handling — typed errors
```swift
enum AppError: LocalizedError {
    case networkUnavailable
    case decodingFailed(String)
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .networkUnavailable: return "No internet connection"
        case .decodingFailed(let detail): return "Data error: \(detail)"
        case .unauthorized: return "Please sign in again"
        }
    }
}
```

### Value types first
Prefer `struct` over `class` unless you need reference semantics, inheritance, or `@Observable`.

---

## Architecture decision tree

```
Is the screen purely data-display with simple interaction?
  YES → MVC / simple SwiftUI View with @State is fine
  NO ↓

Is business logic testable without UI?
  Required → use ViewModel (MVVM) or Store (TCA)

Is navigation/routing complex (deep links, coordinator)?
  YES → read references/navigation.md → Coordinator pattern

Is the team large or is this a long-lived product?
  YES → Clean Architecture or TCA → read references/architecture.md

Default for most apps: MVVM + Coordinator
```

---

## State management quick reference

### SwiftUI state hierarchy
```
Local transient state       → @State
Passed from parent          → @Binding
Shared across views         → @StateObject / @ObservedObject (iOS 16-)
                            → @State with @Observable class (iOS 17+)
App-wide environment        → @EnvironmentObject / @Environment
```

### iOS 17+ preferred (@Observable)
```swift
@Observable
class UserStore {
    var users: [User] = []
    var isLoading = false
}

// In View — no property wrapper needed
struct UserListView: View {
    var store: UserStore  // just pass it
    var body: some View {
        List(store.users) { Text($0.name) }
    }
}
```

### iOS 16 and below (ObservableObject)
```swift
class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false
}

struct UserListView: View {
    @StateObject private var vm = UserViewModel()
}
```

---

## Xcode & project setup checklist

**New project:**
- [ ] Set deployment target explicitly
- [ ] Enable Swift strict concurrency warnings (`SWIFT_STRICT_CONCURRENCY = complete`)
- [ ] Add `.gitignore` for Xcode (xcuserdata, DerivedData)
- [ ] Configure signing (automatic vs manual)
- [ ] Set bundle ID and version/build numbers

**Capabilities to enable when needed:**
- Push Notifications → add `Push Notifications` capability
- Background fetch → `Background Modes`
- iCloud/CloudKit → `iCloud`
- Sign in with Apple → `Sign In with Apple`

---

## Testing baseline

```swift
// Unit test — ViewModel
@MainActor
final class UserViewModelTests: XCTestCase {
    func testLoadUsers() async throws {
        let vm = UserViewModel(service: MockUserService())
        await vm.loadUsers()
        XCTAssertFalse(vm.users.isEmpty)
    }
}

// UI test — basic
func testLoginFlow() {
    let app = XCUIApplication()
    app.launch()
    app.textFields["Email"].tap()
    app.textFields["Email"].typeText("test@example.com")
    app.buttons["Continue"].tap()
    XCTAssertTrue(app.navigationBars["Home"].exists)
}
```

---

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Purple warning: "Publishing changes from background thread" | Wrap in `await MainActor.run { }` or mark func `@MainActor` |
| View re-renders too often | Audit `@State`/`@Published` — split large ViewModels |
| Memory leak in closures | Use `[weak self]` captures in escaping closures |
| `@StateObject` recreated | Move object creation up the tree; don't init in body |
| Keyboard covering text field | Use `.ignoresSafeArea(.keyboard, edges: .bottom)` or ScrollView |
| Slow list | Use `LazyVStack` or `List` with `id:` stability |
| Simulator ≠ device behavior | Always test on real device before submission |
| **Metal: CPU↔GPU stall** | Triple buffer + DispatchSemaphore; никогда не ждать GPU синхронно в draw() |
| **Metal: PSO компилируется в рантайме** | Создавать все PSO до первого кадра, кешировать |
| **Metal: лишние load/store** | storeAction = .dontCare для transient (depth buffer) |
| **Metal: OOM jetsam** | Мониторить currentAllocatedSize vs recommendedMaxWorkingSetSize; освобождать при warning |
| **Metal: статтер при загрузке** | MTLIO + MTLSharedEvent вместо блокирующей загрузки; ODR для тяжёлых ассетов |
| **Metal: перегрев** | Подписаться на thermalStateDidChangeNotification, адаптировать render scale + FPS |

---

## Hardware budget ориентиры (GPU capability levels)

Планировать по capability-уровням, не под конкретную модель. Всегда включать adaptive quality.

| Уровень | SoC | Реалистичный target | Ключевые ограничения |
|---|---|---|---|
| **Широкий охват** | A13–A15 (iPhone SE, 13, 14) | 30–60 FPS, агрессивный render scale | Строгий бюджет RT; MetalFX обязателен для сложных сцен |
| **Средний** | A16 (iPhone 15), M1 | 60 FPS при хорошем пайплайне | MetalFX + динамический render scale |
| **Флагман** | A17 Pro (iPhone 15 Pro), M3+ | 60–120 FPS, тяжёлые эффекты | Ray tracing (аппаратный); всё равно нужен thermal management |

**Важно:** даже флагманы упираются в термальную стабильность при длительной нагрузке, а не в пиковую мощность GPU.

---

## App Store submission checklist

- [ ] Increment build number for every TestFlight upload
- [ ] Privacy manifest (`PrivacyInfo.xcprivacy`) required for sensitive APIs
- [ ] App icons all sizes provided (use Asset Catalog)
- [ ] Screenshots for all required device sizes
- [ ] Export compliance (encryption questions)
- [ ] App Review Information filled in
- [ ] No `UIRequiresFullScreen = NO` without iPad support reasoning
