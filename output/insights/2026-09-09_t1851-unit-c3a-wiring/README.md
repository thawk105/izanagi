# [T-1851] 単位 C3a — 床値 campaign を certified launcher へ配線し、production result を v5 にした

branch `worktree-dev-wave-t1851-unit-c2`、base `21dfbe0f3` (継承 tip `38aed135f` + local main
固定 SHA `cbcdb6c91` の merge)。**land しない (D1341)。** 全単位が揃うまで branch 上の checkpoint に留める。

---

## 1. なぜ C3a なのか (単位の選び方)

前 wave (単位 C2) が返した裁定パッケージの**裁定 2**「契約 9 節『実値域は C2 が供給する』を満たす
単位分割」の結論 (a) に従い、**配線と実値域を新単位 C3 へ分けた**。ユーザーは単位選択を親へ委任し、
迷う点は codex へ諮るよう指示した。

- codex 相談 (read-only、`verbatim/consult-unit-selection.md`) も C3 を推奨し、依存順 `C → D2` を
  6 単位分割の正本 (`2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md:29,34`) で
  裏取りした。D2 (consumers/fixtures) を先行させると、供給元が無いまま fixture を固めることになる。
- 親の独立実測 (着手時点): `launch_floor_attempt()` の production 呼び手 **0 件**、
  `s8b_floor_campaign.py` (8,657 行) から attempt registry への参照 **0 件**、
  `s8b_floor_contract.py:36` が `RESULT_SCHEMA = LEGACY_RESULT_SCHEMA` (v4)。
- **F660 は発火しない** — main 側 `tools/pegasus/admission_registry.json` に
  `floor_campaign.sh` と `submit_floor.sh` が実在する。ただしこれは**静的確認であって
  qsub 成功の実測ではない** (段 3 レンズ A の指摘を採用した表現)。
- 段 2 plan が「現行契約と既存テストを保った C3 実装は成立しない」と結論し、未裁定 blocker 2 件を
  出したため、**C3a (配線・v5 producer・ordinal erratum)** と **C3b (実 campaign と値域 receipt)** に
  分けた。本 wave の確定成果物は C3a である。

## 2. blocker 2 件をどう閉じたか

### 2.1 marker の消費順序 (blocker 1)

`FloorAttemptReservation.consumption_marker` を launcher の pre-probe より先に用意すると、
holdout inspector が「completed session で pre-probe competing かつ marker あり」を
`attempt-ledger-coverage-mismatch` で必ず拒否する
(`s8b_holdout_admission.py:6733-6741`、launcher `:985-997`)。

段 2 と段 3 は (a) inspector 側で v2 の competing marker を許す / (b) launcher API を二段化する、の
2 案を出した。**(a) は受理集合を広げ D1660 の単調縮小方針に逆行するので却下した** (段 3 レンズ B)。

採ったのは (b) だが、**既存 production 入口 `launch_floor_attempt()` の署名も挙動も変えない**形に
小さくした。親の実測: 既存 test が 6 箇所で呼び、`test_s8b_floor_attempt_launcher.py:2222-2230` が
署名と source を pin し、`:1999` が competing 正例を production 入口で通している。
新設したのは 2 つだけである。

- `probe_floor_attempt_preconditions()` — launcher 私有の固定 probe を 1 回だけ実行し、
  **封印した一回限りの** pre-probe を返す。読み取り公開は `competing` と実 raw の immutable copy のみ。
  exact type・issuer state membership・owner identity・capability seal・one-shot を検査する。
- `launch_probed_floor_attempt()` — 封印 pre-probe を `probe_before` として使い、内部で probe を
  やり直さない。`probe_after` は封印 object が保持する capability で取る。

**blocker は「誰がいつ marker を消費するか」で閉じた。** campaign は phase 1 が競合と判定したら
marker を消費せず launcher を呼ばない。**inspector も marker 規則も 1 bit も変えていない**
(base / HEAD の blob が同一 `fab28e9d31b1602e012790ff6610ef2020eafd77`、段 6 レビュー A が検算)。

### 2.2 campaign retry ordinal の束縛 (blocker 2)

契約 v3.1 の identity 規定が `retry_ordinal` を `slot_id[4]` (recovery 軸) へ束縛していたが、
campaign の retry 軸は `slot_id[3]` (measurement ordinal) である。production registry は
`attempt_ordinal != 0` を拒否するため、**旧束縛は retry 側で恒真に 0 を強い、planned の `None` も
拒否していた**。追記訂正 `contract-v3.1-erratum-2.md` を発行し、
`retry_ordinal is None ⟺ measurement_ordinal == 0`、それ以外は等値、へ直した。

