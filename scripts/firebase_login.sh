#!/usr/bin/env bash
# Helper to login to Firebase from the terminal.
# Usage:
#   ./scripts/firebase_login.sh        # interactive login (opens browser)
#   ./scripts/firebase_login.sh --ci   # generate a CI token (prints token)

set -euo pipefail

show_help() {
  cat <<EOF
Usage: $0 [--ci]

Options:
  --ci    Run 'firebase login:ci' to generate a CI token for non-interactive environments.
  --help  Show this help message.

Notes:
 - This script uses 'npx firebase-tools' so you don't need a global npm install.
 - For CI, take the token and store it in your CI secret named FIREBASE_TOKEN.
 - For local interactive login, a browser will open; ensure you have a working X session or run on a machine with a browser.
EOF
}

if [ "${1-}" = "--help" ]; then
  show_help
  exit 0
fi

CI_MODE=0
if [ "${1-}" = "--ci" ]; then
  CI_MODE=1
fi

command -v node >/dev/null 2>&1 || {
  echo "node is required but not found. Install Node.js (https://nodejs.org/) and retry." >&2
  exit 2
}

if [ "$CI_MODE" -eq 1 ]; then
  echo "Generating Firebase CI token..."
  # Use npx so user doesn't need global install
  TOKEN=$(npx --yes firebase-tools login:ci 2>/dev/null || true)
  if [ -z "$TOKEN" ]; then
    # Sometimes firebase-tools writes explanation + token to stderr/stdout; try to capture by running normally
    echo "Could not automatically capture token; running interactively. Follow prompts..."
    npx --yes firebase-tools login:ci
    exit 0
  fi
  echo
  echo "--- FIREBASE CI TOKEN ---"
  echo "$TOKEN"
  echo "-------------------------"
  echo
  echo "Store this value as your CI secret named FIREBASE_TOKEN (do not commit it)."
  exit 0
else
  echo "Starting interactive Firebase login... (this will open a browser)"
  npx --yes firebase-tools login
  echo "Login complete. You can now run firebase deploy or use the token flow for CI via --ci." 
  exit 0
fi
