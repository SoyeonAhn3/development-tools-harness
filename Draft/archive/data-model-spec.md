> **보관 문서**
> 이 문서의 내용은 `ai-development-harness-mvp-plan-v0.5.md`에 흡수되었다.
> v0.5 작성 과정의 설계 기록으로 보존한다. 최신 기준은 v0.5를 따른다.

# 데이터 모델 명세

작성일: 2026-09-14
문서 상태: 확정 (사용자 확인 완료)
관련 결정: `harness-decision-record.md` D-19, D-24~D-33
관련 문서: `rejection-path-spec.md`
반영 대상: `ai-development-harness-mvp-plan.md` v0.5 신설 절

---

## 1. 원칙

1. **파생값을 중복 저장하지 않는다.** 완료 판정에 필요한 `validated_revision`, `reviewed_revision` 같은 값은 검사 이력에서 계산하며 `tasks`에 사본을 두지 않는다. 상태를 두 곳에 두면 반드시 어긋난다.
2. **상태와 단계를 분리한다.** 상태는 Workflow와 무관하게 공통이고, 어느 단계까지 갔는지는 `current_step`으로 관리한다.
3. **AI는 어떤 테이블도 직접 쓰지 않는다.** 모든 기록은 Orchestrator가 수행한다.
4. **시작만 기록된 검사는 성공이 아니다.** `STARTED`로 남은 행은 재개 시 재실행 대상이다.

---

## 2. 저장 위치

```text
%LOCALAPPDATA%/AI-Development-Harness/{project.id}-{repo-path-hash}/
├─ state.db
├─ backups/        최근 10개 순환
└─ logs/           검증 명령 전체 로그
```

`{repo-path-hash}`는 저장소 절대 경로의 짧은 해시다. 같은 `project.id`를 가진 다른 체크아웃을 구분하면서 디렉토리 이름은 사람이 읽을 수 있게 유지한다.

---

## 3. 상태 정의

### 3.1 Phase

| 상태 | 의미 |
|---|---|
| `PLANNING` | Planner가 계획 작성 중 |
| `PLAN_PENDING_APPROVAL` | 계획 승인 대기 |
| `PLAN_REJECTED` | 계획 반려됨, 재계획 대상 |
| `PLAN_BLOCKED` | 계획 반려 3회 초과, 자동 재계획 중단 |
| `PLAN_APPROVED` | 승인됨, 실행 가능 |
| `IN_PROGRESS` | Task 실행 중 |
| `RESULT_PENDING_APPROVAL` | 결과 승인 대기 |
| `RESULT_REJECTED` | 결과 반려됨, 재작업 대상 |
| `REPLAN_REQUIRED` | 요구사항 오해로 재계획 필요 |
| `ACCEPTED` | 사용자 인수 완료 |
| `ABANDONED` | Phase 폐기, 브랜치·커밋은 보존 |

### 3.2 Task

| 상태 | 의미 |
|---|---|
| `PENDING` | 선행 Task 미완료 |
| `READY` | 실행 가능 |
| `RUNNING` | 실행 중 (세부 위치는 `current_step`) |
| `WAITING_APPROVAL` | 승인 대상 행동에서 정지 |
| `REWORK_REQUIRED` | 반려로 재작업 대상 |
| `BLOCKED` | `DENY_STOP` 또는 해결 불가로 중단 |
| `FAILED` | 재시도 한도 초과·실행 환경 문제 |
| `COMPLETED` | 완료 조건 충족 및 커밋 확인 |

`FAILED`(시스템이 수행하지 못함)와 `REWORK_REQUIRED`(사용자가 수용하지 않음)는 다른 상태다.

### 3.3 Step

Workflow가 단계 순서를 정의한다. 상태 집합은 Workflow와 무관하게 동일하다.

```text
Fast      implement → quick_validate → commit
Standard  implement → pre_validate → review → post_validate → commit
Strict    implement → pre_validate → review → post_validate → commit
```

`step_status`는 `STARTED` / `PASSED` / `FAILED` 중 하나다. 재개 시 `STARTED`로 남은 단계는 성공으로 간주하지 않고 현재 Revision에서 다시 실행한다.

