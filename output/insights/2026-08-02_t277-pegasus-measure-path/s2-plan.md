## 変更計画

### 実装単位 A — buildcache / pipeline / loop

- `orchestrator/campaign/buildcache.py:118`
  - `site_policy.PEGASUS_COMPUTE` の明示入力だけを `("gcc", "g++")` に、それ以外と `site=None` を既存 `DEFAULT_CC/CXX=("gcc-13","g++-13")` に解決する helper を追加する。
  - `site=None` で実環境を自動反映すると既存 floor/oracle/T126 の compiler が変わるため行わない。

- `orchestrator/campaign/buildcache.py:172-216`
  - `_toolchain_manifest` の signature/schema は変えない。選択済み `cc/cxx` と CMake の realpath・version を既に記録しており、site/prefix は tool そのものではなく別の build input だからである。

- `orchestrator/campaign/buildcache.py:219-234`
  - `_v2_identity(..., *, site: str, dependency_prefix: str)` とし、完全解決済み site と、実際に configure へ渡す canonical `CMAKE_PREFIX_PATH` 文字列を pre-image に常時追加する。空 prefix も `""` として入れる。
  - contract は既に `cache_root/contracts/<contract_sha256>/<digest>` という namespace に束縛される (`:458-475`) ため、digest pre-image へ重複追加しない。
  - legacy `cache_key` (`:121-135`) は一切変更しない。

- `orchestrator/campaign/buildcache.py:347-383`
  - `_v2_commands` に末尾 keyword `dependency_prefix: str = ""` を追加し、非空時だけ単一 argv `-DCMAKE_PREFIX_PATH=<prefix>` を configure argv へ挿入する。
  - `_v2_result` にも同じ prefix、pre-image、digest を渡し、cache hit 時に再構成される argv が fresh build と一致するようにする。

- `orchestrator/campaign/buildcache.py:138-155, 368-383`
  - `/scr` 消去後にも build identity が残るよう、`BuildResult` に additive default 付きで full digest と canonical pre-image/toolchain record を返す面を追加する。legacy `build()` は `None` のままにする。

- `orchestrator/campaign/buildcache.py:423-590`
  - `build_v2` の末尾に `dependency_prefix: str = ""` を追加する。既存必須引数や positional 受理集合は変えない。
  - prefix は exact `str`、NUL なしとして検証し、driver が canonical 化した文字列をそのまま identity と argv の双方へ使う。ambient `os.environ["CMAKE_PREFIX_PATH"]` は読まない。
  - `_v2_identity` には `_resolve_site(site)` の結果を渡す。これにより既存 v2 digest は全件一度変わるが、旧 entry と衝突せず cold miss になる。
  - cache hit/fresh の両 `_v2_result` (`:500-503`, `:588-590`) と fresh configure (`:516-518`) に同じ prefix/site を通す。

- `orchestrator/campaign/pipeline.py:418-455`
  - 既存末尾の後へ `site: Optional[str] = None`、`dependency_prefix: str = ""` を追加する。既存 `env_contract=None` (`:429`) は維持する。
  - default 時は新 keyword を `build_v2` へ渡さない条件分岐にし、s8b/T126 の呼出し形・compiler・configure argvを維持する。

- `orchestrator/campaign/pipeline.py:526-529`
  - `src_token is None` かつ明示 site がある場合、buildcache の site compiler helper で選んだ `cxx` を `source_digest.resolve` へ渡す。
  - `source_digest.resolve` の既定は `g++-13` (`orchestrator/campaign/source_digest.py:701-702`) なので、この修正なしでは build 前の identity 計算で Pegasus が停止する。

- `orchestrator/campaign/pipeline.py:559-597`
  - `env_contract is None` の legacy 分岐は完全に維持する。
  - v2 分岐では明示 site から compiler を選択し、trace/perf の両 `build_v2` に同一 `site`・`dependency_prefix` を渡す。
  - `site=None` の既存 v2 caller は現在どおり `DEFAULT_CC/CXX` を使い、`build_v2` 自身が実 site を identity/gate 用に解決する。
  - 明示 site を受けた新 P3 経路だけ、`STAGE_BUILD_DONE` (`:606-611`) に full digest、site、prefix、toolchain/pre-imageを additive に記録する。これにより `/scr` 上の completion manifest が消えても proof が残る。

