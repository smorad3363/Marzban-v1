#!/usr/bin/env bash
set -e

INSTALL_DIR="/opt"
if [ -z "$APP_NAME" ]; then
    APP_NAME="marzban"
fi
APP_DIR="$INSTALL_DIR/$APP_NAME"
DATA_DIR="/var/lib/$APP_NAME"
COMPOSE_FILE="$APP_DIR/docker-compose.yml"
ENV_FILE="$APP_DIR/.env"
NODE_APP_NAME="marzban-node"
NODE_APP_DIR="$INSTALL_DIR/$NODE_APP_NAME"
NODE_DATA_DIR="/var/lib/$NODE_APP_NAME"
NODE_COMPOSE_FILE="$NODE_APP_DIR/docker-compose.yml"
NODE_ENV_FILE="$NODE_APP_DIR/.env"
NODE_CLIENT_CERT_FILE="$NODE_DATA_DIR/panel-client.crt"
NODE_RELEASE_REVISION_FILE="$NODE_APP_DIR/.release-revision"
NODE_CLI_VERSION_FILE="$NODE_APP_DIR/.cli-version"
NODE_SCRIPT_PATH="/usr/local/bin/marzban-node"
LAST_XRAY_CORES=10
# =============================================================================
# Fork configuration
# Override at runtime, e.g. MARZBAN_GITHUB_REPO=another-user/Marzban marzban install
# =============================================================================
CLI_RELEASE_VERSION="v1.0.3"
V1_LINEAGE_SOURCE_VERSION="5.2.0"
V1_LINEAGE_SOURCE_IMAGE="ghcr.io/smorad3363/marzban-vnext:v5.2.0"
V1_LINEAGE_TARGET_VERSION="v1.0.0"
MARZBAN_GITHUB_REPO="${MARZBAN_GITHUB_REPO:-smorad3363/Marzban-v1}"
MARZBAN_GITHUB_BRANCH="${MARZBAN_GITHUB_BRANCH:-main}"
MARZBAN_SCRIPTS_PATH="${MARZBAN_SCRIPTS_PATH:-scripts/marzban.sh}"
MARZBAN_DOCKER_IMAGE="${MARZBAN_DOCKER_IMAGE:-ghcr.io/smorad3363/marzban-v1}"
MARZBAN_NODE_COMPOSE_PATH="${MARZBAN_NODE_COMPOSE_PATH:-docker-compose.node.yml}"
MYSQL_TARGET_VERSION="26.7.0"
MYSQL_TARGET_IMAGE="mysql:${MYSQL_TARGET_VERSION}"
CLI_VERSION_FILE="$APP_DIR/.cli-version"
RELEASE_REVISION_FILE="$APP_DIR/.release-revision"
MYSQL_MIGRATION_DIR="$APP_DIR/.mysql-migration"
MYSQL_MIGRATION_STATE="$MYSQL_MIGRATION_DIR/state"
MARZBAN_FILES_URL_PREFIX="https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/refs/heads/${MARZBAN_GITHUB_BRANCH}"
MARZBAN_SCRIPT_URL="https://github.com/${MARZBAN_GITHUB_REPO}/raw/refs/heads/${MARZBAN_GITHUB_BRANCH}/${MARZBAN_SCRIPTS_PATH}"
MARZBAN_RELEASES_API="https://api.github.com/repos/${MARZBAN_GITHUB_REPO}/releases"

github_download() {
    local token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
    if [ -n "$token" ]; then
        curl --retry 3 --retry-delay 2 --connect-timeout 15 --header "Authorization: Bearer $token" "$@"
    else
        curl --retry 3 --retry-delay 2 --connect-timeout 15 "$@"
    fi
}

is_release_version() {
    [[ "$1" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z][0-9A-Za-z.-]*)?$ ]]
}

is_immutable_sha_image() {
    [[ "$1" =~ ^sha-[0-9a-f]{12,40}$ ]]
}

is_allowed_v1_lineage_transition() {
    local current_version="$1"
    local requested_version="$2"
    local configured_image="$3"
    local running_image="$4"
    [ "$current_version" = "$V1_LINEAGE_SOURCE_VERSION" ] &&
        [ "$requested_version" = "$V1_LINEAGE_TARGET_VERSION" ] &&
        [ "$configured_image" = "$V1_LINEAGE_SOURCE_IMAGE" ] &&
        [ "$running_image" = "$V1_LINEAGE_SOURCE_IMAGE" ]
}

latest_published_version() {
    github_download -fsSL "${MARZBAN_RELEASES_API}?per_page=100" 2>/dev/null |
        jq -r '[.[] | select(.draft == false and .prerelease == false)][0].tag_name // empty'
}

resolve_requested_version() {
    local requested_version="${1:-latest}"
    local resolved_version
    if [ "$requested_version" = "latest" ]; then
        resolved_version=$(latest_published_version)
        if ! is_release_version "$resolved_version"; then
            colorized_echo red "Could not resolve the latest published Marzban release." >&2
            return 1
        fi
        echo "$resolved_version"
        return
    fi
    if [ "$requested_version" = "dev" ] || is_release_version "$requested_version" || is_immutable_sha_image "$requested_version"; then
        echo "$requested_version"
        return
    fi
    colorized_echo red "Invalid version format: $requested_version" >&2
    return 1
}

marzban_docker_image() {
    local version="${1:-latest}"
    echo "${MARZBAN_DOCKER_IMAGE}:${version}"
}

colorized_echo() {
    local color=$1
    local text=$2

    case $color in
        "red")
        printf "\e[91m${text}\e[0m\n";;
        "green")
        printf "\e[92m${text}\e[0m\n";;
        "yellow")
        printf "\e[93m${text}\e[0m\n";;
        "blue")
        printf "\e[94m${text}\e[0m\n";;
        "magenta")
        printf "\e[95m${text}\e[0m\n";;
        "cyan")
        printf "\e[96m${text}\e[0m\n";;
        *)
            echo "${text}"
        ;;
    esac
}

check_running_as_root() {
    if [ "$(id -u)" != "0" ]; then
        colorized_echo red "This command must be run as root."
        exit 1
    fi
}

detect_os() {
    # Detect the operating system
    if [ -f /etc/lsb-release ]; then
        OS=$(lsb_release -si)
    elif [ -f /etc/os-release ]; then
        OS=$(awk -F= '/^NAME/{print $2}' /etc/os-release | tr -d '"')
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | awk '{print $1}')
    elif [ -f /etc/arch-release ]; then
        OS="Arch"
    else
        colorized_echo red "Unsupported operating system"
        exit 1
    fi
}


detect_and_update_package_manager() {
    colorized_echo blue "Updating package manager"
    if [[ "$OS" == "Ubuntu"* ]] || [[ "$OS" == "Debian"* ]]; then
        PKG_MANAGER="apt-get"
        $PKG_MANAGER update
    elif [[ "$OS" == "CentOS"* ]] || [[ "$OS" == "AlmaLinux"* ]]; then
        PKG_MANAGER="yum"
        $PKG_MANAGER update -y
        $PKG_MANAGER install -y epel-release
    elif [ "$OS" == "Fedora"* ]; then
        PKG_MANAGER="dnf"
        $PKG_MANAGER update
    elif [ "$OS" == "Arch" ]; then
        PKG_MANAGER="pacman"
        $PKG_MANAGER -Sy
    elif [[ "$OS" == "openSUSE"* ]]; then
        PKG_MANAGER="zypper"
        $PKG_MANAGER refresh
    else
        colorized_echo red "Unsupported operating system"
        exit 1
    fi
}

install_package () {
    if [ -z $PKG_MANAGER ]; then
        detect_and_update_package_manager
    fi

    PACKAGE=$1
    colorized_echo blue "Installing $PACKAGE"
    if [[ "$OS" == "Ubuntu"* ]] || [[ "$OS" == "Debian"* ]]; then
        $PKG_MANAGER -y install "$PACKAGE"
    elif [[ "$OS" == "CentOS"* ]] || [[ "$OS" == "AlmaLinux"* ]]; then
        $PKG_MANAGER install -y "$PACKAGE"
    elif [ "$OS" == "Fedora"* ]; then
        $PKG_MANAGER install -y "$PACKAGE"
    elif [ "$OS" == "Arch" ]; then
        $PKG_MANAGER -S --noconfirm "$PACKAGE"
    else
        colorized_echo red "Unsupported operating system"
        exit 1
    fi
}

install_docker() {
    # Install Docker and Docker Compose using the official installation script
    colorized_echo blue "Installing Docker"
    curl -fsSL https://get.docker.com | sh
    colorized_echo green "Docker installed successfully"
}

detect_compose() {
    # Check if docker compose command exists
    if docker compose version >/dev/null 2>&1; then
        COMPOSE='docker compose'
    elif docker-compose version >/dev/null 2>&1; then
        COMPOSE='docker-compose'
    else
        colorized_echo red "docker compose not found"
        exit 1
    fi
}


apply_runtime_resource_defaults() {
    [ -f "$COMPOSE_FILE" ] || return 0
    command -v yq >/dev/null 2>&1 || return 0

    # Existing installations may still have the pre-1.0.2 always-on
    # phpMyAdmin container. Stop and remove it before assigning the
    # opt-in tools profile, so an update actually releases its RAM.
    local phpmyadmin_id
    phpmyadmin_id=$($COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" ps -q phpmyadmin 2>/dev/null || true)
    if [ -n "$phpmyadmin_id" ]; then
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" stop phpmyadmin >/dev/null 2>&1 || true
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" rm -f phpmyadmin >/dev/null 2>&1 || true
    fi

    # Keep defaults conservative on 1 vCPU / 1 GB installations but
    # preserve operator overrides through normal Compose substitution.
    yq -i '.services.marzban.environment = (.services.marzban.environment // {})' "$COMPOSE_FILE"
    yq -i '.services.marzban.environment.SQLALCHEMY_POOL_SIZE = "${SQLALCHEMY_POOL_SIZE:-5}"' "$COMPOSE_FILE"
    yq -i '.services.marzban.environment.SQLIALCHEMY_MAX_OVERFLOW = "${SQLIALCHEMY_MAX_OVERFLOW:-5}"' "$COMPOSE_FILE"
    sed -i 's/--innodb-buffer-pool-size=256M/--innodb-buffer-pool-size=${MYSQL_INNODB_BUFFER_POOL_SIZE:-128M}/g' "$COMPOSE_FILE"
    if yq -e '.services.phpmyadmin' "$COMPOSE_FILE" >/dev/null 2>&1; then
        yq -i '.services.phpmyadmin.profiles = ["tools"]' "$COMPOSE_FILE"
        yq -i '.services.phpmyadmin.restart = "unless-stopped"' "$COMPOSE_FILE"
    fi
}

marzban_script_ref() {
    local requested_version="${1:-latest}"
    if is_release_version "$requested_version"; then
        echo "$requested_version"
        return
    fi
    if is_immutable_sha_image "$requested_version"; then
        echo "${requested_version#sha-}"
        return
    fi
    echo "$MARZBAN_GITHUB_BRANCH"
}

install_marzban_script_from_repo() {
    local requested_version="${1:-latest}"
    local script_ref="${2:-}"
    local script_ref_path
    local script_url
    local temp_script
    if [ -z "$script_ref" ]; then
        script_ref=$(marzban_script_ref "$requested_version")
    fi
    script_ref_path="$script_ref"
    if [ "$script_ref" = "$MARZBAN_GITHUB_BRANCH" ]; then
        script_ref_path="refs/heads/${script_ref}"
    fi
    script_url="https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${script_ref_path}/${MARZBAN_SCRIPTS_PATH}"
    temp_script=$(mktemp)
    colorized_echo blue "Installing marzban script from ${MARZBAN_GITHUB_REPO}@${script_ref}"
    if ! github_download -fsSL "$script_url" -o "$temp_script"; then
        rm -f "$temp_script"
        colorized_echo red "Could not download marzban script from ${script_ref}."
        return 1
    fi
    if ! bash -n "$temp_script" || ! install -m 755 "$temp_script" /usr/local/bin/marzban; then
        rm -f "$temp_script"
        return 1
    fi
    rm -f "$temp_script"
    if [ -d "$APP_DIR" ]; then
        printf '%s\n' "$requested_version" > "$CLI_VERSION_FILE"
        chmod 644 "$CLI_VERSION_FILE"
    fi
    colorized_echo green "marzban script installed successfully"
}

cleanup_release_build_dir() {
    local build_dir="$1"
    case "$build_dir" in
        /tmp/marzban-release-build.*)
            rm -rf -- "$build_dir"
        ;;
    esac
}