### 3.4 상태 전이

```text
Phase
  PLANNING → PLAN_PENDING_APPROVAL
  PLAN_PENDING_APPROVAL ─approve→ PLAN_APPROVED → IN_PROGRESS
                        ─reject→ PLAN_REJECTED → PLANNING
                                 (3회 초과) → PLAN_BLOCKED
  IN_PROGRESS ─모든 Task 종결→ RESULT_PENDING_APPROVAL
  RESULT_PENDING_APPROVAL ─approve→ ACCEPTED
                          ─NOT_WORKING/QUALITY/MISSING→ RESULT_REJECTED → IN_PROGRESS
                          ─WRONG_REQ→ REPLAN_REQUIRED → PLANNING
                          ─ABANDON→ ABANDONED

Task
  PENDING ─선행 완료→ READY ─Run 선택→ RUNNING
  RUNNING ─승인 대상 행동→ WAITING_APPROVAL ─approve→ RUNNING
                                           ─DENY_ALT→ RUNNING (제약 추가)
                                           ─DENY_STOP→ BLOCKED
  RUNNING ─완료 조건 + 커밋 확인→ COMPLETED
  RUNNING ─재시도 한도 초과→ FAILED
  COMPLETED ─결과 반려→ REWORK_REQUIRED → RUNNING (attempt_no + 1)
  BLOCKED ─사용자 해제→ READY
```

"모든 Task 종결"은 `COMPLETED`, `BLOCKED`, `FAILED`를 포함한다. 미완료 Task가 있어도 결과 승인을 요청할 수 있으며, 결과 자료에 미완료 항목과 사유를 명시한다.

---

## 4. 스키마

