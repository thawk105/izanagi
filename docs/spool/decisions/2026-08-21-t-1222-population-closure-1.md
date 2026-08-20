---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: t-1222-population-closure
seq: 1
---

## {{D:t1222-item2-launcher-fix-supersedes-d499}}. D499 決定(2) の item2 (test_dev_waves_integration.py の self-import launcher) 修正保留を解除し実装する

**決定:** D499 決定(2) が「テスト側の比例欠陥は恒久保留とする。削除も修正もしない。解除はユーザーの
明示命令に限る」と定めた item2 (test_dev_waves_integration.py の self-import launcher、
`_run_contained_serve_child()` が fresh subprocess から自ファイル全体を毎回 re-import する
D463(b) 型欠陥) について、修正保留を解除し実装した。

**理由:**
- 本 wave を起票した command 引数が、item4 (test_check_ai_provenance.py) だけを「accepted
  full-history scan の範囲を保ったまま」と明記して保護し、item2 は同様の保護を与えなかった。
  既知の欠落候補として test_dev_waves_integration.py を名指しし「欠陥が test 側か target 側かを
  分類し、必要な修正…を行う」「欠陥を恒久保留へ登録しない」と明記しており、起票者は D499 の内容
  (item2/item4 双方の disposition) を認識した上で (item2/item4 双方の裁定原文を含む archive 2 本を
  両方とも正本として明示的に引用) item2 を修正対象に含めたと判断した。
- D499 決定(2) の理由は「テスト側は比例部分が 0.214 秒、入力は 14 日間不変で、変異による検証が
  構造的に不能」だった (既存の唯一の実行時 node が `xdist_group` 所属で D452 の mutation 対象条件
  (c) を満たせない)。本 wave は、実際の subprocess launcher が参照する module 名を検査する
  D452 適合の新設 static assertion (`xdist_group` 非所属) を考案し、この技術的制約を解消した。

**却下した選択肢:**
- 解釈を保留しユーザーへ再度諮る — command 原文が対象 file を名指しし恒久保留を明示的に禁じており、
  既に実質的な指示と判断した。誤りであれば本 decision とその根拠から訂正できる。

**参考:** 実装は subprocess launcher を新設 `orchestrator/tests/_dev_waves_serve_child.py` helper
module へ切り出す形。既存 socket roundtrip test の marker・本体・受理集合は不変。変異事前登録は
D452 適合の新設 node 1 件のみ (KILLED、期待どおり単一 node)。launcher 定数を直接書き換える変異は
静的 assertion と実 subprocess 起動の両方に波及し `xdist_group` node を巻き込むため、D452 の
代替条項 (親の直接実測) で裏取りした。
