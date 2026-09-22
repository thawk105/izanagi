# [T-2797] 段 4 裁定 — 発効束の完成 (plan v2・変異事前登録)

入力: brief (`brief.md`)、段 2 plan (`codex/s2-plan.md`)、段 3 相談 A (`codex/s3-consult-A.md`、正しさ・整合)・B (`codex/s3-consult-B.md`、過剰・費用)、
Claude Code 公式 docs の確認 (subagent の `model:` は完全 ID を受理、alias `opus` は「update over time」、`ANTHROPIC_DEFAULT_OPUS_MODEL` で alias→ID を固定可、
解決順は起動時引数 > 定義の model > `CLAUDE_CODE_SUBAGENT_MODEL` > 親の model、`effort:` は `CLAUDE_CODE_EFFORT_LEVEL` に負ける。出典は sub-agents / model-config / cli-reference / setup の各 docs)。
段 4 直前に裁定 inbox を再走査 (最新 = 第 31 回 08:43 JST、T-2797 / B-5 への新裁定なし。項 1「開発の検査も 2 node 時間の線に数える」を本 wave の予算に適用)。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否・処置 |
|---|---|---|---|---|
| 1 | B-1 | repo 内の launcher・LLM tool の製品化は §12 の必須ではない (B-8 は repo 外 runner を束縛) | real (必須性の指摘として) | **不採用 (repo に置く)。** 下の D-1 に理由と「やらない理由の最も強い形」 |
| 2 | B-2 | driver に `block == (series-1)//4+1` の拒否条件を足す案は新しい runtime 検査 | real | **採用。** producer 側の拒否は足さない (consumer の既存検査と schedule の生成で足りる) |
| 3 | B-3 / A-N-e | B-8 の検査秒は extime 10 秒の trace。brief N-e の「read-heavy が W を大きく超えうる」は過大 | real | **採用。** brief N-e を訂正 (3 秒換算で 1 trace 約 148〜186 s)。「write-heavy が最軽」も一般化しない |
| 4 | B-4 | k=2 は換算例では成立するが、旧単価のストレス例では不足 | real | **採用。** D-7 で k=3 を推奨 |
| 5 | B-5 | 総 wall 倍率の分母は試走の raw job Elapse 総和 61,261 s とし、外挿値 (569 h) と混ぜない | real | **採用。** D-7 |
| 6 | A-1 / B-6 | alias 起動 + 事後記録では §4.1「可変 alias のまま発効させない」を満たさない。不一致時の扱いも未定 | real | **採用。** D-4 (起動構成で exact ID を固定 + 不一致時の登録済み処置) |
| 7 | A-2 | 役割別の推論・生成設定 (値・未指定・指定不能・観測不能) の採取が抜けている | real | **採用。** 束に役割別設定表を置く (D-4) |
| 8 | A-3 | P2 は workload 内で block と LLM 位置が完全に交絡する。逆順の組で均衡配置が作れる | real | **採用。** D-2 を相談 A の配置へ差し替え、block-stock は stage 2 |
| 9 | A-4 / B-7 | (b) の結論は感度分析の範囲に限る。D28 と「5 run の第 1 run 除外」は別操作 | real | **採用。** D-5 の文言 |
| 10 | A-5 | prompt の一般化で、狭い `<整数リテラル>` 指示の保持と「同時刻対照」の不正確な但し書きの訂正を変更一覧に入れる | real | **採用。** D-3 の変更一覧 |
| 11 | A-6 | proposal 公開順の変異は consumer から見て等価 | real | **採用。** 変異から外す |
| 12 | A-7 | 既知結果台帳の差分に閲覧者・閲覧時点の欄がない | real | **採用。** 束の §8 差分表に欄を置く (台帳 field ではない) |
| 13 | plan §6 | N1 は report の invalid では検出されず、B が少なく記録されて系列は欠測、比較は判定不能 | real (brief P6 の訂正) | **採用。** D-6 |
| 14 | plan §5 / 親 | (b) 53 session の最大差 0.6960%、1% 以上 0、CV 境界変化 0 | 親が独立再計算で一致 | **採用。** 試走 insight §6.2 の「fitness は動かない」は不正確 (最大 0.70% 動く) と新 insight に記す (旧 insight は書き換えない) |

## 決定

