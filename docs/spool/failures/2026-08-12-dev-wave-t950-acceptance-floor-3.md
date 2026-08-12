---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t950-acceptance-floor
seq: 3
---

## 新規

### {{F:codex-web-search-duplicate-id-discards-output}}. codex 子が正常終了しても web_search を使うと成果物が全損する [観測系の欠落] [恒真ゲート]

- 事象: 段 3 の敵対レンズ 1 本が独立に 2 回失われた。いずれも
  `codex_exit_code=0` / `validator_rc=0` / `termination_verified=true` /
  `process_group_residual=0` / `limit_trigger=null` / model call と wall-clock は上限内で、
  成果物 (17,321 bytes と 17,595 bytes) も完全かつ NFC 正規化済み・`## 総括` 付きだった。
  それでも `evidence_status=invalid` で `accepted=false` になり、`-o` の出力 path には
  何も書かれなかった (`output_sha256=null`)。合計 2,668 秒と input 9.2M token 相当を空費した。
- 根本原因: `tools/codex_worker_launch.py` の `_drain_stdout` が stdout event 行を厳格に検査し、
  失敗すると `stdout_invalid` を立てる。`_evidence_status` はそれを `invalid` にし、
  受理条件が `complete` を要求するため attempt ごと落ちる。
  **拒否されていたのは Codex CLI が出す `web_search` の `item.started` event で、
  同一 object 内に `"id"` が 2 つある** (`"id":"item_32"` と `"id":"exec-..."`)。
  厳格 parser は `JSON key が重複` で拒否する。10 行中 12 行が該当した走もある。
  同時刻の別 lane は web_search を使わず、最大行 1,098,349 bytes でも `complete` だった
  (行長上限 4 MiB は無関係)。
- 恒久対応: 当面の回避は prompt に「Web 検索を使うな」を明記し、判断根拠を repo 内一次資料と
  親の実測に限定すること (3 度目の投入はこれで rc=0)。恒久側は
  {{D:prefilter-safety-rests-on-slow-path-equivalence}} とは独立の裁定事項として
  worklog の新規項目へ起票した (`evidence_status=invalid` の理由を receipt へ書く、
  consult / review 段で web_search を既定無効にする、stdout event の重複キー扱いを分離する、の 3 案)。
  **`tools/` の実装面なので Codex `role=author` が要る。**
- 再発検知: 受理条件は既に fail-closed である。欠けているのは**理由の記録**で、
  現状 receipt には「どの行のどの検査で落ちたか」が一切残らない。上記 3 案のうち
  「理由を receipt へ書く」はどの案を採っても要る。

### {{F:multi-axis-masks-value-side-literal-check}}. 多軸で書いたテストが値側 literal の検査を恒真にした [恒真ゲート] [検査漏れ]

- 事象: 三軸検索の前置フィルタで「値側を必要条件 literal の導出に使わない」ことを固定したはずの
  テストが、**恒真だった**。`keys.append(key)` を `keys.append(key + "=" + value)` にする
  1 行変異が、既存テスト 105 件を 1 本も発火させずに生存した (rc=0、失敗 node ゼロ)。
  静的レビュー 6 本 (起草 + 段 3 の 2 本 + 段 6 の 2 本 + 親) が全て見落とし、変異だけが見つけた。
- 根本原因: 既存テストがすべて**多軸**で書かれていた。軸ごとに値が違うため、
  値を混ぜても最長共通部分文字列が結局 key 側へ戻り、導出結果が変異前後で一致する。
  実害が出るのは**単軸**のときで、値の任意 1 文字メタ文字に一致する text が
  正規表現には一致するのに必要 literal を含まず、正しい hit が捨てられる。
- 恒久対応: 単軸 `expressions` を使う検査 2 件を追加し、変異 matrix の本走で
  当該変異が 2 node で KILLED になることを固定した (10/10 期待どおり)。
- 再発検知: 変異 matrix の当該 entry が恒久の positive control として残る。
  同型 (多軸の共通部分文字列が単軸固有の欠陥を隠す) を疑う場合は、
  **軸数を最小にした経路を必ず 1 本置く**。
