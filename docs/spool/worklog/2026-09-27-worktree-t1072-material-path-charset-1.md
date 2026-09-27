---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-t1072-material-path-charset
seq: 1
title: [T-1072] critic digest の材料 diff_region を表示直前に文字集合で検査し、外部 diff の file path が制御文字・表示偽装のまま critic 入力へ載る経路を閉じた。外側の理由文字列は T-1047 で閉鎖済みを確認し、同じ record の負例を同じ単位に置いた (コード + テスト、branch worktree-t1072-material-path-charset)
---

## 本文

- 依頼 (2026-09-27): 2026-08-25 /rulings 択 (a) のとおり材料の逐語経路に文字集合の制限を掛け、外側の理由文字列も同じ変更単位で閉じる。
  正例と負例を同じ単位で置き、規律 2 を緩めず、本題だけ実装する。記録は `output/insights/2026-09-27/t1072-material-region-charset/README.md`。
- 段 3 相談 2 本の指摘で親 brief を 2 点改めた。(1) 検査は loader と renderer の両方でなく renderer だけに置いた
  (2026-08-15 裁定の「表示直前の無害化に限る」、loader 値を表示・比較する consumer が無い)。(2) 攻撃者制御の値が region に届くのは
  `DiffQuarantine` へ外部 diff を直接渡した場合に限る — 通常の段 4 driver は固定 source_rel から diff を組むので、到達の主張を条件付きにした。
- 実 WAL 154 本に diff 検疫 payload は 0 件で、正当値の網羅証拠にはならない。正例は producer の `_mk_digest` 13 箇所と実 producer 経由のテストで取った。
- 変異: digest.py は contract-loader 閉包に入っており、bytes が HEAD と違うだけで test_critic.py の 64 node が赤になる (comment だけの対照 M0 で測定)。
  WAL を読む今回の新テストもこの層に入るため、固有証拠は直構築テストと、変異を commit した使い捨て木の side run (drift なし) が担う。
  本走 6 / 6 KILLED (対照 M0 を含む、期待外 0)、side run は 5 変異とも事前登録の期待集合と完全一致 (M2 の固有証拠はこちらだけ)。
- scope 外の残余 (実装・起票せず、insight §6 に記録): trace 由来の key・integrity notes の逐語表示 (D2257 が T-1072 を残した根拠) と、
  検疫以外の STAGE_ABORT の外側 reason。どちらも起票の材料 field の外で、到達性は未測定。
- 検査: 焦点走 15 file 2,473 passed / 3 skipped を 2 回、provenance 全史監査 rc=0。三軸語走査 (`s8b_holdout_freeze search`) は rc=1 だが hit は 2026-09-16 の
  `output/env/pegasus/calibration/s8b-floor-official/` の既存 3 file だけで、本 wave の新 file は 0 件。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。
- 工数: codex 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1)、計算ノード job は焦点走 2・変異 3 走 (probe・M0 probe・本走)・side run 6 回・受入。

## 次の一手差分

### 完了

- [T-1072] 材料 (critic digest の diff 検疫 rejection) の diff_region を renderer で文字集合検査し、許可外を sentinel に置き換えた。
  外側の理由文字列は T-1047 で閉鎖済み。正例・負例を同じ commit に置いた。scope 外の残余は insight §6。
  remaining: none
  base: e8602fcd1f2051ea631b4c068729f3e7b5ca4f76ac3bf017de14f4c339bea321
