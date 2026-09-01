結論は **現時点では NO-GO** です。受理枝のコードを先に land すると、正例が実 evaluator を通って発火しない dead branch になり、D841 の「consumer と同時結線」と D431 型の positive control 要求を満たせません。

以下は、P1〜P9 evaluator と実 witness が先に実在した後、T-434 を単一変更単位で実装するための file:line プランです。テストは実走していません。

## 1. 新事実を反映した設計判断

- N1: 無受領証で `generations=1..2` を維持する。現行値は [`p3_autonomous_workload_trial.py:143-144`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:143)。受領証は **3..10 だけ**を支配する。
- N1 への追加攻撃: `MAX_APPROVED_GENERATIONS` を単に 3 へ変えるだけで無受領証の 3 世代が開かないよう、C11 は今後 `cap >= 2` ではなく **receipt-free cap が exact 2** であることも pin する。provisional P1 をそのまま使うだけでは constant-only lift が残る。
- N2: Layer 3 は `layer3-material-report/v3` のまま、`runs.items.properties` に optional field を加える。現行 version と `required` は [`layer3_schema.json:22-34`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_schema.json:22) のまま。
- producer の `SCHEMA_VERSION` / `REPORT_SCHEMA_VERSION` も v3 のままとする。[`test_autonomous_trial_completeness.py:2914-2918`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_autonomous_trial_completeness.py:2914) の既存期待を変更しない。
- N3: C11 contract と evaluator を第 7 consumer として同時更新する。現在の pin は [`contract:436-476`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:436)、AST 判定は [`s8c_preregistration_evidence.py:2525-2569`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:2525)。

## 2. receipt schema v1 の確定表

実装先は新規 `orchestrator/campaign/cap_lift_receipt.py`。現行行番号は存在しないため、先頭から strict parser、sealed 型、git topology verifier の順に置く。

固定 path:

- receipt: `output/cap-lift/receipts/<receipt_raw_sha256>.json`
- witness: `output/cap-lift/witnesses/<witness_sha256>.json`

raw bytes は UTF-8、key sort、空白なし、一行 JSON + LF。raw SHA は LF を含めて計算する。

