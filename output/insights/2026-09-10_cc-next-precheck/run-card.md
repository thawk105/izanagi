# CC次実験: K2新提案1評価と次提案への還流

**T-2783追補 (2026-09-19、D2148項3):** 以下は当時の入力・予算の記録として保持する。
次のK2手動loopでは、明示critic診断をplanner/coder両方の型付き入力へ渡す局所経路を適用する。
手順は `docs/phase3-s4b-runbook.md` のT-2783追補、同機体・同job内stock対照を含む次の実走計画は
`output/insights/2026-09-19/t2783-critic-input/next-run-plan.md`。
旧予算の比較armなしを次走へ流用せず、実走予算は別途確定する。T-2783では3巡目を投入しない。

本カードは2026-09-10の新規ユーザー依頼による静的precheck。実装変更・候補生成・実走は行っていない。
照合起点はlocal main `8ca260c3de0898f4af4db4ba544d04cd05c57804`。

## 判定と実験の問い

既存のClaude登録roleとPegasus job bodyを使うhuman-supervised経路を特定した。
ただし本Codex sessionでは生成roleを起動できない。Claude実行sessionでの登録確認と、
本カードに対する新規実走の指示が揃うまでは投入しない。D1936項1の1本認可はT-2581で実施済み。

問いは「fresh planner/coderが提案を作り、既存検疫・verifier v2による評価結果を
criticと次の提案に使えるか」。backoffの整数1..1000を選ぶパラメータ探索であり、新CC構造の合成ではない。
T-2581は既存proposalの20を再評価しserializable・anomalies=0・1 committedへ到達した成功。
別の値や別bytesも新しい編集軸・de novo・LLM固有優越の証拠にはならない。

## 実行主体と入力・出力

| 段 | 既存の実行主体 | 入力と出力・編集範囲 |
|---|---|---|
| 射影 | fresh Claudeメインsession | manifestを既存resolverで解決。測定データとwhiteboardをinline射影し、専用job rootへ入力と逐語を保存 |
| 方向 | 登録`planner-v4`、opus/high、tools=[] | current_perf、leading_indicators、whiteboard、宣言済みK2 knowledge_inputから方向・magnitudeのみ。値・機序を出さない |
| 候補 | 登録`coder-v4-autonomous-k2`、opus/high、tools=[]、fresh子 | K2-compatibleなhole仕様、planner_direction、baseline、whiteboard、knowledge_input。K2 envelope全体を返す。ファイル編集権限なし |
| 評価 | 親が既存`tools/pegasus/p3_s4_loop_pegasus.sh`を計算ノードへ1本投入 | `load_proposal_file`→帰属照合→既存diff/effect/文法検疫→patchharness→pipeline。正規writerだけがsource・WAL・checkpointを更新 |
| 診断 | 登録`critic`、opus/high、Read/Grep/Glob/Bash | 同走の`s4_loop_digest.txt`。緑の指標と、存在する赤の構造化診断を読み、attribution/recommend/avoid/uncertaintyを返す。書込み禁止 |
| 次提案 | 親→fresh planner→fresh K2 coder | 更新した測定入力と5フィールドのwhiteboardから次proposalを生成。親がcriticを解釈した`prior_critic_reverse`も保存。2本目は評価しない |

Codex native roleは0、static adapter14件はruntime blocked。
`.codex/agents/README.md`が禁止するgeneric child代用、`tools/run_codex_role.py --live`の利用はしない。
`claude` executableは存在するが、実sessionのAgent型一覧・spawnの成立はこのprecheckでは未確認。
D95の開発実装authorと実験のtool-less coderは異なる契約。コード・テスト変更が必要なら
本カードを実行せず別のD95 Codex author作業とし、親やClaudeで代筆しない。

## 固定する最小入力

- 軸: `silo-backoff-magnitude`。holeは`double now_backoff = <接尾辞なし数値リテラル>;`の1文。
  valueは有限な整数1..1000、literalと一致。演算式・呼出し・条件・追加文は文法外。
  `SOURCE_REL`と`MARKER_ID`の既存holeのみ。stock枝・検証・測定・identity・hookは編集しない。
