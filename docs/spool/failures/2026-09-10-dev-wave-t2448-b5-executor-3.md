---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2448-b5-executor
seq: 3
---

## 再発

### F899

- **再発: 2026-09-10** — 軸 B5 の実行器で同型が 2 件出た。どちらも合成 fixture が実際の形を
  1 度も通しておらず、実装子の test は緑だった。
  (1) registration preflight の directory exact set 検査が、`.gitignore` の 2 行目にある
  `__pycache__/` 配下の `.pyc` を「余分な path」と数えた。合成 tree には ignore 対象が
  存在しないので test は緑だったが、**一度でも import した実 repo では必ず落ちる gate** だった。
  親が実 repo で 1 回走らせて初めて出た。
  (2) 条件 1 の OpenAlex 期待 AST について、正例 test が期待側と実測側の双方を production builder から
  作っており恒真だった。同時に合成 fixture が登録構造 (`column_id` / `value` 形) と別の直接 key 形を
  「正常」として持っていた。恒真な test はどちらの誤りも赤にしない。
  恒久対応は F899 の再発検知に既に書かれている「実機出力の逐語 fixture を同じ検査に入れる」で、
  本 wave では実 repo の tree を走査する registration 正例 test と、凍結文由来の独立 literal で
  書いた期待 AST test を置いた。
