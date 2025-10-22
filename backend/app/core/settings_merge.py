# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/settings_merge.py
# Version   : 2025.10-30 · v3.2 (SSOT Merge Policy Final · Banking Ready)
# Purpose   : Hotel Admin — SSOT Merge Engine Settings
# ----------------------------------------------------------------------------
# 목적:
#   • 모든 데이터셋 병합(merge) 작업의 전역·세부 정책을 관리
#   • Canon/History/Batch/ChangeLog와 연동되는 통합 설정 원천(SSOT)
#   • 업로드 어댑터(adapters/*)와 엔진(engine.py)에서 공통 참조
# ----------------------------------------------------------------------------
# 주요 기능:
#   ✅ 전역 기본값(DEFAULTS) — 모든 어댑터 공통
#   ✅ 데이터셋별 오버라이드(DATASET_POLICIES)
#   ✅ 뱅킹 정규화 옵션(BANK_NORMALIZE) — 방향/금액/통화/마스킹
#   ✅ 정책 조회(get_policy) + 로거 초기화(setup_merge_logger)
# ----------------------------------------------------------------------------
# 적용 범위:
#   • app/merge_engine/{engine,repository,audit}.py
#   • app/datasets/adapters/* (rooms_status, sales_front, bank_ledger, expenses, ota_orders ...)
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.2 (2025-10-30)
#     ✅ Banking 정규화 블록 추가(방향 alias/금액 부호/통화/마스킹)
#     ✅ bank_daily_balance / bank_recon 데이터셋 정책 초안 추가
#     ✅ 주석 표준(SSOT) 보강
# ============================================================================
import os
import logging
from typing import Dict, Any

log = logging.getLogger("merge_settings")

# ============================================================================
# 1️⃣ 전역 정책 (DEFAULTS)
# ----------------------------------------------------------------------------
DEFAULTS: Dict[str, Any] = {
    "dry_run": False,                       # ✅ 실제 커밋 모드
    "merge_mode": "snapshot",               # append | snapshot
    "missing_policy": "soft_delete",        # ignore | soft_delete | hard_delete
    "conflict_policy": "upsert",
    "audit_enabled": True,
    "audit_log_to_file": True,
    "log_level": "INFO",

    # 로그 파일 경로 (NAS 기본)
    "audit_log_path": os.environ.get(
        "MERGE_ENGINE_LOG_PATH",
        "/volume1/web/hotel-system/logs/merge_engine.log"
    ),

    "encoding": "utf-8",
    "max_preview_rows": 1000,
}

# ============================================================================
# 2️⃣ 데이터셋별 병합 정책 (DATASET_POLICIES)
# ----------------------------------------------------------------------------
DATASET_POLICIES: Dict[str, Dict[str, Any]] = {
    # ── 기본 운영 데이터 ─────────────────────────────
    "rooms_status": {
        "merge_mode": "append",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },
    "sales_front": {
        "merge_mode": "snapshot",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },
    "fnb_items": {
        "merge_mode": "snapshot",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },
    "fnb_tenders": {
        "merge_mode": "snapshot",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },
    "expenses": {
        "merge_mode": "snapshot",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },

    # ── 뱅킹 계열 ──────────────────────────────────
    # 입출금 장부(일별 라인 추적) → append/ignore (삭제 개념 無)
    "bank_ledger": {
        "merge_mode": "append",
        "missing_policy": "ignore",
        "dedupe_policy": "latest",
    },
    # 일일 잔액(스냅샷) → snapshot/soft_delete
    "bank_daily_balance": {
        "merge_mode": "snapshot",
        "missing_policy": "soft_delete",
        "dedupe_policy": "first",
    },
    # 계정조정(조정표) → snapshot/ignore (조정값이므로 삭제 반영 X)
    "bank_recon": {
        "merge_mode": "snapshot",
        "missing_policy": "ignore",
        "dedupe_policy": "first",
    },

    # ── OTA / 정제 데이터 ─────────────────────────────
    "ota_orders": {
        "merge_mode": "append",
        "missing_policy": "ignore",
        "dedupe_policy": "latest",
    },
}

