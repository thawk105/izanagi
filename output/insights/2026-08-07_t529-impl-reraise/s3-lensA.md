# 敵対レビュー結果

結論から言えば、段 2 の **NO-GO には同意する**。ただし根拠は「正規 g2 の正例がない」ではなく、[T-609] の first-write 閉包が未完了である一点に狭める必要がある。94a4/892707 は `DW-G04` の実在正例素材を既に満たしており、D215 の該当事実は古い。

## must-fix

### M1 — D215 の「発火正例なし」は反証済み。NO-GO の根拠を入口閉包だけに訂正する必要がある

D215 の保留根拠を条文ごとに対応づけると次のとおり。

| D215 の条文 | 現在の判定 | A〜E・実在素材との対応 |
|---|---|---|
| historical resolver の production 配線 | **充足済み** | D215 自身が充足を宣言している。[docs/decisions.md:10144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10144) |
| `DW-G04` を発火させる実在 artifact path / 計測 ID | **充足済み。D215 の事実認定が誤り** | `DW-G04` は既存 path または ID を要求するだけである。[docs/dev-wave/core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/dev-wave/core.md:57)。canonical worklog は既に 94a4 と `892707.nqsv` を accepted publish と記録している。[worklog archive:1931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/archive/worklog-phase3-0806-256-261.md:1931)。したがって D215 の「path も ID も書けない」[docs/decisions.md:10149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10149) は反証される。B(a) は合成正例を禁じるだけで、実在 94a4 を禁じない。 |
| historical authority が ever-active hash に限定されるかという R1 | **裁定レベルでは充足、実装は未実施** | A(b) が問いを解決した。元の未裁定条文は [docs/decisions.md:10164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10164)。 |
| 全入口が最初の書込み前に同一状態を検査する | **未充足** | C(a) は欠陥を [T-609] へ送っただけで、実装していない。[docs/worklog.md:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:867)。floor は Python 前に stdout/stderr/marker を書く。[floor_campaign.sh:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/floor_campaign.sh:882)。T-126 も source-stage evidence を先に書く。[t126_qualification.sh:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/t126_qualification.sh:692)。D215 の未解除条文そのものである。[docs/decisions.md:10153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10153) |
| 世代遷移・loader 起動点 | **裁定済み、未実装** | D は据置/+1、E は共有 leaf＋CLI 後 load を決めた。これらは実装時の不変条件であり、shell pre-write を閉じない。 |

したがって段 2 の結論は正しいが、[s2-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s2-plan.md:5) の「正例は再実測対象」より強く、**正例条件は既に成立している**と訂正すべきである。残る hard blocker は [T-609] の完了であり、単なる起票ではない。

成果物影響: 訂正しないと台帳が成立済みの `DW-G04` を未成立と指し続け、[T-609] 完了後も current contract は `e576…` の g1 に固定され、94a4 を参照する新規 certified trial/proof が不当に生成不能のままになる。

### M2 — 94a4 は「正規 publish 済み g2 候補」だが、loader が publisher 実行を証明するわけではない

94a4 の限定付き評価は次のとおり。

- **実在 publish 素材としては本物**である。artifact は `env_tag=pegasus`、`clocks_per_us=2100`、`quality.status=accepted`、`calibration/v2` を持つ。[artifact:1568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1568)、[artifact:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1599)、[artifact:1637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1637)。publish target と bytes SHA/pass も sidecar にある。[publish.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/attempts/0_892707.nqsv/publish.json:2)、[published-self-comparison.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/attempts/0_892707.nqsv/published-self-comparison.json:2)、[job-result.json:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/job-staging/0:892707.nqsv/job-result.json:3)。
- publisher は品質理由を独立導出し、理由が空のときだけ accepted にする。[report.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/report.py:87)、[cli.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/cli.py:769)。schema を bytes 化の前後で検査し、policy 一致後に create-only publish して公開先 bytes を再読する。[cli.py:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/cli.py:579)、[cli.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/cli.py:798)、[cli.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/cli.py:821)。
- しかし runtime loader が外部検証するのは path containment、bytes SHA、schema、env、clock、policy までである。[env_attestation.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1060)。`publish.json`、job-result、self-comparison、final receipt は読まない。
- さらに schema は `quality.status=rejected` 自体を許し、production loader には `accepted` の明示検査がない。[schema_v2.py:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/calibrator/schema_v2.py:473)、[env_attestation.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1091)。`accepted` を要求する検査は現状 test helper 側にある。[test_env_contract.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:757)。
- D155 も、git 直接追加や attempt からの複製を loader/hook は拒否しないと明記している。[docs/decisions.md:7706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:7706)。したがって「loader が通る＝正規 publisher を通った」は成立しない。
- プロジェクトが選んだ外部 trust boundary は署名ではなく「レビュー済み git commit」である。[worklog archive:698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/archive/worklog-phase3-0806-265-266.md:698)。D218 は同一 process の公開先再読を充足形としている。[docs/decisions.md:10282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10282)。

