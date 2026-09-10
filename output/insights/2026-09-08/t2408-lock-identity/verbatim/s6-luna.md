## real 1 — lock 内の epoch と trial を同時に改変すると測定 identity を偽装できる

- **判定: real、高。** 3 lock の `space_version` を `b10-backoff-shape/v3`、`trial` を `b10-backoff-shape-v3-9c59411476018d51` にそろえると受理され、歴史測定が v3 だったという誤った値が JSON と Markdown に発行される。
- [b10_backoff_shape_sweep.py:3186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3186) は candidate の `locked_epoch` から expected trial を生成し、[同:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3190) は stem しか比較しない。3 系列を同時に変えれば系列間比較 [同:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3524) も通る。
- その値は JSON の `measurement_identity.space_version` [同:4005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4005) と Markdown [同:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4076) へそのまま出る。R1 の fixed trial 比較ではなく、lock 値から期待値を作る別物である。
- 既存の変異 test [test_b10_backoff_shape_sweep.py:2620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2620) は trial 単独しか変えず、この paired mutation を検出しない。

最小修正: 裁定に明記済みの歴史値 `b10-backoff-shape/v2` を exact 比較し、trial もその固定値と固定 spec SHA から作る。space と trial を同時に変える負例を1件足す。

## real 2 — report が現在の site/runtime contract に依存したままである

- **判定: real、高。** 3 lock と全 record が正しくても、現在の runtime contract の `clocks_per_us` が歴史 calibration の 2100 から変わる、または measurement-site 判定が通らないと report は発行されない。
- report は [b10_backoff_shape_sweep.py:4341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4341) から `formal_runtime()` を呼び、live site と contract を [同:4322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4322) で解決する。さらに歴史 calibration を current contract と比較して [同:4357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4357) で停止する。
- `_prepare_official_output` は root 解決だけでなく claim directory も作る [同:4284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4284) ため、歴史入力の読取りに不要な書込み可能性にも依存する。
- 到達 test は site、runtime、official output の全部を成功 stub にしている [test_b10_backoff_shape_sweep.py:2813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2813) ので、この停止条件を検出しない。実装報告の「locked inputs だけ」とも食い違う [s5-author.md:31](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-author.md:31)。

最小修正: report では `resolve_campaign_output_root("official")` だけを使い、`formal_runtime()` と current contract 比較を通さない。locked calibration の `env_tag`、`threads` と locked spec の整合、および locked clocks による residual 検査は残す。

## real 3 — build 専用 binary policy が report より前にある

- **判定: real、中。** `B10_BINARY_PATH_POLICY_ENV` が無いだけで、有効な歴史成果物からの report が `binary-path-policy` で発行不能になる。
- `_require_binary_path_policy()` は report 分岐より前の [b10_backoff_shape_sweep.py:4319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4319) にある。一方、エラー自身は「formal build」の条件である [同:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:296)。
- 到達 test は token を事前設定する [test_b10_backoff_shape_sweep.py:2771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2771) ため、この不要な report 前提を隠している。

最小修正: `_require_binary_path_policy()` を report return 後、非 report 経路の先頭へ移す。

## refuted — R3 の patch、CCBench、toolchain 分離

- **判定: refuted。** 指定された patch read、`validate_patch_bytes`、checkout、applied、`validate_applied_tree` はすべて report return 後の [b10_backoff_shape_sweep.py:4379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4379) 以降にある。
- `_assert_single_tenant`、CCBench pin、compiler/toolchain も [同:4391](/work/1/SFCD/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4391) 以降で、report からは到達しない。
- current analyzer の clean tree、HEAD、module blob 検査は [同:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:627) に限定されている。submission receipt の歴史 prereg commit 検査も [同:4335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4335) と [同:744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:744) で実装されている。

## refuted — provenance v3 の残りと report_root

- **判定: refuted。** real 1 の space laundering を除けば、formula、patch、spec、calibration、系列 binding は lock 由来で JSON に入り [b10_backoff_shape_sweep.py:4005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4005)、current analyzer は別欄 [同:4044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4044) である。Markdown の対応値も [同:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4076) と一致する。
- 3 spec の canonical JSON は exact 共通比較される [同:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3524)。`report_root` はその共通 spec SHA の先頭16桁を使う [同:4355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4355)。旧系列ごとの binding SHA は使っていない。

## refuted — consumer、live 経路、spawn pin、並行 wave

- **判定: refuted。** `orchestrator/tests/` 全体を指定5関数名で検索した結果、所有外の直接 consumer は `test_ccbench_spawn_sites.py` の `load_preregistration` subprocess pin だけだった。
- `_expected_block_cells` と `_require_exact_workload_cells` の production caller は全て `PreregistrationSpec` へ追随している。live verify-perf/perf 経路も [b10_backoff_shape_sweep.py:4642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4642) で `prereg.spec` を渡す。
- `assert_resumable_binding` と `bind_build_start_wal` は [同:1988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:1988) と [同:2025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:2025) のままで、非 report caller も維持される。
- spawn pin の新期待値 3644 / 4460 は実際の `buildcache.build_v2` [同:3644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3644) と `run_campaign` [同:4460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4460) に一致する。呼出し箇所数の変更ではない。
- `_verification_source_disclosure` 本体 [同:3709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3709) と collector 内の呼出し・受け [同:3946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3946) は差分上無変更。test の base 2850 行以降にも hunk は無く、最後の base hunk は 2829 行である。

## テストと裁定差

- **R5 は狭い意味では refuted。** 到達 test は禁止対象の live prereg/calibration/patch を fail stub にし、production `_write_reports` の呼出し地点までは到達する。ただし writer 自体を置換する [test_b10_backoff_shape_sweep.py:2874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2874) ため、この test 単独なら production writer を空にしても緑のままで、最終書込み [b10_backoff_shape_sweep.py:4188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4188) は通らない。実 writer は別 test [test_b10_backoff_shape_sweep.py:3148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:3148) が直接通すので、独立した第4の real とは数えない。
- **R6 の production 欠陥は refuted。** fixture は指定 SHA と一致した。ただし helper は bytes を hash 後に UTF-8 decodeし [同:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:55)、一度 `write_text` してから decoder へ渡す [同:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:62)。裁定の「raw bytes のまま」を文字どおりには満たさないが、現物3本は UTF-8 で値は変わらない。
- **R7、N1〜N3 は refuted。** 実装上の欠落は見つからない。R7 の新 orchestration test は receipt decoder を stub しているため、正例の実 decoder 証明としては弱い。
- fixture 3本は現 worktreeでは untracked で、提供された `s5-diff.patch` に含まれていない。worktreeを採る場合は必ず同じ変更単位へ含める必要がある。

pytest は実走していない。結論は指定どおり静的検査による。

## 総括

- **real 所見は3件。** 最も重いのは、space_version と trial の paired mutation により歴史測定を v3 と偽って provenance v3へ発行できること。
- **この差分は現状のまま採ってはいけない。**
- 親が必ず直すべき点は、(1) 歴史 space/trial を v2へ exact pin、(2) report から current site/runtime contract と claim provision を外す、(3) build binary-policy gate を report return 後へ移す、の3点。加えて untracked fixture 3本を変更単位へ収載すること。