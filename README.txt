좋아—**지금 상태에 맞춘 “유효한 명령/설정 + 안전성 체크리스트” 최신본**으로 깔끔히 정리할게. (네 환경: NAS 경로, 포트, npm 사용, Vite 5173, Uvicorn 8000 기준)

---

# 1) 올리고 내리기 (스크립트)

```bash
# 한방 올림
bash /volume1/web/hotel-system/scripts/dev-up.sh

# 한방 내림
bash /volume1/web/hotel-system/scripts/dev-down.sh

# 개별
bash /volume1/web/hotel-system/scripts/run-backend.sh
bash /volume1/web/hotel-system/scripts/stop-backend.sh
bash /volume1/web/hotel-system/scripts/run-frontend.sh
bash /volume1/web/hotel-system/scripts/stop-frontend.sh
```

> 위 스크립트들은 “현재 구조”에서도 그대로 유효.

---

# 2) 수동 기동 (개발용)

## 백엔드 (Uvicorn)

# uvicorn / vite 싹 종료
pkill -f "uvicorn .*app.main:app" || true
pkill -f "vite" || true

cd /volume1/web/hotel-system/backend
source ../venv39_py39/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

## 프런트 (Vite)

cd /volume1/web/hotel-system/frontend/admin
source ../venv39_py39/bin/activate
npm run dev:all

# 3) 프런트 .env (개발)

```dotenv
# 비워두면 /api를 Vite 프록시가 백엔드로 전달
VITE_API_BASE_URL=

# 프록시 타깃(같은 NAS면 127.0.0.1, 외부기기에선 NAS IP)
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
# VITE_DEV_PROXY_TARGET=http://172.30.1.4:8000  # 외부/다른 PC 접속 시

VITE_HTTPS=false
VITE_ALLOWED_HOSTS=172.30.1.4

# 관리자 토큰 (아래 로그인에서 받은 access_token 붙여넣기)
VITE_ADMIN_TOKEN=<PASTE_ACCESS_TOKEN>
```

> ✅ http.ts가 이 값을 읽어 **Authorization 헤더(또는 X-Internal-Token)로 자동 반영**되게 되어 있음(네 코드 기준).

---

# 4) 관리자 토큰 발급

```bash
# (서버 설정에 맞는 편으로)
# 1) form 방식
curl -s -X POST "http://127.0.0.1:8000/api/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "username=admin@example.com&password=admin1234"

# 2) json 방식
curl -s -X POST "http://127.0.0.1:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin1234"}'
```

> 응답의 `access_token` → **VITE\_ADMIN\_TOKEN**에 붙여넣고 프런트 재시작.

---

# 5) 스모크/헬스 체크

```bash
# 백엔드 살아있는지
curl -s http://127.0.0.1:8000/api/ping

# 내 정보(권한)
curl -s http://127.0.0.1:8000/api/me

# 메뉴
curl -s http://127.0.0.1:8000/api/menu
```

---

# 6) 템플릿 & 업로드 & 리포트

```bash
# 템플릿
curl -I http://127.0.0.1:8000/api/templates/fnb_sales.csv

# 업로드 (모든 데이터셋 동일 패턴)
curl -F business_date=2025-09-23 -F property_code=MOP \
     -F file=@/tmp/fnb_sales.csv \
     http://127.0.0.1:8000/api/upload/fnb_sales

# 업로드 상태 / 월 캘린더 / KPI
curl "http://127.0.0.1:8000/api/closing/status?date=2025-09-23&property_code=MOP"
curl "http://127.0.0.1:8000/api/closing/calendar?month=2025-09&property_code=MOP"
curl "http://127.0.0.1:8000/api/reports/dashboard-kpi?date=2025-09-23&property_code=MOP"
```

> ✅ 파일명은 자동 버저닝(`…_YYYY-MM-DD_vN.csv`)이라 **같은 이름 반복 업로드 OK**.

---

# 7) 유저/직원 빠른 점검

```bash
# 유저 목록
curl "http://127.0.0.1:8000/api/users?q=&page=1&size=20"

# 직원 임포트
curl -F "file=@/volume1/web/hotel-system/backend/_imports/employees.csv" \
     http://127.0.0.1:8000/api/employees/import-csv
```

---

# 8) TypeScript/Vuetify 타입 에러 튕김 방지(선택)

