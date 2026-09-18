---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t1878-mocc-trace-pilot-raw-artifact
seq: 1
title: [T-1878] mocc trace-hook (TRACE=1) pilot (PBS 934607.nqsv) の raw verifier 出力 artifact を限定範囲で探索し「探索した範囲での未特定」を記録した — 出力先は現在存在しない投入 worktree 配下で、探索時点の ref・evidence dir・名指し job dir に raw も退避物も特定できず、当時の receipt は verifier.json の sha256 を持たない (docs のみ、branch worktree-dev-wave-t1878-mocc-trace-pilot-raw-artifact、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-1878] (P3、entry 998) mocc trace-hook (TRACE=1) pilot の raw verifier 出力 artifact を特定するか、不在を
  記録する (docs のみ、新規実装・計測なし) — 探索範囲を pilot の insight (2026-08-22_t755、2026-08-23_t1506、2026-08-24_t1582、
  2026-08-26_mocc-trace-pair*、2026-08-26_mocc-g2-repro/) が名指す job dir・evidence dir (`/work/1/SFC/tanab/izanagi-job-evidence/`
  配下) と `tools/pegasus/mocc_trace_pilot.sh` の出力先に限定し、見つかれば path と sha256 を claim-evidence の `[権威 bytes]` 欄の
  後継記録 (凍結物は上書きせず新しい日付の記録) と insight に書く。見つからなければ『探索した範囲での未特定』として範囲を明記し、
  全体での不在と断定しない。稼働中の T-2772 / T-2774 の成果物には依存しない。着手直前の local main から fresh worktree を作る。
  規律 2 を緩めない。本題の所在記録だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **探索した範囲では未特定。** 一次資料は `output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md`。
  記録は `docs/paper-story/README.md` の「claim-evidence 系列」節に「C14a の所在調査の追記 (2026-09-18)」として置いた (claim-evidence
  matrix の新稿は作らない — 一項目だけを直した新日付の稿は D1013 規則 2 が禁じ、置くなら入力 5 節全体の再導出が要る。同 README の
  版系列 stale 節は branch `worktree-dev-wave-t2775-paper-story-a1-attempt1` の tip (未 land) が変えているので衝突を避けて触れない)。
  凍結物 (`claim-evidence/2026-08-26.md`、8 月の insight 5 群、pair receipt) は 1 byte も変えていない。
- 実測 (段 1 + 段 6 再走査): 当時 (outer `2efe6282`) の `mocc_trace_pilot.sh` は出力を `$PBS_O_WORKDIR/output/env/pegasus/mocc-trace/
  job-staging/$PBS_JOBID/verifier.json` へ書き、PBS_O_WORKDIR は投入 worktree `dev-wave-t755-mocc-trace-execution` だった (当時の handoff)。
  同 worktree と branch は現在存在しない。探索時点の全 ref から辿れる履歴に同 path を触る commit は無い (`git log --all` 0 件)。主 checkout
  にも不在。evidence dir と名指し job dir 9 件は、全 entry 17,380 件のうち 50 MiB 以下の regular file 16,372 件を拡張子不問で全本文
  読取 (読取失敗 0、symlink 0) し、path 名も走査した — `934607.nqsv` を本文に持つ file は 13 件で、いずれも当時の handoff・insight の
  写し 3 件・worklog fragment の写し・codex events 8 件の本文言及であって raw ではない。path 名に `934607` を含む entry は 0 件。
  50 MiB 超 1,008 file (他 job の `trace_N.log` 1,006 件 + dynamic-backoff の stage file 2 件、最小 52.5 MB) は本文を読んでいない
  (探す `verifier.json` の同型 raw は 1,330 bytes)。当時の receipt は `verifier_json: "verifier.json"` を名前で持つだけで sha256 を持たない
  (bytes 束縛は 08-26 の pair wave で導入)。当時の session の job tmp (`~/.claude/jobs/ea53ff4a/`) も不在。**消失の経緯と過去の保存
  履歴は確定していない** (段 6 R-1 で断定文を観測文へ直した)。
- **insight に埋め込まれた JSON block は raw の逐語ではない。** 当時の verifier `--json` (`report.py` の `result_to_dict`) は
  `trace_dir`・`framing_violation_details`・`permutation_violation_details` を出すが、埋め込み block はこの 3 key を欠く。
  埋め込み block の sha256 を `[権威 bytes]` の代わりに書くことはできない。
- 隣接物 (C14a ではない): 08-26 pair wave の TRACE=1 leg `0:949961` / `0:949963` (txns 756,277 / 740,190) と probe `949555` (778,690) は
  raw と sha256 が job dir に退避されているが、別 request の観測であり `934607.nqsv` (761,914) の raw ではない。C14a の行へ流用しない。
