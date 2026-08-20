---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: t1371-official-run-root
seq: 1
---

## {{D:official-output-root-forced-external}}. official campaign の出力 root を repo 外へ強制し、D158 の「official は env を参照しない」記述の該当部分を supersede する

**決定:** `declared_use_class="official"` の campaign 出力 root 解決
(`resolve_campaign_output_root`) を fail-closed 化する。新設 env `IZANAGI_OFFICIAL_OUTPUT_ROOT`
または呼び手の明示 `output_root` のいずれかを要求し、いずれも未指定なら repo 内へ暗黙に
倒れず例外を送出する。explicit 引数も含め毎回、exploration と同水準の外部性検証
(絶対 path 必須・`..` 拒否・symlink 拒否・git 祖先拒否・uid 所有・worktree container 拒否) を
通す。`s8b_oracle_driver.py` の holdout 実走 CLI (`run-block`) は `--output-root` 既定値を
repo 内 fallback から `None` へ変更し、central resolver の拒否を `status="refused"` gate
decision へ変換する。解決済み root 専用の `DurableRootPolicy` を `run_block()` へ注入し、
`default_durable_root_policy()` (repo `output/` のみ approved) 自体は変更しない。
exploration 分岐の既存挙動 (env 未設定時は repo 内 legacy fallback を維持、worktree
container 拒否は resolve 時でなく `.ensure()` 時) は byte-compatible に温存する。

**理由:**
- 正式 holdout run が書く `campaign.lock` は `ycsb_rratio`/`ycsb_zipf_skew`/`ycsb_rmw` を
  同一ファイルに並べる compact canonical JSON であり、`output/campaigns/`・
  `output/exploration/` いずれも `.gitignore` 対象外のため、repo scan の untracked
  非 ignore file 列挙に conjunction hit として拾われる。RatifiedFreeze v2 発効後の
  全 repo scan (`launch_validate`) 契約と自己矛盾する。
- ユーザー裁定 (2026-08-20): 択(a) 正式 run の run root/campaign root を repo 外へ強制する
  採用。一次資料は `docs/archive/worklog-phase3-0818-658.md:618-631` (entry 658)。

**却下した選択肢:**
- (b) 凍結の unknownness 主張を「凍結時点の歴史的記録」と明示し事後 scan を要求しない —
  検出側の緩和であり、生成側の根本原因を放置する。ユーザー裁定で不採用。
- (c) 明示的な exempt path を裁定する — 択一裁定で明示的に不採用。将来の同型 producer が
  無防備なまま残る。
- `default_durable_root_policy()` を env 連動にして任意の外部 path を自動承認する変更 —
  既存 policy を弱め、exploration や他の durable writer へ波及する。

**D158 との関係:** D158 は「official `CampaignLayout` と `output/env/` は env を参照しない」と
記す。本 D はこのうち **official `CampaignLayout` に関する部分だけ** を supersede する —
official は `IZANAGI_OFFICIAL_OUTPUT_ROOT` を参照するようになった。`output/env/`
(`env_scope_dir()`) 自体は本 wave で変更しておらず、D158 のこの部分および
materialization admission (`_admit_materialization`、official=no-op・exploration=worktree
container 拒否) に関する記述は従来どおり有効である。
