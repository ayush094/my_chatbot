const API = {
    loginEmployee: (data) => fetch('/api/auth/employee/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
    loginManager: (data) => fetch('/api/auth/manager/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }),
    chat: (msg) => fetchWithAuth('/api/chat/', { method: 'POST', body: JSON.stringify({ message: msg }) }),
    getLeaves: () => fetchWithAuth('/api/leaves/', { method: 'GET' }),
    getPendingLeaves: () => fetchWithAuth('/api/leaves/pending/', { method: 'GET' }),
    applyLeave: (data) => fetchWithAuth('/api/leaves/', { method: 'POST', body: JSON.stringify(data) }),
    sendLeaveAction: (cmd) => fetchWithAuth('/api/leaves/action/', { method: 'POST', body: JSON.stringify({ command: cmd }) })
};

async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        logout();
        throw new Error("Session expired. Please login again.");
    }
    return response;
}

// State Management
let user = JSON.parse(localStorage.getItem('user')) || null;
let currentTab = 'chat';

// UI Logic
function updateUI() {
    if (!user) {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('app-shell').classList.add('hidden');
    } else {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('app-shell').classList.remove('hidden');
        document.getElementById('user-email').textContent = user.email;
        document.getElementById('user-role-badge').textContent = user.role;

        // Hide/Show Manager specific items
        const managerOnly = document.querySelectorAll('.manager-only');
        managerOnly.forEach(el => el.classList.toggle('hidden', user.role !== 'manager'));

        renderCurrentTab();
    }
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.tab === tab);
    });
    renderCurrentTab();
}

async function renderCurrentTab() {
    const pane = document.getElementById('content-area');
    pane.innerHTML = ''; // Clear

    if (currentTab === 'chat') {
        renderChat(pane);
    } else if (currentTab === 'leaves') {
        renderLeaveDashboard(pane);
    } else if (currentTab === 'manager-leaves') {
        renderManagerDashboard(pane);
    }
}

function renderChat(container) {
    container.innerHTML = `
        <div class="content-pane">
            <div class="chat-window glass">
                <div id="chat-messages" class="chat-messages">
                    <div class="msg ai">Hello! I am your AI assistant. How can I help you?</div>
                </div>
                <div class="chat-input">
                    <input type="text" id="chat-input-field" placeholder="Ask about employees, apply for leave, or approve requests...">
                    <button class="btn-primary" onclick="handleChatSend()">↑</button>
                </div>
            </div>
        </div>
    `;
    const input = document.getElementById('chat-input-field');
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleChatSend(); });
}

async function handleChatSend() {
    const input = document.getElementById('chat-input-field');
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    input.value = '';

    try {
        const res = await API.chat(text);
        const data = await res.json();
        appendMessage(data.answer, 'ai');

        // If it was a leave action, refresh lists if they are open
        if (text.toLowerCase().includes('leave')) {
            // Optional: notify user to check leave tab
        }
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

function appendMessage(text, side) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `msg ${side}`;
    div.textContent = text;
    container.appendChild(div);

    // Improved auto-scroll
    setTimeout(() => {
        div.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 50);
}

async function renderLeaveDashboard(container) {
    container.innerHTML = `
        <div class="content-pane">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h2>My Leave Requests</h2>
                <button class="btn-primary" style="width:auto; padding:0.5rem 1rem;" onclick="showApplyModal()">Apply New</button>
            </div>
            <div class="glass" style="border-radius:1rem; padding:1rem; overflow-x:auto;">
                <table id="leave-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Start</th>
                            <th>End</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="leave-list-body">
                        <tr><td colspan="4" style="text-align:center">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    try {
        const res = await API.getLeaves();
        const leaves = await res.json();
        const body = document.getElementById('leave-list-body');
        body.innerHTML = leaves.length ? leaves.map(l => `
            <tr>
                <td>${l.leave_type}</td>
                <td>${l.start_date}</td>
                <td>${l.end_date}</td>
                <td><span class="status-badge status-${l.status}">${l.status}</span></td>
            </tr>
        `).join('') : '<tr><td colspan="4" style="text-align:center">No leaves found</td></tr>';
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

async function renderManagerDashboard(container) {
    container.innerHTML = `
        <div class="content-pane">
            <h2 style="margin-bottom:2rem;">Pending Employee Leaves</h2>
            <div class="glass" style="border-radius:1rem; padding:1rem; overflow-x:auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Start</th>
                            <th>End</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="manager-leave-body">
                        <tr><td colspan="5" style="text-align:center">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
            <div style="margin-top:2rem;" class="glass p-2">
                <p style="color:var(--text-muted); font-size:0.9rem;">Tip: You can also approve/reject directly from the chat using "approve leave id 3"</p>
            </div>
        </div>
    `;

    try {
        const res = await API.getPendingLeaves();
        const leaves = await res.json();
        const body = document.getElementById('manager-leave-body');
        body.innerHTML = leaves.length ? leaves.map(l => `
            <tr>
                <td>#${l.id}</td>
                <td>${l.start_date}</td>
                <td>${l.end_date}</td>
                <td>${l.leave_type}</td>
                <td style="display:flex; gap:0.5rem;">
                    <button onclick="handleLeaveAction('approve', ${l.id})" class="btn-primary" style="background:var(--success); padding:0.3rem 0.6rem; font-size:0.8rem;">Approve</button>
                    <button onclick="handleLeaveAction('reject', ${l.id})" class="btn-primary" style="background:var(--danger); padding:0.3rem 0.6rem; font-size:0.8rem;">Reject</button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="5" style="text-align:center">No pending leaves</td></tr>';
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

async function handleLeaveAction(action, id) {
    const cmd = `${action} leave id ${id}`;
    try {
        const res = await API.sendLeaveAction(cmd);
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, 'success');
            renderManagerDashboard(document.getElementById('content-area'));
        } else {
            showToast(data.error, 'danger');
        }
    } catch (err) {
        showToast(err.message, 'danger');
    }
}

// Auth Handlers
async function handleLogin(role) {
    const email = document.getElementById(`${role}-email`).value;
    const password = role === 'manager' ? document.getElementById('manager-password').value : null;

    try {
        const res = role === 'manager'
            ? await API.loginManager({ email, password })
            : await API.loginEmployee({ email });

        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);

            // Decode role from token or use the one we know
            // Simple approach: we know the role we just used to login
            user = { email, role: role };
            localStorage.setItem('user', JSON.stringify(user));

            showToast("Login Successful", "success");
            updateUI();
        } else {
            showToast(data.error, "danger");
        }
    } catch (err) {
        showToast(err.message, "danger");
    }
}

function logout() {
    localStorage.clear();
    user = null;
    updateUI();
}

function showToast(msg, type) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initial Run
window.onload = updateUI;
