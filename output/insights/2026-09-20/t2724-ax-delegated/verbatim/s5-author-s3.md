## 変更差分

指定 5 file を更新しました。B-10 の 3 literal、実 repo 6 node の exact 拒否集合、tmp repo テスト 2 本、memo docstring が対象です。commit・add・push はしていません。

`git diff --stat`:

```text
 orchestrator/tests/real_repo_ratified_memo.py      |  8 +--
 orchestrator/tests/test_backoff_extended_sweep.py  |  4 +-
 orchestrator/tests/test_s8b_binding_driftguards.py | 64 +++++++++++++------
 orchestrator/tests/test_s8b_oracle_driver.py       | 74 ++++++++++++++++++----
 tools/pegasus/b10_backoff_grid.sh                  |  2 +-
 5 files changed, 111 insertions(+), 41 deletions(-)
```

`git status --porcelain --untracked-files=all`:

```text
 M orchestrator/tests/real_repo_ratified_memo.py
 M orchestrator/tests/test_backoff_extended_sweep.py
 M orchestrator/tests/test_s8b_binding_driftguards.py
 M orchestrator/tests/test_s8b_oracle_driver.py
 M tools/pegasus/b10_backoff_grid.sh
?? _t2724_probe_refusals.py
```

## B-10 digest の再計算 (2 経路)

test の算法と job script から抽出した埋め込み Python の両方で一致しました。

```text
22 files
92099c87e93536ebecf28e85ebf60222716e0b20c179c94e50dc2fb15ef2f8bb
```

A/X 2 file を除いた対照計算も、旧 20 file・`6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415` に一致しました。

対象 2 file に対する `grep -n 6a4ee1ef` は 0 件（rc=1）。新値は test の 1671・2025 行、script の 22 行の計 3 件です。差分は literal だけで、算法・比較・対象 directory・`fail 2`・`completion.json` は不変です。

## 実 repo 真値の再導出 (probe の実測)

`python3 -B _t2724_probe_refusals.py` は rc=0。

- loader は `RatifiedFreeze` を返し、sha256 は `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`。
- launch validation は `journal-state-invalid`、message は `journal[1] event/status が未知: 'reservation-preflight'`。
- receipt の layer-2 hit と launch refusal の 2 行が、親の `after-g1-refusals.txt` と全文・順序とも一致。

`_ACTIVATED_G1_REFUSALS` の文字列も AST で親の 2 行と exact 照合しました。probe は untracked のまま残しています。

## 静的列挙 (所有外 caller・共有 fixture・consumer test への波及)

- 既存 node 名、各 node の `root=ROOT`、receipt／ratified memo 消費集合は変更前と一致。payer は ratified memo 非使用のままです。
- 共有 helper の AST と memo の実行ロジックは不変。
- serialization pin、growth hold、production module、hook は未変更。
- 新テストは `_t080_repo(receipt="never-issued")` を使用し、`root=root`、memo 非使用。no-active＋manifest schema 拒否を exact 集合で検査し、prepare/evaluate 未呼出と出力・budget・marker 未作成を要求します。

追加 node:

```text
test_active_resolution_error_and_manifest_structure_are_aggregated_in_tmp_repo
test_run_block_broken_binding_manifest_aggregates_refusals_in_tmp_repo
```

## 未実走・限界

Python 4 file の `py_compile` と `git diff --check` は rc=0。**テストは実装済み・未実走**です。

held 6 node、新規 2 node、B-10 の 3 test file、p1/p2 変異・負例の実走は親の dispatch に引き継ぎます。独立レビューも未実施です。

## 総括

S3-a〜d を実装しました。digest と実 repo 拒否集合は再導出済みです。批准 loader は成功しますが、既存の journal 不整合により launch validation は拒否され、P3 全 gate 受理は未達です。