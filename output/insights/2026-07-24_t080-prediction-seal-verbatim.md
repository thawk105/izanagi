# T-080 selector 予測封印 — 逐語凍結 (codex plan + 敵対相談 2 + 敵対レビュー 2)

本 wave (2026-07-24) の各段 codex 逐語。gpt-5.6-sol / reasoning=max / read-only。
F34: 三軸 conjunction 機械検査を通してから凍結 (hit あれば erratum で defang)。

---
## 段2: プラン起草 (codex, read-only)

# T-080 selector 予測封印 実行プラン

結論は次の3点です。

- commit (4) では、commit (1) とは別に `FROZEN_MANIFEST` を再更新し、prediction と実在する `selector-runs` 全件を sha256 pin する必要があります。
- `s8b_ratified_freeze` の production run は本 wave では不要です。floor 実測後の v2 批准・launch lane です。
- selector へ渡るのは workload descriptor と固定候補だけで、floor 測定値・protocol bytes/hash は渡りません。

`floor_protocol.json` の内容は一度も開いていません。

## 1. 実行順プラン

### 0. clean-tree blocker を先に解消

現在の実測状態は `HEAD=c8cbd17c111b965b8a0c36bf9e25b39ae32f8645` ですが、次が untracked です。

```text
?? docs/handoff/2026-07-24-t080-prediction-seal.md
```

seal は `selector-runs/` 外の untracked も拒否します。[s8b_prediction_runner.py:1271](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1271)

親が所有者・内容を確認して保存／吸収したうえで、commit (1) 後に次が空になる状態を作る必要があります。

```bash
git status --porcelain=v1
```

この handoff を無断で commit (1) に混ぜるのは避けます。

### 1. commit (1): floor protocol の manifest pin

対象は [test_frozen_artifacts.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:2) のみです。現在の map は8件で、列挙済み path だけを検査します。[test_frozen_artifacts.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:25)

具体差分は次の形です。

```diff
- exact path→sha256 ... s1 freeze 2 本
- + v1 holdout freeze + 2026-07-16 の裁定資料 2 本と相談逐語 3 本を列挙する
+ exact path→sha256 ... s1 freeze 2 本
+ + v1 holdout freeze + floor protocol + 2026-07-16 の裁定資料 2 本と
+ 相談逐語 3 本を列挙する

 # - v1 holdout freeze (v2 連鎖の trust root、C2-5)
+# - floor protocol (floor データ閲覧前の盲検 protocol trust root)

 FROZEN_MANIFEST = {
     ...
     "output/s8b-freeze/holdout_freeze.json":
         "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688",
+    "output/s8b-freeze/floor_protocol.json":
+        "261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac",
     ...
 }

-assert len(FROZEN_MANIFEST) == 8, "凍結対象は 8 件 (s1 2 + v1 1 + 裁定資料 2 + 逐語 3)"
+assert len(FROZEN_MANIFEST) == 9, \
+    "凍結対象は 9 件 (s1 2 + v1 1 + protocol 1 + 裁定資料 2 + 逐語 3)"
```

sha256 は brief の承認値を使用し、protocol 内容は読まないまま pin します。

commit 前後のゲート:

```bash
python3 orchestrator/tests/test_frozen_artifacts.py
git add -- orchestrator/tests/test_frozen_artifacts.py
git diff --cached --name-only
git commit ...
git status --porcelain=v1
```

commit (1) も AI が実質的に編集するため、`AI-Agent: none` ではなく構造化 AI trailer が必要です。[ai-provenance.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/ai-provenance.md:12)

### 2. commit (1) 直後の HEAD で seal

commit 後の HEAD を固定します。

```bash
PRE_ORACLE_HEAD="$(git rev-parse HEAD)"
test -n "$PRE_ORACLE_HEAD"
test -z "$(git status --porcelain=v1)"
PYTHONPATH=orchestrator python3 -m campaign.s8b_prediction_runner seal \
  --provider claude-headless \
  --pre-oracle-head "$PRE_ORACLE_HEAD"
```

seal は ancestry ではなく、実行時の `HEAD == --pre-oracle-head` を要求します。[s8b_prediction_runner.py:1392](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1392) その commit の protocol blob を読み、承認定数からの再導出 bytes と完全一致させます。[s8b_prediction_runner.py:1418](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1418)

正常時は4 agent call・2 static cell・6行 prediction となり、`.lock` は削除されます。[test_s8b_prediction_runner.py:1262](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_prediction_runner.py:1262)

claim-crash 時の「再試行せず」は、正確には「同じセルを再呼出ししない」です。prediction を作るには、HEAD を動かさず同じコマンドを再起動して残りの未着手セルを処理する必要があります。claim 済みセルは `claimed_missing` として skip されます。[s8b_prediction_runner.py:823](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:823)、[test_s8b_prediction_runner.py:1196](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_prediction_runner.py:1196)

literal に CLI 再起動まで禁止すると `selector_predictions.json` は生成されないため、step (3)/(4) へ進めません。

### 3. 独立 verify

```bash
PYTHONPATH=orchestrator python3 -m campaign.s8b_selector_freeze verify \
  --path output/s8b-freeze/selector_predictions.json
```

CLI は default の v1 holdout freeze を read-once し、固定 sha256 と照合します。[s8b_selector_freeze.py:989](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:989)、[s8b_selector_freeze.py:1001](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:1001)

### 4. commit (4): prediction evidence の manifest pin と即 commit

seal 後に、内容を判断材料として読まず、実在する生成ファイルすべての sha256 を採取します。`FROZEN_MANIFEST` に次を追加します。

