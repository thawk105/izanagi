---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2074-a1-estimand-realign
seq: 1
title: [T-2074] A-1 の estimand 揃え直しを実装しきり、変異 14 件で受理集合を裏取りする
---

## 本文

- **中断からの再開。** 前セッションは親が `cd <別 worktree>` を裸で打って永続シェルの
  作業ディレクトリを動かし、worktree 隔離 guard が全コマンドを拒否して復旧不能になった。
  作業は全て commit 済みで失われていない。本セッションは `bash -c 'cd <path> && <cmd>'` の
  部分シェル形だけを使った。同じ罠を一度踏んだが即座に復旧している。
- **fix 3 巡目が全損していた原因を特定した。** prompt が子に `git checkout` と
  `git reset --hard` を実行させていたが、linked worktree の `.git` は本体 repo 配下にあり
  codex の workspace-write sandbox からは read-only である。子は
  `index.lock: Read-only file system` で落ち、何も着手しないまま終わっていた。
  背景 log は空で rc=1 しか出ないが、**receipt の `attempts[].failure_class` と
  `attempt-0001.output.md` に理由が載っていた**。以後 worktree の同期は親が行う。
- **子が実走できないことが import 漏れを全走まで隠した。** fix 3 巡目は静的検査を通したが
  `collections.Counter` の import を落としており、子は sandbox から計算ノードの queue を
  引けない (`qstat -Q preflight rc=1`、runner rc=16) ため自分では気づけなかった。
  親の全走 1 回 (7 分 25 秒 + queue) を丸ごと使って露見した。fix 4 巡目で閉じた。
  これは `DW-O16` の 3 巡上限にある「親の実機 blocker は別枠」に当たる型である。
- **変異は probe → 較正 → 本走の 3 段で回した。** `DW-M08` が期待 node の完全一致を
  要求するため、まず全件 SURVIVED 期待の probe で観測 node を集めた。
  その結果、**変異が狙った gate とは無関係に一律で落ちる冗長 gate**が
  386 件あることが分かった (`{{F:mutation-drift-mask}}`)。
  さらに main 取り込みで冗長 gate が 383 → 386 へ増えたため、本走の前に 2 変異だけの
  較正走を挟んで現 tip の集合を実測した。較正を省いていれば `pipeline.py` を変異させる
  5 件が全て食い違い、3 時間の本走を無駄にしていた。
- **M3 は初回 probe で生存し、実効 gate へ再照準した** (erratum は変異台帳に逐語で残す)。
  最初の anchor は `_BenchResult` の `cv` を突いていたが、実効 gate
  (`test_balanced_schedule_cv_is_all_rep_cv_not_mean_block_cv`) が見ているのは受領証側の
  `arm_records[...]["cv"]` だった。初回の生存結果は erratum として残す (`DW-M02`)。
- **消えた repo 外 corpus で全 wave が land 不能になっていた件は、別セッションが解決した。**
  09-01 00:54 に `~/.codex/sessions/2026/07` が codex CLI 側で剪定され、
  `test_codex_reasoning_ab.py` の 26 node が決定的に赤になって main が 00:58 から
  5 時間 37 分止まった。本 wave も同じ赤を踏み、`--deselect` は受入 receipt の argv 完全一致で
  塞がれ、hold 登録は main 着地済み F を要求するため land 前に置けないという**相互依存**を
  実測している。06:35 に修正が着地し (skip 判定を根 directory から pin された rollout の実在へ
  変える形。テストは緩めていない)、本 wave も取り込みで解消を実測した。
- **並行セッションの取りまとめ役と調整した。** fold gate が login node で pytest を直接走らせ
  固定 130 秒 / 145 秒の予算を持つため、同時 land は全員 `rc=31` になる (実測 load average 75)。
  今夜は 1 本ずつ直列に通しており、本 wave も投げる前に一報して順番をもらう。

## 次の一手差分

### 更新

- [T-2074] **P1・実装完了、実走待ち**: 新 estimand の実装・検査・変異裏取りは終えた。
  残るのは pilot (各 workload 60 対) の実走、sizing、本走 policy の凍結、本走である。
  base: 8fa6a5b659e28388cb1578c07cfc0fb9aeeb80c616ee84c58177f1169590400a
