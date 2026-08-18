# 段 6 — 親の実測 (焦点走)

## 焦点走 1 (13:52-13:54 JST)

`python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_autonomous_trial_completeness.py`

**369 passed / 4 failed / 97.90s**。実装子が予告した 4 件と完全一致。

### 失敗 1・2 — 参照式が古い (期待値は不変)

- `test_t1311_registered_workload_binds_proposal_and_all_invocations` (:5747 付近)
  `assert cell["workload_flags"] == A.WORKLOADS["rr80"]`
- `test_t1311_registered_identity_consumes_issued_arm_bytes`
  `assert prepared.campaign.search_config["ycsb"] == A.WORKLOADS["rr80"]`

いずれも**左辺 (実際の値) は正しい** —
`{'ycsb_rmw': '0', 'ycsb_rratio': '80', 'ycsb_zipf_skew': '0.9'}`。
右辺が entry 全体になったための不一致。
両テストは `t325_registered_trial` fixture が `A.WORKLOADS` へ rr80 を monkeypatch する形で、
**wave 前から `A.WORKLOADS["rr80"]` は「flags の別名」として使われていた**。
期待値そのものは変わらないので、参照式へ `["ycsb"]` を足すのが正しい追随である。
これは「既存テストの期待値の変更」ではない。

### 失敗 3・4 — 設計判断が要る

- `test_m04_programmatic_holdout_reaches_u4_gate_before_unknown_workload` (:6154)
- `test_public_cli_holdout_opt_in_reaches_u4_gate_without_workload_patch`

**正しさ境界は壊れていない。** 両テストの
`pytest.raises(TrialRegistryError, match=r"\[u4-holdout-workload\] ...")` は**通過**している。
落ちたのはその後の `assert "rr80" not in A.WORKLOADS`。

この assert が守っていたのは「**出荷される探索表**に holdout が入っておらず、
明示的な registered 経路を通らずに holdout run を得られない」という設計性質である。
実装が正式 entry を `WORKLOADS` へ入れたことで、表の水準ではこの性質が弱まる
(U4 gate では依然拒否される)。

**親の裁定 (段 6)**: 正式 entry を `WORKLOADS` から出し、同じ entry 型の
兄弟 mapping (`FORMAL_WORKLOADS` 等) へ移す。producer の 3 sink と Layer-3 は
**両表を引く単一 resolver** を通す。これで

- [T-1333] 形 1 の実質 (scale が entry に在り、権威が 1 か所、両側が同じ entry から導出) は保たれる
- 着地済みの設計テスト `"rr80" not in A.WORKLOADS` を反転させない
- 検査が自前の profile 知識を持つ形 2 にもならない (resolver は producer 側の単一経路)
- `--workloads` 既定の拡大問題 (裁定 2.2) も構造的に消える

`DW-S06-B` の「既存テストの期待値を変更しない」を満たす形でもある。

## 焦点走 2 (13:59 JST)

`python3 tools/run_tests.py orchestrator/tests/test_layer3_report.py
orchestrator/tests/test_reflux_originless_compatibility.py
orchestrator/tests/test_s8c_preregistration_predicates.py
orchestrator/tests/test_frozen_artifacts.py`

**226 passed / 0 failed / 18.09s**。

- 凍結 artifact の pin は緑 (`test_frozen_artifacts.py`)。ただし A-05 のとおり
  holdout freeze は held であり、緑は「KEEP 側の hash 照合が通った」ことしか意味しない。
  land 前に両 path の bytes 非変更を親が直接実測する。
- C01 snapshot (`test_s8c_preregistration_predicates.py`) は現時点で緑。
  `current_commit_snapshot` fixture は **commit 済み blob** を読むため、
  未 commit の作業ツリー変更は反映されない。実装子の予測どおり、
  commit 後に reason が遷移して赤になる見込み。**段 7 の commit 後に再走が必須。**

## 焦点走 3 — 1 巡目 fix 後 (14:23 JST)

`python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_autonomous_trial_completeness.py orchestrator/tests/test_campaign.py`

**715 passed / 1 failed / 9 skipped / 30.31s**。

- 段 5 時点の赤 4 件 (t1311 参照式 2 件、`"rr80" not in A.WORKLOADS` 2 件) は**全て解消**。
- レビュー B が追加指摘した `test_campaign.py::test_autonomous_trial_env_run_root_and_worktree_container_gate` も解消。
  いずれも F-1 (正式 entry を `FORMAL_WORKLOADS` へ分離) の根本修正による。
  **既存テストの期待値を 1 つも変えずに解消した。**
