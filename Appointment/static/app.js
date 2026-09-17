const qs = (s) => document.querySelector(s);

function humanizeStatus(status) {
  const map = {
    scheduled: 'Scheduled',
    completed: 'Completed',
    cancelled: 'Cancelled',
  };
  return map[status] || status;
}

async function fetchAppointments() {
  const date = qs('#filter-date').value;
  const status = qs('#filter-status').value;
  const params = new URLSearchParams();
  if (date) params.set('date', date);
  if (status) params.set('status', status);
  const res = await fetch('/api/appointments?' + params.toString());
  return res.json();
}

function renderAppointments(list) {
  const board = qs('#board');
  board.innerHTML = '';
  if (!list.length) {
    board.innerHTML = '<p>No appointments yet. Add your first one to get started.</p>';
    return;
  }
  list.forEach((a, idx) => {
    const card = document.createElement('div');
    card.className = 'card ' + a.status;
    card.style.animationDelay = (idx * 45) + 'ms';
    card.innerHTML = `
      <div class="row">
        <h3>${a.title}</h3>
        <div class="status-badge">${humanizeStatus(a.status)}</div>
      </div>
      <p class="meta">${a.date} ${a.start_time} - ${a.end_time}</p>
      <p>${a.description || 'No notes added.'}</p>
      <div class="actions">
        <button data-id="${a.id}" class="edit btn-outlined" aria-label="Edit appointment"><span class="material-icons">edit</span></button>
        ${a.status === 'scheduled' ? `<button data-id="${a.id}" class="complete btn-outlined" aria-label="Mark as complete"><span class="material-icons">done</span></button>` : ''}
        ${a.status !== 'cancelled' ? `<button data-id="${a.id}" class="cancel btn-outlined" aria-label="Cancel appointment"><span class="material-icons">cancel</span></button>` : ''}
      </div>
    `;
    board.appendChild(card);
  });
  // re-init ripples for new buttons
  if (typeof initRipples === 'function') initRipples();
}

async function loadAndRender() {
  const list = await fetchAppointments();
  renderAppointments(list);
}

function showForm(mode='add', appt=null) {
  qs('#form-error').textContent = '';
  qs('#form-modal').classList.remove('hidden');
  qs('#form-title').textContent = mode === 'add' ? 'Add a new appointment' : 'Edit appointment';
  qs('#appt-id').value = appt ? appt.id : '';
  qs('#title').value = appt ? appt.title : '';
  qs('#description').value = appt ? appt.description : '';
  qs('#date').value = appt ? appt.date : '';
  qs('#start_time').value = appt ? appt.start_time : '';
  qs('#end_time').value = appt ? appt.end_time : '';
  qs('#status').value = appt ? appt.status : 'scheduled';
}

function hideForm() { qs('#form-modal').classList.add('hidden'); }

async function postForm(e) {
  e.preventDefault();
  const id = qs('#appt-id').value;
  const payload = {
    title: qs('#title').value.trim(),
    description: qs('#description').value.trim(),
    date: qs('#date').value,
    start_time: qs('#start_time').value,
    end_time: qs('#end_time').value,
    status: qs('#status').value,
  };
  try {
    let res;
    if (id) {
      res = await fetch('/api/appointments/' + id, {method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    } else {
      res = await fetch('/api/appointments', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    }
    if (!res.ok) {
      const err = await res.json();
      qs('#form-error').textContent = err.error || 'Error';
      return;
    }
    hideForm();
    await loadAndRender();
  } catch (err) {
    qs('#form-error').textContent = err.message;
  }
}

document.addEventListener('click', async (ev) => {
  // normalize to the nearest button element so clicks on icons work
  const btn = ev.target.closest && ev.target.closest('button');
  if (btn) {
    const id = btn.dataset.id;
    if (btn.id === 'btn-refresh') { await loadAndRender(); return; }
    if (btn.id === 'btn-add') { showForm('add', null); return; }
    if (btn.id === 'btn-cancel') { hideForm(); return; }
    if (btn.classList.contains('edit')) {
      const res = await fetch('/api/appointments');
      const list = await res.json();
      const appt = list.find(x => String(x.id) === String(id));
      showForm('edit', appt);
      return;
    }
    if (btn.classList.contains('complete')) {
      const res = await fetch('/api/appointments/' + id, {method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status:'completed'})});
      if (!res.ok) {
        try {
          const err = await res.json();
          alert(err.error || 'Could not mark this appointment as complete.');
        } catch (e) {
          alert('Could not mark this appointment as complete.');
        }
        return;
      }
      await loadAndRender();
      return;
    }
    if (btn.classList.contains('cancel')) {
      if (!confirm('Are you sure you want to cancel this appointment?')) return;
      await fetch('/api/appointments/' + id, {method: 'DELETE'});
      await loadAndRender();
      return;
    }
  } else {
    // non-button clicks (ignore)
  }
});

document.addEventListener('DOMContentLoaded', () => {
  qs('#appt-form').addEventListener('submit', postForm);
  qs('#btn-refresh').addEventListener('click', loadAndRender);
  qs('#filter-date').addEventListener('change', loadAndRender);
  qs('#filter-status').addEventListener('change', loadAndRender);
  const clearBtn = qs('#btn-clear-filters');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      qs('#filter-date').value = '';
      qs('#filter-status').value = '';
      loadAndRender();
    });
  }
  loadAndRender();
});

// Material ripple effect for buttons
function addRipple(e){
  const btn = e.currentTarget;
  const rect = btn.getBoundingClientRect();
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  const size = Math.max(rect.width, rect.height);
  ripple.style.width = ripple.style.height = size + 'px';
  const x = e.clientX - rect.left - size/2;
  const y = e.clientY - rect.top - size/2;
  ripple.style.left = x + 'px';
  ripple.style.top = y + 'px';
  btn.style.position = btn.style.position || 'relative';
  btn.appendChild(ripple);
  setTimeout(()=> ripple.remove(), 600);
}

function initRipples(){
  document.querySelectorAll('button').forEach(b=>{
    b.addEventListener('click', addRipple);
    b.style.overflow = 'hidden';
  });
}

// init ripples after DOM ready
document.addEventListener('DOMContentLoaded', initRipples);
