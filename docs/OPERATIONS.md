# 운영 및 배포

## 현재 운영 주소

- Cloudflare: <https://yeonseo-math.exambreaker-dev.workers.dev>
- Streamlit: <https://yeonseo-math.streamlit.app>
- GitHub: <https://github.com/crom991/yeonseo_math>
- Streamlit 배포 기준: `main` 브랜치의 `app.py`
- Cloudflare 배포 기준: `cloudflare/wrangler.jsonc`와 `cloudflare/src/index.js`
- 최초 공개 배포 확인: 2026-10-04

Cloudflare 무료 배포판은 2026-10-08에 Worker와 D1로 공개 배포했다. `SESSION_SECRET`은 등록했으며, 기존 Streamlit의 `PARENT_PIN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 Cloudflare Secret으로 옮기기 전까지 부모 인증과 Telegram 전송은 비활성 상태다. 기존 Streamlit 주소는 전환 확인 기간 동안 유지한다.

현재 `PARENT_PIN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`는 Streamlit Secrets에 등록했다. 따라서 부모 화면 인증과 학습 결과 Telegram 전송을 사용할 수 있다. Supabase Secret은 아직 등록하지 않아 학습 기록은 Streamlit 서버 재시작 후 사라질 수 있다. 모든 Secret 값은 문서와 Git에 기록하지 않는다.

## 구성

- `app.py`: 아이용 10분 학습과 결과·Telegram 전송
- `arithmetic.py`: 17단계 문제 생성, 답 판정, 세션 내 난이도 조절
- `curriculum.py`: 영역 해제, 자동 배정, 부모 지정 규칙
- `storage.py`: 로컬 JSON/Supabase 저장
- `notifications.py`: Telegram 메시지 작성·전송
- `pages/1_부모_학습기록.py`: 날짜별 기록과 부모 설정
- `docs/SUPABASE_SETUP.sql`: 운영 저장소 표 생성문
- `cloudflare/public`: Cloudflare 정적 학습·부모 화면
- `cloudflare/src/index.js`: Worker API, D1 저장, 부모 인증, Telegram 전송
- `cloudflare/migrations`: D1 스키마

## Streamlit Secrets

운영 앱의 설정 화면에 아래 이름을 등록한다. 값은 문서나 Git에 저장하지 않는다.

```toml
TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID = "..."
PARENT_PIN = "..."
SUPABASE_URL = "..."
SUPABASE_SERVICE_ROLE_KEY = "..."
```

- Telegram 두 값은 기존 알림 수신처와 같은 값을 재사용한다.
- `PARENT_PIN`은 부모 화면에서만 사용하는 별도 번호로 정한다.
- Supabase 두 값이 모두 없으면 앱은 서버 로컬 파일로 동작한다. 이 방식은 Streamlit Cloud 재시작·재배포 때 기록이 사라질 수 있다.

## Supabase 준비

1. 새 Supabase 프로젝트를 만든다.
2. SQL Editor에서 `docs/SUPABASE_SETUP.sql`을 실행한다.
3. 프로젝트 URL과 service role key를 Streamlit Secrets에 등록한다.
4. 새 연습을 한 번 마친 뒤 부모 화면에서 기록이 보이는지 확인한다.

service role key는 공개 클라이언트에 노출하면 안 된다. 이 앱에서는 Streamlit 서버에서만 사용하며 저장소 표에는 RLS를 활성화한다.

## 배포 절차

1. GitHub `crom991` 계정의 전용 저장소에 `main` 브랜치를 올린다.
2. Streamlit Community Cloud에서 저장소, `main`, `app.py`를 선택한다.
3. 위 5개 Secret을 등록한다.
4. 앱을 재부팅하고 모바일 화면을 확인한다.
5. 1회 학습 후 느낌 저장, Telegram 전송, 부모 기록 조회를 차례로 확인한다.
6. 배포 URL과 확인 시각을 `PROJECT_LOG.md`와 Notion에 남긴다.

## 변경 전 검증

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py app_config.py arithmetic.py curriculum.py notifications.py storage.py pages tests
git diff --check
```

Cloudflare 배포판은 다음 검증을 추가한다.

```powershell
cd cloudflare
npm test
npm run check
npx wrangler deploy --dry-run
```

## Cloudflare 최초 배포

1. Cloudflare 계정에서 D1 `yeonseo-math`를 생성하고 반환된 ID를 `cloudflare/wrangler.jsonc`에 반영한다.
2. `cloudflare/migrations/0001_initial.sql`을 원격 D1에 적용한다.
3. `PARENT_PIN`, `SESSION_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 Wrangler Secret으로 등록한다.
4. Worker와 정적 자산을 배포한다.
5. 공개 주소에서 아이 학습 1회와 느낌 자동 저장을 확인한다.
6. 부모 PIN 인증, 기록 표시, 설정 저장, 로그아웃 재잠금을 확인한다.
7. Telegram 전송은 실제 수신까지 확인한다.

Secret 값은 로컬 파일·Git·문서에 남기지 않는다. `SESSION_SECRET`은 부모 인증 쿠키 서명용으로 충분히 긴 임의 문자열을 사용한다.

## 장애 확인

- Telegram 버튼이 비활성화되면 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 두 Secret이 모두 있는지 확인한다.
- Telegram 전송 실패 시 앱 로그에서 네트워크 오류를 확인하고 기존 봇과 채팅방이 유효한지 점검한다.
- 부모 화면이 잠긴 상태면 `PARENT_PIN` 등록 여부를 확인한다.
- 기록이 재시작 뒤 사라지면 Supabase 두 Secret과 `math_sessions`, `math_settings` 표를 확인한다.
- 문제가 생성되지 않으면 자동 테스트를 실행하고 현재 강제 단계가 선택 영역에 속하는지 확인한다.

## 완료 상태 판정

- 코드 저장: 로컬 파일과 Git 커밋 확인
- 배포 완료: Streamlit 운영 URL과 최신 커밋 일치 확인
- Telegram 완료: 실제 수신 메시지 확인
- 기록 저장 완료: 학습 후 부모 화면 및 Supabase 표에서 동일 기록 확인

각 항목은 서로 대신할 수 없으므로 별도로 확인하고 기록한다.

Cloudflare 전환도 코드 저장, D1 생성·마이그레이션, Secret 등록, Worker 배포, 공개 화면 검증, Telegram 실제 수신을 서로 분리해 판정한다.
