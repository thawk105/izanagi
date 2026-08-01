判定は **NO-GO** です。静的レビューのみで、pytest・ビルド・実走は行っていません。

## 1. 「解禁」が production CLI に到達しない

**深刻度: BLOCKER**

**根拠:** ユーザー裁定は「計算ノードでの role 実行を解禁する」です。[brief.md:7](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:7)、[worklog.md:1506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/worklog.md:1506)。しかし plan 自身が、production caller は opt-in を渡さないと認めています。[plan.md:9](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:9)、[plan.md:88](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:88)。

実コードでも `_provider_set()` は constructor へ opt-in を渡さず、[p3_autonomous_workload_trial.py:628](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:628)、CLI に対応 flag がなく、[p3_autonomous_workload_trial.py:1090](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1090)、`main → run_trial → _provider_set` にも値を運ぶ口がありません。[p3_autonomous_workload_trial.py:1136](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1136)

**放置した場合:** `--provider claude-headless` は計算ノードで従来どおり proxy を落とし、最初の role が `invalid`、cell は `planner-invalid`、`stop_reason=role-invalid`、terminal report は `partial` になります。[p3_autonomous_workload_trial.py:826](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:826)、[p3_autonomous_workload_trial.py:711](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:711)。campaign WAL、candidate evaluation、`certified` outcome には到達しません。それでも D116/worklog に「解禁済み」と書けば、まさに発火しない保証です。

**推奨対応:** 明示 CLI flag を T-276 scope に入れ、`main → run_trial → _provider_set → ClaudeProjectedRoleProvider` まで配線してください。flag 省略時は `False`、明示時だけ admission とする境界テストが必要です。これは `dispatch_compute.py` に `campaign` task を足す T-236 ではありません。T-236 は login/compute 分割の実装であり、今回の all-on-compute opt-in とは別です。[worklog.md:1448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/worklog.md:1448)、[decisions.md:4972](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4972)。ただし build/bench は T-277 の measurement gate が別途残るため、T-276 単独で解禁できるのはまず role/no-build 経路です。

## 2. receipt は成功した外側台帳にしか残らず、proof chain へ届かない

**深刻度: BLOCKER**

**根拠:** brief は「試行台帳の各 role 行が transport identity を持つ」と主張します。[brief.md:61](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:61)。実際の consumer 閉包は次のとおりです。

| 層 | file:line | 実挙動 |
|---|---|---|
| producer | [claude_projected_provider.py:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:297) | `ProviderResponse.provenance` を生成 |
| trial ingest | [p3_autonomous_workload_trial.py:566](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:566) | `ProviderResponse` 型だけを検査し、`dict(...)` で無加工コピー。exact-key/schema gate なし |
| invalid attempt | [p3_autonomous_workload_trial.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:573) | error/error artifact だけ。transport receipt なし |
| journal | [p3_autonomous_workload_trial.py:403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:403) | generic JSONL writer。schema 検査なし |
| terminal report | [p3_autonomous_workload_trial.py:722](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:722) | in-memory event を `cells` へ複製 |
| hash | [p3_autonomous_workload_trial.py:756](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:756) | journal 全 bytes の SHA。receipt schema や report↔journal 一致は検査しない |
| proposal | [p3_autonomous_workload_trial.py:923](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:923) | planner/coder/auditor の解析値のみ。role provenance なし |
| campaign provenance/WAL 側 | [p3_s4_loop_trigger_gating.py:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_s4_loop_trigger_gating.py:503) | proposal path、auditor digest、variant、outcome のみ。transport receipt/hash なし |
| campaign report | [p3_s4_loop_trigger_gating.py:179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_s4_loop_trigger_gating.py:179) | `reports/` の側チャネルで、proof-chain 保護対象外 |
| freeze / plot | [test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_frozen_artifacts.py:38) | autonomous trial/transport policy は列挙なし。plot 経路にも当該 schema/field の consumer は 0 件 |
| 既存 test | [test_p3_autonomous_workload_trial.py:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:1012) | projected provenance の一部 field を個別確認するだけ |

plan も receipt が成功 attempt 限定であること、invocation failure には残らないことを認めています。[plan.md:120](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:120)、[plan.md:231](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:231)。

**放置した場合:** provider-init failure は `provider-init-error` の文字列だけになり、[p3_autonomous_workload_trial.py:1052](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1052)、invoke failure は proxy 注入済みでも receipt が落ちます。`attempts.jsonl` と `report.json` は login/direct、compute/proxy、legacy/custom を一意に区別できません。さらに role 出力から `certified` になった variant の campaign WAL/provenanceにも transport identity が結び付かず、外側 report を失えば certified outcome の生成経路を再構成できません。

