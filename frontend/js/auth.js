/**
 * Auth Module - Handles login, registration, and 2FA verification
 */
const Auth = {
  // State
  currentUserId: null,
  currentEmail: null,
  timerInterval: null,
  codeExpiresAt: null,
  googleClientId: null,
  
  // Initialize
  init() {
    this.bindEvents();
    this.checkAuth();
    this.initGoogleSignIn();
  },
  
  // Initialize Google Sign-In
  async initGoogleSignIn() {
    try {
      // Get Google client ID from server
      const response = await fetch(`${API.BASE_URL}/api/auth/google/config`);
      const result = await response.json();
      
      if (result.data?.configured && result.data?.client_id) {
        this.googleClientId = result.data.client_id;
        
        // Update the Google Sign-In button configuration
        const onloadDiv = document.getElementById('g_id_onload');
        if (onloadDiv) {
          onloadDiv.setAttribute('data-client_id', this.googleClientId);
          
          // Reinitialize Google Sign-In if library is loaded
          if (window.google?.accounts?.id) {
            window.google.accounts.id.initialize({
              client_id: this.googleClientId,
              callback: window.handleGoogleSignIn
            });
            window.google.accounts.id.renderButton(
              document.querySelector('.g_id_signin'),
              { theme: 'filled_black', size: 'large', width: 320, text: 'signin_with' }
            );
          }
        }
        
        console.log('Google Sign-In configured');
      } else {
        // Hide Google Sign-In container and show fallback disabled message
        const container = document.getElementById('googleSignInContainer');
        if (container) {
          container.innerHTML = '<p class="oauth-disabled">Google Sign-In not configured</p>';
        }
        console.log('Google Sign-In not configured on server');
      }
    } catch (error) {
      console.log('Google OAuth not available:', error.message);
    }
  },
  
  // Check if already authenticated
  checkAuth() {
    if (API.isAuthenticated()) {
      window.location.href = 'app.html';
    }
  },
  
  // Bind event listeners
  bindEvents() {
    // Tab switching - using IDs tabLogin and tabRegister
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');
    
    if (tabLogin) {
      tabLogin.addEventListener('click', () => this.switchTab('login'));
    }
    if (tabRegister) {
      tabRegister.addEventListener('click', () => this.switchTab('register'));
    }
    
    // Quick links
    document.getElementById('goRegister')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchTab('register');
    });
    document.getElementById('goLogin')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchTab('login');
    });
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }
    
    // Verification form
    const verifyForm = document.getElementById('verifyForm');
    if (verifyForm) {
      verifyForm.addEventListener('submit', (e) => this.handleVerify(e));
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => this.handleRegister(e));
    }
    
    // Resend code - HTML uses id="resendCode"
    const resendBtn = document.getElementById('resendCode');
    if (resendBtn) {
      resendBtn.addEventListener('click', () => this.handleResendCode());
    }
    
    // Back to login - HTML uses id="backToLogin"
    const backToLoginBtn = document.getElementById('backToLogin');
    if (backToLoginBtn) {
      backToLoginBtn.addEventListener('click', () => this.showLoginForm());
    }
  },
  
  // Switch tabs
  switchTab(tab) {
    // Update tab buttons
    document.getElementById('tabLogin')?.classList.toggle('active', tab === 'login');
    document.getElementById('tabRegister')?.classList.toggle('active', tab === 'register');
    
    // Hide all forms then show the correct one
    document.getElementById('loginForm')?.classList.remove('active');
    document.getElementById('registerForm')?.classList.remove('active');
    document.getElementById('verifyForm')?.classList.remove('active');
    
    document.getElementById(`${tab}Form`)?.classList.add('active');
    
    this.clearMessages();
  },
  
  // Show login form (step 1)
  showLoginForm() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    document.getElementById('verifyForm')?.classList.remove('active');
    document.getElementById('loginForm')?.classList.add('active');
    // Show tabs again
    document.getElementById('tabLogin')?.classList.remove('hidden');
    document.getElementById('tabRegister')?.classList.remove('hidden');
  },
  
  // Show verification form (step 2)
  showVerificationForm(userId, emailHint) {
    this.currentUserId = userId;
    document.getElementById('loginForm')?.classList.remove('active');
    document.getElementById('verifyForm')?.classList.add('active');
    // Hide tabs during verification
    document.getElementById('tabLogin')?.classList.add('hidden');
    document.getElementById('tabRegister')?.classList.add('hidden');
    
    // Show email hint (already masked from server)
    const emailHintEl = document.getElementById('emailHint');
    if (emailHintEl) {
      emailHintEl.textContent = emailHint || '***@***.com';
    }
    
    // Start timer (5 minutes)
    this.startTimer(5 * 60);
    
    // Focus code input - HTML uses id="verifyCode"
    document.getElementById('verifyCode')?.focus();
  },
  
  // Mask email for display (not needed anymore, server sends hint)
  maskEmail(email) {
    const [name, domain] = email.split('@');
    const maskedName = name.charAt(0) + '*'.repeat(Math.min(name.length - 2, 5)) + name.charAt(name.length - 1);
    return `${maskedName}@${domain}`;
  },
  
  // Start countdown timer
  startTimer(seconds) {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    
    this.codeExpiresAt = Date.now() + seconds * 1000;
    
    const updateTimer = () => {
      const remaining = Math.max(0, Math.floor((this.codeExpiresAt - Date.now()) / 1000));
      const minutes = Math.floor(remaining / 60);
      const secs = remaining % 60;
      
      const timerEl = document.getElementById('codeTimer');
      if (timerEl) {
        timerEl.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
      }
      
      if (remaining <= 0) {
        clearInterval(this.timerInterval);
        this.showMessage('authMsg', 'Code expired. Please request a new one.', 'error');
      }
    };
    
    updateTimer();
    this.timerInterval = setInterval(updateTimer, 1000);
  },
  
  // Handle login form submission (step 1)
  async handleLogin(e) {
    e.preventDefault();
    
    // Clear any stale auth data from previous sessions
    API.clearToken();
    API.clearUser();
    
    // HTML uses loginUsername - we send it as username to backend
    const username = document.getElementById('loginUsername')?.value.trim();
    const password = document.getElementById('loginPassword')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    if (!username || !password) {
      this.showMessage('authMsg', 'Please fill in all fields.', 'error');
      return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';
    
    try {
      const response = await API.auth.login(username, password);
      
      // Response is wrapped in { data: {...} }
      const data = response.data || response;
      
      // If verification code was sent
      if (data.verification_required || data.user_id) {
        this.showMessage('authMsg', 'Verification code sent to your email!', 'success');
        setTimeout(() => {
          this.showVerificationForm(data.user_id, data.email_hint);
        }, 1000);
      } else if (data.access_token || data.token) {
        // Direct login without 2FA
        API.setToken(data.access_token || data.token);
        API.setUser(data.user || { user_id: data.user_id, username: data.username });
        window.location.href = 'app.html';
      }
    } catch (error) {
      const errMsg = error.error?.message || error.msg || 'Invalid credentials.';
      this.showMessage('authMsg', errMsg, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Login';
    }
  },
  
  // Handle verification form submission (step 2)
  async handleVerify(e) {
    e.preventDefault();
    
    // HTML uses id="verifyCode"
    const code = document.getElementById('verifyCode')?.value.trim();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    if (!code || code.length !== 6) {
      this.showMessage('authMsg', 'Please enter a valid 6-digit code.', 'error');
      return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Verifying...';
    
    try {
      const response = await API.auth.verifyLogin(this.currentUserId, code);
      console.log('===== VERIFY RESPONSE =====');
      console.log('Full response:', response);
      console.log('Response.data:', response.data);
      
      const data = response.data || response;
      console.log('Data object:', data);
      console.log('data.token:', data.token);
      console.log('data.user_id:', data.user_id);
      console.log('===========================');
      
      // Clear any old auth data first to prevent stale data issues
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      console.log('Cleared old auth data');
      
      // Save token and user info
      const token = data.token || data.access_token;
      if (!token) {
        console.error('❌ NO TOKEN IN RESPONSE!', { response, data });
        throw new Error('No token received from server');
      }
      
      console.log('✅ Token found, saving to localStorage');
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({ 
        user_id: data.user_id, 
        username: data.username, 
        email: data.email 
      }));
      
      // Verify it was saved
      const savedToken = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      console.log('✅ Verification after save:');
      console.log('  - Token saved:', !!savedToken, savedToken ? savedToken.substring(0, 20) + '...' : '');
      console.log('  - User saved:', savedUser);
      
      if (!savedToken) {
        throw new Error('Failed to save token to localStorage');
      }
      
      this.showMessage('authMsg', 'Login successful! Redirecting...', 'success');
      
      // Use a longer delay to ensure localStorage is synced
      setTimeout(() => {
        // Double-check before redirect
        const finalCheck = localStorage.getItem('token');
        console.log('🔍 Final check before redirect - token:', !!finalCheck);
        if (!finalCheck) {
          console.error('❌ TOKEN LOST before redirect!');
          return;
        }
        window.location.href = 'app.html';
      }, 1500);
    } catch (error) {
      console.error('❌ Verify error:', error);
      const errMsg = error.error?.message || error.msg || error.message || 'Invalid verification code.';
      this.showMessage('authMsg', errMsg, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Verify & Login';
    }
  },
  
  // Handle resend code
  async handleResendCode() {
    const btn = document.getElementById('resendCode');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = 'Sending...';
    
    try {
      await API.auth.resendCode(this.currentUserId);
      this.showMessage('authMsg', 'New code sent to your email!', 'success');
      this.startTimer(5 * 60);
      const codeInput = document.getElementById('verifyCode');
      if (codeInput) codeInput.value = '';
    } catch (error) {
      const errMsg = error.error?.message || error.msg || 'Failed to resend code.';
      this.showMessage('authMsg', errMsg, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Resend Code';
    }
  },
  
  // Handle registration
  async handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('regName')?.value.trim();
    const username = document.getElementById('regUsername')?.value.trim();
    const email = document.getElementById('regEmail')?.value.trim();
    const password = document.getElementById('regPassword')?.value;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    // Validation
    if (!username || !email || !password) {
      this.showMessage('authMsg', 'Please fill in all required fields.', 'error');
      return;
    }
    
    if (password.length < 8) {
      this.showMessage('authMsg', 'Password must be at least 8 characters.', 'error');
      return;
    }
    
    if (!/[A-Z]/.test(password)) {
      this.showMessage('authMsg', 'Password must contain at least one uppercase letter.', 'error');
      return;
    }
    
    if (!/[0-9]/.test(password)) {
      this.showMessage('authMsg', 'Password must contain at least one number.', 'error');
      return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
    
    try {
      await API.auth.register({ name, username, email, password });
      
      this.showMessage('authMsg', 'Account created! Please sign in.', 'success');
      
      // Switch to login tab
      setTimeout(() => {
        this.switchTab('login');
        const loginInput = document.getElementById('loginUsername');
        if (loginInput) loginInput.value = username;
      }, 1500);
    } catch (error) {
      const errMsg = error.error?.message || error.msg || 'Registration failed.';
      this.showMessage('authMsg', errMsg, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
    }
  },
  
  // Show message
  showMessage(elementId, message, type) {
    const el = document.getElementById(elementId);
    if (el) {
      el.textContent = message;
      el.className = `auth-msg ${type}`;
      el.classList.remove('hidden');
    }
  },
  
  // Clear all messages
  clearMessages() {
    document.querySelectorAll('.auth-msg').forEach(el => {
      el.classList.add('hidden');
      el.textContent = '';
    });
  }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => Auth.init());

// Global callback for Google Sign-In
window.handleGoogleSignIn = async function(response) {
  try {
    console.log('Google Sign-In callback received');
    
    // Show loading state
    const authMsg = document.getElementById('authMsg');
    if (authMsg) {
      authMsg.textContent = 'Signing in with Google...';
      authMsg.className = 'auth-msg';
      authMsg.classList.remove('hidden');
    }
    
    // Send credential to backend
    const result = await fetch(`${API.BASE_URL}/api/auth/google/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        credential: response.credential
      })
    });
    
    const data = await result.json();
    
    if (result.ok && data.success) {
      // Save token and user info
      localStorage.setItem('token', data.data.token);
      localStorage.setItem('user', JSON.stringify(data.data.user));
      
      const message = data.data.is_new_user 
        ? 'Welcome! Account created successfully!' 
        : 'Login successful!';
      
      if (authMsg) {
        authMsg.textContent = message + ' Redirecting...';
        authMsg.className = 'auth-msg success';
      }
      
      setTimeout(() => {
        window.location.href = 'app.html';
      }, 1000);
    } else {
      throw new Error(data.error?.message || 'Google sign-in failed');
    }
  } catch (error) {
    console.error('Google Sign-In error:', error);
    const authMsg = document.getElementById('authMsg');
    if (authMsg) {
      authMsg.textContent = error.message || 'Google sign-in failed. Please try again.';
      authMsg.className = 'auth-msg error';
      authMsg.classList.remove('hidden');
    }
  }
};
