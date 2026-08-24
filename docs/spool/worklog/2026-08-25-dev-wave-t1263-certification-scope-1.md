---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1263-certification-scope
seq: 1
title: [T-1263] 材料レポートへ認証水準を明記し、載る packet の snapshot evidence を 1 箇所で検査する。親の到達可能性の前提は段 2・3 が反証し、受理集合を実際に狭めるのは別の穴だった (コード + テスト + docs、branch worktree-dev-wave-t1263-certification-scope、変異 matrix = baseline 緑・7 KILLED・SURVIVED 1 (等価と登録)・MISMATCH 0)
---

## 本文

裁定 (2026-08-17 /rulings 全件 第 5 回、明記 + 条件) の実装。装置は
`tools/codex_reasoning_ab.py`。設計判断は {{D:material-report-certification-scope}}。

### 親 brief の 2 つの前提が反証された

親は brief で「未検証 snapshot 由来の packet が `valid: true` へ到達する経路が現行に実在する」
を (P1) として置き、根拠に prelaunch 失敗 attempt が snapshot 検証を通らず final になりうること
を挙げた。段 2 と段 3 レンズ A が独立に反証した。正規経路では `make_packets` が final attempt の
`output` descriptor を必須にするため packet を作れず、packet 一式を手で組んでも
`output_sha256` が無いため adjudication の SHA 結線が別の理由を積む。**親は (P1) を撤回した。**

同時に、brief の「本検査で `valid` の受理集合が狭まる」も撤回した。membership 検査が偽になる
入力はすべて既存 snapshot 理由を同時に積むため、**この検査単独では今日緑の manifest を
赤にできない。** 冗長だが恒真ではないので実装は残し、性格を
「report が snapshot 再検証に依存していることを構造的に固定する検査」と記録した。

### 受理集合を実際に狭めたのは別の穴だった

段 3 レンズ A が、受理集合の変化を membership 検査へ誤帰属しないよう指摘した。実際に狭めるのは
**同一 oracle identity を共有する 2 本目以降の run が、自分の `snapshot_after` を一度も
比較されていなかった穴**を塞いだ側である。pre/post 一致比較が cache miss 分岐の内側にあった。
本 wave 唯一の manifest 級 kill (変異 M6) はこの変更に対応する。

### 宣言が実装より強い主張をしていた

段 6 レビュー B が must-fix を 1 件出した。宣言は未認証 artifact を 4 種類だけ挙げて
`closed_world: true` と言っていたが、`_load_adjudication` は `verdict_freeze` も読む。
列挙が閉じておらず虚偽表示だった。**これは本 wave が防ごうとしていた事故そのものである。**
`verdict_freeze` を足し、`closed_world` の射程を `uncertified_artifact_universe` で限定し、
さらに `_load_adjudication` が実際に読む manifest descriptor key を AST で導出して宣言と
突き合わせる node を対で入れた。将来 `_load_adjudication` が新しい中間 artifact を読み始めたら、
宣言を直さないかぎりこの node が赤くなる。

識別子も弱めた。段 2 案の `source_run_snapshot_verified` は「run 実行時点の歴史的 snapshot が
認証された」と読めるが、実装が保証するのは凍結 pre/post evidence と replay 時現物の再走成功まで
である (段 3 レンズ A / レビュー B の両方が指摘)。`mapped_final_run_snapshot_evidence_replayed`
へ改めた。宣言の置き場所も `_aggregate_verified` から `verify_manifest` へ移した — private
helper に付けると、それを直呼びするだけで宣言付きの `valid: true` を作れてしまう。

### 親が実測で見つけた回帰 1 件

実装子は pytest を実走できなかった (計算ノードの dispatch 障害)。親の焦点走で
`test_real_repo_group_collection_exactly_matches_canonical_nodes` が赤になった
(1 failed / 573 passed / 3 skipped)。新規 node 2 本が module scope の共有 fixture
`benchmark_snapshots` を使うのに `REAL_REPO_SERIAL_NODES` と独立 golden へ未登録だった。
`DW-O26` の consumer 拡張を守って初めて出た赤であり、実装子の名指し範囲だけを走らせていたら
受入全走まで持ち越していた。

### 実行時間の規律に抵触したので must-fix へ上げた

段 6 レビュー B は新 node の所要増を backlog と判定したが、親が計算ノードで per-node 実測すると
新規 2 本だけで **161.09 秒**の直列時間増だった (88.75 + 72.34)。直列化と長時間 node は
規律で禁じられているため、親はレビューの判定を覆して must-fix に上げた。fix で manifest 構築段の
`verify_snapshot` を identity で memo 化し (**replay 段 = 検査対象は本物のまま**)、
再実測で **20.13 秒** (11.04 + 9.09) になった。memo が忠実であることはテスト自身が示している —
memo 値が実 verifier と食い違えば replay 段で canonical mismatch になって赤くなる。

### 変異は probe で期待 node を実測してから本走した

