## 1. 入力組立て — N3 / P3

以下、参照を短縮する。

- `R` = 指定された repo root
- `J2` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2`
- `J3` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3`
- `C2` = `J2/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8`
- `L` = `R/orchestrator/campaign/p3_s4_loop.py`

**N3 は成立する。P3 は受領証の補完検査を強める必要がある。**

`main` は `L:2978` で site を解決し、`L:2979` で admission、`L:2989` で emit 分岐へ入る。`PEGASUS_LOGIN` は許可集合外なので `ExecutionGuardError` になる (`L:133–144`)。site は実 hostname と NQSV 証拠から決まり、環境変数で計算ノードを偽装する経路ではない (`site_policy.py:30–45,66–83`)。

なお「login は OTHER」は一般には誤りである。`pegasus0N` でも NQSV 証拠が無い場合の分類と、通常の `PEGASUS_LOGIN` を区別すること。

| 面 | production 関数直呼びと CLI の関係 | 親の手順 |
|---|---|---|
| 診断抽出 | 同じ bytes と関数なら同じ6 fieldになる。`L:1237–1245` | `J2/verbatim/critic-2.md` を bytes で読み、要約せず抽出 |
| context | 同じ state・cfg・knowledge・診断なら同じ辞書になる。`L:1270–1314` | K2・非B-4・reflux onを維持 |
| 両入力への転写 | 同じ helper。完全入力全体の検証器ではない。`L:1248–1267` | 測定値・knowledge・whiteboard は親が組み立てる |
| 受領証 | CLI は `layout.ensure()` と `write_receipt()` を実行。直呼びでは実行しない。`L:1597–1628` | 旧 campaign には書かず、既存受領証を読取照合 |
| 受領証の一致条件 | **digest だけでなく正準 bytes 全体一致**。`knowledge_manifest.py:575–614` | `receipt_bytes(resolved, classification=旧受領証の宣言値, de_novo_claim=False)` と原本 bytes を比較 |
| layout | CLI は cfg から現 checkout の campaign を選ぶ。probe は `C2` を明示。`L:3001–3004`、`J3/probe_diagnosis_liveness.py:53–56` | campaign IDだけでなく絶対 root と lock の identity preimage を照合 |
| policy_hint | CLI は指定値を search_config に足す。probe は足さない。`L:2990–2994` | 今回は未指定。追加すると identity も変わる |
| site 束縛 | probe は計算ノード契約を明示して cfg を構築。実行場所の admission は受けていない。`probe:44–49` | **入力再構成専用**として記録し、計測認可の代替にしない |

probe の digest 一致・knowledge 一致・campaign IDは `print` であり、不一致時に停止する assertion ではない (`probe:38–51`)。さらに `ki == ki_r2` は JSON オブジェクトの等価性であり、「同 bytes」の検査ではない。親はこれらを実際に照合して不一致なら止める。`probe:74` の単語走査も指示検出の代替にならない。

runbook追補との対応は次のとおり。

1. **手順1と不一致**：CLI emit を使わず直呼びにする。login拒否、receipt処理省略、旧 campaign の明示指定を記録する (`docs/phase3-s4b-runbook.md:136–138`)。
2. **手順2とは一致可能**：同じ抽出器・exact6field・元 bytes の SHA を使う。source SHA は真実性や送達の証明ではない (`同:139–141`)。
3. **手順3に経路差**：context は「手順1のCLI出力」ではなく production builder の返り値。任意dictで代用しない (`同:142–145`)。
4. **手順4はprobe未実施**：probe の coder入力には古い planner-3 の方向が残る。planner-4出力保存後に置き換え、最終JSONを保存して送る (`同:146–149`)。
5. **手順5はprobe未実施**：probe はcontextと診断しか保存しない。両完全入力・両prompt・逐語出力を別途保存する (`同:150–152`、`probe:76–79`)。

## 2. planner-4 / coder-4 の完全入力

**round 2のWALとcheckpointから射影してよい。新しい評価 campaign の履歴とは区別して記録する。**

今回のトップレベル key 集合を次に固定する。`policy_hint` は足さない。

```text
planner-4:
  current_perf
  leading_indicators
  whiteboard
  knowledge_input
  k2_critic_diagnosis

coder-4:
  leakproof_context
  knowledge_input
  baseline
  planner_direction
  whiteboard
  k2_critic_diagnosis
```

