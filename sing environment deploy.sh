[1mdiff --git a/.gitattributes b/.gitattributes[m
[1mnew file mode 100644[m
[1mindex 0000000..7f572ef[m
[1m--- /dev/null[m
[1m+++ b/.gitattributes[m
[36m@@ -0,0 +1,2 @@[m
[32m+[m[32m*.sh text=auto eol=lf[m
[32m+[m[32m.gitattributes text eol=lf[m
[1mdiff --git a/deploy.sh b/deploy.sh[m
[1mindex a39c12d..ed6f717 100755[m
[1m--- a/deploy.sh[m
[1m+++ b/deploy.sh[m
[36m@@ -4,14 +4,14 @@[m [mset -euo pipefail[m
 [m
 PROJECT_DIR="/opt/educational-center/educational_center"[m
 COMPOSE_FILE="docker-compose.prod.yml"[m
[31m-ENV_FILE="${ENV_FILE:-.env.prod}"[m
[32m+[m[32mENV_FILE="${ENV_FILE:-/opt/educational-center/.env.prod}"[m
 BACKUP_DIR="${BACKUP_DIR:-/opt/educational-center/backups}"[m
 BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"[m
 [m
 cd "$PROJECT_DIR"[m
 [m
 if [ ! -f "$ENV_FILE" ]; then[m
[31m-  echo "Missing environment file: $PROJECT_DIR/$ENV_FILE" >&2[m
[32m+[m[32m  echo "Missing environment file: $ENV_FILE" >&2[m
   exit 1[m
 fi[m
 [m
[36m@@ -38,6 +38,7 @@[m [mecho "=== Creating database backup ==="[m
 "${COMPOSE[@]}" exec -T db sh -c 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do sleep 2; done'[m
 "${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$tmp_backup_file"[m
 mv "$tmp_backup_file" "$backup_file"[m
[32m+[m[32mtrap - EXIT[m
 echo "Backup saved to $backup_file"[m
 [m
 echo "=== Removing old database backups ==="[m
