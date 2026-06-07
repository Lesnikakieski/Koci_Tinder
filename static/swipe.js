let currentCat = null;

const statusEl = document.getElementById("status");
const catImg = document.getElementById("cat-image");
const leftBtn = document.getElementById("left-btn");
const rightBtn = document.getElementById("right-btn");

async function loadCat() {
    statusEl.textContent = "Ładowanie kota...";
    catImg.hidden = true;
    const response = await fetch("/api/cat/random");
    const data = await response.json();
    if (!response.ok) {
        statusEl.textContent = data.error || "Błąd ładowania kota.";
        return;
    }
    currentCat = data;
    catImg.src = data.url;
    catImg.hidden = false;
    statusEl.textContent = "Podoba Ci się ten kot?";
}

async function sendSwipe(direction) {
    if (!currentCat) return;
    const response = await fetch("/api/swipes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            cat_id: currentCat.cat_id,
            cat_url: currentCat.url,
            direction: direction
        })
    });
    const data = await response.json();
    if (!response.ok) {
        statusEl.textContent = data.error || "Nie udało się zapisać decyzji.";
        return;
    }
    await loadCat();
}

leftBtn.addEventListener("click", () => sendSwipe("left"));
rightBtn.addEventListener("click", () => sendSwipe("right"));
loadCat();
