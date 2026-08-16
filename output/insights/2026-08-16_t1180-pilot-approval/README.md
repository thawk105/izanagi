# [T-1180] 床値 pilot の承認を投入引数で渡す — 逐語と変異台帳

wave `dev-wave-t1180-pilot-approval` (branch `worktree-dev-wave-t1180-pilot-approval`) の
子成果物の逐語と、変異 matrix の spec / 台帳。判断の要約は worklog の該当エントリ、
設計判断は decisions の該当 D を正本とする。ここは**一次資料の保管**であり、要約ではない。

## 逐語 (`verbatim/`)

| ファイル | 段 | 産出者 | 備考 |
|---|---|---|---|
| `s2-plan.md` | 2 | codex plan (gpt-5.6-sol, reasoning=max) | receipt field 追加 + env 値 `1` を推奨。**段 4 で両方とも不採用** |
| `s3-consult-a-sol.md` | 3 | codex consult (gpt-5.6-sol, max) | 正しさ境界レンズ |
| `s3-consult-b-luna.md` | 3 | codex consult (gpt-5.6-luna, max) | 整合・実効性レンズ |
| `s4-adjudication.md` | 4 | 親 (claude) | 裁定・変異事前登録・実測訂正 |
| `s5-author.md` | 5 | codex author (gpt-5.6-sol, high) | 実装報告 |
| `s6-review-a.md` | 6 | codex review (gpt-5.6-sol, high) | 正しさ境界レンズ |
| `s6-review-b.md` | 6 | codex review (gpt-5.6-sol, high) | 回帰・波及レンズ |
| `s6-fix.md` | 6 | codex fix (gpt-5.6-sol, high) | must-fix の対応表 |
| `s6-focus.md` | 6 | codex focus (gpt-5.6-sol, high) | 焦点再レビュー = GO |

## 変異 matrix (`mutation/`)

権威は **2 巡目** (`mutation-spec-final.json` + `mutation-ledger-final.json`)。

- 対象 commit: `2d3fc157434a2ab6e54825968f748c5150f5197a`
- runner: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_pegasus_floor_tools.py -rf`
- harness: `tools/mutation_worktree.py` (使い捨て worktree、`--runner-mode dispatch`)
- 結果: **KILLED 9 / 9、MISMATCH 0、SURVIVED 0、TIMEOUT 0、baseline PASSED、wrapper rc=0**

1 巡目 (`mutation-spec-probe.json` + `mutation-ledger-probe.json`) は **probe** である。
期待 node を静的に確定できなかったため初回を probe と明記し、実測から完全集合を再導出して
2 巡目を権威とした (`DW-M08`)。1 巡目は KILLED 4 / MISMATCH 5 / SURVIVED 0 で、
**ずれはすべて「期待より多く落ちた」側**であり、殺せなかった変異は 1 件も無い。
ずれた理由は 2 つある。

1. 段 6 fix で新設した構造テスト
   `test_floor_job_confirmation_dataflow_and_admission_order_are_fixed` が、
   自分の担当変異 (n7 / n8) 以外の変異でも赤になる。承認変数の出現集合を固定しているため、
   出現位置を変える変異はすべてこの node に当たる。
2. `test_submit_floor_qsub_argv_does_not_inherit_ambient_confirmation` は
   submitter 側だけでなく driver argv も独立に確認するため、`floor_campaign.sh` 側の
   変異 (n1 / n7) でも赤になる。

### 登録変異

| ID | 対象 | 変異 | 種別 |
|---|---|---|---|
| n1 | `floor_campaign.sh` | driver argv の条件を外し承認 flag を無条件 append | negative |
| n2 | `floor_campaign.sh` | 承認 env の exact 一致比較を「非空なら承認」に緩める | negative |
| n3 | `floor_campaign.sh` | 不一致時に `write_failure` / `exit` せず続行 | negative |
| n4 | `submit_floor.sh` | 承認既定値を `0` から `1` にする | negative |
| n5 | `submit_floor.sh` | 承認引数の有無に関わらず `export_spec` へ append | negative |
| n6 | `submit_floor.sh` | 既定値を ambient env から初期化する | negative |
| n7 | `floor_campaign.sh` | 承認照合の通過後・driver 起動前に承認 env を nonce で再代入する | negative |
| n8 | `floor_campaign.sh` | 冒頭の `unset` に承認 env を加える | negative |
| p1 | `floor_campaign.sh` | env が nonce と一致していても常に `write_failure` する | positive (過剰拒否の検出) |

n7 / n8 は段 6 の敵対レビューが**事前登録の穴**として指摘したものを追加登録した。
指摘前のテストは shell の 2 断片をテスト側で連結実行しており、両断片の間と冒頭 `unset` 行を
1 度も実行していなかった。
