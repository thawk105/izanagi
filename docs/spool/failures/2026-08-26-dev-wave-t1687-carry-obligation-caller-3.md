---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1687-carry-obligation-caller
seq: 3
---

## 新規

### {{F:authority-doc-prescribed-gate-bypass}}. 新設した関門の設計正本が、関門を経由しない直呼びを将来の呼び手へ指示していた [恒真ゲート] [手順漏れ]

- 事象: 段 0 の繰越義務述語を production の前提関門 adapter へ結線する wave で、親が設計正本の
  3 箇所を「段 6 の X 候補提出前に `require_stage0_fixture_obligations_discharged()` を呼び、
  同述語が緑であることを要求する」と書いた。adapter は 2 つの終端を持ち、義務が解消しても
  段 6 policy が `unresolved` である限り拒否する。しかし正本の指示どおり将来の submitter が
  義務述語を**直接**呼ぶと、fixture 義務だけを満たした候補が policy 終端を通らずに writer へ
  進める。段 6 の敵対レビューが実コードと正本の突き合わせでこの構成を作った。land 前に是正した
  near miss である。
- 影響: 是正しなければ、fixture 義務だけ解消した候補が policy 未解決のまま受理され、
  X 候補・後続レポート・台帳の受理集合が広がりえた。関門を新設しながら、正本が
  その関門を通らない経路を推奨している状態だった。
- 根本原因: 関門の**実装**と、関門を**誰がどう呼ぶか**の記述を別々に書いた。実装は
  「adapter が述語を呼ぶ」形にしたのに、正本の文は結線前の「呼び手が述語を呼ぶ」形のまま
  述語名だけを残して更新した。関門を 1 段挟むと、呼び手にとっての正しい入口が
  述語から adapter へ移るが、その移動を文へ反映しなかった。
- 恒久対応: 設計正本 §10 表 row 6 / §10.2 / §12.3 を「呼び手は adapter を呼び、adapter が
  義務述語を呼ぶ。直接呼ぶと adapter の policy 終端を迂回する」へ書き換え、
  {{D:stage6-adapter-vs-operational-caller}} が向きを裁定として固定した。row 6 は contract module の
  逐語 pin と bytes 一致が要求され、§10.2 と §12.3 の断片は
  `orchestrator/tests/test_calibration_freeze_stage6_candidate_gate.py` が設計正本に
  ちょうど 1 回現れることを exact に検査する。いずれかを旧文へ戻す単一変異が赤になる。
- 再発検知: 関門を新設する wave の段 6 レビュー lens に「正本が指示する呼出し経路が、
  新設した関門を必ず通るか」を入れる。実装の呼出し先ではなく、**正本が呼び手へ指示している
  入口**を読み合わせる。
