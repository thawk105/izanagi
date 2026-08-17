# [T-1310] 正式 workload profile (rr80 / rr20) — 実装せず裁定へ返した記録

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` の末尾エントリと現行 phase doc である。
本 package は dev-wave `t1310-formal-workload-profile` (branch
`worktree-t1310-formal-workload-profile`、起点 main `2a3b5055`、2026-08-17 22:41〜) の
逐語凍結と裁定パッケージを保存する。

## 何が起きたか

台帳項 [T-1310] は「正式 holdout `rr80` / `rr20` を producer の production profile として実装し、
ratified freeze の正式 scale (1,000,000 records / 48 threads) を campaign / perf / descriptor の
3 sink へ束縛する」だった。段 2 のプランと段 3 の敵対レンズ 2 本、および親の実測により、
**この配線は単独では成立しない**と判明したため、実装せず裁定へ返した。実装面の差分は 0 件である。

## 塞いでいる 3 点

1. **Layer-3 の campaign-chain 検査が「producer は単一 scale」を機械的に固定している。**
   `orchestrator/campaign/autonomous_trial_completeness.py` の検査は cell の workload が
   探索表 `producer.WORKLOADS` に在ることを要求し、descriptor を profile を渡さない
   `_descriptor_for(flags)` で再導出して完全一致を要求する。
2. **正式受理の材料が未充填。** v1 凍結の `floor` / `budget` は null で、注記自身が
   「対象別 floor 再実測後に再凍結 + 承認で充填する」と要求している。
3. **ratified v2 世代が未発効。** `load_ratified_freeze` は `[no-active] live active pointer が無い`
   で止まる。登録済み manifest も無いため、manifest なしの起動は holdout workload を登録簿が拒否する。

`DW-G04` (条件付き機能の発火 gate) は、発火条件を満たす既存 artifact path も計測 ID も書けない機能を
実装せず設計メモへ送ると定める。また [T-822] の第 6 回ユーザー裁定は
「空振りする検査を置いて保証があるように見せる方が、保証が無いことを明示するより悪い」と定めており、
発火しない配線を置いて C01 の静的条件だけ通す形は採れない。

## ユーザーへ返す択

- **(α) 順序の組み替え (親の推奨)。** 床値/予算の対象別再実測 → v2 世代の発行と承認 →
  Layer-3 検査の profile 対応 (= [T-822] (i) の層) を先に置き、producer 配線を最後にする。
- **(β) 自作の証拠水準を明示的に下げる。** `s8b_ratified_freeze` の `load_legacy_freeze` による
  `legacy-v1` 源を正式 profile の暫定源として認め、non-certifying と明記したうえで
  `rr80` / `rr20` の 1,000,000 records / 48 threads の実測を可能にする。
  **物理的な測定自体は今日でも可能であり、塞いでいるのは v2 承認と床値という自作の手続きである。**
  `load_verified_freeze` を `expected_hash` なしで使う形は任意の working-tree bytes を受けるため採らない。
- **(γ) 現状維持。** 本項を凍結する。親は推奨しない (8c 正式受入が無期限に空のままになる)。

いずれの択でも、下記の「実装時に保存する要件」は変わらない。

## 実装時に保存する要件 (裁定が付いた後の wave 向け)

- 正式値 (read 比率) を producer へ literal で書かない。書くと `s8b_holdout_freeze` の三軸
  conjunction が成立し repo scan invariant が 0 hit から 1 hit へ壊れる (反実仮想で実証済み)。
- 3 sink それぞれに正式 scale の照合を置く。C01 は sink 関数内の整数 literal の**存在**しか見ず、
  その literal が実際に射影へ使われることを検査しないため、C01 の遷移は実射影の証拠にならない。
- 探索既定 (`ycsb-a/b/c` @ 100,000 records / 4 threads) を変えない。profile は明示 selector とし、
  未知 selector は fail-closed にする。
- C01 判定 snapshot の更新対象は実 repo snapshot の 1 箇所だけ。負の control (perf sink を探索 scale へ
  戻す変異を殺す側) は更新しない。

## 収録物

| path | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親) |
| `brief-addendum.md` | 段 1 追記 (親の実測で判明した新事実)。D88 の可逆 defang 記録付き |
| `parent-measurements.md` | 親の実測 M1〜M10 (一次資料) |
| `adjudication.md` | 段 4 裁定 (real / refuted、撤回、裁定パッケージ) |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex `plan`、`reasoning=max`、`read-only`) |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A — 凍結・世代・repo scan・恒真化 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B — 受理集合・探索非回帰・変異帰属 |

子 3 本はいずれも `tools/check_codex_output.py` で rc=0。実装子・fix 子・変異 matrix は
「実装しない」裁定により起動していない。

## この package の限界

- 親の実測は現 HEAD (`2a3b5055`) についての測定であり、v2 世代の将来の承認可能性や、
  正式 scale の runtime 射影の成立を示さない。
- repo scan invariant の**全 repo 検査は実行していない**。当該テストは成長比例コストゆえに恒久保留で、
  解除はユーザーの明示命令のみである。本 package が示すのは、変更した file 本文に対する
  `holdout_conjunction_hits` の結果 (0 hit) だけである。
- 還元判断: 本 package に CCBench 上流への還元候補は含まれない。
