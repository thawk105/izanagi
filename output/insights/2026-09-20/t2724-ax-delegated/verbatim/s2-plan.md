## 前提と判定

以下、`W` は指定 worktree、`J` は指定 job dir。repo 内の `file:line` は W 相対、逐語資料は J 相対で示す。静的読解のみ実施し、pytest・record 作成・commit は行っていない。

実装順は **S1 → 親の実装 commit → S2 approval 作成 → 親 commit A → S2 pointer 作成 → 親 commit X → 焦点走 → S3 → 親の帰結 commit → S4/S5** とする。A と X の間にコード・docs その他の commit を挟まない。

主要な修正点は次の3点。

- **P3 の v1 gate-check 予測は反証。** v1 は active 解決前に分岐するため、`freeze-not-active-generation` を期待できない。
- **P6 は期待値の実測更新だけでは不十分。** 集約テストが従来検査していた「active 解決失敗と manifest 構造拒否の集約」を別の負例で維持する必要がある。
- **runbook P2 の「2 passed」は現物と不一致。** 現在の直接実行 runner は5関数を列挙する。A/X の帰結ではなく既存の文書ずれである。

根拠: `orchestrator/campaign/s8b_oracle_driver.py:627,1324,1340,1366`、`orchestrator/tests/test_s8b_oracle_driver.py:4559`、`orchestrator/tests/test_frozen_artifacts.py:187,201,212,227,234,251`。

## S1 — 判定式と実装箇所

変更点を `orchestrator/campaign/s8b_ratified_freeze.py:558` 付近に限定する。

新 helper は次とする。

```python
def _user_commit_trailer_problem(commit: str, root: Path) -> Optional[str]:
    """受理なら None、拒否なら診断文字列を返す。"""
```

処理順:

1. `_commit_message(commit, root)` で message を一度取得する。
2. `_raw_ai_agent_lines(message)` の長さが1でなければ拒否。
3. `_parsed_ai_agent_values(message, root)` の長さが1でなければ拒否。
4. raw 行が `"AI-Agent: " + values[0]` と完全一致しなければ拒否。
5. `values[0] == "none"` なら受理。
6. 構造化文法に `fullmatch` しなければ拒否。
7. product が予約語、または model / reasoning が `none` なら拒否。
8. その他は受理。

診断文字列は、例えば以下に固定する。

| 条件 | message 内の診断 |
|---|---|
| raw 件数不一致 | `AI-Agent raw 行数が 1 でない: N` |
| parse 件数不一致 | `AI-Agent trailer 値数が 1 でない: N` |
| raw 表記不一致 | `AI-Agent 行が canonical 表記でない` |
| 文法不適合 | `AI-Agent 構造化値が provenance 文法に適合しない` |
| product 予約語 | `AI-Agent product が予約語: VALUE` |
| model / reasoning | `AI-Agent model/reasoning に none は使えない` |

`_assert_user_commit` では現行 trailer 分岐のみを次に置換する。

```python
problem = _user_commit_trailer_problem(commit, root)
if problem is not None:
    raise RatifiedFreezeError(
        "user-commit-trailer", f"commit {commit}: {problem}"
    )
```

merge 検査 → trailer 検査 → ancestry 検査の順も維持する。docstring は「非 merge、AI-Agent trailer ちょうど1行、逐語 none または規約適合の構造化値、H ancestry」へ変更する。

**P1 の判定式は支持。** `_raw_ai_agent_lines` は key の大小文字・前後空白を吸収して候補行を数える一方、返す行自体は加工しない。parser は値を `strip()` する。このため件数検査と raw 完全一致の両方が必要である。構造化行の末尾空白も `ai-agent:` も手順4で拒否できる。none 枝は現行 `_is_none_commit` と同じ受理集合になる。

根拠: `s8b_ratified_freeze.py:518,528,546`。

`_is_none_commit` 自体は変更しない。`_assert_candidate_commit` の none 拒否も変更しない。approval / pointer / revocation / cancellation は既に同じ `_assert_user_commit` を呼ぶので、呼び手の変更は不要。diff と親関係の検査にも触れない。

根拠: 同 file `:573,1204,1219,1234,1247,1298,1305,1312`。

## S1 — 文法の出所と import 経路

