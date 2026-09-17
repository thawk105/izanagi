## must-fix (番号・file:line・成果物影響 1 行・是正案)

なし。静的検査で、受理集合・pin・receipt・台帳を破損する実装不備は確認できなかった。pytest・変異実走・最終 commit の監査は未実施。

## nit

1. **凍結説明の適用範囲が曖昧。** `.claude/agents/planner-v4.md:52–55` の「最新測定値ではない」「iteration ごとの結果は whiteboard でだけ届く」が手動経路にも掛かって読める。両文を「8c 自動 trial では」に明示的に限定する。現物の pin 不整合や receipt 不受理は示せないため nit。

2. **「旧 SHA の記録なし」「§5 未記入」は限定が必要。** `output/insights/2026-08-26/t1697-closed-critic-invocation/verbatim/liveness-probe-real-cli.txt:4` に旧 critic SHA の実 CLI provenance が残る。ただしこれは closed receipt ではない。また `docs/phase3-b4-reflux-ablation-preregistration.md:158–167` は一部記入済みで、prompt／projection hash 欄が未記入。「再受理対象の B-4 receipt は検索で未発見、prompt／projection pin は未登録」と書くのが正確。

## 検算した事実の一覧 (確認 / 反証)

1. **確認 — 4 SHA と Reviewed 行。**
   `orchestrator/codex_roles/review_ledger.py:37–51` の4値を role ファイルの SHA-256 と直接照合し、全件一致。adapter の `review_ledger.source_file_sha256`／`source.sha256` とも一致した。

   | role | 検算した SHA の先頭 |
   |---|---|
   | trigger-gating | `baccfeba3cca` |
   | critic | `51420a1dac35` |
   | critic-experiment | `9b8b753161a5` |
   | planner-v4 | `6c4bb5abbf3f` |

   Reviewed 行は既存と同じ日付・タスク・説明のコメント形式。author の render 前 rc=1 と、依頼文にある親の render 後 rc=0 は矛盾しない。親の実行ログそのものは今回の確認対象資料にはない。

2. **確認／一部反証 — baseline 追随。**
   `orchestrator/tests/test_reflux_originless_compatibility.py:702–738` は既存 helper と同じ固定 old/new 値、置換件数、report 値の assertion を使う。各 role の journal **6行**、report **1行の集約値 `[sha, 6]`** を確認した。baseline literal と helper をメモリ内で評価し、**386 keys** を再確認した。

   「3 role とも T-304 の new 値から繋がる」は厳密には反証。`:660–681` の T-304 helper が更新するのは planner／coder だけであり、この2本は完全一致する。critic は baseline の既存値 `cd1c3652…` を引き継ぐため、実装は正しい。

   auditor は不変、critic-experiment はこの baseline に対象行なし。新 helper と呼出しを除いた AST が HEAD と一致し、`:374` の `_volatile`、`:741` の `_assert_same_structure` を含む既存比較処理は不変だった。

3. **確認 — adapter render。**
   変更された4 adapter の JSON 差分は次の4 field だけ。他10 adapter は不変。

   - `review_ledger.source_file_sha256`
   - `source.sha256`
   - `semantic_digest`
   - `developer_instructions`

   `orchestrator/codex_roles/spec.py:795–801` の本文埋込み規則と一致し、4本とも埋込み本文を role 本文と照合済み。さらに `expected_adapters()` の出力と**全14ファイルの bytes が一致**した。

4. **確認 — 変異の検出経路。ただし kill は未実測。**
   M1／M1a／M1b／M1c はそれぞれ旧 SHA を baseline に残すため、`:1332` の同一 test 内、`:1409` の固定 baseline 比較を失敗させる見込み。`:1319` の対照 test は現行出力同士の比較なので、この変更に依存しない。

   M2 は `test_codex_agents.py:27` → `tools/check_codex_agents.py:44` → `spec.py:587` で import 時拒否。harness 外で checker の非ゼロ rc と **`SOURCE_FILE_SHA256 drift` 診断の両方**を判定する裁定は妥当。

   `tools/mutation_harness.py:1253` は `FAILED ` 行だけを抽出し、`:1543–1554` は collection 不成功を拒否。`:2084–2094` は異常 rc／失敗 node なしを `PARSE_ERROR` とし、`:3294–3298` で停止する。collection error を harness の KILLED と計上できない。

   M0 は等価。`spec.py:745–791` の hash 入力は台帳の定数値と role 本文であり、Reviewed コメントや ledger ファイル全体の bytes は含まれない。

5. **確認 — provenance の必要構成。**
   `tools/check_ai_provenance.py:76,1599–1628` により adapter JSON も実装面で、Codex author が必要。`docs/ai-provenance.md:19–33,47–52` に従い、1 commit の最終 trailer block を次の構成にすればよい。山括弧部分は実際の表示値で置換する。

   ```text
   AI-Agent: product=codex; model=<実表示>; reasoning=<実表示>; role=author; scope=ledger-baseline
   AI-Agent: product=codex; model=<実表示>; reasoning=<実表示>; role=reviewer; scope=review-b
   AI-Agent: product=<親の製品>; model=<実表示>; reasoning=<実表示>; role=integrator; scope=docs-adapter-render
   ```

   他の reviewer も記録し、同一 role が複数行なら各行に scope を付ける。これは構成例であり、未作成 commit の監査成功を意味しない。

6. **確認 — 不変部分と変更部分の境界。**
   統合差分は指定の13ファイル。以下は変更されていない。

   | 対象 | 現物 |
   |---|---|
   | `_PERF_KEYS`・入力検査 | `orchestrator/campaign/autonomous_trial_completeness.py:435`、`s8c_generation_projection.py:58,664` |
   | manifest pin | `orchestrator/codex_roles/review_ledger.py:60` |
   | template pin | 同 `:84` |
   | IO contracts | 同 `:191` |
   | renderer・validator | `orchestrator/codex_roles/spec.py` |
   | schema_version | adapter JSON、既存 baseline とも今回の変更なし |

   変わるのは role 本文 bytes、prompt bytes、source SHA、semantic digest、およびその追随値。**検査述語不変から、過去 receipt の受理不変までは導けない。** `p3_b4_closed_critic.py:1658,1679` は現行 role／projection hash と比較するため、旧 receipt があれば拒否され得る。

   `git grep` では旧 SHA が baseline と過去の insight 記録に残ることを確認。既存 registry／prereg に今回の旧4 SHA を固定する参照、再受理対象の B-4 receipt は見つからなかった。selector の凍結記録は別 role。repo 外・未追跡成果物まで存在ゼロとは証明していない。

## 総括

GO — 静的検査では pin 追随・全14 adapter の再現性・変異判定経路は整合している。実走の成功と最終 commit の provenance は別途確認が必要。