```sql
-- 메타. project_id, repo_path, schema_version, harness_version
CREATE TABLE schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Run은 Phase 실행 단위다.
-- 계획 수립과 기획 검토는 파일 산출물이므로 Run을 만들지 않는다.
CREATE TABLE runs (
  id           TEXT PRIMARY KEY,
  phase_id     TEXT NOT NULL,
  status       TEXT NOT NULL,          -- ACTIVE / SUSPENDED / CLOSED
  branch       TEXT NOT NULL,
  plan_hash    TEXT NOT NULL,
  owner_pid    INTEGER,
  heartbeat_at TEXT,
  started_at   TEXT NOT NULL,
  ended_at     TEXT
);

CREATE TABLE phases (
  id                TEXT PRIMARY KEY,
  title             TEXT NOT NULL,
  status            TEXT NOT NULL,
  plan_hash         TEXT,
  plan_reject_count INTEGER NOT NULL DEFAULT 0,
  branch            TEXT,
  start_commit      TEXT,
  end_commit        TEXT,
  updated_at        TEXT NOT NULL
);

CREATE TABLE tasks (
  id              TEXT PRIMARY KEY,
  phase_id        TEXT,                -- v1.1 독립 Task 대비 NULL 허용
  status          TEXT NOT NULL,
  current_step    TEXT,
  step_status     TEXT,                -- STARTED / PASSED / FAILED
  workflow        TEXT,                -- fast / standard / strict
  workflow_reason TEXT,
  task_hash       TEXT NOT NULL,
  attempt_no      INTEGER NOT NULL DEFAULT 1,
  retry_count     INTEGER NOT NULL DEFAULT 0,
  reject_count    INTEGER NOT NULL DEFAULT 0,
  updated_at      TEXT NOT NULL,
  FOREIGN KEY (phase_id) REFERENCES phases(id)
);

-- 반려·재작업으로 다시 시작할 때마다 1행
CREATE TABLE task_attempts (
  id                 INTEGER PRIMARY KEY,
  task_id            TEXT NOT NULL,
  attempt_no         INTEGER NOT NULL,
  run_id             TEXT,
  started_at         TEXT NOT NULL,
  ended_at           TEXT,
  outcome            TEXT,             -- COMPLETED / REWORK / BLOCKED / FAILED
  commit_sha         TEXT,
  invalidated_reason TEXT,
  UNIQUE (task_id, attempt_no)
);

CREATE TABLE approvals (
  id                TEXT PRIMARY KEY,  -- APR-001
  kind              TEXT NOT NULL,     -- phase_plan / task_plan / risk_decision
                                       -- / phase_result / task_result / push / merge
  target_type       TEXT NOT NULL,     -- phase / task
  target_id         TEXT NOT NULL,
  plan_hash         TEXT NOT NULL,
  task_hash         TEXT,
  requested_payload TEXT NOT NULL,     -- 승인 요청 시 사용자에게 제시한 내용
  requested_at      TEXT NOT NULL,
  decision          TEXT,              -- APPROVED / REJECTED / NULL(대기)
  decided_at        TEXT,
  valid             INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE rejections (
  id                TEXT PRIMARY KEY,  -- REJ-001
  approval_id       TEXT NOT NULL,
  reject_type       TEXT NOT NULL,
  user_text         TEXT NOT NULL,     -- 사용자 자연어 원문
  ai_classification TEXT NOT NULL,     -- AI 분류 결과
  confirmed_at      TEXT NOT NULL,     -- 사용자 확인 시각
  plan_hash         TEXT NOT NULL,
  FOREIGN KEY (approval_id) REFERENCES approvals(id)
);

-- 부분 반려 대상
CREATE TABLE rejection_targets (
  rejection_id TEXT NOT NULL,
  task_id      TEXT NOT NULL,
  PRIMARY KEY (rejection_id, task_id)
);

CREATE TABLE validations (
  id            INTEGER PRIMARY KEY,
  task_id       TEXT NOT NULL,
  attempt_no    INTEGER NOT NULL,
  stage         TEXT NOT NULL,         -- quick / pre_review / post_review
  name          TEXT NOT NULL,
  command       TEXT NOT NULL,
  required      INTEGER NOT NULL,
  code_revision TEXT NOT NULL,
  started_at    TEXT NOT NULL,
  ended_at      TEXT,
  exit_code     INTEGER,
  result        TEXT NOT NULL,         -- STARTED / PASSED / FAILED
                                       -- / SKIPPED_BY_POLICY / ABORTED
  log_path      TEXT
);

CREATE TABLE reviews (
  id                 INTEGER PRIMARY KEY,
  task_id            TEXT NOT NULL,
  attempt_no         INTEGER NOT NULL,
  kind               TEXT NOT NULL,    -- light / strict / delta
  code_revision      TEXT NOT NULL,
  plan_hash          TEXT NOT NULL,
  baseline_review_id INTEGER,          -- Delta Review의 이전 기준
  result             TEXT NOT NULL,    -- STARTED / PASS / CHANGES_REQUESTED
                                       -- / ABORTED / SKIPPED_BY_POLICY
  started_at         TEXT NOT NULL,
  ended_at           TEXT
);

CREATE TABLE review_findings (
  id                    INTEGER PRIMARY KEY,
  review_id             INTEGER NOT NULL,
  severity              TEXT NOT NULL,  -- critical / major / minor
  finding_ref           TEXT,           -- REV-001
  file                  TEXT,
  description           TEXT NOT NULL,
  required_change       TEXT,
  resolved_at           TEXT,
  resolved_in_review_id INTEGER,
  FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- 커밋 직후 중단 복구용
CREATE TABLE commit_intents (
  id            TEXT PRIMARY KEY,      -- 커밋 메시지 메타데이터에 기록
  run_id        TEXT NOT NULL,
  task_id       TEXT NOT NULL,
  attempt_no    INTEGER NOT NULL,
  branch        TEXT NOT NULL,
  parent_commit TEXT NOT NULL,
  code_revision TEXT NOT NULL,
  plan_hash     TEXT NOT NULL,
  status        TEXT NOT NULL,         -- PENDING / CONFIRMED / ABANDONED
  commit_sha    TEXT,
  created_at    TEXT NOT NULL
);

-- 실행에 사용한 계획 입력 사본
CREATE TABLE plan_snapshots (
  plan_hash       TEXT PRIMARY KEY,
  phase_id        TEXT,
  work_items_yaml TEXT NOT NULL,
  domain_rules_md TEXT NOT NULL,
  project_yaml    TEXT NOT NULL,
  created_at      TEXT NOT NULL
);
```