**推奨対応:** admission receipt を invocation 前に run-level で確定し、`run-start`、成功・失敗の全 role event、terminal report に残してください。consumer 側で receipt の exact schema、policy SHA、endpoint SHA を検査し、missing/extra/hash mismatch を拒否する必要があります。proposal または campaign provenance/WAL には少なくとも run-level receipt digest を束縛してください。既定 direct 行にも receipt を足すなら既存 bytes 不変とは両立しないため、report/journal schema v2 として明示裁定が必要です。

## 3. 4 role が同じ transport を使う保証がない

**深刻度: MAJOR**

**根拠:** `_provider_set()` は planner/coder/auditor/critic の constructor を順番に4回呼びます。[p3_autonomous_workload_trial.py:631](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:631)。plan の設計では各 constructor がそれぞれ `current_site()` と policy を読むため、[plan.md:43](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:43)、read-once は「provider 1 個につき1回」であり「trial 全体で1回」ではありません。

receipt 同士を比較する run-level consumer も、4件の一致を拒否方向に発火させる負例テストも計画されていません。

**放置した場合:** provider 構築中に policy bytes が変わると、同一 generation の planner/coder/auditor/critic が異なる endpoint/policy SHA を持ったまま処理が継続します。report には違いが見えても拒否されず、複数 transport の role 出力を合成した proposal が campaign WALで1つの variant/outcomeになります。

**推奨対応:** transport admission は `_provider_set()` の前に1回だけ snapshot し、4 provider へ immutable copy を渡すか、4 receipt の exact 一致を invocation 前に検査してください。「4件中1件だけ policy SHA/endpoint SHA が異なる」positive control で、子 process が1つも起動しないことまで固定すべきです。

## 4. 固定 SHA vector は正しいが、非退化な独立 oracle ではない

**深刻度: MAJOR**

**根拠:** 提案された policy SHA と endpoint-map SHA は、記載 bytes から静的に再計算すると値自体は一致しました。[plan.md:107](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:107)。しかし実 endpoint は `http_proxy` と `https_proxy` が同値で、[plan.md:131](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:131)、key 順も既に辞書順です。

したがって次の実装変異は固定 vector、literal receipt、実 subprocess shim のすべてを通過できます。

- `https_proxy` に誤って `source_env["http_proxy"]` を入れる
- receipt の HTTPS 値を HTTP 値から複製する
- canonical JSON から `sort_keys=True` を外す

値が同一かつ入力順が既に sorted だからです。

**放置した場合:** 現 policy では偶然同値なので直ちに値は変わりませんが、将来 endpoint が分離したときに HTTPS が誤 route へ送られます。また key 順だけ違う同一 policy が異なる `endpoint_values_sha256` になり、レポート集計上は同じ transport が別 identity に分裂します。

**推奨対応:** 現 deployment vectorに加え、HTTP/HTTPS を異なる port/valueにした synthetic policy と、endpoint key を逆順にした第2 vectorを置いてください。key swap、片値複製、`sort_keys` 削除を mutation positive control にします。

質問 9 への直接回答として、SHA を hard-coded literal にすること自体は恒真ではありません。実 file だけを変えれば失敗するためです。ただし、policy bytes・expected bytes・SHA を同じ提案から同時生成しただけでは「site の正しい endpoint」を独立に証明しません。非恒真と言える条件は次です。

- expected SHA を test 実行時に policy/test literalから導出しない
- expected endpoint の権威を新 D の承認値または別保存した probe evidence に置く
- test fixture path を production 定数から作らない
- 上記の異値・逆順 vectorで配線と canonicalization を独立に検査する
- policy/testを同時更新する場合は D96どおり、新 D の人間レビューを oracle とする

## 5. 拒否条件の positive control が不足している

**深刻度: MAJOR**

**根拠:** plan の拒否仕様は [plan.md:43](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:43) に対し、テスト一覧は [plan.md:166](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:166) です。site、TLS 7 key、未受理 proxy 名、required pair、値 drift、基本的な filesystem/JSON/schema は挙がっています。一方、次は負例が明記されていません。

- `source_env` 非 `Mapping`、`repository_root` 非 directory
- constructor の `allow_pegasus_compute_transport` が `1`、`"true"`、`None`
- policy URI 自体の `https:`、port 欠落、userinfo、query、fragment、control character
  `source_env` 側の userinfo drift は単なる policy 値不一致であり、URI validator を削除しても失敗するため positive control ではありません