裁定文の対応表を転記せず、全件 SURVIVED 期待の probe を先に回して観測 node を集めた。
probe = baseline PASSED、7 変異が赤、1 変異が生存。本走 = baseline PASSED、
**KILLED 7 / SURVIVED 1 / MISMATCH 0 / matching 8**。
生存した M8 (cache key を path 単独へ退行させる) は等価変異と判定した。注入実在は harness の
`anchor_counts` と `injection_diff_sha256` で確認したうえで、`_artifact_path` が descriptor の
sha256 を実 bytes と照合して落とすため、同じ path に別の sha / case が結び付く入力は identity を
組む前に必ず拒否される。**検出力ゼロであることを隠さず登録した** (段 6 レビュー B の指摘どおり)。

M1〜M3 (宣言の改竄) は新設の宣言 node だけでなく既存 end-to-end 正例でも殺され、M7 (検証済み集合を
常に空にする過剰拒否の正例) は既存正例だけで殺される。新 node の純増検出力がゼロである組合せは
テスト冒頭の変異対応表へ明記した。

### 変異 harness の既知の穴を回避できた

F494 (xdist の group 注釈付き node を期待 node として書けない) を本 wave も踏んだ。
先行 wave は該当 node を `--deselect` で外して回避したが、本 wave の kill 集合は real-repo
直列 node に依存するため外せなかった。**runner argv へ `-n 0` を渡して分散を切ると、
collection 側と `FAILED` 行側の node 表記が揃い、real-repo node を期待 node として登録できた。**
実測で 7/8 KILLED を得ている。恒久対応ではないが、`--deselect` より射程が広い回避策である。

### 段 4 で scope 外と裁定した real 所見

いずれも本 wave が作った穴ではない。(a) 中間 CLI (`make-packets` / `append-verdicts` /
`freeze-verdicts` / `reveal-mapping` / `score-run`) は packet 由来値を外へ出すが検査されない —
裁定本文が全中間層への再検証を明示的に却下しているため、宣言の `uncertified_artifact_kinds` で
機械可読に告知するだけとした。(b) invalid report にも packet 由来の axis ledger が残る。
(c) 既存の凍結材料 report には宣言が無い。(b) と (c) は起票した。

### 実装が保証しない範囲 (段 3 レンズ A の backlog 所見)

`snapshot_replay_bindings_passed` は「snapshot 関連の理由が一つも無い」ではなく
「replay 由来の束縛検査が全部通った」だけを表す。supervisor ledger の `snapshot_unchanged`
由来の理由はこの flag に伝わらない。ただしその理由が出た時点で `valid` は false なので
材料レポートの値は変わらない。誤解を招く旧名 `snapshot_checks_passed` は改名した。

### 工数と作法

codex 子 8 本 (plan 1、敵対相談 2、実装 1、レビュー 2、fix 1、受入 merge の合成監査 1)。
全子とも `model=gpt-5.6-sol`、`effort=xhigh`。実装子と fix 子はいずれも pytest を実走できず
「実装済み・未実走」と正しく申告したため、焦点走・変異・受入はすべて親が回した。

変異の本走は 3 回起動し直した。1 回目は使い捨て worktree の submodule が再帰初期化されておらず
baseline が赤 (`submodule is not initialized: external/ccbench/third_party/shirakami`)、
2 回目は resume が baseline を再走せず前回の赤を引き継いだ、3 回目は F494 の接尾辞問題だった。
`mutation_worktree.py` が作る使い捨て worktree は submodule を初期化しないため、real repo を
読むテストを変異対象にする wave は先に初期化が要る。

## 次の一手差分

### 完了

- [T-1263] 材料レポートへ `certification_scope` を明記し、載る packet の由来 run が
  snapshot evidence 再走に成功していることを `_load_adjudication` の 1 箇所で検査した。
  宣言の閉世界主張は AST 導出との突き合わせ node と対にした。変異 matrix で
  中間 packet を certified 扱いする向きの変異が赤くなることを実測した。
  remaining: none
  base: 4d94c5218d39d4aecc4610b75cee7385b75ccc32183182e5981611ea57321830

### 新規

- {{T:invalid-report-axis-ledger}} **P3・新規**: `valid: false` の材料レポートにも
  packet 由来の axis ledger (`primary_judgment_axis_ledger` 等) が残る。宣言は
  「certified なのは `valid` だけ」と言うので虚偽ではないが、「未検証由来の値を
  report に載せない」まで求めるなら不足する。report shape と受理集合を変える別判断。
- {{T:frozen-report-certification-scope}} **P3・新規**: 既に凍結済みの材料 report
  (`output/insights/2026-08-09_t181-certified-rerun/` の aggregate / verify) には
  `certification_scope` が無いまま「認証済み集計」として参照されている。凍結 bytes は
  変更できないので、sidecar で明記するか「新規生成 report のみ対象」とするかはユーザー裁定。
