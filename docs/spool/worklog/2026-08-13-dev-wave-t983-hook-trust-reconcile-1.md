---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t983-hook-trust-reconcile
seq: 1
title: [T-983] は起票の 2 時間後に別 wave が実装し land 済みだったと実測で判明した — scope 4 点すべてが着地済みで実装差分ゼロ、[T-815] の rc=0 基準も回復を確認 (docs のみ、branch worktree-dev-wave-t983-hook-trust-reconcile)
---

## 本文

- **本 wave は投入された scope を 1 行も実装しなかった。** 段 1 brief 前の前提実測 (`DW-S01`) で、
  scope 4 点すべてが main tip `adf7997f` に既に着地していると確定したため、docs のみの突合せ記録へ
  切り替えた。これは F35 の恒久対応 1 (「既実行なら stale と裁定し依存項目を繰り上げる」) の経路である。
- **照合は一次資料で行った** (裁定要約ではなく実コード・実 spec・archive 本文)。
  - (1) probe argv の flag と supersede の記録 = `tools/check_codex_hooks.py` の
    `build_codex_argv` が `TRUST_BYPASS_FLAG` を持ち、`validate_production_argv` が
    「trust bypass は option 領域に exact 1 件、sandbox bypass は prompt 内 substring も禁止」の形。
    supersede は D326 に記録済み。
  - (2) launcher の flag + 起動前検証 = `tools/codex_worker_launch.py` の
    `_require_attempt_hook_installation` が retry ごとに `Popen` の直前で走り、赤なら `LaunchError`。
    flag 無し起動への fallback 経路は存在しない。
  - (3) trust 模型の記載 = `hooks/README.md`「Codex hook trust と自動化時の bypass 契約」節に
    パス単位の永続化・worktree / 使い捨て clone への非継承・ephemeral でも信頼済みパスなら発火、が既載。
  - (4) 変異事前登録 = 実施 wave の spec に **M1 = launcher の起動前検証を削除する fail-open 形**、
    **M2 = probe から flag を外す wave 前の形への revert**、M3 = flag を argv 全体で数える形 が
    登録されており **3/3 KILLED**。要求された 2 形はいずれも登録済みだった。
- **実施したのは別 wave** (2026-08-12 14:52 JST の実装 commit、branch `worktree-dev-wave-t-codex-hook-trust`、
  記録はアーカイブ済み worklog エントリ (476))。bytes pin の残穴はその後 [T-905] の commit で追補済み。
  **起票資料は 12:56 執筆で、実装はその約 2 時間後に着地している。**
- **完了基準を実測した。** main tip `adf7997f` (submodule 同期済み) で
  `python3 tools/check_codex_hooks.py` → **rc=0** (codex-cli 0.147.0、2026-08-13 01:00 JST)。
  出力は `OK: Codex PreToolUse live gate (apply_patch + Bash; allowed + protected)` の 1 行。
  [T-815] が [T-983] へ移管していた rc=0 基準はこれで回復した。
- **運用制約「修正まで codex-only dev-wave は投入しない」は解除条件を満たした。** 条件だった修正は
  着地済みで、live gate も rc=0。以後 codex-only dev-wave の投入を止める根拠はない。
- **scope 文言と実体の対応を 1 件訂正する。** 投入 scope は launcher を `tools/dev_wave_codex.py` と
  名指すが、codex の argv を組むのは `tools/codex_worker_launch.py` であり、前者は後者への
  thin dispatcher である。着地実装は正しい側に入っている。起票資料の名指しが不正確だった。
- **重複編集の検査 (投入時の指示分) は 0 件。** main tip `adf7997f` 以降および稼働中の worktree 8 本の
  未 land 差分に、`hooks/` / `tools/dev_wave_codex.py` / `tools/check_codex_hooks.py` /
  `docs/decisions.md` を触るものは無かった。scope の切り直しは重複ではなく既着地を理由に行った。
- **敵対レビュー 2 本と変異 matrix は実施していない。** 投入裁定は「防壁変更につき敵対レビュー 2 本」を
  求めていたが、本 wave の実装差分はゼロで防壁を 1 bit も変えていない。変異 matrix の免除は
  `DW-S04` の「実装差分ゼロの wave」条項による。
- **受入全走は免除せず実走した。実測 = 1 failed / 10239 passed / 65 skipped、130.52 秒**
  (2026-08-13 01:13 JST、tip `538af3a5` / main `adf7997f`)。**赤 1 件は main 由来の既知赤**で、
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` が
  `PreregistrationError: [octopus-merge] d1de13ad` を送出したもの。`d1de13ad` は親 4 つの merge で
  `s8c_preregistration.py` が親 3 つ以上を拒否するため、**履歴に焼き付いた決定的な赤**であり
  再走では消えない。本 wave の差分は `docs/spool/` の fragment 2 本だけで、この検査が読む git 履歴に
  影響しないことを差分一覧で確認した。**ユーザー裁定 (2026-08-13、本 wave へ直接): 既知赤として land
  してよい。** 記録後に main `01487bb4` を取り込み、同じ受入を merge 後の tip で再走してから land した
  (再走の値は本 fragment より後に確定するため、ここには書かない — 実測値は上の 1 走のもの)。
- **同型の再発を台帳へ挙げた** (F35 の再発として記録)。
  起票側 (`/rulings`) に既決照合の防壁が無いという F35 の既知の穴が、そのまま 2 度目を生んだ。
- **段 8 自己改善 = 候補 1 件、routing 先は failures のみ。** 候補は「裁定の起票から wave 投入までの
  時間差で、別 wave が同じ scope を land しうる」。dev-wave 側は `DW-S01` の前提実測が実際に本件を
  止めており欠落は無いため、入口・`docs/dev-wave/` の reference はいずれも編集しない。起票側
  (`/rulings`) の照合義務は F35 が既に「byte 予算の都合で書く場所が無く独立審査へ回した」と
  記録済みであり、本 wave は予算に触れない (自己改善契約の「予算の変更は実装せず裁定パッケージへ」)。

## 次の一手差分

### 完了

- [T-815] 対話 Codex での hook 信頼承認は 2026-08-12 に完了し、[T-983] へ移管していた完了基準
  `check_codex_hooks.py` rc=0 を 2026-08-13 01:00 JST に main tip `adf7997f` で実測した
  (codex-cli 0.147.0)。既裁定 (1)(2)(3) は受容と再訪条件の記録であり未了作業を含まない。
  remaining: none
  base: 9be579719b6a3b6b76191ae3a3ea85ebf5915babada1eb715cec143e122106d4
- [T-983] scope 4 点 (checker の probe argv、launcher の flag + fail-closed 起動前検証、
  `hooks/README.md` の trust 模型、fail-open 形と wave 前の形への revert を含む変異事前登録) は
  すべて 2026-08-12 の別 wave で着地済みと実測で確定した。本 wave の実装差分はゼロで、
  記録の突合せだけを行った。運用制約「修正まで codex-only dev-wave は投入しない」も解除条件を満たす。
  remaining: none
  base: 525f48afbc87a04c24f1fbc846f960aca8a6611c8bc4659c023403ad7e85981e