- `orchestrator/campaign/loop.py:43-50`
  - `run_campaign` の末尾に `env_contract=None`, `site=None`, `dependency_prefix=""` を追加する。
  - default の三値では既存 `evaluate` 呼出しに新 keyword を足さない。これが `p3_s4_loop.py`、sort、OTHER legacy caller を不変にする最小配置である。

- `orchestrator/campaign/loop.py:103-105`
  - 明示 site 時だけ site compiler の `cxx` を `source_digest.resolve` に渡す。未指定時は従来の3引数呼出しを維持する。

- `orchestrator/campaign/loop.py:136-140`
  - 非 default の `env_contract/site/dependency_prefix` だけを `evaluate` へ通す。Pegasus trigger driver は3値を明示し、OTHER と既存 caller は従来形のままになる。

### 実装単位 B — trigger-gating driver / 8c

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:54-79`
  - `env_attestation`、`campaign_claim`、`reservation` を既存 leaf API として追加 import する。
  - `ENV_TAG="linux-baremetal"` は OTHER の legacy selector として残す。site→tag の閉じた対応を `{OTHER: ENV_TAG, PEGASUS_COMPUTE: "pegasus"}` として追加し、環境変数 override は作らない。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:277-298`
  - `_site_admits_measurement(site)` を `OTHER` と `PEGASUS_COMPUTE` の exact set にする。LOGIN/SUSPECT/未知値は拒否する。
  - 最小の signature 変更は `_admit_env_contract(site: str)` である。内部で `_current_site()` を再読せず、admission 後に上記対応の tagを `_lookup` する。
  - `_record_diff_reject_admitted` と `_quarantine_and_audit` に解決済み site を渡す。compute の diff/syntax/auditor reject は `pegasus` tag で記録するが、実測が無いため attestation は発火させない。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:384-418`
  - `run_one_iteration` に末尾 keyword-only で `site`, `dependency_prefix`, `measurement_lease` を追加し、site は iteration ごとに一度だけ解決する。
  - cleanかつ `do_build=True` の分岐 (`:411-418`) だけで contract を解決する。OTHER は `env_contract=None` のまま `run_campaign` へ渡し、legacy build を維持する。
  - PEGASUS_COMPUTE は exact Pegasus contract、site、prefixを `run_campaign` へ渡して v2 を選択する。
  - required contract では、`env_attestation.load_verified_calibration` (`env_attestation.py:643-710`) → `execution_guard.attest_and_build_receipt` (`execution_guard.py:276-338`) → `receipt_matches_contract` (`:88-155`) の順に、`run_campaign` 直前で毎回発火させる。
  - `_admit_env_contract` 内では発火させない。そうすると reject/no-build まで hardware probe を要求してしまう。
  - receipt は計測開始前に provenance の iteration recordへ atomic 保存し、後段 entry 更新でも消えない merge 方式にする。attestation失敗・receipt再検算失敗では `run_campaign` と WAL build stage に到達させない。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:185-272, 468-518`
  - provenance entry 更新を field merge にし、先に書いた execution receiptを post-run の outcome追記で消さない。
  - `drive_iteration` に同じ trailing keywordを追加して `run_one_iteration` へ通す。
  - required contract では、campaign id・現 PID/starttime・reservation binding と一致する acquire済み lease以外を拒否する。

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:538-637`
  - build 時だけ siteを先に解決し、compute では外部 dependency prefixを必須にする。
  - prefix は `;` 区切りの既存 absolute directory群として canonical化し、空要素、symlink escape、`:` を含む path、`/scr` 外を拒否する。
  - `$PBS_JOBID` を `tools/pegasus/certify_calibration.sh:15-22` と同じ文法で検証し、`:` を `_` に変換してから `tempfile.mkdtemp(dir="/scr", prefix=...)` で mode 0700 の fresh cache rootを作る。`--no-build` と OTHER はこの処理を通さない。
  - compute の persistent claim root は campaign rootの兄弟 `claims/` とし、事前 provision済み・非 symlinkを要求する。driverは作成も削除もしない。
  - `reservation.read_binding/check_reservation` で PBS job/host/boot/deadlineを検証し、`campaign_claim.acquire_claim` (`campaign_claim.py:167-227`) を checkout、provider、WALより前に取得する。claimは releaseしない。
  - acquire後に既存 loop stateがあれば `allow_resume=False` として拒否する。同一 process内の後続呼出しだけは同じ leaseを再利用できる。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:651-710, 761-987`
  - `site/dependency_prefix/cache_root/measurement_lease` を `_finish_trial` → `_run_workload` → `trigger.drive_iteration` へ通す。
  - `_run_workload` は cfg/layout算出直後、最初の provider呼出し (`:826`) より前に campaign claimを取得する。
  - `_assert_fresh_campaign_state` (`:196-206`, 呼出し `:779-784`) は残し、claimを先に取ることで D106 が残した freshness TOCTOU (`docs/decisions.md:4882-4890`) を閉じる。
  - receiptの実プローブは 8c 起動時ではなく、各 clean proposalが実測へ進む直前の trigger側に置く。oracle の schedule-row 再検査 (`s8b_oracle_driver.py:915-938`) と同じ鮮度になる。
  - claim record、contract SHA、site、各 generation receiptを attempts journal/reportへ残す。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:990-1075`
  - `run_trial` に trailing default付きの site/prefix/cache/claim関連引数を追加する。`do_build=False` の既存 programmatic testは無変更。
  - `run_root` create-only (`:1017-1024`) は維持する。required contractで claim/reservationが無い場合は artifact作成前に拒否する。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1090-1147`
  - build CLIで site、prefix、reservation、fresh `/scr` cacheを準備して `run_trial` へ渡す。
  - OTHER の `fixed_sub/build-variants` (`:1133-1134`) と no-build の空 cache (`:1121-1124`) は維持する。

