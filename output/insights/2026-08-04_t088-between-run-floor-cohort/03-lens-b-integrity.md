判定は **NO-GO**。計画は brief の完了条件を満たさず、現状の PBS 実行面では全 8 job が Python 版数で失敗する可能性が高い。以下は静的検査結果であり、書き込み・pytest・ジョブ投入は行っていない。

### B1

- **id**: B1
- **主張**: 親 brief の P1 は import 閉包だけを根拠に台帳上の依存を無効化しており、[T-296]/[T-011] の成果物としては反証される。
- **根拠**:
  - 8c の前提 7 は H1/H2 の対象別 floor、consumer、judge、6 セル表を要求する [phase3-8c-preregistration.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8c-preregistration.md:93)、[同:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8c-preregistration.md:109)。1〜12 は全て未充足である [同:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8c-preregistration.md:123)。
  - 現行 checkpoint は official guard → 段階 3・4 →実行 revision 束縛を残 gate とする [phase3.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3.md:118)。
  - [T-296] は between-run floor を [T-011] の重複として保持し、同じ gate 連鎖を明記する [worklog-phase3-0803-131-132.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/archive/worklog-phase3-0803-131-132.md:118)。
  - コード上の official guard 迂回は見つからない。core は無条件拒否する [s8b_floor_campaign.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/s8b_floor_campaign.py:204)、wrapper/core の注入も拒否する [同:2670](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/s8b_floor_campaign.py:2670)、CLI も拒否する [同:3472](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/s8b_floor_campaign.py:3472)。計画自身もこの系列を変更しない [plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:180)。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: rr50 下限 artifact を作れても H1/H2 floor を埋められず、certified 選択は停止したままなのに台帳だけが虚偽に閉じる。
- **推奨**: 本計画を「一般用途 Pegasus lower-bound pilot」という別タスクへ切り離し、[T-296]/[T-011]/[T-088] は未完のまま保持するかを親からユーザー裁定へ返す。

### B2

- **id**: B2
- **主張**: 1 cohort の rr50 測定は計画自身の定義でも between-run compare floor を確立できず、brief の主成果物を生成しない。
- **根拠**:
  - time-window cluster は事前に 1 固定である [plan.md:207](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:207)。
  - artifact は `lower-bound-only`、`between_run_compare_floor.status=not-established` となる [plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:240)。
  - `noise_cv` へ配線しないことも明記されている [plan.md:260](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:260)。
  - D19 は same-window 値を楽観的下限とし、真正な floor を時間分離された cross-campaign データへ錨付けしている [decisions.md:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:329)、[同:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:337)。
  - 正式対象は H1=rr80/H2=rr20 である [phase3-8b-descriptor-design.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8b-descriptor-design.md:3)、[同:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/phase3-8b-descriptor-design.md:115)。計画の rr50 とは別物である。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: certified 選択は従来の 0.030 のままで、材料レポートには「floor 未確立」としか書けず、台帳の取得義務も閉じない。
- **推奨**: 1 wave を lower-bound pilot と明示して終了するか、複数の事前登録時間窓と H1/H2 を測る正式案へ拡大するかを、実装前に再裁定する。

### B3

- **id**: B3
- **主張**: 計画は Pegasus で既知の Python 3.9 問題を抱えた裸の `python3` を再利用するため、新 driver の import 前に失敗する。
- **根拠**:
  - floor wrapper は Pegasus 既定 `python3` が 3.9 で、実 job が失敗した事実を記録し、3.10 以上を選ぶ [floor_campaign.sh:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/floor_campaign.sh:157)。
  - `env_contract.py` は Python 3.10 以上を要する `str | None` 構文を持つ [env_contract.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/env_contract.py:231)。
  - 計画の floor argv は裸の `python3` である [plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:120)。現行 certify script も同様である [certify_calibration.sh:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/certify_calibration.sh:720)。
  - T-272 は Pegasus shell 3 本への版数 gate を「実装待ち」としている [worklog-phase3-0803-125-126.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/archive/worklog-phase3-0803-125-126.md:109)。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 8 job が driver import 前に停止し、member receipt、registered artifact、台帳材料の全てが作られない。
