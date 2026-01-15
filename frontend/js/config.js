/**
 * Frontend Configuration
 * Modify these settings based on your environment
 */
const CONFIG = {
  // API Base URL - change this for production
  API_URL: 'http://localhost:5000',
  
  // Token storage key
  TOKEN_KEY: 'token',
  USER_KEY: 'user',
  
  // Default pagination
  DEFAULT_PAGE_SIZE: 10,
  
  // Chart settings
  CHART_COLORS: {
    primary: '#3182ce',
    success: '#38a169',
    danger: '#e53e3e',
    warning: '#ecc94b',
    secondary: '#ed8936'
  },
  
  // Message timeout (ms)
  MESSAGE_TIMEOUT: 3000,
  
  // Verification code timer (seconds)
  CODE_EXPIRY_TIME: 300, // 5 minutes
  
  // Date format options
  DATE_FORMAT: {
    short: { month: 'short', day: 'numeric' },
    medium: { month: 'short', day: 'numeric', year: 'numeric' },
    long: { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }
  }
};

// Legacy support
window.API_URL = CONFIG.API_URL + '/api';

// Freeze config to prevent accidental modifications
Object.freeze(CONFIG);

// Export for use
window.CONFIG = CONFIG;
