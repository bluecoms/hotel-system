-- ============================================================================
-- File: seed_master_titles.sql
-- Version: 2025.11-05 · v1.0 (SSOT 직책코드 + 한글명 일원화)
-- Purpose: Hotel Admin — Master Titles 초기 Seed
-- ============================================================================

DELETE FROM master_titles;

INSERT INTO master_titles (code, name, is_active, order_no) VALUES
 ('CEO', '총지배인', 1, 1),
 ('AD',  '부지배인', 1, 2),
 ('TM',  '팀장', 1, 3),
 ('HK',  '하우스키핑팀장', 1, 4),
 ('FB',  '식음팀장', 1, 5),
 ('EN',  '시설팀장', 1, 6),
 ('MK',  '마케팅팀장', 1, 7),
 ('ST',  '스태프', 1, 8),
 ('IN',  '인턴', 1, 9);

VACUUM;
