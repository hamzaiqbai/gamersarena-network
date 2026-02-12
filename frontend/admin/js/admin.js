/**
 * GAN Admin Panel - Main Application
 */

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// ==================== State ====================
let currentTab = 'dashboard';
let usersPage = 0;
let transactionsPage = 0;

// ==================== Init ====================

async function initApp() {
    // Check if logged in
    if (ADMIN_API.token) {
        try {
            await ADMIN_API.getProfile();
            showDashboard();
        } catch (e) {
            showLoginScreen();
        }
    } else {
        showLoginScreen();
    }
    
    setupEventListeners();
}

function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('adminDashboard').classList.add('hidden');
    
    // Try to check if setup is needed
    checkSetupNeeded();
}

async function checkSetupNeeded() {
    try {
        // Check if setup is needed via dedicated endpoint
        const response = await fetch(`${ADMIN_API.BASE_URL}/api/admin/auth/check-setup`);
        const data = await response.json();
        
        if (data.setup_needed) {
            // No admin exists, show setup form
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('setupForm').classList.remove('hidden');
        } else {
            // Admin exists, show login form
            document.getElementById('loginForm').classList.remove('hidden');
            document.getElementById('setupForm').classList.add('hidden');
        }
    } catch (e) {
        // Network error - show login form as default
        console.error('Setup check failed:', e);
        document.getElementById('loginForm').classList.remove('hidden');
        document.getElementById('setupForm').classList.add('hidden');
    }
}

async function showDashboard() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('adminDashboard').classList.remove('hidden');
    
    // Set admin name
    const adminUser = JSON.parse(localStorage.getItem('admin_user') || '{}');
    document.getElementById('adminName').textContent = adminUser.full_name || adminUser.email || 'Admin';
    
    // Load dashboard data
    await loadDashboard();
}

// ==================== Event Listeners ====================

function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    
    // Setup form
    const setupForm = document.getElementById('setupForm');
    if (setupForm) setupForm.addEventListener('submit', handleSetup);
    
    // Reset form
    const resetForm = document.getElementById('resetForm');
    if (resetForm) resetForm.addEventListener('submit', handlePasswordReset);
    
    // Forgot password link
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('resetForm').classList.remove('hidden');
        });
    }
    
    // Back to login
    const backToLogin = document.getElementById('backToLogin');
    if (backToLogin) {
        backToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('resetForm').classList.add('hidden');
            document.getElementById('loginForm').classList.remove('hidden');
        });
    }
    
    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => ADMIN_API.logout());
    
    // Tab navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Tournament form
    const createTournamentBtn = document.getElementById('createTournamentBtn');
    if (createTournamentBtn) createTournamentBtn.addEventListener('click', () => openTournamentModal());
    
    const tournamentForm = document.getElementById('tournamentForm');
    if (tournamentForm) tournamentForm.addEventListener('submit', handleTournamentSubmit);
    
    // Add tokens form
    const addTokensForm = document.getElementById('addTokensForm');
    if (addTokensForm) addTokensForm.addEventListener('submit', handleAddTokens);
    
    // User search
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
        userSearch.addEventListener('input', debounce(() => {
            usersPage = 0;
            loadUsers();
        }, 300));
    }
    
    const userSearchBy = document.getElementById('userSearchBy');
    if (userSearchBy) {
        userSearchBy.addEventListener('change', () => {
            usersPage = 0;
            loadUsers();
        });
    }
    
    const userStatusFilter = document.getElementById('userStatusFilter');
    if (userStatusFilter) {
        userStatusFilter.addEventListener('change', () => {
            usersPage = 0;
            loadUsers();
        });
    }
    
    // Tournament filters
    const tournamentStatusFilter = document.getElementById('tournamentStatusFilter');
    if (tournamentStatusFilter) tournamentStatusFilter.addEventListener('change', loadTournaments);
    
    const tournamentGameFilter = document.getElementById('tournamentGameFilter');
    if (tournamentGameFilter) tournamentGameFilter.addEventListener('change', loadTournaments);
    
    // Banner upload
    const tournamentBannerFile = document.getElementById('tournamentBannerFile');
    if (tournamentBannerFile) tournamentBannerFile.addEventListener('change', handleBannerUpload);
    
    // Transaction filters
    const transactionStatusFilter = document.getElementById('transactionStatusFilter');
    if (transactionStatusFilter) {
        transactionStatusFilter.addEventListener('change', () => {
            transactionsPage = 0;
            loadTransactions();
        });
    }
    
    const transactionTypeFilter = document.getElementById('transactionTypeFilter');
    if (transactionTypeFilter) {
        transactionTypeFilter.addEventListener('change', () => {
            transactionsPage = 0;
            loadTransactions();
        });
    }
}

// ==================== Auth Handlers ====================

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        await ADMIN_API.login(email, password);
        showDashboard();
    } catch (error) {
        showError(error.message);
    }
}

async function handleSetup(e) {
    e.preventDefault();
    
    const email = document.getElementById('setupEmail').value;
    const password = document.getElementById('setupPassword').value;
    const confirmPassword = document.getElementById('setupPasswordConfirm').value;
    const fullName = document.getElementById('setupName').value;
    
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }
    
    if (password.length < 8) {
        showError('Password must be at least 8 characters');
        return;
    }
    
    try {
        await ADMIN_API.setup(email, password, fullName);
        showDashboard();
    } catch (error) {
        showError(error.message);
    }
}

