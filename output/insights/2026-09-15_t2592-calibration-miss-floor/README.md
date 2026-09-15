# [T-2592] 較正のレコード数選択規則へ品質検査の取りこぼし率下限を足す

裁定 = D1986 項 1 (2026-09-14 ユーザー裁定、対象 T-2592 / T-2515)。
先行資料 = `output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md` (rr5 の却下実測)。
実装 commit = `632754bbc`、branch = `worktree-dev-wave-t2592-calibration-miss-floor`、
着手時の local main = `0600887d9`。

## 何が壊れていたか

較正の選択器 (`orchestrator/calibrator/analyze.py`) は、採用レコード数を決めたあとで
その点の LLC miss 率が下限 0.50% を割っていれば `cache_floor_warning` を立てるだけだった。
下限は**選択に効いていなかった**。書き込み主体 (rr5) では working set の代理指標 (maxrss) と
実際の miss 率が食い違うため、D15 の下限基準が選ぶ最小点の miss 率が 0.364% にしかならず、
`orchestrator/calibrator/report.py` がそれを `selection-invalid` に落とし、
`quality.status = rejected` になっていた。**選択器が品質検査の却下する点を提案し続ける**状態である。

## 何を変えたか

候補集合は既存規則が admit する集合のまま、その中で miss 率が `cache_floor` 以上の最小 N を採る。
飽和経路 (`find_saturation`) と下限経路 (`_lower_bound`) の両方に同じ形で掛けた。

- 飽和経路は従来どおり系列の最終点を候補から外す (後続が無く平らを確認できないため)。
- 下限経路は従来どおり最終点も候補に含む。
- 下限を満たす候補が無ければ、従来の採用点と従来の警告をそのまま保つ。
  **飽和経路から下限経路へ乗り換えない。** 品質検査は従来と同じ点を却下する。
- `cache_floor` (0.005)、飽和閾値 (0.01)、`l3_multiple` (4.0)、2 つの選択フラグの意味、
  結果 schema はいずれも不変。採用点が動いたときだけ既存 `notes` に旧点・新点・閾値を書く。

判定器 (`report.py` の `selection-invalid` 化、`orchestrator/campaign/b10_backoff_shape_sweep.py`
の preflight) は 1 バイトも触っていない。

## rr5 の観測系列を新規則へ通した実測

先行資料が記録した系列 (L3 総量 110,100,480 bytes = 105 MiB、`l3_multiple=4`) を実装へ通した。

| N | LLC miss 率 | 前点との差 | maxrss | working set / L3 | 新規則の扱い |
|---:|---:|---:|---:|---:|---|
| 1,000,000 | 0.364% | — | 517 MiB | 4.92 | RSS 条件は満たすが miss 下限未満 → 保留 |
| 2,000,000 | 1.392% | +1.028pp | 1,023 MiB | 9.74 | **両条件を満たす最小点として採用** |
| 4,000,000 | 4.762% | +3.370pp | 1,958 MiB | 18.65 | 両条件を満たすが最小ではない |

実装の実出力:

```text
records = 2000000
saturated = False
lower_bound_selected = True
cache_floor_warning = False
```

最後のステップ差 3.370pp が飽和閾値 1pp 以上なので飽和候補は無く、下限経路へ進む。
**選択理由による却下は解消する。** ただし認定全体が accepted になるかは noise CV などの
他の品質条件が決めるので、本 wave はそこまでは主張しない。

## 過去の却下の読み方

2026-09-13 の rr5 の `selection-invalid` は**却下のまま**である。当時の規則の下では正しい判定で
あり、緑へ読み替えない。本 wave が変えたのは選択器であって、当時の判定ではない。
新しいテストは「新規則なら 2,000,000 を選ぶ」という反実仮想の検査であって、
「旧 1,000,000 の却下が誤りだった」という検査ではない。

## 既存の登録済み較正への影響 (非退行の実測)

`output/env/pegasus/calibration/registered/` の**全件**を親が直接読み、系列から手で判定した。
着手時点では 4 件だったが、wave 中に local main が進み `6cf35ee7a`
(non-silo protocols の認定較正) が 3 件を足したので、取り込み後に 7 件で取り直した。

