pytest、campaign、floor 実測は実行していない。以下はファイル、全 Git ref、dangling commit、他 worktree、job 保存域の静的検査結果であり、テスト緑は主張しない。

## 見落とされた成果物

- **refuted** 既存の reviewed spec、v2 世代、budget approval は見つからない。到達可能な全 126 ref のうち対象 module を持つ 77 ref は、両 pin とも非 `None` が 0 件だった。全 Git object、dangling commit の tree、全 worktree、dev-wave job 保存域にも canonical path はない。現行 authority も `APPROVED_SPEC_SHA256 = None` と `BUDGET_APPROVAL_SHA256 = None` のままである。`orchestrator/campaign/s8b_oracle_spec.py:18-23`、`orchestrator/campaign/s8b_holdout_freeze.py:45-50`

- **refuted** docs 内の JSON は承認済み artifact ではない。reviewed spec は schema 例であり、当該 wave が canonical 2 pathへ実ファイルを作らないと明記する。budget も仮のゼロ値と一般名の approver を置いた schema 例で、発行 API は実装しない契約である。`output/insights/2026-08-11_t750-freeze-v2-manifest/verbatim/s2-plan.md:175-183`、`同:122-146`

- **refuted** `PIN_GATE_SPEC_RAW` は見た目が最も近いが、実 reviewed spec ではない。`ccbench_pin="pin"`、`env_tag="test-env"`、ゼロ hash、`genome_canonical="g"`、`n=1` などを持つ独立テスト golden である。別 helper も `n`、seed、campaign ID、除外理由を caller から受け、pin を monkeypatch する。`orchestrator/tests/test_s8b_oracle_manifest.py:64-99`、`orchestrator/tests/s8b_oracle_spec_fixture.py:38-89`、`同:102-113`

- **real** alternate root には official 形の floor result、budget approval、v2 candidate を合成できる test helper がある。ただし自身を `synthetic-only tmp git repository` と明記し、`fixture-human`、便宜値 100 と 50、合成 floor を使う。これは schema の正例であって、実測または承認の証拠ではない。`orchestrator/tests/s8b_v2_freeze_fixture.py:193-222`、`同:264-288`

## 前提を満たす順路

- **refuted** budget 数値が別裁定で承認済みという経路はない。承認済みなのは pinned literal 方式であり、数値自体は後段の人間承認対象である。現コードは pin が `None` なら入力を読む前に拒否する。過去資料も 100 と 50 は test fixture の便宜値だけと明記する。`output/insights/2026-08-11_t750-freeze-v2-manifest/package.md:20-22`、`orchestrator/campaign/s8b_holdout_freeze.py:1161-1168`、`output/insights/2026-08-11_t8b-restart-integration/verbatim-plan.md:442-447`

- **refuted** official floor result も「あとは記入するだけ」ではない。production core は official を無条件拒否し、pilot は再凍結不適格である。tracked な official job result 2 件も `s8b-floor-result/v2` ではなく wrapper 記録で、`driver_rc` は 1 と 2 である。`orchestrator/campaign/s8b_floor_campaign.py:210-220`、`docs/phase3.md:118-123`、`output/env/pegasus/floor/job-staging/0:873225.nqsv/job-result.json:1-12`

- **refuted** approvalと pointer だけを先行設置する順路はない。v2 candidate producer はまず budget pin、budget bytes、official floor result を検証する。ratified resolver は canonical generation record を索引し、pointer がその実在世代を指さなければ拒否する。`orchestrator/campaign/s8b_holdout_freeze.py:1368-1405`、`orchestrator/campaign/s8b_ratified_freeze.py:1092-1101`、`同:1231-1256`

## 親の一般化への反証

