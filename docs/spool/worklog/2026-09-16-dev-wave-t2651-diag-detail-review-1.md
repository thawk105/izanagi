---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2651-diag-detail-review
seq: 1
title: [T-2651] 着地済みの診断本文保持へ敵対レビューを当て、変異 harness を本走した — 実装 must-fix ゼロ、kill 0 件・diagnostic sensitivity pin 6 件 (docs + 計測成果物、branch worktree-dev-wave-t2651-diag-detail-review、変異 matrix = baseline PASSED・6/6 KILLED・期待 node 完全一致・SURVIVED 0・MISMATCH 0)
---

## 本文

直前 wave (エントリ 1515) は `s1_direct_comparison.py` の診断本文保持を着地させたが、
段 3 のレンズを走行前の plan と brief に当てたため実装差分を見ておらず、変異 harness の
本走も未実施だった。本 wave はその 2 つの残件だけを閉じた。実装差分は作っていない。

**レンズ 2 本とも実装の must-fix を確認できなかった。** sol (正しさ境界と受理集合) は
受理集合を広げる反例も fail-closed を倒す到達可能な経路も見つけられず、luna (証拠の
復元可能性と byte 予算) は現行定数での byte 会計・slice 重複・`[-0:]` に欠陥を見つけられなかった。
**両者とも根拠の種別を「読解」と明記している** — read-only sandbox のため実走していない。

git に残らない裁定は次の 3 つである。

1. **6 変異すべてを diagnostic sensitivity pin に分類し、kill は 0 件とした。** `DW-M03`
   「診断文字列だけの赤を kill にしない」と `DW-M08`「受理集合を変えず構造化シグナルだけを
   pin する変異は別枠記録する」に従う。M3 は例外境界を攻撃するので kill 候補に見えるが、
   親が消費側を読み直したところ、整形器の `RuntimeError` が `DriverError` を置換しても
   `_is_transient_prepare_failure()` が `False` を返して再送出し、`main()` は `EXIT_REFUSED` を
   返す。**終端 rc が変わらないため kill と数えない。** kill 0 件は失敗ではなく、着地 commit の
   「受理集合を変えていない」という主張が変異の側からも裏付けられたということである。
2. **変異 runner の対象を `test_s1_direct_comparison.py` 単独に絞った。**
   `test_s8b_oracle_manifest.py` が `s1_direct_comparison.py` の live byte sha256 を golden 逐語で
   pin しており、同 file への任意の変異を一律に赤にする。`DW-M03` の冗長 gate 除外に当たる。
   この除外理由は**読解による存在の同定**であって、repo 全体に masking が他に無いことの
   証明ではない。当該テストは受入全走では通常どおり走る。
3. **前 wave insight §7 の観測範囲が過大だったので追記 erratum を出した。** 絶対規律 7 に従い
   本文は書き換えていない。3 走行が production 経路で直接観測したのは M1 が守る性質だけで、
   「いずれも全文 sha256 の印つきだった」は不正確 (1 回目に digest なし、3 回目の digest は
   argv 用)。M2 / M3 / M5 / M6 は 3 走行のいずれでも発火していない。

probe が必要だった理由も記録する。段 2 plan は pytest の既定 escaping を仮定して日本語 param を
`共通.hh` と予測したが、harness が記録する正規化形は `/u5171/u901a.hh` だった。
`DW-M08` が完全一致を求める以上、静的予測のままでは本走を通せない。本走 spec の期待 node は
probe の `failed_nodes` から機械生成し、人手で書き写していない。node の**件数と顔ぶれ**は
plan の静的予測と完全に一致していた (M1=7 / M2=3 / M3=1 / M5=2 / M6=2 / M7=4)。

`mutation_harness.py` は `--spec` にも checkout 外を要求する (repo 内は rc=2)。
`DW-M07` は `--out` / `--attempt-out` しか挙げていない。記録用の repo 内 copy と実行用の
job dir copy を同一 bytes で 2 本持って回避した。

変異後の復元は byte 完全だった。`git status --porcelain --untracked-files=all` が 0 行で、
driver の sha256 が `test_s8b_oracle_manifest.py` の golden pin と一致する。

scope 外として実装しなかった real 所見は insight §9 に列挙した。上流
`condition_meaning_gate` の 500 bytes 切り詰めによる raw stderr 前半の喪失、兄弟 driver
14 箇所への横展開、未被覆 6 性質、予算定数の母集合。**ユーザーが「仮想リスク向けの
gate・検査・台帳・一般化の追加は scope 外」と明示しているため、新規 T は立てていない。**

工数は Codex 子 3 本 (plan 1・consult 2、いずれも `reasoning=medium`)。計算ノード job は
焦点走 1 回、変異 14 回 (probe 7 + 本走 7)。実装子と fix 子は起こしていない。

詳細は `output/insights/2026-09-16_t2651-diag-detail-review/README.md`。

## 次の一手差分

### 完了

- [T-2651] 着地実装差分への敵対レビュー 2 本と変異 harness 本走を完了した。実装 must-fix ゼロ、
  6 変異は期待 node 完全一致で検出され、kill 0 件・diagnostic sensitivity pin 6 件に分類した。
  前 wave insight §7 へ追記 erratum を出した。
  remaining: none
  base: 8a37193785c1174cbd0cfd03b7c97747c0c862cac454059a12d38b3538ac0569
