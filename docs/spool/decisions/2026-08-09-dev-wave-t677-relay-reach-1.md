---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-t677-relay-reach
seq: 1
---

## {{D:failure-digest-producer-side}}. 失敗診断の中継到達は producer 側の終端ダイジェストで保証する

**決定:** pytest セッションの終端に bounded な失敗診断ダイジェストを出し、その到達を機械検査で
固定する。dispatcher (`tools/pegasus/dispatch_compute.py`) の中継仕様は変更しない。

- 出力位置は `@pytest.hookimpl(wrapper=True, tryfirst=True)` の `pytest_unconfigure` post-yield とする。
  pytest 自身の `short test summary info` と `summary_stats` はこの hook より前に出るため、
  後続出力に上限が無くてもダイジェストが押し出されない。
- 予算はダイジェスト総量を `DEFAULT_FAILURE_RELAY_LIMIT_BYTES` の 3/4 とし、残り 1/4 を後続余白にする。
  定数は複製せず import して導出する。
- 保証範囲は **pytest セッションが完走した場合**に限る。

**理由:**
- 中継は末尾 64 KiB だけであり、失敗が多い全走では診断本体が丸ごと落ちる。実測で
  child stdout 523,987 bytes のうち 458,452 bytes (87.5%) が欠落し、`=== FAILURES ===` の
  見出しごと消えていた。
- `pytest_terminal_summary` は不可。その後に無上限の `short test summary info` が出るため、
  実測 artifact の行長では 156 件目で開始マーカが 64 KiB の外へ出る。
- producer 側なら local 走行・変異 harness・他 transport にも同時に効く。dispatcher は
  sanctioned control plane であり、変更コストと影響範囲が大きい。
- 完全ログへの耐久参照は新規実装を要しない。dispatcher が既に receipt path を表示し、
  receipt の `scheduler_logs.stdout.path` が全文を指す。

**却下した選択肢:**
- 中継予算の増量 — 後続出力に上限が無いため到達保証にならない。
- dispatcher 側でのマーカ抽出 — Pegasus 経路にしか効かず、control plane の変更を要する。
- 完全ログ path だけの中継 — 人間の二段操作が要る。既に receipt 経由で存在する。
- 一行固定マーカ — per-failure の本体と省略会計を失い、原因帰属に足りない。

## {{D:diagnostic-line-prefix-not-pipe}}. 機械可読な出力へ付ける行頭 prefix に `|` を使わない

**決定:** 診断ダイジェスト等、pytest の失敗出力に混ざる機械可読ブロックの行頭 prefix は
`> ` とし、`| ` を使わない。行構造は保ったまま**全物理行**へ付ける。先頭行だけに付けてはならない。

**理由:**
- `tools/mutation_harness.py` の `_strip_relay_prefix` は ANSI 除去と `lstrip` の後、
  行頭の `|` を**個数を問わず**すべて剥がす。その後 `_failed_nodes` が `FAILED ` で始まる行を
  失敗 node として抽出する。
- したがって `| ` を付けた診断本文中に `FAILED path.py::name` があると、実際には落ちていない
  node が変異台帳へ混入する。F65 と同型の consumer 取り残しである。
- `> ` は `_strip_relay_prefix` が剥がさないため、この経路を構造的に塞ぐ。
- 先頭行だけに付ける実装は 2 行目以降が素の `FAILED ...` になり、同じ穴が開く。

**却下した選択肢:**
- `FAILED ` で始まる行だけを無害化する — 単独では成立するが、prefix 側の防護と合わせて
  冗長 gate になり、単独変異では consumer 抽出が破れないため検出力の帰属が曖昧になる。
  両方を持つ方針は維持しつつ、prefix 側を第一の防壁とする。
- 改行をすべて escape して 1 行に潰す — consumer は守れるが、4 KiB 級の 1 行になり
  人間が traceback 構造を読めない。診断が「届く」ことの意味を満たさない。