- `selector_predictions.json`
- `selector-runs/journal.jsonl`
- 全 `payload_*.json`
- journal 宣言済みの全 `envelope_*.json`
- resolved cell の全 `raw_*.txt`

正常4セル時の最終件数は23件です。

```diff
+# - selector prediction 1 本 + selector-runs 証拠一式
...
+    "output/s8b-freeze/selector_predictions.json": "<seal後sha256>",
+    "output/s8b-freeze/selector-runs/journal.jsonl": "<seal後sha256>",
+    ... 実在する12 cell artifact ...
...
-assert len(FROZEN_MANIFEST) == 9, ...
+assert len(FROZEN_MANIFEST) == 23, \
+    "凍結対象は 23 件 (s1 2 + v1 1 + protocol 1 + selector prediction 1 + selector-runs 13 + 裁定資料 2 + 逐語 3)"
```

claim-crash なら件数を23へ無理に合わせず、実在する exact set に合わせます。一般式は次です。

```text
最終件数 = 10 + selector-runs 配下の正常 regular-file 件数
```

- envelope 前に missing となった1セル: 通常21件
- envelope 記録後・raw 前に missing となった1セル: 通常22件

manifest test は未列挙ファイルを自動発見しないため、journal 宣言集合とディレクトリ実在集合を手動でも突き合わせる必要があります。[test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:61)、[s8b_prediction_runner.py:1298](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1298)

## 2. commit (4) の git add パス

正常4 agent cell 時の必須一覧です。

```text
orchestrator/tests/test_frozen_artifacts.py
output/s8b-freeze/selector_predictions.json
output/s8b-freeze/selector-runs/journal.jsonl
output/s8b-freeze/selector-runs/payload_rr20_on.json
output/s8b-freeze/selector-runs/envelope_rr20_on.json
output/s8b-freeze/selector-runs/raw_rr20_on.txt
output/s8b-freeze/selector-runs/payload_rr20_swapped.json
output/s8b-freeze/selector-runs/envelope_rr20_swapped.json
output/s8b-freeze/selector-runs/raw_rr20_swapped.txt
output/s8b-freeze/selector-runs/payload_rr80_on.json
output/s8b-freeze/selector-runs/envelope_rr80_on.json
output/s8b-freeze/selector-runs/raw_rr80_on.txt
output/s8b-freeze/selector-runs/payload_rr80_swapped.json
output/s8b-freeze/selector-runs/envelope_rr80_swapped.json
output/s8b-freeze/selector-runs/raw_rr80_swapped.txt
```

claim-crash 時も `payload_<missing-cell>.json` は残します。存在しない raw/envelope だけを一覧から除き、存在する envelope は missing cell でも追加します。

明示的な非対象:

- `selector-runs/.lock`: transient。成功時に削除必須
- `.selector_predictions.json.*.tmp`: atomic write の一時ファイル
- `selector-runs/cell-*.json`: test fixture 名であり production 出力ではない
- repo 外の neutral cwd / `empty-mcp-config.json`
- `floor_protocol.json`: commit (4) では変更なし

T-080 の状態更新も同じ completion commit に含める場合は、process 文書として別途 `docs/phase3.md:91` と worklog 末尾を追加します。これらは seal の write-path ではありません。

## 3. P1–P6 判定

### P1 — real

commit (4) には新たな `FROZEN_MANIFEST` edit が必要です。step (1) の loose な再掲ではありません。

根拠:

- worklog が protocol pin commit と、prediction evidence + manifest update commit を分離しています。[worklog.md:245](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/worklog.md:245)
- D79 は protocol commit 直後と prediction commit 同梱の「逐次 pin」を明記します。[decisions.md:3288](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/decisions.md:3288)
- `FROZEN_MANIFEST` は literal map であり、自動追加機構はありません。
- `s8b_ratified_freeze` は後に committed `H` の evidence を検証するだけで、manifest を書きません。[s8b_ratified_freeze.py:2455](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2455)

prediction、journal、envelope、raw は時刻・session・LLM応答を含むため、sha256 は seal 後採取で正しいです。payload も同じ採取手順へ揃えるのが安全です。

### P2 — real。ancestry 検査という部分は refuted

commit (1) と commit (4) は別 commit で、`--pre-oracle-head` は commit (1) 直後の HEAD です。

seal 時:

- current HEAD との完全一致
- `pre_oracle_head:floor_protocol.json` blob の取得
- journal run header への記録
- prediction document への記録

を行います。[s8b_prediction_runner.py:1401](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1401)、[s8b_prediction_runner.py:1448](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1448)

step (3) の verifier は commit が解決可能かだけを検査し、HEAD一致・ancestor は検査しません。[s8b_selector_freeze.py:158](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:158) ancestor 検査は後続 ratified launch lane にあります。[s8b_ratified_freeze.py:2544](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2544)

### P3 — refuted

本 wave で ratified production run は不要です。

seal 自身が prediction の disk reload verify と selector-runs exact declaration 検査まで行います。[s8b_prediction_runner.py:1462](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1462)

一方、ratified loader は active v2 generation、approval/pointer、floor source 等を前提とします。[s8b_ratified_freeze.py:1198](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:1198) active pointer 不在は `no-active` です。さらに commit 前の untracked prediction namespace は `namespace-dirty` で拒否されます。[s8b_ratified_freeze.py:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:346)

### P4 — real

production write-path は上記一覧です。

生成箇所:

