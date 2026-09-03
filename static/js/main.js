/* ============================================================
   GTU-ITR R&D & IIC Portal — Main JavaScript
   ============================================================ */

(function () {
  'use strict';

  // ──────────────────────────────────────────────
  // DOM Ready
  // ──────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initDarkMode();
    initToasts();
    initAnimatedCounters();
    initTabs();
    initDropdowns();
    initConfirmDialogs();
    initTableSearch();
    initFileUpload();
    initCopyButtons();
    initAjaxForms();
    initCharts();
    initFlashMessages();
  });

  // ──────────────────────────────────────────────
  // 1. Sidebar Toggle
  // ──────────────────────────────────────────────
  function initSidebar() {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');

    if (!hamburger || !sidebar) return;

    hamburger.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('active');
    });

    if (backdrop) {
      backdrop.addEventListener('click', function () {
        sidebar.classList.remove('open');
        backdrop.classList.remove('active');
      });
    }

    // Close sidebar on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
      }
    });

    // Auto-close sidebar on link navigation for mobile screens
    const sidebarLinks = sidebar.querySelectorAll('.sidebar__link');
    sidebarLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth <= 768) {
          sidebar.classList.remove('open');
          if (backdrop) backdrop.classList.remove('active');
        }
      });
    });
  }

  // ──────────────────────────────────────────────
  // 2. Dark Mode
  // ──────────────────────────────────────────────
  function initDarkMode() {
    const toggle = document.getElementById('dark-mode-toggle');
    const stored = localStorage.getItem('theme');

    if (stored === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      if (toggle) toggle.setAttribute('data-active', 'true');
    }

    if (!toggle) return;

    toggle.addEventListener('click', function () {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        toggle.setAttribute('data-active', 'false');
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        toggle.setAttribute('data-active', 'true');
      }
      // Update icon
      updateDarkModeIcon(toggle, !isDark);
    });

    updateDarkModeIcon(toggle, document.documentElement.getAttribute('data-theme') === 'dark');
  }

  function updateDarkModeIcon(btn, isDark) {
    const icon = btn.querySelector('i');
    if (!icon) return;
    if (isDark) {
      icon.setAttribute('data-lucide', 'sun');
    } else {
      icon.setAttribute('data-lucide', 'moon');
    }
    if (window.lucide) lucide.createIcons();
  }

  // ──────────────────────────────────────────────
  // 3. Toast Notifications
  // ──────────────────────────────────────────────
  let toastContainer;

  function initToasts() {
    toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.className = 'toast-container';
      document.body.appendChild(toastContainer);
    }
  }

  window.showToast = function (type, title, message, duration) {
    if (!toastContainer) initToasts();
    duration = duration || 5000;

    const iconMap = {
      success: 'check-circle',
      error: 'x-circle',
      warning: 'alert-triangle',
      info: 'info'
    };

    const toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.innerHTML =
      '<i data-lucide="' + (iconMap[type] || 'info') + '" class="toast__icon"></i>' +
      '<div class="toast__content">' +
      '  <div class="toast__title">' + escapeHtml(title) + '</div>' +
      '  <div class="toast__message">' + escapeHtml(message) + '</div>' +
      '</div>' +
      '<button class="toast__close" aria-label="Close">' +
      '  <i data-lucide="x" style="width:14px;height:14px"></i>' +
      '</button>';

    toastContainer.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    // Close button
    toast.querySelector('.toast__close').addEventListener('click', function () {
      removeToast(toast);
    });

    // Auto remove
    setTimeout(function () { removeToast(toast); }, duration);
  };

  function removeToast(toast) {
    toast.classList.add('removing');
    setTimeout(function () { toast.remove(); }, 300);
  }

  function initFlashMessages() {
    const flashes = document.querySelectorAll('[data-flash]');
    flashes.forEach(function (el) {
      const type = el.dataset.flashType || 'info';
      const msg = el.dataset.flash;
      window.showToast(type, capitalize(type), msg);
      el.remove();
    });
  }

  // ──────────────────────────────────────────────
  // 4. Animated Counters
  // ──────────────────────────────────────────────
  function initAnimatedCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;

    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });

    counters.forEach(function (el) { observer.observe(el); });
  }

  function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1200;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = Math.round(eased * target);
      el.textContent = current.toLocaleString();
      if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
  }

  // ──────────────────────────────────────────────
  // 5. Tabs
  // ──────────────────────────────────────────────
  function initTabs() {
    document.querySelectorAll('.tabs').forEach(function (tabBar) {
      const buttons = tabBar.querySelectorAll('.tab-btn');
      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          const target = btn.dataset.tab;
          const parent = tabBar.parentElement;

          // Deactivate all
          buttons.forEach(function (b) { b.classList.remove('active'); });
          parent.querySelectorAll('.tab-pane').forEach(function (p) { p.classList.remove('active'); });

          // Activate current
          btn.classList.add('active');
          const pane = parent.querySelector('#' + target);
          if (pane) pane.classList.add('active');
        });
      });
    });
  }

  // ──────────────────────────────────────────────
  // 6. Dropdowns
  // ──────────────────────────────────────────────
  function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(function (dd) {
      const trigger = dd.querySelector('.dropdown__trigger');
      if (!trigger) return;

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        // Close others
        document.querySelectorAll('.dropdown.open').forEach(function (other) {
          if (other !== dd) other.classList.remove('open');
        });
        dd.classList.toggle('open');
      });
    });

    document.addEventListener('click', function () {
      document.querySelectorAll('.dropdown.open').forEach(function (dd) {
        dd.classList.remove('open');
      });
    });
  }

  // ──────────────────────────────────────────────
  // 7. Confirm Dialogs
  // ──────────────────────────────────────────────
  function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        const msg = el.dataset.confirm || 'Are you sure you want to proceed?';
        if (!confirm(msg)) {
          e.preventDefault();
        }
      });
    });
  }

  // ──────────────────────────────────────────────
  // 8. Table Search / Filter
  // ──────────────────────────────────────────────
  function initTableSearch() {
    document.querySelectorAll('[data-table-search]').forEach(function (input) {
      const tableId = input.dataset.tableSearch;
      const table = document.getElementById(tableId);
      if (!table) return;

      input.addEventListener('input', function () {
        const query = input.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function (row) {
          const text = row.textContent.toLowerCase();
          row.style.display = text.includes(query) ? '' : 'none';
        });
      });
    });
  }

  // ──────────────────────────────────────────────
  // 9. File Upload Drag-and-Drop
  // ──────────────────────────────────────────────
  function initFileUpload() {
    document.querySelectorAll('.upload-zone').forEach(function (zone) {
      const input = zone.querySelector('input[type="file"]');
      const preview = zone.querySelector('.upload-zone__preview');

      if (!input) return;

      zone.addEventListener('click', function () { input.click(); });

      zone.addEventListener('dragover', function (e) {
        e.preventDefault();
        zone.classList.add('dragover');
      });

      zone.addEventListener('dragleave', function () {
        zone.classList.remove('dragover');
      });

      zone.addEventListener('drop', function (e) {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
          input.files = e.dataTransfer.files;
          showFilePreview(zone, input.files);
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });

      input.addEventListener('change', function () {
        showFilePreview(zone, input.files);
      });
    });
  }

  function showFilePreview(zone, files) {
    let preview = zone.querySelector('.upload-zone__file-info');
    if (!preview) {
      preview = document.createElement('div');
      preview.className = 'upload-zone__file-info mt-4';
      zone.appendChild(preview);
    }

    if (files.length === 0) {
      preview.innerHTML = '';
      return;
    }

    let html = '';
    Array.from(files).forEach(function (file) {
      const size = (file.size / 1024).toFixed(1);
      html += '<div class="flex items-center gap-3 mt-2">' +
        '<i data-lucide="file-text" style="width:20px;height:20px;color:var(--primary)"></i>' +
        '<span class="text-sm font-medium">' + escapeHtml(file.name) + '</span>' +
        '<span class="text-xs text-muted">(' + size + ' KB)</span>' +
        '</div>';
    });

    preview.innerHTML = html;
    if (window.lucide) lucide.createIcons();
  }

  // ──────────────────────────────────────────────
  // 10. Copy to Clipboard
  // ──────────────────────────────────────────────
  function initCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const target = document.getElementById(btn.dataset.copy);
        const text = target ? target.textContent || target.value : '';

        navigator.clipboard.writeText(text).then(function () {
          window.showToast('success', 'Copied!', 'Content copied to clipboard.');
          btn.classList.add('copied');
          setTimeout(function () { btn.classList.remove('copied'); }, 2000);
        }).catch(function () {
          window.showToast('error', 'Failed', 'Could not copy to clipboard.');
        });
      });
    });
  }

  // ──────────────────────────────────────────────
  // 11. AJAX Form Submissions (AI Tools)
  // ──────────────────────────────────────────────
  function initAjaxForms() {
    document.querySelectorAll('form[data-ajax]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const resultContainer = document.getElementById(form.dataset.resultTarget);
        const loadingEl = form.closest('.card')?.querySelector('.loading-overlay') ||
                         document.getElementById(form.dataset.loading);

        // Show loading
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.dataset.originalText = submitBtn.innerHTML;
          submitBtn.innerHTML = '<span class="spinner spinner--sm"></span> Processing...';
        }
        if (loadingEl) loadingEl.style.display = 'flex';

        const formData = new FormData(form);
        const csrfToken = document.querySelector('meta[name="csrf-token"]');

        fetch(form.action, {
          method: 'POST',
          body: formData,
          headers: csrfToken ? { 'X-CSRFToken': csrfToken.content } : {}
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.success && resultContainer) {
              resultContainer.innerHTML = data.html || '<div class="ai-result__body">' + escapeHtml(data.result || '') + '</div>';
              resultContainer.style.display = 'block';
              resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              window.showToast('success', 'Success', data.message || 'AI processing complete!');
            } else if (data.error) {
              window.showToast('error', 'Error', data.error);
            }
          })
          .catch(function (err) {
            window.showToast('error', 'Error', 'Something went wrong. Please try again.');
            console.error(err);
          })
          .finally(function () {
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.innerHTML = submitBtn.dataset.originalText;
            }
            if (loadingEl) loadingEl.style.display = 'none';
          });
      });
    });
  }

  // ──────────────────────────────────────────────
  // 12. Chart.js Initialization
  // ──────────────────────────────────────────────
  function initCharts() {
    // Proposals by Status (Donut)
    const statusCtx = document.getElementById('proposalStatusChart');
    if (statusCtx && window.Chart) {
      new Chart(statusCtx, {
        type: 'doughnut',
        data: {
          labels: ['Approved', 'Pending', 'Rejected', 'Draft'],
          datasets: [{
            data: [35, 25, 10, 15],
            backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6b7280'],
            borderWidth: 0,
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '70%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 16,
                usePointStyle: true,
                pointStyleWidth: 8,
                font: { family: "'Inter', sans-serif", size: 12 }
              }
            }
          }
        }
      });
    }

    // Publications Trend (Bar)
    const trendCtx = document.getElementById('publicationTrendChart');
    if (trendCtx && window.Chart) {
      new Chart(trendCtx, {
        type: 'bar',
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          datasets: [{
            label: 'Publications',
            data: [8, 12, 6, 15, 10, 18],
            backgroundColor: 'rgba(0, 51, 102, 0.8)',
            borderRadius: 6,
            borderSkipped: false,
            barThickness: 28
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(0,0,0,.06)' },
              ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
            },
            x: {
              grid: { display: false },
              ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
            }
          }
        }
      });
    }
  }

  // ──────────────────────────────────────────────
  // 13. Form Validation Helpers
  // ──────────────────────────────────────────────
  window.validateForm = function (form) {
    let isValid = true;
    form.querySelectorAll('[required]').forEach(function (field) {
      if (!field.value.trim()) {
        field.classList.add('is-invalid');
        isValid = false;

        // Add error message if not exists
        if (!field.parentElement.querySelector('.form-error')) {
          const err = document.createElement('div');
          err.className = 'form-error';
          err.textContent = 'This field is required.';
          field.parentElement.appendChild(err);
        }
      } else {
        field.classList.remove('is-invalid');
        const err = field.parentElement.querySelector('.form-error');
        if (err) err.remove();
      }
    });
    return isValid;
  };

  // Clear validation on input
  document.addEventListener('input', function (e) {
    if (e.target.classList.contains('is-invalid')) {
      e.target.classList.remove('is-invalid');
      const err = e.target.parentElement.querySelector('.form-error');
      if (err) err.remove();
    }
  });

  // ──────────────────────────────────────────────
  // 14. Modal Helpers
  // ──────────────────────────────────────────────
  window.openModal = function (id) {
    const overlay = document.getElementById(id);
    if (overlay) {
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      // Lazy load any iframe inside this modal to prevent auto-downloads on reload
      overlay.querySelectorAll('iframe[data-src]').forEach(function (iframe) {
        if (!iframe.getAttribute('src')) {
          iframe.src = iframe.dataset.src;
        }
      });
    }
  };

  window.closeModal = function (id) {
    const overlay = document.getElementById(id);
    if (overlay) {
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  // Close modal on backdrop click
  document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
      e.target.classList.remove('active');
      document.body.style.overflow = '';
    }
  });

  // Close modal on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(function (m) {
        m.classList.remove('active');
      });
      document.body.style.overflow = '';
    }
  });

  // ──────────────────────────────────────────────
  // Utilities
  // ──────────────────────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

})();
