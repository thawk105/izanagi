# 段 4 裁定 — dev-wave t2265-itt-seq0

段 2 プラン (`s2/s2-plan.md`)、段 3 敵対相談 2 本 (`s3/s3-sol.md` 因果推論レンズ、
`s3/s3-luna.md` 実装規律レンズ) を親が裁定する。親は所見のうち現物で裏を取れたものだけを real とした。

## 1. real と裁定した所見 (採用)

### R1 (sol + luna、独立に一致) — 推定量 §4 の添字域を書き直す。must-fix

v1 §4 は `Y[r,i]`、`i = 0, ..., m_r - 2` と**明示している**。位置除外を §7 にだけ書くと、
§4 と §7 が文書内で食い違い、凍結した推定量が一意にならない。親の草稿の
「推定対象、outcome の定義を 1 字も変えていない」は**誤りであり撤回する**。
§6 の時間 block も残存 outcome の index/count 基準であることを明記する。

**成果物影響:** raw `i = 0` を含むか否かで各 `D[r]`、`theta_log`、`cluster_sd`、CI、
`primary.decision` のすべてが変わる。

### R2 (sol) — v2 を「完全に前向きな事前登録」と呼ばない。must-fix

v2 の除外規則は、v1 の主判定 `inconclusive` と欠測の内訳 (0 commit 57 件、うち 55 件が `seq = 0`) を
**見た後に**選んでいる。`window_commits` は outcome `T` の分子そのものであり、その 0/非 0 は
outcome の粗い観測である。したがって v2 は「outcome を部分的に開示した後に凍結した、事前指定の
再解析計画」であって、独立な前向き確認試験と同格ではない。

**親の判断:** これは本 wave を止める理由にならない。ユーザーの依頼は「規則を結果より先に凍結し、
凍結したことを成果物で示す」ことであり、それは満たせる。**満たせないのは「完全に前向き」という
より強い主張の方**であって、その差を文書と insight に明記する。

**成果物影響:** `primary.decision` の値は変わらないが、それを確認的証拠として受理できる範囲と、
README が主張してよい強さが変わる。

### R3 (sol) — 「`seq = 0` の event は処置と無関係」は言い過ぎ。must-fix

正しいのは「`seq = 0` の**窓** `T[r,0]` は最初の割当 `Z[r,0]` より前に閉じる」である。
event 0 は同時に最初の割当 `Z[r,0]` を持つので、位置除外は**最初の割当の直接対比 `Y[r,0]` を
落とす**。さらに `T[r,1]` は `Z[r,0]` の影響を受けうる状態のまま、新しい最初の対の分母に残る。
除外の正当性は「outcome や割当の値を見ずに、全 run から一律に先頭 1 件を落とす」という
**選択規則が処置前である**ことに依るのであって、「event 0 に処置が無い」からではない。

**成果物影響:** 位置除外を因果的に受理する根拠と、推定対象の記述が変わる。

### R4 (luna) — 「受理集合を広げない」は artifact への射影に限定する。must-fix

public API の入力組 `(diagnostic_paths, preregistration_path)` として見ると、
`(v1 束縛の成果物, v2 文書)` が**新たに受理され**、`(v1 束縛の成果物, v1 文書)` は**拒否へ移る**。
不変条件として書けるのは「成果物 JSON へ射影した受理集合は v1 のまま広がらない」だけである。
brief の書き方を改める。

**成果物影響:** 不変条件の主張範囲が変わる。実装の向きは変わらない。

### R5 (luna) — 解析器は将来の v2 束縛成果物を拒否する。real、ただし設計として受理する

v2 発効後に producer を回すと成果物は v2 の sha を記録するが、本解析器は v1 固定なのでそれを拒否する。
brief の DW-O10 の記述「将来の走行が v2 の sha を記録することは正しい」は、解析器側の狭さを
併記しないと過度な一般化である。

**親の裁定:** 本解析器は**この 12 件の cohort 専用の offline 解析**であり、将来 cohort 用の
互換層は作らない (DW-G05、ユーザーの「仮想リスク向けの追加は scope 外」)。狭さを
事前登録 §9 と解析器の docstring に明記して閉じる。

### R6 (luna) — 変異の帰属修正。must-fix (変異事前登録へ反映)

- M1 (`events[1:]` を `events` へ戻す) は位置除外と 0 commit 判定の 2 つの意味が結合する。
  期待 node は rebasing test **1 本**に限定する。
- M5 は「selected の current だけに狭める」と「検査自体を削除する」の 2 変異へ分ける。
  さらに 0 を最後の event に置くと `math domain error` で死に、帰属が算術例外へ逃げる。
  `_run_difference` を直接呼び、その直前の対を membership から外す設計にする。
- M6 (v2 文書比較を v1 定数へ取り違え) は、現行 file-bound test の形のままでは殺せない。
  未変更の v2 文書を使う正例呼出しを同 test に置く。
- M7 (artifact pin の取り違え) は top-level gate と row gate が二重にあるため、
  「top=v2 / 全 row=v1」と「top=v1 / 対象 row=v2」に分けて別々に変異させる。
- M9 は「診断側を旧文言へ戻す」と「性能側へ診断文言を書く」の 2 変異へ分ける。

**成果物影響:** 変異 matrix の帰属が一意になる。直さないと受理集合を広げる変異が生存する。

### R7 (luna) — 親 brief の pin 記述の誤り。real、訂正する

`tools/check_docs.py` の whole-file SHA-256 pin は codex 用 cleanup-branches **skill だけ**ではなく、
`.claude/commands/cleanup-branches.md` も別 sha で固定している (`check_docs.py:751-753,6546-6554`)。
本件の事前登録文書に whole-file pin が無いという結論は変わらないが、brief の説明は不正確だった。

