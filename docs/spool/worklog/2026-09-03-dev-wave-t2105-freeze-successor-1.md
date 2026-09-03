---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2105-freeze-successor
seq: 1
title: [T-2105] 承認 A と有効 pointer X の別 commit 構成を下位実装が受理するようにした — 正本適合は topology 1 件だけで、残り 4 件と Q 列は裁定へ返す (コード + テスト、branch worktree-dev-wave-t2105-freeze-successor)
---

## 本文

- **依頼の主題は 1 箇所の食い違いだった。** 下位 exact 正本 `docs/freeze-permanent-design-s2.md`
  §S2-1.14 は承認 A と有効 pointer X を別 commit とし X の parent をちょうど A と定めるが、
  `orchestrator/campaign/s8b_ratified_freeze.py` の `_verify_pairing` は両者の同一 commit 導入を
  要求していた。人間が正本どおりに置いた successor は `pairing-commit` で必ず拒否されるため、
  legacy v1 から凍結 g1 への承認可能な successor が原理的に成立しなかった。これを置換した。
  設計判断は {{D:ax-topology-partial-conformance}}、{{D:derived-pin-coordinated-update}}、
  {{D:no-tautological-guard}}。

- **段 3 の敵対検査 2 本はいずれも NO-GO を返し、そのうち最重要の 1 件を親の実測が refute した。**
  レンズ A は「置換すると G と A の順序が拘束されなくなり、G を別枝に置いて merge した history が
  通る」と構成した。親が repo 外 probe で同じ history を**変更前のコード**に掛けたところ
  `RESULT=ACCEPTED generation=1` となり、**この穴は現行実装に既存**であることが確定した。
  本 wave は開けも広げもしていない。正本の解 `A^ == Q` の Q は permanent family の構成要素で
  未実装のため、代替述語を発明せず裁定へ返す。

- **段 5 の 1 回目は実装ゼロで停止し、その判断が正しかった。** calibration fixture の
  invocation digest は原像に合成 repo の HEAD を含むため、A→X 分割で必ず変わる。一方で
  分割しなければ 3 fixture の positive control が新実装で拒否される。どちらに倒しても赤になる
  矛盾を実装子が検出し、hash 差し替えも検査緩和もせずに全差分を戻した。親の裁定が矛盾していた。
  凍結 design 側に当該 hash の pin が無いこと、gate owner literal が `lower-impl-wave` であること、
  commit `b555a2986` が同型の協調更新を実施した先例であることを確かめ、編集可 file を
  4 件から 9 件へ広げて派生値だけの更新を許可した ({{D:derived-pin-coordinated-update}})。

- **恒真な述語を防壁として足さないことを裁定した。** 正本は pairwise 非同一を課すが、
  X は逐語 `AI-Agent: none` を要求され G は `none` を拒否されるため
  `generation-pointer-same-commit` は実 resolver から到達不能である。新設せず、
  `approval-pointer-same-commit` は診断専用と明記して変異登録から外した
  ({{D:no-tautological-guard}})。

- **棄却した所見。** レンズ A の「置換で受理集合が新たに緩む」は上記 probe で refuted。
  レンズ B の「A の parent に G を要求すべき」は正本どおりの完全列を逆に拒否するため不採用。
  段 6 の敵対レビュー 2 本は must-fix ゼロで、nit 4 件はいずれも古い説明文言だった。

- **親の brief の誤りを 2 件、記録として訂正する。** (a)「gate `FREEZE-AX-TOPOLOGY` の射程は
  計 5 件」は上位権限束設計 §12.4 の**記載**であって網羅ではない。レンズ A が
  未知 governance file の無視と mode `100755` 許容の 2 件を追加実測した。
  (b)「W-a / W-c 所有 file は 1 件も存在しない」は誤りで、`orchestrator/tests/conftest.py` と
  `orchestrator/tests/data/freeze_holdout_positive_control_v1.txt` は実在する。正しくは
  producer・resolver・CLI・世代 artifact・receipt・report が不在である。

