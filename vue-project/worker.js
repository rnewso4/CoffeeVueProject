const BACKEND_ORIGIN = 'http://54.205.33.101:5000';

export default {
  async fetch(request, env, _ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      const backendUrl = BACKEND_ORIGIN + url.pathname + url.search;
      const backendRequest = new Request(backendUrl, {
        method: request.method,
        headers: request.headers,
        body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      });
      const res = await fetch(backendRequest);
      return new Response(res.body, {
        status: res.status,
        statusText: res.statusText,
        headers: res.headers,
      });
    }
    return env.ASSETS.fetch(request);
  },
};
