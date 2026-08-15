---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1038-tracked-handoff
seq: 1
title: 起動検査が main landed handoff を通すようにし、握り潰されていた不適格 index record を明示拒否へ変えた — 敵対 4 本が「tracked」の literal 実装を 1 手の gate 迂回として倒した (コード + テスト、変異 9/9 KILLED、branch worktree-dev-wave-t1038-tracked-handoff)
---

## 本文

- 起点は [T-1038] (a) の裁定「`_check_worktree_handoff` は tracked file を foreign control-plane と
  して通し、untracked のみ残置と見なす」と、同 wave の未採番裁定「submodule 初期化失敗時の提示文を
  `-c protocol.file.allow=always` 形へ直す」。裁定の正本は archive entry (537) で、538〜554 の
  「次の一手」はすべて carry stub であることを実測して確認した (覆す後発裁定なし)。
- **裁定文の「tracked」を literal に実装すると、gate を 1 手で迂回できる。** 段 3 の敵対レンズが
  示した具体経路は `git add docs/handoff/x.md && git commit` — index に載るだけで受理されるため、
  自 wave が自分の handoff を commit すれば起動検査を黙らせられる。裁定文の「foreign control-plane」
  は land が保護する対象 = main が持つ file を指すと解し、受理条件を **main landed**
  (index の OID が `refs/heads/main:<path>` と一致) へ狭めた。裁定より狭い方向であり
  絶対規律 2 に反しないが、literal な「tracked」が意図だった場合の緩和方法を {{T:handoff-tracked-literal}}
  として裁定へ返す。設計判断は {{D:handoff-main-provenance}}。
- **段 6 のレビュー 2 本が独立に、実装の受理集合を広げる欠陥を暴いた。** 不適格な直下 index record を
  「受理候補から外す」だけで捨てていたため、worktree に同名 entry が無ければその index 状態は
  どこにも現れず rc=0 になる。`git update-index --skip-worktree` を付けて file を消すだけで
  gate を通せた。直下 record を受理/拒否に明示分類し、拒否が 1 件でもあれば filesystem の有無に
  関係なく failure にした。述語ごとに別診断を出すため、mode / stage / tag の各検査が
  `rev-parse` の成否に依存せず単独で発火するようになり、レビュー D が「SURVIVED する」と予測した
  変異 3 本がすべて KILLED になった。
- **段 2 のプランは、そのままでは本番経路で必ず失敗する実装だった。** `_git()` が stdout を
  `.strip()` するため `-z` 出力の NUL 終端が消え、プランの「NUL 終端でなければ fail-closed」検査が
  常に発火する。段 3 のレンズ B が静的に発見し、strip しない `_git_raw` を足して閉じた。
  既存 6 呼び出しの挙動は変えていない。
- **refuted 2 件 (親が real と認めたうえで不採用にしたもの)。** (1) worktree の raw bytes を
  blob hash して main と照合する案 — `git check-attr filter text eol -- docs/handoff/README.md` が
  すべて `unspecified` で、この repo の handoff に clean/smudge filter も EOL 変換も適用されない
  (global config の LFS filter は `.gitattributes` 不在で発火しない)。checker の出力は
  いかなる成果物の provenance にも記録されないため `DW-G05` の成果物影響を書けない。
  (2) main 側 mode の検査 — 閉じるには `ls-tree` を read-only allowlist へ足す必要があり、
  防壁を 1 つ狭めるために別の面を広げる取引になる。いずれも残存限界として
  {{T:handoff-content-and-mode}} へ起票する。
- **wave 開始後に main 側で同じ問題が 2 度目の手動撤去を受けた。** `952fd45d` が
  `docs/handoff/dev-wave-t971-swo-oracle-floor.md` を main から直接撤去している。
  F286 の「land は handoff の追加を許すので、次に wave が handoff を land した時点で同じ赤が
  再発する」という予告どおりであり、`a3168d85` (2026-08-13) に続く 2 例目である。
  本 wave の修正で checker 側の恒久対応が入った。
