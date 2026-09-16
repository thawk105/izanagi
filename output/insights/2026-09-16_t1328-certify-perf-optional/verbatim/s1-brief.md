# 段 1 brief — [T-1328] `certify_calibration.sh` の perf 全滅時 `exit 2` を直す

wave = dev-wave-t1328-certify-perf-optional / branch = worktree-dev-wave-t1328-certify-perf-optional
worktree (子が読む repo root) = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1328-certify-perf-optional`
基準 = local main 9d52ef145 (着手直前に fresh 作成、起動 gate rc=0)

## 研究前進 (土台)

止めうる研究 = **rr5 / rr95 の認定較正取得** (D1641 認可、現在 wave
`worktree-dev-wave-t2515-rr5-accepted-calibration` が進行中)。本分岐が発火すると、2 時間の予約と
CCBench build をすべて消費した後、測定に 1 度も入らず attempt が捨てられる。
**実測すると現時点で研究は止まっていない**: `output/env/pegasus/calibration/job-staging/` の 19 attempt
のうち perf 段で失敗したものは **0 件**、直近 2026-09-15 の 3 attempt はいずれも
`/usr/lib/linux-tools-5.15.0-135/perf` を選んで LLC 実カウンタを得ている。
一方で D352 自身の根拠実測は「2026-08-12 に計算ノード 8/8 で linux-tools 不在」であり、
**この環境は既に 1 度反転している**。最小差分 = D494 が既に定めた形を本 script の 1 分岐へ適用する。

## scope

- scope 内: `tools/pegasus/certify_calibration.sh` の perf 候補全滅時の分岐と、それが成立するために
  必要な最小の calibrator 側配線 (P1 参照)、および対応するテスト。
- scope 外 (依頼の明示): [T-1329] `floor_scoping.sh`、仮想リスク向けの gate・検査・台帳・一般化の追加、
  `t141_region_profile.sh` (perf profiling が目的そのものなので `fail 2 perf_select` は正しい)。

## 確定済みユーザー裁定 (逐語は `verbatim/` に射影済み)

- **D352**: 性能測定 (床値・**calibration**・oracle を含む) は perf の可用性を前提にしない。
  preflight は可用性を検出して環境タグへ記録し、**実行を止めるためには使わない**。
- **D494**: 候補が 1 本も通らなかった時点では degrade を判定しない。候補解決を済ませた `PATH` の下で
  canonical probe を 1 度だけ呼び、その結果だけで分岐する。判定の入口は `use_perf_from_receipt` 1 本のまま。
  `command -v` / `which` / 環境変数を新しい判定入口にしない。
- **D493**: degraded 受理は「緩い分岐」ではなく「別の厳しい分岐」。perf 有り分岐の受理条件は 1 文字も変えない。
- **D348**: perf preflight の receipt emit は pilot に閉じ、official の受理言語を 1 bit も変えない
  (対象は S8b floor / ratified freeze。calibration 認証が射程に入るかは段 2/3 の検査対象)。
- ユーザーの繰り返し裁定: この計算機では**正式系列も perf 不在で進める**。perf を必須 gate にしない。

## 不変条件

1. **規律 2 を緩めない。** perf 不在経路が、現在 fail する判定を 1 つも pass に変えてはならない。
2. **perf 有り経路の受理集合を 1 文字も変えない** (D493/D494)。
3. **perf が本当に要る判定は通さない。** `orchestrator/calibrator/analyze.py:48-57` の
   `find_saturation` は `miss_rate` 欠損点を候補から外し、全欠損なら
   `records=0 / saturated=False`「飽和判定不能」を返す。下限基準 (L3 倍数) も `usable` にしか効かない。
   → **レコード数の飽和判定は perf 必須**。no-perf 走がレコード数を主張してはならない。
4. 判定入口は `use_perf_from_receipt` 1 本 (D494)。
5. 絶対規律 7: `job_script_sha256` の変化は過去成果物を無効にしない。過去判定を遡って昇格させない。
6. 依頼の scope: 本題の分岐修正だけ。gate・検査・台帳・一般化を足さない。

## 親の provisional 裁定 (段 3 の攻撃対象)

- **(P1)** wrapper だけの修正では成立しない。`use_perf` は `runner.measure_point`
  (`orchestrator/calibrator/runner.py:1086`) の引数として在るが `orchestrator/calibrator/sweep.py` は
  一度も渡さず既定 `True` のままなので、wrapper が先へ進めても calibrate は perf を呼びに行く。
  よって最小配線 = wrapper の分岐 + `sweep` 経路への `use_perf` 伝播。
  **攻撃されるべき点:** 伝播は本当に最小か。scope (本題の分岐修正だけ) を超えていないか。
- **(P2)** no-perf 走の正しい終わり方は「acquisition 判定 (割当・toolchain・binary 同一性・TSC・
  attestation) は成立して記録され、レコード数の飽和判定だけが明示的に不成立になる」形である。
  acquisition receipt は perf 選択**より前** (`certify_calibration.sh:843-846`) に既に生成されている。
  **攻撃されるべき点:** それは 2 時間を消費して却下成果物を作るだけではないか。
  逆に sweep を丸ごと省くと D352 の「perf なしで測定を進める」に反しないか。
- **(P3)** 依頼文の前提「この計算ノードに perf は無く、perf 不在が較正認証を止めるのは実害」は
  計算ノードについて**現在成り立たない** (上記実測)。wave の根拠は実害ではなく **D352 違反の是正**へ
  置き換える。**攻撃されるべき点:** それでも本 wave を走らせる価値があるか。段 4 で再裁定する。

## 変更面 (実アンカー表)

| # | path | 行 | 現状 | 本 wave での扱い |
|---|---|---|---|---|
| 1 | `tools/pegasus/certify_calibration.sh` | 882-909 | 候補 loop → 全滅で `write_failure 2 perf` + `exit 2` | 主対象。D494 の形へ |
| 2 | `tools/pegasus/certify_calibration.sh` | 911-930 | `perf-selection.json` 書き出し・symlink・PATH 前置 | 候補通過時のみ実行へ |
| 3 | `tools/pegasus/certify_calibration.sh` | 857-880 | `PERF_EVENTS` を runner.py の AST から読む | 変更しない見込み |
| 4 | `orchestrator/calibrator/sweep.py` | `run_sweep` / `_measure` / `calibrate` | `use_perf` を渡さない | (P1) 伝播の候補 |
| 5 | `orchestrator/calibrator/runner.py` | 1086 | `use_perf: bool = True` | 引数は既存。変更しない見込み |
| 6 | `orchestrator/tests/test_pegasus_calibration_workload.py` | 1643, 1792-1818 | fixture repo で script を実走 | テスト追加先 |
| 7 | `tools/pegasus/t126_qualification.sh` | 625-670 | D494 の先例実装 | 読むだけ。変更しない |

## 純増 (既存被覆の検索結果)

- `git grep -l certify_calibration` の hit は 17 file。`orchestrator/tests/test_official_perf_closure.py:88`
  は本 script を **既に** `_REVIEWED_PERF_FILES` へ登録済みなので、`probe_perf_availability` /
  `use_perf_from_receipt` を足しても閉包は壊れない見込み (段 2 で確認)。
- 本 script の sha256 を literal で pin する箇所は repo 内に **0 件** (実測)。`job_script_sha256` は
  submission と job result の**相互一致**だけが検査される (`orchestrator/qualification/identity.py:44-50`)。
- 較正認証の活動そのものを止める裁定は索引した範囲で見つからなかった。

## 成果物の形

変更後の `tools/pegasus/certify_calibration.sh` (+ 最小の calibrator 配線)、
`orchestrator/tests/test_pegasus_calibration_workload.py` への正例・負例、
変異事前登録と matrix、worklog / decisions / insights の記録。

## 受入・実測環境

受入全走は login node で `tools/dev_wave_wait.py acceptance --lease-optional`。
計算ノードへの実 job 投入は行わない — 計算ノードでは perf が現に通るので no-perf 経路は実走できず、
fixture harness (上表 #6) が唯一の実測経路である。この非対称は成果物に明記する。

## 並列分割方針

段 2 plan = codex 1 本 (read-only)。段 3 = 2 レンズ並列 (正しさ境界 / 整合・実効性)。
段 5 実装子 = 1 本 (変更面が 1 script + 限定配線のため分割しない)。段 6 = review 2 本 + fix。
