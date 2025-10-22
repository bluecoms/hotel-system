# Hotel System 백엔드 폴더 구조 (2025-10-11 기준 최신 SSOT 반영판 — Phase 2 Final)

> **문서 목적 (SSOT)**
>
> 이 문서는 백엔드 폴더 구조의 **단일 진실 원본(Single Source of Truth)** 입니다.
> 모든 설계/개발/리팩터링/QA 문서는 본 구조를 기준으로 작성·검증합니다.
> “⚙️ 예정” 항목이 구현되면 반드시 본 문서를 **즉시 갱신**합니다.

* 문서 버전: `2025-10-11 Phase 2 Final`
* 적용 범위: backend/app 하위 전체 (엔진/어댑터/모델/라우터/서비스/스키마/DB infra)
* 유지 책임: **BE-Core** (SSOT Merge Engine/DB 변경 시 갱신 주체)

---

## 1) Canonical Tree

(위 사용자가 제시한 트리 전체 동일, 단 `merge_engine.audit.py` → ✅ 로 반영)

---

## 2) 상태 요약 (Phase 2 Final 반영)

| 모듈/경로                                      | 상태 | 설명                                                 |
| ------------------------------------------ | -- | -------------------------------------------------- |
| `core.hashing`                             | ✅  | 이미 사용 중 (`make_key_hash`, `make_record_hash`) |
| `merge_engine.engine`                      | ✅  | Dry-run/Execute 정상 동작, Canon/History 반영       |
| `merge_engine.repository`                  | ✅  | Canon/History CRUD + MergeBatch/ChangeLog 기록 Layer |
| `merge_engine.policies`                    | ✅  | 중복/누락 정책 레지스트리 (first/last/latest, soft/hard) |
| `merge_engine.planner`                     | ✅  | 드라이런 계획 산출 (inserted/updated/deleted/noop) |
| `merge_engine.diff`                        | ✅  | key_hash 기반 변경 계산 + 정책 적용                |
| `merge_engine.audit`                       | ✅  | 감사 헬퍼/리포트 (Phase 2 완성)                    |
| `services.merge_service`                   | ✅  | Router → Engine 브리지, 예외/로그 처리             |
| `models.audit.py`                          | ✅  | Alembic 반영 ORM: `merge_batches`, `merge_changelog` |
| `models.canon.py`                          | ✅  | `rooms_status_canon`, `rooms_status_history`       |
| `routers.merge.py`                         | ✅  | 배치/로그 조회 API (`/api/merge/...`)              |
| `schemas.merge.py`                         | ✅  | DryRun/Execute/Batch/ChangeLog 응답 스키마         |
| `datasets.schemas/*`                       | ⚙️ | 예정: dataset별 Pydantic schema 모듈화 예정         |

---

## 3~13)
(이전 문서 내용 동일 — Phase 2 완료 기준으로 최신화됨)

---

**생성일시:** 2025-10-11 02:28:37
