---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-target-policy
seq: 1
title: [T-2910] VHash の前進先の選び方を比べ、最良設定の Cicada の上で C・F・E を測り直した。E の前進先を「既読の可視区間に収まる最大」にすると skew 0.6 でも回収境界の遅れが約半分 (19.5 → 10.0 ms、「今」は 17.4 ms) になり、skew 0.9 では選び方を変えても効果は小さい。C は部分前進だけが長い tx の成功率を上げ、F は最良設定の上で skew 0.9 の throughput が stock の 0.21〜0.49 倍 (patch + driver + insight、branch dev-wave-vhash-forwarding-target-policy)
---

## 本文

- 依頼: 並行 VHash wave の md_21 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_21.txt`)。正本: `output/insights/2026-09-29/vhash-forwarding-target-policy/README.md`、設計判断は {{D:vhash-forward-target-policy}}、失敗は {{F:positive-control-unreachable-on-policy-path}} と F722 の再発。md_20 (最良設定の正しさ検査) は記録時点で local main に未着地で、一次資料に「最良設定の正しさは md_14 §5 と本 wave §5 の範囲だけ」と明記した。
- 段 3 相談 B の must-fix 3 件 (「1 tx 1 回」の意味、E-max の「今」上限、成功率の分母) と F の追加 (T-2903 のため) を採用。相談 A の「上端の走査が回収・再利用に遭う」は、md_14 §3.3 の不変条件で回収の切れ目が既読版以下にしかなれず既存の再観測と同じ露出、として静的論証で退けた (実行時の証明ではないと一次資料の限界に記した)。段 6 レビュー B の「一次資料が無い」(段の順序) と「壊しが 2 箇所を変える」(親が 5a2 で単一の意味の変更として明示裁定済み) は refuted。
- 親の設計の誤り 1 件: 段 4 で壊し正例を E-max で走らせる設計にし、検査 1 回目で到達 0 だった (F 新規)。段 1 の親の仮説 P3 (C-max は既読不一致を減らせない) は実測と合った (C-max 0.048 対 C-min 0.050、skew 0.6)。
- md_21 の所有外の file を 1 つ編集した: `orchestrator/tests/test_ccbench_spawn_sites.py` の重ね patch 用の表に 2 項目 (target patch の文脈行に `#if CICADA_GC_SAFEPOINT`・`#if CICADA_FWD_COUNT` が入るため、焦点走 1 で 3 件赤)。md_14 の先例 6b72c649f と同じ足跡で期待件数は不変。
- セッション異常 (実害なし): EnterWorktree の name 形が filter driver の読取エラーで失敗し、手動 add → path 形で入った。submodule 初期化は新規の木ごとに 1 回目が `update-no-fetch` で rc=1、再実行で rc=0。fix 4 の 2 本の子で起動器の終端 commit が取り残された空の index.lock (23:53・23:54) で `add-all` 失敗し、git process が無いことを確かめて lock を外し、親が同じ内容を patch 化・記録 commit した。検査起動器は Cicada の `integrity.clean` が構造上 false なので job の rc を 1 で返す (巡回・数値項目は 0)。
- 変異: 16 件 (MT1〜MT16) を束ね経路 (D842) で。probe 36422 (Elapse 2,222 s) で 15 件が登録したテストで kill、MT2 は SURVIVED (外した検査が build 種の振り分けと重なる冗長な検査だった) → 振り分け側へ狙い直し、final 36593 (MT2 だけ・driver のテスト 1 file) で KILLED。**手順の逸脱:** 全件の final を取り直すと計算が合計 2 node 時間を超える見込みだったので、MT1・MT3〜MT16 の kill の証拠は初回の dispatch probe の観測 node とし、final の完全一致照合 (DW-M08) は MT2 だけで行った。
- エージェント工数: Codex plan 1・consult 2・author 3 (単位 A・B と壊し patch の続き)・review 2・focus 1・fix 7 (fix1 A/B、fix2 B、fix3 B、fix4 A/B、fix5 B、いずれも gpt-6-sol / medium)。子の worktree `.claude/worktrees/vhash-ftp-author-a` / `-b` と dispatch 用の detached 木 8 本。計算ノード: smoke 5・検査 2・本計測 7 (7 台同時)・焦点走 3・provenance 監査 1・変異 2、Elapse 合計 6,387 s (約 1.77 node 時間、受入の全走を除く)。

## 次の一手差分

### 完了

- [T-2910] VHash の GC 接続 (構成 E) の前進先の選び方 (今・可視区間の最大・1 tx 1 回) を最良設定の Cicada の上で比べた ({{D:vhash-forward-target-policy}}、一次資料 `output/insights/2026-09-29/vhash-forwarding-target-policy/README.md` §4.2・§4.3)。
  remaining: none
  base: 61746238213fe99dc36ef81d9eb932c63fbc6992056387c29bd0b57289652411
- [T-2894] 選択的 forwarding (構成 C) の前進先の選び方 (最小・可視区間の最大・部分前進・1 tx 1 回) を many_ops と normal で比べ、長い thread と通常 thread の成功率と失敗理由を分けて測った (同 §4.4)。
  remaining: none
  base: 926fe6c9f4b9f145fecaab552d790e163c0b3afcaa58802fff98b5d0f24be0b0
- [T-2903] md_6 の C / F と stock の比較を md_11 の観測最良の Cicada 設定の上で測り直した (同 §4.5)。
  remaining: none
  base: 2b40131f17f2c114fff8467b78b74b7d00a8195b242967140fc51ccb73054c6c

### 新規

- {{T:vhash-doomed-longtx-early-release}} **P2・新規**: VHash の構成 E で、待機中に既読のどれかが自分の時刻より下の時刻で上書きされた長い tx (validation で abort が決まっている tx) を安全点で早く abort させ、回収境界を解放する方策を E-max と比べる。md_21 では skew 0.9 で E-max の要求の約 75% が `no_room` で、前進先の選び方ではこの tx を救えず回収境界の遅れの改善は −1.0 ms に留まった。`no_room` を「成功後」と「成功前」に分ける計数も足す。根拠: `output/insights/2026-09-29/vhash-forwarding-target-policy/README.md` §4.3・§8。
