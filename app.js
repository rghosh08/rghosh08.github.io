(function () {
    // ---------- utilities ----------
    function escHtml(s) {
      return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  
    function safeUrl(url) {
      if (!url) return "";
      return String(url).trim();
    }
  
    // ---------- component ----------
    function pubCard(pub) {
      console.log("Rendering:", pub.title);
      const paperUrl = safeUrl(pub.paperUrl);
      const thumbUrl = safeUrl(pub.thumbUrl);
      console.log("Thumb:", thumbUrl);
  
      const thumbImg = `
        <img class="thumb"
          src="${escHtml(thumbUrl)}?v=3"
          alt="${escHtml(pub.thumbAlt || "Publication thumbnail")}"
          loading="lazy">
      `;
  
      const media = paperUrl
        ? `<a class="pub__media" href="${escHtml(paperUrl)}" target="_blank" rel="noopener noreferrer">${thumbImg}</a>`
        : `<div class="pub__media">${thumbImg}</div>`;
  
      const links = (pub.links || [])
        .filter(l => safeUrl(l.href))
        .map(l => `<a href="${escHtml(safeUrl(l.href))}" target="_blank" rel="noopener noreferrer">${escHtml(l.label)}</a>`)
        .join(' <span class="sep">·</span> ');
  
      return `
        <article class="pub">
          ${media}
          <div class="pub__meta">
            <div class="pub__title">${escHtml(pub.title)}</div>
            <div class="pub__authors">${pub.authorsHtml ? pub.authorsHtml : escHtml(pub.authors || "")}</div>
            <div class="pub__venue">${pub.venueHtml ? pub.venueHtml : escHtml(pub.venue || "")}</div>
            <div class="pub__links">${links}</div>
          </div>
        </article>
      `;
    }
  
    function renderPubs(containerId, pubs) {
      const el = document.getElementById(containerId);
      if (!el) return;
      el.innerHTML = pubs.map(pubCard).join("");
    }
  
    // ---------- bootstrap ----------
    document.addEventListener("DOMContentLoaded", () => {
      const pubs = window.PUBS || { llm: [], mlcommons: [], phd: [] };
      renderPubs("pubs-llm", pubs.llm);
      renderPubs("pubs-mlcommons", pubs.mlcommons);
      renderPubs("pubs-phd", pubs.phd);
    });
  })();
  