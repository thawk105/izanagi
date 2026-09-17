## 利用時拒否の実効性と迂回路

**自己判定：real。現時点で D2002 条件3の実効性は未成立。判定器だけを追加しても、配置によっては部分的に留まる。**

以下、`J` は `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2710-t080-series-inquiry`、`plan` は `J/artifacts/dev-wave-t2710-t080-series-inquiry/s2-plan.md`。repo 内のパスは指定 root からの相対とする。

負例11/11拒否・正例1/1受理は保存結果と一致する。しかし証明しているのは、手製記録を `judge()` に渡した場合の判定だけである。production の通過強制、実完走との結合、最新失敗による旧成功の失効は証明していない。判定器は単一記録を読み、terminal も node 別でなく集計件数で検査する。  
根拠：`J/probe_series_gate.out.txt:1`、`J/series-gate-probe/summary.json:18`、`J/probe_series_gate.py:64,92,113`、`plan:168,172`。

| 迂回路 | 事故への接続と自己判定 | 根拠 |
|---|---|---|
| migration CLI 直叩き | **real**。wrapper・land・driver のみに置いた判定器を通らず、`active-valid` と rc=0 を返せる経路。`verify_receipt` 内の判定なら捕捉可能 | `orchestrator/campaign/t080_freeze_migration.py:2539` |
| driver の Python API | **real**。CLI のみに置く案を迂回する。さらに `run_block` は公開 `gate_check` を経由せず、専用 gate を使う | `orchestrator/campaign/s8b_oracle_driver.py:599,679,1318,1394` |
| 古い／注入済み resolution を adapter に渡す | **real**。adapter は渡された状態を受け取り、系列完走の鮮度を再取得しない。verifier のみの防壁では API 全体を覆わない | `orchestrator/campaign/t080_freeze_migration.py:2424,2432,2454` |
| floor の `receipt_verify_fn` 差し替え | **real：API 上の迂回可能性**。返却 object の形が合えば protocol 書込みへ進む。実 repo での誤用は事故に接続する。ただし通常 CLI は注入しないため、**通常 CLI の抜け穴という主張は refuted** | `orchestrator/campaign/s8b_floor_campaign.py:1419,1426,1440,1447,1467` |
| report の履歴検査 | **real：verifier guard の迂回**。historical/current の両方が `inspect_receipt_history` を直接使う。ただし履歴閲覧自体は事故ではない。現行の検証済み利用へ昇格する境界を分ける必要がある | `orchestrator/campaign/s8b_oracle_report.py:243,246,2364,2388` |
| mock 経由 | **判定保留：本番事故の実在**。隔離 fixture の mock 成功は本番利用の証拠ではない。一方、注入可能 API を本番 root で使用できる以上、任意の Python 差し替えまで防げる保証もない | `orchestrator/campaign/s8b_floor_campaign.py:1423,1426` |
| 旧受入受領証の再利用 | **real**。publish 時だけの判定では、その後の期限切れ・関連変更を land が捕捉できない | `tools/dev_wave_wait.py:3634`、`tools/dev_wave_land.py:1203` |

**配置は「共通判定ロジック1個、呼出し境界は複数」が必要。** 最低限、次を覆う設計が要る。

- migration の検証結果・adapter を検証済みとして返す境界。
- driver の `gate_check` と `run_block`。開始直前の再確認も含む。
- holdout CLI の legacy 分岐を含む利用境界。
- floor の verifier 注入とは独立した、実凍結前の境界。
- report を現行の検証済み結果として利用する境界。
- acceptance 受領証生成と、land の利用時再判定。

根拠：`orchestrator/campaign/s8b_oracle_driver.py:1527`、`orchestrator/campaign/s8b_holdout_freeze.py:1210,1215,1247`、上表の各入口。

`inspect_receipt_history` 全体を止める案では診断まで停止する。反対に診断用 bypass を汎用引数・環境変数として開けば、利用拒否を迂回できる。**診断結果から検証済み利用への昇格境界は未設計**であり、8呼出し箇所を列挙しただけでは解決しない。根拠：`plan:206,208,371`、`J/rulings-verbatim.md:92`。

## 束縛先と費用

**自己判定：real。plan は再走頻度と日次費用を数値化しておらず、起動主体も未決定。**

