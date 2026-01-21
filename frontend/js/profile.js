/**
 * GAN Profile Page Handler
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Handle OAuth callback
    Auth.handleCallback();
    
    // Check if authenticated
    if (!Auth.isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }
    
    // Load existing profile data
    await loadProfile();
    
    // Setup form handlers
    setupFormHandlers();
});

async function loadProfile() {
    try {
        Utils.showLoading();
        const user = await API.getCurrentUser();
        
        if (user) {
            // Update email display
            document.getElementById('userEmail').textContent = user.email;
            
            // Pre-fill form with existing data
            if (user.full_name) document.getElementById('fullName').value = user.full_name;
            if (user.age) document.getElementById('age').value = user.age;
            if (user.city) document.getElementById('city').value = user.city;
            if (user.country) document.getElementById('country').value = user.country;
            if (user.whatsapp_number) {
                const phone = user.whatsapp_number.replace('+92', '');
                document.getElementById('whatsappNumber').value = phone;
            }
            if (user.player_id) document.getElementById('playerId').value = user.player_id;
            if (user.preferred_game) document.getElementById('preferredGame').value = user.preferred_game;
            if (user.preferred_payment) {
                document.querySelector(`input[name="preferred_payment"][value="${user.preferred_payment}"]`).checked = true;
            }
            
            // Show verified badge if already verified
            if (user.whatsapp_verified) {
                showVerifiedState();
            }
            
            // If profile is complete, redirect to dashboard
            if (user.profile_completed) {
                // Allow editing but don't force redirect
            }
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    } finally {
        Utils.hideLoading();
    }
}

function setupFormHandlers() {
    // Send verification code
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    sendCodeBtn.addEventListener('click', sendVerificationCode);
    
    // Verify code
    const verifyCodeBtn = document.getElementById('verifyCodeBtn');
    verifyCodeBtn.addEventListener('click', verifyCode);
    
    // Resend code
    const resendCodeBtn = document.getElementById('resendCodeBtn');
    resendCodeBtn.addEventListener('click', sendVerificationCode);
    
    // Submit profile form
    const profileForm = document.getElementById('profileForm');
    profileForm.addEventListener('submit', submitProfile);
}

async function sendVerificationCode() {
    const phoneInput = document.getElementById('whatsappNumber');
    const phone = phoneInput.value.trim();
    
    if (!phone || phone.length < 10) {
        Utils.showToast('Please enter a valid phone number', 'error');
        return;
    }
    
    const fullPhone = '+92' + phone;
    
    try {
        Utils.showLoading();
        const result = await API.sendWhatsAppCode(fullPhone);
        
        // Show verification section
        document.getElementById('verificationSection').classList.remove('hidden');
        document.getElementById('sendCodeBtn').classList.add('hidden');
        
        // For development - show code prominently since WhatsApp API not configured
        if (result._dev_code) {
            Utils.showToast(`DEV MODE: Your code is ${result._dev_code}`, 'success');
            console.log('DEV: Verification code is:', result._dev_code);
            // Also fill it in automatically for easy testing
            document.getElementById('verifyCode').value = result._dev_code;
        } else {
            Utils.showToast('Verification code sent to WhatsApp!', 'success');
        }
    } catch (error) {
        Utils.showToast(error.message || 'Failed to send code', 'error');
    } finally {
        Utils.hideLoading();
    }
}

async function verifyCode() {
    const codeInput = document.getElementById('verifyCode');
    const code = codeInput.value.trim();
    
    if (!code || code.length !== 6) {
        Utils.showToast('Please enter the 6-digit code', 'error');
        return;
    }
    
    try {
        Utils.showLoading();
        const result = await API.verifyWhatsAppCode(code);
        
        if (result.success) {
            showVerifiedState();
            Utils.showToast('WhatsApp number verified!', 'success');
        }
    } catch (error) {
        Utils.showToast(error.message || 'Invalid code', 'error');
    } finally {
        Utils.hideLoading();
    }
}

function showVerifiedState() {
    document.getElementById('verificationSection').classList.add('hidden');
    document.getElementById('sendCodeBtn').classList.add('hidden');
    document.getElementById('verifiedBadge').classList.remove('hidden');
    document.getElementById('whatsappNumber').disabled = true;
}

async function submitProfile(e) {
    e.preventDefault();
    
    // Validate form
    const form = e.target;
    if (!form.checkValidity()) {
        Utils.showToast('Please fill in all required fields', 'error');
        return;
    }
    
    // Check WhatsApp verification
    const verifiedBadge = document.getElementById('verifiedBadge');
    if (verifiedBadge.classList.contains('hidden')) {
        Utils.showToast('Please verify your WhatsApp number', 'error');
        return;
    }
    
    // Collect form data
    const formData = {
        full_name: document.getElementById('fullName').value.trim(),
        age: parseInt(document.getElementById('age').value),
        city: document.getElementById('city').value.trim(),
        country: document.getElementById('country').value,
        whatsapp_number: '+92' + document.getElementById('whatsappNumber').value.trim(),
        player_id: document.getElementById('playerId').value.trim(),
        preferred_game: document.getElementById('preferredGame').value,
        preferred_payment: document.querySelector('input[name="preferred_payment"]:checked').value,
        mobile_wallet_number: document.getElementById('mobileWallet').value.trim() 
            ? '+92' + document.getElementById('mobileWallet').value.trim() 
            : null
    };
    
    try {
        Utils.showLoading();
        const result = await API.updateProfile(formData);
        
        Utils.showToast('Profile saved successfully!', 'success');
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1000);
    } catch (error) {
        Utils.showToast(error.message || 'Failed to save profile', 'error');
    } finally {
        Utils.hideLoading();
    }
}
