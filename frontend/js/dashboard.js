/**
 * GAN Dashboard Page Handler
 */

let currentPage = 1;
let currentGame = '';
let hasMore = false;

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize auth
    const user = await Auth.init();
    if (!user) return;
    
    // Check profile completion
    if (!user.profile_completed) {
        window.location.href = 'profile.html';
        return;
    }
    
    // Load tournaments
    await loadTournaments();
    
    // Load my registrations
    await loadMyRegistrations();
    
    // Setup event handlers
    setupEventHandlers();
});

function setupEventHandlers() {
    // Game filters
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter tournaments
            currentGame = btn.dataset.game;
            currentPage = 1;
            loadTournaments();
        });
    });
    
    // Load more
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            currentPage++;
            loadTournaments(true);
        });
    }
}

async function loadTournaments(append = false) {
    const grid = document.getElementById('tournamentsGrid');
    const emptyState = document.getElementById('emptyState');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    
    if (!append) {
        grid.innerHTML = `
            <div class="loading-placeholder">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading tournaments...</p>
            </div>
        `;
    }
    
    try {
        const result = await API.getTournaments(currentPage, 12, currentGame || null);
        
        if (!append) {
            grid.innerHTML = '';
        }
        
        if (result.tournaments.length === 0 && !append) {
            emptyState.classList.remove('hidden');
            loadMoreContainer.classList.add('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        
        // Render tournament cards
        result.tournaments.forEach(tournament => {
            grid.appendChild(createTournamentCard(tournament));
        });
        
        // Show/hide load more
        hasMore = (currentPage * 12) < result.total;
        loadMoreContainer.classList.toggle('hidden', !hasMore);
        
    } catch (error) {
        console.error('Error loading tournaments:', error);
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Failed to load tournaments</h3>
                <p>Please try again later</p>
            </div>
        `;
    }
}

function createTournamentCard(tournament) {
    const card = document.createElement('div');
    card.className = 'tournament-card';
    card.onclick = () => {
        window.location.href = `tournament.html?id=${tournament.id}`;
    };
    
    const gameInfo = CONFIG.games[tournament.game] || { name: tournament.game, icon: 'fa-gamepad' };
    const statusInfo = CONFIG.tournamentStatus[tournament.status] || { label: tournament.status, class: '' };
    
    card.innerHTML = `
        <div class="card-banner">
            ${tournament.banner_url 
                ? `<img src="${tournament.banner_url}" alt="${tournament.title}">`
                : ''}
            <span class="game-tag">
                <i class="fas ${gameInfo.icon}"></i> ${gameInfo.name}
            </span>
            <span class="status-tag ${statusInfo.class}">${statusInfo.label}</span>
        </div>
        <div class="card-content">
            <h3>${tournament.title}</h3>
            <div class="card-meta">
                <span><i class="fas fa-calendar"></i> ${Utils.formatDate(tournament.start_date)}</span>
                <span><i class="fas fa-users"></i> ${tournament.current_participants}/${tournament.max_participants}</span>
            </div>
            <div class="card-footer">
                <div class="entry-fee">
                    Entry: <strong>${tournament.entry_fee}</strong> Tokens
                </div>
                <div class="prize-amount">
                    <i class="fas fa-trophy"></i> ${Utils.formatNumber(tournament.prize_pool)}
                </div>
            </div>
        </div>
    `;
    
    return card;
}

async function loadMyRegistrations() {
    const container = document.getElementById('registrationsList');
    
    try {
        const registrations = await API.getMyRegistrations();
        
        if (registrations.length === 0) {
            container.innerHTML = `
                <p style="color: var(--text-muted); text-align: center; padding: 20px;">
                    You haven't registered for any tournaments yet.
                </p>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        registrations.slice(0, 5).forEach(reg => {
            const item = document.createElement('div');
            item.className = 'tournament-card';
            item.style.marginBottom = '12px';
            item.onclick = () => {
                window.location.href = `tournament.html?id=${reg.tournament_id}`;
            };
            
            const tournament = reg.tournament;
            const gameInfo = CONFIG.games[tournament.game] || { name: tournament.game, icon: 'fa-gamepad' };
            
            item.innerHTML = `
                <div class="card-content" style="padding: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin-bottom: 8px;">${tournament.title}</h3>
                            <div class="card-meta">
                                <span><i class="fas ${gameInfo.icon}"></i> ${gameInfo.name}</span>
                                <span><i class="fas fa-calendar"></i> ${Utils.formatDate(tournament.start_date)}</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span class="status-badge ${reg.status === 'confirmed' ? 'open' : ''}" 
                                  style="display: inline-block; padding: 6px 12px; border-radius: 6px; 
                                         background: ${reg.status === 'confirmed' ? 'rgba(0,184,148,0.2)' : 'var(--bg-input)'};
                                         color: ${reg.status === 'confirmed' ? 'var(--success)' : 'var(--text-secondary)'};">
                                ${reg.status.toUpperCase()}
                            </span>
                            ${reg.position ? `<p style="margin-top: 8px; color: var(--warning);">
                                <i class="fas fa-medal"></i> Position #${reg.position}
                            </p>` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(item);
        });
        
    } catch (error) {
        console.error('Error loading registrations:', error);
    }
}
