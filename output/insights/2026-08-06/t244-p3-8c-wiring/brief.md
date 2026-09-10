# 段 1 brief — [T-244] P3 分割 wave: 8c への wiring (U-6)

wave: `dev-wave-t244-p3-8c-wiring` / branch: `worktree-dev-wave-t244-p3-8c-wiring`
起点 local main: `3143302b`。前提実測は同ディレクトリ `parent-measured.md` (N1〜N10) が正本で、
本 brief の主張が N と食い違ったら N を優先する。

## scope

`orchestrator/campaign/p3_autonomous_workload_trial.py::_run_workload` に
**origin ledger の caller 制御流 (U-5 の (b) 成分)** を入れる。すなわち generation ごとに
`BatchReserved` を**候補に影響する最初の role 呼出しより前**に置き、候補 commitment を
**`drive()` (= oracle query) より前**に `BatchCommitted` として固定し、`drive()` 後に
`BatchResultsPrepared` → `BatchSealed` を出し、候補が成立しなかった経路では
`BatchReservationAbandoned` を出す。origin 束縛が無いときは**一切 ledger を呼ばない**。

**含めない**: report v3 / origin-proofs sidecar / completeness / critic 後置 (U-8) /
ever-issued cell 台帳 (U-3) / 本番 provisioning / ledger 本体 (`reflux_origin_ledger.py`) の変更 /
`OriginSealed` の発行。(257) の指示どおり、sidecar・report v3・completeness は本 wave の完了まで起票しない。

## 確定済みユーザー裁定 (前提。覆さない)

- **U-6 = (a)** wiring host = 8c、**pilot 限定** (worklog (236))。生死実験の宿主は E 段既存 CLI で、
  これは liveness wave で既取得 (N8)。
- **U-5 = (c)** 予約 event + caller 制御流の両方。ledger 側 (a) は `2dc107ce` で実装済み、
  本 wave は残る (b) を担当する (reservation FSM wave の brief P4 が本 wave へ明示的に返した)。
- **U-4** 単一候補 × R replicate は `distinct_candidate_count=1` として記録し「候補 batch」と呼ばない。
- **D183 / U-10 未決** 本番 authority (`origins: []`) へ entry を 1 件も書かない。
- **D114** 承認上限 1、**D166** P4 FAIL は不変。
- **D179 §7** 名乗りの上限。

## 親の provisional 裁定 (P1〜P7。**攻撃対象**であり、段 3 のレンズは全件を疑ってよい)

- **(P1) ledger 本体を変更しない。** 差分は driver 側とテストだけに閉じる。ledger の公開 API が
  `_production_store()` 固定であること (N2) は防壁であって欠陥ではない、と親は判断した。
- **(P2) 注入 seam は `drive` / `preview` と同型にする。** `_run_workload` に explicit keyword の
  ledger client を足し (既定 = 実 ledger module 由来の実関数)、`run_trial()` は
  `claude-headless` provider のとき artifact 作成前に拒否する (N5)。
  テストは `_run_workload` を直接呼び、**fixture store 上の実 ledger** を渡す (mock ではない)。
- **(P3) 予約は planner 呼出しの直前、generation あたり 1 件。** `member_row_count = R`。
  pilot は **R=1** (8c は 1 generation につき `drive()` を 1 回だけ呼ぶ、N4)。
  R>1 は本 wave では作らない。
- **(P4) event の位置。** commit = proposal 書出し後・`drive()` 直前。prepare = `drive()` 直後。
  seal = prepare 直後で **critic 呼出しより前**。critic の位置そのものは動かさない (U-8 は別 wave)。
- **(P5) 放棄経路。** planner-invalid / coder-invalid / auditor-invalid / wall-budget / 例外の
  いずれでも、予約済み batch があれば `BatchReservationAbandoned` を出してから抜ける。refund しない。
- **(P6) `DW-G04` の発火 path。** 発火条件を満たす既存 artifact path = **fixture store
  (`_fixture_store_for_test`) 上の実 ledger + 8c の `--provider fixture --no-build` 経路**。
  production 発火は origin 不在 (N1) のため U-10 裁定まで起きない。
  親はこれを「dead code」ではなく「pilot 限定で発火し production では不活性な条件付き機能」と
  裁定した。**この裁定が本 wave で最も割れうる点である。**
- **(P7) 軽量版にしない。** 設計択一が割れるため段 2・3 を実施し、段 6 の敵対レビューも 2 本回す。

## 不変条件 (破ったら停止)

1. `orchestrator/campaign/reflux_origin_authority_v2.json` を変更しない (`origins` は `[]` のまま)。
2. **origin 束縛が無いとき、8c の既存受理集合・journal / report / proposal の bytes を変えない。**
   既定経路の artifact が 1 byte でも変わったら実装が誤り。
3. 事前登録 evidence contract の到達可能性 3 経路 (N6) を壊さない。
   `test_s8c_preregistration_predicates.py` が赤なら停止。
4. `MAX_APPROVED_GENERATIONS = 1`、D114 cap=1、D166 P4 FAIL、
   `certifying=False` / `arm_binding="declared-only"` (N7) を変えない。
5. 既存テストの期待値を**緩めない**。恒真な検査 (通らない正例・発火しない assert) を作らない。
6. ledger 呼出しの失敗を握り潰さない。fail-closed で trial を止める。
7. 予算 counter を減らす経路を作らない (refund 禁止)。

## 成果物の形と `DW-G05` 成果物影響

- 差分 = `p3_autonomous_workload_trial.py` + `test_p3_autonomous_workload_trial.py` の 2 file を
  基本とし、束縛の値型を別 module へ切る場合のみ 3 file。docs は spool fragment + 本 insight。
- **実装しない場合の成果物影響**: certified 選択・材料レポート・試行台帳の**現在値は変わらない**
  (N1: production caller が無く origin も無い)。変わるのは、U-10 が裁定された時点でも
  **予算を消費する caller が 1 本も無い**ため P3 の予算束縛が「名乗りだけ」に留まり、
  (257) が定めた順序 (8c wiring → sidecar / report v3 / completeness) の先頭が空くこと。
  すなわち後続 3 wave の起票根拠が立たない。
- **名乗りの上限**: 「非認定 8c pilot の driver に、予約 → 候補 commit → oracle query →
  結果 prepare → seal の caller 制御流を入れ、fixture store 上の実 ledger で受理・予算消費・
  放棄・seal を実測した」まで。**名乗らない**: P3 充足 / 部分 P3・P4 / 軸 (iii) の anti-oracle /
  provisioning 解禁 / kill-before-commit 対策の完成 / 「候補 batch を作った」/ 物理 query 数の証明 /
  規律 3 の還流完了 / cap 引上げ / 正式 H1・H2。

## 環境

- 静的検査・`--provider fixture --no-build` の軽量走行・codex 子は **Pegasus login ノード**。
- **pytest の全走・部分走は計算ノード** (runbook §7)。変異 matrix も同じ。

## 並列分割方針

- 段 2 プラン起草 = read-only codex 1 本。段 3 敵対 = 2 レンズ並列 (レンズ A = 発火 gate と
  恒真化、レンズ B = 順序と受理集合・既定経路の非変更)。
- 段 5 実装 = codex `role=author` 1 本 (driver とテストは密結合のため分割しない)。
- 段 6 = 敵対レビュー 2 本並列 + fix 1 本 + 変異 matrix + 受入全走。
