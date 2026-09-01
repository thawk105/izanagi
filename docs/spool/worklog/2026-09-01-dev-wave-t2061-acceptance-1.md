---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2061-acceptance
seq: 1
title: [T-2061] 残っていたはずの受入全走は 3 日前に緑で着地済みだった — 次の一手 stub を書くのが land 自身の fold であるため済んだ項が 6 エントリ持ち越された (docs のみ、branch worktree-dev-wave-t2061-acceptance)
---

## 本文

- 依頼は「T-2061 に残っている受入全走を通して本項を閉じる」だった。段 1 で引数の前提を実測した
  ところ **前提が覆った**。T-2061 の受入全走は 2026-08-29 に既に緑で完了し、land も済んでいた。
  新規の受入全走は 1 回も投入していない。
- 一次資料は 4 点。いずれも `dev-wave-jobs/worktree-dev-wave-t2061-wal-admission/dev-wave-job-t2061/`
  にある当時の成果物と、現 repo の ref である。
  - `acceptance-receipt-3.json`: `schema_version` が `dev-wave-acceptance-receipt/v5`、
    `authority_kind` が `dev-wave-acceptance-launcher`、
    `acceptance_wave` が `dev-wave-t2061-wal-admission`、`verdict` が `child-green`、
    `child_rc` が 0、`red_nodeids` と `flake_nodeids` がともに空、
    `argv` が `python3 tools/run_tests.py` の全走、`env_projection` は 4 key すべて未設定。
    絞り込みでも非帰属赤の受理経路でもない、完全に緑の全走である。
  - `acceptance-child-3.log`: 18,983 件収集、18,916 passed、67 skipped、赤 0。
  - `land-1.log`: `status` が `landed`、main を `3bee2071d` から `921646ec2` へ ff、
    fold commit は `8d39f4394`。
  - `git merge-base --is-ancestor 921646ec2 main` が rc=0。tested tip は現 main の祖先である。
  - tested tip `921646ec2` の第 1 親は T-2061 最終実装 commit `d69c491a3` であり、
    受入対象が T-2061 の実装 commit 列を含むことを ref 側から確かめた。
- **「未了」と書かれ続けた構造要因を特定した。** 次の一手 stub「計算ノードの混雑で受入全走が
  残っている」を `docs/worklog.md` へ書き込んだ commit を `git log -S` で引くと、
  **fold commit `8d39f4394` 自身**だった。この fold は T-2061 の land が協調 lock の中で
  行ったものであり、その land を許可したのがまさに上の緑の受領証である。
  つまり **stub を canonical へ焼いた操作と、stub の内容を偽にした操作が同一の land** である。
  fragment は受入より前に書き終える規律 (受入は記録込みの最終 tip に 1 回だけ投入する) があるため、
  **受入の結果を知った後に fragment を書き直す窓が存在しない。** stub は書かれた時点では真で、
  数分後に偽になり、以後 entry 1111 から 1143 まで `(1110)` 形式で 6 回そのまま持ち越された。
  これは書き手の不注意ではなく、記録順序の規律と fold の実行時点がずれていることの帰結である。
- 同型の stale が他の持ち越し項にもありうるが、**本 wave では調べていない** (依頼が本題を
  受入全走と結果記録に限っているため)。件数を主張できる測定はしていない。
- 本 wave は実装面の差分がゼロである。`DW-S04` に従い変異 matrix は免除し、受入全走は免除しない。
  依頼の「受入全走を通す」は、T-2061 の再検証ではなく **本エントリを land するための gate** として
  実行した。`tools/dev_wave_land.py` は docs のみの wave でも `--acceptance-receipt` を
  構造上必須要求し、免除経路がコードに無いためである。
- 依頼の scope 指定に従い、gate・検査・台帳・一般化は 1 つも追加していない。
  上の構造要因についても新しい機構を作らず、本エントリへの記録だけに留めた。

## 次の一手差分

### 完了

- [T-2061] 受入全走は 2026-08-29 に `child-green` (18,916 passed / 67 skipped / 赤 0) で完了し、
  tested tip `921646ec2` が main へ着地済みであることを受領証・child log・land 結果・ref の
  4 点で確認した。新規の受入全走は不要と裁定した。
  remaining: none
  base: ddfeb5afcfb52400b2cbe1fe4d00ab018fb9f76a12c60904f0f3111f9d46e799