plan の具体案は `target_commit` 完全一致であり、closure A/B の定義ではない。関連変更対象は例示に留まり、投入経路も未設計と明記されている。  
根拠：`plan:166,361,372,374,375`。

保存された7日間の遷移数から、毎失効につき1走、1走250秒＋前処理0〜65.5秒と仮定すると次になる。

| 束縛 | 7日間の失効 | 平均回数/日 | 単一計算ノードの占有時間/日 |
|---|---:|---:|---:|
| HEAD | 126 | 18.0 | 75.0〜94.7分 |
| closure A | 59 | 8.43 | 35.1〜44.3分 |
| closure B | 96 | 13.71 | 57.1〜72.1分 |

根拠：`J/probe_binding_churn.7d.txt:1`、束縛定義は `J/probe_binding_churn.py:8`。これは CPU 時間ではなく仮定したノード占有時間。queue 待ち、失敗再走、関連変更のない日の期限維持走は含まない。直近24時間は A=6、B=11 であり、7日平均を将来の定数にしてはいけない（`J/probe_binding_churn.24h.txt:2`）。

**自己判定：real。closure A/B とも完全な閉包ではない。**

- A は `output/` を含まない。しかし fixture は git 可視 output を複製する。
- A/B とも `docs/phase3-8b-descriptor-design.md` を含まない。しかし builder の明示入力である。
- tree OID は未コミット・非 ignored untracked の内容や、実 submodule checkout の状態を表さない。production scanner はそれらに接する。

根拠：`orchestrator/tests/test_s8b_oracle_driver.py:1385,1401`、`orchestrator/campaign/s8b_holdout_freeze.py:370`。したがって「docs-only なら関連しない」という一般化も不可。今回の HEAD 差分が9件すべて docs だったことと、全 docs 変更を安全に無視できることは別である。

**自己判定：判定保留。同期・非同期のどちらも費用と有効化順序が未解決。**

- **同期**：系列を受入と並列実行するなら、全体は概ね `max(毎走系列251〜255秒, 別系列約316秒)`。逐次なら約567〜571秒になる。「同期なら短縮が完全に消える」は強すぎるが、並列でも300秒未満という利得は消える想定である。
- **非同期**：land 後に起動するなら、完走まで新版を有効化しない仕組みが必要。land 自体を有効化と扱う設計では順序が矛盾する。
- **窓の解釈**：関連変更を利用時に必ず検出して拒否できれば、非同期の窓は「未検証利用の許容期間」ではなく「利用不能期間」である。危険な窓になるのは、入口漏れ・閉包漏れ・有効化順序の誤りがある場合。

根拠：`J/rulings-verbatim.md:92,105`、`plan:194,372,374`。起動担当、対象版固定、完走回収、失敗状態の保持が決まらない限り、日次費用だけでは採否を判断できない。

## shard wall の見積もりの妥当性

**自己判定：refuted。lock union 231.9秒を、移動後にも残る直列化下限として使う根拠はない。**

現行実装は read を `LOCK_SH`、write を `LOCK_EX` とし、resource ごとに取得する。保存 interval は最大22本が重なり、総和1916.8秒に対して union は231.9秒。これは「誰かが保持していた時間」であり、必須の直列仕事量ではない。  
根拠：`orchestrator/tests/conftest.py:1261,1476,1548`、`J/probe_lock_modes.895f300a.txt:2,7,12`。

ただし writer 4 node・台帳約0.2秒から「write による待ちも0.2秒」とは言えない。mode 集計は登録 node の台帳であり、interval 自体には mode/node 対応が保存されていない。単独保持28.4秒も exclusive lock 時間ではない。

したがって plan の292〜327秒は、**Rを据え置く仮想感度として計算可能だが、実測に裏付いた下限や有力予測ではない**。親のこの批判は支持できる。根拠：`plan:299,319,325`。

**自己判定：判定保留。親の251〜255秒も、正しい予測と確定できない。**

