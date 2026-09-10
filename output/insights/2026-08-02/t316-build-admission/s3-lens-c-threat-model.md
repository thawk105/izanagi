# 敵対レビュー — レンズ C

**判定: NO-GO。** 指定資料とプランの参照箇所はすべて読めた。以下は read-only の静的検査であり、書き込み、pytest、ビルド、実バイナリ実行は行っていない。テストの緑は主張しない。

## 1. Critical — sandbox の外へ出た artifact が confused deputy になる

- **claim:** プランの sandbox は subprocess を囲うだけで、候補が writable trace/build dir に残す artifact を親 process が安全に取り込む境界を持たない。「credentialless」「timeout」「host filesystem 保護」は成立しない。
- **evidence:** プランは candidate の build/scratch/trace dir を writable としつつ、host credential 読取・resource 消費を閉じると主張する（[s2-plan.md:239](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:239)、[s2-plan.md:249](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:249)）。しかし親は child 終了後に `trace_*.log` を通常の `open()` で追い（[pipeline.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:226)、[parse.py:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/verifier/parse.py:205)）、不正行を raw の `line!r` ごと例外へ載せる（[parse.py:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/verifier/parse.py:174)、[pipeline.py:675](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:675)）。候補は symlink を作るだけで、隔離外の親に `/proc/self/environ` 等を読ませ、内容を WAL の parse error へ流せる。`/dev/zero` や FIFO なら child timeout 後に親を停止できる。build v2 も `isfile()` 後に通常の `open()` で hash するため symlink を拒否しない（[buildcache.py:534](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:534)、[buildcache.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:78)）。
- **impact:** host credential の秘密性、親 process の可用性、trace・binary hash・WAL・proof chain の参照値が sandbox 外で候補 artifact に再汚染される。
- **suggested_fix:** output を in-place で読まず、directory fd 相対の `openat2`/`O_NOFOLLOW|O_NONBLOCK`、`fstat` による regular-file・size・count・device 検査後、trusted dir へ byte copy してから解析する。binary も同じ fd/immutable copy を hash・実行し、trace parser 自体を第二 sandbox に置く。

## 2. Critical — 「非信頼」の一語に異なる敵を押し込んでいる

- **claim:** brief とプランには攻撃者、目的、能力の定義がないため、(c) の必要性も十分性も裁定できない。
- **evidence:** brief は coder 出力を非信頼と置くだけで（[brief.md:4](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:4)）、プランは直ちに (c) を最終形とし、二層の故障を「概ね独立」とする（[s2-plan.md:3](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:3)、[s2-plan.md:299](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:299)）。だが悪意ある provider は既に workload、metrics、diff を受信し、全 role 出力を支配する（[decisions.md:5948](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/decisions.md:5948)）。DSL はその provider に送った情報を守らず、合法 IR 内の探索妨害や reward hack も止めない。一方、偶発的な危険コードだけが敵なら固定 renderer と build 停止で大半を閉じられる。
- **impact:** 「host-safe」「正しい候補」「信頼できる選択」「情報非漏洩」が混同され、受理集合と材料レポートが何を保証するのか決まらない。
- **suggested_fix:** 少なくとも「善良だが誤る LLM」「共通入力で prompt-injected な LLM」「適応的な悪意ある role 出力」「悪意ある provider」を分け、各々について host confidentiality、measurement integrity、availability、proof provenance のどれを守るか宣言する。悪意ある provider を対象外にするなら明記する。

## 3. High — P1 は現在の穴を封じず、プランの対案は最小でもない

