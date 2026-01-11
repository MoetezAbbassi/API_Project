(function () {
  const apiUrlLabel = document.getElementById("apiUrlLabel");
  if (apiUrlLabel) apiUrlLabel.textContent = window.API_URL;

  // If already logged in, go to app
  if (window.api.getToken()) {
    window.location.href = "app.html";
    return;
  }

  const tabLogin = document.getElementById("tabLogin");
  const tabRegister = document.getElementById("tabRegister");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const authMsg = document.getElementById("authMsg");
  const goRegister = document.getElementById("goRegister");
  const goLogin = document.getElementById("goLogin");

  function showMsg(text, type = "error") {
    authMsg.textContent = text;
    authMsg.className = `auth-msg ${type}`;
    authMsg.classList.remove("hidden");
  }

  function hideMsg() {
    authMsg.classList.add("hidden");
  }

  function setMode(mode) {
    hideMsg();
    if (mode === "login") {
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");
      loginForm.classList.remove("hidden");
      registerForm.classList.add("hidden");
    } else {
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");
      registerForm.classList.remove("hidden");
      loginForm.classList.add("hidden");
    }
  }

  tabLogin.addEventListener("click", () => setMode("login"));
  tabRegister.addEventListener("click", () => setMode("register"));
  goRegister.addEventListener("click", (e) => (e.preventDefault(), setMode("register")));
  goLogin.addEventListener("click", (e) => (e.preventDefault(), setMode("login")));

  // LOGIN HANDLER
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideMsg();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    if (!username || !password) {
      showMsg("Username and password required", "error");
      return;
    }

    const res = await window.api.login({ username, password });
    
    if (!res?.success) {
      showMsg(res?.message || "Login failed", "error");
      return;
    }

    const token = res?.data?.token;
    if (!token) {
      showMsg("Login succeeded but token missing from response", "error");
      return;
    }

    window.api.setToken(token, true);
    window.location.href = "app.html";
  });

  // REGISTER HANDLER
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideMsg();

    const name = document.getElementById("regName").value.trim();
    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;

    if (!username || !email || !password) {
      showMsg("Username, email, and password required", "error");
      return;
    }

    const res = await window.api.register({ username, email, password, name });
    
    if (!res?.success) {
      showMsg(res?.message || "Registration failed", "error");
      return;
    }

    showMsg("Account created! Please login.", "success");
    setMode("login");
    document.getElementById("loginUsername").value = username;
  });
})();