# ============================================================================
# 3️⃣ 뱅킹 정규화 옵션 (BANK_NORMALIZE)
# ----------------------------------------------------------------------------
# 어댑터에서 참조하는 표준 옵션:
#  • direction_alias: 방향 IN/OUT 매핑
#  • amount_sign: 금액 부호 규칙(문자/부호/괄호)
#  • currency: 기본 통화 코드
#  • account_mask: 계좌 마스킹 여부/길이/구분자
#  • bank_code_map: 은행 코드 alias → 정규 코드 매핑
# ============================================================================
BANK_NORMALIZE: Dict[str, Any] = {
    "direction_alias": {
        # 입금
        "in": "IN", "deposit": "IN", "credit": "IN", "cr": "IN", "+": "IN",
        "입금": "IN", "유입": "IN",
        # 출금
        "out": "OUT", "withdraw": "OUT", "debit": "OUT", "dr": "OUT", "-": "OUT",
        "출금": "OUT", "지출": "OUT",
    },
    "amount_sign": {
        "bracket_negative": True,   # (1,234) → -1234
        "leading_plus_minus": True, # +1,234 / -1,234 허용
        "strip_commas": True,
        "empty_is_zero": True,
    },
    "currency": "KRW",
    "account_mask": {
        "enabled": True,
        "keep_last": 4,
        "mask_char": "*",
        "delimiter": "-",          # 표시용 구분자
    },
    "bank_code_map": {
        # alias → 정규 코드
        "KB국민": "KB", "국민": "KB",
        "신한": "SH", "우리": "WR", "농협": "NH",
        "기업": "IBK", "하나": "HN", "산업": "KDB",
    },
}

# ============================================================================
# 4️⃣ 정책 조회 함수
# ----------------------------------------------------------------------------
def get_policy(dataset: str) -> Dict[str, Any]:
    """데이터셋별 병합 정책 조회 (DEFAULTS + 오버라이드 병합)"""
    ds_policy = DATASET_POLICIES.get(dataset, {})
    merged = dict(DEFAULTS)
    merged.update(ds_policy)
    return merged

def get_bank_settings() -> Dict[str, Any]:
    """뱅킹 정규화 옵션 조회 (어댑터/엔진에서 공통 사용)"""
    return BANK_NORMALIZE

# ============================================================================
# 5️⃣ 병합엔진 로거 초기화
# ----------------------------------------------------------------------------
def setup_merge_logger() -> None:
    """Merge Engine 로거 초기화"""
    level = getattr(logging, DEFAULTS.get("log_level", "INFO"), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if DEFAULTS.get("audit_log_to_file"):
        try:
            path = DEFAULTS["audit_log_path"]
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fh = logging.FileHandler(path, mode="a", encoding="utf-8")
            fh.setLevel(level)
            fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            fh.setFormatter(fmt)
            logging.getLogger().addHandler(fh)
            log.info("[MERGE_SETTINGS] file logging initialized → %s", path)
        except Exception as e:
            log.warning("[MERGE_SETTINGS] file logging disabled: %s", e)

# ============================================================================
# 6️⃣ 정책 덤프 (개발용)
# ----------------------------------------------------------------------------
def show_policies() -> None:
    """현재 등록된 데이터셋 병합 정책 출력"""
    for ds, pol in DATASET_POLICIES.items():
        log.info("[MERGE_POLICY] %s → %s", ds, pol)
    log.info("[MERGE_SETTINGS] default: %s", DEFAULTS)

# ============================================================================
# 7️⃣ 스탠드얼론 실행 (테스트용)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    print("── Merge Engine Settings Snapshot ──")
    for name in sorted(DATASET_POLICIES.keys()):
        print(f"{name:<18}: {get_policy(name)}")
    print("\nBank Normalize:", BANK_NORMALIZE)
    print("\nDefault Settings:", DEFAULTS)
