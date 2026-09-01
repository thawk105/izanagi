# 段 1 brief — [T-1777] A-1 の対の配置を交互配置へ改める

wave = `worktree-dev-wave-t1777-interleaved-impl`、基準 commit `08a17b3b3` (着手直前の local main)。

## 依頼された scope

閉包 4 member (`ident.py` / `wal.py` / `loop.py` / `pipeline.py`) と driver に、
「単一 campaign の 5-rep ブロック交互 + AB/BA 均衡」の coordinator を入れる。
本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。

## (P1) 親の provisional 裁定 — 攻撃対象

**(P1) 依頼が置いた前提「残るのは実装である」は、着手直前の local main では既に成立していない。**
T-1777 の次の一手 (1) が列挙する実装 — 閉包 4 member の coordinator・ブロック実行器・profile・
collector・投入 selector — は `08a17b3b3` にすべて着地している。したがって本 wave の実装面の
純増はゼロであり、段 4 で「実装しない」と裁定する見込みである。

実測した根拠 (すべて `08a17b3b3` の現物、file:line は本 worktree)。

- 着地 commit 3 本が main の祖先: `ed61448f6` (D1262 の arm 対 + D1295 の均衡配置)、
  `73c6473fa` (配線欠落と受理集合の穴)、`a1f91bdbe` (並行 fix の合成不整合)。
- `ident.py:36-51,76-80,493,524` / `wal.py:97-116,144-150,1834,2004,2015` — 新配置名
  `balanced-a5b5-b5a5-v1` と新 study ID 2 本を exact identity へ追加し、中断を terminal invalid
  へ閉じる経路まで入っている。
- `loop.py:253-282,381-392,424,474-590` — 両 arm を先に `_prepare_evaluation` し、
  `_run_balanced_schedule` へ渡す coordinator。
- `pipeline.py:463-465,532-563,596-640,1904-2210` — 単一 `bench_lock()` で全ブロック、
  5-rep ブロック交替、group ごとに `A^5B^5B^5A^5` / `B^5A^5A^5B^5`、全ブロック完了後にのみ
  `bench_done` と schedule 受領証を出す実行器。
- driver・profile・collector・投入 selector・job script: `paper_story_a1_paired.v3-pilot.json`、
  `paper_story_a1_paired.py:88-89,120,745-755,1527-1600,2002-2013,4227,5103,5375`、
  `tools/pegasus/paper_story_a1_paired.sh:26-60`。

## 不変条件

- 実装面 (コード・テスト・機械設定) を親は直接編集しない。実装面の変更が要ると裁定した場合だけ
  Codex `role=author` を起こす。
- 凍結済みの v2 study と `paper_story_a1_paired.v3-pilot.json` の bytes を変えない。
- 規律 2: 正しさゲートを緩める変更を入れない。受理集合を変えない。
- worklog / decisions / failures は直接編集せず `docs/spool/` の fragment として書く。fold は段 9 の land。

## 成果物の形

- (P1) が生存した場合: 実装面 0 の docs-only wave。insight (D1295 の 7 項目とコードの対応表 +
  検証手順) と worklog fragment (T-1777 の次の一手を実測どおりの現在地へ直す)。
  残る (2)〜(5) は計測と凍結であって実装ではない、という区別を明記する。
- (P1) が反証された場合: 欠けている実装面を段 4 で scope 化し、段 5 の Codex 実装子を起こす。

## 成果物影響 (DW-G05)

(P1) を放置すると、worklog の「次の一手」が完了済みの実装を未了として提示し続け、
next-tasks が同じ wave を再投入する。逆に (P1) を誤って採ると、実在する実装の穴を docs だけで
閉じたことにする。どちらも台帳の値と参照を誤らせるので、(P1) の裁定自体が本 wave の本体である。

## 分割方針

実装面の純増が無い見込みなので段 5 の実装子は起こさない。ただし (P1) は正しさに関わる主張なので、
独立レンズの read-only codex 1 本で敵対検証する (段 3 相当)。所見が real なら段 4 で scope を作り直す。

## 受入・実測環境

login node では pytest 直実行が hook で拒否される。テストは `tools/dev_wave_wait.py acceptance`
の受入経路 (dispatch) だけで走らせる。段 7 の記録 commit 後に最終受入を投入する (DW-O12)。
