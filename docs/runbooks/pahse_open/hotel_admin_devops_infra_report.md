# 📄 Hotel Admin — DevOps/Infra 완료 보고 (2025-10-04)

## 1️⃣ 환경 요약
| 구분 | 위치 | 포트 | 역할 |
|------|------|------|------|
| 운영(NAS) | 127.0.0.1:8000 → 80(Nginx) | 상시 서비스 |
| 개발(NAS 내부) | 0.0.0.0:8001 | 개발·테스트 전용 |
| 프런트 | Vite(5173) | Dev 모드 (Proxy → 8001) |

## 2️⃣ 운영 구성
- **Nginx 설정:** `/etc/nginx/conf.d/hotel-admin.conf`
  - `root /var/www/hotel-admin;` (정적 SPA)
  - `/api/ → 127.0.0.1:8000` 프록시
  - gzip + Cache-Control 헤더 적용
  - 헬스체크 `/usr/local/bin/check-nginx.sh` 로 자동 수행
- **Uvicorn(운영):**
  - 가상환경: `/volume1/web/hotel-system/venv39_py39`
  - 실행 스크립트: `/usr/local/bin/start-hotel.sh`
  - 자동기동: DSM 작업 스케줄러
    - **HOTEL_SERVER_BACKEND** (부팅 시)
    - **HOTEL_SERVER_FRONT** (부팅 시 Nginx reload)
    - **Uvicorn Watchdog** (5분마다 상태 확인)
  - 로그: `/var/log/uvicorn.log`, `/var/log/uvicorn_watch.log`

## 3️⃣ 개발 구성
- **백엔드(개발):**
  ```bash
  cd /volume1/web/hotel-system/backend
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
  ```
- **프런트:**
  - `.env`
    ```env
    VITE_DEV_PROXY_TARGET=http://127.0.0.1:8001
    ```
  - 실행: `npm run dev`
- **주의:** 8001은 개발 전용, 운영은 8000 + 80만 사용.

## 4️⃣ 헬스체크/자동복구
- **헬스체크 스크립트**
  - `/usr/local/bin/check-nginx.sh`
  - `/usr/local/bin/check-uvicorn.sh`
- **자동복구(Watchdog)**
  - `/usr/local/bin/watch-uvicorn.sh`
  - 다운 감지 시 `start-hotel.sh` 자동 재기동

## 5️⃣ 현 상태 (2025-10-04 기준)
✅ Nginx `/api/openapi.json` 200  
✅ Uvicorn(8000) 정상 기동  
✅ Dev(8001) 별도 사용 가능  
✅ 자동기동 + 헬스체크 + 와치독 설정 완료

## 🔜 향후 계획
- 운영 서버를 클라우드로 이전 (AWS 또는 GCP 예정)
- NAS는 개발 전용 환경으로 유지
- SSL(443) 및 Cloudflare Proxy 전환은 2차 단계에서 진행
