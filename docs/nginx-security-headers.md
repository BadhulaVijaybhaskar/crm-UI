# Nginx security headers (in-repo snippets)

Ship these files into the **frontend nginx** image (see `docker/Dockerfile.frontend-nginx`):

| File | Role |
|---|---|
| `docker/nginx/security_headers.conf` | Override base-image `/etc/nginx/snippets/security_headers.conf` |
| `docker/nginx/block-sourcemaps.conf` | `location ~* \.map$ { return 404; }` |
| `docker/nginx/crm.conf` | Includes the above + `/socket.io` same-origin proxy |

## Header ownership (no duplicates)

| Header | Owner |
|---|---|
| `X-Content-Type-Options: nosniff` | **App** (`response_headers.after_request`) |
| `Referrer-Policy: strict-origin-when-cross-origin` | **App** |
| `Content-Security-Policy` (enforcing) | **App** |
| `Permissions-Policy` | **App** |
| `X-Frame-Options: SAMEORIGIN` | Nginx snippet (single value; app also sets for bare :8831) |
| `Strict-Transport-Security` | Nginx only when `$http_x_forwarded_proto = https`; app same rule |

The nginx snippet `proxy_hide_header`s nosniff / Referrer-Policy / CSP / Permissions-Policy
from upstream so edge responses do not double them. Bare backend (:8831, no nginx)
still emits nosniff + Referrer-Policy itself.

## Source maps

1. **Build strip**: `scripts/strip-sourcemaps.sh` (`find -L`) and `crm.overrides.assets_scrub` (`os.walk(..., followlinks=True)`).
2. **Images**: `docker/Dockerfile.backend-assets` and `docker/Dockerfile.frontend-nginx` run the strip at bake time.
3. **Edge**: `block-sourcemaps.conf` returns 404 for `*.map`.

```nginx
# Minimal include inside server {}
include /etc/nginx/snippets/security_headers.conf;
include /etc/nginx/snippets/block-sourcemaps.conf;
```

PWA manifest MIME (when not in the base image):

```nginx
types {
    application/manifest+json webmanifest;
}
```
