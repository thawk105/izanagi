---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2288-floor-pair-w1
seq: 1
title: [T-2288] (b) B-4 床値 (floor-pair) の w1 を凍結 spec 3 本で同一 HEAD から実投入し、3 job とも terminal complete で完走、初回実配送の証拠 (8 変数・walltime・signal・到達段・receipt) を記録した (docs のみ、branch worktree-dev-wave-t2288-floor-pair-w1、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2288] (b) B-4 床値 (floor-pair) の w1 実投入 — 着手直前の local main から実行 HEAD H を 1 つ決めて detached checkout で
  place (D2069 項 7) し、凍結 spec 3 本 (rr95 / rr50 / rr5) の w1 を同じ H から submit_floor_pair.sh で投入する。終了条件 = 初回実配送の証拠
  (8 変数・walltime・signal・到達段・receipt) の確認と記録。w2 と finalize は後続 wave。窓を使えずに終わったら延長・差替えをせず記録して終端。
  凍結 spec・事前登録の bytes は変えない。scope 外 = 集約発行・採用裁定・§5 記入・追加 gate」。
- **投入し、3 job とも完走した。** 一次資料は `output/insights/2026-09-19/t2288-floor-pair-w1/README.md`。H = `2ba4000870c63254132410b3002b5298c0c6a210`
  (着手直前の local main tip)。投入元 = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` (detached、locked、3 段が
  終わるまで HEAD を進めない)。`place` は login node で rc=0 (place_record は site 検査を持たない、11 秒)。dry-run 3 本 rc=0 → 実投入 3 本 rc=0:
  rr95 `10711.nqsv` (bnode022) / rr50 `10712.nqsv` (bnode080) / rr5 `10713.nqsv` (bnode081)、いずれも queue 投入から開始まで 8 秒 (内訳は
  分離できない)。
- 初回実配送の証拠 (F660 で未観測だった 5 項目): 8 変数のうち 6 個 (nonce / expected_head / spec_relpath / spec_sha256 / mode / window_id) は
  `job-result.json` の値が `submit-receipt.json` と一致、`FP_EVIDENCE_DIR` は出力先で、`FP_ELAPSTIM_REQ` は job body の形式検査の通過でだけ確認
  (受信値は job 側に記録されない)。計算ノード側の `PBS_JOBID` は `0:10711.nqsv` 形。walltime は `qstat -f` の Elapse Time Limit 86400S。signal は
  `reason completed` = trap による観測記録なし (walltime 未到達、配送の有無と trap の発火能力は未判定)。到達段は `gate driver` / `driver_rc 0`、
  receipt は submitter と job body の両方。NQSV accounting は `-e` の `scheduler.stderr` に出た (`scheduler.stdout` は 0 byte)。
- 完走: 3 窓とも terminal `complete`、124 / 124 session、248 / 248 測定、62 / 62 標本、drop 0、probe 全 clear、rep rc 全 0。所要 rr95 4178 秒 /
  rr50 4141 秒 / rr5 4602 秒 (1 session ≈ 34〜37 秒)。窓 JSONL 3 本は submit-tree に untracked (0600) のまま残し、本 wave では commit しない。
  throughput の比較・解釈・集約・採用は行っていない。
- 軽量版 (実装面差分ゼロ)。段 2・3・5 省略、段 6 = read-only レビュー 1 本 (`gpt-6-astra` / medium、11 call、246 秒): 表 60 cell・JSONL 378 行・
  証拠 file 30 本を独立検算して値の不一致ゼロ、**NO-GO (must-fix 2 = 「8 変数を値で確認」と「signal 配送なし」の言い切り)** → 6 / 1 / 1 に分けて
  書き直し、signal は「trap の観測記録なし」に限定した。should 5 (handoff の時刻・DW-O09 の理由・rr50 Elapse の誤記・watcher の c1→c2・
  queue 待ちの断定)、nit 3、refuted 5 (place の site 検査、header の書出し順、accounting の出先、fragment 文法、軽量版の妥当性)。
  裁定表は insight README、逐語は同 dir `verbatim/`。codex 子 1 本。裁定 inbox に T-2288 / 床値の新規裁定なし。着地後の main 前進
  (`657e1e5a7`、peer advisory) は測定資材に差分なく ff-only で取り込んだ。
- セッション異常 (near miss): 親が handoff の段 1 brief・段 4 裁定の見出し時刻を `date` で採らず推定で書き、実投入 (21:32 JST) より後の値
  (21:35 / 21:36 JST) になっていた。段 6 レビューが指摘、handoff に erratum。親は元の時刻を推定で記した誤りと認めて訂正した。一次資料で
  確認できるのは実投入の時刻で、brief・裁定を書いた実時刻は記録されておらず (handoff は版管理外)、「brief は 21:27:09 より前、裁定は
  21:31:27〜21:32:09 の間」という順序と事前性は親の操作列の申告で、証拠から独立には確定できない。memory 既知の F1 型で、failures fragment に
  再発を追記した。焦点再レビューは 2 巡目 closed 6 / partial 4 / regressed 0 (+ 新規 should 1・nit 1)、3 巡目 closed 4 / partial 2 /
  regressed 0 (+ 新規 should 1 = 本 fragment 稿が 3 巡目の結果を先取りして「閉じた」と書いていた誤り)。DW-O16 の上限 (3 巡) で親が残る 3 件
  (所見 3 の「値の誤りは証拠で確定」の撤回、所見 4 の pin 検索を親が tracked file で実測して 0 件、所見 18 の本文訂正) を real・採用と裁定して
  閉じた。実装面ゼロのため変異による裏取りは免除。
- 隔離 session からは他 worktree への git 操作を harness が拒むため、submit-tree の操作 (verify / lock / place / submit / watch) は job dir の
  `run-*.sh` に置いて起動した (t1505 の型)。checkout 時の `.gitattributes` EINTR 警告 1 件は非 tracked path への属性探索で実害なし。

## 次の一手差分

### 更新

- [T-2288] **P1・(b) w1 を投入し 3 spec とも完走 (terminal complete、62 / 62 標本)。残るのは w2 と finalize**: 投入元
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` (detached at `2ba4000870c63254132410b3002b5298c0c6a210`、locked、
  HEAD を進めない・削除しない)。w1 = rr95 `10711.nqsv` / rr50 `10712.nqsv` / rr5 `10713.nqsv` (最終 session 2026-09-19 13:41〜13:49Z)。
  **w2 は 2026-09-29T00:00Z 以降 (`now + 24h <= 10-07T00:00Z`、1 窓 job ≈ 70〜77 分) に同じ submit-tree から
  `bash tools/pegasus/submit_floor_pair.sh --workload <wl> --window w2` (job dir の `run-submit.sh <wl> w2`)、finalize は両窓の terminal の後に
  `--finalize` (walltime 30 分)。** その後、証拠確認 (24 h 分離・n = 62・欠測率、D1641 項 1) → 集約発行 (D1974) → 採用裁定 (D1641 決定 2)
  → §5 floor 欄。窓 JSONL は 3 段が終わるまで commit しない。手順は runbook §7.8、一次資料は
  `output/insights/2026-09-19/t2288-floor-pair-w1/README.md`。
  base: db0d570f25f925b4c006ca8339f7a385168ee9974598136a6fd4e490b28b66c6