| field | v1 の型・語彙 | 出所と検証 |
|---|---|---|
| `schema_version` | const `izanagi-cap-lift-receipt/v1` | exact 一致。未知版拒否。 |
| `scope` | const `p3-autonomous-workload-trial` | D114 の 3 `generations` 入口だけ。注入 seam、直接 driver 反復、並行差替えは承認しない。 |
| `decision` | const `APPROVED` | 単独では証拠にしない。導入 commit A の topology と組でのみ有効。 |
| `target_revision` | lowercase 40 hex | receipt 導入 commit A の唯一親 G と exact 一致。 |
| `approved_max_generations` | exact JSON int、bool 禁止、`3..10` | 2 以下は receipt-free 領域なので拒否。10 は [`MAX_GENERATIONS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:143) と照合。 |
| `application_binding` | exact object: `origin_binding_sha256`, `run_configuration_sha256` は lowercase SHA-256、`generalized_cut_claimed` は exact bool | D156 V1 (a′) の revision・origin・運転構成・claim 有無の申請単位束縛。run はこの三値を再導出して一致必須。[P6 contract:187-192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md:187)。 |
| `prerequisite_statuses` | P1〜P10 を順番どおり一度ずつ持つ長さ 10 の array。各 row は exact `{id,status,evidence_sha256}` | P1〜P5・P7〜P9 は `SATISFIED` のみ受理。P10 は `HUMAN_RATIFIED` のみ。P6 の schema 語彙は `SATISFIED`,`NOT_CLAIMED`,`NOT_IMPLEMENTED`、ただし `NOT_IMPLEMENTED` は admission 拒否。 |
| P6 status の整合 | `SATISFIED` iff `generalized_cut_claimed=true`、`NOT_CLAIMED` iff false | どちらも意味的 accreditation が必要。4 値の P6 実行結果は receipt に格納しない。D150 の状態語と実行結果を混同しない。[P6 contract:19-28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md:19)。 |
| `p6_semantic_contract_sha256` | lowercase SHA-256 | 対象 revision の P6 契約 bytes を pin。 |
| `p6_accreditation_ref` | exact `{path,sha256}` | repo-relative canonical POSIX path。対象 revision の blob、record hash、`subject_revision_sha`、contract hash、`verdict=accredited` を照合。[P6 contract:156-177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md:156)。 |
| `ruling_ref` | exact object | `decision_kind=CAP_LIFT_APPROVAL`、`policy_version=izanagi-cap-lift-policy/v1`、`authority_decision_id`、固定 `policy_basis=[D156,D410,D828,D841]`、target/cap/witness の写し、D114(1) と D410 の supersede、`boundary_test_manifest_sha256` を持つ。写しは top-level と exact 比較。 |
| `witness_sha256` | lowercase SHA-256 | G に存在する固定 path の blob hash。status は witness の写しを信じず、P 別 evaluator が typed evidence から再導出する。 |

予約 field は置かない。ただし、次の二つは v1 を発行可能にする前提であり、現在は未定義である。

- P1〜P9 witness manifest の strict inner schema。
- P6 accreditation record の機械可読 exact format。

この二つを opaque data として許すと、設計メモが退けた「申請側の二つの写しが一致するだけ」に戻るため、未定義の間は sealed `VerifiedCapLiftReceipt` を発行しない。

## 3. 実効 cap と 3 入口

[`_validate_generation_budget():501-510`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:501) の直前に純関数を置く。

```text
_derive_effective_generation_cap(generations, verified_receipt):
    exact int と 1..MAX_GENERATIONS を検査
    receipt is None:
        effective_cap = MAX_APPROVED_GENERATIONS  # committed value は exact 2
    receipt exists:
        generations <= MAX_APPROVED_GENERATIONS なら拒否
        effective_cap = min(receipt.approved_max_generations, MAX_GENERATIONS)
    generations > effective_cap なら拒否
    return effective_cap
```

`_validate_generation_budget` は raw SHA を固定 path から読み、topology・witness・申請 conformance を検証した sealed objectを上の純関数へ渡す。環境変数、自動探索、latest receipt、provider 例外は作らない。

3 入口は以下で同じ純関数を通す。

- `_run_workload`: 現行 [`3717`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:3717)。site、campaign identity、provider 処理より前。
- `run_trial`: 現行 [`4397`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:4397)。launch admission [`4442`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:4442) と `run_root` 検査・作成 [`4522-4527`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:4522) より前。
- `main`: 現行 [`5064`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:5064)。build preparation [`5103-5118`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:5103) より前。

CLI は [`5028`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:5028) の直後に `--cap-lift-receipt-sha256` を追加し、`--max-generations` の default literal `1` は維持する。

SHA は `_campaign_for()` の `search_config` 構築 [`762-793`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:762) に `cap_lift_receipt_raw_sha256` として、receipt 利用時だけ追加する。これにより campaign ID preimage に入る。

## 4. 発効 topology

新規 `cap_lift_receipt.py` の verifier は、worktree file ではなく hardened git object を読む。

検査順:

1. `git -c core.useReplaceRefs=false rev-parse HEAD^{commit}` で H を捕捉。shallow repo、replace refs、grafts を拒否。
2. H の全 ancestry を `git rev-list --parents H` で列挙。
3. `git cat-file --batch-check` で全 commit の receipt path entry を調べ、値が absent または期待 blob OID のみであること、導入 commit A が一意であることを確認。
4. `git rev-list --parents -n 1 A` が exact `A G`。これで非 mergeかつ親 G が承認対象。
5. `git diff-tree --no-commit-id --name-status -r -M -C A` が exact `A\t<receipt-path>` の一行。receipt 以外の追加・変更・削除を拒否。
6. `git show -s --format=%B A` と `git -c trailer.separators=: interpret-trailers --parse` の両方で、`AI-Agent: none` が逐語一行かつ値 `none` 一件だけ。
7. receipt の `target_revision == G`。
8. exact-pin は `H == A` とする。A 自身の hash を receipt 内へ自己参照させず、descendant reuse も許さない。

既存の同型実装は [`s8b_ratified_freeze.py:450-515`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:450)、trailer 検査は [`546-570`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:546)、create-only 比較は [`t080_freeze_migration.py:1253-1268`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/t080_freeze_migration.py:1253) を写経せず再利用可能な最小形にする。

限界: `AI-Agent: none` は暗号学的本人確認ではない。悪意ある committer、侵害された host、dirty な実行 source はこの topology だけでは排除できない。保証は「運用上 push は人間」という trust root の範囲に限定する。

## 5. consumer 7 面の exact 述語

| 面 | 編集位置 | 新たに満たす既存 exact 述語 |
|---|---|---|
| 1. runbook | [`phase3-s8c-autonomous-trial-runbook.md:120-154`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:120)、[`238-246`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:238) | 1..2 は SHA 不要、3..10 は事前検証・CLI 引数・事後 journal/report/Layer 3 同一 SHA 確認。silent downgrade 禁止。 |
| 2. producer | [`p3...py:501-510`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:501)、3 入口、`_campaign_for:762-793` | exact built-in int、絶対範囲、receipt-free cap、receipt cap を分離。manifest の generation exact 比較 [`1258-1262`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1258) も維持。 |
| 3. journal | `run-start` 構築 [`4730-4762`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:4730) | 新 event は増やさないため `_EVENTS` 閉集合 [`completeness.py:47-57`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:47) は不変。receipt 利用時だけ `run-start.cap_lift_receipt` envelope。start/finish 一意・順序述語 [`2217-2235`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:2217) を維持。 |
| 4. supervisor report | report 構築 [`3523-3571`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:3523)、write [`3627-3659`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:3627) | `REPORT_SCHEMA_VERSION` は v3。journal/report の envelope exact 一致を追加。completeness 通過前に `_write_json_atomic` へ到達させない。無受領証 report の root key 集合は既存テスト [`8669-8709`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:8669) のまま。 |
| 5. Layer 3 | [`layer3_report.py:342-350`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:342)、[`623-677`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:623)、[`layer3_schema.json:29-64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_schema.json:29) | `runs.items.additionalProperties:false` のため `cap_lift_receipt` を properties に明示。optional のままで `required` を変更せず、schema v3 据え置き。`search_config.cap_lift_receipt_raw_sha256` から固定 repo root の receipt を再読し、全 run row に同一 envelope。 |
| 6. completeness | run-envelope [`2217-2293`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:2217)、search config [`830-865`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:830)、campaign-chain [`4814-4830`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:4814) | producer validator を呼ばず、独自 literal/schema/topology で receipt を再読。`_AUTONOMOUS_SEARCH_CONFIG_KEYS` [`176-181`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:176) に receipt 有無の二つの exact key setを定義。journal/report、report/search_config、receipt cap/budget、persisted/fresh Layer 3 を独立比較。[`fresh rebuild:4652-4684`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:4652)。 |
| 7. C11 | contract [`436-476`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:436)、evaluator [`2525-2569`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:2525) | contract の strict `_CONDITION_KEYS` / `_EVIDENCE_KEYS` / `_CONSUMER_KEYS` [`22-36`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:22) を維持。`field_paths` に receipt SHA 引数、純 cap 導出、3 入口を追加。AST は cap exact 2、各入口が receipt 引数を `_validate_generation_budget` へ渡すこと、validator が純導出を呼ぶことを確認。最終 status は従来どおり `EVIDENCE_UNDEFINED`。 |

