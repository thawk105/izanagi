# 段 4 裁定 — [T-401] racct 欠測の恒久対応 (2026-08-06)

段 3 の 2 レンズ (`s3a-review-trust-boundary.md` = A、`s3b-review-effectiveness.md` = B) が
それぞれ 9 件、計 18 件を real と自己申告した。親が重複を畳み、コードで再照合して裁定した結果を
R 番号で示す。**本 wave は「設計案まで」なので、採用した所見はいずれも実装せず設計へ反映する。**

| R | 出所 | 判定 | 採否 | scope | 親の再照合 |
|---|---|---|---|---|---|
| R-01 | A1 = B1 | **real** | 採用 (推奨案を差し替え) | 内 | `_collect_accounting` は最後の attempt の snapshot を採る。1 回目 permission → 2〜5 回目 present-invalid の応答列で、現行は `available=true, integrity=false` (観測無効)、段 2 の案 A は `available=false, integrity=null` (観測有効) になる。受理集合が広がる。両レンズが独立に到達した |
| R-02 | A2 | **real** (例示は限定) | 採用 (不変条件 I1 の根拠) | 内 | `qsub -e` が job stderr と scheduler 出力を同じ file に合流させ (`run_probes.py:942-954`)、job body も `>&2` を書く。期待 ID と一致する偽 block を採取**前**に弾く行は存在しない。ただし「T-361 で `expected_records=2` に一致して通る」という例は、`.e` を `expected=leg.nodes` の件数検査へ配線した場合にだけ成立する。段 2 はその配線を成立案から除いており、例の射程はそこまで |
| R-03 | A3 ≈ B2 | **real** (帰属は是正) | 採用 (不変条件 I2 の根拠) | 内 | `_select_accounting_snapshot` は available かつ integrity=true の候補を最優先で選び、**available な候補が 1 つでもあれば integrity=false の候補を探しにいかない**。cause 導出も `accounting_snapshot["available"] is True` を `.e` より優先する (`run_probes.py:2826-2834`)。新供給源を同じ slot へ挿すと、既存の racct integrity failure と `.e` cause failure を隠す。ただしこれは案 C / D の**文面**の欠陥ではなく、文面の約束を果たす機構が示されていないことの欠陥である |
| R-04 | A4 | **real** | 採用 (案 C 不採用理由) | 内 | 案 C は同じ `.e` bytes を会計 integrity と終端 path 3 の双方の根拠にする。F92 が求めた 3 経路の独立性が字面だけになる |
| R-05 | A5 | **real・最重** | 採用 (案 C 不採用の決定打) | 内 | 案 C は job-writable な `.e` を `accounting_integrity_valid` の producer にする。危険な job body が `Request ID: <期待値>` を 1 行足すだけで exact-one を落とし、`observation_valid=false` にして**自分の危険観測を台帳から排除できる**。D161 が会計 integrity を gate に残した理由と正反対で、F93 の fail-blind の再発である |
| R-06 | A6 | **real** | 採用 (不変条件 I4 の根拠) | 内 | 段 2 の `O_new = O_current ∧ …` は改修後の値だけで計算すると恒真になる。旧 evaluator を版固定して同じ raw へ再適用しない限り「同じか狭い」は検査ではない |
| R-07 | A7 | **real** | 採用 | 内 | erratum-1 の `permission` / `empty` / `error` は racct command の失敗様態の語彙であり、hash 不一致・署名不一致・roster 採取失敗を区別できない。攻撃由来の不整合を benign な欠測へ畳むと `run_probes.py:396-400` が素通しする |
| R-08 | B3 | **real** | 採用 (実装前提) | 内 | 会計 field の意味を変える案は、legacy 判別・observer adapter・source 選択・保存 raw 再評価・wave-state 再構築・resolve 台帳書換え・attempt-result / session summary・driver README の全経路を同時に動かす必要がある。段 2 はこれを列挙していない |
| R-09 | B4 | **real** | 採用 | 内 | `leg.nodes` は `#PBS -b` の要求 node 数で、現行 exact-count は racctjob stdout の Request ID record 数を数える。qstat roster は job identity の存在数であって Started/Ended/Elapse を持つ最終会計 record ではない。`-b 2` の完全列挙の一次資料も無い |
| R-10 | B6 + 段 2 §90 | **real** | 採用するが**実装しない** | **外** | 親が独立照合した。`_saved_nqsv_stderr_accounting` の `valid` は `bool(matching_blocks) and not errors` で manifest 束縛を要求せず、`scheduler_root.glob("*.e")` が未改名ファイルも候補にする。resolve の終端実証 path 3 はこの弱い `valid` を使う。**会計証拠ではなく終端実証 provenance の問題**なので T-401 の scope 外。裁定パッケージで返す |
| R-11 | B5 | **real** | 採用 (ユーザー裁定へ明示) | 内 | 案 A が改善するのは固定待ち 16 秒と subprocess 8 本だけで、会計欠測も証拠強度も 1 ミリも回復しない。「恒久対応」の成功条件を証拠回復から死荷重削減へ変更する裁定が段 2 に明記されていなかった |
| R-12 | A8 = B7, B8 | **real** | 採用 (erratum-1 で是正済み) | 内 | 親 brief の実測 8 (8 秒)、実測 6 (manifest 束縛の一般化)、(P2) の「唯一の外部信号」。`brief-erratum-1.md` E1–E3 |
| R-13 | A9 = B9 | **real** | 採用 (erratum-1 で是正済み) | 内 | 「certified 選択へ流れない」は直接 schema consumer の話であって因果的独立の証明ではない。`brief-erratum-1.md` E4 |
| R-14 | B3 の付随 | **real・nit** | backlog | 外 | `test_run_probes_evaluator.py` の fixture 既定が `accounting_available=False` に `accounting_integrity_valid=True` を組み合わせる。production の欠測 snapshot は `null` なので、fixture が production の値域を代表していない。受理集合は変えないので nit |

