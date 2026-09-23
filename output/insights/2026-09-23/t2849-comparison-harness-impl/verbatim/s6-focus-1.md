**GO（静的再レビュー）。** `16ee35040` を基準に `bb869de43`・`a4f7a2323` を確認しました。テスト・変異は実行しておらず、焦点走2回目の結果は含めません。以下の closed は静的な閉鎖判定です。

根拠の略記（行番号は `a4f7a2323`）：

- `H` = `orchestrator/campaign/t2849_comparison_harness.py`
- `G` = `orchestrator/campaign/t2849_generators.py`
- `TH/TG/TE/TP/TA/TL/TJ` = `orchestrator/tests/` 配下の順に `test_t2849_comparison_harness.py`、`test_t2849_generators.py`、`test_t2849_loop_entry.py`、`test_t2853_trace_preservation.py`、`test_t2849_comparison_aggregate.py`、`test_t2849_llm_round.py`、`test_t2849_job_contract.py`

| 所見 | 重要度 | 判定 | 根拠・閉鎖理由／未修正なら残る影響 |
|---|---|---|---|
| T1 | must-fix | **closed** | `TE:131–152`：layout を campaign ID ごとに分離。既定 preimage・genome・3種の ID の期待値を維持。未修正なら異なる config が lock を共有し、参照入口の検証が停止する。 |
| T2 | must-fix | **closed** | `TE:38–61`：実際に `run_campaign` へ渡した context と `is` で一致する生成呼出しを1件要求し、その authority を検査。未修正なら policy 束縛用 context を誤って失格とする。 |
| T3 | must-fix | **closed** | `pipeline.py:2601–2604,2658`、`TP:79–159`：障害注入を圧縮関数へ限定し、原本・verdict・例外・未設定時の期待値を維持。未修正なら fixture の git 起動で止まり、保全失敗境界を検証できない。 |
| T4 | must-fix | **closed** | `TH:299–312`、`H:422–444`：正しい4見出しの critic fixture に変更。coder の whiteboard・baseline・prior・diagnosis を一つずつ除く負例は、それぞれ ValueError に届く。未修正なら継承拒否の検証まで到達しない。 |
| T5 | must-fix | **closed** | `H:70–81,255–280,576–589`、`TH:358–366`：公開前に入れ子を複写し、後続 timing 更新の波及を遮断。未修正なら返却 view と保存 event の値が食い違う。 |
| T6 | must-fix | **closed** | `tools/t2849_llm_round.py:139–143`、`TL:153–163`：既存の完全な implementation validator を呼ぶ。未修正なら `1 + 2` のような非 literal proposal が公開される。 |
| A-R1 | must-fix | **closed** | `H:152–157`、`TH:214–250`：参照にも `src_token == STOCK` を要求。全 workload の別 source 負例と STOCK 正例を持つ。未修正なら別 source が参照値・reference ratio に混入する。 |
| A-R2 | should | **closed** | `TG:37–64`、`G:150–154`：実際の `BOGenerator.ask` から EI に渡す分散を独立式と比較。未修正なら EI 呼出しへの雑音追加変異が名指し試験を生存する。 |
| A-R3 | should | **closed** | `TH:235–242`、`H:153`：sidecar・variant は正常で WAL build genome だけを変えた負例を追加。未修正なら WAL 側照合の削除を名指し試験で検出できない。 |
| A-R4 | should | **closed** | `H:536–548`、`TH:322–337`：初回 sweep 順序生成を計時内へ移動し、event と集約で7秒を要求。未修正なら生成費用が過小になる。 |

T1〜T6 の重要度は今回の再レビューで付しています。なお、失敗ログの `DID NOT RAISE ValueError` は T6 の文法試験で、T4 の記録された失敗は critic 見出しエラーです。両経路を別々に確認しました。

**期待値弱体化の攻撃：不成立。**

差分に期待値の反転・skip・試験削除はありません。T1・T3・T4 は裁定された fixture／注入位置の変更です。T2 は追補どおり評価 context だけに限定し、CLI 到達、context の一意性、machine/K0 の authority の有無、submission sidecar を引き続き要求しています。接頭辞を除けば `Boundary` に到達できず、M1 の検出力も残ります。

既存試験の変更は `test_ccbench_spawn_sites.py:94` の登録先関数名の追随だけです。固定 zstd argv の起動件数1という制約は維持されています。

**新規回帰の攻撃：いずれも不成立。**

