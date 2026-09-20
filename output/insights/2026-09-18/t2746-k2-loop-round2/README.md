# [T-2746] 段 4 合成ループを 2 巡目へ進めた — 保存済み proposal-2 (`value=25`) を 1 回評価し、実測を proposal-3 へ戻し、同巡の agent 出力を機序仮説層 v3 で永続化した (2026-09-18)

wave: `dev-wave-t2746-k2-loop-round2` / branch `worktree-dev-wave-t2746-k2-loop-round2`
基点 main: `d2ebef7a407dc6be61622ed596cf08b8b518f606` (記録前に `60334d5bc` を取り込み)。
裁定: `docs/decisions.md` D2120 項 1 (2026-09-17 ユーザー裁定、択 A)。役割入力文書は D2104 項 4 の適用版
(2026-09-17 改訂以降に開始する走行)。機序仮説層 v3 の設計正本は
`output/insights/2026-07-16_layer3-mechanism-wiring-design.md` (T-2681 の着手条件 = agent 出力を生む loop 再走)。

## 一行で

**proposal-2 は既存経路で terminal verdict (serializable / certified / anomalies 0、687508.5 tps) を得て、その実測が
planner-3 / coder-3 の型付き入力になり、proposal-3 (`value=20`、既知値の再提案) が保存された。往復は 2 巡連続で閉じた。**
同巡で生まれた agent 出力 (critic-2 / planner-3 / coder-3) と proposal-2 の planner 出力は、新設した
`runs/agent_outputs.jsonl` に loop harness の取込み口から書かれ、層 3 材料レポートの `mechanism_hypotheses` が初めて非空で
双射検査を通った (`layer3_report.json`)。
**これは合成による改善や探索の有効性の実証ではない。** 新しい値は固定 backoff の初期値であって新しい CC 構造ではない。
`mechanism_hypotheses` は LLM (critic) の帰属記録であって機序の実証ではない。

## 投入は 2 本、評価は 1 本 (裁定の文言からの逸脱を正直に残す)

| attempt | request | 結果 |
|---|---|---|
| attempt-0001 | `4947.nqsv` | job body preflight 拒否 `allocation qstat evidence is not fresh` (Elapse 7 秒、driver 未起動、campaign 未接触)。**原因は親**: 投入直後に `qstat -f` の写しを evidence dir へ置き、job body が自分で書く file (`tools/pegasus/p3_s4_loop_pegasus.sh` 263〜265 行) と衝突した。`evidence/attempt-0001/job.stderr` |
| attempt-0002 | `4954.nqsv` | `driver_rc=0`、評価 1 本 (下表) |

D2120 項 1 は「評価 job 1 本」と「再投入なし」を併記する。評価は 1 本しか走っていないが、投入は 2 本であり、文言上の「再投入なし」からは
逸脱している。**再測定・再抽選には当たらない** (attempt-0001 は測定にも抽選にも到達していない) が、「再投入禁止への適合」とは分けて記録する。
裁定本文は書き換えず、事後承認を裁定パッケージ候補として返す (下の「裁定パッケージ候補」)。preflight 失敗を一律に予算外とする一般規則は
設計しない。段 3 の相談 A#6 と段 4 の裁定 (`reviews/s4-ruling.md`) に経緯を残す。

## 実測 — job `4954.nqsv` (attempt-0002)

