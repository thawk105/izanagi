---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-verifier-cli-timing-probe
seq: 1
title: verifier CLI 単独計時 probe — read-heavy (rr95・3 秒・48 thread・1M records) の trace 有効 bench 1 反復を計算ノード 1 本で走らせ、生成 trace (17.13M commit・204M 行・6.52 GB) に対する `python3 -m orchestrator.verifier` の別 process 実行 421.7 秒を trace 生成 3.3 秒・C 行数え直し 16.9 秒と分けて 1 回観測した (docs のみ、probe は job dir、branch worktree-dev-wave-verifier-cli-timing-probe、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「verifier 単体の計時 probe (台帳 ID 未起票、entry 1654 [T-2229] の scope 外項)。計算ノード 1 本で trace 有効 build の
  read-heavy (rr95・3 秒・48 thread 相当、T-2229 の反復と同条件) を 1 反復走らせ、生成 trace に対して `python3 -m orchestrator.verifier` を
  別 process で単独計時する。trace 生成時間と CLI 実行時間を分け、条件・code と build の識別・入力 trace の識別と規模・検証結果・計時範囲を
  記録し、trace と結果は job dir へ保存する (repo へは insight の要約と原文 path のみ)。これは 1 条件・1 回の観測であり、既往の 23 分の
  内訳・代表所要時間・CC 性能を確定しない (D2144 の試算を置き換えない、規律 7)。一次資料 `output/insights/2026-09-18/t2229-verify-cost-decomposition/README.md`
  §3。実装差分ゼロの probe として返し、probe script は repo に入れない。着手直前の local main から fresh worktree。規律 2 を緩めない。本題の
  計時だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (1 条件・1 反復・1 node の観測を記録した)。** 一次資料は `output/insights/2026-09-18/verifier-cli-timing-probe/README.md`。
  decisions fragment 0 (新しい設計判断なし。D2144 は置き換えない)、failures fragment 0。
- 本走 (job `5868.nqsv`、bnode041、2026-09-18 15:32〜15:40 JST): campaign `ed8a676b` の反復と同じ動作点 (silo、pin `511c953`、
  `TRACE=1 BACK_OFF=0 NO_WAIT_LOCKING_IN_VALIDATION=1 NO_WAIT_OF_TICTOC=0 WAL=0`、1M records・48 thread・extime 3・rr95・zipf 0.9・
  max_ope 10・clocks_per_us 2100、numactl なし) で、trace 有効 bench process は **wall 3.344 秒** (rc 0、commit witness 17,128,612、
  abort 3,066,603)、pipeline と同じ C 行数え直し **16.858 秒**、生成 trace (48 file、204,048,743 行、6,520,332,111 bytes) に対する
  `python3.10 -B -m orchestrator.verifier <dir> --json --expected-commits 17128612 --protocol silo --ccbench-root <checkout>` は別 process で
  **wall 421.707 秒** (rc 0 `serializable` / `certified`、17,128,612 txn、296,980,787 edge、anomaly 0、integrity clean、user 1812.2 秒 /
  sys 89.0 秒、`wait4` の ru_maxrss 43.95 GiB、parse の既定 worker 16)。3 区間の和 441.909 秒の内訳は bench 0.76% / 数え直し 3.81% /
  verifier 95.43% (この 1 回の観測の内訳)。trace の複製 (node local → Lustre) 3.979 秒。計時範囲は Popen 直前〜`os.wait4` 復帰 (段 4 裁定で
  結果を見る前に固定)。smoke (10k records・extime 1、同 job) は code path の実走確認のみ (verifier 92.806 秒 certified)。
- D2144 (t2229 README §4) が契約から置いた「bench process ≤ 約 120 秒 (条件付き)」に対し、この観測の bench は 3.344 秒で trace 無し版の
  別走 3.35〜3.42 秒と同程度。上限の書き換えではなく、異なる時点・code (現行 verifier は 2026-09-02 の並列化後)・node・計時範囲の
  数値の併記に留めた (規律 7)。
- 軽量版: 段 2・3 省略。段 5 = Codex `role=author` 1 本 (probe 544 行、sha256 `03a1efbc…52f8`、job dir に保全し repo へは `.md` 逐語のみ)。
  親が login で `selftest` 25/25 PASS、計算ノード job 1 本 (generic dispatch、smoke → 本走を親の運転 script で直列、Elapse 628 秒)。
- 段 6 レビュー 2 本 (read-only codex、`gpt-6-astra` / medium): A (過剰・削除・測定妥当性) は **NO-GO → fix 後**、must-fix 1 = 親の
  (P1) 根拠「`BACK_OFF=0` では backoff.hh はコンパイル対象外・patch の差は cache 変数のみ」が誤り (`transaction.hh` L9 が無条件 include、
  当時の patch は `BACKOFF_FIXED` / `BACKOFF_NOINLINE` の定義と backoff.hh の変更をコンパイル入力に足す。主張できるのは backoff 動作の対応まで)、
  should 5 (build 差の列挙、CLI と pipeline の差、inventory pass と page cache、`ru_maxrss` の意味、31.4% / 1/36 の併記削除)、nit 1。
  B (整合・数値検算) は **GO**、must-fix 0、§4.1・§4.2・識別・時刻・smoke の全行が原本と一致、派生値も独立再計算で一致 (CPU 合計だけ
  丸め順序で 0.001 秒差)、should 4・nit 3。修正提案は採用、A3・B8〜B10 は疑義棄却 = refuted、他は real
  (観測値の訂正・再測定を要する所見は 0)。焦点再レビューは GO、closed 15 / partial 0 / regressed 0。
  nit 3 件も README に反映済み。closed 表は insight `verbatim/s6-focus.md`。
- 中断作業を回収した。回収着手時 local main `b2037abfa1467507cf92c851c83f262239f81641` から専用 Codex worktree
  `worktree-dev-wave-verifier-cli-timing-recovery` を作り、旧 worktree の staged 6 file を監査して移した。
  job `5868.nqsv` と子の完了、対象 producer/worker の非稼働を確認し、再測定は投入していない。
  author tip `e47ef81bab7e0a8ed3830d61ae18d88c5a8b0bfd` の probe は job dir 原本と照合し、実装として main へ取り込まない。
  元の staged patch と branch bundle は同 job dir の `recovery-original-staged.patch` / `recovery-original-branches.bundle` に保全。
  回収進捗・受入・land・清掃の実測結果は同 job dir `RECOVERY-HANDOFF.md` と受領証に記録する。
  phase の実装完了項に対応しないためチェックを新設しない。dev-wave 改善候補は専用 handoff に記録し、改善実装や次 wave は行わない。
- 回収後の受入attempt1 (tested tip `97fc3aaba`、main `b2037abfa`) は 25,115 passed / 69 skipped / 18 setup error。
  junit本文で確認すると、S8c snapshot準備4件は `git archive` の10秒timeout、t1259準備14件は `git status` と
  `git ls-files --others` の30秒timeoutが各7件で、assertion failureは0。今回の6文書は当該production・test・timeout値を
  変更せず、S8cのarchive対象にも含まれない。DW-O18に従い同tipでt1259全fileとS8c該当4nodeを1回だけ再走し、
  job `6399.nqsv` は **55 passed (106.82秒、Elapse 113秒)** で非再現。テストの除外・期待値変更・timeout緩和はしない。
  初回赤を緑に読み替えず、受入を再走する。原ログと最終受領証は同job dirの `recovery-acceptance-*`、
  切り分けは `recovery-focused-1.log`。計測probeの再投入は0回。
- 受入attempt2はshard1の900秒queue待ちtimeoutによりdispatch infrastructure rc=16で中断し、緑受領証は出ていない。
  兄弟停止時の6416.nqsvはPre-runningでqdel見送りとなったため、runbook §7.6に従い終端まで木とholdを保全した。
  6414/6415/6416の不在、6416の最終child rc=0、source cleanとHEAD不変を確認後、holdをjob dirへ保全して解除。
  この部分結果を受入へ合成しない。次の受入は既存 `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` により
  queue待ち予算だけを延ばし、テストtimeout・期待値・合否条件は維持する。新規gate・機構の追加はない。

## 次の一手差分
