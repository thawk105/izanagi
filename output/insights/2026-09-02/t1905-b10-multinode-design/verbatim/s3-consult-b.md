## 所要見積りの破れ

- [real] 「性能測定本体は 1 workload 4.5 分」は formal perf 相の値ではない。`brief.md:45` と `plan.md:78` は `3 秒 × 6 記録 × 15 変種` を使うが、実装は 3 block × 15 点 × 5 rep × 3 秒であり、実行本体だけでも 675 秒、11 分 15 秒である。`b10_backoff_shape_sweep.py:101-104, 2230-2248, 2978-2997`。settle、起動、集計は別に加わる。
  影響: write-heavy 230 分から 4.5 分を引いた 225.5 分、全 node-hour 表、verify/perf 分離案の値は根拠を失う。

- [real] read-heavy の `305 × 15 / 3 = 1,525 分` は、先頭 3 変種の費用を残り 12 変種へ線形外挿すると同時に、固定 prologue と初期 build まで 5 倍している。`plan.md:78`。305 分は job 全体の経過時間である。`verbatim-worklog-1186.md:14-17`。
  影響: 25 時間 25 分は検証時間の推定値ではなく、固定費を重複させた粗い上側値であり、壁時計や node-hour の予算値に使えない。

- [real] `H` を別扱いすると宣言しながら、既に prologue を含む実測を使った値へ `3H`、`9H`、`45H` を再加算している。`plan.md:80-90`。runbook の比較基準は `H ≈ 900 秒`。`docs/pegasus-runbook.md:1268-1282`。
  影響: 表の node-hour は固定費を二重計上する。runbook の近似だけを機械的に当てると、3 job は 45 分、9 job は 2 時間 15 分、45 job は 11 時間 15 分の prologue node-time になる。B-10 自身の正確な H は未測定である。

- [suspect] `S_w + C_w/P_w` は見積りではなく未測定量を置いた恒等式である。CPU/経過 = 1.0 は job 全体の平均利用率を示すだけで、trace 生成、trace 書き出し、Python 検査のどれが何分かを分離していない。`plan.md:88-92`、`verbatim-insight-t1905.md:140-151`。
  影響: offline verifier だけを多重化しても 12 時間内へ入るか、ユーザーが拒否した 5 時間を下回るかを判定できない。

- [suspect] batch 化は trace 生成を直列に残し、`K × 5` 個の trace を保持してから複数 reader を同一 `/scr` に当てる。現状は 1 反復ごとに作成、検査、削除する。`pipeline.py:1365-1519`、`plan.md:26-29`。
  影響: trace I/O が律速なら `C/P` の短縮は出ず、保持容量と I/O wait だけが増える。

- [real] 175 秒は plan では確定上限に使っていない点は正しい。`plan.md:92`。一方、read-heavy の完了済み 3 変種は 5 rep × 3 変種を 305 分で処理しており、固定費込み平均は約 1,220 秒/rep である。したがって write-heavy 由来の未確認 175 秒を read-heavy の所要上限へ一般化できない。
  影響: 175 秒から worker 数や walltime を逆算する案は read-heavy の投入予算を過小評価する。

## 資源と運用の破れ

- [real] 推奨する process worker pool は現行の認証境界で成立しない。`VerificationCapability` は発行 PID を記録し、commit receipt 作成時に現在 PID との一致を要求する。`orchestrator/verifier/core.py:162-258`。receipt は同一プロセスの capability 列を要求する。`orchestrator/verifier/commit_receipt.py:296-332`。coordinator が commit する現行経路は `pipeline.py:1636-1666, 1714-1772`。
  影響: process worker の結果を coordinator へ戻しても `COMMIT` できず、correctness-certified な成果物にならない。thread pool は PID 境界を保てるが、単一スレッド Python 検査の CPU 多重化にはならない。

- [real] verifier pool、batch size、group ID、job-local root、fan-in の CLI は存在しない。B-10 driver は `phase/workload/prereg/submission-receipt` だけを受ける。`b10_backoff_shape_sweep.py:3096-3115`。B-10 submitter も 1 invocation で 1 workload/phase を 1 回 qsub する。`submit_b10_backoff_shape.sh:7-75, 207-296`。
  影響: plan の推奨形は設定値を変えて投入できず、現状の CLI で実行すると従来の直列 verifier のままである。

