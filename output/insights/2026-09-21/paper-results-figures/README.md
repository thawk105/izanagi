# 論文結果節の図 2 枚 — fig14 (A-1 sized attempt-0002 の記述図) と fig15 (stock mocc 軽量 witness 4 arm) (2026-09-21、台帳 ID 未起票)

wave `dev-wave-paper-results-figures` (branch `worktree-dev-wave-paper-results-figures`、起点 local main `36fb14a3d`、開始 gate 20:46 JST rc=0)。
依頼の逐語は `verbatim/origin.md`。成果物は repo 内の図 6 file と README 2 本の節、生成器の拡張 1 本と新設 1 本、test 2 本。
**results 稿と版の bytes は変えていない。fig9 の png / pdf / provenance の bytes も変えていない。**

## 1. 成果物

| file | 内容 |
|---|---|
| `docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2.{png,pdf,provenance.json}` | A-1 balanced5 sized 本走 attempt-0002 の単独記述図 (fig9 と同形の兄弟、`--attempt attempt-0002`) |
| `docs/paper-story/figures/fig15_mocc_witlight_four_arm.{png,pdf,provenance.json}` | stock mocc 軽量 witness 4 arm × 60 走 (本走 4 block W1〜W4) の G2 signal 検出率・Clopper–Pearson 区間・曝露量 |
| `docs/paper-story/figures/README.md` | 一覧 2 行、fig14 節、fig15 節 (caption 正文と着地 bytes の SHA-256 は provenance と現物から機械転記) |
| `tools/plotting/README.md` | attempt-0002 の節、mocc 生成器の節 |
| `tools/plotting/plot_a1_sized_paired.py` | attempt ごとの repo 所有 exact pin 表 (`ATTEMPTS`、2 entry)、`--attempt`、attempt-0002 の caption・panel 題の breach 表示・図上端の 1 行。attempt-0001 の返り値・caption・描画・既定 CLI は不変 |
| `tools/plotting/plot_mocc_witlight_four_arm.py` (新規) | repo 外 5 file の SHA-256 束縛、summary inputs の exact 照合、240 走からの再計算、1 axes forest + 数値列 + 図中注記、repo 内 / 外部の 2 層閉包 |
| `orchestrator/tests/test_plot_a1_sized_paired.py` | 既存 28 本は本文・期待値とも不変 (AST 比較)、16 本追加 (44 本) |
| `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (新規) | 27 本 (実寸 fixture、独立 literal の CP / Fisher、実 artist、禁止句、二層閉包、着地) |

## 2. 前提として実測したこと (段 1)

- D2194 項 6 (2) は「attempt-0002 の図は作らない。必要になれば単独図 (fig9 と同形、`caption_source` = 本稿) を先に作る」。同日 07:2x JST のユーザー再裁定「fig9b (2 attempt 並記図) は作らない」で先行 wave (`dev-wave-fig9b-a1-attempt2`、repo 変更 0) は停止済み。本依頼は並記図ではない単独図で、同項の「必要になれば」の経路にあたると判断した (brief P1、段 3 の 2 レンズとも同意)。
- attempt-0002 leaf (result `b7e0518e…` / receipt `98c35cca…` / .complete `7ad34232…`、policy `a6228bcd…` は attempt-0001 と共通) は、既存生成器の検査項目で attempt-0001 と同形で、違いは `variance_plan_breach` = [true, false, true] だけだった。
- 既存生成器は `variance_plan_breach is False` を必須にしており、fig9 の着地 test は現行生成器で作り直した caption / cells と着地 provenance の全 key 一致を要求する → attempt-0001 の返り値 key 集合・caption を 1 文字も変えられない (不変条件)。
- mocc の repo 外 5 file の SHA-256 は稿 §5.1 と一致。repo 内の逐語写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` の W1〜W4 `result.json` と `summary.json`) も同一 SHA-256 (生成器は入力にしない)。
  `summary.json` は arm 別の N / m / k / … / cp95 / inputs を持つが Fisher p と commit 数平均は持たない。W1〜W4 の `runs[]` から再計算した commit 数平均 (613,741.47 / 710,659.42 / 788,885.62 / 933,621.80) は稿 §2.2 の丸め表記と一致。
