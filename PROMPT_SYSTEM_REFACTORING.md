# 프롬프트 시스템 재구조화 완료 보고서

## 변경 개요

프롬프트 시스템을 단순화하여 **모듈형 구조**만 사용하도록 재설계했습니다. 기존의 이중 구조(전통형/모듈형)를 제거하고, 사용자가 제공한 프롬프트를 기반으로 통일된 시스템을 구축했습니다.

---

## 주요 변경 사항

### 1. 프롬프트 템플릿 단순화 (`prompts.py`)

#### 변경 전:
- **PROMPT_TEMPLATES**: 8개 카테고리별로 각각 다른 프롬프트 (system_prompt, overview_prompt, detail_prompt)
- **PromptGenerator**: 복잡한 조합 로직 (roles + formats의 INPUT, OBJECTIVE, OUTPUT_REQUIREMENTS, STYLE, CONSTRAINTS 등을 조합)
- **이중 구조**: 전통형과 모듈형 프롬프트가 공존

#### 변경 후:
- **3개의 BASE 템플릿만 유지**:
  - `BASE_OVERVIEW`: 모든 주제에 공통으로 사용되는 간략 요약 프롬프트
  - `BASE_DETAIL_DIALOGUE`: 대화형(인터뷰/대담) 상세 요약 프롬프트
  - `BASE_DETAIL_PRESENTATION`: 발표형(강연/세미나) 상세 요약 프롬프트
  
- **roles 딕셔너리**: 10개 주제별 역할 정의만 유지
  - general, default, tech, business, ai, economy, politics, interview, lecture, daily
  
- **단순한 변수 치환**: `{role}`, `{transcript}` 2개 변수만 사용

#### 핵심 로직:
```python
def create_prompt(self, topic: str, format_type: str, transcript: str, prompt_type: str = "detail") -> str:
    role = self.roles.get(topic, self.roles["general"])
    
    if prompt_type == "overview":
        return self.BASE_OVERVIEW.format(role=role, transcript=transcript)
    else:
        if format_type == "presentation":
            template = self.BASE_DETAIL_PRESENTATION
        else:  # dialogue 또는 기본값
            template = self.BASE_DETAIL_DIALOGUE
        return template.format(role=role, transcript=transcript)
```

### 2. API 엔드포인트 단순화 (`endpoints.py`)

#### 변경 전:
```python
if request.format_type:
    # 모듈형 프롬프트 사용
    ...
else:
    # 전통형 프롬프트 사용 (PROMPT_TEMPLATES 조회)
    prompt_template = get_prompt_template(category)
    ...
```

#### 변경 후:
```python
# 모든 요청이 모듈형 프롬프트 사용 (단일 경로)
category = request.category or "general"
format_type = request.format_type or "dialogue"  # 기본값

prompt_overview = get_modular_prompt(category, format_type, overview_transcript, "overview")
prompt_detail = get_modular_prompt(category, format_type, detail_transcript, "detail")
```

**제거된 기능**:
- `get_prompt_template()` 함수 호출 제거
- `/api/prompts/{category}` 엔드포인트 제거 (더 이상 사용되지 않음)
- 전통형/모듈형 분기 로직 제거

### 3. 스키마 기본값 설정 (`schemas.py`)

#### 변경:
```python
# Before
category: Optional[str] = Field(default="default", ...)
format_type: Optional[str] = Field(default=None, ...)

# After  
category: Optional[str] = Field(default="general", ...)
format_type: Optional[str] = Field(default="dialogue", ...)
```

---

## 데이터/프롬프트 플로우 변경

### 변경 전 (Before)

```
사용자 요청
    ↓
format_type 체크
    ↓
    ├─── format_type 있음 → 모듈형
    │    ├─ roles 딕셔너리에서 역할 선택
    │    ├─ formats 딕셔너리에서 구조 선택
    │    └─ 복잡한 조합 (ROLE+INPUT+OBJECTIVE+OUTPUT+STYLE+CONSTRAINTS)
    │
    └─── format_type 없음 → 전통형
         ├─ PROMPT_TEMPLATES에서 category 조회
         └─ system_prompt + overview_prompt/detail_prompt
    ↓
LLM API 호출
```

**문제점**:
- 이중 구조로 인한 복잡성
- 프롬프트가 분산되어 관리 어려움
- 주제별로 완전히 다른 프롬프트 구조

### 변경 후 (After)

