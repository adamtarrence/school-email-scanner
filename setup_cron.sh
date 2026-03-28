#!/bin/bash
# Setup/remove LOCAL cron job for school email scanner.
#
# NOTE: Production runs via GitHub Actions. This local cron job is
# for development/testing or as a fallback when GitHub Actions is unavailable.
#
# Usage:
#   ./setup_cron.sh install    # Add cron job
#   ./setup_cron.sh remove     # Remove cron job
#   ./setup_cron.sh status     # Show current cron job

PROJECT_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Projects/school-email-scanner"
PYTHON="/usr/local/bin/python3"

# Detect Homebrew python on Apple Silicon
if [ ! -f "$PYTHON" ] && [ -f "/opt/homebrew/bin/python3" ]; then
    PYTHON="/opt/homebrew/bin/python3"
fi

# Fall back to system python3
if [ ! -f "$PYTHON" ]; then
    PYTHON=$(which python3)
fi

TAG="# school-email-scanner-v4"

DAILY_JOB="0 18 * * 1-5 cd \"$PROJECT_DIR\" && $PYTHON digest.py >> \"$PROJECT_DIR/digest.log\" 2>&1 $TAG"

case "${1:-status}" in
    install)
        # Remove any existing scanner jobs first
        crontab -l 2>/dev/null | grep -v "school-email-scanner" | crontab -

        # Add new job
        (crontab -l 2>/dev/null; echo ""; echo "# School Email Scanner v4 — daily digest (6 PM Mon-Fri)"; echo "$DAILY_JOB") | crontab -

        echo "Local cron job installed:"
        echo "   Daily: 6:00 PM, Mon-Fri"
        echo ""
        echo "   Python: $PYTHON"
        echo "   Project: $PROJECT_DIR"
        echo ""
        echo "   NOTE: Production runs via GitHub Actions."
        echo "         This is for local dev/fallback only."
        echo ""
        crontab -l | grep "$TAG"
        ;;

    remove)
        crontab -l 2>/dev/null | grep -v "school-email-scanner" | crontab -
        echo "Cron job removed."
        ;;

    status)
        echo "Current school-email-scanner cron jobs:"
        crontab -l 2>/dev/null | grep -A1 "school-email-scanner" || echo "  (none)"
        ;;

    *)
        echo "Usage: $0 {install|remove|status}"
        exit 1
        ;;
esac