- 図番号 fig14 / fig15 は tracked 全体で未使用 (調査子の grep)。
- 受入所要時間台帳の被覆: login の `pytest --collect-only` で 27,049 node、台帳との交差 26,558 = 98.18%、90% を割るまで 2,459 node の余裕 → 新規 node は台帳に登録しない (P9、fig13 先例)。
- 裁定 inbox に wave 開始後 (21:17 JST) の控え `2026-09-21-vldb-direction-verdicts.md` 項 4 (実験の計算投入は都度ユーザー確認) と、その追補 (21:3x JST、「1 タスクで 2 node 時間以上なら事前確認、開発の検査も同じ線」) を確認した。本 wave は実験の計算を使わず、計算ノードは焦点走 2 回・変異 final・受入だけで 2 node 時間を下回る見込みとして確認を要しないと判断した (P10)。

## 3. 段の経過

| 段 | 内容 | 結果 |
|---|---|---|
| 1 | brief (P1〜P10)、pin 閉包 (read-only 調査子 1 本、Explore / sonnet) | `s1-brief.md`、`s1-pin-closure.md` |
| 2 | codex plan (read-only、21:11 JST 終了) | P1〜P8 の反証なし |
| 3 | codex 相談 2 本 (レンズ A 正しさ境界 / B 過剰・削除、21:15 JST 終了) | 両方とも条件付き GO (must-fix 各 2) |
| 4 | 裁定 `s4-ruling.md` | fig15 は 1 axes forest + 曝露の数値列 (B の最小案。FC §2 の 95% CI 要求に対し、曝露は稿の記録値を数値で示すだけで推論に使わない局所判断)、図中注記と禁止句の可視 Text 走査 (A、F872 型)、測定条件を caption に (B、FC §6)、failure / indeterminate は早期拒否、変異 M0〜M13 を事前登録 |
| 5 | Codex author 2 本 (所有を分けた unit worktree、21:35 / 21:36 JST 終了) | A-1: 43 passed + 着地 test 期待赤 1 (fig9 を既定 attempt で再生成し着地 provenance と 4 key 以外全一致)、mocc: 25 passed + 期待赤 2 |
| 統合 | 所有 path 限定 patch を `diff -u` で作り wave へ適用 (子の現物と sha256 一致) | 実装 commit `e5f1a55d6`、login で作図し docs commit `efd8d191d` |
| 6 | 焦点走 1 (計算ノード `15694.nqsv`、9 file) | 800 passed / 4 failed — 4 件は後述 §4 の型 |
| 6 | codex レビュー 2 本 (A 主張の境界・恒真な検査・docs 照合 / B 過剰・削除、21:50 / 21:49 JST 終了) | A: must-fix 2 / should 1 (条件付き GO)、B: must-fix 0 / should 2 / nit 1 (GO) |
| 6 | 裁定 `s6-ruling.md`、親の docs 訂正 `f2d146cd5`、Codex fix 2 本 (21:58 / 21:59 JST 終了) → fix commit `fc6c4f836` | 焦点走 2 (`15745.nqsv`) 804 passed / 3 skipped (skip 3 件は既存の template patch 系で本 wave の test ではない) |

## 4. 段 6 の所見と処置

- **pytest 下だけ赤 (自分起因、4 件):** 新 test が `assert cond, msg` を捕まえて `str(exc) == msg` と完全一致で比べていた。pytest の assert 書き換えは例外文に説明を足すので pytest 下だけ偽になる。
  子は prompt の指示 (sandbox では `tools/run_tests.py` と `python -m pytest` を使わない) どおり plain runner だけで緑を確かめており、2 本の子が独立に同じ型を書いた (既存 fig9 test は `startswith` で無事)。先頭行の完全一致へ直した。親の焦点走 (pytest) で受入前に検出した。