- **推奨**: profile 分岐より前に T-272 相当の Python 3.10+ 解決、`-I -B`、環境変数除去を実装し、全 Python 呼出しを解決済み interpreter に統一する。

### B4

- **id**: B4
- **主張**: `submit_certify.sh` の任意 job-script seam と実行中 bytes の非束縛により、hash を自己申告する任意 shell が certified receipt を偽造できる。
- **根拠**:
  - real submission でも `--job-script PATH` を受理する [submit_certify.sh:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/submit_certify.sh:5)、[同:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/submit_certify.sh:26)。
  - submitter は指定ファイルの live hash を記録するだけである [同:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/submit_certify.sh:82)。
  - job 側は `$0` ではなく固定された worktree の `certify_calibration.sh` を hash する [certify_calibration.sh:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/certify_calibration.sh:181)。
  - collector は job ID は照合するが、submit/acquisition/result 間の `job_script_sha256` を照合しない [collect_receipt.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/collect_receipt.py:107)。
  - shell materializer と任意 binary path は admission inventory の外である [materializer_admission.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/materializer_admission.py:11)。
  - 既存 official floor 系には `$0`・commit blob・hidden drift を殺す実テストがある [test_pegasus_floor_tools.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_floor_tools.py:355)、[同:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_floor_tools.py:371)、[同:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_floor_tools.py:425)。
- **重大度**: blocker
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 未承認 bytes が生成した floor を正規 receipt として登録でき、材料レポートと台帳の provenance が偽になる。
- **推奨**: real profile では canonical job script を固定し、commit blob・worktree bytes・実行中 `$0`・submit receipt の 4 hash を一致させ、override は dry-run fixture のみに閉じる。

### B5

- **id**: B5
- **主張**: 既存 calibration bytes の pin 閉包は親の「6 箇所」より広い一方、`registered/` ディレクトリの閉集合は存在せず、新ファイル追加だけでは赤くならない。
- **根拠**:
  - 直接 pin は path/sha の [env_contract.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/env_contract.py:186)、Pegasus golden の [test_env_contract.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:231)、contract preimage の [同:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:640)、S8b の [test_s8b_floor_campaign.py:3231](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_s8b_floor_campaign.py:3231) にある。
  - 親が落とした派生 pin は contract digest `e576…` の [test_env_contract.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:652) と [test_s8b_floor_campaign.py:3241](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_s8b_floor_campaign.py:3241)。
  - tracked provenance にも calibration/contract の束縛値がある [silo_ladder_rung1.json:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:10)、[同:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:567)、[gap-result-receipt.json:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/gap-result-receipt.json:19)。これは受動的証拠であり、新しい sibling file の追加検査ではない。
  - path 非依存 pin を独立に調べたが、role ledger の `calibrator` は role source を pin するだけである [review_ledger.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/codex_roles/review_ledger.py:15)、[calibrator.json:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/.codex/role-adapters/calibrator.json:139)。`FROZEN_MANIFEST` は S1/S8b の 23 件だけ [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_frozen_artifacts.py:38)。generator source hash の正本も別の 5 module だけである [s8b_oracle_manifest.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/s8b_oracle_manifest.py:44)。
  - env test は `REGISTRY` が明示的に指した path だけを読む [test_env_contract.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:391)。calibrator の glob は tmp fixture 内の `calibration-*.json` だけである [test_calibrator_certify.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_calibrator_certify.py:491)。
  - 現行 consumer は `between_run_noise_*.json` のみ列挙する [screening_driver.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/screening_driver.py:36)。新 prefix `between-run-floor-*` の consumer は見つからない。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 余分な registered file が無検知で共存し、certified 選択は変わらないまま「登録済み」という台帳上の権威だけが曖昧になる。
- **推奨**: 実測後の exact path/sha inventory を設け、`registered/` の非 symlink・tracked・許可 prefix・ファイル集合を inventory と完全一致させるテストを追加する。

