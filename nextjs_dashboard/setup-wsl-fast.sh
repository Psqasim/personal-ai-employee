#!/bin/bash
# WSL2 Fast Setup: symlink node_modules + .next to native Linux FS
# Gives 10-40x speedup for Next.js startup on /mnt/d/ projects
#
# How it works:
# - node_modules and .next live on ext4 (~3.7s startup vs 160s on /mnt/d/)
# - Source code stays on /mnt/d/ for Windows editor access
# - Turbopack root is set to '/' in next.config.ts to support cross-FS symlinks
#
# Usage: bash setup-wsl-fast.sh
# After npm install: bash setup-wsl-fast.sh --post-install
set -e

CACHE_DIR="$HOME/nextjs_cache"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$CACHE_DIR"

setup_symlink() {
  local name=$1
  local src="$PROJECT_DIR/$name"
  local dst="$CACHE_DIR/$name"

  if [ -L "$src" ]; then
    echo "  $name: already symlinked -> $(readlink "$src")"
    return
  fi

  if [ -d "$src" ]; then
    echo "  $name: copying to Linux FS via tar-pipe (this takes a while on first run)..."
    rm -rf "$dst"
    (cd "$PROJECT_DIR" && tar cf - "$name") | (cd "$CACHE_DIR" && tar xf -)
    rm -rf "$src"
    ln -s "$dst" "$src"
    echo "  $name: symlinked."
  else
    echo "  $name: creating fresh symlink (will be populated by npm install / next build)."
    mkdir -p "$dst"
    ln -s "$dst" "$src"
  fi
}

# --post-install: called after npm install (which replaces symlinks with real dirs)
if [ "$1" = "--post-install" ]; then
  echo "Post-install: re-establishing symlinks..."
  for name in node_modules .next; do
    if [ -d "$PROJECT_DIR/$name" ] && [ ! -L "$PROJECT_DIR/$name" ]; then
      echo "  $name: moving to Linux FS..."
      rm -rf "$CACHE_DIR/$name"
      (cd "$PROJECT_DIR" && tar cf - "$name") | (cd "$CACHE_DIR" && tar xf -)
      rm -rf "$PROJECT_DIR/$name"
      ln -s "$CACHE_DIR/$name" "$PROJECT_DIR/$name"
      echo "  $name: re-symlinked."
    else
      echo "  $name: OK (already symlinked or absent)."
    fi
  done
  echo "Done."
  exit 0
fi

echo "WSL2 Fast Setup for Next.js Dashboard"
echo "======================================"
echo "Cache dir: $CACHE_DIR"
echo ""

setup_symlink "node_modules"
setup_symlink ".next"

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. npm install        (installs deps on Linux FS via symlink)"
echo "  2. npm run build      (builds on Linux FS via symlink)"
echo "  3. npm run start      (should show 'Ready' in ~4s)"
echo ""
echo "If you run 'npm install' and it replaces the symlink, run:"
echo "  bash setup-wsl-fast.sh --post-install"
