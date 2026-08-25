---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1622-resume-acceptance-boundary
seq: 1
title: [T-1622] 起動 gate と受入 post-claim merge の境界を正本・checker・E2E で固定した (コード + docs、branch worktree-dev-wave-t1622-resume-acceptance-boundary、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段 1 の暫定裁定を段 4 で撤回した。** 親は「resume mode の behind-only を専用 rc で分類すれば
  誤適用を機械検出できる」と暫定裁定したが、段 3 の 2 レンズが独立に反証した。checker は
  呼び出された時点が session 開始か受入直前かを**観測できない**ので、専用 rc が分類できるのは
  状態であって時系列ではない。しかも「rc=3 なら受入へ進んでよい」と読める間接 bypass の
  affordance を作る。exit code を増やさず診断の二分だけを固定する裁定へ変えた
  ({{D:resume-gate-boundary-diagnosis-not-exit-code}})。
- **段 2 起動後に未見の新事実を 1 件見つけ、裁定を 1 点変えた。** F524 が F522 の恒久対応へ
  前提条件を足しており、取り込む差分が束縛実行体 (待ち手・launcher・runner) の bytes を変えるなら
  親が先に取り込む必要がある。これを知らずに E2E を書くと F524 が禁じた形を test が正典化する。
  brief へ出して段 3 の両レンズに攻撃させ、段 4 で byte 中立性の明示 assert を必須にした。
  `DW-O18` / `DW-O27` への契約同期は [T-1628] の scope なので本 wave では触っていない。
- **段 3 のレンズ B が E2E の中心命題の破れを見つけた。** 既存 fixture をそのまま使うと
  `HEAD == main` になり、**fresh gate でも通るので resume 経路を踏まない**。wave 側に先行 commit を
  1 件作り「resume は通るが fresh は落ちる」形にした。これが無ければ、この wave の E2E は
  境界を 1 bit も検査していなかった。
- **段 6 のレビュー A の must-fix 1 件を親が反証した。** 「stub runner に `__main__` 入口が無いので
  child が動かない」という指摘だったが、実物の launcher は runner の source を `exec` して
  `namespace['main'](argv)` を呼ぶ契約である。既存 fixture も同じ形で緑になっている。
  子の指摘を実物で裏取りしてから採否を決めた。
- **レビューが採った must-fix 3 件はいずれも「緑のまま残る穴」だった。** (a) checker の受入案内が
  無条件で F524 と矛盾する、(b) fixture が byte 中立なので launcher の**選択元**を
  `tested-tip-bootstrap` へ壊しても E2E が緑のまま (receipt の `launcher_source_revision` /
  `authority_kind` / `launcher_blob_sha` を assert していなかった)、(c) PATH で検証した実行体と
  実際に名前解決される実行体が別になりうる。
- **変異が「この E2E は何を守らないか」を実測で確定した** ({{D:boundary-e2e-is-composition-not-line-gate}})。
  待ち手側の 4 変異 (post-claim の behind 分岐・merge・commit・message) は新設 E2E も殺すが、
  既存の `test_dev_wave_wait.py` が同時に 16〜36 node で殺す。**単独行に対する純増検出力はゼロ**である。
  純増は checker 診断から F524 条件を削る変異 (新設 checker test 3 件でのみ KILLED) だけだった。
  登録済みの対照 MUT-7 (containment 検査を無条件成功) は予測どおり checker 負例 8 件で死に、
  E2E は緑のままだった。境界は単一の production 行に存在しないので、単独変異では分離できない。
  **「E2E が変異を N 件殺した」とは書かない** — 正しい主張は「2 つの production CLI 間の
  時系列結合を固定した」である。
- **変異 1 件が非決定的で登録し直した** ({{F:mutation-double-launch-nondeterministic}})。
  launcher 二重起動の変異は競走を含み、probe 7 node / 本走 2 node と食い違った。
  同じ性質を決定的に測る形 (同一 log stream 内で runner を逐次 2 回実行) へ再照準し、
  6 node (新設 E2E を含む) で KILLED・期待一致を得た。
- **正本は追記でなく圧縮で入れた。** `DW-O20` は L2 単節予算 1000 bytes に対し 984 bytes で、
  残余は約 5 文字しかなかった。既存の安全義務 10 項目を 1 つも落とさずに約 60 字を圧縮し、
  境界の 2 文を入れて 995 bytes に収めた。予算値の変更は自己改善の対象外なので行っていない。
- **この E2E が裁定しないことを明記する。** 実物 `tools/run_tests.py` の収集内容、dispatch 回数、
  leaf subprocess 回数、provenance 実装の正しさ、linked worktree・実 submodule・共有 lease の
  競合・claim 後の再前進は、fixture が stub と合成 repo である以上この test では裁定できない。
  また receipt の `raw_child_rc` は OS の raw rc ではなく、launcher が signal を正規化した後の
  値の複製である。成功時の 0 検査は正しいが、raw と normalized の意味差はこの test では見ていない。
- **段 8 の自己改善は候補 4 件を裁定し、command / reference の編集はゼロだった。**
  (1) `DW-O20` の byte 予算に実効的な余地が無い件は予算値の変更にあたるため裁定パッケージへ。
  (2) 段 2 起動後に brief を更新したときの既起動子の扱いは、入口の「覆す新事実は brief に出して
  段 4 で再裁定する」から導けるので新規則不要。(3) `--reasoning` が author / fix / review 段で
  指定不可という制約は `DW-O01` に既にある。(4) 待ち手の完了通知が先行する事象も
  `DW-O01` の「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない（通知は先行しうる）」
  が既に禁じているので、記録先は failures の再発だけでよい。
- **背景 job の待ち手が producer 生存中に完了通知を返す事象を 5 回観測した** (F24 の再発 near-miss)。
  実害はゼロ。`.done` の実在を判定に使う既存の恒久対応がそのまま効いた。
- 子は 6 単位とも pytest 実走不能 (`qstat -Q` preflight rc=1、sandbox の構造的制約)。
  **本 wave のテスト結果はすべて親の実測**である。
- **ユーザー裁定へ返す件**: 呼び出し時点の誤適用を checker が自動で止めるには、session 開始 gate の
  成功を wave・repo・branch・session epoch へ束縛した phase token として発行し、受入側で消費する
  lifecycle 層が要る。本 wave では実装していない。T-1622 の「機械検出」をこの層まで含めて要求するか、
  正本 + テストによる契約固定で閉じるかはユーザーが決める。

## 次の一手差分

### 完了

- [T-1622] 起動 gate と受入 post-claim merge の境界を、正本 `DW-O20`・checker の診断・
  新設の subprocess E2E の 3 面で固定した。checker は exit code を増やさず診断を二分し、
  E2E は wave-ahead な worktree で gate 成功後の main 前進を単一の待ち手が取り込み
  runner を 1 回だけ起動する時系列を 1 回の決定的走行で固定する。
  runtime の機械検出には別の lifecycle 層が要ることを実測で確定し、裁定へ返した。
  remaining: none
  base: c939a475081c8bd8cd6ee203b51366a3a2f40d1e0c9f67d62ea27f58c09a5aed
