判定は **NO-GO**。親 brief と段 2 プランを全文読んだうえで、実装・成果物を静的に追跡した。read-only 制約に従い pytest は実行しておらず、緑とは判定していない。

## 所見

### 1. 親 P1/P2 の「受理集合不変」は双方向に反証できる

[severity: must-fix]

攻撃シナリオ:

- 有効な legacy cache があり、対応する v2 namespace に stale `.building` がある。変更前の legacy 経路は成功するが、P1 の直接配線後は v2 claim で拒否される。
- 逆に、legacy admission sidecar が不正で、有効な v2 entry が存在する。変更前は legacy sidecar 検査で拒否、P1 後は v2 cache hit を受理する。これは明確な「変更前は拒否、変更後は受理」である。
- さらに `sanity_silo` は現在 NUMA 引数を渡しておらず、trigger-gating は site から contract を動的に選ぶため、「残り 12 本が linux-baremetal 値と完全一致」という実測 3/4 も成立しない。

根拠:

- P1/P2 の主張は [brief.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/brief.md:56)。
- `env_contract` の有無で legacy/v2 が分岐するのは [pipeline.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:745)。
- v2 stale claim は常に拒否される [buildcache.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:674)。
- legacy hit は admission sidecar を再検証する [buildcache.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:851)。
- `sanity_silo` の呼出しには `numactl` がない [sanity_silo.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:52)。
- trigger-gating は site で contract と selector の有無を変える [p3_s4_loop_trigger_gating.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:318)、[p3_s4_loop_trigger_gating.py:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:560)。
- 段 2 プラン自身も同じ双方向反例を認めている [s2-plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:116)、[s2-plan.md:130](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:130)。

提案:

P1/P2 と brief の受理集合不変条件を正式に supersede し、既存 `env_contract` の一斉配線は実装しない。段 2 の却下判断だけでは、親 brief の相反する不変条件が残るため不十分である。

---

### 2. 二本の contract を食い違わせると「旧拒否→新受理」が生じる

[severity: must-fix]

攻撃シナリオ:

1. site=`OTHER`、実行値=`linux-baremetal/1800/numactl`。
2. `authorization_contract=lookup("linux-baremetal")` を渡す。
3. build selector には `env_contract=lookup("pegasus")` を渡す。
4. 新設 authorization は Linux 値だけを検査して成功する。
5. pipeline は Pegasus selector を `isinstance` でしか検査せず、Pegasus namespace の v2 build を使って certified COMMIT へ到達できる。

旧 API へプランの写像どおり `authorization_contract` を除くと、`env_contract=Pegasus` と Linux 実行値の不一致で拒否される。したがってプランの「旧拒否→新受理なし」は偽である。compute 上では authorization=Pegasus、selector=Linux の逆向きも作れる。

別の反例として、正規 authorization と `ExecutionEnvironmentContract` の subclass selector を組み合わせられる。旧 API は exact type で拒否するが、新 selector は `isinstance` なので受理する。

また Pegasus の canonical `numactl=()` に対し、実行引数 `numactl=None`、`""`、`False` はすべて `tuple(numactl or ()) == ()` となる。契約型は「空 tuple は解決済み、None は未解決」と明記しているため、「実行値完全一致」は実際には成立していない。

根拠:

- 分離案に不一致禁止がない [s2-plan.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:80)、[s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:97)。
- 「旧拒否→新受理なし」の主張 [s2-plan.md:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:124)。
- 現行 authorization は exact type を要求する [loop.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:76)。
- falsy な NUMA 値を空 tuple に潰す [loop.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:78)。
- pipeline と build-v2 は selector を `isinstance` でしか検査しない [pipeline.py:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:759)、[buildcache.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:613)。
- build-v2 が実際に使う契約情報は主に namespace の `contract_sha256` [buildcache.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:648)。
- None と解決済み空の区別は契約の明示仕様 [env_contract.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:89)。

予定される `authorization_contract=None` の exact-type gate 自体には具体的発火入力があるため、これは恒真ではない。しかし「完全一致」のうち Pegasus NUMA resolvedness に関する gate は bypass 可能である。

提案:

`env_contract is not None` の場合、出力作成前に以下を必須化する。

