# 운영 및 배포

## 구성

- 실행 파일: `app.py`
- 문제 생성·난이도·결과 계산: `arithmetic.py`
- 의존성: `requirements.txt`
- Streamlit 설정: `.streamlit/config.toml`
- 자동 검증: `tests/test_arithmetic.py`

## 배포 절차

1. GitHub의 `crom991` 계정에 전용 저장소를 만든다.
2. 이 프로젝트를 `main` 브랜치로 올린다.
3. Streamlit Community Cloud에서 저장소, `main`, `app.py`를 선택해 배포한다.
4. 모바일 폭에서 시작 화면, 문제 입력, 정답·오답 처리, 중도 종료, 결과 화면을 확인한다.

## 변경 전 확인

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py arithmetic.py tests
git diff --check
```

## 개인정보 원칙

- 코드와 문서에 아이 이름, 이메일, 학교명 등 개인정보를 기록하지 않는다.
- 비밀값이 생길 경우 값이 아닌 Secret 이름만 문서화한다.
- 풀이 이력 저장 기능은 별도 동의와 보호 방식을 정한 뒤 추가한다.

## 장애 확인

- 앱이 열리지 않으면 Streamlit 배포 로그와 GitHub 최신 커밋 일치를 확인한다.
- 문제가 생성되지 않으면 `tests/test_arithmetic.py`를 실행한다.
- 세션이 예기치 않게 초기화되면 Streamlit 재시작 여부를 확인한다.
