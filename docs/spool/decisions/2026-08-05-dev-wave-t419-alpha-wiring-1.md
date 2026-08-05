---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t419-alpha-wiring
seq: 1
---

## {{D:alpha-acquisition-identity}}. 方式 α の取得手続きを identity に載せ、時間窓を宣言する

**決定:**

1. 本番 attestation の effective clock は、走行 CPU を sysfs CPU 集合 ∩ 元 affinity から決定的に
   等間隔 K=5 点選んで pin しながら `/proc/cpuinfo` を読み、**論理 CPU ごとの最小値**を
   `effective_clock.samples_mhz` とする。受理述語 (全位置が帯内) と `tolerance_pct` は変えない。
   方式 β (reader 除外) と γ (帯外 1 個まで許容) の性質は混ぜない。
2. `effective_clock.method` は K・最小 interval・target 選択規則 ID から組み立て、独立した文字列
   literal にしない。K か規則が変われば identity が必ず変わる。
3. 読み開始は deadline 方式で 50 ms 以上あけ、最小 horizon `(K-1) × interval` を構造で保証する。
   **遅延そのものは拒否理由にしない** — 遅れは horizon を伸ばす方向であり、承認外の過剰拒否を
   新設しないためである。
4. schema key 集合は変えない (`samples_mhz` / `method` / `governor`)。K 読みの生ベクトルは取得中だけ
   メモリに置き、成果物へ出さない。

**理由:**

- 採用された α は「巡回が省略不能」であり、変更面は述語でなく**取得手続き**である。手続きが
  identity に載っていなければ、method を名乗るだけの退化を成果物から区別できない。
- 実験で 9/9 の should-pass を得た α 群は randomized pin sweep の各 target の先頭読みを束ねたもので
  時間幅が広く、本番の連続 5 読み (約 100 ms) とは別プロトコルになる。機序 (reader が居る CPU は
  必ず busy) の除去は時間窓に依存しないが、一過性の吸収は依存する。よって時間窓を宣言値として
  identity に載せ、**9/9 を本番手続きの妥当性根拠には使わない**。
- schema を広げると、旧 probe corpus と登録済み較正が method 比較へ届く前に schema 不正で落ちる
  (必須 key の場合)、または exact schema を弱める (optional key の場合)。observed 側だけに足しても、
  較正発行経路が observed dict を expected へ転用するため clock key の exact 検査に当たる。

**帰結として明記する限定:** 「K 回取得したことの事後証拠」は成果物に残らない。method は手続きの
証明ではない。取得 transcript の凍結は versioned schema の別 wave として裁定へ返す。
また `min` は上向きの一過性を K−1 回まで消し、下向きは 1 回で残す非対称性を持つ。単読みに対する
受理集合と同一ではない。

**却下した選択肢:**

- 生 K ベクトルを observed schema へ保持する — 上記のとおり旧 corpus・較正 loader・profile hash・
  登録 artifact・contract pin を同時に動かすことになり、本 wave の不変条件と両立しない。
- 時間窓を宣言せず連続読みにする — 一過性の吸収について何も保証できず、実験との差も記録に残らない。
- 遅延を拒否理由にする — 実測に基づく閾値がなく、承認外の過剰拒否を新設する。

## {{D:thread-self-stat-for-pin-check}}. pin の実効性検査は `/proc/thread-self/stat` で行う

**決定:** 走行 CPU が pin 先と一致するかの検査は `/proc/thread-self/stat` の processor field を読む。
`/proc/self/stat` を使ってはならない。pin mask の exact 検査は interval 待機の**直後**に置く。
mask 検査・pre 検査・post 検査は互いに mask しない独立な 3 検査として書く。affinity は
`try/finally` で復元し、復元後に再取得して exact 一致を確認する。復元失敗が pin/read の本来の
失敗理由を上書きしないよう、primary と restore を合成して報告する。TSC 測定は復元完了後に固定する。

**理由:**

- `sched_setaffinity(0, ...)` は呼び出し **thread** に作用するのに、`/proc/self/stat` は
  thread-group leader の stat である。worker thread から probe すると pin した thread ではない task を
  検査することになり、誤拒否になるか、leader が偶然 target 上にいると壊れた pin 検査へ偽の裏付けを
  与える。
- mask 検査が待機の前だけにあると、待機中に affinity を広げられても pre/post の瞬間だけ target 上に
  いれば通る。待機区間は最大 50 ms あり、無防備にできない。
- 3 検査を独立に書かないと、1 箇所を壊す変異が別の検査に mask され、変異台帳の kill が
  受理集合の変化へ帰属しなくなる。

**却下した選択肢:**

- affinity 変更を短命な helper process へ隔離する — attest する主体が親 process でなくなるという
  意味変更を伴うため本 wave では採らない。暖機の持ち越し (復元しても走行 CPU・cache・P-state は
  戻らない) は既知限界として残し、ablation は裁定へ返す。
