## 所見

- **real — 直接の汎用化が8c consumerを壊し得るという主張。**  
  `trial_registry.py:51-114,1869-2008,2616-2726,3432-3555` は schema/path、8c固有語彙、slot parser、`TrialManifest` acceptance を固定している。`p3_autonomous_workload_trial.py:443-446,1163-1243,1261-1332,4371-4435,4679-4698` は launch・attempt・lifecycle を同一モジュールへ強く結合しており、既存テストも `test_trial_registry.py:5098-6470`、`test_p3_autonomous_workload_trial.py:6515-7359` に広がる。

- **unclear — 「だから8b専用の新実装が安い」という結論。**  
  attempt機構自体は `trial_registry.py:1818-3555`（約1,738行）にほぼ連続しており、8c固有のacceptanceは `:3432-3555` に集中する。既存8c APIを facade として残し、共通core＋8b adapterへ抽出する方が、同じ約1,700行を8bへ複製する専用実装より保守面で筋がよい。段2 plan `stage2-plan-output.md:136-157` はこの比較を実測していない。  
  したがって推奨は「`trial_registry.py` の公開契約を直接汎用化しない」までは real だが、「専用registryを複製する」は未立証である。

- **refuted — D649が8b registry共有・再利用を禁じたという読み。**  
  `docs/decisions.md:25952-25960` が却下したのは T-1472 scope の judge・3表・validator の二重実装であり、8b attempt registryの再利用可否ではない。D649自身も実装所在を8cの `trial_registry.py` と特定するだけである (`:25916-25927`)。

- **real — 8b専用対応物の所有範囲が未確定。**  
  8bは既に `s8b_holdout_admission.py:76-95` の共有root、`:1133-1141` の全attempt ID事前生成、`:1268-1315` のclaim、`:3796-3841` のconsume ledgerを持つ。`stage2-plan-output.md:149-157` の新 `registry.jsonl` はこれらと二重の正本になり得るため、既存ledgerを副証拠にするのか、新registryを唯一のmasterにするのか、同一lock/transactionでどう束縛するのかを明記しないと実効性がない。

- **real — registryだけではD510の出力前分類を満たさない。**  
  現行8bは `s8b_floor_campaign.py:4773-4840` で `measure_fn` 後に partial/performance 等を導出する。`trial_registry.py:3143-3150` もOSレベルのread-firstを証明しないと明記しているため、8b実装waveには trusted launcher と外部証拠由来の閉じた理由集合が別途必要である。

- **refuted / real — §10.6は実装を止めず、正式測定を止める。**  
  `docs/phase3-8b-descriptor-design.md:545-555` は「仕様だけを発効」「測定は認可しない」「実装の追随は別wave」と明記する。よって8b registryの設計・実装とは矛盾しないが、実装後も8c判定器・証拠契約・registry・結果judgeが発効するまで正式測定はできない。D649 `:25942-25950` の「production callerなし」もこのgateを閉じたままにする。

- **refuted — D649以降の裁定に、本件を逆転させる新規決定はない。**  
  D650 (`docs/decisions.md:25962-25971`) はsanctioned実測主体、D651 (`:25973-25984`) はfixture、D653 (`:26024-26049`) はcacheで無関係。D652 (`:25985-26022`) はverify-only、D654 (`:26051-26078`) は8b freeze producerのHEAD blob束縛、D657 (`:26117-26123`) は8c crashのindeterminate方針であり、8b registry共有を裁定していない。D655–D656、D658–D659 (`:26080-26148`) も直接の反証ではない。  
  今日のworklogでも、T-1476はverify-only (`docs/worklog.md:638-644`)、T-646はfreeze producer (`:1773-1800`)、T-1280/T-1314等はrole出力・report CLI (`:63-95,3454-3496`) であり、本件のregistry方針を変更する一次資料はない。

