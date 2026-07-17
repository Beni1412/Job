/* ═══════════════════════════════════════════════
   builder.js — CV Builder logic
   ═══════════════════════════════════════════════ */

const token = localStorage.getItem('career_token');
if (!token) window.location.href = '/auth';

const email = localStorage.getItem('career_email') || '';

function authHeaders() {
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

// ─── Section Navigation ───────────────────────────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.builder-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.sidebar-section').forEach(s => s.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.add('active');
  document.getElementById(`nav-${name}`).classList.add('active');
}

// ─── PERSONAL INFO ────────────────────────────────────────────────────────────
async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/api/profile`, { headers: authHeaders() });
    if (res.status === 401) { window.location.href = '/auth'; return; }
    const data = await res.json();
    if (data) {
      setValue('p-name', data.full_name);
      setValue('p-phone', data.phone);
      setValue('p-city', data.city);
      setValue('p-address', data.address);
      setValue('p-linkedin', data.linkedin);
      setValue('p-github', data.github);
      setValue('p-about', data.about_me);
    }
  } catch (err) { console.error('Load profile error:', err); }
}

async function saveProfile() {
  const btn = document.querySelector('#section-personal .btn-save');
  btn.textContent = 'Saving...'; btn.disabled = true;

  const body = {
    full_name: getValue('p-name'),
    phone:     getValue('p-phone'),
    city:      getValue('p-city'),
    address:   getValue('p-address'),
    linkedin:  getValue('p-linkedin'),
    github:    getValue('p-github'),
    about_me:  getValue('p-about'),
  };

  try {
    const res = await fetch(`${API_BASE}/api/profile`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('Failed to save');

    const status = document.getElementById('profile-saved-msg');
    status.classList.add('visible');
    setTimeout(() => status.classList.remove('visible'), 2500);
  } catch (err) {
    showToast('Failed to save profile', 'error');
  } finally {
    btn.textContent = 'Save Profile'; btn.disabled = false;
  }
}

// ─── SKILLS ───────────────────────────────────────────────────────────────────
let userSkills = [];

async function loadSkills() {
  try {
    const res = await fetch(`${API_BASE}/api/skills`, { headers: authHeaders() });
    userSkills = await res.json();
    renderSkills();
  } catch (err) { console.error('Load skills error:', err); }
}

function renderSkills() {
  const container = document.getElementById('skills-list');
  if (!userSkills.length) {
    container.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem;">No skills yet. Add your first skill above!</span>';
    return;
  }
  container.innerHTML = userSkills.map(sk => `
    <div class="skill-item">
      <span>${escHtml(sk.skill_name)}</span>
      <span style="font-size:0.7rem;color:var(--text-muted);margin-left:2px;">${escHtml(sk.category || '')}</span>
      <button onclick="deleteSkill('${sk.id}')" title="Remove">×</button>
    </div>
  `).join('');
}

async function addSkill() {
  const input = document.getElementById('skill-input');
  const cat   = document.getElementById('skill-cat').value;
  const name  = input.value.trim();
  if (!name) { input.focus(); return; }

  try {
    const res = await fetch(`${API_BASE}/api/skills`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ skill_name: name, category: cat })
    });
    const sk = await res.json();
    userSkills.push(sk);
    renderSkills();
    input.value = '';
    input.focus();
  } catch (err) {
    showToast('Failed to add skill', 'error');
  }
}

async function deleteSkill(id) {
  try {
    await fetch(`${API_BASE}/api/skills/${id}`, { method: 'DELETE', headers: authHeaders() });
    userSkills = userSkills.filter(s => s.id !== id);
    renderSkills();
  } catch (err) {
    showToast('Failed to delete skill', 'error');
  }
}

// ─── EXPERIENCE ───────────────────────────────────────────────────────────────
let experiences = [];

async function loadExperience() {
  try {
    const res = await fetch(`${API_BASE}/api/experience`, { headers: authHeaders() });
    experiences = await res.json();
    renderExperience();
  } catch (err) { console.error('Load experience error:', err); }
}

function renderExperience() {
  const container = document.getElementById('experience-list');
  if (!experiences.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:12px;">No experience added yet.</p>';
    return;
  }
  container.innerHTML = experiences.map(exp => `
    <div class="entry-card">
      <div class="entry-card-title">${escHtml(exp.title)} @ ${escHtml(exp.company)}</div>
      <div class="entry-card-sub">${escHtml(exp.start_date || '')} ${exp.start_date ? '–' : ''} ${exp.is_current ? 'Present' : escHtml(exp.end_date || '')}</div>
      ${exp.description ? `<div style="color:var(--text-secondary);font-size:0.8rem;margin-top:8px;line-height:1.5;">${escHtml(exp.description).replace(/\n/g,'<br>')}</div>` : ''}
      <button class="btn-delete-entry" onclick="deleteExperience('${exp.id}')">Delete</button>
    </div>
  `).join('');
}

function toggleCurrent() {
  const checked = document.getElementById('exp-current').checked;
  document.getElementById('exp-end').disabled = checked;
  if (checked) document.getElementById('exp-end').value = '';
}

async function addExperience() {
  const title   = getValue('exp-title');
  const company = getValue('exp-company');
  if (!title || !company) { showToast('Title and Company are required', 'error'); return; }

  const body = {
    title, company,
    start_date:  getValue('exp-start') || null,
    end_date:    getValue('exp-end') || null,
    is_current:  document.getElementById('exp-current').checked,
    description: getValue('exp-desc') || null,
  };

  try {
    const res = await fetch(`${API_BASE}/api/experience`, {
      method: 'POST', headers: authHeaders(), body: JSON.stringify(body)
    });
    const exp = await res.json();
    experiences.unshift(exp);
    renderExperience();
    // Clear form
    ['exp-title','exp-company','exp-start','exp-end','exp-desc'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    document.getElementById('exp-current').checked = false;
    showToast('Experience added!', 'success');
  } catch (err) {
    showToast('Failed to add experience', 'error');
  }
}

async function deleteExperience(id) {
  try {
    await fetch(`${API_BASE}/api/experience/${id}`, { method: 'DELETE', headers: authHeaders() });
    experiences = experiences.filter(e => e.id !== id);
    renderExperience();
  } catch (err) {
    showToast('Failed to delete', 'error');
  }
}

// ─── EDUCATION ────────────────────────────────────────────────────────────────
let educations = [];

async function loadEducation() {
  try {
    const res = await fetch(`${API_BASE}/api/education`, { headers: authHeaders() });
    educations = await res.json();
    renderEducation();
  } catch (err) { console.error('Load education error:', err); }
}

function renderEducation() {
  const container = document.getElementById('education-list');
  if (!educations.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:12px;">No education added yet.</p>';
    return;
  }
  container.innerHTML = educations.map(edu => `
    <div class="entry-card">
      <div class="entry-card-title">${escHtml(edu.institution)}</div>
      <div class="entry-card-sub">${escHtml(edu.degree || '')} ${edu.field ? 'in ' + escHtml(edu.field) : ''} ${edu.grad_year ? '· ' + escHtml(edu.grad_year) : ''} ${edu.gpa ? '· GPA: ' + escHtml(edu.gpa) : ''}</div>
      <button class="btn-delete-entry" onclick="deleteEducation('${edu.id}')">Delete</button>
    </div>
  `).join('');
}

async function addEducation() {
  const institution = getValue('edu-institution');
  if (!institution) { showToast('Institution name is required', 'error'); return; }

  const body = {
    institution,
    degree:    getValue('edu-degree') || null,
    field:     getValue('edu-field') || null,
    grad_year: getValue('edu-year') || null,
    gpa:       getValue('edu-gpa') || null,
  };

  try {
    const res = await fetch(`${API_BASE}/api/education`, {
      method: 'POST', headers: authHeaders(), body: JSON.stringify(body)
    });
    const edu = await res.json();
    educations.unshift(edu);
    renderEducation();
    ['edu-institution','edu-degree','edu-field','edu-year','edu-gpa'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    showToast('Education added!', 'success');
  } catch (err) {
    showToast('Failed to add education', 'error');
  }
}

async function deleteEducation(id) {
  try {
    await fetch(`${API_BASE}/api/education/${id}`, { method: 'DELETE', headers: authHeaders() });
    educations = educations.filter(e => e.id !== id);
    renderEducation();
  } catch (err) {
    showToast('Failed to delete', 'error');
  }
}

// ─── DOWNLOAD CV ──────────────────────────────────────────────────────────────
async function downloadCV() {
  const btn = document.getElementById('btn-download');
  btn.textContent = '⏳ Generating...';
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/cv/download`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to generate CV');
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'resume.pdf';
    a.click();
    URL.revokeObjectURL(url);
    showToast('CV downloaded!', 'success');
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  } finally {
    btn.textContent = '⬇ Download PDF';
    btn.disabled = false;
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function getValue(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}
function setValue(id, val) {
  const el = document.getElementById(id);
  if (el && val) el.value = val;
}

function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 3000);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
initParticles();
loadProfile();
loadSkills();
loadExperience();
loadEducation();
