/* ═══════════════════════════════════════════════════════════
   AI Career Advisor — Frontend JavaScript
   ═══════════════════════════════════════════════════════════ */

const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

let currentFile = null;
let activeTab = 'file';
let analysisData = null;

// ─── Initialization ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  fetchStats();
  setupTextArea();
});

// ─── Particle Background ──────────────────────────────────────────────────────
function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  const ctx = canvas.getContext('2d');

  let particles = [];
  let W, H;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.r = Math.random() * 1.5 + 0.3;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.4 + 0.1;
      const colors = ['139,92,246', '6,182,212', '236,72,153', '16,185,129'];
      this.color = colors[Math.floor(Math.random() * colors.length)];
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.color},${this.opacity})`;
      ctx.fill();
    }
  }

  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < 80; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, W, H);

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(139,92,246,${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
  }
  animate();
}

// ─── Stats Fetch ──────────────────────────────────────────────────────────────
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error('API not ready');
    const data = await res.json();

    animateCount('stat-jobs', data.total_jobs || 0);
    animateCount('stat-courses', data.total_courses || 0);
    animateCount('stat-skills', data.total_skills || 0);
    animateCount('stat-cats', data.career_categories || 0);

    document.getElementById('nav-stats-text').textContent =
      `${(data.total_jobs || 0).toLocaleString()} jobs loaded`;
  } catch (e) {
    document.getElementById('stat-jobs').textContent = '—';
    document.getElementById('stat-courses').textContent = '—';
    document.getElementById('stat-skills').textContent = '—';
    document.getElementById('stat-cats').textContent = '—';
    document.getElementById('nav-stats-text').textContent = 'Backend starting...';
  }
}

function animateCount(elemId, target) {
  const el = document.getElementById(elemId);
  if (!el) return;
  const duration = 1500;
  const start = performance.now();
  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const val = Math.round(eased * target);
    el.textContent = val >= 1000 ? val.toLocaleString() : val.toString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ─── Tab Switching ────────────────────────────────────────────────────────────
function switchTab(tab) {
  activeTab = tab;
  document.getElementById('tab-file').classList.toggle('active', tab === 'file');
  document.getElementById('tab-text').classList.toggle('active', tab === 'text');
  document.getElementById('panel-file').classList.toggle('hidden', tab !== 'file');
  document.getElementById('panel-text').classList.toggle('hidden', tab !== 'text');
}

// ─── File Handling ────────────────────────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.add('drag-over');
}

function handleDragLeave(e) {
  document.getElementById('dropzone').classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}

function setFile(file) {
  const allowed = ['.pdf', '.txt', '.doc'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('Please upload a PDF or TXT file', 'error');
    return;
  }
  currentFile = file;
  const dz = document.getElementById('dropzone');
  dz.classList.add('has-file');
  document.getElementById('dropzone-text').innerHTML = `
    <p class="dropzone-main" style="color:var(--green)">✓ ${file.name}</p>
    <p class="dropzone-sub">${formatBytes(file.size)} · Click to change file</p>
  `;
  document.getElementById('dropzone-icon').innerHTML = `
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="22" fill="rgba(16,185,129,0.1)" stroke="rgba(16,185,129,0.3)" stroke-width="1"/>
      <path d="M15 24l7 7 11-14" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `;
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ─── Text Area ────────────────────────────────────────────────────────────────
function setupTextArea() {
  const ta = document.getElementById('cv-text-input');
  if (!ta) return;
  ta.addEventListener('input', () => {
    document.getElementById('char-count').textContent = `${ta.value.length} characters`;
  });
}

function loadSampleCV() {
  const sampleCV = `JOHN DOE
Email: john.doe@example.com | LinkedIn: linkedin.com/in/johndoe

SUMMARY
Experienced Data Scientist with 3 years of expertise in machine learning, 
statistical modeling, and data-driven decision making. Passionate about 
building scalable AI solutions.

SKILLS
Programming: Python (pandas, numpy, scikit-learn, matplotlib), SQL, R, JavaScript
Machine Learning: Regression, Classification, Clustering, Deep Learning, NLP
Frameworks: TensorFlow, PyTorch, Keras, FastAPI, Flask
Tools: Docker, Git, Jupyter, Tableau, Power BI, Excel
Databases: MySQL, PostgreSQL, MongoDB, Redis
Cloud: AWS (S3, EC2, Lambda), Google Cloud Platform

EXPERIENCE
Data Scientist | TechCorp Inc. | Jan 2022 - Present
• Built customer churn prediction model (Random Forest) reducing churn by 23%
• Developed NLP pipeline for sentiment analysis of 1M+ customer reviews
• Automated ETL pipelines using Apache Airflow reducing processing time by 40%