構造化適合の正本は `tools/check_ai_provenance.py:66` の ROLES、`:67` の IDENT、`:68` の RESERVED_PRODUCTS、`:87` の AGENT_VALUE、および `validate_message:1506` 以降の追加制約である。

比較結果:

| 案 | 判定 |
|---|---|
| `tools.check_ai_provenance` を遅延 import | 通常の driver CLI・指定 pytest 経路では成立。repo root を import できない実行形には不十分 |
| module 内に文法を複製し meta-test で正本と pin | runtime の tools 依存を増やさず、コピーされた orchestrator でも判定できる。ただし同期検査が必須 |

遅延 import の具体的な評価:

- `PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_oracle_driver.py …` は driver 自身が repo root を `sys.path` に挿入する。**この実行形は成立する**。根拠: driver `:22`。
- `test_s8b_ratified_freeze.py` は repo root を挿入する。runner も挿入する。根拠: test `:35`、`tools/run_tests.py:57`。
- `floor_liveness.py:15` の先例も、直接 CLI のときに自分で root を挿入してから `tools.pegasus` を import している。**無条件に tools が見える先例ではない**。
- checker `:35` は import 後に root を挿入し、`:44` で `orchestrator.campaign.site_policy` を import する。最初の `tools` 解決失敗を、この処理では救えない。
- `site_policy.py:5` の import は標準ライブラリのみ。`campaign/__init__.py:1` に実行依存はなく、この追加辺から批准 module に戻る循環はない。checker の監査・dispatch は `main:3519` 配下であり、import 自体が全史監査を開始することもない。
- コピー fixture は orchestrator 全体をコピーするが、runtime 補完集合を `orchestrator/campaign/*.py` に限定している。tools の存在を前提にしてはならない。根拠: `test_s8b_oracle_driver.py:1433,1492,1607`。

**推奨実装は複製＋meta-test。** `s8b_ratified_freeze.py:558` 前に `_PROVENANCE_AGENT_VALUE` と `_PROVENANCE_RESERVED_PRODUCTS` を置き、正本への参照コメントを付す。正本と別の文法を設計せず、pattern・flags・予約語集合を exact 比較する `test_user_commit_provenance_grammar_matches_checker` を追加する。model / reasoning 制約は負例で固定する。

これにより P1 は「判定式は支持、遅延 import を全実行形で使えるという主張は条件付き」とする。遅延 import を選ぶ場合は、構造化枝内の `ImportError` を `RatifiedFreezeError("user-commit-trailer", …文法をロードできない…)` に変換し、受理へ倒さない。

## S1 — テスト計画

既存 `_commit:127` と `_approve_and_point:212` は `ai_agent` を文字列として埋めるため、次の値をそのまま渡せる。fixture の引数追加は不要。

```text
product=codex; model=gpt-6-astra; reasoning=medium; role=author; scope=approval-record
```

これはテストデータである。実 record の trailer は launcher receipt の値を使う。

新規・拡張するテスト:

| test 名 | 検査 |
|---|---|
| `test_structured_approval_and_pointer_resolve_active_generation` | A/X 両方を構造化1行で作り、generation・sha・approval/pointer hash を exact 照合 |
| `test_structured_revocation_is_applied` | 構造化 revocation が受理され、`tip-revoked` になる |
| `test_structured_cancellation_is_applied` | cancellation により fork が解消し、選択世代が期待どおりになる |
| `test_user_commit_trailer_requires_one_raw_and_parsed_line` | trailer 無し、構造化2行、none＋適合構造化行、本文にしか存在しない行を拒否 |
| `test_user_commit_structured_value_must_conform` | `claude-opus`、未知 field / role、余分な suffix、予約 product 全4値、model / reasoning の none を拒否 |
| `test_structured_trailer_raw_form_is_exact` | 末尾空白、tab、key 小文字、key 前後空白を拒否 |
| `test_structured_user_merge_commit_rejected` | 適合構造化 trailer の merge を `user-commit-merge` で拒否 |
| `test_user_commit_provenance_grammar_matches_checker` | 複製文法の pattern・flags・予約語集合を正本と exact pin |

revocation の正例は「active を返す」ことではなく、**無効化が適用されること**を確認する。cancellation は既存 fork 回復例を none / structured で parameterize してもよい。

根拠: `test_s8b_ratified_freeze.py:229,2517,2582`。

