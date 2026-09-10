## 所見

### [B-1] fresh なのは build cache だけで、計測 campaign は既存の最終成果物へ衝突する

**深刻度:** BLOCKER

**型:** 説明と実装の食い違い / consumer 取り残し / 恒真な保証

**根拠:** `CampaignConfig` は env を同一性に含めない (`orchestrator/campaign/model.py:63-75`, `orchestrator/campaign/ident.py:76-103`)。一方、compute では claim 取得後に既存 state を拒否し、claim は解放しない計画である (`s2-plan.md:83-84`)。`default_cfg()` の campaign ID は既存の `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` と同じで、実物には iteration=2 の state と linux-baremetal WAL が既にある (`output/campaigns/.../loop_state.json:1-20`, `runs/wal.jsonl:1-12`)。しかもこれはクローズ済みの最終成果物である (`docs/phase3.md:402-410`, `orchestrator/tests/test_layer3_report.py:20`)。

**具体的な失敗シナリオ:** bnode 上で通常の trigger `--run-iteration` を起動する。計画どおり claim を永続作成した後、既存 linux campaign state を検出して build 前に停止する。成果物は Pegasus WAL ではなく、再試行も塞ぐ stale claim だけになる。逆に既存 state 拒否を外すと、同じ WAL に `pegasus` を追記し、Layer3 の env 一意検査 (`layer3_report.py:388-390`) が失敗する。

**提案:** 一般の D13 identity を変えず、Pegasus 用に新しい `trial` または明示的な campaign output namespace を切る。OTHER からその namespace を再開できない対称な env fence も必要。既存最終成果物を再利用してはならない。

### [B-2] `dependency_prefix=""` の互換逃げで D108 の cache 誤 hit がそのまま残る

**深刻度:** BLOCKER

**型:** 説明と実装の食い違い / consumer 取り残し

**根拠:** プランは ambient `CMAKE_PREFIX_PATH` を「読まない」とし、既存 caller では空既定を forward しない (`s2-plan.md:25-32`)。しかし `_run()` は環境を scrub せず `subprocess.run()` するため、CMake は ambient 値を継承する (`buildcache.py:779-791`)。実際、floor wrapper はそれを唯一の dependency seam として export する (`tools/pegasus/floor_campaign.sh:850-856`, `tools/pegasus/README.md:174-176`) が、floor の `build_v2` 呼出しは prefix を渡さない (`s8b_floor_campaign.py:962-981`)。

独立 grep した consumer は次のとおり。

- floor は直接 `build_v2` を呼び、binary SHA と argv を保存する (`s8b_floor_campaign.py:1004-1018`)。
- ratified freeze はその exact key、binary SHA、argv を検査するが full digest は持たない (`s8b_ratified_freeze.py:181-185,1633-1667`)。
- oracle は pipeline 経由で、contract SHA と期待 binary SHA を照合する (`s8b_oracle_driver.py:941-958,1334-1361`, `pipeline.py:621-630`)。
- T126 も pipeline 経由で、別系列の toolchain identity と trace/perf SHA を持つが full build digest は持たない (`qualification/t126_driver.py:519-540`, `qualification/artifacts.py:900-956`)。
- test consumer は `test_buildcache_v2.py:91,357-376,447,511`、`test_build_site_gate.py:118,281-332`、`test_campaign.py:1283-1301`、`test_s8b_floor_campaign.py:2410`、`test_s8b_oracle_driver.py:2341,3822-3866`。

full digest 自体を pin する凍結 consumer は見つからず、「digest 変更だけなら cold miss」というプランの狭い主張は反証できない。問題は、空 prefix identity のまま ambient prefix が実際の build に効くことだ。

**具体的な失敗シナリオ:** post-wave の floor job A が `/scr/jobA/...` を ambient export し、identity には `dependency_prefix=""` を記録して永続 cache を作る。次の job B が異なる dependency bytes を `/scr/jobB/...` から export しても digest は同じなので A の binary を hit する。B の reservation で作られた floor manifest に、A の dependency で作った binary と prefix を欠いた configure argv が記録される。

