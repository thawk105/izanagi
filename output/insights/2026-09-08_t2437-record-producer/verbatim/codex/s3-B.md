## B-1: fixture の既存 WAL が正例を開始前に止める

**主張**  
計画の `case` fixture をそのまま使うと、各 physical root の `wal.jsonl` は既に canonical-list bytes で埋まっており、末尾 LF がない。そこへ `wal.log_trigger_binding()` で追記する段階で失敗する。

**根拠**  
fixture は list JSON を末尾 LF なしで作る [reflux_origin_fixture_builder.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_builder.py:688)。`case` はその bytes を `runs/wal.jsonl` へ配置し、projection も先に作る [test_reflux_formal_consumer.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:225)。production WAL writer は既存非空 file の末尾が LF でなければ拒否する [wal.py:1266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:1266)。record も同じ deterministic path に既に存在し、issuer を呼べば create-only で衝突する [reflux_result_evidence.py:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:385)。

**帰結**  
放置すると端から端 test は FC07 へ届かず、最初の WAL append、または record の O_EXCL で止まる。

**推奨**  
修正案。tmp fixture 内の旧 WAL、旧 projection、旧 result-record だけを明示的に除去してから production writer を呼ぶか、物理 materialization 前の fixture variant を作る。除去対象と順序を計画へ書く。

**確度**  
real 確定。

## B-2: salts は実在するが端から端では使われない

**主張**  
必要な authority/source digest、provenance、trigger、attempt、salts は builder の override API で差し替え可能であり、材料欠落はない。ただし計画の `map_result_evidence_to_sealed_member()` は prepared commitment と salt opening を迂回するため、到達点は「presealed fixture を読む formal consumer」であって ledger 端から端ではない。

**根拠**  
全 leaf override は [reflux_origin_fixture_builder.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_builder.py:163)、WAL/provenance/record builders は同:467,485,500、33 件の salts は同:559-604 にある。opened mapper は salts を受け取る一方、sealed mapper は受け取らない [reflux_result_evidence.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:772)。ledger 本体が prepared commitment を再計算して照合するのは [reflux_origin_ledger.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_origin_ledger.py:1450)。formal consumer は bound envelope bytes と sealed member 写像だけを検査する [reflux_formal_consumer.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:446), [同:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:856)。

**帰結**  
P6Unavailable 到達は示せるが、新 record digest と constraint が recovery salts で実際に開封可能だったとは示せない。

**推奨**  
採用。ただし test 名と説明を「formal-consumer contract integration」に限定し、salts は不変かつ未行使と明記する。ledger replay まで要求するなら別 scope へ送る。

**確度**  
real 確定。

## B-3: typed-only 入力が設計上の issuer へ届かない

**主張**  
P2 の `VerifyResult` 専用 API は、現行 production の最終化点から呼べない。`VerifyResult` は pipeline の局所値で、外へ返る `EvalResult` に保持されず、設計 §3.3 の issuer まで伝播しない。

**根拠**  
設計は issuer を terminal WAL と execution receipt を所有する `run_campaign()` 最終化点に置く [verbatim-design-s3.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-design-s3.md:36)。`EvalResult` には `VerifyResult` がない [pipeline.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:289)。実値 `vr` は verifier 呼出しから abort payload 作成までの局所値である [pipeline.py:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1557)。`OriginProducerInputs` は既成 record bytes を要求するだけで [p3_autonomous_workload_trial.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/p3_autonomous_workload_trial.py:462)、構築 hit は test の [test_p3_autonomous_workload_trial.py:10899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_p3_autonomous_workload_trial.py:10899) だけだった。

**帰結**  
成果物は production module 内の未使用 library API で止まり、「production producer」は成立しない。

**推奨**  
修正案。段 4 で、成果物を明確に「producer core API」と格下げして production 配線を carry するか、`VerifyResult` の保持と issuer 呼出しを scope 内へ戻すか裁定する。「裁定パッケージ候補なし」は撤回する。

**確度**  
real 確定。

## B-4: S3 は条件付きで逆関数になる

**主張**  
隔離された LF 終端の contiguous production frames なら、計画の境界式は consumer を通る。だが source WAL 全体の digest 採取後に追記されない保証は issuer 配線に依存し、本 wave 単独では production 実効性を確定できない。

**根拠**  
production writer は 1 frame + LF を追記する [wal.py:1266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:1266)。`ordered_attempt_frames()` の offsets は LF 込みで、payload の attempt を物理順に選ぶ [wal.py:1671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:1671)。consumer は frame 列を再 canonicalizeし、slice と records を exact 比較する [reflux_result_evidence.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:612)。source ref は file 全体の digest を後刻再検査する [同:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:475)。

通らない入力は A/B/A interleave、truncated tail、root-level にしか attempt ID がない非production frame、digest 採取後に追記された WAL である。前 3 件は fail-closed でよいが、最後は正当な production artifact を後刻拒否する。

