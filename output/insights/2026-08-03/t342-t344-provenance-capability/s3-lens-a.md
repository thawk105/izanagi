静的読解上、変更後も受理集合は閉じない。以下で `s1-brief.md` / `s2-plan.md` は指定された必読ファイルを指す。

### 1. Critical — S8b の内部 core が official materializer gate を迂回する

claim: `run_campaign()` を通さず `_run_campaign_core()` を直接呼び、`mode=official` と非既定 `build_fn` を組み合わせる呼び出し形が残る。この形は、plan 適用後も `buildcache.build_v2()` の admission 境界を通ったことを保証しない。

evidence:

- official での seam 注入拒否と `_assert_official_permitted()` は public wrapper にしかない。`s8b_floor_campaign.py:2642-2671`
- core は同じ seam 群を直接受け、`mode` の値域だけを検査する。`s8b_floor_campaign.py:2685-2710`
- `build_fn` はそのまま `build_cells()` へ渡される。`s8b_floor_campaign.py:2941-2945,2995-2999`
- `build_cells()` は任意関数を呼び、返り値の contract SHA・argv・hash 形状だけを見る。関数が admission を実際に消費したかは検査しない。`s8b_floor_campaign.py:963-1006`
- binary はその返り値を基に store され、hash は由来でなく bytes の同一性だけを証明する。`s8b_floor_campaign.py:1762-1807`
- 最終的な `eligible_for_refreeze` は receipt chain ではなく `mode == "official"` だけで決まる。`s8b_floor_campaign.py:3045-3051,3094-3099`
- plan の S8b 変更面は binding 周辺だけで、wrapper/core の拒否配置を変更対象にしていない。`s2-plan.md:358-359`

impact: 他の official 前提を満たす正規入力を使いながら materializer だけを差し替えた場合、wrapper の拒否分岐を一度も通らず、任意 materializer の binary が official/refreeze 候補へ到達できる。

suggested_fix: official 拒否を core 内へ移し、official では materializer をハードコードする。テスト seam は別の fixture-only core に分離する。`eligible_for_refreeze` は mode ではなく、materializer gateway が発行し再検証できる receipt chain から導出する。

### 2. Critical — capability の発行器を in-process caller が自己利用できる

claim: sealed object と closed enum は偽 object を拒否するが、正規 factory の無権限利用を拒否しない。in-process caller は registered generator または parser-issued authority を自分で発行できる。

evidence:

- `SourceEvidence` 自体は通常の公開 dataclass で、`init=False` ではない。`s2-plan.md:23-40`
- caller が `GeneratorId` を選んで `build_run_context()` を呼べる。`s2-plan.md:86-90`
- `attest_generator_output()` が受けるのは context、source、caller 提供の input SHA だけで、generator を実際に起動した証拠や input bytes はない。`s2-plan.md:92-97`
- class 導出は、その factory が返した receipt を正規 receipt として扱う。`s2-plan.md:133-139`
- parser helper も公開 API であり、同一プロセスから別の parser に登録して authority を発行できる。`s2-plan.md:80-90,143-147`
- plan 自身も parser token が同一 Python process 内の悪意ある caller を防げないと認める。`s2-plan.md:483`
- loop は caller 提供の capability resolver を受ける設計である。`s2-plan.md:230-239`

未拒否の構文クラスは、実 source evidence を取得した後、任意の既知 generator ID で正規 attester を呼ぶ形、および公式 driver を経ず別 parser から正規 authority を発行する形である。どちらも factory 由来なので exact type/seal/context 拒否には該当しない。

impact: coder 由来 source を `MACHINE_GENERATED` または `CODER_AUTHORED` とする能力が、実質的に同一プロセス内の全 caller に残る。registry はラベル集合と module digest を閉じるだけで、generator の実行主体を認証しない。

suggested_fix: 同一プロセスを敵対境界に含めるなら、issuer を別プロセス・OS capability・保護された署名鍵のいずれかへ移す。generator runner 自身が入力を受け、生成し、出力 hash を署名する必要がある。そこまで行わない場合は「capability」ではなく誤用防止用 metadata と明記し、security boundary の主張を撤回する。

### 3. High — STOCK は「承認済み pin」でなく「caller が選んだ HEAD に対して clean」

claim: caller が `ccbench_dir` と `ccbench_commit` を一緒に選べるため、stock 導出は自己参照的である。任意の clean checkout とその HEAD の組は STOCK 条件を満たせる。

evidence:

- `resolve_evidence()` は commit、checkout path、compiler を caller 引数として受ける。`s2-plan.md:34-40`
- stock 規則は `src_token == STOCK` と `tracked_clean` だけで、policy が承認した commit/root との照合を含まない。`s2-plan.md:133-136`
- `build_run_context()` に expected commit/root の入力はない。`s2-plan.md:86-90`
- 現行 digest は選択された directory と、その directory に対する `git show` を比較する。`source_digest.py:541-552,634-659,701-713`
- materializer の commit 検査も、宣言値と同じ選択 tree の HEAD が prefix 一致するかを見るだけである。`buildcache.py:883-906`

