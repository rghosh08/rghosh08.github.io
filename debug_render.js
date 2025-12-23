// Define window mock global BEFORE eval
global.window = {};

const fs = require('fs');
// Read file content
const pubsContent = fs.readFileSync('./publications.js', 'utf8');
// Eval in this context where window exists
eval(pubsContent); 

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

function pubCard(pub) {
    const thumbUrl = safeUrl(pub.thumbUrl);
    return `Title: ${pub.title}\nThumb: ${thumbUrl}\nHTML: <img class="thumb"\n          src="${escHtml(thumbUrl)}?v=3"`;
}

console.log("--- LLM PUBS ---");
window.PUBS.llm.forEach(p => console.log(pubCard(p)));