- `orchestrator/campaign/p3_s4_loop.py:655-656` と `orchestrator/campaign/p3_s4_loop_sort.py:233-234`
  - 変更しない。両 driver は新しい末尾引数を省略するため `run_campaign(env_contract=None, site=None, dependency_prefix="")` となり、legacy build、固定 ENV_TAG/CLK/NUMA、既存 cache namespaceをそのまま使う。

- `orchestrator/campaign/env_contract.py:169-193`、`env_attestation.py:390-425,643-710`、`execution_guard.py:88-155,276-338`、`campaign_claim.py:33-68,167-227`、`reservation.py:159-277`
  - 変更しない。登録 contract SHA、attestation schema、claim/reservation APIを既存のまま再利用する。

- `docs/decisions.md:4269-4296`（実装単位 B、本文は親担当）
  - D96に従い新 D を同一変更単位へ追加する。
  - 記載要点は、exact受理集合、site→contract対応、OTHER legacy不変、computeのv2/prefix/site identity、required attestation、one-shot claim/no-resume、fresh `/scr`、全v2 cache cold化、却下案（allow-all、env override、legacy key拡張、ambient prefix、Pegasus契約の緩和）である。
  - D108との関係を「supersedeするのか、trigger workerだけを開いて8c supervisorは未開放なのか」明記する。

## 新設・更新するテスト

### 実装単位 A

- `orchestrator/tests/test_buildcache_v2.py:64-102`
  - helperに deterministic site/prefixを追加し、明示 siteテスト用 fake `_run` が `site=` を受けられるようにする。

- `orchestrator/tests/test_buildcache_v2.py:205-241`
  - 同一入力で同一 digest、siteだけ変更、prefixだけ変更、compiler/tool version変更の各々で期待どおり hit/missになることを独立固定する。
  - 現行テストは toolchain versionしか identity差を検出せず、site/prefix欠落を検出できない。

- `orchestrator/tests/test_buildcache_v2.py:357-376`
  - exact pre-image期待値に `site` と `dependency_prefix` を追加する。
  - configure argvに非空 prefixがちょうど1 token入り、空 defaultでは入らないことも固定する。

- `orchestrator/tests/test_build_site_gate.py:72-130,196-210`
  - site compiler helper、site/prefix付き `_v2_commands`、実 `_run` への site伝播を固定する。

