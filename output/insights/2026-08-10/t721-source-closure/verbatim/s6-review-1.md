## 所見

### D-01 / M4 は SURVIVE する

- 一行要約: live drift 8 case は先行する capture が drift を拒否するため、`verify_live_*` の disk 比較削除を検出しない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: test は disk を汚した後、新規 campaign の `ensure_campaign_identity()` を呼ぶ。[test_t671_source_binding.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:147) [test_t671_source_binding.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:163)。この経路は capture を先に呼び、[ident.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:245)、capture 自身が disk/blob 不一致を拒否する。[contract_loader_binding.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:324)。したがって live 側の比較 [contract_loader_binding.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:355) を削除しても全8 caseは緑。
- 成果物影響: 保存済み v2 campaign の resume 時に enforcement source が変わっていても WAL 継続を許し得る。
- 最小の修正案: 8 path ごとに、完全な binding を先に作り、その後 disk だけを汚して `verify_live_contract_loader_binding(binding)` を直接拒否確認する node を追加する。

### D-02 / M3 の赤は gate kill ではなく constructor mask

- 一行要約: capture loop を先頭2 pathへ狭めると、後段の exact-8 constructor が常時拒否し、狙った「新6 path の drift 見逃し」には到達しない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: capture は収集した map をそのまま `ContractLoaderBinding` に渡す。[contract_loader_binding.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:328)。constructor は exact-8 map でなければ拒否する。[contract_loader_binding.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:58) [contract_loader_binding.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:72)。新6 caseは target path を含まない invalid-binding になり、path assertion [test_t671_source_binding.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:171) で赤になるだけである。
- 成果物影響: capture が全8 digestを記録しつつ disk比較だけを2 pathへ狭める実際の underbinding は、事前登録証拠の対象外のまま land する。
- 最小の修正案: digest は8 pathすべて計算し、disk比較だけを先頭2 pathへ制限する変異へ再照準する。

### D-03 / M6 の期待 node は subset の向きにかかわらず不正確

- 一行要約: exact→subset 変異は、missing-key node を正しい理由で kill できない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: exact比較の直後、全期待 path を無条件 index する。[campaign_lock.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:167) [campaign_lock.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:174)。`actual ⊆ expected` なら missing key は比較を通過後 `KeyError` で赤になるだけで malformed lock は依然 fail-closed。`expected ⊆ actual` なら missing-key nodes [test_campaign_lock_codec.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:166) は緑で、既存の extra-blob test [test_campaign_lock_codec.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:156) が赤になる。
- 成果物影響: exact-key 受理集合を実際に広げた証拠なしに codec gate を kill 済みと記録してしまう。
- 最小の修正案: M6 を「required-subset にして extra key を許す」へ明確化し、期待 node を `test_v2_rejects_extra_authority_and_blob_keys` に変更する。

### D-04 / admission が live disk を読まない正例がない

- 一行要約: 裁定 A-N-01 の「dirty disk でも committed admission は受理」を固定する test が実装されていない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: dirty fixture test は lock の build/decode までで admission を呼ばない。[test_t671_source_binding.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:280) [test_t671_source_binding.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:301)。`test_valid_v2_campaign_is_admitted` は disk が clean な正例なので、committed verifier を live verifierへ置換しても緑である。[test_artifact_admission.py:933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:933)。裁定は明示的に正例を要求している。[stage4-ruling.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage4-ruling.md:37)。
- 成果物影響: 正当な記録済み artifact が現在の dirty/different checkout を理由に admission 拒否され、レポートの受理集合が縮む。
- 最小の修正案: 正しい記録 blob digestを持つ v2 artifactを作り、同じ fake repoの diskのみ汚した状態で `classify_campaign(...).admission_status == "admitted"` を確認する。

### D-05 / P1 の事前登録 node は緑のまま

- 一行要約: committed verifier を常時拒否へ倒しても、登録された v1 classification test は verifier を通らない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: committed検証は `decoded.is_v2` の内側だけで呼ばれる。[artifact_admission.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:656)。一方、登録 node は全対象が v1 であることを assert する。[test_artifact_admission.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:720)。P1 を適用すると実際に赤くなる正例は `test_valid_v2_campaign_is_admitted` であり、裁定表の node ではない。[stage4-ruling.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage4-ruling.md:91)。
- 成果物影響: 登録 nodeだけを走らせる mutation spec では、全v2 artifactを拒否する過剰拒否が SURVIVE する。
- 最小の修正案: P1 の期待 node を `test_valid_v2_campaign_is_admitted`、または D-04 の dirty committed-admission 正例へ変更する。

### D-06 / 「v1 32本」は30本しか census していない

- 一行要約: 実装報告の32本に対し、追加 test は `output/campaigns` の30本だけを対象にする。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: test の列挙 root は `ROOT / "output/campaigns"` に固定される。[test_artifact_admission.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:721)。残る2本は transport-smoke evidence 配下に実在し、成果物本文も2 campaign directory と記録する。[RESULT.md:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/output/insights/2026-08-04_wave-a-campaign-transport-smoke/RESULT.md:142)。裁定と実装報告は32本を明記する。[stage4-ruling.md:77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage4-ruling.md:77) [stage5-impl.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage5-impl.md:49)。
- 成果物影響: 2本の記録 evidence lock の schema/readability 変化が「既存 artifact 不変」検査から漏れる。
- 最小の修正案: `output/**/campaign.lock` の exact 32-path/schema censusを追加し、classification mappingは完全な30 campaignと、不完全 evidence 2本の既定結果を分けて固定する。

