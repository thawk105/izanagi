## 総括

- 判定は **NO-GO**。残る must-fix は根本原因単位で **2 件**。
- 13 所見は `closed` 6 件、`partial` 2 件、`scope 外 (裁定済み)` 5 件、`regressed` 0 件。
- tracked 可視化、偽 clock、`2/1/1`、5 process 化は最終コードで成立している。
- 後続 fix が前巡の成果を壊した形は見つからない。
- must-fix は、既出の正本台帳 closure と、新規の偽 clock 回帰 control 欠落。
- pytest は実行していない。親提供の焦点走・変異結果と静的読解だけを根拠にした。

## 1. 所見対応表 (13 件)

| 所見 | 判定 | 根拠 | 残る具体的な穴 |
|---|---|---|---|
| レビュー A #1 — tracked descendant を fail-closed にして正当な 418 files を拒否する | `closed` | commit `c983f681`; `output_snapshot_ignores.py:227-293`; `test_s8b_oracle_driver.py:710-732` | なし。tracked path と祖先は可視、同 prefix の untracked peer は除外される。 |
| レビュー A #2 — 偽 clock 未注入、watchdog 不統一 | `closed` | commit `c983f681`; `test_pegasus_dispatch_compute.py:32-39,5403-5430,5470-5505` | 実装自体は閉じた。回帰 control 欠落は新規所見として後述。 |
| レビュー A #3 — summary の cardinality が `1/1/1` に弱体化 | `closed` | commit `c983f681`; `test_flaky_test_holds_contract.py:896-933` | synthetic 2 行で `2/1/1` と digest を復元済み。 |
| レビュー A #4 — failure ledger、分類手順、設計メモ、残余 task が未反映 | `partial` | `p1-stale-hold-detection.md:1-4`; `docs/spool/FOLDED.md:2574`; 一方 `docs/failures.md:5099-5101,13265-13331` | P1 メモと task-runs 用 T-1773 は存在する。F136/F480 の撤去 closure、F480 の 10 秒床への真因訂正、worklog の 6 段分類、wildcard 残余 risk の task が未反映。 |
| レビュー A #5 — linked worktree の contract fixture がない | `scope 外 (裁定済み)` | `test_s8b_oracle_driver.py:653-672`; production は `output_snapshot_ignores.py:91-111` | 裁定どおり fixture は通常の `git init` のまま。linked-worktree fixture は追加されていない。 |
| レビュー A #6 — duration ledger が旧 `10.0` 秒 | `scope 外 (裁定済み)` | `acceptance_duration_ledger.json:7663` | 裁定どおり `10.0` のままで、途中更新されていない。 |
| レビュー B #1 — tracked 418 files による全 snapshot caller の決定的失敗 | `closed` | commit `c983f681`; `output_snapshot_ignores.py:227-293`; `test_s8b_oracle_driver.py:710-732` | なし。A #1 と同じ修理で閉じた。 |
| レビュー B #2 — hold#1 の実 clock、5 秒 wait、10/60 秒 join | `closed` | commit `c983f681`; `test_pegasus_dispatch_compute.py:39,5400-5428,5467-5502` | 全 Event wait と join は 30 秒 watchdog、各 thread は独立 `_Clock` と偽 sleep。 |
| レビュー B #3 — registry 撤去後も F136/F480 と分類手順が未更新 | `partial` | registry は `flaky_test_holds.py:200` で空。一方 `docs/failures.md:5099-5101,13317-13319` は登録状態を記述 | 正本台帳が実行可能 registry と不一致。F480 の族定義訂正と 6 段分類も未記録。 |
| レビュー B #4 — snapshot 1 回 14 process、全走約 821 process | `closed` | commit `c983f681`; `output_snapshot_ignores.py:206-293` | 1 回の combined 呼出しは `rev-parse`、`config`、`check-ignore`、batch tracked、ignored 列挙の 5 process。memo はなく before/after を跨がない。 |
| レビュー B #5 — `output/task-runs/` の並行 writer 競合 | `scope 外 (裁定済み)` | `tools/run_tests.py:1064-1098`; `tools/task_runs/generation.py:1131`; 対象 file は base から差分なし | writer は repository 内のまま。snapshot 除外への中途半端な追加もない。 |
| レビュー B #6 — 内側 xdist subprocess の timeout と cleanup 不在 | `scope 外 (裁定済み)` | `test_real_repo_serialization.py:537-540,3932-3941` | 裁定どおり timeout 引数も process-group cleanup も追加されていない。 |
| レビュー B #7 — hold#1 の duration ledger が `10.0` | `scope 外 (裁定済み)` | `acceptance_duration_ledger.json:7663` | A #6 と同じ。親が段 7 で扱う裁定どおり手つかず。 |

## 2. 3 巡の fix が開けた穴

後の巡が前巡の成果を壊した形は見つからない。

