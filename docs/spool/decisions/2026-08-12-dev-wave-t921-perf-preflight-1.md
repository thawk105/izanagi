---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t921-perf-preflight
seq: 1
---

## {{D:perf-preflight-pilot-scoped}}. perf preflight は pilot に閉じ、official の受理言語を 1 bit も変えない

**文脈.** 第 5 束のユーザー裁定 (branch `worktree-rulings6-20260812` の decisions fragment、
slug `perf-optional-measurement`。本 wave 時点で未 land のため実番号を書かない) が
「perf を測定の前提にしない。
あれば使い、なければ無しで測る。有無は環境タグへ記録、比較は同条件内」を確定し、T-921 の
preflight を「置く」と定めた。素直な実装は、測定条件 (perf の有無) を artifact へ記録し、
run_cmd の期待形をその記録から導出することである。

**問題.** run_cmd は 2 系統の consumer が独立に再導出して**完全一致**を要求する
(`s8b_floor_campaign._project_measure_run_cmd`、`s8b_ratified_freeze` の 3 matcher)。
perf 無し形を足すと、この防壁が「2 形のどちらでも通る」に退化しうる。
段 3 の敵対検証は「`available` は artifact 作者の自己申告であり、偽装すれば official verifier に
no-perf 形を受理させられる」という攻撃を具体化した。create-only は初回からの虚偽を防がない。

**決定.** **receipt の emit と perf 無し形の到達可能性を `mode == "pilot"` に限定する。**
official 経路は従来どおり perf あり形だけを期待し、`s8b_ratified_freeze.py` と
`s8b_holdout_freeze.py` は 1 行も変更しない。official mode で receipt が非 None または
`use_perf=False` になったら `CampaignAbort` で止める。

**根拠 (実測).** pilot artifact は official 検証系へ構造的に入れない。
`s8b_holdout_freeze._validate_floor_inputs` は `mode != "official"` と
`eligible_for_refreeze is not True` を拒否し、`s8b_ratified_freeze` は期待 result に
`"mode": "official"` を固定する。したがって pilot 限定にすれば、official の受理集合は
「広がらない」のではなく**変化しない**。自己申告で買えるものが存在しなくなる。

**却下した代案.** (a) receipt を official にも emit して verifier を拡張する — 自己申告に
受理集合を委ねる。(b) `env_tag` 文字列へ perf 有無を焼く — `contract_sha256` と machine pin に
束縛されており凍結契約の同一性が壊れる。(c) perf 不在時に測定を止める — ユーザー裁定に反する。

**副次の決定.**

- **判定は 3 値** (`available` / `unavailable` / `probe_error`)。timeout・予期しない OSError・
  signal 終了は `probe_error` として **abort** する。`rc != 0` と perf 不在は `unavailable`
  であって異常ではない (T-920 の実測が `perf stat` rc=2 である以上、rc≠0 を abort にすると
  裁定が開けた経路を再び閉じる)。
- **検出は実行で行う。** `shutil.which` 型の存在検査では足りない (perf は PATH に在って rc=2)。
  probe は runner と同じ event 列と `-o` 出力形を使い、行が揃えば値が `<not counted>` でも
  `available` とする (false negative を避ける)。
- **使う perf は PATH の literal `perf` だけ。** `policy.json` の `perf_candidates` は
  receipt へ evidence として記録するのみで選択に使わない。絶対 path を採るには run_cmd・
  toolchain binding・verifier の同時拡張が要り、F89 が未裁定である。
- **回収条件を機械強制する。** `floor_campaign.sh` は driver rc=0 の後に result.json を読み、
  全 holdout の床値が有限実数であることを要求する。欠損なら非 0 rc。
  「完走したのに床値ゼロ」を成功として記録する経路を塞ぐ。

**成果物影響.** 実装しなければ床値 (T-748 W-2) の実測値が 1 つも得られない。
official の受理集合・`eligible_for_refreeze`・certified 選択は本決定では変わらない。
