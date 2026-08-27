# 段 4 裁定 — 実装しない。裁定パッケージをユーザーへ返す

## 結論

**依頼の 2 つの条件は、この計算機では同時に成立しない。** よって本 wave は実装面を変更せず、
実測とともにユーザー再裁定へ返す (`DW-S04` の「承認済み裁定の前提を覆す未見の新事実」)。

依頼は次の 2 つを同時に求めている。

1. tip との byte 等値要求を落とす。
2. 「実行元を tested main の blob に固定する保護」は維持する。

実測の結果、**この計算機の受入全走では、pytest を実際に駆動するのは tested tip 側の
`tools/run_tests.py` (作業ツリーの file) であり、tested main の blob ではない。**
両者が今日一致しているのは、まさに落とそうとしている等値要求のためである。
したがって 1 を実施すると 2 は成立しなくなる。しかも成立しなくなるのは
**本変更が通そうとしている当の wave (実行器を編集する wave) についてだけ**である。

## 実測した連鎖 (すべて親が本 wave 中に実行)

| # | 事実 | 測り方 |
|---|---|---|
| 1 | この host は `PEGASUS_LOGIN`、queue `gen_S` は `ENA=ENA` / `STS=ACT` (待ち 33・実行 41) | `site_policy.current_site()` と `queue_state.dispatch_possible()` を実行 |
| 2 | その条件下で待ち手は受入 launcher へ `IZANAGI_ACCEPTANCE_SHARDS=3` を渡す | `tools/dev_wave_wait.py` `_acceptance_launcher_environment` |
| 3 | launcher は tested main の blob を `exec` するが、`__file__` に作業ツリーの canonical path を入れる | `tools/acceptance_launcher.py` `_RUNNER_BOOTSTRAP` (`'__file__': sys.argv[1]`) と `_run_blob` |
| 4 | 実行器は `__file__` から `_REPO` を導く → **wave worktree** | `tools/run_tests.py:55` |
| 5 | shard mode の LOGIN 実行は必ず dispatch する | `tools/run_tests.py` の LOGIN 分岐 (`if force_dispatch or shard_mode: return _dispatch_result(...)`) |
| 6 | dispatch は `repo_root=Path(_REPO)` を渡す | `tools/run_tests.py` `_default_dispatch` |
| 7 | 計算ノード側の子は `[python, <repo_root>/tools/run_tests.py, *argv]` を **pathname で**起動する | `tools/pegasus/dispatch_compute.py:1013` (`bnode*` hostname 検査の内側) |

したがって、受入の pytest を駆動する実体は `<wave worktree>/tools/run_tests.py` である。
launcher の main blob 実行が覆うのは、dispatch を決める外側の 1 プロセスだけである。

## この事実がなぜ「未見」か

- D838 の裁定文にも、実装 wave (archive worklog 960) の記録にも、dispatch 側の再入は書かれていない。
- `docs/pegasus-runbook.md` は「bounded / dispatch の内側の子は pathname を読み直すため実行 bytes の
  束縛外にある」と**残余としては記録している**。
- **記録されていないのは両者の相互作用である** — すなわち「tip 等値要求こそが、その残余の
  実害を消していた唯一の仕掛けである」という点。等値がある限り pathname 側の bytes は main と
  同一なので、残余は無害だった。等値を外すと残余が実害に変わる。

## 再開する脅威

D838 の裁定文が名指しした脅威そのものである。

> wave が実行器を書き換えるだけで実際は赤の走行を「子は緑」として着地させられる

等値を外した後、実行器を編集した wave は **自分が編集した実行器に自分を判定させる**。
受領証の `runner_executed_sha256` は main の値のままなので、受領証・land 結果・worklog の
どこを見てもこの差は現れない。事故モデル (D387) でも成立する — 実行器の編集が
うっかり選択集合を狭めれば、その wave の受入は自分の回帰を見逃したまま緑になる。

## 順序のデッドロック (ユーザー判断が要る核心)

dispatch 側の穴を塞ぐには、計算ノードの子も tested main の blob から実行させる必要がある。
その実装は `tools/run_tests.py` と `tools/pegasus/dispatch_compute.py` を編集する。
**`tools/run_tests.py` の編集は、いま外そうとしている等値要求そのものによって塞がれている。**

