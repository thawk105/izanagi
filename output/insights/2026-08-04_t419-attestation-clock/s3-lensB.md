結論は **現プランのままでは NO-GO** です。S1 の局所ロジックは発火可能ですが、`registered/` への登録全体を守る gate にはなっておらず、P4 の独立実装理由と S2 の fact pin にも穴があります。pytest は実走しておらず、以下は静的検査と既存 artifact の軽量再計算だけに基づきます。

## 1. 射程 — CLI writer は 1 本だが、登録経路は 1 本ではない

`rg` で確認したコード化済みの自動 writer は `_certify_main` だけです。

| 経路 | 判定 | 根拠 |
|---|---|---|
| Pegasus sanctioned job | S1 を通る | wrapper は固定で `--certify --env-tag pegasus` を呼ぶ。[certify_calibration.sh:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/tools/pegasus/certify_calibration.sh:720) |
| 直接 `calibrate.py --certify` | S1 を通る | canonical slug の任意 env tag が同じ `_certify_main` に入る。[cli.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:462)、[cli.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:686) |
| 自動 publish / fallback | S1 を通る | in-memory artifact を create-only で `registered/` に置く。[cli.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:613)、[cli.py:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:620) |
| 同一 bytes の再 publish | 既存どおり拒否 | no-replace collision。[cli.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:297)、[test_calibrator_certify.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:508) |
| 通常の非-certify CLI | `registered/` へは書かない | `output/env/<tag>/calibration/calibration_t*.json` に上書きする別形式。[cli.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:715) |
| S1/S2 検証用別スクリプト | `registered/` へは書かない | calibration 直下の固有名へ出力。[s1_verify_extime_calibration.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/s1_verify_extime_calibration.py:435)、[s2_verify_calibration.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/s2_verify_calibration.py:370) |
| テスト | production への別 writer ではない | `tmp_path/output/.../registered` で同じ CLI を通すか、一時 repo に copy するだけ。[test_calibrator_certify.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:294)、[test_env_contract.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:444) |
| Git 直接追加、old worktree、attempt からの copy、外部持込み | **S1 を迂回する** | `registered/` は write hook の管轄外で通常書込みを許す。[guard_write.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/hooks/guard_write.py:133) |

最後の層が must-fix です。現物も過去 commit `26a9ad6a...` で attempt、registered copy、`env_contract` pin が同時に Git へ追加されています。今後も古い checkout の pre-S1 calibrator、外部生成 v2、あるいは `attempts/.../calibration.json` を直接追加して pin を更新できます。

しかも consumer admission はこれを止めません。required-mode loader が検査するのは hash、schema、env tag、clock までで、`quality.status == accepted` も自己述語も要求しません。[env_attestation.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:674)–[692](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:692)。schema も rejected artifact を正規に表現でき、自己帯内性は見ません。[schema_v2.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:420)、[schema_v2.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:468)。

したがって、S1 が狭めるのは「現版 `_certify_main` の publish 集合」だけです。「registered/ の受理集合を構造的に狭める」は refuted です。

## 2. 恒真性と latch

S1 は恒真でも constant-false でもありません。

- 現登録 artifact は中央値 2101.0、許容帯 `[2058.98, 2143.02]` に対して 3080.935 を含み、自己比較は false です。[artifact:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440)、[artifact:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484)、[artifact:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1493)。
- 合成 fixture `[2400, 2410, 2390]` / 5% は正例として通ります。[test_calibrator_certify.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:216)。
- 一方、実 probe は `/proc/cpuinfo` の全 CPU 値を一回読むため、親実測 16/16 と観測者効果から Pegasus の現 producer は事実上閉じています。[env_attestation.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:390)、[brief.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/insights/2026-08-04_t419-attestation-clock/brief.md:16)。

これは正しさ上は妥当な fail-closed です。自己不整合な較正を publish できなくなることを「悪化」と数えるべきではありません。ただし運用上は、α等の probe 是正まで sanctioned certification の受理集合が既知の空集合に近くなります。S1 は「回復」ではなく「封じ込め」です。

P3 の probe 是正 scope 外は、ユーザー裁定と凍結 bytes 更新が要るため妥当です。ただし P1 の「今日より悪くない」は certified 成果物についてのみ real で、取得可用性まで含めると refuted です。

## 3. tolerance が gate の迂回ノブになっている

S1 は artifact 内の tolerance を信頼しますが、その値の権威は束縛されていません。

- CLI と submitter は `0 < tolerance <= 100` だけを要求します。[cli.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:471)、[submit_certify.sh:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/tools/pegasus/submit_certify.sh:32)。
- 値はそのまま profile へコピーされます。[cli.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:537)。
- AcquisitionReceipt には tolerance、calibrator source commit、gate version がありません。[schema_v2.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:502)、[certify_calibration.sh:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/tools/pegasus/certify_calibration.sh:595)。