**提案:** 空既定時は ambient 変数の存在を拒否するか、必ず scrub する。あるいは ambient 値を canonical 化して identity と argv に束縛する。floor/oracle/T126 と各 fake を含む全 v2 caller を明示 prefix 化し、ambient A→B 変更で hit しない負例を置く。

### [B-3] prefix・reservation・claim・`/scr` を供給する実 caller が存在しない

**深刻度:** BLOCKER

**型:** 恒真な保証 / 説明と実装の食い違い

**根拠:** プラン自身が、claim root、reservation、prefix を投入する既存 wrapper を発見できなかったと認める (`s2-plan.md:228,236`)。`tools/pegasus/certify_calibration.sh:495-519` は素の CMake build の生存証拠にすぎず、trigger/8c、v2 routing、claim、receipt、domain result を一度も通らない。sanctioned campaign dispatch も存在しない (`docs/pegasus-runbook.md:428-431`)。さらに T276 は先行 land が条件なのに未実装で、proxy provenance 等が残る (`docs/worklog.md:1506-1511`)。プラン自身も D108 の supersede を「最終 gate」として未確定のまま残している (`s2-plan.md:230,234`)。

**具体的な失敗シナリオ:** ユーザーが既存 Pegasus wrapper のいずれかを投入しても target driver は呼ばれない。target CLI を直接呼べば、prefix、事前 provision 済み claim root、reservation、または T276 provider 条件の欠落で `/scr` 作成・build・WAL より前に停止する。結果は certified 行、Layer3 report、attempt ledger のいずれも 0 件なのに、worklog だけが「計測パス開通」になる。

**提案:** `DW-G04` を満たす target 固有 wrapper/caller と、実際に通った measurement ID を受入条件へ入れる。T276 の確定 interface 前に 8c 配線を実装しない。そこまで scope 外なら成果物名を「routing/gate 実装」に格下げする。

### [B-4] 兄弟 driver を不変にするのは安全策ではなく、Pegasus 経路を片肺にする

**深刻度:** MAJOR

**型:** consumer 取り残し

**根拠:** プランは base/sort を意図的に旧経路へ残す (`s2-plan.md:101-102`)。実物は固定値のままである。

- `p3_s4_loop.py:67-71,655-656`
- `p3_s4_loop_sort.py:86-89,233-234`
- `s6_sort_sweep.py:67-70,325`
- `s8a_trigger_sweep.py:84-87,119-132,362-378`
- `s8a_trigger_freq.py:62,181-185`
- `s8a_trigger_coverage.py:59-60,212,279-283`

共通 site gate は LOGIN/SUSPECT だけを拒否し、COMPUTE は許す (`site_policy.py:74-76`)。したがって「未変更だから安全」ではない。

**具体的な失敗シナリオ:** 共有 legacy cache に既存 binary がある状態で bnode 上から `backoff_sweep.py` または sort/s8a driver を起動する。build gate は cache hit で発火せず、compute の throughput が `env_tag=linux-baremetal`, clk=1800, NUMA interleave として WAL に入る。`p2_2_report.py:123,182-188` は Markdown に `env: linux-baremetal`、`backoff_sweep_report.py:71` と `orchestrator/reports/plot.py:40-44` は `.dat` に `# env: linux-baremetal` と表示する。

**提案:** 全兄弟を移行する必要はない。今回 scope 外の driver は COMPUTE を明示拒否し、「Pegasus sanctioned は trigger/8c のみ」と機械化する。これは移行肥大化より小さい。

### [B-5] env_tag は WAL と Layer3 までは届くが、critic・screening・renderer で落ちる

**深刻度:** MAJOR

**型:** consumer 取り残し