| 観点 | 静的な確認 |
|---|---|
| STOCK 参照の正例 | `TH:214–221` の全 workload 正例は新条件を満たし、`H:178–195` の certified 経路へ進む。追加拒否は STOCK 不一致で、正常な参照の値を変えない。 |
| event／view／series.json | `H:74–77` は同じ複写済み event を保存・保持する。後続の計時は `H:576` で追加され、最終 evaluation-result に残る。`H:654–679` の費用集約も最終 event を採る。 |
| handshake | `H:586–589` は複写後の evaluation-result に `digest_path` を加えて公開。`tools/t2849_llm_round.py:167–174` の consumer が必要とする field は維持。role/critic 費用の接続も `H:292–300,664–675` で維持。 |
| zstd 保全境界 | `pipeline.py:2601–2604` は従来と同じ argv・入出力・`check=True`。失敗は `:2177–2194` で捕捉され原本を保持し、未設定なら保全を呼ばず cleanup する。 |
| 正常 literal | `backoff_hole_grammar.py:581–717` の既存 validator は単一の正常 literal を受理する。`TL:37–39,63–66` の `double now_backoff = 12;` 正例も公開まで要求している。 |

変異については、以下の**名指し試験が単一変更で FAIL する静的経路**を確認しました。実測 kill の報告ではありません。

| 変異 | 名指し試験の根拠 | FAIL に至る差 |
|---|---|---|
| M1 | `TE:27–61` | 接頭辞拒否により評価境界へ到達しない。 |
| M2 | `TE:65–88` | 参照 genome と exact flags が不一致になる。 |
| M3 | `TE:92` の `test_reference_rejected_outside_harness` | B-5 入口で期待する拒否が消える。 |
| M4 | `TP:50–66` | 圧縮前削除で完全な inventory・復元 bytes を得られない。 |
| M5 | `TP:79–102` | 失敗後の原本存在 assertion に反する。 |
| M6 | `TP:105–110` | 保全例外が返却結果を置き換える。 |
| M7 | `TP:136–159` | 未設定時に保全を行うと、原本削除・無副作用の期待に反する。 |
| M8 | `TH:118–123` | 初期点の B=0 に反する。 |
| M9 | `TH:126–134` | retry 後の B=1 に反する。 |
| M10 | `TG:67–78` | Tier0 失敗を除外しないと候補1000への限定が崩れる。 |
| M11 | `TG:20–34` | log 距離に基づく独立2×2 oracle と不一致になる。 |
| M12 | `G:152` → `TG:48–64` | `v + NOISE` は EI 入口の独立分散 assertion に反する。既存の直接 EI 検査も維持。 |
| M13 | `TG:95–103` | 同点で親を置換すると `(10,100)` 保持に反する。 |
| M14 | `TH:137–141` | 初期点 endpoint、値5の期待に反する。 |
| M15 | `TA:21–38` | 他系列の anomaly を外すと random 系列の失格訂正・fallback が消える。 |
| M16 | `TA:41–53` | 品質欠測の score=None を stock で埋めてしまう。 |
| M17 | `TH:162–171` | 最良300を採ると最新正常100・initial-2 の期待に反する。 |
| M18 | `H:153` → `TH:235–242` | WAL genome 照合だけを削ると、追加負例が certified に到達する。 |
| M19 | `TH:144–148` | N_eval=2 を reps に使うと5 rep の証拠を正常分類できず、score=100 に反する。 |
| M20 | `TH:151–159` | LLM argv の machine flag 不在要求に反する。 |
| M21 | `TH:174–180` | 拒否後の評価で a を iteration にすると iteration=1 に反する。 |
| M22 | `TH:183–211` | 拒否・評価 event の role 費用転記 assertion に反する。 |
| M23 | `TJ:20–23` | driver が観測する bench lock の値が不一致になる。 |
| M24 | `TJ:26–38` | 単一起動の履歴または driver rc の期待に反する。 |
| M25 | `TL:49–65` | planner/coder 両方への prior 配送・完全一致に反する。 |
| M26 | `H:152` → `TH:245–250` | STOCK 照合だけを削ると、自己整合した別 source 負例が certified に到達する。 |

規模は wave 起点 `3886a1fd3` から対象 HEAD までの `git diff --numstat` の**追加行**を集計しました。役割文書・adapter・review ledger も production に含めています。

| 区分 | 基準 `16ee35040` | 修正後 `a4f7a2323` | 上限 |
|---|---:|---:|---:|
| production | 1,427 | **1,436** | 2,000 |
| test | 1,159 | **1,221** | 1,600 |

規模超過の攻撃は**不成立**です。

## 総括

- 対応表：**closed 10 / partial 0 / regressed 0**
- 新規所見：**must-fix 0 / should 0 / nit 0**
- **GO（静的判定）**。焦点走2回目と変異 kill の実測結果は、この判定には含めていません。