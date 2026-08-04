---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t422-campaign-external-root
seq: 2
---

## {{D:exploration-external-output-root}}. exploration campaign の実行先を env seam で worktree 外へ出す

**決定:** exploration campaign の base output root を環境変数
`IZANAGI_EXPLORATION_OUTPUT_ROOT` で差し替え可能にする (F98 択 (iii) の 2026-08-04 ユーザー裁定の
実装)。契約は次のとおり。

- 優先順位: 非空の明示 `output_root` 引数 > env > repo 既定 (`repo_output_root()`)。
  env 未設定時の既定挙動・path 文字列は従来と byte 同一。official `CampaignLayout` と
  `output/env/` は env を参照しない
- env 値の admission (env 経路のみ): 非空・絶対 path・`..` component なし・resolve 前後で
  固定 suffix (`exploration/campaigns`, `exploration/autonomous-trials`) を含む既存 component の
  lstat walk (symlink / 非 directory 拒否)・resolved root の祖先に `.git` なし
  (main checkout・兄弟 worktree・他 repo を排除)・既存 base は実効 uid 所有
- 解決値は process singleton (`sys.__dict__` + `threading.Lock`、module 二重 identity
  非依存) に pin し、以後の env 変化・削除・不一致は fail-closed で `ValueError`。
  8c trial の `--run-root` 省略既定も同じ resolver を通す (`legacy_base` 引数で env 未設定時の
  旧既定 `ROOT/output` を byte 温存)
- materialization admission は layout の明示 method (`_admit_materialization`) —
  official は no-op、exploration は `.claude/worktrees` / `.codex/worktrees` container 配下への
  作成を拒否する。`ensure()`、WAL の 4 経路 (append / write_lock / acquire_lock_atomic /
  repair_truncated_tail)、`ensure_exploration_namespace()`、8c run_root materialize が同じ gate を
  通る。env 未設定のまま wave worktree 内で campaign を実走しようとすると dirt 生成前に
  fail-fast する (F98 の再発を構造的に防ぐ)
- 機械固有の実 path は shared code・test・docs に置かず、job script / runbook (環境正本) だけが
  持つ。外部 root は repo hooks の campaign tree 防護の外にある使い捨て領域であり、certified
  材料・proof chain 素材を置かない (proof chain へ入る材料は従来どおり repo 内 official 経路のみ)

**理由:**
- F98 の両防壁 (guard の proof chain 保護と land の完全 clean 要求) はどちらも単体で正しく、
  実測でも guard は repo 相対判定・durable-root admission は exploration 非接触のため、
  実行先の外部化だけが両防壁を 1 つも緩めずに交差を解消する
- env seam を layout factory 1 箇所に置くと、既存 driver 19 呼び出し箇所と使い捨て driver が
  無改変で外部化される (per-driver CLI 追加は漏れ面が広い)
- process pin と container gate は、敵対相談・レビューが実測根拠付きで示した root 分裂
  (module 二重 identity・thread 競合・プロセス再入) と設定漏れ (env 未 export の wave 実走) を
  fail-closed に倒す

**却下した選択肢:**
- F98 択 (i) land の clean 要求緩和・択 (ii) guard の worktree carve-out — 防壁を緩めるため
  ユーザー裁定で不採用
- per-driver CLI flag の全追加 — 呼び出し面が広く漏れが構造的に残る
- worktree 検出による自動 redirect — 暗黙の機械結合で、テスト・既定挙動の byte 互換を壊す
- WAL gate の official への無差別適用 (第 1 巡 fix) — 裁定射程 (exploration family のみ) の外で
  official の受理集合を縮小する回帰と再判定し、是正した
