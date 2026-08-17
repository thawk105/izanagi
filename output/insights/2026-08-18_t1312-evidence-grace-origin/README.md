# [T-1312] 子の証拠猶予の起点移動 wave (D498) — 逐語と裁定 (2026-08-18)

`authority: none` / `default_effect: no-state-change` — 可変状態の正本は `docs/worklog.md` 末尾、
設計判断の正本は `docs/decisions.md` の D498 である。本 dir は wave の一次資料 (逐語) を置く。
branch `worktree-t1312-evidence-grace-origin`。凍結記録であり、後から書き換えない。

- `verbatim/s1-brief.md` — 段 1 brief (親)。(P1)〜(P3) の provisional 裁定と実アンカー表。
- `verbatim/s2-plan.md` — 段 2 プラン起草 (codex、read-only、reasoning=max)。総括 GO。
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界)。must-fix 3 件。総括「そのまま採用不可」。
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (閉包と実効性)。must-fix 2 件。総括「採用不可」。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親) と plan v2、変異事前登録 M1〜M5。
- `verbatim/s5-author.md` — 段 5 実装子 (codex、workspace-write、reasoning=high)。
- `verbatim/s6-reviewA.md` — 段 6 敵対レビュー A (実装の正しさと検出力)。
- `verbatim/s6-reviewB.md` — 段 6 敵対レビュー B (退行・閉包・修正案)。
- `verbatim/s6-fix.md` — 段 6 fix 子 (codex、workspace-write、reasoning=high)。
- `mutation-spec.json` — 変異 matrix 本走 spec (M01〜M05)。
- `mutation-spec-m03.json` — M03 単独再走 spec。

## 結論

**D498 を実装した。** `--evidence-grace-s` の deadline 起点を、試行記録の作成時
(`AttemptState.started_ns`) から子の起動完了時 (`spawn_completed` 境界) へ移した。
production 差分は `tools/codex_worker_launch.py` の 3 行。`max_wall_clock_s` は触っていない。

## この wave が確定させたこと

1. **両レーンが独立に、段 2 プランの判別テストが恒真ゲートだと見抜いた。** 論理時計を
   preflight 区間でしか進めない設計では、deadline 起点を preflight 完了時刻に置いた実装も
   同じ結果を出す。3 つの候補起点それぞれの間に**異なる正の値**を注入して初めて分離する。
   採用した形は preflight 0.10 秒 / spawn 0.02 秒 / poll 0.01 秒、猶予 0.05 秒で、
   `supervision_drain` が旧起点 0.01、preflight 起点 0.03、正しい起点 0.05 になる。

2. **F57 の実機序は attempt 2 だった。** attempt 1 だけを検査する判別テストは
   「attempt 1 は新起点、retry は旧起点」の実装を通す。変異 M04 がこれを実証した
   (retry 判別 node だけが赤になる)。

3. **本変更は新しいフレーク形態を導入しうる。** 起点移動後の evidence deadline は
   `attempt 開始 + preflight + spawn + 猶予` に位置するため、猶予 1.0 秒固定の既存 fixture は
   `max_wall_clock_s=3` に対する余裕が縮む。evidence 関門を検査する既存 3 本を 0.3 秒へ下げた。

4. **help 文言の 1 語追加が、無関係に見える既存テストを落とした。** argparse の行折り返し位置が
   動き、既存 assertion の literal `--max-wall-clock-s` が `--max-wall- clock-s` に割れた。
   旧文面を byte 同一の前方 prefix に保ち、新語句を末尾の独立した空白区切り chunk として
   足す形で解決した。textwrap は `break_long_words=True` のため、長い chunk を末尾へ
   連ねるだけでは任意位置で割られうる。

5. **login ノードでの launcher 焦点走は判定に使えない。** 32 worker で 633 item を走らせると
   launcher 系が 68 件赤になったが、同じ集合が計算ノードでは緑だった。しかもこの赤は
   `rc=0` の infrastructure error ではなく、もっともらしいテスト失敗の形で出る。

## 実測

| 走行 | 環境 | 結果 |
|---|---|---|
| 焦点走 1 (修正前) | login、32 worker、3 file 633 item | 69 failed (68 件は F57 族の環境要因、1 件は help 折返し) |
| 焦点走 2 (修正前) | 計算ノード request 919662、48 worker、181 item | 180 passed / 1 failed (help 折返しのみ) |
| 焦点走 3 (修正後) | 計算ノード request 919697、48 worker、181 item | **181 passed / rc=0** |

## 変異 matrix

対象 commit `51dfdc5b29f953b68300f1676cb964d15e56aa0a`、runner 範囲は
`orchestrator/tests/test_codex_worker_launch.py` と `orchestrator/tests/test_dev_wave_codex.py`。
`--runner-mode dispatch`、runner argv に `--force-dispatch`。

| ID | 変異 | 期待 node | 結果 |
|---|---|---|---|
| M01 | 起点を `state.started_ns` へ (**wave 前の実コードの形**) | 新設 3 node | KILLED |
| M02 | 起点を `preflight_now_ns` へ | 新設 3 node | KILLED |
| M03 | spawn sample を診断条件内へ戻し、診断なしは旧起点へ fallback | 診断なし node 1 本 | KILLED (2 走目) |
| M04 | attempt 1 だけ新起点、retry は旧起点 | retry node 1 本 | KILLED |
| M05 | 診断境界と deadline で別サンプルを取る | 新設 2 node + 既存 exact duration node | KILLED |

**erratum:** 本走 1 回目は baseline が F285 族のフレーク (`limit_trigger='max_wall_clock_s'`、
`codex_exit_code=-9`、34 件) で赤になり、harness が production write を開始せずに中止した。
`--resume` は baseline を再走しない (`baseline=0 run(s)`) ため、新しい scratch と出力 path で
最初から走らせ直した。2 回目は baseline PASSED で 4 KILLED / 1 MISMATCH。
MISMATCH は M03 で、**指名 node は正しく発火していた**が、同じ走行に F57/F285 族の
環境フレークが 9 件相乗りして観測 node 集合が完全一致しなかった。M03 を単独 spec で
再走し、期待 node 完全一致の KILLED を得た。初回の観測集合は本 erratum として残す。

## 実装しなかった real 所見 (ユーザー裁定へ返す)

段 3 レンズ A の S2: **`max_wall_clock_s` は receipt の admission bound であって、
launcher process の物理的な hard cap ではない。** 最初の wall 検査より前に各 5 秒 timeout の
preflight が走り、limit 到達後も termination grace と reap が続き、成功経路でも最終 latch 後の
receipt 公開に wall 再検査が無い。receipt 自身は scope を
`launcher_start_to_receipt_fields_finalized` と宣言している。

- 択 (a): 現状の意味 (admission bound) を明記して閉じる。
- 択 (b): 物理 hard cap を要求し、外部 watchdog まで scope に入れる。
- 親の推奨は **(a)**。D498 は起点の意味是正であり、総所要の意味論変更は別問題である。
  (b) は新機構を要し、絶対規律 5 (盛らない) に抵触する。
