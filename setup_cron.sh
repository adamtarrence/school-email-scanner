#!/bin/bash
# Setup/remove LOCAL cron jobs for school email scanner.
#
# NOTE: Production runs via GitHub Actions. These local cron jobs are
# for development/testing or as a fallback when GitHub Actions is unavailable.
#
# Usage:
#   ./setup_cron.sh install    # Add cron jobs
#   ./setup_cron.sh remove     # Remove cron jobs
#   ./setup_cron.sh status     # Show current cron jobs

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

TAG="# school-email-scanner-v3"

DAILY_JOB="0 18 * * 1-5 cd \"$PROJECT_DIR\" && $PYTHON digest.py --mode daily >> \"$PROJECT_DIR/digest.log\" 2>&1 $TAG"
WEEKLY_JOB="5 18 * * 5 cd \"$PROJECT_DIR\" && $PYTHON digest.py --mode weekly >> \"$PROJECT_DIR/digest.log\" 2>&1 $TAG"

case "${1:-status}" in
    install)
        # Remove any existing scanner jobs first
        crontab -l 2>/dev/null | grep -v "school-email-scanner" | crontab -

        # Add new jobs
        (crontab -l 2>/dev/null; echo ""; echo "# School Email Scanner v3 — daily digest (6 PM Mon-Fri)"; echo "$DAILY_JOB"; echo "# School Email Scanner v3 — weekly recap (6:05 PM Friday)"; echo "$WEEKLY_JOB") | crontab -

        echo "✅ Local cron jobs installed:"
        echo "   📚 Daily:  6:00 PM, Mon-Fri"
        echo "   📋 Weekly: 6:05 PM, Friday"
        echo ""
        echo "   Python: $PYTHON"
        echo "   Project: $PROJECT_DIR"
        echo ""
        echo "   NOTE: Production runs via GitHub Actions."
        echo "         These are for local dev/fallback only."
        echo ""
        crontab -l | grep "$TAG"
        ;;

    remove)
        crontab -l 2>/dev/null | grep -v "school-email-scanner" | crontab -
        echo "✅ Cron jobs removed."
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
