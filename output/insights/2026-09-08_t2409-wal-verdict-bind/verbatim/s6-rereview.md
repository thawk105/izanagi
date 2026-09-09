## 所見ごとの対応表

| 対象 | 判定 | 検証結果 |
|---|---|---|
| 段 6 sol must-fix: collector 正例が 3 validator と lock を実際に通ること | **partial** | lock は実検査へ変更されたが、共有 helper は 3 validator を引き続き monkeypatch している。[helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:2997) が作る block record は `record_sha256` 等を欠き、production validator を通る fixture ではない。docstring に制約を書いても段 4 A10 は閉じない。 |
| 段 6 luna must-fix: stale sink pin 4051 | **closed** | `run_campaign` sink は現物の 4061 行。登録簿と expected set も 4061 へ同期され、4051 は残存しない。 |
| 親 F1: `4051 → 4061`、3294 は維持 | **closed** | sink は [4061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:4061)、pin は [885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_ccbench_spawn_sites.py:885) と [2667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_ccbench_spawn_sites.py:2667)。別 sink は現物・pin とも 3294 のまま。親実走 226 passed も通過。 |
| 親 F2: collector 経由の攻撃再現負例 | **closed** | 90 frame、tag 15/75、variant、45 block record、lock bytes を維持し、先頭 frame の `anomalies` だけを `0 → 1` に変更する負例が追加された。期待 error code も `legacy-wal-verdict` に固定。親実走で通過。 |
| 親 F3: lock stub を除き実 lock を通す | **closed** | 新 helper は 3 campaign の実 `campaign.lock` file を書き、`_assert_report_lock_binding` を monkeypatch していない。collector の無条件呼出しを実際に通る。これは lock 部分だけの判定であり、sol must-fix の validator 部分は未達。 |

`regressed` と判定する所見はない。

## fix が作った新しい穴

新しく作られた穴は見つからなかった。ただし、fix 前からの validator stub 問題が残っている。

共有 helper によって拒否側が恒真または過剰決定にはなっていない。

- 正例と拒否例は同じ baseline fixture を使用する。
- 正例は collector が正常復帰し、135 cell と 270 slot を確認する。
- 拒否例はその baseline の deep copy に対して `anomalies` 一値だけを変更する。
- 拒否例は任意の `PreflightError` ではなく `legacy-wal-verdict` を要求する。lock 不正なら `resume-binding` となるため偽陽性にはならない。validator stub 内の失敗も `AssertionError` であり、この期待を満たさない。

実 lock の経路は次のとおり。

1. helper が各 legacy binding を含む canonical JSON を `campaign.lock` に書く。
2. `_collect_report_inputs` が stub validator の正常復帰後、[_assert_report_lock_binding](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:2899) を [3591 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/campaign/b10_backoff_shape_sweep.py:3591)で無条件に呼ぶ。
3. 同関数が `wal.read_lock`、lock decode、`preregistration_binding` の exact 比較を行う。
4. その後に `_verification_source_disclosure` へ進み、変更した `anomalies` で停止する。

したがって lock は素通りしていない。一方、3 validator は [3098 行付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3098)で置換され、production 実装は発火しない。

既存期待値と保護面の静的確認結果:

- 既存期待値の削除・変更は F1 の `4051 → 4061` という 2 箇所だけ。
- 既存 completeness test は fixture に正常な 3 値を追加しただけで、assertion は不変。
- digest literal は write-heavy 45、balanced 45、read-heavy 45、合計 135。
- `meta_digest` golden は `8e5f0b48…` と `27195442…` のまま。
- `_legacy_*_binding()`、3 validator、`_assert_report_lock_binding`、`_collect_report_inputs` は HEAD と AST が一致。
- `_collect_report_inputs` は module 直下の非装飾 `FunctionDef` のまま。
- test の 2463〜2670 行は HEAD と一致。
- `wal.py` は HEAD と byte 一致。
- worktree 差分は production 1 fileと test 2 fileだけで、凍結 block record に差分はない。

## 攻撃再現 test の検証

[拒否側 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind/orchestrator/tests/test_b10_backoff_shape_sweep.py:3142) は T-2409 の最小攻撃を再現している。

- write-heavy WAL は 90 frame のまま。
- tag は legacy 15、performance 75 のまま。
- 全 variant の列と順序は不変。
- 先頭 frame 以外の 89 frame は元と完全一致。
- 先頭 frame も `anomalies=1` を `0` に戻した copy が元 frame と完全一致するため、差分は `anomalies` だけ。
- `certified=True` と `verdict="serializable"` は維持される。三つの対象 field 全部を同時に崩す test ではなく、そのうち一つを崩す最小例である。
- write-heavy の block record は 45 件で deep equality を確認。
- lock は変更前後の bytes equality を確認。
- collector は validator stub と実 lock 検査を通過した後、production の exact 述語で `legacy-wal-verdict` を送出する。

よって拒否理由は、三つの verdict field の一つを崩したことだけに帰属する。

## GO / NO-GO

**NO-GO。**

F1、F2、F3 と luna の所見は閉じた。fix による新規 regression もない。しかし、契約の正本である段 4 A10 と段 6 sol must-fix が要求した「3 production validator と lock を通過済みの専用 collector fixture」は、validator 3 個が stub のままなので未達である。

親実走の 226 passed、および consumer 拡張の 779 passed / 3 skipped は確認材料だが、置換された production validator 経路を通った証明にはならない。私は pytest を実走していない。

## 総括

fix は sink pin、攻撃再現負例、実 lock 経路を正しく閉じ、新しい穴も作っていない。唯一の阻害事項は、collector fixture が production の 3 validator を通らないままという既存 must-fix の残存である。したがって最終判定は **NO-GO**。