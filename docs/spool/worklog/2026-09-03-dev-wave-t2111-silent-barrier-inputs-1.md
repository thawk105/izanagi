---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2111-silent-barrier-inputs
seq: 1
title: [T-2111] 歴史 corpus 消失で沈黙していた防壁 24 node を合成入力で復帰させた — 変更前は防壁を壊す 10 通りのうち 8 通りが素通りしていた (コード + docs、branch worktree-dev-wave-t2111-silent-barrier-inputs、変異 10/10 KILLED・期待 node 完全一致・新旧両走)
---

## 本文

- **読み切りの件数。** 群 A (共有 fixture `benchmark_snapshots` 経由で setup 死) は 21 関数 = 23 node、
  群 B (test 本体から直接 guard を呼ぶ) は 2 関数 = 4 node、群 C (terminal) は 1 関数 = 1 node。
  **合成可能は 21 件 (群 A 全件) と群 B の 3 node、合成不能は 2 件。**
  21 件は 1 件ずつ「何を入力に要求しているか」を file:line で読み切った。要約で済ませた件は無い。
- **律速は防壁ではなく共有 fixture だった。** fixture が POS golden と prompt の SHA-256 照合まで
  先に済ませるため、snapshot 木しか要らない test まで巻き添えで死んでいた。
- **親の検算 2 件が誤りで、子の指摘が正しかった。** (1) 「21 関数はいずれも parametrize されていない」は
  誤りで `test_m3_focus_artifact_directions` が 3 パラメータを持つ (走査が `[` 始まりの継続行で
  状態を捨てていた)。(2) guard 呼び出し行を隣の関数へ誤って帰属した。どちらも現物で確認して訂正した。
- **合成不能の 2 件目は D1382 との衝突ではない。** 段 2 の子は
  `test_m2_production_golden_requires_both_routes` を「裁定の前提と衝突する新しい terminal」と
  報告したが、これは (1119) が既に「回収不能な歴史 anchor 5 件」の 3 層の一つ
  「二経路の独立 golden 再構成」として分類済みで、21 件の外側である。新しい裁定は要らない。
- **terminal の扱いを裁定した ({{D:terminal-is-a-record-not-a-skip}})。** プランは terminal 1 件へ
  静的 skip を足す案を出したが、その関数は実データ無しでも走る assert を持つため、
  関数ごと skip すると受理集合が広がる。**「terminal に落とす」は記録上の分類であって
  検査を止める指示ではない**と裁定し、参照の付け替えだけに留めた。
- **正直に記録すべき副作用。** 復帰した経路では期待値を入力と同じ処理から作るため、
  歴史内容に対する独立 oracle ではなく自己整合性検査へ縮退する。ただし失われるのは
  D1382 が「復元しない」と定めた歴史 anchor の主題であり、21 件の防壁の主題ではない。
  敵対レビューが (a) 歴史 anchor / (b) 防壁 の二分で全箇所を判定し、**(b) の喪失 0 件**を確認した。
- **エージェント工数と中断。** Codex 子 5 本 (plan 1、敵対相談 2、実装 1、敵対レビュー 2 のうち
  レビューは枠復帰後)。実装子は 64 model call・1276 秒まで進んだところで
  **Codex のサブスク利用枠切れ**に当たり、最終報告を書かずに終了した。**実装そのものは
  working tree に完成しており**、契約 (編集 1 file・commit しない・tool 無変更) も守られていた。
  親が実測して保全し、枠が戻るまで段 6 へ進まず fail-closed で停止した。追加購入はしていない。
- **測定の訂正。** 当初「所要が 16 秒から 260 秒へ増えた」と報告したが、これは入口の違う 2 走
  (`tools/run_tests.py` 経由と生 pytest の serial 走) の比較だった。同じ入口で揃えると
  **16.06 秒 → 59.26 秒**。増加は事実だが当初の見立ては過大だった。
  段 6 の review へは訂正前の前提で問いを渡してしまったため、その回答は読み替えて評価した。
- **敵対レビュー 2 本は blocker ゼロ。** 「緑になっただけで何も守っていない」可能性を
  24 node 1 件ずつ判定させ、赤にならない node 0 件。段 3 が出した blocker 2 件・must-fix 4 件は
  すべて closed。main 67 commit 取り込みとの合成干渉も無し。
  残った must-fix 1 件 (構築処理の重複) は、レビュー自身が「正しさも受理集合も変わらない」と
  書いており DW-G05 により backlog へ降格した。fix 子は立てていない。
- **変異の erratum ({{F:mutation-container-submodule-and-resume-trap}} とは別件)。**
  初回 probe で 2 件が狙いを外した。`GIT_*` 洗浄の関門は **SURVIVED** — 洗浄自体は
  `_clean_environment` の allowlist が構造的に担っており、当該 assert は**冗長 gate**だった。
  schedule digest の変異は復帰 node ではなく既存 test に先に捕まった (**他層の mask**)。
  実効 gate へ再照準 (前者は 3 層同時変異、後者は束縛関数そのもの) して両方とも狙いの
  復帰 node を殺した。**初回結果は消していない。**
- **置換数の変異は負例 2 node だけを殺し、正例 `[9]` を殺さない。** 正例が恒真でないことの裏付け。

## 次の一手差分

### 完了

- [T-2111] 沈黙した防壁 21 件の入力要求を file:line で読み切り、件数 (合成可 21 + 群 B 3 node、
  不能 2) を確定した。合成可の件は局所修復で復帰させ、変異 10/10 KILLED・期待 node 完全一致で
  実効性を実証した。歴史 anchor は復元していない。合成不能な 1 件は
  {{D:terminal-is-a-record-not-a-skip}} に従い記録上の terminal として扱い、skip を足していない。
  remaining: none
  base: ec48277d73f619a95e572f58eb2a5ca51939d166421e367a3a781daa2793697e

### 新規

- {{T:benchmark-fixture-construction-sharing}} **P3・backlog**: 復帰した suite の構築処理に
  共有できる重複がある。`_full_manifest` が同じ 10-run experiment を 4 回、
  `_supervisor_pair` を 2 test が別々に構築する。**正しさと受理集合は変わらない**ので
  must-fix ではない。同じ入口で揃えた実測の増分は 16.06 秒 → 59.26 秒であり、
  受入全走の予算への寄与を測ってから着手可否を決める。**費用を削るために検査を減らさない。**
