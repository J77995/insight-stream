# VSCode → Cursor 환경 이동 가이드

## 결론 (요약)

기존 프로젝트를 Cursor로 옮길 때:

### 1. Cursor에서 프로젝트 열기
```bash
# Cursor에서 폴더 열기
File > Open Folder > C:\workspace\insight-stream-main 선택
```

### 2. 가상환경 그대로 사용
```bash
# Backend 터미널
cd backend
venv\Scripts\activate  # 기존 가상환경 활성화
python main.py

# Frontend 터미널 (새 터미널 열기)
cd frontend
npm run dev
```

### 3. Python Interpreter 선택 (Cursor에서)
- `Ctrl + Shift + P`
- "Python: Select Interpreter" 검색
- `.\backend\venv\Scripts\python.exe` 선택

---

## 끝!

**추가 작업 필요 없음:**
- ✅ 가상환경 재생성 불필요 (기존 venv 그대로 사용)
- ✅ 패키지 재설치 불필요 (이미 설치됨)
- ✅ 설정 파일 변경 불필요

**확인 사항:**
- Backend: `python main.py` 정상 실행 확인
- Frontend: `npm run dev` 정상 실행 확인
