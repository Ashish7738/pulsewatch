/* Shared helpers: token storage, auth guards and a fetch wrapper. */
const API_BASE = '/api';
const TOKEN_KEY = 'pulsewatch_token';
const EMAIL_KEY = 'pulsewatch_email';

const getToken = () => localStorage.getItem(TOKEN_KEY);

function saveSession(token, email) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

/* Protected pages: send visitors without a token to the login page. */
function requireAuth() {
  if (!getToken()) {
    window.location.replace('index.html');
    return false;
  }
  return true;
}

/* Login/register pages: skip ahead if already signed in. */
function redirectIfAuthed() {
  if (getToken()) window.location.replace('dashboard.html');
}

function logout() {
  clearSession();
  window.location.replace('index.html');
}

/* fetch wrapper: adds the JWT, parses JSON, throws Error(message) on failure. */
async function apiFetch(path, { method = 'GET', body = null, auth = true } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== null) headers['Content-Type'] = 'application/json';
  if (auth && getToken()) headers.Authorization = `Bearer ${getToken()}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== null ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error('Cannot reach the server. Check your connection and try again.');
  }

  let data = null;
  try { data = await response.json(); } catch (err) { /* non-JSON body */ }

  if (response.status === 401 && auth) {
    logout();
    throw new Error('Session expired. Please log in again.');
  }
  if (!response.ok) {
    throw new Error((data && (data.error || data.message)) || `Request failed (${response.status})`);
  }
  return data;
}

/* Theme: dark by default, toggle persisted in localStorage. */
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('pulsewatch_theme', theme);
}
function toggleTheme() {
  applyTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light');
}