**根拠:** WAL は env_tag を保存し (`wal.py:188-234,499-505`)、Layer3 も WAL から読む (`layer3_report.py:81-101,388-419`)。この二層は追随する。一方、critic の `GenomeLI` / `WorkloadDigest` は env を持たず、loader も `r.env_tag` を読まない (`critic/digest.py:38-77,192-219,446-452`)。renderer も環境なしで数値を出す (`critic/digest.py:478-503`)。その digest は trigger が生成し、8c が critic へ渡す (`p3_s4_loop.py:236-253`, `p3_autonomous_workload_trial.py:955-977`)。実際の保存済み digest も throughput を表示しながら env を一字も持たない (`output/campaigns/.../s8a_trigger_loop_digest.txt:1-28`)。screening の既定 calibration は常に linux 固定である (`screening_driver.py:30-38`)。

**具体的な失敗シナリオ:** B-1 の混在 WAL、または誤って再利用された layout を critic が読むと、Pegasus と Linux の throughput を区別せず平均し、8c の次世代 recommendation を生成する。別経路では `evaluate_candidate(..., env_tag="pegasus")` に calibration_dir を省略すると、Linux floor で screening した判定が Pegasus-tagged WAL に載る。

**提案:** digest schema と表示へ env_tag を追加し、一意でなければ拒否する。screening calibration は env contract から導出する。旧 report は WAL 由来 env を使うか、非 Linux WAL を拒否する。

### [B-6] P4 を切ったまま得られるのは exploratory throughput であって calibrated certified 選択ではない

**深刻度:** BLOCKER

**型:** 説明と実装の食い違い

**根拠:** trigger の動作点は 100k records / 4 threads (`p3_s4_loop_trigger_gating.py:367-375`, `p3_s4_loop.py:513-519`)。Pegasus 登録 calibration は 1M / 48 (`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1612,1685`) である。さらに直接 trigger の `search_config` には `ycsb` がなく、Layer3 は workload 不在時に floor を一致扱いしない (`layer3_report.py:213-290`)。8c は ycsb を持つが 100k/4 のまま (`p3_autonomous_workload_trial.py:426-465`)。登録 artifact は `calibration/registered/` 配下なのに、Layer3 は `calibration/*.json` を非再帰走査する (`env_contract.py:186-191`, `layer3_report.py:217,405-407`)。

D106 自身がこの構成を operational pilot に限定している (`docs/decisions.md:4831-4836`)。D108 も live driver artifact と walltime 前に operational と書くことを禁じる (`docs/decisions.md:5003-5008`)。

**具体的な失敗シナリオ:** compute で correctness を通過して `certified=True` と throughput が WAL に入っても、Layer3 の `noise_floor` は `value=null / no-matching-env-record` になる。性能差を floor 越えとして認証した selected row は作れない。

**成果物への一行影響:** dependency prefix を供給する実 caller が無ければ `build_done/commit=0件`、matching Pegasus calibration が無ければ `Layer3 noise_floor.value=null` で calibrated certified 選択は `0件`。

**提案:** generic dependency staging 自動化は scope 外でもよいが、exact prefix を供給する wrapper は必須。matching calibration と Layer3 discovery を入れないなら「operational pilot の生 throughput」以上を主張しない。なお P4 の PIN 不一致は target trigger には存在しない。

### [B-7] 新テストの一部は先行 gate に mask され、単一理由の mutation kill にならない

**深刻度:** MAJOR

**型:** 恒真な保証 / テスト代表性

**根拠:** 既存 freshness gate が全 site で state を拒否する (`p3_autonomous_workload_trial.py:196-206,779-784`)。したがって compute 固有の `allow_resume=False` 検査を除去しても、既存 state 負例は同じ場所で落ちる。CLI は fixture+build を新 gate より前に拒否する (`:1111-1114`) 一方、計画上 no-build は lookup、attestation、claim、`/scr` を全部通らない (`s2-plan.md:161`)。これは F21/F28 の「実物への配線未検証」「先行検査に食われる変異」と同型 (`docs/failures.md:263-280,405-418`)。

正例の compute clean と負例の LOGIN/SUSPECT は計画にある。しかし次が欠ける。

- 任意の未知 site を拒否する behavioral negative。
- ambient prefix が空 identity に漏れない negative。
- fresh な別 run-root・同一 campaign の二プロセス競合で、旧 freshness ではなく claim だけが落とす試験。
- target CLI/wrapper が prefix→claim→attestation→v2→WAL を通す liveness positive。
- checked-in final campaign 衝突を検出する試験。

