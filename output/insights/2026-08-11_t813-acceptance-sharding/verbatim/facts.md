# [T-813] 段 1 実測 facts (すべて 2026-08-11、本 wave が自分で測った値)

repo = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval` (main `1da73f2b` から作成)

## F-1. 受入形状判定の真理値表 (`probe_shape.py`、`_is_acceptance_run` を直接 import)

| argv 形 | 判定 |
|---|---|
| 引数なし (canonical 受入形) | **ACCEPT** (`_is_full_suite`=True, op=`tests-full`) |
| 既定 target path のみ | ACCEPT |
| 既定 target + `--junitxml=…` | ACCEPT |
| 既定 target + `-q` / `-n 48` / `--dist loadgroup` | ACCEPT |
| **file 列挙 (2 file)** | **no** |
| `-k` 式 / `-m` 式 / `--deselect` / nodeid 直指定 | no |
| `-p <plugin>` (pytest-shard 等) / 未知 flag `--shard-id=0` | no |
| `-o` ini 上書き / `--last-failed` | no |
| **`--tx ssh=…` (xdist 多ホスト)** | **no** |
| **`--rsyncdir .`** | **no** |
| 既定 target + `PYTEST_ADDOPTS='-q'` | no |

→ 分割手段は形を問わず全滅。一方 `--junitxml` / `-n` / `--dist` は `_NONSELECT_FLAGS` /
`_NONSELECT_VALUE_OPTIONS` に載っているため ACCEPT のまま = **「選択に影響しないオプションは許す」設計は既に存在する**。
`--tx` / `--rsyncdir` は選択に影響しない (どこで走るかを変えるだけ) が allowlist に無いだけで落ちている。

## F-2. 受入専用の事前検査 4 箇所 (`tools/run_tests.py`)

| 行 | 実体 | False のとき |
|---|---|---|
| 594 | `_preflight_unstaged_deletions` | 0 を返す (未 stage 削除を検査しない) |
| 632 | `_preflight_ruleops` | 0 を返す (RuleOps 台帳を検査しない) |
| 705 | submodule 初期化 | 警告のみで続行、初期化しない |
| 1677 | 受入形警告 + bounded scope marker | 「受入全走として扱うな」の警告を出す |

594/632 は**無音**で抜ける (rc も出力も変わらない)。705/1677 は文言が出る。

## F-3. suite の現況 (collection 実測、`--collect-only`)

- collected = **8725 item** / 163 test file / collection 13.56 秒。
- xdist_group: `(none)` 8656 / **`real-repo` 44** / `dev-waves-runtime` 22 / `s8c-preregistration-candidate` 3。
  D258 が閉じた `real_repo` 表記ゆれは**現存しない** (2026-08-09 junit には 1 件あった)。
- collection 順の file 連続 block = 184 > file 数 163 → collection 順は file 単位で連続していない
  (D258 決定 (3) の `pytest_collection_finish` 再配置による)。

## F-4. 排他 group の跨り (file 単位分割の可否)

`real-repo` は **13 file** に跨る: `test_campaign.py`, `test_hooks.py`, `test_p3_s4_loop.py`,
`test_p3_s4_loop_sort.py`, `test_p3_s4_loop_trigger_gating.py`, `test_real_repo_serialization.py`,
`test_ruleops.py`, `test_s1_known_axes_freeze.py`, `test_s1_measurement_freeze.py`,
`test_s8b_binding_driftguards.py`, `test_s8b_oracle_driver.py`, `test_s8b_protocol_builder.py`,
`test_s8b_repo_scan_invariant.py`。
`dev-waves-runtime` / `s8c-preregistration-candidate` は各 1 file。

`run_tests.py` docstring 逐語: 「既定 scheduler は ``--dist loadgroup`` で、実 repo / 共有
submodule を使うテストを**単一 runner invocation 内で**相互排他にする」。
→ **排他はプロセス内機構であり、シャード間 (別 invocation・別ノード) では成立しない。**

## F-5. 受入全走の現在の wall (他 wave の acceptance ログ 15 本、2026-08-11 09:03〜16:31)

535.64 / 537.96 / 538.44 / 539.88 / 540.59 / 543.27 / 544.95 / 545.35 / 546.85 / 547.91 /
552.85 / 555.67 / 557.54 / 564.44 / 566.42 秒 (8482〜8751 passed, 20 skipped)。
→ **中央値 ~546 秒、range ±3%。** 裁定パッケージ §1 の「548〜1021 秒」は古い測定の混在。

## F-6. 2026-08-09 の junit 解析 ([T-692] の一次資料、当時 7705 case)

直列総和 16534.55 秒 / wall 1407.97 秒 = **11.74 worker 相当 (48 の 24.5%)**。
当時の critical path 下界 = `real-repo` 直列和 1388.80 秒 ≒ wall。単独 680 秒のテストが存在した。
現在は wall 545 秒なので当時の巨大テストは解消済み → **現在の critical path は本 wave で再測定する**。

## F-7. 計算資源とポイント

- `rbudgetcheck`: SFC group REMAIN **5021.17** / ESTIMATE 216.67〜218.00 / INITIAL 6000.00 (2026-08-11 16:4x)。
- 1 dispatch = 1 PBS request (`qsub -q gen_S -l elapstim_req=00:40:00`)、計算ノードでは affinity 全数 = 48 worker。
- 受入 1 本の PBS Elapse は本 wave の probe で実測する (queue 待ちは課金されない)。

## F-8. dispatch receipt の書き先

`<repo>/output/pegasus-dispatch/`。受入全走の隣で dispatch すると output/ 検査が赤になる既知事故
(memory `no-concurrent-dispatch-during-acceptance`)。本 wave は受入前に probe を終える。

## F-9. **分割の実害 (k=4 arm、実走)**

shard 3 (39 file / 2181 item) が **rc=1**: `2165 passed, 5 skipped, 1 failed, 1 error in 16.46s`。

1. **収集エラー** `orchestrator/tests/test_s8b_approved.py:31` →
   `from tests.skiputil import Skip, skip` が `ModuleNotFoundError: No module named 'tests'`。
2. **失敗** `test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check` →
   `ModuleNotFoundError: No module named 'codex_roles'` (gw39)。

いずれも**全走では緑**である。原因は sys.path の副作用が collection 集合に依存すること
(同一シャードに居ないファイルが path を用意していた)。
→ **suite は分割不変ではない。** 分割は「どの nodeid が緑か」を変える。
