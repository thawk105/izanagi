## 総括

価値判断では、**毎走の費用に見合わない検査はあります。**
35 file の判定は、**毎走必須15 file・5,779.5秒／別系列12 file・8,187.4秒／要分割8 file・6,987.9秒**です。
分割対象から移す695.7秒を合わせると、別系列相当は**8,883.1秒、受入全体の34.5%**です。
上位35 file の毎走側には、分割後 **3,293 node・12,071.7秒**を残します。
認証層比較、文献検索、Codex 比較実験は、CC の材料レポートとは別の成果物です。
runner・履歴監査・文書手順の検査も、CC の正しさ検査と同額の反復投資を正当化できません。
一方、anomaly・verifier・証拠再導出、および F485 を捕まえる実行到達 probe は残します。
wall は条件が整えば**約268〜298秒**という見込みですが、**未測定であり300秒以内を保証しません**。
選択走の道具はありますが、別系列を確実に完走させ、未実行を検知する機構はありません。
**本案は D532 の「selection の縮小」に該当します。価値上の推奨と実装許可は別であり、親は現行裁定のまま実装できません。**

## 判定表

file はすべて `orchestrator/tests/<file>.py`。秒数は指定された費用表の走です。

分類の `A/B` 等は、同じ検査が複数成果物を守る重複関係です。分割対象では、**研究側と純粋な D を重複なしで集計**しました。研究側と運用側の assertion が一つの node に同居する場合、その node 全体を研究側に残しています。

遅れの表記は次の意味です。

- **R**：毎走から外した場合、独立した代替検出の保証がなく、検出までの上限は**無限**。次の成果物発行までに気づく保証がない。
- **S**：現行機構では同じく**無限**。後述の別系列を実装すれば、正常稼働時は**24時間以内の完走**を要求する。障害時に保証できるのは期限超過の検知と利用停止であり、故障箇所の特定まで24時間とは主張しない。
- **R/S**：研究側は R、移す側は S。

「consumer が検査する」は即時の独立検出を意味しません。その consumer の検証器自身が壊れる場合、同じ検証器の再実行は代替になりません。

