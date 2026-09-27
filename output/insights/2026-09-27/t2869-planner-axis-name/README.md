# K0 planner の axis 名の書き違いによる提案拒否を、planner prompt への固定値の明示で直す ([T-2869]、2026-09-27)

## 0. 要約

- **問題:** 5 手法比較基盤 (T-2849) の K0 LLM 手法で、planner が出力の `axis` に `silo-backoff-magnitude` 以外の名前を書き、
  巡 tool (`tools/t2849_llm_round.py` の `cmd_coder`) の完全一致検査で提案が拒否され、提案機会 A を消費していた。
  MOCC 疎通 ([T-2849] 第 2 プロトコル、D2261) で 13 機会中 7 件、silo 試走 v2 ([T-2850]) で 36 機会中 6 件。
- **原因 (観測):** 巡 tool が組む planner prompt にも入力 JSON にも axis 名は無い。手掛かりは役割定義 `.claude/agents/planner-v4.md` の
  出力例の 1 箇所で、方向・magnitude の選択肢表記 (`increase|decrease|…`)・`<…>` の占位と並ぶ裸の文字列として書かれている。
  拒否時に planner へ届くのは `t2849_prior_observations.rejected_opportunities` の `reject_class = role-output` だけで理由は届かず、
  試走 v2 系列 2 では a = 3〜6 に `backoff-magnitude` が 4 連続した。
- **修正:** 巡 tool の planner 向け prompt にだけ次の 1 文を足した (両 protocol 共通)。検査・拒否時の A 消費・coder / critic prompt・
  `planner-input.json` の bytes・役割定義は変えていない。
  `proposal.axis は必ず `silo-backoff-magnitude` とする。この固定名は共通 header の hole marker 名であり、protocol 名を示さない。`
- **生死確認:** 記録済みの拒否 13 入力に、同じ model (`claude-opus-5`) の planner-v4 を修正前・修正後の prompt で 1 回ずつ呼び直した。
  巡 tool の検査を通った出力は **修正前 1 / 13、修正後 13 / 13**。拒否例だけを選んだ標本での効き目の兆候であり、一般の拒否率の推定ではない (§3)。
- **本比較 (T-2850) への扱い:** 効かせない。追補は置かない。本登録 §3.1 に基づいて本比較へ修正を適用するための「具体的な食い違い」を確定できないため (§4)。
  再提示用の択一を §5 に置く。

## 1. 観測 — 記録済みの planner 出力の axis 値 (read-only 集計)

| 出所 | 一致 / 全数 | 不一致の値 |
|---|---:|---|
| MOCC 疎通 (`t2849-mocc-conn-v1`、3 系列) | 6 / 13 | `initial-points-parameter-magnitude`・`tuned-parameter-magnitude` ×2・`single-parameter-magnitude`・`primary-tuning-parameter-magnitude`・`swept-parameter-magnitude`・`backoff-magnitude` |
| silo 試走 v2 (`t2850-trial-v2`、wh 3 系列) | 30 / 36 | `backoff-fixed-magnitude`・`backoff-magnitude` ×4 (系列 2 の a = 3〜6)・`primary-scalar-axis-magnitude` |
| 過去の K2 loop・B-5 対照 (repo の `output/insights/*/verbatim/planner-*.json`) | 15 / 15 | — |

- 材料: `output/insights/2026-09-27/t2849-mocc-conn/README.md` §5、`output/insights/2026-09-27/t2850-trial-v2-analysis/README.md`。生の逐語は repo 外の job dir
  (`dev-wave-jobs/dev-wave-t2849-mocc-conn/materials/`、`dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/materials/`)。
- K2・B-5 と K0 は知識射影・coder の契約・初期点の入力・prompt (B-5 は出力 key の集合を列挙する) が違う。15 / 15 は「役割定義の出力例が常に誤読されるわけではない」ことを示すだけで、
  K0 の拒否の原因を prompt の明示不足だけに帰属する根拠にも、率の比較にもならない。系列内の機会は独立標本ではない。

