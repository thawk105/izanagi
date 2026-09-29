# 確認走行 V2 の結果 (job v2、request 36318.nqsv、bnode026、2026-09-29 23:31:57〜23:35:16 JST、起動器 rc=1)

原本: runs/v2/result-CUSTOM.json、raw = runs/v2/raw/CUSTOM/。起動器 stage5/launch_gcfix_run.py (sha256 62f23a09…)、spec-v2.json。計測木 gcfix-m2 (main 8fe87f852)。

| build | run | 結果 | 期待 | 判定 |
|---|---|---|---|---|
| FIX_F_TRACE (F + instr + instr-tpcc + fix + count) | F×t4×3 | 3/3 rc=0 で完走。W op D = 1,578 / 1,510 / 1,636 件、D を出した thread は 4 つ全部 (0〜3)。計数 patch の読み飛ばし回収 = 261 / 246 / 315 回。**判定器は parse error (rc=2)**: `R <txid> 5  1 0` (key が空の NewOrder の R 行、1 file あたり 82〜114 行、F 3 run・12 file で計 1,142 行 (当初 88〜114 と誤記、焦点再レビュー 2 で訂正)) | trace-pass | 満たさない (新事実 S) |
| FIX_F_TRACE | M×t4×2、R2×t4×2 | 4/4 合格 (indeterminate、巡回 0、integrity 数値項目 0、存在履歴違反 0、C = commit 数) | trace-pass | 満たす |
| STOCK_F_TRACE (F + instr + instr-tpcc) | M×t4×2、R2×t4×2 | 4/4 合格 (同上) | trace-pass | 満たす → delete を含まない cell で修理前後の判定は同じ |
| identity (STOCK_F_TRACE の前) | (F + fix) 対 (F + instr + instr-tpcc + fix)、TRACE=0 | transaction.cc・util.cc・tpcc_cicada.cc の 3 TU で compile command 一致・命令列一致・前処理の実質一致、nm・strings 一致 | 命令列一致 | 満たす |
| SKIPRC_FIX_F_TRACE (+ broken-skip-read-recheck) | F×t4×1 | rc=0 で完走、W op D 6,020 件、読み飛ばし回収 0 回。判定器は同じ parse error | trace-cycles | 満たさない (新事実 S) |

新事実 S: scan (transaction.cc:432) が key を最新版の body から取り、body の無い削除版が最上段にある行で key が空になる。詳細と裁定は s4-ruling-addendum-1.md。
