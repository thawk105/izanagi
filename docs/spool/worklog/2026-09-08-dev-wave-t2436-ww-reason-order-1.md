---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2436-ww-reason-order
seq: 1
title: [T-2436] verifier の理由列挙を key 順に整列した — 既存テストも既存成果物も整列の有無を区別できていなかったので、正例を新設したのが実質の作業 (コード + テスト + insight、branch worktree-dev-wave-t2436-ww-reason-order、変異 3 件すべて期待一致・赤 node は新テスト 1 件の完全一致)
---

## 本文

- **D1817 の実装。** `orchestrator/verifier/dsg.py` の `_reasons()` が WW 理由を未整列の集合から
  走査していたため、同じ trace でも process ごとに理由順が変わり anomaly digest が一致しなかった。
  共通 key の走査を key 文字列の昇順に固定した。詳細と逐語は
  `output/insights/2026-09-08_t2436-ww-reason-order/`。
- **裁定の前提はすべて実測で裏が取れた。** D1817 は相談 (A2) の当たりとして「追跡済みの
  anomaly 非空 JSON 5 件には複数 WW reason の edge が無く再発行は不要」と書いていた。
  親が追跡下の JSON / JSONL を全数 parse したところ、理由を持つ辺があるのは 6 件
  (verifier.json 5 件 + wal.jsonl 1 件) で、**ww を 2 本以上持つ辺は 0 件**だった。
  text renderer の出力面でも 0 件 (`ww key=` を含む追跡下 file は 2 件、1 行に 2 個持つ行は 0 件)。
  **凍結成果物の再発行は不要**という当たりは正しかった。
- **本 wave で一番効いた事実は、既存テストが整列の有無を区別できていなかったことである。**
  `test_verifier.py` の理由 golden 10 ブロックのうち ww を 2 本以上持つものは 0 件で、
  整列を外しても既存テストは全部緑のままだった。**1 行の修正より、その 1 行を撃つ正例の設計が
  実質の作業**になった。変異 3 件の赤 node が新テスト 1 件の完全一致だったことが、この静的走査の
  実走裏取りになっている。
- **`certified` は assert しないと裁定した。** 段 3 のレンズ A は正しさ gate 側の値も固定せよと
  指摘したが、親が実測すると本 wave の合成 trace は proof-surface metadata を持たないため
  counter が全部 0 でも `Integrity.clean()` が False になる。`certified is False` は
  「cycle があるから」と「integrity が unclean だから」の 2 つの独立な理由で成立し、
  `DW-M03` の過剰決定に当たる。cycle だけで決まる `verdict` / `serializable` / `phenomenon` を固定した。
- **変異の区分は `diagnostic sensitivity pin` にした。** 受理集合も fail-closed 挙動も変えず
  構造化シグナルの順序だけを pin する変異なので、`DW-M08` の明文により correctness kill として
  数えない。段 6 のレビュー B が独立にこの区分を支持した。
  `key=hash` で整列する候補は、hash 値が seed で変わることが 6 key の相対順の変化を含意しないため
  期待 node を事前確定できず、登録から外した。
- **enforcement closure の扱い。** dsg.py は `campaign_lock.py` の 63 path 閉包に入るので
  bytes を変えると旧 commit を束縛した campaign の live resume が drift する。D1388 のとおり
  binding は緩めず再走で作り直す。本 wave の作業ではない。
  「path 以外を key にした束縛が無い」ことは探索では原理的に閉じないので、**dsg.py が直近 1 週間で
  3 回変わっており main が緑である**ことをもって live pin の不在とした。
- **段 3 の敵対相談が親の探索閉包を 3 件突き、いずれも実測で解消した。** (1) wr 枝の順序安定性は
  「同じ list を走査するから」という一般化だったので、WR 理由 6 本を持つ辺を作って 6 seed で
  測り直した (全 seed 同一順)。(2) 束縛調査は上記のとおり履歴で閉じた。(3) text 出力面の走査を足した。
- **段 6 のレビューは実装に must-fix ゼロ、運用面に 2 件を出した。** subprocess の timeout 30 秒は
  混雑した共有ノードで正しい実装を偽赤にするので 120 秒へ、`check=True` は子の stderr を隠して
  赤の原因を判別不能にするので終了コードの assert + seed/rc/出力末尾の表示へ改めた。
  焦点再レビューは全 14 所見の対応表を出し 13 closed / 1 partial で閉じた。
- **受入所要時間台帳は触っていない。** worklog 1367 が実測したとおり、branch 側で同 file を更新すると
  main を取り込むたび競合し、解決 merge を land が rc=23 で拒否して受入をやり直す循環に入る。
  被覆 gate は「登録済み ÷ 収集 >= 0.90」で 20042 / 21867 ≒ 91.65%、閾値まで約 1.65 point の
  余裕がある (段 6 レビュー B が独立に検算)。登録は台帳更新を主目的とする別 wave が行う。
- **受入全走は本記録を含む最終 tip に対して 1 回だけ投入する。** land は tested_tip をそのまま
  取り込むため、記録より後に走らせられない。結果は land の receipt が持つ。
  投入前の関門は緑である — 変更 test file の単独走 106 passed (4.19 秒)、参照関係で引いた
  consumer 12 file が 1548 passed / 4 skipped (62.93 秒)、変異 baseline PASSED、
  全史 provenance 監査 8988 件で新規違反なし。
- **残る限界。** 固定 seed 2 本の検出力は実測した CPython 3.10.12 に対する実証であって形式証明ではない。
  本テストは `workers=1` だけを通し、worker 数間の report 同一性は検査対象ではない。
  型注釈を破った手製入力を `DSG` へ直接渡すと整列が `TypeError` を出すが、通常の trace 経路からは
  到達しないため防壁は足していない。

## 次の一手差分

### 完了

- [T-2436] `_reasons()` の WW 交差を key 順に整列し、seed を変えた 2 process の report bytes 一致を
  見る正例を足した。凍結成果物の再発行は不要と実測で確認し、live resume は D1388 のとおり再走対象と
  して据え置いた。
  remaining: none
  base: d0855af3fecb941abed570254bf0c07d9e806a257cb6f6fc1c0f72d0c295c3ac
