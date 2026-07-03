// theme-init.js — виконується СИНХРОННО до рендерингу CSS.
// НЕ додавайте defer/async — це усуне мигання при перезавантаженні.
(function () {
  var saved = localStorage.getItem('theme');
  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.documentElement.classList.add('dark');
  }
}());