- journal: [s8b_prediction_runner.py:260](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:260)
- `.lock`: [s8b_prediction_runner.py:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:735)
- payload: [s8b_prediction_runner.py:847](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:847)
- envelope: [s8b_prediction_runner.py:1145](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1145)
- raw response: [s8b_prediction_runner.py:881](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:881)
- prediction: [s8b_prediction_runner.py:965](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:965)
- lock 削除: [s8b_prediction_runner.py:1485](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1485)

### P5 — real。盲検はコード上維持される

selector stdin は次の経路だけです。

```text
holdout_freeze["holdouts"][descriptor_source]
  → descriptor_for_holdout()
  → build_selector_payload()
  → canonical JSON stdin
```

- descriptor は `ycsb/records/threads` の明示射影だけです。[s8b_descriptor.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_descriptor.py:85)
- payload top-level は `schema_version/descriptor/candidates` の3キー固定です。[s8b_selector_input.py:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_input.py:102)
- runner はその payload bytes だけを stdin に渡します。[s8b_prediction_runner.py:1125](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1125)
- protocol は HEAD blob照合と journal binding にだけ使われ、payload source 集合にも入りません。[s8b_prediction_runner.py:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:97)
- repo 外 cwd、toolsなし、空MCP、env allowlistです。[s8b_prediction_runner.py:1060](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1060)

非漏洩回帰も、holdout名・arm・binding・provenance の排除、binding変更の payload 非干渉、`measured_tps`/`winner` 注入拒否を固定しています。[test_s8b_selector_input.py:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_selector_input.py:74)、[test_s8b_selector_input.py:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_selector_input.py:117)

### P6 — real

step (3) の入力前提:

- `--path` の prediction JSON
- default v1 `holdout_freeze.json` の実在と固定 sha256
- prediction が記録した5 source file の実在・sha256一致
- `pre_oracle_head` が同 repo で commit に解決可能
- resolved row が参照する raw response file
- missing row は raw/provenance/result 全 null

検査内容:

- duplicate key／非有限値拒否
- top-level exact schema
- `body_sha256`
- selector basis、derangement、static default、execution policy
- canonical 6 cell と tagged union
- choice→binding の信頼側再導出
- source file hashes
- raw response の strict reparse
- swapped expectations 再導出

中心実装は [s8b_selector_freeze.py:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:667) と [s8b_selector_freeze.py:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:879) です。

この verify は journal、payload、envelope、protocol blobを検査しません。journal 相互束縛は seal と後続 ratified lane、bytes不変は commit (4) の manifest pin が担います。

## 4. 親が確認すべき前提・落とし穴

- 現在の untracked handoff を解消しない限り seal は開始できません。
- `PRE_ORACLE_HEAD` はcommit (1) 後に採取し、resume 時も同じ値を使います。
- seal 成功後の namespace dirty は期待状態です。commit前に `load_ratified_freeze` 等を走らせないこと。
- claim-crash では selector-runs を削除しません。同セル再呼出しを避けつつ seal CLI を再開します。
- `.lock` が seal 成功後も残る、または undeclared artifact がある場合は commit禁止です。
- prediction は create-onlyです。書込み後 verify failure になった場合、盲目的な削除・再生成はせず調査します。
- invalid LLM output は `choice_id=null` の正規結果であり再試行しません。
- commit (4) では actual selector-runs set と manifest key set を完全一致させます。
- commit (4) は structured AI trailer を付け、commit後に provenance checkerを通します。

受入で緑にすべき中心テスト:

- `test_frozen_artifacts_match_manifest`
- `test_manifest_shape_is_exact`
- `test_seal_rejects_protocol_blob_not_equal_to_rederived_bytes`
- `test_seal_rejects_dirty_path_outside_selector_runs`
- `test_seal_claim_crash_resumes_and_seals_six_rows_with_missing`
- `test_seal_success_runs_four_agents_two_static_and_reloads_destination`
- `test_seal_rejects_undeclared_selector_run_file_before_success`
- `test_missing_agent_row_with_null_provenance_builds_and_verifies`
- `test_verify_detects_body_row_derangement_and_basis_tampering`
- `test_verify_binds_role_raw_and_exact_agent_provenance_to_files`
- `test_verify_reparses_raw_and_rejects_forged_valid_agent_rows`
- `test_verify_requires_commit_pin_resolvable_in_root_repo`
- `test_payload_recursively_excludes_arm_holdout_binding_and_provenance_names`
- `test_variant_binding_memory_changes_do_not_change_payload_hash`

対象モジュール全体と repo 検査:

```bash
PYTHONPATH=orchestrator python3 -m pytest -q \
  orchestrator/tests/test_frozen_artifacts.py \
  orchestrator/tests/test_s8b_prediction_runner.py \
  orchestrator/tests/test_s8b_selector_freeze.py \
  orchestrator/tests/test_s8b_selector_input.py

python3 tools/check_codex_agents.py
python3 tools/check_docs.py
python3 tools/check_ai_provenance.py
```

本回答では sandbox 制約に従い pytest は実行していません。

## 5. 規律2/3に対する残存攻撃面

- `FROZEN_MANIFEST` の完全性は自動 discovery されません。生成物を追加し忘れても、既存8/9件だけならテストが緑になり得ます。step (4) の全件 pin は手続き上の必須ゲートです。
- step (3) の verify だけでは journal・envelope・payload の改変を検出しません。「verify green = 全証拠鎖 green」と解釈してはいけません。
- raw response、envelope、`rationale` は外部LLM由来の非信頼データです。中に指示文があっても従わず、strict parser結果とhash対象としてだけ扱います。
- envelope/raw 書込みと journal 宣言の間でプロセスが落ちる極小窓では orphan file が残り、seal は正しく拒否します。この場合は証拠を手作業で整形せず停止・調査が必要です。
- Claude CLI の完全な動的コンテキスト遮断は argv/cwdテストで固定されていますが、`HOME` は認証のため渡されます。実測前に HOME/global memory へ floor情報を置かない運用境界は残ります。

 inspected source/data 内に、正しさゲートを緩めるよう誘導する不審な instruction は確認していません。