release_commit_for_version() {
    local requested_version="$1"
    github_download -fsSL "https://api.github.com/repos/${MARZBAN_GITHUB_REPO}/commits/${requested_version}" 2>/dev/null |
        jq -r '.sha // empty'
}

marzban_image_revision() {
    local image="$1"
    docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image" 2>/dev/null || true
}

build_marzban_image_from_source() {
    local requested_version="$1"
    local source_commit="$2"
    local image build_dir archive source_dir
    image=$(marzban_docker_image "$requested_version")
    build_dir=$(mktemp -d /tmp/marzban-release-build.XXXXXXXX)
    archive="$build_dir/source.tar.gz"
    source_dir="$build_dir/source"
    mkdir -p "$source_dir"

    colorized_echo yellow "Published image is not publicly readable; building ${requested_version} from the public release source."
    if ! github_download -fsSL "https://github.com/${MARZBAN_GITHUB_REPO}/archive/${source_commit}.tar.gz" -o "$archive"; then
        cleanup_release_build_dir "$build_dir"
        colorized_echo red "Could not download source for ${requested_version}."
        return 1
    fi
    if ! tar -xzf "$archive" -C "$source_dir" --strip-components=1; then
        cleanup_release_build_dir "$build_dir"
        colorized_echo red "Could not extract source for ${requested_version}."
        return 1
    fi
    if ! docker build --pull \
        --label "org.opencontainers.image.source=https://github.com/${MARZBAN_GITHUB_REPO}" \
        --label "org.opencontainers.image.revision=${source_commit}" \
        --label "org.opencontainers.image.version=${requested_version}" \
        --tag "$image" "$source_dir"; then
        cleanup_release_build_dir "$build_dir"
        colorized_echo red "Could not build ${image}."
        return 1
    fi
    cleanup_release_build_dir "$build_dir"
    colorized_echo green "Built ${image} from public release source."
}

ensure_marzban_image() {
    local requested_version="$1"
    local image expected_revision actual_revision
    image=$(marzban_docker_image "$requested_version")
    if ! is_release_version "$requested_version"; then
        if docker pull "$image"; then
            return 0
        fi
        colorized_echo red "Could not pull ${image}; source fallback supports release versions only."
        return 1
    fi
    expected_revision=$(release_commit_for_version "$requested_version")
    if [[ ! "$expected_revision" =~ ^[0-9a-f]{40}$ ]]; then
        colorized_echo red "Could not resolve the source commit for ${requested_version}."
        return 1
    fi
    MARZBAN_VERIFIED_REVISION="$expected_revision"
    if docker pull "$image" >/dev/null 2>&1; then
        actual_revision=$(marzban_image_revision "$image")
        if [ "$actual_revision" = "$expected_revision" ]; then
            colorized_echo green "Downloaded verified ${image}."
            return 0
        fi
        colorized_echo yellow "Published image revision does not match ${expected_revision}; rebuilding verified source."
    elif docker image inspect "$image" >/dev/null 2>&1; then
        actual_revision=$(marzban_image_revision "$image")
        if [ "$actual_revision" = "$expected_revision" ]; then
            colorized_echo green "Using verified local ${image}."
            return 0
        fi
        colorized_echo yellow "Cached ${image} is stale or unverified; rebuilding it."
    fi
    build_marzban_image_from_source "$requested_version" "$expected_revision"
}

record_marzban_release_revision() {
    if [[ ! "${MARZBAN_VERIFIED_REVISION:-}" =~ ^[0-9a-f]{40}$ ]]; then
        colorized_echo red "Verified release revision is unavailable."
        return 1
    fi
    printf '%s\n' "$MARZBAN_VERIFIED_REVISION" > "$RELEASE_REVISION_FILE"
    chmod 644 "$RELEASE_REVISION_FILE"
}

configured_service_image() {
    local service="$1"
    yq -r ".services.${service}.image // \"\"" "$COMPOSE_FILE"
}

running_service_container() {
    local service="$1"
    $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" ps -q "$service" 2>/dev/null
}

runtime_app_version() {
    local container_id
    container_id=$(running_service_container marzban)
    [ -n "$container_id" ] || return 1
    docker exec "$container_id" python -c 'from app import __version__; print(__version__)' 2>/dev/null
}

version_command() {
    if [ "$#" -ne 0 ]; then
        colorized_echo red "Usage: marzban version"
        exit 1
    fi
    check_running_as_root
    if ! is_marzban_installed || [ ! -f "$COMPOSE_FILE" ]; then
        colorized_echo red "Marzban is not installed."
        exit 1
    fi
    detect_compose
    command -v yq >/dev/null 2>&1 || { colorized_echo red "yq is required."; exit 1; }

    local cli_version configured_image container_id runtime_version running_image digest revision
    cli_version="$CLI_RELEASE_VERSION"
    configured_image=$(configured_service_image marzban)
    container_id=$(running_service_container marzban)
    runtime_version=$(runtime_app_version || echo "unavailable")
    if [ -n "$container_id" ]; then
        running_image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || echo "unavailable")
        digest=$(docker image inspect --format '{{if .RepoDigests}}{{index .RepoDigests 0}}{{else}}{{.Id}}{{end}}' "$running_image" 2>/dev/null || echo "unavailable")
        revision=$(marzban_image_revision "$running_image")
    else
        running_image="not-running"
        digest="unavailable"
        revision="unavailable"
    fi

    echo "CLI version: ${cli_version}"
    echo "Runtime app version: ${runtime_version}"
    echo "Configured Docker image: ${configured_image}"
    echo "Running Docker image: ${running_image}"
    echo "Immutable image digest: ${digest}"
    echo "Source revision: ${revision:-unavailable}"
    local mysql_id mysql_version
    mysql_id=$(running_service_container mysql)
    mysql_version=$(mysql_upgrade_server_version "$mysql_id" 2>/dev/null || echo "unavailable")
    echo "Configured MySQL image: $(configured_service_image mysql)"
    echo "Runtime MySQL version: ${mysql_version}"
    verify_version_integrity "$cli_version"
}

verify_version_integrity() {
    local expected_version="$1"
    local expected_image configured_image container_id running_image runtime_version cli_version digest expected_revision running_revision
    expected_image=$(marzban_docker_image "$expected_version")
    configured_image=$(configured_service_image marzban)
    container_id=$(running_service_container marzban)
    [ -n "$container_id" ] || { colorized_echo red "Version integrity failed: application container is not running."; return 1; }
    running_image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
    local running_image_id expected_image_id
    running_image_id=$(docker inspect --format '{{.Image}}' "$container_id" 2>/dev/null || true)
    expected_image_id=$(docker image inspect --format '{{.Id}}' "$expected_image" 2>/dev/null || true)
    [ -n "$running_image_id" ] && [ "$running_image_id" = "$expected_image_id" ] || { colorized_echo red "Version integrity failed: running image content differs from the expected local image."; return 1; }
    runtime_version=$(runtime_app_version | tr -d '\r[:space:]' || true)
    cli_version=$(cat "$CLI_VERSION_FILE" 2>/dev/null | tr -d '\r[:space:]' || true)
    digest=$(docker image inspect --format '{{if .RepoDigests}}{{index .RepoDigests 0}}{{else}}{{.Id}}{{end}}' "$running_image" 2>/dev/null || true)
    expected_revision=$(cat "$RELEASE_REVISION_FILE" 2>/dev/null | tr -d '\r[:space:]' || true)
    running_revision=$(marzban_image_revision "$running_image")

    [ "$configured_image" = "$expected_image" ] || { colorized_echo red "Version integrity failed: configured image is ${configured_image}, expected ${expected_image}."; return 1; }
    [ "$running_image" = "$expected_image" ] || { colorized_echo red "Version integrity failed: running image is ${running_image}, expected ${expected_image}."; return 1; }
    [ "$runtime_version" = "${expected_version#v}" ] || { colorized_echo red "Version integrity failed: runtime is ${runtime_version}, expected ${expected_version#v}."; return 1; }
    [ "$cli_version" = "$expected_version" ] || { colorized_echo red "Version integrity failed: CLI is ${cli_version}, expected ${expected_version}."; return 1; }
    [[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] || { colorized_echo red "Version integrity failed: verified source revision is unavailable."; return 1; }
    [ "$running_revision" = "$expected_revision" ] || { colorized_echo red "Version integrity failed: running source revision is ${running_revision:-unavailable}, expected ${expected_revision}."; return 1; }
    local installed_cli_version mysql_id mysql_version
    installed_cli_version=$(sed -n 's/^CLI_RELEASE_VERSION="\([^"]*\)"$/\1/p' /usr/local/bin/marzban)
    [ "$installed_cli_version" = "$expected_version" ] || { colorized_echo red "Version integrity failed: installed CLI content does not match ${expected_version}."; return 1; }
    mysql_preflight || return 1
    mysql_id=$(running_service_container mysql)
    [ -n "$mysql_id" ] || { colorized_echo red "Version integrity failed: MySQL is not running."; return 1; }
    mysql_version=$(mysql_upgrade_server_version "$mysql_id" 2>/dev/null | tr -d '\r[:space:]' || true)
    [ "$mysql_version" = "$MYSQL_TARGET_VERSION" ] || { colorized_echo red "Version integrity failed: MySQL runtime is ${mysql_version}, expected ${MYSQL_TARGET_VERSION}."; return 1; }
    [ -n "$digest" ] || { colorized_echo red "Version integrity failed: immutable image digest is unavailable."; return 1; }
    colorized_echo green "Version integrity verified for ${expected_version}: ${digest}"
}

is_marzban_installed() {
    if [ -d $APP_DIR ]; then
        return 0
    else
        return 1
    fi
}

identify_the_operating_system_and_architecture() {
    if [[ "$(uname)" == 'Linux' ]]; then
        case "$(uname -m)" in
            'i386' | 'i686')
                ARCH='32'
            ;;
            'amd64' | 'x86_64')
                ARCH='64'
            ;;
            'armv5tel')
                ARCH='arm32-v5'
            ;;
            'armv6l')
                ARCH='arm32-v6'
                grep Features /proc/cpuinfo | grep -qw 'vfp' || ARCH='arm32-v5'
            ;;
            'armv7' | 'armv7l')
                ARCH='arm32-v7a'
                grep Features /proc/cpuinfo | grep -qw 'vfp' || ARCH='arm32-v5'
            ;;
            'armv8' | 'aarch64')
                ARCH='arm64-v8a'
            ;;
            'mips')
                ARCH='mips32'
            ;;
            'mipsle')
                ARCH='mips32le'
            ;;
            'mips64')
                ARCH='mips64'
                lscpu | grep -q "Little Endian" && ARCH='mips64le'
            ;;
            'mips64le')
                ARCH='mips64le'
            ;;
            'ppc64')
                ARCH='ppc64'
            ;;
            'ppc64le')
                ARCH='ppc64le'
            ;;
            'riscv64')
                ARCH='riscv64'
            ;;
            's390x')
                ARCH='s390x'
            ;;
            *)
                echo "error: The architecture is not supported."
                exit 1
            ;;
        esac
    else
        echo "error: This operating system is not supported."
        exit 1
    fi
}

