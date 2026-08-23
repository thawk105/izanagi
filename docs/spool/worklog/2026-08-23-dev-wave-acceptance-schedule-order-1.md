---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-schedule-order
seq: 1
title: 受入全走の投入順を所要降順にした。43.5 秒はスケジューリングの遊びだったが、削除は効かないと実測で確定した (コード+テスト+記録、branch worktree-dev-wave-acceptance-schedule-order、変異 matrix = baseline PASSED・MUT 11/11 KILLED・SURVIVED 0)
---

## 本文

- 依頼は「受入全走の改善。不要な価値の低いテストを削除するとか、テストのボトルネックを
  より賢くより技術的に解決する。必要に応じてウェブ検索してもいいよ」。
  設計判断は {{D:acceptance-duration-order}} と {{D:acceptance-test-deletion-null}}、
  失敗は {{F:silent-key-mismatch-noop}}、{{F:lpt-sync-window}}、
  {{F:invariant-overclaimed-as-outcome}}。

- **親の最初の主張は間違っていて、段 2 の plan 子が崩した。** 親は前 wave の一次資料から
  「投入順の遊びは 70 秒」と brief に書いた。plan 子が `xdist/plugin.py:130-141` を読み、
  **`--loadscope-reorder` の既定が `True`** であること、つまり受入の実既定は collection 順では
  なく件数降順の安定 sort であることを指摘した。親が実 source で裏取りして撤回した。
  さらに親が `_reschedule` の先取り緩衝 (pending<=2 で 1 unit ずつ補充) を event driven で
  model へ入れ直したところ、実既定 155.3 秒 / LPT 111.8 秒 / **利得 43.5 秒**になった。
  当初の 70 秒は先取りを無視した楽観 model の産物である。

- **plan 子は「scheduler option を無効化しないと LPT は完遂できない」と書いたが、これも親が反証した。**
  collection を所要降順にすれば、後段の件数安定 sort を通しても同じ 111.8 秒になる (差 0.0 秒)。
  件数上位 3 unit (103.0 / 103.0 / 14.9 秒) が所要でも上位だからである。
  これにより **D390 / D393 への裁定要求が消え、変更面が collection の並べ替えだけになった。**

- **親の provisional 裁定 (P1) 「未知は先頭寄せ」は実測で逆効果と判明し、撤回した。**
  欠落 1.3% で 166.2 秒 (実既定 155.3 秒より遅い)。原因を instrument して特定した —
  LPT の利得は「重い unit が先頭 96 (= 48 x 2) の同期配布窓に入る」ことに依存し、
  未知を前に置くと重い unit が窓から落ちて 1 台が連続で抱え込む
  (実測で 1 worker が 81.66 + 60.17 + 60.17 = 202 秒を直列、最速 worker は 109.5 秒で遊び)。
  5 案を seed 7 本で比較し「未知 = 既知の第 96 位」を採った ({{F:lpt-sync-window}})。

- **「価値の低いテストの削除」は効かないと実測で確定した。削除 0 件で閉じた。**
  0.01 秒未満が 7750 件で合計 15.1 秒 (wall 換算 0.31 秒)。並べ替え後は wall = 直列総和 / 48 に
  なるので削減の 1/48 しか効かず、103 秒の排他鎖が床なので**余地は最大でも wall 8.8 秒**である。
  高コスト側を実ファイルで確認したが削除できるものは 1 件も無く、すべて
  「同じ前置きを何度も払っている」型だった ({{D:acceptance-test-deletion-null}})。

- **段 3 の敵対 2 レンズと段 6 のレビュー 2 本が計 19 件の所見を出し、親が全部裁定した。
  blocker は 7 件で、最重要は「生成側と消費側の key がずれても赤にならない」だった。**
  新設 26 gate のうち消費側を検査するものが**期待値を消費側の関数そのもので生成**しており、
  自己整合なので両側がずれても全部緑になる。台帳が全件未知になれば並べ替えは静かに no-op へ落ちる。
  対策として「実台帳 x 実 collection の被覆率 >= 90%」gate を置いた ({{F:silent-key-mismatch-noop}})。

