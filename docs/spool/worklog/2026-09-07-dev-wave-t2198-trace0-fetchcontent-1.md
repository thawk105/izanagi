---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2198-trace0-fetchcontent
seq: 1
title: [T-2198] A-2 / A-6 認証経路の測定 build をオフライン依存へ配線した — 変異 probe が新設検査 3 本の穴を暴いた (コード + テスト + policy + shell + insight、branch worktree-dev-wave-t2198-trace0-fetchcontent、変異 19/19 KILLED)
---

## 本文

- D1693 (D1688 の案 1、ユーザー裁定) を実装した。閉じた trace0 configure 文法へ FetchContent の枠を
  厳密な期待値として足し、認証経路の測定 build を計算ノードの環境契約に合う staged 依存へ配線した。
  凍結された認証プロトコル同一性の golden 4 値 (5 箇所) を張り直した。**実測はしていない** —
  A-6 の read-heavy 認証を実際に走らせるのは次の wave である。
- **依頼文と F808 の前提 1 つが現行 main で偽だった。** 「`run_campaign` は FetchContent の
  source dir 引数を持たない」は T-2356 の commit `466528512` で既に解消済みで、共有 pipeline の
  横断改修は不要だった。裁定の効力は変わらないが scope は縮んだ。F808 へ supersede 追記で訂正した。
- **変異 probe 巡が、静的レビュー 2 本が見落とした穴を 3 件暴いた。** 新設した検査のうち
  非空検査・prefix 一致検査・policy 要素数検査の 3 本が、いずれも隣接する別の検査に隠れて
  どのテストにも固定されていなかった。負例を足し、狙った検査の項だけを落とすと対応する 1 node だけが
  赤になることを実測してから復元した。実装は変えていない (穴はテストの不足)。詳細は
  {{F:hidden-negative-behind-adjacent-check}}。
- 段 6 レビュー 2 本の must-fix 3 件はすべて受理集合を**狭める**方向だった。producer が生成できない
  path token (NUL 入り・非 canonical) を認証器が受理していた件 ({{D:trace0-path-values-bound-to-producer-domain}})、
  投入器が正規化後の値を再検査していなかった件、到達不能な下限検査が残っていた件。
  最後の 1 件は両レビューが独立に指摘した。
- 段 3 レンズ B が「`<name>-src` 配置を作る主体が設計から欠落している」を real で出した。
  入力契約を hydrate の実出力形へ変え、変換を job body へ置くことで、新しい供給機構も
  運用手順の変更も要らない形に改めた ({{D:certification-third-party-input-is-hydrate-layout}})。
- `protocol_sha256` が Python 側の判定式や qsub env の exact 集合を束縛しないという射程は、
  絶対規律 7 に従って**明記だけ**した。gate は増やしていない
  ({{D:certification-protocol-hash-scope-is-policy-document}})。
- 変異 matrix は 19/19 KILLED、生き残りゼロ、baseline は全巡 PASSED。ただし
  qsub env key を exact 集合から落とす変異は 74 node を赤にするため、単一理由性が成立せず
  **冗長 gate として単独変異の証拠から外した** (`DW-M03`)。段 3 レンズ A がこの過剰決定を
  事前に予測しており、実測が一致した。
- 変異 probe 巡は計算ノードの混雑で 9 走目に orphan-hold で中断し、変異が repo に残った。
  規約の復旧順序 (qstat 終端確認 → `git checkout --` で復元 → clean/HEAD 確認 → hold 2 file 削除) で
  復旧した。手動 qdel は使っていない。2 巡目は負例追加で parametrize の自動採番 id が 1 つずつ
  ずれたため collection 段で fail-closed に止まり、実 collection から id を取り直して再投入した。
- エージェント工数: codex 子 7 本 (plan 1 / consult 2 / author 1 / review 2 / fix 2)、
  いずれも `gpt-5.6-sol` reasoning=xhigh。親の焦点走 2 本と変異 3 巡は計算ノードへ dispatch した。

## 次の一手差分

### 完了

- [T-2198] D1693 の案 1 を実装し、trace0 の configure 文法へ FetchContent の枠を厳密な期待値として
  足した。golden 4 値 (5 箇所) を張り直し、認証経路・条件 gate・投入器・job body を staged 依存へ
  配線した。変異 19/19 KILLED。
  remaining: none
  base: 7814fd021b8281f037bef55370f0b7c36f38f515068fb318e6734d5029f1e7d2

### 新規

- {{T:a6-read-heavy-certification-run}} **P1・新規**: A-6 の read-heavy 認証を実際に投入する。
  `fetch_third_party.py hydrate` が作る `<root>/{masstree,mimalloc,googletest}` を
  `submit_paper_story_a2_certification.sh` の `--third-party-source-root` へ渡す。
  3 依存の実サイズ・`/scr` 容量・copy 所要は未実測なので初回投入で観測する。