**これは単調な緩和ではなく受理集合の置換である** (段 6 レビュー RA-6 の指摘を採用した表現)。
旧誤軸の受理形 (planned の `0`、retry の recovery 軸 `0`) を新たに拒否し、
契約が要求する planned の `None` と retry の measurement ordinal を新たに受理する。
意図した軸への束縛強度は上がる — retry の `1..N` はこの訂正で初めて実際に束縛される。

## 3. 実装で初めて見えた欠陥 (静的読解でも敵対検査でも出なかった)

**2 件目以降の clean attempt を予約できなかった。** adapter の 3 遷移 (reserve / classify /
observation-start) が検証済み `evidence_by_digest` を捨てて plain v2 profile を core へ渡すため、
1 件目の sealed terminal 後に `[s8b-v2-terminal] v2 terminal requires the sealed evidence API` が
発火する。**1 件だけの fixture では原理的に検出できない**欠陥で、配線子が実装中に踏んで報告した。
3 遷移すべてに検証済み profile を伝播して閉じた。evidence の digest・canonical bytes・binding・
durable identity の検証は transition 前に従来どおり行い、plain profile の拒否 validator と型検査は
1 行も変えていない。

**これは受理集合の限定解除である。** 「無条件拒否だった sealed terminal 後の遷移を、
検証済み terminal 履歴に限って受理する」。段 6 レビュー A の指摘を採用し、
初出の「受理集合を広げていない」という表現は誤りとして訂正した。

## 4. 敵対レビュー 2 本が出した real 所見 4 件 (すべて閉じた)

- **競合分岐が観測していない probe 値を記録していた** (2 レンズが独立に検出、重大)。
  実測 raw を捨てて `{"rc": 0, "stdout": "", "stderr": "", "competing": True}` を合成しており、
  これは canonical classifier (`orchestrator/calibrator/runner.py:327-365`) が
  `inconsistent-output` として拒否する組合せだった。**成果物が実際には観測していない probe bytes を
  証拠として持つ状態**である。封印 pre-probe から実 raw を読む経路 (`read_floor_attempt_pre_probe()`)
  を足して正直に記録する形にした。実測 `{rc: 0, stdout: "competitor", stderr: "", competing: True}` と
  session / journal の 4 field が完全一致することを検算した。
- **cut-6 の M+A- replay に blocker 1 が残っていた。** crash で marker だけ残った状態を replay し、
  新しい pre-probe が競合だと marker を残したまま競合完了を書いていた。exact reason
  `cut6_replay_pre_probe_competing_existing_marker` で fail-closed 停止させ、
  certified 経路の crash-cut test を新設した (既存 cut-6 test は injected `measure_fn` の
  legacy 経路を通るため、この経路を踏まない)。
- **v5 prefix 被覆 test が result producer を通っていなかった。** 全 session 後に prefix を直接
  capture して同じ registry と比べるだけで、`assemble_result()` を通らなかった。live verifier は
  報告 `row_count` までの prefix 一致で受理するため、**producer が古い prefix を result に載せる
  変異でも赤にならない**恒真寄りの検査だった。通常 finalize 経路へ再照準し、1 件目 terminal 後の
  stale prefix を返す変異が赤になること (result `row_count` 6 / live 11) を実測してから戻した。
- **campaign が launcher の module attribute 経由で adapter 境界を迂回していた。**
  既存 guard は import 名と AST `Name` しか見ないため検出できないが、campaign が registry profile と
  core canonicalization の直接 consumer になっていた。狭い名前付き surface 10 個へ置換し、
  間接参照 0 件を AST test で固定した。**guard を緩める方向では解決していない。**

## 5. 変異が暴いた恒真な検査 1 件

事前登録した変異 `repetition=round_no - 1,` → `repetition=round_no,` を当てたところ、
**名前が謳う保証を持つはずの `test_registry_plan_maps_round_to_zero_based_repetition` が
赤にならなかった。** 最終 round を選んで `round-1` の存在だけを見ており、
0 始まりの像 `0..n-1` と 1 始まりの像 `1..n` の**共通部分から値を選んでいた**ためである。

性質自体は exact closure の検査が守っていた (この変異は probe で 8 node が落とした) が、
名前が謳う検査は恒真だった。境界値 (repetition `0` の存在と `n_sessions` の不存在) で発火する形へ
強化し、**強化後に一時変異を当てて実際に赤になることを実測**してから本走の期待 node を作り直した
(M3 の期待 node は 8 → 9 へ増えた)。**初回 probe の結果は `DW-M02` に従い消さずに残す**
(`mutation-probe-out.json` が初回、`mutation-probe2-out.json` が強化後)。

## 6. 変異 matrix

**13 件すべて KILLED。MISMATCH 0、SURVIVED 0、期待 node は完全一致。**
期待 node は推測せず、全件 SURVIVED 登録の probe で観測した完全集合を固定した (`DW-M08`)。

