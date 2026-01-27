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
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Setup form
    document.getElementById('setupForm').addEventListener('submit', handleSetup);
    
    // Reset form
    document.getElementById('resetForm').addEventListener('submit', handlePasswordReset);
    
    // Forgot password link
    document.getElementById('forgotPasswordLink').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('loginForm').classList.add('hidden');
        document.getElementById('resetForm').classList.remove('hidden');
    });
    
    // Back to login
    document.getElementById('backToLogin').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('resetForm').classList.add('hidden');
        document.getElementById('loginForm').classList.remove('hidden');
    });
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        ADMIN_API.logout();
    });
    
    // Tab navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Tournament form
    document.getElementById('createTournamentBtn').addEventListener('click', () => {
        openTournamentModal();
    });
    
    document.getElementById('tournamentForm').addEventListener('submit', handleTournamentSubmit);
    
    // Add tokens form
    document.getElementById('addTokensForm').addEventListener('submit', handleAddTokens);
    
    // User search
    document.getElementById('userSearch').addEventListener('input', debounce(() => {
        usersPage = 0;
        loadUsers();
    }, 300));
    
    document.getElementById('userSearchBy').addEventListener('change', () => {
        usersPage = 0;
        loadUsers();
    });
    
    document.getElementById('userStatusFilter').addEventListener('change', () => {
        usersPage = 0;
        loadUsers();
    });
    
    // Tournament filters
    document.getElementById('tournamentStatusFilter').addEventListener('change', loadTournaments);
    document.getElementById('tournamentGameFilter').addEventListener('change', loadTournaments);
    
    // Banner upload
    document.getElementById('tournamentBannerFile').addEventListener('change', handleBannerUpload);
    document.getElementById('tournamentBanner').addEventListener('input', handleBannerUrlInput);
    
    // Transaction filters
    document.getElementById('transactionStatusFilter').addEventListener('change', () => {
        transactionsPage = 0;
        loadTransactions();
    });
    document.getElementById('transactionTypeFilter').addEventListener('change', () => {
        transactionsPage = 0;
        loadTransactions();
    });
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
        case 'payments':
            loadTransactions();
            break;
        case 'rewards':
            loadRewards();
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
        uploadedBannerUrl = result.url;
        document.getElementById('tournamentBanner').value = uploadedBannerUrl;
        showToast('Banner uploaded successfully', 'success');
    } catch (error) {
        console.error('Banner upload error:', error);
        showToast('Failed to upload banner', 'error');
        preview.innerHTML = '<span>Banner Preview</span>';
        e.target.value = '';
    }
}

function handleBannerUrlInput(e) {
    const url = e.target.value;
    const preview = document.getElementById('bannerPreview');
    
    if (url) {
        preview.innerHTML = `<img src="${url}" alt="Banner preview" onerror="this.parentElement.innerHTML='<span>Invalid image URL</span>'">`;
    } else {
        preview.innerHTML = '<span>Banner Preview</span>';
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