Data Analyst | Analytics Co. | Jun 2020 - Dec 2021
• Created dashboards in Tableau for C-suite reporting
• Performed A/B testing and statistical analysis for product features
• Wrote SQL queries for data extraction and transformation

EDUCATION
B.Sc. Computer Science | University of Technology | 2020
• GPA: 3.8/4.0 | Dean's List
• Thesis: "Predicting Student Performance using Machine Learning"

CERTIFICATIONS
• AWS Certified Machine Learning Specialty
• Google Professional Data Engineer`;

  document.getElementById('cv-text-input').value = sampleCV;
  document.getElementById('char-count').textContent = `${sampleCV.length} characters`;
  switchTab('text');
}

// ─── Analyze CV ───────────────────────────────────────────────────────────────
async function analyzeCV() {
  if (activeTab === 'file' && !currentFile) {
    showToast('Please upload a CV file first', 'error');
    return;
  }
  if (activeTab === 'text' && !document.getElementById('cv-text-input').value.trim()) {
    showToast('Please enter your CV text', 'error');
    return;
  }

  showLoading();

  try {
    let response;

    if (activeTab === 'file') {
      const formData = new FormData();
      formData.append('file', currentFile);
      response = await fetchWithTimeout(`${API_BASE}/api/analyze/upload`, {
        method: 'POST',
        body: formData
      }, 120000); // 2 menit timeout untuk PDF
    } else {
      const text = document.getElementById('cv-text-input').value;
      response = await fetchWithTimeout(`${API_BASE}/api/analyze/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      }, 120000); // 2 menit timeout
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Server error' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    analysisData = data;

    await simulateLoadingSteps();
    hideLoading();
    renderResults(data);

  } catch (err) {
    hideLoading();
    if (err.name === 'AbortError' || err.message?.includes('aborted')) {
      showToast('Analisis terlalu lama. Coba lagi atau gunakan tab Paste Text.', 'error');
    } else if (err.message?.includes('fetch')) {
      showToast('Tidak bisa terhubung ke server. Pastikan server sudah dijalankan.', 'error');
    } else {
      showToast(`Error: ${err.message}`, 'error');
    }
    console.error('Analysis error:', err);
  }
}

async function fetchWithTimeout(url, opts, timeout) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

// ─── Loading States ───────────────────────────────────────────────────────────
function showLoading() {
  document.getElementById('loading-section').classList.remove('hidden');
  document.getElementById('upload').style.opacity = '0.3';
  document.getElementById('upload').style.pointerEvents = 'none';
  resetLoadingSteps();
}

function hideLoading() {
  document.getElementById('loading-section').classList.add('hidden');
  document.getElementById('upload').style.opacity = '';
  document.getElementById('upload').style.pointerEvents = '';
}

function resetLoadingSteps() {
  for (let i = 1; i <= 4; i++) {
    const step = document.getElementById(`step-${i}`);
    step.classList.remove('active', 'done');
    if (i === 1) step.classList.add('active');
  }
}

