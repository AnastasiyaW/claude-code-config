# iOS Data Persistence Reference

## Table of contents
1. SwiftData (iOS 17+)
2. CoreData (iOS 13+)
3. UserDefaults
4. Keychain
5. FileManager
6. When to use what

---

## 1. SwiftData (iOS 17+)

### Model definition
```swift
@Model
final class Product {
    @Attribute(.unique) var id: String
    var name: String
    var price: Decimal
    var createdAt: Date
    var category: Category?  // optional relationship
    
    @Relationship(deleteRule: .cascade)
    var variants: [ProductVariant] = []
    
    init(id: String = UUID().uuidString, name: String, price: Decimal) {
        self.id = id
        self.name = name
        self.price = price
        self.createdAt = .now
    }
}
```

### Setup
```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: [Product.self, Category.self])
    }
}
```

### CRUD in ViewModel
```swift
@Observable
final class ProductStore {
    var products: [Product] = []
    private let modelContext: ModelContext
    
    init(modelContext: ModelContext) {
        self.modelContext = modelContext
        fetch()
    }
    
    func fetch(predicate: Predicate<Product>? = nil, sortBy: [SortDescriptor<Product>] = []) {
        let descriptor = FetchDescriptor<Product>(
            predicate: predicate,
            sortBy: sortBy.isEmpty ? [SortDescriptor(\.createdAt, order: .reverse)] : sortBy
        )
        products = (try? modelContext.fetch(descriptor)) ?? []
    }
    
    func add(_ product: Product) {
        modelContext.insert(product)
        try? modelContext.save()
        fetch()
    }
    
    func delete(_ product: Product) {
        modelContext.delete(product)
        try? modelContext.save()
        fetch()
    }
}
```

### Queries in View (iOS 17+)
```swift
struct ProductListView: View {
    @Query(sort: \Product.createdAt, order: .reverse) private var products: [Product]
    @Environment(\.modelContext) private var context
    
    var body: some View {
        List(products) { product in
            ProductRow(product: product)
        }
    }
}
```

---

## 2. CoreData (iOS 13+)

### Stack setup
```swift
final class PersistenceController {
    static let shared = PersistenceController()
    
    let container: NSPersistentContainer
    
    init(inMemory: Bool = false) {
        container = NSPersistentContainer(name: "Model")
        if inMemory {
            container.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        }
        container.loadPersistentStores { _, error in
            if let error { fatalError("CoreData error: \(error)") }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
    }
    
    // Background context for heavy operations
    func backgroundContext() -> NSManagedObjectContext {
        let ctx = container.newBackgroundContext()
        ctx.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        return ctx
    }
}
```

### Repository on top of CoreData
```swift
final class ProductCoreDataRepository {
    private let context: NSManagedObjectContext
    
    init(context: NSManagedObjectContext = PersistenceController.shared.container.viewContext) {
        self.context = context
    }
    
    func fetchAll() throws -> [Product] {
        let request = ProductEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(key: "createdAt", ascending: false)]
        return try context.fetch(request).map { Product(from: $0) }
    }
    
    func save(_ product: Product) throws {
        let entity = ProductEntity(context: context)
        entity.id = product.id
        entity.name = product.name
        entity.price = product.price as NSDecimalNumber
        try context.save()
    }
    
    func delete(id: String) throws {
        let request = ProductEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %@", id)
        if let entity = try context.fetch(request).first {
            context.delete(entity)
            try context.save()
        }
    }
}
```

### Background operations
```swift
func importProducts(_ products: [Product]) async throws {
    let bgContext = PersistenceController.shared.backgroundContext()
    try await bgContext.perform {
        for product in products {
            let entity = ProductEntity(context: bgContext)
            entity.id = product.id
            entity.name = product.name
        }
        try bgContext.save()
    }
}
```

---

## 3. UserDefaults

### Type-safe wrapper
```swift
@propertyWrapper
struct UserDefault<T> {
    let key: String
    let defaultValue: T
    
    var wrappedValue: T {
        get { UserDefaults.standard.object(forKey: key) as? T ?? defaultValue }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }
}

// Usage
enum Preferences {
    @UserDefault(key: "hasOnboarded", defaultValue: false)
    static var hasOnboarded: Bool
    
    @UserDefault(key: "selectedTheme", defaultValue: "system")
    static var selectedTheme: String
    
    @UserDefault(key: "notificationsEnabled", defaultValue: true)
    static var notificationsEnabled: Bool
}
```

### Codable in UserDefaults
```swift
extension UserDefaults {
    func setCodable<T: Codable>(_ value: T, forKey key: String) {
        let data = try? JSONEncoder().encode(value)
        set(data, forKey: key)
    }
    
    func getCodable<T: Codable>(_ type: T.Type, forKey key: String) -> T? {
        guard let data = data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(type, from: data)
    }
}
```

---

## 4. Keychain

Use for: tokens, passwords, sensitive user data. Never use UserDefaults for these.

```swift
enum KeychainKey: String {
    case accessToken = "app.access_token"
    case refreshToken = "app.refresh_token"
    case userId = "app.user_id"
}

final class SecureStorage {
    static let shared = SecureStorage()
    
    func save(_ value: String, for key: KeychainKey) {
        let data = value.data(using: .utf8)!
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: Bundle.main.bundleIdentifier!,
            kSecAttrAccount: key.rawValue,
            kSecValueData: data
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    func get(_ key: KeychainKey) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: Bundle.main.bundleIdentifier!,
            kSecAttrAccount: key.rawValue,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)
        return (result as? Data).flatMap { String(data: $0, encoding: .utf8) }
    }
    
    func delete(_ key: KeychainKey) {
        SecItemDelete([
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: Bundle.main.bundleIdentifier!,
            kSecAttrAccount: key.rawValue
        ] as CFDictionary)
    }
    
    func clearAll() {
        KeychainKey.allCases.forEach { delete($0) }
    }
}
```

---

## 5. FileManager

```swift
enum FileStorage {
    static let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    static let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
    
    static func save<T: Encodable>(_ value: T, filename: String, directory: URL = documents) throws {
        let url = directory.appendingPathComponent(filename)
        let data = try JSONEncoder().encode(value)
        try data.write(to: url, options: .atomicWrite)
    }
    
    static func load<T: Decodable>(_ type: T.Type, filename: String, directory: URL = documents) throws -> T {
        let url = directory.appendingPathComponent(filename)
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(type, from: data)
    }
    
    static func delete(filename: String, directory: URL = documents) throws {
        let url = directory.appendingPathComponent(filename)
        if FileManager.default.fileExists(atPath: url.path) {
            try FileManager.default.removeItem(at: url)
        }
    }
    
    // Image caching to disk
    static func saveImage(_ image: UIImage, named filename: String) {
        let url = caches.appendingPathComponent(filename)
        try? image.jpegData(compressionQuality: 0.8)?.write(to: url)
    }
    
    static func loadImage(named filename: String) -> UIImage? {
        let url = caches.appendingPathComponent(filename)
        return UIImage(contentsOfFile: url.path)
    }
}
```

---

## 6. When to use what

| Data type | Solution |
|---|---|
| Small settings/flags | UserDefaults |
| Sensitive data (tokens, passwords) | Keychain |
| Structured relational data, iOS 17+ | SwiftData |
| Structured relational data, iOS 13+ | CoreData |
| Large files, user-generated content | FileManager (documents) |
| Temporary/downloaded files | FileManager (caches) |
| In-memory fast access | NSCache |
| Sync across devices | CloudKit / iCloud |
