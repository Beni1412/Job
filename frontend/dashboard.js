/* ═══════════════════════════════════════════════
   dashboard.js — Dashboard logic
   ═══════════════════════════════════════════════ */

const token = localStorage.getItem('career_token');
if (!token) window.location.href = '/auth';

const email = localStorage.getItem('career_email') || '';
document.getElementById('nav-email').textContent = email;

const firstName = email.split('@')[0] || 'there';
document.getElementById('greeting-name').textContent = firstName;

function authHeaders() {
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

function logout() {
  localStorage.removeItem('career_token');
  localStorage.removeItem('career_email');
  window.location.href = '/auth';
}

async function loadDashboard() {
  try {
    // Load skills
    const skillsRes = await fetch(`${API_BASE}/api/skills`, { headers: authHeaders() });
    if (skillsRes.status === 401) { logout(); return; }
    const skills = await skillsRes.json();
    document.getElementById('stat-skills').textContent = skills.length;

    // Preview skills
    const previewEl = document.getElementById('skills-preview');
    if (skills.length > 0) {
      previewEl.innerHTML = skills.slice(0, 15).map(s =>
        `<span class="skill-tag tech" style="font-size:0.8rem;padding:4px 10px;">${escHtml(s.skill_name)}</span>`
      ).join('') + (skills.length > 15 ? `<span style="color:var(--text-muted);font-size:0.8rem;">+${skills.length - 15} more</span>` : '');
    }

    // Load experience count
    const expRes = await fetch(`${API_BASE}/api/experience`, { headers: authHeaders() });
    const exp = await expRes.json();
    document.getElementById('stat-exp').textContent = exp.length;

    // Load education count
    const eduRes = await fetch(`${API_BASE}/api/education`, { headers: authHeaders() });
    const edu = await eduRes.json();
    document.getElementById('stat-edu').textContent = edu.length;

  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

async function analyzeFromSavedSkills() {
  const card = document.getElementById('card-analyze-saved');
  card.style.opacity = '0.6';
  card.style.pointerEvents = 'none';

  try {
    const res = await fetch(`${API_BASE}/api/analyze/saved-skills`, {
      method: 'POST',
      headers: authHeaders()
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis failed');

    // Store result and redirect
    sessionStorage.setItem('quick_analysis', JSON.stringify(data));
    window.location.href = '/?from=saved';
  } catch (err) {
    card.style.opacity = '';
    card.style.pointerEvents = '';
    alert('Error: ' + err.message);
  }
}

loadDashboard();
initParticles();