次の既存 test は改名せず、適合構造化 trailer でも同じ不変条件が働くよう parameterize する。

- `test_non_ancestry_user_commit_rejected` — `:2250`
- `test_approval_commit_with_extra_file_rejected` — `:2328`
- `test_pointer_commit_with_extra_file_rejected` — `:2345`
- `test_pointer_parent_must_be_selected_approval_commit` — `:2362`

`test_generation_introduced_in_none_commit_rejected:2415` は維持する。G の fixture `claude-opus` は、今回変更しない candidate 判定では受理されるので、一括置換しない。

「AI だから拒否」から「非適合だから拒否」へ説明を直す既存 test は次の3本。

| 改名しない test | 書き直す説明 |
|---|---|
| `test_approval_commit_with_ai_trailer_rejected:2264` | `claude-opus` は product/model/reasoning/role の構造化文法を満たさない |
| `test_revocation_with_ai_trailer_is_error_not_ignored:2526` | 非適合 trailer の revocation は無視せず検証エラーにする |
| `test_cancellation_with_ai_trailer_is_error:2608` | 非適合 trailer の cancellation を拒否する |

また `test_trailer_both_none_and_structured_rejected:2274` の第2行は現在 `claude-opus` である。適合構造化値に替え、「混在そのもの」を検査する。

注入 helper の使い分け:

- 通常の構造化正例・予約語・model=none・文法不適合: `_commit`。
- trailer 無し・2行・混在・小文字 key・本文中だけの候補行: `_commit_raw:135`。
- 末尾空白・tab を保存する負例: `_commit_verbatim:142`。Git の既定 cleanup に消されないことを raw と parse の事前 assert で証明する。

件数・表記の負例は helper または `_assert_user_commit` の直接検査も持たせる。既存の「A/X を同じ commit に入れた負例」だけでは、trailer 判定を壊しても後段 topology が拒否し、変異の帰属が曖昧になる。

## S2 — A/X record と親の commit

S1 author はコード・テストのみ編集し commit しない。S2 は別 invocation とし、親から **J の script 作成と指定 record の作成**を明示した作業範囲を渡す。これは brief の直列3巡と整合する。

根拠: `brief.md` の「分割方針」、`verbatim/insight-README-s5.md:8`。

S2 の手順:

1. 実装 commit 後、全体の `git status --porcelain --untracked-files=all` が空であることを確認する。G と X1' の ancestry は README の2コマンドを個別に実行する。
2. author が `J/write-approval.py` を作る。W を明示的に root とし、`python3 -B /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-ax-delegated/write-approval.py` で実行する。
3. 親が approval だけを stage・preflight・commit A する。
4. author が A を確認して `J/write-pointer.py` を実行する。
5. 親が pointer だけを stage・preflight・commit X する。

heredoc に防護 path を同居させない。`hooks/guard_bash.py:113` の `_OPAQUE_RE` は `<<` を検出し、`:2844` 付近で防護 path との同居を拒否する。job script 経路は今回の明示的委任に基づく手順であり、hook の保証として扱わない。

approval の自己検証項目:

- generation file の sha が `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`。
- keys は `generation_sha256 / approver / approved_at / scope` の4つ exact。
- approver は P4 案を使用する。
- `approved_at` は作成時点の UTC、`YYYY-MM-DDTHH:MM:SSZ`。
- `scope="s8b-holdout"`。
- `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`、末尾改行なし。
- filename は generation sha＋`.json`。
- `open("xb")` の create-only。既存 file があれば上書きせず停止。
- 作成後の全体 status は `?? output/s8b-freeze/approvals/<generation-sha>.json` の1行のみ。`--untracked-files=all` を必ず付ける。

根拠: `verbatim/insight-README-s5.md:10,24,26,29`、`s8b_ratified_freeze.py:1195`。

**P4 は支持。** 提案値は委任・裁定日を含む。批准コードは canonical schema と generation sha を検査し、approver の特定書式を要求していない。ただし `13:2x` は原裁定の識別表記であり、実時刻 `approved_at` の代わりに使わない。

親の message file:

```text
Record delegated approval for freeze generation 1

AI-Agent: product=codex; model=<recorded_model>; reasoning=<recorded_effort>; role=author; scope=approval-record
```