現 artifact は 2% なら false、100% なら true です。したがって「自己述語を満たす」という狭い契約には適合しますが、「強い環境同一性 gate」と宣伝するなら tolerance の由来を policy／smoke receipt に束縛しない限り不十分です。100% 正例を raw comparator の仕様として固定する段2案 [s2-plan.md:100](/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/s2-plan.md:100) は、この未解決入力を安全値として見せる危険があります。

## 4. P4 の独立実装は一意の正解ではない

P4 の根拠には誤りがあります。receipt issuer と consumer は既に別実装です。

- issuer: `_recorded_verdict`。[env_attestation.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:564)
- consumer: `_independent_comparison_passes`。[execution_guard.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158)

publisher と consumer が純粋 comparator を共有しても、この issuer–consumer 独立性は失われません。失われるのは publisher–consumer 間の common-mode 耐性だけです。

この不変条件の正本は「実行時 consumer に一致すること」なので、drift 時には consumer が正です。段2案はその権威順を明文化していません。安全な択一は次の二つです。

1. publisher と consumer は canonical pure predicate を共有し、issuer だけを独立に保つ。
2. 3 実装を維持するなら、consumer が正であることを明記し、独立 golden vector で両者を別々に判定する。

後者を選ぶ場合、現表は不足しています。`[90, 110]` は mean も median も 100 なので、段2が主張する median→mean drift を検出しません。[s2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/s2-plan.md:88)、[s2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/s2-plan.md:131)。また tolerance 0・負値は schema 到達不能なので、その挙動を load-bearing に pin しても certified artifact の受理集合を守りません。[schema_v2.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/schema_v2.py:235)。

表が捕まえるのは列挙済みの境界、`all→any`、型エラーだけです。捕まえないのは、wrapper の field 配線、canonical expected/observed の組立て、未列挙の valid-domain 値、将来 field/schema が増えた場合、および両実装を同時に同じ誤仕様へ更新する drift です。

## 5. `assert not` fact pin

現 artifact が false であるという事実自体は real で、strict xfail より直接 `assert not` の方が unrelated exception を隠しません。

ただし、単純に `ec.lookup("pegasus")` の現 pinを読み `assert not` するだけでは、将来の反転を十分強制しません。

- 新しい self-pass artifactへ pin を動かせば赤になる点は有効。
- 新しい artifactを追加しただけで旧 pinを残せば緑のまま。
- pin と golden を別の self-fail artifactへ同時更新しても緑のまま。
- 新 env tag の required-mode entryには効かない。
- consumer が constant false になっても、この test 単独は緑になる。

最低限、既知例外を現 path+SHA の exact pair に限定し、「その pair 以外の required-mode registry entry は必ず self-pass」とする補集合テストが必要です。これは manual/import 層の gateにもなります。

fact pin 単独は production の値・受理集合・参照を変えないため、DW-G05 上は must-fix ではなく移行診断です。must-fix なのは negative publish test と、既知例外以外を正向きに検査する registry invariant です。

## 6. 受理集合と staging／下流

推奨位置へ追加した場合、CLI publish 集合は厳密に

`旧 accepted 集合 ∩ self-comparison-pass`

となるので、局所的には「狭めるだけ」は real です。現登録 artifact と同型の候補は accepted から rejected へ移ります。

出力形については、段2の推奨なら既存 quality rejection と同じです。

- `calibration.json`、`calibration.md`、`window-probes.json` を作る。
- `candidate.json`、`publish.json`、新規 registered artifact は作らない。
- 例外経路でないため `rejection.json` は作らない。

根拠は [cli.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:593)–[611](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:611) と既存品質負例 [test_calibrator_certify.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:481) です。したがって `rejection.json` schema が壊れる懸念は refuted です。

ただし、既に別理由で rejected だった attemptにも新 reasonが追加され、新規 attempt の `calibration.json` bytes／final receipt manifestは変わります。`calibration.md` は status しか出さず reasons を載せません。[cli.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:600)。これは診断性の nit です。

DW-G05 の一行は次です。

- **S1なし:** otherwise-qualified な self-fail artifactに registered hash/pathが発生し、env contract・proof chainが runtime consumer と不整合な参照を束縛し得る。
- **registry/import層なし:** 同じ不整合参照を Git直接追加・old producer・attempt copyで作れるため、S1の成果物効果が迂回される。
- **tolerance権威束縛なし:** 過大 tolerance の artifactが登録され、異なる実効クロック環境でも receipt／certified結果の受理集合が広がる。
- **probe是正なし:** 現 pinは不変で、Pegasus campaignの certified選択・材料レポート・試行台帳は引き続き新規生成されない。
- **fact pinなし:** production成果物は変わらず、既知欠陥の診断だけが失われる。

