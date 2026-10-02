/**
 * CampusFix - Maintenance Management Frontend Logic
 */

// Application State
const state = {
  currentRole: localStorage.getItem('campusfix_role') || 'user', // 'user' or 'admin'
  workers: [],
  complaints: [],
  filters: {
    status: 'All',
    priority: 'All',
    category: 'All',
    search: ''
  },
  stats: {
    status_counts: { Reported: 0, Assigned: 0, 'In Progress': 0, Resolved: 0 },
    priority_counts: { Critical: 0, High: 0, Medium: 0, Low: 0 },
    total: 0
  }
};

// DOM Elements
const userRoleBtn = document.getElementById('userRoleBtn');
const adminRoleBtn = document.getElementById('adminRoleBtn');
const roleBanner = document.getElementById('roleBanner');
const bannerIcon = document.getElementById('bannerIcon');
const bannerText = document.getElementById('bannerText');

const complaintForm = document.getElementById('complaintForm');
const photoInput = document.getElementById('photoInput');
const dropArea = document.getElementById('dropArea');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const uploadPreview = document.getElementById('uploadPreview');
const previewImg = document.getElementById('previewImg');
const removePhotoBtn = document.getElementById('removePhotoBtn');
const submitBtn = document.getElementById('submitBtn');
const submitBtnText = document.getElementById('submitBtnText');

const complaintsContainer = document.getElementById('complaintsContainer');
const totalTicketsCount = document.getElementById('totalTicketsCount');
const filterStatus = document.getElementById('filterStatus');
const filterPriority = document.getElementById('filterPriority');
const filterCategory = document.getElementById('filterCategory');
const searchInput = document.getElementById('searchInput');
const resetFiltersBtn = document.getElementById('resetFiltersBtn');
const refreshStatsBtn = document.getElementById('refreshStatsBtn');

// Modals & Toasts
const photoModal = document.getElementById('photoModal');
const modalFullImg = document.getElementById('modalFullImg');
const photoModalTitle = document.getElementById('photoModalTitle');
const photoModalCaption = document.getElementById('photoModalCaption');
const closePhotoModalBtn = document.getElementById('closePhotoModalBtn');
const toastContainer = document.getElementById('toastContainer');

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  applyRole(state.currentRole);
  await loadWorkers();
  await loadStats();
  await loadComplaints();
});

// ==========================================================================
// Role Switching
// ==========================================================================
function setRole(role) {
  state.currentRole = role;
  localStorage.setItem('campusfix_role', role);
  applyRole(role);
  renderComplaints();
}

function applyRole(role) {
  if (role === 'admin') {
    document.body.classList.remove('mode-user');
    document.body.classList.add('mode-admin');
    adminRoleBtn.classList.add('active');
    userRoleBtn.classList.remove('active');

    roleBanner.className = 'role-banner admin-banner';
    bannerIcon.textContent = '🛡️';
    bannerText.innerHTML = '<strong>Admin Mode Active:</strong> You can assign complaints to maintenance workers, advance ticket statuses, and monitor facility metrics.';
  } else {
    document.body.classList.remove('mode-admin');
    document.body.classList.add('mode-user');
    userRoleBtn.classList.add('active');
    adminRoleBtn.classList.remove('active');

    roleBanner.className = 'role-banner user-banner';
    bannerIcon.textContent = '👤';
    bannerText.innerHTML = '<strong>Resident / User Mode:</strong> Report new maintenance issues and view current repair statuses across campus.';
  }
}

