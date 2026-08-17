# 段 1 brief — [T-1310] 正式 workload profile (rr80 / rr20) を producer へ実装する

wave: `t1310-formal-workload-profile` / branch `worktree-t1310-formal-workload-profile` / 起点 main `2a3b5055`

## scope

producer `orchestrator/campaign/p3_autonomous_workload_trial.py` に **正式 (production) profile** を実装する。
正式 profile は holdout `rr80` / `rr20` を対象とし、正式 scale (records 1,000,000 / threads 48) を
campaign / perf / descriptor の 3 sink すべてへ束縛する。探索 (exploratory) 経路は現状のまま
`ycsb-a/b/c` @ 100,000 records / 4 threads で不変とする (規律 4)。
波及先として C01 evaluator の判定 snapshot と repo scan invariant の 0 hit 契約を scope に含める。

## 実測した前提 (brief 前)

- C01 は現在 `UNSATISFIED` / `workload-projection-mismatch`。`orchestrator/tests/test_s8c_preregistration_predicates.py`
  を runner 経由で実走し 137 passed で緑 (2026-08-17 22:5x JST、worktree `t1310-formal-workload-profile`、
  bounded local)。原因は 3 sink が探索 scale の literal しか持たないこと。
- 稼働 3 wave (T-338 / T-848 / T-1312) は 22:40〜22:41 JST 起動で brief 未生成。台帳項の編集面は
  RF 統計設計 / 変異 TIMEOUT 意味論 / launcher の grace 起点であり、s8b_* と descriptor は含まない。
  **段 5 投入直前に 3 本の brief を再検分する。**

## 実アンカー

| 対象 | anchor |
|---|---|
| 3 sink | `orchestrator/campaign/p3_autonomous_workload_trial.py:637` `_campaign_for` / `:677` `_perf_for` / `:687` `_descriptor_for` |
| 探索 workload 閉集合 | 同 `:188` `WORKLOADS` (ycsb-a/b/c)、`:654` / `:1595` `pilot_scope="exploratory-ycsb-abc"` |
| C01 判定式 | `orchestrator/campaign/s8c_preregistration_evidence.py:1413-1445` (`_evaluate_c01`) |
| C01 snapshot | `orchestrator/tests/test_s8c_preregistration_predicates.py:151`, `:1869` |
| 正式 holdout 定義 | `orchestrator/campaign/s8b_holdout_freeze.py:83-100` (`_holdout` / `HOLDOUTS`、records 1,000,000 / threads 48) |
| ratified 参照 | `orchestrator/campaign/s8b_ratified_freeze.py:1333` `load_ratified_freeze` |
| repo scan 0 hit 契約 | `orchestrator/campaign/s8b_holdout_freeze.py:43` `EXCLUDED_PATHS`、`:501-530` 三軸 conjunction、`:618-630` 0 hit snapshot |
| 凍結 bytes pin | `orchestrator/tests/test_frozen_artifacts.py` (`output/s8b-freeze/holdout_freeze.json`) |

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 正式 profile の workload 値 (rratio / skew / rmw) を **literal で書かず** `load_ratified_freeze`
  経由で実行時に読む。理由 = producer は既に `ycsb_zipf_skew: "0.9"` と `ycsb_rmw: "0"` を持つため、
  rratio の `80` / `20` を literal で足すと三軸 conjunction が成立し repo scan invariant の 0 hit が 1 hit へ壊れる。
  C01 が要求する `load_ratified_freeze` 到達可能性とも同時に満たす。
- **(P2)** 3 sink には正式 scale の literal `1_000_000` / `48` を置き、freeze 由来の値と一致しなければ
  fail-closed で落とす。C01 の `_integers(functions[name])` が sink 関数内の整数 literal を要求するため。
  代償 = scale の二重管理。恒真にならないよう「照合が外れたら落ちる」形にする。
- **(P3)** profile 選択は明示入力とし、既定は探索のまま。既定を正式へ倒さない (規律 4)。
- **(P4)** C01 snapshot は実走後の実測値へ更新する。更新後の期待値を先に書かない (値なし前方参照の禁止)。

## 不変条件

- 探索側の records / threads を上げない (規律 4)。
- `output/s8b-freeze/holdout_freeze.json` の bytes を変えない。`s8b_holdout_freeze.py` は generator source
  hash pin を持つため**編集しない**。
- repo scan invariant の `conjunction_hits` は 0 のままにする。
- 床値表の再発行・再凍結を行わない (D496)。凍結対象は構成集合・holdout 集合側にある。
- 正しさゲートを緩めない。C01 を通すために判定式を弱めない (規律 2)。

## 成果物影響 (DW-G05)

実装しないと [T-822] (i) の Layer-3 必須化は、C01 が `UNSATISFIED` のままなので**正式受理集合を空**にするか、
探索 scale (100,000 / 4) で得た結果を正式 scale (1,000,000 / 48) の certified 選択結果として**偽る**。
どちらも 8c 正式受入の verdict と材料レポートの scale 記載を直接汚す。

## 分割方針

設計択一が割れ (P1/P2)、受理集合が変わるため軽量版を採らない。段 2 プラン起草 1 本、段 3 敵対相談 2 本
(レンズ = 凍結/repo scan 破壊、恒真化と規律 2)、段 5 実装 1 本、段 6 敵対レビュー 2 本 + fix。