send_backup_to_telegram() {
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            if [[ -z "$key" || "$key" =~ ^# ]]; then
                continue
            fi
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            if [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
                export "$key"="$value"
            else
                colorized_echo yellow "Skipping invalid line in .env: $key=$value"
            fi
        done < "$ENV_FILE"
    else
        colorized_echo red "Environment file (.env) not found."
        exit 1
    fi

    if [ "$BACKUP_SERVICE_ENABLED" != "true" ]; then
        colorized_echo yellow "Backup service is not enabled. Skipping Telegram upload."
        return
    fi

    local server_ip=$(curl -s ifconfig.me || echo "Unknown IP")
    local latest_backup=$(ls -t "$APP_DIR/backup" | head -n 1)
    local backup_path="$APP_DIR/backup/$latest_backup"

    if [ ! -f "$backup_path" ]; then
        colorized_echo red "No backups found to send."
        return
    fi

    local backup_size=$(du -m "$backup_path" | cut -f1)
    local split_dir="/tmp/marzban_backup_split"
    local is_single_file=true

    mkdir -p "$split_dir"

    if [ "$backup_size" -gt 49 ]; then
        colorized_echo yellow "Backup is larger than 49MB. Splitting the archive..."
        split -b 49M "$backup_path" "$split_dir/part_"
        is_single_file=false
    else
        cp "$backup_path" "$split_dir/part_aa"
    fi


    local backup_time=$(date "+%Y-%m-%d %H:%M:%S %Z")


    for part in "$split_dir"/*; do
        local part_name=$(basename "$part")
        local custom_filename="backup_${part_name}.tar.gz"
        local caption="📦 *Backup Information*\n🌐 *Server IP*: \`${server_ip}\`\n📁 *Backup File*: \`${custom_filename}\`\n⏰ *Backup Time*: \`${backup_time}\`"
        curl -s -F chat_id="$BACKUP_TELEGRAM_CHAT_ID" \
            -F document=@"$part;filename=$custom_filename" \
            -F caption="$(echo -e "$caption" | sed 's/-/\\-/g;s/\./\\./g;s/_/\\_/g')" \
            -F parse_mode="MarkdownV2" \
            "https://api.telegram.org/bot$BACKUP_TELEGRAM_BOT_KEY/sendDocument" >/dev/null 2>&1 && \
        colorized_echo green "Backup part $custom_filename successfully sent to Telegram." || \
        colorized_echo red "Failed to send backup part $custom_filename to Telegram."
    done

    rm -rf "$split_dir"
}

send_backup_error_to_telegram() {
    local error_messages=$1
    local log_file=$2
    local server_ip=$(curl -s ifconfig.me || echo "Unknown IP")
    local error_time=$(date "+%Y-%m-%d %H:%M:%S %Z")
    local message="⚠️ *Backup Error Notification*\n"
    message+="🌐 *Server IP*: \`${server_ip}\`\n"
    message+="❌ *Errors*:\n\`${error_messages//_/\\_}\`\n"
    message+="⏰ *Time*: \`${error_time}\`"


    message=$(echo -e "$message" | sed 's/-/\\-/g;s/\./\\./g;s/_/\\_/g;s/(/\\(/g;s/)/\\)/g')

    local max_length=1000
    if [ ${#message} -gt $max_length ]; then
        message="${message:0:$((max_length - 50))}...\n\`[Message truncated]\`"
    fi


    curl -s -X POST "https://api.telegram.org/bot$BACKUP_TELEGRAM_BOT_KEY/sendMessage" \
        -d chat_id="$BACKUP_TELEGRAM_CHAT_ID" \
        -d parse_mode="MarkdownV2" \
        -d text="$message" >/dev/null 2>&1 && \
    colorized_echo green "Backup error notification sent to Telegram." || \
    colorized_echo red "Failed to send error notification to Telegram."


    if [ -f "$log_file" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/tg_response.json \
            -F chat_id="$BACKUP_TELEGRAM_CHAT_ID" \
            -F document=@"$log_file;filename=backup_error.log" \
            -F caption="📜 *Backup Error Log* - ${error_time}" \
            "https://api.telegram.org/bot$BACKUP_TELEGRAM_BOT_KEY/sendDocument")

        http_code="${response:(-3)}"
        if [ "$http_code" -eq 200 ]; then
            colorized_echo green "Backup error log sent to Telegram."
        else
            colorized_echo red "Failed to send backup error log to Telegram. HTTP code: $http_code"
            cat /tmp/tg_response.json
        fi
    else
        colorized_echo red "Log file not found: $log_file"
    fi
}





backup_service() {
    local telegram_bot_key=""
    local telegram_chat_id=""
    local cron_schedule=""
    local interval_hours=""

    colorized_echo blue "====================================="
    colorized_echo blue "      Welcome to Backup Service      "
    colorized_echo blue "====================================="

    if grep -q "BACKUP_SERVICE_ENABLED=true" "$ENV_FILE"; then
        telegram_bot_key=$(awk -F'=' '/^BACKUP_TELEGRAM_BOT_KEY=/ {print $2}' "$ENV_FILE")
        telegram_chat_id=$(awk -F'=' '/^BACKUP_TELEGRAM_CHAT_ID=/ {print $2}' "$ENV_FILE")
        cron_schedule=$(awk -F'=' '/^BACKUP_CRON_SCHEDULE=/ {print $2}' "$ENV_FILE" | tr -d '"')

        if [[ "$cron_schedule" == "0 0 * * *" ]]; then
            interval_hours=24
        else
            interval_hours=$(echo "$cron_schedule" | grep -oP '(?<=\*/)[0-9]+')
        fi

        colorized_echo green "====================================="
        colorized_echo green "Current Backup Configuration:"
        colorized_echo cyan "Telegram Bot API Key: $telegram_bot_key"
        colorized_echo cyan "Telegram Chat ID: $telegram_chat_id"
        colorized_echo cyan "Backup Interval: Every $interval_hours hour(s)"
        colorized_echo green "====================================="
        echo "Choose an option:"
        echo "1. Reconfigure Backup Service"
        echo "2. Remove Backup Service"
        echo "3. Exit"
        read -p "Enter your choice (1-3): " user_choice

        case $user_choice in
            1)
                colorized_echo yellow "Starting reconfiguration..."
                remove_backup_service
                ;;
            2)
                colorized_echo yellow "Removing Backup Service..."
                remove_backup_service
                return
                ;;
            3)
                colorized_echo yellow "Exiting..."
                return
                ;;
            *)
                colorized_echo red "Invalid choice. Exiting."
                return
                ;;
        esac
    else
        colorized_echo yellow "No backup service is currently configured."
    fi

    while true; do
        printf "Enter your Telegram bot API key: "
        read telegram_bot_key
        if [[ -n "$telegram_bot_key" ]]; then
            break
        else
            colorized_echo red "API key cannot be empty. Please try again."
        fi
    done

    while true; do
        printf "Enter your Telegram chat ID: "
        read telegram_chat_id
        if [[ -n "$telegram_chat_id" ]]; then
            break
        else
            colorized_echo red "Chat ID cannot be empty. Please try again."
        fi
    done

    while true; do
        printf "Set up the backup interval in hours (1-24):\n"
        read interval_hours

        if ! [[ "$interval_hours" =~ ^[0-9]+$ ]]; then
            colorized_echo red "Invalid input. Please enter a valid number."
            continue
        fi

        if [[ "$interval_hours" -eq 24 ]]; then
            cron_schedule="0 0 * * *"
            colorized_echo green "Setting backup to run daily at midnight."
            break
        fi

        if [[ "$interval_hours" -ge 1 && "$interval_hours" -le 23 ]]; then
            cron_schedule="0 */$interval_hours * * *"
            colorized_echo green "Setting backup to run every $interval_hours hour(s)."
            break
        else
            colorized_echo red "Invalid input. Please enter a number between 1-24."
        fi
    done

    sed -i '/^BACKUP_SERVICE_ENABLED/d' "$ENV_FILE"
    sed -i '/^BACKUP_TELEGRAM_BOT_KEY/d' "$ENV_FILE"
    sed -i '/^BACKUP_TELEGRAM_CHAT_ID/d' "$ENV_FILE"
    sed -i '/^BACKUP_CRON_SCHEDULE/d' "$ENV_FILE"

    {
        echo ""
        echo "# Backup service configuration"
        echo "BACKUP_SERVICE_ENABLED=true"
        echo "BACKUP_TELEGRAM_BOT_KEY=$telegram_bot_key"
        echo "BACKUP_TELEGRAM_CHAT_ID=$telegram_chat_id"
        echo "BACKUP_CRON_SCHEDULE=\"$cron_schedule\""
    } >> "$ENV_FILE"

    colorized_echo green "Backup service configuration saved in $ENV_FILE."

    local backup_command="$(which bash) -c '$APP_NAME backup'"
    add_cron_job "$cron_schedule" "$backup_command"

    colorized_echo green "Backup service successfully configured."
    if [[ "$interval_hours" -eq 24 ]]; then
        colorized_echo cyan "Backups will be sent to Telegram daily (every 24 hours at midnight)."
    else
        colorized_echo cyan "Backups will be sent to Telegram every $interval_hours hour(s)."
    fi
    colorized_echo green "====================================="
}


add_cron_job() {
    local schedule="$1"
    local command="$2"
    local temp_cron=$(mktemp)

    crontab -l 2>/dev/null > "$temp_cron" || true
    grep -v "$command" "$temp_cron" > "${temp_cron}.tmp" && mv "${temp_cron}.tmp" "$temp_cron"
    echo "$schedule $command # marzban-backup-service" >> "$temp_cron"

    if crontab "$temp_cron"; then
        colorized_echo green "Cron job successfully added."
    else
        colorized_echo red "Failed to add cron job. Please check manually."
    fi
    rm -f "$temp_cron"
}

remove_backup_service() {
    colorized_echo red "in process..."


    sed -i '/^# Backup service configuration/d' "$ENV_FILE"
    sed -i '/BACKUP_SERVICE_ENABLED/d' "$ENV_FILE"
    sed -i '/BACKUP_TELEGRAM_BOT_KEY/d' "$ENV_FILE"
    sed -i '/BACKUP_TELEGRAM_CHAT_ID/d' "$ENV_FILE"
    sed -i '/BACKUP_CRON_SCHEDULE/d' "$ENV_FILE"

    local temp_cron=$(mktemp)
    crontab -l 2>/dev/null > "$temp_cron"

    sed -i '/# marzban-backup-service/d' "$temp_cron"

    if crontab "$temp_cron"; then
        colorized_echo green "Backup service task removed from crontab."
    else
        colorized_echo red "Failed to update crontab. Please check manually."
    fi

    rm -f "$temp_cron"

    colorized_echo green "Backup service has been removed."
}

