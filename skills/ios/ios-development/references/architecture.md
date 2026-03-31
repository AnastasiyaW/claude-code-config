# iOS Architecture Reference

## Table of contents
1. MVVM (default choice)
2. MVVM + Coordinator
3. TCA (The Composable Architecture)
4. Clean Architecture
5. VIPER
6. When to use what

---

## 1. MVVM — default choice

### Structure
```
View        → renders UI, forwards user actions to ViewModel
ViewModel   → business logic, state, service calls
Model       → data structs (Codable, value types)
Service     → networking, storage, external APIs
```

### ViewModel template
```swift
@MainActor
final class ProductListViewModel: ObservableObject {
    @Published private(set) var products: [Product] = []
    @Published private(set) var isLoading = false
    @Published private(set) var error: AppError?
    
    private let service: ProductServiceProtocol
    
    init(service: ProductServiceProtocol = ProductService()) {
        self.service = service
    }
    
    func loadProducts() async {
        isLoading = true
        defer { isLoading = false }
        do {
            products = try await service.fetchProducts()
        } catch {
            self.error = error as? AppError ?? .unknown(error)
        }
    }
    
    func delete(_ product: Product) async {
        // optimistic update
        products.removeAll { $0.id == product.id }
        do {
            try await service.delete(product.id)
        } catch {
            await loadProducts() // rollback
        }
    }
}
```

### View template
```swift
struct ProductListView: View {
    @StateObject private var vm = ProductListViewModel()
    
    var body: some View {
        Group {
            if vm.isLoading {
                ProgressView()
            } else {
                List(vm.products) { product in
                    ProductRow(product: product)
                        .swipeActions { deleteButton(product) }
                }
            }
        }
        .task { await vm.loadProducts() }
        .alert("Error", isPresented: .constant(vm.error != nil)) {
            Button("OK") { }
        } message: {
            Text(vm.error?.localizedDescription ?? "")
        }
    }
    
    private func deleteButton(_ product: Product) -> some View {
        Button(role: .destructive) {
            Task { await vm.delete(product) }
        } label: {
            Label("Delete", systemImage: "trash")
        }
    }
}
```

### Protocol for testability
```swift
protocol ProductServiceProtocol {
    func fetchProducts() async throws -> [Product]
    func delete(_ id: String) async throws
}

// Real
final class ProductService: ProductServiceProtocol { ... }

// Test mock
final class MockProductService: ProductServiceProtocol {
    var mockProducts: [Product] = .preview
    func fetchProducts() async throws -> [Product] { mockProducts }
    func delete(_ id: String) async throws { mockProducts.removeAll { $0.id == id } }
}
```

---

## 2. MVVM + Coordinator (navigation)

### Coordinator protocol
```swift
protocol Coordinator: AnyObject {
    func start()
}

// Route enum per flow
enum AppRoute {
    case home
    case productDetail(Product)
    case settings
    case auth
}
```

### AppCoordinator
```swift
@Observable
final class AppCoordinator {
    var path = NavigationPath()
    var sheet: AppRoute?
    var fullScreenCover: AppRoute?
    
    func navigate(to route: AppRoute) {
        path.append(route)
    }
    
    func present(_ route: AppRoute, style: PresentationStyle = .sheet) {
        switch style {
        case .sheet: sheet = route
        case .fullScreen: fullScreenCover = route
        }
    }
    
    func pop() { path.removeLast() }
    func popToRoot() { path = NavigationPath() }
    func dismiss() { sheet = nil; fullScreenCover = nil }
}
```

### Root view with NavigationStack
```swift
struct AppCoordinatorView: View {
    @State private var coordinator = AppCoordinator()
    
    var body: some View {
        NavigationStack(path: $coordinator.path) {
            HomeView(coordinator: coordinator)
                .navigationDestination(for: AppRoute.self) { route in
                    view(for: route)
                }
        }
        .sheet(item: $coordinator.sheet) { route in
            view(for: route)
        }
    }
    
    @ViewBuilder
    private func view(for route: AppRoute) -> some View {
        switch route {
        case .home: HomeView(coordinator: coordinator)
        case .productDetail(let p): ProductDetailView(product: p, coordinator: coordinator)
        case .settings: SettingsView(coordinator: coordinator)
        case .auth: AuthView(coordinator: coordinator)
        }
    }
}
```

---

## 3. TCA (The Composable Architecture)