- selector も exact `ExecutionEnvironmentContract`
- `env_contract == authorization_contract`
- runtime `numactl is not None`
- runtime NUMA は list/tuple と各要素 exact str を確認してから tuple 化

不一致の両方向、subclass、`None`、空文字列を負例にする。既存の Pegasus `None` 受理を縮小するため、必要なら「裁定パッケージ候補」として明示する。

---

### 3. `sanity_silo` の NUMA 補正は実行条件でなく申告値だけを書き換える

[severity: must-fix]

攻撃シナリオ:

プランどおり `numactl=list(contract.numactl)` を `sanity_silo` に追加する。authorization は通るが、`do_bench=False` かつ legacy correctness のため、pipeline は実際の trace verifier を `_run_one_pass(..., None)` で起動する。つまり「numactl 付きで実行した」という authorization と、実際の subprocess が一致しない。

これは実行条件の正当な補正ではなく、gate を通すためにメタデータだけを補正した状態である。`sanity_silo` に対する NUMA gate は謳うだけで効かない。

根拠:

- プランが「authorization を通すため」と明記している [s2-plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:112)。
- `sanity_silo` は verifier sanity で、bench を実行しない [sanity_silo.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:2)、[sanity_silo.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:52)。
- legacy correctness は実行 NUMA 引数を捨てている [pipeline.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1003)、[pipeline.py:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1005)。

提案:

次のいずれかを裁定する。

- verifier subprocess 自体へ NUMA prefix を適用し、歴史的 sanity 条件の変更として正例を再登録する。
- no-bench verifier 用に、実際の no-prefix 実行を表現する別 contract を設ける。
- `sanity_silo` の成果物を measurement-contract-bound certified の対象外と明示する。

単なる caller 引数追加は採用しない。

---

### 4. authorization は WAL/proof chain に束縛されず、旧 unbound COMMIT を再利用できる

[severity: must-fix]

攻撃シナリオ:

1. 変更前に `env_contract=None` で Linux campaign を走らせ、`STAGE_COMMIT` を残す。
2. 変更後、同一 `CampaignConfig` で正しい Linux authorization を渡す。
3. authorization は現在環境について成功する。
4. campaign ID は環境・authorization を含まないため、同じ layout が開かれる。
5. replay は旧 COMMIT を authorization hash の検査なしに terminal とし、再評価を skip する。

さらに plan は `attestation_mode="none"` の receipt 永続化を明示的に先送りしているため、新規 Linux COMMIT も後から契約束縛を証明できない。

根拠:

- plan の receipt 永続化先送り [s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:84)。
- mode=none は receipt を返さない [loop.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:84)。
- campaign identity は env/実測値を明示的に除外する [ident.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/ident.py:125)。
- replay は任意の `STAGE_COMMIT` を契約検査なしで committed にする [wal.py:1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/wal.py:1384)。
- COMMIT payload に contract/authorization hash がない [pipeline.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1017)、[pipeline.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1064)。

提案:

mode=none にも sealed authorization receipt を発行し、contract hash と authorization schema/epoch を campaign lock および各 COMMIT に束縛する。replay 時にも一致を検証し、旧 unbound terminal は quarantine または別 identity に隔離する。

これを本 wave から外すなら、成果物を「proof-chain に束縛された certified writer closure」と呼べないため「裁定パッケージ候補」。

---

### 5. `run_campaign` の外に未認証の certified writer が残る

[severity: must-fix]

攻撃シナリオ:

`s8a_trigger_sweep` を screening 有効で実行すると、`run_campaign` ではなく `screening_driver.evaluate_candidate()` が `pipeline.evaluate()` を直接呼ぶ。そこには authorization も env selector もなく、一般 pipeline の verifier 通過後に `certified=True` と COMMIT が書かれる。同じ経路が `s6_sort_sweep` と `backoff_sweep` にもある。

`s1_direct_comparison` もデフォルト `evaluate_fn=pipeline.evaluate` を直接呼び、contract を渡さない。したがって AST で 12 module/15 `run_campaign` call を閉じても writer 集合は閉じない。

根拠:

