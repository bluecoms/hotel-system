# 📄 FE-Core 전달 사항 — Phase 3 (2025-10-01)

## 0. 공통 규칙
- **HTTP 클라이언트**: `@/services/http` (fetch 기반)만 사용. **axios 금지**.  
- **경로 규칙**: 프론트 호출은 `/ota/*`, `/reports/*` → Vite 프록시 통해 `/api`로 전달.  
- **Vite 프록시 설정** (`vite.config.ts`):
  ```ts
  server: {
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, secure: false } }
  }
  ```
- 절대 `"/api/api/..."` 중복 호출 금지.  

---

## 1. OTA 커미션 화면 (Commission.vue — CRUD)
- 상태: READ/CREATE/UPDATE 완료, DELETE는 BE 미구현 → 버튼 비활성(툴팁 표기).  
- **유효성 검증**
  - rate: `0 ≤ rate ≤ 100`  
  - 기간: `valid_from ≤ valid_to`  
  - channel 필수  
- **겹침 프리체크** (현재 목록 rows 기준, 자기 자신 제외)
  ```ts
  const overlaps = (aFrom,aTo,bFrom,bTo) => (aFrom <= bTo) && (bFrom <= aTo)
  const same = rows.value.filter(r => r.channel === form.value.channel && (editItem.value?.id ? r.id !== editItem.value.id : true))
  const hit = same.find(r => overlaps(form.value.valid_from, form.value.valid_to, r.valid_from, r.valid_to))
  if (hit) return toast('기간 겹침: ' + hit.valid_from + ' ~ ' + hit.valid_to)
  ```
- **에러 처리 가이드**
  ```ts
  catch (e:any) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    if (status === 409) toast(detail || 'Overlapping period for the channel')
    else if (status === 400 || status === 422) toast(detail || '요청 값이 올바르지 않습니다.')
    else toast(e?.message || '저장에 실패했습니다.')
  }
  ```
- **기능 요약**
  - 저장 중 중복 클릭 방지(saving flag)  
  - 취소 시 폼 리셋  
  - API:  
    - `GET /api/ota/commissions?channel=&date_from=&date_to=`  
    - `POST /api/ota/commissions`  
    - `PUT /api/ota/commissions/{id}`  

---

## 2. OTA 채널 목록 (OTAList.vue — READ)
- 기능: `GET /api/ota/channels`  
- 응답: 배열 or `{items:[]}` 모두 수용  
- 표 렌더/빈 데이터 처리/스낵바 에러 처리 포함  
- 액션 없음 (Phase3 범위 제외)

---

## 3. 리포트 — Sales Tags (SalesTags.vue — READ)
- 기능: `GET /api/reports/sales-tags?date_from=&date_to=`  
- 응답: 배열 or `{items:[]}` 모두 처리  
- **강화 사항**  
  - 합계 카드 + 테이블 푸터 합계 표시  
  - 숫자 포맷: `Intl.NumberFormat('ko-KR')`  
  - 에러 처리:  
    - 400/422 → 서버 detail 노출  
    - 그 외 → 공통 메시지  

타입:
```ts
type Row = { tag: string; count: number; amount: number }
```

---

## 4. 스모크 테스트 시나리오

### 4-1. 네트워크/프록시
- DevTools Network 확인:  
  - `GET /api/ota/channels` → 200  
  - `GET /api/ota/commissions?...` → 200  
  - `GET /api/reports/sales-tags?...` → 200  
- `/api/api/...` 요청 없어야 함

### 4-2. 커미션 CRUD
- 생성 201 → 성공 스낵바 “생성되었습니다.”  
- 겹침 409 → 서버 detail 그대로 노출 (예: *Overlapping period for the channel*)  
- 수정 200 → 목록 갱신  
- 프리체크 → 서버 전 검증 스낵바: *기간 겹침: YYYY-MM-DD ~ YYYY-MM-DD*  
- 유효성:  
  - rate=150 → “rate는 0~100 사이여야 합니다.”  
  - valid_from > valid_to → “기간이 역전되었습니다.”

### 4-3. 채널 목록
- 빈/있는 경우 모두 표 정상 렌더  
- 에러 시 스낵바 1종 노출

### 4-4. Sales Tags
- 기간 미지정/지정 → 조회 OK  
- 빈 배열 → “데이터 없음” + 합계 0  
- 데이터 존재 → 테이블 합계 = 카드 합계一致

---

## 5. 파일 경로 요약
- `src/views/OTA/Commission.vue` ← CRUD + 프리체크 + 에러 메시지 강화 + 저장 중 중복 방지 + 취소 리셋 + 삭제 버튼 비활성  
- `src/views/OTA/OTAList.vue` ← 채널 목록 READ  
- `src/views/Reports/SalesTags.vue` ← 리포트 READ + 합계/에러 강화  
- `vite.config.ts` ← `/api` 프록시 (포트 8000)