async function handlePasswordReset(e) {
    e.preventDefault();
    
    const email = document.getElementById('resetEmail').value;
    
    try {
        const result = await ADMIN_API.requestPasswordReset(email);
        showToast('Password reset link sent (check console for token)', 'success');
        
        // In dev mode, show the token
        if (result.reset_token) {
            console.log('Reset Token:', result.reset_token);
            alert(`Reset Token (dev mode): ${result.reset_token}`);
        }
    } catch (error) {
        showError(error.message);
    }
}

// ==================== Tab Switching ====================

function switchTab(tab) {
    currentTab = tab;
    
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tab);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`${tab}Tab`).classList.remove('hidden');
    
    // Load tab data
    switch (tab) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'users':
            loadUsers();
            break;
        case 'wallets':
            loadWallets();
            break;
        case 'tournaments':
            loadTournaments();
            break;
        case 'subscriptions':
            loadProducts();
            break;
        case 'payments':
            loadTransactions();
            break;
        case 'rewards':
            loadRewards();
            break;
        case 'maintenance':
            loadMaintenanceSettings();
            break;
    }
}

// ==================== Dashboard ====================

async function loadDashboard() {
    try {
        const stats = await ADMIN_API.getDashboardStats();
        
        // Update stats
        document.getElementById('statTotalUsers').textContent = stats.users.total;
        document.getElementById('statActiveTournaments').textContent = stats.tournaments.active;
        document.getElementById('statTotalTokens').textContent = formatNumber(
            stats.wallets.total_virtual_tokens + stats.wallets.total_reward_tokens
        );
        document.getElementById('statTotalRevenue').textContent = `PKR ${formatNumber(stats.wallets.total_spent_pkr)}`;
        
        // Load recent users
        const usersData = await ADMIN_API.getUsers({ limit: 5 });
        const recentUsersHtml = usersData.users.slice(0, 5).map(user => `
            <div class="mini-table-row">
                <span>${user.full_name || user.email}</span>
                <span class="badge ${user.is_active ? 'badge-active' : 'badge-blocked'}">
                    ${user.is_active ? 'Active' : 'Blocked'}
                </span>
            </div>
        `).join('');
        document.getElementById('recentUsers').innerHTML = recentUsersHtml || '<p>No users yet</p>';
        
        // Load recent transactions
        const txData = await ADMIN_API.getTransactions({ limit: 5 });
        const recentTxHtml = txData.transactions.slice(0, 5).map(tx => `
            <div class="mini-table-row">
                <span>${tx.type} - ${tx.token_amount || 0} tokens</span>
                <span class="badge badge-${tx.status}">${tx.status}</span>
            </div>
        `).join('');
        document.getElementById('recentTransactions').innerHTML = recentTxHtml || '<p>No transactions yet</p>';
        
    } catch (error) {
        console.error('Dashboard load error:', error);
        showToast('Failed to load dashboard', 'error');
    }
}

// ==================== Users ====================