- **unclear — 並行wave衝突は履歴上は存在したが、現時点の実体では限定的。**  
  `docs/archive/worklog-phase3-0822-815.md:19-28` は T-1371/T-1280/T-1458 系が `trial_registry.py`・`p3_autonomous_workload_trial.py`・`autonomous_trial_completeness.py` を触っていたと記録する。しかし現行 `git worktree list` にはT-1371/T-1280/T-1472-floor-refreezeのworktreeはなく、live diffで対象3コードを変更しているのはT-1458の `autonomous_trial_completeness.py` のみ。`docs/phase3-8b-restart-runbook.md` の未コミット差分・branch差分は全worktreeで確認できなかった。  
  ただし同ファイルは `autonomous_trial_completeness.py:880-884` で `trial_registry` を遅延importしており、共通core抽出時の間接衝突は残る。

- **real — 段2のR-5案はDW-G04の出発点として抽象的すぎる。**  
  `stage2-plan-output.md:215-218` の「元freeze receipt」「次slot」「外部証拠」「epoch gate」は、canonical path、receipt名、`campaign_run_id`、発火判定を特定しない。次waveがそのまま実装開始できる粒度ではない。  
  書き換え案は次のように、実装許可と測定許可を分離すべきである。

  > **R-5（実装許可・正式測定不許可）**  
  > T-1484の実装対象は、`output/s8b-freeze/holdout_freeze.json` と `s8b_holdout_admission.shared_admission_root()` が返す `<git-common-dir>/izanagi/s8b-holdout-admission-v1`（`claims/`, `ledger.jsonl`, `attempt-ledger.jsonl`, `consumed/`）へ束縛された8b adapterに限る。master registryは `<shared-root>/attempt-registries/<freeze_sha256>/registry.jsonl` とし、genesisは観測前にcreate-onlyで作成し、6要素key (`s8b_holdout_admission.py:669-687`)、`campaign_run_id`、`attempt_id`、freeze bytes hashを束縛する。  
  > `D/journal.jsonl` の `session-start` (`s8b_floor_campaign.py:4729-4738`) および `measure_fn` (`:4773`) より前の分類receiptが存在しない限り、production callerを有効化しない。8cの `s8c_result_judge.py`、`output/s8c-preregistration/attempt-registry.jsonl`、証拠契約、判定器版、registry root hashの発効receiptが揃うまで、正式測定は認可せず、runはlegacy/exploratoryとする。旧R-5(a)〜(c)は履歴として残すが、salt・未知freeze再生成・terminal化を現行経路にしない。

- **real（限定付き） — DW-G05の現行HEADへの影響は正確だが、「永久」は条件付き。**  
  `docs/phase3-8b-restart-runbook.md:324-325` が、現行の固定v1 protocol/envではcrash点2〜6後にofficial floorを出せないと明記しており、brief `stage1-brief.md:68-72` の短期的影響は real。  
  一方、§10.3はfloor超過・scale gate・unique-bestを新しい公式性能層から外す (`phase3-8b-descriptor-design.md:499-503`)、oracleもfloorを入力にしない (`s8b_oracle_judge.py:452-464`)。したがって「selectorのcertified受理集合を永久にゼロにする」は将来epochまで一般化できず、現行旧consumerが残る間の運用上の袋小路、と限定して書くべきである。復旧後の対は時間差を持つ弱い証拠として扱う必要があり (`phase3-8b-descriptor-design.md:508-516`)、救出経路の価値は性能主張の強化ではなく、D496に沿った再測定可能性の回復である。

## 総括

段2の「直接汎用化は危険」は実コードで裏付けられるが、「専用複製が最善」は未検証である。  
8bでは既存admission ledgerとの唯一性・原子性を先に決め、共通attempt core＋8c互換facade＋8b adapterを優先候補にすべきである。  
§10.6は実装を妨げず正式測定だけを止める。DW-G05は現行HEAD限定の実害として記述するのが正確である。