# 🧩 Phase 2 → Phase 3 전환 보고 (Backend)

**작성일:** $(date +%Y-%m-%d)
**담당:** BE-Core / PM-Hub
**환경:** Synology NAS (Python 3.9 venv39_py39)

---

## ✅ 완료 항목
| 구분 | 상태 | 설명 |
|------|------|------|
| CanonRecord | 완료 | 표준 레코드 정의 확정 |
| merge_engine.audit | 완료 | MergeBatch + ChangeLog 통합 |
| rooms_status adapter | 완료 | CSV → 정규화 → 파싱 검증 완료 |
| Alembic head | 단일 유지 | fnb_items_header_v1 |
| runbook snapshot | 완료 | openapi + schema 동기화 |

---

## ⚙️ 다음 단계 (Phase 3)
| 단계 | 설명 |
|------|------|
| FNB / Expenses / Bank 어댑터 생성 | rooms_status 패턴 복제 |
| Templates API | /api/templates/{dataset}.csv |
| Upload 프런트 UI | UploadBoard.vue |
| QA | dry_run = 1 결과 검증 |

---

## 🔒 운영 전 주의
- `/api/upload/*` 모두 `X-Internal-Token` 보호
- `dry_run` 모드에서만 INSERT 금지 확인
- `_uploads/` 폴더 권한 777 유지
- Alembic 단일 head 정상 여부 검증

---

## 📦 기록
- Commit: Phase 2 finalize CanonRecord Adapter
- Snapshot: openapi_$(date +%Y%m%d).json
- Verified by: `curl /api/upload/rooms_status --dry_run=1`