X は本文と scope を `active-pointer` に替える。`Co-Authored-By` は付けない。`--message-file` rc=0 の後に `git commit -F <絶対path>`。

`_message_file_paths:1830` が staged path を取り、`_is_implementation_path:1585` は output 配下の通常 JSON を実装面に分類しない。したがってこの2 record は実装面 author 検査の対象外だが、構造化 trailer 自体の文法検査には合格する必要がある。**output 配下すべてが免除なのではない**。例えば `.py` は suffix 規則で実装面になる。

pointer の自己検証項目:

- keys は `generation_number / path / sha256 / parent_active_sha256 / approval_sha256` の5つ exact。
- generation=1、path=g1、sha=上記、parent=null。
- `approval_sha256` は A に導入した approval bytes の hash。
- canonical JSON・末尾改行なし・filename は pointer 自身の bytes hash。
- create-only、status は pointer 追加1行のみ。

A bytes は commit 前にも計算できるが、**確定した A の bytes と X^==A を固定する運用順序として、X は A commit 後にのみ作る**。A の tree blob と worktree bytes の一致も確認する。

親は A/X 各 commit の親数・diff 追加1件・message を検査し、X の親が A exact であること、X 後の status が空であることを確認する。

根拠: `verbatim/insight-README-s5.md:33,39,50,61`、`s8b_ratified_freeze.py:1298,1312`。

**P2 は支持。** `_raw_ai_agent_lines:522` は key が AI-Agent の行だけを数える。CAB を新たに数える変更はしない。CAB の一般規約は provenance checker に残す。

## S3 — B-10 と scan / pin の帰結

**B-10 は A/X の bytes 追加により必ず digest が変わる。P5 は支持。**

`test_backoff_extended_sweep.py:2014` は `output/s1-freeze` と `output/s8b-freeze` の `rglob("*")` 全通常 file を対象にし、path＋NUL＋bytes を hash する。approvals/active/ の除外はない。job 側も `b10_backoff_grid.sh:585` で同じ2 directory を再帰列挙する。

A/X 後に変更する literal は3箇所のみ。

- `orchestrator/tests/test_backoff_extended_sweep.py:1671`
- 同 `:2025`
- `tools/pegasus/b10_backoff_grid.sh:22`

赤になる test は `test_b10_freeze_tree_bytes_match_the_wave_local_gate:2011`。test と job の同時更新の整合は `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs:1650` が検査する。実 job は開始前 `:595` と終了後 `:647` の exact 比較で拒否する。

旧 cohort の digest・completion・結果記録は変更しない。今回の更新は新 phase の事前登録や本走許可ではない。根拠: `verbatim/D2166.md:11,15,16,19,35`。

その他の参照関係:

| 対象 | A/X による帰結 |
|---|---|
| official 床値 clean scan | A/X の適合 path は chain record として許容され、digest には加わる。既存 holdout hit の赤は解消しない |
| T-080 receipt live scan | デフォルト scan の除外 prefix に freeze namespace があるため、A/X 自体は新規 hit を増やさない |
| `FROZEN_MANIFEST` | 固定23 path の列挙。A/X を数えない |
| F6a hook test | file の存在でなく tool/path の拒否を検査するため影響なし |
| real-repo memo | runtime は実 loader の値・例外をそのまま cache するため、ロジック変更不要。現状説明のみ更新 |

根拠:

- `s8b_floor_campaign.py:318,5481,5515,5532,5545`。chain records は namespace allowlist に加わる。
- `s8b_holdout_freeze.py:45,406`、`t080_freeze_migration.py:1718,1891,2272`。v2 委譲後の exact exemption は別の検証経路であり、prefix 除外を広げない。
- `test_frozen_artifacts.py:41,162,171,234`。`FROZEN_MANIFEST` の参照検索でも、追加 file を再帰列挙する契約ではない。`test_s1_9pair_figure_provenance.py:608,618` はこの固定 literal を読む。
- `test_hooks.py:229`、`hooks/guard_write.py:314`。
- `real_repo_ratified_memo.py:14,17,44`。`:46` は payer の名前であり、削除・改名対象ではない。

## S3 — 実 repo consumer の全参照と期待値更新

`_NO_ACTIVE_REFUSAL` の定義・使用は次の5箇所で、exact 使用 node は4本。