async function loadUsers() {
    try {
        const search = document.getElementById('userSearch').value;
        const searchBy = document.getElementById('userSearchBy').value;
        const status = document.getElementById('userStatusFilter').value;
        
        const stats = await ADMIN_API.getDashboardStats();
        document.getElementById('usersActive').textContent = stats.users.active;
        document.getElementById('usersVerified').textContent = stats.users.verified;
        document.getElementById('usersBlocked').textContent = stats.users.blocked;
        document.getElementById('usersNewToday').textContent = stats.users.new_today;
        
        const data = await ADMIN_API.getUsers({
            skip: usersPage * 50,
            limit: 50,
            search,
            search_by: searchBy,
            status
        });
        
        const html = data.users.map(user => `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="user-avatar" style="width:36px;height:36px;font-size:14px;">
                            ${(user.full_name || user.email).charAt(0).toUpperCase()}
                        </div>
                        <span>${user.full_name || 'N/A'}</span>
                    </div>
                </td>
                <td>${user.player_id || 'N/A'}</td>
                <td>${user.email}</td>
                <td>
                    <span class="badge ${user.is_active ? 'badge-active' : 'badge-blocked'}">
                        ${user.is_active ? 'Active' : 'Blocked'}
                    </span>
                    ${user.whatsapp_verified ? '<span class="badge badge-verified">Verified</span>' : ''}
                </td>
                <td>${formatDate(user.created_at)}</td>
                <td>
                    <button class="action-btn view" onclick="viewUser('${user.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${user.is_active 
                        ? `<button class="action-btn block" onclick="blockUser('${user.id}')"><i class="fas fa-ban"></i></button>`
                        : `<button class="action-btn unblock" onclick="unblockUser('${user.id}')"><i class="fas fa-check"></i></button>`
                    }
                    <button class="action-btn delete-user" onclick="deleteUser('${user.id}', '${(user.full_name || user.email).replace(/'/g, "\\'")}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('usersTableBody').innerHTML = html || '<tr><td colspan="6" class="empty-state">No users found</td></tr>';
        
    } catch (error) {
        console.error('Users load error:', error);
        showToast('Failed to load users', 'error');
    }
}

async function viewUser(userId) {
    try {
        const data = await ADMIN_API.getUserDetails(userId);
        const user = data.user;
        const wallet = data.wallet;
        
        const html = `
            <div class="user-detail-header">
                <div class="user-avatar">${(user.full_name || user.email).charAt(0).toUpperCase()}</div>
                <div class="user-detail-info">
                    <h3>${user.full_name || 'N/A'}</h3>
                    <p>${user.email}</p>
                </div>
            </div>
            
            <div class="user-detail-section">
                <h4>Profile Info</h4>
                <div class="user-detail-grid">
                    <div class="user-detail-item">
                        <label>Player ID</label>
                        <span>${user.player_id || 'N/A'}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>WhatsApp</label>
                        <span>${user.whatsapp_number || 'N/A'}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>Status</label>
                        <span class="badge ${user.is_active ? 'badge-active' : 'badge-blocked'}">${user.is_active ? 'Active' : 'Blocked'}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>Verified</label>
                        <span>${user.whatsapp_verified ? 'Yes' : 'No'}</span>
                    </div>
                </div>
            </div>
            
            ${wallet ? `
            <div class="user-detail-section">
                <h4>Wallet</h4>
                <div class="user-detail-grid">
                    <div class="user-detail-item">
                        <label>Virtual Tokens</label>
                        <span>${wallet.virtual_tokens}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>Reward Tokens</label>
                        <span>${wallet.reward_tokens}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>Total Earned</label>
                        <span>${wallet.total_tokens_earned}</span>
                    </div>
                    <div class="user-detail-item">
                        <label>Total Spent PKR</label>
                        <span>PKR ${wallet.total_spent_pkr}</span>
                    </div>
                </div>
                <button class="btn-primary" style="margin-top: 16px; width: auto;" onclick="openAddTokensModal('${userId}')">
                    <i class="fas fa-plus"></i> Add Tokens
                </button>
            </div>
            ` : ''}
            
            <div class="user-detail-section">
                <h4>Recent Transactions (${data.recent_transactions.length})</h4>
                ${data.recent_transactions.length > 0 ? `
                    <div class="mini-table">
                        ${data.recent_transactions.slice(0, 5).map(tx => `
                            <div class="mini-table-row">
                                <span>${tx.type}: ${tx.token_amount} tokens</span>
                                <span class="badge badge-${tx.status}">${tx.status}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : '<p>No transactions</p>'}
            </div>
        `;
        
        document.getElementById('userModalContent').innerHTML = html;
        document.getElementById('userModal').classList.remove('hidden');
        
    } catch (error) {
        showToast('Failed to load user details', 'error');
    }
}

async function blockUser(userId) {
    if (!confirm('Are you sure you want to block this user?')) return;
    
    try {
        await ADMIN_API.blockUser(userId);
        showToast('User blocked successfully', 'success');
        loadUsers();
    } catch (error) {
        showToast('Failed to block user', 'error');
    }
}

async function unblockUser(userId) {
    try {
        await ADMIN_API.unblockUser(userId);
        showToast('User unblocked successfully', 'success');
        loadUsers();
    } catch (error) {
        showToast('Failed to unblock user', 'error');
    }
}

async function deleteUser(userId, userName) {
    if (!confirm(`Are you sure you want to permanently delete user "${userName}"?\n\nThis will also delete:\n- Their wallet\n- All registrations\n- All transactions\n\nThis action cannot be undone!`)) {
        return;
    }
    
    try {
        await ADMIN_API.deleteUser(userId);
        showToast('User deleted successfully', 'success');
        loadUsers();
    } catch (error) {
        console.error('Delete user error:', error);
        showToast('Failed to delete user', 'error');
    }
}

function closeUserModal() {
    document.getElementById('userModal').classList.add('hidden');
}

// ==================== Wallets ====================

async function loadWallets() {
    try {
        const stats = await ADMIN_API.getDashboardStats();
        document.getElementById('totalVirtualTokens').textContent = formatNumber(stats.wallets.total_virtual_tokens);
        document.getElementById('totalRewardTokens').textContent = formatNumber(stats.wallets.total_reward_tokens);
        document.getElementById('totalSpentPKR').textContent = `PKR ${formatNumber(stats.wallets.total_spent_pkr)}`;
        
        const data = await ADMIN_API.getWallets({ limit: 50 });
        
        const html = data.wallets.map(wallet => `
            <tr>
                <td>${wallet.user_name || wallet.user_email || 'Unknown'}</td>
                <td>${formatNumber(wallet.virtual_tokens)}</td>
                <td>${formatNumber(wallet.reward_tokens)}</td>
                <td>${formatNumber(wallet.total_tokens_earned)}</td>
                <td>PKR ${formatNumber(wallet.total_spent_pkr)}</td>
                <td>
                    <button class="action-btn add" onclick="openAddTokensModal('${wallet.user_id}')">
                        <i class="fas fa-plus"></i> Add
                    </button>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('walletsTableBody').innerHTML = html || '<tr><td colspan="6" class="empty-state">No wallets found</td></tr>';
        
    } catch (error) {
        console.error('Wallets load error:', error);
        showToast('Failed to load wallets', 'error');
    }
}

function openAddTokensModal(userId) {
    document.getElementById('addTokensUserId').value = userId;
    document.getElementById('addTokensForm').reset();
    document.getElementById('addTokensModal').classList.remove('hidden');
}

function closeAddTokensModal() {
    document.getElementById('addTokensModal').classList.add('hidden');
}

async function handleAddTokens(e) {
    e.preventDefault();
    
    const userId = document.getElementById('addTokensUserId').value;
    const amount = parseInt(document.getElementById('addTokensAmount').value);
    const tokenType = document.getElementById('addTokensType').value;
    const reason = document.getElementById('addTokensReason').value || 'Admin adjustment';
    
    try {
        await ADMIN_API.addTokens(userId, amount, tokenType, reason);
        showToast(`Added ${amount} ${tokenType} tokens`, 'success');
        closeAddTokensModal();
        closeUserModal();
        loadWallets();
    } catch (error) {
        showToast('Failed to add tokens', 'error');
    }
}

// ==================== Tournaments ====================

// Banner upload handling
let uploadedBannerUrl = null;

async function handleBannerUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showToast('Please upload a valid image file (JPEG, PNG, GIF, or WebP)', 'error');
        e.target.value = '';
        return;
    }
    
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
        showToast('File size must be less than 5MB', 'error');
        e.target.value = '';
        return;
    }
    
    // Show preview
    const preview = document.getElementById('bannerPreview');
    const reader = new FileReader();
    reader.onload = (event) => {
        preview.innerHTML = `<img src="${event.target.result}" alt="Banner preview">`;
    };
    reader.readAsDataURL(file);
    
    // Upload file
    try {
        showToast('Uploading banner...', 'info');
        const result = await ADMIN_API.uploadBanner(file);
        uploadedBannerUrl = result.banner_url;
        document.getElementById('tournamentBanner').value = uploadedBannerUrl;
        showToast('Banner uploaded successfully', 'success');
    } catch (error) {
        console.error('Banner upload error:', error);
        showToast('Failed to upload banner', 'error');
        preview.innerHTML = '<i class="fas fa-image"></i><span>No banner selected</span>';
        e.target.value = '';
        uploadedBannerUrl = null;
    }
}

