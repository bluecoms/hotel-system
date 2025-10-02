# 🟩 FE-Core 스펙 정의 — Phase 3 (실행 템플릿)

## 0) 범위(Scope)
- **OTA/Commission.vue**: 채널별 커미션 **CRUD UI 완성**  
- **Reports/SalesTags.vue**: **실데이터 기반 차트/테이블** + 합계/필터/빈배열 처리  
- **메뉴/권한**: 사이드바에서 **ADMIN만** OTA/Reports 보이도록(roles 기반), 비ADMIN 차단

---

## 1) 라우트 & 권한 (변경 최소)
- 기존 라우트 유지, **meta.roles=['ADMIN']**로 축소(필요 시):
  ```ts
  // src/router/index.ts (해당 라우트 meta만 확인/정비)
  meta: { requiresAuth: true, roles: ['ADMIN'] }
  ```
- 사이드바는 `/api/menu` 응답 기반 렌더(ADMIN 외 roles에는 노출 금지). 비ADMIN이 직접 URL로 접근 시 가드에서 차단.

---

## 2) OTA — Commission.vue (CRUD UI)

### 2.1 화면 구성
- 상단: **채널 선택(Select)** + 기간 필터(Date Range) + “신규” 버튼
- 본문: **커미션 테이블**
- 하단/전역: **신규/수정 다이얼로그** (공통 폼)

### 2.2 데이터 모델(프런트 수용형)
```ts
type Commission = {
  id?: number
  channel: string            // 채널코드
  valid_from: string         // 'YYYY-MM-DD'
  valid_to: string           // 'YYYY-MM-DD'
  rate: number               // 0~100
  note?: string
}
```

### 2.3 API (FE 기대치 — http.ts 사용)
- 목록: `GET /api/ota/commissions?channel=XXX&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - 수용 응답: `{ items: Commission[] }` 또는 `Commission[]`
- 생성: `POST /api/ota/commissions` body=Commission( id 제외 )
- 수정: `PUT /api/ota/commissions/:id` body=Commission
- 삭제: `DELETE /api/ota/commissions/:id`
- 채널목록(Select용): `GET /api/ota/channels` → `{items:[{code,name}]}` 또는 배열

### 2.4 유효성 & UX 규칙
- 필수: `channel`, `valid_from`, `valid_to`, `rate`
- **값 범위**: `0 ≤ rate ≤ 100`
- **기간 검사**: `valid_from ≤ valid_to` (다이얼로그 저장 시 검사, 실패→스낵바 1종)
- 빈 응답/에러 시 테이블/알림은 **깨짐 없이** 표준 메시지/토스트로 처리
- 로딩바(상단 progress), 에러 스낵바 1종

### 2.5 이벤트 플로우(요약)
- 채널/기간 변경 → `list()` 재호출
- 신규 클릭 → 다이얼로그 open(default 값)
- 저장(POST/PUT) 성공 → 다이얼로그 close → `list()` 갱신 → 스낵바 “저장됨”
- 삭제 확인 → `del()` → `list()` → 스낵바 “삭제됨”

---

## 3) Reports — SalesTags.vue (차트/테이블 고도화)

### 3.1 화면 구성
- 상단: **기간 필터(Date Range)** + (옵션) Property/Tag 필터
- 본문 상단: **막대차트(태그별 금액/건수)** — 프로젝트 공통 `BaseChart.vue` 사용
- 본문 하단: **테이블** + **합계 행** (count/amount 총합)
- 빈 배열 시: “데이터 없음” 알림(Info), 레이아웃 유지

### 3.2 데이터 모델(수용형)
```ts
type SalesTagRow = {
  tag: string
  count: number
  amount: number
}
```

### 3.3 API (FE 기대치)
- `GET /api/reports/sales-tags?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
  - 응답 수용: `{ items: SalesTagRow[] }` 또는 `SalesTagRow[]`
- 에러/빈 배열: 차트는 placeholder, 테이블 no-data, 합계=0 표시