根拠は `J2/project_round2_inputs.py:48–55`、`J2/build_coder_input_3.py:13–27`、`L:1258–1263`。planner本文の基本3 fieldに、production contextが供給するknowledgeと今回の診断を加える形である (`.claude/agents/planner-v4.md:28–73`、`L:1287–1307`)。

内側の key は次のとおり。

| field | key集合 |
|---|---|
| `current_perf` / `baseline` | `throughput_tps`, `abort_rate_pct` |
| `leading_indicators` | `cache_miss_rate_pct`, `contention_level`, `IPC_overall` |
| whiteboard各要素 | `iteration`, `direction`, `magnitude`, `result`, `delta_pct` |
| `knowledge_input` | `data_boundary`, `knowledge_level`, `knowledge_manifest_sha256`, `sources` |
| `k2_critic_diagnosis` | `data_boundary`, `source_sha256`, `attribution`, `recommend`, `avoid`, `uncertainty` |

`k2_critic_diagnosis` はトップレベルの兄弟 keyであり、whiteboardやknowledge sourceへ入れない (`L:1226–1234,1287–1307`)。

`planner_direction` は、**round 2とK2 role本文に合わせるなら** `{axis,direction,magnitude,justification}` の4 key (`coder-v4-autonomous-k2.md:94–99`)。一方、runbook追補 `:147` の「そのproposalへ設定」を丸ごと代入と解すると `uncertainty` も入る。これは文書上の差である。今回の「round 2の形に診断を足す」指定に従い、planner-4のproposalから上記4 keyを射影する案とする。planner出力原本の `uncertainty` は削除せず保存する。

現物 `C2/runs/wal.jsonl:4` は以下だった。

- `median_tps=687508.5`
- `abort_rate=0.07400000000000001`
- `llc_miss_rate=null`, `ipc=null`

従って、`throughput_tps=687508.5`、`abort_rate_pct=7.400000000000001`、cacheとIPCはnull、`contention_level="未判定"`。率は欠測を保持して×100する (`runbook:65–67`、`J2/project_round2_inputs.py:39–49`)。

`C2/loop_state.json:2–12` はiteration 1、whiteboard 1件、decrease/small/success、delta null。`load_loop_state` → `whiteboard_for_planner` を使う。後者は非null deltaを拒否する (`L:1198–1218`)。旧stateを新submit-treeへ移植する意味ではない。

入力側検査の範囲にも注意が要る。

- `assert_no_ability_probe_material` は任意の入れ子のkey・文字列を走査する。診断にも免除はなく、禁止字面があれば拒否する (`projection_guard.py:233–243,385–410`)。
- ただし `planner_context_payload` / `k2_next_generation_inputs` はこのtripwireを自動実行しない。loaderでの呼出し対象は**出力proposal**である (`L:2438`)。
- dormant adapterの基本入力schemaはトップレベル `additionalProperties=false` で診断keyを持たないため、完全K2入力を渡せば拒否する (`.codex/role-adapters/coder-v4-autonomous-k2.json:32–145`)。これを変更したり、role起動へ使ったりしない。
- 今回の完全入力についてtripwire実行結果は**未確認**。親が既存検査を行い、拒否されたら診断を削って通す処置はしない。

## 3. proposal-4 の受理検査 — P4

**呼出し形はround 2からそのまま使える。未来のcoder-4出力が通ることは未確認。**

`J2/build_proposal_3.py:14–31` を次の形で写す。

```python
doc = {
    "planner": planner4_output["proposal"],
    "coder": coder4_output,  # K2 envelope全体
    "prior_critic_reverse": False,
}
assert_closed_proposal_schema(
    doc, require_auditor=False, require_coder_value=True,
    coder_contract=CODER_CONTRACT_K2,
)
decision = backoff_hole_grammar.validate_backoff_preflight(
    doc["coder"]["proposal"]["implementation"]
)
# decisionがacceptedでなければ停止
load_proposal_file(
    proposal4_path,
    knowledge_input=ki,
    coder_role="coder-v4-autonomous-k2",
)
```

**注意：文法関数の返り値を表示するだけでは検査通過にならない。** round 2 glueの `:29–30` は表示だけなので、親はacceptedを確認する。

K2 coder envelopeの必須集合は次のとおり。