### R8 (sol) — 凍結の証拠の限界。real、限界として明記する

commit DAG が示せるのは「v2 文書の blob が解析器 commit と結果 commit の祖先にある」ことまでで、
「別経路で先に計算していない」ことは証明できない。remote 公開で強められるが、**本 project は
AI から push しない**ため採らない。

**採用する無料の追加証拠:** 新しい `analysis-result.json` の `inputs[].sha256` を、
前 wave の `output/insights/2026-09-07_t2265-backoff-itt/analysis-result.json` の同 field と
突き合わせ、12 成果物の bytes が同一であることを示す。

## 2. refuted / 不採用と裁定した所見

- **(sol) v2 を独立データまたは未開封 holdout へ当てる。** 本 wave の依頼は既存 12 件の再解析であり、
  新規測定は明示的に scope 外である。限界として書くにとどめる。
- **(sol) 割当列が seed の LCG と一致するかを解析器が検査していない。** 事実だが v1 から不変であり、
  本 wave の変更面ではない。新しい gate を足さない (ユーザーの scope 指定)。持ち越し項として記録する。
- **(sol) v2 文書 commit を remote へ公開する。** push 禁止のため採らない。

## 3. scope 裁定

**本題 (必須):** 事前登録 v2 の凍結 (§0 / §0.1 / §4 / §5 / §6 / §7 / §9)、解析器の位置除外・
0 commit 判定範囲・sha 2 分割・`ANALYSIS_VERSION` の v2 化、テスト、12 件の再解析。

**副題 `not_certified` (採用する。ただし別 commit・別ファイル群):**
luna は scope から外すことを推奨したが、**ユーザーが「余力があれば直す」と名指しした項**であり、
事前登録 §1 と §10 に既知の記録上の欠陥として登録済みである。luna 自身が変更面を
`_artifact_contract_metadata` の exact dict を要求する既存 assertion 2 箇所
(`test_t2187_adaptive_const_probe.py:1968-1985` と `:2079-2097`) まで含めて**完全に列挙した**ので、
実装可能である。

- 編集面は本題と**素集合**である (本題 = `orchestrator/campaign/` + `orchestrator/tests/`、
  副題 = `tools/pegasus/probes/` + `orchestrator/tests/test_t2187_adaptive_const_probe.py`)。
- 性能側の文言は **1 byte も変えない**。`_performance_artifact_identity` と
  `tools/plotting/plot_t2187_adaptive_consts.py:336-345` が exact 一致を要求しているためである。
- 副題が緑にならなければ**副題だけを落として本題を land する**。本題の判定を人質にしない。

**scope 外 (実装しない):** 将来 cohort 用の互換層、割当列の LCG 検査、新規測定、
仮想リスク向けの gate・検査・台帳・一般化。

## 4. 変異事前登録 (実装前に固定。DW-M01)

| # | 位置 | 変異 | 期待 node (単一理由性) |
| --- | --- | --- | --- |
| M1 | `analysis.py` `_run_difference` の `analysis_events = events[1:]` | `events` へ戻す | rebasing test 1 本のみ (全 commit 正の fixture) |
| M2 | 同 `outcome_count = len(analysis_events) - 1` | `len(events) - 1` へ戻す | rebasing test |
| M3 | 同 対の作り方 | 残存 zip をやめ raw zip を enumerate して `seq != 0` で filter | rebasing test (最初の index が 1 になる) |
| M4 | 同 0 commit scan | `analysis_events` を `events` へ戻す | seq0-zero test |
| M5a | 同 0 commit scan | `selected` の `current` だけに狭める | seq>=1-zero test (`_run_difference` 直接呼出し、0 を最後の event に置き直前の対を membership から外す) |
| M5b | 同 0 commit scan | 検査ごと削除する | 同上 |
| M6 | `analyze_counterfactual` の文書 sha 比較 | v1 定数へ取り違える | file-bound test (未変更 v2 文書の正例呼出しを含む) |
| M7a | `_load_artifact` の top-level pin | v2 定数へ取り違える / `{v1,v2}` へ広げる (top=v2・全 row=v1 の入力で検査) | artifact-bound test |
| M7b | `_validate_row` の row pin | 同上 (top=v1・対象 row=v2 の入力で検査) | artifact-bound test |
| M8 | `ANALYSIS_VERSION` | `/v1` のままにする | public analysis test の逐語 `/v2` assertion |
| M9a | producer の `not_certified` 代入 | 診断側で旧文言を書く | mode-specific test (逐語 literal) |
| M9b | 同 | 性能側へ診断文言を書く | 同 test |

**単一理由性の確認は実装後に行う** (F820)。確認できない変異は登録から外し、実効 gate へ再照準する。

## 5. プラン v2 (実装子へ渡す確定手順)

段 2 プランの「変更手順」を、上記 R1〜R7 で次のとおり改める。

1. 事前登録 v2 の docs 編集は**親が行う** (docs-only)。実装子は触らない。
2. 解析器の変更は段 2 プランの本題 7〜10 のとおり。ただし
   - `ANALYSIS_PREREGISTRATION_SHA256_V2` の値は、**親が v2 を commit した後に確定した逐語 sha** を渡す。
   - docstring に「この解析器は 2026-09-07 に取得した 12 件の cohort 専用であり、
     v2 束縛の成果物は受理しない」と書く。
3. テストは段 2 プランのとおり。ただし R6 の帰属修正を反映し、
   `_synthetic_cluster` 型 (production の出力を期待値へ戻す) を新しい test に再利用しない。
4. 副題は別ファイル群で実装し、`test_t2187_adaptive_const_probe.py:1968-1985` と `:2079-2097` の
   exact dict assertion も同時に直す。
