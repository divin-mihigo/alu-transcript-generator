#!/usr/bin/env bash
# organizer.sh - archives grades.csv, resets the workspace and logs the action.

set -u

CSV_FILE="grades.csv"
ARCHIVE_DIR="archive"
LOG_FILE="organizer.log"

# Archive directory: create it only if it does not already exist.
if [ ! -d "$ARCHIVE_DIR" ]; then
    mkdir -p "$ARCHIVE_DIR" || { echo "Error: could not create '$ARCHIVE_DIR'." >&2; exit 1; }
fi

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: '$CSV_FILE' not found in $(pwd). Nothing to archive." >&2
    exit 1
fi

timestamp=$(date +"%Y%m%d-%H%M%S")
archived_name="grades_${timestamp}.csv"

# Avoid overwriting an archive created within the same second.
counter=1
while [ -e "$ARCHIVE_DIR/$archived_name" ]; do
    archived_name="grades_${timestamp}_${counter}.csv"
    counter=$((counter + 1))
done

# Archive the current file, then immediately reset the workspace.
if ! mv "$CSV_FILE" "$ARCHIVE_DIR/$archived_name"; then
    echo "Error: failed to move '$CSV_FILE' to '$ARCHIVE_DIR/'." >&2
    exit 1
fi
: > "$CSV_FILE"

# Append to the log (accumulates across runs).
echo "[$timestamp] original: $CSV_FILE | archived: $ARCHIVE_DIR/$archived_name" >> "$LOG_FILE"

echo "Archived $CSV_FILE -> $ARCHIVE_DIR/$archived_name"
echo "Created a new empty $CSV_FILE. Logged to $LOG_FILE."
