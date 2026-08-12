---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 2
---

## {{D:floor-wrapper-fixed-pilot}}. 床値投入 script の mode は固定 pilot にし、受け口を作らない

**決定:** `tools/pegasus/floor_campaign.sh` は driver を `--mode pilot` 固定で起動する。
mode を環境変数・argv・`eval` から受け取る口を作らない。official を渡す手段も残さない。
将来 official を開くときは wrapper・job-result・失敗文言・guard・手順書を改めて変更し、
**別の source commit と script hash で再投入する**。

**理由:**

- ユーザー裁定 (2026-08-12) が「投入 script へ pilot 経路追加、official は空集合維持、
  `eligible_for_refreeze` は緩めない」を確定した。mode の受け口は「空集合維持」に必要な作業ではなく、
  bypass 面の新設に近い。
- official には発火経路が無い。条件付き機能は発火条件を満たす経路を書けるときだけ実装する規律
  (`DW-G04`) に照らして、渡せるだけの口は作らない。
- submission receipt が source commit と script blob hash を束縛するため、
  **pilot job をそのまま official と解釈することはできない。** 固定化しても将来の解禁を妨げず、
  解禁時には別 identity の投入になることが機械的に保証される。

**却下した選択肢:**

- 環境変数 `IZANAGI_FLOOR_MODE` で受け既定 pilot — production の受理面と `qsub -v` interface を
  増やす。official を渡せる口ができ、driver 拒否に頼る二段構えになる。非同値。
- pilot 専用の別 script — source binding・receipt・guard を複製する。非同値。
- 現状維持 (official 固定) — driver が必ず拒否するため、床値の測定が構造的に不可能なまま。

## {{D:shell-guard-token-counting}}. shell script の bypass 面検査は生文字列でなく token で数える

**決定:** job script が固定の CLI を起動していることを固定する検査は、
**(1) stub が記録した実 argv の完全一致**を主検査、
**(2) script 全体を posix mode の `shlex` で token 化した件数・値の検査**を従検査とする。
生の部分文字列一致 (`source.count(...)`) を検出の主体にしない。

**理由:**

- 生文字列一致は `--mo"de"` や `"s8b_floor_"campaign.py` のような分割記法を素通しする。
  posix mode の `shlex` は隣接引用を 1 token に連結するので、この回避を潰せる。
- 生文字列一致は逆に、説明コメントが同じ語を含むだけで落ちる。安全要件とコメント表現が結合する。
  `shlex` はコメントを除去するので、この誤検知も消える。
- 実 argv の完全一致だけでは、実行されない位置に置かれた第 2 起動を検出できない。
  token 検査と組み合わせて初めて「ファイル全体で 1 起動」を言える。
- 逐語の行一致 (`mode_lines == [...]`) は、意味を変えない整形変更で落ちる過剰拒否になる。
  実際に変異 matrix の正例で検査した。

**却下した選択肢:**

- 逐語の行 exact 一致 — 整形変更で落ち、かつ後続 assert が論理的に従属して恒真になる。
- 実 argv 検査だけ — 実行されない第 2 起動と、区間外の記述を検出できない。
- 検査を marker 区間に限る — 区間外に置くだけで回避できる。
