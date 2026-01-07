// Scroll to top
const scrollBtn = document.getElementById("scrollTopBtn");
if (scrollBtn) {
    window.addEventListener("scroll", () => {
        if (window.scrollY > 250) {
            scrollBtn.style.display = "flex";
        } else {
            scrollBtn.style.display = "none";
        }
    });

    scrollBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
}

// Simple horizontal carousel for categories
document.querySelectorAll(".carousel-arrow").forEach((btn) => {
    btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const direction = btn.dataset.direction;
        const container = document.getElementById(targetId);
        if (!container) return;

        const amount = container.clientWidth * 0.9;
        container.scrollBy({
            left: direction === "next" ? amount : -amount,
            behavior: "smooth",
        });
    });
});

// Tabs (home collection + product details tabs)
function setupTabs(scope) {
    const tabButtons = scope.querySelectorAll(".tab-button");
    const tabPanels = scope.querySelectorAll(".tab-panel");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;
            tabButtons.forEach((b) => b.classList.remove("active"));
            tabPanels.forEach((panel) => panel.classList.remove("active"));
            btn.classList.add("active");
            const panel = scope.querySelector(`#tab-${target}`);
            if (panel) panel.classList.add("active");
        });
    });
}

document.querySelectorAll(".collection-section, .product-description-tabs")
    .forEach(setupTabs);

// FAQ accordion
document.querySelectorAll(".faq-item").forEach((item) => {
    const q = item.querySelector(".faq-question");
    q.addEventListener("click", () => {
        item.classList.toggle("active");
    });
});

// Quantity selector
const qtyInput = document.getElementById("qtyInput");
if (qtyInput) {
    document.querySelectorAll(".qty-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            let value = parseInt(qtyInput.value || "1", 10);
            if (btn.dataset.action === "plus") value++;
            if (btn.dataset.action === "minus") value = Math.max(1, value - 1);
            qtyInput.value = value;
        });
    });
}

// Gallery thumbnails
const mainImage = document.getElementById("mainProductImage");
if (mainImage) {
    const thumbs = document.querySelectorAll(".gallery-thumbs .thumb");
    thumbs.forEach((thumb) => {
        thumb.addEventListener("click", () => {
            thumbs.forEach((t) => t.classList.remove("active"));
            thumb.classList.add("active");
            const src = thumb.dataset.img;
            if (src) mainImage.src = src;
        });
    });
}

// ✅ Unified desktop + mobile nav toggle
document.addEventListener("DOMContentLoaded", () => {
    const navToggle = document.getElementById("navToggle");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const navLinks = document.getElementById("navLinks");

    if (navLinks) {
        const toggleMenu = () => navLinks.classList.toggle("open");

        if (navToggle) navToggle.addEventListener("click", toggleMenu);
        if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", toggleMenu);

        // Optional: close menu when a link is tapped
        navLinks.querySelectorAll("a").forEach(link =>
            link.addEventListener("click", () => navLinks.classList.remove("open"))
        );
    }
});
