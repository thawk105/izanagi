---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t595-reasoning-ab
seq: 3
---

## 再発

### F60

- **再発: 2026-08-07** — `dev-wave-t595-reasoning-ab` で、単層変異 2 件 (可視化フィルタ除去・
  引用除去) が SURVIVED した。親は DW-M04 に従って両層同時変異を追加登録し、2/2 KILLED を得たので
  「単層の生存は冗長層ゆえ」と結論しかけた。焦点再レビューがこれを反証した — その KILLED は
  既存の**裸表記 `reasoning=high`** fixture に対する結果にすぎず、単独 SURVIVED を冗長と判定する
  根拠にならない。実際には検査が現実の起動キー表記 `model_reasoning_effort=` を認識しておらず、
  単層変異のそれぞれが単独で fail-open 反例を構成できた。親が書き込みなし probe で裏取りした。
  今回は F60 と違い期待 node の割当ては正しく、**負例 fixture の表記が現実の攻撃表記を
  覆っていなかった**点が原因である。恒久対応として (a) 過剰拒否を検出する正例 control
  (`orchestrator/tests/test_check_docs.py` の
  `test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`) を足し、
  可視化フィルタ層を単独で kill 可能にした。(b) 負例 fixture に実運用の表記
  (`reasoning_effort=` / `model_reasoning_effort=`、引用符付き) を加えた。
  再照準後の変異は 7/7 KILLED。**両層同時変異の KILLED を単独 SURVIVED の冗長性根拠に使わない。**