| 階層 | exact key集合 |
|---|---|
| coder外側 | `proposal`, `knowledge_use`, `classification`, `data_boundary_report` |
| proposal | `axis`, `value`, `implementation`, `justification`, `confidence` |
| knowledge_use各要素 | `source_index`, `use` |
| data_boundary_report | `instruction_like_content_detected`, `details` |

根拠は `projection_guard.py:44–49,324–335`、`.codex/role-adapters/coder-v4-autonomous-k2.json:150–193`。`instruction_like_content_detected` は外側の兄弟keyではない。

loaderはoutput schema、指示検出申告、knowledge参照indexの順に検査する。検出申告trueは拒否する (`L:2292–2317`)。roleとknowledgeの片方だけ指定も拒否する (`L:2376–2390`)。診断そのものをproposalへ追加するとclosed schema違反になる。

3本とは別に、valueとliteralの帰属一致は評価経路でも強制される。schemaと文法の個別通過だけで同一値を証明したとは書かない (`L:1666–1710,1923`)。

**P4のFalseは妥当。** 比較対象は前の評価proposal-2のdecreaseとcritic-2のdecreaseである (`J2/materials/proposal-2.json:5`、`J2/verbatim/critic-2.md:26`)。planner-4が選ぶ方向から逆算しない。Falseは逆方向連続カウンタを0へ戻す (`L:2279–2289`)。fresh campaignでも、外部から持ち込む前巡feedbackとしてFalseを保存することを明記する。

## 4. 既知値の扱い — P2

**P2の「20だけ評価しない」はユーザー逐語に整合する。25/30/40まで評価禁止を拡張する根拠はない。**

| coder-4の値 | 扱い |
|---|---|
| 20 | 既知値再提案として保存。評価jobを投入しない。再抽選しない |
| 25 | round 2評価済みの既知値と記録。受理検査通過なら予算内の1評価対象 |
| 30 | run-cardで既知値。再提案と記録して1評価対象 |
| 40 | run-cardで既知値。再提案と記録して1評価対象 |
| その他 | 受理域・検査を通れば1評価対象。「この列挙外」だけで未評価と断定しない |
| 範囲外・不正出力 | 拒否として保存。修正生成・再抽選しない |

根拠：`J3/rulings/user-decision-2026-09-19.md:3–10`、`run-card.md:70–72`、`next-run-plan.md:15–17`。旧run-cardの列挙は20/30/40であり、25はround 2の現物WALによって既知になった値である。

- **20で投入しない案**：再評価禁止を守れるが、本巡の新WAL・verdict・stock対照・通常のAO取込み先は生まれない。
- **20で投入する案**：fresh WALなら過去treeの重複によるskipを期待できず、20再評価禁止に反する。旧campaignの入口停止を利用した名目的投入も目的を満たさない (`L:2553–2573`)。

## 5. 評価jobの投入 — P5 / N2

**fresh submit-tree案は成立する。新WAL・新start_wallは新treeで実際に確認する条件であり、現時点の実績ではない。**

親のlogin側手順は次の順に固定する。

1. `J2/setup-submit-tree.sh:4–11` のjob rootをJ3、SHAを `a99425b66258911973785b11fd7d194884aeec64` に置き換え、専用 `J3/submit-tree` を新規作成する。旧treeや旧campaignをコピーしない。
2. 同 `:13–27` の既存submodule初期化を行い、再帰状態とpinを確認する。戻り値を確認せず後続へ進めない。
3. 同 `:29–37` のhydrateを実行する。cache-rootは既存の `/work/1/SFC/tanab/izanagi-thirdparty-cache`。hydrate結果JSONの `.source_root` を採用する。
4. HEAD完全一致、tracked/untracked clean、proposal-4とknowledgeの検査結果、未使用attemptを確認する。
5. `J2/qsub-submit-0002.sh:18–26` を**本巡唯一のattempt**用に写し、README §7の投入形でqsubを1回だけ呼ぶ。

hydrateの `--staging-root` は必須ではない。既定は `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` (`silo_ladder_rung1.py:68–70`、`fetch_third_party.py:143–150`)。親ディレクトリは `.gitignore:25` の対象である。既定を使ってもhydrateログ自体はjob rootへ保存する。

環境変数は以下の9個。