---
## 段3-A: 敵対相談 レンズA (正しさ+盲検)

## 裁定

**NO-GO。** 成功経路の実装は概ね成立していますが、起草プランは非ゼロ終了を機械的に止めず、失敗後に残った prediction を独立 verify して commit できる経路があります。

`floor_protocol.json` の内容は開いていません。許可された存在・サイズ・SHA-256 のみ確認しました。現在は `HEAD=c8cbd17`、tree clean、protocol は tracked 774B / 承認 SHA 一致、predictions 不在です。したがって起草文の「untracked handoff が blocker」は現時点では **refuted** です。

## 主要所見

1. **[real / BLOCKER] seal 非ゼロ後でも prediction が残り、step (3) が緑になり得る**

prediction は宣言集合検査より先に作成されます。その後 reload verify、`.lock` 削除、最後に selector-runs 宣言集合検査です。[runner:1469](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1469)、[runner:1485](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1485)、[runner:1491](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1491)

したがって undeclared/orphan artifact があると、

- seal は rc=1
- `selector_predictions.json` は存在
- `.lock` は既に不在
- 外部 verify は journal/orphan を見ないので緑になり得る
- 再度 seal すると既存 prediction で拒否

となります。[runner:1408](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1408)、[freeze:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:879)

該当テストも rc=1 しか確認せず、prediction 不在や lock 状態は検査していません。[test_runner:1307](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_prediction_runner.py:1307)

**step (3)/(4) は seal の rc=0 と sealed JSON 出力を明示確認した場合だけ到達可能にする必要があります。**

2. **[real / BLOCKER] shell の「ゲート」が後続コマンドを止めない**

起草ブロックには `set -euo pipefail` も `&&` もありません。したがって、

```bash
test -z "$(git status --porcelain=v1)"
PYTHONPATH=... seal ...
```

で `test` が失敗しても通常 shell は seal を実行します。commit (1) の manifest test、stage 一覧、commit も同様です。`git diff --cached --name-only` と `git status` は表示するだけで assertion ではありません。

これは軽微ではありません。内部 clean gate は selector-runs 配下の全 untracked を許します。[runner:1271](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1271) 既存の自己整合 journal は受理され、claim 済みセルは呼び出されません。[runner:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:377)、[runner:823](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:823)

つまり fresh-run clean 検査を黙って通過すると、事前作成された all-missing journal を「seal 実走由来」として封印できる残余があります。

3. **[real] fresh run と claim-crash resume の preflight が矛盾する**

fresh run の完全 clean 検査は正しい一方、claim-crash 後は `.lock`、journal、payload が untracked なので同じ `test -z git status` は必ず失敗します。

CLI 再起動自体は **retry ではありません**。claim 済みセルを skip し、未着手セルだけ進めるのが実装契約です。[runner:840](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:840)、[test_runner:1196](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_prediction_runner.py:1196)

したがって分岐を明記すべきです。

- 初回: tree 完全 clean、selector-runs/prediction 不在
- resume: 同一 HEAD、prediction 不在、selector-runs 外に dirty なし。当該 claim セルは再呼出し禁止
- prediction が既にある非ゼロ終了: resume 禁止、削除・再生成もせず停止

4. **[real/partial] P5 の「漏洩経路なし」は広すぎる**

明示的 stdin 射影は成立しています。payload は descriptor と固定候補だけで、provider はその canonical bytes だけを stdin に渡します。[selector_input:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_input.py:102)、[runner:1125](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1125)

しかし完全な blinding はコードだけでは証明されません。

- 実 HOME を必須で引き継ぐ。[runner:1089](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1089)
- 実行体は PATH から解決した任意の `claude` で、SHA は記録するだけ。承認済み値との照合はない。[runner:1045](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1045)
- テストは fake runner に渡した argv/env を確認するだけで、実際の ambient context 不在は検査しない。[test_runner:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_s8b_prediction_runner.py:525)

よって P5 は「**信頼済み Claude 実行体かつ HOME/global memory に floor 情報がない条件下で real**」。無条件の「経路なし」は refuted です。

5. **[real/partial] P6 verify は意味検証として実効的だが、seal provenance の verifier ではない**

実効的な検査はあります。body hash、basis、canonical cell、binding 再導出、raw strict reparse は恒真ではありません。[freeze:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:667)、[freeze:879](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:879)

一方で step (3) 単独では次を証明しません。

- `pre_oracle_head` は commit に解決できるだけ。[freeze:158](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:158)
- source path は自己申告で、正規5 path との一致を検査しない。[freeze:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:398)
- missing 行は journal/claim を見ずに受理され、raw 再 parse も skip される。[freeze:482](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:482)、[freeze:899](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:899)
- session ID 一意性、envelope、実行体、protocol blob は検査しない。

D79 自身も prediction↔journal と pre-oracle blob 照合の欠如を残余として記録しています。[decisions:3288](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/decisions.md:3288)

したがって「semantic verify は real」「実際に4 callしたことの独立証明は refuted」です。

6. **[real] commit (4) の closure が手動検査のまま**

P1 の「prediction と全 selector-runs を pin」は正しいです。正常時23件という算術も正しいです。