| 順位 | file | 秒 | 守るもの：何が壊れると赤になるか | 分類 A–E | 気づく経路・担当 | 遅れの上限と実害 | 判定 | 費用に対する根拠 |
|---:|---|---:|---|---|---|---|---|---|
| 1 | `test_s8b_oracle_driver` | 2471.4 | 不正な凍結・receipt・manifest を oracle が受理する、検証不成立を completed にする、WAL と観測 envelope の対応を失う。別に fixture の共有・snapshot を検査。 | A/B/C＋D。研究124 node／2248.850秒、D23／222.519秒 | 研究者が public gate・report を使用。gate 自体の回帰を独立に捕まえる保証なし。D は fixture 利用時 | R/S：不正証拠の受理／fixture 再構築・汚染検知の遅れ | **要分割** | 受理集合を実際に通す T-080 E2E は高価でも必要。共有 fixture の構築回数まで毎走138.3秒払う価値は低い |
| 2 | `test_run_tests_preflight` | 2260.3 | 限定走を受入と扱う、削除・RuleOps 拒否を無視する、submodule 準備やメモリ不足時の停止を誤る | D | 開発者が runner を使用。実 preflight は毎回動くが、その回帰は別系列で検出 | S：誤った受入表示、起動拒否、OOM・再投入の誤判断が残る | **別系列へ** | CI の安全は守るが、最大費用は資源判断の fixture。CC の実行時 verifier は別に維持され、2260秒を毎変更払う比率は悪い |
| 3 | `test_s8b_floor_campaign` | 1852.6 | 測定条件、retry、anomaly による無効化、certificate・journal・result の束縛が壊れる。snapshot helper の検査もある | A/B/C＋D。研究493／1671.230秒、D9／181.403秒 | 研究者の floor 走・批准検証。独立再導出は一部を捕まえるが、配線全体の代替ではない | R/S：不適格な床値・誤った再開／テストの非汚染検知遅れ | **要分割** | 床値と公式／pilot の境界は論文数値に直結。snapshot helper の独立回帰は毎走181秒に見合わない |
| 4 | `test_s8b_ratified_verify` | 887.9 | source・世代・未知性・schedule・certificate・journal・result 間の改変を批准／launch 検証が見逃す | A/B/C | 研究者の `launch_validate`・再検証。対象が検証器自身 | R：改変された床値や実行証拠が正規化される | **毎走必須** | 約888秒の仕事量は大きいが、不正証拠の受理を直接検査する。周期化で誤認証の窓を作れない |
| 5 | `test_check_ai_provenance` | 881.5 | AI trailer、免除、前方訂正、履歴到達性の監査や実行不能の扱いを誤る | D | 開発者の commit 後監査・land。checker 自身の誤判定は別系列 | S：AI 作業履歴の誤記・誤拒否が残る | **別系列へ** | CC 試行台帳 C ではなく開発履歴。実監査を続けつつ、監査器の全回帰881秒を毎走払う必要はない |
| 6 | `test_codex_worker_launch` | 854.1 | 子の終了・retry・計量・出力封印・receipt 検査・失敗診断が壊れる | D | 開発者の次の worker 起動。明白な失敗はそこで露見し、偽受理は別系列 | S：失敗した AI 作業を成功扱い、子の残留、作業費用の誤集計 | **別系列へ** | AI 開発道具の品質であり、CC の certified 判定そのものではない。854秒の毎変更投資は重い |
| 7 | `test_p3_b4_producer_auth_experiment` | 844.1 | disposable prototype の guard 配置、kill 帰属、39組の比較、ABORTED 記録を誤る | E | 比較実験の担当者が再実験・比較報告を検証 | S：認証層比較の勝敗・費用を誤る。現行 CC producer の認証結果には直接入らない | **別系列へ** | 現物は production 認証層ではない。844秒を CC の各変更で反復する価値は低い |
| 8 | `test_p3_b4_raw_record_producer` | 843.6 | WAL・receipt からの割付、terminal、欠測、小数値、on/off 対応の再導出が壊れる。fixture lock の検査もある | A/B/C＋D。研究39／843.135秒、D11／0.470秒 | 材料レポート作成者。assembler／evaluator が通常の不正を捕捉するが、再導出の回帰は別問題 | R/S：偽の402 arm、欠測隠し、数値改変／fixture 競合 | **要分割** | 高コスト本体は残す価値がある。移せる0.47秒は速度改善策として扱わない |
| 9 | `test_t126_pegasus_tools` | 842.8 | qualification の投入、会計、二相 receipt、crash 回復、retry 権限・source 束縛を誤る | D | qualification 担当者の collector／receipt 検証。正式 Layer3 はこの来歴を拒否 | S：資格確認の誤判定、二重投入、診断・再試行の誤り | **別系列へ** | `qualification-only`、`statistical_claim=none`。842秒を正式 CC 成果物と同頻度で守る理由はない |
| 10 | `test_related_work_search` | 562.9 | 登録検索母集合、応答 bytes、件数、再開、simulation と本番の区別を誤る | E | 文献調査担当者の bundle 検証・調査結果利用前 | S：検索漏れ、件数・優先権根拠の誤り | **別系列へ** | 論文の位置付けには価値があるが、CC 数値と証拠の検査ではない。検索系の周期に合わせる |
| 11 | `test_autonomous_trial_completeness` | 555.4 | report と journal の役割履歴・世代・予算・試行集合・Layer3・proposal の対応を失う | A/B/C | 研究者の completeness verifier。欠落を検証する当の実装が対象 | R：失敗試行や構築済み世代を落とした「完全」報告が出る | **毎走必須** | 欠測・分母・証拠対応を直接守る555秒。発行後の訂正では試行の選別を取り消せない |
| 12 | `test_trial_registry` | 493.7 | 6試行の exact 集合、事前登録、slot 消費、追記履歴、terminal と receipt の対応を誤る | A/B/C＋D。研究247／493.603秒、D1／0.060秒 | 研究者の登録・受入。独立 completeness は一部を捕捉 | R/S：再試行の恣意的選択・試行欠落／同名 test の上書き検知遅れ | **要分割** | 台帳本体は中核。関数名重複の自己検査0.06秒は純Dで、削減効果は無視できる |
| 13 | `test_t2187_adaptive_const_probe` | 491.4 | 実 verifier の厳密 argv・trace・identity、24 request 完備、backoff 計測の軸・seed・source 束縛を誤る | A/B/C | backoff 研究者の certification／analysis。実 verifier を通す正負例あり | R：未検証群の認証、異なる条件の数値混合 | **毎走必須** | 「probe」という名前でも CC 実験の認証・材料入力。491秒の反復は誤認証防止に直接使われる |
| 14 | `test_paper_story_a1_paired` | 482.0 | static/adaptive の対応、統計量・符号・分類、raw WAL 再導出、noncertifying 表示を誤る | A/B/C | 論文材料の作成者が collector／materializer を使用 | R：効果の向き・区間・分類が誤って論文へ入る | **毎走必須** | 既存値を再表示するだけでなく、生 WAL から判定を再構成する。約482秒で主張そのものを守る |
| 15 | `test_p3_b4_closed_critic` | 476.1 | on/off pair の身元、投影、session 非再利用、terminal receipt、test-only と certified の区別を壊す | A/B/C | B-4 担当者の pair gate・公開 receipt gate | R：別 pair の混合や test-only 証拠を認証する | **毎走必須** | 対照実験の同一性と処置の証拠を守る。AI 起動道具一般とは成果物への接続が違う |
| 16 | `test_p3_autonomous_workload_trial` | 474.7 | workload・役割入力・critic feedback・admission・slot 消費・partial terminal の生成を誤る。掃除・エラー表示も混在 | A/B/C＋D。研究243／468.717秒、D23／6.007秒 | 研究者の trial 完了時に completeness／Layer3。producer と consumer の共通回帰は保証なし | R/S：漏洩・試行消失・不正受入／一時領域残留・診断表示不良 | **要分割** | 合成ループ本体は残す。6秒の運用部分を高速化の主役にはしない |
| 17 | `test_t1259_qsub_env_delivery_probe` | 446.2 | 環境変数の配送、qstat 実機形式、未承認 driver 拒否を誤観測する | D | 投入診断の担当者が probe の観測結果を検証 | S：配送状態の誤診、誤った運用判断 | **別系列へ** | `diagnostic-only`、`official_campaign_executed=False`。実事故由来でも毎走446秒とは釣り合わない |
| 18 | `test_t338_submission_gate_unit5` | 420.3 | authority 無し・stale binding・不正 receipt の公開、任意出力先、conformance vector の拒否漏れ | A/B | receipt 発行者の writer／semantic validator | R：承認されない receipt が公開される | **毎走必須** | 実際の公開境界に正負例を当てる420秒。後追い検出では公開済み証拠を回収する必要が生じる |
| 19 | `test_spool_fold` | 397.1 | 開発台帳の採番、carry、完了、追記、transaction 回復を誤る | D | 開発者の fold／check_docs／land。共通 parser の誤りは別系列 | S：タスク・裁定記録の脱落や着地停止 | **別系列へ** | ここでいう台帳は CC の試行台帳 C ではない。397秒の毎変更投資は過大 |
| 20 | `test_codex_reasoning_ab` | 388.5 | reasoning/model 比較の snapshot、blind 判定、session 集合、価格・分母・比較可能性を誤る | E | Codex 比較実験の担当者が verify／aggregate | S：AI 比較の勝敗・費用を誤報 | **別系列へ** | `material-report` という語があっても CC 材料ではない。比較実験の周期で十分 |
| 21 | `test_s8b_holdout_freeze` | 359.3 | holdout 漏洩検索、正例、凍結束縛、候補床値の適格性・選択・改変検知を失う | A/B | 研究者の freeze 生成・検証・oracle admission | R：漏洩した holdout や不適格床値を正式入力にする | **毎走必須** | holdout による評価の意味を直接守る。359秒を遅延させる損失は数値全体の信用に及ぶ |
| 22 | `test_s8b_ratified_freeze` | 315.6 | 人間承認、世代・pointer・取消し、歴史、床値・registry proof の束縛を誤る | A/B | 研究者の active 世代解決・launch | R：未承認・改変世代を使用 | **毎走必須** | 批准という成果物の前提を検査する315秒。単なる Git 運用検査ではない |
| 23 | `test_s8c_preregistration_predicates` | 312.4 | 未実装・dead call・decoy・不完全な条件を発効済みにする。現在の gap 理由一覧の pin もある | A/B/C＋D。研究217／312.366秒、D1／0.001秒 | 研究者の activation evaluator。gap 一覧は開発者の wave review | R/S：証拠未充足で発効／開発状態一覧の追随遅れ | **要分割** | 発効条件の負例は残す。現状理由の完全一致pinは開発用で、0.001秒を削減成果にしない |
| 24 | `test_layer3_report` | 308.9 | WAL の投影、certifying receipt、epoch、知識・floor の出所、失敗の表示を誤る | A/B/C | 論文材料の作成者・下流 completeness | R：未認証結果の認証表示、出所や欠測の誤報 | **毎走必須** | 論文へ渡る表現と証拠対応を直接守る309秒 |
| 25 | `test_codex_agents` | 304.3 | CC role の禁止入力、coder 値、verifier 出力等の意味検査と、休眠 adapter の生成・配置・model pin | A/B＋D。研究17／250.374秒、D29／53.877秒 | CC ループの意味検査／開発者の adapter checker | R/S：不正提案・検証出力の受理／休眠 adapter の不整合 | **要分割** | native 起動が休眠でも、本番 `p3_s4_loop` が意味検査を使用。丸ごとDにはできない |
| 26 | `test_critic` | 299.6 | 未COMMIT性能の混入、anomaly・liveness・integrity 理由の消失、未認証性能の露出を起こす | A/B/C | 合成ループの critic 入力、研究者の拒否理由確認 | R：壊れた variant の性能が次の探索を誘導し、正しさシグナルが消える | **毎走必須** | 規律2・3の実際の feedback 経路。約300秒の費用は研究目的そのものに使われる |
| 27 | `test_paper_story_a2_job_contract` | 296.8 | 認証 job の pin・予約・実行場所・事前登録、投入順、request 記録を誤る | A/B/C | A2/A6 研究者の投入・認証 receipt 消費 | R：条件不明の認証走、投入済み試行の欠落・二重化 | **毎走必須** | shell の検査だが、正式認証走の証拠生成を直接担う。単なる投入診断とは違う |
| 28 | `test_check_docs` | 253.5 | 文書欠落、手順・byte pin・参照・開発 backlog・dispatch 表の整合違反を見逃す | D | 開発者の実 `check_docs`、誤った checker は別系列 | S：手順の逸脱、記録欠落、誤拒否が残る | **別系列へ** | 実 checker の実行は維持し、その577 node の回帰を毎走する費用を分離できる |
| 29 | `test_run_tests_shards` | 237.6 | shard activation、割付・集合・完了の6 gate、計装・資源判断を誤る | D | 開発者の受入 runner。実6 gate は各受入で維持 | S：受入の偽緑・実行不能・計装誤りが残る | **別系列へ** | 計測走では2つの資源判断 node が234.6秒を占める。runner 回帰全体の毎走費用は価値に比べ重い |
| 30 | `test_real_repo_serialization` | 235.3 | test fixture の lock・memo・tmpdir と、T-080 11 node の既定選択・setup 到達を守る | A/B実行保証＋D。保持1／3.895秒、D56／231.396秒 | T-080 脱落は保持 probe が毎走捕捉。fixture 不整合は開発者・別系列 | R/S：核心検査の沈黙／fixture 競合・cache 不整合・速度退行 | **要分割** | DB の serializability 検査ではない。F485 の直接再発検査3.895秒は費用対効果が高い |
| 31 | `test_t139_submission_path` | 225.2 | manifest・projection の偽造、同名差替え、sealed authority の改変を許す | A/B | receipt 発行者の resolver・`binding.assert_intact` | R：未承認の事前登録に receipt を束縛する | **毎走必須** | 承認から公開までの信頼連鎖を直接守る225秒 |
| 32 | `test_p3_b4_material_report` | 224.4 | 201 block／402 source、floor authority、数値・判定・非保証、二ファイル公開の整合を壊す | A/B/C | 論文材料の作成者が builder・renderer を使用 | R：欠測・floor 不在の隠蔽、誤った材料レポート公開 | **毎走必須** | 指定成果物 B そのもの。224秒を節約して公開後検出へ送る合理性はない |
| 33 | `test_ccbench_spawn_sites` | 219.7 | 新しい build／spawn 経路が条件 gate を迂回する、別 macro の検査を流用する、保護比率へ無検査で到達する | A/B | 開発者の構造検査。新しい迂回路には既存実行時 gate がない場合がある | R：未検査変異・測定条件で実行できる | **毎走必須** | 静的検査だが、正しさ検査を通らない経路の新設を直接検出する219秒 |
| 34 | `test_login_headroom` | 218.8 | charged memory、祖先上限、予約・PID再利用・scope 回収を誤る | D | 開発者の local admission／実際の資源不足、別系列 | S：過剰投入・OOM・不要 dispatch | **別系列へ** | 2本の定数所在走査だけで約218.6秒。運用価値はあるが毎走投資には見合わない |
| 35 | `test_dynamic_backoff_transitions` | 216.9 | CC backoff の更新境界、clamp、policy 反転、LCG、trace の完全除去を誤る | A/B | backoff 研究者の compile／実遷移検査。serial verifier だけでは処置違いを捕まえない | R：実験したつもりの処置が違う、trace による性能汚染 | **毎走必須** | 処置の意味と観測者効果を直接守る217秒。serializable でも誤った実験になるため必要 |