| 区分 | 変数・設定 |
|---|---|
| 必須4個 | `IZANAGI_S4_REPO_ROOT`, `IZANAGI_S4_EXPECTED_HEAD`, `IZANAGI_S4_EVIDENCE_ROOT`, `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` |
| proposal | `IZANAGI_S4_PROPOSAL_PATH=J3/materials/proposal-4.json` |
| K2 | `IZANAGI_S4_KNOWLEDGE_MANIFEST`、`IZANAGI_S4_CODER_ROLE=coder-v4-autonomous-k2` |
| K2宣言 | `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION=known_result_conditioned_derivative`、`IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM=false` |

shell契約上、K2後半2個は任意だが、今回は宣言を固定して明示する (`p3_s4_loop_pegasus.sh:19–20,55–96`、`tools/pegasus/README.md:359–365`)。coder自身のclassificationと差があれば保存し、黙って一致させない。

投入argvは `tools/pegasus/README.md:394` と同じ9変数の `qsub -v … -o "$ATTEMPT/job.stdout" -e "$ATTEMPT/job.stderr" tools/pegasus/p3_s4_loop_pegasus.sh`。submit-treeをcwdにする。

**F1028対策**：親はattempt directoryを作るだけ。qstatの写し・親ログはその外へ置く。job bodyが `allocation-qstat.*`、reservation、receiptを所有する (`README.md:373–379`、shell `:263–265`)。

identityは `spec_content`, `ccbench_commit`, `search_tag`, `search_config`, `trial` の5 key (`ident.py:212–229`)。現物C2のpreimageをSHA-256計算した結果は `409e13f81d8a…` だった。現行 `default_cfg`、Pegasusの `measurement_env`、同knowledge digestを束縛する形は同じである (`L:147–161,1552–1628`)。ただし**現行builderからの再計算一致は今回未確認**なので、親はpreimage全体とIDを照合する。短いIDだけの一致にしない。

新treeではcampaign/WAL/checkpointがまだ存在しないことを確認する。layoutはmoduleのrepoを基点に出力する (`layout.py:42–48`)。checkpoint不在なら `LoopState(start_wall=time.time())` が作られ、入口停止判定へ進む (`L:2553–2564`)。wall予算は新start_wallとの差、上限3600秒 (`L:165,1327–1337`)。旧stateの時刻を更新して再利用する案ではない。

preflight拒否時はrequest ID、stdout/stderr、存在する場合のcompute-result、driver起動有無、campaign生成有無を記録して終了する。初期拒否ではcompute-resultが作られない場合もある (`README.md:359–362`)。**評価0本でも投入attemptは1回として残し、再投入しない。**

## 6. 同jobのstock対照 — N1 / P1

**既存S4 job bodyにはstock armがない。候補だけを評価しても、ユーザー要求のstock対照を満たしたことにはならない。**

- shellはproposalまたはfixtureの排他的1起動のみ (`p3_s4_loop_pegasus.sh:580–593`)。
- S4 CLIの値口は `--value` と `--run-iteration`。stock指定口はない (`L:2797–2854`)。
- 値は有限な数学的整数1..1000。`-1` は `value-range` 拒否 (`backoff_hole_grammar.py:745–759`)。
- 候補genomeは `BACKOFF_FIXED=int(coder.value)`、templateとholeを通って評価される (`L:1930,1969–2012`)。`--value -1` をstock代用にはできない。

`tools/pegasus/*.sh` と `orchestrator/campaign/*.py` のCLIを検索し、近い経路を確認した結果は以下。

| 経路 | 本要求の代替にならない理由 |
|---|---|
| A1 paired | stock genomeはあるが、study・acquisition receipt・policyのscaleに束縛される。S4 proposalを追加するCLIではない (`paper_story_a1_paired.py:1467,7107–7128,8917–8928`) |
| B10 grid | 登録sweepを起動する。通常extendedはP2の100万records/48threads/3秒/5repを使う (`b10_backoff_grid.sh:610–635`、`backoff_extended_sweep.py:1384–1389`、`p2_2.py:54–57`) |
| floor campaign | official protocol束縛のdriver起動。S4候補とstockを同一jobへ組み合わせる口ではない (`floor_campaign.sh:1213–1225`) |
| guided `--genome` | 過去landscapeのreplayであり新しいstock実測ではない (`guided.py:225–242`) |
| `loop.run_campaign` | stockを評価し得るPython APIはあるが、既存S4 shellから呼ぶstock CLIではない (`loop.py:347–383`) |