**帰結**  
S3 単体 test は緑にできても、issuer 最終化保証なしでは production record の参照が安定しない。

**推奨**  
scope 外へ送る。S3 は production issuer と同じ carry に置くのが DW-G05 上最小である。残すなら、single-snapshot 読取、root-relative path、隣接性、truncated-tail 拒否、以後追記なしを明示的 precondition にする。

**確度**  
要実測。

## B-5: synthetic verifier 値は production へ一般化できない

**主張**  
brief の fixture 実測と production verifier は同じ束縛ではない。production では実 build に封印された source snapshot と commit witness が `integrity.clean()` を変えるため、synthetic test で到達する accepted/rejected 枝が production では発行拒否になる場合がある。

**根拠**  
test wrapper は合成 Silo sourceへ `protocol` と `ccbench_root` を固定する [test_verifier.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_verifier.py:41)。production は `genome`、`SourceEvidence`、`BuildAdmission` から exact compiled snapshot を検証する [core.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/core.py:199)うえ、`expected_commits` を渡す [pipeline.py:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/pipeline.py:1557)。X/P source evidence と commit witness は `Integrity.clean()` の必要条件である [model.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/model.py:450)。

cycle があれば verdict は引き続き `non-serializable` だが、source surface または commit witness が不一致なら `integrity.clean=False` となり producer は rejected record を発行しない。acyclic 側も `certified=False` へ変わる。

**帰結**  
fixture test は三分岐の synthetic 到達性だけを示し、production の accepted/rejected 到達性は示さない。

**推奨**  
修正案。test 名と主張を synthetic source 束縛へ限定する。production 到達性を成果に含めるなら、`verify_trace_dir_with_capability()` と exact build-bound snapshotを使う別 control が必要である。

**確度**  
real 確定。

## B-6: golden bytes と P1 は静的には閉じている

**主張**  
計画の編集面なら fixture builder、golden 4 値、baseline entry は変更不要で、P1 も consumer の source hash を壊さない。consumer に source-byte digest pin はなく、該当 test は AST の禁止構築走査である。

**根拠**  
golden は [test_reflux_result_evidence.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:24)、baseline の record digest/length は [reflux_origin_fixture_baseline.json:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_baseline.json:23)、独立再計算は [test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_origin_fixture_builder.py:107)。現行 digest 式は [reflux_formal_consumer.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1237)。source test は 15 files を AST parseして `OriginSealed(aborted=False)` 等を探すだけである [test_reflux_formal_consumer.py:2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:2088)。

**帰結**  
P1 により consumer file 自体の bytes は変わるが、record bytes、fixture baseline、受理集合の pin は変わらない。

**推奨**  
採用。shared helper は `ArtifactError` をそのまま wrapper へ伝え、既存 FC07 変換 test の monkeypatch owner だけを変える。実装後の byte diff 検査は必須。

**確度**  
real 確定。

## B-7: pin 閉包の記述に二つ不足がある

**主張**  
新 test file を作らない判断と ledger 追加は正しい。ただし pin 閉包の列挙には README を読むメタテストと、15 production file の AST scan が抜けている。

**根拠**  
既存 3 test file は pytest-only allowlist 登録済み [README.md:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/README.md:144)。登録を機械強制するのは [test_plain_runner_coverage.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_plain_runner_coverage.py:50)。coverage gate は実 collection の 90% [test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_acceptance_schedule_order.py:660)。既存 ledger block は [acceptance_duration_ledger.json:11780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/acceptance_duration_ledger.json:11780)。`git grep` では新関数名、新 nodeid は 0 件、現行 hit は private `_witness_class_sha256` だけだった。対象 test に `xdist_group` はなく、conftest に file/node 登録もない。role 名に相当する issuer pin は `trusted-physical-harness` のみ [reflux_result_evidence.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:64)。

**帰結**  
編集漏れは直ちに生じないが、計画の「全 pin」主張は不完全で、レビュー時に二つの既存 gate を見落とす。

**推奨**  
修正案。`test_plain_runner_coverage` と `test_consumer_source_has_no_nonaborted_construction_or_success_variant` を pin checklist に追加する。新 xdist group、role、gate、別台帳は足さない。既存の stale `wrong-version` entry も本 wave では触らない。

**確度**  
real 確定。

## 総括

real 確定は 6 件、要実測は 1 件。  
最重所見は B-3 の typed `VerifyResult` が設計上の production issuer へ届かない点である。  
S1/S2 の standalone producer core と bytes 不変方針は支持する。  
現行プラン全体は支持しない。B-1 と B-3 を修正し、S3 は issuer 配線と同じ scope 外へ送るべきである。  
test は実行しておらず、以上は静的検査結果である。