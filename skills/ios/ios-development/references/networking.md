# iOS Networking Reference

## Table of contents
1. URLSession + async/await
2. API Client architecture
3. Authentication & tokens
4. REST patterns
5. Error handling & retry
6. Caching & offline
7. WebSockets

---

## 1. URLSession + async/await

### Base request
```swift
func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T {
    let (data, response) = try await URLSession.shared.data(from: url)
    guard let http = response as? HTTPURLResponse else {
        throw NetworkError.invalidResponse
    }
    guard 200..<300 ~= http.statusCode else {
        throw NetworkError.statusCode(http.statusCode)
    }
    return try JSONDecoder().decode(T.self, from: data)
}
```

### URLSession configuration
```swift
let config = URLSessionConfiguration.default
config.timeoutIntervalForRequest = 30
config.timeoutIntervalForResource = 300
config.waitsForConnectivity = true
config.requestCachePolicy = .reloadIgnoringLocalCacheData

let session = URLSession(configuration: config)
```

---

## 2. API Client architecture

### Generic API client
```swift
protocol APIClientProtocol {
    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T
}

final class APIClient: APIClientProtocol {
    private let session: URLSession
    private let decoder: JSONDecoder
    private let baseURL: URL
    
    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601
    }
    
    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        let urlRequest = try endpoint.urlRequest(baseURL: baseURL)
        let (data, response) = try await session.data(for: urlRequest)
        try validate(response: response, data: data)
        return try decoder.decode(T.self, from: data)
    }
    
    private func validate(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        switch http.statusCode {
        case 200..<300: return
        case 401: throw NetworkError.unauthorized
        case 404: throw NetworkError.notFound
        case 400..<500:
            let apiError = try? JSONDecoder().decode(APIErrorResponse.self, from: data)
            throw NetworkError.clientError(apiError?.message ?? "Bad request")
        case 500...: throw NetworkError.serverError(http.statusCode)
        default: throw NetworkError.statusCode(http.statusCode)
        }
    }
}
```

### Endpoint definition
```swift
struct Endpoint {
    let path: String
    let method: HTTPMethod
    var queryItems: [URLQueryItem]?
    var body: Encodable?
    var headers: [String: String] = [:]
    
    func urlRequest(baseURL: URL) throws -> URLRequest {
        var url = baseURL.appendingPathComponent(path)
        if let items = queryItems {
            url.append(queryItems: items)
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        headers.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        if let body {
            request.httpBody = try JSONEncoder().encode(body)
        }
        return request
    }
}

enum HTTPMethod: String {
    case get = "GET", post = "POST", put = "PUT", patch = "PATCH", delete = "DELETE"
}

// Usage
extension Endpoint {
    static func products(category: String? = nil) -> Self {
        Endpoint(
            path: "/products",
            method: .get,
            queryItems: category.map { [URLQueryItem(name: "category", value: $0)] }
        )
    }
    
    static func createProduct(_ product: CreateProductRequest) -> Self {
        Endpoint(path: "/products", method: .post, body: product)
    }
}
```

---

## 3. Authentication & tokens

### Token manager
```swift
actor TokenManager {
    private var accessToken: String?
    private var refreshToken: String?
    private var refreshTask: Task<String, Error>?
    
    func validToken() async throws -> String {
        if let token = accessToken, !isExpired(token) {
            return token
        }
        return try await refreshAccessToken()
    }
    
    private func refreshAccessToken() async throws -> String {
        // Coalesce concurrent refresh requests
        if let task = refreshTask { return try await task.value }
        
        let task = Task<String, Error> {
            defer { refreshTask = nil }
            guard let refresh = refreshToken else { throw AuthError.notAuthenticated }
            let response = try await AuthAPI.refresh(token: refresh)
            accessToken = response.accessToken
            return response.accessToken
        }
        refreshTask = task
        return try await task.value
    }
}
```

### Authenticated client with auto-refresh
```swift
final class AuthenticatedAPIClient: APIClientProtocol {
    private let base: APIClient
    private let tokenManager: TokenManager
    
    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        var ep = endpoint
        let token = try await tokenManager.validToken()
        ep.headers["Authorization"] = "Bearer \(token)"
        
        do {
            return try await base.request(ep)
        } catch NetworkError.unauthorized {
            // Force refresh and retry once
            let newToken = try await tokenManager.forceRefresh()
            ep.headers["Authorization"] = "Bearer \(newToken)"
            return try await base.request(ep)
        }
    }
}
```