| # | 変異 | 期待 kill node 数 |
|---|---|---:|
| M1 | campaign が certified launcher へ dispatch しない | 10 |
| M3 | registry plan の repetition を 1 始まりにする | 9 |
| M6 | campaign が consumption marker の検証を飛ばす | 8 |
| M7 | journal が launcher terminal の改変 copy を emit する | **1** |
| M9 | production result の schema を v4 へ戻す | 4 |
| M10 | capture した prefix が最後の行を落とす | 4 |
| M11 | terminal identity を recovery 軸へ束縛する | 46 |
| M16 | terminal leaf が planned の `None` を拒否する | 57 |
| M17 | durable replay を recovery 軸へ束縛する | 2 |
| M18 | competing pre-probe でも marker を消費して launch する | 6 |
| M19 | competing 分岐が合成 probe payload を記録する | **1** |
| M20 | cut-6 replay が既存 marker の下で競合完了を書く | **1** |
| M21 | campaign が launcher の module attribute 経由で registry へ届く | **1** |

単一理由が 4 件あり、いずれも事前登録した狙いどおりの node だけを落とした。
M11 / M16 が広い (46 / 57) のは、1 つの gate に多数の検査がぶら下がっているためで、
複数 gate による過剰決定ではない。

## 7. 最終状態の実測

- 親の焦点走 (14 file): **1611 passed / 5 skipped / 0 failed**。
- 親の consumer 拡張走 (`DW-O26`、31 file): **3080 passed / 11 skipped / 1 error**。
  error は `from tests import` の file 選択走で出る既知の偽赤で (`DW-O18` が明記)、変更に帰属しない。
- 変異本走: **13 / 13 KILLED**、`repo_head` `3d3576882`。
- **受入全走 `child-green`: 22,654 passed / 68 skipped / 0 failed** (attempt 4、receipt 発行済み)。
  tested main `61171ddf0`、tested tip `4f9b8c081`。

### 受入 4 回の内訳と赤の帰属

| attempt | 結果 | 帰属 |
|---|---|---|
| 1 | 走行前に停止 | 親の argv 誤り (`--wave` が branch 名の接尾辞と不一致)。実装とは無関係 |
| 2 | 走行前に停止 | post-claim merge が受入所要台帳 1 file で競合 (main が node を追加したため) |
| 3 | 22,653 passed / 1 failed | **帰属** — 自走 harness を足した file が pytest 専用 allowlist に残っていた |
| 4 | **22,654 passed / 0 failed** | — |

**非帰属の赤は 1 件も出なかった。** attempt 3 の 1 件は本 wave に帰属し、
allowlist の 1 行削除で閉じた (fix 5)。

## 8. commit 列 (base `21dfbe0f3` から)

| commit | 内容 | 実装 / test |
|---|---|---|
| `cfb538af3` | A1: launcher の封印 pre-probe 二段入口 | +124 / +411 |
| `6a8223dd0` | A2: ordinal 束縛を実軸へ | +15 / +141 |
| `c0bb35af3` | fix1: launcher planned helper の訂正 | — / +111 -5 |
| `62b419fb4` | B: campaign の production 配線 | +436 / +535 |
| `adb740134` | fix2: adapter 3 遷移へ検証済み evidence profile | +21 / +361 |
| `197d529b9` | fix3: 敵対レビュー real 4 件 | +592 -207 (4 file) |
| `3d3576882` | fix4: 恒真な検査を境界値で発火する形へ | — / +30 -9 |
| `246ed2dd9` | 段 7 の記録 (insight・erratum・台帳 fragment 3 本) | docs |
| `dc1a28730` | 受入 post-claim の main 取り込み (台帳を和集合 22,483 件へ) | — |
| `4f9b8c081` | fix5: 自走 harness を足した file を allowlist から外す | — / -1 |

## 9. 収録物

- `s1-brief.md` — 段 1 brief (実測アンカーと pin 閉包、(P1) の攻撃対象)
- `s4-adjudication.md` — 段 4 裁定 + 変異事前登録 + 段 6 裁定 (追記)
- `contract-v3.1-erratum-2.md` — 契約 v3.1 の追記訂正 2 (ordinal 束縛軸)
- `mutation-probe-spec.json` / `mutation-probe-out.json` — 初回 probe (恒真な検査を暴いた回)
- `mutation-probe2-out.json` — 強化後の probe (期待 node の出所)
- `mutation-final-spec.json` / `mutation-final-out.json` — 本走 (13/13 KILLED)
- `verbatim/` — 単位選択相談、plan、敵対レンズ 2 本、実装子 3 本、fix 4 本、merge 解決、
  敵対レビュー 2 本の逐語
- `verbatim/prompts/` — 全子へ渡した prompt の逐語
