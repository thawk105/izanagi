# 段 1 brief — B-2 delta_min の接続確認 (wave: dev-wave-b2-delta-min-connection)

- 基準: local main `abc7085ae` (2026-09-17)。worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b2-delta-min-connection`、branch `worktree-dev-wave-b2-delta-min-connection`。
- 起点: 第 20 回 /rulings 全件 (2026-09-17) 項 12 (a)。fragment `docs/spool/decisions/2026-09-17-rulings-all-20260917-1.md` は commit `ad12ba35b` (branch `worktree-rulings-all-20260917`) にあり **main へ未 land・D 番号未採番** (着手時実測)。裁定文は command 引数と一致。正本 = D2049 + worklog entry 1533 (`docs/archive/worklog-phase3-0916-1533.md`)。

## 研究前進 (1 行)
8b/8c 主経路の正式測定を止めている gate (D649: `judge()` に production caller 無し、8c 事前登録 §6 条件 7) を開く前に、D1640/D2049 が定める **holdout 別 `delta_min = 0.03 × R_h`** が判定器へ届く経路が現物に在るか無いかを確定し、無ければ「何を足せば届くか」を裁定へ返す。完了判定 = 対応表 + 結論が insight に書かれ、段 6 レビューが対応表の各行を file:line で反証できないこと。

## scope
- **read-only 確認 + insight (docs)。実装面の差分ゼロ。** 検査・gate・台帳の新設なし (項 12 (b))。差異は直さず構造化して裁定へ返す。規律 2 を緩めない。
- 対象: `orchestrator/campaign/s8c_result_judge.py`、`orchestrator/campaign/s8c_preregistration.py`、`docs/phase3-8b-descriptor-design.md` §10.2、`docs/phase3-8c-preregistration.md` §4/§5/§6 条件 7、D1640、D2049、凍結側 (`s8b_holdout_freeze.HOLDOUTS`、`trial_registry.HOLDOUT_BINDINGS`、`output/s8b-freeze/holdout_freeze.json`)。
- scope 外: 接続の実装、照合 gate、`judge()` の production caller 追加、D1640 の値の記入。

## 確定済みユーザー裁定
- D2049: H1 = rr80、H2 = rr20、係数 0.03、向き on − off、単位 tps 絶対値、`R_h` は各 holdout 自身の stock 参照。凍結側は 1 byte も変えない。「判定器が受け取る対比パラメータは現状 1 組で、holdout ごとに別の `delta_min` を渡す接続は確認していない」。
- 項 12 (a)(b): 接続確認は検査を足さず現物で行う。参照 artifact の照合は新設しない。
- D649: `judge()` に production caller が無く gate は閉じたまま。8b §10.2: 値の記入は「型・有限性・符号・単位・向きを機械検証する consumer が実在するとき」に限る。

## 親の実測 (対応表の素材、段 2・3 の攻撃対象)
| # | 主体 | 現物 | 読み |
|---|---|---|---|
| 1 | 判定器 params | `s8c_result_judge.py:129-141` `_ContrastParams(n, delta_min, sd_max, unit, direction, source_binding)` | **1 組。holdout 軸を持たない** |
| 2 | 判定器 検証 | `:293-314` `_validate_contrast_params` — 型・有限・正、`unit == "throughput_tps"` (`:44`)、`direction == "on_minus_off"` (`:45`) | 単位・向きの照合主体は判定器 (D2049 と一致) |
| 3 | 判定器 適用 | `:1436` `for holdout_id in holdouts:` … `:1550` `mean_delta > float(params.delta_min)` | **H1 と H2 に同じ `delta_min` を適用** (generation 経路 `:1900` も同じ params) |
| 4 | 判定器 holdout の知識 | `:379-381` manifest の cells から `holdout_id` を 2 つ集めるだけ | 判定器は rr80/rr20 を知らない。H1/H2 のラベルは manifest 由来 |
| 5 | 事前登録 欄 | `s8c_preregistration.py:135-137` `SECTION5_ITERATION_CONTRAST_FIELD` = 「反復単位対比の判定パラメータ (H1 / H2: …)」 | 欄名が holdout 別を宣言 |
| 6 | 事前登録 validator | `:891-961` `_validate_iteration_contrast_parameters` — root keys `{"H1","H2"}`、block keys `{delta_min, direction, n, sd_max, unit}`、`delta_min` 有限・正、unit/direction は非空文字列のみ | **holdout 別 block。値の割り当て (どの R_h から) は見ない** (D2049 と一致) |
| 7 | 事前登録 現物 | `docs/phase3-8c-preregistration.md:208` 欄は「未記入」、`:176-180` 記入条件、`:248-256` §6 条件 7 (validator の production 到達 + judge 実装 + 3 表) | 値は未記入。記入解除条件は未成立 |
| 8 | 橋 | `_ContrastParams(` の生成元は `orchestrator/tests/test_s8c_result_judge.py:104,573` のみ。`SECTION5_ITERATION_CONTRAST_FIELD` の読み手は validator 登録 (`:968`) のみ。`s8c_result_judge` の production import は 0 件 (`s8c_preregistration_evidence.py:3050,3362` は名前 "result_judge" の静的 C07 検査で、import しない) | **§5 の H1/H2 block を `_ContrastParams` へ変換する経路は存在しない** |
| 9 | 凍結側 | `s8b_holdout_freeze.py:101-104` `HOLDOUTS = {"rr80": H1, "rr20": H2}`、`trial_registry.py:83-108` `HOLDOUT_BINDINGS` は同 dict から導出、`output/s8b-freeze/holdout_freeze.json` rr80→`candidate_id: H1` / rr20→`H2` | D2049 の訂正どおり。本 wave で触らない |
| 10 | D1640 逐語 | `docs/decisions.md:50294-50310` 「H1 = rr20、H2 = rr80」のまま (D2049 が追補で訂正、遡及改変なし) | 規律 7 どおり |

## 不変条件
- 実装面 (D95 決定 2) の差分ゼロ。docs-only は親が書く。凍結側・判定器・事前登録の bytes を変えない。
- insight は `authority: none` / `default_effect: no-state-change` を冒頭に置く。可変状態の正本にしない。
- 結論の型は「接続の有無」であり、「誤受理の実証」ではない (gate は閉じていて測定は起きていない、F965)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) **接続は不在**: 判定器は 1 組しか受けず、事前登録は holdout 別 block を要求するので、D1640/D2049 の holdout 別 `delta_min` を現行の `judge()` へ届ける経路は存在しない。これは「未接続」であって「逆接続 (H1 に rr20 の値が渡る)」ではない — 渡る先が無い。
- (P2) **現行形では届けられない**: `judge()` は manifest に holdout がちょうど 2 つあることを要求する (`:380-381`、generation 経路 `:682-683`) ので、「holdout ごとに `judge()` を 2 回呼び分ける」代替も現行契約では成立しない。届けるには (a) `_ContrastParams` に holdout 軸を足す、(b) 呼び手が 2 値を 1 値へ潰す (D1640 と非同値)、のいずれかを要し、どちらも裁定事項。
- (P3) **8c §6 条件 7 の文言は既に holdout 別を前提にしている** (「H1 / H2 について §5 に記入」) が、同条件が要求する judge の側は holdout 別を受けない。文書と実装の食い違いは「条件 7 が未充足」の一形態であり、新規欠陥ではない (D649 が既に gate 閉を確定)。
- (P4) 本 wave の成果は insight 1 本 + spool fragment (worklog) + decisions fragment は **不要** (裁定は出さない。裁定パッケージは insight に置き worklog fragment から指す)。

## 成果物
- `output/insights/2026-09-17/b2-delta-min-connection/README.md` (対応表・結論・裁定パッケージ候補・限界)。verbatim/ に段 2・3・6 の子成果物。
- `docs/spool/worklog/2026-09-17-dev-wave-b2-delta-min-connection-1.md` (entry 本文 + 次の一手)。
- decisions fragment は書かない (P4)。

## 分割方針
- 段 2: read-only plan 1 本 — 親の対応表を **見ずに** 同じ問いを file:line で独立導出させ、その後で親表と突き合わせる (親表は別 file で渡し「独立導出の後に読め」と指示)。
- 段 3: 並列 2 本 (lane sol = 正しさ境界: 受理集合・規律 2 への含意・(P1)(P2) の反証、lane luna = 整合・実効性: docs/decisions/prereg 文言との整合・(P3)(P4)・裁定パッケージの形)。
- 段 5 は無し (実装しない)。段 6: insight のレビュー 2 本 (対応表の各行を file:line で反証、結論の過剰断定)。変異 matrix は DW-S04 により免除。受入全走は免除しない。

## 追補 (06:53 JST、段 2 の走行中に親が既存被覆を検索して判明。段 2 plan 子は本追補を見ていない可能性がある。段 3 はこの追補込みで攻撃する)
- **(P2) は半分誤り。** 「(a) `_ContrastParams` に holdout 軸を足す / (b) 呼び手が 2 値を 1 値へ潰す、どちらも裁定事項」と書いたが、**D1481 (2026-09-02、ユーザー裁定) が (a) を採り (b) を却下済み** (「判定パラメータの分断は、判定側を holdout 別へ広げる方向で確定する。読み取り側を単一値へ寄せる案は採らない。実装の着手は D1326 のとおり完了証明層が着地するまで行わない」)。着手時期は D1326 (2026-09-01)。よって本 wave が裁定へ返す設計択は無い。
- **分断の事実そのものは既知。** worklog entry 1147 (T-1875、2026-09-01、`docs/archive/worklog-phase3-0901-1147-1148.md`) 停止理由 3 「§5 parser は H1/H2 の 2 根 key、judge は単一の `_ContrastParams` を 6 cell 全体へ適用、H 別の値を渡す経路が無い。この欠陥は T-1874 の完了条件に属する」。T-1874 裁定パッケージ (`output/insights/2026-08-28/t1874-s8c-section5-consumer/README.md`) 質問 2 も同じ。validator の production 到達と発火は T-1875 の 2026-09-14 insight (`output/insights/2026-09-14_t1875-delta-min-gate/README.md`) が実測済み。
- **(P4) を改める。** 裁定パッケージは新設せず、insight は「接続確認 (項 12 (a)) の結果 = 未接続、既裁定 D1481/D1326 の設計択と順序に変更を要する新事実なし」を書く。worklog fragment は T-1874 / T-1875 の本文を更新 (`更新`、base digest は main の現物) し、新規 T は切らない (裁定待ちが無いため)。
- **本 wave の純増 (これだけを insight に書く):** (1) 現行 main `abc7085ae` での接続不在の file:line 確認 (先行 insight は行番号の drift を明記しており、D2049 は「確認していない」と書いている)。(2) H1/H2 ラベルが各層のどこで workload (rr80/rr20) に束縛されるかの対応表 — §5 root key → validator (割り当ては見ない) → [空隙] → judge params (holdout 軸なし) → judge cells の `holdout_id` (manifest 由来) → `trial_registry.HOLDOUT_BINDINGS` (H1→rr80、凍結から導出) → 凍結成果物。これにより D2049 の訂正 (H1 = rr80) が D1481 実装後にどこで効き、どこが機械照合されないか (= 項 12 (b) が新設を却下した照合の位置) を 1 表で示す。(3) D1481 の実装 wave が扱うことになる副次項目の列挙 (裁定不要、設計メモ): `n` / `sd_max` / `unit` / `direction` も §5 では holdout 別 block にあるが判定器は単一 `n` で完全 block を検査する (`:1992`)、等。
- (P5) **上の (3) は裁定パッケージではなく設計メモ**であり、DW-G04 に従い実装しない。

## 受入・実測環境
- 受入全走: `tools/dev_wave_wait.py acceptance --lease-optional` (所在 = worklog 1595 と同じ計算ノード経路)。docs-only なので焦点走は無し、`python3 tools/check_docs.py` と provenance 監査を親が実走。
