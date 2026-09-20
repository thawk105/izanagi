# 段 1 brief — [T-2724] 凍結 v2 g1 の承認 A → active pointer X を AI が作る (13:2x 裁定の履行)

wave `dev-wave-t2724-ax-delegated`、branch `worktree-dev-wave-t2724-ax-delegated`、base = local main `947fd160a` (2026-09-20 13:4x JST)。
worktree `W = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-ax-delegated`、job dir `J = /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-ax-delegated`。
裁定の逐語は `J/ruling-13-2x.md`。全 9 段 (受理集合を変える正しさ防壁 = 独立の敵対検証子必須、DW-C00)。

## 研究前進 (1 行)
8b oracle の再開 (runbook W-4 → W-5、B-2 / B-3 の主張) は凍結 v2 g1 の発効で止まっている。完了判定 = wave 木で `load_ratified_freeze(root)` が generation 1・sha `7e1114068433…` を返し (README §5 手順 6 の JSON 1 行)、runbook §2 P3 gate-check を g1 path で走らせて `freeze-ratify:` / `v2-execution: launch-validate:` / `freeze-not-active-generation:` の拒否が 0 件、全史 provenance 監査 rc=0、受入全走緑で main に着地。

## 確定済みユーザー裁定 (13:2x、`J/ruling-13-2x.md` 逐語)
A/X は AI が作る (D2120 項 2 (b)・D2174 項 4 を supersede)。(1) decisions fragment に委任を記録し attestation を「none 逐語」→「記録済みの委任裁定 + 構造化 AI trailer」へ。(2) Codex author が `_assert_user_commit` を「非 merge・AI-Agent trailer ちょうど 1 行 (逐語 none または規約適合の構造化 trailer)・H ancestry」へ。G の generation-commit-none 拒否・diff 1 file・X^ == A は不変。正例/負例 + 変異 matrix。(3) 同 author が README §5 手順 2〜5 の形で A/X record を書く (approver にユーザー委任と裁定日)。(4) loader・P1〜P4・全史監査。docs 3 箇所。scope 外: W-4/W-5、hook の変更、鍵署名、床値・certification。規律 2 を緩めない。

## scope (純増) と成果物
- S1 実装面 (Codex author 1 巡目): `orchestrator/campaign/s8b_ratified_freeze.py:558-570` `_assert_user_commit` の trailer 条件を改訂 (新 helper で「ちょうど 1 行」判定、reason code は `user-commit-trailer` を維持し message で理由を分ける)。`orchestrator/tests/test_s8b_ratified_freeze.py` に正例 (構造化 1 行の A/X で `resolve_active_generation` 成功、revocation / cancellation も同型) と負例 (trailer 無し / AI-Agent 2 行 (構造化 2 行、none + 構造化) / merge / X^ ≠ A / diff 1 file 超 / 規約非適合の構造化行 / 末尾空白付き構造化行 / product が予約語 / model=none) を追加。既存負例 3 本 (2263・2532・2614 行、`claude-opus` = 非適合行) は意味を「非適合だから拒否」に書き直す (拒否は不変)。
- S2 governance record (Codex author 2 巡目、W の root で shell/python): approval record (keys ちょうど `generation_sha256` / `approver` / `approved_at` / `scope`、canonical JSON、末尾改行なし、filename = 世代 sha) → 親が commit A。pointer record (keys ちょうど 5、`parent_active_sha256` null、`approval_sha256` = approval bytes の sha、filename = 自身の canonical bytes の sha) → 親が commit X。A/X とも非 merge・diff 1 file・trailer は Codex author の構造化 1 行のみ・間に他 commit なし。
- S3 帰結 (Codex author 3 巡目、A/X の後にしか計算できない): (a) B-10 pin 3 literal (`orchestrator/tests/test_backoff_extended_sweep.py:1671,2025`、`tools/pegasus/b10_backoff_grid.sh:22`) を A/X 込み tree の digest へ (D2166 と同型: 旧測定の記録は不変、新 phase の事前登録成立ではない)。(b) 実 repo を root にする consumer test の期待値: `orchestrator/tests/test_s8b_oracle_driver.py:127` `_NO_ACTIVE_REFUSAL` を exact 要求する 4 node (4074 / 4554 / 4585 / 5416 行) と `orchestrator/tests/real_repo_ratified_memo.py:18,46` の「実 repo の現状は no-active」記述。A/X 後の焦点走で実測した新しい真値に書き直す (弱体化ではない。payer node id `test_nonnull_floor_without_active_generation_is_refused` は `test_real_repo_serialization.py:203,536,2819` が pin するので改名しない)。
- S4 docs (親): decisions fragment `docs/spool/decisions/2026-09-20-dev-wave-t2724-ax-delegated-1.md` (`{{D:t2724-ax-delegated}}`)、README §5 (人間手番 → 委任後の形、実施記録)、runbook W-3 の「approvals/・active/ は人間 commit」、hooks/README.md:150-154 の「`AI-Agent: none` 逐語」、worklog fragment、insight `output/insights/2026-09-20/t2724-ax-delegated/README.md`。
- S5 検証 (親): README §5 手順 6 の loader script (job dir に Write)、runbook §2 P1 (`git ls-tree HEAD external/ccbench` = 511c9538…) / P2 (`test_frozen_artifacts.py` 2 passed) / P3 (gate-check、g1 path と v1 path の両方を記録) / P4 (`qstat -u`)、`python3 tools/check_ai_provenance.py` 全史 (dispatch、rc=16 は失敗)。

