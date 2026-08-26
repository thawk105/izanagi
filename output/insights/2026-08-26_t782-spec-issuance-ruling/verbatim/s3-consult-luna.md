静的検査のみです。pytest は実行しておらず、緑とは主張しません。

### L1 — 単位 A は fixture と同じ assembler を二重化する一方、交差検査を完成させていない

- **file:line:** [plan.md:50-74](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:50)、[s8b_oracle_spec_fixture.py:38-89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/tests/s8b_oracle_spec_fixture.py:38)
- **噛み合わない具体的な状態と、そのときに起きること:** `make_reviewed_spec` は既に schedule 構築、top-level document 組立て、validation、canonical bytes、SHA、snapshot 作成まで持つ。単位 A との差は holdout/configuration/binding/generator の入力を内部導出する点と CLI だけである。計画は `independent_canonical_bytes` だけを再利用し、`make_reviewed_spec` が独立に組み立てた document との同一入力差分検査を計画していない。したがって assembler は二つ残るが、独立実装を oracle として使う交差検査は serializer 部分にしか効かない。fixture を production 化すれば独立 serializer を失い、現計画どおり分離すれば document 組立て drift が残るという二律背反を解いていない。
- **成果物影響:** fixture 経由の driver/report/judge テストが緑でも production candidate の field・spec SHA・manifest ID が異なり、official loader/manifest が拒否して certified 選択・レポート・台帳は発行されない。

### L2 — 「CLI は指紋照合だけ」という D840 は現在も計画後も成立しない

- **file:line:** [decisions.md:31717-31731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/docs/decisions.md:31717)、[s8b_oracle_spec.py:259-270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:259)、[s8b_oracle_manifest.py:1123-1157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:1123)、[s8b_oracle_manifest.py:1198-1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:1198)、[plan.md:168-179](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:168)
- **噛み合わない具体的な状態と、そのときに起きること:** D840 は「内容の再導出や束縛検査を持たない」と逐語で定めるが、`build-approved` CLI は `load_approved_spec` を呼び、schema、schedule、binding、live generator bytes を再検証する。さらに `verify_manifest` は schedule と spec の各 projection を再構築・比較する。計画はこれを `C_before=C_after` として温存するため、D840 を「新しい解釈を追加しない」へ無断で弱めている。単位 A も `validate_reviewed_spec`、`_canonical_bytes`、manifest の private helper を共有するので、module 分割だけでは境界にならない。
- **成果物影響:** official manifest の受理集合は「hash 一致」ではなく「hash＋全内容＋live source 一致」のままで、source drift 等により D840 が通すはずの pinned bytes も拒否され、certified 選択・レポート・台帳が欠落する。

### L3 — candidate bytes を読む production consumer は repo 内に存在しない

- **file:line:** [plan.md:60-62](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:60)、[s8b_oracle_spec.py:183-201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:183)、[s8b_oracle_manifest.py:1213-1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:1213)、[s8b_oracle_driver.py:1323-1332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_driver.py:1323)
- **噛み合わない具体的な状態と、そのときに起きること:** 計画上の consumer は新規 producer test だけである。production の manifest builder、driver、report、judge、verdict はすべて `SPEC_REL` の fixed-path bytes を `load_approved_spec` で読む。producer の API 戻り値や stdout を読む caller はなく、producer は canonical path へ書かず、単位 B も producer 出力を読まない。`output/insights` への保存は未定義の「親 orchestration」手作業である。
- **成果物影響:** 単位 A を land しても `APPROVED_SPEC_SHA256=None`、spec 0件、official manifest 0件のままで、certified 選択・レポート・台帳の値は一つも変わらない。D841 の「受領証はあるが誰も読まない」型である。

### L4 — A/B の編集面が素集合という主張は、必要な境界検査を落としたときだけ成立する

- **file:line:** [brief.md:99-102](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/brief.md:99)、[test_s8b_oracle_manifest_contract.py:39-104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/tests/test_s8b_oracle_manifest_contract.py:39)、[plan.md:80-84](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:80)、[test_plain_runner_coverage.py:44-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/tests/test_plain_runner_coverage.py:44)
- **噛み合わない具体的な状態と、そのときに起きること:** 親が A の機械強制根拠とする contract test は、official artifact loader 3個と `verify_manifest` の caller しか列挙しない。candidate module の `load_approved_spec`、`validate_reviewed_spec`、candidate import の依存方向は監視対象外である。A の「構造で守る」を実効化するなら、この contract test の AST inventory を拡張する必要があり、B が直接編集する同一 file と重なる。さらに新規 `test_s8b_oracle_spec_candidate.py` は全 test file を列挙する plain-runner meta test に入るため、自走 harness または `orchestrator/tests/README.md` allowlist の編集が必要だが計画の file 集合にない。
- **成果物影響:** 現分割では D840 境界が未検査のままか受入が赤になり、単位別の焦点走が通っても land 不能になる。official artifact 値自体は変わらない。