固定 SHA の専用 submit-tree (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2/submit-tree`、HEAD `d2ebef7a4` = 投入時の
現行 main、tracked + untracked clean、CCBench `511c9538…`) から `tools/pegasus/README.md` §7 の 9 変数で投入。third-party は同 checkout へ
`fetch_third_party.py hydrate` で offline 供給 (cache-root `/work/1/SFC/tanab/izanagi-thirdparty-cache`、5 source)。
1 巡目の tree (`d97c423bd`) は使っていない。

| 項目 | 値 |
|---|---|
| request / `pbs_jobid` | `4954.nqsv` / `0:4954.nqsv` (Created 06:35:44 → Started 06:36:14 → Ended 06:43:21 JST、Elapse 432 秒) |
| `driver_rc` | **0** |
| campaign | `p3-s4-loop-s4-autonomous-409e13f8` (identity 5 key が同じなので 1 巡目と同 ID。新規 WAL、skip なし = `1 committed`) |
| variant / genome | `3dec27291054` / `silo\|BACKOFF_FIXED=25,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| verdict | **`serializable` / `certified=true`**、anomalies **0** (commits 445394 / aborts 71877) |
| bench | median **687508.5 tps**、2 反復 `[692403, 682614]`、run 内 CV 1.0068%、`settled=true` |
| abort 率 | 7.40% (T-2702 以降の集約: 偶数 reps では中央 2 件の中央値。1 巡目の 7.75% は速い側 rep の代表値で規則が違う) |
| `llc_miss_rate` / `ipc` | **null (欠測)** — `perf_observation.preflight` `status=unavailable` / `rc=2`。0 でも差なしでもない |
| 終端 / 停止判定 | `1 committed / 0 aborted / 0 skipped`、`outcome=certified`、`iteration=1`、**`continue`** |
| WAL | 5 record (build_start / build_done / verify_done / bench_done / commit)、sha256 `03ac8508…`; `loop_state.json` sha256 `03ebaf94…` |

投入前に login で通した production 検査 3 本 (`assert_closed_proposal_schema(..., coder_contract=CODER_CONTRACT_K2)` OK /
`validate_backoff_preflight("double now_backoff = 25;")` accepted / `load_proposal_file(..., coder_role="coder-v4-autonomous-k2")` OK、
負例 `25 + 1` は拒否) と、manifest の resolver digest (`396cd559…`、run-card の固定値と一致) は 1 巡目と同じ手順で再実測した。
`materials/knowledge-input.json` (sha256 `05f2b267…`) は 1 巡目と同じ射影である。

**1 巡目 (value 20、719324.5 tps、job 1216.nqsv、tree d97c423bd) との差 −4.4% は、時刻・tree・集約規則が違う非同時刻比較であり、
退行とも改善とも読まない。** 同時刻の対照 (stock、または同 job 内の別値) は本 campaign に無い。

## 還流 — critic-2、planner-3、coder-3 (各 1 回、予算どおり)

停止判定が `continue` だったので、critic → planner-3 → coder-3 と進めた。役割への入力は file に固定してから逐語で渡した
(`materials/critic-input-2.json` / `planner-input-3.json` / `coder-input-3.json`、prompt 全文は `planner-prompt-3.md` / `coder-prompt-3.md`)。
`current_perf` / `leading_indicators` は本走の `bench_done` から射影 (率は ×100)、whiteboard は本 campaign の `loop_state.json` の 1 件
(`whiteboard_for_planner`)、`delta_pct` は harness の設計 (`_DELTA_PCT_LIVE = False`) で null。

- **critic-2** (`verbatim/critic-2.md`、sha256 `d2b2ab77…`): digest (sha256 `a0a4c204…`) と WAL に指示めいた文字列は無い (規律 6)。
  **attribution: どの設計選択にも帰属できない** (campaign 内 1 点、stock 対照なし、非同時刻比較は根拠にしない)。機序の候補として
  「abort 1 回につき backoff 1 回、value 25 で thread 時間の約 34% が backoff spin (計測値ではなく導出)」を挙げ、
  **recommend R1 = decrease / large、候補 10** (刻み 5 の往復は floor 内の差を追い続けるため避ける)、R0 = 同一 job 内に stock 対照。
  逆方向 (increase) は推奨していない → 親の解釈 `prior_critic_reverse=false`。critic は `success` が certified の意味であって改善ではないことを明記した。
  出力の見出し形 (`## attribution` 等 4 見出し) は親が入力 JSON の `output_format_request` で指定した (harness の決定論抽出のため)。
- **planner-3** (`verbatim/planner-3.json`): `direction=decrease` / `magnitude=medium`。実測 (abort 率 7.4%、iteration 1 certified) と K2 記録の向きを
  根拠にし、欠測・機体差・集約規則差・2 反復の分散を自ら不確実性に挙げた。
- **coder-3** (`verbatim/coder-3.json`): **`value=20`**、`implementation="double now_backoff = 20;"`、`confidence=medium`、
  `classification=known_result_conditioned_derivative`、`instruction_like_content_detected=false`。K2 記録の 40→30 の向き (約 +7%、abort +1 pt 弱) を
  30 の下側へ外挿して 20 を選んだ、と説明する。

**`value=20` は run-card が名指しする既知値である** (1 巡目 proposal-1 と T-2581 が現行 pin で評価済み)。run-card の規定どおり「既知値の再提案」と
記録し、未評価値生成の成功には数えない。**再抽選はしていない。** coder の入力 (whiteboard は抽象、この campaign の loop_state は 1 件) には
20 が評価済みであることは載っていない — 同 campaign ID の 1 巡目は別 tree の WAL / loop_state であり、この tree の harness からは見えない。
critic の recommend (候補 10) も coder には届いていない (下の「閉じていないもの」)。

proposal-3 (`materials/proposal-3.json`、sha256 `7277e526…`) は production 検査 3 本を通した (schema OK / 文法 accepted / loader OK、
planner=decrease/medium、coder value=20、`prior_critic_reverse=False`)。**評価していない。3 巡目へ進んでいない。**

## 機序仮説層 v3 (T-2681) の実装と本巡への適用

実装は Codex author 3 単位 + fix 3 巡 (全 commit に `role=author` の Codex 行)。設計 §2 の 4 点をそのまま実装した。

| 単位 | file | 内容 |
|---|---|---|
| A0 `39b728324` | `orchestrator/campaign/agent_outputs.py` (新規)、`layout.py`、`tests/test_agent_outputs.py` (新規、二重 runner) | envelope 検証 (exact 5 key、stage 3 種、payload / provenance の必須 key、critic の output 5 key)、canonical bytes / sha256、JSONL reader (空行・未終端最終行・不正 UTF-8・duplicate key・完全重複・semantic 重複を fails-closed)、flock 内で既存検査 → 単一 write → file/dir fsync の durable append、`CampaignLayout.agent_outputs_file` |
| A1 `fcaab6f84` | `p3_s4_loop.py`、`tests/test_p3_s4_loop.py` | live 経路 (`--agent-inputs` 指定時に `drive_iteration` の入口停止後・評価前に planner/coder 2 event を追記、未指定は従来どおり) と取込み口 `--record-agent-output STAGE FILE --agent-campaign-dir DIR --agent-input INPUT.json [--agent-output-key] [--agent-variant] [--agent-digest] [--agent-wal-ref ...] [--agent-prompt]` (parse 直後に専用分岐、評価用 option と排他、site 解決より前に return = login で呼べる)。整合検査: stage↔key、役割 schema、`input_sha256` は harness が計算、K2 `knowledge_manifest_sha256` と受領証の一致、critic の digest 一致 (入力と campaign の両方)、variant の WAL 実在、`--agent-wal-ref` の実在。入力側射影 (`planner_context_payload` / `whiteboard_for_planner` / `project_whiteboard` / `_prepare_knowledge_campaign`) は AO を読まない (実行・不変・AST の 3 検査) |
| A2 `0b6a07d88` | `layer3_report.py`、`layer3_schema.json`、`tests/test_layer3_report.py` | `runs/agent_outputs.jsonl` を whiteboard と独立に読み (不在 = `mechanism_hypotheses_provenance: absent`、存在 = `agent_outputs`、部分 file・未知 stage・重複・snapshot 不一致は fails-closed)、全 envelope を `agent_outputs` 区画へ一次配置、`critic_attributed` だけを `mechanism_hypotheses` へ決定論射影 (`{variant, attribution 逐語, source_ref: ao:<sha>, refs, digest_sha256}`)、双射の期待側を独立に読んだ AO で拡張 (`ao:` prefix)、view の独立再射影一致・WAL ref 実在・variant 実在・`raw_markdown` からの再抽出一致。schema: `verifications.items` に `commit_witness` (integer 2 key) / `proof_surfaces` (X/P/I 3 値、protocol string\|null) を optional 追加、`mechanism_hypotheses` items 定義、`agent_outputs` / `mechanism_hypotheses_provenance` optional、`schema_version` v3 据え置き (D828)、`required` 不変 |
| fix 1〜3 `9da9f5dd5` / `185b593c5` / `f57eabeeb` | 上の 6 file + `tests/test_p3_b4_wiring_probe.py` | 段 6 レビュー所見 (下) の是正 |

**着手時の新事実 (N1):** 現行 renderer は本 loop 型の campaign を描画できなかった — `verify_done` の `commit_witness` (ee81c4311、2026-08-11) と
`proof_surfaces` (e4c949f08、2026-09-03) が schema に無く `additionalProperties` 違反 (1 巡目 campaign で実測、schema error はこの 1 件だけ)。
v3 の材料を出す前提としてこの 2 property を optional で足した (D829: view で消さない、D828: 版据え置き)。台帳に未記録だった。

**段 6 レビュー (2 本) と fix 3 巡:** must-fix = (1) critic 節抽出の規則が harness (改行消費 + rstrip) と renderer (行末 + strip) で不一致 →
親の dogfood でも `critic raw_markdown と節が一致しない` で赤 → `agent_outputs.extract_critic_sections` を両側で共有 (次行から次の unfenced `## ` 直前まで、前後 strip、CRLF)、
(2) fenced code block 内の偽見出し → fence 追跡で除外、(3) planner/coder の非 null variant の受理条件が harness (任意 stage) と renderer (commit) で違う →
両側とも「対象 WAL の任意 stage に実在」(裁定 A8 の逐語)、(4) provenance の主張限定を docstring / schema description に明記 (`mode` は記録方式、`ts` は記録時刻、
`input_sha256` は申告した保存 JSON の canonical sha256 で実送達の証明ではない)、(5) D830 の閉包検査を `update` 経路と `_view_row` の除外集合 (exact 2 key を pin) の
AST 導出へ。既知の赤 2 件 (既存の双射 message pin を A2 が変えた → 実装側で復元、新設 fixture の WAL topology) と、B-4 静的 inventory の
`.start` heuristic (F8、共有関数化で消滅)、module 数 pin 46→47 (F10、`agent_outputs` が `p3_s4_loop` の静的 import 閉包へ入った)、
入力側防壁テストの receipt 衝突 (F9) を含め、fix 後の焦点再レビューは **新規 must-fix なし・regressed なし** (`reviews/` に全文)。

**本巡への適用 (取込み 4 event、coder-2 は取込み不能):**

| 順 | stage | 出力 | 入力 (`input_sha256` の計算元) | variant | `ao:` ref |
|---|---|---|---|---|---|
| 1 | planner_proposed | `materials/proposal-2.json` の `planner` | 1 巡目 job root の `planner-input-2.json` (raw sha256 `9366671d…`) | `3dec27291054` | `e8d6a80e…` |
| 2 | critic_attributed | `verbatim/critic-2.md` | `materials/critic-input-2.json` (digest sha256 `a0a4c204…` を含む) | `3dec27291054` | `7248960c…` |
| 3 | planner_proposed | `verbatim/planner-3.json` | `materials/planner-input-3.json` (prompt `planner-prompt-3.md`) | null (未評価) | `47790668…` |
| 4 | coder_proposed | `verbatim/coder-3.json` | `materials/coder-input-3.json` (prompt `coder-prompt-3.md`) | null (未評価) | `4851c52d…` |

各 event の `refs` は本走の WAL 5 record の canonical ref (`materials/wal-refs.json`)。**coder-2 (proposal-2 の coder 出力) は取り込んでいない** —
1 巡目で coder-2 へ渡した実入力 JSON が保存されておらず、`input_sha256` を真に計算できないため (裁定 A4: `input_sha256: null` も再構成入力も採らない)。
取込み前後で `campaign.lock` / `runs/wal.jsonl` / `loop_state.json` / `s4_loop_digest.txt` / `knowledge_manifest_receipt.json` の sha256 は不変。
AO は `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/runs/agent_outputs.jsonl` (4 行、sha256 `804c62c7…`、repo へは複製しない)。

**材料レポート `layer3_report.json`** (sha256 `f6dca3b9…`、`--output-root <submit-tree>/output`、`--generated-from-head 8232c7e0a`):
`agent_outputs` 4 件、`mechanism_hypotheses` 1 件 (variant `3dec27291054`、attribution = critic-2 の逐語、refs 5、digest `a0a4c204…`)、
`mechanism_hypotheses_provenance = agent_outputs`、`source_refs` **10 = wal 5 + wb 1 + ao 4** (双射通過)、`verifications[0]` に `commit_witness` / `proof_surfaces`、
`noise_floor` は within/between とも `no-matching-env-record` (submit-tree に較正記録が無い。段 3 相談 B#7 の予告どおり)、
`admission_decision.admission_status = admitted` / `classification = admitted-new-schema`、`certifying_input = false`、`acceptance_receipt = null`、
`knowledge_provenance.knowledge_level = K2`。**この report は材料であって certifying 入力ではない。**

## 閉じていないもの (1 巡目と同じ)

- **critic の診断は次の生成の型付き入力へ届かない。** 届くのは実測 (`current_perf` / `leading_indicators`)、5 field の whiteboard、
  `planner_direction` だけ。critic-2 の「候補 10」に対し coder-3 は 20 を出した — この不一致は経路の限界を示す実例であり、本 wave は直していない
  (run-card の固定入力契約の外)。`prior_critic_reverse` の機械 consumer は `_fold_critic_reverse` と停止判定のみで、proposal-3 は評価しないので
  本 wave 内では消費されない。**v3 は報告層の記録であり、入力側へ還流する経路は作っていない (設計 §2-2、テストで固定)。**
- whiteboard の `delta_pct` は `_DELTA_PCT_LIVE = False` で常に null (規律 2/6 の防壁)。裁定パッケージの「同機体 2 点なので delta を書ける」は誤りだった
  (段 2 plan と段 3 相談が独立に指摘、brief を訂正)。新 submit-tree の `loop_state.json` は本 campaign の 1 件だけを持つ。
- perf 欠測、legacy critic のため B-4 ablation 非適格、`classification` の自己申告と呼び手宣言の非照合は変わらない。
- `input_sha256` / `mode` / `ts` は申告と記録時刻であって、role が実際にその入力を受け取ったことの証明ではない。旧実装との bytes 同一性は
  静的確認 (未指定時は capture / agent_record を渡さない) であって実測比較ではない。

## 変異 matrix (段 6、`tools/mutation_harness.py`、container worktree `t2746-mutcontainer` = f57eabeeb、runner = `run_tests.py` の 3 file
`test_agent_outputs.py` / `test_layer3_report.py` / `test_p3_s4_loop.py`、`--force-dispatch`)

2 走で確定した (DW-M07/M08): probe 走 (全件 SURVIVED 登録、観測 node を収集。spec sha256 `b4f07de5…`、attempt 1 は spec の
`timeout_seconds=3000` が dispatch 待ち契約 4200 を下回り起動前 rc=2、attempt 2 で完走) → final 走 (観測集合を完全集合として KILLED 登録、
spec sha256 `e61b9436…`)。**final: baseline PASSED (803 passed)、M0 SURVIVED (等価変異)、M1〜M11 KILLED、期待 node 完全一致 13/13、MISMATCH 0。**
spec は `mutation/spec-probe.json` / `spec-final.json`、要約 (期待・観測 node 全列挙) は `mutation/final-summary.json`。原本 (stdout 込み) は
job root の `mutation-probe2.json` / `mutation-final.json`。

| id | 述語 (壊すと赤) | 置換 | 観測 node 数 |
|---|---|---|---|
| M0 | 等価 (comment のみ) | `agent_outputs.py` docstring 1 語 | 0 (SURVIVED) |
| M1 | reader の stage 白名簿 | `if env["stage"] not in STAGES` → `if False and …` | 2 |
| M2 | 未終端最終行の拒否 | `if frames[-1]` → `if False and …` | 4 |
| M3 | semantic 重複 (ts だけ変えた再取込み) | `if key in semantic_seen` → `if False and …` | 3 |
| M4 | planner/coder を一次配置から落とす | `agent_outputs` 区画を critic だけに | 18 |
| M5 | view の二重計数 | `_report_primary_refs` が `mechanism_hypotheses` も数える | 19 |
| M6 | 期待 Counter を report 側から作る | `_assert_bijection` の期待側を `report["agent_outputs"]` に | 2 |
| M7 | view の独立再射影との比較を外す | `if False and report.get("mechanism_hypotheses") != _mechanism_view(...)` | 4 |
| M8 | 不在時 provenance | 不在でも `"agent_outputs"` を発行 | 92 |
| M9 | 入力 builder が AO を読む | `planner_context_payload` に `read_agent_outputs(...)` を挿入 | 17 |
| M10a | K2 外側 metadata の欠落 | live 追記で coder output から `knowledge_use` を落とす | 3 |
| M10b | `input_sha256` を出力 hash に替える | 取込み口の計算元を `output` に | 1 |
| M11 | verification の `commit_witness` integer 型 | schema を `["integer","null"]` に | 1 |

M8 の 92 node は provenance の view 検査が AO 不在の全 campaign fixture で発火するためで、赤理由は 1 つ (view の再射影不一致) だが
検出範囲が広い。M1 は reader 直接負例 (`test_agent_reader_unknown_stage`) と module 単体負例 (`test_unknown_stage`) の 2 層で殺され、
DW-M03 の意味で冗長 gate を含む (単独変異の証拠としては reader 側 1 本で足りる)。等価変異 M0 は注入後 diff を harness が確認した上で SURVIVED。

## 主張しないこと

- **2 巡が閉じたことは、合成による改善や探索の有効性の実証ではない。** 20 と 25 の 2 点の差は同時刻対照ではない。
- 新しい数値が出ても、**固定 backoff の初期値であって新しい CC 構造の合成ではない。** proposal-3 は既知値の再提案であり、未評価である。
- proposal-2 の `certified` は**候補間の certified な選択ではない**。
- `mechanism_hypotheses` は **LLM の帰属記録であって機序の実証ではない**。材料レポートは非 certifying (`certifying_input=false`)。
- `knowledge_use` / `classification` は role の自己申告であり、**K2 の利用因果を証明しない。**
- critic 診断の「保存」「入力への投入」「改善効果」は**それぞれ別である**。本 wave は「保存」を機械化した (v3)。
- **本経路は legacy critic を使うため B-4 ablation には非適格である。**
- `job rc=0` だけを成功の根拠にしていない。verdict と WAL の terminal record を見ている。
- 投入 2 本 / 評価 1 本の逸脱は事後承認待ちであり、承認済みではない。

## 裁定パッケージ候補 (3 件、本 wave は判定しない)

1. **attempt-0002 の事後承認** — D2120 項 1 の「再投入なし」からの逸脱 (親の操作ミスによる preflight 拒否後の再投入、評価は 1 本)。
   記録は上のとおり。preflight 失敗を予算外とする一般規則は設計しない。
2. **層 3 の v1 全文 reader** — 既存 v1 artifact 1 件 (`p3-s8a-trigger-loop-…3f72ecd5`) は変更前から 6 種の不一致 (版・必須項目・`noise_floor` 構造)。
   本 wave は v2 6 件 / v3 1 件の通過を確認し、v1 は触っていない (段 3 相談 B#10)。
3. **保存済み report と fresh 比較 consumer の整合** — `autonomous_trial_completeness.py` の比較射影は `generator.sha256` と新 optional 区画を保持するため、
   旧保存 report との一致は保証されない。旧 report の再生成・sha 差替えはしない (段 3 相談 B#10、段 2 plan §5)。

## 証拠の所在

repo 内 (本 dir):

- `evidence/attempt-0001/` — `job.stderr` (sha256 `4cfbe015…`)、`compute-result.json` (driver_rc 2)
- `evidence/attempt-0002/` — `job.stdout` / `job.stderr` / `compute-result.json` / `reservation.json` / `masstree-prebuild-receipt.json`
- `materials/` — proposal-2 / proposal-3、knowledge-input、leakproof-context-k2 (改訂版から作った K2 射影)、役割の入力 JSON 3 本、prompt 2 本、wal-refs
- `verbatim/` — critic-2 / planner-3 / coder-3 の逐語
- `reviews/` — 段 2 plan、段 3 相談 2 本、段 4 裁定、段 6 レビュー 2 本
- `layer3_report.json` — 本巡 campaign の材料レポート (v3 適用後、`mechanism_hypotheses` 非空)

**可逆最小正規化 (DW-S07):** `evidence/attempt-0002/job.stdout` は行末空白 2 行が `git diff --check` に抵触するため行末の空白 / tab を除去した
(可視文字不変)。原文 sha256 `e4288e94b229bc50334751023dff24e5363f017a85bb1e19e4a5aab3a6b01147` (12359 bytes)、正規化後
`aa270954d49af27d18eaeef0e3117d4a7ae4351e80daf09c33f04b11422a43dc` (12355 bytes)。`diff -w -B` で原文と一致する (実測 rc=0、2026-09-18)。
他の file は無変更の複製で、原文 sha256 は `job.stderr`=`da46ac82…`、`compute-result.json`=`8dc4062f…`、`reservation.json`=`37006a16…`、
`masstree-prebuild-receipt.json`=`457e6349…`、attempt-0001 の `job.stderr`=`4cfbe015…`。

**campaign WAL・`campaign.lock`・`s4_loop_digest.txt`・`runs/agent_outputs.jsonl` は repo へ複製していない** (`guard_bash` / `guard_write` の
防護対象)。原本は repo 外 job root `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2/` の下に残る:

- WAL / AO: `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/runs/{wal.jsonl,agent_outputs.jsonl}`
- checkpoint / digest / 受領証: 同 `loop_state.json` / `s4_loop_digest.txt` / `knowledge_manifest_receipt.json`
- job 出力の原本: `evidence/attempt-0001/`、`evidence/attempt-0002/`
- 各段の prompt・逐語・fix 3 巡の報告・dogfood log (`ingest-scratch*.log`、`ingest-real.log`)・変異 spec と結果

## erratum (2026-09-20 19:25 JST): 「原本は repo 外 job root の下に残る」は現況と異なる — submit-tree は撤去された

本文「証拠の所在」の `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/` は、2026-09-20 19:25 JST の
cleanup 引き渡し script の退避不備 (退避 tar が空のまま撤去) により消失した。同 job dir の `scratch-campaign/` (2026-09-18 08:00 の
dogfood 用写し) の `runs/wal.jsonl` (`03ac8508…`)・`loop_state.json` (`03ebaf94…`)・`s4_loop_digest.txt` (`a0a4c204…`)・
`knowledge_manifest_receipt.json` (`c42dc712…`) は本文の sha256 と byte 一致し、原本の写しとして使える。**`runs/agent_outputs.jsonl`
(4 行、`804c62c7…`) の原本は消失** (scratch 側は別走 `1866ebc8…`)、`campaign.lock` は本文に sha 記載が無く照合不能。
本文の値・結論は変えない。事故の記録と損失表は `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`。
