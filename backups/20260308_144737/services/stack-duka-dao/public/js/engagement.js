// public/js/engagement.js - Client-side JS for engagement

// Lazy loading for images (if any)
document.addEventListener('DOMContentLoaded', () => {
  // Example: Add social share buttons dynamically
  const shareBtn = document.createElement('button');
  shareBtn.className = 'btn btn-secondary mt-3';
  shareBtn.textContent = 'Share on X';
  shareBtn.onclick = () => {
    window.open('https://x.com/intent/tweet?text=Join Duka DAO - Marketplace for Emerging Markets!&url=' + window.location.href);
  };
  document.querySelector('.text-center.mt-4').appendChild(shareBtn);

  // Success message if redirected
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('success') === 'true') {
    alert('Signup successful! Welcome to Duka DAO.');
  }
});