Use when: complex side effects, strict testability, large team, composable feature modules.

### Feature structure
```swift
@Reducer
struct ProductListFeature {
    
    // MARK: — State
    @ObservableState
    struct State: Equatable {
        var products: [Product] = []
        var isLoading = false
        var destination: Destination.State?
        
        @Reducer
        enum Destination {
            case detail(ProductDetailFeature)
            case alert(AlertState<Action.Alert>)
        }
    }
    
    // MARK: — Actions
    enum Action {
        case onAppear
        case productsLoaded(Result<[Product], Error>)
        case productTapped(Product)
        case deleteProduct(IndexSet)
        case destination(PresentationAction<Destination.Action>)
        
        enum Alert { case confirmDelete }
    }
    
    // MARK: — Dependencies
    @Dependency(\.productService) var productService
    
    // MARK: — Reducer
    var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .onAppear:
                state.isLoading = true
                return .run { send in
                    await send(.productsLoaded(
                        Result { try await productService.fetchAll() }
                    ))
                }
                
            case .productsLoaded(.success(let products)):
                state.isLoading = false
                state.products = products
                return .none
                
            case .productsLoaded(.failure):
                state.isLoading = false
                return .none
                
            case .productTapped(let product):
                state.destination = .detail(ProductDetailFeature.State(product: product))
                return .none
                
            default:
                return .none
            }
        }
        .ifLet(\.$destination, action: \.destination)
    }
}
```

### Dependency registration
```swift
extension DependencyValues {
    var productService: ProductServiceProtocol {
        get { self[ProductServiceKey.self] }
        set { self[ProductServiceKey.self] = newValue }
    }
}

private enum ProductServiceKey: DependencyKey {
    static let liveValue: ProductServiceProtocol = ProductService()
    static let testValue: ProductServiceProtocol = MockProductService()
    static let previewValue: ProductServiceProtocol = MockProductService(products: .preview)
}
```

---

## 4. Clean Architecture

Use when: domain logic heavy, multiple data sources, team > 4 people.

### Layer structure
```
Presentation (ViewModels, Views)
    ↓ calls
Domain (Use Cases, Entities, Repository protocols)
    ↓ calls
Data (Repository implementations, API clients, DB)
```

### Use case
```swift
protocol FetchProductsUseCaseProtocol {
    func execute(category: Category?) async throws -> [Product]
}

final class FetchProductsUseCase: FetchProductsUseCaseProtocol {
    private let repository: ProductRepositoryProtocol
    
    init(repository: ProductRepositoryProtocol) {
        self.repository = repository
    }
    
    func execute(category: Category?) async throws -> [Product] {
        let products = try await repository.fetchAll()
        return category.map { c in products.filter { $0.category == c } } ?? products
    }
}
```

### Repository pattern
```swift
protocol ProductRepositoryProtocol {
    func fetchAll() async throws -> [Product]
    func fetch(id: String) async throws -> Product
    func save(_ product: Product) async throws
    func delete(id: String) async throws
}

final class ProductRepository: ProductRepositoryProtocol {
    private let remote: ProductAPIProtocol
    private let local: ProductCacheProtocol
    
    func fetchAll() async throws -> [Product] {
        if let cached = try? local.getAll(), !cached.isEmpty {
            // Return cache and refresh in background
            Task { try? await refreshAndCache() }
            return cached
        }
        return try await refreshAndCache()
    }
    
    @discardableResult
    private func refreshAndCache() async throws -> [Product] {
        let products = try await remote.fetchProducts()
        try? local.save(products)
        return products
    }
}
```

---

## 5. VIPER

Use when: very large teams, strict separation, legacy codebases.

```
View       → UI only, zero logic
Interactor → business logic, use cases
Presenter  → transforms Interactor output for View
Entity     → data models
Router     → navigation
```

Avoid VIPER for new SwiftUI projects — overhead without gain over Clean+MVVM.

---

## 6. When to use what

| Situation | Pattern |
|---|---|
| Single screen, simple data | MVC / plain SwiftUI |
| Most apps | MVVM |
| Complex navigation | MVVM + Coordinator |
| Complex side effects / large team / strict tests | TCA |
| Domain-heavy / multiple data sources | Clean Architecture |
| Legacy UIKit large codebase | VIPER |

**DI principle:** Always inject dependencies through `init`. Never use singletons in business logic.