- screening の直接 evaluate [screening_driver.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:134)、[screening_driver.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:170)。
- S8a の分岐 [s8a_trigger_sweep.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8a_trigger_sweep.py:456)、[s8a_trigger_sweep.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8a_trigger_sweep.py:463)。
- S6 も同型 [s6_sort_sweep.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s6_sort_sweep.py:352)。
- backoff は baseline/candidate とも直接 screening driver を使う [backoff_sweep.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_sweep.py:84)。
- S1 の直接 evaluate [s1_direct_comparison.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:626)、[s1_direct_comparison.py:793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:793)。
- 一般 pipeline の contract gate は qualification branch にしかない [pipeline.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:546)。
- certified/COMMIT sink [pipeline.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1009)。
- plan の閉包テストは `run_campaign` call だけ [s2-plan.md:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:229)。

また、将来 pipeline 深部に guard を足すだけでは、screening の `except Exception` が失敗を通常の variant abort へ降格する [screening_driver.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:181)。S1 も例外を retryable 扱いする [s1_direct_comparison.py:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s1_direct_comparison.py:806)。規律 3 の失敗帰属も失われる。

別系統として、S8b oracle と T126 は直接 pipeline caller だが、前者は env contract を渡し [s8b_oracle_driver.py:1351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_oracle_driver.py:1351)、後者は qualification exact gate を使う [t126_driver.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:524)。collector は最終成果物 writer [collector.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/collector.py:1118)、`guided.py` は replay 値から独自 COMMIT を書く [guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/guided.py:127)。floor driver は correctness-certified ではない独自計測路 [s8b_floor_campaign.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:17)。

提案:

- 真に閉じるなら、pre-authorized capability を ultimate certified sink まで運び、各 driver が layout/attempt 作成前に取得・検証する。
- scope を限定するなら、名称を「`loop.run_campaign` と二 wrapper の closure」に縮め、screening、S1、guided、collector、S8b/T126 独自系を明示的に scope 外とする。未認証の screening/S1 は「裁定パッケージ候補」。

---

### 6. shell preflight は required attestation を実施せず、実環境 drift 後にも書き始める

[severity: must-fix]

攻撃シナリオ:

hostname/site は Pegasus compute、submit receipt・source commit・protocol・calibration bytes はすべて正しいが、CPU topology、affinity、governor、TSC のいずれかが較正時から変化した状態を作る。

プランの preflight は `load_verified_calibration()` までしか行わないため成功し、その後 TMPDIR/job-staging を作る。実際の hardware probe は floor/T126 driver 内で初めて失敗する。`attestation_mode="required"` の契約を「最初の書込み前に検査した」という主張は偽である。

根拠:

- plan は probe を意図的に呼ばない [s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:159)。
- `load_verified_calibration` は静的な bytes/schema leaf への委譲だけ [env_attestation.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_attestation.py:1023)。
- 実 probe は CPU、NUMA、TSC、visibility を観測する [env_attestation.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_attestation.py:639)。
- required receipt は probe と比較が通らなければ発行されない [execution_guard.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:435)。
- floor の現在の最初の書込み [floor_campaign.sh:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:29)、T126 は [t126_qualification.sh:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:74)。
- floor の full attestation は後段 [s8b_floor_campaign.py:2841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:2841)、T126 も後段で probe する [t126_driver.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:439)。

提案:

静的 gate には stale hash/site という具体的発火入力があるため、全体が恒真なわけではない。しかし required-attestation 部分については、**この gate は謳うだけで効かない**。

書込みを伴わない full probe を分離するか、source identity に pin した事前ビルド済み TSC probe を使い、比較結果を構造化 stderr と非 0 exit で返す。それが scope 内で不可能なら、P3 を「静的 contract material preflight」に狭め、full attestation-before-write を「裁定パッケージ候補」とする。

---

### 7. floor protocol は source commit に束縛されず、意味的に有効な別 bytes を実行できる

[severity: must-fix]

攻撃シナリオ:

1. clean tree で floor job を submit し、receipt に source commit と wrapper hashを記録する。
2. qsub 後、`output/s8b-freeze/floor_protocol.json` の `master_seed` を別の非空文字列へ変更する。
3. job 側の git status は `output/` を除外するため変更を検出しない。
4. planned helper の strict parse と current contract 検査は通る。`master_seed` は非空であれば受理される。
5. driver は working-tree の変更後 protocol を読み、別 schedule を実行する。

