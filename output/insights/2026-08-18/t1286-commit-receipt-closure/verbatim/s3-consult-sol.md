## 総括

**NO-GO。** 批准 JSONL は自己批准可能で、receipt の verifier 由来性と layout 横断 single-use も成立していない。  
さらに final closure 20 から新しい receipt gate の実装面が漏れ、T-762 の負対照は現行検査だけでも落ちる恒真テストになり得る。  
以下は read-only 静的検査結果であり、pytest は実走していない。

### [A-1] T-1287 の JSONL 台帳は自己批准を防げない

- 分類: real
- 場所: [s2-plan.md:264](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:264)、[hooks/README.md:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/hooks/README.md:150)、[decisions.md:13168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/docs/decisions.md:13168)、[decisions.md:17328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/docs/decisions.md:17328)
- 攻撃: closure を弱化し、その新 digest を同じ主体が `hooks/enforcement-source-closure-ratifications.v1.jsonl` に追記して commit すれば、strict-prefix 履歴検査を含めすべて自己整合して新 lock が通る。hook は誤操作抑止であって認証ではなく、D287 は同一主体が書ける approval JSON を明示的に却下し、D414 も repo 内 JSON を authority と認めていない。
- 成果物影響: 弱化済み closure が `ratified` と記録され、その digest を持つ新 campaign.lock・認証レポート・後続 certified 選択が正規品として受理される。
- 最小修正: 台帳データを closure 外に置く判断自体は自己参照回避として正しいが、authority は AI が変更できない外部 trust root とし、その検証鍵だけを closure 内へ pin すること。用意できなければ批准値を未設定のまま fail-closed にし、T-1287 の機械保証を land せずユーザー裁定へ戻すこと。

### [A-2] 「exact 20 closure」から新しい enforcement source が漏れている

- 分類: real
- 場所: [s2-plan.md:320](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:320)、[s2-plan.md:402](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:402)、[campaign_lock.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/campaign_lock.py:29)
- 攻撃: final 20 は現行 14・S8C 3・批准自己保護 3 だけで、段 B が実際に信頼する `guided.py`、`replay.py`、`qualification/artifacts.py`、`t126_driver.py`、新 receipt issuer/schema module を含まない。これらで source proof や qualification lock binding を弱化しても、批准対象 digest は変わらない。
- 成果物影響: campaign.lock 上の closure digest を変えずに、guided/qualification の偽 receipt から certified COMMIT と評価台帳を生成できる。
- 最小修正: [s2-plan.md:320](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:320) の exact 集合を、receipt の発行・検証・source-proof 解決・qualification binding に実際に関与する production dependency から再導出し、少なくとも段 B の上記実装面と新 issuer module を追加する。

### [A-3] 束縛する値は正しいが、receipt は verifier-issued になっていない

- 分類: plausible
- 場所: [model.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/model.py:170)、[model.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/model.py:203)、[model.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/model.py:217)、[core.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/verifier/core.py:141)、[s2-plan.md:147](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:147)、[s2-plan.md:179](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:179)
- 攻撃: 権威ある値が `VerifyResult.verdict` と `VerifyResult.certified` である点は正しいが、計画では caller である `pipeline.py` が deterministic JSON/hash を組み立て、in-memory `CommitReceipt` も「可能なら」に留まる。`VerifyResult` は public mutable dataclass であり、低層 writer は `{verdict:"serializable", certified:true, verifier_result_sha256:<自己整合hash>}` が本当に `verify_trace_dir` から出たか判別できない。なお [pipeline.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/pipeline.py:1235) の `res.certified=True` は明確に非権威であり、receipt 入力にしてはならない。
- 成果物影響: 実 verifier が indeterminate/non-serializable でも、caller 製の自己整合 evidence により COMMIT・qualification event・certified report が緑になる。
- 最小修正: issuer を verifier entrypoint 内へ置き、trace、expected commits、workload、binary/build attempt を実検証した同じ呼出しから PID/process-seal 付き capability を返すことを必須化する。`wal.append` と qualification sink は直列化 dict/hash だけでは受理せず、全 pass の capability と payload 対応を検査する。

### [A-4] single-use は WAL/event-file ごとであり、layout 横断では破れる

- 分類: real
- 場所: [s2-plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:188)、[s2-plan.md:196](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:196)、[layout.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/layout.py:168)、[layout.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/layout.py:222)、[artifacts.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/qualification/artifacts.py:768)
- 攻撃: 同じ campaign.lock bytes を任意の 2 `CampaignLayout.root` へ置けば、両 WAL の消費済み集合は空なので同じ receipt が各 1 回通る。fork 後の親子も別 layout/event file なら同様である。qualification receipt は `qualification_attempt_id`、`round_index`、`member_role`、`event_index` を core に含めず、消費集合も member event JSONL ごとなので別 role/file へ移植できる。
- 成果物影響: 同一 receipt ID が複数の COMMIT/evaluation record を認証し、評価回数・member 成績・certified 選択が二重計上される。
- 最小修正: P2 を撤回して全 eligible sink が共有する原子的な consumption registry を置くか、AI が複製できない ledger-instance authority を導入すること。qualification は少なくとも attempt-level 共通 flock/集合を使い、attempt・round・role・event index を receipt に束縛する。外部状態を拒むなら「全 layout 横断の一回限り」は証明できないため再裁定が必要。

