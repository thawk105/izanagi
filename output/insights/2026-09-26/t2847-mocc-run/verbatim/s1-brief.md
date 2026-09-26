# 段 1 brief — [T-2847] 残り (2) mocc 既存 4 本 + 新規 V25・V34 を pin C で実走 (2026-09-26)

wave: dev-wave-t2847-mocc-run / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run` (branch `worktree-dev-wave-t2847-mocc-run`) / 起点 local main `42d1488685df4850b2be9275cb7b32fcfc5f249f` (開始 gate fresh rc=0、13:4x JST) / CCBench gitlink = pin C `68106660686232781bca3be792a750d3e19d7a8a`。依頼逐語 = 同 dir `request.md`。

**研究前進:** VLDB 差分分析 P0「検証の意味」の検出表 (設計書 `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4) のうち、mocc の 6 行 (既存 V13 lockskip・V14 permutation-erase・V15 early-unlock・V16 hot-update-unlock、新規 V25・V34) を現 pin C の実測で埋める。完了判定 = 6 行それぞれに「期待した層で検出 / 別の層で検出 / 盲点として certified / 未発生 / 誤検出」を計算ノードの実測で書いた insight (`output/insights/2026-09-26/t2847-mocc-run/README.md`)。

**親の実測 (brief 前):**
- pin C の `cc/mocc/transaction.cc` (1358 行) に対し `git apply --check`: 壊し 4 本 (`patches/broken-mocc-{lockskip-validation,early-unlock,permutation-erase,hot-update-unlock}.patch`) は計装 patch なしで rc=0。`patches/instr-mocc-lock-coverage.patch` と `-pin-candidate` は rc=1 (C が計装を含むため)。
- 既存 driver `orchestrator/campaign/s3_mocc_mutation_proof.py` は `PIN = legacy.PIN = e9e477ca` (s3_mocc_lock_coverage.py:42) を checkout し `INSTRUMENTATION_PATCH` を先に当てる (main() 内) ので、pin C ではそのまま走らない。matrix = 6 build-label × 3 regime (hot 0 / cold 21 / default 10) × thread {1,4} = 36 run、workload W = 200 tuple・zipf 0.9・rratio 0・rmw true・max_ope 5・1 s、U = W の rmw false・max_ope 1、CLK 2100、STOCK_G = mocc {BACK_OFF 1, KEY_SORT 0, TEMPERATURE_RESET_OPT 1}。verify は証人なし `python -m verifier --protocol mocc`、run timeout 120 s の run は verify しない。
- T-2858 の記録 (`output/insights/2026-09-23/t2858-mocc-xp-pin-revalidation/README.md`) では C 上の stock mocc 2 走が certified (X/P の emitter が evidence-present)。
- V34 の温度述語 4 site は pin C で 297・460・567・971 行 (設計書の M:296/459/566/970 から +1)。V25 の対象 (正準順への復元 = `vioctr != 0` の解放と CLL_ 除去) は pin C で 835〜859 行、続く 862〜879 行が正準順の無条件 lock。
- **既存被覆 (純増の確認):** `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json` (ccbench_commit = C、`s3_mocc_lock_coverage.py` の pin 候補経路、all_pass) に C 相当の 6 走 (既定 temp_threshold のみ): stock 1/4 thread は certified、lockskip 1 thread は X だけで indeterminate・4 thread は巡回 3,525 で non-serializable、perm-erase 1 thread は P だけ、early-unlock 1 thread は X だけ。本 wave の純増 = hot/cold regime、perm・early-unlock の 4 thread、hot-update-unlock の全 cell、V25・V34。この 6 走は insight で先行記録として並記し、再利用はしない (同 job の stock 対照と揃えるため 36 run を取り直す)。decisions / failures に V25・V34 の既存記録なし (grep 0 件)。
- 並走 [T-2849] (MOCC の差し込み) の branch `t2849-unit-a` / `worktree-t2849-mocc-insertion` が `orchestrator/tests/test_ccbench_spawn_sites.py` を変更中。本 wave の登録と同じ file になりうる (取り込み時に照合、DW-O23)。