**条件を満たす既存経路は見つからなかった。** 全shellと全CLIのあらゆる組合せについての不在証明までは未確認であり、N1の「他jobではpinも揃えられない」という強い一般化は採らない。確認できた障害は、S4候補と同条件stockを同jobで実行する既存の結線がないことである。

scope外の設計メモは次に限る。

- job bodyに、同allocation・同compiler・同依存prefix・同pinを保持するstock評価stepが必要。
- driver側に、無改変stock源、`BACK_OFF=1`、同 `default_perf()` を既存 `run_campaign` へ渡す評価口が必要。
- trace/perf別build、verifier、admission、排他、receiptを既存pipelineのまま通す。
- stock WALはpipeline自身が発行する。候補WALへ親がrecordを手書き・移植しない。
- stockを同campaignに含めるか別campaignにするかでidentityとdigestの意味が変わる。spec/search_configを変えればIDも変わる (`ident.py:196–229`)。`409e13f8`維持を先に約束しない。

従ってP1は「今回stock未実走として返す」方針にはできるが、**原依頼の完全達成条件としては不成立**。親の裁定にこの未充足を明記する。

## 7. 走行後の還流とAO取込み — P6 / P7

**P6は既存1巡の終端criticとして説明できる。P7の3 event・件数は正常分岐に限定する。**

critic-3の起動条件は、評価がcertifiedで、停止理由がcontinueであること。`check_stop` はiteration予算、wall予算、収束、逆方向枯渇を先に判定し、最後だけcontinueを返す (`L:1319–1354`)。末尾判定は `L:2606–2607`。runbook `:117–125` に従い、continue以外では起動しない。

`check_stop` 自体はcertified条件を検査しない。P6のcertified条件は親側の追加の制限であり、anomaly/reject後のcritic起動を今回省く理由として記録する。critic後にplanner/coderを再度起動しない。

正常分岐では、新campaignを `C3`、新WALで確認したvariantを `V` として次の順に取り込む。

```bash
python3 -B -m orchestrator.campaign.p3_s4_loop \
  --record-agent-output planner_proposed "$J3/verbatim/planner-4.json" \
  --agent-campaign-dir "$C3" --agent-input "$J3/materials/planner-input-4.json" \
  --agent-variant "$V" --agent-wal-ref "${REFS[@]}" \
  --agent-prompt "$J3/materials/planner-prompt-4.md"

python3 -B -m orchestrator.campaign.p3_s4_loop \
  --record-agent-output coder_proposed "$J3/verbatim/coder-4.json" \
  --agent-campaign-dir "$C3" --agent-input "$J3/materials/coder-input-4.json" \
  --agent-variant "$V" --agent-wal-ref "${REFS[@]}" \
  --agent-prompt "$J3/materials/coder-prompt-4.md"

python3 -B -m orchestrator.campaign.p3_s4_loop \
  --record-agent-output critic_attributed "$J3/verbatim/critic-3.md" \
  --agent-campaign-dir "$C3" --agent-input "$J3/materials/critic-input-3.json" \
  --agent-variant "$V" --agent-digest "$C3/s4_loop_digest.txt" \
  --agent-wal-ref "${REFS[@]}"
```

`J3` は上記絶対path、`REFS` は新WALから作るshell配列とする。plannerは `{proposal: …}` wrapper、coderはK2 envelopeの逐語を使い、この形では `--agent-output-key` を付けない (`L:2719–2730`)。

取込み分岐はparse直後、site解決より前にreturnするためloginで利用できる。評価用optionとは併用できない (`L:2847–2854,2865–2879`)。

- `input_sha256` は**保存した実入力JSONをparseしたオブジェクトのcanonical SHA-256**。出力hashやraw file hashではない (`L:2731–2764`)。
- `--agent-wal-ref` は `J2/wal_refs.py:10–14` と同じく、新WAL各recordに `layer3_report.canonical_record_ref("wal", record)` を適用する。round 2のhash列をコピーしない。
- 取込みはWALが非空・非truncated・単一envであること、variant/refの実在、knowledge receipt digestを検査する (`L:2704–2709,2740–2760`)。
- criticは入力のdigest SHA、指定digest、campaign digestの三者一致を要求する (`L:2767–2773`)。

critic入力は `J2/materials/critic-input-2.json:2–21` の形を写し、campaign root、digest path/hash、variant、genome、実測値、request ID、HEADを新走行へ更新する。fresh campaignのiterationは通常1であり、role名critic-3に合わせて3へ書き換えない。