## 要分割の file の分割点

以下の範囲は**test 関数定義の開始行**で指定しています。範囲内の helper・fixture を削除する指示ではありません。対象関数の全 parameter node を含み、補集合を保持します。

| file:line | 残す node | 移す node |
|---|---|---|
| [test_s8b_oracle_driver.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:577) | 下記以外の124 node／2248.850秒。T-080 public gate・履歴・改変拒否の11 node は全保持 | 定義開始行577〜1283の23 node／222.519秒。snapshot、ignore-rule、`test_t080_shared_base_*`、consumer/nodeid 一覧 |
| [test_s8b_floor_campaign.py:1796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_floor_campaign.py:1796) | 下記以外の493／1671.230秒。公式証明書・resume・anomaly・実測条件の検査を保持 | 定義開始行1796〜2199の9／181.403秒。snapshot の reference、cache、parser、再観測、digest failure |
| [test_p3_b4_raw_record_producer.py:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_p3_b4_raw_record_producer.py:906) | production producer を検査する39／843.135秒 | 行906の mutation 対応表と、定義開始行1422〜1847の fixture lock・metadata 検査。11／0.470秒 |
| [test_trial_registry.py:2249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_trial_registry.py:2249) | それ以外の247／493.603秒 | `test_t822_trial_registry_test_top_level_function_names_are_unique`、1／0.060秒 |
| [test_p3_autonomous_workload_trial.py:3032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_p3_autonomous_workload_trial.py:3032) | 下記以外の243／468.717秒。漏洩防止・critic・admission・trial lifecycle を保持 | 定義開始行3032〜3082の表示用redaction、6072〜6127のprovider解放、6313のhelp、6711〜6870の一時領域掃除。23／6.007秒 |
| [test_s8c_preregistration_predicates.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8c_preregistration_predicates.py:282) | それ以外の217／312.366秒。発効状態・negative control・本番到達性を保持 | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`、1／0.001秒 |
| [test_codex_agents.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_codex_agents.py:552) | 定義開始行552〜1299の17／250.374秒。禁止入力、coder値、verifier意味検査、消費されるschemaの弱体化検知 | その外側の29／53.877秒。休眠adapterの配置・生成・model対応・checker整合 |
| [test_real_repo_serialization.py:1190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_real_repo_serialization.py:1190) | `test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default`、1／3.895秒 | それ以外の56／231.396秒。fixture lock・memo・tmpdir の回帰 |

最後の保持 node は、対象11 node の集合一致だけでなく、`skip/skipif/xfail` 不在と全 node の setup 到達を検査します。**F485 に対応する実測防壁を3.895秒で維持する投資**として残します。

0.470秒、0.060秒、0.001秒の分離は意味上の分類です。これらを独立した高速化作業として実装することは勧めません。

## 機構

**D711／D1728：等式だけなら再定義した集合でも成立するが、現行契約にはその再定義が含まれない。**

[D711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/decisions.md:27929) の逐語は、

> 「各 shard が同一の全 collection を行ってから担当外を deselect する。」

さらに、

> 「login 側が独立に走らせた `--collect-only` の集合が `U` と一致」  
> 「`Σ selected_i == U`、各 count = 1」  
> 「全 shard で `finished_i == selected_i`」

です。実装も [acceptance_shards.py:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/acceptance_shards.py:675) からこの順で検査します。

したがって、

- **U を維持して実行だけ省く**と、selected の完全分割か finished 一致を破る。
- **全員が縮小した U を観測するように変える**と、等式は成立し得る。しかし、その緑は除外した検査の実行を証明しない。
- **後日の別走を足す**ことは、今回の全 shard の完了を要求する現行契約の代替にならない。

D1728 の逐語も、

> 「gate 2（全 shard の `observed_universe` 一致）は現行のまま置き、代替述語も新設しない。」

です。**「U の定義を変えれば等式は保てる」は、実装許可の根拠になりません。**

**D532：本案は却下された形に当たる。**

[D532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/docs/decisions.md:21928) は、

> 「テストの削除・skip・selection の縮小で速くする — 規律 2 に反する。検討対象にしない。」

と明記しています。

本案はテストを保存していても、**各受入で実行する selection を縮小して速くする案**です。「別系列で必ず走る」という条件による例外は本文にありません。**本依頼の明示指示を例外許可と読み替えて、親が実装することはできません。**

価値評価の結果を反映するには、D532 の頻度変更に関する適用範囲と、D711 の受入母集合を、別途明示的に改訂する必要があります。D700 が個別に禁止した T-080 の別 gate 化は、本推奨では行いません。

**既存手段は部分的にある。完成した別系列はない。**

| 手段 | 現物で確認した状態 |
|---|---|
| file／nodeid／`-k`／`-m` 指定 | [run_tests.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/run_tests.py:550) が pytest へ渡す。選択走は可能 |
| 選択走を通常受入として扱う | 不可。[run_tests.py:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/run_tests.py:693) は targeting や `-k/-m` 等を受入形から外す |
| runner 所有の除外契約 | [test_selection_contract.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/test_selection_contract.py:58) の `SANCTIONED_EXCLUSIONS` は空。既存の閉じた特例を任意リストとして流用できない |
| marker | `xdist_group` 等の配置・排他用はある。日次／研究別系列の実行保証 marker は確認できない |
| 別 runner | 実験・probe 用 CLI はあるが、今回の検査群を周期実行して期限管理する runner はない |
| 定期実行 | repo 内の CI workflow／cron／timer と、その完走・未実行監視は見つからない。repo 外の運用は未確認 |

**腐らせないために必要な最小機構。以下は新設案で、現存の保証ではありません。**

1. 外部の scheduler が日次で対象系列を起動し、既存 `tools/run_tests.py` を通す。E はその研究結果を利用する前にも走らせる。
2. 起動対象の commit、系列定義、期待 node 集合、実際の selected／finished、成否、完了時刻を記録する。**起動成功や job ID を完走と扱わない。**
3. 「最後の成功から24時間」を検査する経路を scheduler 本体とは別に置く。未起動・queue停止・途中死も期限超過として検知する。
4. 赤または期限切れなら、該当道具の新しい版や E の結果を検証済みとして利用できないようにする。停止や失敗で成功時刻を更新しない。
5. 関連道具を変更した場合は、その変更の焦点走にも対象系列を含める。ただし参照関係だけの抽出には依存しない。repo 全体 checker を漏らした F521 があるためです。

**保証できるのは、正常時の24時間以内の検出と、異常時に未検証状態を放置して利用しないことです。** 計算資源が永久に使えない場合まで、バグの検出時間を有限とは言えません。

F485 の問題は「任意実行という名称」ではなく、11日間の未実行が何も止めず、誰にも露見しなかったことです。日次という散文だけでは再発防止になりません。

## 数値の見込み

**新しい pytest・性能測定は行っていません。**

親の費用集計 script が参照する既存3 shard の [JUnit 置場](/work/1/SFC/tanab/.izanagi-acceptance-shards/75eff2a295fea1b219611b8beff239c9) を読み、分割部分を node ごとに再集計しました。

| 量 | 既存費用による集計 |
|---|---:|
| file 丸ごとの別系列相当 | 8,187.396秒 |
| 要分割 file 内の別系列相当 | 695.733秒 |
| 合計 | **8,883.129秒** |
| 元の受入全体に対する割合 | **34.50%** |
| 残る受入の直列和 | **約16,862.4秒** |

これは fixture 費用を含む**観測された仕事量の分類**です。分割後に fixture が別 worker で再構築されれば、単純な差し引きどおりには減りません。

wall の見積もりには次の条件を置きます。

- K=3、各48 worker を維持する。
- 残った単体の所要が、親の最新実測の208.1秒程度で変わらない。
- 再配分後に、それを超える排他 group や fixture 再構築の鎖を作らない。
- 長い仕事を早く開始できる。
- collection・dispatch・teardown 等の残余を、新しい実行系列で確認する。

この条件下では、単純な容量指標は約117.1秒ですが、**208.1秒の最長単体を下回れません**。したがって、

`見込みwall ≈ 208.1秒 + 残余`

という、単体が支配する場合の模型になります。

| 仮定する残余 | 条件付きwall |
|---:|---:|
| 60秒 | 268.1秒 |
| 80秒 | 288.1秒 |
| 90秒 | 298.1秒 |
| 100秒 | 308.1秒 |

**約268〜298秒は残余60〜90秒という条件付き見込みであり、測定結果ではありません。** 今回の資料だけでは残余がその範囲に収まることも、現在の306.9秒から必ず短縮することも保証できません。

また、費用表の走には208.1秒より長い raw producer 等の node があり、親の最新wall・最長単体とは同一走の数値として扱えません。古い node 所要と新しいwallを結合した、正確なスケジューリング予測はしていません。

## お前の推奨

**価値上は、まず丸ごと別系列とした12 file を移す案を採るべきです。** 約8,187秒という主要部分を扱えます。0.001〜0.47秒の分割から始めるべきではありません。

ただし、親が**今の裁定のまま実装できるのは selection を変えない変更まで**です。本相談を理由に除外表や marker を追加してはいけません。今回の価値判断を採用するなら、D532 と受入母集合の定義変更、別系列の完走・期限超過機構を、一つの具体的な変更案として先に成立させる必要があります。

その後の分割優先順位は、oracle の222.5秒、floor の181.4秒、fixture 管理の231.4秒です。**本物の oracle／anomaly／verifier 検査と、F485 の実行到達 probe は保持します。**

成立後は canonical 受入の最遅 shard wall で確認します。34.5%の仕事量移動を、そのまま34.5%のwall短縮として報告してはいけません。

## 読めなかった file / 確かめられなかったこと

- 必読2 file と指定35 file は読めました。現物の関数・主要 assertion・関連 consumer を確認しました。
- 調査で仮定した `orchestrator/campaign/artifact_admission/`、`orchestrator/qualification/README*`、`orchestrator/conftest.py`、`.github/`、`.gitlab-ci.yml` は存在しませんでした。実体は関連 `.py` と `orchestrator/tests/conftest.py` で確認しています。
- 読んだ HEAD は `c1808fe78`。費用資料の文献検索122 node のうち、完全重複の1 node・0.001秒は既に `c170bee92` で削除済みです。差分の本文を確認しました。**新たな削減としては数えません。**
- 全 node の独立代替検査や依存関係を完全に証明した監査ではありません。「別の検査が必ず即座に捕まえる」とは認定していません。
- repo 外の scheduler／timer の稼働、期限監視、通知・利用停止経路は確認できません。
- pytest、再計測、編集は行っていません。緑の認定も、300秒達成の認定もありません。