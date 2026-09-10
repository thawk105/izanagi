### L2-01 / v1 corpus test が 32 本中 30 本しか固定していない

- **一行要約:** 「既存 v1 lock 32 本の分類不変」という裁定を満たさず、`output/campaigns` の30本だけを検査している。
- **判定:** real
- **重要度:** must-fix
- **根拠:** 裁定は `stage4-ruling.md:77,91` で32本を要求する一方、`test_artifact_admission.py:720-740` は `output/campaigns` だけを走査する。実物は同ディレクトリ30本に加え、`output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/campaign-layout/campaigns/**/campaign.lock` が2本あり、合計32本。`stage5-impl.md:49` の「32本を確認」ともテスト射程が一致しない。
- **成果物影響:** insight 配下の既存2 lock が v2 化・破損・消失しても受理集合回帰テストが緑のままになる。
- **最小の修正案:** `output/**/campaign.lock` を独立走査して exact 32・全件 v1 を固定し、現在の30 campaignについては既存の admission classification mapping を併用する。

### L2-02 / 波及 census は 15 ではなく16 fixture consumerで、decode-only production consumerもある

- **一行要約:** 実装報告の consumer census は過少だが、未対応の実害箇所は後述の独立 `test_layer3_report.py` に絞られる。
- **判定:** real
- **重要度:** nit
- **根拠:** `stage5-impl.md:54-75` は production 2 module・共有 fixture 15ファイルとしているが、`grep -rl campaign_lock_test_support orchestrator/tests/` は次の16ファイルを返す。
  - `test_artifact_admission.py:38`
  - `test_autonomous_trial_completeness.py:40`
  - `test_campaign.py:78`
  - `test_campaign_lock_wal_consumers.py:24`
  - `test_critic.py:51`
  - `test_p3_autonomous_workload_trial.py:39`
  - `test_p3_exploration_namespace.py:34`
  - `test_p3_s4_loop.py:59`
  - `test_p3_s4_loop_sort.py:33`
  - `test_p3_s4_loop_trigger_gating.py:62`
  - `test_s1_direct_comparison.py:43`
  - `test_s6_sort_sweep.py:51`
  - `test_s8a_trigger_sweep.py:53`
  - `test_screening_driver.py:33`
  - `test_t126_qualification_artifacts.py:49`
  - `test_t671_source_binding.py:284`
  
  production の直接 binding gate は `ident.py:249-250,369` と `artifact_admission.py:556-560`。exact-2→exact-8 の codec 波及先には、さらに `autonomous_trial_completeness.py:174`、`layer3_report.py:94`、`wal.py:701,728`、`qualification/artifacts.py:813` がある。独立 production capture は `test_layer3_report.py:64` だけであり、全 repo census 上これ以外はない。
- **成果物影響:** handoffだけを根拠に将来の変更を行うと、1テストと4つのdecode-only production境界を棚卸しから落とす。
- **最小の修正案:** 段7記録では「共有16、独立capture 1、production binding 2、追加decode-only 4」と訂正する。

### L2-03 / T-720の未commit状態では独立fixtureとproduction captureが偽の赤になる

- **一行要約:** T-721 land後、T-720が `execution_guard.py` または `pipeline.py` を編集した状態では、独立fixtureが必ず `contract-loader-drift` で停止する。
- **判定:** real
- **重要度:** nit
- **根拠:** T-720 は `u1.patch:391-406` で `execution_guard.py`、`:1187-1216` で `pipeline.py` を変更する。両者は `campaign_lock.py:32,34` の閉包内であり、production captureは `contract_loader_binding.py:324-337` でdisk≠HEADを拒否する。共有helperは `campaign_lock_test_support.py:10-20` でHEAD blobだけを使うため16 consumerの偽赤を避けるが、`test_layer3_report.py:53-64` は引き続きproduction captureを使う。T-720側も同ファイルのimport部を変更する（`u2.patch:1598-1622`）が、helper本体とは別hunkなので直接のmerge conflictではない。
- **成果物影響:** T-720はcommit前の `test_layer3_report.py` と新規certified lockを作るproduction-pathテストを緑にできず、機能赤とsource-drift赤が混在する。
- **最小の修正案:** `test_layer3_report.py` のローカルhelperも共有されたrecorded-HEAD bindingへ寄せ、T-720のproduction capture検査はcommit済み候補に対して行う。

### L2-04 / private関数依存は実在するが、現差分にfail-openはない

- **一行要約:** `_validated_root`・`_head_commit`・`_blob` への直接依存は将来のco-drift危険だが、現在の失敗経路を成功へ倒してはいない。
- **判定:** real
- **重要度:** nit
- **根拠:** private依存は `campaign_lock_test_support.py:12-17`。例外は捕捉されず伝播し、生成値も `ContractLoaderBinding` のexact commit/map検査を通る（`contract_loader_binding.py:58-61,64-86`）。さらに `test_t671_source_binding.py:280-315` は独立した `git cat-file` 結果とfixture digestを比較し、`:318-350` はproduction call siteを固定する。live driftとcommitted mismatchも8 path全件でparameterizeされている（`:131-176,179-248`）。
- **成果物影響:** private関数の意味がproducerとverifierで同時に変わると、未被覆の意味論だけはfixtureも追随して検出を失う可能性がある。
- **最小の修正案:** dirty recorded-blob正例を8 pathすべてにparameterizeし、各digestを独立したGit呼出し結果と比較する。

### L2-05 / 既存テストの期待値緩和・負例理由のすり替わり

- **一行要約:** assert削除・skip・xfail・期待値反転はなく、digest変更は負例の誤った早期失敗を除去している。
- **判定:** refuted
- **重要度:** nit
- **根拠:** `_authority()` は `test_campaign_lock_codec.py:34-48` で全8 digestを有効な64桁SHA-256にする。旧 `str(index) * 64` はindex 10以降で128桁となり、対象変異より先にhash shapeで落ち得た。新しいkey欠落負例は `:166-179`、exact-2負例は `:182-196` でエラー理由まで固定する。既存の `[-1]` は `test_artifact_admission.py:1147-1153` で明示pathへ置換されただけで、拒否期待は維持されている。
- **成果物影響:** なし。closure関連の負例は以前より単一理由性が強い。
- **最小の修正案:** なし。

### L2-06 / exact-2拒否・exact-8受理と未裁定の受理集合変更

- **一行要約:** v2の2点は固定できており、裁定外のproduction受理拡張は見つからない。ただしv1の32本固定だけはL2-01で未達。
- **判定:** refuted
- **重要度:** nit
- **根拠:** exact-2拒否は `test_campaign_lock_codec.py:182-196`。独立exact-8 tupleは `test_t671_source_binding.py:22-31,119-128`、admission正例は `test_artifact_admission.py:933-944` で8 keyと最終admissionを検査する。codec本体は `campaign_lock.py:167-180` でexact集合比較を維持する。productionのcapture/live/committedはいずれも全8 pathを走査し、失敗を無視する分岐はない（`contract_loader_binding.py:324-377`）。
- **成果物影響:** v2 wire受理集合は裁定どおりexact-2からexact-8へ置換され、それ以外は引き続き拒否される。
- **最小の修正案:** L2-01だけを修正する。

## 総括

- **NO-GO**
- real must-fix: **1件**
- real nit: **3件**
- refuted: **2件**
- blockerは「32本不変」を称するテストが実際には30本しか覆わない一点。
- productionのfail-closedロジック自体に緩和は見つからない。
- T-720との直接merge conflictは薄いが、commit前のsource-drift偽赤は具体的に残る。