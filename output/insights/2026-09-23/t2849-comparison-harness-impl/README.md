# 5 手法比較基盤 (S1) の実装と、標準評価経路の trace 保全口 ([T-2849] 単位 1〜7、[T-2853] (1)、2026-09-23)

- 位置づけ: 実装記録。設計の正本は D2220 と `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` (以下「設計 insight」)。本 wave の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: `worktree-dev-wave-t2849-comparison-harness` (起点 local main `3886a1fd3`、開始 gate fresh rc 0 は 2026-09-23 07:43 JST)。実装面は Codex author 3 単位 (D95)、role adapter は親が repo の renderer で生成 (D1861)。
- 依頼の逐語は `verbatim/request.md`。段 1〜6 の記録は `verbatim/` (§9)。
- **性質の断り:** 実装と単体試験・焦点走・変異までで、比較基盤を計算ノードで実際に 1 系列走らせてはいない (第 2 プロトコルの疎通と同じく scope 外)。B・A・k・系列数・費用上限の値は [T-2850] の事前登録で決める。

## 0. 要約

1. **5 arm が同じ単回評価経路を通る。** random・sweep・BO (逐次 GP-EI)・進化 ((1+1))・K0 LLM の各候補は、いずれも `p3_s4_loop --run-iteration` → 文法・帰属・検疫 → Tier0 → `run_campaign` / `pipeline.evaluate` を通る (手法で経路を変えない、D2220 項 1)。系列制御は B-5 の module を編集せず、兄弟 module `orchestrator/campaign/t2849_comparison_harness.py` に置いた。
2. **初期点 5・10 µs** は系列ごとに fresh に測り、B の外 (総評価数 k + B)、endpoint 候補に含める。endpoint は B-5 の `select_endpoint` を直接呼び、同じ cohort・workload の全系列 (初期点・探索・score・共有対照) で anomaly が出た値を失格にする。
3. **参照点 `p2_2_flag_opt`** (BACK_OFF=0 の exact 4 flags) を stock と同じ検証・計測へ渡す入口 `--reference-genome` を足し、block ごとの共有対照 (block stock + 参照) を測れるようにした。参照値は生成器へ渡さない (R0)。
4. **K0 LLM** は役割定義を改訂して D2220 どおりにした: planner-v4 と coder-v4-autonomous に、T-2849 の K0 arm に限り critic 診断 (`k2_critic_diagnosis`、D2155 の 6 field のまま) と初期点・投入前拒否の兄弟 key `t2849_prior_observations` を渡す。
5. **trace 保全口:** `pipeline.py` の検証 1 反復の一時 dir を、env `IZANAGI_TRACE_ARCHIVE_ROOT` があるときだけ `zstd -T0 -3` で file ごとに保全し inventory を書いてから消す。未設定なら挙動・出力とも不変。保全の失敗は原本を残し、評価結果・例外を置き換えない。WAL・proof chain・受領証の schema は変えていない。
6. 正しさゲート (verify・anomaly 即 reject) と trace の compile 時除去は変えていない (規律 1・2)。

## 1. 変更の一覧

