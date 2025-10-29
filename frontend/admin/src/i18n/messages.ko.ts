// ============================================================================
// File      : src/i18n/messages.ko.ts
// Version   : 2025.11-09 · v4.3 (SSOT Phase 4 Final · RoomType/HKUnitRule/HK 보드 추가)
// Purpose   : Hotel Admin — i18n Korean Messages (프런트 전역 한글 리소스)
// ----------------------------------------------------------------------------
// 변경 요약 (v4.3)
//   ✅ 네비게이션: 하우스키핑(nav.housekeeping) 추가
//   ✅ 기준정보: 객실 타입 / 하우스키핑 단위규칙(master.*) 라벨/필드 추가
//   ✅ 하우스키핑 보드(hk.*): 빌드/배정/통계/유닛 관련 문자열 추가
//   ✅ 표/토스트/검증 메시지에 unit_value/description 등 필드 한글화 추가
// ----------------------------------------------------------------------------
// 주의
//   • 기존 키는 그대로 유지 (하위 호환성)
//   • 신규 키는 기능 구현에 맞춰 선택적으로 사용 가능
//   • TS/ESM 환경에서 default export 유지
// ============================================================================

export default {
  // ─────────────────────────────────────────────
  // 앱/브랜드
  // ─────────────────────────────────────────────
  app: {
    title: '호텔 어드민',
    subtitle: '호텔 운영 자동화 시스템',
    brand: 'Hotel Admin Suite',
    version: '버전',
  },

  // ─────────────────────────────────────────────
  // 내비게이션 라벨
  //  - router/menu.ts 의 라벨과 의미적으로 일치(문자열만 한글화)
  // ─────────────────────────────────────────────
  nav: {
    dashboard: '대시보드',
    closing: '마감',
    closingBoard: '보드',
    closingCal: '캘린더',
    ota: 'OTA',
    reports: '리포트',
    admin: '관리',
    users: '사용자',
    upload: '업로드',
    audit: '감사로그',
    contracts: '계약서',
    hr: '인사관리',
    settings: '설정',
    docsAdmin: '문서관리',
    // ✅ 신규: 하우스키핑 메뉴 라벨
    housekeeping: '하우스키핑',
  },

  // ─────────────────────────────────────────────
  // 인증/세션
  // ─────────────────────────────────────────────
  auth: {
    needLogin: '로그인이 필요합니다.',
    noPermission: '권한이 없습니다.',
    invalidToken: '인증 토큰이 유효하지 않습니다.',
    expired: '세션이 만료되었습니다. 다시 로그인해주세요.',
    logout: '로그아웃되었습니다.',
    loginTitle: '내부 관리자 로그인',
    email: '이메일',
    password: '비밀번호',
    remember: '로그인 유지',
    submit: '로그인',
    fail: '로그인 실패: 이메일 또는 비밀번호를 확인해주세요.',
  },

  // ─────────────────────────────────────────────
  // 공통 CTA
  // ─────────────────────────────────────────────
  cta: {
    new: '추가',
    save: '저장',
    update: '수정',
    delete: '삭제',
    apply: '적용',
    export: 'CSV 내보내기',
    import: '가져오기',
    refresh: '새로고침',
    close: '닫기',
    load: '불러오기',
    download: '다운로드',
    restore: '복구',
    print: '인쇄',
    back: '뒤로가기',
    confirm: '확인',
    cancel: '취소',
    search: '검색',
    clear: '초기화',
    edit: '편집',
    select: '선택',
    // ✅ 하우스키핑 보드용
    build: '빌드',
    assign: '배정',
  },

  // ─────────────────────────────────────────────
  // 상태/알림
  // ─────────────────────────────────────────────
  state: {
    loading: '불러오는 중…',
    empty: '데이터가 없습니다.',
    error: '오류가 발생했습니다.',
    notFound: '데이터를 찾을 수 없습니다.',
    done: '완료되었습니다.',
    saving: '저장 중…',
    success: '성공',
    fail: '실패',
    pending: '대기 중…',
  },

  // ─────────────────────────────────────────────
  // 표/컬럼 공통 라벨
  // ─────────────────────────────────────────────
  table: {
    total: '합계',
    count: '건수',
    amount: '금액',
    weight: '가중치',
    active: '활성',
    inactive: '비활성',
    createdAt: '생성일',
    updatedAt: '수정일',
    status: '상태',
    date: '일자',
    name: '이름',
    code: '코드',
    // ✅ 기준정보: 객실/유닛
    unitValue: '유닛값',
    description: '설명',
  },

  // ─────────────────────────────────────────────
  // 네트워크/에러 메시지
  // ─────────────────────────────────────────────
  msg: {
    networkError: '네트워크 오류가 발생했습니다.',
    timeout: '요청이 시간 초과되었습니다.',
    unauthorized: '로그인이 만료되었거나 권한이 없습니다.',
    forbidden: '해당 작업에 대한 권한이 없습니다.',
    conflict: '이미 처리되었거나 충돌이 발생했습니다.',
    serverError: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
    validation: '입력값을 확인해주세요.',
    closedDayBlocked: '마감(CLOSED) 일자에는 실행할 수 없습니다.',
    fileRequired: '파일을 선택해주세요.',
    fileTooLarge: '파일 용량이 너무 큽니다.',
    fileType: '파일 형식을 확인해주세요 (CSV/XLSX 권장).',
    unexpected: '예상치 못한 오류가 발생했습니다.',
    success: '정상적으로 처리되었습니다.',
    saveFail: '저장 중 오류가 발생했습니다.',
    retry: '잠시 후 다시 시도해주세요.',
  },

  // ─────────────────────────────────────────────
  // UI 공통
  // ─────────────────────────────────────────────
  ui: {
    confirmTitle: '확인',
    confirmOk: '예',
    confirmCancel: '아니오',
    print: '인쇄',
    back: '뒤로',
    yes: '예',
    no: '아니오',
    next: '다음',
    prev: '이전',
    upload: '파일 업로드',
    loading: '처리 중입니다…',
    placeholder: '입력하세요',
  },

  // ─────────────────────────────────────────────
  // 입력값 검증
  // ─────────────────────────────────────────────
  validation: {
    required: '{field}은(는) 필수 항목입니다.',
    email: '올바른 이메일 주소를 입력해주세요.',
    minLength: '{field}은(는) 최소 {min}자 이상이어야 합니다.',
    maxLength: '{field}은(는) 최대 {max}자까지 가능합니다.',
    number: '{field}은(는) 숫자여야 합니다.',
    date: '{field}의 형식이 잘못되었습니다 (YYYY-MM-DD).',
    mismatch: '{field}의 값이 일치하지 않습니다.',
    range: '{field} 범위를 확인해주세요.',
    pattern: '{field} 형식이 올바르지 않습니다.',
    unique: '{field} 값이 중복되었습니다.',
    fileExt: '허용되지 않는 파일 형식입니다.',
    maxFileCount: '파일은 최대 {max}개까지 업로드할 수 있습니다.',
    // ✅ 추가: 유닛값/코드 검증 문구
    unitValuePositive: '유닛값은 0 이상이어야 합니다.',
    codePattern: '코드는 영문/숫자/언더스코어만 사용할 수 있습니다.',
  },

  // ─────────────────────────────────────────────
  // 토스트/피드백
  // ─────────────────────────────────────────────
  toast: {
    saveSuccess: '저장되었습니다.',
    saveFail: '저장 실패: {why}',
    updateSuccess: '수정되었습니다.',
    deleteSuccess: '삭제되었습니다.',
    deleteFail: '삭제 실패',
    uploadDone: '{count}건 업로드 완료',
    uploadFail: '업로드 실패: {why}',
    restoreOk: '복구 완료',
    restoreFail: '복구 실패',
    applyOk: '적용 완료',
    applyFail: '적용 실패',
    actionCanceled: '작업이 취소되었습니다.',
    // ✅ 하우스키핑 전용
    hkBuildOk: '청소 대상 객실 빌드 완료',
    hkBuildFail: '청소 대상 빌드 실패',
    hkAssignOk: '배정이 완료되었습니다.',
    hkAssignFail: '배정 실패',
  },

  // ─────────────────────────────────────────────
  // Closing (마감)
  // ─────────────────────────────────────────────
  closing: {
    title: 'Closing',
    property: '자산',
    monthLabel: '월 (YYYY-MM)',
    businessDate: '영업일 (YYYY-MM-DD)',
    open: 'OPEN',
    closed: 'CLOSED',
    status: '마감 상태',
    progress: '진행 {done}/{total} ({pct}%)',
    needUploadTitle: '업로드 필요 항목',
    goToBoard: '보드로 이동',
    statusToggleClose: '마감',
    statusToggleReopen: '재오픈',
    toastClosed: '해당 영업일 마감',
    toastReopened: '해당 영업일 재오픈',
    calendarLoadFailed: '캘린더 로드 실패',
    statusChangeFailed: '상태 변경 실패',
    closeConfirm: '영업일을 마감하시겠습니까?',
    reopenConfirm: '영업일을 재오픈하시겠습니까?',
    holiday: '공휴일',
    holidayShort: '휴일',
    holidayBadge: '휴일 · 운영 확인 필요',
  },

  // ─────────────────────────────────────────────
  // Board / Uploads (업로드)
  // ─────────────────────────────────────────────
  board: {
    title: 'Closing Board',
    noteClosed: '선택한 영업일은 CLOSED 상태입니다. 업로드가 차단됩니다.',
    dataset: {
      rooms_status: '객실상태',
      sales_front: '프론트 매출',
      fnb_sales: 'F&B 매출',
      fnb_items: 'F&B 상품별',
      fnb_tenders: 'F&B 결제수단별',
      expenses: '지출내역',
      pay_settlement: '입금내역',
      reservations: '예약내역',
    },
    headers: {
      rooms_status: 'room_no,status_code,is_dirty,hk_note',
      sales_front: 'date,folio_no,amount,currency,note',
      fnb_sales: '(결제수단별 + 상품별)',
      expenses: 'date,category,amount,currency,note',
      pay_settlement: 'date,method,amount,currency,note',
    },
    partsLabel: '필수 파트',
    partitionPlaceholder: 'Partition 입력/선택',
    upload: '업로드',
    template: '템플릿',
    history: '이력',
    noHistory: '이력이 없습니다.',
    restoreConfirm: 'v{ver} 으로 되돌리고 새 버전을 생성할까요?',
    restoreOk: '복구 완료 → v{ver}',
    restoreFail: '복구 실패',
    downloadFail: '다운로드 실패: {why}',
    fnbPairHint: '두 파일 모두 선택 후 업로드를 눌러주세요.',
    fnbBothRequired: '결제수단별/상품별 파일을 모두 선택해주세요.',
    closedUploadBlocked: '마감(CLOSED) 일자는 업로드할 수 없습니다.',
    partitionRequired: 'Partition을 선택/입력하세요.',
    uploadSuccess: '업로드 완료',
    templateHint: 'CSV 템플릿 예시를 다운로드하여 형식을 맞춰주세요.',
    version: '버전',
    uploadedAt: '업로드 일시',
    uploadedBy: '업로드 사용자',
  },

  // ─────────────────────────────────────────────
  // Reports
  // ─────────────────────────────────────────────
  reports: {
    salesTags: '태그별 매출',
    range: { today: '오늘', thisMonth: '이번 달', prevMonth: '지난 달' },
    rooms: '객실 매출',
    fnb: 'F&B 매출',
    from: '시작일 (YYYY-MM-DD)',
    to: '종료일 (YYYY-MM-DD)',
    export: '리포트 내보내기',
    empty: '리포트 데이터가 없습니다.',
    filters: '필터',
    resetFilters: '필터 초기화',
  },

  // ─────────────────────────────────────────────
  // Dashboard
  // ─────────────────────────────────────────────
  dashboard: {
    title: '대시보드',
    rooms: '객실',
    front: '프런트 매출',
    fnb: 'F&B 매출',
    expenses: '경비',
    settlement: '정산',
    stockSummary: '재고 요약(입/출/재고)',
    attendanceSummary: '근태 요약(필요/출근/부족)',
    today: '오늘',
    openProgress: 'OPEN · {done}/{total}',
    closedDone: '마감 완료',
    kpiUpdatedAt: 'KPI 갱신: {time}',
  },

  // ─────────────────────────────────────────────
  // OTA
  // ─────────────────────────────────────────────
  ota: {
    title: 'OTA',
    tabs: { sales: '판매', aliases: '채널 동의어', fees: '수수료' },
    exportCsv: 'CSV 내보내기',
    importCsv: 'CSV 가져오기',
    aliasPlaceholder: '별칭을 입력하세요.',
    channel: '채널',
    commission: '수수료',
    effectiveDate: '적용일',
  },

  // ─────────────────────────────────────────────
  // Keywords
  // ─────────────────────────────────────────────
  kwd: {
    title: '키워드',
    manage: '관리',
    test: '분석 테스트',
    group: '그룹',
    search: '검색 (k / v)',
    active: '활성',
    new: '신규',
    edit: '수정',
    deleteConfirm: '정말 삭제하시겠습니까?',
    importCsv: 'CSV 가져오기',
    exportCsv: 'CSV 내보내기',
    saved: '저장되었습니다.',
    loadFailed: '로드 실패',
    saveFailed: '저장 실패',
    deleteFailed: '삭제 실패',
    importDone: '완료: {ok}건, 실패: {fail}건',
    key: '키',
    value: '값',
  },

  // ─────────────────────────────────────────────
  // Master (운영 기준정보) — Room Types / HK Unit Rules
  // ─────────────────────────────────────────────
  master: {
    roomType: {
      title: '객실 타입',
      code: '타입 코드',
      name: '타입명',
      unitValue: '기본 유닛값',
      description: '설명',
      active: '활성',
      toast: {
        saved: '객실 타입이 저장되었습니다.',
        deleted: '객실 타입이 삭제되었습니다.',
      },
    },
    hkUnitRule: {
      title: '하우스키핑 단위규칙',
      code: '조건 코드',
      name: '설명',
      unitValue: '유닛값',
      active: '활성',
      toast: {
        saved: '단위규칙이 저장되었습니다.',
        deleted: '단위규칙이 삭제되었습니다.',
      },
    },
  },

  // ─────────────────────────────────────────────
  // Housekeeping Board (업무 보드)
  // ─────────────────────────────────────────────
  hk: {
    title: '하우스키핑 보드',
    tabs: {
      today: '오늘 현황',
      history: '정비 이력',
      settings: '설정',
    },
    buildConfirm: '오늘 청소 대상 객실을 빌드하시겠습니까?',
    buildRunning: '빌드 중입니다…',
    assignHint: '팀장이 담당 직원을 선택하여 객실을 배정하세요.',
    stats: {
      totalUnits: '총 유닛',
      tasks: '작업 수',
      completed: '완료',
      byStaff: '직원별 유닛',
    },
    staff: {
      title: '직원',
      noStaff: '소속 팀원이 없습니다.',
      selectStaff: '담당 직원 선택',
    },
    task: {
      title: '작업',
      roomNo: '객실',
      memo: '메모',
      units: '유닛',
      status: {
        pending: '대기',
        done: '완료',
      },
    },
    error: {
      statsFailed: '통계 로드에 실패했습니다.',
      buildFailed: '청소 대상 빌드에 실패했습니다.',
      assignFailed: '배정에 실패했습니다.',
    },
  },
}
