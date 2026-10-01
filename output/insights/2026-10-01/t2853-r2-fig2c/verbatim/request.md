md_4: 再現パッケージの R2 — 主論文の fig2c (B-10 拡張格子) を元の driver で測り直し、原 attempt と並べる (計算 2.98 node 時間はユーザー承認済み)

最初に同じ directory の common.txt を読むこと。

■ 台帳の項目の探し方
docs/worklog.md の「次の一手」で、本文に「再現パッケージ」と「fig2c (2.98 node 時間) と fig10 (3.40) は承認済み」を含む item を grep して対象にする。この wave は fig2c だけを扱う (fig10 は別の wave が並行で扱う)。

■ 根拠
D2305 項 9 (ユーザー裁定): fig2c (2.98 node 時間) と fig10 (3.40) を承認し、計算の空きで 1 図 1 タスクとして投げる (生成器対照の本走と node を取り合わない順で)。
単価と job の対応: output/insights/2026-09-27/t2853-repro-rest/README.md §3.1〜§3.3 (fig2c = B-10 拡張格子 3 job × 31 variant、元 job 951689〜951691)。

■ やること
- 前例 output/insights/2026-09-28/t2853-r2-fig8b/README.md と同じ形で進める: 元の driver `tools/pegasus/submit_b10_backoff_grid.sh` を、原 cohort の source commit (fig2c の provenance が指す group から特定する) で使い、原 attempt と合成しない別 attempt として測り直す。
- 投入の直前に qstat を見て、生成器対照の本走 (job 名 izs4loop 系) に待ち (QUE) があれば、この wave の job の優先度を qalter -p で下げて投げる (待たずに投げてよい。本走を追い越さない)。
- 見積りが 2.98 node 時間を大きく超えると分かったら、投入前に land 調整役へ示し直す。正しさ検査は削らない。
- 原 attempt と並べた表と、同じ生成器の図を作る。生成器のレイアウト検査が R2 の値で拒否したら、図は作らずその事実を書く (生成器の変更はこの wave の scope 外)。

■ 成果物
output/insights/<着手日>/t2853-r2-fig2c/README.md (投入・Elapse・正しさ・表・図・原 attempt との比較・言えないこと)、spool fragment。

■ 所有
上の新設物と自分の fragment だけ。driver・生成器・既存の図と原 attempt の成果物は編集しない。

■ scope 外
本題の再実行と記録だけ。他の図には進まない。仮想リスク向けの gate・検査・台帳・一般化の追加はしない。規律 2 は緩めない。
