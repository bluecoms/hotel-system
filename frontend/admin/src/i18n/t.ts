// src/i18n/t.ts (아주 얇은 임시 레이어)
const ko: Record<string,string> = {
  'app.title': 'Mokpo Ocean Hotel 업무시스템',
  'dashboard.title': '대시보드',
  'closing.title': '일마감',
  'users.title': '사용자',
  'btn.search': '검색',
  'btn.upload': '업로드',
};
export function t(key: string) { return ko[key] ?? key; }
