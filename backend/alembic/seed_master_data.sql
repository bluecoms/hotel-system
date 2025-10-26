-- ============================================================================
-- File: seed_master_data.sql
-- Version: 2025.11-04 · v1.0 (Hotel Admin — Master Departments SSOT)
-- Purpose: 7개 부서코드(AD, FR, HK, FB, EN, MK, MG) 초기 Seed
-- ============================================================================

DELETE FROM departments;

INSERT INTO departments (property_code, dept_code, dept_name, order_no, is_active) VALUES
 ('MOP', 'MG', '경영지원', 1, 1),
 ('MOP', 'AD', '총무부', 2, 1),
 ('MOP', 'FR', '프런트', 3, 1),
 ('MOP', 'HK', '하우스키핑', 4, 1),
 ('MOP', 'FB', '식음팀', 5, 1),
 ('MOP', 'EN', '시설팀', 6, 1),
 ('MOP', 'MK', '마케팅팀', 7, 1);

VACUUM;