- **人間の手番には踏み込んでいない。** 承認 record の発行と有効 pointer の commit は
  D1391 のとおり人間が行う。本 wave が作ったのは検証器の変更と合成 fixture だけで、
  `output/` 配下には 1 file も置いていない。gate `FREEZE-AX-TOPOLOGY` は
  `nonconforming` のまま据え置いた (上位権限束設計 §12.4 が topology 単独での resolved を明文で禁じる)。

- **変異 matrix (実測)。** baseline PASSED、KILLED 3 / SURVIVED 0 / MISMATCH 0。
  事前登録した 3 変異の観測 node は期待 node と完全一致した (各 1 件)。
  M01 = A の追加 path exact-set を包含検査へ緩める →
  `test_approval_commit_with_extra_file_rejected`。M02 = X 側の同型 →
  `test_pointer_commit_with_extra_file_rejected`。M03 = `X^ == A` guard の無効化 →
  `test_pointer_parent_must_be_selected_approval_commit`。
  `approval-pointer-same-commit` と `generation-approval-same-commit` は恒真または診断専用のため
  登録していない ({{D:no-tautological-guard}})。過剰拒否の正例
  `test_happy_path_resolves_and_loads` は baseline で緑である。

- **工数。** codex 子 7 本 (plan 1、段 3 consult 2、段 5 author 2 — 1 本目は矛盾検出で実装ゼロ、
  段 6 review 2)。段 5 の 1 本目と、段 6 の変異走は投入 5 回のうち 4 回が
  計算ノードの基盤障害・queue 混雑で失われ、5 回目で完走した (F333 の再発として記録した)。

## 次の一手差分

### 更新

- [T-2105] **P2・部分完了 → 残りは裁定待ち**: 承認 A と有効 pointer X の別 commit 構成は
  下位実装が受理するようになった (commit 0d4310647)。**正本適合として閉じたのは
  `FREEZE-AX-TOPOLOGY` の 5 件のうち topology 1 件だけ**である。残る approval 8 field /
  pointer 7 field / revocation 7 field・対象 `bundle_digest` / cancellation 6 field は、
  正本が 3 family bundle (known / measurement / holdout + receipt + 3 report) を前提とし、
  その family の producer・resolver・CLI・世代 artifact・receipt・report が repository に
  1 件も存在しないため着手できない。gate は `nonconforming` のまま。
  base: df48129f0b7d4f4635f0c35978332c4e50698277dad4a93a3fab5bd241ef21a0

### 新規

- {{T:freeze-ax-predecessor-ruling}} **P2・新規・ユーザー裁定待ち**: 承認 commit A の
  predecessor が無制約である穴をどう扱うかを決める。G を別枝に置く列、G と A の間に無関係な
  commit を挟む列、g2 導入後に g1 を承認する列がいずれも受理される。**これは現行実装に既存の
  穴で、[T-2105] の topology 適合は開けも広げもしていない** (親が repo 外 probe で
  変更前コードでの受理を実測済み)。正本の解は `A^ == Q` だが Q は permanent family の
  構成要素で未実装。選択肢は (a) Q 列を実装するまで放置、(b) 縮約 topology 用の代替述語を
  新しい裁定で定義する、の 2 つ。**(b) を親の判断で実装しない** — G を Q の代替に据えると
  正本どおりの完全列 `G <- R <- L_prod <- L_manifest <- Q <- A` を逆に拒否するため。

- {{T:freeze-ax-scope-beyond-five}} **P3・新規**: gate `FREEZE-AX-TOPOLOGY` の差分列挙を
  実測に合わせて広げる。上位権限束設計 §12.4 は 5 件を挙げるが網羅ではなく、
  段 3 の敵対検査が (a) `_collect_records` が governance namespace の未知 file を明示的に
  無視する (正本は拒否を要求)、(b) namespace 列挙が mode `100755` を許し収集時に mode を
  検査しない (正本 §S2-1.1 は `100644` のみ) の 2 件を追加で実測した。
  台帳・設計文書のどちらを直すかを含めて扱う。