| 成果物 | rratio | 採用 N | 採用点 miss 率 | 新規則で動くか |
|---|---:|---:|---:|---|
| `calibration-449d0ad22f13e366.json` | 50 | 1,000,000 | 14.8213% | 動かない |
| `calibration-5c836a22eff9ab40.json` | 95 | 1,000,000 | 6.0233% | 動かない |
| `calibration-753f535a8d024727.json` | 50 | 1,000,000 | 2.6453% | 動かない |
| `calibration-94a4b79fa31bba3c.json` | 50 | 1,000,000 | 2.7093% | 動かない |
| `calibration-9b49335d02ad4d2e.json` | 50 | 1,000,000 | 7.9688% | 動かない |
| `calibration-b3329d93417c76ad.json` | 95 | 1,000,000 | 17.0084% | 動かない |
| `calibration-cb98513996e5ae35.json` | 95 | 1,000,000 | 9.5573% | 動かない |

7 件とも最終ステップ差が飽和閾値 1pp 以上なので飽和候補が無く、下限経路の最初の RSS 適合候補
(N=1,000,000、maxrss 518〜640 MiB ≥ 4×L3 = 420 MiB) が既に下限を満たす。したがって採用点は動かない。
ただし**同じ系列を再解析すると `notes` の文言は変わる**ので、採用点の非退行と
bytes・SHA の同一性は別である。既存成果物を再生成する経路は本実装には無い。

**着手時の 4 件だけで「全件動かない」と書くと誤りになるところだった。** 登録簿は wave 中に増える。

## 射程の限界 (謳わないために書く)

1. **飽和候補が全て下限未満で、最終点だけが両条件を満たす系列では、新規則でも却下が残る。**
   例: N=(1m, 2m, 4m)、miss=(.001, .002, .006)、全点 RSS ≥ 4×L3。全ステップ差が閾値未満なので
   飽和候補は 1m と 2m (最終点 4m は候補外)、どちらも下限未満 → 1m を保持し警告 True。
   候補集合を広げない判断の帰結であり、現行コードでも同じ挙動である (本 wave の退行ではない)。
   正しい応手はスイープを上へ延ばすこと。
2. 倍々スイープの早期停止 (`orchestrator/calibrator/sweep.py`) は警告を条件に含めないので、
   「未観測の点まで含めて下限適合点を必ず得る」保証は無い。変更の前後で同じ。
3. 本 wave は rr5 の較正を走らせ直していない。裁定条件「走らせ直す前に規則を登録する」は、
   本 wave の decisions エントリが main へ着地することで満たす。再測定はその後の別作業である。

## 段 3 敵対相談 (2 レンズ) の結末

| ID | レンズ | 判定 | 結末 |
|---|---|---|---|
| S-1 | 正しさ防壁 | real | 採用。警告閾値を `floor*0.8` へ緩める変異が提案テスト群を生き延びる。miss 率が 0.40〜0.50% の帯に入る負例を 1 本追加した |
| S-2 | 正しさ防壁 | real | 採用 (文言訂正のみ)。有効点ゼロの経路は元から警告処理を通らない。親 brief の「必ず警告 True」が広すぎた |
| L-1 | 裁定条件・実効性 | real | **不採用 + 記録**。上の「射程の限界 1」。裁定の「**も**満たす」は既存候補条件への追加を指す |
| L-2 | 裁定条件・実効性 | real | 採用。下限経路だけを `>` にする変異に歯が無かった。境界例を 1 本追加した |
| L-3 | 裁定条件・実効性 | real | 採用。「却下の連鎖」テストは既存の認定テストと同じ変異で赤くなるため作らせなかった |

親 brief 自身の誤りも 4 件挙がり、全件採用して訂正した。最も重いのは
「片側の経路だけに掛けると workload 非依存にならない」という親の理由づけで、
2 レンズが独立に否定した。結論 (両経路へ掛ける) は維持し、理由を
「裁定が名指すのは選択規則全体であって片方の経路ではない」へ差し替えた。

**S-1 は変異で裏が取れた。** 下の M3 は警告閾値を下方へ緩める変異で、
S-1 が足させた負例 1 本だけが殺している。段 3 を省いていれば、
正しさ防壁の閾値を緩める変異が素通りする状態で着地していた。