つまり「穴を塞いでから等値を外す」は現行契約では実行できない。
どちらを先にするかはユーザーの裁定が要る。

## 選択肢 (親の推奨は B)

- **A. 依頼どおり等値だけ外し、dispatch 側の穴は残余として受容する。**
  目的 ([T-1932] を含む実行器変更 wave の解禁) は即座に達成される。
  代償は上記の自己判定窓が開いたままになること。窓が閉じるのは dispatch 束縛 wave の land 後。
  D838 以降その file は 1 度も変更されていないので、母集合は小さく、各 wave は意図的である。
- **B (推奨). 等値の撤去と dispatch 束縛の実装を 1 つの wave に載せ、その wave だけ
  「実行器を編集した wave の land」を明示的に一度だけ認める。**
  受入の権威が一度も薄くならない。代償は、その 1 wave の land を通常経路の外で認める判断が要ること
  (親は迂回できないので、認可の形はユーザーが決める必要がある)。
- **C. 等値を維持し、[T-1932] は別経路で解く。**
  現状維持。既に D1103 が「既定値は変えない」と裁定済みで、受入経路だけの回避策は land 済み。

**親が B を推す理由:** A は「正しさゲートを一時的に緩めて後で戻す」形であり、
その窓の間に実行器を触る wave が 1 本でも通れば、その wave の受入は証拠として無効になる。
B は同じ結果を、権威を一度も薄くせずに得る。追加費用は認可の 1 手だけである。

## 段 3 所見の裁定

| 所見 | 判定 | 扱い |
|---|---|---|
| B-1 dispatch 経路で tip runner が実行される | **real (最重)** | 本裁定の根拠。実装停止の理由 |
| B-2 claim 後 merge が runner 変更 main を取り込んでも古い claim main を receipt に残す | real | 上記と同根。B の設計へ含める |
| B-3 D987 未実装、段 2 の positive test 案が D987 違反を固定する | real | 実装しないので発生しない。次の一手へ登録 |
| B-4 checker 受理経路 (ii) は D690 以降到達不能、runbook が古い | real・scope 外 | 本変更が原因ではない既存の docs 陳腐化。次の一手へ登録 |
| B-5 「既存の受領証は 1 件も変わらない」は未証明 | real | brief の過大主張。記録で言い方を狭める |
| B-6 D1103・T-1932・worklog の現在形記述への追随 | real | 実装時に必要。次の一手へ登録 |
| B-7 本 wave の受領証は旧 launcher の値になる | nit | 記録に残す |
| B-8 変異 harness は追加関門ではない | nit | 追認 |
| B-9 到達不能な `non-attributable-only` land 検証枝の存廃 | scope 外 | 裁定パッケージへ |
| A-1 実 Git reader の revision 束縛に mutation kill が無い | real | 実装時の必須テスト。次の一手へ登録 |
| A-2 tip runner の実在・blob 条件が片側 fixture で殺されていない | **real・等値の可否と独立** | 次の一手へ登録 (今日の関門の検出力不足) |
| A-3 caller 側 SHA 形式述語 2 行は恒真 | nit | 防御的重複として残す。保証として数えない |
| A-4 divergence 後に `retryable_same_request` / `release_safe` の分類が変わる | real | 実装時に受理集合差分の主張へ含める |
| A-5 実 E2E 2 本が同型 | real | A-1 と同一。統合 |
| A-6 削除対象は 2 か所 | 追認 | 親の実測と一致 |
| A-7 launcher 先例は完全な同型ではない (bootstrap mode、tip 実在要求の有無) | nit | 記録の言い方を狭める |
| A-8 変異 matrix の誤帰属候補 | real | 実装時の事前登録へ持ち越し |

## 段 2 プランの扱い

プラン自体は正確で、削除 2 か所・残す述語・テスト 3 分類・runbook 文案まで実装可能な水準である。
**破棄せず次 wave の入力として保存する。** 変更面の骨格が同一なら、
入口の規定により次 context は段 2・3 成果物を流用して段 4 から再開できる。

## 本 wave の成果物

実装面の差分はゼロ。記録するのは (1) dispatch 連鎖の実測、(2) 裁定パッケージ、
(3) 次 wave が即実行できる形の所見。受入全走は差分ゼロでも免除されない。