backup_command() {
    local backup_dir="$APP_DIR/backup"
    local temp_dir
    temp_dir=$(mktemp -d /tmp/marzban_backup.XXXXXX)
    local timestamp=$(date +"%Y%m%d%H%M%S")
    local backup_file="$backup_dir/backup_$timestamp.tar.gz"
    local error_messages=()
    local log_file="/var/log/marzban_backup_error.log"
    > "$log_file"
    echo "Backup Log - $(date)" > "$log_file"

    if ! command -v rsync >/dev/null 2>&1; then
        detect_os
        install_package rsync
    fi

    install -d -m 700 "$backup_dir"

    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            if [[ -z "$key" || "$key" =~ ^# ]]; then
                continue
            fi
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            if [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
                export "$key"="$value"
            else
                echo "Skipping invalid line in .env: $key=$value" >> "$log_file"
            fi
        done < "$ENV_FILE"
    else
        error_messages+=("Environment file (.env) not found.")
        echo "Environment file (.env) not found." >> "$log_file"
        send_backup_error_to_telegram "${error_messages[*]}" "$log_file"
        exit 1
    fi

    local db_type=""
    local sqlite_file=""
    if grep -q "image: mariadb" "$COMPOSE_FILE"; then
        db_type="mariadb"
        container_name=$(docker compose -f "$COMPOSE_FILE" ps -q mariadb || echo "mariadb")

    elif grep -q "image: mysql" "$COMPOSE_FILE"; then
        db_type="mysql"
        container_name=$(docker compose -f "$COMPOSE_FILE" ps -q mysql || echo "mysql")

    elif grep -q "SQLALCHEMY_DATABASE_URL = .*sqlite" "$ENV_FILE"; then
        db_type="sqlite"
        sqlite_file=$(grep -Po '(?<=SQLALCHEMY_DATABASE_URL = "sqlite:////).*"' "$ENV_FILE" | tr -d '"')
        if [[ ! "$sqlite_file" =~ ^/ ]]; then
            sqlite_file="/$sqlite_file"
        fi

    fi

    if [ -n "$db_type" ]; then
        echo "Database detected: $db_type" >> "$log_file"
        case $db_type in
            mariadb)
                if ! docker exec "$container_name" mariadb-dump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases --ignore-database=mysql --ignore-database=performance_schema --ignore-database=information_schema --ignore-database=sys --events --triggers > "$temp_dir/db_backup.sql" 2>>"$log_file"; then
                    error_messages+=("MariaDB dump failed.")
                fi
                ;;
            mysql)
                if ! docker exec "$container_name" mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" marzban --events --triggers  > "$temp_dir/db_backup.sql" 2>>"$log_file"; then
                    error_messages+=("MySQL dump failed.")
                fi
                ;;
            sqlite)
                if [ -f "$sqlite_file" ]; then
                    if ! cp "$sqlite_file" "$temp_dir/db_backup.sqlite" 2>>"$log_file"; then
                        error_messages+=("Failed to copy SQLite database.")
                    fi
                else
                    error_messages+=("SQLite database file not found at $sqlite_file.")
                fi
                ;;
        esac
    fi

    cp "$APP_DIR/.env" "$temp_dir/" 2>>"$log_file"
    cp "$APP_DIR/docker-compose.yml" "$temp_dir/" 2>>"$log_file"
    rsync -av --exclude 'xray-core' --exclude 'mysql' --exclude 'mysql-*' "$DATA_DIR/" "$temp_dir/marzban_data/" >>"$log_file" 2>&1

    if ! tar -czf "$backup_file" -C "$temp_dir" .; then
        error_messages+=("Failed to create backup archive.")
        echo "Failed to create backup archive." >> "$log_file"
    fi

    rm -rf "$temp_dir"

    if [ ${#error_messages[@]} -gt 0 ]; then
        send_backup_error_to_telegram "${error_messages[*]}" "$log_file"
        return 1
    fi
    chmod 600 "$backup_file"
    colorized_echo green "Backup created: $backup_file"
    send_backup_to_telegram "$backup_file"
}



get_xray_core() {
    identify_the_operating_system_and_architecture
    clear

    validate_version() {
        local version="$1"

        local response=$(curl -s "https://api.github.com/repos/XTLS/Xray-core/releases/tags/$version")
        if echo "$response" | grep -q '"message": "Not Found"'; then
            echo "invalid"
        else
            echo "valid"
        fi
    }

    print_menu() {
        clear
        echo -e "\033[1;32m==============================\033[0m"
        echo -e "\033[1;32m      Xray-core Installer     \033[0m"
        echo -e "\033[1;32m==============================\033[0m"
        echo -e "\033[1;33mAvailable Xray-core versions:\033[0m"
        for ((i=0; i<${#versions[@]}; i++)); do
            echo -e "\033[1;34m$((i + 1)):\033[0m ${versions[i]}"
        done
        echo -e "\033[1;32m==============================\033[0m"
        echo -e "\033[1;35mM:\033[0m Enter a version manually"
        echo -e "\033[1;31mQ:\033[0m Quit"
        echo -e "\033[1;32m==============================\033[0m"
    }

    latest_releases=$(curl -s "https://api.github.com/repos/XTLS/Xray-core/releases?per_page=$LAST_XRAY_CORES")

    versions=($(echo "$latest_releases" | grep -oP '"tag_name": "\K(.*?)(?=")'))

    while true; do
        print_menu
        read -p "Choose a version to install (1-${#versions[@]}), or press M to enter manually, Q to quit: " choice

        if [[ "$choice" =~ ^[1-9][0-9]*$ ]] && [ "$choice" -le "${#versions[@]}" ]; then
            choice=$((choice - 1))
            selected_version=${versions[choice]}
            break
        elif [ "$choice" == "M" ] || [ "$choice" == "m" ]; then
            while true; do
                read -p "Enter the version manually (e.g., v1.2.3): " custom_version
                if [ "$(validate_version "$custom_version")" == "valid" ]; then
                    selected_version="$custom_version"
                    break 2
                else
                    echo -e "\033[1;31mInvalid version or version does not exist. Please try again.\033[0m"
                fi
            done
        elif [ "$choice" == "Q" ] || [ "$choice" == "q" ]; then
            echo -e "\033[1;31mExiting.\033[0m"
            exit 0
        else
            echo -e "\033[1;31mInvalid choice. Please try again.\033[0m"
            sleep 2
        fi
    done

    echo -e "\033[1;32mSelected version $selected_version for installation.\033[0m"

    # Check if the required packages are installed
    if ! command -v unzip >/dev/null 2>&1; then
        echo -e "\033[1;33mInstalling required packages...\033[0m"
        detect_os
        install_package unzip
    fi
    if ! command -v wget >/dev/null 2>&1; then
        echo -e "\033[1;33mInstalling required packages...\033[0m"
        detect_os
        install_package wget
    fi

    mkdir -p $DATA_DIR/xray-core
    cd $DATA_DIR/xray-core

    xray_filename="Xray-linux-$ARCH.zip"
    xray_download_url="https://github.com/XTLS/Xray-core/releases/download/${selected_version}/${xray_filename}"

    echo -e "\033[1;33mDownloading Xray-core version ${selected_version}...\033[0m"
    wget -q -O "${xray_filename}" "${xray_download_url}"

    echo -e "\033[1;33mExtracting Xray-core...\033[0m"
    unzip -o "${xray_filename}" >/dev/null 2>&1
    rm "${xray_filename}"
}

# Function to update the Marzban Main core
update_core_command() {
    check_running_as_root
    get_xray_core
    # Change the Marzban core
    xray_executable_path="XRAY_EXECUTABLE_PATH=\"/var/lib/marzban/xray-core/xray\""

    echo "Changing the Marzban core..."
    # Check if the XRAY_EXECUTABLE_PATH string already exists in the .env file
    if ! grep -q "^XRAY_EXECUTABLE_PATH=" "$ENV_FILE"; then
        # If the string does not exist, add it
        echo "${xray_executable_path}" >> "$ENV_FILE"
    else
        # Update the existing XRAY_EXECUTABLE_PATH line
        sed -i "s~^XRAY_EXECUTABLE_PATH=.*~${xray_executable_path}~" "$ENV_FILE"
    fi

    # Restart Marzban
    colorized_echo red "Restarting Marzban..."
    if restart_command -n >/dev/null 2>&1; then
        colorized_echo green "Marzban successfully restarted!"
    else
        colorized_echo red "Marzban restart failed!"
    fi
    colorized_echo blue "Installation of Xray-core version $selected_version completed."
}

install_marzban() {
    local marzban_version=$1
    local database_type=$2
    local source_ref files_url_prefix
    if [ "$database_type" != "mysql" ]; then
        colorized_echo red "Error: This Marzban build supports MySQL only. Use --database mysql."
        exit 1
    fi

    source_ref=$(marzban_script_ref "$marzban_version")
    files_url_prefix="https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${source_ref}"

    umask 077
    mkdir -p "$DATA_DIR"
    mkdir -p "$APP_DIR"

    # Compose is release-owned configuration. Fetch the exact same ref
    # as the installer so fresh installs cannot drift from the tested
    # runtime defaults. Only the requested application image is changed.
    colorized_echo blue "Fetching docker-compose.yml from ${MARZBAN_GITHUB_REPO}@${source_ref}"
    github_download -fsSL "$files_url_prefix/docker-compose.yml" -o "$COMPOSE_FILE"
    yq -i ".services.marzban.image = \"$(marzban_docker_image "${marzban_version}")\"" "$COMPOSE_FILE"
    yq -i ".services.mysql.image = \"${MYSQL_TARGET_IMAGE}\"" "$COMPOSE_FILE"
    apply_runtime_resource_defaults
    colorized_echo green "File saved in $COMPOSE_FILE"

    colorized_echo blue "Fetching .env file"
    github_download -fsSL "$files_url_prefix/.env.example" -o "$ENV_FILE"
    sed -i 's/^# \(XRAY_JSON = .*\)$/\1/' "$ENV_FILE"
    sed -i 's~\(XRAY_JSON = \).*~\1"/var/lib/marzban/xray_config.json"~' "$ENV_FILE"

    prompt_for_marzban_password
    MYSQL_ROOT_PASSWORD=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)

    {
        echo ""
        echo "# Database configuration"
        echo "MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD"
        echo "MYSQL_DATABASE=marzban"
        echo "MYSQL_USER=marzban"
        echo "MYSQL_PASSWORD=$MYSQL_PASSWORD"
        echo ""
        echo "# SQLAlchemy Database URL"
        echo "SQLALCHEMY_DATABASE_URL=\"mysql+pymysql://marzban:${MYSQL_PASSWORD}@127.0.0.1:3306/marzban\""
    } >> "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    colorized_echo green "File saved in $ENV_FILE"

    colorized_echo blue "Fetching xray config file"
    github_download -fsSL "$files_url_prefix/xray_config.json" -o "$DATA_DIR/xray_config.json"
    colorized_echo green "File saved in $DATA_DIR/xray_config.json"
    colorized_echo green "Marzban's files downloaded successfully"
}

up_marzban() {
    mysql_preflight
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" up -d --remove-orphans
}

mysql_compose_data_source() {
    yq -r '.services.mysql.volumes[]? | select(test(":/var/lib/mysql$")) | split(":")[0]' "$COMPOSE_FILE" | head -n 1
}

mysql_preflight() {
    [ -f "$COMPOSE_FILE" ] || return 0
    command -v yq >/dev/null 2>&1 || return 0
    local image data_source expected_source
    image=$(configured_service_image mysql)
    [ -n "$image" ] || return 0
    data_source=$(mysql_compose_data_source)
    expected_source="$DATA_DIR/mysql-${MYSQL_TARGET_VERSION}"
    if [ "$image" != "$MYSQL_TARGET_IMAGE" ]; then
        colorized_echo red "MySQL preflight refused ${image}; required image is ${MYSQL_TARGET_IMAGE}."
        colorized_echo yellow "Run: marzban mysql-upgrade"
        return 1
    fi
    if [ "$data_source" != "$expected_source" ]; then
        colorized_echo red "MySQL preflight refused direct use of ${image} with legacy data directory ${data_source}."
        colorized_echo yellow "Run marzban mysql-upgrade for logical dump/restore. Existing data will not be overwritten."
        return 1
    fi
}

verify_marzban_health() {
    local container_id
    local attempt
    for attempt in $(seq 1 150); do
        container_id=$($COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" ps -q marzban 2>/dev/null)
        if [ -n "$container_id" ] && docker exec "$container_id" python \
            /code/scripts/healthcheck.py --mode internal --timeout 3 \
            >/dev/null 2>&1; then
            if ! docker exec "$container_id" python \
                /code/scripts/healthcheck.py --mode all --timeout 3 \
                >/dev/null 2>&1; then
                colorized_echo yellow "Internal health passed, but the public health check is unavailable"
            fi
            return 0
        fi
        if [ $((attempt % 15)) -eq 0 ]; then
            colorized_echo blue "Waiting for Marzban health check (${attempt}/150)"
        fi
        sleep 2
    done
    if [ -n "$container_id" ]; then
        colorized_echo yellow "Final Marzban health check error:"
        docker exec "$container_id" python \
            /code/scripts/healthcheck.py --mode internal --timeout 3 || true
        mkdir -p "$DATA_DIR"
        docker logs --tail 200 "$container_id" > "$DATA_DIR/update-failed.log" 2>&1 || true
        colorized_echo yellow "Container logs saved to $DATA_DIR/update-failed.log"
    fi
    colorized_echo red "Marzban internal health check failed"
    return 1
}

follow_marzban_logs() {
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" logs -f
}

status_command() {

    # Check if marzban is installed
    if ! is_marzban_installed; then
        echo -n "Status: "
        colorized_echo red "Not Installed"
        exit 1
    fi

    detect_compose

    if ! is_marzban_up; then
        echo -n "Status: "
        colorized_echo blue "Down"
        exit 1
    fi

    echo -n "Status: "
    colorized_echo green "Up"

    json=$($COMPOSE -f $COMPOSE_FILE ps -a --format=json)
    services=$(echo "$json" | jq -r 'if type == "array" then .[] else . end | .Service')
    states=$(echo "$json" | jq -r 'if type == "array" then .[] else . end | .State')
    # Print out the service names and statuses
    for i in $(seq 0 $(expr $(echo $services | wc -w) - 1)); do
        service=$(echo $services | cut -d' ' -f $(expr $i + 1))
        state=$(echo $states | cut -d' ' -f $(expr $i + 1))
        echo -n "- $service: "
        if [ "$state" == "running" ]; then
            colorized_echo green $state
        else
            colorized_echo red $state
        fi
    done
}


prompt_for_marzban_password() {
    colorized_echo cyan "This password will be used to access the database and should be strong."
    colorized_echo cyan "If you do not enter a custom password, a secure 20-character password will be generated automatically."

    # Запрашиваем ввод пароля
    read -p "Enter the password for the marzban user (or press Enter to generate a secure default password): " MYSQL_PASSWORD

    # Генерация 20-значного пароля, если пользователь оставил поле пустым
    if [ -z "$MYSQL_PASSWORD" ]; then
        MYSQL_PASSWORD=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)
        colorized_echo green "A secure password has been generated automatically."
    fi
    if [[ ! "$MYSQL_PASSWORD" =~ ^[A-Za-z0-9_-]+$ ]]; then
        colorized_echo red "Database password must contain only letters, numbers, underscore or hyphen; press Enter for a generated password."
        exit 1
    fi
    colorized_echo green "This password will be recorded in the .env file for future use."

    # Пауза 3 секунды перед продолжением
    sleep 3
}

install_command() {
    check_running_as_root

    # Default values
    database_type="mysql"
    marzban_version="latest"
    marzban_version_set="false"

    # Parse options
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --database)
                database_type="$2"
                shift 2
            ;;
            --dev)
                if [[ "$marzban_version_set" == "true" ]]; then
                    colorized_echo red "Error: Cannot use --dev and --version options simultaneously."
                    exit 1
                fi
                marzban_version="dev"
                marzban_version_set="true"
                shift
            ;;
            --version)
                if [[ "$marzban_version_set" == "true" ]]; then
                    colorized_echo red "Error: Cannot use --dev and --version options simultaneously."
                    exit 1
                fi
                marzban_version="$2"
                marzban_version_set="true"
                shift 2
            ;;
            *)
                echo "Unknown option: $1"
                exit 1
            ;;
        esac
    done

    if [ "$database_type" != "mysql" ]; then
        colorized_echo red "Error: This Marzban build supports MySQL only. Use --database mysql."
        exit 1
    fi

    # Check if marzban is already installed
    if is_marzban_installed; then
        colorized_echo red "Installation already exists at $APP_DIR. Use marzban update; install never overwrites existing configuration."
        exit 1
    fi
    detect_os
    if ! command -v jq >/dev/null 2>&1; then
        install_package jq
    fi
    if ! command -v curl >/dev/null 2>&1; then
        install_package curl
    fi
    if ! command -v tar >/dev/null 2>&1; then
        install_package tar
    fi
    if ! command -v docker >/dev/null 2>&1; then
        install_docker
    fi
    if ! command -v yq >/dev/null 2>&1; then
        install_yq
    fi
    detect_compose
    marzban_version=$(resolve_requested_version "$marzban_version") || exit 1
    # Function to check if a version exists in the GitHub releases
    check_version_exists() {
        local version=$1
        repo_url="$MARZBAN_RELEASES_API"
        if [ "$version" == "latest" ] || [ "$version" == "dev" ]; then
            return 0
        fi

        # Fetch the release data from GitHub API
        response=$(github_download -fsSL "$repo_url") || return 1

        # Check if the response contains the version tag
        if echo "$response" | jq -e ".[] | select(.tag_name == \"${version}\")" > /dev/null; then
            return 0
        else
            return 1
        fi
    }
    # Check if the version is valid and exists
    if [[ "$marzban_version" == "dev" ]] || is_release_version "$marzban_version"; then
        if check_version_exists "$marzban_version"; then
            ensure_marzban_image "$marzban_version" || exit 1
            install_marzban "$marzban_version" "$database_type"
            apply_runtime_resource_defaults
            record_marzban_release_revision || exit 1
            echo "Installing $marzban_version version"
        else
            echo "Version $marzban_version does not exist. Please enter a valid version (e.g. v0.5.2)"
            exit 1
        fi
    else
        echo "Invalid version format. Please enter a valid version (e.g. v5.0.0-rc.9)"
        exit 1
    fi
    if [ "$marzban_version_set" = "true" ]; then
        install_marzban_script_from_repo "$marzban_version"
    else
        install_marzban_script_from_repo "$marzban_version" "$MARZBAN_GITHUB_BRANCH"
    fi
    chmod 600 "$ENV_FILE"
    up_marzban
    if ! verify_marzban_health; then
        exit 1
    fi
    if ! verify_version_integrity "$marzban_version"; then
        exit 1
    fi
    colorized_echo green "Marzban ${marzban_version} installed and healthy."
    colorized_echo yellow "Create the first Owner with: marzban create-owner USERNAME"
}

