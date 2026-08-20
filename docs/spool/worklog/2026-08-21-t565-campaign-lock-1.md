---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t565-campaign-lock
seq: 1
title: '[T-565] campaign単位advisory flockを実装した (コード+テスト、branch worktree-T-565-campaign-lock、変異matrix = baseline PASSED・2/2 KILLED・SURVIVED0・MISMATCH0)'
---

## 本文

- 一次資料は裁定確定文 `docs/archive/worklog-phase3-0806-267.md:339-345` [T-565]。「同一ホスト内のみ」
  という当時の前提は [T-1162] 実測2 (`dev-wave-jobs/rulings-inbox/2026-08-18-rulings-full8-19rulings.md:51-56`)
  で誤りと判明済み (cross-node flock は [T-361]/[T-402] で実測済み、`/work`・`/home` とも
  Lustre `flock` mount option を確認)。sanctioned cross-node probe の投入枠 (`FLOCK_LEG_ONLY_SUBMISSION_LIMIT`)
  は [T-402] で 1/1 消費済みのため、本waveでは新規cross-node実測をせず前提として使った。
- 段2 codex plan (`campaign.flock` を campaign root 内へ置く案) に対し、段3 敵対相談2レンズ
  (sol=正しさ境界、luna=scope・波及) が独立に収束する重大所見を発見した:
  `layer3_report.py`/`autonomous_trial_completeness.py` が campaign root 配下を exact-set 比較
  するため、campaign root 内に置くと既存campaignのresume時に偽のcompleteness fail-closeを招く。
  また `run_campaign()` は唯一のcampaign書き手ではなく (`screening_driver.py`/`guided.py`/
  `s1_direct_comparison.py`/`s8b_oracle_driver.py`が直接評価でbypassする)、この点は
  D528決定(9)の先例 (`run_campaign`を通らないproducerのgateは別裁定へ送る) と整合させ、
  本waveのscope外と裁定した (`campaign_lock`の保護対象は`run_campaign()`呼び出しに限定)。
- 段4裁定で設計変更: `campaign.flock`はcampaign root**外**の新設`output/campaign-locks/`
  (`sha256(realpath(layout.root))[:20]`で命名) に置く形へ変更した。`campaign_claim.py`の
  claimは「releaseが意図的に存在しない」設計 (同ファイルdocstringで確認) であり、
  `CampaignBusy`後のorphan claimへ追加のrelease機構は実装せず、既存の手動回収運用モデルに
  従うと裁定した (D528先例と同じく、条件を迂回する機構を作らないという方針を維持)。
- 段5実装 (codex role=author) → 段6敵対レビュー2本が、hash鍵のtest網羅性不足 (realpath正規化・
  桁数のいずれも変異退行を検出するテストが無い) を独立に指摘し、fix (test_campaign.py限定) で
  2テストを追加して解消した。
- **lock receipt (4シナリオ実測、`orchestrator/tests/test_campaign.py`)**:
  同一process再入 = `test_campaign_lock_reentry_rejected_in_same_process` PASSED
  (2回目のflock取得が`CampaignBusy`)。同一campaign並列 (拒否) =
  `test_campaign_lock_same_campaign_rejects_competing_process` PASSED (実subprocess、
  競合processが`CampaignBusy`)。別campaign並列 (許可) =
  `test_campaign_lock_different_campaigns_can_run_in_parallel` PASSED (2実subprocessが同時生存)。
  解放後再取得 = `test_campaign_lock_released_can_be_reacquired` PASSED。
  加えて lock pathがcampaign root外であること・symlink realpath正規化・hash鍵20桁の3テストも
  PASSED。**環境情報**: host=pegasus02、`site_policy.current_site()`=PEGASUS_LOGIN、
  `/work`・`/home`とも同一Lustre (`10.110.64.1@o2ib10...`)、mount option
  `rw,flock,user_xattr,lazystatfs,encrypt` (`localflock`でない) を`mount`コマンドで確認済み。
  cross-node保証の範囲は[T-361]/[T-402]が実測したhost pair・`/work`・`/home`に限られ、
  全host/kernelへの一般化ではないことを{{D:campaign-lock-scope}}へ明記した。
- 統合commit `06acc7fddde3044cb268e28786833deafca3416c` (5 file、AI-Agent 4行)。
  `orchestrator/campaign/loop.py`が`contract_loader_binding.py`の`CONTRACT_LOADER_RELATIVE_PATHS`
  に含まれるため、commit前は同ファイル依存テスト約37件 (identity/claim/attestation関連) が
  disk-vs-HEAD-blob drift で構造的に赤だった。commit後は`orchestrator/tests/test_campaign.py`
  350 passed・10 skipped・0 failedを確認した (既知の期待済み挙動、実装のバグではない)。
  `orchestrator/tests/test_s8b_oracle_driver.py`の29件失敗は、`run_campaign()`を経由しない
  direct-evaluate (段3レンズBが確認済み) かつ最終変更者が本waveと無関係な[T-1372]であることを
  `git log`で確認し、DW-O18に従い非帰属とした。
- 変異事前登録 (DW-M01) は`campaign_lock_path()`のhash鍵導出2点 (realpath正規化・桁数) を
  段4で候補登録し、段6 fix後に実測で確定した。`tools/mutation_worktree.py`で1回目は
  dispatch congestion由来の`orphan-hold`(reason=dispatch-runner-timeout) が2回発生し、
  `docs/dev-wave/mutation.md`ではなく実測手順 (qstat不在確認→scratch側`git checkout --`→
  clean/HEAD確認→hold+orphan-stop sidecar削除→`--resume`) で復旧した。結果:
  baseline PASSED (11 passed)、M2 (realpath→abspath) = KILLED
  (`test_campaign_lock_path_normalizes_symlink_realpath`のみ、期待一致)、M3 (hexdigest[:20]→[:4])
  = KILLED (`test_campaign_lock_path_hash_key_is_twenty_hex_chars`のみ、期待一致)。
  2/2 matches_expectation=true。spec = `/work/1/SFC/tanab/dev-wave-jobs/t565-campaign-lock/mutation-spec.json`
  (sha256 `542fdc8dbea05ed898209fcc1f213c0062398d50aa1e6d7684eb274e6c997d1c`)、結果は同
  ディレクトリ`mutation-out.json` (repo_head=`06acc7fddde3044cb268e28786833deafca3416c`)。
  M1 (errno tuple縮小) はLinux flock()がEACCESを発火させないため検出不能と判断し登録しなかった
  (bench_lockの既存パターンをそのまま継承、新規リスクではない)。

## 次の一手差分

### 完了

- [T-565] campaign単位advisory flockを実装し、4シナリオ実測・変異matrix・受入検査を完了した。
  remaining: none
  base: d280040e89e4ad94f083e3b3ee98860aae3c37847d1fed67fe9ba1bbb208bc9c
