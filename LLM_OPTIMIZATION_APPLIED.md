# LLM 입출력 최적화 완료 보고서

## 적용 날짜
2026-01-25

## 변경 사항 요약

### 1. 스크립트 입력 제한 확장 ✅
- **위치**: `backend/app/core/config.py` (line 51)
- **변경**: `TRANSCRIPT_LIMIT_DETAIL: int = 12000` → `50000`
- **효과**: 긴 영상(30분 이상)의 전체 스크립트가 LLM에 전달됨

### 2. Gemini 출력 토큰 증가 ✅
- **위치**: `backend/app/core/config.py` (line 40)
- **변경**: `GEMINI_MAX_TOKENS_DETAIL: int = 2000` → `4000`
- **효과**: 더 긴 상세 요약 생성 가능

### 3. OpenAI 출력 토큰 증가 ✅
- **위치**: `backend/app/core/config.py` (line 47)
- **변경**: `OPENAI_MAX_TOKENS_DETAIL: int = 2000` → `4000`
- **효과**: 더 긴 상세 요약 생성 가능

### 4. .env 파일 동기화 ✅
- **위치**: `backend/.env`
- **변경**: 위의 3가지 설정을 .env 파일에도 적용
- **효과**: 환경변수가 코드 기본값과 일치

### 5. 프롬프트 표시 개선 ✅
- **위치**: `backend/app/api/endpoints.py` (line 199-209)
- **변경**: `remove_script_section()` 함수 추가
- **효과**: "프롬프트 수정" 메뉴에서 [TARGET SCRIPT] 부분이 보이지 않음

## 변경 파일 목록
1. `backend/app/core/config.py` - 기본 설정값 변경
2. `backend/.env` - 환경변수 값 변경
3. `backend/app/api/endpoints.py` - 프롬프트 표시 로직 추가

## 재부팅 후 확인 사항

### 백엔드 서버 시작
```bash
cd C:\workspace\insight-stream-main\backend
.\venv\Scripts\activate
python main.py
```

서버가 `http://0.0.0.0:8000`에서 시작되는지 확인

### 변경사항 확인 방법

1. **스크립트 길이 확인**:
   - 30분 이상의 긴 영상으로 테스트
   - 로그에서 `detail_transcript` 길이 확인
   - 예상: 최대 50,000자까지 처리

2. **출력 토큰 확인**:
   - 상세 요약 길이가 이전보다 길어졌는지 확인
   - "(Summarized from Youtube)" 문구가 끝에 나오는지 확인

3. **프롬프트 표시 확인**:
   - "프롬프트 수정" 버튼 클릭
   - Overview/Detail 프롬프트에 [TARGET SCRIPT] 부분이 **없는지** 확인
   - 프롬프트가 깔끔하게 보이는지 확인

## 예상 효과

### 긍정적 효과
- ✅ 긴 영상도 전체 내용을 기반으로 요약
- ✅ 더 상세하고 구조화된 요약 생성
- ✅ 화자별/주제별 요약이 더 풍부
- ✅ 프롬프트 편집 UI가 더 깔끔

### 비용 증가
- ⚠️ 입력 토큰: 약 4배 증가 (12K → 50K 문자)
- ⚠️ 출력 토큰: 2배 증가 (2K → 4K 토큰)
- ⚠️ 총 API 비용: 약 2.5-3배 증가 예상

### 성능 영향
- ⏱️ 응답 시간: 약 2-3배 증가 가능
- ✅ Gemini 2.0 Flash와 GPT-4o-mini는 충분히 빠름

## 8001 포트 문제 해결
- 임시로 설정된 환경변수가 원인
- 컴퓨터 재부팅으로 완전히 초기화됨
- 코드에는 8001 관련 내용이 없음 (모두 8000 사용)

## 다음 테스트 영상 추천
긴 영상으로 테스트하여 개선 효과를 확인하세요:
- 20-30분 이상의 인터뷰/대담
- 발표/강연 영상
- 패널 토론
