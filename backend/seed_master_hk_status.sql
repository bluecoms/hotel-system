-- ============================================================================
-- File: seed_master_hk_status.sql
-- Purpose: 하우스키핑 상태 기준정보 초기 데이터 (Hotel Admin)
-- ============================================================================

INSERT OR IGNORE INTO master_hk_status (code, name, is_active, created_at) VALUES
('VC',  '청소 완료',            1, datetime('now')),
('VD',  '청소 필요',            1, datetime('now')),
('OC',  '투숙 중 청소 완료',     1, datetime('now')),
('OD',  '투숙 중 청소 필요',     1, datetime('now')),
('OOO', '수리 중 (Out of Order)', 1, datetime('now')),
('OOS', '서비스 제외 (Out of Service)', 1, datetime('now')),
('INS', '점검 중 (Inspection)',  1, datetime('now')),
('BLK', '블록 (Blocked)',        1, datetime('now')),
('STF', '직원용 (Staff Use)',    1, datetime('now')),
('DLQ', '대청소 예정',           1, datetime('now'));