| 区分 | file | 内容 |
|---|---|---|
| 評価入口 | `orchestrator/campaign/p3_s4_loop.py` | `--b5-slot` の接頭辞に `t2849-harness-v1|` を追加 (B-5 接頭辞の条件は不変)。`--reference-genome PATH.json` は `--stock-control` かつ harness slot のときだけ受理し、JSON は `{"protocol": "silo", "flags": {4 key}}` の exact 形。参照の canonical genome を search_config に入れ campaign identity を分ける。未指定時の config・genome は不変 |
| 保全口 | `orchestrator/campaign/pipeline.py` | `_run_one_repetition` の cleanup 前に opt-in 保全。`_compress_trace_archive` (zstd 起動だけ) と `_preserve_trace_directory` (配置 `ROOT/<campaign>/<variant>/<build-attempt>/<tag>/<tmp 名>/archive/<相対 path>.zst` + `inventory.json`、完了時だけ status complete) |
| 系列 driver | `orchestrator/campaign/t2849_comparison_harness.py` (新) | CLI `run-series` / `run-block-controls` / `aggregate`。台帳 schema `t2849-harness-ledger/v1` (B-5 と同じ header・番号付き events・series.json)。配置 `<cohort-root>/<workload>/<arm>/series-<R>/` と `<cohort-root>/<workload>/controls/block-<Q>/` |
| 生成器 | `orchestrator/campaign/t2849_generators.py` (新) | random (B-5 の重み表、名前空間 `t2849-harness-v1`)・sweep (28 点格子から 5・10 を除く 26 点を preimage 昇順)・BO・進化。標準ライブラリだけ |
| K0 巡 tool | `tools/t2849_llm_round.py` (新) | driver が公開する `request-<a>.json` を読み、planner / coder の入力を組み、出力を検査して `proposal-<a>.json` + `inputs-<a>.json` か `proposal-<a>.rejected.json`、`role-costs-<a>.json`、critic 後の `critic-costs-<b>.json` を公開する。役割の呼出しは親 session が行う |
| job body | `tools/pegasus/p3_s4_loop_pegasus.sh` | B-5・proposal・pair・fixture と排他的な harness 分岐 (env `IZANAGI_S4_T2849_*`)。prebuild 後に driver を 1 回起動し rc で終える。driver 起動直前だけ `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` (D2209 と同形) |
| 役割定義 | `.claude/agents/planner-v4.md`・`coder-v4-autonomous.md` | T-2849 K0 arm に限る任意入力の節 (K1・B-4・8c・従来の段 4 loop には適用しない) |
| pin 追随 | `.codex/role-adapters/planner-v4.json`・`coder-v4-autonomous.json`、`orchestrator/codex_roles/review_ledger.py`、`orchestrator/tests/test_reflux_originless_compatibility.py` | adapter は `orchestrator.codex_roles.spec.render_adapter` の出力そのもの (key set 不変、変わる pointer は `developer_instructions`・`source/sha256`・`review_ledger/source_file_sha256`・`semantic_digest` の 4 つ。段 6 レビューが独立に再計算して byte 一致を確認) |
| 試験 | `orchestrator/tests/test_t2849_*.py` 6 本・`test_t2853_trace_preservation.py`、既存 `test_ccbench_spawn_sites.py`・`test_p3_s4_loop_job_contract.py` の登録追随 | 既存試験の期待値は変えていない |

規模 (起点 `3886a1fd3` からの追加行): production 1,436 行 (役割文書・adapter を含む)、test 1,221 行。段 4 の上限 (2,000 / 1,600) の内。

## 2. 設計からの具体化 (実装で決めた値)

設計 insight に「案」とあった値と、実装で初めて決めた選択。いずれも [T-2850] の事前登録で確認・凍結する対象で、較正済みとは称さない。

- BO: 長さ尺度の格子 {0.25, 0.5, 1, 2}、信号分散の格子 {0.25, 1, 4}、観測雑音 (ln 1.03)^2、jitter 1e-10、平均は学習 y の平均を差し引く、同点は長さ尺度・信号分散の昇順。EI は潜在関数の予測分散で採点し、1..1000 を全列挙、同点は小さい v。header の `numerics` に記録する。
- 進化: λ = ln 4、丸め `floor(exp(ln v_親 + δ) + 0.5)`、δ = 0 は正の向き、親置換は真に大きいときだけ。
- 初期点: 定数 `INITIAL_VALUES = (5, 10)`、順序固定。
- session の rep 数: 評価口の固定 5 (`SESSION_REPS`) と、endpoint 再計測・参照の session 数 `--n-eval` を分けた。
- BO の失敗集合は outcome `rejected-tier0`・`build-failed`・`anomaly` (設計 §3.2 の列挙どおり)。`classify_slot` が候補起因 (`failure_class="candidate"`) として返す `rejected-preprocess`・`bench-aborted`・`aborted` は入れていない。S1 の機械生成 literal では前 2 者はまず起きないが、入れるかどうかは [T-2850] で決める論点として残す。

### 2.1 並走で land した [T-2850] 試走の事前登録 (D2231) との照合

本 wave の途中 (2026-09-23 11:07 JST、local main `4acf0350f`) に D2231 と `docs/search-repetition-trial-preregistration.md` (v1) が land した。親が本実装と照合した範囲では食い違いは無い。B = 10・A = 30・N_eval = 5 は driver の必須引数 `--b-limit`・`--a-limit`・`--n-eval` で渡し、初期点 k = 2 (5 → 10 µs) は driver の定数と順序に一致する。D2231 項 2 が「発効束で固定する」とした実装の定数 (BO の格子・jitter など) は header の `numerics` に記録される。経過時間の族 E_T に要る slot ごとの開始・終了・結果が使えるようになった時刻は event の `timing` に残る。試走の費用の参考として、`p2_2_flag_opt` の 3 秒 trace の verify 実測が `output/insights/2026-09-23/t2847-verifier-capacity/README.md` §4.3 にある (本 wave は測っていない)。

