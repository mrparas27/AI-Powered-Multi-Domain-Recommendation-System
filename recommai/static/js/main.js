const form = document.querySelector("[data-recommend-form]");
const results = document.querySelector("[data-results]");

if (form && results) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const params = new URLSearchParams(new FormData(form));
    results.innerHTML = '<p class="loading">Finding best matches...</p>';
    try {
      const response = await fetch(`/api/v1/recommendations/?${params.toString()}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Recommendation failed");
      results.innerHTML = renderRows(payload.results, payload.domain);
    } catch (error) {
      results.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
    }
  });
}

document.querySelectorAll("[data-live-form]").forEach((liveForm) => {
  const output = liveForm.parentElement.querySelector("[data-live-results]");
  liveForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const endpoint = liveForm.dataset.endpoint;
    const kind = liveForm.dataset.kind;
    const params = new URLSearchParams(new FormData(liveForm));
    output.innerHTML = '<p class="loading">Checking live source and fallback catalog...</p>';
    try {
      const response = await fetch(`${endpoint}?${params.toString()}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Live search failed");
      const list = payload.results || payload.movies || payload.tracks || [];
      const message = payload.notice || payload.warning || "";
      const badge = message
        ? `<p class="source-badge ${payload.warning ? "warning" : ""}">${escapeHtml(payload.source || "Local")}: ${escapeHtml(message)}</p>`
        : `<p class="source-badge">${escapeHtml(payload.source || "Local")}</p>`;
      output.innerHTML = badge + renderRows(list, kind);
    } catch (error) {
      output.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
    }
  });
});

function renderRows(items, kind) {
  if (!items || !items.length) {
    return '<p class="result-row warning">No matches yet. Try a richer query with genre, skill, artist, or mood.</p>';
  }

  return items.map((item) => {
    const title = item.title || item.name || "Untitled";
    const subtitle = item.artist || item.company || item.genres || item.location || "";
    const detail = item.overview || item.description || item.skills || item.album || item.requirements || "";
    const score = item.score ?? item.rating ?? item.popularity ?? "";
    const image = item.poster_url || item.image_url || item.company_logo || "";
    const imageHtml = image ? `<img class="mini-thumb" src="${escapeHtml(image)}" alt="">` : "";
    const apply = item.apply_url ? `<a class="inline-link" href="${escapeHtml(item.apply_url)}" target="_blank" rel="noreferrer">Apply</a>` : "";
    return `
      <div class="result-row ${escapeHtml(kind || "")}">
        ${imageHtml}
        <div>
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(subtitle)}</span>
          <small>${escapeHtml(detail).slice(0, 180)} ${apply}</small>
        </div>
        ${score !== "" ? `<b>${escapeHtml(score)}</b>` : ""}
      </div>
    `;
  }).join("");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}
