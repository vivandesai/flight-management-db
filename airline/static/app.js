// Keep the interface server-rendered; prevent accidental double-click submissions.
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener('submit', () => {
    form.querySelectorAll('button[type="submit"], button:not([type])').forEach(button => {
      button.disabled = true;
      button.textContent = 'Running…';
    });
  });
});