async function loadTournaments() {
    try {
        const status = document.getElementById('tournamentStatusFilter').value;
        const game = document.getElementById('tournamentGameFilter').value;
        
        const data = await ADMIN_API.getTournaments({ status, game });
        
        const html = data.tournaments.map(t => `
            <div class="tournament-card">
                <div class="tournament-banner">
                    ${t.banner_url 
                        ? `<img src="${t.banner_url}" alt="${t.title}">`
                        : `<i class="fas fa-trophy"></i>`
                    }
                </div>
                <div class="tournament-info">
                    <span class="badge badge-${t.status}">${t.status}</span>
                    <h3>${t.title}</h3>
                    <div class="tournament-meta">
                        <span><i class="fas fa-gamepad"></i> ${t.game}</span>
                        <span><i class="fas fa-users"></i> ${t.current_participants}/${t.max_participants}</span>
                        <span><i class="fas fa-coins"></i> Entry: ${t.entry_fee}</span>
                    </div>
                    <div class="tournament-prizes">
                        <span class="prize-badge">🥇 ${t.first_place_reward}</span>
                        <span class="prize-badge">🥈 ${t.second_place_reward}</span>
                        <span class="prize-badge">🥉 ${t.third_place_reward}</span>
                        <span class="prize-badge fourth">🏅 ${t.fourth_place_reward || 0}</span>
                        <span class="prize-badge fifth">🏅 ${t.fifth_place_reward || 0}</span>
                    </div>
                    <div class="tournament-meta">
                        <span><i class="fas fa-calendar"></i> ${formatDate(t.start_date)}</span>
                    </div>
                    ${t.room_id ? `<div class="tournament-meta"><span><i class="fas fa-door-open"></i> Room: ${t.room_id}</span></div>` : ''}
                    <div class="tournament-actions">
                        <button class="action-btn edit" onclick="editTournament('${t.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        ${t.status !== 'completed' ? `
                            <button class="action-btn view" onclick="completeTournament('${t.id}')">
                                <i class="fas fa-check"></i> Complete
                            </button>
                        ` : ''}
                        <button class="action-btn delete" onclick="deleteTournament('${t.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('tournamentsGrid').innerHTML = html || '<div class="empty-state"><i class="fas fa-trophy"></i><p>No tournaments found</p></div>';
        
    } catch (error) {
        console.error('Tournaments load error:', error);
        showToast('Failed to load tournaments', 'error');
    }
}

function openTournamentModal(tournament = null) {
    const form = document.getElementById('tournamentForm');
    form.reset();
    uploadedBannerUrl = null;
    
    const preview = document.getElementById('bannerPreview');
    document.getElementById('tournamentBannerFile').value = '';
    
    if (tournament) {
        document.getElementById('tournamentModalTitle').textContent = 'Edit Tournament';
        document.getElementById('tournamentId').value = tournament.id;
        document.getElementById('tournamentTitle').value = tournament.title;
        document.getElementById('tournamentGame').value = tournament.game;
        document.getElementById('tournamentDescription').value = tournament.description || '';
        document.getElementById('tournamentEntryFee').value = tournament.entry_fee;
        document.getElementById('tournamentPrizePool').value = tournament.prize_pool;
        document.getElementById('tournament1stReward').value = tournament.first_place_reward;
        document.getElementById('tournament2ndReward').value = tournament.second_place_reward;
        document.getElementById('tournament3rdReward').value = tournament.third_place_reward;
        document.getElementById('tournament4thReward').value = tournament.fourth_place_reward || 0;
        document.getElementById('tournament5thReward').value = tournament.fifth_place_reward || 0;
        document.getElementById('tournamentMaxParticipants').value = tournament.max_participants;
        document.getElementById('tournamentMinParticipants').value = tournament.min_participants;
        document.getElementById('tournamentStatus').value = tournament.status;
        document.getElementById('tournamentBanner').value = tournament.banner_url || '';
        document.getElementById('tournamentRules').value = tournament.rules || '';
        
        // Show banner preview if URL exists
        if (tournament.banner_url) {
            preview.innerHTML = `<img src="${tournament.banner_url}" alt="Banner preview" onerror="this.parentElement.innerHTML='<span>Invalid image URL</span>'">`;
        } else {
            preview.innerHTML = '<span>Banner Preview</span>';
        }
        
        if (tournament.start_date) {
            document.getElementById('tournamentStartDate').value = tournament.start_date.slice(0, 16);
        }
        if (tournament.end_date) {
            document.getElementById('tournamentEndDate').value = tournament.end_date.slice(0, 16);
        }
        if (tournament.registration_start) {
            document.getElementById('tournamentRegStart').value = tournament.registration_start.slice(0, 16);
        }
        if (tournament.registration_end) {
            document.getElementById('tournamentRegEnd').value = tournament.registration_end.slice(0, 16);
        }
    } else {
        document.getElementById('tournamentModalTitle').textContent = 'Create Tournament';
        document.getElementById('tournamentId').value = '';
        preview.innerHTML = '<span>Banner Preview</span>';
    }
    
    document.getElementById('tournamentModal').classList.remove('hidden');
}

function closeTournamentModal() {
    document.getElementById('tournamentModal').classList.add('hidden');
}

async function editTournament(tournamentId) {
    try {
        const data = await ADMIN_API.getTournament(tournamentId);
        openTournamentModal(data.tournament);
    } catch (error) {
        showToast('Failed to load tournament', 'error');
    }
}

async function handleTournamentSubmit(e) {
    e.preventDefault();
    
    const tournamentId = document.getElementById('tournamentId').value;
    
    const data = {
        title: document.getElementById('tournamentTitle').value,
        game: document.getElementById('tournamentGame').value,
        description: document.getElementById('tournamentDescription').value || null,
        entry_fee: parseInt(document.getElementById('tournamentEntryFee').value) || 0,
        prize_pool: parseInt(document.getElementById('tournamentPrizePool').value) || 0,
        first_place_reward: parseInt(document.getElementById('tournament1stReward').value) || 0,
        second_place_reward: parseInt(document.getElementById('tournament2ndReward').value) || 0,
        third_place_reward: parseInt(document.getElementById('tournament3rdReward').value) || 0,
        fourth_place_reward: parseInt(document.getElementById('tournament4thReward').value) || 0,
        fifth_place_reward: parseInt(document.getElementById('tournament5thReward').value) || 0,
        max_participants: parseInt(document.getElementById('tournamentMaxParticipants').value) || 100,
        min_participants: parseInt(document.getElementById('tournamentMinParticipants').value) || 2,
        status: document.getElementById('tournamentStatus').value,
        banner_url: document.getElementById('tournamentBanner').value || null,
        rules: document.getElementById('tournamentRules').value || null,
        start_date: document.getElementById('tournamentStartDate').value || null,
        end_date: document.getElementById('tournamentEndDate').value || null,
        registration_start: document.getElementById('tournamentRegStart').value || null,
        registration_end: document.getElementById('tournamentRegEnd').value || null
    };
    
    try {
        if (tournamentId) {
            await ADMIN_API.updateTournament(tournamentId, data);
            showToast('Tournament updated successfully', 'success');
        } else {
            await ADMIN_API.createTournament(data);
            showToast('Tournament created successfully', 'success');
        }
        
        closeTournamentModal();
        loadTournaments();
    } catch (error) {
        showToast('Failed to save tournament', 'error');
    }
}

async function deleteTournament(tournamentId) {
    if (!confirm('Are you sure you want to delete this tournament?')) return;
    
    try {
        await ADMIN_API.deleteTournament(tournamentId);
        showToast('Tournament deleted', 'success');
        loadTournaments();
    } catch (error) {
        showToast('Failed to delete tournament', 'error');
    }
}

async function completeTournament(tournamentId) {
    if (!confirm('Mark this tournament as completed?')) return;
    
    try {
        await ADMIN_API.completeTournament(tournamentId);
        showToast('Tournament completed', 'success');
        loadTournaments();
    } catch (error) {
        showToast('Failed to complete tournament', 'error');
    }
}

// ==================== Transactions ====================

async function loadTransactions() {
    try {
        const txStats = await ADMIN_API.getTransactionStats();
        document.getElementById('completedTransactions').textContent = txStats.by_status.completed || 0;
        document.getElementById('pendingTransactions').textContent = txStats.by_status.pending || 0;
        document.getElementById('failedTransactions').textContent = txStats.by_status.failed || 0;
        document.getElementById('totalRevenuePKR').textContent = `PKR ${formatNumber(txStats.total_revenue_pkr)}`;
        
        const status = document.getElementById('transactionStatusFilter').value;
        const type = document.getElementById('transactionTypeFilter').value;
        
        const data = await ADMIN_API.getTransactions({
            skip: transactionsPage * 50,
            limit: 50,
            status,
            type
        });
        
        const html = data.transactions.map(tx => `
            <tr>
                <td><code>${tx.id.slice(0, 8)}...</code></td>
                <td>${tx.user_id ? tx.user_id.slice(0, 8) + '...' : 'N/A'}</td>
                <td>${tx.type}</td>
                <td>${tx.token_amount || 0} ${tx.token_type || ''} tokens</td>
                <td><span class="badge badge-${tx.status}">${tx.status}</span></td>
                <td>${formatDate(tx.created_at)}</td>
            </tr>
        `).join('');
        
        document.getElementById('transactionsTableBody').innerHTML = html || '<tr><td colspan="6" class="empty-state">No transactions found</td></tr>';
        
    } catch (error) {
        console.error('Transactions load error:', error);
        showToast('Failed to load transactions', 'error');
    }
}

// ==================== Rewards ====================

async function loadRewards() {
    try {
        const stats = await ADMIN_API.getRewardsStats();
        document.getElementById('totalDistributed').textContent = formatNumber(stats.total_distributed);
        document.getElementById('currentRewardBalance').textContent = formatNumber(stats.current_reward_balance);
        
        const leaderboard = await ADMIN_API.getLeaderboard();
        
        const html = leaderboard.leaderboard.map((entry, index) => `
            <tr>
                <td>
                    ${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                </td>
                <td>${entry.user_name || 'Unknown'}</td>
                <td>${entry.player_id || 'N/A'}</td>
                <td>${formatNumber(entry.total_earned)}</td>
                <td>${formatNumber(entry.current_reward_balance)}</td>
            </tr>
        `).join('');
        
        document.getElementById('leaderboardTableBody').innerHTML = html || '<tr><td colspan="5" class="empty-state">No data yet</td></tr>';
        
    } catch (error) {
        console.error('Rewards load error:', error);
        showToast('Failed to load rewards', 'error');
    }
}

// ==================== Utilities ====================

function formatNumber(num) {
    return new Intl.NumberFormat().format(num || 0);
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showError(message) {
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    setTimeout(() => errorEl.classList.add('hidden'), 5000);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Make functions global
window.viewUser = viewUser;
window.blockUser = blockUser;
window.unblockUser = unblockUser;
window.closeUserModal = closeUserModal;
window.openAddTokensModal = openAddTokensModal;
window.closeAddTokensModal = closeAddTokensModal;
window.openTournamentModal = openTournamentModal;
window.closeTournamentModal = closeTournamentModal;
window.editTournament = editTournament;
window.deleteTournament = deleteTournament;
window.completeTournament = completeTournament;
window.deleteUser = deleteUser;
window.saveMaintenanceSettings = saveMaintenanceSettings;
window.closeProductModal = closeProductModal;
window.goToProductStep = goToProductStep;
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.toggleProductStatus = toggleProductStatus;

// ==================== Products (Subscriptions & Tokens) ====================

let selectedProductType = null;
let selectedCategory = null;
let editingProductId = null;
let uploadedProductBannerUrl = null;

const CATEGORY_LABELS = {
    'pubg_royal_pass': 'PUBG Royal Pass',
    'pubg_royal_pass_elite': 'Royal Pass Elite',
    'freefire_booyah_pass': 'Free Fire Booyah Pass',
    'freefire_booyah_pass_pro': 'Booyah Pass Pro',
    'pubg_uc': 'PUBG UC',
    'freefire_diamond': 'Free Fire Diamond'
};

const VALIDITY_LABELS = {
    'current_season': 'Current Season',
    'current_event': 'Current Event',
    'lifetime': 'Lifetime'
};

async function loadProducts() {
    try {
        const productType = document.getElementById('productTypeFilter').value;
        const status = document.getElementById('productStatusFilter').value;
        
        const data = await ADMIN_API.getProducts({ product_type: productType, status });
        
        const html = data.products.map(p => `
            <div class="product-card ${p.is_active === 'inactive' ? 'status-inactive' : ''}">
                <div class="product-banner">
                    ${p.banner_url 
                        ? `<img src="${p.banner_url}" alt="${p.name}">`
                        : `<i class="fas ${p.product_type === 'subscription' ? 'fa-crown' : 'fa-coins'}"></i>`
                    }
                    <span class="product-type-badge ${p.product_type}">${p.product_type === 'subscription' ? 'Subscription' : 'Game Token'}</span>
                </div>
                <div class="product-info">
                    <h3>${p.name}</h3>
                    <div class="product-meta">
                        <span><i class="fas fa-tag"></i> ${CATEGORY_LABELS[p.category] || p.category}</span>
                        <span><i class="fas fa-clock"></i> ${VALIDITY_LABELS[p.validity] || p.validity}</span>
                    </div>
                    ${p.product_type === 'game_token' && p.token_amount ? `
                        <div class="product-meta">
                            <span><i class="fas fa-gem"></i> ${p.token_amount} ${p.category === 'pubg_uc' ? 'UC' : 'Diamonds'}</span>
                        </div>
                    ` : ''}
                    <div class="product-price">
                        <i class="fas fa-coins"></i>
                        <span>${p.token_price}</span>
                        <small>tokens</small>
                    </div>
                    <div class="product-actions">
                        <button class="action-btn edit" onclick="editProduct('${p.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="action-btn ${p.is_active === 'active' ? 'view' : 'edit'}" onclick="toggleProductStatus('${p.id}', '${p.is_active}')">
                            <i class="fas ${p.is_active === 'active' ? 'fa-eye-slash' : 'fa-eye'}"></i>
                        </button>
                        <button class="action-btn delete" onclick="deleteProduct('${p.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('productsGrid').innerHTML = html || '<div class="empty-state"><i class="fas fa-gem"></i><p>No products found. Click "Add Product" to create one.</p></div>';
        
    } catch (error) {
        console.error('Products load error:', error);
        showToast('Failed to load products', 'error');
    }
}

function openProductModal(product = null) {
    editingProductId = product ? product.id : null;
    selectedProductType = product ? product.product_type : null;
    selectedCategory = product ? product.category : null;
    uploadedProductBannerUrl = product ? product.banner_url : null;
    
    document.getElementById('productModalTitle').textContent = product ? 'Edit Product' : 'Add Product';
    
    // Reset all steps
    document.getElementById('productTypeStep').classList.remove('hidden');
    document.getElementById('productCategoryStep').classList.add('hidden');
    document.getElementById('productDetailsStep').classList.add('hidden');
    
    // Reset selections
    document.querySelectorAll('.product-type-card').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.category-card').forEach(c => c.classList.remove('selected'));
    
    // Reset form
    document.getElementById('productForm').reset();
    document.getElementById('productBannerPreview').innerHTML = '';
    
    if (product) {
        // Go directly to details step for editing
        selectedProductType = product.product_type;
        selectedCategory = product.category;
        goToProductStep(3);
        
        // Fill in details
        document.getElementById('productId').value = product.id;
        document.getElementById('selectedProductType').value = product.product_type;
        document.getElementById('selectedCategory').value = product.category;
        document.getElementById('productName').value = product.name;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productTokenPrice').value = product.token_price;
        document.getElementById('productValidity').value = product.validity;
        
        if (product.product_type === 'game_token') {
            document.getElementById('tokenAmountGroup').classList.remove('hidden');
            document.getElementById('productTokenAmount').value = product.token_amount || '';
            updateTokenAmountLabel(product.category);
        }
        
        if (product.banner_url) {
            document.getElementById('productBannerPreview').innerHTML = `<img src="${product.banner_url}" alt="Preview">`;
        }
    }
    
    document.getElementById('productModal').classList.remove('hidden');
}

function closeProductModal() {
    document.getElementById('productModal').classList.add('hidden');
    editingProductId = null;
    selectedProductType = null;
    selectedCategory = null;
    uploadedProductBannerUrl = null;
}

function goToProductStep(step) {
    document.getElementById('productTypeStep').classList.add('hidden');
    document.getElementById('productCategoryStep').classList.add('hidden');
    document.getElementById('productDetailsStep').classList.add('hidden');
    
    if (step === 1) {
        document.getElementById('productTypeStep').classList.remove('hidden');
    } else if (step === 2) {
        document.getElementById('productCategoryStep').classList.remove('hidden');
        
        // Show correct category cards
        if (selectedProductType === 'subscription') {
            document.getElementById('subscriptionCategories').classList.remove('hidden');
            document.getElementById('gameTokenCategories').classList.add('hidden');
        } else {
            document.getElementById('subscriptionCategories').classList.add('hidden');
            document.getElementById('gameTokenCategories').classList.remove('hidden');
        }
    } else if (step === 3) {
        document.getElementById('productDetailsStep').classList.remove('hidden');
        document.getElementById('selectedProductType').value = selectedProductType;
        document.getElementById('selectedCategory').value = selectedCategory;
        
        // Update labels based on type
        if (selectedProductType === 'subscription') {
            document.getElementById('tokenPriceGroup').querySelector('label').textContent = 'Subscribe for (Tokens) *';
            document.getElementById('tokenAmountGroup').classList.add('hidden');
            // Remove lifetime option for subscriptions
            const validitySelect = document.getElementById('productValidity');
            const lifetimeOption = validitySelect.querySelector('option[value="lifetime"]');
            if (lifetimeOption) lifetimeOption.style.display = 'none';
        } else {
            document.getElementById('tokenPriceGroup').querySelector('label').textContent = 'Price (Tokens) *';
            document.getElementById('tokenAmountGroup').classList.remove('hidden');
            updateTokenAmountLabel(selectedCategory);
            // Show all validity options for game tokens
            const validitySelect = document.getElementById('productValidity');
            const lifetimeOption = validitySelect.querySelector('option[value="lifetime"]');
            if (lifetimeOption) lifetimeOption.style.display = '';
        }
    }
}

function updateTokenAmountLabel(category) {
    const label = document.getElementById('tokenAmountLabel');
    if (category === 'pubg_uc') {
        label.textContent = 'Amount of UC *';
    } else {
        label.textContent = 'Amount of Diamonds *';
    }
}

async function editProduct(productId) {
    try {
        const data = await ADMIN_API.getProduct(productId);
        openProductModal(data.product);
    } catch (error) {
        console.error('Failed to load product:', error);
        showToast('Failed to load product', 'error');
    }
}

async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        await ADMIN_API.deleteProduct(productId);
        showToast('Product deleted successfully', 'success');
        loadProducts();
    } catch (error) {
        console.error('Failed to delete product:', error);
        showToast('Failed to delete product', 'error');
    }
}

