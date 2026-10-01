md_5: 再現パッケージの R2 — 主論文の fig10 (B-7 fixed 5 µs × 3 workload) を現行の certification driver で測り直し、原 attempt と並べる (計算 3.40 node 時間はユーザー承認済み)

最初に同じ directory の common.txt を読むこと。

■ 台帳の項目の探し方
docs/worklog.md の「次の一手」で、本文に「再現パッケージ」と「fig2c (2.98 node 時間) と fig10 (3.40) は承認済み」を含む item を grep して対象にする。この wave は fig10 だけを扱う (fig2c は別の wave が並行で扱う)。

■ 根拠
D2305 項 9 (ユーザー裁定): fig2c と fig10 (3.40 node 時間) を承認し、計算の空きで 1 図 1 タスクとして投げる (生成器対照の本走と node を取り合わない順で)。
単価: output/insights/2026-09-27/t2853-repro-rest/README.md §3.3 (fig10 = B-7 fixed 5 µs × 3 workload、5 node)。

■ やること
- 前例 output/insights/2026-09-29/t2853-r2-fig11/README.md (fig11 の R2) と output/insights/2026-09-29/t2853-r2-fig6/README.md と同じ形で進める: 現行 repo の paper-story の certification driver (tools/pegasus/submit_paper_story_a2_certification.sh 系) と現行 policy で、原 attempt と合成しない別 attempt として測り直す。collect は repo 外の空 dir へ materialize し、原 attempt の tracked leaf に触れない。
- 投入の直前に qstat を見て、生成器対照の本走 (job 名 izs4loop 系) に待ち (QUE) があれば、この wave の job の優先度を qalter -p で下げて投げる (待たずに投げてよい。本走を追い越さない)。
- 見積りが 3.40 node 時間を大きく超えると分かったら、投入前に land 調整役へ示し直す。正しさ検査は削らない。
- 原 attempt と並べた表と、同じ生成器の R2 図を作る。生成器が R2 の値を拒否したら、図は作らずその事実を書く。

■ 成果物
output/insights/<着手日>/t2853-r2-fig10/README.md (投入・Elapse・outer status・効果・正しさ・表・図・原 attempt との比較・言えないこと)、spool fragment。

■ 所有
上の新設物と自分の fragment だけ。driver・policy・生成器・既存の図と原 attempt の成果物は編集しない。

■ scope 外
本題の再実行と記録だけ。他の図には進まない。仮想リスク向けの gate・検査・台帳・一般化の追加はしない。規律 2 は緩めない。
