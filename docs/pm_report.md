좋아요. 다음 PM에게 바로 넘겨도 되는 \*\*핵심 정리(세팅/구현 현황/남은 이슈/운영 방법)\*\*를 한 번에 묶었습니다. 지금 보이는 “유저 목록 로드 불가 / 키워드 화면이 대시보드로 연결 / OTA 화면 미동작”은 **라우팅·뷰 컴포넌트 배치 문제**라 백엔드/데이터 구조에는 영향 없습니다. 아래 “빠른 수정 포인트”에 해결 가이드도 넣었습니다.

# 1) 시스템 개요

* **백엔드**: FastAPI + SQLAlchemy (SQLite)

  * DB 파일: `/volume1/web/hotel-system/backend/hotel.db`
  * 업로드 저장: `/volume1/web/hotel-system/backend/_uploads/`
  * 직원 CSV 임포트(참고): `/volume1/web/hotel-system/backend/_imports/` (임의 경로 가능)
* **프런트엔드**: Vue3 + Vite + Vuetify + Pinia

  * Dev 서버: `http://<NAS IP>:5176`
  * `/api/*`는 Vite 프록시로 `http://127.0.0.1:8000`(백엔드)로 전달

# 2) 환경 변수 / 인증·권한

* `.env` (백엔드):

  * `APP_ENV=dev | prod`
  * `APP_DB_URL=sqlite:////volume1/web/hotel-system/backend/hotel.db`
  * `INTERNAL_API_TOKEN=dev-admin-token` (예시)
* **DEV** 모드

  * 토큰 검사 완화(우회). 헤더 `X-Debug-Role` 로 역할 에뮬레이트 가능: `SUPERADMIN`/`ADMIN`
  * 프런트에서 `setDebugRole('SUPERADMIN')` 호출 시 `X-Debug-Role` 추가됨.
* **PROD** 모드

  * `X-Internal-Token: <INTERNAL_API_TOKEN>` 필수.
  * 역할 매핑은 현재 간단(ADMIN 기본). 확장 예정.

# 3) 역할(Role) 정책 (현재 버전)

* `SUPERADMIN`: 전부 가능(삭제는 **소프트 삭제** 컨셉 유지), 설정/임포트/관리자 화면 접근.
* `ADMIN`: 업로드/읽기/쓰기 가능, **삭제 불가**.
* 일반 유저: 아직 비활성(라우팅/메뉴에서 제외).

# 4) 데이터셋 & 파일 포맷

* 데이터셋 키(신규 명명):
  `rooms_status`, `sales_front`, `fnb_sales`, `expenses`, `pay_settlement`

  * 과거명 `fac_sales` → **alias** 로 `fnb_sales` 처리됨.
* 템플릿 컬럼

  * rooms\_status: `room_no,status_code,is_dirty,hk_note`
  * sales\_front: `date,folio_no,amount,currency,note`
  * fnb\_sales: `date,dept,amount,currency,note`
  * expenses: `date,category,amount,currency,note`
  * pay\_settlement: `date,method,amount,currency,note`
* 업로드 파일은 같은 이름 반복 업로드해도 **버전(v1, v2, …)** 으로 누적 저장:

  * 저장 경로 예: `_uploads/{dataset}_{property}_{YYYY-MM-DD}_{ver}.csv`

# 5) 구현된 API (요약)

* 헬스체크: `GET /api/ping`
* 내 정보(권한 포함): `GET /api/me`
* 메뉴: `GET /api/menu` (roles 포함 반환)
* 직원

  * 목록: `GET /api/employees?q=&page=&size=`
  * 생성: `POST /api/employees` (**ADMIN+**)
  * 소프트삭제: `DELETE /api/employees/{id}` (**SUPERADMIN**)
  * CSV 임포트: `POST /api/employees/import-csv` (**SUPERADMIN**)
* 사용자

  * 목록: `GET /api/users?q=&page=&size=`
  * 생성: `POST /api/users` (**SUPERADMIN**)
  * 활성화 토글: `PUT /api/users/{id}/approve` (**SUPERADMIN**)
  * 소프트삭제 유사(비활성화): `DELETE /api/users/{id}` → `is_active=false`
* 마감/업로드

  * 템플릿 다운로드: `GET /api/templates/{dataset}.csv`
  * 업로드: `POST /api/upload/{dataset}` (폼필드: `business_date`, `property_code`, `file`) (**ADMIN+**)
  * 일자별 업로드 상태: `GET /api/closing/status?date=YYYY-MM-DD&property_code=MOP`
  * 월간 캘린더: `GET /api/closing/calendar?month=YYYY-MM&property_code=MOP`
* 대시보드 KPI: `GET /api/reports/dashboard-kpi?date=YYYY-MM-DD&property_code=MOP`

  * rooms: `rooms_status` CSV로 점유/더티 개수 계산
  * front/fnb/exp/pay: `amount` 합계

# 6) 프런트 페이지 현황

* **Dashboard**: 날짜 입력 → KPI 조회 (정상)
* **Closing Board**: 5종 업로드 카드(템플릿/업로드 버튼) (정상)
* **Closing Calendar**: 월간 업로드 현황(진행률, 버전 표기) (정상)
* **Users**:

  * 목록/검색/페이지네이션, 유저 생성, 직원 매핑, 직원 CSV 임포트(대화형)
  * **현재 증상**: “유저 목록이 로드 안 됨” → 아래 “빠른 수정 포인트” 참조
* **Keywords / OTA**:

  * 라우팅만 잡혀 있고, **컴포넌트 매핑 오류**로 Dashboard가 뜨거나 빈 페이지 → 아래 “빠른 수정 포인트”

# 7) 운영 방법(Dev)

