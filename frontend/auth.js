/* ═══════════════════════════════════════════════
   auth.js — Login & Register logic
   ═══════════════════════════════════════════════ */

// Redirect to dashboard if already logged in
if (localStorage.getItem('career_token')) {
  window.location.href = '/dashboard';
}

function switchAuthTab(tab) {
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
  document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
  hideAuthError();
}

function showAuthError(msg) {
  const el = document.getElementById('auth-error');
  el.textContent = msg;
  el.style.display = 'block';
}

function hideAuthError() {
  document.getElementById('auth-error').style.display = 'none';
}

async function handleLogin(e) {
  e.preventDefault();
  hideAuthError();
  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Logging in...';

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');

    localStorage.setItem('career_token', data.access_token);
    localStorage.setItem('career_email', data.email);
    window.location.href = '/dashboard';
  } catch (err) {
    showAuthError(err.message);
    btn.disabled = false;
    btn.textContent = 'Login →';
  }
}

async function handleRegister(e) {
  e.preventDefault();
  hideAuthError();

  const password = document.getElementById('reg-password').value;
  const confirm  = document.getElementById('reg-confirm').value;

  if (password !== confirm) {
    showAuthError('Passwords do not match');
    return;
  }
  if (password.length < 6) {
    showAuthError('Password must be at least 6 characters');
    return;
  }

  const btn = document.getElementById('btn-register');
  btn.disabled = true;
  btn.textContent = 'Creating account...';

  const email = document.getElementById('reg-email').value.trim();
  try {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');

    localStorage.setItem('career_token', data.access_token);
    localStorage.setItem('career_email', data.email);
    window.location.href = '/dashboard';
  } catch (err) {
    showAuthError(err.message);
    btn.disabled = false;
    btn.textContent = 'Create Account →';
  }
}