- CCBench pinは`p3_s4_loop.PIN`。T-2581 run-cardの完全SHAと一致する版を使用。
- manifestは`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2182-k2-eval-run/materials/knowledge-manifest-wal-only.json`。
  bytes SHA-256=`68eb3d5f4bcdab1e91a379868d188493bda548c5f26d6c3965a00dc5c9a70977`。
  resolver digest=`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`。
  sourceはcommit `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の
  `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl` 1件。
  source bytes SHA-256=`2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`。
  全文を解決して使い、設計説明の混入・指示検出をすり抜ける加工はしない。
- 初期whiteboardは空。初期測定入力は同sourceの時系列最後の`bench_done`
  （variant `dad58f9f9000`、ts `1783560370.5855775`）を選び、最良値選択はしない。
  throughput=487088.5、abort_rate_pct=7.2、cache_miss_rate_pct=32.29014422247246、
  IPC_overall=0.7387153219395488、last_delta_pct=null、contention_levelは「未判定」とする。
  これは歴史測定の初期参照値であり、現pinのbaseline測定・現在の比較対照とは呼ばない。
  sourceのsettled=falseと環境差を親の射影に明示し、不確実性を隠さない。
- `--emit-planner-context`はwhiteboardと任意knowledge_inputを出すだけ。
  current_perf/leading_indicatorsは親の責務であり、率0..1をpercentへ100倍する。
  K2ではleakproof_contextへ既存K0/K1向けの知識禁止全文を混入させない。
- 新しいrole出力を`proposal-1.json`へ保存。plannerは内側proposal、coderは
  proposal/knowledge_use/classification/data_boundary_reportを含むK2 envelope全体。
  `prior_critic_reverse=null`。T-2581の`proposal-wal-only.json`は再利用しない。
- 呼び手分類は`known_result_conditioned_derivative`、de_novo_claim=false。
  coder自身の分類と差があれば差を残し、再現値ならreproduction_or_selectionとして報告する。

## 既存job bodyへの投入契約（将来の実行担当用）

1. 登録roleを確認したfresh Claude sessionで、ここまでの入力と新proposalを保存する。
   新提案が20/30/40を再提案した場合は「既知値の再提案」と記録し、未評価値生成の成功へ数えない。
   新しい値が出るまで再抽選する操作はしない。
2. 固定した実行commitから専用submit-treeを作り、既存`dev_wave_submodule_init.py`と既存の
   `tools/pegasus/fetch_third_party.py hydrate`で初期化・依存供給する。
   cache-rootはT-2581で使った`/work/1/SFC/tanab/izanagi-thirdparty-cache`を明示する。
   T-2581 submit-treeと出力を再利用しない。
   実行commit、source_root、入力hash、request ID、証拠rootは当該runの記録へ保存する。
3. `qsub -v`で下表を渡し、既存job bodyを投入する。scheduler stdout/stderrはrepo外の新規file。
   新shell・launcher・harnessは作らない。submit時のqueue状態、計算ノードでの既存排他判定、
   pinned-clean、依存供給、reservation、正しさゲートを満たさない場合は投入・継続しない。

| 環境変数 | 値の決め方 |
|---|---|
| `IZANAGI_S4_REPO_ROOT` | 当該run専用submit-treeの絶対path |
| `IZANAGI_S4_EXPECTED_HEAD` | そのtreeの固定40桁HEAD |
| `IZANAGI_S4_EVIDENCE_ROOT` | 当該runの新規`evidence/attempt-0001`絶対path |
| `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` | 既存hydrate成功結果のsource_root |
| `IZANAGI_S4_PROPOSAL_PATH` | 新しい`proposal-1.json`の絶対path（必須、fixture fallbackを使わない） |
| `IZANAGI_S4_KNOWLEDGE_MANIFEST` | 上記wal-only manifest絶対path |
| `IZANAGI_S4_CODER_ROLE` | `coder-v4-autonomous-k2` |
| `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` | `known_result_conditioned_derivative` |
| `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` | `false` |

job bodyは`--allow-coder-derived-build --isolate-worktree --fetchcontent-prebuild-receipt`
とK2引数、`--run-iteration`を渡す。外部output-root上書きはunsetされるので、
出力の分離は専用submit-treeで行う。同manifest/configではT-2581と同じcampaign ID
`p3-s4-loop-s4-autonomous-409e13f8`になり得る。新しいrunの識別はsubmit-tree・実行commit・
request・証拠rootの組で行い、「新campaign ID」とは主張しない。過去出力をコピーして
checkpointやduplicate cacheを持ち込まない。旧treeの同campaignは非接触。

## 予算・停止・完了の読み方

- 親の上限: planner/coderを各2回、critic1回、評価job1本。再投入・再抽選・比較armなし。
  1本目の診断を使った2個目のproposal保存までで止める。実走は別依頼でのみ行う。
- 既存machine budgetは10 iteration/3600秒。job reservationは既存3時間。
  3600秒はcheckpointの入口/末尾で判定する値で、buildを中断するwatchdogではない。
  3時間は依存build等を含む外枠で、10本走らせる認可ではない。
- scaleはrecords=100000、threads=4、rr50、skew0.9、rmw=false、extime=1、reps=2。
  既存defaultの配線規模に限定し、headline性能・正式選択・因果効果は主張しない。
- schema/指示検出/帰属/検疫の赤はその候補を拒否。anomalyは即rejectで失格。
  検証赤の性能を推定せず、残る構造化診断をcriticへ渡す。trace parse/build failureは
  verifier terminal取得としない。job rc=0だけでも成功としない。
- harnessのstopがcontinue以外なら既存runbookどおり停止。continueならdigestをcriticへ渡し、
  実測whiteboardと親が解釈した逆方向boolを次proposalへ反映する。
  接続先を区別する。`prior_critic_reverse`のconsumerは`_fold_critic_reverse`と停止判定であり、
  planner/coderの方向生成器ではない。次生成へ届く既存の型付き入力は測定値、抽象whiteboard、
  planner_directionである。criticの豊かな反例・機序文を次coderへ自動投入する接続はこの経路にない。
  親の解釈を介するrunbook上の還流と、このboolの機械的消費を同一視しない。
  raw反例の自動入力やcriticによる改善の因果実証を完了条件にすると本カードの範囲では足りない。
  赤が出なければ「赤の反例還流を実証した」とは書かず、緑結果の還流として報告する。
- 完了証拠は新規spawn入力/逐語、proposal、検疫結果、当該runのverifier terminalとWAL、
  digest、critic出力、次proposalとその入力。重複値・拒否・停止は正直に結果として残す。
  次proposalは未評価でありcertifiedではない。次提案への利用と改善の因果実証も別である。
- 本経路はlegacy criticを使うためB-4 ablationには非適格。D1936項8・9の赤precursorや
  正式選択の不足を、この1本で充足したとは扱わない。

## 最小の未充足事項

1. 実行側fresh Claude sessionで`planner-v4`、`coder-v4-autonomous-k2`、`critic`の登録を確認する。
   executableの存在だけでは代替できず、Codex role有効化の開発は必要条件にしない。
2. 本カードの1評価＋次提案までを実走する新規指示。本waveはprecheckのみという依頼であり、
   D1936項1で認可済みのT-2581の1本を追加実走の認可へ広げない。

新proposalとそのhash、実行commit・allocation・依存source_rootは将来の実行時に既存手順で
確定するrun入力であり、新機構の欠落ではない。このprecheckで架空の値や実行成功を埋めない。

## 現物の照合先

- `docs/decisions.md` D95、D1429、D1936項1・2・8・9。
- `docs/phase3-s4b-runbook.md` §§0–4、`docs/phase3.md` 後続段2・4・5。
- `output/insights/2026-09-10/paper-methods-ja/implementation.md`
  （2026-09-11再開時に、mainの資料整理後の実在pathへ追従）。
- `output/insights/2026-09-10_t2581-k2-pin/run-card.md`、同README、worklog(1431)、指定job handoff。
- `.claude/agents/planner-v4.md`、`coder-v4-autonomous-k2.md`、`critic.md`、`.codex/agents/README.md`。
- `p3_s4_loop.py`: `planner_context_payload`、`load_proposal_file`、`default_cfg`、
  `_prepare_knowledge_campaign`、`drive_iteration`、`make_critic_digest`、`check_stop`。
- `backoff_hole_grammar.py`、`pipeline.py`、`knowledge_manifest.py`、既存Pegasus job body。
