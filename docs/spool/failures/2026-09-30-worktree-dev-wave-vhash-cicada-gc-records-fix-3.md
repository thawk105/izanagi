---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-dev-wave-vhash-cicada-gc-records-fix
seq: 3
---

## 新規

### {{F:request-file-overwritten}}. 稼働中の wave の依頼 file を、親セッションが同じ名前で別の依頼に上書きした [手順漏れ]

- 事象: 2026-09-29、VHash の親セッションが並行 wave の依頼を `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_N.txt` に書いて起動している中、21:35 に書いて本 wave (gc_records の修理) が 21:43 に読んだ `md_23.txt` を、21:59 に別の依頼 (VHash 本体の hot 配置) で上書きした。段 3 の相談子が依頼 file を読み直し「依頼と plan が食い違う」と指摘して判明した。本 wave は起動引数と開始時の読みで主題を保持していたので作業は失われず、会話に残った本文を job dir に逐語で保存した。子に依頼 file の path を渡していたため、相談子 1 本が別依頼を正本として読んだ。
- 根本原因: 依頼の置き場が番号付きの共有 file で、書き手が既存 file の有無を確かめずに書いた。wave 側は依頼 file を wave 開始時に job dir へ逐語で写しておらず (DW-O02 の「必読資料の逐語を job dir へ出す」を依頼 file に適用していなかった)、子に共有 file の path を渡した。
- 恒久対応: 書き手は置き場へ書く前に存在を確かめる (親セッションが合意、記憶 `parallel-wave-prompts-in-external-files`)。wave 側は DW-O02 に従い依頼 file を開始時に job dir へ逐語で写し、子にはその写しの path を渡す (本 wave の `request-md_23.txt`、md_17 の `request-md_17.txt` が先例)。
- 再発検知: 子の報告が「依頼と plan・brief が食い違う」と言ったら、依頼 file の mtime と開始時に読んだ内容を照合する。
