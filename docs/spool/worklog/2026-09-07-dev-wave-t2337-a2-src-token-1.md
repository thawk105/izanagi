---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2337-a2-src-token
seq: 1
title: [T-2337] A-2 の canonical identity を pin + patch 束縛の src_token で計算し、受領証を独立権威にした (コード + テスト、branch worktree-dev-wave-t2337-a2-src-token、焦点走 652 件緑)
---

## 本文

- D1644 案 1 を実装した。認証 driver は `run_workload` の関門文脈内 (patch がまだ revert されて
  いない位置) で cell ごとに source evidence を解決し、その src_token で variant id を計算する。
- **段 1 の実測で D1644 の述語の到達可能性を確かめた。** 使い捨て probe を Codex author に書かせ、
  親が login node で実走した。patch 済み隔離木では stock cell が `stock`、adopted cell が非 `stock`
  になり、patch 未適用の木では 4 cell とも `stock` になった。現行 driver の期待値は後者と一致する。
  D1644 の言う誤分類 (patch が効かない木を通し、効いた木を拒む) が実測で裏付いた。
  **本番の cxx は `g++-13` でこの機体には login にも compute にも存在しないため、probe は
  `g++-12` で測った。** patch 前後を同一 preprocessor で一貫比較するので stock / 非 stock の
  判定には答えられるが、digest の値そのものは本番と異なる。本番条件は未実測である。
- 段 3 のレンズが、段 2 プランの凍結再構成が raw 自身の src_token を期待値にしており
  D1644 が却下した案 2 (記録された値をそのまま確かめる恒真判定) へ戻ると指摘した。親はこれを採り、
  裁定 3 の「campaign より前に保存する受領証」をそのまま独立した期待値の出所にする形へ変えた。
  2 つの裁定が 1 つの機構になった。
- 段 6 のレンズ 2 本が must-fix を 2 件出した。(1) 受領証 authority の失敗が tracked artifact を
  作った後の停止になっており、同じ token 欠落が raw 側なら確定的な拒否、受領証側なら判定不能に
  なる非対称があった。(2) 新 full manifest と legacy partial manifest が同じ schema 名を持ち、
  中身の意味 (受領証の有無) が違っていた。両方とも fix で閉じた。
- 親の解釈: D1644 の「新 file 1 つ」は campaign 1 つにつき受領証 file 1 つと読んだ。
  A-2 は workload ごとに独立した campaign を別 job で起動するため、全 workload に先立つ
  単一 file は原理的に書けない。裁定の目的 (campaign 後に落ちても受領証が残る) はこれで満たされる。
- 段 5 の実装子は model call 上限 100 回に達して打ち切られ、完了報告を書かずに終わった
  (`control_limit_trigger=max_model_calls`、28 分、29.5 万トークン)。成果は保全して実走で
  127 件緑を確認し、裁定 8 項目がすべて実装済みであることを親が照合した。以後の子は上限を上げた。
- 変異の事前登録は 16 本のうち 10 本だけが単一の理由で赤にできる。残り 6 本 (M1 M4 M7 M8 M10 M16) は
  複数 node が同時に落ちて帰属が成立しないと段 6 のレンズが静的に判定した。
  {{D:a2-src-token-receipt-authority}} の方針どおり、確定できないものは登録しない。
- scope 外として裁定パッケージへ返した real 所見は {{D:a2-src-token-receipt-authority}} に書いた。

## 次の一手差分

### 完了

- [T-2337] D1644 案 1 を実装した。関門文脈で cell ごとに source evidence を解決し、
  campaign より前の受領証を凍結再構成の独立した期待値にした。裁定 3 と裁定 4 も同梱した。
  A-2 の新 attempt 取り直しは本 wave の scope 外で、{{T:a2-src-token-rerun}} へ送った。
  remaining: none
  base: 76c0f0898f8663fd817e963f06cf411e43af9b859be2e99da6b9819f211008bc

### 新規

- {{T:a2-src-token-rerun}} **P1・新規**: 新しい identity で A-2 attempt を取り直す。
  取り直しの前に {{T:a2-figure-v4}} を済ませないと図が作れない。
- {{T:a2-figure-v4}} **P2・新規**: `tools/plotting/plot_a2_certification.py` を新 schema へ対応させる。
  同 file は schema を厳密一致で要求するので、凍結済みの旧版は読めるが新版の certification では
  図を作れない。A-2 取り直しの前段。
- {{T:a2-full-report-rederivation}} **P2・新規**: full certification の materializer に exact 再導出を
  入れる。partial 側は acquisition から再導出して一致を要求するのに、full 側は外形と identity しか
  見ない非対称が既存で残っている。本 wave が作った欠陥ではなく受理集合も広げていないため scope 外とした。