`docs/phase3-8c-preregistration.md` は編集しない。正式系列は exact `G=2` [`91-95`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-8c-preregistration.md:91) なので receipt-free 集合内であり、T-435 所有を先取りしない。条件 11 の本文 [`279-284`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-8c-preregistration.md:279) も C11 evaluator の根拠として読むだけにする。

なお、`test_s8c_preregistration_evidence*.py` という名前のファイルは現 tree に 0 件。実在する関連テストは `test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_core.py`。

## 6. 既存テスト追随

### 期待値を変えずに済むもの

- generation 1・2 pass、3 reject: [`test_p3...:1042-1083`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:1042)。
- `run_trial` / direct / CLI の無受領証 3 拒否と副作用前停止: [`2408-2420`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:2408)、[`3104-3118`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:3104)、[`6148-6170`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:6148)。
- two-generation feedback 正例: [`4396-4460`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:4396)。
- completeness の budget 3 無受領証拒否: [`3031-3045`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_autonomous_trial_completeness.py:3031)。
- report/run-start version pin: [`2896-2932`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_autonomous_trial_completeness.py:2896)。
- Layer 3 v2/v3 legacy read、v3 version、run required 集合: [`1113-1130`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_layer3_report.py:1113)、[`1262-1282`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_layer3_report.py:1262)。
- C11 cap=1 negative と projection 不在 negative: [`3923-3938`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_s8c_preregistration_predicates.py:3923)、[`4010-4033`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_s8c_preregistration_predicates.py:4010)。

