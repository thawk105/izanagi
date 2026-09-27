### 所見 1 — 定数の import 時検査は plan 外

**主張:** `FROZEN_TEMPLATE_ABORT_HEAD_BYTES` の宣言行を `startswith` と `count` で検査する処理は、固定リテラルに対する追加検査です。[build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/build_admission.py:90)  
**根拠:** plan v2 が求めるのは凍結した2形の照合と、head 定数の pin 原文との独立テストです。宣言行の個数検査は指定されていません。  
**影響:** 現在の受理集合は変わりませんが、定数を編集した際に admission の拒否ではなくモジュールの import 失敗が起こり得ます。  
**推奨:** **should** — import 時検査を削り、2形の構築と独立照合テストに任せる。

### 所見 2 — tally 正例の再検査が重複

**主張:** tally 正例は `derive_build_admission` の成功で M3 を検出できます。続く `require_build_admission` の呼出しは、この正例の目的に対して重複です。[test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_build_admission.py:779)  
**根拠:** 既存テストが `require_build_admission` による source 再検査を扱っています（同ファイル680行）。  
**影響:** 受理集合は変わりませんが、別の再検査の不具合でも tally 形の正例が失敗し、失敗理由が曖昧になります。  
**推奨:** **nit** — この正例では derive の結果だけを確認する。

## 総括

**GO**。静的確認では、plan v2 が要求する凍結2形、負例10件、正例2件、独立照合3本に欠落は見つかりませんでした。  
M1〜M7 には、それぞれを単独で検出する想定 node があります。  
負例の似た byte 変更は R4/R5/R7 の異なる意味と配置を確認しており、削減対象とは判断しません。  
docstring は閉じた範囲を `abort()` 宣言から BEGIN 直前に限定し、R1、R3、R6、ENOENT、stock 受理も残しています。  
fixture の既定値変更は既存ケースを新しい凍結形に合わせるもので、期待値の変更は見つかりませんでした。  
これは read-only の静的レビューです。テスト実走の成否は判断に含めていません。