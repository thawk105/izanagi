# [T-428] 変異 matrix — 19/19 KILLED (上位集合 erratum 3 件)、正例 4/4 受理

日付: 2026-08-04。repo_head = a44c276 (merge local main dcd8a2a 後)。
harness = `tools/mutation_harness.py --runner-mode dispatch --detached` (計算ノード dispatch、
flock 単一走行・固定 HEAD 束縛・復元検証は harness が強制)。spec sha256 = 75de08ca…dc76c。
raw 台帳 = 本 dir の mutation-ledger.json、spec = mutation-spec.json。

## 判定

- **baseline**: rc=0 (無変異で全対象テスト緑)
- **19 変異 (M-A1〜A6、M-B1〜B9、M-C1〜C4): 全件 KILLED** (各変異で rc=1、期待 kill node が
  失敗集合に含まれる)
- **erratum 3 件 (M-B2 / M-B4 / M-B6)**: harness 判定は MISMATCH だが、内訳は
  「失敗 node 集合が事前登録の**上位集合**」(expected ⊆ observed、missing 0 件)。
  共有 validator を tamper する変異が、登録した replay 側だけでなく admission 側・
  受理境界側のテストにも正しく波及したもので、**検出力不足ではなく事前登録が狭かった**。
  判定 (KILLED) は 1 件も変わらない。初回 harness 出力は消さず本 erratum で記録する
  (DW-M02。先例 = 2026-08-04 (168) の同型 erratum)
- **正例 (過剰拒否検出、spec 外・同 HEAD で実走)**: 4 node すべて passed —
  P+1 (public drive の no-build fixture E2E)、P+2 (32 正準述語 + 外側空白の sink 受理)、
  P+3 (projection mode 閉包の正側 + sort/backoff marker 不変)

## 手続メモ

- 初回投入は「期待 node が collection に実在しない」で fail-closed 中止 — 親が runner の
  対象リストに test_reflux_ir.py を入れ忘れたため (M-A3 の期待 kill が同ファイルにある)。
  spec・変異には問題なし。リスト修正後の再投入で完走
- anchor 検証 (DW-M07): merge (a44c276) 後に全 19 変異 × 全 replacement の old 逐語が
  一意 1 箇所であることを親が実測 (drift 0)