---

## 5. Revision과 Hash

### 5.1 코드 Revision

임시 index를 사용해 작업 폴더 전체의 Git tree hash를 계산한다.

```bash
GIT_INDEX_FILE=<임시파일> git add -A
GIT_INDEX_FILE=<임시파일> git write-tree
```

- `.gitignore`를 그대로 따르므로 로그·캐시 제외 규칙을 다시 구현하지 않는다.
- 새 파일, 삭제, 이름 변경, 실행 권한 변경이 모두 반영된다.
- 사용자의 스테이징 영역을 건드리지 않는다.
- 추가 제외 대상: `.dev-harness/reports/`. 보고서 생성 때문에 코드 Revision이 바뀌지 않게 한다.
- 프로젝트는 Git 저장소여야 한다. D-12에서 이미 전제된 제약이다.

### 5.2 task_hash

Task 정의만으로 계산한다. 반려 후 무효화 범위를 Task 단위로 좁히는 데 사용한다.

- 포함: `id`, `title`, `acceptance_criteria`, `requirement_refs`, `domain_rule_refs`, `risk_tags`, `depends_on`
- 제외: 실행 상태, 재시도 횟수, 승인 여부

목록은 정렬해 정규화하고 공백 차이는 무시한다.

### 5.3 plan_hash

Phase 단위로 계산한다. 승인은 이 값에 연결한다.

- 포함: Phase 정의, 소속 Task의 `task_hash` 정렬 목록, 공통 Domain Rule 본문, 참조된 Domain Rule 본문, `validation` 설정, `workflow_routing` 설정, `approval` 정책
- 제외: 실행 상태, 로그, 보고서, **`plan.md`의 서술 문장**

`plan.md`는 사람이 읽는 설명이므로 문구 수정만으로 승인이 무효화되지 않게 한다. 전역 hash 하나를 쓰면 무관한 Phase의 Task 추가로 모든 승인이 무효화된다.

---

## 6. 동시 실행 제어

- `runs.owner_pid`와 `heartbeat_at`으로 실행 소유권을 확인한다.
- `ACTIVE` Run의 프로세스가 살아 있으면 새 실행을 시작하지 않는다.
- heartbeat가 끊긴 Run은 `SUSPENDED`로 전환하고 재개 절차를 따른다.
- 파일 락은 사용하지 않는다. OneDrive 동기화 폴더에서 신뢰하기 어렵고, DB는 LocalAppData에 있어 안전하다.

---

## 7. 재개 시 검사 순서

```text
1. runs에서 해당 프로젝트의 ACTIVE/SUSPENDED Run 조회
2. owner_pid 생존 확인
3. schema_meta.repo_path와 현재 저장소 경로 대조
4. runs.branch와 현재 HEAD 대조
5. commit_intents에 PENDING이 있으면 커밋 복구 절차 수행
6. plan_snapshots의 plan_hash와 현재 계획 파일 hash 대조
7. 코드 Revision 재계산 후 마지막 체크포인트와 대조
8. tasks.current_step / step_status로 재개 지점 결정
   - step_status = STARTED  → 해당 단계 재실행
   - step_status = PASSED   → 다음 단계
```

설명되지 않는 불일치는 `STATE_MISMATCH`로 중단하고 차이를 표시한다. 자동으로 덮어쓰거나 되돌리지 않는다.

---

## 8. 백업과 스키마 버전

- Task 완료와 정상 중단 시 SQLite 백업 API로 `backups/`에 사본을 만든다. 최근 10개를 순환 보관한다.
- `schema_meta.schema_version`을 기록한다. 하네스 버전과 DB 스키마 버전이 맞지 않으면 실행하지 않고 안내한다. 자동 마이그레이션은 v1.1로 미룬다.
