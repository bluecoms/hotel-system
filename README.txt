############################################
# [1] 수동 기동(백엔드/프런트)
############################################
# 프로세스 정리(충돌 방지)
pkill -f "uvicorn .*app.main:app" || true
pkill -f "vite" || true

# BE (Uvicorn 8000)
cd /volume1/web/hotel-system/backend
source ../venv39_py39/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# FE (Vite 5173)
cd /volume1/web/hotel-system/frontend/admin
npm run dev:all
# 브라우저: http://192.168.0.6:5173

############################################
# [2] 프런트 .env (개발용)
############################################
# 파일: /volume1/web/hotel-system/frontend/admin/.env

VITE_API_BASE_URL=
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
VITE_HTTPS=false
VITE_ALLOWED_HOSTS=192.168.0.6
VITE_ADMIN_TOKEN=<관리자 access_token 또는 내부 토큰>
```
############################################
# [3] SQLite 빠른 접근
############################################
sqlite3 /volume1/web/hotel-system/backend/hotel.db
# 예시:
# .tables
# .schema closing_days
# SELECT * FROM closing_days LIMIT 10;
# .quit

############################################
# [4] Git & SSH 메모 (원격/키/명령 TOP10)
############################################
# Remote: origin (SSH)
# URL   : git@github.com:bluecoms/hotel-system.git
# Branch: master
# Repo  : https://github.com/bluecoms/hotel-system

# SSH 키(이미 등록됨)
# 개인키: ~/.ssh/id_ed25519   # 절대 공유 금지
# 공개키: ~/.ssh/id_ed25519.pub
# Fingerprint: SHA256:/i1gobgkIIa6YR5UstKUdFI5V6olA2FzyKQGP12El2Q

# 인증 테스트
ssh -i ~/.ssh/id_ed25519 -T git@github.com
# 기대: Hi bluecoms! You've successfully authenticated...

# TOP10
git status
git diff
git add -A
git commit -m "msg"
git push
git pull
git branch --show-current
git remote -v
git checkout -b feature/x
git push -u origin feature/x

############################################
# [5] 리비전 alembic 명령어
############################################
# 현재 DB가 가리키는 리비전(실제 적용 상태)
alembic current

# 최신 HEAD(들) — 브랜치가 갈라졌으면 여러 개 나올 수 있음
alembic heads

# 히스토리를 위에서 아래로 보기
alembic history

# 최근 10개만 보기
alembic history -r-10:
