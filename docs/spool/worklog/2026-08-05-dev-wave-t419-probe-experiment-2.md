---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t419-probe-experiment
seq: 2
title: [T-419] probe 因果実験を実装して計算ノードで 1 回走らせた — 因果は未立証のまま fail-closed で停止し、止めた 2 つの環境事実を裁定へ返す (コード + docs、branch worktree-dev-wave-t419-probe-experiment)
---

## 本文

- **ユーザー裁定 U-1 (2026-08-04 /rulings) を実行した。** 走行 CPU・cpufreq driver・boost 設定・
  同居プロセスを束縛した probe 実験の driver、PBS wrapper、解析関数テストを実装し、
  計算ノード bnode138 で 1 回走らせた。**是正 (probe 本体・較正再取得・凍結 bytes と pin) は
  scope 外のまま 1 bit も触っていない。Pegasus campaign は開いていない。**
- **因果は立証も反証もされていない。** `execution_validity=INVALID` /
  `causal_verdict=NOT_EVALUATED` (probe_rc=3)。fail-closed で A0 の直後に停止し、
  因果の本体である A1 (pin sweep) は走らなかった。止めた 2 件は
  {{F:single-tenancy-unreachable-on-compute-node}} と {{F:unreadable-diagnostic-treated-as-fatal}} で、
  **いずれも再実行では解消しない環境事実**である。裁定パッケージは
  `output/insights/2026-08-04_t419-probe-causality/ruling-package.md`。
- **予備データ (A0 30 読み、arm は INVALID なので判定に使わない)。** 帯外はどの読みでも
  ちょうど 1 個で毎回 CPU 44、reader も 30/30 とも CPU 44。帯内値 1410 個はすべて厳密に 2101.0。
  **reader が一度も移動しなかったため「reader の CPU だから」と「CPU 44 が特別」を区別できない**
  — それを分けるのが A1 である。常駐デーモンが居た CPU 22 は一度も帯外にならなかった。
- **親の記述誤りを一次資料で訂正した。** 中間成果物で α を「K 回読み位置ごと最小」と短縮したが、
  裁定原文は「**走行 CPU を移しながら** K 回読み論理 CPU ごとに最小値を採る」である。
  予備実測が 0/6 で落ちたのは巡回を抜いた形であり、**α の否定ではなく巡回部分が
  load-bearing である証拠**として insight と裁定パッケージを訂正した。
- **段 3 の敵対レンズ 2 本 (29 所見) と段 6 の敵対レビュー 2 本 (18 所見) は全件 real で全採用、
  refuted は 0 件。** 段 6 は fix 3 巡 + 焦点再レビュー 2 巡 (1 巡目 NO-GO = closed 9 /
  partial 7 / regressed 2、2 巡目 NO-GO)。**焦点再レビュー 3 巡目は codex の利用枠切れ
  (回復予定 2026-08-08 12:37) で実行できず**、`DW-O16` の「3 巡上限 → 親が変異で裏取りして
  裁定して閉じる」経路で閉じた。
- **段 4 erratum-1**: 事前登録の読み数を 430 → 445 に訂正した (arm 一覧に含めていた A3+A2 の
  15 読みを規模欄が計上していなかった。arm を増やしたのではない)。
- **変異 matrix (事前登録 8 本 + 両層裏取り 1 本、計算ノード dispatch、baseline 両走とも PASSED):**
  KILLED 5 (M1 / M2a / M2b / M4 / M6、いずれも実際の赤 node が予測と一致)、
  KILLED 2 は node 列挙の erratum (M3 は 3 予測に対し実 2 = 過剰列挙、
  M5b は 1 予測に対し実 5 = 過少列挙で検出力は予測より強かった)、
  **SURVIVED 1 (M5a) は等価変異**だった — 条件を偽にしても直後の
  `elif attribution not in {"CLEAN", "ATTRIBUTION_UNRESOLVED"}` が COMPETITOR を拾い続け、
  受理挙動は変わらず診断文字列だけが変わる。`DW-M02` に従い両層同時変異で裏取りしたところ
  事前登録どおり 2 node が赤になり、**gate 自体はテストで pin されている**ことを実測で確定した。
  harness の赤 node 抽出が dispatch 経路で `None` を返したため、赤 node は job stdout 全文から
  親が抽出した (F71 の正本規則)。
- **新テストを pytest 専用 allowlist へ分類した。** `parametrize` 5 箇所と `monkeypatch` 16 箇所に
  依存する意図的な pytest 専用テストで、`orchestrator/tests/README.md` の allowlist 規約に
  そのまま該当する。自走 harness を足して meta-test を回避したのではない。
- **受入の 1 回目は自己汚染で赤だった。** `output/` を snapshot 比較する
  `test_s8b_floor_campaign.py` の 2 node が、走行中に親が同じ `output/insights/` 配下を
  編集したために失敗した。実装差分から到達しえない経路であり (`DW-O18`)、
  書き込みを止めてから単独再走で確認した。
- **段 8 の dev-wave 改善候補 2 件は、いずれも実装せず記録に留めた。**
  (a) 段 1 の前提実測が**実行環境そのものの実測を欠いた** — 本 wave は login ノードしか測らず、
  計算ノードに何が常駐し・どの sysfs が読めるかを job 投入まで知らないまま到達不能な合格条件を
  裁定した ({{F:single-tenancy-unreachable-on-compute-node}} の直接原因)。`DW-S01` へ
  「read-only 子には測れない実環境の事実は本走前に親が安価な 1 発で測る」を足したいが、
  `docs/dev-wave/` は 25,196 / 25,200 bytes で**残り 4 bytes** である。**上限引き上げは提案しない。**
  (169) の V5、(181) の `DW-O18` 追記に続く 3 例目で、解放は [T-454] が所有する。
  (b) `tools/mutation_harness.py` の赤 node 抽出が dispatch 経路で `None` を返し、`DW-M08` の
  「赤くなった test node を毎回記録する」を harness が満たしていない (本 wave は job stdout から
  親が抽出して代替した)。こちらは実装面の修正だが **Codex 利用枠切れで着手できない**。

## 次の一手差分

### 更新

- [T-419] **P1・実験は実装済み・1 回走行済み、因果は未立証 → 2 件の裁定待ち**:
  U-1 の実験 driver (`tools/pegasus/probes/t419_probe_causality.py`) と PBS wrapper は land 済みで、
  計算ノード bnode138 での初回走行 (888740) も証拠として凍結した
  (`output/env/pegasus/t419-probe-causality/0_888740.nqsv/`)。
  **実験は fail-closed で停止し因果は未立証** — 止めた 2 件
  ({{F:single-tenancy-unreachable-on-compute-node}} / {{F:unreadable-diagnostic-treated-as-fatal}}) は
  再実行では解消しない環境事実である。裁定パッケージ
  (`output/insights/2026-08-04_t419-probe-causality/ruling-package.md`) が求めるのは
  (a) Codex 利用枠の回復待ち (2026-08-08 12:37) か D105 免除か、
  (b) 単独性 gate と診断 snapshot の 2 点の修正可否。**U-2 (較正再取得と pin 更新) は依然 U-1 の後**で、
  受理集合・述語・凍結 bytes・pin は本 wave で 1 bit も動いていない。
  予備データは α の巡回部分が load-bearing であることを示す (β・γ は静穏ノードで通るが
  specificity 未測定)。一次資料 = 同 insight / D143 / F97 / F108
  base: 0e58bd958c9dcb8619755cd4fd27f836382067a6b1416d4899d01da2a9d50064