**具体的な失敗シナリオ:** `allow_resume` の参照または compute isolation 配線を削除した変異でも、existing-state test は旧 freshness、fixture build test は CLI 拒否、no-build test は未発火によって期待どおり拒否される。mutation 台帳は新 gate を検出していないのに KILLED と記録しうる。

**提案:** 各 mutation について先行 gate を neutral 化し、期待する一つの reason/code と到達 spy を固定する。AST pin は behavioral unknown-site 負例の代わりにしない。

### [B-8] login node の compiler 観測を compute 全体へ一般化する根拠は brief 内にはない

**深刻度:** MINOR

**型:** 誤前提

**根拠:** brief の実測対象は明示的に login node である (`brief.md:55-62`)。ただし `g++-13` 不在そのものは runbook が login/compute 両方で独立に裏付けるため反証できない (`docs/pegasus-runbook.md:297-299`)。一方、「compute の module に gcc がない」は未確認である。登録 calibration の compiler は gcc-11 (`calibration-753f...json:58-64`) だが、計画は各 node の `gcc/g++` をその場で選ぶ。attestation は hardware profile を比較し (`execution_guard.py:311-316`)、runtime compiler と calibration acquisition toolchain の一致は検査しない。

**具体的な失敗シナリオ:** これは node 間 compiler drift の実測がないため推測である。別 bnode で `gcc` が異なる版へ解決された場合、build digest は分かれても Layer3 は両方を同じ `env_tag=pegasus` として扱い、gcc-11 calibration との toolchain 差を比較条件から落とす。

**提案:** compiler の有無・realpath・version は計算 node の実行時 preflight で確定し、calibration acquisition toolchain と照合するか report の比較 key に含める。module 不在という一般化には依存しない。

## 親 brief の誤り

- **P3 は反証済み。** calibration の素 CMake build は target route の liveness artifact ではない。v2、claim、receipt、8c、domain result のどれも通らない (`brief.md:46-48`)。
- **P4 の「PIN 不一致」は target について誤り。** trigger は `axis_trigger_gating.PIN = pin.CURRENT_PIN` (`axis_trigger_gating.py:27`, `pin.py:28`) で、gitlink も `d706650...` で一致する。
- **「計測パスを開く」は現 scope では誤り。** 直接 trigger は既存のクローズ済み campaign に衝突し、8c には sanctioned caller がない。
- **S2 の影響範囲は過小。** target WAL は Pegasus になるが、critic、screening、旧 reporter、兄弟 driver は追随しない。
- **「Pegasus 値が certified 選択へ入る」は過大。** correctness-certified WAL は作れても matching floor がなく、calibrated selection は作れない。
- **gcc/g++-13 不在という結論は反証できず。** runbook に compute 実測がある。ただし compute module の一般化は未証明。
- **full build digest 変更だけで凍結成果物が壊れる、とは反証できず。** 実際、production の full-digest pin は見つからない。破綻点は ambient prefix の未束縛である。

## GO / NO-GO

**NO-GO。** 直接経路は既存最終 campaign に衝突し、8c には実 caller がない。  
空 prefix の互換策が D108 の誤 hit を温存し、正式レポートは calibration 不一致で値が出ない。  
まず namespace、全 v2 caller、T276 interface、単一理由テストを裁定し直すべきである。

## 総括

- gate を開くだけでは計測経路は開かず、現在の直接 trigger は静的に到達不能である。
- fresh `/scr` は fresh campaign/WAL を保証しない。
- build identity は明示 prefix では改善するが、既存 caller の ambient seam で再び破れる。
- 兄弟 driver は「不変」ではなく、Pegasus 値を Linux として残す旧入口になる。
- 得られるのは exploratory throughput であり、calibrated certified 選択ではない。
- 新テストには先行 gate に mask される候補があり、実 target liveness positive もない。
- pytest、build、実 Pegasus 計測は実行していない。