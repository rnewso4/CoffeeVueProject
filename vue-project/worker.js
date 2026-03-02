const BACKEND_ORIGIN = 'http://54.205.33.101:5000';

export default {
  async fetch(request, env, _ctx) {
    const url = new URL(request.url);

    // Proxy API requests to the backend
    if (url.pathname.startsWith('/api/')) {
      const backendUrl = BACKEND_ORIGIN + url.pathname + url.search;

      const init = {
        method: request.method,
      };

      // Forward body for non-GET/HEAD methods only
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        init.body = request.body;
      }

      // Do NOT blindly forward browser headers such as Origin/Host/Referer,
      // since many backends will reject those and return 403.
      const res = await fetch(backendUrl, init);

      return new Response(res.body, {
        status: res.status,
        statusText: res.statusText,
        headers: res.headers,
      });
    }

    // Everything else is a static asset request
    return env.ASSETS.fetch(request);
  },
};
