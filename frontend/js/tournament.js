/**
 * GAN Tournament Detail Page Handler
 */

let tournamentData = null;
let userData = null;
let walletBalance = 0;

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize auth
    userData = await Auth.init();
    if (!userData) return;
    
    // Get tournament ID from URL
    const tournamentId = Utils.getUrlParam('id');
    if (!tournamentId) {
        window.location.href = 'dashboard.html';
        return;
    }
    
    // Load tournament data
    await loadTournament(tournamentId);
    
    // Setup event handlers
    setupEventHandlers();
});

async function loadTournament(tournamentId) {
    Utils.showLoading();
    
    try {
        // Load tournament and wallet in parallel
        const [tournament, wallet] = await Promise.all([
            API.getTournament(tournamentId),
            API.getBalance()
        ]);
        
        tournamentData = tournament;
        walletBalance = wallet.total_balance;
        
        // Update token balance display
        document.getElementById('tokenBalance').textContent = Utils.formatNumber(walletBalance);
        
        // Render tournament details
        renderTournament(tournament);
        
        // Load participants
        await loadParticipants(tournamentId);
        
    } catch (error) {
        console.error('Error loading tournament:', error);
        Utils.showToast('Failed to load tournament', 'error');
    } finally {
        Utils.hideLoading();
    }
}

function renderTournament(tournament) {
    // Banner
    const banner = document.getElementById('tournamentBanner');
    if (tournament.banner_url) {
        banner.style.backgroundImage = `url(${tournament.banner_url})`;
        banner.style.backgroundSize = 'cover';
        banner.style.backgroundPosition = 'center';
    }
    
    // Game badge
    const gameInfo = CONFIG.games[tournament.game] || { name: tournament.game };
    document.getElementById('gameBadge').textContent = gameInfo.name.toUpperCase();
    
    // Title and meta
    document.getElementById('tournamentTitle').textContent = tournament.title;
    document.getElementById('startDate').textContent = Utils.formatDate(tournament.start_date);
    document.getElementById('participants').textContent = `${tournament.current_participants}/${tournament.max_participants}`;
    document.getElementById('prizePool').textContent = Utils.formatNumber(tournament.prize_pool);
    
    // Status badge
    const statusInfo = CONFIG.tournamentStatus[tournament.status] || { label: tournament.status };
    const statusBadge = document.getElementById('statusBadge');
    statusBadge.textContent = statusInfo.label;
    statusBadge.className = `status-badge ${statusInfo.class || ''}`;
    
    // Info items
    document.getElementById('entryFee').textContent = `${tournament.entry_fee} Tokens`;
    document.getElementById('slotsInfo').textContent = `${tournament.slots_available}/${tournament.max_participants}`;
    document.getElementById('regEndDate').textContent = tournament.registration_end 
        ? Utils.formatDate(tournament.registration_end)
        : 'TBD';
    
    // Prize distribution
    document.getElementById('prize1').textContent = `${Utils.formatNumber(tournament.first_place_reward)} Tokens`;
    document.getElementById('prize2').textContent = `${Utils.formatNumber(tournament.second_place_reward)} Tokens`;
    document.getElementById('prize3').textContent = `${Utils.formatNumber(tournament.third_place_reward)} Tokens`;
    
    // Description and rules
    document.getElementById('description').textContent = tournament.description || 'No description available.';
    
    const rulesContainer = document.getElementById('rules');
    if (tournament.rules) {
        const rules = tournament.rules.split('\n').filter(r => r.trim());
        rulesContainer.innerHTML = '<ul>' + rules.map(r => `<li>${r}</li>`).join('') + '</ul>';
    } else {
        rulesContainer.textContent = 'No rules specified.';
    }
    
    // Registration button
    const registerBtn = document.getElementById('registerBtn');
    const registeredBadge = document.getElementById('registeredBadge');
    
    if (tournament.user_registered) {
        registerBtn.classList.add('hidden');
        registeredBadge.classList.remove('hidden');
        
        // Show room details if available
        if (tournament.room_id) {
            const roomCard = document.getElementById('roomCard');
            roomCard.classList.remove('hidden');
            document.getElementById('roomId').textContent = tournament.room_id;
            document.getElementById('roomPassword').textContent = tournament.room_password || '-';
        }
    } else if (tournament.is_registration_open) {
        registerBtn.disabled = false;
        registerBtn.onclick = showRegisterModal;
    } else {
        registerBtn.disabled = true;
        registerBtn.textContent = 'Registration Closed';
    }
}