## 3. K0 LLM の入力 — 役割定義の改訂 (段 4 で親の暫定案を撤回)

段 1 で親は「役割定義を変えず既存契約内で K0 入口を作り、critic 還流と兄弟 key は別 T へ送る」を暫定案にした (planner-v4 が `k2_critic_diagnosis` を「K0/K1・B-4・8c へ適用しない」と明記し、coder-v4-autonomous の入力は 4 key だけだったため)。段 3 の相談 2 本はそろって反対し、親も real と判定した: 設計 insight §2.7 が K2 限定の射影を既に指摘して K0 への拡張を単位 4 に含めており、「裁定時に未見」は不正確だった (新しく分かったのは役割定義の sha 束縛の波及範囲だけ)。暫定案のままでは LLM の提案列・費用が D2220 の構成と変わる。そこで前例 [T-2783] (commit `4bd962643`) と同じ分担で、役割 .md は親、adapter・pin は Codex author と親の render で改訂した。key 名 `k2_critic_diagnosis` は D2155 の射影をそのまま使うために残した (K0 でも同じ 6 field)。

## 4. B-5 発効束との関係

B-5 発効束 draft (`output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json`、ユーザー承認待ち) の `files_sha256` は、本 wave が変えた `orchestrator/campaign/p3_s4_loop.py`・`orchestrator/campaign/pipeline.py`・`tools/pegasus/p3_s4_loop_pegasus.sh`・`.claude/agents/planner-v4.md` の sha256 を束縛している (wave 開始時は 4 つとも現行と一致、親と段 3 の相談 2 本が照合)。束の `target_commit_rule` は承認対象を「[T-2797] の land commit と、束の status・effective 節だけを変える発効 commit」とし、校正と本走をその発効 commit の固定 checkout で行う。**したがって発効 commit は [T-2797] の land commit を親にして作る必要があり、本 wave 以後の local main 先端で作ると束の sha と食い違う。** 本 wave は束を編集していない。

## 5. 段 3・段 6 の所見と裁定

- 段 3 (Codex read-only 相談 2 本): 相談 A (正しさ境界・整合) must-fix 2・should 3、相談 B (実効性・過剰) must-fix 1・should 4。重複をまとめた 10 件をすべて real と判定し採用した (役割定義の改訂、費用の producer→consumer の固定、N_eval と rep の分離、cohort 配置の固定、参照分類の負例、lock を job body だけに置く、`select_endpoint` の直接再利用、変異の単一変更化)。裁定の全文は `verbatim/s4-ruling.md`。
- 段 6 焦点走 1 回目 (統合 commit `16ee35040`): 3,631 passed / 10 failed。赤 10 件はすべて本 wave の新規試験の中 (試験の fixture・注入位置の誤り 7 件、実装側 3 件: 台帳 event の入れ子共有、巡 tool の文法検査漏れ、critic fixture)。既存試験の回帰は 0 件。
- 段 6 敵対レビュー: レンズ A (正しさ) NO-GO — must-fix 1 (参照分類が WAL の `src_token` と STOCK の一致を要求しない)・should 3 (M12・M18 の名指し試験の検出力、sweep 生成の計時漏れ)。レンズ B (過剰・削除) GO — should 1 (同じ計時漏れ)・nit 2。nit 2 件 (台帳 `append` を B-5 から継承できる、生成器の未使用の設定引数) は成果物を変えないので採用せず、ここに記録する。
- fix: U-B・U-C は 1 巡、U-A は 2 巡 (1 巡目の fix 子が、本 wave が足した試験の期待値の誤りを見つけて停止。親が「評価へ渡す context だけを検査する」と再裁定)。焦点再レビュー (Codex read-only) は closed 10 / partial 0 / regressed 0、新規所見 0 で GO。
- 焦点走 2 回目 (fix 後 `a4f7a2323`): 3,645 passed / 0 failed / 18 skipped。

## 6. 変異 matrix (DW-M01〜M08)

- 対象 commit `a4f7a2323` (fix 後の実装の最終 commit)。`main` をこの commit に固定した独立 clone (D1009) を `tools/mutation_worktree.py` の source にし、runner は `tools/run_tests.py --force-dispatch -q -rf` で本 wave の新規試験 7 file に限った (production file を変える変異で一律に赤になる contract loader 系の冗長 gate を対象外にするため)。
- 事前登録 (段 4 §5 の M1〜M25、段 6 の訂正で M12・M18 の位置確定と M26 追加) の 26 件と、docstring だけを変える対照 1 件。置換アンカーは生成 script が対象 commit の blob でちょうど 1 回現れることを assert した (同じ file の複数置換は累積適用)。
- probe (全件 SURVIVED 期待、09:38〜11:34): 対照は SURVIVED、26 件すべてで赤 node が出て、どれも事前登録の名指し試験を含んだ (帰属成立)。観測 node は計 131 件、全て ASCII。
- 本走 (観測 node を KILLED 期待に登録、11:43〜13:17): baseline PASSED、**26 件すべて KILLED (期待 node と完全一致)、対照は SURVIVED**。
- 名指し試験の外にも赤が出た変異がある (例: M19 の N_eval を rep 数に使う変異は 31 node。多くの fixture が N_eval = 2 を使うため)。いずれも同じ単位の意味のある試験で、冗長 gate ではない。
- spec と台帳は `verbatim/mutation-spec-probe.json`・`mutation-spec-final.json`・`mutation-probe.json`・`mutation-final.json`。本走の受領証 28 件の写しは wave の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-comparison-harness-impl/mut/final-receipts/`)。spec の生成 script (`s6/make_spec.py`、sha256 `25502a76…`) と帰属検査 (`s6/attribution.py`、`e04fb783…`) は親が書いた Python なので repo に入れず、同じ job dir に置く。

## 7. 計算の費用 (D2212 項 4)

- 開発の検査の job Elapse (実測): 焦点走 1 回目 120 s・2 回目 121 s (試験 3,6xx 件)、新規試験の collect 8 s、変異 job の単価の実測 13 s、変異本走 28 job 計 435 s。probe 29 job は、使い捨て作業木と一緒に受領証が消えて実測できない。同じ runner argv なので本走と同程度 (≈ 435 s) とみなす。以上の合計は ≈ 1,130 s ≈ **0.31 node 時間**。受入全走は記録 commit の後に走るので、ここには書かない。
- 段 4 は「≤ 0.99 node 時間」と見積もったが、変異 job の単価は実測していなかった。probe の後に単価を 1 job で実測してから本走を投げた。

## 8. 残り

- [T-2849] (2) MOCC の差し込み (単位 8、pin 前進と動作点の較正の後)、(3) 第 2 プロトコルでの疎通。いずれも本 wave の scope 外。
- [T-2853] (1) のうち「R1 の入力一式 (verifier の argv・repo commit・pin・patch・verifier module の sha256) を D2160・B-8 の runner と同じ組で残す」部分 (並走 wave が同項の文面に足した) は、本 wave の保全口に入れていない。保全口の inventory が持つのは file ごとの sha256・bytes・行数、workload flags、genome、trace binary の sha256 まで。
- BO の失敗集合に候補起因の `rejected-preprocess`・`bench-aborted`・`aborted` を含めるか (§2)。
- 段 6 レビュー B の nit 2 件 (§5)。

## 8.5 記録前の検査 (2026-09-23 13:2x JST、wave 木 = local main `fb12a492b` 取り込み後の merge `78ef5f205` + 本 insight と fragment 2 本)

- `python3 tools/check_docs.py` 違反なし、`python3 tools/spool_fold.py --dry-run` rc 0。
- 三軸語の走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc 1。hit はすべて main に既存の file で、本 wave の変更 file・新規 file との交差は 0 件。
- 本 insight・fragment の行末空白 0 件、verbatim を含め全 file が NFC。
- 全史の provenance 監査 (`python3 tools/check_ai_provenance.py`) は main 取り込みの merge の後で rc 0 (12,707 件、新規違反なし)。
- 受入全走は、この記録 commit と段 8 の後に走るので、ここには書かない。

## 9. 記録

`verbatim/` に段ごとの資料を置く: 依頼 (`request.md`)、段 1 brief、段 2 plan、段 3 相談 A/B、段 4 裁定、段 5 実装子の報告 3 本、段 6 レビュー 2 本・fix 裁定・fix 子の報告・焦点再レビュー、変異 spec と台帳。