これは stale `contract_sha256` の 1 nibble 変更テストでは検出できない。

根拠:

- plan の floor 検査は strict parse と `_validate_protocol_against_current()` まで [s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:151)。
- `master_seed` は非空文字列しか要求されない [s8b_floor_contract.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_contract.py:153)。
- seed は実際の schedule を変える [s8b_floor_contract.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_contract.py:375)。
- runtime の dirty-tree 検査は `output` を除外する [floor_campaign.sh:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:491)。
- driver は working-tree path を直接読む [floor_campaign.sh:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:880)。
- submit receipt は source commit と job-script hashを持つが protocol hashを持たない [submit_floor.sh:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_floor.sh:455)。
- frozen manifest には exact protocol digest がある [test_frozen_artifacts.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_frozen_artifacts.py:43) が、wrapper はこれを trust root にしていない。

提案:

receipt の `source_commit` から `git cat-file` で protocol blob を読み、承認 SHA-256 と一致させる。preflight 後はその検証済み bytes を attempt 内へ create-only で materializeし、driver は working-tree pathでなくそのコピーを読む。

「contract hash は正しいが master_seed だけ異なる」負例と、helper 非 0 時に TMPDIR・attempt・driver launch がすべて発生しない wrapper 結合テストを追加する。

---

### 8. T126 helper 追加は既存 identity の受理集合を縮小し、P4 の一般化に反する

[severity: must-fix]

攻撃シナリオ:

変更前に妥当だった T126 `series_identity.code_identity` を変更後の validator へ渡す。plan が helper path を `REQUIRED_CODE_IDENTITY_PATHS` に追加すると、旧 identity は新 key を持たないため exact-set 検査で拒否される。

これは fail-closed な縮小ではあるが、plan の受理集合表にも parent P4 にも記載されていない。future series ID、submission receipt、job-result chain も必ず変わる。

根拠:

- helper を required code identity に追加する計画 [s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:157)。
- current required code/script set [contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:38)、[contract.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:67)。
- validator は key 集合の完全一致を要求する [contract.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:501)。
- driver は全 identity file の current/commit hash を取る [t126_driver.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:346)。
- collector も wrapper hashを identity から復元する [collector.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/collector.py:499)。

狭義の「現在の FROZEN_MANIFEST 23 bytes を編集しない」には静的反例を見つけなかった。ただし P4 の「したがって DW-O10 不成立」は反証される。また brief が挙げる `94a4…` は歴史的登録物であり、current Pegasus contract が使う active calibration は `753f…` [env_contract.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:256)。

提案:

identity schema/version と required-set 世代を分け、旧 identity の検証規則をその世代に固定する。既存成果物を書き換えない。互換性を切るなら受理縮小と future series ID 変更を「裁定パッケージ候補」として承認対象にする。

---

### 9. 親の「実測 1〜8」は 1、5 以外をそのまま証拠にできない

[severity: should-fix]

攻撃シナリオ:

誤った caller 数・固定値・write ordering・test coverage を証拠として implementation acceptance を組むと、未被覆経路を「検証済み」と誤認する。

根拠:

1. **実測 1: 狭義には正しい。** `None` bypass は site-specific gate より前 [loop.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:68)。
2. **実測 2: 偽。** brief が caller と数えた T126 と S8b oracle は `run_campaign` でなく直接 `pipeline.evaluate` を呼ぶ [t126_driver.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:524)、[s8b_oracle_driver.py:1351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_oracle_driver.py:1351)。静的 inventory は 12 module/15 call expression。
3. **実測 3: 偽。** `sanity_silo` は NUMA を渡さず、trigger-gating は runtime site で値を解決する。
4. **実測 4: contract literal 自体は記述どおりだが、12 driver との完全一致と受理集合不変への一般化が偽。** Linux 値は [env_contract.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:237)。
5. **実測 5: 正しい。** exact Pegasus gate は qualification branch 内のみ [pipeline.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:546)。
6. **実測 6: 部分的。** explicit `None` 拒否テストが 0 件なのは正しいが、既存 coverage が monkeypatched 1 本だけという記述は偽。required contract の attestation order test がある [test_campaign.py:4127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:4127)。
7. **実測 7: floor 側は偽。** 最初の script write は line 30 の TMPDIR mkdir [floor_campaign.sh:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:29)。T126 line 75 は正しい。
8. **実測 8: 狭義の frozen manifest 非包含は正しいが、identity/trust-root 影響なしという一般化は偽。** exact frozen manifest は [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_frozen_artifacts.py:38)。

