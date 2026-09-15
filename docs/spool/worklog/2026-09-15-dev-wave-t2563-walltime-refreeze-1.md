---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2563-walltime-refreeze
seq: 1
title: [T-2563] 認定較正の予約式を実体へ合わせ、保証しない範囲を凍結文面へ出した (コード + テスト、branch worktree-dev-wave-t2563-walltime-refreeze、変異 matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、受理集合を変えないため全件 diagnostic sensitivity pin として kill に数えない)
---

## 本文

- ユーザーが引数で起票した wave。scope は「本題の実装だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」「効果帰属できない並行化は再提案しない」「規律 2 を緩めない」と明示された。
  軽量版でなく段 2・3 と段 6 review を回した (凍結される proof chain の文面に触り、設計択一が割れたため)。
- **持ち越し文の前提が 1 つ覆った。** 「6910 / 6610 / 7870 の 3 通りが食い違う」は現在成り立たない。
  2026-09-13 の commit `b3c62ee7f` が `condition_gate(300)` を撤去し、job 冒頭コメントを receipt 側と
  同じ 6610 へ既に揃えていた。残る食い違いは comment・receipt と**実処理**の間の 1 本である。
- **親の provisional 裁定を 2 度撤回した。** 段 1 の (P1) は要求枠を 7200→10800 へ上げる案、
  段 3 直前の (P1′) は `required_s` を配分 5590 へ再定義する案。前者は絶対規律 4 と受理集合の拡大、
  後者は**受理集合の縮小**で倒れた。決め手は段 3 luna の算術で、`reservation_budget()` が
  `3190 + 360p` であるため点数 6 の呼び出しが 5590 では拒否される。親が独立に検算して一致を確認した。
  段 2 plan・段 3 sol・段 3 luna は独立に同じ第 3 案 (数値据え置き + 文面訂正) へ収束した。
- **親が D1986 を過度に一般化していた (段 3 sol)。** 同 D の項 3 / 9 / 10 は別対象の限定裁定であり、
  前文は「各実装は名指しの変更に限定」と定める。限界を明記する形の前例にはなるが、
  `required_s` の意味を変える授権にはならない。裁定は {{D:certify-walltime-allocation-not-bound}}。
- **親の主張が 1 件反証された (段 3 sol / luna が独立に、段 6 r2 が現物で再確認)。**
  「窓不足は fail-closed に失敗するので誤認定は生じない」は成立しない。CLI は accepted を決めた後、
  候補・材料レポート・registered を公開してから正常終了する。公開と終了の間に TERM を受けると
  accepted な公開物が残ったまま wrapper が非ゼロ終了しうる。下流の検証は wrapper の終了コードを
  必須にしていない。**限定 (両子一致):** 計測完了前の打ち切りが部分標本から accepted を組み立てる
  経路は無い。既存の限界であり本変更が作ったものではないため関門を足さず、文面の包括保証を撤回した。
  新規項として起票する。**F は起こしていない** — 事象が発生した記録ではなく静的な限界所見であり、
  発生したら同型として failures へ回す。
- **親のアンカー表に数え誤りがあった (段 2 が訂正、段 3・段 6 が独立に確認)。** 計測前の
  `timeout` 指定値の和を 3230 秒としたが、`policy.json` の perf 候補が 2 件あり version と smoke が
  最大 4 回走りうるため **3250 秒**が正しい。親は 1 候補分しか数えていなかった。
- 段 2 が pin 閉包の未確認 1 件を実測で閉じた。`output/env/pegasus/calibration/attempts/**` の
  JSON 59 件を実読し、`walltime.formula` を持つ 6 件はすべて旧式・`required_s=6610`・要求 7200 で、
  **過去 receipt を現行式で再計算する consumer は 0 件**だった。過去 receipt は据え置く。
