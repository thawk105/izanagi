## 所見 1 — F-1 は効果量設計の根拠にならない

- **severity:** blocker
- **主張:** F-1 の 1.774% は node 効果の証拠でないだけでなく、意思決定上の損失関数を伴わないまま `κ*=0.5` の materiality 根拠へ転用されており、`CV/√10` も独立性未確認なので推論用 SE ではない。
- **根拠:** 実 record は bnode011 / bnode048、`submit_epoch=1784404710 / 1785983265`、`binary_sha256=9ef841… / 25c82a…` と異なる。両者の `noise_floor.kind` は `within-run` で、10 点は [sweep.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/calibrator/sweep.py:235) の「連続 noise_reps 回」を [runner.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/calibrator/runner.py:435) の直列 loop で得たものにすぎない。[stability.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/calibrator/stability.py:102) は独立 session と within-run を明確に分離し、settle は独立性を作らず thermal drift も含まないとする。段 2 はそれでも [s2-plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:180) で 1.774% に合うよう `κ*=0.5` を選んでいる。
- **成果物影響:** 偶然の binary・occasion 差から判定閾値と標本数を逆算し、「設計から導いた」という誤った確信を残す。
- **提案:** 1.774% と「名目 3.3 SE」は記述統計に封じ、materiality は node CV や throughput 比について運用上許容できる上限を先に人間が定めるか、同一 bytes・複数 occasion の独立 pilot から別途計画する。

## 所見 2 — 単一 arm の出力は T-139 pilot を支えない

- **severity:** blocker
- **主張:** 同一 node 内 contrast というだけでは T-139 の `H`・`RF`・同時領域に対する node 効果は一般に相殺されず、単一-arm T-810 は必要な loading を識別できないため、この測定は T-139 pilot を支えない。
- **根拠:** T-139 の実契約は [preregistration-draft.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/output/insights/2026-08-07_t139-mainrun-design/preregistration-draft.md:29) の `N=X−Dg, D=S−Dg, G=S−X`、`RF=E[N]/E[D]`、[同:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/output/insights/2026-08-07_t139-mainrun-design/preregistration-draft.md:45) の二つの `H` である。共通加法効果 `c_i` なら `N,D,G,RF` は不変だが、`H_a→H_a−k_wc_i`、`H_b→D/(S+c_i)−k_w`。共通乗数 `q_i>0` なら `H_b` は不変、`H_a→q_iH_a` だが、平均受理量と `RF` は `E[q_iN_i]/E[q_iD_i]` となり、純粋な分離可能モデルまたは独立性なしには元の `RF` と一致しない。段 2 自身も [s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:85) で `L_w` が未識別、[同:87](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:87) で pilot covariance・受理確率・`J` のいずれにも入れないと認めている。
- **成果物影響:** 「node 分散が pilot の幅をどれだけ説明するか」という目的に対し、観測値から識別された入力が一つも残らない。
- **提案:** 段 4 で、(A) 推奨: T-139 目的を削除し「当該 workload・occasion の単一-arm snapshot」に限定する、または (B) T-139 の 3 arm×2 workload を同一 node で交差させ、同一 host を複数 occasion で再測定して joint node×arm loading を推定する、のどちらかを選ぶ。

## 所見 3 — `κ=σ_a/σ_e` は material node variance ではない

- **severity:** blocker
- **主張:** 主 estimand の `κ=σ_a/σ_e` は node 差を測定雑音で割った検出容易性であって運用上の node 差ではなく、`κ_U<0.5` から「material node variance を反証」は導けない。
- **根拠:** 段 2 は [s2-plan.md:29](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:29) で `κ` を主 estimand、[同:361](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:361) で materiality 判定にする。同じ `σ_a/μ` でも benchmark が騒がしく `σ_e` が大きければ `κ` は小さくなり、逆なら大きくなる。0.624% node CV への換算も現在の `σ_e/μ` ではなく別 binary・別 occasion の historical within-run CV を使用している。
- **成果物影響:** 測定が騒がしいほど実在する相対 node 差を「非 material」と結論しやすい逆向きの判定になる。
- **提案:** 主 estimand を `τ=σ_a/μ` または log-throughput 上の node SD とその上側限界に変更し、運用 margin も同じ尺度で固定する。`κ` と ICC は測定系の診断的副次量に降ろす。

## 所見 4 — ANOVA の “exact” CI は現設計では exact でない

- **severity:** blocker
- **主張:** 一 occasion・scheduler 選択 node・連続反復に対する F/χ² CI は、正規性・等分散・独立性が成立した working model の下だけで exact であり、現プランには仮定破れ時の有効な主解析がない。
- **根拠:** CI は [s2-plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:109) の common `σ_e²` と正規 random effect に依存する一方、node は [同:252](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:252) で無作為抽出されていない。記録予定も [同:279](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:279) の benchmark 前後情報だけで、rep ごとの時刻・温度・実効周波数がない。実 record `calibration-94a4…::noise_floor.throughputs` は先頭 3,900,644 から末尾 3,799,018 へ約2.6%動いており、drift の可能性を排除できない。正の系列相関は実効自由度を減らし、node 別分散差は `MS_A/MS_E` の F 分布を壊し、外れ node・thermal throttling は `a_i` と transient を混同する。P6 は [s2-plan.md:553](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:553) で正直に書かれているが、推定されるのは stable node effect ではなく `node + node×occasion` の合成である。
- **成果物影響:** 上側限界の被覆率が不明となり、「小さい／大きい」の両方向で誤判定し得る。
- **提案:** rep ごとの時刻・温度・実効 clock を保存し、round を同期または block 化する。raw ANOVA は副次にし、観測 node 集合について log-scale の median/IQR/MAD・node-mean range を主にするか、同一 host×複数 occasion を追加して cluster/block bootstrap または wild bootstrap を事前固定する。`N=12,O=1` の bootstrap は superpopulation variance の95%上限を救えないため、その主張を要するなら設計自体を拡張する。