```
사용자 요청
    ↓
기본값 적용
  - category: "general" (없으면)
  - format_type: "dialogue" (없으면)
    ↓
모듈형 프롬프트만 사용 (단일 경로)
    ↓
    ├─ prompt_type 확인
    │   ├─ "overview" → BASE_OVERVIEW
    │   └─ "detail" → format_type 확인
    │       ├─ "dialogue" → BASE_DETAIL_DIALOGUE
    │       └─ "presentation" → BASE_DETAIL_PRESENTATION
    ↓
roles에서 topic에 맞는 역할 선택
    ↓
템플릿에 {role}, {transcript} 삽입
    ↓
LLM API 호출
```

**개선점**:
- 단일 경로로 단순화
- 3개의 명확한 템플릿
- 주제는 역할(Role)만 변경
- 형식은 템플릿 선택만 영향

---

## 프롬프트 구조

### BASE_OVERVIEW (모든 주제 공통)

```
[ROLE]
{role}  ← 주제별 역할만 변경

[INPUT]
아래에는 두 명 이상이 참여한 대담, 인터뷰, 패널 토론, Q&A 세션의 원문 스크립트가 제공됩니다.
구어체, 중복, 끼어들기, 즉흥 발언이 포함될 수 있습니다.

[OBJECTIVE]
- 이 스크립트의 핵심 내용과 인사이트에 대해 8줄 이내로 요약하시오.
인사이트는 이 스크립트의 독자가 얻어갈 수 있는 정보와 통찰, 이 컨텐츠만의 차별화된 내용이나 관점이 담기는 것이 필요하다

==========
[TARGET SCRIPT]
{transcript}
```

### BASE_DETAIL_DIALOGUE (대화형)

```
[ROLE]
{role}

[INPUT]
아래에는 두 명 이상이 참여한 대담, 인터뷰, 패널 토론, Q&A 세션의 원문 스크립트가 제공됩니다.

[OBJECTIVE]
# 상세 요약
전체 스크립트를 아래 조건들에 따라 상세히 요약하시오.

[OUTPUT REQUIREMENTS]
* 화자별/발언순/주제별 상세 요약 (필수)
   - 발언 순서를 유지한 채 요약하십시오.
   - 각 발언은 반드시 화자를 명시하십시오.
   - 각 대담의 내용을 소주제별로 그룹화하고, 소주제명 아래 해당되는 발언요약들을 넣으시오
   - 중요한 메시지나 통찰을 담은 발언은 따옴표("") 안에 굵은 글씨로 원문을 인용하며 강조하시오
   - 이 부분 요약 본문의 내용은 전체 스크립트 내용 분량의 20% 정도가 되는 것을 목표하시오

* 핵심 질문과 답변 정리 (필수)
* 관점 차이 및 합의 지점 (조건부)
* 상세 요약문을 끝까지 출력한 후 맨 뒤에는 "(Summarized from Youtube)"라는 문구를 추가하시오

[STYLE GUIDELINES]
- 회의록 + 리서치 노트 중간 톤
- 화자 의도 왜곡 금지

[CONSTRAINTS]
- 화자 혼동 금지
- 발언 순서 임의 변경 금지

==========
[TARGET SCRIPT]
{transcript}
```

### BASE_DETAIL_PRESENTATION (발표형)

```
[ROLE]
{role}

[INPUT]
아래에는 단일 발표자 또는 소수의 발표자가 진행하는 강연, 발표, 세미나의 원문 스크립트가 제공됩니다.

[OBJECTIVE]
# 상세 요약
전체 스크립트를 내용의 논리 구조와 메시지가 선명하게 드러나는 구조 중심 요약으로 작성하시오.

[OUTPUT REQUIREMENTS]
* 전체 강연 구조 요약 (필수)
   - 발표의 논리 전개 구조를 목차 형태로 제시하십시오.
   - 번호 기반 계층 구조를 사용하십시오. (1, 1.1, 1.2, 2, 2.1 ...)

* 내용 순서별 상세 요약 (필수)
   - 발표 순서를 유지한 채 내용을 요약하십시오.
   - 소주제별로 그룹화하고, 각 소주제 아래 핵심 내용을 정리
   - 전체 스크립트 분량의 20% 정도를 목표로 요약

* 핵심 개념 및 프레임워크 정리 (필수)
* 발표자의 핵심 메시지 및 결론 (필수)
* 상세 요약문을 끝까지 출력한 후 맨 뒤에는 "(Summarized from Youtube)"라는 문구를 추가하시오

[STYLE GUIDELINES]
- 강의 노트 + 리서치 요약 톤
- 논리 구조가 한눈에 보이도록 작성

[CONSTRAINTS]
- 시간 순 단순 나열 금지
- 논리적 연결 없이 발언 나열 금지

==========
[TARGET SCRIPT]
{transcript}
```

---

## 사용자 선택에 따른 변화

### 1. 주제(Topic/Category) 선택

