# 段 6 fix 裁定 — レビュー A (10 所見 + テスト節) / レビュー B (12 所見) の親裁定

両レビューとも NO-GO。所見は大きく重なり、**共通の根本原因は 1 つ**である。

> 各 module は「caller が渡した dict を検証する純粋関数」としては正しいが、
> **production 経路が実体 (ファイル・凍結 prereg・policy・git identity) へ束縛されていない。**
> そのため呼び手が値を合成すれば、barrier も allowlist も presence も恒真化する。

すべて real と裁定する (refuted 0)。nit は B-12 のみ。以下の共通契約を先に固定し、
fix を **逐次 3 巡** で投入する (並列にすると interface が再びずれるため)。

## 共通 interface 契約 (親が先に固定。全 fix 子はこれに従う)

### C-1. limitation ID の閉じた集合 (schema module が正本)

`t810_harness_schema.py` に `LIMITATION_IDS: frozenset` を置き、次の 6 個だけとする。
policy・guard receipt・budget receipt・node event・terminal state はすべて**この ID を使う**
(別名を作らない)。

- `shared_mount_repository_reachability_not_eliminated`
- `execution_mediation_incomplete`
- `guard_snapshot_to_release_race_not_eliminated`
- `approval_receipt_trust_root_absent`
- `repository_absence_not_proven_from_node`
- `budget_ledger_trust_root_absent`

### C-2. authorization token (A-10 / B-1 の実装形)

`t810_harness_schema.py` に `AuthorizationToken` (frozen dataclass) を置き、
`verify_launch_authorization(document, *, run_kind, preregistration_sha256, policy_sha256)
-> AuthorizationToken` だけがこれを構成できるようにする (`__init__` を経由した外部構成を
実質不能にするため、module 内 private sentinel を要求する)。
**effect を持つ低水準 adapter は `AuthorizationToken` 型の引数を必須にする** —
`_subprocess_scheduler`、`_subprocess_runner`、`publish_cancel`、marker/manifest の書込み経路、
`prepare_group`。`None` や dict は型で拒否する。fixture seam も token を要求する
(テストは `verify_launch_authorization` を通して token を得る)。

### C-3. repo 外判定 (A-7 / B-9)

`t810_harness_schema.py` に `assert_repository_external(path, *, repository_roots)` を置く。
`repository_roots` は **git common-dir から導出した全 worktree の realpath 集合**とし、
呼び手が渡す。coordinator・budget ledger・PBS `-o/-e`・work/output/control root・cwd の
すべてに同じ関数を適用する。node 側 wrapper は repository_roots を渡せないため
`repo_absence` の該当 boolean を **false 固定**とし、`repository_absence_not_proven_from_node`
を limitations に載せる (B-9 の裁定: 証明不能な boolean を true にしない)。

### C-4. prereg 由来の測定 argv (A-8 / B-4)

`canonical_benchmark_argv` と executable identity は **`VerifiedT810Preregistration` の projection
からのみ**導出する。`WrapperRequest` から受け取らない。runner policy は
`build_runner_policy(preregistration, *, executable_sha256)` のみで構成でき、
その digest を intent → manifest → wrapper request → node event へ束縛する。

### C-5. 実ファイル束縛 (A-3 / A-4 / B-3 / B-5 / B-7)

coordinator は config 埋め込み event を**受け取らない**。slot ごとの create-only JSONL を
work_root 下で監視し、**自分が読み取った瞬間**を単一 monotonic clock で刻む。
JSONL は sequence 連番・`previous_event_sha256` 連鎖・event 順序を検証し、
`node_receipt_sha256` は**実ファイル bytes の sha256 と照合**する。
presence は filesystem を lstat して expected set と比較して**再計算**する
(`presence_valid` の自己申告は入力として受け取らない)。

### C-6. 終端集約の順序 (A-5 / B-6)

completion verifier は **全 node の terminal state/reason を先に集約**し、
state 1/2/3 が 1 件でもあれば完了数判定へ進まない。`terminal_reduced` は
「脱落 1 件が state 1〜3 の理由を持たず、残り 12 件が全条件成立」のときだけ。
wrapper は **release 後の再検査 (依存 manifest・module list・trace・NUMA・第 2 process 走査) が
すべて成功した後にだけ** `start_ack` を書く。

### C-7. admission の最上流 deny (B-2)

coordinator の最上流で admission policy 全体を exact load し、
**ratifiable status が 1 つでも `ratified` でなければ、receipt 評価より前に deny** する。
guard/budget receipt は typed validator (schema_version・policy_sha256・phase・decision literal・
ledger after digest・`launch_intent_sha256`) を通す。

## fix の分割 (逐次)

| 巡 | 所有 | 閉じる所見 |
|---|---|---|
| fix-1 | `t810_harness_schema.py` + `t810_coordinator.py` (+ 両 test, coordinator fixture) | C-1〜C-3 の schema 側、C-5、C-6 の coordinator 側、C-7、A-1/A-2/A-3/A-4/A-5/A-6/A-7、B-1/B-2/B-3/B-5/B-8/B-10、B-12 (未使用面の縮約) |
| fix-2 | `t810_pbs_wrapper.py` + `t810_runner_policy.py` (+ 両 test, wrapper fixture) | C-2/C-3/C-4/C-6 の wrapper 側、A-8、B-4/B-6/B-7/B-9、A テスト節の cancel 第 2 確認の変異が生存する件、AST tripwire の対象拡大 |
| fix-3 | `t810_guard.py` + `t810_budget.py` + `t810_admission_v1.json` (+ 両 test) | C-1 の受信側、C-2 の guard/budget 側、C-3 の ledger、A-9、B-11 |

## テストへの共通要求 (A のテスト節への裁定。全 fix 子へ継承)

- **恒真テストの禁止。**production の表を import して同じ表から期待値を得ない。
  protocol 由来の literal は test 側に独立の fixture として書き下す。
- **変異が生きるテストにする。**特に cancel の第 2 確認は、**第 1 確認の時点では cancel が無く、
  ack 後に cancel が現れる**時系列 fixture で検査する (第 1 確認が mask しない形)。
- AST tripwire は本 wave の 6 module すべてを走査対象にする。
- 既存テストの期待値は、本裁定が要求する箇所以外変更しない。緩和・skip・xfail 化を禁じる。

## 規模と上限

fix は 3 巡を上限とする (`DW-O16`)。fix-1 が最大で、既存 coordinator の I/O 層の作り直しを含む。
**この裁定で閉じきれない残余は、段 7 で正直に「未達」と記録し、後続タスクへ送る。**