async function toggleProductStatus(productId, currentStatus) {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    
    try {
        await ADMIN_API.updateProduct(productId, { is_active: newStatus });
        showToast(`Product ${newStatus === 'active' ? 'activated' : 'deactivated'}`, 'success');
        loadProducts();
    } catch (error) {
        console.error('Failed to update product status:', error);
        showToast('Failed to update product status', 'error');
    }
}

async function saveProduct(e) {
    e.preventDefault();
    
    const productData = {
        product_type: document.getElementById('selectedProductType').value,
        category: document.getElementById('selectedCategory').value,
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        token_price: parseInt(document.getElementById('productTokenPrice').value),
        validity: document.getElementById('productValidity').value,
        banner_url: uploadedProductBannerUrl
    };
    
    if (productData.product_type === 'game_token') {
        productData.token_amount = parseInt(document.getElementById('productTokenAmount').value);
    }
    
    try {
        if (editingProductId) {
            await ADMIN_API.updateProduct(editingProductId, productData);
            showToast('Product updated successfully', 'success');
        } else {
            await ADMIN_API.createProduct(productData);
            showToast('Product created successfully', 'success');
        }
        
        closeProductModal();
        loadProducts();
    } catch (error) {
        console.error('Failed to save product:', error);
        showToast('Failed to save product', 'error');
    }
}

