---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: t1312-evidence-grace-origin
seq: 1
title: 子の証拠猶予の起点を子の起動完了時へ移した (D498) — 判別テストは論理時計で 3 起点を分離し、変異 5 件を全件殺した (コード + テスト、branch worktree-t1312-evidence-grace-origin)
---

## 本文

- D498 の実装。`--evidence-grace-s` の deadline 起点を、試行記録の作成時
  (`AttemptState.started_ns`) から子の起動完了時 (`spawn_completed` 境界) へ移した。
  production 差分は `tools/codex_worker_launch.py` の 3 行で、時刻サンプルを診断条件の外で
  1 回だけ取り、診断境界と deadline が同一値を使う形にした。`max_wall_clock_s` の判定式・
  起点・既定値・検証は触っていない。attempt wall clock の起点も `state.started_ns` のまま。

- **段 3 の敵対 2 レーンが独立に同じ最重要欠陥を挙げた。** 段 2 プランの判別テストは
  論理時計を preflight 区間でしか進めないため、deadline 起点を preflight 完了時刻に置いた
  実装も同じ結果を出し、テストを通ってしまう (恒真ゲート)。裁定で spawn 区間にも
  異なる正の値を注入する形へ差し替えた。preflight 0.10 秒 / spawn 0.02 秒 / poll 0.01 秒、
  猶予 0.05 秒とすると、`supervision_drain` は旧起点 0.01、preflight 起点 0.03、
  正しい起点 0.05 に分離する。3 値すべてを exact で assert する。

- **F57 の実機序は attempt 2 だった** (レンズ A の S3)。attempt 1 だけを検査する判別テストは
  「attempt 1 は新起点、retry は旧起点」という実装を通す。`max_attempts=2` と
  `FAKE_SEQUENCE="retry_reject,no_rollout"` の retry 判別 node を足した。変異 M04 がこれを
  実証し、retry node 1 本だけが赤になった。

- **本変更が新しいフレーク形態を導入する経路を、レンズ B が見つけた** (L4)。
  起点移動後の evidence deadline は `attempt 開始 + preflight + spawn + 猶予` に位置するため、
  猶予 1.0 秒固定の既存 fixture は `max_wall_clock_s=3` に対する余裕が縮み、
  負荷時に max-wall が先に発火して evidence 関門テストが別の理由で赤くなりうる。
  evidence 関門を検査する既存 3 本の猶予を 0.3 秒へ下げた。これは fixture の hardening で
  あり production の受理集合は触らない。さらに段 6 レビュー A の指摘 (A2) を受け、
  `no_rollout` の 2 本には `session_ids` 非空の検査を足した。猶予を短くしたことで
  「session は見えたが rollout が無い」ではなく「session がまだ見えない」側で関門が発火し、
  本来の検査対象を一度も観測しないまま通る余地があったためである。

- **help 文言の 1 語追加が、無関係に見える既存テストを落とした。** `--evidence-grace-s` の
  help 先頭へ語句を足したところ、argparse の行折り返し位置が動き、既存 assertion の
  literal `--max-wall-clock-s` が `--max-wall- clock-s` に割れて落ちた
  (`_help_option_block` は改行を空白 1 個へ潰すため復元できない)。
  旧文面を byte 同一の前方 prefix として復元し、新語句を末尾の独立した空白区切り chunk
  として足す形で解決した。textwrap は `break_long_words=True` のため、
  長い chunk を末尾へ連ねるだけでは任意位置で割られうる (段 6 レビュー B の指摘)。

- **login ノードでの焦点走は判定に使えなかった。** 32 worker で 3 file 633 item を走らせると
  launcher 系が 68 件赤になったが、計算ノードでは同じ集合が緑だった。**この 68 件は
  本 wave の修正を適用した木で出ている** — preflight が猶予を食い切る機序を除いても、
  login ノードの過負荷下では F57 署名の赤が残る。判定に使ったのは計算ノードの走行だけである
  (F57 へ再発として記録)。

- 変異 matrix は 5/5 KILLED。M01 は wave 前の実コードの形 (旧起点) そのもので、狙いどおり
  新設 3 node が赤になった。**本走 1 回目は baseline が F285 族のフレークで赤になり中止した。
  `--resume` は baseline を再走しない (`baseline=0 run(s)`) ため、新しい scratch と出力 path で
  最初から走らせ直す必要があった。** 2 回目は 4 KILLED / 1 MISMATCH で、MISMATCH の M03 は
  指名 node が正しく発火しつつ環境フレーク 9 件が相乗りして完全一致を崩したものだった。
  M03 を単独 spec で再走して完全一致の KILLED を得た。初回の観測集合は erratum として
  insight へ残した。

