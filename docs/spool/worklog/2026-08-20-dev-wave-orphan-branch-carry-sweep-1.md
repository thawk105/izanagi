---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-orphan-branch-carry-sweep
seq: 1
title: 取り残しbranch5本の吸収を対象fileの差分で検証し、worklog carry [T-1419]/[T-1183]/[T-949] を実体に合わせて閉じた (docsのみ、branch worktree-dev-wave-orphan-branch-carry-sweep)
---

## 本文

- **`git branch --no-merged main` の5本 (roadmap-workload-hint / rulings-20260818-floor-measurement /
  rulings-20260818-second / workload-policy-hint-impl-unitB / -unitC、いずれも非占有) を対象file
  だけの差分で検証した。** 全repo diffは無関係な並行waveの進行で膨れるため使わず、
  `git diff <branch> main -- <対象file>` と `docs/spool/FOLDED.md` のhash照合を用いた。
  5本とも吸収済みを確認した: roadmap-workload-hint / unitB / unitC は squash commit `627c5019`
  (docs/roadmap.md のD568文言・orchestrator/campaign/{s8b_descriptor,p3_s4_loop,layer3_report}.py
  へのpolicy_hint配線・対応テストが現main と一致、unitB/unitCの残差分は無関係な後続waveの上書きの
  みで欠落なし)。rulings-20260818-floor-measurement / -second はFOLDED.md receipt
  (content_sha256一致) と fold commit `c79c88d8`/`4f5bb9ec` がmainの祖先であることで確認した
  (元fragment fileの不在はfold後の正常な削除)。unitB/unitCは相互に完全同一内容 (duplicate branch)。
- **[T-1419] は実装・テストとも実在を確認した。** s8b_descriptor.py の型検査、
  p3_s4_loop.py の exact str 契約、layer3_report.py の記録配線、test_s8b_descriptor.py /
  test_layer3_report.py の専用テスト (test_policy_hint_is_omitted_when_absent 等5本) が揃っている。
  D568 の境界 (hole・勝ち筋は含めない) とも一致する。
- **[T-1183] は [T-1140]/[T-330] という別IDの下で同日中 (2026-08-16) に実装済みだった。**
  origin (entry578) が指す D435 は実際には正例要件 (点4) だけの根拠で、3分割変異 (leaf単体/
  wrapperを通らない呼び手/実運用end-to-end) の方は D436 が定めている — origin 文言はこの2件を
  1つの `(D435)` 引用へ圧縮していた。commit `6eb77ef9` (campaign_claim.py へ protocol_digest/
  boot_id/proc_starttime/`_owner_state` を実装) と `52950716` (段7記録) が要件を完全に満たす:
  変異11件 (M01-M09=leaf単体、M10-M11=wrapperを通らない呼び手、M01/M05/M11由来の実subprocess
  end-to-end test) が全KILLED・SURVIVED 0、過剰拒否検出の正例8件 (POS-1〜8) も事前登録済み。
  現行 orchestrator/tests/test_campaign_claim.py (559行) で全項目を直接確認した。
  **D464/D435/D436いずれも実装済みで、追加実装は不要と判定する。**
- **[T-949] は当初裁定 (entry510「(a) cherry-pick -x」) とは異なる経路で解決していた。**
  対象branch `worktree-dev-wave-t657-t660-g2-activation` は、2026-08-17に
  「未着地11 commitを破棄しmainのreseal_protocol()で立て直す」という entry510 より後発の
  直接ユーザー指示 (所有衝突のため立て直し自体は不実装) により**削除済み**
  (`git rev-parse` で不在を確認)。破棄前に段3敵対レンズが名指しした2資産 ([T-660] 変異台帳と
  2026-08-09 裁定 package.md) だけを `output/insights/2026-08-17_t657-activation-rebuild/
  preserved-t657-t660/` へ保全した (commit `505accdb`)。元branchが持っていた残り約18ファイルの
  insightsは保全されず、branch自体も無く再取得できない。archive worklog 6エントリ
  (0812-499/0809-351/0812-491/0810-359/0813-539-540/0817-634、いずれも凍結済み) が同branchの
  package.mdを「正本」と引用しているが、文言どおりの参照先は無くなっている
  (package.mdの内容自体は保全先で読める)。**「別waveが解決」は正しいが、解決の実体は当初の
  cherry-pick -x land ではなく、より後発かつ具体的なユーザー指示による branch 破棄と選択的資産
  保全である。**
- {{F:carry-stub-cross-id-drift}} — 3件とも、実装・解決が別ID・別waveのprovenanceでlandした
  ために carry stub が自動更新されず、当該branchのblob照合・commit `--grep` 検索・対象fileへの
  直接grepでしか発見できなかった。branch削除は本waveの scope外 (ユーザー裁定または
  cleanup-branchesスキルへ)。

## 次の一手差分

### 完了

- [T-1419] workload descriptor policy_hint の実装・テスト実在を確認し、carry を閉じた。
  remaining: none
  base: f0d9ad95834448825dfdf30483a3adbc8237df13467588f554ae0e9f3063e0a3

- [T-1183] campaign claim 排他の D464/D435/D436 要件が [T-1140]/[T-330] (`6eb77ef9`) の下で
  完全実装済みであることを確認し、追加実装なしで carry を閉じた。
  remaining: none
  base: 8b6d3985db44969078b5d9729e518b60aac6174bff65eed3e02764e33f90536c

- [T-949] 対象branchが2026-08-17の直接ユーザー指示で破棄され、資産2件のみ保全 (`505accdb`)
  済みであることを確認し、carry を閉じた。
  remaining: none
  base: 7ee6d18eba96fecb7a4d1f40dd9c4b37077fd86c6c5ebdb3937870b7297d3b1d