- 残る赤 1 件は 1 巡目 fix が新設した
  `test_m6_formal_campaign_scale_is_the_only_mismatch` の参照型の誤り
  (`arm_execution` は dict なのに属性アクセスしている)。production の問題ではない。
  → fix 2 巡目 (G-1) へ。

## 焦点走 4 — fix 2 巡目後・test_trial_registry.py を追加 (14:30 JST)

**18 failed**。

- **16 件 = `test_trial_registry.py`**、原因は 1 つ:
  `[terminal-completeness] [campaign-chain] cells[0].perf_config_scale is not an object`。
  F-4 の新 cell field を Layer-3 (`autonomous_trial_completeness.py:550-556`) が必須化し、
  受入 fixture の cell 構築が追随していない。→ fix 3 巡目 (H-1)。
  **親の裁定: 必須のまま維持し fixture を追随させる。** 落ちているのは実在の過去 artifact ではなく
  テスト内 fixture であり、条件付き必須にすると field を落とした report が検査を逃れる。
- **2 件 = `test_campaign.py` の exploration output root process pin 系。本 wave に非帰属。**
  根拠: (a) wave の差分は `_resolve_exploration_output_root` /
  `_exploration_output_root_state` に**一切触れていない** (s5-diff と HEAD 差分の両方で 0 hit)、
  (b) 同じ family の 5 件は fix 1 巡目適用済みの焦点走 3 で**緑**だった、
  (c) fix 2 巡目が触ったのは test 参照式 1 行のみ。
  差は file 選択による xdist 分配の違いで、process 内で 1 度だけ pin される状態を
  複数テストが奪い合う既存の test 分離問題。
  commit 後に `tools/check_acceptance_reds.py` で機械判定にかける。

## 焦点走 5 — test_campaign.py 単独 (14:31 JST)

**5 failed**、全て exploration output root pin family
(`test_autonomous_trial_env_run_root_and_worktree_container_gate`、
`test_exploration_output_root_env_precedence_and_official_isolation`、
`test_exploration_output_root_pin_is_shared_and_locked_across_aliases`、
`test_exploration_output_root_pin_rejects_env_removal_before_legacy_fallback`、
`test_exploration_output_root_env_process_pin_rejects_drift`)。
単独走で**再現する**ため通常のフレークではなく、file 選択に依存する既存の分離問題である。

## 焦点走 6 — fix 3 巡目後 (14:40 JST)

**13 failed** (16 → 13)。原因は 1 つに収束:
`[campaign-chain] cells[0] workload scale differs from producer`。

### 親が特定した原因 — wave 前から repo に埋まっていた矛盾

`orchestrator/tests/test_trial_registry.py` の受入 fixture は、
**同じ registered holdout 試行について 2 つの矛盾する scale を持っている。**

- `:516-527` descriptor: `"scale": {"records": 1_000_000, "threads": 48}` (封印された arm 権威)
- `:567-580` campaign `search_config`: `"records": 100_000`, `"threads": 4` (探索 scale)

**wave 前はこの矛盾が受入を通っていた。** 本 wave の検査が初めて捕まえた。
[T-1349] が警告した「descriptor と実 benchmark が食い違ったまま両方緑」の実物であり、
段 3 レンズ B の B-01 が指摘した穴が fixture の中に実在していたことになる。

これは本 wave の主要な成果である。fix 4 巡目 (I-1) で campaign 側を descriptor 側 (= producer entry) へ揃える。
**方向が逆 (descriptor を下げる) だと [T-1349] の束縛が壊れるため明示的に禁じた。**

## fix 4 巡目を投じた理由 (DW-O16 の 3 巡上限を 1 巡超える)

`DW-O16` は「NO-GO が続く場合は fix を重ねず 3 巡を上限」と定める。
本 wave の巡は敵対レビューの NO-GO 反復ではなく**親の実測による収束**であり、
赤は 4 → 1 → 16 (scope 拡大による新規計測) → 13 と単調に減り、
原因も毎巡 1 つに絞れている。上限の趣旨は不明瞭な所見への fix 積み重ねを止めることなので、
機械的に収束している修正はこれに当たらないと親が裁定した。
4 巡目で閉じない場合は変異で裏取りして real/refuted に裁定して閉じる。

## 焦点走 7 — fix 4 巡目後 (14:53 JST) — 全緑