- 段 3 レンズ A が挙げた「`max_wall_clock_s` は物理的な launcher 総所要を有界化していない」
  は real だが D498 の scope 外と裁定し、実装せずユーザー裁定へ返す
  ({{T:launcher-wall-clock-bound-semantics}})。本 wave の不変条件としては、
  「総所要の有界化」を receipt の admission bound の意味で読む。

- レンズ B の L3 (既定 90 秒では起点移動で max-wall との発火順が変わりうる) は real だが
  欠陥ではない。D498 が「総所要は `max_wall_clock_s` が有界化する」と定めた帰結そのもので
  あり、先に max-wall が止めるため受理集合は広がらない。記録のみとする。

- D286 は「既定 5 秒の evidence grace 内に起動イベントが出ない」と書いており、起点を
  試行記録の作成時と誤読しうる。D498 が新起点を定めた後の読み手のために、両者の関係を
  ここに残す (台帳本文は改めない)。

- 段 8 の自己改善は候補 2 件。help 折返しの罠は
  {{F:argparse-help-rewrap-breaks-literals}} として台帳へ落とし、memory へ手順を置いた。
  もう 1 件 (「候補となる起点が複数ある判別テストでは、隣り合う起点の**間すべて**に
  異なる正の値を注入する。1 区間でも 0 のままなら、そこを起点にした実装が同じ結果を出して
  テストを通る」) は `docs/dev-wave/` の既存 leaf 節へ統合すべき手順だが、
  同 docs は 3 層とも予算満杯で 1 行も入らない。`DW-S08` に従い実装せず
  {{T:mutation-origin-interval-injection-rule}} としてユーザー裁定へ返す。

- 工数: codex 子 7 本 (plan 1 / 敵対相談 2 / 実装 1 / 敵対レビュー 2 / fix 1)、いずれも
  receipt は accepted。実装子と fix 子はいずれも pytest を実走できず
  (`qstat -Q preflight rc=1`、runner `rc=16`)、所見を `closed` と申告せず
  「実装済み・未実走」と報告した。実測はすべて親が行った。
  逐語は `output/insights/2026-08-18_t1312-evidence-grace-origin/`。

## 次の一手差分

### 完了

- [T-1312] D498 を実装した。deadline 起点を子の起動完了時へ移し、判別テストで 3 起点を
  分離した。変異 5 件を全件殺した。
  remaining: none
  base: f30bac93753a2234bd8275ae367717ba9c78647f45340cd79a9c5d18a45057ad

- [T-1298] 修理は D498 の実装で閉じた。preflight が猶予を食い切る機序は消えた。
  3.6 倍の内訳は引き続き詰めない。ただし login ノード過負荷下では別機序で F57 署名の赤が
  残ることを実測した。
  remaining: none
  base: 9b872efda5c1ebfc5a89ad506fd01ef5337897afce2516b0db28aeb8d7596d11

### 新規

- {{T:launcher-wall-clock-bound-semantics}} **P2・ユーザー裁定待ち**:
  `max_wall_clock_s` は receipt の admission bound であって launcher process の物理的な
  hard cap ではない。最初の wall 検査より前に preflight が走り、limit 到達後も termination
  grace と reap が続き、成功経路でも最終 latch 後の receipt 公開に wall 再検査が無い。
  択 (a) 現状の意味を明記して閉じる。択 (b) 物理 hard cap を要求し外部 watchdog まで scope に
  入れる。親推奨は (a) — (b) は新機構を要し絶対規律 5 に抵触する。

- {{T:mutation-origin-interval-injection-rule}} **P3・ユーザー裁定待ち**:
  候補となる起点が複数ある判別テストでは、隣り合う起点の間すべてに異なる正の値を注入する
  規則を `docs/dev-wave/` へ入れたいが、3 層とも予算満杯で 1 行も入らない。本 wave では
  段 3 の敵対 2 レーンが独立に指摘して救われたが、レンズが 1 本なら恒真ゲートのまま
  land していた。択 (a) 予算内の既存節を意味等価に縮約して収容する
  (同族 docs で exact pin を壊した実績があり危険)。択 (b) 新規 L2 節を作る
  (D271 の鏡像 3 条件の充足審査が要る)。択 (c) docs へ入れず memory 止まりにする。
  親推奨は (c) — 本 wave の救済は敵対レンズ 2 本という既存の仕組みが機能した結果であり、
  新しい義務を足さずに済む。