**D-1 (scope、P1 の改訂)。** 本走の投入に要る最小の実装を repo に置く。
- 実装単位 A: driver の purpose / cohort (既定 pilot、registered は定数 `b5-registered-v1`、producer 側の新しい拒否条件は足さない)、job body の
  `IZANAGI_S4_B5_PURPOSE` の検証と受け渡し、launcher の registered 入口 (D-2 の schedule を返す純関数、D-7 の walltime、job ごとの submit-tree、block・stage 指定の
  dry-run / submit)、登録簿の launcher の説明文の更新 (class・evidence は不変)。
- 実装単位 B: `tools/b5_llm_round.py` 1 file (template は file 内の文字列、別 dir は作らない) と test。試走版 `llm_round.py` の一般化と `record-models`。
- **採らない案とその最強の形 (相談 B):** §12 が要るのは bytes と hash と所在だけで、B-8 は repo 外 runner を hash で束縛した。repo 外の小さい投入 script と試走版 prompt 生成器の
  最小差分なら test・変異・受入の対象が減り、承認までの工数が小さい。**それでも repo に置く理由:** (i) job dir の原本は消える (F1034、K2 loop 原本の消失)。本走は数日に
  わたり 36 本の親 session が同じ tool を使う。(ii) §7.1 の配置性質 (6 順序 × 2、各 stage の LLM 4 本、block と系列の関係) は schedule 生成の test で確かめるのが最も安い。
  (iii) driver と job body の変更は test・変異・受入を要するので、launcher と tool を同じ変更単位に入れる追加費用は小さい。(iv) 既存 launcher の `_validate_job` は
  pilot 形しか受けず、repo 外 script は env 組立てを複製することになる。
- 変更しない: report、子 (`p3_s4_loop.py`)、pipeline、事前登録本文、role 定義 3 file (sha256 が `.codex/role-adapters/*.json`・`orchestrator/codex_roles/review_ledger.py`・
  test・図の provenance に束縛されている)、Tier0・lock・親数・待機時間・walltime 式。

**D-2 (schedule、P2 の改訂 = 相談 A の配置)。** 逆順の組 A = {LRS, SRL}、B = {LSR, RSL}、C = {RLS, SLR} (L = llm、R = random、S = sweep-matched、左から stage 1・2・3)。
workload 番号 w (write-heavy 0 / balanced 1 / read-heavy 2)、block b (1..3、系列 4(b−1)+1〜4b) で除く組を e = (w + b − 1) mod 3 (A 0 / B 1 / C 2) とし、残る 2 組を番号の昇順に
X・Y として、block 内の 4 系列 j = 1..4 に X の第 1 順序・Y の第 1 順序・X の第 2 順序・Y の第 2 順序を割り付ける。stage s ではその block の全 (w, 系列) について順序の s 番目の arm を走らせる。
性質: 各 workload で 6 順序が各 2 回、各 (block, stage) の LLM 系列はちょうど 4 本 (= p)、各 (w, b) で LLM と各 baseline の先後が 2 対ずつ。block-stock (workload ごと 1 job、
series = block) は各 block の stage 2 に置く (block の時間的中央)。次の stage は前 stage の全 job 終了後、次の block は前 block の全 job 終了から 1 時間以上後に投入する (手順。runtime 検査は足さない)。

