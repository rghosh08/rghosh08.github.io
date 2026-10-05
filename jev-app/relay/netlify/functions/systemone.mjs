// Relay for the Jev Runner page at https://rajatghosh.me/jev.html.
//
// TypeSafe's API rejects cross-origin browser calls, so the hosted page posts
// here and this function forwards the request to TypeSafe with the caller's
// own API key, passed through in memory only. Nothing is logged or stored.
//
// A caller may instead send an X-Jev-Access token and no key. The token is
// derived in the browser from the site's gate username and password. When it
// matches JEV_ACCESS_TOKEN, the relay uses the key in JEV_API_KEY. Both are
// Netlify environment variables and are never committed to the repository.
import { createHash, timingSafeEqual } from "node:crypto";

const UPSTREAM = "https://api.typesafe.ai/v1/systemone";
const ALLOWED_ORIGINS = new Set(["https://rajatghosh.me", "https://www.rajatghosh.me"]);
const MAX_BODY_BYTES = 1024 * 1024;

const digest = (s) => createHash("sha256").update(s).digest();
function hasAccess(token) {
  const expected = process.env.JEV_ACCESS_TOKEN;
  return Boolean(expected && token) && timingSafeEqual(digest(token), digest(expected));
}

const json = (status, body, headers) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...headers } });

export default async (req) => {
  const origin = req.headers.get("origin") || "";
  if (!ALLOWED_ORIGINS.has(origin)) return json(403, { error: "This relay only serves rajatghosh.me." });
  const cors = {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Jev-Access",
    "Access-Control-Max-Age": "7200",
    Vary: "Origin",
  };
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method !== "POST") return json(405, { error: "Use POST." }, cors);

  let auth = req.headers.get("authorization") || "";
  if (!/^Bearer \S+$/.test(auth)) {
    const token = req.headers.get("x-jev-access") || "";
    if (!token) return json(401, { error: "Enter a TypeSafe API key." }, cors);
    if (!hasAccess(token)) return json(403, { error: "Access was refused. Unlock the page again, or enter your own TypeSafe API key." }, cors);
    if (!process.env.JEV_API_KEY) return json(503, { error: "No saved API key is configured on the relay. Enter your own TypeSafe API key." }, cors);
    auth = "Bearer " + process.env.JEV_API_KEY;
  }

  const text = await req.text();
  if (text.length > MAX_BODY_BYTES) return json(413, { error: "Request body is too large." }, cors);
  let body;
  try { body = JSON.parse(text); } catch { return json(400, { error: "Request body is not valid JSON." }, cors); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return json(400, { error: "Request body must be a JSON object." }, cors);

  // Forward only the fields the System One API takes.
  const payload = { model: body.model || "jev-latest", state: body.state, questions: body.questions };
  let upstream;
  try {
    upstream = await fetch(UPSTREAM, {
      method: "POST",
      headers: { Authorization: auth, "Content-Type": "application/json", Accept: "application/json", "User-Agent": "jev-runner-relay/1.0" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(25000),
    });
  } catch (err) {
    return json(502, { error: "The relay could not reach the Jev API." }, cors);
  }
  return new Response(await upstream.text(), {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json", "Cache-Control": "no-store", ...cors },
  });
};

export const config = { path: "/systemone" };