### L5 — `run_contract` の導出可能性を訂正した親記録と、計画の入力契約が正面衝突している

- **file:line:** [measurements-2.md:6-18](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/measurements-2.md:6)、[plan.md:22-35](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:22)、[s8b_oracle_manifest.py:424-455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:424)、[s8b_oracle_driver.py:929-956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_driver.py:929)、[test_env_contract.py:69-76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/tests/test_env_contract.py:69)
- **噛み合わない具体的な状態と、そのときに起きること:** 計画は `run_contract` 全体を caller 入力に残す。spec validator が固定するのは `verify=legacy+s2`、`screening=off`、`bench_max_rounds=1`、`reps=5`、`extime=5` で、`clocks` は任意の正整数、`contract_sha256` は任意の64hex、`ccbench_pin`/`env_tag` は任意 identifier である。runtime は初めて env 契約と照合する。現在の実効値域は `linux-baremetal → clocks=1800, contract=1b2e…`、`pegasus → clocks=2100, contract=e576…`、ccbench gitlink `511c9538…`。Pegasus g2 `1346…` は登録済みだが ever-active でなく拒否される。親の「5自由軸以外は導出」と計画の「run_contract は外部入力」は両立しない。
- **成果物影響:** schema-valid だが runtime-invalid な clocks/hash/pin でも spec SHA、manifest ID、campaign config preimage が発行され、driver が実走前拒否するため certified 選択・レポート・台帳は空のままになる。

### L6 — `allowed_excluded_reasons` の「承認済み4行」は oracle spec の実値域ではない

- **file:line:** [measurements-2.md:10-13](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/measurements-2.md:10)、[s8b_floor_stats.py:52-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_floor_stats.py:52)、[s8b_floor_contract.py:523-528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_floor_contract.py:523)、[s8b_oracle_spec.py:172-178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:172)、[test_s8b_oracle_manifest.py:67-99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/tests/test_s8b_oracle_manifest.py:67)、[s8b_oracle_report.py:1396-1400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_report.py:1396)
- **噛み合わない具体的な状態と、そのときに起きること:** 四値は floor protocol の閉じた表であり、oracle spec validator は任意の重複なし非空文字列列を受理する。oracle の既存 positive fixture も `machine-failure` や `machine-failure-日本` を意図的に通している。したがって「repo authority から導出済み」とする追測は、floor authority を oracle authority へ無裁定で移植している。一方、計画はこの field を外部入力に戻しており、親資料同士も不一致である。
- **成果物影響:** 選んだ一覧により spec SHA・manifest IDと、report が protocol violation にせず受理する `excluded_reason` 集合が変わり、judge の cell 状態・verdict 理由・レポート行が変わる。

### L7 — `binding_identity` は repo 導出値ではなく、実行 site/compiler に依存する

- **file:line:** [plan.md:35-45](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:35)、[source_digest.py:1501-1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/source_digest.py:1501)、[buildcache.py:1628-1632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/buildcache.py:1628)、[s8b_oracle_driver.py:1373-1378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_driver.py:1373)、[s8b_oracle_driver.py:1603-1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_driver.py:1603)
- **噛み合わない具体的な状態と、そのときに起きること:** `source_digest` 自身が digest は cxx/環境依存と明記する。計画は design の `env_tag` から compiler を決めず、「producer を実行した現在 site」から `g++` または `g++-13` を選ぶ。例えば Pegasus 用 design を login/別 site で作ると、runtime compute node が使う compiler と異なる identity を凍結しうる。専用テストは materializer spy なのでこの不一致を踏まない。
- **成果物影響:** `src_token`、`variant_id`、`binding_sha256`、spec SHA、manifest IDが生成 site で変わり、runtime 再実体化比較が `binding-refused` となって選択・レポート・台帳を発行できない。

### L8 — 現時点の正しい順序は「A/B とも設計メモ止まり」である

- **file:line:** [plan.md:149-179](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:149)、[brief.md:75-82](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/brief.md:75)、[decisions.md:15537-15540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/docs/decisions.md:15537)
- **噛み合わない具体的な状態と、そのときに起きること:** A は consumer がなく、設計値・freeze authority・site binding が未確定である。B は現在の `(None, empty)` に何も加えず、将来の受理集合だけを広げるが、D355 が要求した runtime 接続と actual approved bytes の正例を持たない。B先行でもA先行でも、この wave の成果物は一つも増えない。D840 は構成選択の裁定であって、exact bytes や v1-derived identity の批准ではない。
- **成果物影響:** 両方を実装しなくても pin、spec、manifest、certified selection、report、ledger の全値は現在と同一である。実装だけ先行すると休眠 capability/test state のみ増える。

