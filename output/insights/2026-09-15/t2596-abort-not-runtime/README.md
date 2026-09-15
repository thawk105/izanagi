# [T-2596] 非 certified 床値 campaign で CampaignAbort が launch_failure へ化けていた件

- authority: none
- default_effect: no-state-change
- wave: dev-wave-t2596-abort-not-runtime
- 実装 commit: 85c4f15ac3f94bbdc274270821d87f7cd46756a4
- 日付: 2026-09-15

この dir は本 wave の一次資料である。可変状態の正本ではない (正本は worklog 末尾と現行 phase doc)。

## 何が起きていたか

`orchestrator/campaign/s8b_floor_campaign.py` の `_Runner._run_session` は、測定呼び出しを
`except (RuntimeError, subprocess.TimeoutExpired)` で包み、捕まえた例外を `measure_error` に入れて
`launch_failure` の session record へ落としていた。

`CampaignAbort` は `FloorCampaignError` を介して `RuntimeError` を継承している (同 :360, :408)。
したがって測定経路から投げられた `CampaignAbort` はこの except に捕まり、即時停止ではなく
「起動失敗の session」へ変換され、campaign は retry 枠を消費しながら走り続けていた。

飲まれていた停止は、`_wrap_admission_aware_measure` が返す `measure_attempt` の 3 つである。

| 位置 | 停止の理由 |
|---|---|
| `s8b_floor_campaign.py:5983` | holdout admission is absent |
| 同 `:5988` | measure callback coordinates differ from frozen cell |
| 同 `:6002` | holdout attempt admission refused |

いずれも「凍結との束縛が破れた」ことを意味する。これが `launch_failure` に化けると、
journal の試行行・retry 枠・terminal 診断が、起こっていない事象 (プロセス起動失敗) を記録する。

certified 経路は `s8b_floor_attempt_launcher.OpenedFloorAttempt.failure` を使う別構造で、
この except を通らない (`:6259` の早期 return で分岐する)。T-2596 の「非 certified 経路」という
限定はこの構造差と一致する。

## 実装

`_run_session` の測定呼び出しに `except CampaignAbort: raise` を前置した (2 行)。
継承の順序があるため、節の順序が唯一の分岐点である。bare `raise` で元の例外オブジェクトを保つ。

**post-probe は abort 経路では実行しない。** `strict_probe` 自身が `CampaignAbort` を投げる
(同 `:1711`, `:1713`, `:1717`) ため、先に走らせるとそこで出た別の abort が元の停止理由を置き換え、
`:7957-7963` が journal へ書く `terminal/status=aborted` の `reason` が失われうる。

## 受理集合の変化

- certified 経路と最終 inspection の受理条件は不変。
- **非 certified の実行継続条件だけが厳しくなる。** これは意図した変更である。
- plain `RuntimeError` と `subprocess.TimeoutExpired` は従来どおり `launch_failure` へ落ちる。

## 変異台帳

spec は `mutation-spec.json` (sha256
`3d30103cf9296e1501b39d480ba23c4bbb3644de444481b2a625309d75a850e5`)、
結果は `mutation-out.json` (repo_head = 85c4f15ac)。

| ID | 変異 | 期待 | 結果 | 赤くなった node |
|---|---|---|---|---|
| baseline | なし | PASSED | PASSED | 0 |
| M1 | 追加 2 行を削除 | KILLED | KILLED (matches) | 新設負例 1 |
| M2 | `except RuntimeError: raise` へ拡大 | KILLED | KILLED (matches) | 新設正例 + 既存 `test_post_probe_runs_on_launch_error_and_competing_takes_precedence` の 2 |
| M3 | 再送出前に `strict_probe` を挿入 | KILLED | KILLED (matches) | 新設負例 1 |

3 件とも `matches_expectation: true` で、赤くなった node の集合が事前登録と完全一致した。