- **claim:** test-only は T-277 まで安全に先送りする措置ではない。現行 gate は Pegasus を止めるだけで、`OTHER` では既に role-derived build を許す。一方、直ちに三軸 DSL 全実装まで要求する必要もない。
- **evidence:** 親 P1 は gate を実装しない（[brief.md:34](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:34)）が、実装上 `_site_admits_measurement()` は `OTHER` を受理する（[p3_s4_loop_trigger_gating.py:278](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:278）。brief 自身もコード片 loop の既実走 artifact を認める（[brief.md:30](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:30)）。プランは最後に、より小さい fail-closed switch が代替になると自ら認めている（[s2-plan.md:369](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:369)）。
- **impact:** P1 のままでは非 Pegasus 上の受理集合が任意 C++ のまま残り、逆にプラン案を丸ごと採ると安全停止だけで閉じられる wave を不必要に拡大する。
- **suggested_fix:** 最初の実装を「全 site・全 driver 共通の role-derived build 既定拒否」に縮める。test-only で終えるなら T-316 を未完、T-277 を閉じたままにし、「危険 payload が通る」ことを正常系として固定しない。

## 4. High — T-277 の blocker 認定が粗すぎる

- **claim:** T-316 は T-277 全体ではなく、「未レビュー role 出力から作った候補を build/run/certify するモード」の blocker である。
- **evidence:** D122 は T-277 を開くと封じ込めが消えるとして一括 blocker 化する（[decisions.md:5944](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/decisions.md:5944)）。しかし危険な遷移は proposal 受理後の `run_campaign` 到達であり（[p3_s4_loop_trigger_gating.py:408](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:408)）、stock や exact reviewed binary の計測とは分離できる。逆にプラン自身、sandbox 後も measurement hack と任意 C++ の certification 問題が別だと認める（[s2-plan.md:258](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:258)）。
- **impact:** blanket blocker は安全な stock/pinned 計測を止める一方、T-316 完了を T-277 全モードの安全証明と誤認させる。
- **suggested_fix:** T-277 admission を `stock/exact-pinned`、`human-promoted`、`bounded-IR unsandboxed`、`bounded-IR + containment receipt` に分割する。前二者は条件付きで先行可能、raw role C++ は拒否、credentialless 運用だけの候補は exploratory 扱いとして certified 集合へ入れない。

## 5. High — coder と外部 TCB の二重基準に根拠がない

- **claim:** Coder だけを適応的敵として扱い、CCBench・patch・CMake・toolchain を trusted residual とする非対称は説明されていない。pin は identity であって安全性ではない。
- **evidence:** 規律6は CCBench source も外部入力に含める（[CLAUDE.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/CLAUDE.md:86)、[CLAUDE.md:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/CLAUDE.md:89)）。現行 harness は commit と tracked-clean を確認するだけ（[patchharness.py:162](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/patchharness.py:162)）、patch は path からそのまま apply する（[patchharness.py:234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/patchharness.py:234)）。プランも source digest は安全性でなく identity と認めながら（[s2-plan.md:72](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:72)）、patch digest 追加だけで非対称を済ませる（[s2-plan.md:301](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:301)）。
- **impact:** proof chain は「この bytes を実行した」としか示せず、基底コードや build logic が値を偽装した場合も certified median_tps の意味を回復できない。
- **suggested_fix:** TCB を明記し、CCBench commit・patch・CMake・toolchain の trust-promotion 根拠を記録する。合理的な非対称は「coder は高頻度・未レビュー・適応的、基底は一度人間レビューして immutable pin」とすることであり、その証拠が無ければ claim を coder-origin containment に限定する。

## 6. High — 正本 docstring が存在しない防壁を数えている

- **claim:** `DiffQuarantine` の正本説明は、source digest と auditor が「意味的逸脱の完全性」を担うとしており、今回の前提実測とプラン自身に反する。プランの最小変更一覧はこの虚偽参照を直さない。
- **evidence:** docstring は semantic completeness を preprocess hash、auditor、規律6へ委譲する（[diff_quarantine.py:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/diff_quarantine.py:17)）。しかし digest は source identity を決めるだけで（[source_digest.py:650](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/source_digest.py:650)）、auditor gate は digest の一致しか証明しない（[auditor_gate.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/auditor_gate.py:64)）。プランもこの二点を認めるが、最小実装集合に docstring 修正がない（[s2-plan.md:347](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:347)）。
- **impact:** 実装後も設計参照と review accounting が identity gate・LLM self-report を semantic 防壁として二重計上し、proof chain の保証説明が誤る。
- **suggested_fix:** 同じ wave で docstring を「structural containment のみ」「source digest は identity のみ」「auditor は advisory」「semantic admission の正本は新 gate」と改める。

## 7. Medium — P3 は「security boundary でない」を「価値ゼロ」と取り違えている

- **claim:** 同一 transport は auditor の独立性を否定する根拠ではない。悪意ある provider に対する形式防壁には数えられないが、偶発的誤りに対する別文脈の検出器としては価値がある。
- **evidence:** 親とプランは同一 transport を理由に解から除外する（[brief.md:41](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:41)、[s2-plan.md:342](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:342)）。実際の provider は role ごとの fresh tool-less context を作り（[claude_projected_provider.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/claude_projected_provider.py:91)）、session persistence を止め、session-id 再利用も拒否する（[claude_projected_provider.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/claude_projected_provider.py:221)、[claude_projected_provider.py:295](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/claude_projected_provider.py:295)）。coder と auditor も別 invocation である（[p3_autonomous_workload_trial.py:1216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1216)、[p3_autonomous_workload_trial.py:1269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1269)）。
- **impact:** auditor を価値ゼロ扱いすると formal acceptance set は変わらないが、mutation の検出率、uncertainty、proposed-tests、監査証拠が失われる。
- **suggested_fix:** deterministic gate だけを admission boundary とし、auditor は security credit 0 の advisory/detective control として残す。偶発脅威に対する価値は mutation catch-rate で測り、強い独立性が必要なら model/provider diversity を別裁定にする。

## 8. Medium — (c) は最終裁定ではなく、未検証の条件付き仮説である

- **claim:** sandbox backend の成立性が未確認なのに、プランは (c) を最終形として裁定済みにしている。さらに typed IR が守るのはコード能力と軸帰属であり、scientific correctness 全体ではない。
- **evidence:** `perf`、NUMA、hardware counter と rootless sandbox の両立は未確定（[s2-plan.md:247](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:247)）で、プランの総括も最大の未解決点としている（[s2-plan.md:389](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:389)）。backend 不在時は全 build を停止する設計なので（[s2-plan.md:244](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:244)）、成立しなければ受理集合は空になる。また合法 IR 内の fairness/reward hack は残り（[s2-plan.md:303](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:303)）、現 verifier に fairness 観測がないことも既決である（[decisions.md:1263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/decisions.md:1263)）。
- **impact:** backend 非対応なら T-277 は永久停止し、対応しても median_tps・certified 選択は合法な starvation/measurement hack を含み得る。
- **suggested_fix:** (c) は target architecture とだけ裁定し、(b) は compute-node capability と artifact-import 境界が実証されるまで未採用とする。T-316 の closure 文言も「role-code capability admission」に限定し、fairness・measurement validity を別 gate/task として残す。

## 総括

**脅威モデル:** 現実的な最低線は「適応的で悪意を持ち得る role 出力」だが、悪意ある provider まで守る設計ではない。守る資産を host confidentiality、可用性、measurement integrity、proof provenance に分ける必要がある。

**親裁定の最大の飛躍:** P1 の test-only を T-277 前なら安全と見なした点である。任意 C++ 経路は `OTHER` で既に生きており、逆に T-277 全体を blocker 化する必要もない。

**この wave の最小集合:** 全 site・全 driver の role-derived build を既定拒否する switch、backoff/trigger の schema互換 fixed renderer、sort の build停止、reject/safe-control integration test、虚偽 docstring 修正まで。sandbox は artifact-import 防壁と計算ノード capability が静的計画でなく実証されるまで次段へ送る。