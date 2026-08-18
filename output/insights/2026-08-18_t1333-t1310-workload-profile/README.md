# [T-1333] / [T-1310] / [T-1349] — workload 表 entry を scale の単一権威にする

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` の末尾エントリと現行 phase doc である。
本 package は dev-wave `t1333-t1310-workload-profile` (branch
`worktree-dev-wave-t1333-t1310-workload-profile`、起点 main `a160f4aa`、2026-08-18 12:23〜) の
逐語凍結と裁定パッケージを保存する。

## 何をしたか

ユーザー裁定 (2026-08-18) の 3 件を実装した。

- **[T-1333] 形 1** — scale (records / threads) を workload 表の entry に持たせ、producer の
  3 sink (`_campaign_for` / `_perf_for` / `_descriptor_for`) と Layer-3 の campaign-chain 検査が
  **同じ entry から** descriptor を導出する。
- **[T-1349]** — arm resolver が読む `s8b_holdout_freeze.HOLDOUTS` と producer 側 profile が
  同一を指すことを assert する。
- **[T-1310] 択 (β)** — `load_legacy_freeze` の `legacy-v1` 源を暫定源として
  non-certifying と明記のうえ受理する。

## 裁定の前提が 2 点崩れた (ユーザー再裁定へ返す)

### R-01 — 正式 run は今日いかなる経路でも起動できない

択 (β) は「正式 scale の実測を開始できるようにする」ことを目的としていたが、
**producer 経由で正式 rr80 / rr20 run を起動する経路は存在しない**と実測で判明した。

- `trial_registry.admit_registered_launch` は `EffectivePreregistration` を要求する。
- `s8c_preregistration` の `effective` は **12 predicate 全部が SATISFIED** であることを要求する。
- 現 snapshot の SATISFIED は **0 件** (`test_s8c_preregistration_predicates.py` が
  `sum(SATISFIED) == 0` を assert している)。
- 未登録の探索経路は holdout workload を `u4-holdout-workload` で明示的に拒否する。

[T-1310] 正本の塞ぐ点 (3) は「manifest が無い」までを記録していたが、
**全 predicate SATISFIED という形の要求は記録されていない**。
C01 を UNSATISFIED のまま残す (β) の設計と正面から衝突する。

**択**: (a) 正式 non-certifying 専用の launch admission mode を新設する /
(b) 8c registered 経路を通さず oracle driver 側または手動で測る (ただし oracle も
`LaunchValidatedFreeze` → `RatifiedFreeze` を要求し v2 未発効で塞がる) /
(c) 択 (α) へ戻る。**親の推奨 = (a)** — (β) を選んだ意図を実際に実現するのは (a) だけである。

### R-02 — 正式 run は自分が書く artifact で repo scan の 0-hit を壊す (完全に新規)

正式 rr80 run が書く `campaign.lock` は compact canonical JSON で
`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw` を**同一ファイルに**並べる。
凍結文書自身の positive control が
`output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/campaign.lock` を
rratio=50 の conjunction hit として記録しており、実証済みの形である。
`output/exploration/` は `.gitignore` に無く、repo scan は untracked 非 ignore file も列挙する。

前 wave の敵対レンズは source / test / fixture / golden / docs までしか見ておらず、
**run 自身の生成物は射程外だった。未記録の新事実である。**

即時の赤にはならない (live の全 repo scan `launch_validate` は `RatifiedFreeze` を要求し
v2 未発効で到達不能)。しかし v2 発効時に起動を塞ぐ。

**択**: (a) 正式 run の run root / campaign root を repo 外へ強制する /
(b) 凍結の unknownness 主張を「凍結時点の歴史的記録」と明示して事後 scan を要求しない /
(c) 明示的な exempt path を裁定する。**親の推奨 = (a)**。

### R-03 — oracle driver が freeze 文書から別 scale を読む

`s8b_oracle_driver._perf_for_holdout` は freeze **文書**から `PerfConfig` を作り、
module 表とも producer entry とも束縛されていない。schema-valid な `records=2_000_000` を
入れると通過する。`DW-G03` (族一般化には独立 2 例) は producer + oracle の 2 例で満たすが、
oracle は本 wave の編集面外であり scope 拡張の裁定が要る。

## 実装しなかったもの (形 A)

正式 profile 専用の Layer-3 受理枝 — `search_config.workload_profile` key の追加、
正式 `pilot_scope`、正式 `spec_content` — を**実装しなかった**。R-01 により正式 run は
admission を通れず、置いても発火しないためである。`DW-G04` は発火条件を書けない
条件付き機能を実装せず設計メモへ送ると定め、[T-822] 第 6 回ユーザー裁定は
「空振りする検査を置いて保証があるように見せる方が、保証が無いことを明示するより悪い」と定める。

代わりに正式 selector を渡した経路は
`formal launch is not admissible: effective preregistration unavailable` で fail-closed に止める。
R-01 が解けた時点で 1 箇所を外せば通る形にしてある。

この形 A により、段 2 プランが予測した `test_trial_registry.py` 24 件を含む
40 件超の波及は大幅に縮んだ。

## 本 wave の主要な収穫 — repo の受入 fixture に矛盾が埋まっていた

新設した検査が、**wave 前から `orchestrator/tests/test_trial_registry.py` に埋まっていた
scale の矛盾を捕まえた。** 同じ registered holdout 試行の fixture が、

- descriptor: `"scale": {"records": 1_000_000, "threads": 48}` (封印された arm 権威)
- campaign `search_config`: `"records": 100_000`, `"threads": 4` (探索 scale)

という 2 つの矛盾する scale を持ち、**それが受入を通っていた**。
[T-1349] が警告した「descriptor と実 benchmark が食い違ったまま両方緑になる」状態の実物であり、
段 3 レンズ B の所見 B-01 が指摘した穴が fixture の中に実在していたことになる。

併せて、Layer-3 は従来 descriptor について `descriptor_schema` と `descriptor_sha256` の
**自己整合しか見ておらず**、`_perf_for` 単独の scale 変異は cell から不可視ですらなかった。
本 wave は実際に構築した `PerfConfig` の scale を cell へ残し、
Layer-3 が entry から独立再投影して descriptor・cell perf・campaign・entry の四者を照合する。

## 段 6 で親が差し戻した実装の形

- **恒真な照合**。段 5 実装が `_ = (records, threads) == (1_000_000, 48)` と
  **比較結果を捨てて**いた。C01 が sink 内の整数 literal の存在しか見ないことを利用して
  検査を通すだけの形であり、本 wave が最も避けるべきものだった。実際に `raise` する形へ直させた。
- **fail-closed の迂回**。段 5 実装は正式 entry を `WORKLOADS` へ入れたため、
  正式 selector を**渡さなければ**素通りした。実装自身の fixture がそれを実証していた。
  正式 entry を別表 `FORMAL_WORKLOADS` へ移し、単一 resolver を通す形へ直させた。
- **mutable alias**。正式 entry の `ycsb` が `HOLDOUTS` と同じ可変 dict を共有しており、
  一方の変更が module 表と arm resolver を同時に動かせた。deep copy で断った。

## 収録物

| path | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。実測 M1〜M9 を含む |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex `plan`) |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A — 凍結・恒真化・正しさ境界 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B — 受理集合・非回帰・変異帰属 |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (real/refuted、形 A、変異事前登録、裁定パッケージ) |
| `verbatim/s5-author.md` | 段 5 実装子の報告 |
| `verbatim/s6-reviewA.md` | 段 6 敵対レビュー A |
| `verbatim/s6-reviewB.md` | 段 6 敵対レビュー B |
| `verbatim/s6-focus.md` | 段 6 焦点再レビュー (GO) |
| `parent-measurements.md` | 親の焦点走 1〜9 の実測 (一次資料) |

## この package の限界

- 親の実測は本 wave の checkout についての測定であり、正式 run の将来の起動可能性を示さない。
- repo scan invariant の**全 repo 検査は実行していない**。当該テストは成長比例コストゆえに
  恒久保留であり、解除はユーザーの明示命令のみである。本 package が示すのは、
  変更した file 本文に対する `holdout_conjunction_hits` の結果 (0 hit) だけである。
- 還元判断: 本 package に CCBench 上流への還元候補は含まれない。
