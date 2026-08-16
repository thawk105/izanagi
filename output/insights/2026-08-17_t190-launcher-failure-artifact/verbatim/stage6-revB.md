**所見 1: 走 A は超過した gate までは分かるが、遅延の発生箇所と超過時の観測値を特定できない**

- 分類: `判定力`
- 深刻度: Major
- 根拠: [tools/codex_worker_launch.py:574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:574) の snapshot は `{"site", "comparison", "conditions_met"}` だけで、呼出し時に渡されている `elapsed`、`model_calls`、`cli_reported`、limit 値、観測時刻を捨てる。テストも [test_codex_worker_launch.py:3674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3674) でこの 3 field だけを固定している。さらに [tools/codex_worker_launch.py:2593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:2593) から [tools/codex_worker_launch.py:2636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:2636) の間には receipt 再構築、再 audit、slot 予約、output read/hash/publish、再 hash、公開後 audit、receipt staging があるが、途中の時刻はない。
- **失敗シナリオ:** 走 A と同じ 21 件で `post_first_receipt_audit` は閾値未満、`post_receipt_staging` は `max_wall_clock_s` 成立となる。どの処理が 10〜265 ms を費消したか、各 node が何秒で境界を越えたかは残らず、「late path のどこか」以上へ絞れない。
- 提案: snapshot に、既に引数で受け取っている actual、limit、`job_elapsed_s_at` を保存する。これは追加 clock 不要。late path の主要操作にも境界時刻を置く。個別 I/O latency まで取る部分は段 4 の B1 により `scope 外・裁定候補`。

**所見 2: 走 B と走 C の `codex_exit_code=-9` は launcher 起因か否かまでは分かるが、外部 kill の原因は依然未確定になる**

- 分類: `判定力`
- 深刻度: Major
- 根拠: sidecar が持つ終了情報は [tools/codex_worker_launch.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:491) の `termination_initiated_by_launcher` と `termination_signals_sent` だけである。signal は launcher が実際に `killpg` した場合だけ [tools/codex_worker_launch.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1450) で記録される。cgroup、OOM、PBS、scheduler の情報は保存しない。
- **失敗シナリオ:** 走 B または走 C の 1 件で、sidecar が `termination_initiated_by_launcher=false`、signal 空、receipt が `codex_exit_code=-9` となる。launcher 自身の停止ではないことは確定するが、OOM kill、scheduler、外部管理操作、child 自身の signal のどれかは判定できない。
- 提案: cgroup `memory.events`、PBS job 状態、終了直前の資源情報、外部 signal の根拠を run と結合して保存する。段 4 の B4 で明示的に外された面なので `scope 外・裁定候補`。なお launcher 強制停止だった場合は `evidence_forced_stop` と送信 signal により走 B の M2 仮説を判定できる。

**所見 3: bundle だけでは pytest が何を期待し、どの assertion で落ちたかへ到達できない**

- 分類: `到達性`
- 深刻度: Major
- 根拠: hook は [test_codex_worker_launch.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:341) で `call.excinfo.value` を得るが、archive へ渡した例外は Timeout 判定にしか使わない。`metadata.json` の field は [test_codex_worker_launch.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:280) の nodeid、worker、PBS、host、snapshot 状態、diagnostics 有無だけである。sidecar 不在理由も [test_codex_worker_launch.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:291) の `"preflight-failure-external-kill-or-no-launcher-run"` という三択未分離の文字列である。
- **失敗シナリオ:** launcher receipt 自体は意図どおり reject しているが、テストが期待 rc、期待 field、または別の生 assert で落ちる。bundle の receipt と sidecarから launcher attempt は読めても、どの期待との不一致だったか分からず、元の pytest log を別途探す必要がある。sidecar 不在時は preflight failure、外部 kill、launcher 未実行のどれかさえ絞れない。
- 提案: metadata に bounded な例外型、例外 message、pytest call report、期待値と実値、call duration、traceback digestを保存する。sidecar 不在理由は観測根拠別の enum に分ける。

**所見 4: 4096 files / 256 MiB は bundle 単位で、21 件全体の容量上限ではない**

