---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2445-next-tasks-skill-relocation
seq: 1
title: [T-2445] [T-2680] next-tasks の Codex skill を repo 内 adapter へ移設し、共通自己改善契約の終端 pin と Codex Skill guard へ登録し、絶対 path を runbook へ移した (docs + checker + test、branch worktree-dev-wave-t2445-next-tasks-skill-relocation、変異 matrix = baseline PASSED・M1〜M6 KILLED・等価 M0 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「(1) Codex 側 `~/.agents/skills/next-tasks/` を repo 内 `.agents/skills/next-tasks/` へ移設
  (第 20 回 /rulings 項 37、byte 予算は既存 3 skill と同じ)、(2) D1890 (1) = `docs/skill-self-improvement.md` へ
  `.claude/commands/next-tasks.md` を登録、(3) D1890 (2) = 「本ファイル (repo 外)」を消し `/work/1/SFC/tanab/scripts/`
  の絶対 path 依存は runbook へ。候補生成ロジックの拡張・追加ガードレール・next-tasks 実行は含めない。docs / skill
  文書のみ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2445-next-tasks-skill-relocation/README.md`。設計判断は
  {{D:next-tasks-codex-adapter}}。docs commit `835a2dc33` / `3183ec132` (親、D744)、checker commit `e9a4efeae` /
  `988905881` (Codex author)。項 37 は wave 中に main で D2104 として fold された。
- **引数の前提「checker 側は登録済み」を段 1 で覆した。** それは command の予算・interface pin (entry 1352) で、
  D1890 (1) / T-2680 が言う終端 pin `REQUIRED_SELF_HEADINGS[3]` は 3 command のままだった。docs だけを当てた
  `check_docs.py` は孤児 H3 `next-tasks` の 1 件で赤 (実測) → checker/test への最小登録を Codex author で行い
  rc=0。「docs / skill 文書のみ」では裁定 2 件の中身を満たせないと段 4 で裁定した (段 3 レンズ A が 3 事実を追認)。
- **移設の形は薄い adapter (5,730 bytes)。** 旧 Codex 版 (13,255 bytes、2026-09-10 版) は D2051 決定 5 が上書きした
  「相談は 1 往復で終える」をまだ含んでいた。D2051 の Codex 起動時の対応付け (事実も選定判断も起動主体、Claude の
  見解は独立検査) は adapter の設計判断として新 D に記録。plan の「事実は Claude」案は段 3 レンズ B が反証。
- **旧 Codex 版だけにあった出力の義務 5 件** (投げ文の自己改善終端、CC 不採用の理由、既存 patch・OID・handoff の
  束ね、補助 artifact・検証済み単独行・handoff 記録、半角番号) は Codex overlay として adapter に保持。Claude 側
  command は拡張しない (scope 外、記録のみ)。
- 契約文書は 5,999 → 5,997 bytes に縮約して収め (上限 6,000 不変、`## routing` は byte 同一)、D782 の上限引き
  上げは発火しない。command は 26,903 → 26,950 bytes (上限 27,100 不変、絶対 path 0)。
- 段 6 レビュー A (受理集合) は実装本体 must-fix 0、変異 M5 の anchor 一意性を指摘 (spec は 3 行 anchor で既に
  1 件、閉じている)。レビュー B (意味保存) は must-fix 2 (adapter の編集禁止条件の曖昧さ、旧版 L59 の handoff 記録
  義務の欠落) → 親が adapter を直し、予算 5,460 → 5,732 の追従を fix 子へ。焦点再レビューは GO (全件 closed、
  nit: 負例 needle が汎用文言、`docs-fix.diff` の比較基点の説明ずれ)。
- 実走: `check_docs.py` rc=0。焦点走 7 file (test_check_docs + importer 3 + dev_waves_checker + growth_test_holds_contract
  + hold_inventory) は fix 前後とも 1245 passed / 8 skipped (計算ノード、40 秒)。全史 provenance 10,910 件・新規違反
  なし。変異 matrix (container worktree、`run_tests.py test_check_docs.py`、probe 8 request + 本走 8 request) は
  M0 (comment) SURVIVED、M1〜M6 KILLED で期待 node 完全一致、MISMATCH 0。M3〜M5 は新規 PIN + 専用負例の 2 node、
  M2 は skill 負例 4 node の専属 kill。M1 (H3 集合) と M6 (FILES 集合) は合成 fixture が checker 定数に追従する型で
  337 node の過剰決定 kill (PIN と H3 負例を含む)。
- 残存 (scope 外、記録のみ): Codex の skill 探索順 (repo `.agents/skills/` と `~/.agents/skills/` の優先) は未実測。
  land 成功後に親が `~/.agents/skills/next-tasks/` を `~/.agents/skills-retired/next-tasks-2026-09-17/` へ退避して
  二重化を解く (記録時点では未実施。退避時の sha256 は wave の最終報告と job dir handoff に残す)。
  `next_tasks_consult.sh claude` の CLI 疎通は未実測。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  check_docs 4 回、焦点走 2 本、変異 2 走、provenance full 1 本。受入全走は記録 commit 後の tip で 1 本投げ、結果は
  land の受領証が持つ (記録時点では未実施)。

## 次の一手差分

### 完了

- [T-2445] next-tasks の編集境界 (D1890 (1)(2)(3)) を反映し、Codex 側 skill を repo 内 `.agents/skills/next-tasks/`
  へ移設して checker に登録した。
  remaining: none
  base: 2112c9c3a259927968f884b390b2b91e6e9fa13256dc4758e80b5350b16a3072
- [T-2680] D1890 (1) の未反映を閉じた。`docs/skill-self-improvement.md` に next-tasks の発火 gate と `### next-tasks`
  終端を登録し、`tools/check_docs.py` の終端 pin `REQUIRED_SELF_HEADINGS[3]` に `next-tasks` を足した。
  remaining: none
  base: 4801c441f35c791ba5433d480a4e2fff03995d32d0085327ec862e63f711efa1
