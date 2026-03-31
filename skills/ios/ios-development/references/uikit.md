# UIKit Pipeline Reference

## Table of contents
1. ViewController lifecycle
2. Auto Layout
3. Custom UIView components
4. Table & Collection views
5. Delegates & protocols pattern
6. UIKit + SwiftUI interop

---

## 1. ViewController lifecycle

```
init → viewDidLoad → viewWillAppear → viewDidAppear
                   → viewWillDisappear → viewDidDisappear → deinit
```

```swift
class ProductListVC: UIViewController {
    // MARK: — Properties
    private lazy var tableView = UITableView()
    private var viewModel: ProductListViewModel
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: — Init
    init(viewModel: ProductListViewModel) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }
    required init?(coder: NSCoder) { fatalError() }
    
    // MARK: — Lifecycle
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConstraints()
        bindViewModel()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        // deselect rows, etc.
    }
    
    // MARK: — Setup
    private func setupUI() {
        title = "Products"
        view.backgroundColor = .systemBackground
        view.addSubview(tableView)
        tableView.delegate = self
        tableView.dataSource = self
        tableView.register(ProductCell.self, forCellReuseIdentifier: ProductCell.reuseId)
    }
    
    private func setupConstraints() {
        tableView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
    }
    
    private func bindViewModel() {
        viewModel.$products
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in self?.tableView.reloadData() }
            .store(in: &cancellables)
    }
}
```

---

## 2. Auto Layout

### Programmatic (preferred for code-only UIKit)
```swift
// Always set this
view.translatesAutoresizingMaskIntoConstraints = false

// Activate all at once
NSLayoutConstraint.activate([
    // Pin to superview with padding
    subview.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 16),
    subview.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
    subview.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
    
    // Fixed height
    subview.heightAnchor.constraint(equalToConstant: 48),
    
    // Relative sizing
    imageView.widthAnchor.constraint(equalTo: view.widthAnchor, multiplier: 0.5),
    imageView.heightAnchor.constraint(equalTo: imageView.widthAnchor),  // square
    
    // Center
    label.centerXAnchor.constraint(equalTo: view.centerXAnchor),
    label.centerYAnchor.constraint(equalTo: view.centerYAnchor),
])
```

### UIStackView for linear layouts
```swift
let stack = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel, button])
stack.axis = .vertical
stack.spacing = 8
stack.alignment = .leading
stack.distribution = .fill
view.addSubview(stack)
```

### Content hugging & compression resistance
```swift
// Which view expands when there's extra space (lower = expands more)
label.setContentHuggingPriority(.defaultLow, for: .horizontal)
button.setContentHuggingPriority(.defaultHigh, for: .horizontal)

// Which view resists being clipped (higher = resists more)
label.setContentCompressionResistancePriority(.defaultHigh, for: .vertical)
```

---

## 3. Custom UIView components

```swift
final class ProductCardView: UIView {
    // MARK: — Subviews
    private let imageView: UIImageView = {
        let iv = UIImageView()
        iv.contentMode = .scaleAspectFill
        iv.clipsToBounds = true
        iv.layer.cornerRadius = 8
        return iv
    }()
    
    private let nameLabel: UILabel = {
        let l = UILabel()
        l.font = .systemFont(ofSize: 16, weight: .semibold)
        l.numberOfLines = 2
        return l
    }()
    
    private let priceLabel: UILabel = {
        let l = UILabel()
        l.font = .systemFont(ofSize: 14)
        l.textColor = .systemGray
        return l
    }()
    
    // MARK: — Config model (not the domain model)
    struct Config {
        let imageName: String
        let name: String
        let price: String
    }
    
    // MARK: — Init
    override init(frame: CGRect) {
        super.init(frame: frame)
        setup()
    }
    required init?(coder: NSCoder) { fatalError() }
    
    private func setup() {
        let stack = UIStackView(arrangedSubviews: [imageView, nameLabel, priceLabel])
        stack.axis = .vertical
        stack.spacing = 8
        addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            imageView.heightAnchor.constraint(equalToConstant: 160),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -12),
        ])
        
        layer.cornerRadius = 12
        layer.shadowColor = UIColor.black.cgColor
        layer.shadowOpacity = 0.1
        layer.shadowRadius = 4
    }
    
    func configure(with config: Config) {
        imageView.image = UIImage(named: config.imageName)
        nameLabel.text = config.name
        priceLabel.text = config.price
    }
}
```

---

## 4. Table & Collection views

