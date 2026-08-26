# S' の 9 対を失敗報告図にした wave の一次資料 (2026-08-26)

`docs/paper-story/2026-08-26.md` §4 が「描ける (未作図)。失敗報告の図として有用」と記していた
縮小主張 S' の登録 9 対を作図した。**新規計測はしていない。** 既存の tracked 成果物だけを使った。

図・キャプション正文・再現手順・入力表・proof chain の正本は
`docs/paper-story/figures/README.md` の該当節である。本書はそこへ書かない一次資料を持つ。

---

## 1. 母集合の確定 (実測)

`output/reports/s1_direct_comparison/report.json` の
`hard_gates.certified.accepted_evidence` は標本ごとの `fitness_tps` を持つ。
role が `block1` と `block2` の標本だけを取り (セルあたり 4+4=8)、
`<workload>:system_gate` の中央値から相手の中央値を引き、相手の中央値で割ると、
同 JSON の `effect_sizes[*].relative_median_difference` **12 件すべてが小数 6 桁まで一致**した。

| 母集合 | 12 件の一致 | 最大差 |
|---|---|---:|
| `block1 ∪ block2` | 12/12 一致 | 0 |
| `floor` 単独 | 0/12 | 0.015312 |
| `floor ∪ block1 ∪ block2` | 0/12 | 0.006271 |

この結論は実装でも裏付けた。`orchestrator/campaign/s1_report.py` の `bind_left_target` は
target/control を `block1` と `block2` だけから作り、`floor_cmp` の CV は
`_between_session_cv` が `floor` role の 8 セッションだけから出す。
**効果量の母集合は block1 ∪ block2、floor は判定境界の算出だけに使う。**

9 対の確定値 (親・段 2 plan 子・段 3 レンズ B が独立に再計算し、3 者とも一致):

| workload | compile-time flags | static backoff | lock ordering |
|---|---:|---:|---:|
| write-heavy | −9.34% | −35.99% | +55.50% |
| balanced | −37.38% | −44.60% | +83.51% |
| read-heavy | −55.12% | −51.89% | +98.43% |

## 2. 測定は `perf stat` 下である (実測)

S-1 の performance 3 campaign の WAL の `run_cmd` は **288/288 件**が
`numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles -- ...`。
`perf record` は 0 件。

同じ検査を既存の後継図 fig2b の入力 campaign 3 件にも掛けたところ、**24/24 件**が同じく
`perf stat` 下だった。

D20 (`docs/decisions.md`) の位置づけ節の字義は「perf 下 tps は overhead 込みで headline 非使用」で
あり、`perf record` に限定していない。D497 は「perf が**無い**ことを性能主張の信頼性の条件に
しない」という別方向の決定で、perf 下で採った tps を headline に使ってよいとは定めていない。

したがって `docs/paper-story/figures/README.md` が fig2b を「D20 の意味で headline 適格」と
分類していたのは D20 本文に支持されない。同 README は自身を「凍結物ではない」と宣言する
living document なので、本 wave で分類語を実測事実へ訂正した。
**図の PNG / PDF / provenance JSON の bytes、各図のキャプション正文、凍結スナップショットは
一切変えていない。**

## 3. `stock_common` を図に描かなかった理由 (段 3 の 2 レンズが対立した論点)

親の provisional は「`stock_common` を参照線として描き、sort の勝ちを相対化する」だった。
実測では sort_best は stock_common を write-heavy +3.34% / balanced +1.36% / read-heavy +0.64% しか
上回らず、system_gate は stock_common を +60.7% / +86.0% / +99.7% 上回る。

段 3 のレンズ B は「描け」、レンズ A は「描くな」と割れた。**レンズ A を採った。**

理由: 参照線にすると、図は「合成軸は stock を 61〜100% 上回る」という**事前登録されていない
第 10 の比較**を主張する器になる。その差は記述計算できるが、S-1a の登録 9 対と p 値が支持する
優越主張ではない。失敗報告の図が登録外の肯定的主張を運んではいけない。

