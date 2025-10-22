# 📢 [PM-Hub] Hotel Admin — Backend 통합 정리 보고 (2025-10-04)

## ✅ 1. 수행 내역 (완료)

| 구분 | 파일/모듈 | 주요 변경 사항 |
|------|-------------|----------------|
| A. Upload / Reports / OTA / Closing 라우터 정비 | app/routers/upload.py, reports.py, ota.py, closing.py | 업로드·리포트·OTA·마감 라우터 정상화 및 필드/파라미터 정리. /api/closing/calendar 패턴 기반 유효성 검증 교체(regex → pattern) |
| B. Keyword 기능 추가 | app/routers/keywords.py | 신규 라우터 생성 (/api/keywords/test), SUPERADMIN 전용. DB keywords 테이블 매핑 완료. |
| C. DB 마이그레이션 정비 (Alembic) | alembic/versions/* | 기존 sales_front 충돌 정리 후 키워드/스냅샷 리비전 병합. Head=20251004_03_create_snapshot_table 유지. |
| D. Core 인증/환경 통합 | app/core/auth.py, settings.py, me_router.py, .env | DEBUG/ENV 기반 개발모드 판별 _is_dev_env() / X-Debug-Role 동작 복구 / .env 추가(APP_ENV=dev, DEBUG=1, INTERNAL_API_TOKEN=dev-admin-token) / /api/me에서 SUPERADMIN 반영 확인 완료 |
| E. Snapshot 모듈 | app/core/snapshot.py | 신규 생성, 향후 일일 ETL/스냅샷 API 확장 포인트. 현재 스텁 포함. |
| F. 검증 및 상태 확인 | - | alembic current → 20251004_03_create_snapshot_table (head) / /api/closing/calendar 200 OK / /api/keywords/test SUPERADMIN 권한 OK / /api/me Debug Role 반영 OK (roles=["SUPERADMIN"]) |

---

## 🧾 2. 현재 Alembic 상태

```bash
$ alembic current
20251004_03_create_snapshot_table (head)
```

---

## 🧩 3. 환경/동작 체크

| 항목 | 결과 |
|------|-------|
| DB 연결 | OK (hotel.db 존재, keywords/sales_front 테이블 확인) |
| Alembic 단일 head | OK |
| .env 로드 | OK (settings.APP_ENV=dev, DEBUG=1) |
| X-Debug-Role → SUPERADMIN | OK |
| Upload/Reports/Closing/OTA/Keywords API | OK (200 응답) |

---

## 🧰 4. 향후 인수 대상 (BE → Infra/QA 연계)

### Infra
- Uvicorn autostart 확인 (HOTEL_SERVER_BACKEND 등록됨)
- Nginx /api/ → 127.0.0.1:8000 프록시 확인
- .env 퍼미션(600) 및 경로 /volume1/web/hotel-system/backend/.env 고정 확인

### QA
- /api/upload/sales_front dry_run=1/0 케이스 테스트
- /api/reports/sales-tags/export CSV 헤더 검증
- /api/ota/channels, /api/ota/commissions CRUD 케이스
- /api/keywords/test SUPERADMIN 권한 필수 확인

---

## 🏁 5. 판정

✅ **BE 단위 작업: 완료 (Go)**  
- Alembic head/Schema 정합성 확보  
- FastAPI 기동 시 오류 없음  
→ **Infra·QA 단계로 인계 가능**  
