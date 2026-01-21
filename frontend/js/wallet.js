/**
 * GAN Wallet Page Handler
 */

let selectedBundle = null;
let transactionPage = 1;
let pollingInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize auth
    const user = await Auth.init();
    if (!user) return;
    
    // Load wallet data
    await loadWalletData();
    
    // Load bundles
    await loadBundles();
    
    // Load transactions
    await loadTransactions();
    
    // Setup event handlers
    setupEventHandlers();
});

async function loadWalletData() {
    try {
        const wallet = await API.getBalance();
        
        document.getElementById('totalBalance').textContent = Utils.formatNumber(wallet.total_balance);
        document.getElementById('virtualTokens').textContent = Utils.formatNumber(wallet.virtual_tokens);
        document.getElementById('rewardTokens').textContent = Utils.formatNumber(wallet.reward_tokens);
        document.getElementById('availableReward').textContent = Utils.formatNumber(wallet.reward_tokens);
        
    } catch (error) {
        console.error('Error loading wallet:', error);
    }
}

async function loadBundles() {
    const grid = document.getElementById('bundlesGrid');
    
    try {
        const result = await API.getBundles();
        
        grid.innerHTML = '';
        
        result.bundles.forEach(bundle => {
            const card = document.createElement('div');
            card.className = `bundle-card ${bundle.is_featured ? 'featured' : ''}`;
            card.onclick = () => selectBundle(bundle);
            
            card.innerHTML = `
                ${bundle.badge ? `<span class="bundle-badge">${bundle.badge}</span>` : ''}
                <div class="bundle-tokens">
                    <span class="amount">${Utils.formatNumber(bundle.tokens)}</span>
                    <span class="label">Tokens</span>
                </div>
                ${bundle.bonus_tokens > 0 ? `
                    <div class="bundle-bonus">
                        +${bundle.bonus_tokens} Bonus Tokens
                    </div>
                ` : ''}
                <div class="bundle-price">
                    <span class="price">${Utils.formatCurrency(bundle.price_pkr)}</span>
                </div>
            `;
            
            grid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading bundles:', error);
        grid.innerHTML = '<p style="color: var(--text-muted);">Failed to load bundles</p>';
    }
}

async function loadTransactions(append = false) {
    const container = document.getElementById('transactionsList');
    const loadMoreBtn = document.getElementById('loadMoreTransactions');
    
    try {
        const result = await API.getTransactions(transactionPage);
        
        if (!append) {
            container.innerHTML = '';
        }
        
        if (result.transactions.length === 0 && !append) {
            container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 20px;">No transactions yet</p>';
            return;
        }
        
        result.transactions.forEach(tx => {
            const typeInfo = CONFIG.transactionTypes[tx.type] || { 
                label: tx.type, 
                icon: 'fa-circle',
                class: ''
            };
            
            const isPositive = ['purchase', 'tournament_reward', 'transfer_in', 'refund', 'bonus'].includes(tx.type);
            
            const item = document.createElement('div');
            item.className = 'transaction-item';
            item.innerHTML = `
                <div class="transaction-icon ${typeInfo.class}">
                    <i class="fas ${typeInfo.icon}"></i>
                </div>
                <div class="transaction-details">
                    <h4>${typeInfo.label}</h4>
                    <span>${Utils.formatDate(tx.created_at)}</span>
                </div>
                <div class="transaction-amount">
                    <span class="tokens ${isPositive ? 'positive' : 'negative'}">
                        ${isPositive ? '+' : '-'}${Utils.formatNumber(tx.token_amount)}
                    </span>
                    <span class="status">${tx.status}</span>
                </div>
            `;
            
            container.appendChild(item);
        });
        
        // Show/hide load more
        loadMoreBtn.classList.toggle('hidden', !result.has_more);
        
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

function setupEventHandlers() {
    // Buy tokens button (scrolls to bundles)
    document.getElementById('buyTokensBtn').addEventListener('click', () => {
        document.getElementById('bundlesSection').scrollIntoView({ behavior: 'smooth' });
    });
    
    // Transfer button
    document.getElementById('transferBtn').addEventListener('click', () => {
        document.getElementById('transferModal').classList.remove('hidden');
    });
    
    // Payment modal handlers
    document.getElementById('closePaymentModal').addEventListener('click', closePaymentModal);
    document.getElementById('cancelPayment').addEventListener('click', closePaymentModal);
    document.getElementById('confirmPayment').addEventListener('click', initiatePayment);
    
    // Payment method selection
    document.querySelectorAll('input[name="payment_method"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.querySelectorAll('.method-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            e.target.closest('.method-option').classList.add('selected');
        });
    });
    
    // Processing modal
    document.getElementById('cancelProcessing').addEventListener('click', () => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        document.getElementById('processingModal').classList.add('hidden');
    });
    
    // Transfer modal handlers
    document.getElementById('closeTransferModal').addEventListener('click', () => {
        document.getElementById('transferModal').classList.add('hidden');
    });
    document.getElementById('cancelTransfer').addEventListener('click', () => {
        document.getElementById('transferModal').classList.add('hidden');
    });
    document.getElementById('confirmTransfer').addEventListener('click', processTransfer);
    
    // Success modal
    document.getElementById('successClose').addEventListener('click', () => {
        document.getElementById('successModal').classList.add('hidden');
        window.location.href = 'dashboard.html';
    });
    
    // Load more transactions
    document.getElementById('loadMoreBtn').addEventListener('click', () => {
        transactionPage++;
        loadTransactions(true);
    });
}

