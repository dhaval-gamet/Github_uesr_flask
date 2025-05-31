document.getElementById("scrape-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {};
    for (const [key, value] of formData.entries()) {
        if (value !== "") data[key] = value;
    }

    const response = await fetch("/api/scrape", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    const result = await response.json();

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = `<h3>${result.total_users} यूज़र्स पाए गए (${result.new_users} नए)</h3><ul>${result.users.map(u => `<li><a href="${u.html_url}" target="_blank">${u.login}</a></li>`).join('')}</ul>`;
});