なお既存 E2E は samples を帯内へ clamp し toleranceを100へ置換するため、物理 Pegasus の回復証明にはなりません。[test_s8b_floor_campaign.py:3446](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_s8b_floor_campaign.py:3446)–[3477](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_s8b_floor_campaign.py:3477)。S2はS1ロジックの正負例にはなりますが、「実 producerが通る」という主張はできません。

## 7. scope 外で返すべき consumer 層

`execution_guard` が唯一の attestation predicateという前提も project-wide には false です。`silo_ladder_rung1` は registered artifactを直接読み、全 observed samplesではなく expected median と observed medianだけを比較します。[silo_ladder_rung1.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/silo_ladder_rung1.py:1932)、[silo_ladder_rung1.py:1961](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/silo_ladder_rung1.py:1961)。S1合格 artifactはこの自己比較も通るためS1 implication自体は壊しませんが、runtime受理集合は execution_guard より広いままです。材料成果物へ影響する別 consumer として裁定パッケージへ返すべきです。

## 総括

- **所見と real / refuted**
  - **REAL:** コード化済み自動 writer は `_certify_main` の1本だけ。[cli.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:613)
  - **REFUTED / must-fix:** S1が `registered/` への全経路を守る。Git直接追加、old worktree、attempt copy、外部持込み、pin更新を loaderもhookも拒否しない。[env_attestation.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:674)、[guard_write.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/hooks/guard_write.py:133)
  - **REFUTED:** S1は恒真または論理的constant-false。合成正例は通る。[test_calibrator_certify.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:216)
  - **REAL / 裁定要:** 現物理Pegasus producerの受理集合は実測上ほぼ空で、S1単独は回復でなくfail-closed封じ込め。[brief.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/insights/2026-08-04_t419-attestation-clock/brief.md:16)
  - **REAL / must-fixまたは明示scope外:** toleranceは手入力で権威束縛されず、100%なら現artifactも自己検査を通る。[cli.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:471)
  - **REFUTED / must-fix:** P4の「共有するとissuer–consumer独立性が失われる」。receipt issuerは別実装のまま。[execution_guard.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158)、[env_attestation.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:564)
  - **REAL / must-fix:** 提案した even-median vectorはmean driftを検出しない。[s2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/s2-plan.md:88)
  - **REALだがnit:** 現artifactのdirect `assert not` は正しい移行事実。
  - **REFUTED / must-fix:** 単純なfact pinが将来の反転を十分強制する。新しいself-fail pinにも緑になるため、exact既知例外＋それ以外正向きの補集合が必要。[env_contract.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_contract.py:186)
  - **REAL局所・REFUTED全体:** S1はCLI publish集合を狭めるだけだが、システム全体のregistered受理集合は狭まらない。
  - **REFUTED:** 推奨位置で `rejection.json` やcollector形が壊れる。既存quality rejection形と同じ。[cli.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:595)
  - **REAL:** execution_guard以外にmedian-to-medianの直接consumerが残る。[silo_ladder_rung1.py:1962](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/silo_ladder_rung1.py:1962)

- **scope外だが返すべき層**
  - registered tree／env-contract pin更新時の land admission。
  - old checkout・外部artifact・attempt copyの provenance／semantic admission。
  - toleranceのsmoke/policy receipt束縛。
  - `silo_ladder_rung1` の別attestation受理集合。
  - probe α、再取得、path/hash/contract hash更新。

- **段4で親が決めるべき択一**
  - **登録面:** 推奨は「CLI S1＋現path/SHAだけを既知例外とするregistry全走査」。対案は accepted schema/loaderで即時強制し、現artifactを直ちにload不能にする。
  - **述語所有:** 推奨は publisher–consumerのcanonical pure predicate共有＋issuer独立。対案は3独立実装だが、consumer正本の明記と識別力あるgolden vector修正を必須にする。
  - **投入時期:** 推奨は封じ込めを先にlandし、certification停止を明記してαを別裁定へ送る。対案はα＋再取得＋positive反転まで原子的に待つ。
  - **tolerance:** 今waveで権威束縛するか、少なくとも再登録前blockerとして明示するか。未裁定のまま「正しさgate」とは呼ばない。

- **must-fix**
  - CLI外のregistered/pin層を閉じるか、S1の主張をCLI限定へ明確に縮める。
  - tolerance権威の扱いを裁定する。
  - predicateの正本とdrift解決方向を明記する。
  - median→meanを本当に殺す表vectorへ直す。
  - exact既知例外＋将来entry正向きのregistry invariantを置く。

- **nit**
  - fact pin単独、reason codeの綴り。
  - `calibration.md` にreasonsを表示すること。
  - post-benchmark rejectionかpre-benchmark fail-fastかの資源効率。
  - schema到達不能な tolerance 0／負値ケースをraw comparator仕様として残すかどうか。