- wildcard の期待値修正後も、非実在 literal の主眼は残っている。`test_s8b_oracle_driver.py:690-699` は path 作成前に `runs`、`cache/deep`、`global-cache`、`info-cache` を exact に要求する。`701-707` で変えたのは、実在後の wildcard subtree を Git が畳む実挙動だけである。wildcard の実在依存は解消したことにせず、明示的に残している。

- 3 件の `subprocess.run` 差し替えは `mock.patch` の `with` 内に閉じる (`test_s8b_oracle_driver.py:744-785`)。例外経路でも context manager が復元し、commit `bc2f2aa2` はこの test file 以外の実装を変更していない。test 外への差し替え漏れはない。

- 5 process 化は tracked 可視化を維持している。batch `ls-files --cached` の結果から tracked path と祖先を作り (`output_snapshot_ignores.py:227-285`)、prefix 判定前に例外化する (`:330-342`)。対の contract は tracked 3 path の可視と untracked peer の不可視を同時に要求する (`test_s8b_oracle_driver.py:710-732`)。

- `f3ed1d7a` は逐語文書と変異 receipt の追加だけで、実装面を変更していない。

## 3. 変異で撃たれていない領域

7/7 KILLED は登録された 7 変異について正しいが、patch 全体の網羅を意味しない。

| 未照射領域 | 問題か | 判定理由 |
|---|---|---|
| 2 thread test の偽 clock / `sleep=clock.sleep` | **問題。must-fix** | `mutation-final-spec.json:4-123` に Pegasus 変異がない。偽 sleep を外しても元の約 10 秒床は 30 秒 watchdog 内なので、性質 assertion を保ったまま通過しうる。 |
| `_THREAD_COORDINATION_WATCHDOG_S = 30.0` の値 | 問題ではない | 親実測は注入後 0.01 秒で、30 秒は約 3000 倍の hang 回収枠。値そのものは受理性質ではなく運用上の回収方針である。 |
| summary の `2/1/1` cardinality | 問題ではない | matrix 変異はないが、`test_flaky_test_holds_contract.py:896-933` が 2 行入力と 3 個の異なる count を exact に固定する。相互代入は直接赤になる。 |
| `rev-parse --git-path`、`core.excludesFile`、root `.gitignore` の列挙 | 現 scope では問題ではない | `test_s8b_oracle_driver.py:653-696` が 3 source 由来の literal を期待する。linked-worktree topology への退行だけは未検査だが、明示的な scope 外。 |
| tracked batch 照会と 5 process 化 | 問題ではない | process 数自体は変異対象でないが、tracked 可視性は contract と m03 が守る。最終コードは静的に 5 process で、後続 commit による再分割もない。 |
| hold#3 の hookwrapper と yield 前記録 | 問題ではない | matrix 外だが、test 自身が decorator 除去と post-yield 移動の 2 mutant を構築して拒否する (`test_real_repo_serialization.py:3830-3866`)。 |

偽 clock には、wall-clock 上界を再導入せず、注入した sleep の呼出しまたは fake clock の進行を決定的に観測する control が必要である。その control と対になる「`sleep=clock.sleep` を外す」変異を登録すべきである。

## 4. 受入全走の前に直すべきもの

must-fix は **2 件**。

1. 既出の台帳 closure を完了する。

   - F136 に hold#2 の修理、`c983f681`、撤去、再導入 node を追記。
   - F480 から hold#1 を負荷依存例として扱う誤記を訂正し、決定的な 10 秒床と偽 clock 修理を記録。
   - hold#1 / hold#3 の撤去と、6 段分類手順を worklog に記録。
   - wildcard 残余 risk の canonical backlog が無ければ起票する。

2. 偽 clock 修理へ決定的な control と変異を追加する。

   `sleep=clock.sleep` の削除で元の固定床が戻っても、現在の 30 秒 watchdog と性質 assertionだけでは通過しうる。高価な全走の前に、この root cause が回帰不能であることを固定する必要がある。

上記以外に must-fix はない。task-runs writer、wildcard の実在依存、内側 xdist timeout、linked-worktree fixture、duration ledger は裁定済み scope 外として扱う。

## 所見一覧 (新規のみ)

- **所見 1: 偽 clock 修理が変異でも決定的 control でも固定されていない**
  - 場所: `orchestrator/tests/test_pegasus_dispatch_compute.py:5403-5415,5470-5485`; `output/insights/2026-08-26_flaky-holds-removal/mutation-final-spec.json:4`
  - 分類: must-fix
  - なぜ問題か: `sleep=clock.sleep` を外して元の約 10 秒床へ戻しても、30 秒 watchdog 内で性質 assertion が成立し、回帰が通過しうる。
  - もし放置したら成果物の何がどう変わるか: 変異レポートは SURVIVED 0 のまま根本修理を未検査とし、将来の削除で受入集合と failure report が再び負荷依存になる。
  - 確度: high — 7 変異に Pegasus 対象がなく、親実測の注入前 10.015 秒は現在の 30 秒 watchdog より短い。