M2 は「受理集合を縮小する wave の、承認外の過剰拒否の正例」を兼ねる (DW-M01)。
M2 は既存テストも赤にするため、全走の赤だけでは新設正例への帰属を示せない。
本走は新設正例を含む 3 node を個別指定した範囲で走らせ、帰属を確定した。

登録から外した変異とその理由は `stage4-ruling.md` の「6. 変異事前登録」に逐語で残してある。

## 実走 (すべて緑)

| 対象 | 結果 |
|---|---|
| 新設 2 本 | 2 passed, 516 deselected in 8.01s |
| `test_s8b_floor_campaign.py` 単独走 | 515 passed, 3 skipped in 697.41s |
| consumer + meta-test 5 対象 | 113 passed in 98.56s |

consumer の列挙は symbol `_run_session` の参照関係で引いた (`test_s8b_oracle_n_pilot.py`)。
meta-test は自走 harness (`test_plain_runner_coverage.py`)、所要台帳の網羅率、pytest 収集設定、
real repo 収集の 4 件。

トップレベル test 関数は 359 から 361 へ増え、削除はゼロ (HEAD との集合比較で確認)。

## real だが scope 外と裁定した所見

- **族一般化しない。** 「どこで発生した `CampaignAbort` でも停止する」は成立しない。
  `orchestrator/calibrator/runner.py:1184` や `s8b_floor_attempt_launcher.py:1400 / 1443` にも
  広い捕捉がある。本件の 3 つの abort はその外側で起きる。DW-G03 は族一般化に独立 2 例を要求し、
  本件は 1 例である。
- **注入 callback が非 abort の `FloorCampaignError` を投げる経路。** 現在も捕捉される。
  既定の実装経路からは到達しない (予約段の `:7924` は対象 try の外)。
- **wrapper 内の 3 つの拒否条件それぞれの到達性は本 wave の検査範囲外。**
  負例は admission を通過した後の callback abort を注入する。機構 (except 節の順序) は実体を
  通して検査できるが、3 条件それぞれのテストは足していない。
- **β-7 の全称表現との不一致。** 同 file 冒頭 `:33-34` の「measure が例外を投げた経路でも
  finally 相当で必ず post-probe を実行する」は、この abort 経路には文字どおりには成立しない。
  既存の `_SimulatedCrash` (Exception 継承) も同じく post-probe を飛ばしている。
  docs は変更せず、解釈上の未解消点として記録する。

## 親 brief の訂正 (段 3 の 2 レンズが指摘、親が現物で検算)

`stage4-ruling.md` の「4. 親 brief の訂正」に 8 件を逐語で残してある。主なものは次の 3 つ。

1. 「非 certified 経路で該当する唯一の except」は限定不足。正しくは「この measure 呼出しを包む
   except として唯一」で、非 certified 経路全体の唯一ではない。
2. `runner.py:963` は `open_measurement_point` (定義 936)、`:1184` が `measure_point` (定義 1072)。
   親は両者を混同していた。
3. 「凍結 bytes の pin は無い」は断言が強すぎる。正しくは「確認範囲で該当 pin 未発見」。

## この dir の file

| file | 中身 |
|---|---|
| `stage2-plan.md` | 段 2 plan の逐語 (codex, read-only) |
| `stage3-consult-sol.md` | 段 3 敵対レンズ (1) 停止の意味と受理集合 |
| `stage3-consult-luna.md` | 段 3 敵対レンズ (2) 既存の取り決めとテストの実効性 |
| `stage4-ruling.md` | 親の裁定 (実装子への正本) |
| `stage5-author-report.md` | 段 5 実装子の報告 |
| `stage6-review-a.md` | 段 6 敵対レビュー A (実装の忠実性と停止の意味) |
| `stage6-review-b.md` | 段 6 敵対レビュー B (テストの実効性) |
| `mutation-spec.json` | 変異事前登録 |
| `mutation-out.json` | 変異 matrix の実行結果 |