### D-07 / M2 の副期待 node は赤にならない

- 一行要約: `artifact_admission.py` を閉包から削除しても、明示 path 化した missing-blob test は `env_contract_activation.py` しか対象にしない。
- 判定: **real**
- 重要度: **nit**
- 根拠: M2 は sentinelに加えて admission testも期待する。[stage4-ruling.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/stage4-ruling.md:85)。実 test の対象は固定で `env_contract_activation.py` である。[test_artifact_admission.py:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:1147)。独立 sentinel は正しく赤になるため mutation 自体は kill される。[test_t671_source_binding.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:119)。
- 成果物影響: exact-8保証は sentinel が維持するが、mutation matrix が実際より多い独立検出を報告する。
- 最小の修正案: M2 の期待 node を sentinel のみに訂正する。

### D-08 / exact-8 正例中の tuple assertion は production-derived

- 一行要約: `test_valid_v2_campaign_is_admitted` の tuple equality は同じ production定数から生成・decodeされた値を同定数へ戻して比較している。
- 判定: **real**
- 重要度: **nit**
- 根拠: helper は production tupleを列挙する。[campaign_lock_test_support.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:14)。decoderも同じ tuple順に mapを再構築する。[campaign_lock.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:174)。その結果との equality [test_artifact_admission.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:940) は path同一性を独立には検出しない。ただし `len == 8` と独立 sentinel があるため、test node全体は恒真ではない。
- 成果物影響: なし。独立 sentinel が exact path集合を守る。
- 最小の修正案: tuple assertionを独立 goldenへ向けるか、冗長 assertion として削除する。

### D-09 / 共有 fixture 変更で固有の production 検出力が失われた、は refuted

- 一行要約: 15 consumer の helper使用は WAL・recovery・admission・report用の setupで、capture driftを検査する意図ではない。
- 判定: **refuted**
- 重要度: **nit（修正不要）**
- 根拠: helper は実HEAD blobを直接hashし、合成値ではない。[campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:10)。代表的 consumer は WAL authority検査用 setupである。[test_campaign_lock_wal_consumers.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_wal_consumers.py:89)。production lockとの比較を行う consumerは production `ensure_campaign_identity` を別に実行するため、capture経路は残る。[test_autonomous_trial_completeness.py:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_autonomous_trial_completeness.py:1341)。独立 helperの `test_layer3_report.py` も production captureを維持する。[test_layer3_report.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53)。
- 成果物影響: 共有 fixture由来の偽赤だけが除去され、production capture/live/committed のロジック差分はない。
- 最小の修正案: なし。ただし D-04 の admission専用正例は別途必要。

### D-10 / census は呼出し削除でも緑、は refuted

- 一行要約: 期待された6 call／4 functionのいずれかを削除すると exact Counter が不一致になる。
- 判定: **refuted**
- 重要度: **nit（修正不要）**
- 根拠: censusは file・function・callee・件数を exact Counterで比較する。[test_t671_source_binding.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:318) [test_t671_source_binding.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:350)。現物の呼出しは ident の capture/live/resume [ident.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:249) [ident.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:369) と admission の committed [artifact_admission.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:556) に一致する。
- 成果物影響: 単純な呼出し削除は検出される。ただし到達可能性・結果使用までは census の保証外で、D-01の動的testが必要。
- 最小の修正案: census自体は変更不要。

## 変異静的照合

| 変異 | 静的結果 | 赤になる node |
|---|---|---|
| M1 | KILL | exact-8 sentinel。live/committed各caseも冒頭tuple assertionで赤 |
| M2 | KILL | exact-8 sentinel。登録された missing-blob admission nodeは緑 |
| M3 | RAW KILL / **無効な証拠** | 新6 drift caseは exact-map constructor maskで赤。P2正例もclean capture不能で赤 |
| M4 | **SURVIVE** | 追加・変更 nodeに赤なし |
| M5 | KILL | committed mismatch の8 parameterized nodes |
| M6 | RAW KILL / **期待node不正** | subset方向により extra-blob node、またはmissing-key nodeの uncaught `KeyError` |
| M7 | KILL | dirty shared-fixture digest assertion、exact-8 admission正例 |
| P1 | 登録nodeは **SURVIVE** | v1 mappingは緑。実際にはexact-8 v2 admission正例が赤 |
| P2 | KILL | `test_live_verification_uses_recorded_commit_when_head_has_advanced` |

追加・変更された test node 全体で完全な恒真 test はない。ただし D-08 の tuple assertion単体は production-derived で検出力を持たない。

## 総括

- **NO-GO**
- real must-fix: **6件**
- real nit: **2件**
- refuted: **2件**
- 明示 SURVIVE: **M4**
- M3・M6は赤になっても単一理由性を満たさず、kill証拠として数えられない。
- pytestは実行していない。結論は指定どおり静的検査のみ。