未拒否の構文クラスは、caller が選んだ clean checkout、同 checkout の commit、そこから解決した evidence を一組として渡す形である。内部整合性検査はすべて成立し、承認済み gitlink との比較分岐は存在しない。

impact: 「clean-at-declared-pin」と「信頼された stock baseline」が混同される。caller 管理の source を事前に commit すれば coder 相当の内容でも STOCK 権限を得られる。これは caller が checkout を選べるという本レビューの脅威条件下での結論であり、任意 pin を信頼する運用なら名称・主張側を弱める必要がある。

suggested_fix: `BuildAdmissionPolicy` に外部正本由来の full gitlink、repository identity、許可された source root を焼き込み、evidence の自己申告 pin ではなく policy pin と照合する。

### 4. Critical — 永続 receipt は hash だけで、capability を再検証できない

claim: cache/WAL に残る map は runtime の sealed capability を保存せず、その hash だけを保存する。したがって replay 時に generator/reviewer の真正性を検査する情報がない。

evidence:

- 永続形には `generator_receipt_sha256` と `review_receipt_sha256` しかなく、GeneratorId、generator input、review ID、receipt body がない。`s2-plan.md:153-171`
- runtime の generator receipt 検証に必要な source と input SHA は API 上存在する。`s2-plan.md:92-104`
- replay validator は `expected_source=None` も許す。`s2-plan.md:121-126`
- `receipt_sha256` は同じ map に対する通常の outer SHA であり、issuer の署名ではない。`s2-plan.md:153-174`

未拒否の構文クラスは、exact-key map に内部整合する source/class/policy と、保存先のない receipt digest を載せる形である。outer SHA も再計算できるため、schema・outer SHA・map 間 equality のどの拒否にも該当しない。特に generator input が永続形にないので、正規 receipt の再導出もできない。

impact: この schema が証明するのは「同じ map が複数面にコピーされたこと」までであり、registered generator や human review が実在したことではない。cache/manifest/WAL の書換え可能主体に対する provenance 境界にはならない。

suggested_fix: generator/review receipt の完全な canonical body を保存して再検証するか、content-addressed かつ署名済みの append-only ledger を参照する。署名者は finding 2 の in-process caller から隔離する。

### 5. High — materializer 全件表になっておらず、直接 CMake と binary 取得経路が残る

claim: `s2-plan.md:252-276` は `BuildAdmission`/`buildcache` caller の表であり、CCBench binary を作る全 materializer の表ではない。

evidence: repository-wide の直接 CCBench build 箇所には少なくとも次がある。

- 診断・broken-control build:
  `s2_verify_calibration.py:243-275`、`s3_lock_coverage.py:136-162`、`s5_permutation_coverage.py:132-158`
- trigger coverage とその再利用:
  `s8a_trigger_coverage.py:102-131`、`s8a_trigger_freq.py:60,140-145`
- 独自 evidence campaign:
  `t152_write_intent_coverage.py:340-395`、`silo_ladder_rung1.py:2111-2179,3777-3845`
- shell materializer:
  `tools/pegasus/certify_calibration.sh:495-520`、
  `tools/pegasus/t141_region_profile.sh:1156-1207`、
  `tools/pegasus/probes/t139_positive_control_probe.sh:32-45`
- arbitrary binary の取得面:
  calibrator は caller 指定 executable path を受ける。`calibrator/cli.py:100-105`
- S8b は作成済み binary を content-addressed store へ複製し、resume では hash だけで取得する。`s8b_floor_campaign.py:1762-1829`

plan の静的検査は direct `BuildAdmission` constructor の探索に限定されるため、これらを検出しない。`s2-plan.md:408`

impact: 診断専用 materializer が直ちに certified になるとは限らないが、「診断専用で admission-aware consumer には流入不能」という機械契約がない。S8b は finding 1 により実際に official 経路へ再合流できる。したがって「materializer は build/build_v2 だけ」という前提は成立しない。

suggested_fix: 全 executable producer/loader を inventory 化する。認証対象は単一 gateway を必須にし、broken/probe 用は schema 上 `non-admissible` として downstream が拒否する。静的検査は direct CMake target、shell build、外部 binary path、store/resume loader も対象にする。

### 6. High — pre/post evidence 再取得では ABA と mixed snapshot を塞げない

claim: plan の「同じ snapshot」は immutable snapshot の作成ではなく、変更可能な working tree の複数回読取として書かれている。build 中だけ tree が動き、終了前に元へ戻る順序は検出されない。

evidence:

- 現行 digest は Options、protocol CMake、複数 source を逐次読む。`source_digest.py:525-552`
- baseline、status、source digest も別々の subprocess/read である。`source_digest.py:634-713`
- 実 build はその後に外部 CMake process が source を読む。`buildcache.py:584-624,724-739`
- `_recheck_src_token()` と `_assert_trace_diff()` は build 後の最終状態だけを検査する。`buildcache.py:750-796`
- plan は「同じ snapshot」と pre/post equality を要求するが、staging、read-only tree、tree object の固定を指定していない。`s2-plan.md:187-196`