`output_format_request` は次の4見出しを各1回とする。

```text
## attribution
## recommend
## avoid
## uncertainty
```

旧実測値を残さず、stock不在、欠測、非同時刻比較の限界も当該走行の事実で記す。入力保存後にcriticへ渡し、出力を逐語保存する。

材料レポートは次の形。

```bash
python3 -B -m orchestrator.campaign.layer3_report \
  "$C3" "$J3/layer3_report.json" \
  --output-root "$J3/submit-tree/output" \
  --generated-from-head a99425b66258911973785b11fd7d194884aeec64
```

argvは `layer3_report.py:1163–1177`。正常分岐の期待値はAO 3、機序仮説1、`source_refs = WAL N + wb 1 + ao 3`。WALが5なら9件である。双射は `同:331–339`。

例外分岐は以下。

- certifiedだが停止：criticなし、通常AO 2。
- reject/anomaly：criticなし。WAL/checkpointの実在・内容に応じた件数。
- 20で評価なし、またはpreflightでcampaign未生成：取込み口の既存WAL条件を満たさない。**C2へ書かず**、J3に入力・逐語を保存し「本巡AO取込みなし」と記録。
- どの分岐でも、3件へ合わせるためにcriticやWALを捏造しない。

## 8. 記録の主張限定

根拠はround 2 README `:172–182` と `next-run-plan.md:15–30`。本巡では次の境界を保つ。

| 書いてよい主張 | 書いてはいけない主張 |
|---|---|
| 同じ診断6 fieldを両完全入力へ組み込み、保存JSON全文をinline送付した | source SHAやAOのinput hashだけで実受領を証明した |
| role出力が診断を参照・採用したと自己申告した | 診断が提案値を変えたという因果 |
| 候補値、既知値再提案、検査の受理・拒否 | 10が正解、既知値が出たから生成失敗 |
| verifier verdict、anomaly数、terminal WAL、実測値 | 改善の実証、候補間のcertified選択 |
| knowledge_use/classificationの逐語 | K2利用の因果、新CC構造の合成 |
| criticのattributionを材料として保存した | 機序の実証、B-4適格化 |
| stock対照は未実走だった | 過去20/25を今回の同時刻stock対照として使用した |

本wave固有の追加記載は次のとおり。

- **入力生成はCLI emit未使用**。production関数直呼びと補完照合の範囲を明記する。評価・AO取込みCLIまで未使用だったとは書かない。
- 同job stock対照は未実走で、ユーザー要求のこの部分は未達。候補だけの結果をpair評価として報告しない。
- 入力のwhiteboardはC2、新評価のcheckpointはC3。同じcampaign IDでも別走行である。
- `delta_pct=null`、successはcertifiedの意味。性能改善に読み替えない。
- 20分岐・preflight拒否・critic非起動・AO未取込みを欠落なく記録する。

AOのprovenanceは申告した入力と記録方式を残すもので、送達receiptではない (`L:2761–2764`、round 2 README `:140–141`)。材料レポートも既定で `certifying_input=false` (`layer3_report.py:982`)。

## 総括

| 前提 | 検算結果 |
|---|---|
| P1 | 既存S4口でstock対照を出せない点は確認。stock未実走は原依頼の未充足として残す |
| P2 | 妥当。20は評価しない。25/30/40は既知値として記録し、受理後の1評価対象 |
| P3 | 条件付き。digest一致だけでなくreceipt正準bytes、identity全体、完全入力を照合 |
| P4 | Falseで妥当。前評価のdecreaseに対しcritic-2もdecrease |
| P5 | fresh tree・唯一のattemptで妥当。新WALと新start_wallは投入前後に確認 |
| P6 | certifiedかつcontinue時のcritic最大1回。次の生成へは進まない |
| P7 | 正常分岐のみAO 3・source_refs=N+4。評価なし・停止時は件数を減らして正直に記録 |

コード・設定・scriptの編集、pytest、評価、commit、pushは実施していない。proposal-4の受理、role送付、現行builderのID再計算は未確認である。

読取専用のPython照合を1回試みたが、`guard_bash` が「防護pathと不透明構文の同居」を理由に実行前拒否した。その後は許可されたcat/jqによる読取りへ切り替えた。拒否された検査を緑とは扱っていない。