- [real] 汎用 `dispatch_compute.py` にも N-job 投入または group wait の CLI はない。parser は単一 task と単一 argv を `dispatch()` へ渡し、1 submission directory、1 qsub を作る。`dispatch_compute.py:3465-3517, 3750-3785, 4459-4496`。runbook も明記する。`pegasus-runbook.md:1364-1386`。
  影響: expected set、request と rc の対応、単一待ち手、partial success を閉じるには、新規の group orchestration または明示的な手動運用が必要である。現行機構による機械強制とは報告できない。

- [suspect] 表の「必要 node」「最大壁時計」は全 request が近い時刻に開始する前提を暗黙に置く。fair-share と後続 request の優先度は未確認である。`pegasus-runbook.md:1265-1273, 1401-1402`。
  影響: 3、9、45 本を同時提出しても同時開始は保証されず、end-to-end 所要は表から出せない。

- [real] 欠陥 3 は「4 か所」ではなく少なくとも 5 literal site にある。`b10_backoff_shape_campaign.sh:5, 168-170, 260-261`、`submit_b10_backoff_shape.sh:199-200`、`b10_backoff_shape_sweep.py:488-495`。
  影響: walltime の変更漏れは各 request を起動時または driver 入場時に拒否する。plan 自身の read-heavy 25 時間台推定は現行 12 時間を超えるため、未確認の 2 倍超 speedup を前提にしない限り投入不能である。

- [real] 欠陥 4 では SIGTERM 時に `failure.json` だけでなく、後段の `job-result.json` も作られない。`b10_backoff_shape_campaign.sh:107-115, 351-381`。scheduler の exit `9` は walltime と実行中 qdel を区別しない。`pegasus-runbook.md:178-184`。
  影響:打ち切られた各 request について、timeout、操作者取消、実行段階の対応が durable 記録から失われ、group fan-in は「成果物欠落」以上に分類できない。

- [real] qdel は RUN job には使えず、receipt と照合済みの QUE/HLD だけが対象である。`pegasus-runbook.md:1393-1400`。
  影響: 1 本が早期失敗しても、既に RUN の兄弟 request を fail-fast で止める運用は採れず、全 terminal を待つ必要がある。

## 中断からの回復

- [real] claim は WAL recovery より前に取得される。`loop.py:208-229`。claim は stale 判定、自動削除、release を持たない。`campaign_claim.py:383-436`。したがって crash 後の同一 identity 再投入は、まず残存 claim で停止する。
  影響: 新しい submission nonce だけでは当該 job を再取得できない。

- [real] 操作者が claim を保全して除去しても、build_done、verify_done、bench_done のいずれかを持つ active attempt は D193 により 1 byte も追記せず拒否される。`wal.py:1940-1973`。`ensure_resumable_wal` はこの検査を必ず通す。`ident.py:472-508`。
  影響: verify 中に壁時計で切れた request は同一 WAL を再開できず、fresh campaign identity でその分散単位全体を取り直す。

- [real] perf 中断だけは、WAL の verify attempt がすべて terminal なら、既存 block record を読み、完了 cell を skip できる構造がある。`b10_backoff_shape_sweep.py:2941-2945, 2978-2981`。ただし残存 claim の手動処理は依然必要である。
  影響: create-only block record は perf cell の再利用には効くが、read-heavy で実際に問題となる verify 中断の救済にはならない。

- [real] 推奨 3-job 案では、失敗した workload request は 15 変種の認証から取り直しになる。9-job 案では失敗した block request も15変種を全部ローカル認証し直す。45-job 案はそもそも現行 CLI に存在しない。
  影響: 「失敗した 1 request の残りだけ」の再開ではなく、その request が所有する認証単位全体の再走になる。

