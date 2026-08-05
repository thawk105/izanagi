---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t476-flock-race-flake
seq: 2
---

## {{D:flock-observation-by-event}}. プロセス間 flock を観測するテストの待ちは、時計でなく事象で終端させる

**決定:** 別プロセスの状態を観測するテストでは、待ちの終了条件に wall-clock を使わない。
観測対象の値は**子の stdout へ 1 行**で通知させ、親は fd から 1 byte ずつ改行まで読む。
親から子への解放通知は**子の stdin への 1 byte / EOF** で行う。ファイルの存在
(`Path.exists()`) を「値が publish された」ことの代理にしない。
真のデッドロックに備えた hang guard は既存の `SUBPROCESS_TIMEOUT` だけを使い、
正常経路の成否がその値に依存しないようにする。両子プロセスは単一の `try/finally` が所有し、
片方の回収失敗で他方を飛ばさずに独立して bounded 回収する。

**理由:**
- ファイルへの `write_text` は「生成 → 内容書込」の 2 段であり原子的でない。
  親が `exists()` で待つと、内容書込前の空ファイルを読む窓が生まれる。実測では
  受入全走 5900 件のうちこの 1 件だけが赤くなり、単独走行では緑という形で現れた。
- deadline 超過を失敗の根拠にすると、**正しい実装が負荷で赤くなる**。計算ノードは 32〜48 並列で
  走り、1 プロセスが数十秒 descheduled されうる。timeout を伸ばすのは確率を下げるだけで、
  受理集合の時間条件を暗黙に持ち込むこと自体が非決定性の源である。
- pipe の read は「相手が書く」か「相手が死ぬ (EOF)」で必ず終端する。終了条件が時計から
  独立するため、負荷の大小で受理集合が変わらない。
- 通知の受理は完全一致にする。prefix 除去 (`removeprefix`) は不一致時に元文字列を返すため、
  形式の壊れた通知を正常値として受理してしまう。

**却下した選択肢:**
- 一時 file へ書いて `os.replace` で原子的に publish する — 空読みは消えるが、
  親が「deadline 直前に publish された値を poll 位相の都合で読まない」race と、
  deadline 超過を失敗にすることによる受理集合の縮小が残る。
- timeout 値の延長 — 機序を直さず確率を下げるだけで、負荷が上がれば再発する。
- 空値を `blocked` とみなす、空値を再試行して後続の値を採用する — 非原子的 publish を隠し、
  相互排他の証明力を下げる。
- buffered `readline()` に `select` を組み合わせる — Python 側 buffer に先読みされた行は
  後続の `select` から見えず、子が親の解放を待ち親が `select` で待つ循環待ちを作る。
