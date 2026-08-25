---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t843-coder-value-integrality
seq: 3
---

## 再発

### F106

- **再発: 2026-08-25** — [T-843] coder value 値域 wave。変異 probe を計算ノードへ投入した直後、
  親が待ち時間に段 7 の decisions fragment を worktree へ書いた。`tools/mutation_harness.py` の
  preflight が untracked file を検出して rc=2 で止まり、8 run 分の走行が投入前に破棄された。
  fail-closed で止まったので実害は再走の一手間だけである。本 wave の親は起動前に自分の handoff へ
  「変異走行中は tree を触らない」と書き、read-only レビュー子との競合を理由に変異の起動時刻まで
  ずらしたうえで、なお踏んだ。2026-08-06 の「注意書きでは誘因が消えない」という観察を 1 例強める。
  恒久対応は F106 のままとし、本 wave の親は再走前に fragment を commit してツリーを clean に戻した。

### F531

- **再発: 2026-08-25** — [T-843] coder value 値域 wave の段 6 敵対レビュー レンズ A。
  `codex_exit_code=0`・15 model call・4685 bytes・`check_codex_output.py` rc=0 の健全な出力が
  `evidence_status=invalid` / `accepted=false` で不採用になり `-o` が書かれなかった。
  F217 (web_search) ではない — 親の prompt は全子に web 検索禁止を明記しており、
  events に `web_search` は 0 件だった。台帳が定める判定法どおり
  `orchestrator.codex_roles.events.parse_jsonl` へ events を通すと
  `JSONL:35 のJSON parse失敗: Unterminated string starting at: line 1 column 328` を得た。
  子の仕事は `p3_s4_loop.py` の差分読解であり、同 file は
  `_NOW_BACKOFF_RE = re.compile(r"now_backoff\s*=\s*(-?\d+(?:\.\d+)?)")` のような backslash を
  多く含む正規表現リテラルを持つ。F531 が「子の仕事自体が正規表現リテラルを扱う内容のときは
  決定的に再発すると考えてよい」と書いたとおりの条件で、これで 6 例目である。
  **新しい情報は、差分を読ませるだけの読み手でも発火する点である** — 子が正規表現を
  書く wave でなくても、対象 file が正規表現を持てば `git show` / `sed` の tool 出力経由で入る。
  親は F531 の回避手順どおり `attempt-0001.output.md` を検収して保全し、
  内容を変えない新 job として再投入して rc=0 を得た。独立 2 走とも所見ゼロで一致した。
  恒久対応は F531 のまま未実施である。