`tsconfig.json`에 아래(이미 있으면 유지):

```json
{
  "compilerOptions": {
    "skipLibCheck": true,
    "types": ["vite/client", "vuetify"]
  }
}
```

> Vuetify d.ts(특히 labs VVideo) 관련 에러를 **빨리 잠재우는 실전 설정**.
> (엄밀한 타입 검증은 점진적으로 켬)

---

# 9) 자주 나는 오류 & 즉시 해결법

* **401 Unauthorized**
  → 토큰 만료/불일치. 토큰 재발급 후 `.env`의 `VITE_ADMIN_TOKEN` 갱신 → Vite 재시작.
  → 프록시 사용 시 `VITE_API_BASE_URL`은 **빈 값**이어야 함.

* **403 Forbidden**
  → 역할 부족. SUPERADMIN/ADMIN 권한 확인(개발에서는 디버그 역할 헤더를 켜둔 경우만 허용).
  → prod에서는 **X-Debug-Role 금지**.

* **ECONNREFUSED / 프록시 에러**
  → 백엔드 먼저 켜고(`8000` 확인), `VITE_DEV_PROXY_TARGET`이 실제 백엔드로 향하는지 점검.

* **포트 점유(5173/8000)**
  → `ps aux | grep -E "uvicorn|vite"` → `kill -9 <PID>` 후 재기동.

* **서버 로그 보기**
  → `tail -n 200 /tmp/uvicorn.out`

---

# 10) 운영/안전성(우리가 약속한 가드레일)

**권한/역할**

* 운영 1차 릴리즈: **SUPERADMIN, ADMIN**만 사용.
* SUPERADMIN: 모든 화면/액션 허용 **(단, 삭제는 하드 삭제 금지)**
* ADMIN: 업로드/읽기/쓰기 허용, **삭제 불가**.

**삭제 정책(Soft Delete 원칙)**

* DB에는 `deleted_at`/`deleted_by` 기록. 조회 시 기본필터 `deleted_at IS NULL`.
* UI는 삭제 전에 **강한 Confirm**.
* 복구가 필요하면 `/restore` 류의 엔드포인트 추가 예정(지금은 운영 중 실삭제 없음).

**파일/데이터 안정성**

* 업로드는 항상 **버전 누적 저장**(덮어쓰기 금지).
* `_uploads` 경로 상시 보관, 버전 번호로 롤백 용이.
* 템플릿 헤더가 틀리면 400으로 **초기 차단**.

**환경 분리**

* `APP_ENV=prod`일 때:

  * `X-Debug-Role`/DEV 토큰 **무시**.
  * CORS/보안 헤더/로그 레벨 보수적으로.
  * Uvicorn은 `--reload` 끄고 **workers** 사용(예: `--workers 2~4`).

**로그/백업**

* Uvicorn 로그 `/tmp/uvicorn.out`. 롤링 필요시 logrotate 설정.
* DB/업로드 디렉토리 정기 백업(스냅샷).
* 배포 전 `alembic upgrade head`(쓰고 있으면) → 백업 → 재시작.

**프런트 안정성**

* 메뉴/라우터는 `meta.roles`로 보호. 미일치면 `/403`로 리다이렉트.
* **Confirm + 토스트** 패턴 통일. 실패도 사용자에게 명확 피드백.
* TypeScript는 `skipLibCheck`로 외부 d.ts 폭발 방지, 내부 코드 위주로 점진 개선.

**장애 대응 플로우**

1. 프런트 5xx 보이면 **먼저 백엔드 로그** 확인(`tail /tmp/uvicorn.out`).
2. 401/403이면 **토큰/역할/헤더** 체크.
3. 업로드 반영 안 되면 **closing/status / calendar / KPI** 순서로 원인 추적.
4. 포트 충돌/좀비 프로세스 정리 후 재시작.

---

---

# 0) 한 번만 해두는 기초 설정 (설정함)

## tsconfig.json (타입 폭탄 방지)

`skipLibCheck`을 켜서 Vuetify d.ts 에러들을 막아둡니다.

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "preserve",
    "strict": true,
    "skipLibCheck": true,
    "types": ["vite/client", "vuetify"],
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

# 1) 필요한 도구 설치(설치함)

