# [T-243] exploration namespace 移行 — 変異台帳と erratum

wave: dev-wave [T-243] (branch `worktree-dev-wave-t243-exploration-ns`)
実装 commit `0e056e5` / main 取り込み `966a158`。判断の正本は D123、経緯は worklog。

## 走行

| 走 | spec | 結果 |
|---|---|---|
| run1 | `mutation-spec-run1.json` | KILLED 7 / MISMATCH 3 / SURVIVED 2 (12 変異) |
| run2 (再照準) | `mutation-spec-run2.json` | KILLED 2 / MISMATCH 2 (4 変異) |

生台帳は `mutation-ledger-run1.json` / `mutation-ledger-run2.json`。**初回結果は消していない** (DW-M02)。

## 実効判定 (親の裁定)

**negative 10 件が実効 KILL** — M01 / M02 / M03b / M09 / M10 / M11 / M12b / M13b / M14-B / M15。
いずれも受理集合または fail-closed 挙動が期待方向へ変わって赤くなった。

**positive control 1 件成立** — M16b (`_namespace_marker_violation` を「exploration を含む token は全部拒否」へ
広げる過剰拒否) が hook の許可テスト 3 件を赤にした。過剰拒否が検出できることを実証している。

## erratum (初回結果と登録の誤り)

1. **M12 SURVIVED は他層 mask だった。** `guard_write.py` の marker 判定は
   lexical path と realpath の **2 経路の OR** である。初回 M12 は realpath 側だけを壊したため
   lexical 側が拒否を維持し、テストが赤くならなかった。両層同時変異 (M12b) で KILL を確認した。
   **防壁の穴ではなく、変異の当て損ないである。**
2. **M13 SURVIVED は変異位置の誤りだった。** 初回 M13 は `_MENTION_RE` を編集したが、
   tree 破壊の判定は `_CAMPAIGN_TREE` タプルが担う。実効 gate へ再照準した M13b で KILL を確認した。
3. **M03 / M16 / M17 の MISMATCH は expected_nodes の登録不足である。**
   - M03: runtime テストに加えて補助 AST テストも赤くなる。両方を登録した M03b で一致した。
   - M16b: 登録した 4 node のうち `test_bash_exploration_wal_reads_allowed` は赤くならなかった。
     WAL の read 許可は marker 判定とは**別の分岐**を通るためで、実装の分岐構造を親が取り違えていた。
     過剰拒否の検出自体は残り 3 node で成立している。
   - M17: `_BANNED_OUTPUT_NAMESPACES` へ `task-runs` を足す変異は dev-waves 系テスト群を巻き込み、
     **過剰決定**だった (DW-M03)。単独証拠から外し、正例の担保は M16b へ寄せた。
4. **M13b の実測 node に無関係な 1 件が混じった。**
   `test_codex_worker_launch.py::test_parallel_jobs_preserve_both_manifest_entries` が赤くなったが、
   単独再走で緑 (計算ノード実測)。並行 dev-wave ジョブ由来のフレークであり、
   本 wave の実装差分へは帰属しない (DW-O18)。

## 帰属不成立で本走しなかった変異

段 3 レビュー A の F28 判定に従い、M03〜M08 の初期形 (helper だけを official へ戻す単独変異) は
「helper を戻しても selector が exploration のままなので WAL と loop state が分裂するだけ」で
単一理由性が立たない。helper + selector の累積変異 (M03b の形) へ再照準した。
M04〜M08 は同型のため run1 では代表 1 件 (M03) のみを登録し、run2 で M03b として確定させた。
残る driver の配線は `test_p3_exploration_namespace.py` の runtime テスト
(loop / sort / trigger_gating / red / kickoff の 5 パラメータ) が公開入口から検査している。