- **段 1 の documented deviation は解消した。** 開始時 (07:22 JST) は
  `--external-handoff` 付き検査が `NG: worktree-local handoff remains
  (dev-wave-t971-swo-oracle-floor.md)` の 1 行だけで rc=1、当該 file は tracked
  (`git ls-files docs/handoff/` = 2 件、`git status --short docs/handoff/` = 0 行) だった。
  他の NG はゼロだったため 1 件のみを deviation として続行し、main 取り込み後は rc=0 になった。
- **完了条件 ([T-1028]) の実データ検証。** fix 後の最終 tip で
  `python3 tools/check_wave_startup.py --mode resume --external-handoff <repo 外 handoff>` が rc=0。
  さらに新判定が実データ上で生きていることを、`docs/handoff/README.md` へ
  `git update-index --skip-worktree` を付けて確認した — `NG: worktree handoff index tag is not H
  (docs/handoff/README.md: S)` で rc=1 になり、`--no-skip-worktree` で戻すと rc=0、
  作業ツリーは 0 行差分に復元した (index flag のみの可逆 probe)。
- **測定環境の異常 1 件。** 焦点走の bounded local が login node で 3 回連続 rc=16
  (`bounded scope の memory.max / memory.oom.group を走行中に attest できない` =
  dispatcher infrastructure failure) になった。同じ command が 08:22 には成功しており、
  テスト結果ではない。`--force-dispatch` で計算ノードへ回して 95 passed / 0 failed
  (2.53 秒) を得た。
- **エージェント工数:** codex 子 6 本 (plan 1・consult 2・author 1・review 2・fix 1)。
  全 6 本が完走し `check_codex_output.py` rc=0。異常なし。

## 次の一手差分

### 完了

- [T-1038] (a) checker 側修正と submodule 提示文の是正をどちらも実装した。変異 9/9 KILLED。
  [T-1037] / [T-1039] は wave 中に並行の棚卸しが「陳腐化 = 実測で解消、構造的な再発防止は
  [T-1038] が所有」として見送りへ移しており、その所有分を本 wave が果たした。
  remaining: none
  base: 357533da14106935c6a90ef03afdee4c143408e35cd58a7c00c097dc156b6ee1

### 新規

- {{T:handoff-tracked-literal}} **P3・ユーザー裁定待ち**: 本 wave は [T-1038] の「tracked」を
  「main landed」へ狭めて実装した。literal な「tracked」が意図だった場合は
  `rev-parse` 照合の 1 ブロックを落とせば緩和できる。どちらを正とするか。
- {{T:handoff-ownership-lifetime}} **P2・新規**: main に landed した handoff の所有・寿命・回収が
  未定義である。起動検査は main landed を通すが、`docs/handoff/README.md` は「ファイルが残っている
  = 稼働中か中断」と定義し、land は削除を rc=21 で拒む。(1) 所有と寿命の定義、(2) land での回収方法、
  (3) README 契約と `DW-O20` の意味を一体で裁定する必要がある。
- {{T:handoff-content-and-mode}} **P3・新規**: 起動検査の残存限界 2 件。clean/smudge filter や
  EOL 変換のある path では clean-tree との連言が raw bytes 一致を含意しない。また main 側の
  mode を検査していないため、main が symlink で worktree が同一 bytes の regular file の場合を
  区別できない。どちらも本 wave では成果物影響を書けず不採用にした。
- {{T:startup-git-timeout}} **P3・新規**: `tools/check_wave_startup.py` の `_git` は
  subprocess に timeout を渡していない (既存 6 呼び出しすべて)。git が無期限停止すると
  起動検査も止まる。単発なので `DW-G03` の独立 2 例が成立するまで起票のみとする。
- {{T:startup-help-text}} **P3・新規**: `--forbid-worktree-handoff` の help は
  「README.md 以外の worktree-local handoff が無いこと」とだけ書き、新しい受理条件
  (main landed) を反映していない。1 行の文言修正。

### 見送り追記

- [T-1037] 2026-08-15 に所有先の [T-1038] が checker 側の恒久修正を実装した (main landed だけを通す)。再訪不要。
- [T-1039] 2026-08-15 に所有先の [T-1038] が checker 側の恒久修正を実装した。S-2 (README の削除契約) は裁定どおり現状維持。
