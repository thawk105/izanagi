# [T-1881] 軸 3 検索実行器の変異検査 — 生の台帳

- 作成日: 2026-09-02
- wave: `dev-wave-t1881-axis3-executor`
- 変異対象 commit: `ae994c8dc07dccb1442186b82af6d30299bda84c`
- test command: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_related_work_search.py -q -rf`
- harness: `tools/mutation_worktree.py`（使い捨て worktree、`--runner-mode dispatch`、`--detached`）

## 3 走行の関係

| 走行 | spec | 台帳 | 目的と結果 |
|---|---|---|---|
| probe | `mutation-probe.json` | `mutprobe-ledger.json` | 全 10 件を `SURVIVED` 期待で登録し、実際に赤くなる node を観測する巡。**9 件が検出され、`MU-4b` だけが生存した。** baseline は 107 passed / 11.92 秒で緑 |
| 本走 attempt 1 | `mutation-real.json` | `mutreal-ledger.json` | probe の観測 node を期待集合に固定した巡。**9 KILLED / 1 MISMATCH。** MU-6a だけ期待 5 node に対し実測 6 node になった |
| 本走 attempt 2 | `mutation-real2.json` | `mutreal2-ledger.json` | MU-6a の期待集合を attempt 1 の実測へ訂正した巡。**10 KILLED / 0 MISMATCH** |

**初回の結果を消していない。** 3 走行の spec と台帳をすべてここに残す。

## MU-4b が生存したこと (probe)

`MU-4b` は「未評価の count-only control 行は完走を主張しない」という fail-closed 保証の
**2 箇所目 (bundle 再導出側)** を `complete=False` → `complete=True` へ書き換える変異である。
probe ではこの変異を当てても 107 件のテストが 1 件も落ちなかった。

この保証は凍結契約
`docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` の限界節に書いてある。
1 箇所目 (`_run_stream` 側) は `MU-4a` が示すとおり検査されていたが、2 箇所目は無検査だった。
負例 `test_bundle_rederived_count_only_control_never_claims_completion` を新設して閉じた。

## MU-6a の MISMATCH (本走 attempt 1)

期待していた 5 node に対し、実測は 6 node だった。増えた 1 件は
`test_bundle_rederived_count_only_control_never_claims_completion` で、probe の**後**に
MU-4b を閉じるために新設したものである。この負例も normal checkpoint producer に依存するため、
producer から独立 pass request を落とせば赤になるのが正しい挙動である。

期待集合を実測へ訂正して attempt 2 を走らせた。**期待値を結果に合わせて緩めたのではなく、
probe と本走の間にテストが 1 本増えた分を反映しただけである。**

## attempt 2 の wrapper 事後検査 (rc=125)

`mutreal2-ledger.json` の `summary` は
`{"KILLED": 10, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0, "completed": 10, "matching": 10, "recorded": 10, "registered": 10}`
であり、`repo_head` と `spec_sha256` を pin している。台帳は完備している。

一方 `mutation_worktree.py` の wrapper は
`共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で rc=125 を返した。
この検査は source worktree と main checkout の `git status` / `git submodule status --recursive` の
stdout bytes を走行の前後で比較するものである。**親の worktree は走行中ずっと clean だった**
(`git status --porcelain` が空)。変化したのは共有 checkout 側であり、並行して稼働している
他 wave の untracked 集合が動いたことによる。

**したがってこの赤は本 wave の変更に帰属しない。** ただし wrapper が主張するはずだった
「共有木が走行前後で不変だった」は主張できない。変異自体は固定 commit の使い捨て worktree 内で
実行されており、共有木の状態に依存しない。

## 登録した 10 変異

| ID | 壊した対象 | 期待 node 数 |
|---|---|---|
| MU-1 | production transport の exact type 検査 | 1 |
| MU-2 | catalog schema の「母集合の外」7 項目の `minItems` | 1 |
| MU-3 | arXiv の解釈後クエリ照合 | 1 |
| MU-4a | `_run_stream` 側の control fail-closed | 1 |
| MU-4b | bundle 再導出側の control fail-closed | 1 |
| MU-5 | 封印 closure の HEAD blob 比較 | 1 |
| MU-6a | normal checkpoint producer の独立 pass request | 6 |
| MU-6b | quota checkpoint producer の cursor request | 3 |
| MU-7 | 応答受領時刻の記録 | 1 |
| MU-8 | 凍結 amendment digest の literal | 1 |

**登録しなかった変異とその理由**は段 6 裁定に従う。runtime の exact 7 aggregate は自分が作った
固定長 list の要素数を自分で数える恒真検査、control 通過は evaluator 未実装、
production authenticity / private state は gate されておらず帰属不能である。
