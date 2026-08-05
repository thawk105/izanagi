> **改訂済み。本 brief は段 4 裁定 (`s4-adjudication.md`) によって 5 点訂正された。**
> 衝突したら段 4 裁定が優先する。訂正点: (1) 名乗りは「U-5 の ledger 側成分」までで
> **U-5 完了を名乗らない** (2) scope は 2 file でなく **3 file** (3) 「予算消費点を候補生成より前へ」は
> 「`BatchCommitted` より前へ」に限定 (4) (P4) の根拠を差し替え (5) (P2) の射程を縮小。
> 前提実測の erratum は `parent-measured.md` の E1〜E3。

# 段 1 brief — [T-244] P3 分割 wave 第 1 弾: reservation FSM (U-5)

wave: `dev-wave-t244-p3-reservation-fsm` / branch: `worktree-dev-wave-t244-p3-reservation-fsm`
起点 local main: `cfda4abe`。前提実測は同ディレクトリ `parent-measured.md` (N1〜N9) が正本。

## scope

`orchestrator/campaign/reflux_origin_ledger.py` の event FSM へ **pre-query reservation** を入れ、
予算消費点を `BatchCommitted` 受理時から**候補生成より前**へ移す。D96 の同一変更単位として
(1) 実装 (2) 境界テスト `test_v02_...transition_matrix` 他の追随 (3) 新 D の記録 を 1 wave で閉じる。
**含めない**: report v3 / origin-proofs sidecar / completeness / critic 後置 (U-8) /
ever-issued cell 台帳 (U-3) / 本番 provisioning。これらは別の分割 wave ((241) の次の一手)。

## 確定済みユーザー裁定 (前提。覆さない)

- **U-5 = (c)** 予約 event を FSM へ追加 + caller 制御流の両方 (worklog (236))。
- **D183** 本番 authority (`origins: []`) へ entry を 1 件も書かない。生死は fixture store 上だけ。
- **U-10 未決** 予算値が決まるまで production provisioning を解禁しない。
- **D96** 受理集合を変えるので新 D + 境界テストを同じ変更単位に含める。

## 親の provisional 裁定 (P1〜P6。**攻撃対象**であり、段 3 のレンズは全件を疑ってよい)

- **(P1) 予約を必須にする。** `IDLE` から直接 `BatchCommitted` を受理せず、`BatchReserved` を経る。
  optional にすると caller が予約を飛ばせて U-5 が名乗りだけになる。
- **(P2) 予約放棄の terminal 表現を同一変更単位に入れる。** `BatchReserved` 後に候補が作られない行が
  必ず生じる (provider 失敗・kill)。terminal が無いと origin は `OriginSealed` へ到達できず
  (N1: seal は `IDLE` 限定)、永久に seal 不能な相が生まれる。stock wire で埋めるのは禁止。
- **(P3) refund しない。** 放棄・失敗のいずれでも `iterations_used` / `queries_used` を減らさない。
  放棄分は `sealed` でも `tombstoned` でもない第 3 の計上先へ入れる。
- **(P4) U-5 の (b) 成分 (caller 制御流) は本 wave の scope 外。** N5 のとおり production caller が
  repo 内に存在しないため、書く対象が無い。8c 結線 wave の担当として裁定パッケージへ返す。
- **(P5) 予約・放棄の counter は pre-seal 射影 (`_preseal_semantic_sha`) に残す。** 候補内容でも
  結果 outcome でもなく資源消費の事実であり、cardinality は既に `open_batch` 長で観測可能である。
- **(P6) `OriginSealed` の counter 集合を拡張する。** 拡張しないと seal が query partition を
  証明できない。payload 形が変わるため、これも受理集合変更の一部として扱う。

## 不変条件 (破ったら停止)

1. 予算 counter は全 event を通じて**単調非減少**。減らす経路を作らない。
2. `queries_used == sealed + tombstoned + forfeited + pending` を全遷移後に維持する (N4 の拡張)。
3. 本番 authority JSON と `_initialize_locked` の production 初期化禁止を変更しない。
4. `MAX_APPROVED_GENERATIONS = 1`、D114 の cap=1、D166 の P4 FAIL は不変。
5. 既存テストの期待値を**緩めない**。赤なら実装が誤り。恒真な検査 (通らない正例) を作らない。
6. `DW-G04`: 正例は fixture store 経路 (N9) で作る。本番 provisioning は開かない。

## 成果物の形と `DW-G05` 成果物影響

- 差分 = `reflux_origin_ledger.py` + `test_reflux_origin_ledger.py` の 2 file のみ。docs は spool fragment。
- **実装しない場合の成果物影響**: certified 選択・材料レポート・試行台帳の**現在値は変わらない**
  (N5: production caller が無い)。変わるのは ledger の受理集合で、将来の caller が
  kill-before-commit で予算を消費せずに候補を引き直せる経路が開いたままになる。すなわち
  P3 の予算束縛は「名乗りだけ」に留まり、[T-244] の残り分割 wave が乗る土台が成立しない。
- **名乗りの上限**: 「origin ledger の FSM に pre-query reservation を入れ、fixture store 上で
  受理・予算消費・放棄・seal を実測した」まで。P3 充足・provisioning 解禁・kill-before-commit の
  実運用防止・候補 batch・cap 引上げは名乗らない。

## 分割方針

段 5 は所有素集合の 2 単位を**逐次**投入する — A = `reflux_origin_ledger.py` (module)、
B = `test_reflux_origin_ledger.py` (テスト。A の所有パス限定 patch を展開してから起動)。
分けるのは、境界テストの期待受理集合を実装子と別の頭で再導出させるためである (D96 の趣旨)。
段 6 は敵対レビュー 2 本 (正しさ境界 / 実効性・会計) を並列。