// ==========================================================================
// API Calls
// ==========================================================================
async function loadWorkers() {
  try {
    const res = await fetch('/api/workers');
    if (res.ok) {
      state.workers = await res.json();
    }
  } catch (err) {
    console.error('Failed to load workers:', err);
  }
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (res.ok) {
      state.stats = await res.json();
      updateStatsUI();
    }
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

function updateStatsUI() {
  const { status_counts, priority_counts, total } = state.stats;

  // Status counts
  document.getElementById('countReported').textContent = status_counts['Reported'] || 0;
  document.getElementById('countAssigned').textContent = status_counts['Assigned'] || 0;
  document.getElementById('countInProgress').textContent = status_counts['In Progress'] || 0;
  document.getElementById('countResolved').textContent = status_counts['Resolved'] || 0;

  // Priority counts
  document.getElementById('countCritical').textContent = priority_counts['Critical'] || 0;
  document.getElementById('countHigh').textContent = priority_counts['High'] || 0;
  document.getElementById('countMedium').textContent = priority_counts['Medium'] || 0;
  document.getElementById('countLow').textContent = priority_counts['Low'] || 0;

  totalTicketsCount.textContent = total;
}

async function loadComplaints() {
  complaintsContainer.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading complaints...</p>
    </div>
  `;

  try {
    const params = new URLSearchParams();
    if (state.filters.status !== 'All') params.append('status', state.filters.status);
    if (state.filters.priority !== 'All') params.append('priority', state.filters.priority);
    if (state.filters.category !== 'All') params.append('category', state.filters.category);
    if (state.filters.search.trim()) params.append('search', state.filters.search.trim());

    const res = await fetch(`/api/complaints?${params.toString()}`);
    if (res.ok) {
      state.complaints = await res.json();
      renderComplaints();
    } else {
      complaintsContainer.innerHTML = `<div class="empty-state"><p>Error loading complaints.</p></div>`;
    }
  } catch (err) {
    console.error('Failed to load complaints:', err);
    complaintsContainer.innerHTML = `<div class="empty-state"><p>Network error loading complaints.</p></div>`;
  }
}

// ==========================================================================
// Rendering Complaints
// ==========================================================================
function renderComplaints() {
  if (!state.complaints || state.complaints.length === 0) {
    complaintsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📋</div>
        <p><strong>No complaints match your criteria.</strong></p>
        <p style="font-size: 0.85rem; margin-top: 0.25rem;">Try adjusting filters or submit a new complaint using the form.</p>
      </div>
    `;
    return;
  }

  const categoryIcons = {
    Electrical: '⚡',
    Plumbing: '🚰',
    Furniture: '🪑',
    Cleaning: '🧹',
    Other: '📦'
  };

  const priorityBadges = {
    Critical: '<span class="badge badge-critical"><span class="pulse-indicator"></span> Critical</span>',
    High: '<span class="badge badge-high">🟠 High</span>',
    Medium: '<span class="badge badge-medium">🔵 Medium</span>',
    Low: '<span class="badge badge-low">🟢 Low</span>'
  };

  const statusBadges = {
    Reported: '<span class="badge badge-status-reported"><span class="stat-dot dot-reported"></span> Reported</span>',
    Assigned: '<span class="badge badge-status-assigned"><span class="stat-dot dot-assigned"></span> Assigned</span>',
    'In Progress': '<span class="badge badge-status-in-progress"><span class="stat-dot dot-inprogress"></span> In Progress</span>',
    Resolved: '<span class="badge badge-status-resolved"><span class="stat-dot dot-resolved"></span> Resolved</span>'
  };

  const nextActionLabels = {
    Reported: 'Assign / Move to Assigned ➔',
    Assigned: 'Start Work (In Progress) ➔',
    'In Progress': 'Mark Resolved ✓'
  };

  const html = state.complaints.map(item => {
    const pBadge = priorityBadges[item.priority] || item.priority;
    const sBadge = statusBadges[item.status] || item.status;
    const catIcon = categoryIcons[item.category] || '🔧';

    // Photo preview markup
    let photoMarkup = '';
    if (item.photo_filename) {
      photoMarkup = `
        <span class="complaint-photo-thumb" onclick="openPhotoModal('${item.photo_filename}', '${item.ticket_no} - ${escapeHtml(item.location)}')">
          📷 Photo
        </span>
      `;
    }

    // Worker options for select dropdown
    let workerOptions = `<option value="">Select worker to assign...</option>`;
    state.workers.forEach(w => {
      const selected = (item.assigned_worker_id === w.id) ? 'selected' : '';
      workerOptions += `<option value="${w.id}" ${selected}>${w.name} (${w.role})</option>`;
    });

    // Advance button logic
    let advanceBtnMarkup = '';
    if (item.status in nextActionLabels) {
      const actionLabel = nextActionLabels[item.status];
      const isResolve = item.status === 'In Progress';
      advanceBtnMarkup = `
        <button class="btn btn-sm btn-advance ${isResolve ? 'advance-resolve' : ''}" onclick="advanceStatus(${item.id})">
          ${actionLabel}
        </button>
      `;
    } else {
      advanceBtnMarkup = `
        <span style="font-size: 0.775rem; color: #059669; font-weight: 600;">
          ✓ Fully Resolved
        </span>
      `;
    }

    // Workflow indicator
    const workflowSteps = ['Reported', 'Assigned', 'In Progress', 'Resolved'];
    const currentIdx = workflowSteps.indexOf(item.status);
    const workflowTrail = workflowSteps.map((step, idx) => {
      const isCurrent = idx === currentIdx;
      return `<span class="workflow-step ${isCurrent ? 'current' : ''}">${step}</span>`;
    }).join('<span class="workflow-arrow">›</span>');

    return `
      <div class="complaint-card" id="card-${item.id}">
        <div class="complaint-top-row">
          <div class="ticket-meta">
            <span class="ticket-id">${item.ticket_no}</span>
            <span class="category-tag">${catIcon} ${item.category}</span>
            <span style="color: #94a3b8; font-size: 0.75rem;">• ${item.created_at.split(' ')[0]}</span>
          </div>
          <div class="badges-group">
            ${pBadge}
            ${sBadge}
          </div>
        </div>

        <div class="complaint-location">
          📍 ${escapeHtml(item.location)}
        </div>

        <div class="complaint-desc">
          ${escapeHtml(item.description)}
        </div>

        <div class="complaint-bottom-row">
          <div class="worker-info">
            <span>Assigned:</span>
            ${item.assigned_worker_name 
              ? `<span class="worker-badge-assigned">👷‍♂️ <strong>${escapeHtml(item.assigned_worker_name)}</strong> (${escapeHtml(item.assigned_worker_role)})</span>` 
              : `<span class="worker-unassigned">Not assigned</span>`}
          </div>

          <div>
            ${photoMarkup}
          </div>
        </div>

        <!-- Admin Action Bar (visible only in admin mode) -->
        <div class="admin-action-bar">
          <div class="admin-assign-box">
            <select class="form-control form-control-sm" id="assignSelect-${item.id}" style="width: auto; min-width: 190px;">
              ${workerOptions}
            </select>
            <button class="btn btn-outline btn-sm" onclick="assignWorker(${item.id})">
              Assign
            </button>
          </div>

          <div class="admin-workflow-box">
            <div class="workflow-trail" style="margin-right: 0.5rem;">
              ${workflowTrail}
            </div>
            ${advanceBtnMarkup}
          </div>
        </div>
      </div>
    `;
  }).join('');

  complaintsContainer.innerHTML = html;
}