- **plotting README の照合先の誤記 (A#1 / B#1):** Fisher p と commit 数平均まで summary と照合したように読めた → summary が持つ量だけ照合し、Fisher p・commit 数平均・on/off 比は稿の表セルとの逐語一致を test が照合する、と書き分けた。
- **新節の「F36 の自己参照回避」(A#2):** F36 本文は「結果欄をプレースホルダのまま commit した」型で自己参照の規則ではない。ただし `docs/dev-wave/core.md` の `DW-S07` が「hash 自己参照は禁止（F36）」と引いており、既存の fig9 節の書き方はその先例に従っていた (一部 refuted)。
  新節は F 番号を外して理由 (稿と provenance が互いの hash を持つ循環を避ける) を直接書いた。**既存の fig9 / fig13 節と plotting README の既存 3 節、`DW-S07` の同じ引き方は本 wave では変えていない** (観察として記録)。
- **曝露比注記の可視検査漏れ (A#3、F623 / F653 型):** 図中の on/off 曝露比 2 行を消しても test が緑だった → 可視 Text を稿 §2.6 の独立 literal と照合する検査を足した (変異 M14 の kill 先)。
- **mocc test の import (B#2):** `PYTHONPATH` 前提だった → 既存 A-1 test と同じ同階層 `skiputil` に揃えた。**到達不能な隣接 panel 検査 (B#3):** 1 axes 制約の下で到達しない 4 行を削った。
- **焦点再レビュー (codex focus 1 本、GO):** 上の 10 行を closed 8 / refuted 妥当 1 (A#2) / partial 1 (A#3 = 曝露比の可視検査は外部 root 不在時に skip される test の中にあり、その射程が README に無い) と判定、
  新しい所見は should 1 (同じ射程の明記)。親が fig15 節に追記した (`1a54c0e66`)。

## 5. 変異 matrix (DW-M01 / M07 / M08)

事前登録 = `verbatim/s4-ruling.md` (M0〜M13) と `verbatim/s6-ruling.md` (M14、段 6 の real 所見の fix 前)。期待 node は login の自走 harness で注入 → 両 test file の
自走 → 復元 (sha256 一致) で観測し (`verbatim/mutation/login-probe.log`、baseline 44 + 27 passed)、その集合で dispatch の final を 1 回走らせた。
final = `tools/mutation_harness.py --runner-mode dispatch` (変異用 worktree `.codex/worktrees/mut-paper-figs` @ fix commit `fc6c4f836`、spec `verbatim/mutation/mutation-spec-v3-final.json`
sha256 `b7e713b8…`、13:06〜13:23 UTC = 22:06〜22:23 JST)。結果の要約 = `verbatim/mutation/mutation-final1-summary.json` (full results は job dir、sha256 `134a6960…`、391,606 byte)。

**KILLED 14 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0、15 件すべて期待 node の完全集合と一致。** baseline は計算ノードで 71 passed。

| # | 変異 | 結果 | 赤 node 数 | 備考 |
|---|---|---|---:|---|
| M0 | A-1 生成器へコメント 1 行 (等価対照) | SURVIVED (予測どおり) | 0 | `generator.sha256` は生成時の記録で現行 source の pin ではない |
| M1 | attempt-0001 の breach true 拒否を除去 | KILLED | 1 | 既存 `test_variance_plan_breach_true_is_rejected` |
| M2 | attempt-0002 の result pin を 1 文字変更 | KILLED | 3 | 稿 §5.1 照合・実 leaf・着地 fig14 (同一理由 = pin 不一致) |
| M3 | attempt-0001 caption の 1 語 | KILLED | 1 | 既存 fig9 着地閉包 (fig9 の不変性を守る最終 oracle) |
| M4 | attempt-0002 caption からプール・比較禁止の固定文を除去 | KILLED | 2 | caption 固定文 test・着地 fig14 |
| M5 | attempt-0002 panel 題の breach 行を描かない | KILLED | 2 | 描画 artist test・着地 fig14 |
| M6 | summary.json の pin を 1 文字変更 | KILLED | 4 | 稿 §5.1 照合・実証拠・着地 2 本 (同一理由) |
| M7 | summary inputs の exact 照合を除去 | KILLED | 2 | smoke 第 5 entry・inputs exact の 2 test |
| M8 | CP 上限の分位 .975 → .95 | KILLED | 17 | **過剰決定** — 独立 literal の CP test に加え、loader の summary cp95 照合が全 fixture を拒否する。単独変異の証拠からは外す (DW-M03)、CP の破壊が検出されることの証拠には数える |
| M9 | 片側 Fisher を全台の和へ | KILLED | 6 | Fisher test・caption / 注記の p = 0.500・稿照合 |
| M10 | commit 平均の分母を 240 へ | KILLED | 6 | commit 平均 test・閉包・稿照合 |
| M11 | 図中注記の `not performance` を削除 | KILLED | 2 | 可視開示 test・着地 fig15 |
| M12 | 図の題へ `equivalent` を足す | KILLED | 2 | caption + 可視 Text の禁止句走査・実証拠 |
| M13 | publish 前の layout 検査呼出しを除去 | KILLED | 1 | `test_layout_failure_publishes_nothing` |
| M14 | 図中の曝露比注記 2 行を描かない | KILLED | 1 | 実証拠 test の可視検査 (外部 root 不在の環境では skip される) |

## 6. 計算ノードの使用 (P10)

裁定 inbox の控え (2026-09-21 vldb-direction 項 4 と追補) の線 (1 タスクで 2 node 時間以上なら事前確認) に対し、本 wave の計算ノード投入は
焦点走 2 回 (`15694.nqsv`、`15745.nqsv`、各 1 job・テスト本体 36.7 / 44.5 秒)、変異 final の 16 run (各 1 job、harness 記録の `duration_s` は 15 run が 32〜38 秒、M3 だけ 416 秒で内訳は未確認)、
provenance 全史監査 1 回と、この記録の後の受入全走である。実験の計算 (計測・探索・合成) は無い。記録時点でこの線を下回ると判断し、確認は求めていない。

## 7. 限定 — この記録と図が言わないこと

- 図は論文の結果節で使える**図素材**であり、論文本文・版・results 稿への組み込みはしていない。A-1 の充足・formal 化・L-A1S-4 の解除、mocc の certified 昇格・pin 前進を意味しない。
- fig14 と fig9 を並べて読むときも、2 attempt の差・比・区間の重なり・再現判定は作らない (D1993 項 6、D2194 項 6)。`variance_plan_breach` の原因は帰属しない。
- fig15 の repo 側閉包は provenance の自己整合であって外部原本との一致の証明ではない。外部原本との一致の検査 (`validate_external_sources` と実証拠 test) は外部 root が見える環境でだけ走る。
- 着地した fig15 の provenance は fix 前の生成器 (到達不能な 4 行を含む) で作られた。`generator.sha256` はその時点の記録で、fix commit の生成器とは異なる。描画・caption・provenance の値は同じ (fix 子の比較)。
- 受入全走と land の結果はこの README に書けない (この README を含む記録 commit の後に受入を投入するため)。

## 8. 観察 (本 wave では変えていないもの)

- 既存の fig9 / fig10 / fig11 / fig12 / fig13 節と一覧表の 1 行 (`docs/paper-story/figures/README.md`、`awk` で F36 を含む行を節ごとに列挙)、`tools/plotting/README.md` の既存 3 節
  (A-1 attempt-0001・B-7・K2 図の節)、attempt-0002 稿 §2.6、`docs/dev-wave/core.md` の `DW-S07` は、
  「稿は provenance の SHA-256 を持たない」の根拠に F36 を引いている。F36 本文は「結果欄のプレースホルダ」の型で、自己参照の規則を直接は定めていない。
  本 wave の新節は F 番号を外して理由を直接書いた。既存箇所の引き方を揃えるかは本 wave の scope 外。

## 9. 工数

- codex 子 10 本 (全て `gpt-6-astra` / `medium`、受領証の記録値): plan 15 call / 554 秒、consult A 16 call / 244 秒・B 13 call / 241 秒、author A-1 23 call / 686 秒・mocc 15 call / 728 秒、
  review A 11 call / 225 秒・B 9 call / 130 秒、fix A-1 10 call / 147 秒・mocc 15 call / 204 秒、focus 7 call / 146 秒。read-only 調査子 1 本 (Explore / sonnet、pin 閉包、59 tool use / 571 秒)。
- 親: login の plain runner、作図 2 回、README の機械転記 script、collect-only 1 回 (46 秒)、login の変異 probe 1 回、計算ノードの焦点走 2 回・変異 final 1 回。
- wave の壁時計は開始 gate 20:46 JST (`verbatim/startup-gate.log`) → この記録 commit まで。