// Setup product event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Product type selection
    document.querySelectorAll('.product-type-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.product-type-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedProductType = card.dataset.type;
            goToProductStep(2);
        });
    });
    
    // Category selection
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.category-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedCategory = card.dataset.category;
            goToProductStep(3);
        });
    });
    
    // Add Product button
    const addProductBtn = document.getElementById('addProductBtn');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', () => openProductModal());
    }
    
    // Product form submit
    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', saveProduct);
    }
    
    // Product filters
    const productTypeFilter = document.getElementById('productTypeFilter');
    const productStatusFilter = document.getElementById('productStatusFilter');
    if (productTypeFilter) {
        productTypeFilter.addEventListener('change', loadProducts);
    }
    if (productStatusFilter) {
        productStatusFilter.addEventListener('change', loadProducts);
    }
    
    // Product banner upload
    const productBannerFile = document.getElementById('productBannerFile');
    if (productBannerFile) {
        productBannerFile.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${ADMIN_API.BASE_URL}/api/admin/tournaments/upload-banner`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${ADMIN_API.token}`
                    },
                    body: formData
                });
                
                if (!response.ok) throw new Error('Upload failed');
                
                const result = await response.json();
                uploadedProductBannerUrl = result.banner_url;
                document.getElementById('productBannerPreview').innerHTML = `<img src="${result.banner_url}" alt="Preview">`;
                showToast('Image uploaded successfully', 'success');
            } catch (error) {
                console.error('Upload error:', error);
                showToast('Failed to upload image', 'error');
            }
        });
    }
});

