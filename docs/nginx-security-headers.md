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
| `X-Content-Type-Options: nosniff` | **App** (pass through nginx — do not hide) |
| `Referrer-Policy: strict-origin-when-cross-origin` | **App** (pass through) |
| `Content-Security-Policy` (enforcing) | **App** (pass through) |
| `Permissions-Policy` | **App** (pass through) |
| `X-Frame-Options: SAMEORIGIN` | Nginx snippet hides upstream then sets once (app also sets for bare :8831) |
| `Strict-Transport-Security` | Nginx hides upstream; sets only when `$http_x_forwarded_proto = https` |

Bare backend (:8831, no nginx) emits nosniff + Referrer-Policy + CSP + Permissions-Policy itself.

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
