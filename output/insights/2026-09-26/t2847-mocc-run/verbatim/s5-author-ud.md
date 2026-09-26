起動器を [launch_mocc_run.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ud/.t2847-launcher/launch_mocc_run.py) に作成しました。tracked file は編集していません。

```bash
/usr/bin/python3.10 launch_mocc_run.py --job J1 --third-party-cache <絶対パス> --out-dir <絶対パス> --repo-root <計測用checkoutの絶対パス>
```

`--job` は J1〜J4、`--dry-run` で build・run なしの計画表示です。指定 unit worktree を `--repo-root` にして実走した dry-run の出力を、cell 一覧にまとめると次のとおりです。`t1/t4` は thread 数です。

| Job | Build と cell |
|---|---|
| J1 | S・L・P：各 `W-hot-t1,t4 / W-cold-t1,t4 / W-default-t1,t4` |
| J2 | S：上記 W 6 ＋ `U-hot-t1,t4 / U-cold-t1,t4 / U-default-t1,t4`。E：W 6。H：U 6 |
| J3 | S・R：各 `W-hot-t4 / W-hot-t1 / W-cold-t4 / W-default-t4` |
| J4 | S・T：各 J1 の W 6 |

全 job の source OID は `68106660686232781bca3be792a750d3e19d7a8a` です。`python3 -m py_compile`、`--help`、J1〜J4 の `--dry-run` は成功しました。build・run は未実走です。

driver から使う名前は、[mutation proof](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ud/orchestrator/campaign/s3_mocc_mutation_proof.py:35) の patch・macro 定数、`REGIMES`、`RUN_TIMEOUT_S`、`CLK`、`OTHER_INTEGRITY_KEYS`、`_cell_flags`、`_build_variant`、`_verify`、`_summary`、`_trace_counts`、`checkout`、`assert_pinned_clean`、`_assert_single_tenant` と、[lock coverage](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ud/orchestrator/campaign/s3_mocc_lock_coverage.py:120) の `_load_policy`、`_resolve_toolchain`、`_prepare_dependencies`、`_apply_owned_patch` です。

前回起動器の compiler・依存物供給は、今回 policy に束縛された既存関数へ置き換えました。subprocess の受動記録と `T2847_FIRED` 抽出は引き継ぎ、[局所 `run_one`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ud/.t2847-launcher/launch_mocc_run.py:121) で stdout・stderr を全文保存します。driver の `_run_trace` と argv の順序、trace tempdir を cwd とする点、`IZANAGI_TRACE_DIR`、120 秒 timeout、非ゼロ rc・timeout では verify しない規則は同じです。局所版は timeout を `timed_out: true` として記録します。完走時の判定は既存 `_verify` をそのまま呼び、record 全体を保存します。`compute_checks` と `all_pass` は呼びません。

所有外 caller・共有 fixture・consumer test の変更はありません。

## 総括

起動器の実装と dry-run 検査は完了しました。計算ノードでの build・run と実測判定は未実走です。