## 不変条件
- 規律 2: 受理集合の拡大は「1 行・規約適合」に限る。G の `generation-commit-none` 拒否、`approval-commit-diff` / `pointer-commit-diff` (diff 1 file)、`pointer-approval-parent` (X^ == A)、`user-commit-merge`、`user-commit-ancestry`、`_is_none_commit` の byte-for-byte 検査 (R3) は 1 byte も緩めない。
- hook (`hooks/guard_write.py` F6a) は変更しない。A/X の bytes は Bash 経路 (shell/python) で書く (G と同じ。hooks README 150 行「誤操作抑止であって認証防壁ではない」)。
- 世代文書 G (`32ba8cae4`) と X1' (`cc82edc8c`) は base の祖先 (実測 rc=0)。世代 file sha256 = `7e1114068433…` (実測一致)。approvals/ active/ は不在 (実測)。
- B-10 pin の算法 (sorted rglob、path + NUL + bytes、対象 dir 2 つ) は不変。旧 cohort の記録 `freeze_trees_sha256` は不変 (規律 7)。
- A/X の commit 主体は親 (DW-C01)。trailer は Codex author 1 行 (Git 操作の機械的代行は記録しない、ai-provenance.md「記録単位」)。`Co-Authored-By` は付けない (G と同じ)。model / reasoning は launcher receipt の `recorded_model` / `recorded_effort` から取る。
- 実装 commit → A → X → 帰結 commit の順。A と X の間に他 commit を挟まない。
- pin 閉包 (DW-O09、実測): 変更 file の sha256 前半で output/・tests・docs に hit 0。`_assert_user_commit` の外部参照は docs/decisions (D15577 付近・D48642 付近) と過去 insight のみ (t080_freeze_migration.py の `_is_none_commit` は別関数、T-080 受領証用で本 wave は触れない)。B-10 literal `6a4ee1ef…` は test 2 箇所 + job script 1 箇所 + 歴史記録 (不変)。`acceptance_duration_ledger.json` は未登録 node を fail-soft で扱う。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 「ちょうど 1 行」の判定式: raw の AI-Agent 系行 (`_raw_ai_agent_lines`) が 1 本 ∧ parse 値 (`_parsed_ai_agent_values`) が 1 個 ∧ (その行が byte-for-byte `AI-Agent: none` ∨ 構造化適合) 。構造化適合 = 値が `tools/check_ai_provenance.py:87` `AGENT_VALUE` に fullmatch ∧ product ∉ `RESERVED_PRODUCTS` ∧ model / reasoning ≠ `none` ∧ raw 行が byte-for-byte `"AI-Agent: " + 値` (末尾空白・key の大小文字違いを拒否、R3 と同型)。文法の出所は `tools.check_ai_provenance` からの遅延 import (D75「同名識別子を二義化しない」、`orchestrator/campaign/floor_liveness.py:21` が `tools.pegasus` を import する先例)。ImportError は fail-closed (`RatifiedFreezeError`)。代替 = module 内へ regex を複製して meta-test で `AGENT_VALUE.pattern` と等値 pin。
- (P2) `Co-Authored-By` 行は AI-Agent 系行に数えない (現行 `_raw_ai_agent_lines` の定義どおり)。A/X には付けない。
- (P3) P3 gate-check の「受理」= g1 path 指定で `freeze-ratify:` / `v2-execution: launch-validate:` / `freeze-not-active-generation:` の拒否 0 件。`allowed: true` は期待しない (W-4 の spec 承認が未了 = runbook W-4 の scope)。残る拒否集合は exact に記録して W-4 へ渡す。v1 path 指定は `freeze-not-active-generation` を期待 (runbook 表 3 段目「委譲されず前段の期待のまま」の実測で確認)。
- (P4) `approver` の値 = `user (delegated to AI by user ruling 2026-09-20 13:2x JST; supersedes D2120 item 2(b) and D2174 item 4)`、`scope` = `s8b-holdout`、`approved_at` = record を書いた実時刻 (UTC)。批准側は値の書式を検査しない (README §5)。
- (P5) B-10 pin を同 wave で更新する (D2166 と同じ授権根拠: pin の対象 dir から A/X を外せない、hold / 除外 / 条件付き assert は不採用、更新だけが規律 2 と両立)。変異 (test literal だけ旧値 / job 定数だけ旧値) と負例 (別 file 追加 / 1 byte 変更) を D2166 の形で取る。
- (P6) A/X 後、実 repo root の consumer 4 node の真値は焦点走で実測してから書く。予測 (先行 session の推定) = `run_block` は `freeze-not-active-generation` (v1 path)。予測を期待値にせず実測を期待値にする。
- (P7) 既存 test の `ai_agent="claude-opus"` (非適合の構造化行) は「AI だから拒否」でなく「規約非適合だから拒否」として残す。改名はしない (ledger / xdist の node id を保つ)。