## 2. 変更 (commit は worklog 参照)

- `tools/t2849_llm_round.py` の `prompt()`: `role == "planner-v4"` のときだけ、共通文面の後・`入力 (逐語):` の前に上の 1 文を足す。`protocol` 引数は足していない。
- `orchestrator/tests/test_t2849_llm_round.py`: T1 = silo・mocc の planner prompt 全文を test 内の literal と照合 (固定文を含む)、
  T2 = silo・mocc の coder prompt 全文を従来の literal と照合 (固定文を含まない)、T3 = silo・mocc で非一致 axis の planner 出力を `cmd_coder` が
  `ValueError("invalid planner proposal")` で拒否し coder 入力を作らない。fixture `prepared()` に `run_coder` (既定 True) を足した (T3 だけが False を使う)。
- 実装は Codex author (段 5)、統合・検査は親。段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本 (いずれも Codex、read-only) を経た。
- 役割定義の改訂 (出力例の axis が固定値であることを文で明示する) は案として挙がったが、役割本文の改訂はユーザー承認事項 (D2256 項 7 の先例、[T-2870] と同じ扱い) なので本 wave では行っていない。
  B-5 の巡 tool (`tools/b5_llm_round.py`) も同じ完全一致検査を持つが、B-5 の登録の構成なので触れていない。

## 3. 生死確認 — 修正前後の prompt で planner-v4 を呼び直す

**手順 (repo 外、親が実行、2026-09-27 19:47〜19:53 JST):**

1. 拒否 13 機会の `round-<a>/planner-input.json` の raw bytes を読み、修正前の module (main `339d7c188`) の `prompt()` で prompt を作り直した。
   記録済みの `planner-prompt.md` と **13 / 13 が byte 一致**した (本番で planner に渡った prompt をそのまま再現している)。
2. 修正後の module (`88a57ed48`) で同じ入力から prompt を作った。修正前との差は **13 / 13 で固定文 1 文だけ**。
3. 各 prompt を `claude -p --agent planner-v4 --model claude-opus-5 --output-format json` に標準入力で逐語に渡した (fresh session、修正前後を交互に並べ 4 並列、各 1 回)。
   サブスクのログインで、API キーは使っていない。26 回すべて rc = 0・`is_error` なし・`modelUsage` は `claude-opus-5` のみ。