よって正確な表現は、**「レビュー済み commit が束縛する正規 publish 済み較正であり、prospective g2 の実在素材」**である。「正規 g2」「活性化済み g2」「loader が publish provenance を証明した」は不可である。実際、現行 `GENERATIONS` には Pegasus g1 しかない。[env_contract.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:256)

成果物影響: activation loader が `load_verified_calibration` 成功だけを publish 証拠と扱うと、手書きまたは rejected の較正まで活性化受理集合へ入り、current contract hash・oracle report の受理行・proof 参照が未レビュー bytes に切り替わり得る。

### M3 — g2 current 化の影響は「live は止まる、historical proof は維持される」と分ける必要がある

94a4 を g2 として扱う際に壊れる、または維持される境界は次のとおり。

1. **単純 append は activation ではない。** 現行 `REGISTRY` は世代列末尾を無条件に current とする。[env_contract.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:344)。fuse だけ外して g2 を足すと即 current になり、D176 が禁止した「source に足しただけで切替」に戻る。[docs/decisions.md:8684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:8684)

2. **live floor の受理集合は空になる。** 凍結 protocol は g1 の `e576…` を pin する。[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/s8b-freeze/floor_protocol.json:1)。live validator は current lookup を渡し、hash 不一致を拒否する。[s8b_floor_campaign.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308)、[s8b_floor_contract.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:139)。

3. **凍結 protocol をその場で g2 へ書き換えることもできない。** `FROZEN_MANIFEST` は protocol bytes の SHA を固定する。[test_frozen_artifacts.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:45)。ただしこれは同一 repo 内で共編集可能な provisional sentinel であり、独立改竄境界ではない。[test_frozen_artifacts.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:87)。

4. **既存 historical proof は壊れない。** `reverify_published_freeze` は記録 hash を historical resolver へ渡す。[s8b_ratified_freeze.py:3244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:3244)。protocol validator も resolver が返した記録契約で検査する。[s8b_ratified_freeze.py:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2803)。この点は D215 も既に充足済みと裁定している。[docs/decisions.md:10144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10144)。前設計凍結の「g2 で既存 proof がすべて読めなくなる」[README.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-06_t529-activation-authority/README.md:52) は現在は superseded である。

5. **oracle report には別の迂回が残る。** official report の freeze 再検証は historical 経路なので g1 proof を維持する。[s8b_oracle_report.py:1747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1747)。一方 observation の `run_contract` は raw `resolve_by_contract_sha256` を直接使う。[s8b_oracle_report.py:1640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1640)。A(b) の共有 ever-active leaf をここへ結線しなければ、未活性 g2 を記録した report row まで受理される。

6. **既存 certified 選択値は自動では変わらないが、新規 seal は止まる。** 既存 selector evidence は `pre_oracle_head` の protocol blob SHA へ束縛される。[s8b_ratified_freeze.py:2613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2613)。対して新規 seal は current 契約から protocol を再導出し、committed bytes と一致しなければ拒否する。[s8b_prediction_runner.py:1457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_prediction_runner.py:1457)、[s8b_prediction_runner.py:1564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_prediction_runner.py:1564)。

成果物影響: 正しく分離しないと、既存 certified 選択値・g1 proof 参照を不要に再凍結するか、逆に live floor の受理集合がゼロになる事実を見落として、新規 certified 選択を発行できない状態を「活性化成功」と記録する。

### M4 — docs-only 成果物には「実装済み」と読める余地を残してはならない

docs-only で終える場合、最低限次を明記すべきである。