## 変更面 (実アンカー)
| file | 行 | 変更 |
|---|---|---|
| `orchestrator/campaign/s8b_ratified_freeze.py` | 518-570 | 新 helper (構造化適合判定) + `_assert_user_commit` の条件・docstring・message |
| `orchestrator/tests/test_s8b_ratified_freeze.py` | 127-160, 203-227, 2263-2330, 2520-2535, 2600-2616 | fixture の構造化 trailer 対応 + 正例/負例追加 + 既存負例の意味書き直し |
| `orchestrator/tests/test_backoff_extended_sweep.py` | 1671, 2025 | B-10 literal (A/X 後) |
| `tools/pegasus/b10_backoff_grid.sh` | 22 | 同上 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | 127-130, 4074, 4554, 4585, 5416 | 実 repo の新しい真値 (A/X 後、実測後) |
| `orchestrator/tests/real_repo_ratified_memo.py` | 18, 46 | docstring の「現状 no-active」 |
| `output/s8b-freeze/approvals/7e1114….json`、`output/s8b-freeze/active/<sha>.json` | 新規 | A / X |
| docs | README §5 (136-229 行)、runbook 301-331 行 W-3、hooks/README.md 150-154 行、decisions/worklog fragment、insight | 委任後の形 |

## 分割方針
段 2 plan 1 本 (read-only)。段 3 相談 2 本 (レンズ A = 正しさ境界・整合: 受理集合の拡大が規律 2 と provenance 規約に閉じるか、判定式の穴、既存負例の含意、変異の帰属; レンズ B = 実効性と過剰・帰結: A/X 後に赤になる consumer の全列挙、B-10 pin と真値の書き換えが弱体化でないこと、P3 の受理定義、scope 外へ滲む実装の有無)。段 5 author は直列 3 巡 (S1 → 親 commit → S2 → 親 commit A / X → 焦点走 → S3 → 親 commit)。段 6 review 2 本 (S1〜S3 の統合差分) + fix + 変異 matrix (`_assert_user_commit` 群 + B-10 pin) + 受入。
