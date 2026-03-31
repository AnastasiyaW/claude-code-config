# SwiftUI Pipeline Reference

## Table of contents
1. View lifecycle & identity
2. State & data flow
3. Layout system
4. Modifiers & styling
5. Animations
6. Lists & collections
7. Forms & input
8. Environment & preferences
9. Custom components

---

## 1. View lifecycle & identity

SwiftUI views are value types — recreated on every render. `body` should be pure and free of side effects.

```swift
struct MyView: View {
    var body: some View {
        // This is called frequently — keep it fast
    }
}
```

**Lifecycle hooks:**
```swift
.onAppear { /* view appeared */ }
.onDisappear { /* view gone */ }
.task { /* async work, auto-cancelled on disappear */ }
.task(id: value) { /* re-runs when value changes */ }
```

**Stable identity for animations/diffing:**
```swift
// Good — stable ID
List(users, id: \.id) { UserRow(user: $0) }

// Bad — index-based, unstable
List(users.indices, id: \.self) { i in UserRow(user: users[i]) }
```

---

## 2. State & data flow

### Ownership rules
```
Who owns the data?         → @State (structs) or @StateObject (classes)
Who receives the data?     → let property or @Binding
Who observes shared data?  → @ObservedObject or @EnvironmentObject
```

### @State — local value
```swift
@State private var isExpanded = false
@State private var name = ""
@State private var items: [Item] = []
```

### @Binding — two-way connection
```swift
// Parent owns
@State private var isOn = false

// Child receives — note: no default value
struct Toggle: View {
    @Binding var isOn: Bool
    var body: some View {
        Button { isOn.toggle() } label: { Text(isOn ? "ON" : "OFF") }
    }
}

// Usage
Toggle(isOn: $isOn)
```

### @Observable (iOS 17+)
```swift
@Observable
class CartStore {
    var items: [CartItem] = []
    var totalPrice: Decimal { items.reduce(0) { $0 + $1.price } }
    
    func add(_ item: CartItem) { items.append(item) }
}

// Views auto-track only accessed properties
struct CartView: View {
    var cart: CartStore  // no wrapper needed
}
```

### ObservableObject (iOS 16-)
```swift
class CartViewModel: ObservableObject {
    @Published var items: [CartItem] = []
    @Published var isLoading = false
    private var cancellables = Set<AnyCancellable>()
}
```

### @EnvironmentObject — DI via environment
```swift
// Root
ContentView().environmentObject(authStore)

// Any descendant
struct ProfileView: View {
    @EnvironmentObject var auth: AuthStore
}
```

### Combine (when needed for iOS 16-)
```swift
// Debounce search
$searchText
    .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
    .removeDuplicates()
    .sink { [weak self] query in
        Task { await self?.search(query) }
    }
    .store(in: &cancellables)
```

---

## 3. Layout system

### Stack basics
```swift
VStack(alignment: .leading, spacing: 8) { }
HStack(alignment: .center, spacing: 16) { }
ZStack(alignment: .bottomTrailing) { }
```

### Grid
```swift
// Fixed columns
LazyVGrid(columns: [GridItem(.fixed(100)), GridItem(.fixed(100))]) { }

// Adaptive (fills width)
LazyVGrid(columns: [GridItem(.adaptive(minimum: 120))]) { }

// Flexible (equal sizes)
LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3)) { }
```

### Geometry & sizing
```swift
GeometryReader { geo in
    Rectangle()
        .frame(width: geo.size.width * 0.8)
}

// Preferred — avoid GeometryReader when possible
.frame(maxWidth: .infinity)
.frame(height: 200)
.aspectRatio(16/9, contentMode: .fit)
```

### Safe area
```swift
.ignoresSafeArea()              // all edges
.ignoresSafeArea(.keyboard)     // keyboard only
.safeAreaInset(edge: .bottom) { BottomBar() }
```

---

## 4. Modifiers & styling

**Order matters** — each modifier wraps the previous:
```swift
Text("Hello")
    .padding()        // adds padding first
    .background(.red) // background around padded text
    .cornerRadius(8)  // clips the background
```

**ViewModifier for reusable styles:**
```swift
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(16)
            .background(.white)
            .cornerRadius(12)
            .shadow(radius: 4)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}
```

**ButtonStyle:**
```swift
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(configuration.isPressed ? .blue.opacity(0.8) : .blue)
            .foregroundColor(.white)
            .cornerRadius(8)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

Button("Save") { }.buttonStyle(PrimaryButtonStyle())
```

---

## 5. Animations

### Implicit — change value, view animates
```swift
@State private var isOpen = false

Rectangle()
    .frame(height: isOpen ? 200 : 50)
    .animation(.spring(response: 0.4, dampingFraction: 0.7), value: isOpen)
```

### Explicit — animate specific block
```swift
withAnimation(.spring()) {
    isOpen.toggle()
}
```

### Transitions — for appear/disappear
```swift
if isVisible {
    Card()
        .transition(.asymmetric(
            insertion: .move(edge: .bottom).combined(with: .opacity),
            removal: .opacity
        ))
}
```

### matchedGeometryEffect — hero animations
```swift
@Namespace private var heroNS

// Source view
Image(item.image)
    .matchedGeometryEffect(id: item.id, in: heroNS)

// Destination view
Image(item.image)
    .matchedGeometryEffect(id: item.id, in: heroNS)
```

---

## 6. Lists & collections

```swift
// Basic list
List(items) { item in
    ItemRow(item: item)
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) { delete(item) } label: {
                Label("Delete", systemImage: "trash")
            }
        }
}
.listStyle(.insetGrouped)
.refreshable { await reload() }

// Section support
List {
    ForEach(sections) { section in
        Section(section.title) {
            ForEach(section.items) { ItemRow(item: $0) }
        }
    }
}
```

**Performance — LazyVStack for custom layouts:**
```swift
ScrollView {
    LazyVStack(spacing: 12, pinnedViews: .sectionHeaders) {
        ForEach(items) { ItemCard(item: $0) }
    }
    .padding(.horizontal)
}
```

---

## 7. Forms & input

```swift
Form {
    Section("Personal") {
        TextField("Name", text: $name)
        DatePicker("Birthday", selection: $birthday, displayedComponents: .date)
        Toggle("Notifications", isOn: $notificationsOn)
    }
    
    Section("Account") {
        SecureField("Password", text: $password)
        Picker("Role", selection: $role) {
            ForEach(Role.allCases) { Text($0.label).tag($0) }
        }
    }
}
```

**Focus management:**
```swift
@FocusState private var focused: Field?

enum Field { case email, password }

TextField("Email", text: $email).focused($focused, equals: .email)
SecureField("Password", text: $password).focused($focused, equals: .password)
    .onSubmit { focused = nil }

// Programmatically focus
.onAppear { focused = .email }
```

---

## 8. Environment & preferences

```swift
// Read system environment
@Environment(\.colorScheme) var colorScheme
@Environment(\.dismiss) var dismiss
@Environment(\.openURL) var openURL

// Custom environment key
private struct ThemeKey: EnvironmentKey {
    static let defaultValue = AppTheme.default
}

extension EnvironmentValues {
    var appTheme: AppTheme {
        get { self[ThemeKey.self] }
        set { self[ThemeKey.self] = newValue }
    }
}

// Usage
view.environment(\.appTheme, .dark)
@Environment(\.appTheme) var theme
```

---

## 9. Previews

```swift
#Preview {
    UserCard(user: .preview)
        .padding()
}

#Preview("Loading state") {
    UserCard(user: nil)
}

// With environment
#Preview {
    ContentView()
        .environmentObject(AuthStore.preview)
}
```