- **不変条件の書き方が誤っていたことも段 6 が示した。** 「台帳の障害は順序の質だけを変える」と
  「順序を変えても outcome は変わらない」を 1 文にまとめていた。後者は順序依存のテストがある限り
  成立しない。2 つに分け、後者は「本 repo の受入が既に要求している前提」と位置づけ直した
  ({{F:invariant-overclaimed-as-outcome}})。

- **段 5 の実装子 B は仕様どおり台帳生成を拒否した。仕様のほうが過剰だった。**
  実物の受入 junit が `failures="10"` の赤走行で、親の仕様が「failures/errors が 0」を要求していた。
  B は拒否条件を弱めず止め、診断用に repo 外で除外版を作って確認し、それを削除した。
  親が裁定を改訂し (R1)、「failure/error の testcase は除外して残りを受理」へ広げた。
  順序台帳は正しさに一切影響しないので、赤走行の junit を丸ごと拒否する理由が無い。

- **fix は単位 A で 4 巡になった。** `DW-O16` の 3 巡上限を超えた理由を裁定へ記録した。
  A4 の後に残った赤は 1 件で、レビュー所見ではなく**本 wave が新設した test helper の 1 行**だった
  (`--collect-only` 走で `config.getvalue("loadgroup")` が `ValueError` -> INTERNALERROR)。
  親が計算ノードで内側 subprocess の逐語を採り frame 単位まで特定した。
  受入が緑でなければ land できず、削除・skip・xfail は禁じられているので、
  「未解決の所見への 4 巡目」ではなく「診断済みの 1 行欠陥への指示」と裁定した。

- **子は 1 度も pytest を実走できなかった。** 実装子 2 本・fix 子 5 本すべてが
  `qstat -Q preflight rc=1` で child 未起動になり、「実装済み・未実走」と正しく申告した。
  親が数分後に叩くと rc=0 で、一過性である。**実走はすべて親が行った** (焦点走 5 巡)。

- **live gate 11 件がこの機体で構造的に走れない問題を 2 段階で踏んだ。** `pytester` は
  `HOME` を tmp へ差し替えるが、この機体の pytest は user site にあるため内側 subprocess が
  `No module named pytest` で即死する。`PYTHONPATH` へ user site を足すと今度は
  `No module named 'orchestrator'` になり、repo root も要った。
  親が `HOME=/tmp` の再現と `PYTHONPATH` 付きの成功を実測して裏取りしてから子へ渡した。

- **待ち手の失敗を 2 種類踏んだ。** (1) `tools/dev_wave_wait.py producer` が成果物なしで
  rc=0 を返す事象が同一 wave で 2 回再現した (どちらも出力ゼロ・約 7 分)。tool の
  `wait_for_producer` は `.done` と artifact が揃うまで `RC_OK` を返さない構造なので、
  外側 (背景 job の harness) が待ち手 process を回収していると見るのが自然。
  (2) 代替として使った Monitor も**完了イベントを 2 回誤報**した (`.done` が存在しないのに
  `DONE rc=0` を出した)。**`DW-O01` の「完了は `.done` と exit code だけで判定し、
  通知を判定にしない」に従っていたので 4 回とも現物照合で救えた。**

- **peer session と [T-1563] の交絡を共有した。** 「worker 数を減らすと速い」という観測を
  現行の投入順のまま測ると、投入順の遊び (n=16/32/48 で 21.1/60.3/69.8 秒) を worker 数の
  効果として帰属してしまう。ただし親の simulation では所要固定なら n=48 が n=32 より速く、
  実測と向きが逆なので**機序は別**である旨も併せて伝え、peer が [T-1563] の測定設計へ
  条件として記録した。

- **scope 外と裁定した所見が 5 件ある。** (1) controller の `worker_collection.index()` は
  test ごとに 14467 要素の線形探索をしており、未解明の残余 61.3 秒の候補である。
  (2) parametrize 族 1637.4 秒 (総 work の 30.5%)、(3) pytest を subprocess 起動する上位 4 file の
  724.2 秒、(4) worker 数の対測定 ([T-1563] 側)、(5) resource-aware grouping。

