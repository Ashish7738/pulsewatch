/* Handles the login and register forms (index.html, register.html). */
(function () {
  redirectIfAuthed();

  const form = document.getElementById('auth-form');
  const errorBox = document.getElementById('form-error');
  const submit = document.getElementById('submit-btn');
  const mode = form.dataset.mode; // "login" | "register"

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.hidden = true;

    const email = form.email.value.trim();
    const password = form.password.value;

    if (mode === 'register') {
      if (password.length < 8) return showError('Password must be at least 8 characters.');
      if (password !== form.confirm.value) return showError('Passwords do not match.');
    }

    submit.disabled = true;
    const idleLabel = submit.textContent;
    submit.textContent = mode === 'register' ? 'Creating account…' : 'Logging in…';

    try {
      const data = await apiFetch(`/auth/${mode}`, {
        method: 'POST',
        body: { email, password },
        auth: false,
      });
      saveSession(data.access_token, data.email || email);
      window.location.replace('dashboard.html');
    } catch (err) {
      showError(err.message);
      submit.disabled = false;
      submit.textContent = idleLabel;
    }
  });
})();