| node | 使用行 |
|---|---|
| 定数定義 | `test_s8b_oracle_driver.py:127` |
| `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing` | `:4053,4074` |
| `test_nonnull_floor_without_active_generation_is_refused` | `:4528,4554` |
| `test_active_resolution_and_manifest_structure_refusals_are_aggregated` | `:4559,4585` |
| `test_cli_subprocess_returns_rc_2_on_gate_refused` | `:5386,5416` |

`rg -n 'ROOT|REAL_FREEZE|_NO_ACTIVE_REFUSAL'` の参照箇所は、同 file 内で以下。定数・helper・fixture 内の参照も含めて確認した。

```text
34,40,59,111,127,
534,555,565,576,580,598,624,961,
1434,1438,1463,1486,1522,1632,1983,
2302,2306,2323,2350,2361,2362,2399,2400,
2792,2803,2817,2940,2946,
3274,3322,3381,3386,3408,3443,3451,3510,3595,3667,3688,
3779,3790,3801,3822,3827,
4068,4069,4074,4449,4455,4549,4554,4579,4585,
5063,5090,5093,5107,5110,5344,5372,5403,5404,5416,
5511,5587,6051,6462,6471,6506,6511,6519,6523,
6551,6556,6564,6568,6705,6717
```

このうち `test_real_freeze_gate_lists_floor_and_budget_null:3790` は v1 `gate_check` で、上記4 node の `run_block` と分ける。既存の floor/budget だけの期待と chain 導入後の live scan の差は、A/X が新たに生む差ではない。保留解除時の既存赤を今回の期待値変更へ混ぜない。

またコピー fixture `:1438` は実 output を取り込む。active-v2 fixture は `:1440` 以降で独立世代用 namespace を整える。このような間接参照は焦点4本だけでは検証しきれないため、変更後の driver file 走と受入全走で確認する。「他には絶対に赤がない」とは静的読解だけで断言しない。

焦点走は、A/X 後の変更前期待値で以下を実行し、失敗出力を保存する。4本とも growth hold 登録があるので、明示された今回の焦点走に限り解除 token を付ける。保留台帳自体は変更しない。

```bash
IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command python3 tools/run_tests.py -n 0 -vv --tb=long \
  orchestrator/tests/test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing \
  orchestrator/tests/test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused \
  orchestrator/tests/test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated \
  orchestrator/tests/test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused
```

根拠: `growth_test_holds.py:17,189,525,536,547`、`tools/run_tests.py:74,999`。

**P6 は条件付き支持。** 予測を期待値にしない方針は正しい。ただし `run_block:1340` は requested freeze の hash 比較より先に `launch_validate` を行う。これが失敗すれば `v2-execution: launch-validate:`、成功して指定 bytes が違えば `freeze-not-active-generation` となる。

`launch_validate` は単なる active 解決ではない。以下を要求する。

- 同一 activation HEAD、generation=1。
- G/H/worktree の artifact bytes・mode 一致。
- current environment contract、current build admission policy。
- protocol / cert / manifest / journal / result / admission evidence と床選択の整合。
- binding graph と cert / G の lineage。
- active-chain・selector evidence の exact exemption。
- occurrence から導いた hit 集合と repository live scan の完全一致、scan 前後の列挙・artifact 不変。

根拠: `s8b_ratified_freeze.py:3035,3106,3134,3191,3236,3259,3295,3336,3502,3525,3531,3546,3559,3583`。

更新時は `_NO_ACTIVE_REFUSAL` を意味の合う名前へ替えてよいが、**test node 名は維持**する。payer の root=ROOT・memo 非使用と、既存 memo consumer 集合も維持する。根拠: `test_real_repo_serialization.py:203,536,2819,2824,2834`。

特に集約 node の既存 assertion `:4585` は、A/X 後に早期の freeze mismatch / launch failure へ移れば manifest refusal を観測しなくなる。そこで新規 `test_active_resolution_error_and_manifest_structure_are_aggregated` を追加し、独立した未発効 tmp repo と不正 manifest で、従来の **no-active＋manifest schema error の exact 集合**と書込みなしを維持する。既存 node の期待値を減らすだけで完了にしない。

## S4/S5 — 文書と検証の実行形

親の docs 更新:

- `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md:136` — 現行手順を委任後の形へ。過去の実施事実は保持。
- `docs/phase3-8b-restart-runbook.md` の W-3 — 人間専用記述を委任裁定・構造化 trailer へ。
- `hooks/README.md:150` — attestation を委任裁定＋構造化 trailer＋topology と説明。hook を認証防壁に数えない。
- decisions / worklog fragment、新 insight — A/X SHA、loader JSON、焦点走、変異、検証の実測を記録。

loader は `J/verify-active.py` に `verbatim/insight-README-s5.md:69` の処理を置く。root を引数から resolve して `sys.path` に挿入し、`resolve_active_generation` と `load_ratified_freeze` の generation / activation_head / sha 一致を assert、指定 sha を確認して JSON 1行を出す。

```bash
python3 -B /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-ax-delegated/verify-active.py /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-ax-delegated
```

P1〜P4 は各コマンドの stdout/stderr/rc を別々に保存する。

```bash
git ls-tree HEAD external/ccbench
```

```bash
python3 orchestrator/tests/test_frozen_artifacts.py
```

```bash
PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_oracle_driver.py gate-check --freeze output/s8b-freeze/holdout_freeze.v2.g1.json
```

```bash
PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_oracle_driver.py gate-check --freeze output/s8b-freeze/holdout_freeze.json
```

```bash
qstat -u tanab
```

P1 は `160000 commit 511c9538…`。P2 は現物の runner が5関数を実行するため、**正常時は5 passed / 0 failed が静的予測**であり実測で確定する。held marker がある場合は、それを bytes 全検証済みと報告しない。根拠: `test_frozen_artifacts.py:162,187,251`。

**P3 は一部反証。**

- g1 で批准関連3 prefix が0件という条件は、wave の「批准経路成功」の部分判定として採用できる。
- それは runbook 全 gate の「受理」と同義ではない。`allowed: true` でなければ W-4/W-5 へ進まない。
- v1 `gate_check` は `s8b_oracle_driver.py:627` で active 解決前に戻るため、P3 案の `freeze-not-active-generation` 予測は不成立。runbook の「前段の期待のまま」がコードと整合する。既知4拒否の exact 集合を実測照合する。
- g1 に残った拒否は件数・全文・reason・対象 path を記録し、W-4 の spec 未承認以外を推測で正当化しない。

全史監査:

```bash
python3 tools/check_ai_provenance.py
```

実行場所の判定:

| 操作 | 実行形 |
|---|---|
| status / ancestry / hash / record script / loader / gate-check / P1 / P4 | 性能測定ではなく、専用 compute dispatch 必須の入口はない。login で実行可能 |
| P2 直接 runner | `:251` は pytest を呼ばない小さい独自 runner。runbook 指定の直接実行を使用 |
| pytest / 受入全走 | 必ず `tools/run_tests.py`。headroom に応じ bounded local または dispatch |
| `--message-file` | checker `:3546` が通常の site gate から免除。login で実行可能 |
| 全史 provenance | checker 自身が headroom / queue / scope / dispatch を判定。rc=16 は検証成功ではない |

根拠: driver `:2042`、`tools/run_tests.py:2493,2502,2510,2539,2620`、checker `:3546,3584,3593,3615`。現在の hostname は `pegasus02`。実行場所を固定する場合のみ各 runner の `--force-dispatch` を使う。キュー停止かつ local の余裕なしなら実行不能として記録する。

S1/S3 後の関連 test、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、受入全走を親の検証段へ渡す。焦点走・変異結果を受入全走の代わりにしない。

## 段4事前登録 — 変異候補

以下は提案名であり、まだ実施・KILLED 判定していない。

