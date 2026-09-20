# [T-2384] 8c formal consumer の FC07 に terminal record の外枠 exact gate を入れた (D1730 の実装)

- 日付: 2026-09-20。wave branch `worktree-dev-wave-t2384-terminal-outer-shape`、base = local main `b7f970dfa` (着手直前)。
- 実装 commit: `2579b4638` (Codex author + Claude integrator)。変更は `orchestrator/campaign/reflux_formal_consumer.py` (+23 行) と
  `orchestrator/tests/test_reflux_formal_consumer.py` (+96 行) だけ。producer (`pipeline.py` / `wal.py`)・fixture builder・他 gate・reason code・`_wal_field` は 1 byte も変えていない。
- 裁定: D1730 (2026-09-07 ユーザー裁定、推奨どおり)。本 insight の設計判断は {{D:terminal-outer-shape-gate-impl}}。
- 逐語: `verbatim/` (段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定、author 報告、段 6 レビュー 2 本、変異 spec / 台帳、DW-O13 実測)。

## 1. 何を閉じたか

| | 変更前 (D1715 の後) | 変更後 |
| --- | --- | --- |
| terminal record (ordered projection の末尾) の outer key 集合 | 検査なし (root shadow・余分 key・欠落 key が通る) | `{variant, stage, env_tag, ts, payload}` と exact 一致を要求 |
| outer 値の型 | 検査なし | `variant` / `env_tag` は `str`、`ts` は bool でない有限数、`payload` は `dict` |
| terminal の重複 | 検査なし (`[trigger, commit, abort]` も末尾だけ見て通る) | projection 内で `stage ∈ {commit, abort}` の record がちょうど 1 件 |
| 違反時の reason | — | FC07 (新設なし) |
| `stage` の読取り | `terminal.get("stage")` (root だけ) | 変えない。exact key 集合の下で `_wal_field(terminal, "stage")` と同値になる |

helper `_wal_terminal_shape_valid(records)` を `_validate_wal_outcomes()` の直前に置き、`terminal = wal_records[-1]` の直後
(`build_attempt_id` 一致の前) で `_require(FormalReasonCode.FC07, ...)` する。D1665 が FC05C へ入れた `_wal_trigger` と同じ検査項目を
terminal へ写像したもので、定数は共有せず (`_wal_trigger` の bytes を変えないため)、payload の key 集合は閉じず (commit / abort で
payload の形が違う)、非 terminal record (build_start 等) の外枠は検査しない (D1730 の名指しは terminal だけ)。

`_wal_field` の root→payload fallback は残す。gate 後に死ぬのは `stage` の fallback だけで、`build_attempt_id` / `verify_configs` /
`reason` / `verify` は exact 外枠に含まれないので payload fallback が必須で残る (段 3 相談 A / B が親 brief の (P3) を訂正)。

## 2. 到達性の実測 (DW-O13)

