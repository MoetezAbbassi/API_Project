function getToken() {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
}

function setToken(token, remember = true) {
  if (remember) localStorage.setItem('token', token);
  else sessionStorage.setItem('token', token);
}

function clearToken() {
  localStorage.removeItem('token');
  sessionStorage.removeItem('token');
}

async function request(path, options = {}) {
  const cleanPath = path.replace(/^\//, '');
  const url = window.API_URL + '/' + cleanPath;
  console.log('[API]', url);
  
  const token = getToken();
  const headers = new Headers(options.headers || {});
  
  if (options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }
  
  if (token) headers.set('Authorization', `Bearer ${token}`);
  
  try {
    const res = await fetch(url, {
      method: options.method || 'GET',
      headers: headers,
      body: options.body,
    });
    
    const contentType = res.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');
    
    let data = isJson ? await res.json() : { success: false, message: await res.text() };
    
    if (!res.ok) {
      return { success: false, message: data?.message || `HTTP ${res.status}`, status: res.status };
    }
    return data;
  } catch (err) {
    return { success: false, message: `Network error: ${err.message}`, status: 0 };
  }
}

async function login(payload) {
  return request('auth/login', { method: 'POST', body: JSON.stringify(payload) });
}

async function register(payload) {
  return request('auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

window.api = { request, login, register, getToken, setToken, clearToken };
