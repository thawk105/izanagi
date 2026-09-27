## 所見

- **must-fix — F42 の「再発」分類が合いません。** [failures fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/docs/spool/failures/2026-09-27-dev-wave-t2854-d297-header-v2-3.md:20) は既存 test の AST 契約を実装子が見落とした事象です。一次資料の [F42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/docs/failures.md:2467) は、新規 test ファイルの自走 harness／allowlist 契約を満たさず受入全走が赤になる型です。F42 の再発から外し、適切な既存型へ付け替えるか新規型として記録してください。

- **should — F819 の「再発」分類も狭義には合いません。** [fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/docs/spool/failures/2026-09-27-dev-wave-t2854-d297-header-v2-3.md:24) の子は相対 path を誤解して即停止しました。一次資料の [F819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/docs/failures.md:23481) は、親 worktree を指す投げ文により子が無変更で成功扱いになった型です。「関連例」として区別するか、別の失敗型へ移してください。

## 検算した値の一覧（一致したもの）

- 判定 2 回目は両 compiler とも **rc=0、pass**。GCC 11.4 は 980 秒、12.3 は 988 秒。各 [report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/output/insights/2026-09-27/t2854-d297-header-v2/verbatim/evidence/judge2-gcc11.report.json) と job dir の rc・seconds が一致します。選定は stock＋silo 8＋mocc 8＝17、未選定の tictoc・cicada は各 24 genome。各 configure で consumer 21 entry／12 file、予定・実行 357 件、集約後 118 件です。比較 118 件の configure 展開も計 357 件。.cc 2 本は各 16 文脈で一致し、gitlink は `third_party/shirakami` の `fb14e659…`。C/C++ compiler はそれぞれ gcc/g++ 11.4.0、12.3.0 です。
- 負例は **rc=1、951 秒**で、stderr は stock の `tpcc_cicada.exe` entry に対する `header expanded 不一致`。判定 1 回目は両版 rc=1、gitlink の非 regular file 拒否でした。
- Elapse は 170＋13＋10＋1,944＝**2,137 秒**。変異結果の所要は 368.896＋373.834＝**742.730 秒**、合計 2,879.730 秒＝**約 0.800 node 時間**。dry-run を除く receipt は **12 本、178 model call、wall 3,177.027 秒**です。
- 変異 probe は baseline PASSED、12 件は期待 SURVIVED に対して実測 MISMATCH（狙いの test が赤）。final は baseline PASSED、**12 件すべて KILLED**で、失敗 node の集合も spec と一致します。V2・V12 を外した理由は [実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:948) の依存取得と 4 引数検査に整合します。
- [worklog の更新本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/docs/spool/worklog/2026-09-27-dev-wave-t2854-d297-header-v2-1.md) は更新前の [T-2854] の既存事実を保持し、実装後の状態を加えています。pass の保証名と D780 項 1 の文言は report・既裁定と一致し、trace 完全除去、TPC-C certified、pin 前進は名乗っていません。F899 の再発は、既存エントリにある「合成 fixture が実機の形を通さず緑」の型に合います。新規 F が指す memory 名のファイルも存在します。

## 判定（GO / NO-GO）

**NO-GO。** 判定結果や費用の数値ではなく、failures 台帳の F42・F819 の再発分類を直す必要があります。

## 総括

判定・変異・実費・保証範囲・[T-2854] の状態更新は一次資料と整合しました。修正対象は failures fragment の分類 2 件です。ファイル変更とテスト実行はしていません。