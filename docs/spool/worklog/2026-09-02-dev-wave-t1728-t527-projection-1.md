---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1728-t527-projection
seq: 1
title: [T-2161] [T-1728][T-527] の変異 matrix を走らせた — 9 件中 8 件が検出され、1 件は防壁が launch admission と重複していることを示した (記録のみ、branch worktree-dev-wave-t1728-t527-projection、baseline 781 passed)
---

## 本文

- エントリ 1160 の時点では計算ノードの混雑で走らせられなかった変異 matrix を、queue が空いた
  直後に着地 tip `68cf9bce4722bdc16d3f1b91e76568b9070f3dce` に対して走らせた。
  baseline は 781 passed / 3 skipped で緑。9 件すべて完走し timeout も parse error も無い。
  逐語 anchor の一意性は走行前に機械検査済み (9/9)。生 台帳は
  `output/insights/2026-09-01_t1728-t527-formal-launch-blockers/mutation-ledger.json`。

- **単一理由で検出された 4 件。** 落ちた node が新設テストだけで、他層に mask されていない。
  M1 (activation gate を丸ごと削る) は
  `test_formal_profile_effective_none_rejects_before_binding_and_run_root` の 1 件、
  M3 (`registered-effective` の workload 受理を元へ戻す) は
  `test_formal_profile_accepts_registered_effective_binding_via_formal_resolver` の 1 件、
  M5 (trigger-gating の pass-through を削る) は trigger-gating の新設 2 件、
  M8 (非認証併用の拒否を削る) は
  `test_formal_profile_rejects_noncertifying_before_launch_admission_and_run_root` の 1 件。

- **冗長と事前に判定していた 1 件は予想どおりだった。** M7 (拒否文字列を変える) は
  本 wave より前から存在する pin 2 件 (`:618` / `:682`) が落とす。新設テストの寄与はない。

- **`loop.py` の 3 件は過剰決定だった。** M4 / M6 / M9 はいずれも意図した新設テストが
  実際に落ちている (`test_run_campaign_forwards_only_non_none_holdout_observation_admission`、
  `..._rejects_balanced_schedule_with_holdout_admission_before_output`、
  `..._rejects_multiple_genomes_with_holdout_admission_before_output`) が、同時に 61〜62 件が
  落ちる。内訳は 3 file に散っており、削った guard と無関係な
  `test_clean_dry_pass_still_admitted_on_pegasus` のような node を含む。
  **原因は `loop.py` が `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の 24 path に含まれ、
  blob SHA-256 が HEAD へ束縛されていることである。** 変異は作業ツリーの bytes を変えるが
  HEAD は元のままなので、guard の効果とは別に contract-loader drift が広く発火する。
  したがってこの 3 件は「検出された」とは言えるが**単独変異の証拠としては採らない**。
  この 24 file に対しては、変異 harness が構造的に単一理由の証拠を作れない。
  一般化して他 wave へ持ち出す前に、同型の観測が別 file でも出るか確かめる必要がある。

- **M2 だけが生存した。これは穴ではなく重複だった。** `_preflight_workload_profile` から
  `load_launch_binding` の呼出しと `prereg_commit` 一致検査を丸ごと削っても、落ちるテストが
  1 件も無い (injection diff は実在を確認済みなので注入漏れではない)。理由は
  `_trial_launch_admission` が通る registry 側の経路が同じ P/C/H 検査
  (`require_effective_preregistration` と `load_launch_binding`) を独立に行うためで、
  preflight 側の binding 検査は**受理集合を 1 件も変えない多重防壁**である。
  段 6 の fix が呼出し回数の決め打ちを性質検査へ緩めたとき、この変異を検出する手段が
  無くなったという経緯もある。**多重防壁を残すか、preflight 側を薄くして launch admission に
  一本化するかは裁定事項**であり、本 wave では現状維持とした。
  {{T:preflight-binding-redundancy}} へ送る。

- 変異走はエントリ 1160 の記録時点では「走らせられなかった」と書いた。その後 queue が
  空いたため先送りにせず実行した。実行手順として起きたことをそのまま記録する。

## 次の一手差分

### 完了

- [T-2161] 変異 matrix を着地 tip に対して走らせた。baseline 緑、9 件完走、
  単一理由の検出 4 件、冗長 1 件、過剰決定 3 件、生存 1 件。
  remaining: none
  base: 487db8abb007c6952e27d6d2fe1786cafe11568747b0400b2f5b117870254917

### 新規

- {{T:preflight-binding-redundancy}} **P3・新規・裁定待ち**: `_preflight_workload_profile` の
  launch binding 検査は `_trial_launch_admission` の registry 経路と同じ P/C/H 検査を重ねており、
  削っても受理集合が変わらない (変異 M2 が生存)。多重防壁として残すか、preflight を薄くして
  一本化するかを決める。残すなら「受理集合を変えない防壁」であることを明記し、
  変異の単独証拠から外す扱いを固定する。
- {{T:contract-loader-mutation-masking}} **P3・新規**: `CONTRACT_LOADER_RELATIVE_PATHS` の
  24 file は blob が HEAD へ束縛されるため、変異 harness がこれらの file へ注入すると
  contract-loader drift が広く発火し、単一理由の証拠を作れない (本 wave で `loop.py` へ
  3 件注入し、いずれも 61〜62 node が落ちた)。同型が他 file でも起きるかを確かめ、
  起きるなら変異の当て方か drift 検査の扱いを決める。