1. `65.512 + 184.8〜188.7 = 250.3〜254.2秒`という算術は成立する。しかし M 除去後には shard 間・worker 間の割付が変わる。旧workerの順位をそのまま残存 chain にできない。根拠：`J/probe_worker_occupancy.895f300a.txt:2,7`、`tools/acceptance_shards.py:434`。
2. 現行は所要時間順への並べ替えもあるので、「無条件に空き順だけ」とする説明も不正確。ただしこれは変更後の worker chain の再現ではない。根拠：`orchestrator/tests/conftest.py:1776,2267`。
3. 当日の337.9→344〜351秒は基準から約+1.8〜3.9%。plan は走間変動を定性的に書くが、この幅を予測数値へ織り込んでいない。±4%を機械的に付けても、238〜255秒は約228〜265秒という**感度表示**に過ぎず、信頼区間にはならない。根拠：`J/s1-brief.md:9`、`plan:367`。
4. **shard-1 の逆転を plan が無視したという疑義は refuted**。比例モデルは shard-1=247.2秒を最遅としている。shard-0の238秒だけを全体予測として引用する方が誤り。根拠：`plan:289`。
5. M′で173.8秒 nodeを除いても184.8秒 nodeが残るため、**最長単体nodeによる床は下がらない**。ただし共有I/O・開始順への影響は未測定なので、wallの追加効果が「ほぼゼロ」とまでは確定しない。根拠：`J/probe_worker_occupancy.895f300a.txt:7`。

結論は、**両βとも移動後wallを実証していない**。238〜255秒は単走から作ったモデル値であり、「300秒を切る」とは書けない。D357の仕事量とnode秒の区別、D2068の対比較要求を満たす実測はまだない。根拠：`plan:366`、`J/rulings-verbatim.md:172,179`。

## T-2750 との関係

**自己判定：real。親の「M込み5165×3」は probe の台帳参照破壊による値で、撤回が必要。**

probe は仮想 file へ移す際、`nodeid` 自体を `__ungrouped.py` に変更する。そのため台帳 lookup に失敗し、対象nodeを一律1秒として計算する。さらに全対象を同じ仮想fileへまとめており、node単位分割にもなっていない。  
根拠：`J/probe_shard_wall.py:126`、`tools/acceptance_shards.py:397,404`。

nodeidを保ち、file成分だけをメモリ上で変更して `allocate()` を再計算した。ファイル変更はしていない。現行割付が保存済み3 report の selected と一致することも確認した。

| 仮想変更 | shard負荷 | Mの配置 | wallについて言えること |
|---|---|---|---|
| 別系列化のみ | 約5285.4×3 | 毎走から除外 | 非Mの184.8秒級nodeが残る |
| oracle非groupをnode単位へ分割、M維持 | 約6052.7×3 | 0 / 6 / 5 node | 240秒台帳nodeが残る |
| 上記分割＋別系列化 | 約5285.4×3 | 毎走から除外 | 負荷総和は別系列化のみと同じ |
| 非group全体をnode単位へ分割、M維持 | 約6052.7×3 | 0 / 6 / 5 node | 同じく240秒台帳nodeが残る |

これは T-2750 完成実装の予測ではなく、明示した成分分割だけの仮想計算である。根拠となる allocator は `tools/acceptance_shards.py:325,381`。

**自己判定：refuted。「成分粒度変更だけで別系列化と同程度のwallになる」は未証明。**

前処理を65.5秒、最長nodeを台帳240秒で据え置けば約305.5秒。今回実測の最長M node 252.455秒を据え置けば約318秒になる。これは変更後の下限保証ではないが、均等負荷だけでは消えない長時間nodeの存在を示す。根拠：`J/probe_worker_occupancy.895f300a.txt:5,30`。

別系列化の独自利得は、この長時間nodeを**毎走の実行経路から外すこと**。成分分割は負荷配置を変えるが、そのnode自体は残す。ただし別系列完走を同期必須にすれば、その待ちが全体へ戻る。両案併用の追加wall利得は現状の数値から確定できない。

## 段階導入と既存策

**自己判定：real。別系列化は選択集合の変更だけでは成立しない。**

| 必要物 | 既存策で足りるか | 根拠 |
|---|---|---|
| 完走記録schema・真正な発行 | **不足**。producer/compute受領証は完了・accountingの証跡であり、Mのexact集合・node別terminal・系列版を証明しない | `tools/dev_wave_wait.py:1908,2080` |
| 独立期限検知 | **不足**。利用時の純粋判定だけでは、利用のない期間の未起動を検知できない | `plan:373`、`J/rulings-verbatim.md:90` |
| 利用拒否と診断の分離 | **不足**。前節の複数境界と初回完走循環が未解決 | `plan:208,371` |
| 計算ノード起動・完走回収 | **部分再利用可能、運用未設計**。既存dispatchがあっても、定期・変更時起動の責任は別途必要 | `plan:374` |
| gate 4・allocator・受領証scope | **変更必要**。現行gate 4はC全体のexact partitionを要求する | `tools/acceptance_shards.py:684`、`plan:350` |
| D701との整合 | **既存probeだけでは不足**。collection/setup到達は本体完走を証明しない | `J/rulings-verbatim.md:49`、`plan:359` |
| docs・復旧手順・閉包定義 | **追加必要**。起動担当、失敗後処理、有効化対象、関連path集合が未確定 | `plan:361,372` |