| 変異 | kill を要求する test |
|---|---|
| raw 件数検査を削除し、本文中の余分な AI-Agent 行を許す | `test_user_commit_trailer_requires_one_raw_and_parsed_line` |
| parse 件数を検査せず raw 値だけで受理する | 同 test の本文内のみ case |
| raw / parse の「1件」をともに「1件以上」にして先頭を採用 | 同 test の構造化2行 case |
| raw 完全一致を `strip()` 後比較へ変更 | `test_structured_trailer_raw_form_is_exact` |
| raw key の大小文字を正規化してから比較 | 同 test の小文字 key case |
| 構造化文法検査を削除 | `test_user_commit_structured_value_must_conform` |
| RESERVED_PRODUCTS 検査を削除 | 同 test の予約語4 case |
| model / reasoning の none 検査を削除 | 同 test の model / reasoning case |
| none と構造化の混在を特別扱いで許可 | `test_trailer_both_none_and_structured_rejected` |
| merge 検査を削除 | `test_structured_user_merge_commit_rejected` |
| H ancestry 検査を削除 | `test_non_ancestry_user_commit_rejected` |
| G の `generation-commit-none` 拒否を削除 | `test_generation_introduced_in_none_commit_rejected` |

G の変異は後続 `generation-commit-provenance` へ理由が変わる場合も、既存の exact reason assertion で kill する。受理へ変わったと誤報しない。

`AGENT_VALUE` は `^…$` で anchor され、parser 値は1行かつ strip 済みである。したがって **fullmatch→search だけでは等価変異になり得る**。無条件に kill 必須へ登録せず、非等価性を示せる場合のみ採用する。根拠: checker `:87`、批准 module `:528`。

B-10 の2変異:

| 変異 | kill を要求する test |
|---|---|
| test 側 literal を旧値へ戻す。job は新値 | `test_b10_freeze_tree_bytes_match_the_wave_local_gate`、script 文字列側なら `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs` |
| job 定数だけ旧値へ戻す。test は新値 | `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs` |

別 file 追加・既存 file 1 byte 変更も独立コピーで digest 不一致を確認する。job 全体の測定を起動せず、`:585` の算法と `:596` の比較を対象にする。本番 freeze record を変異実験で変更しない。

## 不確定点 — 親への択一

- **Q1:** 文法の runtime tools 依存を避ける「複製＋pattern / flags / 予約語集合の meta-test」を採用するか、正規起動経路に限定した「遅延 import＋ImportError fail-closed」を採用するか。推奨は前者。
- **Q2:** P3 の完了文言を「批准関連拒否0件」と「全 gate 受理」に分け、v1 は既知4拒否との照合へ修正するか。推奨は修正。現行 P3 の v1 予測はコードと不一致。
- **Q3:** 既存4 node を改名せず実測値へ更新し、失われる active 解決失敗＋manifest 集約の負例を別 tmp repo test で補うか。推奨は補う。
- **Q4:** runbook P2 の件数を現物の5関数に合わせて訂正するか、今回の実測記録に文書ずれとして残すか。推奨は同 wave の docs 修正。

## 総括

変更予定 file と概算差分:

| file | 概算 |
|---|---:|
| `orchestrator/campaign/s8b_ratified_freeze.py` | 50〜75行 |
| `orchestrator/tests/test_s8b_ratified_freeze.py` | 180〜280行 |
| `orchestrator/tests/test_backoff_extended_sweep.py` | literal 2行 |
| `tools/pegasus/b10_backoff_grid.sh` | literal 1行 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | 50〜100行 |
| `orchestrator/tests/real_repo_ratified_memo.py` | 説明5〜12行 |
| approval / active record | 新規各1行、末尾改行なし |
| 既存 README §5 / runbook / hooks README | 合計60〜120行程度 |
| decisions / worklog / 新 insight | 新規、実測量に依存 |
| J の作成・検証 script | 合計80〜120行程度、repo 外 |

P1〜P7 判定:

- **P1: 条件付き支持。** 判定式は支持。遅延 import の可用性は起動経路に依存する。
- **P2: 支持。** CAB は AI-Agent 件数に含めず、今回の A/X には付けない。
- **P3: 一部反証。** g1 の部分成功判定は可。全 gate 受理とは区別し、v1 の mismatch 予測は撤回する。
- **P4: 支持。** approver に委任・裁定日、approved_at に実 UTC 時刻を記録する。
- **P5: 支持。** A/X 込み tree の3 literal を更新し、算法・旧測定記録は保持する。
- **P6: 条件付き支持。** 実測後更新に加え、集約検査の検出力を補完する。
- **P7: 支持。** 3 test を改名せず、非適合 trailer の拒否として説明を更新する。

親の択一は **Q1 文法共有方式、Q2 P3 成功定義、Q3 集約負例の補完、Q4 P2 件数訂正**。本段ではテスト・変更・commit は未実施。