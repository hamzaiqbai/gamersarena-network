/**
 * GAN Authentication Handler
 */

const Auth = {
    // Check if user is authenticated
    isAuthenticated() {
        return !!localStorage.getItem(CONFIG.storageKeys.token);
    },
    
    // Require authentication - redirect to login if not authenticated
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    },
    
    // Handle OAuth callback token
    handleCallback() {
        const token = Utils.getUrlParam('token');
        if (token) {
            API.setToken(token);
            // Clear URL params
            window.history.replaceState({}, document.title, window.location.pathname);
            return true;
        }
        return false;
    },
    
    // Initialize user menu
    async initUserMenu() {
        try {
            const user = await API.getCurrentUser();
            if (user) {
                this.updateUserUI(user);
                return user;
            }
        } catch (error) {
            console.error('Failed to get user:', error);
        }
        return null;
    },
    
    // Update user interface elements
    updateUserUI(user) {
        // Update avatar
        const avatarEls = document.querySelectorAll('#userAvatar');
        avatarEls.forEach(el => {
            if (user.avatar_url) {
                el.src = user.avatar_url;
            }
        });
        
        // Update name
        const nameEls = document.querySelectorAll('#userName');
        nameEls.forEach(el => {
            el.textContent = user.full_name || 'User';
        });
        
        // Update email
        const emailEls = document.querySelectorAll('#userEmail');
        emailEls.forEach(el => {
            el.textContent = user.email;
        });
    },
    
    // Initialize wallet balance display
    async initWalletBalance() {
        try {
            const wallet = await API.getBalance();
            if (wallet) {
                const balanceEl = document.getElementById('tokenBalance');
                if (balanceEl) {
                    balanceEl.textContent = Utils.formatNumber(wallet.total_balance);
                }
            }
        } catch (error) {
            console.error('Failed to get balance:', error);
        }
    },
    
    // Setup logout handler
    setupLogout() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                API.logout();
            });
        }
    },
    
    // Setup user dropdown menu
    setupDropdown() {
        const userMenu = document.getElementById('userMenu');
        const dropdown = document.getElementById('dropdownMenu');
        
        if (userMenu && dropdown) {
            userMenu.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('hidden');
            });
            
            // Close on outside click
            document.addEventListener('click', () => {
                dropdown.classList.add('hidden');
            });
        }
    },
    
    // Full initialization for authenticated pages
    async init() {
        // Check authentication
        if (!this.requireAuth()) return null;
        
        // Handle callback if present
        this.handleCallback();
        
        // Setup UI
        this.setupDropdown();
        this.setupLogout();
        
        // Load user data
        const user = await this.initUserMenu();
        await this.initWalletBalance();
        
        return user;
    }
};

// Export for use in other files
window.Auth = Auth;