凍結された計測設計 (`output/s1-freeze/measurement_freeze.json`) の各比較定義の `note` は
`stock_common は併記用の文脈セルであり、検定比較対には含めない。` と書いている。
併記は設計の意図どおりだが、**基準線にすることまでは許していない** —
FIGURE_CONVENTIONS §3 の基準線は「主曲線との差を目で追わせる」ものと定義されており、併記とは別物。

代替として (a) 図の構図 (対称軸・等面積 marker・失敗領域の塗り・不成立 banner)、
(b) provenance の `facts.context_cells` に `registered_comparison: false` を付けた記録、
(c) 本書と README への事実の記載、の 3 段で担わせた。

**評価語 (「最弱」「根拠が弱い」) はキャプションに入れていない。** レンズ A の指摘どおり、
否定結果の忠実性は肯定部分を事後に矮小化することも許さないためである。事実の記載と
評価語の付与を分けた。

参考として、凍結設計自身が記録している `sort_best` の選定履歴を逐語で残す。

- write-heavy (`sk_ad`): 本走 argmax 規則で固定。remeasure は参考値としてのみ併記し、再選定には使わない。
- balanced (`sp_dd`): 本走 argmax 規則により sp_dd を固定。balanced の sp_dd は remeasure campaign
  p3-s6-sort-sweep-balanced-sweep-1b39095e で floor 超を再現せず、D46 裁定は差なし。
- read-heavy (`sk_ad`): read-heavy は sweep 未実施。D52 §2.1 の事前固定 sk_ad を採用し、
  comparator は write-heavy 本走 provenance から流用。

## 4. report が参照する freeze と現行 bytes の差 (実測)

凍結 report の `freeze_ref.sha256` = `5c719c07…` は commit
`b4e5cb621e3f8f93de952e9400d4b8dcd34107e0` 時点の bytes。現行
`output/s1-freeze/measurement_freeze.json` = `203de36b…` との差は次の 3 か所だけ。

- `/frozen_at_head`
- `/implementation_hashes/known_axes_freeze/sha256`
- `/cells/read-heavy:sort_best/variant/sources[0]/sha256`

**本図が使う意味内容 — 18 セル定義、12 比較定義とその `note`、`operating_point`、
`workload_flags` — は両版で完全に同一。** provenance の `facts.freeze_proof` に記録した。
旧 bytes の取得を検査の前提にはしていない (bytes 級 gate を作らない)。

## 5. 検査の実効性 — 変異 matrix の結果