async function loadParticipants(tournamentId) {
    try {
        const participants = await API.getParticipants(tournamentId);
        
        document.getElementById('participantCount').textContent = participants.length;
        
        const grid = document.getElementById('participantsGrid');
        grid.innerHTML = '';
        
        if (participants.length === 0) {
            grid.innerHTML = '<p style="color: var(--text-muted);">No participants yet. Be the first to register!</p>';
            return;
        }
        
        participants.forEach(p => {
            const card = document.createElement('div');
            card.className = 'participant-card';
            card.innerHTML = `
                <img src="${p.avatar_url || 'https://via.placeholder.com/40?text=U'}" alt="${p.full_name}">
                <div class="participant-info">
                    <h4>${p.full_name || 'Player'}</h4>
                    <span>${p.player_id || '-'}</span>
                </div>
                ${p.checked_in ? '<i class="fas fa-check-circle" style="color: var(--success);"></i>' : ''}
            `;
            grid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading participants:', error);
    }
}

function setupEventHandlers() {
    // Copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.copy;
            const text = document.getElementById(targetId).textContent;
            Utils.copyToClipboard(text);
        });
    });
    
    // Register modal
    document.getElementById('closeModal').addEventListener('click', hideRegisterModal);
    document.getElementById('cancelRegister').addEventListener('click', hideRegisterModal);
    document.getElementById('confirmRegister').addEventListener('click', confirmRegistration);
    
    // Insufficient balance modal
    document.getElementById('closeInsufficientModal').addEventListener('click', () => {
        document.getElementById('insufficientModal').classList.add('hidden');
    });
    document.getElementById('cancelBuy').addEventListener('click', () => {
        document.getElementById('insufficientModal').classList.add('hidden');
    });
}

function showRegisterModal() {
    const modal = document.getElementById('registerModal');
    
    // Check balance first
    if (walletBalance < tournamentData.entry_fee) {
        showInsufficientModal();
        return;
    }
    
    // Fill modal data
    document.getElementById('confirmTournament').textContent = tournamentData.title;
    document.getElementById('confirmFee').textContent = `${tournamentData.entry_fee} Tokens`;
    document.getElementById('confirmBalance').textContent = `${walletBalance} Tokens`;
    document.getElementById('confirmPlayerId').value = userData.player_id || '';
    
    modal.classList.remove('hidden');
}

function hideRegisterModal() {
    document.getElementById('registerModal').classList.add('hidden');
}

function showInsufficientModal() {
    const modal = document.getElementById('insufficientModal');
    const needed = tournamentData.entry_fee - walletBalance;
    
    document.getElementById('requiredTokens').textContent = tournamentData.entry_fee;
    document.getElementById('currentBalance').textContent = walletBalance;
    document.getElementById('neededTokens').textContent = needed;
    
    modal.classList.remove('hidden');
}

async function confirmRegistration() {
    const playerId = document.getElementById('confirmPlayerId').value.trim();
    
    if (!playerId) {
        Utils.showToast('Please enter your player ID', 'error');
        return;
    }
    
    Utils.showLoading();
    
    try {
        await API.registerForTournament(tournamentData.id, playerId);
        
        hideRegisterModal();
        Utils.showToast('Registration successful!', 'success');
        
        // Reload tournament data
        await loadTournament(tournamentData.id);
        
        // Update wallet balance
        const wallet = await API.getBalance();
        document.getElementById('tokenBalance').textContent = Utils.formatNumber(wallet.total_balance);
        
    } catch (error) {
        console.error('Registration error:', error);
        
        if (error.message && error.message.includes('insufficient')) {
            showInsufficientModal();
        } else {
            Utils.showToast(error.message || 'Registration failed', 'error');
        }
    } finally {
        Utils.hideLoading();
    }
}
