# Cloudflare 배포판

기존 Streamlit 앱의 학습 흐름을 Cloudflare 정적 자산, Workers, D1으로 옮긴 버전이다. Python 서버를 깨우는 과정 없이 정적 화면을 즉시 제공하고, 기록·부모 인증·Telegram 전송만 Worker API가 처리한다.

## 구성

- `public/`: 아이용 학습 화면과 부모용 화면
- `src/index.js`: Worker API, D1 저장, 부모 인증, Telegram 전송
- `migrations/`: D1 표와 인덱스
- `tests/`: 문제 생성·난이도·인증·메시지 테스트
- `wrangler.jsonc`: Worker, 정적 자산, D1 연결 설정

## 로컬 확인

```powershell
cd cloudflare
npm install
npm test
npm run check
npm run db:local
npm run dev
```

## 운영 Secret

실제 값은 파일이나 Git에 기록하지 않고 Wrangler Secret으로만 등록한다.

- `PARENT_PIN`
- `HAEUN_PARENT_PIN`
- `SESSION_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## 멀티 프로필 데이터 규칙

- 아이 화면은 로그인 없이 `연서 / 하은`을 선택한다.
- 학습 기록과 학습 설정은 `profile_id`로 분리한다.
- 기존 `profile_id` 없는 D1 기록은 `0002_multi_profile.sql` 적용 때 `yeonseo`로 보존한다.
- `PARENT_PIN`은 연서, `HAEUN_PARENT_PIN`은 하은 부모 화면에 연결한다.
- 부모 PIN 인증 뒤에는 해당 PIN에 연결된 아이의 기록과 설정만 표시한다.
- 운영 반영은 코드 배포보다 먼저 `npm run db:remote`로 최신 마이그레이션을 적용한다.

## 최초 배포 순서

1. `npx wrangler d1 create yeonseo-math`로 D1을 만든다.
2. 출력된 `database_id`를 `wrangler.jsonc`의 자리표시자와 교체한다.
3. `npm run db:remote`로 마이그레이션을 적용한다.
4. 다섯 Secret을 `npx wrangler secret put <NAME>`으로 등록한다.
5. `npm run deploy`로 배포한다.
6. 공개 주소에서 학습 저장, 느낌 저장, Telegram 실제 수신, 부모 PIN 로그인·로그아웃을 각각 확인한다.