### B6

- **id**: B6
- **主張**: PBS 資材の変更面から policy registry 更新が漏れており、新 policy を追加した時点で既存閉集合テストが必ず赤くなる。
- **根拠**:
  - policy の唯一索引と閉集合検査義務は README に明記される [tools/pegasus/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/README.md:15)。
  - 現行 registry は新 policy を含まない [registry_v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/policies/registry_v1.json:1)。
  - テストは policy directory の実ファイル集合と registry を完全一致させる [test_pegasus_policy_registry.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_policy_registry.py:354)、[同:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_policy_registry.py:410)。
  - 計画の C 所有一覧には `registry_v1.json` と `test_pegasus_policy_registry.py` がない [plan.md:363](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:363)。
  - `certify_calibration.sh` bytes の系譜は、producer=`submit_certify.sh:92,134-170,215-240`、job 検証=`certify_calibration.sh:181-215`、acquisition 伝播=`certify_calibration.sh:563-632`、exact candidate=`make_acquisition_receipt.py:30-48`、型/hex 検査=`schema_v2.py:392-416,558-574` である。collector はこの hash を cross-check しない。
  - 現在の test は任意の同じ synthetic hash を両側へ与えるだけで、script の literal digest は pin しない [test_pegasus_tools.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_tools.py:1014)。既存 artifact は当時の hash を記録するだけである [calibration JSON:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:43)。
  - 従って script 変更だけでは literal golden は赤くならず、旧 receipt を持つ in-flight job の job-side check だけが赤くなる。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: policy 閉集合テストで統合不能となるか、検査を外せば未索引 policy で作られた artifact が台帳へ入る。
- **推奨**: C に registry と閉集合テストを明示割当する。兄弟 job script 案へ変える場合、`.sh` 自体は policy registry 対象ではないため、その task policy を registry へ追加し、script 用には別途 syntax、PBS header、commit blob、実行中 bytes、receipt、3 段 collector の検査を足す。

### B7

- **id**: B7
- **主張**: γ-16 へ対象 module を追加する方針は正しいが、対象一覧自体を同じ test が所有するため entry を削除する変異には無力である。
- **根拠**:
  - 禁止集合は `"linux-baremetal"`, `"pegasus"`, `--interleave=all`, `/scr`, 1800, 2100 である [test_env_contract.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:45)。
  - 実際の対象 module 一覧は [test_env_contract.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:61) から `:75` であり、現状 `between_run_floor.py` は含まれない。
  - 検査はその一覧だけを loop する [同:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:691)。positive control は AST 機構の非恒真性だけを示し、target membership は固定しない [同:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_env_contract.py:707)。
  - 計画は driver と registry を一覧へ追加する [plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:68)。追加されれば検査に触れるが、追加行を消す変異は通る。
  - γ-16 は未列挙値を検出しないと自認している [env_contract.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/campaign/env_contract.py:242)。1M/48 は別の導出検査が必要である。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: module entry を落とすだけで Pegasus literal や clock hardcode が通り、異なる環境値の artifact が正規登録され得る。
- **推奨**: γ-16 とは独立に exact target-set または必須 membership を固定し、1M/48 は異なる calibration fixture を与えて導出を検証する。

### B8

- **id**: B8
- **主張**: `require_all_reps=True` だけでは plan が約束する rep return code は保存されない。
- **根拠**:
  - 計画は strict flags だけで throughput と return code を残すとしている [plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:33)。
  - `measure_point` は `rep_returncodes` が明示された場合だけ list を `run_once` へ渡す [runner.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/runner.py:416)、[同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/calibrator/runner.py:448)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: registered member に 5 rep の終了状態が残らず、材料レポートと台帳から成功 rep の完全性を監査できない。
- **推奨**: 5 要素の専用 list を渡し、長さ・順序・全ゼロを schema と registry で再検証し、missing/nonzero/reordered の各変異を殺す。

### B9

