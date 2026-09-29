---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: worktree-dev-wave-t2853-r2-fig6
seq: 1
title: [T-2853] R2 の fig6 単位 (A-2) を現行 driver・現行 policy 5 node で Pegasus に測り直した — attempt t2853r2-20260929a は observed-positive (rr5 +65.4129%・rr50 +12.8953%)、原 attempt と合成しない対照表と同じ生成器の図 (insight のみ、計算 2.16 node 時間、branch worktree-dev-wave-t2853-r2-fig6)
---

## 本文

- 見積りは同じ A-2・同じ 5 node 形の probe t2489 の Elapse (680 + 728 s × 5 node) で 1.96 node 時間、受入 0.25 を足して約 2.21 で線を越えたので、投入前検査を済ませてからユーザーに確認し「投入してよい」を得た (14:52 JST)。repro-rest の 1.70 は B-7 の Elapse を当てた試算で、同形の実測の方を使った。
- 実消費は 2.16 node 時間 (rr5 973 s・rr50 583 s × 5 node) で見積りを 0.20 上回り、受入を足すと確認時に示した 2.21 を超える見込み。超過は rr5 の Elapse (t2489 の 680 s に対し 973 s) による。原因は調べていない。
- trace 保全口は、driver の `qsub -v` が環境変数を固定で列挙し渡す口が無いので使っていない (driver の変更は scope 外)。
- collect の `--repo-root` を repo 外の一時 root にして、policy の tracked destination (原 attempt の dir) へは書かなかった。collect は既存 leaf を拒否する作りで、原 attempt を上書きする経路は元から無い。
- 図は生成器の Python の差し替え口 `expected_hashes` に実行時計算した sha256 を渡す repo 外 wrapper (Codex author 1 本) で描いた。陽性対照で既存 fig6 の artist_series と完全一致。provenance の再現 argv は生成器の直接起動で、pin 表に R2 が無いためそのままでは再生成できない (insight §5 に wrapper 経由の argv を書いた)。
- EnterWorktree が name 形 (git config 読み取り) と path 形 (worktree list の 10 秒上限) の両方で失敗したので、手動 add の作業木を絶対 path で使った。submodule 初期化 tool は 1 回目に rc=1 (入れ子 googletest 未初期化) を 3 か所で返し、wave 作業木は 2 回目も rc=1 だったが `git submodule status --recursive` で 3 本とも初期化済みを確かめた。
- 段 2・3 は軽量版で省略 (設計択一なし、repo の実装面の差分ゼロ)。変異は免除、受入は land 前の最終 tip に 1 回 (受領証 `/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/acceptance-receipt-1.json`、実測 Elapse は受領証と shard の会計にあり、tested tip の中には書けないので本 entry には書かない)。
- 段 6: レビュー A (一次資料・正しさ境界) GO 所見なし、B (過剰・削除) NO-GO の 3 件と焦点再レビューの 1 件はすべて docs で処置 (図の置き場の注記と、実行できる再生成手順。親が手順をそのまま実行して bytes 一致を確認)。
- 段 8: submodule 初期化 tool の rc=1 と木の完備が食い違う件は、DW-O08 の「なお赤なら止める」と「rc でなく中身で測る」の食い違いとして候補にしたが、原因を調べておらず dev-wave 文書の byte 予算も満杯なので、文書は変えずここに観測として残す。

## 次の一手差分