install_yq() {
    if command -v yq &>/dev/null; then
        colorized_echo green "yq is already installed."
        return
    fi

    identify_the_operating_system_and_architecture

    local base_url="https://github.com/mikefarah/yq/releases/latest/download"
    local yq_binary=""

    case "$ARCH" in
        '64' | 'x86_64')
            yq_binary="yq_linux_amd64"
            ;;
        'arm32-v7a' | 'arm32-v6' | 'arm32-v5' | 'armv7l')
            yq_binary="yq_linux_arm"
            ;;
        'arm64-v8a' | 'aarch64')
            yq_binary="yq_linux_arm64"
            ;;
        '32' | 'i386' | 'i686')
            yq_binary="yq_linux_386"
            ;;
        *)
            colorized_echo red "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac

    local yq_url="${base_url}/${yq_binary}"
    colorized_echo blue "Downloading yq from ${yq_url}..."

    if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
        colorized_echo yellow "Neither curl nor wget is installed. Attempting to install curl."
        install_package curl || {
            colorized_echo red "Failed to install curl. Please install curl or wget manually."
            exit 1
        }
    fi


    if command -v curl &>/dev/null; then
        if curl -L "$yq_url" -o /usr/local/bin/yq; then
            chmod +x /usr/local/bin/yq
            colorized_echo green "yq installed successfully!"
        else
            colorized_echo red "Failed to download yq using curl. Please check your internet connection."
            exit 1
        fi
    elif command -v wget &>/dev/null; then
        if wget -O /usr/local/bin/yq "$yq_url"; then
            chmod +x /usr/local/bin/yq
            colorized_echo green "yq installed successfully!"
        else
            colorized_echo red "Failed to download yq using wget. Please check your internet connection."
            exit 1
        fi
    fi


    if ! echo "$PATH" | grep -q "/usr/local/bin"; then
        export PATH="/usr/local/bin:$PATH"
    fi


    hash -r

    if command -v yq &>/dev/null; then
        colorized_echo green "yq is ready to use."
    elif [ -x "/usr/local/bin/yq" ]; then

        colorized_echo yellow "yq is installed at /usr/local/bin/yq but not found in PATH."
        colorized_echo yellow "You can add /usr/local/bin to your PATH environment variable."
    else
        colorized_echo red "yq installation failed. Please try again or install manually."
        exit 1
    fi
}


down_marzban() {
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" down
}



show_marzban_logs() {
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" logs
}

follow_marzban_logs() {
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" logs -f
}

marzban_cli() {
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" exec -e CLI_PROG_NAME="marzban cli" marzban marzban-cli "$@"
}

create_owner_command() {
    local username="${1:-}"
    local password command_status
    if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && { [ "$1" = "-h" ] || [ "$1" = "--help" ]; }; }; then
        colorized_echo blue "Usage: marzban create-owner [USERNAME]"
        [ "$#" -eq 1 ] && exit 0
        exit 1
    fi
    check_running_as_root
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi
    detect_compose
    if ! is_marzban_up; then
        colorized_echo red "Marzban is not up."
        exit 1
    fi
    if [ -z "$username" ]; then
        read -r -p "Owner username: " username
    fi
    if [ -z "$username" ]; then
        colorized_echo red "Owner username is required."
        exit 1
    fi
    read -r -s -p "Owner password: " password
    echo
    if [ -z "$password" ]; then
        colorized_echo red "Owner password is required."
        exit 1
    fi
    export MARZBAN_ADMIN_PASSWORD="$password"
    if $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" exec -T \
        -e CLI_PROG_NAME="marzban cli" \
        -e MARZBAN_ADMIN_PASSWORD \
        marzban marzban-cli admin bootstrap-owner --username "$username"; then
        command_status=0
    else
        command_status=$?
    fi
    unset MARZBAN_ADMIN_PASSWORD password
    return "$command_status"
}

set_owner_command() {
    if [ "$#" -eq 0 ]; then
        # Let Typer prompt for an existing username. This keeps the documented
        # `marzban set-owner` command usable without requiring hidden CLI flags.
        cli_command admin set-owner
        return
    fi
    if [ "$#" -eq 1 ] && { [ "$1" = "-h" ] || [ "$1" = "--help" ]; }; then
        colorized_echo blue "Usage: marzban set-owner [username]"
        cli_command admin set-owner --help
        return
    fi
    if [ "$#" -eq 1 ]; then
        cli_command admin set-owner --username "$1"
        return
    fi
    if [ "$#" -eq 2 ] && { [ "$1" = "-u" ] || [ "$1" = "--username" ]; }; then
        cli_command admin set-owner --username "$2"
        return
    fi
    colorized_echo red "Usage: marzban set-owner [username]"
    exit 1
}


is_marzban_up() {
    if [ -z "$($COMPOSE -f $COMPOSE_FILE ps -q -a)" ]; then
        return 1
    else
        return 0
    fi
}

uninstall_command() {
    check_running_as_root
    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    read -p "Do you really want to uninstall Marzban? (y/n) "
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        colorized_echo red "Aborted"
        exit 1
    fi

    detect_compose
    if is_marzban_up; then
        down_marzban
    fi
    uninstall_marzban_script
    uninstall_marzban
    uninstall_marzban_docker_images

    read -p "Do you want to remove Marzban's data files too ($DATA_DIR)? (y/n) "
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        colorized_echo green "Marzban uninstalled successfully"
    else
        uninstall_marzban_data_files
        colorized_echo green "Marzban uninstalled successfully"
    fi
}

uninstall_marzban_script() {
    if [ -f "/usr/local/bin/marzban" ]; then
        colorized_echo yellow "Removing marzban script"
        rm "/usr/local/bin/marzban"
    fi
}

uninstall_marzban() {
    if [ -d "$APP_DIR" ]; then
        colorized_echo yellow "Removing directory: $APP_DIR"
        rm -r "$APP_DIR"
    fi
}

uninstall_marzban_docker_images() {
    images=$(docker images | grep marzban | awk '{print $3}')

    if [ -n "$images" ]; then
        colorized_echo yellow "Removing Docker images of Marzban"
        for image in $images; do
            if docker rmi "$image" >/dev/null 2>&1; then
                colorized_echo yellow "Image $image removed"
            fi
        done
    fi
}

uninstall_marzban_data_files() {
    if [ -d "$DATA_DIR" ]; then
        colorized_echo yellow "Removing directory: $DATA_DIR"
        rm -r "$DATA_DIR"
    fi
}

restart_command() {
    help() {
        colorized_echo red "Usage: marzban restart [options]"
        echo
        echo "OPTIONS:"
        echo "  -h, --help        display this help message"
        echo "  -n, --no-logs     do not follow logs after starting"
    }

    local no_logs=false
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -n|--no-logs)
                no_logs=true
            ;;
            -h|--help)
                help
                exit 0
            ;;
            *)
                echo "Error: Invalid option: $1" >&2
                help
                exit 0
            ;;
        esac
        shift
    done

    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    down_marzban
    up_marzban
    if [ "$no_logs" = false ]; then
        follow_marzban_logs
    fi
    colorized_echo green "Marzban successfully restarted!"
}
logs_command() {
    help() {
        colorized_echo red "Usage: marzban logs [options]"
        echo ""
        echo "OPTIONS:"
        echo "  -h, --help        display this help message"
        echo "  -n, --no-follow   do not show follow logs"
    }

    local no_follow=false
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -n|--no-follow)
                no_follow=true
            ;;
            -h|--help)
                help
                exit 0
            ;;
            *)
                echo "Error: Invalid option: $1" >&2
                help
                exit 0
            ;;
        esac
        shift
    done

    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    if ! is_marzban_up; then
        colorized_echo red "Marzban is not up."
        exit 1
    fi

    if [ "$no_follow" = true ]; then
        show_marzban_logs
    else
        follow_marzban_logs
    fi
}

down_command() {

    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    if ! is_marzban_up; then
        colorized_echo red "Marzban's already down"
        exit 1
    fi

    down_marzban
}

cli_command() {
    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    if ! is_marzban_up; then
        colorized_echo red "Marzban is not up."
        exit 1
    fi

    marzban_cli "$@"
}

up_command() {
    help() {
        colorized_echo red "Usage: marzban up [options]"
        echo ""
        echo "OPTIONS:"
        echo "  -h, --help        display this help message"
        echo "  -n, --no-logs     do not follow logs after starting"
    }

    local no_logs=false
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -n|--no-logs)
                no_logs=true
            ;;
            -h|--help)
                help
                exit 0
            ;;
            *)
                echo "Error: Invalid option: $1" >&2
                help
                exit 0
            ;;
        esac
        shift
    done

    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    if is_marzban_up; then
        colorized_echo red "Marzban's already up"
        exit 1
    fi

    up_marzban
    if [ "$no_logs" = false ]; then
        follow_marzban_logs
    fi
}