- 段 3 luna が親の pin 閉包の説明を 1 件訂正した。`test_pegasus_policy_registry.py` の当該定数は
  key の存在検査ではなく**移設済み key 名の集合定義**であり、検査対象は production が共有 policy から
  それらを直接読むことである。値の pin ではないので今回の更新対象ではない。
- **段 6 レビューは 2 本とも must-fix 0 件。** 変更前 HEAD とのバイト比較で、差分は 3 箇所だけ
  (script の冒頭コメント、formula 文字列、test の逐語 pin) と実測された。過去 receipt 335 file は
  Git blob とバイト一致、`orchestrator/calibrator/cli.py` は 51035 bytes 全体一致、
  `timeout` は 19 箇所すべて不変。`finalize_reserve\((\d+)\)` の実測は 2 件・集合 `{600}`。
- **変異は受理集合を変えない。** 本 wave の production 変更は receipt へ凍結される記述文字列だけで
  あり、どの attempt が受理されるかを動かさない。`DW-M08` に従い全件を
  **diagnostic sensitivity pin** として記録し、kill の数に数えない。2 pass で行い、
  全件 SURVIVED 期待の probe で観測 node を集めてから完全集合を KILLED 期待で本登録した。
  本走は baseline PASSED・KILLED 4・SURVIVED 0・MISMATCH 0・matching 4 で、4 件とも
  観測 node は 1 件だけだった (単一理由性)。新旧両走の代わりに、各変異の対象文が変更前 HEAD に
  在るかを実測した — M2 / M3 / M4 は 0 件で、旧 pin は守りようがなかった (守るべき文が無かった)。
  M1 の対象文だけ旧版にも在り、旧 pin でも検出できた。
- **T-2563 は完了にしない。** 最大経路を収容する再凍結は未解決のまま残す。閉じるには要求枠を
  8840 秒以上へ上げるユーザー裁定か、完了の定義を「文面の整合と限界の明示」へ狭める裁定が要る。
  本 wave はどちらも決めていない。D1971 の「時間式再凍結を完了扱いにしない」を維持する。
- 子の工数は plan 1・consult 2・author 1・review 2。fix 巡は所見ゼロのため回していない。
- 逐語・変異台帳・spec は `output/insights/2026-09-15/t2563-walltime-allocation/`。

## 次の一手差分

### 更新

- [T-2563] **P2・一部前進**: 予約式の偽の内訳を実体へ合わせ、保証しない範囲を凍結文面へ出した。
  **最大経路を収容する再凍結は未解決。** 数値 (要求枠 7200・`required_s` 6610・各 timeout・標本数)
  は 1 つも動かしていない。閉じるには (a) 要求枠を 8840 秒以上へ上げる裁定、または
  (b) 完了の定義を「文面の整合と限界の明示」へ狭める裁定のいずれかが要る。
  (a) は絶対規律 4 と受理集合の拡大に触れるため親は推さない。
  正本 = `output/insights/2026-09-15/t2563-walltime-allocation/README.md` と
  {{D:certify-walltime-allocation-not-bound}}。
  base: f8310b3c42876a4dce9713c6cfcbb0e07d60c16a9dd4023114aae7c947976032

### 新規

- {{T:certify-publish-term-residue}} **P2・新規**: 認定較正 CLI は `accepted` 判定の後に
  候補・材料レポート・registered を公開してから正常終了する。**公開と正常終了の間に TERM を
  受けると、`accepted` な公開物が残ったまま wrapper が非ゼロ終了しうる。** wrapper の失敗処理も
  終了時の清掃も公開物を撤去せず、下流の検証 (`calibration_verify.py` / `collect_receipt.py`) は
  wrapper の終了コードを必須にしていない。計測完了前の打ち切りが部分標本から `accepted` を
  組み立てる経路は無いので、残るのは**中身の妥当な較正が失敗記録の job から公開されうる**という
  帳簿上のずれである。既存の限界であり、静的所見であって発生記録ではない。
  関門を足すか、公開と終了の順序を変えるか、限界のまま置くかを裁定する。
