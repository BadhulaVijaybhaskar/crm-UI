#!/usr/bin/env bash
# Remove browser-downloadable *.map files from served asset trees.
# Safe to run after `bench build`, image bake, or yarn build.
# -L: follow symlinks (sites/assets/frappe/dist is often linked).
set -euo pipefail

ROOTS=()
if [[ -n "${BENCH_PATH:-}" ]]; then
  ROOTS+=("${BENCH_PATH}/sites/assets")
  ROOTS+=("${BENCH_PATH}/sites/assets/frappe")
  ROOTS+=("${BENCH_PATH}/sites/assets/frappe/dist")
fi
if [[ -d "sites/assets" ]]; then
  ROOTS+=("sites/assets")
fi
# App checkout / installed app public bundles
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOTS+=("${REPO_ROOT}/crm/public/frontend")
ROOTS+=("${REPO_ROOT}/crm/public/js")
if [[ -n "${FRAPPE_BENCH:-}" ]]; then
  ROOTS+=("${FRAPPE_BENCH}/sites/assets")
  ROOTS+=("${FRAPPE_BENCH}/apps/crm/crm/public/frontend")
fi
# Frontend nginx image asset copies (common mount / bake paths)
for extra in \
  /assets \
  /usr/share/nginx/html \
  /var/www/html \
  "${FRONTEND_ASSETS_PATH:-}" \
  "${NGINX_ASSETS_PATH:-}"
do
  [[ -n "$extra" && -d "$extra" ]] && ROOTS+=("$extra")
done

removed=0
for root in "${ROOTS[@]}"; do
  [[ -d "$root" ]] || continue
  while IFS= read -r -d '' f; do
    rm -f "$f"
    removed=$((removed + 1))
  done < <(find -L "$root" -type f -name '*.map' -print0 2>/dev/null || true)
done

echo "strip-sourcemaps: removed ${removed} .map file(s)"
