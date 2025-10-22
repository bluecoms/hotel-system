# -*- coding: utf-8 -*-
# Dummy helpers module to silence [startup:migrate] warnings
# ----------------------------------------------------------------------------
# 목적:
#   • dev_bootstrap.py 에서 호출되는 _ensure_employees_schema(db) 함수 정의
#   • 반환값을 문자열 iterable(list)로 맞춰 join() 오류 방지
# ----------------------------------------------------------------------------

def _ensure_employees_schema(*args, **kwargs):
    """개발용 더미: 직원 스키마 보강 없음"""
    # dev_bootstrap에서 join()을 시도하므로 리스트 형태 반환
    return []
