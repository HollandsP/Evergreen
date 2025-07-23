#!/bin/bash

# Evergreen AI Video Pipeline - Backup Script
# Automated backup for production deployment

set -e

# Configuration
BACKUP_DIR="/backups"
DB_BACKUP_DIR="$BACKUP_DIR/database"
MEDIA_BACKUP_DIR="$BACKUP_DIR/media"
LOGS_BACKUP_DIR="$BACKUP_DIR/logs"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# AWS S3 configuration
S3_BUCKET=${BACKUP_S3_BUCKET:-}
AWS_REGION=${AWS_REGION:-us-east-1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directories
create_backup_dirs() {
    log "Creating backup directories..."
    mkdir -p "$DB_BACKUP_DIR"
    mkdir -p "$MEDIA_BACKUP_DIR" 
    mkdir -p "$LOGS_BACKUP_DIR"
    success "Backup directories created"
}

# Backup PostgreSQL database
backup_database() {
    log "Starting database backup..."
    
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL not set"
    fi
    
    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
    DB_PASSWORD=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    
    export PGPASSWORD="$DB_PASSWORD"
    
    # Full database backup
    BACKUP_FILE="$DB_BACKUP_DIR/evergreen_full_$TIMESTAMP.sql"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-password \
        --verbose \
        --format=custom \
        --compress=9 \
        --file="$BACKUP_FILE"
    
    success "Database backup completed: $BACKUP_FILE"
    
    # Schema-only backup for quick restores
    SCHEMA_FILE="$DB_BACKUP_DIR/evergreen_schema_$TIMESTAMP.sql"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-password \
        --schema-only \
        --file="$SCHEMA_FILE"
    
    success "Schema backup completed: $SCHEMA_FILE"
    
    unset PGPASSWORD
}

# Backup Redis data
backup_redis() {
    log "Starting Redis backup..."
    
    # Redis backup (if accessible)
    if command -v redis-cli >/dev/null 2>&1; then
        REDIS_BACKUP="$DB_BACKUP_DIR/redis_dump_$TIMESTAMP.rdb"
        redis-cli --rdb "$REDIS_BACKUP" || warning "Redis backup failed"
        success "Redis backup completed: $REDIS_BACKUP"
    else
        warning "redis-cli not available, skipping Redis backup"
    fi
}

# Backup media files
backup_media() {
    log "Starting media backup..."
    
    MEDIA_DIRS=(
        "/app/output"
        "/app/exports"
        "/var/lib/postgresql/data"
        "/var/lib/redis/data"
    )
    
    for dir in "${MEDIA_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            log "Backing up $dir..."
            BACKUP_FILE="$MEDIA_BACKUP_DIR/$(basename "$dir")_$TIMESTAMP.tar.gz"
            tar -czf "$BACKUP_FILE" -C "$(dirname "$dir")" "$(basename "$dir")" || warning "Failed to backup $dir"
            success "Media backup completed: $BACKUP_FILE"
        else
            warning "Directory $dir not found, skipping"
        fi
    done
}

# Backup logs
backup_logs() {
    log "Starting logs backup..."
    
    LOG_DIRS=(
        "/var/log"
        "/app/logs"
    )
    
    for dir in "${LOG_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            log "Backing up logs from $dir..."
            BACKUP_FILE="$LOGS_BACKUP_DIR/logs_$(basename "$dir")_$TIMESTAMP.tar.gz"
            tar -czf "$BACKUP_FILE" -C "$(dirname "$dir")" "$(basename "$dir")" --exclude="*.gz" || warning "Failed to backup logs from $dir"
            success "Logs backup completed: $BACKUP_FILE"
        else
            warning "Log directory $dir not found, skipping"
        fi
    done
}

# Upload to S3 (if configured)
upload_to_s3() {
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        log "Uploading backups to S3 bucket: $S3_BUCKET"
        
        # Upload with proper S3 structure
        aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/evergreen-backups/$(date +%Y/%m/%d)/" \
            --region "$AWS_REGION" \
            --exclude "*" \
            --include "*.sql" \
            --include "*.tar.gz" \
            --include "*.rdb" \
            --storage-class STANDARD_IA
        
        success "Backups uploaded to S3"
    else
        if [ -z "$S3_BUCKET" ]; then
            warning "S3_BUCKET not configured, skipping S3 upload"
        else
            warning "AWS CLI not available, skipping S3 upload"
        fi
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete || warning "Failed to clean some local backups"
    
    # S3 cleanup (if configured)
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        # Use S3 lifecycle policy for efficient cleanup
        CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "evergreen-backups/" \
            --query "Contents[?LastModified<='$CUTOFF_DATE'].{Key: Key}" \
            --output text | while read -r key; do
                if [ -n "$key" ]; then
                    aws s3 rm "s3://$S3_BUCKET/$key"
                fi
            done
    fi
    
    success "Old backups cleaned up"
}

# Verify backup integrity
verify_backups() {
    log "Verifying backup integrity..."
    
    # Check database backups
    for backup in "$DB_BACKUP_DIR"/*.sql; do
        if [ -f "$backup" ]; then
            if pg_restore --list "$backup" >/dev/null 2>&1; then
                success "Database backup verified: $(basename "$backup")"
            else
                error "Database backup corrupted: $(basename "$backup")"
            fi
        fi
    done
    
    # Check tar.gz files
    for backup in "$MEDIA_BACKUP_DIR"/*.tar.gz "$LOGS_BACKUP_DIR"/*.tar.gz; do
        if [ -f "$backup" ]; then
            if tar -tzf "$backup" >/dev/null 2>&1; then
                success "Archive verified: $(basename "$backup")"
            else
                error "Archive corrupted: $(basename "$backup")"
            fi
        fi
    done
    
    success "All backups verified successfully"
}

# Generate backup report
generate_report() {
    log "Generating backup report..."
    
    REPORT_FILE="$BACKUP_DIR/backup_report_$TIMESTAMP.txt"
    
    cat > "$REPORT_FILE" << EOF
Evergreen AI Video Pipeline - Backup Report
==========================================
Date: $(date)
Backup Location: $BACKUP_DIR
S3 Bucket: ${S3_BUCKET:-"Not configured"}
Retention: $RETENTION_DAYS days

Database Backups:
$(ls -lh "$DB_BACKUP_DIR"/*_$TIMESTAMP.sql 2>/dev/null || echo "No database backups")

Media Backups:
$(ls -lh "$MEDIA_BACKUP_DIR"/*_$TIMESTAMP.tar.gz 2>/dev/null || echo "No media backups")

Log Backups:
$(ls -lh "$LOGS_BACKUP_DIR"/*_$TIMESTAMP.tar.gz 2>/dev/null || echo "No log backups")

Total Backup Size:
$(du -sh "$BACKUP_DIR" | cut -f1)

Disk Space:
$(df -h "$BACKUP_DIR")
EOF
    
    success "Backup report generated: $REPORT_FILE"
    cat "$REPORT_FILE"
}

# Main backup function
main() {
    log "Starting Evergreen AI Video Pipeline backup..."
    log "Timestamp: $TIMESTAMP"
    
    # Install required tools if not present
    if ! command -v pg_dump >/dev/null 2>&1; then
        log "Installing PostgreSQL client..."
        apk add --no-cache postgresql-client
    fi
    
    if ! command -v aws >/dev/null 2>&1 && [ -n "$S3_BUCKET" ]; then
        log "Installing AWS CLI..."
        apk add --no-cache aws-cli
    fi
    
    # Execute backup steps
    create_backup_dirs
    backup_database
    backup_redis
    backup_media
    backup_logs
    verify_backups
    upload_to_s3
    cleanup_old_backups
    generate_report
    
    success "Backup completed successfully!"
    log "Backup location: $BACKUP_DIR"
    
    if [ -n "$S3_BUCKET" ]; then
        log "S3 location: s3://$S3_BUCKET/evergreen-backups/$(date +%Y/%m/%d)/"
    fi
}

# Execute main function
main "$@"