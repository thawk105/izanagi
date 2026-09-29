---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-output-pruning
seq: 2
---

## 新規

### {{F:path-scan-misses-renamed-and-conceptual-refs}}. path 文字列の参照走査が改名 (gz 化・配置移行) と概念での参照を取りこぼし、削除候補を過大に出した [ドリフト] [手順漏れ]

- 事象: output/ 整理の第 1 段で、固定 commit の全 blob を参照元とする 7 軸の走査 (full path・相対 path・basename・sha256・blob id・祖先 dir・glob) が「参照 0」の A 候補を 131 件出した。段 3 の「消すと困る」側レンズと親の照合で 6 件まで絞られた。取りこぼしの型は 4 つ。(1) D577 で `.gz` へ置き換えた file を README が元の名前で引く (A の gz 75 件中、gz 化前 basename が md 58 本に出現)。(2) 2026-09-10 の配置移行 (588 dir を `YYYY-MM-DD/名前/` へ) より前の docs は旧 path `<日付>_<名前>` で引く (docs/failures.md が `2026-08-17_t190-launcher-failure-artifact/first-real-bundle/` を引いていた)。(3) `{1,2}`・`before/after/x` の束表記。(4) README が file 名でなく「本 wave の中心的な証拠」「原 job 資料も保持する」と概念で指す。
- 根本原因: 参照閉包を「現行 path の文字列一致」で定義し、repo 内で行われた改名 (gz 置換・配置移行) の対応表と、本文の意味による参照を閉包に入れていなかった。
- 恒久対応: {{D:output-pruning-policy}} 決定 2 が参照閉包に gz 化前の名前・配置移行前の旧 path・同 root md 本文での言及を含めると定めた。走査器の修正と再走査は worklog の新規項 {{T:output-pruning-stage2}}。一次資料 `output/insights/2026-09-29/output-pruning/README.md` §6。memory `output-pruning-scan-holes`。
- 再発検知: 次段の削除候補に対し、段 3 の「消すと困る」側レンズが標本ではなく全数を監査する (今回は全数監査で発見した)。削除前に索引生成器の verify と README 本文の照合を行う。