### fixture 追加で済むもの

`MAX_APPROVED_GENERATIONS=3` monkeypatch で 3 世代を通している次の 4 件は、期待 assertion を変えず、将来の real evaluator-backed receipt fixture を渡す。

- [`2033-2059`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:2033)
- [`2273-2308`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:2273)
- [`2311-2342`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:2311)
- [`2345-2376`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:2345)

C11 の `TOKEN_ONLY_C11` [`979-1000`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_s8c_preregistration_predicates.py:979) は receipt 引数と純導出 call を含む fixture に拡張するが、最終期待 `EVIDENCE_UNDEFINED` は変えない。

### 新規テスト

- 新規 `test_cap_lift_receipt.py`: canonical JSON、全 field 型、固定 path、全 topology 条件、history mutation、P status 再導出、P6 conformance。
- producer: 3 入口の missing/fake/stale receipt、副作用前拒否、cap 3 の 3 pass / 4 reject、receipt を 1・2 に付ける過剰指定拒否。
- completeness: producer validator を monkeypatch で恒真化しても偽 receipt を拒否する独立性、journal/report/search_config/Layer 3 の各一面欠落・不一致。
- Layer 3: v3 据え置き、`required` 据え置き、optional envelope の正負、古い v2/v3 無 envelope の後方互換。
- C11: committed cap=3 の constant-only lift、3 入口の各一呼出し除去、receipt 引数落ち、純導出 call 落ち。

既存期待値の反転・緩和・skip・削除は不要。`REPORT_SCHEMA_VERSION` を v4 に上げる案だけは既存 version pin の変更を要するため採らない。

## 7. 到達可能性

### (a) 受理枝を実装してよいか

source を書くこと自体は可能だが、**現時点で採用・land してはいけない**。

理由:

- 設計正本自身が P evaluator と実 artifact の land を再開条件にしている。[`design-v2.md:17-24`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md:17)。
- P1〜P9 を `SATISFIED` へ再導出する独立 evaluator がない。
- witness/status の自己一致だけでは恒真 evaluator を拒否できない。
- receipt branch を一度も通さないまま consumer wiring を land すると、D841 が禁止した「あるが効かない保証」になる。

### (b) 実体を stub せず正例を発火できるか

現在はできない。

次はいずれも正例にならない。

- receipt/witness に `SATISFIED` を手書きする。
- evaluator や sealed object constructor を monkeypatch する。
- `MAX_APPROVED_GENERATIONS` を 3 へ monkeypatch する。
- generation 2 で envelope だけ運ぶ。cap-lift 受理枝を通っていない。

正例を置けるのは、P1〜P9 evaluator と P6 accreditation checker が land した後、temp git repo で実 evidence を生成し、G と create-only A を実 commit し、production evaluator をそのまま通す場合だけ。

### (c) 発火不能なまま採用してよいか

採用すべきでない。代わりに今行うべきことは:

- production code、schema、dead CLI flagを追加しない。
- 現行の無受領証 1..2 受理、3..10 拒否を維持する。
- P evaluator・witness schema・P6 accreditation format の実装を先行依存として起票する。
- それらが成立した後、このプランの A/B/C 全単位を一つの commit にまとめる。

## 8. 編集 path 所有の素集合

これらは作業分担単位であり、別々に land しない。

