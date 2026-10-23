[한국어](README_ko.md) | [English](README.md)

# development-tools-harness

AI가 구현하고, 하네스가 검증하며, 사람은 중요한 결정을 승인합니다.

언어에 묶이지 않는 로컬 개발 도구입니다. 완성된 개발 기획서를 주면 Phase 0(환경 준비)부터 Phase를 나누고, 시작을 지시하면 기획서에 적힌 언어와 도구로 환경을 세팅해 개발과 테스트를 진행합니다. 끝나면 산출물을 안내하고, 인수하면 Phase를 완료 처리합니다. 목적은 중복 코드, 잘못된 코드, 낮은 품질의 코드를 줄이는 것입니다.

## 현재 상태

- **기획서 1.10 확정(2026-10-23).** [새 기획서](Draft/ai-development-harness-plan-v1.md)가 축소 MVP 0.4를 대체하며 언어 제약을 없앴습니다.
- **2026-10-23 Phase 0을 인수·완료했습니다.** 환경 검사와 전체 회귀 691개가 통과했습니다(실패·skip 0). 테스트 ID 집합도 이전 기록과 같습니다. 기준선과 41개 모듈 대응표를 인수했습니다. [Phase 1](Phase/Phase1_ValidationContract.md)은 상세 계획을 작성했으며 구현은 미시작입니다. 회귀 검사는 보관된 Codex CLI 0.155.1로 수행했고 PC 기본 0.163.0은 미검증입니다. [Phase 0 기록](Phase/Phase0_Baseline.md)을 참고하세요.
- **기존 코드를 재사용합니다.** 축소 MVP 0.4로 만든 CLI(Phase 1–3을 2026-09-18, 2026-09-21, 2026-10-07에 인수)가 출발점입니다. 지금은 Python과 pytest 프로젝트만 지원합니다. 해당 Phase 묶음은 [Phase/archive/lean-mvp-0.4](Phase/archive/lean-mvp-0.4/Overview.md)에 보관했고, 그 Phase 4(자체 개발)는 취소했습니다.

## 동작 방식(목표)

```text
1. 사용자가 기획서를 준다
2. 하네스가 Phase와 영문·국문 Phase 문서를 만든다. 항상 Phase 0부터 시작한다
3. 사용자가 검토하고 "시작"을 지시한다
4. Phase 0: 환경을 세팅하고 기준선을 기록한다
5. 개발 Phase: 개발, 테스트, 품질 검사, 별도 리뷰, 제한된 수정
6. 하네스가 보고서로 산출물을 안내한다
7. 사용자가 인수(Phase 완료 처리)하거나 수정을 요청한다
```

- **하네스에는 언어 지식이 없습니다.** 종료 코드, JUnit XML 테스트 보고서, 파일 해시로만 결과를 판정합니다. 언어 지식은 기획서와 AI가 가집니다.
- **품질 장치.** 작성 전 기존 코드 탐색, 재사용 근거, 그대로 복사한 코드의 중복 보고, 품질 검사, 프로젝트 규칙, 고정된 기준표로 리뷰하는 독립 Reviewer, 검사 기준 완화 차단. 기존 문제는 기준선으로 기록하고 새로 생긴 문제만 막습니다.
- **통제는 사용자에게 있습니다.** 시작 전에는 아무것도 실행하지 않습니다. 계획에 없는 설치, 네트워크 사용, 시스템 변경은 승인이 필요합니다. 버전은 승인 없이 바뀌지 않습니다. 관리자 권한 작업, Git 쓰기, 배포는 수동입니다.
- **첫 버전 검증 범위.** Python, TypeScript, Java. DB는 SQLite만 검증하고 서버 DB는 미검증 한계로 남깁니다.

## 로드맵

| Phase | 내용 | 상태 |
|---|---|---|
| [0 — 기준선 확인](Phase/Phase0_Baseline.md) | 현재 환경과 전체 회귀 검사 확인, 기준선 기록, 모듈 대응표 확정 | ✅ |
| [1 — 검사 계약과 격리](Phase/Phase1_ValidationContract.md) | 언어와 무관한 검사 계약, 격리 방식 C, Java 다운로드 확인. 최소 Python·Java 예제 각 1개로 검증 | 🔲 |
| [2 — 계획 확장과 환경 세팅](Phase/Phase2_PlanningAndSetup.md) | Phase 0을 포함한 계획, 기술 구성·버전 제안, Phase 문서, Phase 0 실행 | 🔲 |
| [3 — 개발 흐름과 품질 장치](Phase/Phase3_WorkflowAndQuality.md) | AI 권한, 품질 장치, 보고서, 인수, CLI 단순화 | 🔲 |
| [4 — 실사용 검증](Phase/Phase4_RealWorldValidation.md) | Decision Desk Phase 1, 기존 Python 프로젝트, 모의 Java 프로젝트 | 🔲 |

## 현재 CLI 사용법

새 Phase에서 바꾸기 전까지 CLI는 축소 MVP 0.4 그대로 동작합니다. Windows, Python 3.12.10, pytest 프로젝트만 지원하며 `register`, `plan`, `plan-approve`, `workflow-prepare`, `workflow-approve`, `workflow-run`, `workflow-accept` 같은 명령을 씁니다. 설치와 사용법은 보관한 [0.4 README](Phase/archive/lean-mvp-0.4/README_ko_v0.4.md)에 있습니다. 단순화할 명령은 `plan`, `start`, `status`, `approve`, `accept`, `feedback`, `resume`입니다(기획서 2.2).

## 프로젝트 구조

```text
development-tools-harness/
├── README.md
├── README_ko.md
├── pyproject.toml
├── requirements-dev.lock
├── .agents/skills/
│   ├── phase-doc/                      # Phase 문서 작성 규칙과 템플릿
│   └── harness-github-push/
├── src/development_harness/            # 하네스 CLI (모듈 41개)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Phase/
│   ├── Overview.md
│   ├── Phase0_Baseline.md              # ✅ 2026-10-23 인수
│   ├── Phase1_ValidationContract.md    # 🔲 미시작
│   ├── Phase2_PlanningAndSetup.md      # 🔲 미시작
│   ├── Phase3_WorkflowAndQuality.md    # 🔲 미시작
│   ├── Phase4_RealWorldValidation.md   # 🔲 미시작
│   └── archive/lean-mvp-0.4/           # 이전 Phase, 근거, README 사본
└── Draft/
    ├── ai-development-harness-plan-v1.md   # 현재 기획서 (1.10)
    └── archive/                            # 축소 MVP 0.4와 이전 계획
```

## 문서

- [기획서 1.10](Draft/ai-development-harness-plan-v1.md): 제품 정의, 흐름, Phase 0, 검사 계약, 품질 장치, 권한, 보고서, 범위, 결정 기록.
- [Phase 개요](Phase/Overview.md): Phase 계획, 요구사항 대응표, 공통 완료 규칙. 각 Phase 문서에는 영문과 국문 전체 내용이 있습니다.
- [보관한 축소 MVP 0.4 Phase](Phase/archive/lean-mvp-0.4/Overview.md)와 [0.4 기획서](Draft/archive/ai-development-harness-lean-mvp-plan-v0.4.md): 기존 코드의 이력입니다. 기록된 근거는 수정하지 않았습니다.
- [이전 계획 문서](Draft/archive/): 과거 설계입니다. 그 범위는 현재 기획서에 적용되지 않습니다.