- `orchestrator/tests/test_build_site_gate.py:281-289`
  - OTHERで作った v2 entryを LOGINからhitできるという現期待は破棄する。同一 siteのhitは `_run` を呼ばず、別siteはmissとなりLOGIN gateが subprocess前に拒否することへ変更する。

- `orchestrator/tests/test_build_site_gate.py:292-332`
  - legacyではsiteがidentity外である既存性質を残す一方、v2はsiteがidentityに入る期待へ変更する。
  - jobsがidentity外という検査は、同一compute siteで affinity値だけ変えてhitする形に分離する。

- `orchestrator/tests/test_campaign.py:1283-1301,1399-1427`
  - v2 fakeに新引数の記録面を足し、明示compute時に trace/perf双方へ Pegasus contract、site、prefix、`gcc/g++` が渡ることを固定する。
  - env_contractのみの既存 v2 opt-inは、site/prefix省略時に従来 compiler/argvを保つ negative controlにする。

- `orchestrator/tests/test_campaign.py:2460-2526`
  - loop→evaluateの contract/site/prefix伝播と、compute時の `source_digest.resolve(..., cxx="g++")` を追加検査する。
  - default呼出しでは新 keywordを渡さず legacy形を保つことも固定する。

### 実装単位 B

`orchestrator/tests/test_p3_s4_loop_trigger_gating.py` の admission境界は次をすべて更新する。

| 現行行 | 更新内容 |
|---|---|
| `:107-125` | `ENV_TAG` がOTHER fallbackとして残ることを維持する。 |
| `:156-188` | `_admit_env_contract(site)` と閉じたsite→tag lookupのexact ASTへ更新する。 |
| `:191-236` | `_current_site` の解決位置と新selector名のscope/countを更新する。 |
| `:244-311` | measurement spyでenv_contract/site/prefix/receipt順序を観測する。 |
| `:314-357` | compute rejectはPegasus tagで記録するがattestation/buildを呼ばないことを固定する。 |
| `:362-369` | `OTHER=True`, `COMPUTE=True`, `LOGIN=False`, `SUSPECT=False` のexact matrixへ変更する。 |
| `:372-431` | OTHERがENV_TAGをlookupし、legacy引数・attestationなしを維持する。 |
| `:434-475` | compute cleanはrequired attestation後にv2へ到達し、compute rejectは拒否でなくtag付き記録になるよう変更する。 |
| `:478-529` | default compute seamが `"pegasus"` lookupへ到達することを固定する。 |
| `:532-634` | import時に束縛したsite/lookup seamでもOTHERとcomputeの対応がdriftしないことを固定する。 |
| `:637-665` | compute clean `--no-build` はlookup・attestation・claim・`/scr`作成を全て行わないことを維持する。 |
| `:668-757` | LOGIN/SUSPECT許可、compute→Linux契約、ambient env override、attestation bypassを各mutationとして赤にする。 |
| `:910-981` | pre-run receiptがpost-run provenance mergeでも消えず、receipt SHA/contract/siteが残ることを追加する。 |
| `:1028-1132` | computeの既存state、claim衝突、別process resumeをprovider/build前に拒否する境界を追加する。 |

- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:450-460`
  - required calibration load、production probe、receipt再検算、run_campaignの厳密な順序を固定する。probe失敗・比較不一致・receipt改変では campaign/WAL が空であることを検査する。

- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:817-838`
  - grep上の追加候補だが `_quarantine_and_audit(write=False)` 単体でありmeasurement admissionを通らないため、期待値変更は不要。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:34-52`
  - `_fake_drive` に新しい末尾keywordを受ける面を足す。no-build既存試験では値がdefaultであることを確認する。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:291-457`
  - 既存 freshness拒否を残し、claim取得後・provider前に発火すること、同じcampaign claimの第二processが拒否されることを追加する。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:164-215,460-539`
  - no-build reportは従来どおり完結すること、required buildではcontract/site/claim/receiptがjournalとreportに束縛されることを固定する。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:578-673`
  - LOGIN/SUSPECTがcheckout/cache作成前に拒否されること、computeではprefix/reservation/claimを必須とすること、OTHER/no-buildの既存CLI受理を維持することを追加する。

