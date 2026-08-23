---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-t1510-sort-swo-sigabrt
seq: 2
---

## {{D:sort-swo-oracle-baseline-visibility}}. sort SWO oracle の corpus 変異検出器は候補から不可視な場所へ基準を移すまで信用しない

**決定 (裁定パッケージ・ユーザー裁定待ち):** sort SWO oracle の `snapshot_corpus()` による
corpus 変異検出は、**候補 comparator が基準 snapshot を書き換えられる限り、正しさ防壁として
数えない。** 本 wave では実装せず、設計択一をユーザーへ返す。

**実測 (親が repo 外 probe で確定):**

- `trusted_snapshot` は候補文と同じ翻訳単位の file-scope 変数である。候補が corpus を壊した後に
  `trusted_snapshot = snapshot_corpus();` と書くと、変異 witness が消える。
  変異のみの候補は witness 検出、変異 + 基準再計算の候補は witness なしで正常終了した。
- 上流の `coder_effect_gate.DENY_TABLE` は host 副作用 (process/file/network/sleep/escape-hatch) しか
  塞いでおらず、この識別子は素通りする。単一 sort 文の構文 gate も comparator 本文を制限しない。
- 合法な SWO を作る候補が `a.body_.get_val()` を読むだけで SIGABRT し、構造化拒否ではなく
  `UNAVAILABLE` になる。現行 corpus の要素は body を与えない 4 引数 ctor で構築されるためである。

**時間関係 (裁定に必要な事実):** 修理前は全評価が起動直後に SIGABRT していたため、この穴は
到達不能だった。**修理の着地と、穴が生きる時点が一致する。** 緩和事実として、sort 合成
エージェントは filesystem 経路を構造的に持たず `trusted_snapshot` を知り得ないが、
これは隠蔽への依存であり防壁ではない。

**推奨案:** sort 呼出し前の snapshot をその場で出力 pipe へ書き出し、親側で前後を比較する。
一度 process を出た bytes は候補が取り消せない。wire protocol と `PROTOCOL_VERSION` の変更を伴う。

**却下した選択肢:**

- `-DNDEBUG` を足して assert を殺す — 正しさゲートを緩める変異であり絶対規律 2 に真正面から反する。
- 上流 `HeapObject::view()` の assert を緩める — 上流の事前条件は正しく、誤っているのは呼び手側である。
- 修理と同じ wave で防壁を再設計する — 正しさ防壁の設計変更は裁定パッケージへ送る契約であり、
  受理集合を変える設計を実装 wave へ混ぜない。
- 検出器を信用したまま運用する — 最適化圧力は必ず正しさを攻撃しに来るという前提に反する。