- [real] plan は group ID を campaign preimage に入れる一方、失敗 member の置換規則を定めていない。`plan.md:68, 111-114`。同じ group ID では stale claimとD193に阻まれ、新しい group IDでは成功済み member と同じ fresh groupにならない。
  影響: 現案で機械的に定義されている回復経路は whole fresh group の再取得だけであり、runbook の「成功 request を巻き添えで再実行しない」を満たさない。1 本だけの replacement を認めるなら、外側 composition の受理集合を別途設計、裁定、実装する必要がある。

## 共有 root の競合

- [real] 現行 3-workload fan-outでも各 worker は他 workload の block directory を走査する。`b10_backoff_shape_sweep.py:3047-3063`。block record は `O_EXCL` で file を公開してから書く一方、reader は直ちに全文 JSON を読む。`同:2283-2306, 2329-2350`。
  影響: writer と走査が重なると、partial record の parse failureまたは時刻依存の部分集合 reportになり、同じ正式系列から request ごとに異なる参照集合ができる。

- [real] report path 自体は `submission.trial`、すなわち request ID と nonce で分かれる。`b10_backoff_shape_sweep.py:330-344, 3064-3075`。したがって直接の create-only filename 衝突ではなく、各 request が異なる時点の全 workload snapshot を生成することが本質的な欠陥である。
  影響: 3 本が成功しても、exact 135 cell を唯一の入力にした正式 fan-in report は生成されない。

- [real] 同一 workload を block 分割する9-job案は、現行 identity に block がないため同じ claim、campaign lock、WAL、block filenameへ向かう。`config_for:1449-1521`、`run_formal:2906-2910, 2941-3045`。
  影響: そのまま投入すれば claimまたはlockで停止し、そこを越えても create-only block record が衝突する。

- [real] 共通 cache root も共有 writer面である。`b10_backoff_shape_sweep.py:2883-2893`。runbook は build-cache claim を非独立集合に含める。`pegasus-runbook.md:1300-1305`。
  影響: plan の job-local cache 化なしでは、3-job案も runbook 上の独立 job として投入できない。

- [real] `brief.md:47` の「欠陥1は main で解決済み」は単一 job の official root承認に限れば正しいが、分散形では未解決である。`_prepare_official_output` は一つの共通 claim rootを作るだけである。`b10_backoff_shape_sweep.py:2811-2822`。
  影響: この記述を分散対応済みと読むと、共有 cache、横断 reader、fan-in欠落を残したまま正式投入する。

## 親 brief の誤り

- [real] P1の「律速は直列化可能性検査」は実測から確定していない。CPU/経過 = 1.0 は trace I/O と verifier の内訳を持たず、さらに現行 capability は process 間移送不能である。`brief.md:74-77`。
  影響: P1を前提に設計すると、実装後に speedup が出ないか、認証 commit 自体が失敗する。

- [real] P2の9-job第一候補は成立しない。各 block jobが全15変種の認証を払うため verifyを3重化し、現行 identityにはblockがない。`brief.md:78-81`、`plan.md:8, 103`。
  影響: 壁時計をほぼ縮めず node-hourと中断点を約3倍にする。planがP2を退けた判断は支持できる。

- [real] P3の45 variant案への懸念は実体と一致する。現行 block loopは各 blockの登録順15点を一つのcampaignで走査する。`b10_backoff_shape_sweep.py:2978-3045`。
  影響: 45分割は設定変更では表現できず、R2のscheduleと外側集約の受理集合を変更する。

- [real] P4の「D1220はbinary輸送を直接裁定していない」は文言上正しい。ただし binary のRUNPATHが元jobの削除される `/scr` closureを指すため、単体copyは実行不能である。`plan.md:55-57`、`b10_backoff_shape_campaign.sh:277-282`。
  影響: D1220の追加解釈を待たなくても、現物の単体輸送案は正式実行に使えない。

- [real] P5は競合集合を過小列挙している。共通 build cache、blockを含まないcampaign identity、固定campaign trial、横断report readerも含む。`brief.md:88-90`、`plan.md:106`。
  影響: claimとblock recordだけを分離しても、正式な3-job fan-outは成立しない。

- [real] P6は支持できる。ただし「影響が比例」は故障確率の主張としては未測定である。確実に言えるのは、k本がsignal終了すればk本の `failure.json` と実行段階が失われることまでである。
  影響: 正式投入の前提条件に置く判断は妥当だが、確率的な線形増加を所要や信頼度の計算へ使えない。

