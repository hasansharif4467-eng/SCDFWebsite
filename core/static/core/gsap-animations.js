document.addEventListener("DOMContentLoaded", function () {
    // Respect accessibility preferences.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }

    // Stop safely if GSAP libraries are unavailable.
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
        console.warn("GSAP or ScrollTrigger could not be loaded.");
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Hero entrance animation.
    const heroTimeline = gsap.timeline({
        defaults: {
            ease: "power3.out"
        }
    });

    heroTimeline
        .from(".hero-content .hero-subtitle", {
            opacity: 0,
            y: 25,
            duration: 0.7
        })
        .from(".hero-content h1", {
            opacity: 0,
            y: 40,
            duration: 1
        }, "-=0.35")
        .from(".hero-content .hero-description", {
            opacity: 0,
            y: 25,
            duration: 0.7
        }, "-=0.5")
        .from(".hero-content .hero-buttons", {
            opacity: 0,
            y: 20,
            duration: 0.6
        }, "-=0.35");

    // Scroll reveal for section headings and content.
    const revealElements = gsap.utils.toArray(
        ".section-heading, .about-content, .training-content, " +
        ".career-content, .contact-intro, .contact-form"
    );

    revealElements.forEach(function (element) {
        gsap.from(element, {
            opacity: 0,
            y: 45,
            duration: 0.85,
            ease: "power2.out",
            scrollTrigger: {
                trigger: element,
                start: "top 88%",
                once: true
            }
        });
    });
});


// Floating Donate Button - Auto-select Donation
document.addEventListener("DOMContentLoaded", function () {
    const donateButton = document.querySelector(".floating-donate");
    const subjectField = document.querySelector("#contact-subject");

    if (donateButton && subjectField) {
        donateButton.addEventListener("click", function () {
            subjectField.value = "donation";
            subjectField.dispatchEvent(new Event("change", { bubbles: true }));
        });
    }
});