- **real** 「spec の書き手が存在しない」は production に限定すれば正しいが、一般命題としては誤りである。test helper は arbitrary root に spec を構築、設置でき、driver、report、judge には root 差替え面もある。ただし production の `build-approved` は current `ROOT` を固定し、spec を生成せず消費するだけなので、現在の (A) は開かない。`orchestrator/tests/s8b_oracle_spec_fixture.py:38-113`、`orchestrator/campaign/s8b_oracle_driver.py:1646-1659`、`orchestrator/campaign/s8b_oracle_manifest.py:1170-1251`

- **real** 「設置は即赤」は現行 worktree の schema v1 に限定される。contract test は自身の `ROOT` だけを走査するため、別 root の fixture は対象外である。また D302 は durable 発行後の変更には再発行が必要と定めており、将来の正式な schema 再発行まで永久禁止してはいない。ただし現在は再発行も reviewed bytes もない。`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-143`、`docs/decisions.md:14013-14019`

- **real** v2 candidate directoryの不在自体は blocker ではない。writer は固定 candidate path の親 directory を安全に新規作成できる。真の blocker はその前段にある budget pin と official floor である。`orchestrator/campaign/s8b_holdout_freeze.py:1451-1497`

- **real** 「AI は approval commit を物理的に作れない」も広すぎる。検査するのは actor の身元ではなく逐語 `AI-Agent: none` であり、規約はユーザーが exact 内容を決定した後の機械的 Git 代行を AI 関与として記録しない。したがって exact bytes へのユーザー承認が既にあれば機械代行は可能である。今回はその exact bytes がなく、AI 自身が承認判断をすれば実質的関与になるため、この例外は使えない。`orchestrator/campaign/s8b_ratified_freeze.py:524-547`、`docs/ai-provenance.md:67-74`、`docs/decisions.md:3773-3775`

- **refuted** D328 を (B) の独立 blocker とする親の補強は成立しない。D328 は correctness と admission を明示的に対象外とし、同日の既存敵対相談も reviewed spec、approvalと pointer、`reverify_published_freeze` を明示的な keep 集合へ入れるよう要求している。現行 report と judge がその再検証を呼ぶのは、保留解除ではなく正しさ経路として整合する。`docs/decisions.md:14784-14793`、`output/insights/2026-08-12_freeze-chain-hold-sweep/verbatim/s3-consult-sol.md:110-120`、`orchestrator/campaign/s8b_oracle_report.py:1753-1770`

## 今日できる部分

- **real** AI が今日正当に完了できるのは、docs の readiness 記録と D328 判定の訂正である。(A) は candidate 不在、研究値未確定、canonical 不在、pin `None`、(B) は budget pin 不在、official floor 不在、generation 不在、exact user approval 不在、と機械可読に記録できる。canonical namespace、pin、承認 record、受理集合には触れないため正しさゲートを緩めない。`brief.md:49-53`、`orchestrator/campaign/s8b_oracle_spec.py:182-200`、`orchestrator/campaign/s8b_holdout_freeze.py:1161-1168`

- **refuted** artifact 側に今日完了可能な部分はない。特に (A) の `n`、master seed、block size、campaign ID は未確定で、schema-valid な draft を作っても reviewed にはならない。(B) の test fixture や pilot 結果を昇格することも承認と実測の意味論を失わせる。`output/insights/2026-08-11_t804-spec-sha256/brief.md:24-38`、`orchestrator/campaign/s8b_holdout_freeze.py:1252-1259`

## 総括

- **real** (A) 親の実施不能判定は妥当。決め手は reviewed bytes と研究設計値が未確定のまま pin が `None` であること。`orchestrator/campaign/s8b_oracle_spec.py:21-23`、`output/insights/2026-08-11_t804-spec-sha256/brief.md:24-31`
- **real** (B) 親の実施不能判定は妥当。ただし D328 と「AI は commit 不可」は決め手ではなく、budget pin、production official floor、canonical generation の三者不在が決定的である。`orchestrator/campaign/s8b_holdout_freeze.py:1161-1164`、`orchestrator/campaign/s8b_floor_campaign.py:210-220`、`orchestrator/campaign/s8b_ratified_freeze.py:1231-1256`