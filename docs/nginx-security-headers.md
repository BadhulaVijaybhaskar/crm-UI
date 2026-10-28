# Nginx security headers (snippet only)

CRM-12 ships app-side headers via `crm.overrides.response_headers.after_request`:
enforcing CSP, `X-Frame-Options`, `Permissions-Policy`, and HSTS only when the
request is HTTPS (`X-Forwarded-Proto`).

**Edge owns** `X-Content-Type-Options: nosniff` and
`Referrer-Policy: strict-origin-when-cross-origin` so those values are set once
(no app/nginx duplicates). Keep the same literal values if you also set them
elsewhere.

Use the following nginx snippet on the edge if you want defence in depth.
**Do not apply blindly** — validate CSP against your CDN, analytics, and websocket hosts first.

This repo has no `docker/nginx` (or similar) config checked in. Apply the
`webmanifest` MIME type on deploy — `/assets/*.webmanifest` is served by nginx,
not Python, so app-side `Content-Type` overrides never reach the browser.

After `bench build` / image bake, run `scripts/strip-sourcemaps.sh` (also hooked
from `after_migrate`) so framework `*.map` files are not left under `sites/assets`.

```nginx
# Example server / location block additions for the CRM site.

# PWA manifest (default mime.types often maps .webmanifest → octet-stream)
types {
    application/manifest+json webmanifest;
}
# Prefer merging with the stock mime.types include rather than replacing it.

# Block source map downloads (defence in depth; assets scrub also deletes *.map)
location ~* \.map$ {
    return 404;
}

add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-Frame-Options "SAMEORIGIN" always;

# Optional defence in depth — app already sends enforcing CSP + Permissions-Policy.
# add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; ..." always;
# add_header Permissions-Policy "camera=(), microphone=(self), geolocation=()" always;

# Optional: hide upstream fingerprinting
proxy_hide_header X-Powered-By;
proxy_hide_header Server;
```

App-side already strips `Server`, `X-Powered-By`, and `X-Frappe-*` response headers where possible.