- `/scr` helperには、raw PBS job idの`:`置換、unsafe job id拒否、atomic fresh作成、既存namespace非再利用、OTHER/no-buildで未作成、prefixの`:``/scr`外/不存在拒否を独立テストする。

- repo-wide grepでは `_site_admits_measurement` / `_admit_env_contract` の直接境界は `test_p3_s4_loop_trigger_gating.py` だけだった。`orchestrator/tests/test_p3_s4_loop.py:166-168` は `TRIGGER_LOOP.ENV_TAG` の存在確認のみで、ENV_TAGを残すため更新不要である。

- `orchestrator/tests/test_frozen_artifacts.py:38-85,125-153` は更新しない。回帰実行対象には含めるが、今回の計画調査ではテストを一件も実行していない。

## 波及と互換

- OTHER/legacy callerは、`env_contract=None`, `site=None`, `dependency_prefix=""` の末尾defaultと条件付きforwardingにより呼出し形まで維持する。対象には `backoff_sweep.py:144`、`demo.py:50-57`、`p3_s4_loop.py:655-656`、`p3_s4_loop_sort.py:233-234`、`s6_sort_sweep.py:325`、`p3_kickoff.py:99-103` 等がある。

- floorは `s8b_floor_campaign.py:975-981` で `build_v2` を直接呼び、pinするのは `contract_sha256` (`:982-986`) と、成果物へ射影するbinary SHA/configure argv/build argv (`:1004-1018`) である。full build digestはpinしていない。

- ratified floor成果物のexact keysは `s8b_ratified_freeze.py:181-185` で、binary SHAとargvは検査するがfull digestは含まない (`:1633-1667`)。

- oracleは `s8b_oracle_driver.py:1334-1361` で `evaluate(env_contract=...)` を呼び、floor由来perf binary SHAを `expected_perf_sha256` としてpinする。build contract wrapperが見るのは `BuildResult.contract_sha256` だけ (`:941-958`)。full digestはpinしていない。

- T126は `qualification/t126_driver.py:519-540` でenv contract/cache rootを渡すが、full digestは保存しない。別系列のtoolchain manifestとseries identityを `:793-844,870-879` でpinしており、buildcache digestとは別物である。

- `rg full_build_digest` のproduction/test出現は `buildcache.py:299-312,560` だけで、consumer側のgolden pinは無い。

- したがって全既存v2 consumerで一度cold missになるが、壊れる凍結成果物は無い。旧cache entryは上書きされず孤立して残る。確実に期待修正が必要なのは `test_buildcache_v2.py:357-376` と、siteがidentity外であることを固定している `test_build_site_gate.py:281-332` である。

- cold rebuild後のbinary bytesが既存oracle pinと異なれば、oracle store検査 (`s8b_oracle_driver.py:824-835`) またはpipelineの期待SHA gate (`pipeline.py:621-630`) が安全側に拒否する。凍結bytesを書き換える対処はしない。

- `test_frozen_artifacts.py:38-85` の23件にはbuildcache completion manifestやfull digestが無いため更新不要である。

- compute cacheはdriverが `/scr` 直下にfresh作成し、schedulerがjob終了時に削除する。既存作法は `certify_calibration.sh:24-31,771-774`、runbookは `/scr` をjob-local・終了時削除と定める (`docs/pegasus-runbook.md:228-238`)。

- `/scr` へ置くのはv2 cache、staging、build binary、外部wrapperが作ったgflags/glog installなど再生成可能な中間物だけとする。WAL、loop state、provenance、attestation receipt、claim、attempt journal、report、失敗理由は永続repo/output側へ置く。

- `$PBS_JOBID` の `:` は必ず `_` に変換する。根拠は `docs/pegasus-runbook.md:366-370` と `certify_calibration.sh:24-31` である。

## 親 brief への反論

- **P1: 同意。** `pipeline.evaluate` には既に `env_contract` opt-inと明示的なlegacy/v2分岐がある (`pipeline.py:453-455,559-597`)。legacy `cache_key` を拡張するより、Pegasusだけv2へroutingする方が既存OTHERを守れる。