async function simulateLoadingSteps() {
  const delays = [300, 500, 600, 400];
  for (let i = 1; i <= 4; i++) {
    await sleep(delays[i - 1]);
    const prev = document.getElementById(`step-${i}`);
    prev.classList.remove('active');
    prev.classList.add('done');
    prev.querySelector('.step-icon').textContent = '✓';
    if (i < 4) document.getElementById(`step-${i + 1}`).classList.add('active');
  }
  await sleep(300);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Render Results ───────────────────────────────────────────────────────────
function renderResults(data) {
  const cv = data.cv_analysis || {};
  const jobs = data.job_recommendations || [];
  const courses = data.course_recommendations || [];
  const gap = data.skill_gap || {};

  // Profile card
  const category = cv.career_category || 'Professional';
  const confidence = Math.round((cv.confidence || 0) * 100);
  document.getElementById('profile-category').textContent = category;
  document.getElementById('profile-career-title').textContent = category + ' Profile';
  document.getElementById('profile-avatar-letter').textContent = category[0] || '?';
  document.getElementById('confidence-pct').textContent = `${confidence}%`;
  document.getElementById('pstat-skills').textContent = cv.skill_count || 0;
  document.getElementById('pstat-jobs').textContent = jobs.length;
  document.getElementById('pstat-courses').textContent = courses.length;

  setTimeout(() => {
    document.getElementById('confidence-fill').style.width = `${confidence}%`;
  }, 300);

  // Skills
  renderSkillTags('tech-skills-tags', cv.tech_skills || [], 'tech');
  renderSkillTags('tool-skills-tags', cv.tool_skills || [], 'tools');
  renderSkillTags('soft-skills-tags', cv.soft_skills || [], 'soft');

  // Fallback: if all empty but has all_skills
  if (!cv.tech_skills?.length && !cv.tool_skills?.length && cv.all_skills?.length) {
    renderSkillTags('tech-skills-tags', cv.all_skills || [], 'tech');
  }

  // Skill Gap
  renderSkillGap(gap.top_missing_skills || []);

  // Jobs
  renderJobs(jobs);

  // Courses
  renderCourses(courses);

  // Show results
  document.getElementById('results').classList.remove('hidden');
  document.getElementById('nav-results').classList.remove('hidden');

  setTimeout(() => {
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

function renderSkillTags(containerId, skills, type) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!skills.length) {
    container.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">None detected</span>';
    return;
  }
  container.innerHTML = skills.map((s, i) => `
    <span class="skill-tag ${type}" style="animation-delay:${i * 0.04}s">${escHtml(s)}</span>
  `).join('');
}

function renderSkillGap(missingSkills) {
  const container = document.getElementById('gap-skills');
  if (!container) return;
  if (!missingSkills.length) {
    document.getElementById('gap-card').style.display = 'none';
    return;
  }
  container.innerHTML = missingSkills.map((item, i) => `
    <div class="gap-skill-item" style="animation-delay:${i * 0.06}s">
      <span class="gap-skill-name">${escHtml(item.skill || item)}</span>
      ${item.demand ? `<span class="gap-skill-demand">${item.demand}× demand</span>` : ''}
    </div>
  `).join('');
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobs-grid');
  if (!grid) return;
  if (!jobs.length) {
    grid.innerHTML = '<p style="color:var(--text-muted)">No job matches found. Try adding more skills to your CV.</p>';
    return;
  }
  grid.innerHTML = jobs.map((job, i) => {
    const matchPct = job.match_score || job.match_percentage || 0;
    const matched = job.matched_skills || [];
    const missing = job.missing_skills || [];
    const allSkills = [...matched.slice(0, 3), ...missing.slice(0, 2)];

    return `
    <div class="job-card" onclick="openJobModal(${i})" style="animation-delay:${i * 0.07}s">
      <div class="job-card-top">
        <div>
          <div class="job-title">${escHtml(job.title || 'Job Title')}</div>
          <div class="job-company">${escHtml(job.company || 'Company')}</div>
        </div>
        <div class="job-match-badge">
          <span class="job-match-dot"></span>
          ${matchPct}%
        </div>
      </div>
      <div class="job-meta">
        ${job.location && job.location !== 'nan' ? `<span class="job-meta-item">📍 ${escHtml(job.location)}</span>` : ''}
        ${job.level && job.level !== 'nan' ? `<span class="job-meta-item">🏢 ${escHtml(job.level)}</span>` : ''}
        ${job.type && job.type !== 'nan' ? `<span class="job-meta-item">⏰ ${escHtml(job.type)}</span>` : ''}
      </div>
      ${job.salary && job.salary !== 'N/A' ? `<div class="job-salary">💰 ${escHtml(job.salary)}</div>` : ''}
      <div class="job-skills-preview">
        ${matched.slice(0, 3).map(s => `<span class="job-skill-tag matched">✓ ${escHtml(s)}</span>`).join('')}
        ${missing.slice(0, 2).map(s => `<span class="job-skill-tag missing">${escHtml(s)}</span>`).join('')}
        ${(job.skills || []).length > 5 ? `<span class="job-skill-more">+${(job.skills || []).length - 5} more</span>` : ''}
      </div>
    </div>`;
  }).join('');
}

function renderCourses(courses) {
  const grid = document.getElementById('courses-grid');
  if (!grid) return;
  if (!courses.length) {
    grid.innerHTML = '<p style="color:var(--text-muted)">No course recommendations available.</p>';
    return;
  }
  grid.innerHTML = courses.map((c, i) => {
    const platform = c.platform || 'Online';
    const platformClass = platform.toLowerCase().includes('udemy') ? 'platform-udemy' : 'platform-coursera';
    const platformIcon = platform.toLowerCase().includes('udemy') ? '🎯' : '🎓';
    const students = c.subscribers ? formatNumber(c.subscribers) : null;
    const rating = c.rating ? parseFloat(c.rating).toFixed(1) : null;
    const price = c.is_paid === false || c.price === 0 ? 'FREE' : (c.price ? `$${c.price}` : null);

    return `
    <a class="course-card" href="${escHtml(c.url || '#')}" target="_blank" rel="noopener noreferrer" style="animation-delay:${i * 0.07}s">
      ${price ? `<div class="course-price ${price === 'FREE' ? 'price-free' : 'price-paid'}">${price}</div>` : ''}
      <div class="course-platform-badge ${platformClass}">${platformIcon} ${platform}</div>
      <div class="course-title">${escHtml(c.title || 'Course Title')}</div>
      ${c.subject ? `<div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:8px">${escHtml(c.subject)}</div>` : ''}
      <div class="course-meta">
        ${rating ? `<span class="course-rating">⭐ ${rating}</span>` : ''}
        ${students ? `<span class="course-students">${students} students</span>` : ''}
        <span class="course-level-badge">${escHtml(c.level || 'All Levels')}</span>
      </div>
    </a>`;
  }).join('');
}

// ─── Job Modal ────────────────────────────────────────────────────────────────
function openJobModal(index) {
  if (!analysisData) return;
  const job = (analysisData.job_recommendations || [])[index];
  if (!job) return;

  const matched = job.matched_skills || [];
  const missing = job.missing_skills || [];
  const allSkills = job.skills || [];

  document.getElementById('modal-body').innerHTML = `
    <div style="margin-bottom:24px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <h3 style="font-size:1.3rem;font-weight:800;letter-spacing:-0.02em;flex:1">${escHtml(job.title)}</h3>
        <div class="job-match-badge" style="flex-shrink:0">
          <span class="job-match-dot"></span>
          ${job.match_score || 0}% Match
        </div>
      </div>
      <p style="color:var(--text-secondary);font-weight:600">${escHtml(job.company || 'Company')}</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:24px">
      ${job.location && job.location !== 'nan' ? `<div style="padding:12px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid var(--border)"><div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">Location</div><div style="font-weight:600">📍 ${escHtml(job.location)}</div></div>` : ''}
      ${job.level && job.level !== 'nan' ? `<div style="padding:12px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid var(--border)"><div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">Level</div><div style="font-weight:600">🏢 ${escHtml(job.level)}</div></div>` : ''}
      ${job.type && job.type !== 'nan' ? `<div style="padding:12px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid var(--border)"><div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">Type</div><div style="font-weight:600">⏰ ${escHtml(job.type)}</div></div>` : ''}
      ${job.salary && job.salary !== 'N/A' ? `<div style="padding:12px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid var(--border)"><div style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">Salary</div><div style="font-weight:600;color:var(--cyan-light)">💰 ${escHtml(job.salary)}</div></div>` : ''}
    </div>

    ${matched.length ? `
    <div style="margin-bottom:20px">
      <h4 style="font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--green);margin-bottom:12px">✓ Your Matching Skills</h4>
      <div class="skill-tags">${matched.map(s => `<span class="skill-tag tech">✓ ${escHtml(s)}</span>`).join('')}</div>
    </div>` : ''}

    ${missing.length ? `
    <div style="margin-bottom:20px">
      <h4 style="font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--amber);margin-bottom:12px">⚡ Skills to Learn</h4>
      <div class="skill-tags">${missing.map(s => `<span class="skill-tag" style="background:rgba(245,158,11,0.08);border-color:rgba(245,158,11,0.2);color:var(--amber)">${escHtml(s)}</span>`).join('')}</div>
    </div>` : ''}

    ${job.url && job.url !== 'nan' && job.url !== '#' ? `
    <a href="${escHtml(job.url)}" target="_blank" rel="noopener noreferrer"
       style="display:flex;align-items:center;justify-content:center;gap:8px;padding:14px;background:linear-gradient(135deg,rgba(139,92,246,0.2),rgba(6,182,212,0.1));border:1px solid rgba(139,92,246,0.3);border-radius:10px;color:var(--purple-light);font-weight:600;text-decoration:none;transition:var(--transition)">
      View on LinkedIn →
    </a>` : ''}
  `;

  document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

// ─── Reset ────────────────────────────────────────────────────────────────────
function resetToUpload() {
  document.getElementById('results').classList.add('hidden');
  document.getElementById('nav-results').classList.add('hidden');
  document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
  currentFile = null;
  analysisData = null;

  // Reset dropzone
  const dz = document.getElementById('dropzone');
  dz.classList.remove('has-file');
  document.getElementById('dropzone-text').innerHTML = `
    <p class="dropzone-main">Drop your CV here</p>
    <p class="dropzone-sub">or click to browse · PDF, TXT supported</p>
  `;
  document.getElementById('dropzone-icon').innerHTML = `
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="22" fill="rgba(139,92,246,0.1)" stroke="rgba(139,92,246,0.3)" stroke-width="1"/>
      <path d="M24 32V20M24 20l-5 5M24 20l5 5" stroke="#8b5cf6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="14" y="33" width="20" height="3" rx="1.5" fill="rgba(139,92,246,0.4)"/>
    </svg>
  `;

  document.getElementById('cv-text-input').value = '';
  document.getElementById('char-count').textContent = '0 characters';
  document.getElementById('file-input').value = '';
}

// ─── Toast ────────────────────────────────────────────────────────────────────
let toastTimeout;
function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  toast.classList.remove('hidden');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.add('hidden'), 4000);
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

function formatNumber(n) {
  if (!n) return '0';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
  return String(n);
}

// Close modal on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});