未拒否の実行順序は、evidence A の発行後、compile が source B または A/B 混在を読む時間帯だけ tree が変わり、post-evidence 前に A へ戻る形である。前後 evidence は一致するため、予定された TOCTOU 拒否分岐に入らない。

impact: receipt/cache key は A を指す一方、binary は一時状態または混合状態を含み得る。その binary が新 admission namespace に publish される。

suggested_fix: evidence から content-addressed source tree を一度だけ作り、build の `-S` をその read-only snapshot に固定する。pre/post 再読は補助検査に留める。

### 7. High — overlay validator を通らない raw replay と派生 artifact の laundering が残る

claim: overlay は campaign directory を直接読む列挙済み consumer にしか配線されない。旧 WAL を prefix/path で読む consumer と、旧結果を既に凍結した派生 artifact は validator を通らない。

evidence:

- plan の guard 対象は layer3、critic、S6/S8a、autonomous completeness、backoff report などに限定される。`s2-plan.md:292-317`
- `replay.py` は campaign ID 変更を意図的に避けるため prefix で旧 directory を発見する。`replay.py:87-105`
- 同 loader は `COMMIT` と旧 `VERIFY_DONE.certified` だけで landscape を certified として返す。`replay.py:113-145`
- `p2_5.py` はその raw replay landscape と別の旧 WAL を集計する。`p2_5.py:40-61,74-104`
- 編集禁止の `s1_known_axes_freeze.py` は P2/backoff の glob、S6 の raw WAL/COMMIT、S8a provenance を直接読む。`s1_known_axes_freeze.py:128-199,241-315,361-455,471-528`
- `verify_document()` は同じ raw source から document を再構成するだけで admission receipt を要求しない。`s1_known_axes_freeze.py:718-766`
- その freeze は S1 measurement の cell sourceになり、さらに holdout/oracle は known-axes の byte hash を信頼する。`s1_measurement_freeze.py:156-190,245-277`、`s8b_holdout_freeze.py:548-559,709-711`、`s8b_oracle_manifest.py:702-705,848-855`
- plan はこのファイルを無編集としつつ、S1 経路を human review receipt に昇格する。`s2-plan.md:266,361-365`

未拒否の構文クラスは、旧 campaign を `replay.load_landscape()` 型の prefix loader で読む形と、旧 campaign の値を内包した known-axes freeze を human-reviewed source として渡す形である。どちらも original campaign path を `require_admitted_campaign()` に提示しない。

impact: receiptless 測定が新しい replay 結果、freeze、S1/S8b materialization の入力へ再発行される。overlay の positive validation は推移的 provenance を保証しない。

suggested_fix: raw WAL reader と admission-aware view を型として分離し、selection/report は後者しか受けないようにする。派生 artifact は全 source campaign の admission classification を推移的に保持する。既存 known-axes を残すなら `legacy-derived` とし、human review による暗黙の provenance 昇格とは分離する。

### 8. Medium — 旧 cache/lock の「拒否」分岐は通常の到達順では発火しない

claim: plan が実際に塞ぐのは新 namespace 間の跨ぎであり、既存 artifact の能動的拒否ではない。

evidence:

| 面 | plan 後の通常到達 | 発火しない拒否 |
|---|---|---|
| legacy key | admission digest で新 key へ行く。`s2-plan.md:198-201,371` | 旧 key は探索されず、sidecar 欠落拒否は旧 entry を新 key 下へ置いた場合だけ |
| v2 preimage | 新 digest へ行く。`s2-plan.md:203-207,372` | 旧 digest の completion manifest は開かれない |
| completion manifest | 新 schema entry だけを読む。`s2-plan.md:203-207,373` | exact-key 拒否は移設・複製された旧 manifest にだけ発火 |
| campaign lock/WAL | policy を入れた新 campaign ID を先に導出する。`s2-plan.md:209-215,230-236,374` | 旧 directory の lock mismatch・receiptless terminal 検査には到達しない |

現行も campaign ID/layout の決定が lock/replay より先である。`loop.py:120-147`。これは brief の「旧3 campaign の resume で実発火する」という P5 と両立しない。`s1-brief.md:71-74`

impact: 安全効果としての非再利用は得られるが、historic bytes が拒否されたという監査証拠にはならない。さらに finding 7 の path/prefix reader では orphan 化自体が防壁にならない。

suggested_fix: 「拒否」ではなく「通常 resolver から到達不能」と記述を改める。能動的拒否が要件なら、新 identity を作る前に旧 identity/path を read-only probe し、存在時は structured legacy error にする。

## 総括

最も危険な残存迂回路は、S8b の `_run_campaign_core` 直呼びと `build_fn` seam の組合せである。wrapper の official 拒否を外し、任意 materializer の返り値を refreeze eligible まで運べる。

撤回すべき主張は `s2-plan.md:384,495-497` の「receiptless legacy artifact は通らず、全 identity 面を束縛した」である。静的に言えるのは新 generic namespace の分離までで、issuer、直接 materializer、raw/派生 consumer は未閉鎖である。