### Keychain storage
```swift
enum Keychain {
    static func save(_ value: String, key: String) {
        let data = value.data(using: .utf8)!
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecValueData: data
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    static func get(key: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecReturnData: true
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)
        return (result as? Data).flatMap { String(data: $0, encoding: .utf8) }
    }
    
    static func delete(key: String) {
        SecItemDelete([kSecClass: kSecClassGenericPassword, kSecAttrAccount: key] as CFDictionary)
    }
}
```

---

## 4. REST patterns

### Paginated list
```swift
struct PaginatedResponse<T: Decodable>: Decodable {
    let items: [T]
    let nextCursor: String?
    let total: Int
}

@Observable
class PaginatedViewModel<T: Decodable> {
    var items: [T] = []
    var isLoading = false
    var hasMore = true
    private var cursor: String?
    
    func loadNext(endpoint: (String?) -> Endpoint) async {
        guard !isLoading, hasMore else { return }
        isLoading = true
        defer { isLoading = false }
        
        do {
            let page: PaginatedResponse<T> = try await api.request(endpoint(cursor))
            items.append(contentsOf: page.items)
            cursor = page.nextCursor
            hasMore = cursor != nil
        } catch { }
    }
}
```

### Multipart upload
```swift
func uploadImage(_ image: UIImage, to endpoint: URL) async throws -> String {
    let imageData = image.jpegData(compressionQuality: 0.8)!
    let boundary = UUID().uuidString
    
    var request = URLRequest(url: endpoint)
    request.httpMethod = "POST"
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(UploadResponse.self, from: data).url
}
```

---

## 5. Error handling & retry

```swift
enum NetworkError: LocalizedError {
    case invalidResponse
    case unauthorized
    case notFound
    case clientError(String)
    case serverError(Int)
    case statusCode(Int)
    case noInternet
    
    var errorDescription: String? {
        switch self {
        case .unauthorized: return "Session expired. Please sign in."
        case .notFound: return "Content not found."
        case .clientError(let msg): return msg
        case .serverError: return "Server error. Try again later."
        case .noInternet: return "No internet connection."
        default: return "Something went wrong."
        }
    }
}

// Exponential backoff retry
func withRetry<T>(maxAttempts: Int = 3, operation: () async throws -> T) async throws -> T {
    var lastError: Error?
    for attempt in 0..<maxAttempts {
        do {
            return try await operation()
        } catch let error as NetworkError {
            // Don't retry client errors
            if case .clientError = error { throw error }
            if case .unauthorized = error { throw error }
            lastError = error
            if attempt < maxAttempts - 1 {
                try await Task.sleep(nanoseconds: UInt64(pow(2.0, Double(attempt))) * 1_000_000_000)
            }
        }
    }
    throw lastError!
}
```

---

## 6. Caching & offline

```swift
final class CachedAPIClient: APIClientProtocol {
    private let base: APIClientProtocol
    private let cache = NSCache<NSString, CacheEntry>()
    
    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        let key = endpoint.cacheKey as NSString
        
        // Return cached if fresh
        if let entry = cache.object(forKey: key), !entry.isExpired {
            return try JSONDecoder().decode(T.self, from: entry.data)
        }
        
        do {
            let result: T = try await base.request(endpoint)
            let data = try JSONEncoder().encode(result as! Encodable)
            cache.setObject(CacheEntry(data: data, ttl: 300), forKey: key)
            return result
        } catch {
            // Return stale cache on network failure
            if let entry = cache.object(forKey: key) {
                return try JSONDecoder().decode(T.self, from: entry.data)
            }
            throw error
        }
    }
}
```

---

## 7. WebSockets

```swift
actor WebSocketClient {
    private var webSocketTask: URLSessionWebSocketTask?
    private var continuation: AsyncStream<Message>.Continuation?
    
    var messages: AsyncStream<Message> {
        AsyncStream { continuation in
            self.continuation = continuation
        }
    }
    
    func connect(to url: URL) {
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        startReceiving()
    }
    
    func send(_ message: Message) async throws {
        let data = try JSONEncoder().encode(message)
        try await webSocketTask?.send(.data(data))
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        continuation?.finish()
    }
    
    private func startReceiving() {
        Task {
            while let task = webSocketTask {
                do {
                    let message = try await task.receive()
                    if case .data(let data) = message,
                       let decoded = try? JSONDecoder().decode(Message.self, from: data) {
                        continuation?.yield(decoded)
                    }
                } catch {
                    continuation?.finish()
                    break
                }
            }
        }
    }
}
```