update_command() {
    help() {
        colorized_echo red "Usage: marzban update [--version <version>]"
        echo ""
        echo "OPTIONS:"
        echo "  -v, --version    update to an exact version or immutable sha-* image tag"
        echo "  -h, --help       display this help message"
    }

    local requested_version="latest"
    local requested_version_set="false"
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -v|--version)
                if [ -z "${2:-}" ]; then
                    colorized_echo red "Error: --version requires a value."
                    exit 1
                fi
                requested_version="$2"
                requested_version_set="true"
                shift 2
            ;;
            -h|--help)
                help
                exit 0
            ;;
            *)
                colorized_echo red "Error: Invalid option: $1"
                help
                exit 1
            ;;
        esac
    done

    if [[ ! "$requested_version" =~ ^[A-Za-z0-9._-]+$ ]]; then
        colorized_echo red "Error: Invalid version tag: $requested_version"
        exit 1
    fi

    check_running_as_root
    # Check if marzban is installed
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi

    detect_compose

    if ! command -v yq >/dev/null 2>&1; then
        install_yq
    fi
    if ! command -v jq >/dev/null 2>&1; then
        install_package jq
    fi

    requested_version=$(resolve_requested_version "$requested_version") || exit 1

    local current_version backup_path source_container
    local configured_source_image app_container running_source_image
    current_version=$(runtime_app_version | tr -d '\r[:space:]')
    if ! is_release_version "$requested_version" || ! is_release_version "v${current_version}"; then
        colorized_echo red "Production update requires a known runtime and exact release version."
        exit 1
    fi
    if [ "$(printf '%s\n%s\n' "$current_version" "${requested_version#v}" | sort -V | head -n 1)" != "$current_version" ]; then
        configured_source_image=$(configured_service_image marzban)
        app_container=$(running_service_container marzban)
        running_source_image=$(docker inspect --format '{{.Config.Image}}' "$app_container" 2>/dev/null || true)
        if ! is_allowed_v1_lineage_transition "$current_version" "$requested_version" "$configured_source_image" "$running_source_image"; then
            colorized_echo red "Application downgrade refused. Restore a matching offline database/configuration backup into an isolated installation."
            exit 1
        fi
        colorized_echo yellow "Verified product-line transition: ${V1_LINEAGE_SOURCE_IMAGE} -> $(marzban_docker_image "$requested_version")."
    fi
    exec 9>"$APP_DIR/.update.lock"
    flock -n 9 || { colorized_echo red "Another update is running."; exit 1; }
    source_container=$(running_service_container mysql)
    [ -n "$source_container" ] || { colorized_echo red "A running MySQL source is required for the pre-update backup."; exit 1; }
    backup_path=$(mktemp -d "$APP_DIR/pre-update.XXXXXXXX")
    chmod 700 "$backup_path"
    cp "$COMPOSE_FILE" "$ENV_FILE" "$backup_path/"
    chmod 600 "$backup_path/.env"
    $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" stop marzban
    if ! docker exec "$source_container" sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --user=root --databases "$MYSQL_DATABASE" --single-transaction --routines --events --triggers --set-gtid-purged=OFF --hex-blob' > "$backup_path/database.sql" || [ ! -s "$backup_path/database.sql" ]; then
        colorized_echo red "Pre-update backup failed; application remains stopped. No upgrade performed."
        exit 1
    fi
    tar --exclude='./mysql' --exclude='./mysql-*' -czf "$backup_path/data.tar.gz" -C "$DATA_DIR" .
    (cd "$backup_path" && sha256sum database.sql data.tar.gz > SHA256SUMS)
    colorized_echo green "Pre-update recovery snapshot: $backup_path"

    local mysql_upgrade_state
    if mysql_upgrade_required_for_update; then
        colorized_echo yellow "MySQL ${MYSQL_UPDATE_SOURCE_VERSION} requires logical migration to ${MYSQL_TARGET_IMAGE}."
        mysql_upgrade_command
    else
        mysql_upgrade_state=$?
        if [ "$mysql_upgrade_state" -eq 2 ]; then
            colorized_echo red "Configured MySQL requires migration, but the current server is not healthy enough to dump safely."
            colorized_echo yellow "Restore the compose image that last worked, start MySQL, then run marzban update again."
            exit 1
        fi
    fi

    # Normalize resource defaults only after the pre-update recovery snapshot
    # and any required logical MySQL migration have completed.
    apply_runtime_resource_defaults

    local previous_image
    local target_image
    previous_image=$(yq -r '.services.marzban.image' "$COMPOSE_FILE")
    target_image=$(marzban_docker_image "$requested_version")
    yq -i ".services.marzban.image = \"${target_image}\"" "$COMPOSE_FILE"
    yq -i '.services.marzban.volumes += ["/opt/marzban/.env:/opt/marzban/.env:ro"] | .services.marzban.volumes |= unique' "$COMPOSE_FILE"

    colorized_echo blue "Pulling Marzban version ${requested_version}"
    if ! update_marzban "$requested_version"; then
        yq -i ".services.marzban.image = \"${previous_image}\"" "$COMPOSE_FILE"
        colorized_echo red "Update failed. Restored previous image: ${previous_image}"
        exit 1
    fi
    record_marzban_release_revision || exit 1

    colorized_echo blue "Restarting Marzban's services"
    down_marzban
    up_marzban

    if ! verify_marzban_health; then
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" stop marzban
        colorized_echo red "Update health check failed. Application left stopped; automatic image rollback is unsafe after migrations."
        colorized_echo yellow "Preserved pre-update recovery snapshot: $backup_path"
        exit 1
    fi

    if [ "$requested_version_set" = "true" ]; then
        update_marzban_script "$requested_version"
    else
        update_marzban_script "$requested_version" "$MARZBAN_GITHUB_BRANCH"
    fi
    if ! verify_version_integrity "$requested_version"; then
        colorized_echo red "Update completed health checks but failed version integrity verification."
        exit 1
    fi
    colorized_echo green "Marzban updated successfully to ${requested_version}"
}

update_marzban_script() {
    local requested_version="${1:-latest}"
    local script_ref="${2:-}"
    colorized_echo blue "Updating marzban script"
    install_marzban_script_from_repo "$requested_version" "$script_ref" || return 1
    colorized_echo green "marzban script updated successfully"
}

update_marzban() {
    local requested_version="$1"
    ensure_marzban_image "$requested_version" || return 1
    $COMPOSE -f $COMPOSE_FILE -p "$APP_NAME" pull mysql
}

mysql_upgrade_required_for_update() {
    local desired_image data_source expected_source
    local container_id
    desired_image=$(yq -r '.services.mysql.image // ""' "$COMPOSE_FILE")
    data_source=$(mysql_compose_data_source)
    expected_source="$DATA_DIR/mysql-${MYSQL_TARGET_VERSION}"
    if [ "$desired_image" = "$MYSQL_TARGET_IMAGE" ] && [ "$data_source" = "$expected_source" ]; then
        return 1
    fi

    container_id=$(mysql_upgrade_container_id)
    if [ -z "$container_id" ]; then
        return 2
    fi
    MYSQL_UPDATE_SOURCE_VERSION=$(mysql_upgrade_server_version "$container_id" 2>/dev/null | tr -d '\r[:space:]' || true)
    if [ -z "$MYSQL_UPDATE_SOURCE_VERSION" ]; then
        return 2
    fi
    return 0
}

mysql_upgrade_container_id() {
    $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" ps -q -a mysql 2>/dev/null
}

mysql_source_version_supported() {
    local source_numeric="${1%%-*}"
    [[ "$source_numeric" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || return 1
    [ "$(printf '%s\n%s\n' "$source_numeric" "$MYSQL_TARGET_VERSION" | sort -V | head -n 1)" = "$source_numeric" ]
}

mysql_upgrade_wait_for_ready() {
    local stage="$1"
    local container_id=""
    local state=""
    local attempt

    for attempt in $(seq 1 90); do
        container_id=$(mysql_upgrade_container_id)
        if [ -n "$container_id" ]; then
            if docker exec "$container_id" sh -c \
                'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin --user=root --host=127.0.0.1 ping --silent' \
                >/dev/null 2>&1; then
                return 0
            fi

            state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
            if [ "$state" = "exited" ] || [ "$state" = "dead" ]; then
                break
            fi
        fi

        if [ $((attempt % 10)) -eq 0 ]; then
            colorized_echo blue "Waiting for MySQL ${stage} (${attempt}/90)"
        fi
        sleep 2
    done

    colorized_echo red "MySQL ${stage} did not become ready."
    if [ -n "$container_id" ]; then
        docker logs --tail 200 "$container_id" || true
    fi
    return 1
}

mysql_upgrade_server_version() {
    local container_id="$1"
    docker exec "$container_id" sh -c \
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --user=root --batch --skip-column-names --execute="SELECT VERSION()"'
}

mysql_upgrade_command() {
    if [ "$#" -ne 0 ]; then
        colorized_echo red "Usage: marzban mysql-upgrade"
        exit 1
    fi

    check_running_as_root
    if ! is_marzban_installed; then
        colorized_echo red "Marzban's not installed!"
        exit 1
    fi
    if [ ! -f "$COMPOSE_FILE" ] || [ ! -f "$ENV_FILE" ]; then
        colorized_echo red "MySQL upgrade requires $COMPOSE_FILE and $ENV_FILE."
        exit 1
    fi

    detect_compose
    if ! command -v yq >/dev/null 2>&1; then
        detect_os
        install_yq
    fi
    if [ "$(yq -r '.services.mysql.image // ""' "$COMPOSE_FILE")" = "" ]; then
        colorized_echo red "The compose file does not define a mysql service."
        exit 1
    fi

    install -d -m 700 "$MYSQL_MIGRATION_DIR"
    local phase=""
    local source_version=""
    local source_image=""
    local source_data=""
    local target_data="$DATA_DIR/mysql-${MYSQL_TARGET_VERSION}"
    local logical_backup="$MYSQL_MIGRATION_DIR/marzban.sql"
    local container_id upgraded_version timestamp

    if [ -f "$MYSQL_MIGRATION_STATE" ]; then
        # Root-owned state contains only values written by this script.
        . "$MYSQL_MIGRATION_STATE"
        colorized_echo blue "Resuming MySQL migration at phase ${phase}."
    else
        container_id=$(mysql_upgrade_container_id)
        if [ -z "$container_id" ] || ! mysql_upgrade_wait_for_ready "source"; then
            colorized_echo red "The source MySQL server must be healthy before migration."
            colorized_echo yellow "Restore its last working image without changing its data directory, then retry."
            exit 1
        fi
        container_id=$(mysql_upgrade_container_id)
        source_version=$(mysql_upgrade_server_version "$container_id" | tr -d '\r[:space:]')
        if ! mysql_source_version_supported "$source_version"; then
            colorized_echo red "MySQL downgrade or unknown source version refused: ${source_version} -> ${MYSQL_TARGET_VERSION}"
            exit 1
        fi
        source_image=$(configured_service_image mysql)
        source_data=$(mysql_compose_data_source)
        if [ -z "$source_data" ] || [ "$source_data" = "/" ]; then
            colorized_echo red "Unsafe or missing source MySQL data mapping: ${source_data}"
            exit 1
        fi
        if [ "$source_image" = "$MYSQL_TARGET_IMAGE" ] && [ "$source_data" = "$target_data" ]; then
            colorized_echo green "MySQL already uses ${MYSQL_TARGET_IMAGE} with the dedicated target data directory."
            return 0
        fi
        if [ -e "$target_data" ] && [ "$(find "$target_data" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
            colorized_echo red "Target MySQL directory is not empty: ${target_data}"
            colorized_echo yellow "Existing target data was not overwritten. Remove or relocate it only after verifying its ownership."
            exit 1
        fi

        timestamp=$(date +"%Y%m%d%H%M%S")
        logical_backup="$APP_DIR/backup/mysql-migration-${timestamp}/marzban.sql"
        install -d -m 700 "$(dirname "$logical_backup")"
        cp "$COMPOSE_FILE" "$(dirname "$logical_backup")/docker-compose.yml.before-migration"
        cp "$ENV_FILE" "$(dirname "$logical_backup")/.env.before-migration"
        chmod 600 "$(dirname "$logical_backup")/.env.before-migration"
        # Quiesce the API and its accounting/scheduler writers before the dump.
        # Keep MySQL running. On failure, leave the application stopped so a
        # retry cannot silently discard writes made after the backup snapshot.
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" stop marzban || exit 1
        colorized_echo blue "Creating consistent logical backup of application database"
        if ! docker exec "$container_id" sh -c \
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --user=root --databases "$MYSQL_DATABASE" --single-transaction --routines --events --triggers --set-gtid-purged=OFF --hex-blob' \
            > "$logical_backup" || [ ! -s "$logical_backup" ]; then
            colorized_echo red "Logical MySQL backup failed or is empty; migration aborted before any data change."
            exit 1
        fi
        sha256sum "$logical_backup" > "$logical_backup.sha256"
        phase="DUMPED"
        printf 'phase=%q\nsource_version=%q\nsource_image=%q\nsource_data=%q\ntarget_data=%q\nlogical_backup=%q\n' \
            "$phase" "$source_version" "$source_image" "$source_data" "$target_data" "$logical_backup" > "$MYSQL_MIGRATION_STATE"
        chmod 600 "$MYSQL_MIGRATION_STATE"
    fi

    if [ "$phase" = "DUMPED" ]; then
        sha256sum -c "$logical_backup.sha256" >/dev/null || { colorized_echo red "Backup checksum validation failed."; exit 1; }
        down_marzban
        install -d -m 700 "$target_data"
        yq -i ".services.mysql.image = \"${MYSQL_TARGET_IMAGE}\"" "$COMPOSE_FILE"
        yq -i ".services.mysql.volumes = [\"${target_data}:/var/lib/mysql\"]" "$COMPOSE_FILE"
        phase="TARGET_CONFIGURED"
        sed -i 's/^phase=.*/phase=TARGET_CONFIGURED/' "$MYSQL_MIGRATION_STATE"
    fi

    if [ "$phase" = "TARGET_CONFIGURED" ]; then
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" pull mysql
        $COMPOSE -f "$COMPOSE_FILE" -p "$APP_NAME" up -d mysql
        mysql_upgrade_wait_for_ready "$MYSQL_TARGET_VERSION" || exit 1
        container_id=$(mysql_upgrade_container_id)
        upgraded_version=$(mysql_upgrade_server_version "$container_id" | tr -d '\r[:space:]')
        [ "$upgraded_version" = "$MYSQL_TARGET_VERSION" ] || {
            colorized_echo red "Expected MySQL ${MYSQL_TARGET_VERSION}, got ${upgraded_version}."
            exit 1
        }
        sha256sum -c "$logical_backup.sha256" >/dev/null || { colorized_echo red "Backup checksum validation failed before restore."; exit 1; }
        colorized_echo blue "Restoring logical backup into fresh ${MYSQL_TARGET_IMAGE} data directory"
        if ! docker exec -i "$container_id" sh -c \
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root' < "$logical_backup"; then
            colorized_echo red "Logical restore failed. Source data remains untouched at ${source_data}."
            exit 1
        fi
        phase="RESTORED"
        sed -i 's/^phase=.*/phase=RESTORED/' "$MYSQL_MIGRATION_STATE"
    fi

    if [ "$phase" = "RESTORED" ]; then
        up_marzban
        mysql_upgrade_wait_for_ready "$MYSQL_TARGET_VERSION" || exit 1
        verify_marzban_health || exit 1
        phase="COMPLETE"
        sed -i 's/^phase=.*/phase=COMPLETE/' "$MYSQL_MIGRATION_STATE"
    fi

    colorized_echo green "MySQL migrated successfully: ${source_version} -> ${MYSQL_TARGET_VERSION}"
    colorized_echo green "Logical backup: ${logical_backup}"
    colorized_echo green "Original data preserved: ${source_data}"
}

node_is_installed() {
    [ -f "$NODE_COMPOSE_FILE" ] && [ -f "$NODE_ENV_FILE" ]
}

node_prepare_host() {
    detect_os
    if ! command -v jq >/dev/null 2>&1; then
        install_package jq
    fi
    if ! command -v curl >/dev/null 2>&1; then
        install_package curl
    fi
    if ! command -v tar >/dev/null 2>&1; then
        install_package tar
    fi
    if ! command -v openssl >/dev/null 2>&1; then
        install_package openssl
    fi
    if ! command -v docker >/dev/null 2>&1; then
        install_docker
    fi
    detect_compose
}

node_validate_port() {
    local value="$1"
    local name="$2"
    if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
        colorized_echo red "$name must be an integer between 1 and 65535."
        return 1
    fi
}

node_validate_event_rows() {
    local value="$1"
    if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1000 ] || [ "$value" -gt 1000000 ]; then
        colorized_echo red "--event-max-rows must be between 1000 and 1000000."
        return 1
    fi
}

node_validate_client_cert() {
    local path="$1"
    if [ -z "$path" ] || [ ! -f "$path" ]; then
        colorized_echo red "A readable panel certificate is required with --client-cert-file."
        return 1
    fi
    if ! openssl x509 -in "$path" -noout >/dev/null 2>&1; then
        colorized_echo red "--client-cert-file is not a valid X.509 PEM certificate."
        return 1
    fi
}

NODE_INTERACTIVE_CERT_FILE=""

node_prompt_client_cert() {
    local temp_file line found_begin="false" found_end="false" line_count=0
    temp_file=$(mktemp /tmp/marzban-node-cert.XXXXXXXX)
    chmod 600 "$temp_file"

    colorized_echo blue "Paste the Marzban Node certificate from the Master panel."
    colorized_echo yellow "Paste the full PEM block including BEGIN/END CERTIFICATE lines. Input finishes automatically after END CERTIFICATE."

    while IFS= read -r line; do
        line="${line%$'\r'}"
        if [ "$found_begin" = "false" ]; then
            [ "$line" = "-----BEGIN CERTIFICATE-----" ] || continue
            found_begin="true"
        fi
        printf '%s\n' "$line" >> "$temp_file"
        line_count=$((line_count + 1))
        if [ "$line" = "-----END CERTIFICATE-----" ]; then
            found_end="true"
            break
        fi
        if [ "$line_count" -ge 256 ]; then
            break
        fi
    done

    if [ "$found_begin" != "true" ] || [ "$found_end" != "true" ]; then
        rm -f "$temp_file"
        colorized_echo red "Certificate paste was incomplete. Paste the full certificate from BEGIN CERTIFICATE through END CERTIFICATE."
        return 1
    fi
    if ! openssl x509 -in "$temp_file" -noout >/dev/null 2>&1; then
        rm -f "$temp_file"
        colorized_echo red "The pasted certificate is not a valid X.509 PEM certificate."
        return 1
    fi

    NODE_INTERACTIVE_CERT_FILE="$temp_file"
}

node_source_ref_path() {
    local requested_version="$1"
    local ref
    ref=$(marzban_script_ref "$requested_version")
    if [ "$ref" = "$MARZBAN_GITHUB_BRANCH" ]; then
        printf 'refs/heads/%s\n' "$ref"
    else
        printf '%s\n' "$ref"
    fi
}

install_node_script_from_repo() {
    local requested_version="$1"
    local ref_path script_url temp_script
    ref_path=$(node_source_ref_path "$requested_version")
    script_url="https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/${MARZBAN_SCRIPTS_PATH}"
    temp_script=$(mktemp)
    if ! github_download -fsSL "$script_url" -o "$temp_script"; then
        rm -f "$temp_script"
        colorized_echo red "Could not download Node CLI from ${requested_version}."
        return 1
    fi
    if ! bash -n "$temp_script"; then
        rm -f "$temp_script"
        colorized_echo red "Downloaded Node CLI failed syntax validation."
        return 1
    fi
    if ! install -m 755 "$temp_script" "$NODE_SCRIPT_PATH"; then
        rm -f "$temp_script"
        return 1
    fi
    # A co-located panel owns /usr/local/bin/marzban and its CLI metadata.
    # Never replace either from a Node install/update. Node-only hosts keep the
    # familiar `marzban node ...` command in addition to `marzban-node node ...`.
    if ! is_marzban_installed; then
        if ! install -m 755 "$temp_script" /usr/local/bin/marzban; then
            rm -f "$temp_script"
            return 1
        fi
    fi
    rm -f "$temp_script"
    printf '%s\n' "$requested_version" > "$NODE_CLI_VERSION_FILE"
    chmod 644 "$NODE_CLI_VERSION_FILE"
    colorized_echo green "Node CLI installed at $NODE_SCRIPT_PATH"
}

node_source_supports_runtime() {
    local requested_version="$1"
    local ref_path
    ref_path=$(node_source_ref_path "$requested_version")
    github_download -fsSL \
        "https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/node_runtime/main.py" \
        -o /dev/null 2>/dev/null
}

node_fetch_compose() {
    local requested_version="$1"
    local ref_path
    ref_path=$(node_source_ref_path "$requested_version")
    install -d -m 700 "$NODE_APP_DIR"
    github_download -fsSL \
        "https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/${MARZBAN_NODE_COMPOSE_PATH}" \
        -o "$NODE_COMPOSE_FILE"
    chmod 600 "$NODE_COMPOSE_FILE"
}

node_env_value() {
    local key="$1"
    local fallback="$2"
    local value=""
    if [ -f "$NODE_ENV_FILE" ]; then
        value=$(sed -n "s/^${key}=//p" "$NODE_ENV_FILE" | tail -n 1)
    fi
    printf '%s\n' "${value:-$fallback}"
}

node_write_env() {
    local requested_version="$1"
    local service_port="$2"
    local api_port="$3"
    local event_max_rows="$4"
    umask 077
    cat > "$NODE_ENV_FILE" <<EOF
MARZBAN_NODE_IMAGE=$(marzban_docker_image "$requested_version")
NODE_RUNTIME_VERSION=$requested_version
NODE_RUNTIME_PORT=$service_port
XRAY_API_PORT=$api_port
EVENT_MAX_ROWS=$event_max_rows
EOF
    chmod 600 "$NODE_ENV_FILE"
}

node_compose() {
    $COMPOSE --env-file "$NODE_ENV_FILE" -f "$NODE_COMPOSE_FILE" -p "$NODE_APP_NAME" "$@"
}

node_service_container() {
    node_compose ps -q marzban-node 2>/dev/null
}

node_wait_for_health() {
    local container_id=""
    local state=""
    local health=""
    local attempt
    for attempt in $(seq 1 45); do
        container_id=$(node_service_container)
        if [ -n "$container_id" ]; then
            state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
            health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id" 2>/dev/null || true)
            if [ "$state" = "running" ] && { [ "$health" = "healthy" ] || [ -z "$health" ]; }; then
                return 0
            fi
            if [ "$state" = "exited" ] || [ "$state" = "dead" ]; then
                break
            fi
        fi
        sleep 2
    done
    colorized_echo red "Marzban Node did not become healthy."
    if [ -n "$container_id" ]; then
        docker logs --tail 200 "$container_id" || true
    fi
    return 1
}

verify_node_version_integrity() {
    local expected_version="$1"
    local expected_image expected_revision container_id running_image image_id running_revision
    expected_image=$(marzban_docker_image "$expected_version")
    expected_revision=$(release_commit_for_version "$expected_version")
    [[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] || {
        colorized_echo red "Node integrity failed: release source revision is unavailable."
        return 1
    }
    container_id=$(node_service_container)
    [ -n "$container_id" ] || { colorized_echo red "Node integrity failed: container is not running."; return 1; }
    running_image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
    [ "$running_image" = "$expected_image" ] || {
        colorized_echo red "Node integrity failed: running image is ${running_image:-unavailable}, expected ${expected_image}."
        return 1
    }
    image_id=$(docker inspect --format '{{.Image}}' "$container_id" 2>/dev/null || true)
    running_revision=$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image_id" 2>/dev/null || true)
    [ "$running_revision" = "$expected_revision" ] || {
        colorized_echo red "Node integrity failed: source revision is ${running_revision:-unavailable}, expected ${expected_revision}."
        return 1
    }
    printf '%s\n' "$expected_revision" > "$NODE_RELEASE_REVISION_FILE"
    printf '%s\n' "$expected_version" > "$NODE_CLI_VERSION_FILE"
    chmod 644 "$NODE_RELEASE_REVISION_FILE" "$NODE_CLI_VERSION_FILE"
    colorized_echo green "Node image integrity verified for ${expected_version}."
}

node_install_command() {
    local requested_version="latest"
    local client_cert_file=""
    local service_port="62050"
    local api_port="62051"
    local event_max_rows="20000"
    NODE_INTERACTIVE_CERT_FILE=""
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -v|--version)
                [ -n "${2:-}" ] || { colorized_echo red "--version requires a value."; return 1; }
                requested_version="$2"; shift 2 ;;
            --client-cert-file)
                [ -n "${2:-}" ] || { colorized_echo red "--client-cert-file requires a path."; return 1; }
                client_cert_file="$2"; shift 2 ;;
            --service-port)
                [ -n "${2:-}" ] || { colorized_echo red "--service-port requires a value."; return 1; }
                service_port="$2"; shift 2 ;;
            --api-port)
                [ -n "${2:-}" ] || { colorized_echo red "--api-port requires a value."; return 1; }
                api_port="$2"; shift 2 ;;
            --event-max-rows)
                [ -n "${2:-}" ] || { colorized_echo red "--event-max-rows requires a value."; return 1; }
                event_max_rows="$2"; shift 2 ;;
            -h|--help)
                echo "Usage: marzban node install [--version VERSION] [--client-cert-file PATH] [--service-port PORT] [--api-port PORT] [--event-max-rows ROWS]"
                return 0 ;;
            *)
                colorized_echo red "Unknown node install option: $1"
                return 1 ;;
        esac
    done

    check_running_as_root
    if node_is_installed; then
        colorized_echo red "Marzban Node already exists at $NODE_APP_DIR. Use: marzban node update"
        return 1
    fi
    node_prepare_host
    requested_version=$(resolve_requested_version "$requested_version") || return 1
    if ! is_release_version "$requested_version"; then
        colorized_echo red "Built-in Node deployment accepts published release versions only."
        return 1
    fi
    node_validate_port "$service_port" "--service-port" || return 1
    node_validate_port "$api_port" "--api-port" || return 1
    [ "$service_port" != "$api_port" ] || { colorized_echo red "Node service and Xray API ports must differ."; return 1; }
    node_validate_event_rows "$event_max_rows" || return 1
    if [ -n "$client_cert_file" ]; then
        node_validate_client_cert "$client_cert_file" || return 1
    fi
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    ensure_marzban_image "$requested_version" || return 1

    if [ -z "$client_cert_file" ]; then
        node_prompt_client_cert || return 1
        client_cert_file="$NODE_INTERACTIVE_CERT_FILE"
    fi

    install -d -m 700 "$NODE_APP_DIR" "$NODE_DATA_DIR"
    if ! install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"; then
        [ -n "$NODE_INTERACTIVE_CERT_FILE" ] && rm -f "$NODE_INTERACTIVE_CERT_FILE"
        NODE_INTERACTIVE_CERT_FILE=""
        return 1
    fi
    if [ -n "$NODE_INTERACTIVE_CERT_FILE" ]; then
        rm -f "$NODE_INTERACTIVE_CERT_FILE"
        NODE_INTERACTIVE_CERT_FILE=""
    fi
    node_fetch_compose "$requested_version" || return 1
    node_write_env "$requested_version" "$service_port" "$api_port" "$event_max_rows"
    node_compose up -d --remove-orphans || return 1
    node_wait_for_health || return 1
    verify_node_version_integrity "$requested_version" || return 1
    install_node_script_from_repo "$requested_version" || return 1
    colorized_echo green "Marzban Node ${requested_version} is installed and healthy."
    colorized_echo blue "Node data: $NODE_DATA_DIR"
    colorized_echo blue "Panel certificate: $NODE_CLIENT_CERT_FILE"
}

