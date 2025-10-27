// Auto-detect backend base: we assume your proxy is bound to host:80
// const API_BASE = `${window.location.protocol}//${window.location.hostname}`;
const API_BASE = `${window.location.protocol}//${window.location.hostname}/api`;

// Simple session store (demo only)
const sessionKey = "demoUser";

function setSession(userObj) {
  localStorage.setItem(sessionKey, JSON.stringify(userObj));
  renderSession();
}
function clearSession() {
  localStorage.removeItem(sessionKey);
  renderSession();
}
function getSession() {
  const raw = localStorage.getItem(sessionKey);
  return raw ? JSON.parse(raw) : null;
}
function renderSession() {
  const s = getSession();
  const el = document.getElementById("sessionInfo");
  el.textContent = s ? `Logged in as: ${s.username} (id=${s.id})` : "Not logged in";
}

async function registerUser(username, password) {
  const res = await fetch(`${API_BASE}/users`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Registration failed");
  return data;
}

async function loginUser(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  return data;
}

async function listUsers() {
  const res = await fetch(`${API_BASE}/users`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Fetch users failed");
  return data;
}

// ---- wire up UI ----
document.addEventListener("DOMContentLoaded", () => {
  renderSession();

  const regForm = document.getElementById("registerForm");
  const regOut = document.getElementById("registerResult");
  regForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    regOut.textContent = "Registering...";
    const form = new FormData(regForm);
    try {
      const user = await registerUser(form.get("username"), form.get("password"));
      regOut.textContent = JSON.stringify(user, null, 2);
    } catch (err) {
      regOut.textContent = `Error: ${err.message}`;
    }
  });

  const loginForm = document.getElementById("loginForm");
  const loginOut = document.getElementById("loginResult");
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginOut.textContent = "Logging in...";
    const form = new FormData(loginForm);
    try {
      const user = await loginUser(form.get("username"), form.get("password"));
      setSession(user);
      loginOut.textContent = JSON.stringify(user, null, 2);
    } catch (err) {
      loginOut.textContent = `Error: ${err.message}`;
    }
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    clearSession();
  });

  const usersTbody = document.querySelector("#usersTable tbody");
  document.getElementById("refreshUsersBtn").addEventListener("click", async () => {
    usersTbody.innerHTML = "<tr><td colspan='3'>Loading...</td></tr>";
    try {
      const users = await listUsers();
      usersTbody.innerHTML = users.map(u =>
        `<tr><td>${u.id}</td><td>${u.username}</td><td>${u.created_at}</td></tr>`
      ).join("");
    } catch (err) {
      usersTbody.innerHTML = `<tr><td colspan="3">Error: ${err.message}</td></tr>`;
    }
  });
});