ただし現 manifest test は列挙済み key だけを hash 検査し、未知ファイルを発見しません。[test_frozen_artifacts:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:61) `len()` も完全性ではなく、任意の同数集合で通ります。[test_frozen_artifacts:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:75)

commit (4) には少なくとも以下を fail-closed assertion にする必要があります。

- seal rc=0
- `.lock` と prediction temp 不在
- actual selector-runs regular-file 集合 = journal 宣言集合 = manifest の selector-runs key 集合
- staged path 集合が期待集合と完全一致
- manifest test 成功
- commit 後の tree clean
- committed HEAD に対する verify/関連テスト成功

namespace-clean/ratified 検査を commit 前に走らせない点は維持すべきです。

7. **[real / 残余] R3 resume が成立する crash 範囲は限定される**

R3 resume が安全に成立するのは、durable claim と parse 可能な journal が残り、undeclared artifactや prediction がない場合です。

- journal append は途中断片を自動修復せず strict parse 拒否。[runner:267](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:267)
- artifact 書込み中 crash は partial/orphan file を残し得る。[runner:676](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:676)
- prediction temp は `delete=False` で、hard crash では `finally` cleanup に到達しない。[freeze:921](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:921)
- flock は `drive_journal` 終了時に解放され、prediction/commit まで保持されない。[runner:900](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:900)

これらは削除して再試行する分岐ではなく、停止・保存・調査分岐です。「seal と commit は原子的」は実装上の事実ではなく、単一運用者による手続き上の critical section と表現すべきです。

## P1–P6 再裁定

| 命題 | 裁定 |
|---|---|
| P1: commit (4) で prediction + selector-runs 全件を manifest pin | **real**。正常時23件も正しい。ただし discovery の機械化が必要 |
| P2: commit (1)/(4) 分離、pre-oracle=commit (1) HEAD | **real**。ancestry 検査という説明だけ refuted |
| P3: 本 wave で ratified production run 不要 | **real**。起草文の「P3 — refuted」はラベル逆転 |
| P4: git add は全 production write-path | **real on successful seal**。失敗時の orphan/tmp を通常一覧へ混ぜてはならない |
| P5: floor 値は selector に混入しない | **partial**。明示 stdin は real、HOME/実行体まで含む無条件保証は refuted |
| P6: verify は実効的 | **partial**。prediction 意味検証は real、seal実行・journal・protocol provenance 証明は refuted |

最小修正は、全コマンド列を fail-fast にし、fresh/resume/post-write-failure の三分岐を明文化し、seal rc=0 を step (3) の到達条件にし、commit (4) の staged/manifest/actual 集合を機械的に完全一致させることです。
---
## 段3-B: 敵対相談 レンズB (freeze-pin+consumer)

## 判定

**条件付き NO-GO。** 「正常時 23 件を全 pin」という結論自体は安全側ですが、現案には次の2つの実効性の穴があります。

### 1. real — git add 漏れでも manifest test は緑になれる

`test_frozen_artifacts_match_manifest` は worktree の実ファイルを直接読むだけで、index／HEAD に入っているか検査しません。[test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:61)

したがって、例えば raw 1本を `git add` し忘れても、

- untracked raw は worktree に残る
- manifest test はその raw を読んで緑
- commit 自体には raw が入らない

という偽緑が成立します。commit (4) には次が必須です。

- evidence を先に index へ stage
- manifest の hash は可能なら worktree でなく staged blob から採取
- commit 前に staged path 集合を exact 比較
- commit 後に `git status --porcelain=v1 --untracked-files=all` が空
- manifest の新規全 path が `HEAD` の `100644 blob` として実在し、HEAD blob の SHA-256 が literal と一致

手書き15 pathより、`.lock`／tmp 不在を確認してから `output/s8b-freeze/selector-runs/` を明示 pathspec として stageし、staged exact-set を検査する方が漏れにくいです。

### 2. real — ratified consumer は payload bytes を再 anchor しない

後続 `_selector_evidence_exempt_exact()` は payload について、journal と prediction row の「path/hash文字列」が一致することしか検査しません。[s8b_ratified_freeze.py:2649](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2649)

raw と envelope は実際に H blob／worktree bytes を読み、宣言 hash と照合します。[s8b_ratified_freeze.py:2677](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2677)、[s8b_ratified_freeze.py:2692](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2692)

payload は意図的に scan exemption から外されていますが、「scanされる」ことは「宣言 SHA と一致する」ことではありません。無害な別 bytes への置換は scan を通過できます。

したがって選択肢は次の二つです。

- 本 waveを実行専用のままにするなら、起草案どおり **payloadを含む全 selector-runs を FROZEN_MANIFEST に直接 pin**する。
- production consumer単独で完全閉鎖を主張するなら、payloadを H/worktreeから読み、claim hashと照合した上で、exemptionには加えず通常scanへ残すコード修正が必要。

前者でも `FROZEN_MANIFEST` は production consumerから読まれないため、「production trust chainが自己完結した」とは書けません。「Git＋毎commitのliteral testで歴史的変更を防ぐ」が正確です。

## pin 集合の裁定

- predictions のみ: **refuted**。prediction schemaはjournalを束縛しません。
- predictions＋journal: **最低限必要**。D79も逐次pinを要求しています。[decisions.md:3288](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/decisions.md:3288)
- raw/envelope: journalから推移的に束縛され、ratifiedもbytesを検査するため直接pinは防御的重複。ただし追加して問題ありません。
- payload: 現ratified実装の穴を補うため、直接pinする実益があります。
- 結論: **現コードを変えないなら、実在する selector-runs 全件pinが妥当**です。

件数も正しいです。

