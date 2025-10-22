````markdown
#  [PM-Hub] FE 작업 결과 보고 (Users / Employees / Closing / Reports / Dashboard 완료)

##  공통 상태
- 빌드/런타임 오류 **0**
- 라우트 충돌 및 404 없음
- Dashboard, Closing, Reports, OTA, Upload, Admin Users/Employees 메뉴 정상 진입
- 모든 통신은 **src/services/http.ts (fetch 기반)** 사용 — Axios 금지
- `X-Internal-Token` 헤더 인증 정상

---

##  라우팅 정리
### router/index.ts
```ts
const Users      = () => import('@/view/Users/Users.vue')
const Employees  = () => import('@/view/Users/employees.vue')

{ path: '/admin/users', name: 'admin-users', component: Users,
  meta: { title: 'Users', roles:['SUPERADMIN'], requiresAuth:true } },
{ path: '/admin/employees', name: 'admin-employees', component: Employees,
  meta: { title: 'Employees', roles:['ADMIN','SUPERADMIN'], requiresAuth:true } },
````

### router/menu.ts

```ts
{ label: 'Users', to: '/admin/users', icon: 'mdi-account-cog', roles: ['SUPERADMIN'] },
{ label: 'Employees', to: '/admin/employees', icon: 'mdi-account-group', roles: ['ADMIN','SUPERADMIN'] },
```

---

##  Users.vue

* CRUD + 사원 매핑 완전 동작
* **SUPERADMIN 전용**:

  * 신규 생성
  * 활성/비활성 toggle
  * 사원 Import (`/api/employees/import`)
* Alert/Msg 핸들링 개선

##  employees.vue

* 사원 목록 + 상세 HR 카드 + 계정 매핑
* CSV/XLS 업로드 (`/api/employees/import`)
* 템플릿 다운로드 (`/api/templates/employees.csv`)
* 계정 생성 버튼 (`/api/users/from-employee`)
* `Ctrl+S` 저장 단축키
* Vuetify 3 `v-data-table` 최신 문법(`v-model:page`) 적용

---

##  Closing.vue

* 달력 레이아웃 복원 (`.cal-grid`, `.week-row`, `.day-card` 스타일 포함)
* `UploadNeedDialog` 클릭 레이어 정상 오픈
* `CLOSED` 클릭 시 안내만 출력(toast)
* Toast 개선: 자동소멸 + `clear/remove` 지원
* `@click.stop` 반영 → 버튼 클릭 시 카드 클릭 이벤트 차단

---

##  Reports/SalesTags.vue

* 탭 2종 전환(객실 / F&B) 정상
* “Not Found” → 한국어화 (“페이지를 찾을 수 없습니다”)
* `KeywordTester` 제거, KPI store 제거
* 날짜 필터, 로딩/빈 데이터 대응 완비

---

##  Dashboard.vue

* KPI 카드 + “재고 요약”, “근태 요약” **스켈레톤 카드 2종** 추가
* 향후 BE 연동 시 값만 주입

---

##  useToast.ts

* 자동 제거 및 수동 `clear` 지원
* 확장형 메시지 템플릿:

  * `success`: 저장, 생성, 완료
  * `error`: 실패, 권한 오류, 네트워크 장애
  * `info`: 로드, 알림

---

##  i18n/messages.ko.ts

```ts
state: {
  empty: '데이터가 없습니다',
  error: '요청 처리 중 오류가 발생했습니다',
  notFound: '페이지를 찾을 수 없습니다',
},
auth: {
  noPermission: '권한이 없습니다',
  needLogin: '로그인이 필요합니다',
},
closing: {
  title: '일자별 마감 현황',
  open: 'OPEN',
  closed: 'CLOSED',
  needUpload: '업로드 필요 항목',
},
```

---

## ⚙️ DoD (최종 기준)

* 빌드 및 런타임 경고 0
* `/ota` 탭 전환 3종 정상
* `/reports/sales-tags` 탭 전환/날짜 필터 OK
* `/closing` 미완료 클릭 → 레이어 → 이동 OK
* `/dashboard` 스켈레톤 2종 노출 OK
* `/admin/users`, `/admin/employees` 노출 및 기능 정상

```
```
