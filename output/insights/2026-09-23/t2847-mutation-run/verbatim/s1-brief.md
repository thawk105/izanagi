# 段 1 brief — [T-2847] 残り (2) 変異実走のうち pin C 非依存部分 (2026-09-23)

wave: dev-wave-t2847-mutation-run / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run` (branch `worktree-dev-wave-t2847-mutation-run`) / 起点 local main `65fd1422fa1cfa6289c3c194078ff8e604b69857` (開始 gate rc=0) / CCBench `e9e477ca1b55348ab4530de0b1cf663ce4555290`。依頼逐語 = 同 dir `request.md`。

**研究前進:** VLDB 差分分析 P0「検証の意味」の検出表 (設計書 = `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4) を、既存 silo 10 本 (実走済み、`output/insights/2026-09-23/t2847-patch-verify/README.md`) に加えて trigger-misattr と新規変異の実測で埋める。完了判定 = 対象各行に「期待した層で検出 / 別の層で検出 / 盲点として certified / 未発生・誤検出」を計算ノードの実測で書いた insight。

**scope (本体):**
- (A) V08 trigger-misattr: 既存 driver `orchestrator/campaign/s8a_trigger_coverage.py` (`main()` 334 行〜、3 run と checks) を計算ノードで走らせる。骨格 `patches/silo-backoff-trigger-gating-variant.patch`・計装 `instr-silo-backoff-trigger-gating-tally.patch`・`broken-silo-trigger-misattr.patch` は e9e477ca に順に重ねて `git apply` が通った (親実測、misattr は offset 24 行、fuzz なし)。
- (B) 新規変異: 設計書 §4 の新規 18 のうち silo の 14 (V17・V18・V19・V20・V21・V22・V23・V24・V26・V27・V35 と対照 V31・V32・V33) を D16 の out-of-tree patch として `patches/` に置き、既存経路 `s2_verify_calibration._broken_build_and_verify` (295 行、`applied()` + `_require_condition_gate` + `-DCMAKE_CXX_FLAGS=-D<macro>=1` + `_run_once` + `_verifier_run` = commit 証人つき) で build・実走する。
- (C) 実行: 前回の repo 外起動器 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py` (依存物・compiler・出力先の供給、verifier 出力の受動保存) を写して s8a と新規変異の mode を足す (Codex author、repo 外)。投入は `tools/pegasus/dispatch_compute.py --task generic`、条件を割って複数 job を同時投入。

**(P1) 親の provisional 裁定・攻撃対象 — scope 外:** mocc の V25・V34 (X/P の emitter は pin C = mocc 計装の内容で、既存 mocc 4 本と同じく C 依存)。si の V28・V29 (現行 parser が si の v1 trace を拒否し、変異の有無に関わらず E。v2 化 = T-2854 単位 (12) の後に意味を持つ)。既存 mocc 4 本・sort-nonswo (依頼で scope 外)。
**(P2)** 新規 patch は既存の壊し patch と同じく、`CCBENCH_` 外の裸マクロ (`IZANAGI_BREAK_*`、対照も同じ隔離) の `#if`/`#ifdef` 枝に閉じ、未定義で pin と preprocess 一致 (inert)。条件 gate の登録 (`orchestrator/campaign/condition_meaning_gate.py` `_DEFINE_SPECS` 79 行〜 と `_CONDITIONAL_BRANCH_WITNESSES` 273 行〜) と、patch 一覧を固定する test の表 (`orchestrator/tests/test_condition_meaning_gate.py` 36 行・73 行、`orchestrator/tests/test_p3_s4_loop.py` 8400 行付近の許容表、`orchestrator/tests/test_ccbench_spawn_sites.py` の patch 由来 define 表) を同じ変更で足す。これは既存 14 本と同じ登録であって新しい gate ではない。
**(P3)** workload は変異ごとに設計書 §4 の「発生条件」へ届く最小構成を、s2 / s8a の既存 flag (200 tuple・zipf 0.9・rratio・rmw・max_ope・thread 1 / 4・1 s) から選ぶ。期待 (層と verdict) は投入前に表として job dir に固定する (事前登録)。同じ job に stock (patch なし) の対照 run を置く。
**(P4)** V21 は設計書 §4.2 の期待が「証人ありは I、証人なしは S になりうる」なので、同じ trace を証人なしでも verifier に掛ける (verifier・driver の判定は変えない、起動器の追加呼び出し)。
**(P5)** 期待と違う結果が出ても、patch・workload を事後に変えて期待へ寄せない。直すのは「patch が意図した機構を変えていない」ことを source で示せる実装の誤りだけで、その場合も初回の結果を記録に残す。

**不変条件:** 規律 2 (verifier・driver の判定・condition gate の受理条件・patch 適用の厳密さを緩めない、壊し patch を baseline に混ぜない)。規律 1 (trace-enabled build のみ、性能値を取らない)。pin を動かさない (並走 T-2858 が C へ進める wave。本 wave は e9e477ca 固定)。tracked の calibration JSON を上書きしない (出力は job dir)。仮想リスク向けの gate・検査・台帳・一般化を足さない。

**成果物:** `patches/` の新規 patch 14 本 + README 節、登録 4 file、repo 外起動器、insight `output/insights/2026-09-23/t2847-mutation-run/README.md` (検出表・事前登録表・job 表・raw)、worklog / decisions の fragment。

**計算 (D2212 項 4):** 見込み = 新規 14 本を 4〜5 job に分割 (1 job ≈ build 3〜4 本 + run) + s8a 1 job、各 134〜300 s 程度 ≈ 0.4 node 時間、開発の検査 (焦点走・変異 matrix・受入 2 回) を足して 1.5 node 時間未満の見込み。段 4 で内訳を再見積りし、2 node 時間以上ならユーザー確認。

**分割方針:** 段 5 は patch 2 組 (V17〜V21・V35 / V22〜V27・V31〜V33) の並列 author → 登録と起動器の author (patch の macro 名・site 数が確定した後)。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