- commit (1): 9件
- 正常時 commit (4): `8 + protocol 1 + prediction 1 + selector-runs 13 = 23`
- 一般式: `10 + selector-runs配下の実在通常ファイル数`
- 1セルがenvelope前にmissing: 21
- envelope後・raw前にmissing: 22

時刻・session・LLM応答によりhashが非決定的でも、seal後にcreate-only成果物の実hashをliteral化するため exact manifestとは矛盾しません。**23を先行固定せず、実在集合確定後に件数を決める**点だけ必須です。

## consumer 波及

| 面 | 判定 |
|---|---|
| `FROZEN_MANIFEST` | productionから参照されず、実行consumerは当該testだけ。更新必要 |
| official preflight | 固定4件＋journal宣言payload/raw/envelopeを動的構成済み。更新不要。[s8b_floor_campaign.py:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_floor_campaign.py:133)、[s8b_floor_campaign.py:1444](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_floor_campaign.py:1444) |
| namespace exact allowlist | 実在集合との双方向比較済み。更新不要。[s8b_floor_campaign.py:1569](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_floor_campaign.py:1569) |
| launch certificate | path一覧でなく`clean_scan_digest`だけを持つ。literal変更不要 |
| generator hash pin | 対象5 sourceはいずれも今回変更しないファイル。波及なし。[s8b_oracle_manifest.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_oracle_manifest.py:44) |
| V1 trust root／protocol承認hash | bytes不変なので更新不要 |
| ratified／oracle driver／report | manifestを読まずH証拠鎖を検証。上記payload非照合だけ残る |

`test_manifest_shape_is_exact` は現在、実際には「件数＋path prefix＋64hex」しか検査しておらず、同件数でのpath差替えを検出しません。[test_frozen_artifacts.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:75) 件数だけでなく、新 selector evidence の exact key set assertも追加すべきです。module docstring、分類コメント、件数メッセージも9→実最終件数へ同期が必要です。

## P判定の訂正

- P1: **real（上記限定付き）**
- P2: **real**
- P3: 「本waveでratified production run不要」という命題は **real**。起草案の見出し「P3 — refuted」はラベル誤りです。commit (4) 直後はactive pointer不在なのでfull loaderは`no-active`になるのが正常です。[s8b_ratified_freeze.py:1237](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:1237)
- P4: **partial real**。write-path一覧は正しいが、staged／HEAD exact-set検査が不足
- P6: **real**。step (3) はprediction/rawを検査するだけで、journal/cell全体の受入証明ではありません

`.lock` はseal成功時に削除され、その後selector-runs宣言集合がexact照合されます。[s8b_prediction_runner.py:1485](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1485) prediction tmpも`finally`で削除されます。[s8b_selector_freeze.py:948](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_selector_freeze.py:948) どちらかが残ればcommit禁止で正しいです。

なお、現在の実測ではworktreeはcleanで、起草案が挙げたhandoffは存在しません。したがって step 0 の「untracked handoff blocker」は **refuted／stale** です。protocolは内容を開かず、HEAD blobが774 bytes・指定SHA-256であることだけ確認しました。
---
## 段6-1: 敵対レビュー レンズ1 (正しさ+盲検 closure)

## 総合判定

**条件付き**です。盲検入力への情報混入、R3 の c06 fallback 化、hash／manifest／tree の不整合は見つからず、これらは GO です。

ただし、成果物だけから「Claude を4回実際に呼び出した」ことを機械保証する closure は未達です。ローカル実行者を信頼境界に含めるなら GO、成果物単独で実走真正性まで要求するなら NO-GO です。

## real 所見

### F1 — real / partial：完成済み journal を実呼出しなしで seal 可能

seal は `selector-runs/` の既存 untracked を許可し、既存 header を受理し、resolved cell を再呼出しせずスキップします。

- [s8b_prediction_runner.py:1271](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1271)
- [s8b_prediction_runner.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:377)
- [s8b_prediction_runner.py:840](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:840)

したがって、header・payload・envelope・raw・receipt を事前作成すれば、provider 呼出しゼロでも `status:sealed` に到達できます。hash はすべて同じ作成者が後付けでき、外部署名やサービス側 attestation はありません。

今回の実物には、実走と整合する強い傍証があります。

- commit A → journal 開始 → 4 セル逐次実行 → commit B の時系列が自然
- 4 session ID はすべて一意
- modelUsage、正の token 数、duration、cost が存在
- envelope.result と raw は4件とも byte-equivalent
- 同一 payload の別セルでも個別 session・個別応答
- 現在の Claude 実行体 bytes は journal の `e1207175…` と一致

したがって「捏造された」とする証拠はありませんが、真正性の機械証明にもなっていません。

**影響:** 事前作成者は4 agent 行の choice_id を任意に選べるため、`body_sha256`、prediction file SHA、manifest pin を変えながら、非実走成果物を seal の受理集合へ入れられます。

### F2 — real / regressed：commit B の provenance trailer が実記録より低精度

commit B は selector prediction を次で記録しています。

```text
model=not-exposed; reasoning=not-exposed; scope=selector-predictions
```

しかし封印成果物はモデルを `claude-opus-4-8` と記録し、runner は `--effort high` を明示しています。[規約](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/ai-provenance.md:22)上、当該 scope が4 selector セルを指すなら `model=claude-opus-4-8; reasoning=high` が整合します。

**影響:** prediction/manifest の受理 bytes は変わりませんが、commit B の生成モデル・推論設定という provenance 参照が誤分類され、後続監査・集計結果が変わります。

## refuted / closed