- [real] 「欠陥3は4か所」は実体と不一致で、現在は5 literal siteである。
  影響: 修正対象を4か所として実装すると、残った1か所の照合で全requestが拒否されうる。

## 実装量の見積り

- [real] verifier多重化は新機構である。`pipeline.py:1365-1519` の trace取得と検査を分離し、`loop.py:466` のvariant直列処理をbatch化し、`core.py:162-258` と `commit_receipt.py:296-332` の同一PID authorityを保ったまま並列結果をcommitできる新しい receipt seamが要る。
  影響: pool sizeを設定するだけではなく、正しさ認証の中核を再設計する実装になる。

- [real] group identityと外側compositionも新機構である。`config_for:1449-1521`、prereg spec loader `b10_backoff_shape_sweep.py:830-1250`、driver CLI `:3096-3115` にgroup/member/exact集合を束縛し、protocol hashへ反映する必要がある。
  影響: A-2の設定を流用するだけではB-10の受理集合を変更できない。

- [real] job-local durable/cache rootと単一fan-inが必要である。`_prepare_official_output:2811-2822`、`cache_root:2883`、worker内集約 `3047-3075` を分離し、exact 3×45を一度だけ `judge` と `_write_reports` へ渡すconsumerを新設する必要がある。
  影響: 現行runを3回起動するだけでは正式reportが得られない。

- [real] login側group orchestrationが必要である。`submit_b10_backoff_shape.sh:7-296` は単一request専用なので、事前expected set、request/rc/receipt対応、単一待ち手、部分成功、replacementを扱う新CLIまたは同等の手動手順が要る。
  影響: runbook要件は現在、B-10について機械強制されていない。

- [real] 中断対応には少なくとも「成功memberを保持し、失敗memberのfresh identityを外側groupがどう受理するか」の規則と実装が要る。変更面は `campaign_claim.py:383-436` を緩めることではなく、B-10のmember identityとfan-in側expected setである。
  影響: この規則なしでは1本のwalltime終了がwhole group再走になる。

- [real] localized fixで済むのはsignal handlerとwalltime契約だけである。signalは `b10_backoff_shape_campaign.sh:107-115`、walltimeは上記5 siteと対応テストを変更する。
  影響: これらを直しても分散、多重化、fan-inは有効にならない。

- [real] 検証面は少なくとも `orchestrator/tests/test_b10_backoff_shape_sweep.py`、`test_campaign_claim.py`、`test_paper_story_a2_certification.py`、`test_pegasus_tools.py`、およびcampaign/receipt系テストへの追加が必要である。
  影響: 「docsまたは設定だけ」の変更量ではない。

- [real] 上記の実装はすべて `brief.md:5-8, 94-99` が定める本waveのdocs-only scope外である。
  影響: 本waveの設計文書は、これらを正式投入の未実装前提として列挙し、投入可能と表現してはならない。

## nit (影響を言えないもの)

- [real] briefの実アンカーには1行程度のずれがある。`run_formal` は2825、block loopは2978、横断集約は3047、SHA呼出しは2988、`performance_correctness_workload` は177である。`brief.md:59-66`。
  影響: 実行結果は変わらないが、レビュー時の参照精度が下がる。

- [real] planは並行度 `P` を固定せず、`P=47`を明示的に退けている。`plan.md:35-47`。
  影響: 根拠のない「N並列可能」という断定はplanにはない。この点は修正不要である。

## 総括

[real] 推奨された「3 workload job + node内process verifier pool +単一fan-in」は、所要が未証明であるだけでなく、現行のPID束縛された verifier capabilityにより、そのままではcorrectness commitできない。さらにgroup投入、単一待ち手、job-local root、exact fan-in、member replacementはいずれも未実装である。

影響: 現時点では投入可能な設計ではない。設定変更で済まず、認証経路と外側group orchestrationの新設が必要であり、それらは本waveのdocs-only scope外である。静的検査のみを行い、pytestまたは実走を緑とは記録していない。