## 所見 5 — `N=12,R=10` は規模最適化の解ではない

- **severity:** blocker
- **主張:** `N=12,R=10` は先に選んだ数へ `κ*=0.5`・assurance 80%・RSE 25%を合わせた逐次導出であり、絶対規律4が要求する明示的な資源目的に対する最小設計ではない。
- **根拠:** 対象目標は [s2-plan.md:178](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:178)、導出は [同:188](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:188) と [同:204](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:204)。同じ式を使う `N=9,R=13` は `df=(8,108)`, `F_.05=0.336560`, assurance `0.807958`, per-node SD RSE `0.204124` で全条件を満たし、117 node-rep と 12×10=120 より少ない。逆に primary の pooled `σ_e` の精度を指すなら RSE は概ね `1/√(2N(R−1))` であり、段 2 の `1/√(2(R−1))` は別の estimand である。elapsed time、node-hours、最大同時 node 数のどれを最小化するかも未定義。
- **成果物影響:** 必要以上の node を確保するか、逆に本当に必要な occasion・node 数を削って再現不能な測定になる。
- **提案:** material margin、真値ごとの operating-characteristic、per-nodeかpooledかの精度対象、最大 node 数、elapsed/node-hours の目的関数を先に固定し、`N,R,occasion` を同時最適化する。現時点では 12/10 を事前登録しない。

## 所見 6 — 測定後に選べる分岐が残っている

- **severity:** blocker
- **主張:** 感度解析・validity・retry・secondary の規則が閉じておらず、結果を見て有利な解析または attempt を選べる。
- **根拠:** `Ω_node` は [s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:85) で「上限または点推定」、`L_w` は構造仮定次第、結論条件は [同:361](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:361) の未定義な「全 validity 条件」。失敗分類は [同:365](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:365) の `invalid または incomplete`、release 前失敗は [同:375](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:375) で invalid に「できる」、retry も [同:376](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:376) で条件付きである。preregistration field は [同:544](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:544) の secondary 有無だけで、構成 identity・loading・感度表の結論対応がない。
- **成果物影響:** 低い分散なら点推定、高い分散なら上限、または不利な attempt を validity 違反として再投入する選択が可能になる。
- **提案:** 実走だけでなく liveness の性能値を見る前に、exact boolean validity predicate、開始境界、status FSM、release 後は再投入不可、release 前最大 attempt 数、最初の適格 attempt、`Ω` の使用量、全 `L_w` scenario と全件報告、secondary の exact binary/workload/orderを literal に固定する。

## 所見 7 — 実 record の field 名を誤認している

- **severity:** nit
- **主張:** 段 2 が根拠に挙げる `noise.repetitions` は実 record に存在しない。
- **根拠:** [schema_v2.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/calibrator/schema_v2.py:576) と [同:676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/orchestrator/calibrator/schema_v2.py:676) の noise key 集合に `repetitions` はなく、実 record は `noise_floor.throughputs` の長さが10であるだけだが、段 2 は [s2-plan.md:202](/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/s2-plan.md:202) で同 field を引用している。
- **成果物影響:** preregistration と receipt の照合実装が存在しない field を要求する。
- **提案:** 現 record については `len(noise_floor.throughputs)==10` と正確に記述し、新 protocol では `planned_repetitions` と実測配列長の一致を schema で検証する。

## 総括

**NO-GO。blocker 6 件、nit 1 件。**

P6 の one-occasion 制限と P7 の single-arm 制限は文面上は認識されている。しかし P6 は `σ_a` の名称と exact CI に、P7 は未識別な `L_w` 感度表に再侵入しており、制限を書いただけでは閉じていない。

段 4 では次を択一裁定すべきである。

1. **目的:** T-139 への寄与を削除して snapshot 測定に限定する（推奨）／T-139 と同型の crossed design へ拡張する。
2. **estimand:** relative node SD・log SD を主にする（推奨）／`κ` を検出容易性の診断量としてのみ残す。
3. **一般化:** 当該 occasion の観測 node だけに限定する／同一 host×複数 occasion を追加して stable node effect を推定する。
4. **規模:** 現行 12/10 を棄却し、operating characteristic と資源目的を固定して `N,R,occasion` を再計算する。
5. **推論:** robust finite-sample summaryを主にする／仮定を明記した variance-component CIを主にするなら複数 occasion と事前固定 bootstrap を追加する。
6. **事後自由度:** `Ω/L`、validity FSM、retry、secondary identity を完全に閉じる。閉じるまでは実装・投入へ進まない。

静的検査のみで、pytest・build・測定・編集は実施していない。