**scope (本体):**
- (A) 既存 4 本: pin C の上に直接当て (計装 patch なし)、既存 driver と同じ 36 run matrix (stock W/U を含む) を計算ノードで実走。driver の tracked コード・PIN 定数・旧 JSON は変えない。repo 外の起動器が driver の関数 (`_build_variant`・`_variant_run`・`_verify`・`_summary`・`compute_checks` の述語) を import して pin C を checkout し、計装 patch を当てない経路で組む (Codex author、job dir)。
- (B) 新規 V25・V34: D16 第 3 類の out-of-tree patch (`CCBENCH_` 外の裸マクロ 1 個の `#if` 枝、未定義で pin C と一致、発火診断つき) を Codex author が書き、条件 gate の許可ドメインへ登録 (先例 58fd15b58 と同じ 4 file の表)。同じ起動器で build・実走。
- (C) 投入: `tools/pegasus/dispatch_compute.py --task generic`、job ごとに別の計測用 checkout (wave tip の detached worktree + submodule 初期化 + lock)、条件を割って同時投入。

**(P1) 親の provisional 裁定・攻撃対象:** 既存 4 本の patch は変えない (発火診断を足さない)。S になった行は、事前登録で「発火の証拠が無い S」= D2239 項 3 の規則どおり「未発生」側に数え、機構への到達は source の条件 (H の cold/default は hot 分岐に届かない) で注記する。
**(P2)** V25 は停止 (相互待ち) しうる。run timeout (120 s) で止まった run は「停止」と記録し、verdict は付けない (設計書: 停止自体に verdict は無い)。起動器は停止した run の部分 trace も追加で verifier に掛けて記録する (driver の判定は変えない、起動器の追加呼び出し)。V25 の発火診断 = reached (vioctr≠0 で復元を飛ばした回数)・changed (飛ばした lock 数 ≥ 1)・committed。停止で終了時 destructor が走らない場合に備え、診断の出し方は plan で決める。
**(P3)** V25・V34 の cell: V34 (正しさを保つ対照) は W の 6 cell (3 regime × {1,4})。V25 は W の hot t4 を主、hot t1 (相互待ちが起きない対照側) と cold/default t4 を副に置く。期待は投入前に表で固定する。
**(P4)** job 分割 = 各 job に stock build 1 + 変異 build 1〜2。stock run は job 内で使う workload×regime×thread ごとに 1。期待と違う結果が出ても patch・workload を事後に変えない (D2239 項 4)。
**(P5)** verify は既存 mocc driver と同じ証人なし verifier (commit 証人つきの silo 経路に揃えない)。判定基準は変えない。

**不変条件:** 規律 2 (verifier・driver・condition gate の受理条件・patch 適用の厳密さを緩めない、壊し patch を baseline に混ぜない)。規律 1 (TRACE=1 build のみ、性能値を取らない)。pin を動かさない。tracked の calibration JSON を上書きしない (出力は job dir)。仮想リスク向けの gate・検査・台帳・一般化を足さない。

**成果物:** `patches/` の新規 patch 2 本 + README 節、登録 file (条件 gate と表の test)、repo 外起動器、insight (検出表・事前登録表・job 表・raw)、worklog / decisions の fragment。

**計算 (D2212 項 4):** 見込み = 実走 4 job × 200〜300 s (V25 の停止 run は 1 本 120 s 上乗せ、最悪 +600 s) ≈ 0.25〜0.45 node 時間、焦点走 2 回 ≈ 0.1、変異 matrix ≈ 0.4、受入 2 回 ≈ 0.5。合計 ≈ 1.2〜1.5 node 時間 < 2 の見込み。段 4 で再見積りし、2 以上なら投入前にユーザー確認。

**分割方針:** 段 5 = U-A (patch V25・V34) と U-D (起動器、job dir 側) を並列、U-C (登録 + test 表) は U-A の macro 名確定後。patches/README.md の節は親。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