// ==================== Maintenance Mode ====================

async function loadMaintenanceSettings() {
    try {
        const settings = await ADMIN_API.getMaintenanceSettings();
        
        document.getElementById('maintenanceEnabled').checked = settings.enabled;
        document.getElementById('maintenanceTitle').value = settings.title || 'Under Maintenance';
        document.getElementById('maintenanceMessage').value = settings.message || "We're performing scheduled maintenance. We'll be back soon!";
        
        if (settings.end_time) {
            // Convert ISO string to datetime-local format
            const date = new Date(settings.end_time);
            const localDateTime = date.toISOString().slice(0, 16);
            document.getElementById('maintenanceEndTime').value = localDateTime;
        } else {
            document.getElementById('maintenanceEndTime').value = '';
        }
        
        updateMaintenanceUI(settings.enabled);
        updatePreview();
        
    } catch (error) {
        console.error('Failed to load maintenance settings:', error);
        showToast('Failed to load maintenance settings', 'error');
    }
}

function updateMaintenanceUI(enabled) {
    const statusText = document.getElementById('maintenanceStatusText');
    if (enabled) {
        statusText.textContent = 'Site is Under Maintenance';
        statusText.style.color = '#f59e0b';
    } else {
        statusText.textContent = 'Site is Online';
        statusText.style.color = '#10b981';
    }
}