### L9 — 承認・設置・受入・runbook の層が scope 外のままで、publication workflow が閉じない

- **file:line:** [plan.md:60-62](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:60)、[s8b_oracle_manifest.py:1263-1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:1263)、[既存 producer 設計:53-56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/output/insights/2026-08-12_t499-spec-producer-design/verbatim/s2-plan.md:53)、[同:99-106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/output/insights/2026-08-12_t499-spec-producer-design/verbatim/s2-plan.md:99)
- **噛み合わない具体的な状態と、そのときに起きること:** 既存設計資産は `preview` と approval 後の create-only `install-approved`、staged bytes/pin/receipt の同時検査まで列挙していた。現計画は installer/writer を削り、live runbook・phase docsにも reviewed-spec approval 手順や CLI 導線がない。既存 `build-approved` CLI は spec を生成せず、既に設置済みの spec と active ratified freeze を要求するため、空白を埋めない。
- **成果物影響:** candidate SHA を得ても canonical spec、pin、manifestへ移す正規経路・参照がなく、certified 選択・レポート・台帳は生成されない。

裁定パッケージ候補は、exact design 5軸と除外理由の authority、v1 freeze SHAとactive-v2前提、preview→人間 review→spec+pin同時設置、generator drift時の失効・再発行、`load_approved_spec`/`build-approved` positive control、D356の非機械的人間承認限界、runbook上の運用入口である。

### L10 — 「批准を経ていない v1」という論点設定は半分誤りで、残り半分は実装欠落である

- **file:line:** [blocker-correction.md:39-54](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/blocker-correction.md:39)、[s8b_ratified_freeze.py:20-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_ratified_freeze.py:20)、[s8b_ratified_freeze.py:63-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_ratified_freeze.py:63)、[s8b_ratified_freeze.py:1409-1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_ratified_freeze.py:1409)、[s8b_oracle_spec.py:25-34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:25)、[s8b_oracle_spec.py:161-166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:161)
- **噛み合わない具体的な状態と、そのときに起きること:** v1 freeze は repo 内で `V1_FREEZE_SHA256` に束縛された明示的な “v1 trust root” であり、完全な無批准入力ではない。しかし計画は `load_legacy_freeze` を使わず、canonical path を普通に strict-loadするだけなので、その既存 trust root を迂回する。さらに reviewed-spec schema は生成元 freeze の path/hash を持たず、binding validator は内部 hash と cell 集合しか見ない。したがって「裁定だけ」の問題ではなく、dirty/差替え済み v1 bytes から candidate を作れないようにする機械 gate が欠けている。
- **成果物影響:** producer追加だけなら受理集合は広がらないが、bytes設置＋pinでは approved-spec受理集合が0件から1件へ真に拡大する。active v2 と runtime binding が不一致なら certified 選択はfail-closedのままだが、loaderが受理する「承認済みだが実走不能なspec」とそのmanifest参照を作れる。

### L11 — 単位 B は hash が合う stale spec を「正しい lifecycle」と受理する

- **file:line:** [plan.md:92-107](/home/SFC/tanab/.claude/jobs/79399294/tmp/t782/plan.md:92)、[s8b_oracle_spec.py:259-270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_spec.py:259)、[s8b_oracle_manifest.py:458-498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/orchestrator/campaign/s8b_oracle_manifest.py:458)、[decisions.md:19943-19947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t782-reviewed-spec-issuance/docs/decisions.md:19943)
- **噛み合わない具体的な状態と、そのときに起きること:** B の approved branch が調べるのは file 1件と `SHA256(bytes)==pin` だけである。spec が記録する production source 5本のどれかが変わっても lifecycle test は緑のままだが、実 consumer の `load_approved_spec` は live source hash 不一致で拒否する。D480 が数日単位の失効を実測済みであるのに、B の正例は consumer viability を発火させない。
- **成果物影響:** acceptance は「approved exact-one」と記録しても manifest CLIは拒否し、manifest ID・certified selection・report・ledgerは作られない。受領状態と実 consumer が乖離する。

## 総括

- **must-fix:** L1–L8、L10、L11。特に L2（D840との逐語衝突）、L3（consumer不在）、L5–L7（値域・環境依存）、L10（v1 trust root迂回）が実装前の停止理由である。
- **nit:** なし。各所見は受理集合、spec/manifest identity、report/verdict、または発行不能へ一行で到達する。
- **親 brief への反対:** A/B の実効編集面は素集合でなく、Aは既存 fixtureとの二重assemblerかつconsumer不在である。D840は既に実装済みではなく、現 consumer の内容再導出と逐語で衝突している。
- **裁定パッケージへ送る項目:** exact値のauthority、oracle除外理由表、v1 trust root利用可否とactive-v2前提、compiler/site束縛、preview→承認→同時設置、consumer positive control、generator失効、live docs/runbook/CLI導線、D356の保証限界。