P5 の「login node で pytest 全走」も固定できない。raw pytest/build は禁止され、`tools/run_tests.py` がメモリにより local/dispatch を決める [AGENTS.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/AGENTS.md:31)、[AGENTS.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/AGENTS.md:39)。

提案:

brief の実測を「確認済み事実」「反証済み」「一般化不可」に分けて訂正する。P5 は `python3 tools/run_tests.py ...` と動的実行場所へ置換する。qsub を行わない境界は維持できる。

---

### 10. 変異 M1/M2 は帰属可能だが、中核リスクの変異が未登録

[severity: should-fix]

攻撃シナリオ:

- **M1:** OTHER site、他入力正常、`authorization_contract=None`。bypass を戻すと downstream legacy 経路に別の拒否はないため、M1 は単一理由で帰属できる。
- **M2:** compute site、Linux authorization と Linux runtime、selector=None。compute exact-Pegasus 条件だけを削除すると、一般 pipeline と heavy-work site gate は compute を許すため、M2 も単一理由で帰属できる。
- default 復活は explicit-None guard と過剰決定になるため、plan が登録から外した判断は妥当。
- production caller の keyword 削除は、必須 signature と AST inventory の双方が同じ入力を拒否する。kill を authorization body の証拠として数えられない。
- shell preflight の predicate 削除は後段 gate でも拒否されるため、最終 reject だけを見る変異では帰属不能。ただし「最初の write が発生しない」という観測なら単一理由化できる。

根拠:

- M1 定義と単一理由性主張 [s2-plan.md:246](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:246)。
- M2 定義 [s2-plan.md:260](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:260)。
- 過剰決定として除外した位置 [s2-plan.md:277](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s2-plan.md:277)。
- compute/OTHER は heavy-work gateで拒否されない [buildcache.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:441)。

提案:

実装後に少なくとも次を事前登録する。

- authorization/selector equality guard の削除
- selector exact type を `isinstance` に緩和
- `numactl is None` 拒否の削除
- screening/S1 の authorization capability 削除
- wrapper が helper の非 0 exit を無視する変異
- floor exact protocol-byte pin の削除

shell 変異は最終 reject でなく、write/driver-launch の有無を kill 観測点にする。

## 総括

(i) **must-fix は 8 件。**

1. P1/P2 の受理集合不変という親前提
2. authorization/selector の不一致・subclass・NUMA falsy bypass
3. `sanity_silo` の申告 NUMA と実 subprocess の不一致
4. authorization の WAL/proof-chain 非永続化と旧 COMMIT replay
5. screening/S1 等の残存 certified writer
6. required hardware attestation を行わない shell preflight
7. floor protocol の source-commit 非束縛・TOCTOU
8. T126 identity key-set 変更による未申告の受理縮小

(ii) **P1〜P5 の反証結果。**

- **P1:** 反証。直接配線は authorization 追加でなく build protocol 移行。
- **P2:** 反証。cache 状態により双方向の受理集合変化がある。
- **P3:** 反証。静的 material gate は作れるが、required attestation-before-write と protocol-byte binding は達成していない。
- **P4:** 部分反証。現行 frozen 23 bytes 不変は成立し得るが、DW-O10/identity 影響なしという一般化は偽。
- **P5:** 反証。raw pytest と login 固定は不可。`tools/run_tests.py` が実行場所を決める。qsub 不実施部分は維持可能。

(iii) **段 2 プランは NO-GO。** 二重 contract の整合性、ultimate writer 閉包、proof-chain 永続化、full attestation-before-write、protocol/identity の世代束縛を解決するまで実装へ進めない。dev-wave 段 3 の read-only 規律に従った静的レビューであり、テスト実走結果は含まない。