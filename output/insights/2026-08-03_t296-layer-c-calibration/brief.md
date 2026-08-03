# 段 1 brief — [T-296] Pegasus 層 C 量 (環境束縛) の取得

基準: main `1a3604b` / branch `worktree-dev-wave-t296-layer-c-calibration` (clean, submodule init 済み)

## 起票時の T-296 本文 (worklog (103) が実体)

> Pegasus での**層 C 量 (環境束縛) の取得が未起票**。登録済み calibration は certification の 1 点のみで、
> rr80 / rr20 の較正点と between-run noise floor が無い。roadmap §5 の 3 層分類で層 A / B は転移するので
> 焼き直さないが、層 C は主張を立てる env で取得が要る。[T-277] が Pegasus 計測パスを開いた直後が最短の着手点

## 段 1 前提実測 (DW-S01「承認済み裁定の前提を実測する」) — 2 件とも覆った

**F-1. rr80/rr20 の較正点は設計上取得不要。** `docs/phase3-8b-descriptor-design.md:6-10` の
2026-07-16 ユーザー承認記録は、H1=`rratio=80` / H2=`rratio=20` を採り H3 (skew 変更) / H4 (rmw 変更) を
落とした理由を「校正動作点 (skew=0.9, rmw=0 で確定した records/threads) の前提が変わり、descriptor 効果と
校正のずれが交絡する」と書く。H1/H2 は `skew=0.9, rmw=0, 1m records, 48 threads` (同 :115-116) で、
rr50 で確定した校正動作点を**継承する設計**である。

**F-2. rr80/rr20 で calibration を回すと holdout の未既知性を壊す。**
`output/s8b-freeze/holdout_freeze.json` は `frozen_at_head=2e20d441`, `confirmed_by=thawk105`,
`confirmed_at=2026-07-16`、`match_convention` = *file-level conjunction (rratio/skew/rmw の三軸正規表現
すべてに一致したファイルを 1 hit)*。本日の実測: rr80 = 2 行 hit / rr20 = 2 行 hit で、どちらも
holdout_freeze.json 自身の宣言と正規表現のみ。**実測値は repo に 1 件も無い。**
positive control rr50 = 316 行 hit (>0) で検索式は生きている。

**F-3. between-run floor は「未起票」ではなく既起票 [T-088] の段階 3・4 待ち。**
- 事前登録 protocol は実在: `output/s8b-freeze/floor_protocol.json`
  (`env_tag=pegasus`, `n_sessions=8`, `reps=5`, `extime_s=5`, `schedule_algorithm=round-permutation/v2`,
  `session_cv_max=0.10`, `cell_cv_max=0.15`, `contract_sha256=e576e9cd...`)
- driver も実在: `orchestrator/campaign/s8b_floor_campaign.py`
- 人間手番は**済**: protocol 実凍結をユーザーが 2026-07-24 に実行 (`c8cbd17`)、予測封印実走と
  [T-011] §5-(viii) 受諾も 2026-07-24 完了 (`docs/phase3.md:116`)
- 残 gate = official guard 解禁 = **[T-088]** (設計 = D86、PBS wrapper = D87、段階 1 は 2026-07-28 に
  実機閉鎖 = job `873225` rc=2)。**未着手 = 段階 3・4 (単一 admission predicate + CLI rc 翻訳)
  → 実行 revision 束縛** (`docs/phase3.md:118-121`)
- 実機拒否の一次資料: `output/env/pegasus/floor/job-staging/0:873225.nqsv/floor-driver.stdout`
  = `{"status": "refused", "reason": "official mode は承認束縛方式が §8 未裁定のため現時点で拒否する (pilot のみ実行可)"}`
  実装 = `orchestrator/campaign/s8b_floor_campaign.py:202` (core) と `:3441` (CLI) の二重拒否
- **優先度は 2026-07-27 ユーザー裁定 (2) で意図的に後退済み**「8b selector 側の残作業 (床値実測の
  前提整備・oracle 実走・認証機構の拡張) の優先度を下げる。床値実測は他候補にも要る測定土台なので
  廃止ではなく順序の後退」(`docs/phase3.md`)

**F-4 (派生・未起票).** `orchestrator/campaign/screening_driver.py:30-31` の
`load_between_run_floor` は既定 dir を `output/env/linux-baremetal/calibration` に**固定**する。
Pegasus 側に `between_run_noise_*.json` は 0 件。sweep driver 群 (`backoff_sweep.py:173`,
`s6_sort_sweep.py:601`, `s8a_trigger_sweep.py:675`) は `--floor-dir` 相当の override を持つが、
**渡さなければ linux-baremetal の floor が黙って適用される** (D59 の env-tag 束縛違反が fail-open)。
ただし発火する計測 ID は現存しない (`output/env/pegasus/` に sweep 出力なし)。

## scope (親の provisional 裁定 — 攻撃対象)

- **(P1) 本 wave は実装せず docs-only とし、T-296 を訂正して依存へ繋ぎ替える。** 取得 (calibration 実走・
  floor 実走) は行わない。根拠 = F-1/F-2/F-3。段 4 で「実装しない」と裁定し `4→7→8→9` を辿る
- **(P2) rr80/rr20 の較正点取得は恒久に却下し、その理由 (設計継承 + holdout 汚染) を台帳へ残す。**
- **(P3) F-4 は起票のみとし本 wave では直さない。** DW-G04 = 発火条件を満たす計測 ID を書けないため。
  なお [T-331] (兄弟 driver の COMPUTE 閉鎖、裁定済み択 (a)) が実装されれば同じ穴が塞がる可能性がある
- **(P4) 一般用途 (8b 非依存) の Pegasus between-run floor を取るかはユーザー裁定へ返す。**
  roadmap §5 は正本環境を `linux-baremetal` とし、active env は worklog 正本。Pegasus が主張 env に
  なるかが未確定なまま取ると層 C の空振りになる

## 不変条件

- holdout の未既知性を本 wave で壊さない (rr80/rr20 の実測値を repo へ入れない)
- 2026-07-27 ユーザー裁定 (2) の優先度後退を親が独断で覆さない
- 凍結成果物 (`holdout_freeze.json` / `floor_protocol.json`) の bytes を変えない
- [T-088] / [T-331] の scope を本 wave が奪わない

## 成果物の形と DW-G05 (実装しない場合の成果物影響)

成果物 = worklog fragment (T-296 の訂正 + F-4 の新規起票) + 裁定パッケージ (insights)。
- F-1/F-2 を書かない場合: 後続 wave が rr80/rr20 calibration を善意で回し、holdout の未既知性
  (現在 hit 0) が壊れる → 8b selector 実験の主張が成立しなくなる
- F-3 を書かない場合: T-296 が独立タスクとして再着手され、[T-088] 段階 3・4 の実装を重複して行う
- F-4 を書かない場合: Pegasus で sweep を回した際に linux-baremetal の floor が compare の丸め閾値に
  黙って適用され、selected/tie の判定が別 env の noise で決まる

## 分割方針

docs-only・子ゼロを既定 (DW-C00 軽量版)。ただし本 wave は既起票の前提を覆すため、段 3 の敵対レンズを
1 本だけ立てて brief の事実主張を攻撃させる。段 2 の実装プランは実装が無いため作らない (逸脱を記録する)。
