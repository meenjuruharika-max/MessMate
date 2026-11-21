
const menuForm = document.getElementById("menuForm");
const message = document.getElementById("message");

async function loadMenus() {
    try {
        const response = await fetch("/api/menu/today");
        const data = await response.json();

        ["breakfast", "lunch", "snacks", "dinner"].forEach(meal => {
            const container = document.getElementById(meal);
            const items = data.menus[meal] || [];

            container.replaceChildren();

            if (items.length === 0) {
                container.textContent = "Not updated yet";
                return;
            }

            items.forEach(item => {
                const card = document.createElement("div");
                card.className = "food-entry";

                const food = document.createElement("p");
                food.textContent = item.food;

                const count = document.createElement("p");
                count.textContent =
                    `👍 ${item.confirmations} confirmations | ⚠️ ${item.reports} reports`;

                const confirmButton = document.createElement("button");
                confirmButton.textContent = "👍 Correct";

                confirmButton.onclick = () => updateMenu(item.id, "confirm");

                const reportButton = document.createElement("button");
                reportButton.textContent = "⚠️ Report";

                reportButton.onclick = () => updateMenu(item.id, "report");

                const suggestionBox = document.createElement("textarea");
                suggestionBox.placeholder =
                    "Suggest the correct food details...";

                const suggestionButton = document.createElement("button");
                suggestionButton.textContent = "Submit Correction";

                suggestionButton.onclick = () =>
                    submitCorrection(item.id, suggestionBox);

                card.append(
                    food,
                    count,
                    confirmButton,
                    reportButton,
                    suggestionBox,
                    suggestionButton
                );

                container.appendChild(card);
            });
        });

    } catch (error) {
        console.log("Could not load menu:", error);
    }
}

async function updateMenu(id, action) {
    try {
        const response = await fetch(
            `/api/menu/${id}/${action}`,
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) throw new Error(data.error);

        message.textContent = data.message;
        loadMenus();

    } catch (error) {
        message.textContent = error.message;
    }
}

async function submitCorrection(id, suggestionBox) {
    const suggestion = suggestionBox.value.trim();

    if (!suggestion) {
        message.textContent = "Please enter a correction.";
        return;
    }

    try {
        const response = await fetch(
            `/api/menu/${id}/suggest-correction`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ suggestion })
            }
        );

        const data = await response.json();

        if (!response.ok) throw new Error(data.error);

        message.textContent = data.message;
        suggestionBox.value = "";

    } catch (error) {
        message.textContent = error.message;
    }
}

menuForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const meal = document.getElementById("meal").value;
    const food = document.getElementById("food").value.trim();

    if (!meal || !food) {
        message.textContent = "Please enter all details.";
        return;
    }

    try {
        const response = await fetch("/api/menu", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ meal, food })
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error);

        message.textContent = data.message;
        menuForm.reset();
        loadMenus();

    } catch (error) {
        message.textContent = error.message;
    }
});

loadMenus();
