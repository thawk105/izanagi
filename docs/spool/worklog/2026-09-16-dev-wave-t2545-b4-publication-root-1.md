---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2545-b4-publication-root
seq: 1
title: [T-2545] 事前登録が publication root を 1 つ名指しし、発行器がそれ以外を拒否する (コード + docs、branch worktree-dev-wave-t2545-b4-publication-root、変異 matrix = baseline 緑・5/5 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

D1881 の名指し実装。呼び手が実行時に publication root を選べる状態をやめ、事前登録が名指す
1 箇所以外での発行を発行器が拒否するようにした。

**依頼は「裁定済みなので設計は変えず、名指しの実装に限定する」「仮想リスク向けの gate・検査・
台帳・一般化の追加は scope 外」。** 起動時に、稼働中の producer layer r1/r3 design ([T-2293]) と
編集面が重ならないことを全 worktree の未 commit 差分と branch tip の両方で実測した (該当 0 件)。

**置き場所は §6 に決めた。実測で 2 か所が塞がっていた。** §5.1.1 は D2016 項 6 が
「1 byte も触れない」と定めた凍結節で、事前登録 consumer が直下の H5 をちょうど 6 個・指紋順一致で
要求する。§5 の固定表は `p3_b4_admission_record` が 10 ラベルとの exact 集合一致と行数一致を要求し、
**行追加は集合比較に到達する前の行数検査で落ちる**ので「1 行足す」では済まない。§6 の見出し逐語は
事前登録 consumer の test が抽出終端として pin しているが、見出しを変えなければ項目の追加は通る。

**敵対相談 2 本 (レンズ = 正しさ境界 / 整合と実効性) が親 brief の主張を 4 件縮めさせた。**

- 「既存の拒否 reason を 1 つも変えない」は偽。別 root と予定群不正を併発させた入力では、
  新 reason が既存 reason より先行する。正しくは「受理集合は縮小のみ。既存 reason がそのまま
  残るのは正常な宣言かつ名指し root の場合に限る」。
- 「`output/` 配下 0 件ゆえ既存 publication の再発行は発生しない」は探索範囲を超える。
  旧発行器は `output/` に限らず任意の絶対 root を受けたので、範囲を明示した表現に限定した。
- §5 への行追加が落ちる地点の帰属が誤っていた (上記)。
- §6 の test pin は見出し全文ではなく抽出終端の prefix である。

**完了主張を「発行器を置いた checkout」に限定した (段 4 裁定 R1)。** loader と bootstrap 束縛は
呼び手から受け取った root をそのまま使うので、別の checkout で名指しどおりに発行した bundle を
別の呼び手が絶対 path で指す経路は閉じない。非保証列
`publication_under_a_different_root_is_not_prevented` は系全体の非保証として依然真なので 1 項も
削っていない。同列は receipt bytes と材料レポートの provenance hash に束縛されており、
文言だけの訂正にはならない — この閉包は [T-2546] へ引き継ぐ。

**公開 API に repository root や事前登録 path の引数を足さないことを不変条件に置いた。**
呼び手が指定できる時点で D1881 が閉じる穴が再び開くためである。

**関連 fixture 3 file の追従を scope 内へ入れた。** 新検査は発行器の全呼び手に効くので、
`test_p3_b4_raw_record_producer.py`、`p3_b4_proposal_binding_support.py`、
`test_p3_b4_material_report.py` の発行先を追従させないと関連テストが機構へ到達しない。
新検査の無効化と期待 reason の置換は禁じた。

**descendant を変異の帰属証拠から外した。** 名指し root を未作成にしたときの descendant は、
新検査が無くても親ディレクトリ不在で `PUBLICATION_ROOT_INVALID` になる。単一理由性が立たないので
既存の親を持つ sibling へ差し替えた。

**焦点走の赤 1 件は変更の回帰ではなかった。**
`test_p3_b4_producer_auth_experiment.py::test_main_worktree_has_no_permanent_prototype_or_pin_change`
は保護 path が `git diff --exit-code <HEAD>` で無差分であることを要求する。未 commit の作業木で
焦点走をかけたことによる赤で、commit 後の単独再走は 50 passed・rc=0 だった。

**所要台帳は関門ではないが登録した。** 未登録 nodeid には `tools/acceptance_shards.py` が
D104 の割当ヒントとして 1.0 秒を与えるだけで、赤にはならない。値は正本 producer
(`tools/update_acceptance_duration_ledger.py --add-only`) に計算させ、実装面として Codex author が
書いた (added=8、skipped_existing=160、既存 entry の変更 0 件)。

工数: codex 子 7 本 (plan 1・consult 2・author 1・review 2・fix 1、いずれも gpt-6-astra / medium)。
計算ノード job は焦点走 1・単独検証 1・台帳検査 1・JUnit 取得 1・変異 probe 6 走・変異本走 6 走・
全史 provenance 監査 1。

## 次の一手差分

### 完了

- [T-2545] D1881 を実装した。事前登録の §6 が publication root を 1 つ名指しし、発行器が
  canonical 化した root の不一致・名指しの不在/重複/書式不正/読取失敗を
  `publication_root_not_preregistered` で fail-closed にする。閉じたのは発行器を経由する発行だけで、
  loader と bootstrap の受理条件は変えていない。
  remaining: none
  base: e7a1b651ae06add65abdd3afe7e5efef6d24de636479ed7df45d43ece1bf8315
