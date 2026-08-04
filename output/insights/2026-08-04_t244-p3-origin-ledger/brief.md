# 段 1 brief — [T-244] D121 P3: origin ledger

## scope

新規 leaf 1 本とそのテストで、origin ledger に P3 の 4 性質 (**単一 in-flight・CAS・crash replay・
削除耐性**) を実装する。P1 (固定 5-bit IR・正準 emitter) と P5 (provider 注入・role 間 session 共有・
未予約 token) の面には触らない。既存 consumer (`wal.py` の `WAL_STAGES`、`layer3_report.py`) へは
**結線しない**。

## 確定済みユーザー裁定 (一次資料で実測、2026-08-04)

- **予算値 (§8 択一 1)** = 「択一 3 の結論を待ってから再導出する」。択一 3 は確定したので着手条件は
  成立したが、**値そのものは未導出**。よってハードコード禁止・後差し可能にする。[T-244] U4 の下限式
  `Q >= 1 + 32R + E_min` は draft 候補値 `Qmax=2` と両立しないことが確定済み
- **origin authority (§8 択一 6)** = **裁定済み**。「repo 内 tracked registry から始める。
  『同一 UID の caller からの秘匿は不可』を残余として明示する」(archive worklog (126))
- **軸 (iii) / batch 事前凍結 (§8 択一 3)** = **必須に裁定済み**。P4 は無条件義務へ移った。
  本 wave の scope 外だが、ledger の event 文法が batch freeze を**閉ざさない**ことを条件にする
- **親 brief の前提訂正 (command 引数への訂正):** 引数は「P10 が未裁定」としたが、P10 の 3 要素の
  うち **origin authority と軸 (iii) は 2026-08-03 (126) で裁定済み**で、未確定は**予算値だけ**である。
  指示 (値をハードコードせず後差し可能にする) は変わらず有効であり、U4 の下限式がそれを補強する

## 不変条件

- 受理集合・certified 選択・材料レポート・proof chain・凍結 bytes はいずれも不変 (consumer 未結線)。
  `FROZEN_MANIFEST` は `output/` の 23 path のみで source leaf は対象外 (実測)
- `MAX_APPROVED_GENERATIONS = 1` (D114) は変えない。**「P3 を充足した」とは名乗らない**
- 削除耐性は主張の上限を明示する。全削除の検出は外部 anchor に依存し、同一 UID の改竄は防げない

## 親の provisional 裁定 (攻撃対象)

- **(P1) 削除耐性の anchor を tracked registry に置く。** registry に origin が開かれている以上、
  local ledger の全削除は「予算 0 への reset」ではなく **fail-closed な使用不能**になる。
  攻撃面: registry も同一 UID で編集可能であり、「検出」でなく「git 追跡下へ置く」に過ぎないのでは
- **(P2) 単一 in-flight の粒度は「予約 slot 1 件」とする。** 択一 3 の batch freeze は別 slot 種として
  後付けできる形にする。攻撃面: batch 必須化で slot 単位の in-flight 制約が恒真化しないか
- **(P3) 新規 leaf に閉じ、WAL と `layer3_report.py` へ結線しない。** 攻撃面: `DW-G04`・D115・
  D122 決定 (4) の「結線しない保証は発火しない」と同型ではないか。本 wave は「保証」を名乗らず
  「P3 の leaf 契約の実装」と名乗ることで分ける — この線引きが成立するかを攻撃せよ
- **(P4) 予算は leaf が値を持たず、caller 注入の immutable policy として受け取り、欠落は fail-closed。**
  攻撃面: 既定値ゼロが実質的な既定値 (無制限 / 即枯渇) として振る舞わないか

## 成果物の形

`orchestrator/campaign/reflux_origin_ledger.py` (新規 leaf) と
`orchestrator/tests/test_reflux_origin_ledger.py`。docs は spool fragment (worklog / decisions) と
`output/insights/` の逐語。

## 成果物影響 (DW-G05)

実装しなければ P3 は無条件義務のまま未充足で、cap-lift (`MAX_APPROVED_GENERATIONS > 1`) が開けられず、
8c 正式系列 H1/H2 ([T-324]) の複数世代設計が着手できない。実装しても**本 wave では certified 選択・
材料レポート・proof chain の値は 1 つも変わらない** (consumer 未結線)。

## 既存被覆と純増検出力 (実測)

`test_campaign_claim.py` = `O_EXCL` one-shot claim、`test_bench_first_real_wal.py` = WAL tail 切断修復。
**単一 in-flight slot・CAS・event 列の idempotent replay・ledger 削除 / rollback 検出はいずれも未被覆**
(grep で 0 hit)。純増検出力はこの 4 vector に限る。

## 分割方針・環境

設計択一が割れるため `DW-C00` の軽量版は採らない。段 2 プラン (codex read-only) → 段 3 敵対 2 レンズ →
段 5 実装 codex author 1 本 (leaf と test は同一所有面のため分割しない) → 段 6 敵対レビュー 2 本
(レンズ A = 状態機械と crash 窓の網羅、レンズ B = 削除耐性の主張過大と恒真テスト)。
受入は login ノードで `python3 tools/run_tests.py`。計測なし。