`output/insights/2026-08-26_s1-9pair-figure/mutation-spec-final.json`。
runner は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s1_9pair_figure_provenance.py -q -rf`。

baseline PASSED (26 passed)。8 変異すべて KILLED、期待 node と観測 node が完全一致
(MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0)。

| 変異 | 何を壊すか | 落ちる意味検査 |
|---|---|---|
| m01 strict-gate | 判定境界の厳密不等号 `>` → `>=` | `test_n3` |
| m02 judgment-authority | 判定源を凍結 report から奪う | `test_n10` |
| m03 trust-boundary | 未知 field を実装分岐へ入れる (規律 6) | `test_p6` |
| m04 admission-purpose | admission の purpose 差し替え | `test_p7` |
| m05 internal-labels | 内部識別子を図へ露出 | `test_n12` |
| m06 floor-line-shift | 判定線 +3% → +4% | `test_n11` |
| m07 unstable-filter | unstable 標本を落とす | `test_n4` |
| m08 evidence-order | 照合順序 | **意味検査なし** |

**m08 だけは `test_p3` (生成器 source SHA の包括層) でしか落ちない。**

親は当初これを「実 WAL の行が既に `schedule_index` 順なので入力等価」と見たが、
**段 6 の焦点再レビューがこの見立てを否定した。** 実 WAL は整列済みでも、
**凍結 report の `accepted_evidence` は非整列**であり、`_evidence_sort` の sort は
現在の正規入力を受理するために実際に必要である。したがって m08 は等価変異ではなく、
**意味的検出器が存在しない本物の穴**である。現在の production の挙動は正しいが、
この sort を削っても意味検査は 1 件も落ちない。

DW-M03 に従い、m08 を冗長 gate のみと明記して**単独変異の意味的証拠から外す**。
穴を塞ぐ production-facing な負例の追加は、本 wave の成果物 (図・キャプション・provenance・
README) のどの値も変えないため must-fix にはせず、検査上の nit として次の一手へ送る。

probe (全件 SURVIVED 期待で観測 node を集める形) の ledger と本走 ledger は job 側に残した。
probe では 8 件すべてが MISMATCH = 実際には KILLED であり、そこで得た node 集合を
本走の `expected_nodes` に確定した。

## 6. 段 3 と段 6 が見つけた実質的な破れ

段 3 の 2 レンズと段 6 の 2 レビューが、実装前・実装後に次を見つけた。すべて修正済み。

- **絶対規律 6 違反**: `_trace_disabled()` が `build_done.payload` の全文字列を走査しており、
  未知 field が実装分岐を変えられた。裁定済みの単一 key だけを読む形へ直した (m03 が検査)。
- **裁定契約違反**: banner の `NOT ESTABLISHED` と凡例の件数が固定文字列で、凍結 report の
  judgment から導出されていなかった。
- **検出力の穴**: 変異 M1 / M4 / M11 相当が成果物再生成後に生き残る設計だった。
  境界ちょうどの例が実データに無く、report の judgment と再計算 gate が全件一致し、
  unstable 標本が 0 件のため。負例を production を通す形へ置き換えた。
- **独立 golden の取り残し**: real-repo 直列化の inventory を conftest だけ更新すると、
  `test_real_repo_serialization.py` の**独立 oracle 6 集合**のうち 2 つが取り残されて赤になる。
  この二重管理は意図的なので、conftest から import・導出する形へ書き換えてはならない。

## 7. 図の描画欠陥 5 件と、そこから出た検査の穴

親が生成器を実走して PNG を目で見て見つけたもの。V1〜V4 は最初の fix で、V5 と回帰は後続で直した。

- V1: 横軸の目盛 `0` と `3` が重なり「03」と読めた。重なり検査が tick 同士を除外していた。
- V2: データラベルが自分の marker と重なった。offset が data 単位で、実 pixel 距離が不足。
- V3: 凡例の label 文字列が marker glyph を重複して含んでいた。
- V4: 負値のラベルが判定境界側へ伸びて破線・注記と近接した。
- V5: 下段の凡例が回転した x 目盛ラベルと重なった (実測交差 31.87〜419.69 px²)。

**V5 の修正が回帰を生んだ。** 凡例を figure 下端へ移す際に `set_in_layout(False)` を使ったため、
`savefig(bbox_inches="tight")` の bbox 計算からも外れ、**凡例が図から完全に消えた。**
重なり検査は緑のままだった — **存在しない artist は何とも重ならない**ためである。

これは親が実物を見て初めて分かった。恒久対応として、必須テキストの exact 集合が実在し、
かつ実保存 bbox の内側にあることを検査へ加え、負例 2 件 (凡例削除、`set_in_layout(False)` 復元) を
required にした。

## 8. 作図規約への適合は「部分適合」である

provenance の `facts.figure_conventions_compliance` は `"partial"` を記録している。
標本と集約値は WAL からその場で再計算するので FIGURE_CONVENTIONS §1 を満たすが、
判定と p 値は hash で束縛した凍結 report を権威として読むので §1 の字義には合わない。

これは意図した設計である。作図側が判定を作り直すことは絶対規律 2 に触れるため、
凍結された裁定をそのまま描くことを優先した。
**規約側にこの限定例外を書き足すかは未裁定であり、ユーザー裁定へ返す。**
