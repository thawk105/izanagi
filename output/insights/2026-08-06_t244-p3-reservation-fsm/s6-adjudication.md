# 段 6 裁定 — 敵対レビュー 2 本の所見処理

wave: `dev-wave-t244-p3-reservation-fsm`
レビュー逐語: `s6/revA.md` (正しさ・恒真化・検出力) / `s6/revB.md` (受理集合・会計・名乗り)。
**両レンズが独立に NO-GO を返した。** 実装そのものの受理集合違反は**両者とも見つけていない** —
所見はすべて**検出力の欠落**と手続面である。

親の実測 (統合 snapshot `641...` 前、対象 2 file): **35 passed / 1 failed**。

## 裁定表

| # | 出所 | 判定 | 区分 | 要旨 |
|---|---|---|---|---|
| X0 | 親実測 | real | **fix** | V28 の診断文言不一致。`OriginSealed` guard だけが旧文言 `origin seal requires no open batch` を残し、他 5 つの相 guard の `... is not allowed in current phase` と不揃い。予約中は「open batch」が無いので文言自体が不正確。**拒否は正しく起きており受理集合は正しい** |
| X1 | A-F1 | real | **fix** | abandon / recovery の fixture が全て `cardinality=2` × abandon 1 回。cardinality を定数化する変異や forfeited を上書きにする変異を区別できない |
| X2 | A-F2 | real | **fix** | `OriginSealed` の prepared projection が producer / verifier で同じ関数を使うため共動する。counter を落とす変異を現テストは検出しない |
| X3 | A-F3 | real | **fix** | 旧 V06 が持っていた committed operation の candidate identity 負例が、先頭 event の予約差し替えで失われた。**検出力の低下**である |
| X4 | A-F4 | real | **fix** | V02 の `42 / 7 / 35` はテスト内の局所集合を数え直すだけで、event union の完全性と受理後の遷移先 phase を固定していない。未裁定 event を足しても緑のまま |
| X5 | A-F5 | real | **fix** | V19 の policy-injection 負例が `batch-committed` から `batch-reserved` へ**移動**した。両方に要る |
| X6 | B-2 | real | **fix** | `origin-sealed` の raw wire 受理集合 (8 field 必須) が直接固定されていない。旧 6-field / 欠落 / bool を decoder へ直接渡す負例が無い |
| X7 | B-3 | real (nit) | **fix** | `test_v26_prequery_reservation_is_required...` の node 名が「query より前」と読ませる。保証できるのは「`BatchCommitted` より前」まで。名乗りの問題なので採る |
| X8 | B-4 | 疑い | **fix** | abandon 後に別 batch を完走して certifiable seal できる正例が無い。`DW-M01` が受理集合縮小 wave へ要求する「承認外の過剰拒否を検出する正例」に該当するため採る |
| X9 | B-1 | real | **段 7 で閉じる** | D96 の新 D が未記録。これは段 7 (記録) の親の仕事であり fix 子の対象ではない。同一 land commit に含める |
| X10 | A / B | refuted | — | codec oracle の共動 / 拒否 35 組の手前落ち / recovery テストの変数持ち回し / 予算の減算・二重 commit / partition 呼出し漏れ / probe の名乗り弱体化 / v3 混入 / 歴史記録改変 / feasibility literal / 本番 authority 正例 / consumer 取り残し / 後続 wave 閉塞。**両レンズが独立に refuted としたものを含む** |

## scope 外の real 所見 (裁定パッケージへ追加)

- **prepared operation crash の caller WAL** (A)。予約後の commit / abandon が `head-prepared` で
  落ちると、exact request を失った新 process は公開 binding だけでは cancel / resume できない。
  `OriginSnapshot` は prepared operation ID も未書込み payload も公開しない。
  caller 制御流と WAL の scope なので本 wave では実装しない。
  **成果物影響**: proof chain が prepared 状態で停止し、その origin の terminal report を作れない。
- **1 予約下の provider 呼出し回数**は無制約 (両レンズ、既知)。段 4 裁定パッケージ (3) に既出。

## fix の分割

**一枚岩の 1 単位とする。** 理由 = X0 が `reflux_origin_ledger.py` の 1 行 (診断文言) を変え、
X0 のテスト側期待がその文言に依存するため、2 単位に割ると 1 行のために直列化するだけになる。
所有は `reflux_origin_ledger.py` と `test_reflux_origin_ledger.py` の 2 file。
`liveness_probe.py` は今回の fix 対象外 (両レンズが refuted)。

fix 前の統合 snapshot patch は `s6/snapshot-before-fix.patch` に退避済み。