### [A-5] 受理集合は実際に変わるが、各差分を production sink で固定する必要がある

- 分類: real
- 場所: [wal.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:379)、[artifacts.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/qualification/artifacts.py:749)、[s2-plan.md:353](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:353)
- 攻撃: 現在は (1) v1 lock 下の receiptless `WalRecord(STAGE_COMMIT)`、(2) receiptless qualification `emit(STAGE_COMMIT)`、(3) 未批准 closure からの新 v2 lock、(4) serial-1 の registry 整合だが calibration artifact が壊れた activation を `ident` から読む入力が通り得る。実装後はいずれも拒否対象なので、受理集合差分は存在する。一方、producer が常に receipt を発行した後に producer だけを呼ぶ「receipt 無し」テストは恒真になる。
- 成果物影響: production sink を直接駆動する負対照が無ければ、receipt 要求を producer 側だけから削除してもテストが緑のままになり、receiptless COMMIT が再受理される。
- 最小修正: 計画済みの direct `wal.append` 負対照を保持し、qualification も実 `QualificationEventSink.emit` へ receipt を渡さず event bytes 不変を確認する。T-1287 は批准済み正例を先に成立させてから closure だけを変える負例を置き、単なる「台帳が空だから全部拒否」で済ませない。

### [A-6] T-762 の既存 serial-2 fixture は経由化の負対照にならない

- 分類: real
- 場所: [env_contract_activation.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract_activation.py:400)、[env_contract.py:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/env_contract.py:631)、[ident.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:211)、[ident.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:294)、[test_env_contract_activation.py:1952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/tests/test_env_contract_activation.py:1952)、[s2-plan.md:357](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:357)
- 攻撃: 親 brief の「4 検査をすべて素通り」は実行経路としては正しいが、直接 validator も全 row の catalog 交差検査を行い、serial-2 の変更 row には既に calibration callback を実行する。実際、既存 `test_ident_*serial2_fires_artifact_admission` は wave 前の直接呼出しでも赤になるため、その fixture を新 wrapper test に流用しても経由化の検出力を示さない。差分が出るのは successor callback が呼ばれない serial-1、または後続 record で不変の terminal row である。
- 成果物影響: 直接呼出しへ戻す変異が生存したまま、初期 active contract の未検証 calibration が新 lock authority や歴史 lock の対象 contract として受理される。
- 最小修正: serial-1 の catalog/hash は整合するが calibration blob が壊れた fixtureを作り、「現行 direct は通る／新 wrapper は拒否」を固定する。current wrapper は `_verify_entry_calibration`・terminal registry 再照合・`_VERIFIED_CONTRACT_SHA256S` 更新・PID/fork cache を全て保持する。

### [A-7] historical activation は current head と prefix の二重検証が必要

- 分類: plausible
- 場所: [ident.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:294)、[ident.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:303)、[s2-plan.md:400](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:400)
- 攻撃: `verify_recorded_activation_tuple` はまず current chain head 全体を検証し、その後 `records[:authority.activation_serial]` を記録済み serial/hash に対して検証する。計画は current/historical wrapper を分けるとだけ書き、historical の exact 契約を固定していない。head wrapper を prefix にそのまま使えば正当な旧 v2 lock を拒否し、prefix wrapper だけに置換すれば不正な current suffix/head を見逃す。
- 成果物影響: 過去 lock の replay/recovery が誤拒否されるか、現在の activation head が壊れていても recorded prefix だけを根拠に certified admission が通る。
- 最小修正: `ident.py:294` は full-current verified wrapper、`ident.py:303` は `(activation_serial, activation_state_sha256)` を取る historical-prefix wrapperへ別々に置換し、current serial-2／recorded serial-1 の正例、不正 current suffix、不正 prefix の三対照を固定する。

### [A-8] `guided.py:141` は `cmd_evaluate` 経路で実際に無防備である

- 分類: real
- 場所: [guided.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/guided.py:131)、[guided.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/guided.py:141)、[guided.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/guided.py:187)、[guided.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/guided.py:196)、[replay.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/replay.py:181)、[replay.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/replay.py:200)
- 攻撃: `cmd_start` は `assert_complete` を呼ぶが、`cmd_evaluate` は landscape を再読込して直接 `_log_eval` へ渡す。`load_landscape` は最後の VERIFY_DONE を単なる `bool` に潰し、`_log_eval` は `certified=False` でも `"unknown"` VERIFY_DONE の直後に必ず COMMIT する。tracked P2-2 WAL の現物は全 genome green なので現在データでは発火しないが、親の「上流 assertion が全経路を守る」という一般化は誤りである。
- 成果物影響: 未認証 genome が guided WAL の COMMIT・評価済み集合・trial result に入り、後続選択が certified 結果として扱う。
- 最小修正: bare `GenomeResult.certified` を authority とせず、`_log_eval` 自身で immutable source receipt/evidence を要求する。`cmd_evaluate` にも complete/source-proof 検査を置き、false verifier result を実 source view から流す負対照を追加する。