| 攻撃面 | 判定 | 実測結果 |
|---|---|---|
| 盲検混入 | refuted / closed | 4 payload は exact 3 keys、固定6候補、descriptor のみ。protocol値、floor値、holdout名、arm、binding、winner、measured_tps、provenance はなし。`protocol_flag_bundle` と `maximize_throughput_tps` は承認済み固定語彙 |
| raw/envelope の floor 認知 | refuted / closed | floor、holdout、binding、winner、測定値なし。根拠は descriptor と候補機構だけで説明可能 |
| body/journal 整合 | refuted / closed | canonical body SHA=`69c7ad3e…`、file SHA=`5884c83f…`。journal は seq 1–15、header 1 + claim/envelope/invocation 各4 + static 2。row・receipt・raw・envelope は全件一致 |
| R3 | refuted / closed | 6行すべて `status=valid`、null choice は0。agent は c03/c04 のみ、c06 は off の static 2行だけ。missing の握りつぶしなし |
| basis/derangement | refuted / closed | selector basis を再構成して `779c6396…`。derangement は rr20↔rr80 の固定点なし全単射。全 binding hash も再計算一致 |
| correctness gate | refuted / closed | A/B は production seal/verify code を変更していない。Aはmanifest testのみ、Bはmanifest test＋成果物のみ |
| 原子性 | refuted / closed | commit B の selector-runs は regular file 13件ちょうど。journal宣言集合・manifest集合・tree集合が一致し、`.lock`、tmp、orphan、symlink、undeclared file はなし |

`swapped_follow_expectations` も正しく、rr20 は rr80-on の c04、rr80 は rr20-on の c03から再導出されています。rr20-swapped の実選択が c03で期待 c04と異なるのは将来の追従評価結果であり、文書不整合ではありません。

## 親ハンク

親ハンクに転記・件数・pin 集合の誤りはありません。

- commit A: floor protocol 1件追加。8→9 は正しい。commit A blob は774 bytes、SHA-256=`261cec1c7f423b…`。
- commit B: prediction 1 + selector-runs 13 の14件追加。9→23 は正しい。
- commit B tree の新規14 artifact は、[FROZEN_MANIFEST](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:38)の14 SHAとすべて一致。
- 同一 payload hash が2組あるのは正常です。rr20-on＝rr80-swapped、rr20-swapped＝rr80-on という derangement 由来です。
- 既存9 pin の削除・書換えなし。

Git 関係も、`00b9faa^` は完全な `776640790752a969baee9246b2531b5dde49244d` で、prediction の `pre_oracle_head` と一致します。commit A の floor protocol blob SHAも manifest pin と一致しています。

## 残存懸念・nit

- 既知境界どおり、HOME/global memory と Claude 実行体が floor 情報を持たなかったことは成果物から証明できません。neutral cwd、空 settings/MCP、toolsなし、server tool use 0 により経路は狭められています。
- `test_manifest_shape_is_exact` は実際には件数・path prefix・64hex を検査するだけで、カテゴリから期待 path 集合を独立再導出しません。今回の集合は手動照合で正しいため nit です。
- 指示どおり pytest は再実行していません。96 passed や各 check の実行履歴自体は本レビューでは再認証していません。
---
## 段6-2: 敵対レビュー レンズ2 (freeze-pin+provenance closure)

## 総合判定

**条件付き GO**。

commit B の byte-level 封印、manifest 転記、selector 証拠集合、consumer closure に破損はありません。条件は、commit B の provenance 誤記を訂正・追補し、`00b9faa128633ebdc83b81710ae785f53924ae4a` を外部基準として保持するか、裁定済み durable key-set/lineage を下流利用前に導入することです。

pytest は再実行せず、指定どおり Git tree/blob、`sha256sum`、JSON 構造、caller の静的読解で検査しました。

## Real findings

### R1 — `real / regressed`: commit B の headless selector provenance が実測と不一致

commit B は headless selector を

```text
model=not-exposed; reasoning=not-exposed
```

としていますが、role は `model: opus` / `effort: high` を固定し、runner も `--effort high` を渡しています。[selector-8b.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/.claude/agents/selector-8b.md:5) [s8b_prediction_runner.py:1095](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1095)

さらに4 invocation の receipt は全て `model=claude-opus-4-8` で、envelope の `modelUsage` にも同 slug が露出しています。[journal.jsonl:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/output/s8b-freeze/selector-runs/journal.jsonl:4) 規約上も表示された slug/選択値を使う必要があります。[ai-provenance.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/docs/ai-provenance.md:22)

正確な記録は少なくとも次です。

```text
AI-Agent: product=claude; model=claude-opus-4-8; reasoning=high; role=author; scope=selector-predictions
```

`role=author` と scope 自体は妥当です。4 agent row の choice/rationale を直接生成しており、同一構成4セルを1行へ集約するのも規約どおりです。Codex の `researcher` / `reviewer` 帰属にも過不足は認めません。

**影響:** 放置すると4 agent cell が実在する Opus/high ではなく not-exposed 構成へ誤帰属され、commit trailer と封印済み receipt の provenance 参照が分断されます。

### R2 — `real / partial`: `test_manifest_shape_is_exact` は exact key-set を検査しない

実装は `len == 23`、`output/` prefix、64hex だけです。[test_frozen_artifacts.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:110) したがって、既存 path を未知 path に同数差し替え、その新 bytes の hash を入れれば両テストとも通ります。関数名・docstring の “exact” と「移動・削除を検出」は継続保証として過大です。

