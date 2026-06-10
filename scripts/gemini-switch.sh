#!/usr/bin/env bash
# gemini-switch.sh - swap between Gemini CLI OAuth accounts
#
# Two named stashes live in ~/.gemini-stash/<name>/{oauth_creds.json,google_accounts.json}.
# The "active" account is whatever ~/.gemini/oauth_creds.json + google_accounts.json hold.
#
# Subcommands:
#   gemini-switch status         - show currently active account + matching stash
#   gemini-switch list           - list all stashes with their email
#   gemini-switch use <name>     - atomic swap: stash current, install <name>
#   gemini-switch sync           - re-sync currently active stash from ~/.gemini/
#                                  (use after gemini auto-refreshed access_token)

set -u
GEMINI_DIR="$HOME/.gemini"
STASH_DIR="$HOME/.gemini-stash"

FILES=(oauth_creds.json google_accounts.json)

die() { echo "gemini-switch: $*" >&2; exit 1; }

email_of() {
  # $1 = path to google_accounts.json
  python -c "import json,sys; print(json.load(open(sys.argv[1]))['active'])" "$1" 2>/dev/null
}

active_email() {
  [ -f "$GEMINI_DIR/google_accounts.json" ] || { echo "(none)"; return; }
  email_of "$GEMINI_DIR/google_accounts.json"
}

stash_email() {
  # $1 = stash name
  local f="$STASH_DIR/$1/google_accounts.json"
  [ -f "$f" ] || { echo "(missing)"; return; }
  email_of "$f"
}

list_stashes() {
  [ -d "$STASH_DIR" ] || return
  for d in "$STASH_DIR"/*/; do
    [ -d "$d" ] || continue
    basename "$d"
  done
}

find_stash_for_email() {
  # echo the stash name whose google_accounts.json matches given email; empty if none
  local target="$1"
  for name in $(list_stashes); do
    if [ "$(stash_email "$name")" = "$target" ]; then
      echo "$name"
      return
    fi
  done
}

cmd_status() {
  local email; email="$(active_email)"
  echo "Active account: $email"
  local match; match="$(find_stash_for_email "$email")"
  if [ -n "$match" ]; then
    echo "Matches stash:  $match"
  else
    echo "Matches stash:  (none - run 'gemini-switch sync <name>' to register)"
  fi
  echo ""
  echo "Available stashes:"
  for name in $(list_stashes); do
    local marker="  "
    [ "$name" = "$match" ] && marker="* "
    printf "%s%-12s %s\n" "$marker" "$name" "$(stash_email "$name")"
  done
}

cmd_list() {
  for name in $(list_stashes); do
    printf "%-12s %s\n" "$name" "$(stash_email "$name")"
  done
}

cmd_sync() {
  local target="${1:-}"
  [ -n "$target" ] || die "usage: gemini-switch sync <stash-name>"
  [ -d "$STASH_DIR/$target" ] || die "stash '$target' does not exist (try: gemini-switch list)"
  local email; email="$(active_email)"
  [ "$email" != "(none)" ] || die "no active gemini credentials in $GEMINI_DIR"
  local stash_e; stash_e="$(stash_email "$target")"
  if [ "$stash_e" != "$email" ]; then
    echo "Warning: active email ($email) differs from stash '$target' ($stash_e)"
    echo "Sync would overwrite the stash with current credentials."
    read -r -p "Continue? [y/N] " ans
    [ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "aborted"
  fi
  for f in "${FILES[@]}"; do
    cp "$GEMINI_DIR/$f" "$STASH_DIR/$target/$f.tmp"
    mv "$STASH_DIR/$target/$f.tmp" "$STASH_DIR/$target/$f"
  done
  echo "Synced active credentials -> $target ($email)"
}

cmd_use() {
  local target="${1:-}"
  [ -n "$target" ] || die "usage: gemini-switch use <stash-name>"
  [ -d "$STASH_DIR/$target" ] || die "stash '$target' does not exist (try: gemini-switch list)"

  local target_email; target_email="$(stash_email "$target")"
  local current_email; current_email="$(active_email)"

  if [ "$current_email" = "$target_email" ]; then
    echo "Already on $target ($target_email) - nothing to do."
    return
  fi

  # Step 1: save current state back to its matching stash (preserve refreshed tokens)
  if [ "$current_email" != "(none)" ]; then
    local current_stash; current_stash="$(find_stash_for_email "$current_email")"
    if [ -n "$current_stash" ]; then
      for f in "${FILES[@]}"; do
        cp "$GEMINI_DIR/$f" "$STASH_DIR/$current_stash/$f.tmp"
        mv "$STASH_DIR/$current_stash/$f.tmp" "$STASH_DIR/$current_stash/$f"
      done
      echo "Saved current -> $current_stash ($current_email)"
    else
      echo "Warning: active email $current_email matches no stash; current state NOT saved."
      echo "         Run 'gemini-switch sync <name>' first if you want to keep it."
      read -r -p "Proceed anyway? [y/N] " ans
      [ "$ans" = "y" ] || [ "$ans" = "Y" ] || die "aborted"
    fi
  fi

  # Step 2: atomic install of target stash into ~/.gemini/
  for f in "${FILES[@]}"; do
    cp "$STASH_DIR/$target/$f" "$GEMINI_DIR/$f.tmp"
    mv "$GEMINI_DIR/$f.tmp" "$GEMINI_DIR/$f"
  done

  echo "Switched to: $target ($target_email)"
}

case "${1:-status}" in
  status)  cmd_status ;;
  list)    cmd_list ;;
  use)     shift; cmd_use "${1:-}" ;;
  sync)    shift; cmd_sync "${1:-}" ;;
  -h|--help|help)
    cat <<EOF
gemini-switch - swap between Gemini CLI OAuth accounts

Usage:
  gemini-switch                    show current account and stashes (default: status)
  gemini-switch status             same
  gemini-switch list               list available stashes
  gemini-switch use <name>         switch to named stash
  gemini-switch sync <name>        save current ~/.gemini/ credentials into <name>

Stashes live in ~/.gemini-stash/<name>/
EOF
    ;;
  *) die "unknown command: $1 (try: gemini-switch help)" ;;
esac
