좋아. 프런트 전달사항은 “기존 13개 항목을 절대 생략 없이” 그대로 포함하고, 추가 이슈들을 14번 이후로 정리해 붙였어. 전부 ASCII만 썼고, 이모지나 특수 숫자 기호 없음.

---

## Frontend Integration Guide v1

1. 서버와 포트

* 동일 NAS에서 개발과 운영이 함께 동작
* 개발 서버: [http://192.168.0.6:8001](http://192.168.0.6:8001)
* 운영 서버: [http://192.168.0.6:8000](http://192.168.0.6:8000)
* 현재 운영 서버는 의미 없음. 개발 서버(8001)만 대상

2. 인증 헤더

* 모든 업로드/적용 API는 내부 토큰 필요
* Header: X-Internal-Token: dev-admin-token
* 권한: ADMIN 또는 SUPERADMIN 필요 (백엔드에서 검사함)

3. 공통 폼 필드

* business_date: YYYY-MM-DD (필수)
* property_code: 기본 MOP (미지정 시 MOP로 보냄)
* dry_run: 0 또는 1 (업로드 시만 사용)
* file: multipart/form-data 의 파일 파트
* split_by_date: 필요 시 0 또는 1 (sales_front 기본 0, rooms_status 기본 1)

4. 사용 가능한 엔드포인트

* POST /api/upload/rooms_status

  * 기능: CSV 업로드 저장
  * 응답 예시(dry_run=1): { ok: true, dry_run: true, counts.rows: 123 }
  * 응답 예시(dry_run=0): { ok: true, dry_run: false, dataset, version_no, file.path }
* POST /api/upload/sales_front

  * 위와 동일 패턴. split_by_date=1 지원
* POST /api/upload/fnb_sales

  * file_pay, file_items 두 파일 파트 사용
* POST /api/upload/bank_ledger

  * account_code 폼 필드 추가
* GET /api/upload/versions?dataset=xxx&business_date=YYYY-MM-DD&property_code=MOP

  * 업로드 버전 목록. 없으면 items: [] 반환
* GET /api/upload/canon?dataset=xxx&business_date=YYYY-MM-DD&property_code=MOP

  * 정규화된 CSV 다운로드. 브라우저 다운로드 또는 텍스트 미리보기 용
* POST /api/upload/apply/rooms_status

  * 최신 업로드를 DB에 반영. 응답 예시: { ok: true, dataset: "rooms_status", applied: 42 }

5. 예약 이슈 정리

* reservations 라우트 및 개념은 사용하지 않음
* 예약 데이터도 rooms_status 로 일원화
* 프런트 표기, 메뉴, 로그 모두 rooms_status 로 통일

6. 업로드 파일 관련

* NAS에 샘플이 항상 있다고 가정하지 말 것
* 파일 입력은 로컬 파일 선택 또는 메모리 스트림(FormData에 Blob)로 전송 가능
* 큰 파일 업로드 시 progress 이벤트 처리 가능. 서버 타임아웃 기본값 내에서 완료됨

7. 예외와 상태코드

* 200 OK: 정상 처리
* 422 Unprocessable Entity: 날짜 형식 등 검증 실패
* 401/403: 토큰 또는 권한 문제
* 404 Not Found: 데이터셋 없음, 또는 파일 이력 전무한 상태에서 일부 조회 API 호출
* 405 Method Not Allowed: HEAD로 file 엔드포인트 호출 시 발생. GET만 사용
* 에러 응답 포맷: { detail: "메시지" } 또는 { ok: false, error: "메시지" }

8. CORS 및 도메인

* 허용 오리진에 로컬 개발 도메인 5173 포함
* 프런트는 fetch 사용 시 credentials 기본 off. 필요 시 쿠키 미사용 전제

9. 샘플 호출 흐름

* 업로드 드라이런

  * POST /api/upload/rooms_status
  * form: business_date, property_code, dry_run=1, file
  * 응답에서 preview.head, counts.rows 확인 후 안내 표시
* 실제 저장

  * 같은 엔드포인트에 dry_run=0
  * 응답의 version_no, file.path 로 완료 배지 표시
* 적용

  * POST /api/upload/apply/rooms_status
  * 적용 결과인 applied 건수 표시
* 검증용 프리뷰

  * GET /api/upload/canon?dataset=rooms_status&business_date=...&property_code=...

10. 프런트 구현 유의사항

* 파일 업로드는 반드시 multipart/form-data
* FormData 키 이름은 백엔드와 정확히 일치시킬 것

  * business_date, property_code, dry_run, file
* 파일 없이 apply 호출 가능. apply 는 서버에 저장된 최신 버전을 사용
* 숫자 이모지, 특수 문자인 버튼 라벨 금지. UTF-8 텍스트만 사용
* rooms_status 화면에서 버전 보기, 정규화 미리보기, 적용 세 단계 버튼 구성 권장
* 오류 메시지는 서버 detail 문구 그대로 보여주되 사용자 안내 문구 별도 추가

11. 개발 서버 점검 포인트

* 스웨거: GET /api/openapi.json
* 헬스: GET /api/upload/ping
* 로그 파일

  * 유저가 보는 운영 로그는 별도. 프런트는 네트워크 에러만 브라우저 콘솔로 확인

12. 데이터셋별 필드 힌트

* rooms_status canon 헤더: business_date, property_code, room_no, status_code, is_dirty, hk_note
* sales_front canon 헤더: business_date, property_code, tag, amount
* bank_ledger canon 헤더: business_date, property_code, account_code, direction, amount, balance_after, note, branch, txn_time

13. 용어 정리

* SSOT: Canon CSV가 유일한 진실. 조회는 canon 기준
* split_by_date: 여러 날짜가 한 파일에 섞여 있을 때 날짜별로 분할 저장하는 옵션
* apply: 최신 업로드를 실제 테이블에 반영

---

## Addendum: 추가 주의사항과 장애 포인트

14. Content-Type 헤더 자동 설정

* fetch 로 업로드할 때 Content-Type 을 수동으로 multipart/form-data 로 지정하지 말 것.
* FormData 를 그대로 body 로 넘기면 브라우저가 boundary 포함해 자동 설정한다.
* 수동 지정 시 boundary 누락으로 422 또는 빈 바디 처리 가능.

15. 파일 이름과 확장자

* 파일 파트에 filename 이 없으면 일부 환경에서 파일명 빈 문자열로 저장됨.
* Blob 업로드 시 new File([...], "rooms_status.csv") 형태로 파일명을 명시하는 것을 권장.

16. 인코딩과 줄바꿈

* 백엔드는 UTF-8-sig, cp949, euc-kr 를 자동 판별. 프런트는 어떤 인코딩이든 그대로 전송.
* CSV 안쪽 줄바꿈은 CRLF/LF 모두 허용. 엑셀에서 저장한 CSV도 그대로 전송.

17. 날짜 포맷

* 폼의 business_date 는 YYYY-MM-DD 권장.
* 파일 내부의 날짜는 다양한 포맷을 허용하나, 혼재된 경우 split_by_date 동작을 고려.

18. HEAD 요청 금지

* 파일 존재 확인을 HEAD 로 하지 말고, GET /api/upload/versions 결과로 판별.
* HEAD 로 /api/upload/file, /api/upload/canon 호출하면 405가 뜬다.

19. 권한 토큰 취급

* X-Internal-Token 은 FE 로컬 개발에서만 사용. 저장 위치는 .env.local 등 비공개 영역.
* Authorization 헤더와 혼용하지 말 것.

20. 버전 선택 적용

* apply/rooms_status 는 기본적으로 최신 버전을 사용.
* 특정 버전을 적용하는 파라미터(version_no)는 서버에 존재하더라도 공개 UI에서는 최신만 쓰는 정책.
* UI 상에서는 “가장 최근 업로드”를 명확히 표기하고, 과거 버전은 프리뷰 및 다운로드 용도로만 노출.

21. 동시 업로드와 중복 클릭

* 버튼 디바운스 또는 비활성 처리로 중복 제출 방지.
* 동일 파일 재업로드는 허용되며, apply 이전에는 DB에 반영되지 않는다.

22. 큰 파일 전송

* 진행률 UI 구현 시 XMLHttpRequest 또는 fetch + ReadableStream 을 사용.
* AbortController 로 취소 가능하게 만들 것.

23. 오류 처리 패턴

* 서버는 detail 필드를 반환. 프런트는 detail 우선 노출.
* 422 에러 중 rate, date range 관련 메시지는 번역 문자열이 이미 서버에 있음. 단순 노출로 충분.

24. 미리보기 안전 처리

* preview.head 는 5행 정도만 제공. 전체를 표시하려면 canon 다운로드를 사용.
* 미리보기 렌더 시 CSV 안의 큰 수치가 과학표기법으로 바뀌지 않도록 문자열로 다루기.

25. 파라미터 키 누락 체크

* rooms_status 업로드 시 반드시 business_date, file 두 키가 있어야 함.
* property_code 미지정 시 MOP 기본값을 서버가 채우지만, 프런트에서도 기본값을 명시 전송 권장.

26. bank_ledger 주의

* account_code 를 Form 에 포함해야 계좌별 파일이 구분 저장됨.
* 같은 날짜라도 account_code 가 다르면 별도 버전으로 관리.

27. FNB 업로드

* fnb_sales 는 file_pay, file_items 두 파트가 모두 필요.
* 한쪽만 업로드하면 422 발생. 드래그 앤 드롭 멀티선택 또는 두 입력 필드 제공.

28. 캐논 다운로드 응답

* Content-Disposition 헤더로 파일명 설정됨.
* 브라우저에서 바로 열 때 한글 파일명이 꺾이면, 수동 저장 버튼과 함께 제공 권장.

29. UI 워크플로

* 1 업로드 드라이런 결과 표시(counts.rows, preview.head)
* 2 저장(dry_run=0) 후 version_no 표기
* 3 적용(apply) 후 applied 건수 표기
* 4 필요 시 canon 다운로드로 추가 검증

30. 환경 분기

* .env 등에서 API_BASE_URL 을 8001(dev) 과 8000(prod)로 분리.
* 현재는 8001만 의미 있으나, 훗날 전환 대비 분기 코드는 유지.

31. 파일 보관소 경로는 서버 내부

* 프런트는 NAS 경로에 직접 접근하지 않는다.
* 버전 조회와 다운로드는 반드시 API로만 처리.

32. split_by_date 의미

* sales_front: 기본 0. 요청에 따라 1로 보내면 날짜별로 분할 저장.
* rooms_status: 기본 1. 여러 날짜가 포함된 엑셀 덤프를 그대로 올려도 된다.

33. 네트워크 타임아웃

* 프런트 요청 타임아웃을 너무 짧게 두지 말 것. 30초 이상 권장.
* 재시도는 업로드가 중복될 수 있으므로, 재시도 전에 사용자가 중복 업로드를 의도했는지 확인 모달 권장.

34. 로깅과 디버그

* 서버는 app_debug.log 로 별도 로깅 중.
* 프런트는 네트워크 에러만 콘솔에 출력하고, 사용자에게는 간결한 알림 제공.

35. 용어와 화면 라벨

* reservations 라벨 금지. rooms_status 로 통일.
* FNB 는 outlet_code 기반. 화면에서 Outlet 을 기본 용어로 사용.

---

36. 엔드포인트 명세 (최신 백엔드 기준)

1) 업로드 Upload
   POST /api/upload/{dataset}
   예: /api/upload/rooms_status, /api/upload/sales_front, /api/upload/fnb_sales, /api/upload/pay_settlement, /api/upload/expenses, /api/upload/bank_ledger

필수 Form 필드

* business_date: YYYY-MM-DD
* property_code: 기본 MOP
* dry_run: 0 또는 1
* split_by_date: 0 또는 1 (dataset별 기본값 다름)
* file: CSV 파일 (multipart/form-data)
  옵션
* outlet_code: FNB용
* account_code: bank_ledger용
* source_kind: daily|weekly|monthly|full

응답

* dry_run=1 → { ok, dry_run: true, counts, preview, plan }
* dry_run=0 → { ok, dry_run: false, dataset, version_no, file_path }

2. 버전 목록
   GET /api/upload/versions?dataset=rooms_status&business_date=2025-10-08&property_code=MOP
   응답: { ok: true, items: [ {version_no, created_at, file_name, rows}, ... ] }

3. 원본 파일 다운로드
   GET /api/upload/file/{file_id}/download
   옵션 쿼리 inline=1 사용 시 브라우저 미리보기 가능

4. 정규화(캐논) CSV 조회
   GET /api/upload/canon?dataset=rooms_status&business_date=2025-10-08&property_code=MOP
   응답: CSV 텍스트 스트림 (Content-Type: text/csv)

5. 데이터 적용 (Apply)
   POST /api/upload/apply/{dataset}
   예: /api/upload/apply/rooms_status, /api/upload/apply/sales_front 등
   폼 파라미터

* business_date
* property_code
* (파일 없음)

응답: { ok: true, dataset, applied, mode, batch_id }

6. Merge 이력 조회
   GET /api/merge/batches?dataset=rooms_status
   응답: { ok: true, items: [ {batch_id, created_at, mode, counts}, ... ] }

7. Merge 로그 상세
   GET /api/merge/batch/{batch_id}/changelog
   응답: { ok: true, items: [ {action, key_hash, reason}, ... ] }

---

37. 연결 시 자주 발생하는 문제

* 경로 오타: /api/upload/apply/rooms_status 에서 apply 앞뒤 슬래시 누락 주의
* dataset 파라미터 대소문자: 반드시 소문자 (rooms_status, sales_front 등)
* FormData 내 키 이름 오타: businessDate(X) → business_date(O)
* Content-Type 직접 지정으로 boundary 누락: 절대 금지
* 파일 미포함 상태로 /upload 호출 시 422 발생
* apply 호출 시 dry_run 필드 포함 금지 (있으면 무시되거나 422 가능)
* versions 호출 시 dataset 또는 business_date 누락 → 422
* 브라우저 CORS 오류 발생 시 dev proxy 확인 (5173 → 8001 proxy 정상동작 필요)
* 토큰 누락 시 401 Unauthorized
* property_code 누락 시 MOP 기본값 자동 삽입되지만, 프런트에서도 기본값 지정 권장

---

38. 호출 순서 권장 플로우

1단계: 파일 업로드(dry_run=1)
→ 응답 preview.head 표시
2단계: 업로드 확정(dry_run=0)
→ version_no, file_path 저장
3단계: apply 호출(파일 없이)
→ 최신 업로드 적용
4단계: /api/upload/versions 재조회하여 최신 상태 확인
5단계: /api/upload/canon 으로 CSV 프리뷰 제공

---

39. 개발/QA 호출 예시

업로드 드라이런

```
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-08 \
  -F property_code=MOP \
  -F dry_run=1 \
  -F file=@/path/to/rooms_status_sample.csv \
  http://192.168.0.6:8001/api/upload/rooms_status | jq .
```

적용

```
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-08 \
  -F property_code=MOP \
  http://192.168.0.6:8001/api/upload/apply/rooms_status | jq .
```

---


