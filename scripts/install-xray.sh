#!/usr/bin/env bash
set -Eeuo pipefail

# Keep build-time Xray behavior reproducible for both supported image platforms.
# Changing the release requires reviewing its archive hashes and Node E2E tests.
xray_version="${1:-v26.10.31}"
if [ "$xray_version" != "v26.10.31" ]; then
    echo "Unreviewed Xray release: $xray_version" >&2
    exit 1
fi

case "$(uname -m)" in
    x86_64|amd64)
        xray_arch=64
        xray_archive_sha=e4bd9119f50ae7c41658b1abd0679ae06f98bd864a2907ff33f2f2cf7081b214
        ;;
    aarch64|arm64)
        xray_arch=arm64-v8a
        xray_archive_sha=1811c8f1da0c3b6dc707ebaf1c8390e987ba39859a8f0a7aadd8526157f2ec8d
        ;;
    *)
        echo "Unsupported image architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

xray_workdir=$(mktemp -d)
trap 'rm -rf -- "$xray_workdir"' EXIT
xray_archive="$xray_workdir/xray.zip"
curl --fail --location --silent --show-error --retry 3 \
    --connect-timeout 20 --max-time 180 \
    "https://github.com/XTLS/Xray-core/releases/download/$xray_version/Xray-linux-$xray_arch.zip" \
    --output "$xray_archive"
printf '%s  %s\n' "$xray_archive_sha" "$xray_archive" | sha256sum --check --status
unzip -q "$xray_archive" xray geoip.dat geosite.dat -d "$xray_workdir"
install -m 755 "$xray_workdir/xray" /usr/local/bin/xray
install -d /usr/local/share/xray
install -m 644 "$xray_workdir/geoip.dat" /usr/local/share/xray/geoip.dat
install -m 644 "$xray_workdir/geosite.dat" /usr/local/share/xray/geosite.dat
/usr/local/bin/xray version | grep -F 'Xray 26.10.31 '