function updatePreview() {
    const title = document.getElementById('maintenanceTitle').value;
    const message = document.getElementById('maintenanceMessage').value;
    const endTime = document.getElementById('maintenanceEndTime').value;
    
    document.getElementById('previewTitle').textContent = title || 'Under Maintenance';
    document.getElementById('previewMessage').textContent = message || "We're performing scheduled maintenance. We'll be back soon!";
    
    if (endTime) {
        const now = new Date();
        const end = new Date(endTime);
        const diff = end - now;
        
        if (diff > 0) {
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            document.getElementById('previewCountdown').innerHTML = 
                `<span>${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}</span>`;
        } else {
            document.getElementById('previewCountdown').innerHTML = '<span>00:00:00</span>';
        }
    } else {
        document.getElementById('previewCountdown').innerHTML = '<span>--:--:--</span>';
    }
}

async function saveMaintenanceSettings() {
    const enabled = document.getElementById('maintenanceEnabled').checked;
    const title = document.getElementById('maintenanceTitle').value;
    const message = document.getElementById('maintenanceMessage').value;
    const endTimeValue = document.getElementById('maintenanceEndTime').value;
    
    const settings = {
        enabled,
        title,
        message,
        end_time: endTimeValue ? new Date(endTimeValue).toISOString() : null
    };
    
    try {
        await ADMIN_API.updateMaintenanceSettings(settings);
        showToast(`Maintenance mode ${enabled ? 'enabled' : 'disabled'}`, 'success');
        updateMaintenanceUI(enabled);
    } catch (error) {
        console.error('Failed to save maintenance settings:', error);
        showToast('Failed to save maintenance settings', 'error');
    }
}

// Setup maintenance event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Only run if on admin page with maintenance elements
    const maintenanceEnabled = document.getElementById('maintenanceEnabled');
    const maintenanceTitle = document.getElementById('maintenanceTitle');
    const maintenanceMessage = document.getElementById('maintenanceMessage');
    const maintenanceEndTime = document.getElementById('maintenanceEndTime');
    
    if (maintenanceEnabled) {
        maintenanceEnabled.addEventListener('change', () => {
            updateMaintenanceUI(maintenanceEnabled.checked);
        });
    }
    
    if (maintenanceTitle) {
        maintenanceTitle.addEventListener('input', updatePreview);
    }
    if (maintenanceMessage) {
        maintenanceMessage.addEventListener('input', updatePreview);
    }
    if (maintenanceEndTime) {
        maintenanceEndTime.addEventListener('change', updatePreview);
    }
});
