# 오늘의 연산 10분

두 명의 초등학생이 모바일에서 하루 약 10분씩 기초 연산을 연습하는 웹앱입니다. 로그인 없이 `연서 / 하은` 프로필을 선택하며, 각자의 기록과 난이도 설정은 서로 섞이지 않습니다.

## 공개 서비스

- Cloudflare: <https://yeonseo-math.exambreaker-dev.workers.dev>
- 웹앱: <https://yeonseo-math.streamlit.app>
- GitHub: <https://github.com/crom991/yeonseo_math>

Cloudflare 무료 배포판은 `cloudflare/`에 구축했다. 정적 화면은 즉시 제공하고, Worker API와 D1이 기록·부모 인증·Telegram 전송을 담당한다. 기존 Streamlit 주소는 전환 확인 기간 동안 함께 유지한다.

## 핵심 기능

- 두 자리 수 덧셈에서 시작해 뺄셈·곱셈·나눗셈·소수·분수로 확장하는 17단계
- 로그인 없이 연서·하은 프로필을 선택하고 기록·진도·설정을 아이별로 분리
- 최근 풀이와 아이의 `쉬웠어요 / 딱 좋았어요 / 어려웠어요` 응답을 함께 반영하는 난이도 조절
- 한 영역을 충분히 연습하면 다음 영역을 열고, 열린 영역 중 덜 연습한 영역을 우선 배정
- 부모 PIN으로 보호된 날짜별 기록·정확도 추이·학습 설정 화면
- 부모가 특정 영역과 시작 단계를 강제로 지정하는 기능
- 결과 화면의 `아빠에게 학습 결과 보내기` 버튼과 중복 전송 방지
- 로컬 JSON 저장 및 운영용 Supabase 저장소 지원

## 로컬 실행

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

로컬에서 부모 화면을 시험하려면 연서용 `PARENT_PIN`과 하은용 `HAEUN_PARENT_PIN` 환경 변수를 설정합니다. 비밀값은 코드나 문서에 기록하지 않습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py app_config.py arithmetic.py curriculum.py notifications.py profiles.py storage.py pages tests
```

Cloudflare 배포판은 다음처럼 확인한다.

```powershell
cd cloudflare
npm install
npm test
npm run check
```

## 운영 설정

Streamlit Secrets에 다음 이름을 등록합니다. 실제 값은 Git에 올리지 않습니다.

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `PARENT_PIN`
- `HAEUN_PARENT_PIN`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

형식은 [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example), 온라인 저장소 표는 [docs/SUPABASE_SETUP.sql](docs/SUPABASE_SETUP.sql)을 참고합니다.

## 문서

- [제품·학습 설계](docs/PRODUCT_SPEC.md)
- [작업 진행 기록](docs/PROJECT_LOG.md)
- [운영 및 배포](docs/OPERATIONS.md)
- [Cloudflare 배포판](cloudflare/README.md)