- D215 の「正例なし」は supersede し、**94a4 は正例素材、未登録・未活性**と記録する。
- remaining blocker は **既存 [T-609] の完了**である。P4 の「新規タスク起票」は既に [docs/worklog.md:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:867) に存在するため重複起票してはならない。
- A/D/E は「裁定・設計のみ」であり、activation chain、receipt、共有 leaf、全入口被覆は未実装とする。
- D197 の識別子は名称決定にすぎず、試行台帳に durable に記録済みとは書かない。[docs/decisions.md:9530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:9530)
- D176 の「名ばかりの型」[docs/decisions.md:8680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:8680)、D196 の「自己申告 receipt を非偽造証拠とする」失敗型 [docs/decisions.md:9524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:9524)、D215 の Python-only 被覆過大報告 [docs/decisions.md:10171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10171) を明示的に否定する。

成果物影響: この限定がないと試行台帳が「activation authority・durable identity・全入口 receipt が存在する」と誩読され、gate 外で先に書かれた floor/T-126 artifact が保護済み集合へ入り、台帳の受理集合と参照が実装より広く報告される。

## should-fix

### S1 — P3 の核心は正しいが、「人間 commit だけが blocker」は機械保証としては言い過ぎ

[T-529] の env-contract activation が [T-607] の `no-active` を解消しない、という核心は正しい。freeze 側は独立に candidate、approval、active pointer を必要とし、pointer がなければ `no-active` になる。[s8b_ratified_freeze.py:1214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1214)

ただし次の限定が必要である。

- candidate generation も現状存在せず、先に AI trailer 付き非-merge commit が要る。[s8b_ratified_freeze.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:552)
- approval/pointer の checker が機械的に証明するのは非-mergeかつ逐語 `AI-Agent: none` であることまでで、人間性やレビュー済みであることではない。[s8b_ratified_freeze.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:537)
- よって正確には「AI candidate generation の後、運用上人間専有とした `AI-Agent: none` approval/pointer が必要」である。

成果物影響: `AI-Agent: none` を機械的な人間証明と誤記すると、レビューされていない同 trailer commit でも active freeze 集合へ入り、oracle report が参照する active generation/proof が切り替わり得る。

## (P1)〜(P4) の独立判定

| provisional 裁定 | 判定 |
|---|---|
| **P1** | **結論は正しいが理由の前半が誤り。** 正例不足は 94a4/892707 で解消済み。未完了 [T-609] のため実装 scope がない、という後半だけが成立する。[s1-brief.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-impl-reraise/s1-brief.md:31) |
| **P2** | **狭義には正しい。** 現行世代列は各 env 一世代で、historical index は全 entry、current は末尾なので、今の production 受理集合は変わらない。[env_contract.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:329)、[env_contract.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:349)。ただし「ゆえに発火素材もない」への一般化は誤り。 |
| **P3** | **核心は正しいが表現過大。** T-529 は T-607 を解消しない。一方 blocker は人間 commit一個ではなく、AI candidate＋人間専有 approval/pointer の governance chain である。 |
| **P4** | **docs-only という結論は正しいが成果物列挙が不完全。** D215 の正例事実訂正が必要で、C(a) の新規タスクは既存 [T-609] と重複する。[s1-brief.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-impl-reraise/s1-brief.md:40) |

## nit

該当なし。

## 検査境界

pytest、build、campaign、性能計測は一切実行していない。上記はソース・tracked artifact・git 記録の静的検査であり、緑は主張しない。prospective g2 の full-import、activation chain、first-write probe、受入・変異の実測は親が行う必要がある。

## 総括

1. **段 2 の NO-GO 結論には同意する。** ただし根拠は正例不足ではなく、D215 の first-write 条件を満たす [T-609] が未完了であることだけである。

2. 誤りは **P1 の正例不足部分**（既存 94a4/892707 が反証）と **P4 の成果物列挙**（[T-609] は起票済み）。P3 は核心正しいが「人間 commit だけ」という機械保証は [s8b_ratified_freeze.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:537) より過大。P2 は狭義には正しい。

3. 親は 94a4 を使う実 `GenerationEntry(g2)` の full-import/activation 正例と、未活性 g2 の historical 拒否を実測し、その前に [T-609] の floor・T-126・`env_contract=None` 経路で「gate 前の書込みゼロ」を確認すべきである。テストは必ず `tools/run_tests.py` 経由とし、historical g1 report が維持され live g2 floor が意図どおり分岐することまで測る。