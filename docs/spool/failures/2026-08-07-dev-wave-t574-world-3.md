---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t574-world
seq: 3
---

## 新規

### {{F:tautological-exception-type-pin}}. 例外型だけを見る負例試験が、後段の無関係な失敗で満たされ恒真になった [恒真ゲート] [テスト代表性]

- 事象: 段 2 のプランが「current 契約が後継世代へ進んだ状態で resume を呼び、
  `pytest.raises(FloorCampaignError)` の型だけを確認する」試験を推奨した。しかし守るべき
  current 契約検査を削除しても、制御が 1 段先の calibration 読込みへ進み、そこが**必ず**
  `AttestationError` を出して同じ `FloorCampaignError` へ翻訳されるため、試験は緑のままだった。
  必ず失敗するのは、正当な後継世代が calibration 参照を必ず変えるのに対し、当該 env の
  attestation mode が grandfathered な唯一の bytes しか受理しないためである。
  段 3 の 2 レンズが独立に land blocker として検出し、段 4 で設計を差し替えた。
- 根本原因: 負例試験の oracle を「拒否されたこと」で書き、「**どの層が拒否したか**」で書かなかった。
  同じ例外型へ翻訳する層が下流にあると、拒否の事実は上流 gate の存在を証明しない。
  F133 が node 粒度の不一致だったのに対し、こちらは oracle 自体が層を区別しない弱さである。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` が求める単一理由性を、
  **負例試験の oracle 側にも適用する**。拒否の因果を、下流の副作用が起きていないこと
  (下流 loader の呼出し回数 0 等) で pin し、対象 gate を外す変異でその assert が赤くなることを
  変異検査で確認する。本 wave では calibration loader の呼出し回数 0 で pin し、変異 M3 が
  この assert でのみ KILLED になることを実測した。
- 再発検知: 変異事前登録の各行に「その変異で赤くなる assert」を書き、赤の原因が
  `pytest.raises` の型一致だけの行を登録しない。

## 再発

### F75

- **再発: 2026-08-07** — 別 wave が使い捨て解析スクリプト 2 本を `.py` のまま insights へ凍結し、
  実装面 Codex `role=author` を欠いたまま main へ land した。本 wave の記録後 provenance 監査
  (full history) で顕在化した。前回の再発時に判別条件を「親が実行可能ファイルを書くとき常に」へ
  広げたが、`--message-file` preflight は当該 wave の commit 経路では発火していない。

### F138

- **再発: 2026-08-07** — 過剰拒否検出用の正例変異の期待 node を、狙った新設正例 1 本だけで
  登録した。実際には同じ入力経路を共有する既存 2 node も赤くなり MISMATCH。変異の適用範囲を
  field 不在経路だけへ狭めたうえで、コードを読んで期待 node を 2 件に確定して再走し 4/4 一致。
  初回台帳は erratum として保持している。
