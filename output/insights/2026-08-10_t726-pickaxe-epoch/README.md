# [T-726] pickaxe 履歴範囲の epoch 限定 — 変異台帳と決定的な逐語

wave: `dev-wave-t726-pickaxe-epoch` / 実装 commit `5f38b96f`、fix `fcef0c0c`、docs `de8eb271`。
設計判断の正本は decisions の「RuleOps の pickaxe は candidate epoch 窓に限り、窓は対象の最終変更を
必ず含む」、経緯は同日の worklog エントリ。

## 前提の実測 (計算ノード、`-n0 -s`)

```
RULEOPS_MAX_PACKAGE_PREFLIGHT_SECONDS=36.467   # 2,502 commit / signal token 6 件 / 1 passed 69.38s
```

= 14.6 ms/commit (package 全体)、`r0 = 36.467 / (2502 * 6) = 0.002429` 秒/(token·commit)。
外側 60 秒までの残余は約 1,610 commit。commit 増加は 189/日 (直近 7 日) / 74/日 (直近 30 日) で、
裁定文の「5〜11 日」より猶予は長い (8.5〜22 日) が、決定論的に赤になる事実は変わらない。

**重複起動していた別 job の独立実測は 36.527 秒**で 0.06 秒差。同 job が login node で測った
3 token 8.7〜9.3 秒 (6 token 換算 52〜56 秒) は計算ノードと整合せず、機体差が大きいため
定数導出にも律速帰属にも使っていない。

## 変異 matrix

`tools/mutation_harness.py`、runner-mode=dispatch、対象コマンドは
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_ruleops.py -q -rf`。

| 走 | spec | ledger | 内容 |
|---|---|---|---|
| 1 | `mutation-spec.json` | `mutation-ledger.json` | 事前登録 8 件。M2/M3/M4/M5/M6 が期待どおり KILLED、M1/M7/M8 は MISMATCH |
| 2 | `mutation-spec-2.json` | `mutation-ledger-2.json` | M1/M7/M8 を実測 node で再走 → 3 件 KILLED |
| 3 | `mutation-spec-3.json` | `mutation-ledger-3.json` | M5 を単一理由 fixture で再走 → KILLED |

baseline はいずれの走も PASSED。**SURVIVED / TIMEOUT はゼロ。**

### 走 1 の MISMATCH は親の過小予測である (erratum、`DW-M02`)

M1 / M7 / M8 は「予測より多くの node が落ちた」形であり、変異が生存したのではない。実測は次。

- M1 (`^{epoch}` を外して全史へ戻す) — 予測 1 件に対し実測 4 件
  (`test_pickaxe_queries_only_validated_epoch_window`、
  `test_epoch_horizon_residual_allows_path_refresh_to_hide_old_signal_history`、
  `test_local_rename_config_does_not_change_evidence_or_acceptance`、
  `test_receipt_head_outside_epoch_window_is_rejected`)。
- M7 (timeout units を全履歴へ戻す) — 予測 1 件に対し実測 2 件
  (`test_pickaxe_uses_epoch_commit_count_for_d265_timeout_budget` を親が数え落としていた)。
- M8 (窓列挙を `--first-parent` にする) — 予測 1 件に対し実測 2 件。

### 走 1 の M5 KILLED は偽緑だった (erratum、`DW-M03`)

段 6 の焦点再レビューが指摘した。fixture が receipt head の側に candidate path の変更を含んで
いたため、`receipt-head-outside-epoch` の検査を外しても既存の `receipt-epoch-path` が拒否し、
赤くなるのは **reason の差だけ**で受理境界の差ではなかった。`receipt_head..HEAD` の path 変更を
package が pin する receipt path だけに収めた DAG へ fixture を作り替え (`fcef0c0c`)、
**gate を外すと `check` が rc=0 で通る**単一理由 fixture にしてから再走した。
production の検査は 1 行も変えていない。

### M7 は kill でなく diagnostic sensitivity pin (`DW-M08`)

timeout units を全履歴へ戻しても**受理集合は変わらない** (内部 timeout の予算が変わるだけ)。
したがって受理境界の kill は 7 件、診断シグナルの pin が 1 件である。

## 段 3・段 6 の敵対レビューが設計を変えた点 (逐語)

- 段 3 A-01 (sol/max):「`epoch == HEAD` なら窓が空になり、`_compare_signals` は `∅ == ∅`。
  距離は 0 なので `stale-epoch` も発火しない」→ 窓が candidate path の最終変更 commit を含むことを
  要求する条件を新設。既定 epoch も捕捉 HEAD から「最終変更 commit の第 1 親」へ変更。
- 段 3 B-02 (luna/max) が同じ穴を独立に指摘。
- 段 6 C-03 (sol/high):「`S` は `E..HEAD` に含まれるため membership を通る。しかし `S..HEAD` には、
  S から到達できない E 側の古い main 履歴が含まれる」→ receipt head の条件を
  `merge-base(epoch, receipt_head) == epoch` へ変更。
- 段 6 C-02 (sol/high): read-only probe で `diff.renames=true/false` を切り替えると pickaxe 出力が
  変わることを実測 → `diff.renames` / `diff.renameLimit` を防護 override へ固定。
- 段 6 C-06 (sol/high):「`assert 30.0 <= 45.0` は production 定数を参照せず、常に緑」→ 恒真な
  assert を production 定数由来の計算へ差し替え。

## 受入

`python3 tools/run_tests.py --force-dispatch` (受入形、select flag なし)、tip `edc9455e`。

```
8037 passed, 20 skipped in 505.41s (0:08:25)   # rc=0
```

受入 lease は 21 回の `claim` 後に `acquired`、待ち手内で local main を取り込んでから投入し、
終了時に `release` した。