- 分類: `受入発火`
- 深刻度: Major
- 根拠: 上限は [test_codex_worker_launch.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:53) の定数で、`files_seen` と `bytes_copied` は各 `_snapshot_tmp_path` 呼出しで [test_codex_worker_launch.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:116) のゼロから始まる。上限後も [test_codex_worker_launch.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:119) の再帰走査を止めず、全 omitted entry を manifest に積む。
- **失敗シナリオ:** 21 件が同時に上限近くまでコピーすると、最大 5.25 GiB、86,016 files を共有 root へ作れる。途中で容量、inode、walltime を使い切ると、後続 hook は [test_codex_worker_launch.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:328) の `archive_status=failed` だけを report に残し、21 bundle はそろわない。上限後も巨大 tree を走査するため manifest 自体も無制限に膨らむ。
- 提案: PBS run 全体の予約式 byte/file 上限を設け、critical artifact を優先する。上限到達後は再帰を止め、集約 omission record を残す。retention/GC は段 4 で外されているため `scope 外・裁定候補` だが、run 単位上限は本 wave 内で必要。

**所見 5: 失敗 bundle の全 tree コピーは call report 中の同期処理で、F57 の連鎖発火を増やしうる**

- 分類: `性能影響`
- 深刻度: Major
- 根拠: [test_codex_worker_launch.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:337) の `pytest_runtest_makereport` が同期的に `_archive_launcher_failure_without_masking` を呼ぶ。そこから [test_codex_worker_launch.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:274) で全 `tmp_path` を走査し、regular file ごとに [test_codex_worker_launch.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:194) の `shutil.copyfile` で固定 root へコピーする。非同期化、帯域制限、run 全体の排他はない。
- **失敗シナリオ:** 最初の数件が 3 秒境界を越えた直後、複数 worker が `/tmp` から `/work/.../output/runs` へ同時コピーする。まだ launcher call 内にいる他 worker の audit、fsync、artifact 処理と競合し、追加の wall 超過を発生させる。観測対象の 21 件自体を計装が増やす。
- 提案: receipt、sidecar、attempt streams/output、manifestなど原因判定に必要な小さい集合だけを同期退避し、全 `tmp_path` snapshot は suite 後の処理へ分離する。少なくとも run 全体の同時コピー数と総量を制限する。

**所見 6: 緑走行の追加コストが未計測で、3 秒境界と PBS 上限への影響を否定できない**

- 分類: `性能影響`
- 深刻度: Major
- 根拠: autouse fixture は [test_codex_worker_launch.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:350) で全 test に `tmp_path`、UUID、plugin register/unregister を追加する。静的数え上げでは 126 test 関数、parametrize 展開相当 148 cases、うち 25 cases は従来 test signature に `tmp_path` が無い。launcher の監視 loop は各 poll で [tools/codex_worker_launch.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1820) から dict/list を再構築する。さらに緑 launcher でも finally から sidecar writer が必ず呼ばれ、receipt を [tools/codex_worker_launch.py:2749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:2749) で再読・hashし、[tools/codex_worker_launch.py:2802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:2802) で新規 file を書く。
- **失敗シナリオ:** F285 の最小超過は約 9.9 ms である。10 ms poll ごとの allocation、追加 sidecar read/write、148 cases 全体の fixture処理が緑側を押すと、launcher flake または PBS 30 分超過が増える。PBS が suite ごと止めれば call-phase hookが動かず bundleも残らない。
- 提案: 変更前 HEAD と差分版で、対象 module の緑所要、launcher job wall 分布、全受入所要を同条件で比較する。監視 loop snapshot は条件が変化した時だけ更新するか、allocation を固定構造へ寄せる。autouse fixture は `tmp_path` を既に持つ launcher testだけに限定できるか検討する。

## 総括

3 バーストへの判定力は次の状態です。

- 走 A: latch site の絞り込みは可能だが、site actualと late path 内の時刻が無いため、遅延原因の確定には不足。
- 走 B: launcher の evidence forced stopなら確定可能。launcher 外の `-9` は外部 kill以上へ進めない。
- 走 C: `residual=None` の4出所は判定可能。`codex_exit_code` は走 B と同じ外部 kill限界を持つ。

`index.jsonl` は `O_APPEND` と、short-write loop全体を囲む `flock` により、同一 PBS 走の21並列で行が混ざるコード形ではない。一意 leaf も `mkdtemp` で成立している。ただし容量、同期コピー、archive失敗により21 bundleがすべて残る保証はない。

段5報告のうち、receipt schema、受理式、gate比較、公開順を意図的に変えていないという主張は差分と一致した。旧 nodeid は独立検索でも `output/insights` の履歴記録にのみ残り、active code、test設定、実行scriptの consumerは見つからなかった。pytestは実走しておらず、以上は差分と周辺コードによる静的検査である。