# Nginx security headers (snippet only)

CRM-12 ships app-side headers via `crm.overrides.response_headers.after_request`.
Use the following nginx snippet on the edge if you want defence in depth.
**Do not apply blindly** — validate CSP against your CDN, analytics, and websocket hosts first.

This repo has no `docker/nginx` (or similar) config checked in. Apply the
`webmanifest` MIME type on deploy — `/assets/*.webmanifest` is served by nginx,
not Python, so app-side `Content-Type` overrides never reach the browser.

```nginx
# Example server / location block additions for the CRM site.
# Review before enabling Content-Security-Policy (enforcing).

# PWA manifest (default mime.types often maps .webmanifest → octet-stream)
types {
    application/manifest+json webmanifest;
}
# Prefer merging with the stock mime.types include rather than replacing it.

add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-Frame-Options "SAMEORIGIN" always;

# Enforcing CSP is stricter than the app's report-only header.
# Start in report-only, then switch:
# add_header Content-Security-Policy-Report-Only "default-src 'self'; frame-ancestors 'self'; ..." always;
# add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; ..." always;

# Optional: hide upstream fingerprinting
proxy_hide_header X-Powered-By;
proxy_hide_header Server;
```

App-side already strips `Server`, `X-Powered-By`, and `X-Frappe-*` response headers where possible.
