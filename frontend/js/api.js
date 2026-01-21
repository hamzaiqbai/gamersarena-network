/**
 * GAN API Client
 */

const API = {
    // Get auth token
    getToken() {
        return localStorage.getItem(CONFIG.storageKeys.token);
    },
    
    // Set auth token
    setToken(token) {
        localStorage.setItem(CONFIG.storageKeys.token, token);
    },
    
    // Clear auth
    clearAuth() {
        localStorage.removeItem(CONFIG.storageKeys.token);
        localStorage.removeItem(CONFIG.storageKeys.user);
    },
    
    // Make API request
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const token = this.getToken();
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.clearAuth();
                window.location.href = 'index.html';
                return null;
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    // ==================== Auth ====================
    
    async getCurrentUser() {
        return this.request('/api/auth/me');
    },
    
    async checkAuth() {
        return this.request('/api/auth/check');
    },
    
    async logout() {
        this.clearAuth();
        window.location.href = 'index.html';
    },
    
    // ==================== Users ====================
    
    async getProfile() {
        return this.request('/api/users/profile');
    },
    
    async updateProfile(profileData) {
        return this.request('/api/users/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    },
    
    async checkProfileStatus() {
        return this.request('/api/users/check-profile-status');
    },
    
    async searchUser(email) {
        return this.request(`/api/users/search?email=${encodeURIComponent(email)}`);
    },
    
    // ==================== WhatsApp ====================
    
    async sendWhatsAppCode(phoneNumber) {
        return this.request('/api/whatsapp/send-code', {
            method: 'POST',
            body: JSON.stringify({ whatsapp_number: phoneNumber })
        });
    },
    
    async verifyWhatsAppCode(code) {
        return this.request('/api/whatsapp/verify-code', {
            method: 'POST',
            body: JSON.stringify({ code })
        });
    },
    
    // ==================== Wallets ====================
    
    async getBalance() {
        return this.request('/api/wallets/balance');
    },
    
    async getTransactions(page = 1, perPage = 20) {
        return this.request(`/api/wallets/transactions?page=${page}&per_page=${perPage}`);
    },
    
    async transferTokens(recipientEmail, amount) {
        return this.request('/api/wallets/transfer', {
            method: 'POST',
            body: JSON.stringify({
                recipient_email: recipientEmail,
                amount: amount,
                token_type: 'reward'
            })
        });
    },
    
    // ==================== Payments ====================
    
    async getBundles() {
        return this.request('/api/payments/bundles');
    },
    
    async initiatePayment(bundleId, paymentMethod, mobileNumber) {
        return this.request('/api/payments/initiate', {
            method: 'POST',
            body: JSON.stringify({
                bundle_id: bundleId,
                payment_method: paymentMethod,
                mobile_number: mobileNumber
            })
        });
    },
    
    async checkPaymentStatus(transactionId) {
        return this.request(`/api/payments/status/${transactionId}`);
    },
    
    async getReceipt(transactionId) {
        return this.request(`/api/payments/receipt/${transactionId}`);
    },
    
    // ==================== Tournaments ====================
    
    async getTournaments(page = 1, perPage = 20, game = null, status = null) {
        let url = `/api/tournaments?page=${page}&per_page=${perPage}`;
        if (game) url += `&game=${game}`;
        if (status) url += `&status=${status}`;
        return this.request(url);
    },
    
    async getTournament(tournamentId) {
        return this.request(`/api/tournaments/${tournamentId}`);
    },
    
    async registerForTournament(tournamentId, playerId = null, teamName = null) {
        return this.request(`/api/tournaments/${tournamentId}/register`, {
            method: 'POST',
            body: JSON.stringify({
                player_id: playerId,
                team_name: teamName
            })
        });
    },
    
    async getMyRegistrations(status = null) {
        let url = '/api/tournaments/my-registrations';
        if (status) url += `?status=${status}`;
        return this.request(url);
    },
    
    async getParticipants(tournamentId) {
        return this.request(`/api/tournaments/${tournamentId}/participants`);
    },
    
    async checkIn(tournamentId) {
        return this.request(`/api/tournaments/${tournamentId}/check-in`, {
            method: 'POST'
        });
    }
};

// Export for use in other files
window.API = API;
