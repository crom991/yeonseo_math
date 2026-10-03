# 오늘의 연산 10분

초등학교 5학년 학습자가 모바일에서 부담 없이 기초 연산을 연습하도록 만든 Streamlit 웹앱입니다. 한 화면에 한 문제만 보여 주며, 10분이 지나면 푼 문제 수·정답 수·정확도·걸린 시간을 정리합니다.

## 핵심 기능

- 두 자리 수 덧셈부터 시작하는 6단계 문제
- 최근 풀이 결과에 따라 한 단계씩 오르내리는 난이도
- 모바일에 맞춘 큰 문제·답 입력·버튼
- 10분 자동 종료와 중도 종료
- 세션 결과와 최근 오답 최대 5개 확인
- 이름, 연락처 등 개인정보를 수집하지 않는 세션 전용 구조

## 로컬 실행

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py arithmetic.py tests
```

## 문서

- [제품·학습 설계](docs/PRODUCT_SPEC.md)
- [작업 진행 기록](docs/PROJECT_LOG.md)
- [운영 및 배포](docs/OPERATIONS.md)
