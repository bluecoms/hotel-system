# 📄 Phase 5 — BE QA Upload Verification Report

**Date:** 2025-10-04 18:57:26
**Environment:** DEV (http://192.168.0.6:8001)
**Database:** /volume1/web/hotel-system/backend/hotel.db
**Token:** dev-admin-token

---

## ✅ 1. Test Context

| 항목 | 값 |
|------|----|
| Backend | http://192.168.0.6:8001 |
| Auth Header | X-Internal-Token: dev-admin-token |
| Dataset | sales_front |
| CSV | /tmp/sf.csv |
| property_code | MOP |
| dry_run | 0 |

---

## 🧪 2. Command Used

```bash
curl -sS -H "X-Internal-Token: dev-admin-token"   -F dry_run=0   -F property_code=MOP   -F file=@/tmp/sf.csv   "http://192.168.0.6:8001/api/upload/sales_front" | jq .
```

---

## 📊 3. Result

```json
{
  "detail": "upload-failed: (sqlite3.OperationalError) ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE constraint"
}
```

**Interpretation:**  
- CSV 파싱 및 유효성 검증까지 정상 통과 (422 제거됨)  
- DB 레벨에서 UNIQUE 제약 미존재로 인해 UPSERT 실패 발생

---

## 🔧 4. Fix Recommendation

**SQL to apply once:**

```sql
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;
CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_front_bizprop_tag
  ON sales_front(business_date, property_code, tag);
COMMIT;
PRAGMA foreign_keys=on;
```

---

## ✅ 5. Expected Result After Fix

```
HTTP 200 OK
{
  "ok": true,
  "session_id": "...",
  "version_no": 1
}
```

---

**Prepared by:** Backend QA / Hotel-System Phase 5  
**Generated at:** 2025-10-04 18:57:26