4. 最終応答の JSON (```json の囲み) を取り出し、巡 tool の `cmd_coder` と同じ条件 (key 集合・axis・direction・magnitude・非空文字列) で判定した。

**結果:**

| case | 系列 | a | 元の axis (拒否) | 修正前の再呼出し | 修正後 |
|---:|---|---:|---|---|---|
| 1 | MOCC balanced s1 | 1 | `initial-points-parameter-magnitude` | `initial-point-value-axis` | 一致 |
| 2 | MOCC balanced s1 | 2 | `tuned-parameter-magnitude` | `single-tunable-scalar-magnitude` | 一致 |
| 3 | MOCC balanced s1 | 3 | `tuned-parameter-magnitude` | `backoff-magnitude` | 一致 |
| 4 | MOCC balanced s1 | 4 | `single-parameter-magnitude` | 一致 | 一致 |
| 5 | MOCC read-heavy s1 | 1 | `primary-tuning-parameter-magnitude` | `initial-points-value-axis` | 一致 |
| 6 | MOCC write-heavy s1 | 1 | `swept-parameter-magnitude` | `primary-tuned-parameter-magnitude` | 一致 |
| 7 | MOCC write-heavy s1 | 2 | `backoff-magnitude` | `single-tuned-parameter-magnitude` | 一致 |
| 8 | silo wh s1 | 3 | `backoff-fixed-magnitude` | `backoff-fixed-wait-magnitude` | 一致 |
| 9 | silo wh s2 | 3 | `backoff-magnitude` | `backoff-magnitude` | 一致 |
| 10 | silo wh s2 | 4 | `backoff-magnitude` | `fixed-backoff-magnitude` | 一致 |
| 11 | silo wh s2 | 5 | `backoff-magnitude` | `backoff-wait-magnitude` | 一致 |
| 12 | silo wh s2 | 6 | `backoff-magnitude` | `backoff-magnitude` | 一致 |
| 13 | silo wh s3 | 1 | `primary-scalar-axis-magnitude` | `swept-parameter-magnitude` | 一致 |
| | | | **検査を通った数** | **1 / 13** | **13 / 13** |

**限界:**

- 標本は拒否が起きた入力だけを選んだもので、同じ系列内の機会は独立ではない。修正後の一般の拒否率や、本比較での発生確率の推定ではない。
- 各 prompt 1 回の呼び出しで、同じ prompt の呼び出し間の揺れは測っていない。
- 本番は親 session (`claude-opus-5`、B-5 の専用 settings) が Agent (`planner-v4`) を子として呼ぶ。本確認は `--agent planner-v4` の session を直接起動しており、
  model の exact ID は同じだが、system prompt の構成と settings は同一ではない。
- 最終応答から JSON を取り出す処理は本確認の集計器が行った。本番では親 session が逐語を保存し、巡 tool が読む。
- 生の出力と集計は repo 外の job dir (`/work/SFC/tanab/tmp/t2869-axis-name-20260927/probe/`、`summary.json`) にある。本節の表は `summary.json` の写しである。

## 4. 本比較 ([T-2850]) への扱い — 効かせない

**結論:** 本比較 (追補 3 §5 の固定 commit `299aa022e`、未発効) は現行の prompt のまま行う。本修正を本比較へ適用する追補は置かない。

**理由 (条文):**

- 拒否と A の消費は登録どおりである。基盤設計 (`output/insights/2026-09-22/t2849-comparison-harness-design/README.md`) §2.5 は空出力・schema 不合格・値域違反も A を 1 消費すると定め、
  §3.4 は親による候補の修正・再抽選をしない B-5 §4.1 の運用を継承し、§5.1 も A に空出力・不正出力を含める。D2261 項 7 も「救済せず A を消費する現行の扱いは変えない」とした。
  追補 3 §1 は試走 v2 の 6 件をこの扱いで記録し「本書は手法の定義を変えない (本登録 §3.1)」と書いている。
- 役割定義の出力例は axis に単一の文字列を示すが、固定値だと文では書いていない。これは契約の明示不足として要確認の点だが、例を固定値の指定と読めば、観測された別名は契約どおりに拒否された不正出力である。
  **本登録 §3.1 に基づいて本比較へ修正を適用するための具体的な食い違いは、現資料からは確定できない。** 役割定義を改訂するなら、それはユーザー承認事項である。
- prompt は手法の一部である。試走の発効束 (`output/insights/2026-09-23/t2850-trial-effect-bundle/bundle/t2850-trial-effect-bundle.json` の `role_definitions_and_role_prompts`) は
  「planner・coder・critic の prompt は固定 commit の巡 tool が組む」と定め、本登録 §10 も全役割の prompt を発効束に含める。未発効であることは、固定値 (追補 3 §5) を自由に変えてよい理由にならない。
- 本登録 §3.1 が禁じるのは結果を見た後の性能調整である。具体的な食い違いを正す実装修正には追補の道がある。今回はその食い違いを確定できないので、その道は使わない。

**効かせない場合に本比較の報告で開示するもの:** 系列・cell ごとの A 消費・B 到達・有効候補率 (A 基準と B 基準)・投入前拒否の分類と件数。
K0 の `role-output` のうち axis 名の不一致を識別できる形で示す。試走 v2 の 6 / 36 は先例として別記し、本比較の率に混ぜない。拒否で B に届かず score が欠けた系列は、その系列の結果として残す。
本 insight と決定の記録は、最終報告でのこの開示を代替しない。

## 5. 再提示用の択一 ([T-2850] の順番と規模の再提示に並べる)

| 選択 | 登録上の扱い | 費用と限界 |
|---|---|---|
| **A (推奨) 固定済み prompt のまま本比較** | 追補 3 §5 の commit を維持する。本修正は以後に登録・投入する K0 系列 (S2 MOCC・S3 の追補など) で使う | 再試走は不要。axis 拒否による A 消費と、B 未到達・score 欠測の可能性を受け入れ、§4 の開示を行う。試走 v2 では 3 系列とも A = 11〜14 で B = 10 に届いた |
| **B 修正 prompt を本比較へ適用** | 生成の前に追補で、固定 commit と prompt の変更・理由・結果を見た後の事後改訂であること (本登録 §0 の別欄報告)・影響系列を登録する。旧 LLM 3 系列を修正後の構成の分散 s_{wh,llm}・c(wh,llm)・ℓ(wh) の推定に使わず、LLM 系列を試走し直して §8 の規模と計算確認を再提示する | 試走 v2 の LLM 3 job の実績は **12.41 node 時間** (18,376 + 12,198 + 14,095 秒) で、これに LLM の直列時間が加わる。全 18 job の実績は 28.70 node 時間。いずれも将来の費用の保証ではない。T_c(wh) は非 LLM 12 系列だけから作る量なので、非 LLM 系列と測定方法を変えなければ流用の根拠を追補に書ける。s_plan は試走 v2 で random–sweep の対が最大だったが、修正後も同じになるとは保証できない |

- 追補 3 §2 の c(wh, llm) = 15,780.8 秒を 3 倍した 13.15 node 時間は、block job の按分と E_T の追加再計測を含む計画用単価の換算であり、再試走の費用ではない。

## 6. 変異 matrix

段 4 で実装前に登録した 4 変異を、変異用の独立 clone (固定 commit `88a57ed48`) で `tools/mutation_worktree.py` + `tools/mutation_harness.py` (runner = `tools/run_tests.py --force-dispatch`、
`test_t2849_llm_round.py` と consumer の `test_t2849_comparison_harness.py`) に通した。期待 node は login の自走 (注入 → 2 file の自走 → 復元、sha256 と clean を照合) で集めた。

| ID | 変異 | 期待 node (login 自走で観測) |
|---|---|---|
| m1-drop-axis-sentence | 固定文を削除 | `test_planner_prompt_exact_axis_instruction[silo]`・`[mocc]` |
| m2-wrong-axis-value | 固定文の値を `backoff-magnitude` に置換 | 同上 |
| m3-sentence-to-all-roles | role 条件を外し coder prompt にも固定文 | `test_coder_prompt_exact_existing_text[silo]`・`[mocc]` |
| m4-drop-axis-check | `cmd_coder` の axis 条件を削除 | `test_coder_rejects_wrong_planner_axis_without_input[silo]`・`[mocc]` |

baseline は 2 file とも緑、consumer test は全変異で緑。各変異の赤は登録した test の 2 node だけで、単一理由性を満たす。

### 6.1 dispatch final (2026-09-27 20:24〜20:27 JST、計算ノード)

- 結果: harness rc = 0、baseline PASSED (failed node 0)、**KILLED 4 / 登録 4**、MISMATCH・SURVIVED・TIMEOUT・PARSE_ERROR 0、4 件とも観測 node が期待 node と完全一致。変異 4 件の runner 所要の合計 109 秒。
- 束縛: `repo_head` = `88a57ed48293ff42e4a62af809134e2e57ba2e0b`、spec sha256 `af268559302b96e98b33d27d01c11322023eaea4c533a3b362fd1e97b84f6623`、
  結果 JSON sha256 `2f12952f7fb2962b635724cffb8f3ed446af228c11c169eeacb520ac458c621d` (repo 外の job dir `/work/SFC/tanab/tmp/t2869-axis-name-20260927/mutation-final-results.json`)。
