"""
Admin audit logging.

Every destructive or privileged admin action writes a row to audit_logs.
Reads never fail silently — writes do (a logging failure must never block admin work).

DB prerequisite:
  CREATE TABLE IF NOT EXISTS audit_logs (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      admin_id UUID NOT NULL,
      admin_username TEXT NOT NULL,
      action TEXT NOT NULL,
      target_type TEXT,
      target_id TEXT,
      detail_json JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
"""

from utils.db_client import supabase


def log_admin_action(admin_id, admin_username, action,
                     target_type=None, target_id=None, detail=None):
    try:
        supabase.table("audit_logs").insert({
            "admin_id": str(admin_id),
            "admin_username": admin_username,
            "action": action,
            "target_type": target_type,
            "target_id": str(target_id) if target_id else None,
            "detail_json": detail,
        }).execute()
    except Exception:
        pass


def get_audit_log(limit=100):
    resp = (
        supabase.table("audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data
