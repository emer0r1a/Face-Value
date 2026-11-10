window.FV = window.FV || {};

(function (FV) {
    const KEYS = { products: 'fv-products', settings: 'fv-settings', notifications: 'fv-notifications', flash: 'fv-flash' };
    const memory = {};

    FV.CATEGORIES = ['Cleanser', 'Toner', 'Serum', 'Moisturizer', 'Sunscreen', 'Exfoliant', 'Mask', 'Eye Care', 'Treatment'];

    function read(key, fallback) {
        try {
            const raw = localStorage.getItem(key);
            return raw === null ? fallback : JSON.parse(raw);
        } catch (err) {
            return key in memory ? memory[key] : fallback;
        }
    }

    function write(key, value) {
        memory[key] = value;
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (err) {}
    }

    function daysAgo(n) {
        return new Date(Date.now() - n * 86400000).toISOString();
    }

    function seedProducts() {
        return [
            { id: 's1', name: 'Hydrating Facial Cleanser', brand: 'CeraVe', category: 'Cleanser', description: 'A gentle, non-foaming cleanser that removes dirt and makeup without stripping the skin barrier. Suitable for normal to dry skin.', ingredients: ['Water', 'Glycerin', 'Ceramide NP', 'Ceramide AP', 'Ceramide EOP', 'Hyaluronic Acid', 'Cholesterol', 'Phytosphingosine'], added: daysAgo(12) },
            { id: 's2', name: '10% Niacinamide Serum', brand: 'The Ordinary', category: 'Serum', description: 'A lightweight serum aimed at visible blemishes and congestion. Patch test first if you are new to niacinamide.', ingredients: ['Water', 'Niacinamide', 'Zinc PCA', 'Pentylene Glycol', 'Tamarindus Indica Seed Gum'], added: daysAgo(9) },
            { id: 's3', name: 'Daily Moisturizing Lotion', brand: 'Cetaphil', category: 'Moisturizer', description: 'Fragrance-free daily lotion with a light, fast-absorbing texture.', ingredients: ['Water', 'Glycerin', 'Dimethicone', 'Panthenol', 'Niacinamide'], added: daysAgo(7) },
            { id: 's4', name: 'Anthelios Melt-in Milk SPF 60', brand: 'La Roche-Posay', category: 'Sunscreen', description: 'Broad spectrum, water-resistant sunscreen for face and body. Reapply every two hours outdoors.', ingredients: ['Aqua', 'Homosalate', 'Octocrylene', 'Avobenzone', 'Glycerin', 'Silica'], added: daysAgo(5) },
            { id: 's5', name: 'BHA Liquid Exfoliant 2%', brand: "Paula's Choice", category: 'Exfoliant', description: 'Leave-on salicylic acid exfoliant that unclogs pores and smooths texture. Use in the evening, a few times a week.', ingredients: ['Water', 'Methylpropanediol', 'Butylene Glycol', 'Salicylic Acid', 'Polysorbate 20', 'Camellia Oleifera Leaf Extract', 'Sodium Hydroxide', 'Tetrasodium EDTA'], added: daysAgo(3) },
            { id: 's6', name: 'Rose Soothing Toner', brand: 'Klairs', category: 'Toner', description: '', ingredients: [], added: daysAgo(1) }
        ];
    }

    function seedNotifications() {
        return [
            { id: 'n1', title: 'Welcome to Face Value', body: 'Start by adding the products on your shelf.', time: 'Just now', read: false },
            { id: 'n2', title: 'Patch-test reminder', body: 'Try new actives on a small area for 24 hours first.', time: '1 day ago', read: false },
            { id: 'n3', title: 'Sunscreen check', body: 'Daily SPF is the single biggest win for your skin.', time: '3 days ago', read: true }
        ];
    }

    FV.store = {
        getProducts() {
            let list = read(KEYS.products, null);
            if (!Array.isArray(list)) {
                list = seedProducts();
                write(KEYS.products, list);
            }
            return list;
        },
        addProduct(product) {
            const list = this.getProducts();
            const record = Object.assign({ id: 'p' + Date.now().toString(36), added: new Date().toISOString() }, product);
            list.unshift(record);
            write(KEYS.products, list);
            return record;
        },
        resetProducts() {
            write(KEYS.products, seedProducts());
        },
        getSettings() {
            return Object.assign({ name: '', bio: '', darkMode: false, emailNotifications: true }, read(KEYS.settings, {}));
        },
        saveSettings(patch) {
            const next = Object.assign(this.getSettings(), patch);
            write(KEYS.settings, next);
            return next;
        },
        getNotifications() {
            let list = read(KEYS.notifications, null);
            if (!Array.isArray(list)) {
                list = seedNotifications();
                write(KEYS.notifications, list);
            }
            return list;
        },
        markAllRead() {
            const list = this.getNotifications().map(function (n) { return Object.assign({}, n, { read: true }); });
            write(KEYS.notifications, list);
            return list;
        },
        setFlash(message, type) {
            try {
                sessionStorage.setItem(KEYS.flash, JSON.stringify({ message: message, type: type || 'success' }));
            } catch (err) {
                memory[KEYS.flash] = { message: message, type: type || 'success' };
            }
        },
        takeFlash() {
            let value = null;
            try {
                value = JSON.parse(sessionStorage.getItem(KEYS.flash));
                sessionStorage.removeItem(KEYS.flash);
            } catch (err) {
                value = memory[KEYS.flash] || null;
                delete memory[KEYS.flash];
            }
            return value;
        }
    };

    FV.parseIngredients = function (text) {
        const seen = new Set();
        const names = [];
        let duplicates = 0;
        String(text).split(/[,\n]/).forEach(function (part) {
            const name = part.trim().replace(/\s+/g, ' ');
            if (!name) return;
            const key = name.toLowerCase();
            if (seen.has(key)) {
                duplicates += 1;
                return;
            }
            seen.add(key);
            names.push(name);
        });
        return { names: names, duplicates: duplicates };
    };

    FV.plural = function (n, one, many) {
        return n + ' ' + (n === 1 ? one : many || one + 's');
    };

    FV.formatDate = function (iso) {
        const d = new Date(iso);
        if (isNaN(d)) return '';
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    FV.cardColor = function (index) {
        return ['c-blue', 'c-butter', 'c-mint', 'c-lilac'][index % 4];
    };
})(window.FV);
