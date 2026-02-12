/**
 * GAN Configuration
 */

// API Base URL - Auto-detect based on environment
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const API_BASE_URL = isProduction ? 'https://gamersarena.network' : 'http://localhost:8000';

// App Configuration
const CONFIG = {
    appName: 'GAN - Gaming Arena Network',
    tokenName: 'Tokens',
    currency: 'PKR',
    currencySymbol: 'Rs.',
    
    // Local Storage Keys
    storageKeys: {
        token: 'gan_token',
        user: 'gan_user'
    },
    
    // Game Types
    games: {
        freefire: { name: 'Free Fire', icon: 'fa-fire', color: '#FF5722' },
        pubg: { name: 'PUBG Mobile', icon: 'fa-crosshairs', color: '#FFC107' },
        cod_mobile: { name: 'COD Mobile', icon: 'fa-gun', color: '#4CAF50' },
        valorant: { name: 'Valorant', icon: 'fa-shield-alt', color: '#E91E63' },
        counter_strike: { name: 'Counter Strike', icon: 'fa-bullseye', color: '#2196F3' },
        fortnite: { name: 'Fortnite', icon: 'fa-hammer', color: '#9C27B0' }
    },
    
    // Transaction Types Display
    transactionTypes: {
        purchase: { label: 'Token Purchase', icon: 'fa-shopping-cart', class: 'purchase' },
        tournament_entry: { label: 'Tournament Entry', icon: 'fa-ticket-alt', class: 'spend' },
        tournament_reward: { label: 'Tournament Reward', icon: 'fa-trophy', class: 'reward' },
        transfer_in: { label: 'Tokens Received', icon: 'fa-arrow-down', class: 'reward' },
        transfer_out: { label: 'Tokens Sent', icon: 'fa-arrow-up', class: 'spend' },
        refund: { label: 'Refund', icon: 'fa-undo', class: 'purchase' }
    },
    
    // Status Display
    tournamentStatus: {
        draft: { label: 'Draft', class: 'draft' },
        upcoming: { label: 'Upcoming', class: 'upcoming' },
        registration_open: { label: 'Registration Open', class: 'open' },
        registration_closed: { label: 'Registration Closed', class: 'closed' },
        active: { label: 'Live Now', class: 'active' },
        completed: { label: 'Completed', class: 'completed' },
        cancelled: { label: 'Cancelled', class: 'cancelled' }
    }
};

// Utility Functions
const Utils = {
    // Format number with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    // Format currency
    formatCurrency(amount, currency = 'PKR') {
        if (currency === 'PKR') {
            return `Rs. ${this.formatNumber(Math.round(amount))}`;
        }
        return `$${amount.toFixed(2)}`;
    },
    
    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Format relative time
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = date - now;
        
        if (diff < 0) {
            return 'Started';
        }
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(hours / 24);
        
        if (days > 0) {
            return `${days}d ${hours % 24}h`;
        }
        return `${hours}h`;
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to document
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
    
    // Show loading overlay
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    },
    
    // Hide loading overlay
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    },
    
    // Get URL parameter
    getUrlParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },
    
    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }
};

// Maintenance Check - runs on all pages except maintenance.html
async function checkMaintenanceMode() {
    // Skip if already on maintenance page
    if (window.location.pathname.includes('maintenance.html')) {
        return false;
    }
    
    // Skip if on admin panel
    if (window.location.pathname.includes('/admin/')) {
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/maintenance/status`);
        const data = await response.json();
        
        if (data.maintenance === true) {
            // Redirect to maintenance page
            window.location.href = 'maintenance.html';
            return true;
        }
    } catch (error) {
        console.error('Failed to check maintenance status:', error);
    }
    
    return false;
}

// Auto-check maintenance on page load
document.addEventListener('DOMContentLoaded', () => {
    checkMaintenanceMode();
});

// Export for use in other files
window.CONFIG = CONFIG;
window.Utils = Utils;
window.API_BASE_URL = API_BASE_URL;
window.checkMaintenanceMode = checkMaintenanceMode;
