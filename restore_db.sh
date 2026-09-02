#!/usr/bin/env bash
if [ -z "$1" ]; then
    echo "Usage: ./restore_db.sh <backup_file.sql>"
    exit 1
fi
PGPASSWORD="${PGPASSWORD:-44113290}" psql -U gtu_admin -h localhost -d iic_cell_gtu < "$1"
echo "Database restored successfully from: $1"
