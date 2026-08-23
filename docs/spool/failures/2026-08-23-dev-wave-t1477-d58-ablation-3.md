---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1477-d58-ablation
seq: 3
---

## 新規

### {{F:merge-conflict-child-cannot-be-launched}}. merge 途中の作業ツリーでは Codex 子を起動できず、子自身に merge させることもできないため「子は競合解決だけ」が字義どおり実行不能だった [ドリフト] [手順不整合]

- 事象: [T-1477] の再開 wave で local main を取り込んだところ AI provenance の known-violation
  台帳 2 file が競合した。両親が同じ実装面 file を触るため `DW-O17` により競合解決は Codex
  `role=author` が担う必要がある。ところが `DW-C01` の定める形 (親が merge し、子は競合解決だけ)
  を実行しようとすると、2 段階で失敗した。
  (1) merge 途中の作業ツリーで子を起動すると
  `NG: docs/dev-wave/operations.md: working tree が authority commit と異なる` で rc=2 になり
  起動できない。`tools/dev_waves/launch_authority.py` の `snapshot_authority()` は `commit=None`
  のとき `docs/dev-wave/*` の working tree bytes が HEAD blob と一致することを要求するが、
  main 側でこれらの docs が変わっていると merge 途中のツリーは必ずこの検査に落ちる。
  (2) では子自身に `git merge --no-ff --no-commit main` を実行させればよいかというと、
  子の sandbox は `.git` へ書けないため `ORIG_HEAD.lock` の Read-only エラーで rc=128 になり、
  これも成立しない。
- 根本原因: 子の起動 gate (working tree == HEAD を要求) と、子に要求する作業 (working tree が
  HEAD と異なる merge 状態でしか存在しない) が両立しない。`docs/dev-wave/*` が両親で同一なら
  (1) は起きないため、この不整合は「main 側が dev-wave docs を触った期間に main を取り込む
  wave」でだけ発火する。今回はまさにその条件が揃っていた。
- 恒久対応: 実際に成立した手順は次のとおり。親が `git merge --no-ff --no-commit <main tip>` を実行し、
  競合した file の本文 (conflict marker 入り) を repo 外の job dir へ退避してから
  `git merge --abort` で作業ツリーを clean へ戻す。この clean な状態で子を起動し、
  「退避した本文を repo 内 path へ写し、marker だけを解消せよ。git は一切実行するな」と指示する。
  子の解決結果を親が job dir へ保存し、`git checkout --` で復元、改めて merge を実行して
  子の解決本文を転記し `git add` と commit を親が行う。この形なら子の起動 gate を満たしつつ
  解決の著作は子に残る。親は解決結果の全行がどちらかの親に存在することを機械照合して監査する
  (今回は「どちらの親にも無い行 0 件」、追加は構文成立用の区切りだけだった)。
- 未実施 (候補として返す): 上記手順を `DW-C01` の「mergeは親。子は競合解決だけ」の行へ
  1〜2 行で統合したいが、`DW-C01` は `tools/check_docs.py` の
  `DEV_WAVE_DW_C01_SECTION_LITERAL` で exact section literal として pin されており、
  節本文の変更は実装面 file (`tools/check_docs.py` と `orchestrator/tests/test_check_docs.py`
  の合成 fixture) の同時変更を要する。本 wave の成果物 (certified 選択・レポート・台帳) の値・
  受理集合・参照は変わらないため `DW-G05` に従い本 wave では実装せず、後続 wave またはユーザー
  裁定へ返す。
- 再発検知: main 側が `docs/dev-wave/*` を触った期間に main を取り込み、かつ両親が同じ実装面
  file を触る wave が、同じ rc=2 と rc=128 の対で即座に検知する (fail-closed のため実害は
  時間損失だけ)。
