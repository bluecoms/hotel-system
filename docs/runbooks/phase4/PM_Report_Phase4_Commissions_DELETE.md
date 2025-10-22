# 📢 [PM-Hub] Phase 4 BE-Core — Commissions DELETE 연동 결과 (2025-10-03)

## BE-Core
- 신규 엔드포인트 구현:  
  **DELETE /api/ota/commissions/{id}**
  - 성공: 204 No Content
  - 실패:
    - 404: 대상 없음
    - 409: 제약으로 삭제 불가 (옵션)
    - 405: 미구현(FE 주석 확인용)
- 동작 방식:  
  기본은 **하드 삭제**, 감사로그(`audit_logs`) 기록 지원
  - action: `OTA_COMMISSION_DELETE`
  - target: `commission_id={id}`
  - meta_json: `{"hard": true}`

## FE-Core
- Commission.vue 내 **삭제 버튼** → DELETE 호출
- 기대 응답: 204 → 목록에서 즉시 제거
- 실패 시: 에러 메시지 처리(404/409 구분)
- 주석으로 405(미구현) 대응 루틴 존재

## QA
- CRUD 전체 시나리오 검증:
  - POST → 생성
  - PUT → 수정
  - GET → 조회
  - DELETE → 삭제
- Smoke PASS:
  - 존재하지 않는 ID 삭제 시 404
  - 정상 삭제 시 목록에서 제거 확인
  - 감사로그 레코드 확인

## 증빙
- `docs/runbooks/phase4/2025-10-03_BE/evidence/commission_delete_*.txt`
- `.../audit_logs_after_delete.json`

---

✅ 결론: **Commissions CRUD(생성·수정·삭제) End-to-End 동작 PASS**  
➡️ Phase 4 BE-Core는 업로드/Export/페이징/Audit 개발로 계속 진행
