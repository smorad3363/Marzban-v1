#!/usr/bin/env python3
"""Deploy a reviewed static UI without upgrading or modifying the backend image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tarfile
import tempfile
import time
import urllib.request

TARGET_IP = "167.233.62.226"
BASELINE_VERSION = "1.1.21"
PANEL_ROOT = Path("/opt/marzban")
CONTAINER = "marzban-marzban-1"
MYSQL = "marzban-mysql-1"


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def bundle_digest(build):
    entries = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(build).as_posix()}\n" for p in sorted(build.rglob("*")) if p.is_file()]
    return hashlib.sha256("".join(entries).encode()).hexdigest()


def mount_frontend(compose, build):
    """Change exactly one static-file mount; preserve every other Compose byte."""
    lines = compose.splitlines(keepends=True)
    service = next((i for i, line in enumerate(lines) if re.fullmatch(r"  marzban:\s*\n?", line)), None)
    if service is None:
        raise ValueError("Expected the existing marzban service")
    end = next((i for i in range(service + 1, len(lines)) if re.match(r"  \S", lines[i])), len(lines))
    volumes = [i for i in range(service + 1, end) if re.fullmatch(r"    volumes:\s*\n?", lines[i])]
    if len(volumes) != 1:
        raise ValueError("Expected one block-style marzban volumes list")
    start = volumes[0] + 1
    stop = next((i for i in range(start, end) if re.match(r"    \S", lines[i])), end)
    block = lines[start:stop]
    if not any(re.match(r"      - ", line) for line in block):
        raise ValueError("Expected the existing block-style volume entries")
    if any("/code/app/dashboard/build" in line for i, line in enumerate(lines) if i < start or i >= stop):
        raise ValueError("Unexpected static mount outside the marzban volumes list")
    original = [line for line in block if ":/code/app/dashboard/build" not in line]
    new_line = f"      - {build}:/code/app/dashboard/build:ro\n"
    return "".join(lines[:start] + original + [new_line] + lines[stop:])


def inspect(name, field):
    return command("docker", "inspect", "--format", "{{" + field + "}}", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--target-ip", required=True, choices=[TARGET_IP])
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit) or not re.fullmatch(r"[0-9a-f]{64}", args.bundle_sha256):
        parser.error("Full immutable commit and bundle SHA256 are required")
    if os.geteuid() != 0:
        parser.error("Run as root on the specified master")
    if not re.search(r"\binet " + re.escape(TARGET_IP) + r"/", command("ip", "-4", "-o", "addr", "show", "dev", "eth0")):
        parser.error("Server identity mismatch; refusing deployment")
    compose = PANEL_ROOT / "docker-compose.yml"
    original_compose = compose.read_text()
    environment = PANEL_ROOT / ".env"
    env_hash = hashlib.sha256(environment.read_bytes()).hexdigest()
    backend_image = inspect(CONTAINER, ".Image")
    mysql_id = inspect(MYSQL, ".Id")
    version = command("docker", "exec", CONTAINER, "python", "-c", "import ast,pathlib; t=ast.parse(pathlib.Path('/code/app/__init__.py').read_text()); print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='__version__' for x in n.targets)))")
    if version != BASELINE_VERSION:
        parser.error("Review this UI against the installed backend version before deploying")
    release = PANEL_ROOT / "frontend-releases" / args.commit
    release.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ui-stage-", dir=release.parent) as tmp:
        stage = Path(tmp)
        archive = stage / "source.tar.gz"
        url = f"https://github.com/smorad3363/Marzban-v1/archive/{args.commit}.tar.gz"
        with urllib.request.urlopen(url, timeout=90) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        prefix = f"Marzban-v1-{args.commit}/app/dashboard/build/"
        with tarfile.open(archive) as tar:
            for member in tar:
                if not member.name.startswith(prefix) or not member.isfile():
                    continue
                relative = Path(member.name[len(prefix):])
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Unsafe archive path")
                target = stage / "build" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
        build = stage / "build"
        if bundle_digest(build) != args.bundle_sha256:
            raise ValueError("The downloaded static bundle does not match the reviewed SHA256")
        if not (build / "index.html").is_file() or not (build / "404.html").is_file():
            raise ValueError("Incomplete frontend bundle")
        metadata = json.loads((build / "statics/console-ui.json").read_text())
        if metadata["backend_baseline"] != BASELINE_VERSION:
            raise ValueError("Frontend/backend compatibility mismatch")
        if release.exists():
            if bundle_digest(release / "build") != args.bundle_sha256:
                raise ValueError("Immutable release directory differs")
        else:
            release.mkdir()
            shutil.move(str(build), release / "build")
    if compose.read_text() != original_compose:
        raise RuntimeError("Compose changed during preparation; refusing to overwrite it")
    updated = mount_frontend(original_compose, release / "build")
    backup = PANEL_ROOT / "frontend-backups" / time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    backup.mkdir(parents=True, mode=0o700)
    (backup / "docker-compose.yml").write_text(original_compose)
    command("docker", "cp", f"{CONTAINER}:/code/app/dashboard/build", str(backup / "build"))
    (backup / "deployment.json").write_text(json.dumps({"commit": args.commit, "bundle_sha256": args.bundle_sha256, "backend_image": backend_image, "mysql_id": mysql_id, "env_sha256": env_hash}, indent=2))
    compose_args = ["docker", "compose", "-f", str(compose)]
    activated = False
    try:
        temporary = compose.with_suffix(".yml.ui-tmp")
        temporary.write_text(updated)
        shutil.copymode(compose, temporary)
        os.replace(temporary, compose)
        activated = True
        command(*compose_args, "config", "--quiet")
        command(*compose_args, "up", "-d", "--no-deps", "--force-recreate", "marzban")
        for attempt in range(20):
            try:
                # The origin certificate is intentionally used only on loopback, never for remote downloads.
                request = urllib.request.Request("https://127.0.0.1/dashboard/", headers={"Host": "newmaster.javaher.shop"})
                with urllib.request.urlopen(request, timeout=3, context=ssl._create_unverified_context()) as response:
                    served = response.read()
                if hashlib.sha256(served).hexdigest() == hashlib.sha256((release / "build/index.html").read_bytes()).hexdigest():
                    break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise RuntimeError("The panel did not serve the reviewed index")
        assert inspect(CONTAINER, ".Image") == backend_image, "Backend image changed"
        assert inspect(MYSQL, ".Id") == mysql_id, "Database container changed"
        assert hashlib.sha256(environment.read_bytes()).hexdigest() == env_hash, "Environment changed"
    except Exception:
        if activated:
            compose.write_text(original_compose)
            command(*compose_args, "up", "-d", "--no-deps", "--force-recreate", "marzban")
        raise
    print(json.dumps({"ui": metadata["version"], "backend": version, "commit": args.commit, "backup": str(backup), "database_container_unchanged": True, "environment_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
