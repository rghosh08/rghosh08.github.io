// Relay for the Claude call made by https://rajatghosh.me/jev-router.html.
//
// The page calls api.anthropic.com directly from the browser first. When that
// fetch fails at the network level (an extension, proxy, or network that
// blocks the call), the page retries through this edge function, which
// forwards the streaming request with the caller's own Anthropic key, passed
// through in memory only. Nothing is logged or stored.
//
// This is an Edge Function rather than a regular function because regular
// functions stop after 60 seconds, while an edge function only has to start
// its response within 40 seconds and can keep streaming after that.

const UPSTREAM = "https://api.anthropic.com/v1/messages";
const ALLOWED_ORIGINS = new Set(["https://rajatghosh.me", "https://www.rajatghosh.me"]);
const ALLOWED_MODELS = new Set(["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]);
const MAX_BODY_BYTES = 1024 * 1024;

const json = (status, body, headers) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...headers } });

export default async (req) => {
  const origin = req.headers.get("origin") || "";
  if (!ALLOWED_ORIGINS.has(origin)) return json(403, { error: "This relay only serves rajatghosh.me." });
  const cors = {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Api-Key, Anthropic-Version, Anthropic-Beta",
    "Access-Control-Max-Age": "7200",
    Vary: "Origin",
  };
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method !== "POST") return json(405, { error: "Use POST." }, cors);

  const apiKey = req.headers.get("x-api-key") || "";
  if (!apiKey) return json(401, { error: "Enter an Anthropic API key." }, cors);

  const text = await req.text();
  if (text.length > MAX_BODY_BYTES) return json(413, { error: "Request body is too large." }, cors);
  let body;
  try { body = JSON.parse(text); } catch { return json(400, { error: "Request body is not valid JSON." }, cors); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return json(400, { error: "Request body must be a JSON object." }, cors);
  if (!ALLOWED_MODELS.has(body.model)) return json(400, { error: "Unknown model." }, cors);
  body.stream = true;

  const headers = {
    "x-api-key": apiKey,
    "anthropic-version": req.headers.get("anthropic-version") || "2023-06-01",
    "Content-Type": "application/json",
    Accept: "text/event-stream",
    "User-Agent": "jev-router-relay/1.0",
  };
  const beta = req.headers.get("anthropic-beta");
  if (beta) headers["anthropic-beta"] = beta;

  let upstream;
  try {
    upstream = await fetch(UPSTREAM, { method: "POST", headers, body: JSON.stringify(body) });
  } catch {
    return json(502, { error: "The relay could not reach the Anthropic API." }, cors);
  }
  // Pipe the SSE bytes back unchanged. The page parses them exactly as it
  // would a direct response.
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") || "text/event-stream",
      "Cache-Control": "no-store",
      "X-Jev-Relay": "edge",
      ...cors,
    },
  });
};

export const config = { path: "/messages" };