```bash
cd /volume1/web/hotel-system/frontend/admin

# 타입체크, 멀티 스크립트 실행 도구
npm i -D vue-tsc concurrently npm-run-all

# (이미 있다면 생략) 안 쓰는 import 잡을 때
npm i -D eslint-plugin-unused-imports
```

---

# 2) package.json 스크립트 추가/정리 (추가함)

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "vite build",
    "preview": "vite preview --port 5173",

    "typecheck": "vue-tsc --noEmit",
    "typecheck:watch": "vue-tsc --noEmit --watch",

    // 둘 다 동시에(프런트 + 타입체크 감시)
    "dev:all": "run-p dev typecheck:watch"
  }
}
```

* `dev` : Vite 개발 서버
* `typecheck` : 단발성 타입 검사
* `typecheck:watch` : 파일 변경 시마다 **실시간 타입 검사**
* `dev:all` : 둘을 같이 실행(터미널 하나에서 병렬 실행)

> 포트 5173은 현재 환경 기준 통일. 이미 점유돼 있으면 아래 “트러블슈팅” 참고.

---

# 3) .env 개발값 확인

`/volume1/web/hotel-system/frontend/admin/.env` (또는 `.env.development.local`)에 최소 이렇게:

```dotenv
VITE_API_BASE_URL=
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
VITE_HTTPS=false
VITE_ALLOWED_HOSTS=172.30.1.4
VITE_ADMIN_TOKEN=<관리자 access_token>
```

> `VITE_API_BASE_URL` 비워두면 `/api`가 **Vite 프록시**를 통해 백엔드(8000)로 향합니다.

---

# 4) 실행 방법 (Watch 포함)

### 방법 A) 터미널 하나에서 같이 돌리기 (추천)

```bash
# 프런트 + 타입체크 워치 동시 실행
npm run dev:all
```

### 방법 B) 터미널 두 개로 나눠 돌리기

```bash
# 터미널 1: Vite
npm run dev

# 터미널 2: 타입체크 감시
npm run typecheck:watch
```

둘 다 켜두면, 코드 저장할 때마다:

* 브라우저는 Vite HMR로 즉시 새로 그림
* 타입 에러는 터미널에 실시간으로 표시

---

# 5) 자주 나는 이슈 빠른 해결

* **포트 점유 (5173/8000)**

  ```bash
  # 뭐가 물고 있는지 확인
  ps aux | grep -E "vite|uvicorn"

  # 걸려 있으면 종료
  kill -9 <PID>
  ```

* **/api 프록시 에러 (ECONNREFUSED)**
  → 백엔드 먼저 켜기:

  ```bash
  cd /volume1/web/hotel-system/backend
  source ../venv39/bin/activate
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

  → 그리고 프런트 `npm run dev` 또는 `npm run dev:all`.

* **401/403**
  → 토큰 갱신해서 `.env`의 `VITE_ADMIN_TOKEN` 다시 저장 → 프런트 재시작.
  → 역할권한 필요한 화면이면 SUPERADMIN/ADMIN인지 확인.

* **Vuetify d.ts 타입 에러 폭주**
  → `tsconfig.json`의 `skipLibCheck:true`가 켜져 있어야 함.
  → 그래도 뜨면 일단 `typecheck:watch` 종료하고 `dev`만 띄워도 개발은 계속 가능.

---

# 6) 의미 정리 (왜 이렇게 쓰는지)

* **Vite(dev)**: 브라우저 HMR(핫 리로드) 담당. 빌드 없이 빠른 개발.

* **vue-tsc --watch**: Vue SFC + TS 타입을 **런타임과 별개로** 계속 검사.
  → 빌드는 성공해도 타입 문제가 숨어 있는 걸 **사전에** 잡아줌.
  → Vite가 깨지는 걸 막고, 에러를 안전하게 터미널에서만 경고.

* **run-p (npm-run-all)**: 여러 npm 스크립트를 **병렬**로 동시에 실행.


필요하면 **eslint/prettier 워치**도 더 붙여줄 수 있어. 우선은 `dev:all`로 \*\*“화면 갱신 + 타입 감시”\*\*가 다 되니까 이 조합으로 안정적으로 가자.


sql명령어 사용 셸에서 DB 열기

sqlite3 /volume1/web/hotel-system/backend/hotel.db


