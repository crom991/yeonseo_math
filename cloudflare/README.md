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
- `SESSION_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## 최초 배포 순서

1. `npx wrangler d1 create yeonseo-math`로 D1을 만든다.
2. 출력된 `database_id`를 `wrangler.jsonc`의 자리표시자와 교체한다.
3. `npm run db:remote`로 마이그레이션을 적용한다.
4. 네 Secret을 `npx wrangler secret put <NAME>`으로 등록한다.
5. `npm run deploy`로 배포한다.
6. 공개 주소에서 학습 저장, 느낌 저장, Telegram 실제 수신, 부모 PIN 로그인·로그아웃을 각각 확인한다.