- **id**: B9
- **主張**: bundle submitter は二重実行を識別する安定した wave identity を持たず、再実行は冪等でなく別の 8-job wave を黙って作る。
- **根拠**:
  - submitter は実行ごとに bundle nonce と member nonce を新規生成する [plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:152)。
  - 現行 submitter も毎回 random nonce の新 namespace を作る [submit_certify.sh:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/submit_certify.sh:93)。
  - 同じ PBS job ID の compute staging は `mkdir` 失敗で fail-closed する [certify_calibration.sh:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/certify_calibration.sh:41)。
  - 同じ final receipt path は `"x"` で fail-closed する [collect_receipt.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/collect_receipt.py:191)。
  - 同じ registered bytes/name も collision として止める予定である [plan.md:301](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:301)。
  - **推測**: 通常の二回目は job ID・nonce・時刻を artifact が含むため別 digest となり、registered collision せず二個目が増える。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 操作ミス一回で 16 job と複数の lower-bound artifact が生まれ、どれが裁定済み wave か台帳で一意にならない。
- **推奨**: ユーザー指定または事前凍結した wave ID を create-only claim として qsub 前に確保し、同じ ID の二回目は副作用前に拒否する。

### B10

- **id**: B10
- **主張**: 計画のテスト表には target 自己除外や同値 hardcode を殺せない検査と、既存被覆を純増扱いする項目が残る。
- **根拠**: 計画の全テスト一覧は [plan.md:346](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:346) にある。

|計画テスト|これを消すと黙って通る変異|現状の穴・既存被覆|
|---|---|---|
|`test_between_run_floor.py` 拡張|env/1M/48 hardcode、CLI override、rr5/rr95、probe 順序逆転、legacy 上書き|1M/48 と同値の fixture だけでは hardcode を殺せない。異なる calibration を渡す必要がある。binary mismatch は既に [test_calibrator_certify.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_calibrator_certify.py:358) が被覆する。|
|`test_env_contract.py` γ-16|対象 module 内への禁止 literal 注入|target entry 自体を消す変異は通る。|
|新規 registry test|missing/duplicate/mixed member、producer 自己申告 CV・cluster、非 canonical bytes|誤った producer median/CV、return code、time-window を raw から再計算して拒否する変異が明記されていない。|
|`test_pegasus_tools.py` 拡張|open argv、binding 欠落、7/9 qsub、replacement job、hash chain 欠落|期待値 8 を policy と同じ source から導出すると恒真になる。現行 calibration argv の部分検査は既に [test_pegasus_tools.py:952](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/orchestrator/tests/test_pegasus_tools.py:952) にある。|
|collector 対応テスト|異なる bundle/member/policy/script/log の混入|現 collector は job ID しか cross-check しないため、各 hash を独立に反転する mutation が必要。|
|既存 `test_s8b_floor_campaign.py`|official guard、既存 calibration/contract pin の回帰|完全に既存被覆であり、本 wave の純増検出力ではない。|

- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 壊れた binding や自己申告集計がテストを通り、誤った lower-bound と receipt が材料レポートへ流れる。
- **推奨**: 各テストに独立な一変異一失敗表を付け、期待値を production policy と同じ式から導出せず、既存被覆と新規 vector を分離して数える。

### B11

- **id**: B11
- **主張**: A/B/C 間の同一ファイル競合はないが、必須の policy registry と閉集合 test が ownerless である。
- **根拠**:
  - A/B/C の列挙上、同一ファイルの二重所有はない [plan.md:363](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:363)。
  - A が `test_env_contract.py` を所有するため、B の新 registry を γ-16 対象へ加える場所にも形式上の競合はない [同:365](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:365)。
  - ただし C の一覧に `tools/pegasus/policies/registry_v1.json` と `orchestrator/tests/test_pegasus_policy_registry.py` がない [同:367](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:367)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: C の実装完了後も閉集合テストが赤く、登録・実測段へ進めない。
- **推奨**: 両ファイルを C の排他的所有へ追加し、Python interpreter hardening とその test の owner も同時に明記する。

### B12

