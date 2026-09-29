---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-target-policy
seq: 3
---

## 新規

### {{F:positive-control-unreachable-on-policy-path}}. 壊し正例を、検査したい方策の構造上その壊れ方が起きない経路に置き、到達 0 の検査を 1 巡走らせた [テスト代表性]

- 事象: VHash md_21 で、前進先の方策 E-max の壊し正例 (確認での既読不一致を ok とみなす) を E-max で走らせるよう段 4 で設計した。E-max は既読の可視区間の内側に目標を取るので確認で既読不一致が構造上ほぼ起きず、検査 1 回目 (request 36358) で壊しの到達は 0 (forced_success 0)、同じ run の E-max の確認での既読不一致も 0.0 だった。壊しを E-now で走らせ直して (fix 4)、2 回目で到達 5,449・5,993 と保持版検査の検出を得た。段 3 の相談 2 本・段 6 のレビュー 2 本は指摘しなかった。
- 根本原因: 正例の設計で「壊す判定」を選ぶとき、その判定が検査対象の方策で実際に偽になる入力が生じるかを確かめなかった。目標の選び方が確認の前提を満たすように作られている方策では、確認を壊しても到達しない。
- 恒久対応: 親の永続 memory へ `positive-control-must-reach-on-target-path` を登録した (段 4 で正例を置くとき、その壊れ方が発火する経路と到達計数を先に書く)。検査起動器は正例ごとに到達 (`reached`) と検出 (`detected`) を別々に記録する (job dir `verify/launch_cicada_run_target.py`)。
- 再発検知: 正例の結果が「到達なし」のとき。到達 0 を「検出されなかった」と読まず、正例の置き場所を疑う。

## 再発

### F722

- **再発: 2026-09-29** — VHash md_21 で、C++ の計数行を新しく読む driver の解析を、実装子が推測で組んだ fixture だけで検査した。実物との食い違いが smoke 1 (`CICADA_LONGTX_V1` の top-level key に `schema` があった) と fix 後の焦点再レビュー (SAFEPOINT の無い build の GC 行の mode は `"none"`、driver は `"off"` を要求) で 1 巡に 1 件ずつ出て、fix を 2 巡追加した。どちらも login のテストと段 6 のレビュー 2 本では捕まらなかった。直した後は実 stdout の行を写した回帰テストと、build の macro 集合から期待を導く形にした。