今回の B tree については、full commit OID と tree が一回限りの別錨になり、手動双方向照合も成立しています。ただし将来の descendant HEAD に対する機械防壁ではありません。裁定パッケージへの繰延は、B の full OID を保持し、そのパッケージを下流 ratification より前に置く条件なら妥当です。

**影響:** 将来1件を同数 path へ差し替えると、旧封印ファイルが機械的な受理集合から脱落しても manifest テストが緑のままになります。

### R3 — `real / partial`: 初回導入の真正性は自己整合 bundle を排除しない

A は protocol と source 時点を先に固定していますが、prediction、journal、12 cell files、それらの manifest hash は B で同時導入です。したがって B 以後の bytes 不変性は強い一方、「実際に headless seal を走らせた」ことと「同じ形の bundle を後付け生成した」ことを commit 内だけでは暗号学的に区別できません。

時系列、4 session ID、envelope、現在残る実行体 hash は全て整合しましたが、外部署名 receipt や B より前の output commitment ではありません。D80 の初回導入捏造 residual と同じです。

**影響:** 自己整合する raw/envelope/journal/prediction を同時生成できる主体なら、4 agent choice/rationale を任意値へした bundle も封印済み予測として受理させられます。

### R4 — `real / partial`: HOME/global memory の盲検境界

実 payload は3 top-level key、descriptor、固定6候補だけで、protocol/floor/binding 対応表の混入はありません。neutral cwd、tools/MCP 無しもコードと記録に一致します。

一方、runner は認証のため `HOME` を引き継ぎます。[s8b_prediction_runner.py:1089](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_prediction_runner.py:1089) 記録された Claude 実行体は現在も存在し、SHA-256 `e1207175…` は journal と一致しましたが、seal 時の HOME/global memory に floor 情報が無かったことは commit から証明できません。

**影響:** global memory に floor 情報が存在した場合、manifest hash を一切破らずに4 agent row の選択・根拠が汚染され得ます。

## 親ハンクの正当性

`refuted / closed` です。

| 検査 | 結果 |
|---|---|
| commit A manifest | 9 entry、9 unique、全 SHA 一致 |
| commit B manifest | 23 entry、23 unique、全 SHA 一致 |
| Git object | 23件すべて `100644 blob` |
| B blob SHA vs manifest | 23/23 一致、mismatch 0 |
| working tree SHA vs B blob | 23/23 一致 |
| selector tree vs manifest | prediction 1 + selector-runs 13、差集合なし |
| selector-runs tree vs journal 宣言 | 13/13、差集合なし |
| manifest phantom path | 0 |

件数内訳も実 dict と一致します。

- s1: 2
- v1 holdout: 1
- protocol: 1
- prediction: 1
- selector-runs: 13 = journal 1 + 4 × payload/envelope/raw
- 裁定資料: 2
- 逐語: 3

合計23です。[FROZEN_MANIFEST](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/tests/test_frozen_artifacts.py:38)

`output/insights/2026-07-16_s8b-selector-leak-control-case.md` も名前上は selector 関連ですが、「selector 未実走」の設計事例で、B の実走証拠・journal 宣言・prediction source のいずれでもないため未 pin 穴ではありません。

## Trust chain・consumer closure

`refuted / closed` — B 以後の repo 内 bytes closure に欠落はありません。

- `B^ == A` で、prediction の `pre_oracle_head` も A と完全一致。
- protocol `261cec1c…` は A/B blob、manifest、journal header で一致。
- holdout `315b1e…` は V1 trust root、prediction source、journal header で一致。
- prediction file SHA は `5884c83f…`。`body_sha256=69c7ad3e…` と `selector_basis_sha256=779c6396…` は独立再構成でも一致。[selector_predictions.json:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/output/s8b-freeze/selector_predictions.json:27)
- prediction の5 source hashとjournalのparser hashは全て A の `100644` blobに一致。
- 4セル全てで envelope `.result` bytes == raw bytes。choice/rationale/session ID は raw == journal == prediction。
- Git commit B は manifest と14件の新規証拠を単一 tree に含み、commit 原子性は成立。

Consumer の「更新不要」裁定も反証できません。

- Official preflight は固定4 fileを read-once し、journal から12 artifactを導出して実在/hash/集合を照合します。[s8b_floor_campaign.py:1311](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_floor_campaign.py:1311)
- Namespace exact 検査は H tree の prediction/journal/raw/envelope と source historyを再検証します。[s8b_ratified_freeze.py:2455](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/orchestrator/campaign/s8b_ratified_freeze.py:2455)
- Payload は意図どおり exemption 外ですが、canonical holdout key表現を持たずscan対象として安全です。B snapshotでは4 payload全て直接 manifest pin されています。
- Launch cert は将来の preflight allowlist全体から新規生成されるため、既存 cert の更新対象はありません。
- A/B は generator、V1 trust-root、launch/ratified codeを変更しておらず、generator hash pinの波及もありません。
- Ratified runを今実行しない判断は裁定順序と整合します。

## Provenance の形式面

A/B とも `git interpret-trailers` が全 `AI-Agent` 行を trailer として認識し、途中の空行分断はありません。B の2つの `author` 行には双方 scope があり、Codex は異なる role なので scope 必須条件外です。形式 checker が通るという主張は正しい一方、checker は値を artifact と照合せず正規表現しか見ないため、R1 の意味的誤記は検出できません。[check_ai_provenance.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/t080-prediction-seal/tools/check_ai_provenance.py:22)

## Nit

- コメントの「sha256 は seal 後採取で非決定的」は、「artifact bytes が非決定的なため SHA は seal 後採取」が正確です。
- `プラン … line 140` は文書 path のない脆い参照ですが、今回の pin/受理集合には影響しません。