**refuted はゼロ**である。R-02 と R-03 は主張の核が real で、例示・帰属の射程だけを親が狭めた。

## 段 2 の推奨 (案 A) を採らない

段 2 は案 A (permission marker を見た command の retry を 1 回で打ち切る) を推奨したが、
R-01 により「受理集合不変」という採用根拠が崩れた。**両レンズが独立に同じ反例列へ到達しており、
親のコード再照合でも成立する。** 段 2 の推奨はここで却下する。

## 採用する設計 — 案 A′

案 A から**取得回数を減らす部分だけを外した**もの。

- 正式な会計源は `racctjob` + `racctreq` のまま据え置く。`.e` を `accounting_available` /
  `accounting_integrity_valid` へ昇格させない。
- **sample 数を減らさない。** permission に分類されたときに落とすのは attempt 間の 2 秒 sleep だけとし、
  5 回の取得自体は行う。R-01 の反例列でも現行と同じ最終 snapshot に到達するため、受理集合は変わらない。
  削減されるのは固定待ち 16 秒であって、観測の情報量ではない。
- `REQUIRED_EXTERNAL_COMMANDS` は据置。存在検査を外すと permission policy の変化を検出できなくなる。
- 会計欠測の恒久性は「そのとき観測された分類」であって「将来もそうであるという保証」ではないと
  台帳へ明記する (A1 後段、レンズが brief の一般化を攻撃した点)。

案 A′ でも回復するのは待ち時間だけで、独立した会計裏取りはゼロのままである (R-11)。
これは欠点ではなく、**現在の権限では証拠回復が不可能**という事実の正直な記述である。

## どの案を採るにせよ守る不変条件

- **I1**: job-writable stream (`.e`) から来た bytes を `accounting_integrity_valid` の producer に
  しない。危険な主体が自分の観測を無効化できる経路を作らない (R-05、F93)。
- **I2**: 新しい会計源を既存 `_select_accounting_snapshot` の同じ slot へ挿さない。source 別 integrity を
  独立の conjunct にし、`racct=false ∧ 新源=true` が必ず観測無効へ倒れることを設計表で示す (R-03)。
- **I3**: 同一 artifact / hash を会計 gate と終端 path の双方の根拠に数えない (R-04、F92)。
- **I4**: 「受理集合が同じか狭い」は、旧 evaluator を版固定して保存 raw corpus へ再適用し
  `new_authoritative ⇒ old_authoritative` を機械検査したときだけ主張する (R-06)。

## 実装しない裁定と、その射程

本 wave はユーザー引数どおり設計案までで終える。**実装差分が無いため、変異 matrix と受入全走は
対象外**である (`DW-S04`)。案 A′ の実装、R-10 の是正、I1–I4 の機械化はいずれも次 wave 以降に属し、
着手はユーザー裁定 (下記 U-1〜U-4) の後とする。
