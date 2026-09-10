# 段 1 brief — [T-470] + [T-327] U-1/U-4/U-5 配線 wave (+ [T-468])

対象 = 起動 (launch admission) と受入 (post-run acceptance) の必須配線。裁定は
docs/worklog.md (209) 行 360-392 / 628-642、一次資料は
output/insights/2026-08-05_t327-prereg-activation/s4-ruling.md §2。**U-4 が最優先要件**。

## scope (各行末が DW-G05 の成果物影響)

1. **U-4 (最優先)**: 未登録 trial_id の実走を既定で拒否し、holdout 束縛 workload
   (rr80/rr20) は登録なしでは無条件に拒否する。→ 実装しないと H1/H2 の事前観測 run が
   台帳に残らないまま §5 を結果適合に記入でき、certified 選択の holdout 未既知性が偽になる。
2. **U-1**: `effective_at(C)` の sealed capability を launch admission と acceptance の
   必須引数にする。→ 実装しないと未発効の事前登録下で formal trial が走り、その report が
   certified 選択の根拠に混入する。
3. **U-5 + T-470**: canonical authority、同一 trial の一回性 (restart 禁止)、acceptance が
   **receipt bytes を tracked artifact として発行**し、下流 (層3 生成・certified 選択) が
   rc でなく receipt bytes を要求して無ければ拒否する。→ 実装しないと best-of-N の manifest
   差し替えで certified 選択の値が入れ替わり、レポートの参照が実走と乖離する。
4. **T-468**: registry の canonical authority を [T-295] approval record + registry commit に
   束縛する。→ 実装しないと同一 trial 集合に対し複数 registry が並立し、受理集合が非一意になる。

## 不変条件

- **12 述語の SATISFIED は 0 件のまま** (s4-ruling §4-3、test_s8c_preregistration_invariant.py
  `test_candidate_is_not_effective_and_has_zero_satisfied_predicates`)。本 wave の配線は
  UNSATISFIED → EVIDENCE_UNDEFINED までしか動かさない。SATISFIED を作るなら negative control を同時に足す。
- 正しさゲートを緩めない。gate 追加は fail-closed、既存 gate の緩和は不採用。
- 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・commit のみ。
- 計測は行わない (静的層 + pytest のみ、login node)。

## 段 1 前提実測 (承認済み裁定の前提を覆しうる新事実)

- **N1**: `python3 -m orchestrator.campaign.s8c_preregistration check` は 12 述語すべてを
  `ERROR: evaluator-exception` として返す。原因は二重 import — `-m` で core が `__main__` として
  読まれ、evidence module の `from . import s8c_preregistration as core` が別 class を持つため
  `_normalize_predicate_results` の `isinstance` が落ちる。API 直呼びでは正常 (C01 は
  EVIDENCE_UNDEFINED)。fail-closed 側なので誤受理はないが、**U-1 の配線先に CLI を選ぶと恒久的に
  閉じたままになる**。→ 配線は API (`effective_at`) 経由に限定する。CLI 修復の要否は段 4 で裁定。
- **N2**: evidence contract (`s8c_preregistration_evidence_contract.v1.json`) が本 wave の
  consumer 名を既に規定している — `trial_registry` に `admit_preregistration` (C08、
  `effective_at(prereg_commit) -> run start`)、`accept_trial` (C02/03/08/09/10)、
  `bind_trial_arm` (C02)、`load_manifest` (C03)、`forbid_trial_restart` (C04)、
  `p3_autonomous_workload_trial` に `mark_experiment_indeterminate` (C04)。**いずれも未実装**。
- **N3**: holdout workload `rr80` / `rr20` は `WORKLOADS` に存在しない (ycsb-a/b/c のみ)。
  束縛表は `trial_registry.HOLDOUT_BINDINGS` と `s8b_holdout_freeze` に実在するので、U-4 の gate は
  WORKLOADS でなく束縛表を入力にすれば今日から発火可能 (DW-G04 充足)。
- **N4**: `docs/phase3-s8c-autonomous-trial-runbook.md` §3.1/3.2/3.3 の正規手順は manifest 無しの
  探索実走である。U-4 を素朴な全面禁止にすると正規手順が壊れる。
- **N5**: acceptance は stdout に JSON を print するだけで tracked receipt を書かない。
  `AcceptanceSummary.certifying` は常に False (T-470 の「rc でなく receipt bytes」の前提は成立)。
- **N6**: registry path `output/s8c-trial-registry/registry.jsonl` は未作成、FROZEN_MANIFEST 等の
  bytes pin なし (DW-O09 の path 検索と key 側検索を実施、hit 0)。

## 既存被覆と純増検出力 (性質で検索)

- 「未登録 ID の実走を止める」性質: 既存は `assert_unregistered_for_exploratory` のみで、
  **登録済み ID が manifest 無しで走る場合しか拒否しない**。未登録 ID は素通り。純増 = 未登録側の拒否。
- 「発効を起動の必要条件にする」性質: 既存被覆ゼロ (`effective_at` の production consumer は皆無)。
- 「同一 trial の再走を止める」性質: 既存被覆ゼロ。
- 「下流が receipt bytes を要求する」性質: 既存被覆ゼロ (層3 生成は campaign dir だけを見る)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** U-4 は二層で実装する: (i) 要求 workload が holdout 束縛集合と交わる run は登録済み
  manifest binding + 発効を**無条件必須**にする (逃げ道なし)、(ii) manifest 無し launch は
  既定で拒否し、明示 opt-in flag を渡したときだけ許して report/journal に non-certifying を刻む。
  既定拒否で裁定文の字義 (未登録 ID の実走拒否) を満たし、(i) が opt-in 経路から H1/H2 を構造的に
  切り離す。N4 の正規手順は flag 追記で存続する。
- **(P2)** 新設関数名は N2 の contract 名に揃える (`admit_preregistration` / `accept_trial` /
  `forbid_trial_restart` / `bind_trial_arm`)。後続の述語 green 化段での改名を避ける。
- **(P3)** receipt は `output/s8c-trial-registry/receipts/<manifest_sha256>.json` に tracked で
  書き、下流は receipt bytes の再検証 (manifest hash・registry blob・report/journal SHA) を必須にする。
- **(P4)** T-468 の canonical authority は本 wave では registry commit の一意性検査までとし、
  [T-295] approval record への実結線は approval record の実在が確認できた場合だけ行う (DW-G04)。

## 成果物の形

`orchestrator/campaign/trial_registry.py` (admission/acceptance/receipt)、
`orchestrator/campaign/p3_autonomous_workload_trial.py` (launch 側配線)、下流 consumer 1 本、
対応 test、runbook 追記、spool fragment。commit は wave branch のみ、push しない。

## 並列分割方針

段 5 は所有素集合で 3 単位: A = U-4 gate (trial_registry + launcher)、
B = U-1 発効配線 + U-5 一回性、C = receipt 発行と下流消費 (T-470 + T-468)。
依存は A → B → C だが所有が重なるため直列 1 子 + 段 6 で敵対レビュー 2 本を並列。