- **実台帳が「失敗 10 件の不在」を独立に証明していないことは限界として残る。** source junit は
  repo 外にあり、repo 内の gate から検証できない。除外の正しさは生成 tool 側の gate が担保する。
  `--junit-prefix` を付けた junit から誤った key を「正常に」生成しうる経路も partial のまま残る。

- **変異 matrix: 11/11 KILLED、SURVIVED 0。** baseline は 2 走とも PASSED (失敗 node 0)。
  全件 SURVIVED 期待の probe を先に回し、観測 node を expected へ焼いてから本走した。
  **harness の表現力の制約を 1 件踏んだ。** 観測 node に内側 pytester 走の node
  (`test_sample.py::test_fail`) が混ざるが、harness は期待 node としてそれを
  「pytest collection に実在しない」と拒否する。exact 一致が原理的に成立しないので、
  内側 node を出す唯一の gate (`test_g5_two_ledgers_preserve_outcomes_skip_markers_and_properties`)
  を `--deselect` した argv で m01 / m07 だけ再走し、13 / 9 node の完全一致で KILLED を得た。
  単独 node で kill するのは m08 (identity 検査を `assert` へ戻す)、
  m15 (消費側の key から `@group` を落とさない)、m16 (生成側の module 一意性検査を外す) の 3 件で、
  単一理由性が明確である。m01 (13 node) と m07 (10 node) は過剰決定で冗長 gate と明記する。

- **`--runner-mode dispatch` から `local` へ切り替えた。** probe は dispatch で 12/12 走完走したが、
  本走の baseline が `PARSE_ERROR` で止まった。`run_tests.py` が login node の余裕を見て
  local 実行を選び、dispatch receipt 行を 1 行も出さなかったためである
  ({{F:mutation-runner-mode-coupling}})。`--attempt-out` / `--wrapper-attempt` は
  dispatch 専用なので同時に外した。

- **子の工数 (receipt 実測):** codex 子 13 本。内訳は plan 1 / consult 2 / author 2 / review 2 / fix 6。
  全て `gpt-5.6-sol`、`reasoning=xhigh`、`outcome=accepted`。
  **13 本すべてが pytest を 1 件も実走できなかった** (`qstat -Q preflight rc=1` で child 未起動)。
  全員が「実装済み・未実走」と正しく申告した。実走は親が焦点走 5 巡で行った。

## 次の一手差分

### 新規

- {{T:acceptance-controller-overhead}} **P2・新規**: 受入の未解明残余 61.3 秒のうち、
  controller の `worker_collection.index()` (test ごとに 14467 要素の線形探索) と
  `_pending_of` の累積再走査が占める量を分離計測する。
  {{D:acceptance-duration-order}} を入れても残る固定費であり、
  「安いテストを減らしても wall に効かない」が未証明である理由でもある。

- {{T:acceptance-repeated-setup}} **P2・新規**: 受入の高コスト側にある
  「同じ前置きを何度も払っている」型を共有化する。実測した候補は
  parametrize 族 1637.4 秒 (総 work の 30.5%、1175 族)、pytest を subprocess 起動する
  上位 4 file の 724.2 秒、`test_s8c_preregistration_predicates.py::test_current_repository_*`
  6 件で計 206.5 秒 (同じ repository snapshot 走査の繰り返し)、
  `test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo`
  40 case で 45.2 秒 (`git ls-files` を 40 回 spawn)。
  **削除ではなく共有化**であり、{{D:acceptance-test-deletion-null}} の限界節に対応する。

- {{T:acceptance-duration-ledger-refresh}} **P3・新規**: 所要台帳の定期再生成の運用を決める。
  被覆率 gate が 90% を下限にしているが、再生成の契機は誰も持っていない。
  値の精度は要らない (4 倍ずれても makespan 不変) ので頻度は低くてよい。
  現在の被覆率と、90% を割るまでに増やせるテスト件数を実測して決める。

- {{T:acceptance-order-dependence-audit}} **P2・新規**: 受入 suite の順序依存を能動的に調べる。
  {{D:acceptance-duration-order}} は順序を大きく変えるので、潜在的な順序依存があれば
  受入全走が赤になって露見する。露見を待つのではなく、
  module / session scope fixture と `tmp_path_factory` の連番と共有 output tree の
  first-writer 判定を静的に棚卸しし、順序依存の実在を先に測る。
