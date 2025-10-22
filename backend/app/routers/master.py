# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master.py
# Version   : 2025.10-30 · v4.0 (SSOT Final Stable · Titles & Positions 확정)
# Purpose   : Hotel Admin — Unified Master Router Hub (기준정보 통합 허브)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 운영 시스템의 "기준정보(Master)" API 라우터를 단일 허브로 통합 관리
#   • 모든 마스터 관련 서브라우터를 일괄 include하여 단일 진입점을 제공 (SSOT)
# ----------------------------------------------------------------------------
# 포함 대상 (총 10개)
#   1) /api/master/departments       → 부서 기준정보
#   2) /api/master/ranks             → 직급 기준정보
#   3) /api/master/titles            → 직책 기준정보 ✅ (v4.0 확정)
#   4) /api/master/positions         → 직위 기준정보 ✅ (v4.0 확정)
#   5) /api/master/empno-policy      → 사번 정책
#   6) /api/master/salary-grades     → 급여 등급 기준정보
#   7) /api/master/properties        → 지점(Property) 기준정보
#   8) /api/master/banks             → 은행(Bank) 기준정보
#   9) /api/master/hk-status         → 하우스키핑 상태코드 기준정보
#  10) /api/master/ota-channels      → OTA 채널 기준정보
# ----------------------------------------------------------------------------
# 변경 로그:
#   v2.8 (2025-10-28)
#     ✅ MasterPosition(직위) 라우터 추가
#     ✅ MasterBank 업그레이드 반영 (order_no / meta 등)
#   v4.0 (2025-10-30)
#     ✅ MasterTitle 구조 확정 (master_titles → 테이블 정규화 완료)
#     ✅ MasterPosition + MasterBank + OTAChannel 포함 기준 완성
#     ✅ SSOT Final Stable 버전으로 고정
# ============================================================================

from fastapi import APIRouter
from app.routers import (
    master_departments,     #  1) 부서
    master_ranks,           #  2) 직급
    master_titles,          #  3) 직책 ✅ (v4.0 확정)
    master_positions,       #  4) 직위 ✅ (v4.0 확정)
    master_empno_policy,    #  5) 사번 정책
    master_salary_grade,    #  6) 급여 등급
    master_property,        #  7) 지점(Property)
    master_bank,            #  8) 은행(Bank)
    master_hk_status,       #  9) 하우스키핑 상태코드
    master_ota_channel,     # 10) OTA 채널
    # NOTE: master_ota_commission (삭제) — 운영 라우트(/api/ota/commissions)로 분리
)

# ─────────────────────────────────────────────
# Router 허브 생성
# ─────────────────────────────────────────────
router = APIRouter(tags=["master"])

# ─────────────────────────────────────────────
# 라우터 등록 (순서 고정)
# ─────────────────────────────────────────────
router.include_router(master_departments.router)
router.include_router(master_ranks.router)
router.include_router(master_titles.router)
router.include_router(master_positions.router)
router.include_router(master_empno_policy.router)
router.include_router(master_salary_grade.router)
router.include_router(master_property.router)
router.include_router(master_bank.router)
router.include_router(master_hk_status.router)
router.include_router(master_ota_channel.router)

# ============================================================================
# 유지보수 참고
# ----------------------------------------------------------------------------
# • 새로운 기준정보 추가 시 절차:
#   ① app/routers/master_<domain>.py 생성
#   ② 본 허브에 import 및 include_router 추가
# ----------------------------------------------------------------------------
# • 각 서브라우터 공통 원칙:
#   prefix: "/api/master/<domain>"
#   tags: ["master-<domain>"]
#   dependencies:
#       기본  : [require_token_local, require_roles(["ADMIN","SUPERADMIN"])]
#       선택적: HRADMIN 허용 여부는 도메인별 정책에 따름
# ----------------------------------------------------------------------------
# • OTA 관련 운영 라우트(참고):
#   - OTA 수수료(운영):  /api/ota/commissions (master 허브에 포함하지 않음)
#   - OTA 채널(기준):   /api/master/ota-channels
# ============================================================================