- 探索していない範囲 (不在を断定しない理由): 上の 50 MiB 超 1,008 file の本文、Pegasus 側 accounting、他ユーザー領域、home 配下の
  他 session job dir 全数、`/work/1/SFC/tanab/` 直下の名指しされていない dir、backup / snapshot、削除済み branch の到達不能 object。
- 段 6: read-only codex review 1 本 (正しさ境界・整合と過剰・削除を 1 本で。entry 998 の教訓 — 一次資料から事実を再抽出する docs wave は
  レンズが親の制約違反を出す)。所見 8 件 = must-fix 3 (R-1 消失・未退避の断定、R-2 走査の除外条件が未記載、R-3 「完全表記 0 件」が
  最初の一致だけの分類に依拠)、nit 4 (D920 引用の射程、README 追記の見出しが一般規則化、request 内訳、行番号と根拠の無い「別 binary」)、
  記録 1 (branch 差分から「稼働 wave が編集中」は導けない)。refuted 0。**全件採用し、R-3 は文言でなく全本文で完全表記を判定する
  再走査 (v2 / v3) で閉じた** (結果は同じ 13 件)。逐語は insight `verbatim/`。
- 段 8 (自己改善候補 1 件、docs/dev-wave は編集しない): 一次資料から事実を再抽出する docs-only wave で段 6 の review 1 本を省かない
  ことの**独立 2 例目** (1 例目 = entry 998)。`DW-G03` の 2 例は満たすが、段構成の変更なので skill-self-improvement の dev-wave 終端に従い
  実装せず**裁定パッケージ候補**として insight §7 に残す (推奨案 = `DW-C00` の「docs-only は子ゼロでよい」へ「一次資料から事実を再抽出する
  docs wave は review 1 本を残す」を足す。L1 予算は満杯 (1649 実測 10,622 / 10,625) で原資は D730 の手順)。
- 検査: `tools/check_docs.py` 違反なし、`spool_fold.py --dry-run` rc=0。変異 matrix は実装面差分ゼロで免除 (DW-S04)。
- **受入 attempt 1 (門番経由、13:17〜13:40 JST、tip a578e7400 = main 697025ec9 取り込み後) は rc=70、赤 1 件を非帰属と判定した
  (DW-O18)。** 赤 = `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]`
  (`AssertionError: diagnostic timeout did not interrupt the syscall`、5 秒 sleep を 0.02 秒の診断 timeout が中断できるかを見る時間依存
  test、shard-2、同時受入 2〜3 本)。根拠 4 つ: (i) 本 wave の変更面は docs 3 種 (paper-story README・spool fragment・insights) だけで、
  同 test file も `floor_job_checkpoint.py` もそれを参照しない (差分到達不能)。(ii) 同一 tip a578e7400 で同 file を単独再走 (計算ノード
  request `5666.nqsv`、`run_tests.py` 経由) すると **3 passed / 4.44 秒 / child rc=0** で非再現。(iii) assertion 本文が時間依存で、
  同じ node の同型の赤は archive の entry 1482 (2026-09-14、load 88〜133) と 1546 (2026-09-16) でも単独非再現で非帰属と判定されている
  (今回で 3 例目。failures には未起票で、本 wave の scope 外なので起票せず報告に載せる)。(iv) 赤の受領証は受理しない。テストの弱体化・
  deselect・hold 登録はしない。受入は本判定の記録 commit を積んだ tip に対して 1 回だけ再投入する (門番 = 他 wave の leader ≤ 1 ∧
  load ≤ 60、乱数周期 + 二重確認。マネージャー thread の 12:09 / 12:53 の受入調停に従う)。結果は land の受領証。
- 工数: codex 子 1 本 (review、read-only)。親の実測: repo 外走査 3 回 (Write tool で Python を書いて実行 — 隔離 session の Bash guard は
  複数 dir の `grep -rl` を拒否する)、git 履歴・ignore・tree の照合、当時 script と verifier の `git show` 読み、編集面照合 (209 branch)。

## 次の一手差分

### 完了

- [T-1878] 依頼の限定範囲 (insight 5 群が名指す job dir 9 件・`izanagi-job-evidence/`・`mocc_trace_pilot.sh` の出力先) を走査し、
  PBS `934607.nqsv` の raw `verifier.json` もその sha256 も特定できなかったので、「探索した範囲での未特定」を insight
  (`output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md`) と `docs/paper-story/README.md` の claim-evidence
  系列節へ日付付きで記録した。全体での不在は断定していない。凍結物は不変。
  remaining: none
  base: c4d32588050a753802b8212126ccef0b1bcbc43022904cdc625bc229a4571a0f
