export default {
  async fetch(request) {
    const url = new URL(request.url);
    const probe = request.headers.get("X-Forwarded-Host");
    const bypass = /no-cache/i.test(request.headers.get("Cache-Control") || "") || /no-cache/i.test(request.headers.get("Pragma") || "");
    const headers = new Headers({
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": bypass || url.pathname === "/clean" ? "no-store" : "public, max-age=120",
    });
    if (url.pathname === "/vulnerable" && probe) headers.set("X-HeaderProof-Fixture", probe);
    if (url.pathname === "/safe") headers.set("Vary", "X-Forwarded-Host");
    return new Response(url.pathname.slice(1) || "clean", { headers });
  },
};