- **id**: B12
- **主張**: 3 段連鎖は設計上は残るが bundle collector がなく、end-to-end の人間手番は「1 回」の運用には収まらない。
- **根拠**:
  - 必須連鎖は submit receipt → compute staging → final receipt である [tools/pegasus/README.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/README.md:7)。
  - 計画は submit、8 job 完了後の final receipt、register を順に置くため、連鎖そのものは省略していない [plan.md:370](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:370)。
  - しかし collector CLI は一つの attempt/job-staging/stdout/stderr だけを受ける [collect_receipt.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/tools/pegasus/collect_receipt.py:209)。
  - 呼出し数は 8 qsub（1 bundle submitter command）、8 collector、1 register。さらに dry-run と real submit 間に少なくとも 1 回の人間確認がある。計画資材だけなら最低 11 command 相当で、collection を一括する provenance-aware wrapper はない。
  - 計算量も最大 16 node-hours である [plan.md:380](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:380)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: 8 組のログ対応を人手で誤るか一部を収集し忘れ、登録不能または別 job の receipt 混入になる。
- **推奨**: bundle plan の exact 8 member を一括収集・照合する collector を作るか、この人間手番数と 16 node-hours が裁定の「1 wave」に含まれるかを再確認する。

### B13

- **id**: B13
- **主張**: 親 brief の「飽和最小は充足済み」と Pegasus の within-run 1.17% から between-run 影響を一般化する前提はいずれも実測に反する。
- **根拠**:
  - brief は「飽和最小」を充足済みとする [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/brief.md:23)。
  - artifact は `lower_bound_selected=true`、`saturated=false` である [calibration JSON:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1603)。計画自身も訂正済みである [plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/t088-floor/plan.md:5)。
  - 1.17% は一つの node/session の within-run CV である [calibration JSON:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577)。
  - D19 が塞いだ穴は、まさに within-run を between-run compare に一般化して偽 faster を出す経路である [decisions.md:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:331)、[同:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t088-floor/docs/decisions.md:335)。
- **重大度**: must-fix
- **これを直さないと成果物 (certified 選択・材料レポート・台帳) の何がどう変わるか**: certified 選択は実際には不変なのに、材料レポートと台帳が「Pegasus floor により過剰 tie を是正した」と過大主張する。
- **推奨**: 1M/48 は「4×L3 下限規則で選択」と記し、1.17% は within-run 品質の一点観測に限定して、between-run への効果推論を削除する。

## 総括

**(a) 判定: NO-GO。** 台帳上の gate を満たさず、測定しても compare floor は `not-established`、さらに現 PBS interpreter と job-script provenance では実行・認証の両方が成立しないためである。

**(b) 最も重い所見 3 件**

1. **B1** — P1 が台帳の [T-296]/[T-011]/[T-088] 依存を誤って無効化している。
2. **B2** — 1 cohort rr50 は計画自身の schema でも真正な between-run floor を生成しない。
3. **B3** — Pegasus 既定 Python 3.9 により新 driver が import 前に落ちる。

**(c) P1〜P6**

- **P1: 不同意。** コード上の official guard 迂回はないが、brief が名乗る台帳 task には同 guard と段階 3・4・revision 束縛が残る。
- **P2: 不同意。** 複数 PBS request を一括投入すること自体は可能だが、1 cohort は floor を確立せず、人間手番と 16 node-hours の解釈も未裁定である。
- **P3: 条件付き同意。** `calibration_ref` を動かさない方針は正しいが、新 registered prefix の閉集合・authority・consumer が未設計である。
- **P4: 同意。** within-run 品質と between-run compare floor の役割分離は正しいが、今回確立できるのは前者と同時 cohort 下限だけである。
- **P5: 不同意。** argv seam 再利用は Python 版数、任意 job script、commit blob/実行 bytes 束縛を先に硬化しなければ certified 実行面にならない。
- **P6: 不同意。** 実装資材の整備自体は禁止されないが、本スコープを [T-296]/[T-011] の完了と扱うことと、1 wave で不足すると事前に判明した測定へ進むことには再裁定が必要である。