gate が要求する値が実環境で到達可能かを、campaign の実走 log (`runs/wal.jsonl`) で測った (`verbatim/o13-measurement.md`、出力原本は同 dir の `o13-scan-output-campaigns.txt` / `o13-scan-a5-second-boot.txt`。走査 script は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/o13_scan_real_terminals.py` (sha256 71747179b303cc07a74ee00f71fcd31001b8ff5d89f7f112d66d8231f11ab520、読み取り専用の集計、実装面なので repo には入れない)。

| 母集合 | file | terminal record | outer key 集合 EXACT | ts float | variant / env_tag str | payload dict | attempt ごとの terminal 件数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| repo 内 `output/campaigns` (attempt 世代前) | 30 | 474 | 474 / 474 | 474 / 474 | 474 / 474 | 474 / 474 | (`build_attempt_id` 無し、測れない) |
| a5 second boot 実走 (2026-09-06、attempt 世代) | 2 | 16 (commit 16) | 16 / 16 | 16 / 16 | 16 / 16 | 16 / 16 | 1 件 = 16 / 16 |

過剰拒否の実例は 0。abort の attempt 単位の一意性は実測母集合に無く、producer の code 経路で確認した: `pipeline.py` の prebuild abort
(1775〜1786、emit して return)、通常 `_abort` (1912〜1932、1 件 emit して return)、verify 内 abort で評価終了 (2436〜2437)、abort 済みの
commit を拒む (2530〜2531)、recovery は active attempt にだけ ABORT を追記 (`wal.py` 2627〜2671)。`wal.py` 2355〜2371 は
「terminal を見た attempt を active から除く処理」であり、それ自体が二重追記を禁じる機構ではない (相談 A の A01 / A3)。

8c formal consumer が読む ordered WAL projection の実成果物は 8c 正式系列が未開通 (D1829) のため存在しない。projection は同じ
WAL record を 5 key へ射影するので外枠は同一である (`reflux_result_evidence.py` `_canonical_wal_interval`)。

## 3. 両入力経路への効き方

- canonical-list 経路 (`_canonical_wal_interval` が list を返す): `wal.parse_line` を通らないので外枠は上流で検査されない。本 gate が唯一の外枠検査。
- frame 経路 (`parse_line` を通る): 外枠の key / 型は上流で閉じるが、projection 内の terminal 件数は上流が見ない (`parse_line` は 1 行単位)。件数検査は frame 経路でも実効。
- 新 test はすべて canonical-list 経路 (`_rewrite_wal` が canonical list を書く)。frame 経路の実測は本 wave では行っていない。

## 4. test (9 関数 / 14 node)

| # | node | 入力 | 期待 | 新 gate で最初に落ちる条件 |
| --- | --- | --- | --- | --- |
| 1 | `test_fc07_rejects_terminal_root_attempt_shadow` | root `build_attempt_id` = 正、payload = 別値 | FC07 | exact keys |
| 2 | `test_fc07_rejects_terminal_extra_root_key` | root に `extra` | FC07 | exact keys |
| 3 | `test_fc07_rejects_terminal_missing_root_key[env_tag\|ts\|variant]` | root key 欠落 | FC07 ×3 | exact keys |
| 4 | `test_fc07_rejects_terminal_invalid_outer_type[ts-bool\|ts-str\|variant-int\|env-tag-none]` | 型違い | FC07 ×4 | 型検査 |
| 5 | `test_fc07_rejects_payload_only_terminal_stage` | `stage` を payload へ移す | FC07 | exact keys (既存 stage 判定も拒否 = 過剰決定、M06 の証拠に数えない) |
| 6 | `test_fc07_rejects_duplicate_abort_terminals` | `[trigger, abort, abort]` | FC07 | 件数 2 |
| 7 | `test_fc07_rejects_commit_before_abort_terminal` | `[trigger, commit 形, abort]` | FC07 | 件数 2 |
| 8 | `test_fc07_accepts_float_timestamp_abort_terminal_shape` | abort の `ts` = float | P6Unavailable | (通る) |
| 9 | `test_fc07_accepts_nonterminal_extra_root_key` | 中間 build_start に余分 key | P6Unavailable | (通る、非 terminal は検査しない) |

負例が手前の判定 (evidence 解決の attempt 混在検査 / FC05B / FC05C / FC06) で先に落ちていないことは、段 3 相談 A と段 6 レビュー A が
判定順で 1 件ずつ否定した (`_rewrite_wal` は root `build_attempt_id` があれば root を書き換えて payload を残す)。
既存正例 `test_exact_fixture_contract_reaches_only_p6_unavailable` / `test_fc07_accepts_production_commit_terminal_shape` は無変更。

作らなかった負例: 非 dict payload (root attempt 無しは resolver `_projection_attempt_id`、有りは exact keys が先に落とす)、非有限 ts
(canonical JSON に乗らない)、JSON 重複 key (`strict_json_loads` が拒否、record の重複とは別)、terminal の後に非 terminal
(既存 stage 判定と過剰決定、DW-M03)。

## 5. 変異 matrix (事前登録 = 段 4 裁定 §3、実装前に凍結)

runner は 12 file の焦点走 (`tools/run_tests.py --force-dispatch … -q -rf`)、`tools/mutation_harness.py --repo` を主 repo の登録 worktree
`.codex/worktrees/t2384-mutation` (commit `2579b4638`、branch `mut-t2384-mutation`) に直接当てた。probe 走 (全件 SURVIVED 登録で観測 node を
集める) → final 走 (完全集合) の 2 段。

**erratum (DW-O12):** 段 4 裁定は「D1009 の独立 clone を `mutation_worktree.py --source-repo` へ渡す」を主経路とし、clone の submodule 初期化が
拒否されたときの fallback を事前に書いていた。実測では `git clone --local --no-checkout` の clone に対し `dev_wave_submodule_init.py` が
`registered worktree does not belong to this repository` (rc=2) で拒否したため、事前に書いた fallback (登録 worktree + `mutation_harness.py --repo`) へ切り替えた。
拒否された clone は job dir に `mutation-source-clone-rejected/` として残した。

probe 走 (08:20〜08:33 JST、spec sha256 `c5887d0e…`、全件 SURVIVED 登録・`expected_nodes` 空): baseline PASSED、M01 SURVIVED、M02〜M09 MISMATCH (観測 node を収集)。
final 走 (08:35〜08:50 JST、spec sha256 `6032ea6274739cb18e4e598a9a4758ab16c93f352a8ebfaa76ace4d5606eb38b`、repo_head `2579b4638`、wrapper attempt 1、rc=0): baseline PASSED、**8/8 KILLED、期待 node 完全一致、M01 SURVIVED (期待どおり)、matches 9/9**。
probe の観測 node と段 4 の静的予測は 9 本すべてで一致した (M02 = M06 の 11 node + payload-only-stage、M06 は payload-only-stage を含まない)。

| id | category | 置換 (consumer 内) | 期待 | 結果 | kill node |
| --- | --- | --- | --- | --- | --- |
| M01 逐語 B-057-M5 | positive | `terminal.get("stage") == STAGE_ABORT` → `_wal_field(terminal, "stage") == STAGE_ABORT` | SURVIVED (等価) | **SURVIVED** (注入 diff sha256 `0ac58017…` で注入実在を確認) | 0 |
| M02 gate 無効化 + M5 | both-layers | `_wal_terminal_shape_valid(wal_records)` → `True` と M01 の置換 | KILLED | **KILLED** | 12 (M06 の 11 + `test_fc07_rejects_payload_only_terminal_stage`) |
| M03 superset 許容 | negative | `!= set(terminal)` → `not … <= set(terminal)` | KILLED | **KILLED** | 2 (root shadow、extra key) |
| M04 ts bool 許容 | negative | `not in (int, float)` → `not in (int, float, bool)` | KILLED | **KILLED** | 1 (`[ts-bool]`) |
| M05 件数検査除去 | negative | `return terminal_count == 1` → `return True` | KILLED | **KILLED** | 2 (duplicate abort、commit before abort) |
| M06 gate 無効化 | negative | `_wal_terminal_shape_valid(wal_records)` → `True` | KILLED | **KILLED** | 11 (shadow、extra、missing ×3、type ×4、重複 ×2) |
| M07 variant 型検査除去 | negative | `if type(terminal["variant"]) is not str:` → `if False:` | KILLED | **KILLED** | 1 (`[variant-int]`) |
| M08 env_tag 型検査除去 | negative | `if type(terminal["env_tag"]) is not str:` → `if False:` | KILLED | **KILLED** | 1 (`[env-tag-none]`) |
| M09 過剰拒否 (ts を int 限定) | positive | `not in (int, float)` → `is not int` | KILLED | **KILLED** | 1 (`test_fc07_accepts_float_timestamp_abort_terminal_shape`) |

M01 の生存は「B-057-M5 が露出した緩さ (root `stage` 欠落を fallback で救う) が、exact key 集合の下では到達不能になった」ことの実測である。
同じ緩さは M02 (gate を外した合成) でだけ再び現れ、新負例 `test_fc07_rejects_payload_only_terminal_stage` が殺す。
M06 (gate 無効化) を同 test が殺さないのは既存の `terminal.get("stage")` 判定が先に FC07 にするためで、事前登録どおり M06 の kill 集合に含まれない。
台帳: `verbatim/mutation-probe-results.json`、`verbatim/mutation-final-results.json`、spec: `verbatim/mutation-spec-probe.json`、`verbatim/mutation-spec-final.json`。

登録しなかった変異 (到達不能・等価): payload dict 述語の無効化、ts 有限性述語の無効化 (§4 の理由)。

## 6. 実走した検査

- 焦点走 12 file (計算ノード dispatch、job 11911.nqsv、`bnode007`、Elapse 26 s): **1016 passed / 0 failed** (pytest 20.47 s、48 worker)。
  file 集合は dispatch receipt `output/pegasus-dispatch/08b603691cbf531dca322b92e8ccbf88/receipt.json` の `request.args` が裁定の 12 file と一致 (レビュー A が確認)。
  新規 14 node は login の `--collect-only` で 14 件を確認。
- commit 後の全史 provenance 監査 `check_ai_provenance.py`: 11770 件、新規違反なし。
- 段 6 レビュー: A (正しさ境界・整合) must-fix 0 / nit 0、B (過剰・削除・変異帰属・pin 閉包) must-fix 0 / nit 1 (焦点走 log 単体に file 集合が無い → 上の receipt で補う)。fix 子は起動していない。
- 変異: §5。
- 受入全走・land: 受入全走 (`tools/dev_wave_wait.py acceptance`、計算ノード) と land は記録 commit の後に行い、結果は worklog エントリ (fold 後) と job dir の receipt に残す。本 README は受入前に凍結する。

## 7. pin 閉包

変更 2 file の変更前 sha256 / blob sha を tracked file 全体で検索して 0 件。fixture builder を変えないので `reflux_origin_fixture_baseline.json` と
`test_reflux_result_evidence.py` の golden は動かない (焦点走に両 test file を含めて緑)。consumer の構造検査
(`test_consumer_source_has_no_nonaborted_construction_or_success_variant`、production file 15 本) も不変。`acceptance_duration_ledger.json`
の新 node 未登録は allocator が重み 1 秒で扱うので更新しない。`docs/phase3-8c-wiring-design.md` 893 行 (表の項目 17) は説明であり pin ではない。

## 8. 限界

- certified 選択集合は変わらない。consumer は全検査通過後も `P6Unavailable` を返す (D1730 限界節)。変わるのは reason と receipt / evidence-root 参照だけ。
- rejected 側の本番 projection が FC07 で止まる件 (D1715 の限界節、witness 系 field の producer 不在) は解消していない。
- 新 test は canonical-list 経路だけ。frame 経路は上流の `parse_line` に依存し、本 wave では実測していない。
- abort の attempt 単位一意性は code 経路の確認で、実走の観測は commit 16 件のみ。

## 9. 工程の記録

- 条件 dispatch 13 (DW-O13、期限 = 段 2 前) を段 3 の後に読んだため、段 2〜4 の r1 成果物 (`verbatim/invalidated-r1/`) を無効化し、実測を済ませてから
  段 2〜4 をやり直した (F50 型の再発。r1 と r2 の結論は同じだったが流用していない)。
- 工数: codex 子 = plan 2 (r1 / r2)、相談 4、author 1、レビュー 2 (fix 0)。計算ノード job = 焦点走 1、provenance 監査 1、変異 probe (10 run) + final (10 run)、受入。
- 段 8 候補は worklog fragment に記録。