- **P2: 同意。** exact受理集合は `{OTHER, PEGASUS_COMPUTE}` とし、LOGIN/SUSPECTを拒否する。`buildcache._run` の重処理gateも維持する。

- **P3: 条件付きで反対。** calibration scriptはsystem compiler・prefixによるCCBench buildの生死を示す (`certify_calibration.sh:494-517`) が、新しいv2 routing、site/prefix identity、attestation、claim、domain resultを通した証拠ではない。またD108は使い捨てworker先行を明記する (`docs/decisions.md:5016-5024`)。既存artifactで代替するなら、新DでD108のこの順序を明示的にsupersedeする必要がある。

- **P4: 一部同意。** trigger driverのPINは現行系であり、Python内でdependencyをbuildしないscopeは妥当。ただし外部prefixを必須CLI入力として検証しなければ運用可能な経路にならない。`default_perf` はD106が明記する100k records/4 threadsのoperational pilot (`docs/decisions.md:4831-4836`) に限ればscope外でよいが、formal/certified Pegasus calibration済み計測とは主張できない。

- 親briefのS3には一つ実装漏れがある。`pipeline.py:579-580` だけ直しても、`loop.py:103-105` が先に `source_digest.resolve` を呼び、その既定compilerは `g++-13` (`source_digest.py:701-702`) である。loop側にもsite compilerを通さなければcomputeでbuild前に失敗する。

- Bの「driver 2本だけ」ではsingle_processの運用前提が閉じない。floorと同様、durable claim rootの事前provisionと `IZANAGI_RESERVATION_*` が必要 (`s8b_floor_campaign.py:2821-2844`, `docs/pegasus-runbook.md:388-389`)。wrapper追加をscope外にするなら外部前提として受入条件へ明記すべきである。

- さらにD108はsupervisor/LLMをlogin、機械部分をcomputeに置き、現時点ではsanctioned campaign dispatchが無いと定める (`docs/decisions.md:4965-4985`, `docs/pegasus-runbook.md:428-431`)。8cは同一processでproviderを呼ぶ (`p3_autonomous_workload_trial.py:628-642,826-835`) ため、S5で「8c全体をcomputeで運転可能」にするなら新Dによる明示的supersedeかdomain-result transportが必要である。

## 未確認・リスク

- 新DがD108をsupersedeするのか、trigger-gatingの機械workerだけを開くのかは、読んだ資料だけでは確定できない。ここがB実装の最終gateである。

- P3/8c用のdurable claim rootをprovisionし、reservation環境変数とdependency prefixを投入する既存wrapperは見つからなかった。driver内で勝手に作るとfloorのone-shot claim作法を弱める。

- dependency prefixのpre-imageはpath文字列を束縛するが、依存ライブラリbytes自体のhashではない。fresh `/scr` により跨job偽hitは防げるが、同一job内でprefix内容を書き換える攻撃までは覆わない。

- `/scr` のcompletion manifestとbinaryは消えるため、full pre-image/toolchain/binary SHAをpersistent WAL/provenanceへ射影しない実装ではS4の起源証明が失われる。

- 現行8cの承認世代数は1である (`test_p3_autonomous_workload_trial.py:94-151`)。将来複数世代を再許可するときは、同一processのlease再利用と別process resume拒否を分離したまま維持する必要がある。

- sandboxはread-onlyであり、pytest・build・実Pegasus計測は実行していない。テスト結果を緑とは評価していない。

## 総括

- Aでは末尾defaultと条件付きforwardingにより、Pegasusだけをv2へ通しOTHER/既存v2 callerを保つ。
- v2 identityへresolved siteとexact dependency prefixを加え、computeではsystem `gcc/g++` を使う。
- Bではcomputeだけを追加受理し、required attestationを実測直前に発火させる。
- `/scr` cacheはdriver作成・scheduler削除、証拠とclaimは永続領域へ残す。
- 既存v2 cacheは全件cold化するが、full digestの凍結pinは無く、凍結成果物の更新は不要である。
- 8cの直接compute運転はD108と衝突するため、新Dでの明示裁定が必要である。