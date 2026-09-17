---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2756-pin-evidence
seq: 1
title: [T-2756] ccbench pin 更新項 ([T-167]) の再承認材料 3 点を揃えた — 候補 e9e477ca (mocc 単独、現 pin の直系子孫)、直接区間の D297 検査は GCC 2 版 pass・clang 14 は検査不能、pin 束縛 134 file の層別波及表 (docs のみ、branch worktree-dev-wave-t2756-pin-evidence、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2756] (D2114 項 3、D1603) mocc 第 2 例に向けた ccbench pin 更新項の再承認材料 3 点を揃え、見送り台帳へ提示できる状態にする。(1) 候補 full OID の確定 = mocc 単独、hook branch の先端 e9e477ca、(2) `tools/check_trace0_preprocess_identity.py` による D297 検査の結果と checker の保証範囲の明記、(3) 承認済み定数・事前登録・identity・凍結への波及表。成果物は insight (docs のみ)。検査が拒否しても『前進可能』とは判定しない。gitlink・pin.py・s8b_approved.py は動かさない。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (材料が揃った)。pin 前進は未承認のまま。** 一次資料は `output/insights/2026-09-17/t2756-pin-evidence/README.md`。見送り台帳 [T-167] 行へは本 fragment の見送り追記で参照を足す。decisions fragment は無し (新しい設計判断なし。plan・レンズ 2 本とも同意)。
- 材料 3 点の要点 (詳細は insight §2〜§4): 候補 `e9e477ca` は現 pin `511c9538` の直系子孫 4 commit 先で追加差分は `cc/mocc/transaction.cc` 1 file、GitHub には未 push (push は人間、D16)。直接区間の D297 検査は g++ 11.4 / g++-12 で rc=0・16 context 全一致、clang++ 14 は環境 prefix 不一致で比較前に fail-closed (候補の拒否ではないが clang での同一性は未確認、「3 本すべて成功」は未達)。保証範囲は D297 の保証名に限り、解決不能な CMake 間接値を拒否しない残余 (D774、[T-1644] 据え置き) があるため D986 の全面閉塞は主張しない。pin の値を含む tracked file 134 件を A〜G に全数分類し集合外依存を別表化、骨格 §5 の「凍結 evidence manifest = full SHA」は誤り (7 桁)。結論 = pin 前進は旧 pin・旧 identity の測定事実と当時の判定を無効化しない (規律 7)。新 pin で継続する系列は登録・identity・凍結・consumer・テスト契約の整合と明示された再実測を要する。**残る裁定 (再承認パッケージ)**: 候補の承認、GitHub push、clang 未確認を GCC 2 版で足りるとするか、旧較正 record の新 pin 系列への流用 (親の推奨 = 既定は再取得)。
- 段 2 plan は親 brief を 6 点訂正 (D986 全件閉塞の断定、preprocess 引数、拒否時は report が出ない、134 は文字列集合、F は機械更新でない、追記は spool の見送り追記)。段 3 レンズ A (正しさ境界) must-fix 8 / nit 2、レンズ B (波及表) must-fix 6 / nit 2、すべて採用 (親が実測で確認: version-body digest、分岐被覆表、raw-manifest の 7 桁、blob sha、GitHub の ref)。段 6 レビュー 2 本の所見と是正は insight §6。
- 実走: checker 3 本 (login、各 33〜50 秒)、`check_docs.py`、三軸語走査、受入全走 (docs commit 後の最終 tip、結果は land の受領証)。子は read-only の静的検査のみ。
- 工数: codex 子 5 本 (plan 1、consult 2、review 2、全段 `gpt-6-astra` / `medium`)。親の実測: checker 3 走、probe (clang / gcc の prefix 各 1)、閉包走査 1、GitHub ls-remote 1。

## 次の一手差分

### 完了

- [T-2756] 材料 3 点を `output/insights/2026-09-17/t2756-pin-evidence/README.md` に揃え、見送り台帳 [T-167] 行から参照した。pin 前進の再承認は同項の裁定として別途 (本 wave は判定しない)。
  remaining: none
  base: 6d824725fb89347c9827d5d9d495071d0638951ff9a101c0b17eac4b6b18845f

### 見送り追記

- [T-167] 【2026-09-17 追記: [T-2756] の候補 commit・直接区間検査の結果と保証限界・pin 更新の波及資料を `output/insights/2026-09-17/t2756-pin-evidence/README.md` に記録。本追記は判断材料の参照追加である】
