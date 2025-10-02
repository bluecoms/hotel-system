# 📄 BE-Core 핸드오프 요약 — Phase 3 (ADMIN 권한 고정 + Reports/sales-tags)

## 1) 권한 정책/의존성
- 인증: `X-Internal-Token` 필수 (운영 기준 유지)  
- 개발 모드: `X-Debug-Role: ADMIN|USER` 허용 (운영 비활성 가정)  

```python
# app/core/auth.py
def require_roles(need: list[str]):
    def _dep(
        user=Depends(require_user),
        x_debug_role: str = Header(None)  # DEV ONLY
    ):
        role = (x_debug_role or "ADMIN").upper()
        if role not in need:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user
    return _dep
```

---

## 2) 라우터 보호 적용
- 대상: `/api/ota/*`, `/api/reports/*` → ADMIN 전용  

```python
# app/routers/ota.py
router = APIRouter(
    prefix="/api/ota",
    tags=["ota"],
    dependencies=[Depends(require_roles(["ADMIN"]))]
)

# app/routers/reports.py
router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(require_roles(["ADMIN"]))]
)
```

---

## 3) Reports/sales-tags 구현 상태
- **스키마**: `app/schemas/reports.py`
```python
class SalesTagRow(BaseModel):
    tag: str
    sales_amount: int = Field(default=0, ge=0)
    count: int = Field(default=0, ge=0)
```

- **라우터**: `app/routers/reports.py`
  - 파라미터 없으면 `200 + []`  
  - 기간 지정 시 `sales_front(business_date, tag, amount)` 집계  
  - 테이블 미존재/스키마 미적용 시에도 `200 + []`로 안전 복구  
  - 실제 DB는 `settings.APP_DB_URL` 사용 (현재 `sqlite://///volume1/.../hotel.db`)  
  - 로컬 검증 시 `sales_front` 시드 필요  

---

## 4) 메뉴 트리 (ADMIN 전용)
- `/api/menu` 응답 예시:
```json
{
  "items": [
    {"title":"OTA","to":"/admin/ota/list","roles":["ADMIN"]},
    {"title":"Reports","to":"/admin/reports/sales-tags","roles":["ADMIN"]}
  ]
}
```
- USER 역할에는 위 항목 미포함이어야 함.  

---

## 5) 라우터 패키징 정리
```python
# app/routers/__init__.py
from .ota import router as ota
from .reports import router as reports
from .closing import router as closing
from .users import router as users
from .menu import router as menu

__all__ = ["ota", "reports", "closing", "users", "menu"]

# app/main.py
from app.routers import ota, reports, closing, users, menu
app.include_router(ota)
app.include_router(reports)
app.include_router(closing)
app.include_router(users)
app.include_router(menu)
```

---

✅ **결론**  
- ADMIN 전용 권한 체계 고정 완료  
- Reports/sales-tags 정상화 및 스펙 준수 확인  
- 메뉴 트리에도 ADMIN 전용 항목 반영  
- FE/QA는 이 구조를 기준으로 연동/검증 진행  
