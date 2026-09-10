# [T-422] 段 4 裁定 — plan v2

各所見の real/refuted・採否・scope。親が段 3 の根拠行を全点照合済み (B-1/A-5/B-5 は親の実測で確認)。

## 所見裁定

| # | 裁定 | 採否 | 内容 |
|---|---|---|---|
| A-1 suffix symlink | real | 採用 (bounded) | env 検証で base の既存 component + 固定 suffix (`exploration`, `exploration/campaigns`) を lstat walk し symlink を拒否。残余 TOCTOU は「job 専用 root 運用」を前提とする文書化された限界とする。capability 化は scope 外 (設計メモ) |
| A-2 受理集合が広すぎ | real | 採用 (bounded) | env root の検証に追加: (i) resolved root の祖先に `.git` があれば拒否 (main checkout・兄弟 worktree・他 repo を排除)、(ii) 既存 base directory は euid 所有必須。負例テスト追加。job 間の root 共有は runbook で job 専用を義務化 (identity への root 混入は scope 外・設計メモ) |
| A-3 防護の実質縮小 | real (観測) | blocker 不採用 / docs 採用 | 裁定前提どおり: 外部化されるのは使い捨て exploration runtime 出力で、certified 材料・proof chain は official 経路 (repo 内・admission 付き) のまま。ただし「外部 root は repo hook 防護外」を output/README.md に明記 (B-6 と統合)。promotion receipt は scope 外 (設計メモ)。scope を裁定 (iii) から戻す提案は、裁定時点で既知の事実 (guard の repo 相対性は F98 本文と brief 実測 3 に記録済み) に基づくため、承認済み裁定の停止条件 (未見の新事実) を満たさない — 不採用 |
| A-4 / B-4 root drift | real | 部分採用 | env 由来の解決値を process 内で pin し、以後の env 変化・解決値不一致は ValueError (fail-closed)。テスト専用 reset 関数を置き production は呼ばない。プロセス跨ぎ resume manifest は scope 外 (設計メモ + runbook に「再入時は同一 env を保証」) |
| A-5 cwd 要求 | real | 採用 | F98 テストは `_cwd(wave)` 内で `_verify_repository` → `_verify_wave_clean` を呼ぶ |
| B-1 8c run_root | real | 採用 | `--run-root` 省略 + env 設定時は `<base>/exploration/autonomous-trials/<trial-id>` を同じ resolver 経由で使う。env 未設定時は現行既定のまま |
| B-2 設定主体不在 | real | 部分採用 | fail-fast gate を新設 (下記署名)。qsub wrapper 新設・凍結済み smoke_job.sh の改変は scope 外 — T-420 再走 wave が runbook §8 チェックリスト (本 wave で追記) に従い export する |
| B-3 テスト代表性 | real | 採用 | 正例は fake evaluator の最小 `run_campaign()` を完走させ、外部側 marker + campaign.lock + WAL と worktree clean + `_verify_wave_clean` 例外なしを同時検査。RC_DIRT 対照は plain untracked file で固定 (campaign gate と独立) |
| B-5 sweep は対象外 | real | 採用 (明文化のみ) | 保証範囲は exploration family (D123) のみと worklog / docs に明記。official/sweep root の外部化は新タスク起票 (実装しない) |
| B-6 正本文書の齟齬 | real | 採用 | output/README.md と 8c runbook に抽象記述を追記 (機械固有 path なし) |

## 新設 gate の署名 (DW-S04 / DW-O13)

**G-worktree-container (fail-fast):** `ExplorationCampaignLayout.ensure()` (および 8c run_root の
materialization 直前) で、解決済み root の path component 列に `.claude/worktrees` または
`.codex/worktrees` の連続が含まれる場合 `ValueError`。
**通る正例:** (1) env=`/work/<job dir>/out` → `<env>/exploration/campaigns/<id>` は通る。
(2) main checkout (worktree container 外) の既定 root → 通る (現行互換)。
**入力の実在 (DW-O13):** 判定入力は `self.root` の path 文字列のみ (実在 field、二義なし)。
gate を factory/resolve 時でなく ensure 時に置く理由: 既定 root の path 文字列計算は無害で、
既存テスト (「既定が現在と文字列単位で同じ」) を wave worktree 内での受入実行でも壊さないため。

**env 検証 (resolve 時、env 経路のみ):** 非空・絶対 path・祖先に `.git` なし・既存 component
symlink なし (固定 suffix 含む)・既存 base は euid 所有。明示 output_root 引数の契約は不変。

## 変異事前登録 (B-057 / DW-M01)

各変異は単一理由赤 (検出テスト 1 本、同一入力を拒否する他層なし — resolver/ensure/trial main の
検査は相互に独立な入力面を持つ) をコードで確認済み。

| ID | 変異 (実装後の anchor で確定) | 期待 kill (赤くなるテスト) |
|---|---|---|
| M1 | resolver の env lookup を除去し常に repo 既定を返す | env 優先順位テスト |
| M2 | 優先順位を反転し env が明示引数に勝つ | 明示引数優先テスト |
| M3 | 空文字 env を「未設定」として黙って既定へ fallback | 不正値拒否テスト (空文字) |
| M4 | 祖先 `.git` 拒否を除去 | 不正値拒否テスト (repo 配下) |
| M5 | suffix symlink lstat walk を除去 | 不正値拒否テスト (symlink) |
| M6 | G-worktree-container を除去 | F98 負例テスト |
| M7 | 8c run_root の env 接続を除去し常に ROOT 既定 | 8c run_root テスト |

**正例 (過剰拒否検出):** 有効な外部 temp root で factory + ensure + 最小 run_campaign が緑。
env 未設定・通常 repo で既定 path 文字列が現行と同一。

## scope 外 (設計メモ → worklog 次の一手へ)

1. official/sweep launcher (s6_sort_sweep / s8a_trigger_sweep, official campaign_layout) の
   実行先外部化 — 新タスク起票
2. プロセス跨ぎ resume の root manifest 束縛 (B-4) — 新タスク起票
3. 外部 root の capability 化 / promotion receipt (A-1 残余 TOCTOU, A-3) — 設計メモ

## plan v2 = s2-plan.md + 本裁定の delta

s2-plan.md の骨子 (env 変数名 `IZANAGI_EXPLORATION_OUTPUT_ROOT`、優先順位、呼び出し元不変、
conftest autouse 隔離、docs 2 点) は維持。追加/変更:
- resolver に A-1/A-2 の検証と A-4 の process pin (+ テスト専用 reset) を追加
- `ensure()` に G-worktree-container を追加
- 8c `--run-root` 既定の env 接続 (B-1) + 同 gate
- F98 テストは B-3/A-5 の形 (最小 run_campaign 完走 + _cwd 内 _verify_wave_clean)
- docs は 4 点に拡大: orchestrator-design.md、pegasus-runbook §8、output/README.md、
  phase3-s8c-autonomous-trial-runbook.md (いずれも抽象記述のみ)
