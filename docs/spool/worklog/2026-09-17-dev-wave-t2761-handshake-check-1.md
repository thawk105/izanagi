---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2761-handshake-check
seq: 1
title: [T-2761] release handshake 不在検査を環境 path 非依存の候補行検査へ置換した — F1022 の恒久対応、暫定防壁 (wave 名に release を含めない) は不要 (コード + テスト + docs、branch worktree-dev-wave-t2761-handshake-check、変異 matrix = 新 arm baseline PASSED・負例 5/5 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0、旧 HEAD arm b-handshake KILLED 1/1)
---

## 本文

- ユーザー依頼は「`test_compute_marker_is_cross_namespace_evidence_without_release_handshake` が script 本文へ掛ける
  `"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する release 行) の不在検査へ
  変える。着手直前の local main から fresh worktree。Codex author (D95)。変異事前登録 = (a) repo path に release を含む fixture で緑、
  (b) handshake 行を注入した script で赤。着地後に暫定防壁が不要になる旨を worklog に書く。規律 2 を緩めない。本題の検査置換だけ。
  追加 gate は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2761-handshake-check/README.md`。設計判断は
  {{D:path-independent-word-absence-check}}、失敗の型は F50 再発 + F1022 supersede。実装 commit `6dcbf6113` (Codex author、test file 1 本)。
- **暫定防壁は不要になった。** 6 つの環境依存の埋込み値 (submission dir 配下 4 path、repo_root 配下 2 path) を位置限定で token 化し
  (固定 basename・suffix・`DC._COMPUTE_MARKER_NAME` は残す)、正規化後の本文の release 候補行を全件拒否する。memory
  `wave-slug-must-not-contain-release.md` の「wave の slug / branch / worktree 名に `release` を含めない」は撤去してよい。
  **ただし release 専用の防壁だけ**で、`"while" not in script` の同型偽赤は scope 外で残る (次の一手に起票)。
- ユーザーの括弧書き「marker を操作する release 行」を同一行共起に狭めなかった理由 = 旧検査が拒否していた `RELEASE=1` 単独行・comment・
  alias 経由の複数行待機 (`gate="$MARKER"` / `RELEASE_FILE="$gate.release"` / `until …`) を見逃すため (規律 2)。広い定義はその部分集合を含む。
- **段 2/3 を 1 度 invalidate した。** 段 1 で `DW-O13` を参照節の本文を読まずに非成立と判定したが「受理形を増やす既存述語の改訂」に
  該当し、段 3 の後に気づいて読み込み契約どおり段 2 から再実行した (F50 再発、codex 3 本分の再投入)。v1 の所見は v2 brief へ取り込んだ。
- 段 3 v2 の must-fix 2 件を裁定で採用: needle が shell word の接頭辞に当たる境界反例 (`/__t2761__/rele` + template `ase`) → 置換前提に
  word 終端検査を追加。負例の即抜けを file 実在 (`-f "$marker_tmp"`) から非空変数 (`-n "$MARKER"`) へ (書込み失敗時の hang 経路を塞ぐ)。
- 段 6 レビュー A の must-fix 1 件 (改行を含む basetemp に `REPO=<repo path>` が埋め込まれると置換前提検査が偽赤) は親が
  real / nit / 不採用と裁定 (仮想リスク、DW-G05)。既知の限界として D に記録。レビュー B は must-fix なし。fix 子なし。
- 実走 (すべて計算ノード dispatch): 対象 2 node 2 passed (request 4017)、file 単独 339 passed (request 4038)。login probe (dispatch なし):
  marker 定数を `compute-visible.release` に差し替えると候補行に現れて赤、境界反例は word 終端検査で赤、対照は緑。全史 provenance
  11,076 件、新規違反なし。受入全走は docs commit 後の最終 tip に land 前に 1 回 (結果は land の受領証)。
- **変異 matrix (container 2 本、計算ノード dispatch、probe 走で観測 node を集めてから本走)。** 新 arm (実装 commit): baseline PASSED、
  負例 5 件 (a-old-check `{R}`、b-handshake / ab / b2-alias / b3-same-line `{C,R}`) すべて KILLED で期待 node と観測 node が完全一致、
  等価 m0-comment SURVIVED、MISMATCH 0、TIMEOUT 0。旧 HEAD arm (38353207f): b-handshake KILLED `{O}` 1/1。a-old-check の赤は旧 assert の
  `'release' is contained here:` に合成 path = F1022 の再現、b の赤は release 候補行 assert の注入行のみ (単一理由)。
  runner は container の `dispatch_compute.py` 経由なので `_job_script` への本物の待機注入は dispatch を hang させる (DW-M07) —
  負例は実行時に即抜ける until 行にし、marker 定数改名は login probe で代替した。DW-M08 の新旧両走は「新 baseline が合成 release path を
  受理・旧検査復元が同 path を拒否・handshake 注入は新旧とも拒否」の 3 点で示した (偽赤除去 wave に「新テストだけが検出する差分」は無い)。
- 段 8 (自己改善): 候補 1 件 (DW-O13 の判定漏れ) は routing 1 (failures、F50 再発) で記録済み。入口・reference の byte 予算は満杯で
  条件表の文言変更は行わず。段構成・権限の変更なし。
- 工数: codex 子 8 本 (plan 2、consult 4、author 1、review 2、fix 0、全段 `gpt-6-astra` / `medium`)。親: 焦点走 2、login probe 1、
  変異 4 走 (18 run)、provenance full 1、受入 1。

## 次の一手差分

### 完了

- [T-2761] test 側の是正を着地し、暫定防壁 (wave 名に `release` を含めない) が不要になった。`while` の同型偽赤は別起票。
  remaining: none
  base: b29d66f30e6e9e50700ec5fed6e7a3b414b20a858efad29040158468bfba8579

### 新規

- {{T:while-path-false-red}} **P3・新規** (F1022 と同型): 同 test の `assert "while" not in script` は元の script に掛かったままで、
  repo / submission path に `while` を含むと偽赤になる。{{D:path-independent-word-absence-check}} の標準形 (位置限定の正規化本文へ掛ける)
  へ揃える。Codex `role=author`。変異 = (a) path に `while` を含む合成 repo_root で緑、(b) template へ `while` 待機行 (即抜け) を注入して赤。
