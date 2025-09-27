 
        document.addEventListener('DOMContentLoaded', () => {

          const products = [
    {
        id: 1,
        name: 'Tonal Chair',
        price: 450,
        description: 'A minimalist chair crafted from solid oak.',
        imageUrl: 'https://images.pexels.com/photos/2082092/pexels-photo-2082092.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'The Tonal Chair is an exercise in restraint and balance. Its solid oak frame provides a sturdy foundation, while the woven linen canvas seat offers surprising comfort. Perfect as a dining chair or a standalone accent piece.',
        details: { materials: 'Solid Oak, Linen Canvas', dimensions: 'H 78cm x W 45cm x D 50cm' }
    },
    {
        id: 2,
        name: 'Ceramic Vase',
        price: 120,
        description: 'Hand-thrown ceramic vase with a matte glaze finish.',
        imageUrl: 'https://images.pexels.com/photos/7194915/pexels-photo-7194915.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'Each vase is uniquely shaped by hand, bearing the subtle marks of its creator. The matte white glaze provides a contemporary finish that complements any floral arrangement or stands beautifully on its own.',
        details: { materials: 'Stoneware Clay, Matte Glaze', dimensions: 'H 25cm x Ø 15cm' }
    },
    {
        id: 3,
        name: 'Arc Lamp',
        price: 780,
        description: 'An elegant floor lamp with a sweeping arc of brushed metal.',
        imageUrl: 'https://images.pexels.com/photos/1125136/pexels-photo-1125136.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'Make a statement with the Arc Lamp. Its dramatic form is balanced by a heavy marble base, ensuring stability. It provides warm, diffused light, perfect for reading nooks and living spaces.',
        details: { materials: 'Brushed Steel, Marble Base', dimensions: 'H 210cm x W 180cm' }
    },
    {
        id: 4,
        name: 'Modular Desk',
        price: 1250,
        description: 'A versatile desk system with configurable modules.',
        imageUrl: 'https://images.pexels.com/photos/7147040/pexels-photo-7147040.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'The Modular Desk adapts to your workflow. Constructed from sustainable bamboo and recycled aluminum, its components can be rearranged to suit your needs, offering a personalized and organized workspace.',
        details: { materials: 'Bamboo, Recycled Aluminum', dimensions: 'H 75cm x W 140cm x D 60cm' }
    },
    {
        id: 5,
        name: 'Woven Rug',
        price: 620,
        description: 'A hand-woven rug made from natural jute fibers.',
        imageUrl: 'https://images.pexels.com/photos/8346033/pexels-photo-8346033.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'Ground your space with the natural texture of our Woven Rug. Made from 100% jute, it is both durable and biodegradable. Its neutral tone and simple weave add warmth and texture to any room.',
        details: { materials: '100% Natural Jute', dimensions: '200cm x 300cm' }
    },
    {
        id: 6,
        name: 'Gravity Clock',
        price: 350,
        description: 'A unique timepiece that uses magnetic spheres to tell time.',
        imageUrl: 'https://images.pexels.com/photos/1299459/pexels-photo-1299459.jpeg?auto=compress&cs=tinysrgb&w=800',
        longDesc: 'The Gravity Clock is more than a way to tell time; it\'s a piece of kinetic art. Magnetic spheres move silently around the wooden face, marking the hours and minutes in a mesmerizing display.',
        details: { materials: 'Anodized Aluminum, Magnets', dimensions: 'H 30cm x W 30cm' }
    },
];
            let cart = JSON.parse(localStorage.getItem('apertureCart')) || [];

            // --- Element Selectors ---
            const Selectors = {
                pages: document.querySelectorAll('.page'),
                navLinks: document.querySelectorAll('.nav-link'),
                productGrid: document.getElementById('product-grid'),
                featuredGrid: document.getElementById('featured-product-grid'),
                productDetailContent: document.getElementById('product-detail-content'),
                cartBtn: document.getElementById('cart-btn'),
                cartCount: document.getElementById('cart-count'),
                mobileMenuBtn: document.getElementById('mobile-menu-btn'),
                mobileMenu: document.getElementById('mobile-menu'),
                contactForm: document.getElementById('contact-form'),
                toast: document.getElementById('toast'),
                cartOverlay: document.getElementById('cart-overlay'),
                cartModal: document.getElementById('cart-modal'),
                closeCartBtn: document.getElementById('close-cart-btn'),
                cartItemsContainer: document.getElementById('cart-items'),
                cartTotalEl: document.getElementById('cart-total'),
                preloader: document.getElementById('preloader'),
                header: document.getElementById('header'),
            };

            // --- UI/UX Functions ---
            const UI = {
                showPage(pageId) {
                    Selectors.pages.forEach(page => page.classList.remove('active'));
                    const activePage = document.getElementById(pageId);
                    if (activePage) {
                        activePage.classList.add('active');
                        window.scrollTo(0, 0);
                        setTimeout(() => this.handleScrollAnimations(), 100);
                    }
                },
                showToast(message) {
                    Selectors.toast.textContent = message;
                    Selectors.toast.classList.add('show');
                    setTimeout(() => Selectors.toast.classList.remove('show'), 3000);
                },
                handleScrollHeader() {
                    if (window.scrollY > 50) Selectors.header.classList.add('scrolled');
                    else Selectors.header.classList.remove('scrolled');
                },
                handleScrollAnimations() {
                    const observer = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                entry.target.classList.add('visible');
                            }
                        });
                    }, { threshold: 0.1 });
                    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
                },
                toggleMobileMenu() {
                    Selectors.mobileMenu.classList.toggle('-translate-y-full');
                },
                openCart() {
                    Cart.render();
                    Selectors.cartOverlay.classList.add('active');
                    Selectors.cartModal.classList.add('active');
                },
                closeCart() {
                    Selectors.cartOverlay.classList.remove('active');
                    Selectors.cartModal.classList.remove('active');
                }
            };

            // --- Product Rendering ---
            const ProductRenderer = {
                _createCard(product, index, delay = 0) {
                   return `
                        <div class="product-card cursor-pointer reveal" data-product-id="${product.id}" style="transition-delay: ${index * 0.1 + delay}s;">
                            <div class="product-image-container aspect-[3/4]"><img src="${product.imageUrl}" alt="${product.name}" class="product-image w-full h-full object-cover"></div>
                            <div class="p-6">
                                <h3 class="text-xl font-semibold">${product.name}</h3>
                                <p class="text-lg text-gray-400 mt-1">$${product.price}</p>
                            </div>
                        </div>`;
                },
                renderAll() {
                    if (!Selectors.productGrid) return;
                    Selectors.productGrid.innerHTML = products.map((p, i) => this._createCard(p, i, 0.3)).join('');
                },
                renderFeatured() {
                    if (!Selectors.featuredGrid) return;
                    const featured = products.slice(0, 3);
                    Selectors.featuredGrid.innerHTML = featured.map((p, i) => this._createCard(p, i)).join('');
                },
                renderDetail(productId) {
                    const product = products.find(p => p.id == productId);
                    if (!product) return;
                    Selectors.productDetailContent.innerHTML = `
                        <a href="#shop" class="nav-link secondary-btn mb-12">← Back to Shop</a>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-16 items-start">
                            <div class="bg-gray-800 rounded-2xl aspect-[3/4] reveal"><img src="${product.imageUrl}" alt="${product.name}" class="w-full h-full object-cover rounded-2xl"></div>
                            <div class="reveal" style="transition-delay: 0.2s;">
                                <h2 class="text-4xl md:text-5xl font-bold mb-4">${product.name}</h2>
                                <p class="text-3xl text-indigo-500 font-semibold mb-6">$${product.price}</p>
                                <p class="text-lg text-gray-400 mb-8">${product.longDesc}</p>
                                <div class="border-t border-gray-700 pt-6 mb-8">
                                    <h4 class="font-semibold mb-2">Materials</h4><p class="text-gray-400">${product.details.materials}</p>
                                    <h4 class="font-semibold mt-4 mb-2">Dimensions</h4><p class="text-gray-400">${product.details.dimensions}</p>
                                </div>
                                <button class="add-to-cart-btn primary-btn w-full sm:w-auto" data-product-id="${product.id}">Add to Cart</button>
                            </div>
                        </div>`;
                }
            };
            
            // --- Cart Logic ---
            const Cart = {
                save() {
                    localStorage.setItem('apertureCart', JSON.stringify(cart));
                },
                add(productId) {
                    const existingItem = cart.find(item => item.id == productId);
                    if (existingItem) {
                        existingItem.quantity++;
                    } else {
                        cart.push({ id: parseInt(productId), quantity: 1 });
                    }
                    this.save();
                    this.updateUI();
                    const product = products.find(p => p.id == productId);
                    UI.showToast(`${product.name} added to cart!`);
                },
                updateQuantity(productId, newQuantity) {
                    const item = cart.find(item => item.id == productId);
                    if (item) {
                        if (newQuantity > 0) item.quantity = newQuantity;
                        else this.remove(productId);
                        this.save();
                        this.render();
                    }
                },
                remove(productId) {
                    cart = cart.filter(item => item.id != productId);
                    this.save();
                    this.render();
                    const product = products.find(p => p.id == productId);
                    if(product) UI.showToast(`${product.name} removed from cart.`);
                },
                updateUI() {
                    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
                    Selectors.cartCount.textContent = `(${totalItems})`;
                },
                render() {
                    this.updateUI();
                    if (cart.length === 0) {
                        Selectors.cartItemsContainer.innerHTML = '<p class="text-gray-400">Your cart is empty.</p>';
                        Selectors.cartTotalEl.textContent = '$0';
                        return;
                    }

                    let total = 0;
                    Selectors.cartItemsContainer.innerHTML = cart.map(cartItem => {
                        const product = products.find(p => p.id === cartItem.id);
                        if (!product) return ''; // Skip if product not found
                        total += product.price * cartItem.quantity;
                        return `
                            <div class="flex items-center gap-4 mb-4">
                                <img src="${product.imageUrl}" alt="${product.name}" class="w-16 h-20 object-cover rounded-md">
                                <div class="flex-grow">
                                    <h4 class="font-semibold">${product.name}</h4>
                                    <p class="text-gray-400">$${product.price}</p>
                                    <div class="flex items-center gap-2 mt-2">
                                        <button class="cart-quantity-btn" data-id="${product.id}" data-change="-1">-</button>
                                        <span>${cartItem.quantity}</span>
                                        <button class="cart-quantity-btn" data-id="${product.id}" data-change="1">+</button>
                                    </div>
                                </div>
                                <button class="remove-from-cart-btn text-red-500 hover:text-red-400 font-bold" data-id="${product.id}">Remove</button>
                            </div>`;
                    }).join('');
                    Selectors.cartTotalEl.textContent = `$${total}`;
                }
            };
            
            // --- Event Listeners ---
            function setupEventListeners() {
                Selectors.navLinks.forEach(link => link.addEventListener('click', e => {
                    e.preventDefault(); UI.showPage(link.getAttribute('href').substring(1));
                    if (!Selectors.mobileMenu.classList.contains('-translate-y-full')) UI.toggleMobileMenu();
                }));
                const handleProductClick = e => {
                    const card = e.target.closest('.product-card');
                    if (card) {
                        ProductRenderer.renderDetail(card.dataset.productId);
                        UI.showPage('product-detail');
                    }
                };
                Selectors.productGrid.addEventListener('click', handleProductClick);
                Selectors.featuredGrid.addEventListener('click', handleProductClick);
                Selectors.productDetailContent.addEventListener('click', e => {
                    if (e.target.classList.contains('add-to-cart-btn')) Cart.add(e.target.dataset.productId);
                });
                Selectors.mobileMenuBtn.addEventListener('click', UI.toggleMobileMenu);
                Selectors.cartBtn.addEventListener('click', UI.openCart);
                Selectors.closeCartBtn.addEventListener('click', UI.closeCart);
                Selectors.cartOverlay.addEventListener('click', UI.closeCart);
                Selectors.cartItemsContainer.addEventListener('click', e => {
                    const target = e.target;
                    const id = target.dataset.id;
                    if (target.classList.contains('remove-from-cart-btn')) Cart.remove(id);
                    if (target.classList.contains('cart-quantity-btn')) {
                        const item = cart.find(i => i.id == id);
                        const change = parseInt(target.dataset.change);
                        Cart.updateQuantity(id, item.quantity + change);
                    }
                });
                Selectors.contactForm.addEventListener('submit', e => { e.preventDefault(); UI.showToast("Message sent!"); Selectors.contactForm.reset(); });
                window.addEventListener('scroll', () => { UI.handleScrollHeader(); UI.handleScrollAnimations(); });
                const cursor = document.querySelector('.cursor');
                window.addEventListener('mousemove', e => { cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px'; });
                document.querySelectorAll('a, button, .cursor-pointer').forEach(target => {
                    target.addEventListener('mouseenter', () => cursor.classList.add('hover-grow'));
                    target.addEventListener('mouseleave', () => cursor.classList.remove('hover-grow'));
                });
            }

            // --- Initial Load ---
            function init() {
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        Selectors.preloader.classList.add('fade-out');
                        setTimeout(() => Selectors.preloader.style.display = 'none', 500);
                        UI.showPage('home');
                        ProductRenderer.renderFeatured();
                        ProductRenderer.renderAll();
                        Cart.render();
                        setupEventListeners();
                    }, 500); // Simulate loading time
                });
            }

            init();
        });
    