// ==========================================================================
// Admin Actions: Assign & Advance Workflow
// ==========================================================================
async function assignWorker(complaintId) {
  const select = document.getElementById(`assignSelect-${complaintId}`);
  const workerId = select.value;

  if (!workerId) {
    showToast('Please select a maintenance worker first.', 'error');
    return;
  }

  try {
    const res = await fetch(`/api/complaints/${complaintId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ worker_id: parseInt(workerId, 10) })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Assigned to ${data.complaint.assigned_worker_name}. Status: ${data.complaint.status}`, 'success');
      await loadStats();
      await loadComplaints();
    } else {
      showToast(data.error || 'Failed to assign worker', 'error');
    }
  } catch (err) {
    console.error('Error assigning worker:', err);
    showToast('Network error while assigning worker', 'error');
  }
}

async function advanceStatus(complaintId) {
  try {
    const res = await fetch(`/api/complaints/${complaintId}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Status updated to: ${data.complaint.status}`, 'success');
      await loadStats();
      await loadComplaints();
    } else {
      showToast(data.error || 'Could not advance status', 'error');
    }
  } catch (err) {
    console.error('Error advancing status:', err);
    showToast('Network error while advancing status', 'error');
  }
}

// ==========================================================================
// Form Submission
// ==========================================================================
complaintForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData(complaintForm);
  submitBtn.disabled = true;
  submitBtnText.textContent = 'Submitting...';

  try {
    const res = await fetch('/api/complaints', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Complaint ${data.complaint.ticket_no} submitted successfully!`, 'success');
      complaintForm.reset();
      clearPhotoPreview();

      // Reset priority radio to Low
      const lowRadio = complaintForm.querySelector('input[name="priority"][value="Low"]');
      if (lowRadio) lowRadio.checked = true;

      await loadStats();
      await loadComplaints();
    } else {
      showToast(data.error || 'Failed to submit complaint', 'error');
    }
  } catch (err) {
    console.error('Error submitting form:', err);
    showToast('Network error while submitting complaint', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtnText.textContent = 'Submit Maintenance Ticket';
  }
});

// ==========================================================================
// Photo Upload Preview & Drag-and-Drop
// ==========================================================================
photoInput.addEventListener('change', handleFileSelect);

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      previewImg.src = event.target.result;
      uploadPreview.classList.remove('hidden');
      uploadPlaceholder.classList.add('hidden');
    };
    reader.readAsDataURL(file);
  }
}

removePhotoBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  clearPhotoPreview();
});

function clearPhotoPreview() {
  photoInput.value = '';
  previewImg.src = '';
  uploadPreview.classList.add('hidden');
  uploadPlaceholder.classList.remove('hidden');
}

// Drag & drop handlers
['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
  }, false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
  }, false);
});

dropArea.addEventListener('drop', (e) => {
  const dt = e.dataTransfer;
  const files = dt.files;
  if (files.length > 0) {
    photoInput.files = files;
    handleFileSelect({ target: { files } });
  }
});

// ==========================================================================
// Photo Modal
// ==========================================================================
function openPhotoModal(filename, title) {
  modalFullImg.src = `/static/uploads/${filename}`;
  photoModalTitle.textContent = title || 'Attached Photo';
  photoModalCaption.textContent = title;
  photoModal.classList.remove('hidden');
}

closePhotoModalBtn.addEventListener('click', () => {
  photoModal.classList.add('hidden');
});

photoModal.addEventListener('click', (e) => {
  if (e.target === photoModal) {
    photoModal.classList.add('hidden');
  }
});

// ==========================================================================
// Filters & Interactive Dashboard Stat Cards
// ==========================================================================
function setupEventListeners() {
  userRoleBtn.addEventListener('click', () => setRole('user'));
  adminRoleBtn.addEventListener('click', () => setRole('admin'));

  filterStatus.addEventListener('change', () => {
    state.filters.status = filterStatus.value;
    updateActiveStatCard();
    loadComplaints();
  });

  filterPriority.addEventListener('change', () => {
    state.filters.priority = filterPriority.value;
    updateActiveStatCard();
    loadComplaints();
  });

  filterCategory.addEventListener('change', () => {
    state.filters.category = filterCategory.value;
    loadComplaints();
  });

  let searchTimeout;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.filters.search = searchInput.value;
      loadComplaints();
    }, 250);
  });

  resetFiltersBtn.addEventListener('click', () => {
    state.filters.status = 'All';
    state.filters.priority = 'All';
    state.filters.category = 'All';
    state.filters.search = '';

    filterStatus.value = 'All';
    filterPriority.value = 'All';
    filterCategory.value = 'All';
    searchInput.value = '';

    updateActiveStatCard();
    loadComplaints();
  });

  refreshStatsBtn.addEventListener('click', async () => {
    await loadStats();
    await loadComplaints();
    showToast('Refreshed data from server.', 'success');
  });

  // Clicking status cards filters the list
  document.querySelectorAll('.stat-card[data-filter-status]').forEach(card => {
    card.addEventListener('click', () => {
      const targetStatus = card.getAttribute('data-filter-status');
      if (state.filters.status === targetStatus) {
        state.filters.status = 'All';
        filterStatus.value = 'All';
      } else {
        state.filters.status = targetStatus;
        filterStatus.value = targetStatus;
      }
      updateActiveStatCard();
      loadComplaints();
    });
  });

  // Clicking priority cards filters the list
  document.querySelectorAll('.stat-card[data-filter-priority]').forEach(card => {
    card.addEventListener('click', () => {
      const targetPriority = card.getAttribute('data-filter-priority');
      if (state.filters.priority === targetPriority) {
        state.filters.priority = 'All';
        filterPriority.value = 'All';
      } else {
        state.filters.priority = targetPriority;
        filterPriority.value = targetPriority;
      }
      updateActiveStatCard();
      loadComplaints();
    });
  });
}

function updateActiveStatCard() {
  document.querySelectorAll('.stat-card').forEach(card => {
    card.classList.remove('active-filter');
    const s = card.getAttribute('data-filter-status');
    const p = card.getAttribute('data-filter-priority');
    if (s && s === state.filters.status) {
      card.classList.add('active-filter');
    }
    if (p && p === state.filters.priority) {
      card.classList.add('active-filter');
    }
  });
}

// ==========================================================================
// Utilities: Toast & HTML Escaping
// ==========================================================================
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type === 'success' ? 'toast-success' : type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️'}</span>
    <span>${escapeHtml(message)}</span>
  `;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Expose modal handler globally for inline onclick
window.openPhotoModal = openPhotoModal;
window.assignWorker = assignWorker;
window.advanceStatus = advanceStatus;
