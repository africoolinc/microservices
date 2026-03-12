// StackForge E-Commerce App
document.addEventListener('DOMContentLoaded', () => {
    console.log('StackForge E-Commerce Platform Initialized');

    // Smooth scroll for nav links
    document.querySelectorAll('.nav-links a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Simple observer for bento items reveal
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.bento-item, .pricing-card').forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        observer.observe(item);
    });

    // Newsletter form handling
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = e.target.querySelector('input').value;
            if (email) {
                alert(`Thank you for subscribing, ${email}! You'll be the first to know about new agentic features.`);
                e.target.reset();
            }
        });
    }

    // Hero visual interaction
    const heroVisual = document.querySelector('.hero-visual');
    if (heroVisual) {
        document.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
            heroVisual.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
        });
    }
});