- ancestor component symlink と final symlink の区別、read error、size 上限ぴったり/上限+1
- `current_site()` の exactly-once、policy の exactly-once read
- endpoint drift エラーに attacker-controlled 実値が含まれないこと
- missing/extra/malformed receipt を trial consumer が拒否すること
- report の receipt と `attempts.jsonl` の receipt が一致すること
- import 時に site 判定や policy readをしないこと

とくにエラー文字列はそのまま invalid event または `fatal_error` へ保存されます。[p3_autonomous_workload_trial.py:582](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:582)、[p3_autonomous_workload_trial.py:1052](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1052)。単に `pytest.raises` するだけでは値漏洩変異を殺せません。

また実 subprocess shim が観測できるのは child の env だけです。CLI が proxy を実際に利用したこと、TCP peer、CONNECT、証明書 chain は証明しません。plan 自身もこの限界を認めています。[plan.md:228](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:228)。したがって brief の「proxy は CONNECT metadata しか見えない」は、このテストでは発火不能な assert です。[brief.md:50](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:50)。

**放置した場合:** URI validatorやredactionを丸ごと削除してもテストが緑になり得ます。attacker-controlled endpoint/credential が trial reportへ残る、または未検査 policy が受理され、role 出力・proposal・candidate outcomeが変わります。

**推奨対応:** 上記を1 caseずつ parameterizeし、単に「raiseした」ではなく、error code、leaf/policy read/runner call count、秘密 sentinel の不在まで検査してください。MITM 防止は主張せず、「列挙 env overrideをforwardしない」までに限定すべきです。

## 6. D96 は leaf API にしか掛からず、実際の受理集合を固定していない

**深刻度: MAJOR**

**根拠:** D96 は新 D と「その受理集合を固定する境界テスト」を同一変更単位に要求します。[decisions.md:4271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4271)。plan は D116 と leaf test を予定しているため形式的な方向は正しいですが、[plan.md:211](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:211)、固定するのは leaf/provider API の受理集合だけです。実 CLI acceptance、run-level receipt 一致、ledger consumer acceptance は未固定です。

既存境界テストの判定は次のとおりです。

- [test_p3_autonomous_workload_trial.py:995](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:995) は opt-out/default の env 境界としては生きていますが、名前上は provider 全体の保証に見え、opt-in 追加後は射程を明記すべきです。
- [test_s8b_prediction_runner.py:887](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_s8b_prediction_runner.py:887) の literal 5-key env と [同:920](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_s8b_prediction_runner.py:920) の exact 8-key provenance は意味を失いません。
- registry test は所在・tracked・閉集合だけを検査し、policy の意味やlive consumerを保証しません。[test_pegasus_policy_registry.py:354](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:354)。D115も inventory は run の再導出元ではないと明記しています。[decisions.md:5420](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:5420)。

さらに新 `test_claude_transport.py` には自走 harness または pytest-only allowlist登録が必要です。そうでなければ `python3 test_claude_transport.py` は0件実行・exit 0になります。[orchestrator/tests/README.md:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/README.md:107)。full suite の meta-test は検出しますが、plan はこの検査を列挙していません。[test_plain_runner_coverage.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_plain_runner_coverage.py:60)。

**放置した場合:** D116 に「CLI解禁」「各role行にreceipt」と書きながら、実際に固定されるのは呼ばれないAPIと成功provider単体だけになります。台帳・report・campaign provenanceを落とす変異が検出されません。

**推奨対応:** D116、leaf tests、provider tests、CLI flag境界、4-role一致、invalid event、journal/report/campaign provenance E2Eを同一commitに入れてください。implementation commitとdocs commitを分けず、D96の「同一変更単位」を明記する必要があります。

## 7. 「既定は1 bitも変わらない」は射程が広すぎる

**深刻度: MINOR**

**根拠:** repo-wide caller は production 1箇所と直接 constructor test 4箇所で、plan の列挙は正しいです。[p3_autonomous_workload_trial.py:635](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:635)、[test_p3_autonomous_workload_trial.py:731](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:731)、[同:978](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:978)、[同:997](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:997)、[同:1021](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:1021)。全て新引数省略なら subprocess env/argv/provenance の既定値は維持可能です。

ただし plan は default objectへ `self.transport_receipt = None` を追加するため、[plan.md:62](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:62)、`vars(provider)`、pickle/introspection、module import graph、registry/file bytesまでは不変ではありません。また「leafを呼ばない」testは通常module import後にmonkeypatchするため、import-time policy read/site判定を検出できません。

