---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t523-holdout-admission
seq: 3
title: freeze 由来 holdout を実測へ渡す下位境界に admission と一回性台帳を置き、8b を実結線した — 敵対 5 本が中心欠陥を独立に倒し、変異 8/8 KILLED (コード + docs、branch worktree-dev-wave-t523-holdout-admission)
---

## 本文

- **起票どおりの 2 つ (族一般化の設計起票と 8b 側の実結線) を両方行った。** 実測の下位境界は
  `run_once` (実 subprocess を張る層) とし、8b floor campaign をそこへ結線した。
  設計の正本は {{D:holdout-observation-boundary}}。
- **起票の前提を親が実測で確認した。** `s8b_floor_campaign` は文字列 `trial_registry` /
  `lifecycle` を 0 箇所しか含まず、実 freeze + 実 protocol から列挙される 12 セルの
  holdout 識別子は 8c 側の保護 workload 集合と**完全に同一**だった。
  8c が admission 無しで拒否する対象を 8b は無検査で実測できていた。
- **親 brief の中核が段 2 で反証された。** 「実測の最下層は `measure_point`」は誤りで、
  `measure_point` は `run_once` の呼び手にすぎない。加えて `run_once` を通さず ccbench を
  直接起動する production site が 4 本ある (trace 系 3 本と backoff profile)。
  **`run_once` すら「今日の共通境界」ではない**という事実を受けて、
  gate 位置を一段下げ、起動箇所の構造検査を別に置いた。
- **敵対レンズ 5 本 (段 3 の 2 本、段 6 の 2 本、焦点 1 本) がすべて NO-GO を返した。**
  2 レンズが**独立に**倒した中心欠陥が 2 つある。(a) 公開されていた発行関数を直接呼べば
  台帳も ticket も通さずに許可証を得られた。(b) production の中核が許可の差し替え口 4 つを
  外へ公開し、**既存 campaign テストが 4 つとも無効化した状態で走っていた** —
  結線を壊しても緑のままになる「謳っているのに発火しない保証」だった。
- **fix は 3 巡 + 限定 1 本。** 3 巡目で 16 → 5 → 0 と赤を閉じた。
  `DW-O16` の上限に達した時点で親が残所見を裁定した (`s6-adjudication.md`)。
- **変異 harness の baseline が本 wave 最大の欠陥を掘り当てた。** 無変異の固定 HEAD 走行が
  launch certificate の clean scan で赤になり、**本 wave が追加したテストに holdout 三軸が
  同居して H1 の未知性証拠を汚染していた**ことが判明した ({{F:holdout-triple-in-test-fixture}})。
  親が全 12,645 file を走査して範囲を確定し (H1 = 1 file、H2 = 0 件)、限定 fix で 0 件へ戻した。
  **この汚染は通常の焦点テスト走では発火しない。** 変異を省いていれば受入全走まで見えなかった。
- **fix 子が既存規律を破ったのを親が差し戻した。** 合成 fixture が実物と違う holdout 名を
  使っているのは意図的な規律だが、fix 子はこれを実 holdout 名へ 52 箇所一括改名した。
  対になっていた「実 holdout 名がセル ID に現れない」assert が赤になって露見し、全数戻した。
- **変異 8/8 KILLED、生存ゼロ、期待 node 完全一致** (固定 HEAD、runner-mode=dispatch)。
  第 1 走は期待 node の完全集合を確定する probe と位置づけ、実測集合で再登録して本走した。
  第 1 走の台帳も erratum として保持している。
  実行時にサフィックスが付く real-repo 変種 1 件は**事前登録できないため runner から除外**した
  ({{F:dynamic-node-id-cannot-be-preregistered}})。**当該 test は受入全走が担保する。**
- **親の手順ミスを 1 件記録する。** 変異走行中に spool fragment を書いたため、harness が
  untracked 検出で中止した。既知の罠であり、待ち時間を作業に使おうとして踏んだ。
  fragment を commit して木を clean にしてから再走した。
- **本 wave が主張しないことを 5 項目、設計判断へ明示した。** 特に 5 項目目
  (private な Python API を直接 import できる呼び手への保護) は、焦点レビューが
  「公開 issuer を消しても private 経路が残る」と指摘したことを受けて**新たに追加した保証の縮小**である。
  Python ではこの境界を機構的に封じられないため、実装で塞げたことにはしない。
- 材料の正本 = `output/insights/2026-08-16_t523-holdout-admission/`
  (逐語 14 本、裁定 2 本、変異 spec/台帳 4 本)。

## 次の一手差分

### 完了

- [T-523] 族一般化の設計を {{D:holdout-observation-boundary}} として起票し、8b 側の実結線を
  行った。実測の下位境界を `run_once` に置き、共有 durable root 上の cell 確保と
  attempt ticket の消費を経た許可だけが保護比率の実測を通す。変異 8/8 KILLED。
  残る所見は下記の新規項目へ分割した。
  remaining: none
  base: f3ebd4232dfcb9e45767f466ac5d109860c2fce4d5f6c971f2f97cd101457a72

### 新規

- {{T:holdout-ledger-downstream-binding}} **P1・新規 (段 6 レンズ B-3、焦点で closed 判定)**:
  台帳の無い floor result を下流が拒否するようにする。現状 `result.json` は admission 台帳の
  digest も claim identity も持たず、verifier / ratified closure / report は台帳を検査しない。
  **本 wave は「台帳を通さずに実測できない」までしか主張していない** — 実測後に台帳だけを
  消しても成果物側は気付かない。成果物 schema を変えるため独立 wave が要る。
- {{T:holdout-private-core-publish-split}} **P1・新規 (焦点レビュー 所見 2)**:
  private core の外部 measure から publishable artifact を作れる経路を閉じる。
  `_run_campaign_core(..., measure_fn=...)` は attempt marker を 1 件消費しつつ callback 内で
  任意回数 spawn でき、選別値を通常の `result.json` へ載せられる。publish 経路と
  注入可能 harness の分離という構造変更が要り、本 wave の fix 上限を超えたため分離した。
- {{T:pilot-approval-propagation}} **P2・新規 (焦点レビュー 所見 3)**:
  canonical holdout に対する pilot 実測の不可逆承認を、標準の PBS wrapper から人間が
  明示的に与えられる経路を設計する。現状 wrapper は承認 flag を渡さないため
  **標準投入経路からは pilot が安全側で拒否される**。無条件付与は採らないと裁定済みなので、
  誰がどう承認しどこへ記録するかの運用裁定が要る。実害は現時点でゼロ (floor run 実績 0 件)。
- {{T:holdout-claim-after-preflight-recovery}} **P2・新規 (焦点レビュー 所見 4)**:
  cell 確保の後に走る非計測検査 (live admission 再検査・host provenance・process identity) で
  失敗した場合に、12 セルの一回性 key が journal 不在のまま焼ける経路を塞ぐ。
  本 wave では docstring を実体へ合わせるに留め、順序自体は変えていない。
  claim をこれらの後へ移すには admission authority の段階分割が要る。
- {{T:freeze-io-fixture-holdout-names}} **P3・新規 (焦点レビュー §4)**:
  `test_s8b_freeze_io.py` の合成 fixture が実 holdout 名を使っている。主 fixture は
  実物と違う名前を維持しているので、こちらも揃えて production 中立表との誤結線に対する
  識別力を戻す。
