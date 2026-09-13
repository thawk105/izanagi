---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2566-tail-formal-driver
seq: 1
title: [T-2566] 静的tail本走driverを実装し、投入前条件5件を実測で満たした
---

## 本文

- 依頼は事前登録 §8.1 の投入前条件 5 件を満たす本走 driver の実装。**本走の投入は行っていない。**
  5 件はいずれも production の経路を通して実測した。
- 段 3・段 6 の敵対レビューが、**正常な 3 走が必ず無効判定になる欠陥を 2 箇所で見つけた。**
  (a) 集団の同一性に測定順の先頭の格子点に依存する値を使っていた。3 走は設計上それぞれ別の
  workload を測るので先頭が違い、同じ checkout でも不一致になる。追跡 checkout の bytes から
  workload にも格子点にも依存しない digest を作る形へ直した。(b) 拒否時に失敗理由と観測値を伴う
  報告が出ず、例外で終わっていた。**直したのは拒否のしかたであって拒否するかどうかではない。**
  先行 wave T-2500 が事前登録の本文で作り込んだのと同じ型が、今度は実装側に出た。決定は
  {{D:static-tail-cohort-identity-and-refusal-reporting}}。
- **scheduler 問い合わせが別方式の JSON 形式を前提にしていた。** 親が実機で叩くと、この計算機の
  scheduler ではその指定は JSON を返さず項目一覧の説明を出して rc=0 で終わる。放置すれば本走は
  1 cell も測らずに冒頭で止まる。既存投入 script の text 解析を正本として合わせ、保存された実物を
  入力にした検査を入れた。失敗の型は {{F:scheduler-format-assumed-from-another-batch-system}}。
- 自由度が非整数の Student t 分位点で実装とテストが食い違い、**親が独立に高精度の数値積分と
  二分法で検算して、実装が正しくテストの期待 literal が誤っていた**ことを確かめた
  (期待値の累積確率が目標から 9.1e-9 ずれていた)。期待値の側を直した。真値 2.9430993234069955。
- **変異 12 件のうち 2 件が初回に生存した。** どちらも現在のテストに対して等価で、後段の別の検査が
  同じ例外を出していた。同じ byte 数の別語の fence と、小数点・符号・空白・指数表記の文字列を
  渡す否定例を足して実効 gate へ再照準した。**字句検査の緩和だけでは受理集合が変わらず、
  検出は診断文字列の違いによるものだと実測でわかった**ので、本走の変異は緩和と浮動小数経由の
  変換を同時に入れる形へ変えた。初回の生存結果は insight に残した。
- 段 5 の実装子 2 名は**テストを 1 件も走らせずに終わった。** 子の sandbox には scheduler の
  実行 file が PATH に無く、`tools/run_tests.py` の投入 preflight が rc=1 になって rc=16 で止まる。
  親が同じ木で自走 harness を叩くと普通に走る。以後の fix 子には自走 harness の叩き方を渡した。
  失敗の型は {{F:codex-sandbox-lacks-scheduler-binary}}。
- 段 8 の自己改善は 1 件を failures 台帳へ送って閉じた。dev-wave の手順書側へ 1 行入れようとしたが、
  **L1.5 層の予算に余地が無く (9696 byte 上限に対し追記で 9930〜9998 byte)**、
  安全記述を削って空ける形は契約が禁じている。独立実例は 2 件で D730 の例外収容 (3 件以上) に
  届かないため、上限は引き上げず、恒久対応は
  {{F:codex-sandbox-lacks-scheduler-binary}} の恒久対応欄に残した。
- 投入経路の配線 (既存投入 script・job script が旧 3 系列しか受理しない、3 走を 1 集団として
  集める入口が無い) は依頼の境界により scope 外とし、裁定パッケージとして返す。
  **「§8.1 の 5 件が外れ、残る blocker は投入経路の配線 1 件になった」**が正しい言い方であり、
  「唯一の blocker が外れた」とは書かない。
- Codex 子 10 本 (plan 1 / consult 2 / author 3 / review 2 / fix 4)。review 2 本は
  `--reasoning` が段別に禁止されている argv 誤りで 1 度 rc=2 即死し、同じ prompt を投げ直した。
  fix 第 1 巡では wrapper が完了 file を落としたが、launcher の receipt が
  `outcome=accepted` と成果物 hash を封じており、hash 照合で完了を確かめた。
- 成果物と生証拠 = `output/insights/2026-09-14_t2566-tail-formal-driver/`。

## 次の一手差分

### 完了

- [T-2566] 事前登録 §8.1 の投入前条件 5 件を満たす本走 driver を実装し、production の経路を
  通して実測で確かめた。本走の投入は行っていない。
  remaining: none
  base: fe7e6e889fff007f02426e306d9e91afcae9184926dda3c269079db6955aa613

### 新規

- {{T:static-tail-submission-wiring}} **P1・新規**: 静的 tail 本走の投入経路を配線する。
  `tools/pegasus/submit_b10_backoff_grid.sh` と `tools/pegasus/b10_backoff_grid.sh` が
  新しい走行種別 `t2500-tail-formal` と成果物 stem を受理し、job script が新 driver を起動し、
  完了確認が新 stem を見るようにする。3 走の成果物を 1 集団として集める投入側の入口も要る。
  **これが本走投入に残る唯一の blocker である。**