**D-3 (LLM 巡 tool の一般化)。** 試走版からの変更は次に限り、束に試走 prompt との差分として載せる。
(1) 試走の label「試走 (T-2797、…、write-heavy 系列 1」「試走 (T-2797)」を header の cohort・workload・系列の label へ。(2) 動作点の文字列を `calibrated_perf(workload)` から整形 (rratio と workload 名)。
(3) 「系列開始 stock (適応 backoff) との同時刻対照は本系列の台帳にある」を「系列開始 stock (適応 backoff) は本系列の最初に同 job・同機体で逐次測ったもので、同時刻の対照ではない。台帳にある」へ訂正。
(4) coder の「B-5 試走の動作点と検証手順」を「B-5 本走の…」へ。(5) critic の run 内 CV が欠測のとき 0 と書かず「欠測」と書く。(6) 絶対 path (REPO・J・MAT・LEDGER・MANIFEST・KI_R2・LEAKPROOF) を引数へ。
(7) 知識射影の bytes 照合先を repo 内の T-2746 の `materials/knowledge-input.json` の写しへ。**保持するもの:** `<整数リテラル>` の生成指示 (共通受理文法より狭い、試走の構成事実として束に明記)、
B = 10 / A = 30 の開示、規律 6 の文、whiteboard・k2_critic_diagnosis の射影 (既存関数)、a と k の分離、初回は診断 key なし。
workload 別の leakproof context は試走版の動作点表・測定手順・冒頭説明だけを差し替え、知識集合は workload で選別しない。

**D-4 (exact model と生成設定、P4 の改訂)。** B-5 の LLM arm の親 session は `claude --model claude-opus-5 --settings <束の b5-parent-settings.json>` で起動する。
settings は `{"env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5"}}` (alias `opus` の解決先を固定する変数で、API キーではない。親 session の process にだけ入り、利用者の shell には入らない)。
role 定義 (`model: opus`、`effort: high`) はそのまま使い、Agent 起動時に `model` 引数を渡さない。`CLAUDE_CODE_SUBAGENT_MODEL`・`CLAUDE_CODE_EFFORT_LEVEL` は未設定であることを起動手順で確かめる。
`record-models` は巡ごとに role の会話記録から `message.model` の全件・client の版・記録 file の sha256 を記録し、予定 ID との一致を `matches_expected` として書く (拒否 gate ではない)。
**不一致時の登録済み処置:** 観測 ID が {claude-opus-5} と一致しない、または欠落した巡では親は proposal を公開せず、その系列は handshake の期限切れ (`proposal-wait-timeout`、分類不能欠測) で
終わる。救済・再抽選しない。束には役割別の設定表 (model 指定・予定 exact ID・effort・tool・温度等の生成 parameter は client が指定口を持たず観測もできない、と明記) を置く。
Claude Code の版は巡ごとに記録するだけで固定しない (alias の解決は env で固定済み)。

**D-5 ((b)、P5 の文言)。** 結論は「保存済みの試走 53 session では、登録した感度基準 (rep 1 を除いた 4 rep の中央値との差 ≥ 1%、CV 5% 判定の変化) から session 定義の変更を要求する差は
見つからなかった。現行の 5 rep 構成を維持する」に限る。warm-up 不要の一般証明とは書かない。rep 1 高値は lock 待ちのない 7 session でも 7 / 7 で残る (+0.95〜+2.41%) ので lock 待ちだけでは説明できない。
D28 (1 run 内の冒頭区間の破棄) と、5 本の独立 run の第 1 run を除く操作は別である。

**D-6 ((c) N1、P6 の訂正)。** コードは変えない。通常運用 (slot・attempt ごとの fresh layout、1 呼出し 1 genome) では `loop.py` の `done` が空で skip しない。到達しうるのは同じ slot を
同じ submit-tree で再起動する・既存 campaign を持ち込むなどの前提破れだけで、これは事前登録上も禁じた操作である。初回 attempt が投入後 skip した場合、B は 1 少なく記録され、report の件数照合と
sidecar 回収では検出されず、その系列は score 欠測となり、含む比較は判定不能になる (成果物影響 = 当該比較の判定不能。優越の誤判定は起きない)。retry attempt の skip は `submitted_once` により B を保持する。

**D-7 (k と総 wall 倍率、P7)。** k は 3 を推奨する (W = 63,777 s、W_stock = 16,341 s)。根拠: 換算の中心では read-heavy の LLM 系列 ≈ 24,500 s で k=2 に収まるが、旧単価のストレス例
(≈ 47,900 s) と、原提案を A = 30 まで使い切る場合の親待ち (30 × 780 s) を重ねた最悪例 (≈ 63,500 s) まで覆うのは k=3。k を上げても消費は実 Elapse で増えない (予約だけ)。
総 wall の管理上限は試走の job Elapse 総和 61,261 s (17.02 h) への倍率で書く。推奨倍率と数値は束の表で出所 (実測 / 換算 / 試算) を分けて決める。

**D-8 (親の起動)。** 自動化しない。親への指示文 template (md) を束に置き、D-4 の起動構成・系列ごとの fresh context・許す入力範囲・固定知識の所在・助言禁止・不一致時の処置を書く。

**D-9 (束の形)。** D2202 と同型: 実験構成の値を固定した draft JSON (`status: draft`) と表。承認後の発効 commit は構成値を変えず status と effective 節 (承認情報) を足す。自己 hash は書かない。

**D-10 (予算)。** 本 wave の計算 (焦点走・変異・受入) は job Elapse の実測で積算し、合計 2 node 時間未満に収める (第 31 回項 1)。超えそうなら投入前にユーザーへ確認する。

## plan v2 (plan からの差分)

- A: plan §1 のとおり。ただし §1.1 の registered 探索系列への `block == (series-1)//4+1` 検査は**足さない**。schedule は D-2 の配置。block-stock は stage 2。
  launcher の registered 入口は plan §1.3 の形 (`registered-schedule` / `registered`、`--block --stage --walltime-factor --submit-trees MAP.json ...`)。`k` は `0 < k ≤ 4.06` の有限 Decimal。
- B: plan §2 のとおり。ただし template は `tools/b5_llm_round.py` 内に置き、別 dir を作らない。prompt の回帰 test は、試走の round-1 prompt の bytes に D-3 (1)〜(4) の置換だけを
  手で当てた期待値 (renderer を通さずに作る) と、registered renderer の出力を照合する。`record-models` に `--expected-model` を足し、`matches_expected` を記録する (rc で拒否しない)。
- 親: 採取 (plan §3 の表 + 役割別生成設定表 + 既知結果差分の閲覧者・時点) と (b)(c) の記録、workload 別 leakproof context 3 file、親指示 template、`b5-parent-settings.json`。

## 変異事前登録 (DW-M01)

各変異は実装後に「同じ入力を拒否する層が前後・内側に無く赤理由が 1 つ」を確認し、できなければ登録から外して再照準する。M0 (comment 1 行) は SURVIVED を期待する。

| id | 対象 | 変異 | 落ちるべき node |
|---|---|---|---|
| MA1 | driver | registered の header の purpose を pilot にする | `test_b5_generator_contrast.py::test_registered_header_consumed_by_existing_report` |
| MA2 | driver | registered の cohort を pilot 定数にする | 同 `::test_purpose_cohort_mapping` |
| MA3 | driver | pilot の limits 第 2 文を変える | 同 `::test_pilot_header_bytes_unchanged` |
| MA4 | driver | run-block-stock が purpose を header へ渡さない | 同 `::test_registered_block_stock_header` |
| MA5 | launcher | 系列 → block の算式を 1 ずらす | `test_b5_contrast_launch.py::test_registered_schedule_coordinates` |
| MA6 | launcher | 除く組の回転 (+ b − 1) を外す | 同 `::test_registered_schedule_llm_four_per_stage` |
| MA7 | launcher | 組の第 2 順序 (逆順) を使わず第 1 順序を 2 回使う | 同 `::test_registered_schedule_six_orders_twice` |
| MA8 | launcher | block-stock を stage 1 に置く | 同 `::test_registered_stage_job_counts` |
| MA9 | launcher | submit-tree の割当 key から系列番号を落とす | 同 `::test_registered_job_specific_submit_trees` |
| MA10 | launcher | walltime の ceil を floor にする | 同 `::test_registered_walltime_decimal_boundaries` (積が非整数の k で) |
| MA11 | launcher | block-stock にも 21,259 s を使う | 同 `::test_registered_walltime_decimal_boundaries` |
| MA12 | launcher | random / sweep の job に K2 env を渡す | 同 `::test_registered_environment_exact` |
| MA13 | launcher | dry-run で mkdir する | 同 `::test_registered_dry_run_has_no_side_effects` |
| MA14 | launcher | pilot の env に purpose を足す | 既存 `test_b5_contrast_launch.py::test_four_qsub_argv_and_explicit_environment_are_exact` |
| MA15 | job body | purpose の値検査を外す | `test_p3_s4_loop_job_contract.py::test_b5_purpose_invalid_before_prebuild` |
| MA16 | job body | registered を driver へ渡さない | 同 `::test_b5_registered_purpose_reaches_driver` |
| MB1 | tool | balanced の context に rr5 を書く | `test_b5_llm_round.py::test_context_uses_calibrated_workload` |
| MB2 | tool | a を k として扱う | 同 `::test_rejected_opportunity_preserves_evaluation_number` |
| MB3 | tool | 初回に診断 key を足す / 片側だけに診断を渡す | 同 `::test_initial_and_inherited_inputs` |
| MB4 | tool | 欠測 CV を 0 と書く | 同 `::test_critic_missing_metrics_remain_missing` |
| MB5 | tool | 最初の assistant の model だけ採る (異なる ID が混在する fixture) | 同 `::test_models_collect_all_assistant_ids` |
| MB6 | tool | meta の agentType / toolUseId を落とす | 同 `::test_model_record_metadata_and_raw_hashes` |
| MB7 | tool | `matches_expected` を常に true にする | 同 `::test_model_record_flags_mismatch` |
| MB8 | tool | prompt の JSON 整形 (separators / indent) を変える | 同 `::test_registered_round1_prompt_golden` |
| M0 | driver | comment 1 行 | SURVIVED 期待 |