### 3.4 합계 계산 & 차트 데이터
- 합계: `totalCount = Σ count`, `totalAmount = Σ amount`
- 차트 데이터: `labels = rows.map(tag)`, datasets=[count, amount] (단위/축 라벨 표기)

---

## 4) 공통 UX/기술 규칙
- **axios 금지**, `import http from '@/services/http'` 후 `http.get/post/put/del`
- **로딩바 1종 + 에러 스낵바 1종** 표준화
- 응답 수용 형식: 배열/`{items:[]}` 둘 다 허용
- 타입 안전: 
  ```ts
  const body:any = res ?? {};
  const arr = Array.isArray(res) ? (res as any[]) : (Array.isArray(body.items) ? body.items : []);
  ```
- 날짜는 문자열(YYYY-MM-DD)로 주고받기(프런트 포맷 표준화)

---

## 5) DoR (Definition of Ready)
- [x] 라우트/meta.roles=ADMIN 확정 (접근 권한 정의)
- [x] Commission 폼 스키마/필수필드·검증 규칙 정의
- [x] SalesTags 필터(기간) & 합계/차트 정책 정의
- [x] API 엔드포인트·쿼리키 구조 합의(배열/`{items}` 수용)

---

## 6) DoD (Definition of Done)
- [x] **ADMIN 로그인 시**  
  - Commission: 목록 조회/신규 생성/수정/삭제 UI **정상 동작**  
  - SalesTags: 기간 필터 반영, 차트/테이블/합계 **정상 표시**  
- [x] **비ADMIN**: 라우터/사이드바 **비표시 또는 접근 차단**
- [x] 빈 응답/에러에도 **UI 깨짐 없음**, 로딩/스낵바 1종 동작
- [x] axios 미사용, http.ts만 사용

---

## 7) 테스트(실행 체크리스트)
- Commission
  - 채널 선택 + 기간 선택 후 조회 → 행 표시
  - 신규 → rate=150 시도 → 저장 실패(검증 에러 토스트)
  - 정상 값 저장 → 목록 갱신/토스트
  - 행 편집 → 저장 → 갱신
  - 삭제 → 확인 → 갱신
- SalesTags
  - 기간 필터 변경 → 차트/테이블/합계갱신
  - 빈 응답 → no-data + 합계 0
  - 에러 → 스낵바 노출
- 권한
  - ADMIN: OTA/Reports 표시/진입 OK
  - 비ADMIN: 사이드바 비표시 + URL 직접 접근 차단

---

## 8) 코드 스니펫(패턴 예시 — 붙여넣기 OK)

### Commission — list/create/update/delete 패턴
```ts
import http from '@/services/http'

// 조회
async function list(channel:string, from?:string, to?:string){
  const q = new URLSearchParams()
  if(channel) q.set('channel', channel)
  if(from) q.set('date_from', from)
  if(to) q.set('date_to', to)
  const res = await http.get(`/api/ota/commissions?${q.toString()}`)
  const body:any = res ?? {}
  return Array.isArray(res) ? (res as any[]) : (Array.isArray(body.items) ? body.items : [])
}

// 생성/수정/삭제
const create = (payload:any)=> http.post('/api/ota/commissions', payload)
const update = (id:number, payload:any)=> http.put(`/api/ota/commissions/${id}`, payload)
const remove = (id:number)=> http.del(`/api/ota/commissions/${id}`)
```

### SalesTags — fetch & 합계
```ts
import http from '@/services/http'

async function fetchSalesTags(from?:string, to?:string){
  const q = new URLSearchParams()
  if(from) q.set('date_from', from)
  if(to) q.set('date_to', to)
  const res = await http.get(`/api/reports/sales-tags?${q}`)
  const body:any = res ?? {}
  const rows:any[] = Array.isArray(res) ? res : (Array.isArray(body.items) ? body.items : [])
  const totals = rows.reduce((acc, r)=>({
    count: acc.count + Number(r.count||0),
    amount: acc.amount + Number(r.amount||0)
  }), {count:0, amount:0})
  return { rows, totals }
}
```
