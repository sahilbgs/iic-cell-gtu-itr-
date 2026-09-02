#!/usr/bin/env bash
BACKUP_FILE="db_backup_$(date +%Y%m%d_%H%M%S).sql"
PGPASSWORD="${PGPASSWORD:-44113290}" pg_dump -U gtu_admin -h localhost -d iic_cell_gtu > "$BACKUP_FILE"
echo "Backup created successfully: $BACKUP_FILE"
