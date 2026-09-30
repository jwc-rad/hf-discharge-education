# 기여 가이드

> 이 저장소는 공개(public)이지만 **프로젝트 팀원만 기여하는 저장소**이다.
> (2026-2 서울대학교 「디지털 헬스케어 데이터의 이해와 실습」 6팀) 팀 외부의 fork·PR·issue는 받지 않을 수 있다.

## 1. 반드시 지킬 것 (공개 저장소 규칙)

이 저장소는 누구나 읽을 수 있고, **git 기록은 삭제해도 남는다.** 아래는 커밋·PR·issue·메모 어디에도 올리지 않는다.

- 환자 데이터: MIMIC 노트, EHR 추출본, 실제 환자 정보 (일부·요약·재서술 포함)
- 원본 PDF, 가이드라인 원문 (`data/raw/`는 git-ignored이며 팀 Shared Drive에서만 받는다)
- 자격 증명: API key, token, `.env` (`.env.example`만 커밋), SNUH 내부 접속 정보
- Shared Drive 링크, 내부 회의록(`meetings/`), 개인 메모(`MVP/`)
- 합성 노트에는 **팀이 만든 가상 사례만** 쓴다

실수로 올렸다면 지우는 커밋을 추가하는 것으로 끝나지 않는다. 즉시 팀에 알리고 key는 폐기(rotate)한다.
기록 삭제는 별도 작업(history rewrite)이 필요하다.

커밋 전 확인:

```bash
git status            # 의도하지 않은 파일(.env, PDF, data/)이 없는지
git diff --staged     # 환자 정보·key가 섞이지 않았는지
```

## 2. 개발 환경

conda + pip만 사용한다. 자세한 내용은 [README](README.md#빠른-시작) 참고.

```bash
conda env create -f environment.yml
conda activate hf-edu
cp .env.example .env
pytest -q          # GPU/LLM 불필요 (fake LLM)
ruff check .       # line-length 100
```

## 3. 작업 흐름

1. 팀원은 이 저장소에 직접 push할 수 있지만 **`main`에 바로 push하지 않는다.** 브랜치를 만든다.
   ```bash
   git switch -c <part>/<short-topic>     # 예: eng/kb-ingest, med/fixture-04
   ```
2. 작게 커밋하고 push한 뒤 **Pull Request**를 연다. 대상은 `main`이다.
3. PR에는 무엇을·왜 바꿨는지, 어떻게 확인했는지(`pytest -q` 결과 등)를 적는다.
4. 리뷰어 1명 이상의 승인을 받고 merge한다. **파트 간 걸치는 변경**(스키마, KB 계약 등)은 양쪽 파트 리뷰어를 지정한다.
5. merge 후 브랜치를 삭제한다.

### 커밋 메시지

`type(scope): 요약` 형식을 쓴다 (한국어 또는 영어). type은 `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
예: `docs(roadmap): 파트별 로드맵 디렉터리 추가`

## 4. 파트별 안내

팀은 **기술/엔지니어링 파트**와 **의료진(임상) 파트**로 나뉜다. 문서 목차는 [docs/README.md](docs/README.md).

| 하려는 일 | 읽을 문서 |
|---|---|
| 코드 구조·pipeline 이해 | [architecture.md](docs/engineering/architecture.md) |
| KB 스키마·검색·인용 규칙 변경 | [db_contract.md](docs/engineering/db_contract.md) |
| LLM 실행·SNUH endpoint | [local_llm.md](docs/engineering/local_llm.md) |
| 데모 샘플/fixture 추가·수정 (의료진) | [demo_fixture_guide.md](docs/medical/demo_fixture_guide.md) |
| 진행 중인 작업·체크리스트 | [roadmap/](roadmap/README.md) |

- 로드맵 규칙: 체크리스트는 `- [ ]`/`- [x]`, 담당자는 `(@이름)`, 메모는 `MM-DD`와 함께 하단에 추가. 환자 데이터는 메모에도 쓰지 않는다.
- **의료진**: JSON/git이 부담되면 [fixture 가이드](docs/medical/demo_fixture_guide.md#2-작업-방식-직접-작성-vs-기술-파트-인계)의 "초안 인계" 방식으로 기술 파트에 넘겨도 된다.

## 5. 코드 변경 시 주의

- **테스트**: 동작을 바꾸면 테스트를 추가·수정하고 `pytest -q`가 통과해야 한다.
- **데모 재생성**: pipeline, 템플릿, KB seed, fixture를 바꾸면 `python demo/build_demo.py`를 실행하고 바뀐 `demo/index.html`을 함께 커밋한다. `main`의 `demo/index.html` 변경은 GitHub Pages에 자동 배포되며 **공개된다.**
- **fixture**: `tests/test_demo.py`가 fixture를 `01`, `02`, `03`으로 고정해 검사한다. 새 fixture를 추가하면 테스트도 갱신한다.
- **LLM 호출**: 테스트·데모는 fake LLM으로 동작해야 한다 (`LLM_FAKE=1`). 실제 endpoint 호출을 테스트에 넣지 않는다.
- **의료 내용**: 출력물은 의료진 검토용 초안이다. 임상 내용(주제, trigger, 문구)의 변경은 의료진 파트 리뷰를 받는다.

## 6. 문의

- 질문·논의: 팀 Slack 채널
- 버그·작업 항목: GitHub Issues (환자 정보·key를 붙여넣지 않는다)
