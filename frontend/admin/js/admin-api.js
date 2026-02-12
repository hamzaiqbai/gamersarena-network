/**
 * GAN Admin Panel - API Service
 */

const ADMIN_API = {
    // Detect environment and set base URL
    // Always use main domain for API calls (CORS is configured to allow admin subdomain)
    BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : 'https://gamersarena.network',
    
    token: localStorage.getItem('admin_token'),
    
    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            if (response.status === 401) {
                this.logout();
                throw new Error('Session expired. Please login again.');
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * Set auth token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('admin_token', token);
    },
    
    /**
     * Clear auth token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('admin_token');
    },
    
    /**
     * Logout
     */
    logout() {
        this.clearToken();
        localStorage.removeItem('admin_user');
        window.location.reload();
    },
    
    // ==================== Auth ====================
    
    async login(email, password) {
        const data = await this.request('/api/admin/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        this.setToken(data.token);
        localStorage.setItem('admin_user', JSON.stringify(data.admin));
        return data;
    },
    
    async setup(email, password, full_name) {
        const data = await this.request('/api/admin/auth/setup', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name })
        });
        this.setToken(data.token);
        localStorage.setItem('admin_user', JSON.stringify(data.admin));
        return data;
    },
    
    async requestPasswordReset(email) {
        return await this.request('/api/admin/auth/reset-password-request', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    },
    
    async resetPassword(token, new_password) {
        return await this.request('/api/admin/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, new_password })
        });
    },
    
    async getProfile() {
        return await this.request('/api/admin/auth/me');
    },
    
    // ==================== Dashboard ====================
    
    async getDashboardStats() {
        return await this.request('/api/admin/dashboard/stats');
    },
    
    // ==================== Users ====================
    
    async getUsers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/admin/users?${query}`);
    },
    
    async getUserDetails(userId) {
        return await this.request(`/api/admin/users/${userId}`);
    },
    
    async blockUser(userId) {
        return await this.request(`/api/admin/users/${userId}/block`, {
            method: 'PUT'
        });
    },
    
    async unblockUser(userId) {
        return await this.request(`/api/admin/users/${userId}/unblock`, {
            method: 'PUT'
        });
    },
    
    async deleteUser(userId) {
        return await this.request(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });
    },
    
    // ==================== Wallets ====================
    
    async getWallets(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/admin/wallets?${query}`);
    },
    
    async addTokens(userId, amount, tokenType, reason) {
        const query = new URLSearchParams({
            amount,
            token_type: tokenType,
            reason
        }).toString();
        return await this.request(`/api/admin/wallets/${userId}/add-tokens?${query}`, {
            method: 'POST'
        });
    },
    
    // ==================== Tournaments ====================
    
    async getTournaments(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/admin/tournaments?${query}`);
    },
    
    async getTournament(tournamentId) {
        return await this.request(`/api/admin/tournaments/${tournamentId}`);
    },
    
    async uploadBanner(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const url = `${this.BASE_URL}/api/admin/upload/banner`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return await response.json();
    },
    
    async createTournament(data) {
        return await this.request('/api/admin/tournaments', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async updateTournament(tournamentId, data) {
        return await this.request(`/api/admin/tournaments/${tournamentId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async deleteTournament(tournamentId) {
        return await this.request(`/api/admin/tournaments/${tournamentId}`, {
            method: 'DELETE'
        });
    },
    
    async completeTournament(tournamentId, winners = null) {
        return await this.request(`/api/admin/tournaments/${tournamentId}/complete`, {
            method: 'POST',
            body: JSON.stringify({ winners })
        });
    },
    
    // ==================== Transactions ====================
    
    async getTransactions(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/admin/transactions?${query}`);
    },
    
    async getTransactionStats() {
        return await this.request('/api/admin/transactions/stats');
    },
    
    // ==================== Rewards ====================
    
    async getLeaderboard(limit = 20) {
        return await this.request(`/api/admin/rewards/leaderboard?limit=${limit}`);
    },
    
    async getRewardsStats() {
        return await this.request('/api/admin/rewards/stats');
    },
    
    // ==================== Products (Subscriptions & Tokens) ====================
    
    async getProducts(params = {}) {
        const query = new URLSearchParams();
        if (params.product_type) query.append('product_type', params.product_type);
        if (params.status) query.append('status', params.status);
        return await this.request(`/api/admin/products?${query.toString()}`);
    },
    
    async getProduct(productId) {
        return await this.request(`/api/admin/products/${productId}`);
    },
    
    async createProduct(productData) {
        return await this.request('/api/admin/products', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    },
    
    async updateProduct(productId, productData) {
        return await this.request(`/api/admin/products/${productId}`, {
            method: 'PUT',
            body: JSON.stringify(productData)
        });
    },
    
    async deleteProduct(productId) {
        return await this.request(`/api/admin/products/${productId}`, {
            method: 'DELETE'
        });
    },
    
    async getProductCategories() {
        return await this.request('/api/admin/products/categories/all');
    },

    },
    
    async updateMaintenanceSettings(settings) {
        return await this.request('/api/admin/maintenance', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    }
};

// Export for use
window.ADMIN_API = ADMIN_API;