node_update_command() {
    local requested_version="latest"
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -v|--version)
                [ -n "${2:-}" ] || { colorized_echo red "--version requires a value."; return 1; }
                requested_version="$2"; shift 2 ;;
            -h|--help)
                echo "Usage: marzban node update [--version VERSION]"
                return 0 ;;
            *)
                colorized_echo red "Unknown node update option: $1"
                return 1 ;;
        esac
    done

    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    node_prepare_host
    requested_version=$(resolve_requested_version "$requested_version") || return 1
    if ! is_release_version "$requested_version"; then
        colorized_echo red "Built-in Node deployment accepts published release versions only."
        return 1
    fi
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    [ -f "$NODE_CLIENT_CERT_FILE" ] || { colorized_echo red "Stored panel certificate is missing: $NODE_CLIENT_CERT_FILE"; return 1; }
    node_validate_client_cert "$NODE_CLIENT_CERT_FILE" || return 1
    ensure_marzban_image "$requested_version" || return 1

    local service_port api_port event_max_rows backup_dir
    service_port=$(node_env_value NODE_RUNTIME_PORT 62050)
    api_port=$(node_env_value XRAY_API_PORT 62051)
    event_max_rows=$(node_env_value EVENT_MAX_ROWS 20000)
    node_validate_port "$service_port" "NODE_RUNTIME_PORT" || return 1
    node_validate_port "$api_port" "XRAY_API_PORT" || return 1
    node_validate_event_rows "$event_max_rows" || return 1
    backup_dir="$NODE_APP_DIR/update-backup-$(date +%Y%m%d%H%M%S)"
    install -d -m 700 "$backup_dir"
    cp "$NODE_COMPOSE_FILE" "$backup_dir/docker-compose.yml"
    cp "$NODE_ENV_FILE" "$backup_dir/.env"
    chmod 600 "$backup_dir/.env" "$backup_dir/docker-compose.yml"

    node_fetch_compose "$requested_version" || return 1
    node_write_env "$requested_version" "$service_port" "$api_port" "$event_max_rows"
    if ! node_compose up -d --remove-orphans || ! node_wait_for_health || ! verify_node_version_integrity "$requested_version"; then
        colorized_echo red "Node update failed. Previous configuration is preserved at $backup_dir."
        return 1
    fi
    install_node_script_from_repo "$requested_version" || return 1
    colorized_echo green "Marzban Node updated successfully to ${requested_version}."
}