**自己判定：判定保留。「既存策で300秒に届くので別系列化は不要」とも、逆に「必要」ともまだ言えない。**

T-2750の根拠数値は前節の訂正が必要。台帳精度向上は割付を改善しても長時間nodeを短くしない。worker増減についても、既裁定では24/32/48本の差が走間変動に埋もれている。根拠：`tools/acceptance_shards.py:401`、`J/rulings-verbatim.md:77`。

規律5に沿う現段階の結論は、別系列化の新機構を正当化する前に、正しい台帳重みで既存策との比較を成立させること。TTL延長や閉包縮小を費用対策にする余地はない。

## 親 brief の実測値と一般化

**自己判定：real。主な数値は再現するが、その意味づけに過剰な一般化がある。**

保存済み `895f300a…/shard-0/{report.json,junit.xml}` を読み直して検算した。

| 値 | 検算結果 | 注意点 |
|---|---:|---|
| JUnit wall | 337.860秒 | 1走の値 |
| test span | 272.347860秒 | 272.3秒と一致 |
| wall−span | 65.512140秒 | 「約65.5秒」が正確。純粋な前処理時間ではなくspan外全体 |
| collection→first test | 0.019849秒 | 当該走ではdispatch待ち約29.6秒ではない |
| M 11 nodeのJUnit時間合計 | 2539.249秒 | 2539.2秒と一致。CPU時間ではない |
| Mの最大JUnit時間 | 252.455秒 | 台帳240秒と区別が必要 |
| 12番目worker占有 | 187.397412秒 | 187.4秒と一致 |
| 11番目worker占有 | 188.692311秒 | 12番目だけを残存最大として採る根拠はない |

対応する根拠：`plan:313,317`、`J/probe_worker_occupancy.895f300a.txt:2`。集計方式は `J/probe_worker_occupancy.py:19,36`、`J/probe_shard_wall.py:99`。

**自己判定：判定保留。「上位10workerが重いMを1本ずつ抱える」の直接証明は、提示probeにない。**

probe はworker占有順位とJUnit node時間を別々に出し、node→workerを結合していない。保存reportも占有の集計値を出す構造である。したがって「Mを除けばこの10workerだけが消え、次の順位がそのまま床になる」は証拠を一段飛ばしている。  
根拠：`J/probe_worker_occupancy.py:20,36`、`tools/acceptance_shards.py:1127,1174`。

1走内の48workerの分布は、走間変動の分布ではない。planの占有比31.462を将来の実効worker数へ固定すること、親の185〜189秒chainを変更後へ移すことが一般化箇所である。前waveには代表nodeが198.8〜482.7秒に振れた記録もあり、今回の±4%を普遍的な誤差幅にはできない。  
根拠：`plan:305,313`、`output/insights/2026-09-16/t2559-acceptance-floor-t080/README.md:44,102`。

## 総括

- **real：** T-2750比較probeはnodeid変更で台帳重みを失っている。5165×3を撤回し、M維持なら約6052.7×3へ訂正する必要がある。
- **real：** 負例11/11は判定器単体の結果。productionの利用時拒否、完全な閉包、起動責任、旧成功の失効は未成立。
- **refuted：** lock unionを移動後の直列化下限として扱う推論。
- **判定保留：** 親の251〜255秒、M′の追加効果、T-2750のみでの300秒達成。いずれも変更後の実測ではない。
- **real：** closure Aの再走費用は仮定上35〜44分/日、Bは57〜72分/日。同期・非同期の有効化契約と併記しなければ採否材料として不足する。

**現資料から別系列化の採用は支持できない。比較probeと費用・利用境界の訂正を先に行い、Mは毎走に残すのが妥当。** 本検査は静的読取りと既存データのメモリ上再計算のみで、ファイル変更・pytest・新規性能測定は行っていない。