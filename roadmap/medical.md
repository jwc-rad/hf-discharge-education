# 의료진(임상) 파트 계획

전체 흐름은 [docs/engineering/architecture.md](../docs/engineering/architecture.md) 참고. 기술 파트 계획은 [engineering.md](engineering.md). 데모 샘플 작성법은 [docs/medical/demo_fixture_guide.md](../docs/medical/demo_fixture_guide.md).
코드를 직접 수정하지 않아도 되며, 검토 의견은 이 파일의 메모나 issue로 남기면 기술 파트가 반영한다.

## 원천 자료 (KB)

- [ ] 사용할 가이드라인·교육자료 목록 확정 (KSHF, ESC, AHA/ACC, SNUH 원내 자료 등) — 파일은 [data/raw/](../data/raw/README.md) 규칙대로 공유 Drive에 보관
- [ ] 자료별 라이선스/사용 가능 여부 확인
- [ ] 영어 자료 처리 방식 결정: 미리 번역 vs. 생성 시 번역 — [engineering.md](engineering.md)와 협의

## 주제 · 개인화 trigger

- [ ] 핵심 주제 4개 검토: 식이 / 재활 / 복약 / 주의사항(증상악화 대처법, 매일 체중 측정 포함)
- [ ] `TriggerCode` 목록 검토 (현재: 고칼륨혈증, 저칼륨혈증, 저나트륨혈증, CKD, 당뇨, 수분 제한, 와파린, ICD/심박동기) — 추가·삭제·정의
- [ ] trigger별로 영향을 받는 주제 확인 (예: 고칼륨혈증 → 식이)
- [ ] trigger가 켜졌을 때 "의료진 상담 필요" 안내 문구 확정

## chunk 태깅

- [ ] 태깅 방식·담당자 결정 (매핑 시트 등) — [engineering.md](engineering.md)와 협의
- [ ] 각 chunk에 `topics` 와 `applies_when`(해당 trigger) 태깅
- [ ] 환자용(`patient`) / 의료진용(`clinician`) 구분

## 프롬프트 · 출력 검토

- [ ] 추출·생성 프롬프트 검토 (`src/hf_edu/pipeline/prompts.py`) — 누락된 임상 정보, 표현 수위
- [ ] 데모 페이지(`demo/index.html`, 브라우저로 열기)의 샘플 출력 검토: 의학적 정확성, 환자 눈높이, 어조
- [ ] 필요하면 데모 샘플(합성 노트 + fixture) 추가·수정 — 작성 방법: [demo_fixture_guide.md](../docs/medical/demo_fixture_guide.md)
- [ ] 출처 각주·의료진 상담 안내 표시 방식 검토

## 평가 기준 (1차 평가 10월말)

- [ ] 평가 항목 정의: **누락 없이** / **기존 정보(근거)로** / **가독성**
- [ ] 항목별 채점 기준(rubric)과 척도 확정
- [ ] 평가자 구성 및 평가 방식 (블라인드 여부, 표본 수) 결정

## 메모

- 09-30: 개인화 자료가 비식별화되어 있으므로, 식이 위험 trigger(예: 고칼륨혈증)를 추출해 on/off에 따라 교육자료를 달리하고 trigger가 있으면 의료진 상담 필요를 알리기로 함.
- 09-30: 외래예약(`followup`) 데이터는 실제 활용이 어려워 핵심 주제에서 제외.