node_status_command() {
    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    detect_compose
    local container_id state health image version revision
    container_id=$(node_service_container)
    if [ -z "$container_id" ]; then
        colorized_echo red "Marzban Node is down."
        return 1
    fi
    state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
    health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id" 2>/dev/null || true)
    image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
    version=$(node_env_value NODE_RUNTIME_VERSION unknown)
    revision=$(cat "$NODE_RELEASE_REVISION_FILE" 2>/dev/null || true)
    echo "Status: ${state:-unknown}"
    echo "Health: ${health:-unavailable}"
    echo "Runtime version: ${version}"
    echo "Image: ${image:-unavailable}"
    echo "Source revision: ${revision:-unavailable}"
}

node_logs_command() {
    local follow="true"
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -n|--no-follow) follow="false"; shift ;;
            -h|--help)
                echo "Usage: marzban node logs [--no-follow]"
                return 0 ;;
            *) colorized_echo red "Unknown node logs option: $1"; return 1 ;;
        esac
    done
    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    detect_compose
    if [ "$follow" = "true" ]; then
        node_compose logs -f marzban-node
    else
        node_compose logs marzban-node
    fi
}

node_command() {
    local action="${1:-help}"
    [ "$#" -gt 0 ] && shift || true
    case "$action" in
        install) node_install_command "$@" ;;
        update) node_update_command "$@" ;;
        status) node_status_command "$@" ;;
        logs) node_logs_command "$@" ;;
        help|-h|--help)
            echo "Usage: marzban node <install|update|status|logs> [options]"
            ;;
        *)
            colorized_echo red "Unknown node command: $action"
            echo "Usage: marzban node <install|update|status|logs> [options]"
            return 1
            ;;
    esac
}

rollback_command() {
    if [ "$#" -ne 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        colorized_echo red "Usage: marzban rollback <version>"
        echo "Example: marzban rollback v4.3.0"
        [ "$#" -eq 1 ] && exit 0
        exit 1
    fi

    colorized_echo yellow "Rolling back the application image to $1. Database migrations are not downgraded."
    update_command --version "$1"
}

check_editor() {
    if [ -z "$EDITOR" ]; then
        if command -v nano >/dev/null 2>&1; then
            EDITOR="nano"
            elif command -v vi >/dev/null 2>&1; then
            EDITOR="vi"
        else
            detect_os
            install_package nano
            EDITOR="nano"
        fi
    fi
}


edit_command() {
    detect_os
    check_editor
    if [ -f "$COMPOSE_FILE" ]; then
        $EDITOR "$COMPOSE_FILE"
    else
        colorized_echo red "Compose file not found at $COMPOSE_FILE"
        exit 1
    fi
}

edit_env_command() {
    detect_os
    check_editor
    if [ -f "$ENV_FILE" ]; then
        $EDITOR "$ENV_FILE"
    else
        colorized_echo red "Environment file not found at $ENV_FILE"
        exit 1
    fi
}

usage() {
    local script_name="${0##*/}"
    colorized_echo blue "=============================="
    colorized_echo magenta "           Marzban Help"
    colorized_echo blue "=============================="
    colorized_echo cyan "Usage:"
    echo "  ${script_name} [command]"
    echo

    colorized_echo cyan "Commands:"
    colorized_echo yellow "  up              $(tput sgr0)– Start services"
    colorized_echo yellow "  down            $(tput sgr0)– Stop services"
    colorized_echo yellow "  restart         $(tput sgr0)– Restart services"
    colorized_echo yellow "  status          $(tput sgr0)– Show status"
    colorized_echo yellow "  logs            $(tput sgr0)– Show logs"
    colorized_echo yellow "  cli             $(tput sgr0)– Marzban CLI"
    colorized_echo yellow "  set-owner       $(tput sgr0)– Select Owner and migrate the admin hierarchy"
    colorized_echo yellow "  create-owner    $(tput sgr0)– Create or repair the first Owner"
    colorized_echo yellow "  install         $(tput sgr0)– Install Marzban"
    colorized_echo yellow "  update          $(tput sgr0)– Update to latest or an exact version"
    colorized_echo yellow "  rollback        $(tput sgr0)– Roll back to an exact version"
    colorized_echo yellow "  version         $(tput sgr0)– Show CLI, runtime, image, and digest integrity"
    colorized_echo yellow "  mysql-upgrade   $(tput sgr0)– Safely migrate MySQL to ${MYSQL_TARGET_IMAGE}"
    colorized_echo yellow "  node            $(tput sgr0)– Install, update, inspect, or read logs from built-in Node Runtime V2"
    colorized_echo yellow "  uninstall       $(tput sgr0)– Uninstall Marzban"
    colorized_echo yellow "  install-script  $(tput sgr0)– Install Marzban script"
    colorized_echo yellow "  backup          $(tput sgr0)– Manual backup launch"
    colorized_echo yellow "  backup-service  $(tput sgr0)– Marzban Backupservice to backup to TG, and a new job in crontab"
    colorized_echo yellow "  core-update     $(tput sgr0)– Update/Change Xray core"
    colorized_echo yellow "  edit            $(tput sgr0)– Edit docker-compose.yml (via nano or vi editor)"
    colorized_echo yellow "  edit-env        $(tput sgr0)– Edit environment file (via nano or vi editor)"
    colorized_echo yellow "  help            $(tput sgr0)– Show this help message"


    echo
    colorized_echo cyan "Directories:"
    colorized_echo magenta "  App directory: $APP_DIR"
    colorized_echo magenta "  Data directory: $DATA_DIR"
    colorized_echo blue "================================"
    echo
}

if [[ -z "${BASH_SOURCE[0]:-}" || "${BASH_SOURCE[0]}" == "$0" ]]; then
case "$1" in
    up)
        shift; up_command "$@";;
    down)
        shift; down_command "$@";;
    restart)
        shift; restart_command "$@";;
    status)
        shift; status_command "$@";;
    version)
        shift; version_command "$@";;
    logs)
        shift; logs_command "$@";;
    cli)
        shift; cli_command "$@";;
    set-owner)
        shift; set_owner_command "$@";;
    create-owner)
        shift; create_owner_command "$@";;
    backup)
        shift; backup_command "$@";;
    backup-service)
        shift; backup_service "$@";;
    install)
        shift; install_command "$@";;
    update)
        shift; update_command "$@";;
    rollback)
        shift; rollback_command "$@";;
    mysql-upgrade)
        shift; mysql_upgrade_command "$@";;
    node)
        shift; node_command "$@";;
    uninstall)
        shift; uninstall_command "$@";;
    install-script)
        shift; install_marzban_script_from_repo "$@";;
    core-update)
        shift; update_core_command "$@";;
    edit)
        shift; edit_command "$@";;
    edit-env)
        shift; edit_env_command "$@";;
    help|*)
        usage;;
esac
fi
