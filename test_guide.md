프론트엔드 + 백엔드 테스트 계획                                                                                                                                                                         
  1단계: 백엔드 테스트 (5분)                                                                            
  1.1 의존성 설치 & 서버 실행                                                                        
  
  cd C:\workspace\insight-stream-main\backend
  pip install -r requirements.txt
  python main.py

  ✅ 확인사항:
  - 콘솔에 🚀 Insight Stream API v1.0.0 starting... 표시
  - Using OpenAI provider 메시지 확인
  - 에러 없이 서버 실행됨

  1.2 Health Check

  새 터미널 열고:
  curl http://localhost:8000/

  예상 결과:
  {
    "status": "ok",
    "message": "Insight Stream API is running",
    "version": "1.0.0"
  }

  ---
  2단계: 프론트엔드 테스트 (3분)

  2.1 프론트엔드 실행

  새 터미널 열고:
  cd C:\workspace\insight-stream-main
  npm install  # 처음이면
  npm run dev

  ✅ 확인사항:
  - 브라우저에서 http://localhost:8080 자동 열림
  - UI가 정상적으로 표시됨

  ---
  3단계: 통합 테스트 (실제 영상 요약)

  3.1 테스트용 YouTube URL

  아래 URL 중 하나 사용 (한국어 자막 있음):
  https://www.youtube.com/watch?v=XfCBSQ1ZF-w
  https://www.youtube.com/watch?v=dQw4w9WgXcQ

  3.2 테스트 절차

  1. 프론트엔드에서 YouTube URL 입력
  2. "요약 생성" 버튼 클릭
  3. 기대 결과:
    - ✅ 자막 패널에 자막 표시
    - ✅ 간단 요약 (2-3문장) 표시
    - ✅ 상세 요약 (마크다운 형식) 표시

  3.3 백엔드 로그 확인

  백엔드 터미널에서:
  📥 Received request for URL: ...
  🆔 Extracted video ID: ...
  ✅ Transcript fetched (N entries)
  🤖 Generating AI summaries with OPENAI...
  ✅ AI summaries generated successfully
  ✅ Successfully processed video ...

  ---
  4단계: 에러 테스트 (선택사항)

  4.1 잘못된 URL 테스트

  https://www.google.com
  예상: "유효하지 않은 YouTube URL입니다" 에러

  4.2 자막 없는 영상 테스트

  자막 없는 영상 URL 입력
  예상: "자막이 제공되지 않습니다" 에러

  ---
  체크리스트

  - 백엔드 서버 정상 실행 (port 8000)
  - Health check 성공
  - 프론트엔드 실행 (port 8080)
  - YouTube URL 입력 가능
  - 자막 추출 성공
  - AI 요약 생성 성공 (OpenAI 사용)
  - 에러 처리 동작 확인

  ---
  문제 발생 시

  CORS 에러

  → 백엔드 .env에서 FRONTEND_URL=http://localhost:8080 확인

  OpenAI 에러

  → API 키 확인 및 크레딧 잔액 확인

  포트 충돌

  → 이미 사용 중인 포트면 종료 후 재시작