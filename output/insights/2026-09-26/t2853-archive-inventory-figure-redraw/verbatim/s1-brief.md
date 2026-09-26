# 段 1 brief — [T-2853] (1') 保全口 inventory に R1 入力一式の残り + (5') 17 図の描き直し

- 基準: local main 74e6d2f237d3cf6501731fc9fa06a7ce22d4e07e (ff-only 済み、開始 gate fresh rc=0 13:57 JST)
- 研究前進: (1') 今後の論文根拠の実験 (P0・P1・P3・TPC-C) で標準経路が保全した trace を、R1 (保存 trace の再判定) に掛けられる入力一式にする。
  完了判定 = 保全口の inventory 1 件から R1 の CLI argv・CCBench の source (pin + patch)・verifier の版 (repo commit + module sha256) が組めることを試験で確かめる。
  (5') 論文図 17 本が保存データから値の一致で再現できることを確かめる。完了判定 = 17 図 rc=0、provenance の値の差 0 (段 1 の生死確認で既に成立、下記)。
- 確定済みユーザー裁定: 依頼文 (本 wave の引数) — 実装は Codex author (D95)、規律 2 不変、凍結 chain・仮想リスク向け gate・検査・台帳・一般化は scope 外、provenance は粗い粒度 (D320)。
  fig1 の生成器作成と fig15 の repo 外入力の写しは含めない。D2233 項 4 (opt-in、未設定なら追加 I/O・subprocess なし、保全の失敗は原本を残し評価結果・例外を置き換えない、WAL・proof chain・受領証に入れない)。

## (1') 変更面 (実アンカー、74e6d2f2)

| file:line | 現状 | 変更 |
|---|---|---|
| orchestrator/campaign/pipeline.py:2166-2208 `_run_one_repetition` | finally で `_preserve_trace_directory(tdir, …, workload_flags, genome, trace_binary_sha256)` | 反復の outcome (commit witness) と `evidence` (source_root・ccbench_commit・tracked_diff_sha256) を保全へ渡す |
| orchestrator/campaign/pipeline.py:2624-2690 `_preserve_trace_directory` | inventory = status・original_directory・workload_flags・genome・trace_binary_sha256・files | 下の 5 項目を足す |
| orchestrator/campaign/pipeline.py:493-640 `_execute_verification_repetition` | verifier は in-process (`verify_trace_dir_with_capability(trace_dir, expected_commits=commit_count_witness, genome, source_evidence…)`) | 変えない |
| orchestrator/tests/test_t2853_trace_preservation.py | 7 test | 新項目の値の試験を足す |

足す 5 項目 (名前と形は D2160・B-8 runner v5 の `result.json` に揃える、runner 写し `izanagi-repro-archive/t2853-20260923/data/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py` 222-227・610-613 行):
- `verifier_argv`: runner の `verifier_argv` と同じ形 `[python, -B, -m, orchestrator.verifier, <trace dir>, --json, --expected-commits, <N>, --protocol, <P>, --ccbench-root, <source root>]`
- `repo_head`: `git rev-parse HEAD` (orchestrator を含む repo)
- `ccbench_pin`: CCBench の commit
- `patch_sha256`: CCBench source に当たっていた patch の sha256
- `verifier_module_sha256`: `{name: sha256}`、`orchestrator/verifier/*.py` (runner と同じ非再帰 glob)

## 親の provisional 裁定 (攻撃対象)

- (P1) 標準経路の verifier は CLI でなく in-process なので、`verifier_argv` は「同じ trace を CLI で再判定する等価 argv」として記録し、in-process だったことを inventory に 1 field で明記する。<N> は反復の commit witness (`commit_count_witness`)、<P> は genome の protocol、<source root> は evidence.source_root、<trace dir> は元の一時 dir の path。trace が witness まで届かなかった反復は argv を null にする。
- (P2) patch は source root の `git diff --binary HEAD` の bytes を archive 内に zstd で保全し (`archive/` の trace と別名の 1 file)、その sha256 を `patch_sha256` にする。evidence.tracked_diff_sha256 も並べて記録するが、一致を gate にしない (記録だけ)。
- (P3) `ccbench_pin` = evidence.ccbench_commit。`repo_head` の dirty は記録しない (D320、verifier の bytes は module sha256 が束縛)。
- (P4) 取得は保全時 (finally 内) に行い、env 未設定なら git も hash も呼ばない。取得の失敗は既存の保全失敗の経路 (inventory failed、原本を残す、評価結果・例外は不変)。
- (P5) verify fan-out の remote 反復 (兄弟 node) は現状も保全対象外。本 wave は触れない。
- (P6) 保全口の opt-in を job body で有効にする配線は依頼外 (carry の「あわせて入れる」は次の実験 wave へ残す)。

## 不変条件

規律 1・2 (trace の compile 時除去・正しさゲート・anomaly 即 reject) 不変。評価結果・verdict・WAL・受領証・proof chain の bytes 不変。env 未設定なら挙動・I/O・subprocess 不変。

## (5') 生死確認の結果 (段 1 で実施、node 時間 0)

login (pegasus02) で 17 図の再現コマンドを出力 prefix だけ job dir に替えて実行: 17/17 rc=0 (fig2c・fig4 は生成器が repo 内 prefix を要求するので worktree 内一時 dir に描いて移し、木は clean)。
provenance の leaf 差は 17 図で 142 件、すべて時刻・出力 path/sha256・argv・生成器/検査器/依存の sha256・説明文の版更新 (`campaign_verifier_epoch` の scope 文と `verifier_assessment_basis`、fig6 の `study`)・入力 2 件 (fig12 の planner-v4.md = D2233 の改訂、fig2c の依存 plot_backoff.py)。数値・系列・caption・可視文字の差は 0。
(5') は insight に記録するだけで実装面の差分なし。

## 分割

実装子 1 本 (pipeline.py + test)。段 2・3 は省く (軽量版: 設計択一は P1〜P6 で親が決め、正しさ防壁に触れず受理集合も変えない。ただし評価経路の file なので段 6 の敵対レビュー 1 本 (2 レンズ) と変異 matrix を残す)。
受入: `tools/dev_wave_wait.py acceptance --lease-optional` (計算ノード、受入 1 回 ≈ 0.25 node 時間)。変異は単価を 1 job で実測してから。合計は 2 node 時間未満の見込み。
