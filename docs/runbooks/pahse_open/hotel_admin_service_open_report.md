# ✅ \[완료 보고\] Hotel Admin 서비스 오픈 (HTTP/80)

## 1) 적용 내역

-   **프런트 배포 경로:** `/var/www/hotel-admin` (SPA, try_files 구성)
-   **도메인:** `hotel.mokpooceanhotel.co.kr`
-   **Nginx vhost:** `/etc/nginx/conf.d/hotel-admin.conf`
    -   `/` 정적 서빙
    -   `/api/` → `127.0.0.1:8000` (Uvicorn 프록시)
    -   `map $http_upgrade $connection_upgrade` 포함(WebSocket 대비)
-   **백엔드(Uvicorn):** `127.0.0.1:8000`에서 실행 확인
-   **부팅 자동 기동:** Synology 작업 스케줄러 적용
    -   `HOTEL_SERVER_BACKEND` (Uvicorn)
    -   `HOTEL_SERVER_FRONT` (Nginx 재적용/헬스체크)
    -   두 작업 모두 활성화 & 부팅 시 실행

------------------------------------------------------------------------

## 2) 검증 결과 (로컬 루프백)

``` bash
curl -I -H "Host: hotel.mokpooceanhotel.co.kr" http://127.0.0.1/ 
→ 200 OK

curl -I -H "Host: hotel.mokpooceanhotel.co.kr" http://127.0.0.1/api/openapi.json 
→ 200 OK

curl -s -H "Host: hotel.mokpooceanhotel.co.kr" -H "X-Internal-Token: prod-admin-token" http://127.0.0.1/api/me 
→ 200 OK
(토큰 미포함 시 401 정상 동작)
```

------------------------------------------------------------------------

## 3) 로그 경로

-   **Nginx**
    -   기본: `/var/log/nginx/error.log` (동작 확인용 메시지 존재)
    -   사이트 전용: `/var/log/nginx/hotel.access.log`,
        `/var/log/nginx/hotel.error.log`
-   **Uvicorn:** `~/uvicorn.log` (재기동부터 기록)

📌 참고: `error.log` 내 `/var/services/web/ 403/404`,
`.env/manager/html` 스캔 요청은 외부 크롤러 트래픽이며 서비스와 무관.

------------------------------------------------------------------------

## 4) 운영 명령 (요약)

``` bash
# Nginx 테스트/재적용
sudo nginx -t
sudo /usr/sbin/nginx -s reload   # 또는 service/systemctl 환경에 맞게

# Uvicorn 상태 확인/재기동
ps -ef | grep -v grep | grep "uvicorn app.main:app"
pkill -f "uvicorn app.main:app"
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >"$HOME/uvicorn.log" 2>&1 &
```

------------------------------------------------------------------------

## 5) 완료 기준(AC)

-   대시보드 접속(HTTP/80) 노출 ✅
-   `/api/openapi.json` 200 ✅
-   `/api/me` 토큰 포함 200 / 미포함 401 ✅
-   부팅 후 자동 기동(백/프론트) 설정 완료 ✅

------------------------------------------------------------------------

## 6) 후속(선택)

-   HTTPS(LE 또는 Cloudflare) 적용
-   `robots.txt`, `favicon.ico` 추가 (404 감소)
-   logrotate 설정 (nginx, uvicorn)
