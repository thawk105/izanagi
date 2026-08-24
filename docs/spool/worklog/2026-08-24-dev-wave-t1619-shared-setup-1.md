---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1619-shared-setup
seq: 1
title: [T-1619] 受入の重複前置きを s8c predicate 族で共有化した。work は 147.28 秒から 38.9 秒へ減り、変異の kill 集合は前後で完全一致した (テスト、branch worktree-dev-wave-t1619-shared-setup、変異 matrix = baseline 緑・5/5 KILLED・SURVIVED 0)
---

## 本文

- ユーザー指示は 4 候補から 1 族だけを選ぶことだった。親は独立性と変更面を実測し
  `test_s8c_preregistration_predicates.py` の `test_current_repository_*` を選んだ。
  pytest subprocess 族は受入 control-plane に集中し稼働中の並行 wave と所有が重なる恐れがあり、
  subprocess の存在理由が隔離そのものなので意味保存を負の対照で示しにくい。
  parametrize 族は一括変更が禁止指示。t126 は効果が余地の 11% と小さい。
- **親 brief の誤り 4 件が段 3 の敵対レビューで訂正された。** いずれも採用した。
  (1) 削減量の過大評価 — 台帳の 207 秒には現 source に存在しない nodeid の 32 秒が混入していた。
  実在 5 件は 175 秒である。(2) 台帳 key の誤解 — runtime も生成器も group 接尾辞を落として
  引くので key は不変で、変わるのは所要値だけ。「nodeid 表記が変わる」は誤り。
  (3) 過剰一般化 — setup 回数は 5 node を実行した distinct worker 数 k (1 以上 5 以下) であり、
  「48 worker でも必ず 5 回」とは言えない。(4) 悪化量の言い方 — 既存鎖へ足す案の悪化は
  「鎖 147.6 秒、下界増分 約 36 から 40 秒」であって 45 秒ではない。
- **親が段 5 進行中に変異の帰属不成立を見つけ、事前登録を全面的に差し替えた。** 詳細は
  {{F:mutation-blob-face-invisible}}。plan も敵対 2 レンズもこの欠陥を指摘していない。
  当初登録の 3 変異は偽 SURVIVED になる型で、親が probe 2 本で可視・不可視の両方を実証してから
  可視面へ再照準した。
- **段 6 の敵対レビュー 2 本は must-fix ゼロ。** sol の should-fix 1 件 (m04 に SATISFIED を
  選ぶと 4 件目も赤くなる) は、実装した m04 が status ではなく reason code の置換なので
  構造的に回避済みだった。luna の should-fix 2 件は表現の限定として採用した
  (効果の外挿は k=5 と焦点走と同じ費用比を仮定した条件付き推定、shard 検査は閉包のみ証明)。
- **luna の nit 1 件は fix を投じた。** 独立 oracle が canonical 名の set 比較だったため、
  将来 parametrize されると鎖の item 増加を検出できなかった。本 wave が作った
  「鎖は floor 103.0 秒を超えない」という不変条件の guard 自体の穴なので閉じた。
  件数を 6 にする probe で `actual=6 expected=5` の赤を実測し、同時に set 比較側が
  発火しないことも確認して、穴の実在と閉塞の両方を示した。
- **不採用にした所見。** gap-reason test を group 先頭へ移す案 (受入は fail-fast で走らないため
  成果物のどの値も受理集合も変わらない)。未使用変数の改名 (luna 自身が repo に lint 経路が
  実在しないと確認)。受入全走を old-ledger と updated-ledger で 2 回に分ける案 (scope 外)。
- **変異 harness の構造的制約を発見した。** {{F:mutation-harness-group-suffix}}。
  版 B は 5 件とも MISMATCH になるが、これは検出力の差ではなく label の問題である。
  親は両版の失敗 node 集合を正規化して比較し、5 変異すべてで完全一致することを確かめた。
- 受入所要台帳に現 source へ存在しない nodeid
  `test_s8c_preregistration_predicates.py::test_current_repository_c12_allocation_binding_helper_accepts_both_calls`
  が残っている。台帳の定期再生成 [T-1620] の実証材料であり、本 wave では台帳を変更しない。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1)。すべて
  `gpt-5.6-sol` / `xhigh` / `outcome=accepted`。変異 matrix は 4 回投入し 2 回は
  決定的な失敗で直した (runner argv の `-rf` 欠落、collection の nodeid に group 接尾辞が
  付かないこと)。失敗した使い捨て container は worktree 登録ごと撤去し prune 済み。

## 次の一手差分

### 更新

- [T-1619] **P2**: 受入の高コスト側にある「同じ前置きを何度も払っている」型を共有化する。
  s8c predicate 族 (`test_current_repository_*` 5 件) は本 wave で完了した。
  残る候補は parametrize 族 (総 work の 30.5%、1175 族)、pytest を subprocess 起動する
  上位 4 file の 724.2 秒、`test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo`
  40 case の 45.2 秒である。次に着手する族も、既存の直列鎖 (`real-repo` 102.6 秒、
  `s8c-preregistration-candidate` 103.0 秒) を伸ばさないこと、変異の可視面を
  {{F:mutation-blob-face-invisible}} に従って先に実測することを前提にする。
  base: eca559f36c3259d3cd160b201a4d21bcf75050a13468e3e0bd70abd1502c64c1

### 新規

- {{T:mutation-harness-group-suffix}} **P2・新規**: 変異 harness が xdist group 接尾辞を
  正規化しないため、group を新設した wave は KILLED 判定を構造的に得られない。
  期待 node は collection (接尾辞なし) で検証され、失敗 node は接尾辞付きで記録されるので、
  どちらの書き方でも完全一致しない。`tools/mutation_harness.py` の記録側で
  `_strip_group_suffix` 相当の正規化を入れ、正規化前後の両方を receipt へ残す。
  接尾辞ありの期待 node を書いた spec が collection 検査で落ちる負例と、
  group 化した族が KILLED になる正例を対で登録する。