## 段 6 敵対レビュー (2 レンズ) の結末

**must-fix 0 件。** nit 2 件はいずれも裁定文の説明の誤りであって実装ではない。

- R-1: 「M3 の変異だけがこのテストを殺す」という裁定の書き方は言い過ぎで、同じテストは
  M5 でも赤くなる。証拠の限定として記録する (下の表で実測済み)。
- R-2: 裁定は L-1 の系列で「既存 note がスイープ延長を促す」と書いたが、現物ではその系列は
  飽和経路へ入るため出る note は「最小点で既に飽和」+ 下限警告であり、延長を促す note は出ない。
  裁定の理由 4 は事実と違っていた。**選択結果そのものは裁定どおりである。**

## 変異検査

`tools/mutation_harness.py` を実装 commit `632754bbc` へ束縛して走らせた。
probe を全件 SURVIVED 期待で先に流し、観測 node から本走の期待 node 完全集合を作った
(probe は 7 件すべて MISMATCH = 実際には KILLED。初回記録も `mutation-probe-report.json` に残す)。
runner は `python3 tools/run_tests.py --force-dispatch -rf orchestrator/tests/test_calibrator.py
orchestrator/tests/test_calibrator_certify.py`。

**本走: baseline PASSED (失敗 node 0)、7/7 KILLED、期待 node 完全一致、SURVIVED 0・MISMATCH 0。**

| ID | 変異 | 失敗 node 数 | 単一理由性 |
|---|---|---:|---|
| M1 | 飽和経路の下限比較 `>=` → `>` | 1 | **あり**。`test_saturation_cache_floor_boundary_and_override` だけ |
| M2 | 下限経路の下限比較 `>=` → `>` | 1 | **あり**。`test_lower_bound_cache_floor_boundary` だけ |
| M3 | `_flag_cache_floor` の閾値を `floor * 0.8` へ | 1 | **あり**。`test_saturation_cache_floor_warning_inside_margin` だけ。S-1 が足させた負例 |
| M4 | 下限経路の従来候補復帰を削除 | 1 | **あり**。`test_lower_bound_cache_floor_no_match` だけ |
| M5 | 飽和経路の従来候補復帰を削除 | 3 | 過剰決定。同じ性質 (適合候補なしで採用点と警告を保つ) を 3 本が独立に拒否する |
| M6 | 下限経路で最初の適合候補で止めず最後を採る | 3 | 過剰決定。最小性を 3 本が拒否する |
| M7 | 飽和候補の範囲 `range(n - 1)` → `range(n)` | 10 | **冗長 gate**。既存 4 本 (`test_saturation_never` 等) も拒否するので、単独変異の証拠から外す (DW-M03) |

M1〜M4 が単一理由性を持つことが、新規テスト 4 本それぞれに固有の歯があることの実測である。
`test_calibrator_certify.py` を同じ走行に含めたが、どの変異もそこでは赤を出さなかった。
認定層が選択層の欠陥を mask していないことの裏取りになる。

生の spec と report は本 directory の `mutation-spec.json` / `mutation-report.json` /
`mutation-probe-spec.json` / `mutation-probe-report.json` を正本とする。

## 検査

- 変更した test file 単独走 (`orchestrator/tests/test_calibrator.py`): **69 passed / 0 failed**。
- consumer 焦点走 10 file (`test_calibrator_certify` / `test_calibrator_deferred_output` /
  `test_schema_v2` / `test_b10_backoff_shape_sweep` / `test_stability` / `test_between_run_floor` /
  `test_pegasus_calibration_workload` / `test_holdout_observation` / `test_floor_pair_driver` /
  `test_silo_ladder_rung1_driver`): **925 passed / 0 failed**。
- テスト関数名集合の基底突き合わせ: 削除・改名 **0 件**、新規 **9 件**。
- `tools/check_ai_provenance.py` 全史 rc=0 (10,105 件、新規違反なし)。
- 段 3 敵対相談 2 本、段 6 敵対レビュー 2 本。実装への must-fix は 0 件。
- 受入全走の実測は worklog に記す。

## 所在

- 親 brief / 裁定 / 子成果物 / 待ち手 receipt: `/home/SFC/tanab/.claude/jobs/c46bd823/tmp/wave/`