function selectBundle(bundle) {
    selectedBundle = bundle;
    
    // Update modal
    document.getElementById('bundleName').textContent = bundle.name;
    document.getElementById('bundleTokens').textContent = Utils.formatNumber(bundle.tokens);
    document.getElementById('bundleBonus').textContent = `+${bundle.bonus_tokens} Bonus`;
    document.getElementById('bundlePrice').textContent = Utils.formatCurrency(bundle.price_pkr);
    document.getElementById('payAmount').textContent = Utils.formatCurrency(bundle.price_pkr);
    
    // Show modal
    document.getElementById('paymentModal').classList.remove('hidden');
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.add('hidden');
    selectedBundle = null;
}

async function initiatePayment() {
    if (!selectedBundle) return;
    
    const mobileInput = document.getElementById('paymentMobile');
    const mobile = mobileInput.value.trim();
    
    if (!mobile || mobile.length < 10) {
        Utils.showToast('Please enter a valid mobile number', 'error');
        return;
    }
    
    const fullMobile = '+92' + mobile;
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
    
    Utils.showLoading();
    
    try {
        const result = await API.initiatePayment(selectedBundle.id, paymentMethod, fullMobile);
        
        closePaymentModal();
        
        // Show processing modal
        const processingModal = document.getElementById('processingModal');
        document.getElementById('walletName').textContent = paymentMethod === 'easypaisa' ? 'Easypaisa' : 'JazzCash';
        document.getElementById('processingTxId').textContent = result.transaction_id;
        document.getElementById('processingAmount').textContent = Utils.formatCurrency(result.amount_pkr);
        processingModal.classList.remove('hidden');
        
        // Start polling for payment status
        startPaymentPolling(result.transaction_id);
        
    } catch (error) {
        Utils.showToast(error.message || 'Payment failed', 'error');
    } finally {
        Utils.hideLoading();
    }
}

function startPaymentPolling(transactionId) {
    let attempts = 0;
    const maxAttempts = 60; // Poll for 5 minutes (every 5 seconds)
    
    pollingInterval = setInterval(async () => {
        attempts++;
        
        if (attempts >= maxAttempts) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            document.getElementById('processingModal').classList.add('hidden');
            Utils.showToast('Payment timeout. Please check your transaction history.', 'error');
            return;
        }
        
        try {
            const status = await API.checkPaymentStatus(transactionId);
            
            if (status.status === 'completed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                
                document.getElementById('processingModal').classList.add('hidden');
                
                // Show success modal
                const receipt = await API.getReceipt(transactionId);
                document.getElementById('tokensAdded').textContent = Utils.formatNumber(receipt.total_tokens);
                document.getElementById('newBalance').textContent = Utils.formatNumber(receipt.new_balance);
                document.getElementById('successModal').classList.remove('hidden');
                
                // Refresh wallet data
                await loadWalletData();
                await loadTransactions();
                
            } else if (status.status === 'failed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                
                document.getElementById('processingModal').classList.add('hidden');
                Utils.showToast('Payment failed. Please try again.', 'error');
            }
            
        } catch (error) {
            console.error('Error checking payment status:', error);
        }
    }, 5000); // Check every 5 seconds
}

async function processTransfer() {
    const recipientEmail = document.getElementById('recipientEmail').value.trim();
    const amount = parseInt(document.getElementById('transferAmount').value);
    
    if (!recipientEmail) {
        Utils.showToast('Please enter recipient email', 'error');
        return;
    }
    
    if (!amount || amount <= 0) {
        Utils.showToast('Please enter a valid amount', 'error');
        return;
    }
    
    Utils.showLoading();
    
    try {
        const result = await API.transferTokens(recipientEmail, amount);
        
        document.getElementById('transferModal').classList.add('hidden');
        Utils.showToast(`Successfully sent ${amount} tokens to ${recipientEmail}!`, 'success');
        
        // Refresh data
        await loadWalletData();
        await loadTransactions();
        
    } catch (error) {
        Utils.showToast(error.message || 'Transfer failed', 'error');
    } finally {
        Utils.hideLoading();
    }
}
