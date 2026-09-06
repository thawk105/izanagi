---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2195-policy-binding
seq: 1
title: [T-2195] mocc trace policy の raw SHA と compiler mapping を投入時に捕捉し、job 側で照合する (コード + テスト、branch worktree-dev-wave-t2195-policy-binding)
---

## 本文

- D1541 の実装 wave。三者照合 (実体 bytes・shell 変数・最終受領証) に、qsub 環境変数と受領証の argv を
  足した 5 者の raw SHA 照合として実装した。設計判断は {{D:mocc-policy-binding-five-party-sha}}。
  版ずれ検出の拡張 (D1542) と他 field への一般化は scope 外に置いた (ユーザー指示)。
- 段 3 の敵対相談 2 本が must-fix 10 件を出し、全件採用した。主なもの: 受領証の自己 pin だけでは投入
  権威の独立した証人にならないので qsub `-v` を足す、早期 parser にも raw SHA を出させる、負例は
  production の shell 接着を実走する。
- 段 6 の敵対レビュー 2 本が must-fix 2 件 (書き手なし FIFO で open が block する、`json.loads` が
  非有限定数を受理する) を出し、fix 1 で閉じた。
- **変異走行が段 6 レビューの見落としを 2 件出した。** 詳細と数値は
  `output/insights/2026-09-07_t2195-policy-binding/README.md`。
  1 件は {{F:fifo-negative-leaks-blocked-grandchild}} として台帳へ。もう 1 件は gate の regular file 検査が
  非 blocking 読みに隠れて単独では効かない (冗長 gate) という記録で、受理集合は変わらないため取り除いていない。
- 変異本走は 22 件すべて期待どおり (KILLED 19 / SURVIVED 3、期待外れ 0、baseline 緑)。SURVIVED 3 は
  冗長 gate 2 件と等価変異 1 件で、登録どおりである。
- エージェント工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 2)。fix 2 本はいずれも
  1 attempt で accepted。

## 次の一手差分

### 完了

- [T-2195] mocc の compiler 期待値を投入時に捕捉した内容へ束縛し、5 者照合として実装した。負例は
  「書き換え → 読ませる → 復元」経路を production fragment で実走して拒否を示す。
  remaining: none
  base: d53f60d6fd806362e989e77ef690a8a08cbecfc39814252e5ec94c876f77aeb7

### 新規

- {{T:mocc-policy-binding-pair-consumer}} **P3・新規**: mocc trace pair の consumer 側でも policy 束縛の
  推移的証明を持たせるか決める。今は job 単位の束縛までで、pair を跨いだ証明はない。
- {{T:nonblocking-strict-json-helper-generalization}} **P3・新規**: policy / 受領証を読む他の submitter へ
  non-blocking open と strict JSON の読み口を一般化するか決める。今回は mocc trace の 3 script に閉じた。
