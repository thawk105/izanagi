---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-22
wave: dev-wave-t2849-comparison-harness-design
seq: 2
---

## {{D:five-method-comparison-harness}}. 5 手法の比較基盤は候補 identity・評価要求・結果分類・費用計上の 4 契約だけを共通化し、具体化は silo の backoff 値空間に限る。主構成は参照値を生成器へ渡さない R0・知識射影なしの K0 LLM・系列ごとの共通初期点とし、BO と進化は逐次 GP-EI と (1+1) の再実装にする

**決定 (設計のみ、実装しない):** VLDB 方針 (D2212) の差分分析 P2 に当たる比較基盤 (T-2849) の設計を、insight `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` のとおり定める。要点は次のとおり。

1. **共通化の範囲。** random・sweep・BO・進化・LLM が共有するのは、候補の identity (protocol・genome flags・PIN・材料化した source)、評価の要求 (`p3_s4_loop` の単回評価 → 検疫 → Tier0 → `run_campaign` / `pipeline.evaluate`、手法で経路を変えない)、結果の分類 (B-5 の分類)、費用の計上の 4 つの契約だけとする。候補を運ぶ入口 (S1 の proposal 文書、S3 の IR JSON・C++ 本文) は空間ごとに別とする。汎用の系列 runner・汎用台帳・S3 の表現設計は作らない。
2. **具体化するのは S1 (silo の backoff 値 1..1000 µs) だけ。** random は B-5 の log-uniform、sweep は B-5 の 28 点格子から初期点の値を除いた hash 順の非適応走査 (1 次元では座標探索が格子の走査順に退化すると明記する)、BO は x = ln v の逐次 GP-EI (追加の初期 design 0)、進化は log 尺度の (1+1) 変異、LLM は B-5 §4.1 の運用契約から knowledge manifest を除いた K0 構成 (planner・coder・critic、還流あり) とする。critic 診断の射影 (D2155) は K0 へ適用範囲だけを広げる (射影の中身と 6 field は変えない)。
3. **揃え方。** 全 arm が読める共通入力 (自系列の slot の記録) と、各手法が消費する field を分けて定義する。主構成 R0 では、生成器へ渡すのは系列開始 stock と空間内の初期点の観測だけとする。`p2_2_flag_opt` は exact flags で block ごとに同じ動作点・session 契約・correctness 条件で fresh に測る報告用の対照とし、値を生成器へ渡さない。渡す構成は R1「既知結果を条件とする探索」として別に名乗る。S1 の初期点は静的 5 µs と 10 µs (案) で、系列ごとに fresh に測り、最初の提案の前に全 arm へ渡し、B の外に置き (総評価数 k + B)、endpoint の候補に含める。anomaly による endpoint 資格の喪失は集約側で全系列へ波及させ、生成器へは還流しない。
4. **費用の計上。** A は候補提出の機会 (空出力・不正出力を含む) で全 arm に上限を掛ける。A を消費しない内部計算は獲得関数の採点・乱数の偏り除去・事前に定めた構成規則だけとする。重複 (同じ系列で評価済みの identity の再提案) は A と B を消費して fresh に測る。Tier0 の compile / smoke 不通過は A だけを消費し、所要は物理費用に入れる。pipeline 内の build 失敗と anomaly は B を消費する。job Elapse は job ごとに 1 回数え、slot の wall は内訳とする。LLM の役割呼び出しは A でなく物理費用とし、token 数を金額に換算しない。統計単位は独立な探索系列、時間原点は系列開始 stock の開始時刻とし、checkpoint の最良は結果が使えるようになった候補だけから求める。B・A・k・系列数・費用上限・checkpoint・N_eval の値と比較の族は T-2850 の事前登録へ残す。
5. **B-5 の再利用。** 規則 (A/B・retry・品質欠測・endpoint・fallback・Tier0・全 arm 同一 walltime・LLM 親運用) は継承し、S1 で呼べる関数 (重み表・格子・文法・`SeriesLedger`・slot の分類) は呼び、B-5 固有の結合 (arm 3 固定・slot 接頭辞・K2 必須・系列 1..12) は変える。B-5 の事前登録・cohort・判定規則は変えず、標本を混ぜない。
6. **MOCC の差し込み口。** 人間の push → D1603 の材料での pin 再承認の提示と承認 → gitlink 等を更新する別 wave、の順が済むまで S2 は無効とする。S2 は、固定した MOCC flags (BACK_OFF=1 必須) の上で S1 と同じ literal の材料化 (合成枝を `double now_backoff = <v>;` に置換) が成立する場合の差し込み候補とする。MOCC の比較は stock 比で報告し、既知最良の参照が無いことを明記する。温度述語 hole は使わない (D2134 項 9)。
7. **S3 を足すときの条件。** 5 手法の主比較では、全 arm が同じ支持集合を探索するか、支持集合の制限を含む構成比較と明記するかを結果を見る前に選ぶ。LLM×C++ は比較 B で 5 手法の族に入れない (D2214)。

