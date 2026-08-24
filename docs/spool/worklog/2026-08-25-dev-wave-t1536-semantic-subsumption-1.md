---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1536-semantic-subsumption
seq: 1
title: [T-1536] 意味的包含で C12 個別 snapshot 2 件を退役させた。包含は成立しておらず、不足 assert を移植してから退役した (テスト、branch worktree-dev-wave-t1536-semantic-subsumption、変異 matrix = 8 走すべて baseline 緑・直列 4 走は完全一致 KILLED・並列 4 走は接尾辞のため MISMATCH で node 集合は同一)
---

## 本文

- 権威は 2026-08-23 /rulings 全件のユーザー裁定 (択 (a)、証拠水準を下げない)。手順の正本は
  {{D:semantic-subsumption-retirement}}、退役一覧と各件の実測根拠は
  `output/insights/2026-08-25_t1536-semantic-subsumption-retirement.md`。
- **依頼の前提だった「退役先が候補を包含する」は偽だった。** 退役先は C12 の status を
  dict 等価の `==` で、候補 2 件は `is` で比較していた。`PredicateStatus` が
  `str` 混入 Enum なので素の文字列は `==` を通り `is` を通らない。
  段 2 プランと段 3 レンズ A が独立に同じ反例を構成し、親が裏取りした。
  **退役候補 2 件は gate レポート生成を守る唯一の identity 検査だった** —
  worktree 内の直接評価で `s8c_gate_report._status_counts` が素の str に対し
  `AttributeError` になることを確認した (正常系は正常な件数辞書を返す)。
  そこで identity 検査を退役先へ移植してから退役した。記録では
  「元から包含されていた」と書かず「不足 assert を移植したうえで検出力の維持を実測した」と書く。
- **裁定文の「約 24 秒」は誤りである。** これは duration ledger の `32.0` という
  日程並べ替え用 placeholder から導かれた値で実測ではない。計算ノードの焦点走では
  0.005 秒以上の項が 2 件だけで、どちらも退役対象ではなかった (24.77 秒は共有 module fixture の
  setup で退役後も消えない、13.15 秒は別 node)。D532 と D692 は所要短縮を退役の根拠にすること
  自体を禁じているので裁定の論拠は崩れない。
- **変異 harness の group 接尾辞問題 (F95) を、harness を直さずに越えた。** 正規化の設計は
  別 ID が所有しているため触らず、**実行形を 2 通り測る**ことで機械照合を通した。
  受入と同じ loadgroup 走で node 集合を取り (label は MISMATCH のまま)、
  runner の正規経路である `-n 0` の直列走で `DW-M08` の完全一致を成立させた。
  全 3 版で 2 走の失敗 node 集合は接尾辞を除いて完全一致した。
- **段 3 の敵対レンズ B は 1 回目が launcher の `evidence_status=invalid` で不採用になった。**
  本文 9,879 bytes は完全で `check_codex_output.py` rc=0 を通っていたが、親は採用せず
  同じ prompt を別 job-id で再投入した。再投入は成功し、**保全版と再投入版が 2 点で食い違った**
  (NC-S が semantic kill か、harness 修理が `DW-G03` を満たすか)。親が両方を実測で裁定し、
  前者は再投入版の事実認識、後者も再投入版 (F408 が実在し `DW-G03` は満たす。ただし所有が
  別 ID にあるので含めない) を採った。**同一 prompt の 2 回の実行が異なる結論を出しうる**ことの実例。
- **親自身の誤りを 3 件記録する。** (1) 「semantic kill を 1 件も主張しない」と保守側へ倒したのは
  過剰で誤りだった。`DW-M03` が除外するのは診断文字列だけの赤であり、型契約を壊す変異は該当しない。
  親は D692 の KILL の読みについても自説を取り下げ、レビューの読み (`DW-M03` と同一概念) を採用した
  うえで、実測で要件充足を示した。争点は解釈ではなく事実だった。
  (2) commit message の collect node 数を 1 件過大に書いた (正は 236 → 234)。抽出が
  `IZANAGI_GROWTH_HOLD_V1` の受領証行を node と数えていた。
  (3) `s8c_result_judge` を C12 consumer と書いたが誤り。同 file の `.status.value` は
  判定器内部の別の型を読む。実際に壊れるのは gate レポートと素の CLI 出力である。
  **commit は amend していない** — 最終 tip に束縛した変異証拠が壊れるため、訂正は台帳と
  insights に残した。
- 段 6 のレビュー 2 本はいずれも、削除そのものと golden 更新には検出力の欠落を見つけられなかった。
  fix は docstring 1 語 (「退役予定」→「退役した」) のみで、`DW-M07` に従い最終 tip で
  変異を測り直した。

## 次の一手差分

### 完了

- [T-1536] 意味的包含による退役を 2 件実施した。包含が成立していないことを実測で確定し、
  不足していた identity assert を退役先へ移植してから退役した。D692 (a)(b)(c) は
  collect 差分 236 -> 234 (退役 2 件ちょうど、追加 0、他の消失 0)、
  移植後の対 3 node が KILL、削除後の残存 node が KILL で満たした。
  remaining: none
  base: 35cf7efb67bb1894579d454051aafc76f9076438358e4d06aea23ae551ea1ec4
