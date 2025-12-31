const tabs = document.querySelectorAll(".tab");
const cards = document.querySelectorAll(".plan-card");

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        const network = tab.dataset.network;

        cards.forEach(card => {
            card.style.display =
                card.dataset.network === network ? "block" : "none";
        });
    });
});