```bash
# 백엔드 기동 (백엔드 폴더에서)
source /volume1/web/hotel-system/venv39_py39/bin/activate
cd /volume1/web/hotel-system/backend
: > /tmp/uvicorn.out
PYTHONPATH=/volume1/web/hotel-system/backend \
nohup python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --workers 1 --no-access-log \
  </dev/null >/tmp/uvicorn.out 2>&1 & disown

# 상태확인
curl -s http://127.0.0.1:8000/api/ping

# 프런트 기동 (프런트 폴더에서)
cd /volume1/web/hotel-system/frontend/admin
npm run dev   # 기본 5176
# 브라우저: http://<NAS IP>:5176
```

# 8) 테스트 플레이북 (cURL)

```bash
# 템플릿
curl -I http://127.0.0.1:8000/api/templates/fnb_sales.csv

# 업로드(예시)
curl -F business_date=2025-09-23 -F property_code=MOP -F file=@/tmp/fnb_sales.csv \
  http://127.0.0.1:8000/api/upload/fnb_sales

# 업로드 상태
curl "http://127.0.0.1:8000/api/closing/status?date=2025-09-23&property_code=MOP"

# 캘린더
curl "http://127.0.0.1:8000/api/closing/calendar?month=2025-09&property_code=MOP"

# 대시보드 KPI
curl "http://127.0.0.1:8000/api/reports/dashboard-kpi?date=2025-09-23&property_code=MOP"

# 직원 임포트
curl -F "file=@/volume1/web/hotel-system/backend/_imports/employees.csv" \
  http://127.0.0.1:8000/api/employees/import-csv

# 유저 목록
curl "http://127.0.0.1:8000/api/users?q=&page=1&size=20"
```

# 9) 알려진 이슈 & 빠른 수정 포인트

### (A) 유저 목록이 로드되지 않음

* **원인 후보 1: http 헬퍼의 반환 형태 불일치**

  * 현재 `http.get<T>('users?...')` 가 **JSON 본문을 그대로** 반환하도록 통일되어 있습니다.
  * 따라서 `Users.vue`는 다음처럼 써야 합니다:

    ```ts
    const data = await http.get<{ total:number; items:UserRow[]; page:number; size:number }>(
      `users?q=${encodeURIComponent(q.value)}&page=${p}&size=${size.value}`
    )
    rows.value  = data.items
    total.value = data.total
    ```
  * 만약 `const { data } = await http.get...` 형태가 남아있으면 `Property 'data' does not exist` 오류/빈 화면 발생.
* **원인 후보 2: 라우터 가드/권한 문제**

  * `/api/me` 실패하면 메뉴/보호 라우트 접근이 막히면서 리스트 호출 자체가 안 됨.
  * Dev에선 `X-Debug-Role` 세팅(`setDebugRole('SUPERADMIN')`) + 토큰(dummy) 저장 후 `/api/me` 200 확인 필요.

### (B) Keywords 화면이 Dashboard로 나옴

* **원인**: 라우터에서 `/keywords`가 `Dashboard` 컴포넌트로 매핑됐거나, `import` 경로가 잘못됨.
* **조치**: `src/router/index.ts` 확인.

  ```ts
  { path: '/keywords', component: () => import('@/views/Keywords.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  ```

### (C) OTA 화면 미동작

* **원인**: 라우트는 있으나 컴포넌트 파일이 없거나, 빈 스텁.
* **조치**: 최소 스텁 생성.

  ```vue
  <!-- src/views/OTA.vue -->
  <template><v-container class="py-6"><h2 class="text-h5">OTA Codes (Admin)</h2>
    <v-alert type="info" class="mt-4">초기 스텁 화면입니다. CRUD 추후 연동.</v-alert>
  </v-container></template>
  <script setup lang="ts"></script>
  ```

  라우터:

  ```ts
  { path: '/ota', component: () => import('@/views/OTA.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  ```

### (D) 새로고침 시 로그아웃처럼 보이는 증상

* **원인**: 초기 부트스트랩 시 `/api/me` 실패(백엔드 다운/프록시 실패/토큰 없음).
* **조치**:

  1. 백엔드 헬스체크 OK인지 확인
  2. `vite.config.ts` 프록시 타깃이 실제 백엔드와 일치하는지
  3. Dev에선 `auth.devLogin('SUPERADMIN')` 버튼/액션으로 더미 토큰 + 역할 세팅 후 `/api/me` 200 확인

# 10) 삭제 정책(현행)

* **소프트 삭제 우선**:

  * Employee: `deleted_at`(mixin) 사용
  * User: 현재는 `DELETE /api/users/{id}` → `is_active=false` (완전 삭제 아님)
* **복구**: Employee는 `deleted_at` null로 복구 엔드포인트 추후 추가 예정.

# 11) 다음 스텝(로드맵 제안)

1. **라우터/메뉴 정리**: Keywords/OTA 올바른 컴포넌트 매핑, 가드(roles) 점검.
2. **Users 화면 통일**: http 반환형(직접 JSON) 기준으로 전 컴포넌트 수정.
3. **권한 가드 UX**: 401/403 시 공통 핸들러(토스트/리다이렉트).
4. **Soft Delete 확장**: User에도 SoftDeleteMixin 적용(+ 복구 API).
5. **데이터 분석 확장 준비**: OTA 코드/키워드 관리 화면에서 코드값 저장만 선 구현 → 이후 통계/필터 구조로 확장.

---

필요하면 위 “빠른 수정 포인트(B/C)”용 **짧은 PR** 단위로 라우터/뷰 두 군데만 먼저 정리해도 전체 흐름은 안정화됩니다.
추가 로그나 파일 구조 캡처 주시면, 해당 부분 기준으로 라우터/컴포넌트 경로를 바로 맞춰드릴게요.