**영향**: `[ROLE]` 섹션만 변경

예시:
- **general**: "대담·인터뷰·패널 토론을 분석하는 전문 에디터이자 회의·대화 기록을 구조화하는 리서치 애널리스트"
- **ai**: "AI/ML 분야의 기술적 깊이와 실용적 응용을 모두 이해하는 AI 리서치 애널리스트"
- **tech**: "최신 기술 트렌드와 엔지니어링 문맥을 깊이 이해하는 테크 전문 에디터이자 테크니컬 라이터"
- **economy**: "경제 현상과 금융 시장을 분석하는 이코노미스트이자 금융 애널리스트"

→ **프롬프트의 나머지 부분은 동일**

### 2. 형식(Format) 선택

**영향**: Detail 프롬프트의 템플릿 선택

- **dialogue** (기본값):
  - INPUT: "대담, 인터뷰, 패널 토론, Q&A 세션..."
  - OUTPUT: "화자별/발언순 요약", "핵심 질문과 답변", "관점 차이"
  - STYLE: "회의록 + 리서치 노트 톤", "화자 의도 왜곡 금지"
  
- **presentation**:
  - INPUT: "강연, 발표, 세미나..."
  - OUTPUT: "강연 구조 요약", "내용 순서별 요약", "핵심 개념 정리"
  - STYLE: "강의 노트 톤", "논리 구조 중심"

→ **Overview는 항상 동일**

### 3. 조합 예시

| 사용자 입력 | 실제 적용 값 | Overview Role | Detail 템플릿 | Detail 특징 |
|------------|-------------|--------------|--------------|------------|
| category만 지정 (ai) | ai + dialogue | AI 리서치 애널리스트 | DIALOGUE | 화자별 발언 구조화 |
| category + dialogue | tech + dialogue | 테크 전문 에디터 | DIALOGUE | 화자별 발언 구조화 |
| category + presentation | economy + presentation | 이코노미스트 | PRESENTATION | 논리 구조 중심 |
| 아무것도 지정 안함 | general + dialogue | 전문 에디터 | DIALOGUE | 화자별 발언 구조화 |

---

## 핵심 개선 효과

### 1. 단순성 (Simplicity)
- 3개 템플릿, 2개 변수, 1개 경로
- 복잡한 조합 로직 제거
- 코드 라인 수: 527줄 → 202줄 (62% 감소)

### 2. 일관성 (Consistency)
- 모든 요청이 동일한 방식으로 처리
- 주제 변경 = 역할만 변경
- 형식 변경 = 템플릿만 변경

### 3. 유지보수성 (Maintainability)
- 프롬프트 수정 시 1곳만 변경
- 새 주제 추가 시 roles에 1줄만 추가
- 명확한 구조로 이해하기 쉬움

### 4. 확장성 (Extensibility)
- 새로운 형식 추가 간단 (BASE_DETAIL_XXX 추가)
- 새로운 주제 추가 간단 (roles에 추가)
- 독립적인 변경 가능

---

## 테스트 시나리오

### 시나리오 1: category만 지정
```json
{
  "url": "https://youtube.com/watch?v=...",
  "category": "ai"
  // format_type 없음
}
```
**결과**: ai 역할 + dialogue 템플릿 (기본값)

### 시나리오 2: category + format_type 지정
```json
{
  "url": "https://youtube.com/watch?v=...",
  "category": "tech",
  "format_type": "presentation"
}
```
**결과**: tech 역할 + presentation 템플릿

### 시나리오 3: 아무것도 지정 안함
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```
**결과**: general 역할 + dialogue 템플릿 (기본값)

---

## 마이그레이션 가이드

### 기존 코드 사용자
기존에 `format_type` 없이 `category`만 사용하던 경우:
- **자동으로 dialogue가 기본값으로 적용됨**
- 동작 변경 없이 호환됨
- 단, 프롬프트 내용은 새로운 BASE 템플릿 기준으로 변경됨

### API 변경 사항
- **제거**: `GET /api/prompts/{category}` 엔드포인트
- **유지**: `GET /api/prompts/categories` (카테고리 목록 조회)
- **유지**: `POST /summarize` (동작 개선)
- **유지**: `POST /api/prompts/custom` (커스텀 프롬프트)

---

## 결론

프롬프트 시스템을 전면 재설계하여:
1. **사용자 제공 프롬프트를 기반**으로 통일
2. **주제 선택 → 역할만 변경**
3. **형식 선택 → Detail 템플릿만 변경**
4. **전통형 시스템 완전 제거**

단순하고 일관된 구조로 변경하여 유지보수성과 확장성을 크게 개선했습니다.