### [A-9] 変異事前登録がなく、提案負対照の帰属も一部成立しない

- 分類: real
- 場所: [brief.md:63](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/brief.md:63)、[s2-plan.md:351](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:351)、[s2-plan.md:376](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:376)、[contract_loader_binding.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/contract_loader_binding.py:324)、[ident.py:470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/ident.py:470)
- 攻撃: plan §7 はテスト一覧であり、brief が要求した mutation→killer nodeid→帰属の事前登録表が無い。`ident.py`、`wal.py`、`campaign_lock.py` の未 commit 変異は closure blob drift で semantic gate より先に落ち得る。特に `ident` を旧 direct call へ戻す変異は、新 lock testでは `ident.py:470` の loader-binding capture が先に失敗する。また既存 serial-2 calibration test は direct call の時点で既に落ち、`wal.log` だけを数える AST gate の変更は production 緩和ですらない。
- 成果物影響: generic drift/schema failureを新 gate の検出力として誤計上し、receipt・wrapper・批准比較を外しても専用 killer が無い状態で land する。
- 最小修正: 実装前に各変異へ専用 nodeid と期待する最初の失敗を登録し、隔離実行では closure pin/批准を意図的に再固定して semantic failure まで到達させる。wave 前の形として「receipt 検査なし／v2 内限定」「wal.log 2 箇所 census」「ident direct current/prefix」「old exact-14」を明記する。

### [A-10] repo-wide lock は 32 件であり、v2 read gate の live witness は 0 件

- 分類: real
- 場所: [brief.md:30](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/brief.md:30)、[s2-plan.md:216](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:216)、[wal.py:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:1054)、[frozen campaign.lock 1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/campaign-layout/campaigns/p3-t178-ycsb-a-workload-conditioned-autonomous-0a11751c/campaign.lock:1)
- 攻撃: `git ls-files '*campaign.lock'` では `output/campaigns` 30 件に frozen insight 2 件を加えた 32 件で、全件 v1、v2/authority は 0 件だった。2 frozen layout には WAL が無く report だけがある。したがって `wal.py:1054` や recorded-activation の v2 read branch は live artifact では一度も発火しない。一方、plan は receipt を version 分岐外、批准を新 lock encode 前に置くため、T-1286/T-1287 全体が恒真という攻撃は反証される。
- 成果物影響: 30 件だけを repo 全体と扱うと frozen report の参照検査を漏らし、逆に 32 件すべてを replay 対象と扱うと存在しない WAL の互換性を誤報する。
- 最小修正: inventory を「WAL を持つ live campaign 30／lock-only frozen snapshot 2／計32、全 v1」と固定し、legacy replay は前者、参照整合は全32で検査する。T-1287 は v2 不在を無害化理由にせず、新 lock construction の synthetic 負対照で発火させる。

### [A-11] 同一 WAL 内の retry/replay/recovery については攻撃不成立

- 分類: refuted
- 場所: [s2-plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:188)、[wal.py:398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:398)、[wal.py:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:1106)、[wal.py:1170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:1170)、[wal.py:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/wal.py:1370)
- 攻撃: 同じ WAL へ親子 process／再試行が同時 append しても、計画どおり flock 内で全既存 receipt ID を走査すれば一方だけが勝つ。fsync 後の誤再試行も既存 COMMIT を見る。現行 topology も duplicate attempt ID と同 attempt の二重 COMMIT を拒否し、recovery は `_append_records_locked` から ABORT だけを追記するため receipt を再消費しない。
- 成果物影響: 同一 WAL 内では COMMIT 数と消費済み receipt 集合は増殖せず、残る破れは A-4 の別 ledger/layout 間に限定される。
- 最小修正: 設計を維持し、実 fork 二 writer、fsync 後 retry、tail repair、recovery 二回の各テストで「COMMIT/receipt ID は1件」を固定する。

### [A-12] T-1252 の S8C exact 3 module 導出は反証できない

- 分類: refuted
- 場所: [s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/wave-t1286-commit-receipt/out/s2-plan.md:299)、[s8c_preregistration.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/s8c_preregistration.py:40)、[s8c_preregistration_evidence.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/s8c_preregistration_evidence.py:18)、[s8c_generation_projection.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1286-commit-receipt/orchestrator/campaign/s8c_generation_projection.py:1)
- 攻撃: core が権威的に core/evaluator/projection の3 pathを定義し、evaluator の project-local import は core、projection は stdlib leaf である。親候補の `s8b_oracle_judge.py` は S8B 側から使われる別判定器で、S8C closure に含める根拠はない。3 module のいずれかだけを変更すれば旧14は通り、拡張 closure は拒否する実入力も作れる。
- 成果物影響: plan の exact 3 を維持すれば S8C 判定器差替えで lock closure digest が変わり、無関係な S8B 編集による偽失効は起きない。
- 最小修正: exact 3 は維持し、定数から再導出する pin と各1 module差替えの負対照を置く。ただし A-2 の receipt enforcement source 漏れは別途修正する。