**放置した場合:** 現行成果物の値は通常変わりませんが、import時副作用やobject shapeの変化を「1 bit不変」と誤記録します。import failureなら既存login callerも起動不能になります。

**推奨対応:** 不変条件を「flag省略時の child argv/env、既存17-key response provenance、journal/report bytes」に限定してください。fresh subprocessでmodule importだけを行い、policy read/current_siteが発火しないことも検査します。

## 8. 親 brief の実測3主張の独立判定

**深刻度: MINOR**

**根拠と判定:**

- 「ログインノードにproxyがない」
  必須の `probe-out.txt` は bnode009 のみで、login証拠を含みません。[probe-out.txt:1](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:1)。本レビュー時の read-only確認では `hostname=pegasus02`、該当proxy key名0件で点観測は再現しました。ただし「全login node/profile/surface」への一般化は未成立です。
- 「禁止はproseのみで機械gateなし」
  **支持します。** 禁止本文は D108 とrunbookです。[decisions.md:4965](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4965)、[pegasus-runbook.md:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/pegasus-runbook.md:428)。`guard_bash` のheavy command列挙にClaudeはなく、[guard_bash.py:598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/hooks/guard_bash.py:598)、防護pathを含まなければfast pathで許可されます。[guard_bash.py:880](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/hooks/guard_bash.py:880)。現providerがproxyを落として通信失敗するのは機能的不通であり、computeを認識して拒否するgateではありません。
- 「projected provenanceにexact-key gateなし」
  **支持します。** `_invoke()` は型確認後に無加工コピーし、[p3_autonomous_workload_trial.py:566](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:566)、journal/reportもgenericです。この不在は互換性の根拠ではなく、receipt integrityを検査するconsumer不在という欠陥です。

compute probe自体は、scriptが `env -i` で5+2 keyを明示しており、[probe.sh:27](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe.sh:27)、A=rc0/B=rc1も raw outputにあります。[probe-out.txt:17](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:17)。ただし1 allocation・1 node・1 profile・1 CLI版の証拠です。全bnodeや将来profileへの一般化は不可です。

**放置した場合:** profile drift時はexact policy admissionがfail-closedになり、provider-init-error、空cells、`report.status=partial`へ変わります。安全側ですが「Pegasus computeで解禁済み」という可用性主張は偽になります。

**推奨対応:** 新Dとrunbookは「bnode009の当該profile/CLIで観測」と限定し、runごとのsite、CLI SHA、policy SHAをreceiptへ残してください。

## 凍結波及の判定

この点は親境界を反証できませんでした。s8b除外は現scopeでは正当です。

- 共有定数は5 keyのままです。[s8b_prediction_runner.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:71)
- projected providerがs8b helperを一方向importしており、逆importはありません。[claude_projected_provider.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:22)
- s8b providerのenv投影は共有5 keyだけです。[s8b_prediction_runner.py:1153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1153)
- s8b producerは8 key、[s8b_prediction_runner.py:1303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1303)、freeze consumerもexact 8 keyです。[s8b_selector_freeze.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_selector_freeze.py:88)、[s8b_selector_freeze.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_selector_freeze.py:223)
- `FROZEN_MANIFEST` は既発行s8b出力23件を固定しており、新policy/provider sourceは対象外です。[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_frozen_artifacts.py:38)

したがって `CLAUDE_ENV_ALLOWLIST`、`ProviderResponse` の共有形、`ClaudeHeadlessProvider`、既存s8b outputを変更しない限り、transport追加はs8b bytesへ到達しません。将来s8bもcompute対応するなら、今回へ便乗せず、exact 8-key schemaと凍結成果物再発行を伴う別裁定にすべきです。

## 総括

**NO-GO。**

最重要3件は次です。

1. production CLIへopt-inが届かず、「解禁済み」と書けば発火しない保証になる。
2. receiptが成功した外側journal/reportにしか残らず、invalid attempt・campaign WAL・certified outcomeのproof chainへ束縛されない。
3. 固定SHA vectorが「同値2 endpoint＋既にsorted」の退化入力で、key取り違え・片値複製・`sort_keys`削除を検出できない。

段4では、CLI flag配線、run-level admissionの単一snapshot、全attempt＋campaign provenanceへのreceipt digest束縛、consumer exact gate、異値・逆順vectorをscope内へ入れたplan v2が必要です。