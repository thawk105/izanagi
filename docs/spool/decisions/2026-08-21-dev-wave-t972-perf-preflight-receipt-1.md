---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t972-perf-preflight-receipt
seq: 1
---

## {{D:t972-perf-preflight-resume-allowlist}}. perf preflight 診断イベントは journal 再利用 + allowlist 方式で resume classifier へ安全統合する

**決定:** build_cells 前の perf availability preflight receipt は、専用ファイルを新設せず既存の
journal.jsonl (`_journal_append`、append+fsync 済み) へ `perf-preflight` イベントとして追記する。
resume classifier (`classify_journal_resume_state`) の L/M-prestart 判定は、この診断イベントだけを
明示的に許可する allowlist 方式で拡張し、以下を必ず満たす検証を通す。
(1) outer key を exact 検証し inner receipt を `validate_perf_preflight_receipt()` で再検証する、
(2) event の重複・pre-measure 以外の位置・terminal/session 後の出現を拒否する、
(3) L/M-prestart/M-running を含む全 resume state で同じ検証を通す、
(4) sealed manifest がある状態では manifest 内 receipt との一致を確認する、
(5) pilot の pre-manifest L は現行どおり拒否を維持する (新規許可対象にしない)。

**理由:**
- journal.jsonl は既に L 状態の resume verifier が許可する run_dir 内ファイルであり
  (`_verify_resume_journal` の file 集合検査)、専用ファイル新設よりも安全側である。
- 単純な classifier 緩和 (event を無条件で許容範囲外にする) は、正しさ検証ロジックを弱め
  偽装 event の混入を見逃す。allowlist + 厳密検証の組合せで正しさ防壁 (規律2/3) を保つ。
- reservation-preflight などの将来の同種診断 event を追加しやすい形 (allowlist 方式) にしたが、
  今回は perf-preflight だけを許可対象とする (盛らない、規律5)。

**却下した選択肢:**
- 専用の create-only ファイルへ永続化する — resume の L verifier は run_dir 内の許可 file 集合を
  厳密に固定しており (`names != {"launch_certificate.json", "journal.jsonl"}`)、新ファイルの追加は
  この検査に抵触し L resume を壊す。journal 再利用より不利。
- classify_journal_resume_state の L/M-prestart 判定から診断イベントを単純に除外 (無視) する —
  診断イベントの exact schema・重複・位置を検証しないまま通すと、偽装 event が classifier を
  すり抜ける経路を残す。厳密な検証を伴う allowlist のほうが安全側。

## {{D:t972-trace-lane-closure-unrealizable}}. trace-enabled 経路との比較テストは要求しない

**決定:** perf preflight journal record が trace 処理と混同されていないことの検証を、
production の trace=False 固定を spy で実測確認するテスト (`build_cells` への実際の `trace`
kwarg をキャプチャする) と、journal record に `trace`/`use_perf`/`claim_scope` キーが混入しない
ことを成功時・build 失敗時それぞれで確認するテストの組合せに限定する。「trace-enabled 経路との
比較」は実装しない。

**理由:**
- floor campaign の production 経路には `trace=True` を渡す手段が存在しない
  (`build_cells` のシグネチャに `trace` 引数はなく、呼び出し側 2 箇所が `trace=False` を
  ハードコードしている)。これは規律1 (性能計測用ビルドから trace 処理をコンパイル時に完全除去)
  の設計そのものである。
- 存在しない経路を模す sentinel/monkeypatch でテストを書くと、実際の trace 経路の非混同を
  検証したことにならない (敵対レビューが独立に指摘した懸念と同型)。
- 上記 2 テストの組合せで、規律1 が要求する分離 (trace-disabled build のみを使う・journal record
  に trace 情報が漏れない) は実質的に検証できている。

**却下した選択肢:**
- `trace=True` を模した build_cells の sentinel 差し替えで journal record を比較する —
  実在しない経路の試験になり、規律1 の遵守を証明する根拠として無効。
- floor campaign に `trace` 切り替えパラメータを新設してテスト可能にする — production コードに
  不要な trace 分岐を持ち込むことになり、規律1 (ランタイム分岐にしない) に抵触しうる。scope 外。