**理由:**
- 依頼は口の形・揃え方・B-5 の再利用範囲・BO / 進化の出所・費用単位・MOCC の差し込み口を求め、gate・検査・台帳・一般化の追加を scope 外とした。現に口が実在するのは S1 だけで、S3 は実装コードが無く (D2214 の段階 C 以前)、S2 は pin 前進前である。
- 空間外の参照値 (BACK_OFF=0 の `p2_2_flag_opt`) を使えるのは LLM だけなので、主構成で渡すと LLM だけに情報が増え、差が情報の差か探索の差か分からなくなる。
- 評価数 8〜10 程度の小予算で BO に初期 design を払わせると獲得による提案がほぼ起きず、(μ+λ) では 1 世代で終わる (予算の算術)。共通初期点を学習データと親に使う逐次更新なら、最初の提案から手法の性質が出る。
- login の python3 で import できる外部 package は numpy 2.2.6 だけで、scipy・sklearn・optuna は無い (親が実測)。計算ノードは未測定。S1 は学習点が数十・候補 1000 点なので標準ライブラリで足りる。numpy を使わないことは研究要件ではなく、使うなら実装 wave が可用性を測ってから。
- 合成枝の既定式は BACKOFF_FIXED の千の位で待ち方の形を切り替える (`patches/silo-backoff-fixed.patch`) ので、MOCC で macro の値だけを流用すると 1..1000 µs の意味が S1 と一致しない。
- 段 3 の Codex 相談 2 本 (比較の公平性・情報の漏れ / 実効性と過剰・再利用) の must-fix 15 件と should 6 件をすべて real と判定し、上の形へ直した。

**却下した選択肢:**
- 汎用の系列 runner と arm 汎用の台帳 — 依頼の scope 外。`SeriesLedger` は arm も値も検査しないので、schema 名を変えるだけで足りる。
- S3 で sweep / BO だけが template の部分集合を動く構成を「探索法の比較」と呼ぶ — 表現制限の効果が混ざる。
- 参照値を全 arm へ渡す構成を主比較にする — 上記の情報の非対称。R1 として別に名乗るのは許す。
- 初期点を B の中に入れる、または系列間で測定値を共有する — 前者は手法ごとの初期化支援量が予算を変え、後者は系列の独立性を崩す。
- 初期点を endpoint から外す — 初期点より劣る探索点が endpoint になりうる。
- BO の初期 design と (μ+λ) の個体群を B から払う — 小予算で手法が初期点の比較に退化する。
- 外部の最適化 library の移植・呼び出し — login で使えず、計算ノードも未測定。S1 では不要。
- K2 知識つきの LLM を主比較に入れる — 非 LLM に無い既知結果の射影を LLM だけが持つ (B-5 の限界と同じ)。K2 は B-5 cohort の構成として残す。
- MOCC で BACKOFF_FIXED の macro だけを使う — 値の意味が S1 と違う。
- MOCC の flag 8 点の全列挙を差し込みの必須前提にする — 指定条件の flag 参照最良を得る別研究であり、差し込み口の成立条件ではない。