| 単位 | 所有 path | 内容 |
|---|---|---|
| A: receipt core | 新規 `orchestrator/campaign/cap_lift_receipt.py`、新規 `orchestrator/tests/test_cap_lift_receipt.py`、必要なら新規 test support 1 ファイル | strict schema、sealed 型、fixed-path reader、topology、P evaluator adapter。 |
| B: producer + completeness | `p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py`、対応する既存 test 2 本 | 3 入口、identity SHA、journal/report envelope、独立 run-envelope/campaign-chain 再検証。 |
| C: Layer 3 + C11 + runbook | `layer3_report.py`、`layer3_schema.json`、`s8c_preregistration_evidence.py`、contract JSON、`test_layer3_report.py`、preregistration predicates/invariant tests、runbook | v3 optional run property、fresh rebuild、C11 exact field/call pin、運用記述。 |

依存順は `P evaluator群 → A → B と C → B/C cross-integration tests → 単一 commit`。B と C は path 上は並行可能だが、最終検査前には両方揃える。

## 9. 変異事前登録

### 負例

| 変異 | 殺す受理判定 |
|---|---|
| receipt SHA 欠落、偽 SHA、別 filename | fixed-path content addressing |
| duplicate key、未知 key、非 UTF-8、非 canonical bytes | strict parser |
| `approved_max_generations` が 2、11、bool | receipt schema と絶対 cap |
| receipt cap=3 で generations=4 | pure effective-cap 判定 |
| target revision 差替え | A の唯一親との一致 |
| A を merge commit 化、wrong parent | 非 merge・親 G |
| A で別 file も変更 | create-only exact diff |
| `AI-Agent: none` 欠落、重複、表記揺れ | raw + parsed trailer 二重検査 |
| receipt の削除再導入、同 path 別 bytes | 一意導入・履歴 immutability |
| witness bytes drift | `witness_sha256` |
| P1〜P5/P7〜P9 の一つを非 SATISFIED | 全前提合接 |
| P4 を非適用扱い | D150 の無条件性 |
| P6=`NOT_IMPLEMENTED` | D150 fail-closed |
| `NOT_CLAIMED` だが claim=true、config/origin drift | D156 application conformance |
| accreditation subject/contract/hash drift | P6 accreditation |
| `MAX_APPROVED_GENERATIONS=3` だけ変更 | C11 exact receipt-free cap=2 |
| 3 入口の一つから validator call または receipt 引数を削除 | C11 entrypoint boundary |
| journal/report の片側 envelope 欠落・変更 | run-envelope exact 比較 |
| search_config SHA 欠落・変更 | exact key set、campaign identity |
| Layer 3 run envelope の欠落・変更 | schema + fresh rebuild comparison |
| completeness を producer validator 呼出しへ差替え | independent recomputation test |

### 正例

| 正例 | 殺す過剰拒否 |
|---|---|
| receipt 無し generation 1 | 現行最小受理集合の縮小 |
| receipt 無し generation 2 | N1 で最重要の現行受理集合縮小 |
| real evaluator-backed cap=3 receipt で generation 3 | receipt branch の dead/no-op 化 |
| 同 receipt で journal/report/search_config/Layer 3 が同一 SHA | consumer 一面取り残し |
| accredited `NOT_CLAIMED`、claim=false、同 revision/origin/config | D156 V1 (a′) の免責経路の過剰拒否 |
| 古い v2/v3 Layer 3、cap field 不在 | D828 の後方互換破壊 |
| current v3 Layer 3、optional envelope 有り | v4 を誤って必須化する変異 |

real evaluator-backed 正例は現時点では登録候補に留まり、実行可能とは記録しない。

## 総括

骨子は、receipt-free cap を exact 2 に固定し、3..10 だけを content-addressed receipt が支配し、同一 envelope を journal・report・Layer 3へ、SHA を campaign identity へ投影し、completeness と C11 が独立に再検証する形です。Layer 3、run-start、report の版はすべて据え置きます。

最大の未解決点は schema の書式ではなく、P1〜P9 evaluator と実 witness が存在せず、sealed receipt の正例が到達不能なことです。

親が段 4 で裁定すべき択一は次です。

- **推奨: WAIT** — P evaluator・witness schema・P6 accreditation checker の land 後に、A/B/C を一つの変更単位で実装する。
- 非推奨: 今すぐ rejection-only/dead acceptance branch を land する。これは正例なしで D841/D431 型の恒真保証を作る。