### UITableView with diffable data source
```swift
enum Section { case main }

class ProductListVC: UIViewController {
    private var tableView: UITableView!
    private var dataSource: UITableViewDiffableDataSource<Section, Product>!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        configureTableView()
        configureDataSource()
    }
    
    private func configureTableView() {
        tableView = UITableView(frame: view.bounds, style: .plain)
        tableView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        tableView.register(ProductCell.self, forCellReuseIdentifier: ProductCell.reuseId)
        view.addSubview(tableView)
    }
    
    private func configureDataSource() {
        dataSource = UITableViewDiffableDataSource(tableView: tableView) { tableView, indexPath, product in
            let cell = tableView.dequeueReusableCell(withIdentifier: ProductCell.reuseId, for: indexPath) as! ProductCell
            cell.configure(with: product)
            return cell
        }
    }
    
    func applySnapshot(products: [Product], animated: Bool = true) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Product>()
        snapshot.appendSections([.main])
        snapshot.appendItems(products)
        dataSource.apply(snapshot, animatingDifferences: animated)
    }
}
```

### UICollectionView with compositional layout
```swift
private func createLayout() -> UICollectionViewLayout {
    UICollectionViewCompositionalLayout { sectionIndex, _ in
        // Item
        let item = NSCollectionLayoutItem(
            layoutSize: NSCollectionLayoutSize(
                widthDimension: .fractionalWidth(0.5),
                heightDimension: .fractionalHeight(1.0)
            )
        )
        item.contentInsets = NSDirectionalEdgeInsets(top: 8, leading: 8, bottom: 8, trailing: 8)
        
        // Group (2 items per row)
        let group = NSCollectionLayoutGroup.horizontal(
            layoutSize: NSCollectionLayoutSize(
                widthDimension: .fractionalWidth(1.0),
                heightDimension: .absolute(220)
            ),
            subitem: item,
            count: 2
        )
        
        // Section
        let section = NSCollectionLayoutSection(group: group)
        section.contentInsets = NSDirectionalEdgeInsets(top: 0, leading: 8, bottom: 0, trailing: 8)
        
        // Header
        let headerSize = NSCollectionLayoutSize(widthDimension: .fractionalWidth(1.0), heightDimension: .absolute(44))
        section.boundarySupplementaryItems = [
            NSCollectionLayoutBoundarySupplementaryItem(layoutSize: headerSize, elementKind: UICollectionView.elementKindSectionHeader, alignment: .top)
        ]
        
        return section
    }
}
```

---

## 5. Delegates & protocols pattern

```swift
// Define protocol
protocol ProductCellDelegate: AnyObject {
    func productCell(_ cell: ProductCell, didTapFavorite product: Product)
    func productCell(_ cell: ProductCell, didTapAdd product: Product)
}

// Cell
final class ProductCell: UITableViewCell {
    static let reuseId = "ProductCell"
    
    weak var delegate: ProductCellDelegate?
    private var product: Product?
    
    func configure(with product: Product) {
        self.product = product
        // update UI
    }
    
    @objc private func favoriteTapped() {
        guard let product else { return }
        delegate?.productCell(self, didTapFavorite: product)
    }
}

// ViewController implements delegate
extension ProductListVC: ProductCellDelegate {
    func productCell(_ cell: ProductCell, didTapFavorite product: Product) {
        Task { await viewModel.toggleFavorite(product) }
    }
}
```

---

## 6. UIKit + SwiftUI interop

### SwiftUI inside UIKit (UIHostingController)
```swift
let swiftUIView = ProductGridView()
let hostingVC = UIHostingController(rootView: swiftUIView)

// As child view controller
addChild(hostingVC)
view.addSubview(hostingVC.view)
hostingVC.view.frame = containerView.bounds
hostingVC.didMove(toParent: self)
```

### UIKit inside SwiftUI (UIViewRepresentable)
```swift
struct MapView: UIViewRepresentable {
    @Binding var region: MKCoordinateRegion
    var annotations: [MKPointAnnotation]
    
    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator
        return mapView
    }
    
    func updateUIView(_ mapView: MKMapView, context: Context) {
        mapView.setRegion(region, animated: true)
        mapView.addAnnotations(annotations)
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, MKMapViewDelegate {
        var parent: MapView
        init(_ parent: MapView) { self.parent = parent }
        
        func mapView(_ mapView: MKMapView, regionDidChangeAnimated animated: Bool) {
            parent.region = mapView.region
        }
    }
}
```