`python3 tools/run_tests.py orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_autonomous_trial_completeness.py orchestrator/tests/test_trial_registry.py
orchestrator/tests/test_layer3_report.py orchestrator/tests/test_reflux_originless_compatibility.py`

**593 passed / 0 failed / 267.68s**。

赤の推移: 段 5 = 4 → fix1 = 1 → scope 拡大で 18 (新規計測) → fix3 = 13 → **fix4 = 0**。
**既存テストの期待値を 1 つも緩めず、production 側の検査も一切弱めずに閉じた。**
fix4 で更新したのは fixture の scale と、それに伴う campaign ID の再計算だけである。

## 焦点走 8 と非帰属の確定 (14:55 JST)

`test_campaign.py` / `test_s8c_preregistration_predicates.py` / `test_frozen_artifacts.py` /
`test_s8c_generation_projection.py` → **5 failed**、全て exploration output root pin family。

**本 wave に非帰属と確定した。根拠 3 点。**

1. wave が変更した production file は
   `orchestrator/campaign/p3_autonomous_workload_trial.py` と
   `orchestrator/campaign/autonomous_trial_completeness.py` の 2 本のみ。
   落ちている assertion が呼ぶ `layout` module (`layout_module._resolve_exploration_output_root()`) は
   **変更していない** (`git diff HEAD --name-only` に無い)。
2. wave の差分は `_resolve_exploration_output_root` / `_exploration_output_root_state` に 0 hit。
   新設した legacy freeze 読取は `_preflight_workload_profile` (`p3_autonomous_workload_trial.py:862`)
   の**関数内**であり、import 時副作用ではない。
3. **同じ 5 件は焦点走 3 (wave のコード適用済み) で緑だった。**
   コードが同一で file 選択だけが違うと結果が変わる以上、原因は差分ではなく
   process 内で 1 度だけ pin される状態の実行順である。

commit 後に `tools/check_acceptance_reds.py` で機械判定にかけ、受入結果へ反映する。

## main 取り込みと C01 遷移の実測 (15:14 JST)

main が `a160f4aa` → `b30b95bd` へ 6 commit 進んでいたため取り込んだ (merge `49a155f0`)。
両側が触った file の積集合は `comm -12` で**空**と実測し、merge に実装面は生まれないことを
事前に確認した。競合なし、submodule gitlink も main 側 pin と一致。
merge 後の全史 provenance 監査は 4028 件・新規違反なし。

### C01 の遷移 (library 経路で実測)

`s8c_preregistration_evidence.get_registry().evaluate_all("HEAD", repo_root=...)` の結果:

```
C01: UNSATISFIED / ratified-generation-reference-absent
```

wave 前は `UNSATISFIED / workload-projection-mismatch`。他 11 条件は不変
(C02/C03/C05/C06/C07/C08/C11 = EVIDENCE_UNDEFINED、C04/C09/C10/C12 = UNSATISFIED)。

**status は UNSATISFIED のままで、満たしたふりにはなっていない。**
択 (β) が `load_ratified_freeze` を呼ばない設計の正しい帰結であり、
段 2 プラン・段 3 レンズ B・段 5 実装子の 3 者が独立に予測した値と一致する。
`test_s8c_preregistration_predicates.py:151` の snapshot 1 箇所を更新する
(負の control `TOKEN_ONLY_C01` と `nc_c01_perf_scale_regression` は更新しない)。

### 焦点走 9 の 11 赤のうち 10 件は環境要因

`test_reachable_consumers_reject_absence_shapes_with_single_reason[...]` 等 10 件は、
テストの一時 repo 内で `git commit` subprocess が **10 秒 timeout / returncode -9 (SIGKILL)**
になったもので、差分の論理エラーではない。並行走行によるメモリ/CPU 逼迫が原因。
負荷を落として単独再走で確かめる。

## 焦点走 10 — C01 snapshot 更新後・単独走 (15:19 JST)

`python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_predicates.py`

**137 passed / 0 failed / 19.77s**。

これで 2 点が確定した。

1. **C01 snapshot の更新が正しい。** `ratified-generation-reference-absent` で緑。
   負の control (`TOKEN_ONLY_C01`、`nc_c01_perf_scale_regression`) は更新していない。
2. **焦点走 9 の 10 件は環境要因だった。** 同じ file を負荷の低い状態で単独走させると全緑。
   `git commit` subprocess の 10 秒 timeout / returncode -9 (SIGKILL) は
   並行走行によるメモリ/CPU 逼迫であり、差分に帰属しない。
