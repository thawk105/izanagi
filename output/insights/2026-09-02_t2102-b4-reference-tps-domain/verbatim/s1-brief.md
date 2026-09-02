# 段 1 brief — [T-2102] B-4 `reference_tps` の実値域を実測し D1344 の択一を確定する

- wave branch: `worktree-dev-wave-t2102-b4-reference-tps-range`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2102-b4-reference-tps-range`
- base local main: `28ebff456b9f57a927854950b5030fa77aec6529`

## scope

D1344 が求める実測を行い、その結果に基づいて択一 (registry の受理値域を狭める /
凍結 consumer を exact ratio 受理へ改訂する) を確定する。**本 wave の成果物は実測と択一の確定まで**
(ユーザー引数の明示)。受理値域を狭めるコード変更そのものは本 wave では実装せず、
確定した裁定と file:line 粒度の実行案を次 wave へ渡す。丸めて受理する案は採らない (D1344)。

## 確定済みユーザー裁定

- **D1344** — 実測を先に置く。ゼロなら registry の受理値域を狭め、実在するなら consumer を改訂。
  丸め受理は規律 2 違反として却下済み。(逐語: `verbatim-D1344.md`)
- **D95** — 実装面は Codex `role=author` が書く。親は直接編集しない。
- ユーザー引数 — 「本題の実測と実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。

## 起動時検査で覆した引数の前提

引数は「稼働中の t441-grammar-version-canon が p3_b4 系 test file を触っている」とするが、
T-441 wave は**完了・land 済み**である。branch 0 件、worktree 不在、job dir の `usage.json` が
2026-09-02 02:08 (段 9 後の `collect_wave_usage`)、main に merge commit `34399cde9` ほか。
よって編集面の重複はゼロで、「重なるなら実測と裁定案までで終える」の条件は不成立。
本 wave は**裁定案でなく裁定の確定**まで出す。

## 親の実測 (段 2・3 の攻撃対象)

母集合の定義 — `reference_tps` は「その block の precursor から祖先方向へ辿って最初に現れる
certified snapshot の session-level throughput」(事前登録 §5.1.1、逐語:
`verbatim-prereg-5-1-1.md`)。現行 repo でその値を保持する一次資料は campaign WAL の
終端 `commit` record の `payload.fitness_tps` であり、raw-record producer も arm の throughput を
同じ場所から取る (`orchestrator/campaign/p3_b4_raw_record_producer.py:1320-1325`)。

計数 (結果は `measurement-1.json`、手順は `measure_reference_tps_domain.py`):

| 母集合 | 観測数 | 相異なり | 非有限十進 |
|---|---|---|---|
| `commit.fitness_tps` | 852 | 426 | **0** |
| `bench.median_tps` | 854 | 427 | **0** |
| `bench.tps[]` 系列 | 4222 | 2110 | **0** |

走査 root は worktree の `output/` と共有 checkout の `output/`。WAL 60 file、JSON parse 失敗 0、
stage 内訳は `commit` 918 / `bench_done` 854 / `verify_done` 1144 / `abort` 30 ほか。
十進 token 経由 (`Fraction(Decimal(token))`) と float 往復経由 (`Fraction(float(token))`) の
両方で非有限十進 0。解析不能 token 0。`fitness_tps` が `null` の 66 件は
s1-direct-comparison campaign の commit で、throughput を持たない。

構造的裏づけ — CCBench 出力の解析器 `orchestrator/calibrator/benchparse.py` の
`throughput_tps()` は `float` を返し、代替経路 `commits / extime` も float 除算。
中央値は `orchestrator/calibrator/model.py:236 _median()` の float 演算。
有限 IEEE-754 double は必ず分母が 2 の冪の有理数であり、十進展開は常に有限。
throughput を作る側に有理数演算は無い (`Fraction` の非 test 利用は B-4 分析系・
`paper_story_a1_headline.py`・`s8b_floor_stats.py`・`b10_backoff_shape_sweep.py` だけ)。

実在する scheduled input の列挙 — **0 件**。`output/` 配下で `reference_tps` を含む file は
全 29 件、すべて `output/insights/` 配下の設計文書・変異仕様・裁定逐語であり、
封印済み registry・分析 manifest の生産物は存在しない (完全走査、切り詰めなし)。

## 実測で判明した新事実 (段 4 で明示裁定する)

狭める対象の registry (`orchestrator/campaign/p3_b4_analysis_ledgers.py`) は
**凍結された 5-file analysis source closure の一員**である
(`p3_b4_analysis_prereg_consumer.py:98-104` の `_CLOSURE_PATHS`)。
したがって「registry を狭める」も凍結 closure を動かす。D1344 が却下理由に挙げた
「凍結を動かす費用」は両選択肢に掛かる。ただし closure member の bytes を固定値で pin する
成果物・docs は存在せず (`git grep -ln p3_b4_analysis_ledgers -- docs/` は archive worklog 1 件のみ)、
receipt は live bytes から生成される。拘束は AST 構造 assertion と文書 §5.1.1 の literal 一致である。

## 不変条件

- 規律 2 — 受理集合を**緩める**方向の変更を採らない。丸め受理は不可。
  狭める側は受理集合を縮めるので規律 2 に反しない。
- 事前登録 §5.1.1 の純関数契約・判定順序・invalid 理由 enum を壊さない。
- 本 wave では実装面の差分を作らない (docs / insight / spool fragment のみ)。
- 既存の凍結成果物 bytes・campaign WAL・`output/s8b-freeze` を変更しない。

## 成果物の形

1. `output/insights/2026-09-02_t2102-b4-reference-tps-domain/` — 実測手順・母集合定義・
   計数結果 JSON・段 3 の逐語。
2. `docs/spool/` の worklog fragment と decisions fragment — 択一の確定と、
   registry が凍結 closure 内にあるという新事実。
3. 次 wave 向けの file:line 粒度の実行案 (実装はしない)。

## 分割方針

実装面ゼロの docs-only wave。ただし受理集合に関する択一を確定する段なので
`DW-C00` に従い独立の敵対検証子を省かない。段 2 に plan 子 1 本 (read-only)、
段 3 に異なるレンズの敵対子 2 本 (read-only)。段 5・6 は実装面が無いので飛ばす
(`DW-S04` の実装面差分ゼロによる変異 matrix 免除)。受入全走は免除せず親が実走する。

## (P1) 親の provisional 裁定 — 攻撃対象

- (P1a) `commit.fitness_tps` が `reference_tps` の母集合として正しい。別の
  「certified snapshot の session-level throughput」を保持する一次資料が他に無い。
- (P1b) 上流の全 throughput が float である以上、非有限十進は正当な upstream 出力として
  生じえない。将来の producer が exact ratio を作る余地は「正当な upstream 出力」に当たらない。
- (P1c) 択一は (a) registry を狭める。狭める先は「既約分母の素因数が 2 と 5 だけ」。

## DW-G05 — 成果物影響

放置すると、封印済み registry が「publish 段階で必ず拒否される参照点」へ事前に commit できる。
campaign 実走後に `EVIDENCE_SCHEMA` で落ちるため、201 試行分の実行が raw 記録へ到達しない。
狭めれば同じ拒否が封印前 (実走前) に起きる。値・受理集合・参照のどれが変わるかは
「registry の受理集合が finite-decimal 有理数へ縮む」の 1 点。
