# 段 6 レビュー裁定 — [T-2145]

親 = dev-wave manager。実装 patch = `s5.patch` (14 file、1066 行追加)、適用先 = wave worktree。

## 親が実走した検査 (fix 前)

計算ノードのキューが空いたので実走できた。**`orchestrator/tests/test_sort_swo_oracle.py`
= 104 passed / rc=0 / 55.13s** (Pegasus request 967196.nqsv、Elapse 60S)。
batch conformance node を含む。これにより段 3 レンズ A が残した唯一の拡大経路
(trusted evaluator と実行行列の食い違い) は、**production の producer で**閉じたことになる
(記録済み成果物の再利用ではない)。

親が pytest 抜きで直接呼んだ検算 (`probe_s5_verify.py`) も全項目一致。値域 79、round-trip 失敗 0、
旧 2 gate 全通過、権威集合 15 件が byte exact かつ admission 通過 (過剰拒否 0)、
正準化は冪等、非 IR 8 例は全件拒否。

## 所見の裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| F1 | 親 + A1 | body 異常が `parameter-signature` へ誤分類 | **real・must-fix** |
| F2 | A2 | 正準 TU の compile/run failure が候補 `REJECT` のまま | **real・must-fix (最重要)** |
| F3 | A3 | auditor が恒真化した型で正準 IR を veto しうる | **real・must-fix (最小修正)** |
| F4 | A4 | 現役 docstring が旧「動的反例 gate」を名乗る | **real・must-fix (分割)** |
| F5 | A5 | 既存 public 拒否 test が private 恒真検査へ弱められた | **real・must-fix** |
| F6 | B1 | critic が `rule_id` を落とし `admission_stage` を持たない | **real・must-fix** |
| F7 | B2 | ledger 未更新、かつそれだけでは赤にならない | **real・採用 (実測後)** |
| F8 | B3 | M10 の指定 node が admission を呼ばない | **real・must-fix (帰属の修正)** |
| F9 | B4 | R10 の検査が producer 定数の自己参照で独立でない | **real・must-fix** |
| F10 | B5 | `assert compile_count == 1` が恒真 | **real・nit だが採用** |

refuted は無し。両レンズとも「token 化・正準化から受理集合が広がる経路」「行列不一致が
`PASS` になる経路」は見つからないと報告し、親の実走 104 passed と整合する。

## F2 の裁定 (最重要) — 親が現物で確認した

`sort_swo_oracle.py:3264` が `candidate_source = _translation_unit(canonical_statement)` で
**正準形**を compile しているのに、`:3380` の `if finding is not None: return REJECT` が
その compile/run failure を候補の欠陥として返す。正準形は admitted IR から trusted renderer が
生成したものなので、その compile 失敗は候補の欠陥ではない。

段 4 裁定 R1 と D344 決定 4 に反する。**受理集合を狭める wave が起こしがちな過剰拒否**であり、
`DW-M01` が正例対照を要求している向きそのものである。

**修正:** `ir` が確定している評価経路では、compile / run / timeout / 非決定性の finding を
候補 finding にせず `UNAVAILABLE` へ帰属させる。`ir` が無い旧 raw harness 経路の分類は変えない。
`PASS` へ倒す経路は作らない (規律 2)。

## F4 の分割 (docs は親が書く)

- `orchestrator/campaign/p3_s4_loop_sort.py:47` と
  `orchestrator/campaign/s6_sort_sweep.py:28` の docstring / コメント → **fix 子**。
  `s6_sort_sweep.py` は `CANDIDATES` の変更を禁じているが、**docstring とコメントの修正は許可する**。
- `docs/phase3-s5-sort-runbook.md:190` → **親が段 7 で書く** (実装子・fix 子は docs 禁止)。

## F7 の扱い (実測に依存する)

ledger の更新は実測 JUnit が要る。値を合成してはならない。
fix 完了後に親が JUnit 付きで走らせて ledger と suite count / digest を更新する。
キュー混雑で最後まで実測できない場合は、**未更新のまま land せず、残件として明記する**。

## F8 の帰属修正

M10 (過剰拒否の正例対照) の sink を、`CANDIDATES` 15 件が render 集合に含まれることを見る
node から、**15 件が `validate_sort_implementation` に実際に通ることを見る node**へ改める。
fix 子が当該 node へ admission 呼び出しの assert を足す。

## 変異事前登録の改訂 (DW-M01、fix 前)

R9 の M1〜M9 は据え置き。M10 の sink だけ上記 F8 のとおり改める。
`test_contract_manifest_hashes_and_literal_are_exact_snapshot` と
`_CURRENT_ORACLE_CONTRACT_ID_GOLDEN` は identity churn なのでどの変異の kill 根拠にも数えない
(F568)。fix で新設・改名した node は、実装後に親が collected nodeid の実在を再確認する。

## fix の分割 (DW-S06-B)

**1 子の一枚岩とする。** 理由: F1・F2・F5・F8・F9・F10 は `sort_swo_oracle.py` と
`test_sort_swo_oracle.py` の同じ受理・分類契約を触り、F6 はその producer 出力の consumer 側である。
reason id の閉集合と `REJECT`/`UNAVAILABLE` の分類は 1 つの producer/consumer 契約であり、
分割すると契約が単位を跨いで壊れる。
