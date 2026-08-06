### [所見 1] 本 wave は現行のユーザー裁定 T-560 と正面衝突している

根拠: 現行台帳は「別 process verifier + 最終 receipt 束縛の完全形は作らない。同一 process 内再読で足りる」と明示している（[docs/worklog.md:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/docs/worklog.md:1567)）。一方、brief はその完全形を本 wave の対象としている（[s1-brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-brief.md:20)）。現 checkout の後続 worklog に上書き裁定は見当たらない。

**成果物への影響:** land すると、ユーザーが見送った gate により future certification job の成功集合が縮み、台帳には T-560「見送り」と T-419(iii)「完了」が併存する。

推奨: **裁定へ返す。** T-560 を明示的に上書きするか、T-419(iii) を「同一 process 内再読で充足済み」と改定するかを先に決める。現状のまま実装へ進めない。

### [所見 2] 実現するのは process-local state からの分離であって「完全独立」ではない

根拠: 新 verifier は別 PID・別 interpreter になるため、calibrator 内の monkeypatch・module global・policy 再束縛からは独立する。しかし同一 checkout、同一 predicate/schema/policy、同一 host/filesystem/UID、同一親 shell を共有する（[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:30)、[s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:108)）。D191 はこれを保証済みとはせず、別 process と最終 receipt 束縛を未保証として返している（[docs/decisions.md:9312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/docs/decisions.md:9312)）。

**成果物への影響:** schema/predicate の共通欠陥があれば、in-process と「独立」receipt が同じ不正 artifact を二重に pass し、レポート上だけ独立な追試が一致した形になる。

推奨: schema/path 名を `independent-*` ではなく `separate-process-*` または `process-isolated-replay-*` に変更し、worklog には次のように書く。

> 同一 PBS job の wrapper が、calibrator 終了後、同一 checkout・host・filesystem・UID 上の別 Python interpreter で、published bytes を canonical predicate により再評価した。process-local state からは分離されるが、独立実装・独立 subject 選定・別 trust domain・最終 receipt への semantic 束縛ではないため、[T-419](iii) の「完全独立」は未達である。

### [所見 3] P4 は成立しない。producer が検証対象を選び、少なくとも 9 系統の迂回が残る

根拠: verifier は calibrator が書く `publish.json.target` を locator にする（[s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:118)）。そのファイルは被検証側の calibrator が生成する（[cli.py:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:845)）。静的に確認できる迂回は次の 9 系統。

1. `publish.json` を既存の良性 artifact B へ向け、実際に publish した A を検証させない。
2. 親 job script が verifier 呼出しを削除・条件偽化する。
3. 同 script が `|| true`、rc 再代入、`overall_rc=0` で非 0 を握り潰す。
4. `job-result.json` を検証結果と無関係な値で作る。
5. job 冒頭の clean 検査後に共有 source の verifier/schema/predicate/policy を変更する。source 照合は冒頭だけである（[certify_calibration.sh:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:172)）。
6. bare `python3` と ambient `PYTHON*`/site import を利用する。計画には `-I -B`、絶対 interpreter、version/hash pin がない。
7. calibrator が残した同一 UID の子 process が source/staging を変更する。子孫 scan は build 後だけで、calibrator 後にはない（[certify_calibration.sh:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:519)）。
8. collector は verdict/rc を再検算せず、ファイルがあれば manifest に列挙するだけである。
9. registry・loader・consumer は verification を一切要求せず、後続の手編集で未検証 artifact を登録できる。

calibrator 自身から起動する形との差は「calibrator の process-local state が verifier executable を直接呼ぶか」だけである。取得システム全体を被検証者と見れば、同じ wrapper が argv・subject・rc を所有するため P4 の広い主張は偽。

**成果物への影響:** 不正 A を publish しつつ既存良性 B を検証して `overall_rc=0` にでき、A は registered namespace に残ったまま後続登録候補になり得る。

推奨: [s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:118) を変更し、wrapper 側で `attempt/calibration.json` の digest・埋込 job ID・期待 basename を独立導出し、`publish.json`、published raw bytes、`PBS_JOBID` の四者一致を必須にする。symlink/非 regular file も拒否する。完全独立を名乗るなら launcher と subject 選定を producer job 外の driver に移す。

### [所見 4] 効く層は future certify wrapper だけで、選択結果までの gate にはなっていない

根拠:

| 層 | プランが触るか | 実際の効力 |
|---|---:|---|
| 取得 / certify job | はい | future job の shell exit を非 0 にできる |
| publish | いいえ | verifier より先に publish 済み。reject 後も file を保持 |
| 中央 `verifications/` | はい | 派生 evidence を追加するだけ |
| 登録 / `env_contract` | いいえ | active ref は旧 753f のまま（[env_contract.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/env_contract.py:256)） |
| loader | いいえ | hash/schema/env/clocks/tolerance のみ。verification は読まない（[env_attestation.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/env_attestation.py:1060)） |
| floor / oracle / campaign | いいえ | active contract と loader の結果だけを消費（[s8b_floor_campaign.py:2752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/s8b_floor_campaign.py:2752)、[loop.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/loop.py:86)） |
| final receipt | 部分的 | future staging file の hash 列挙のみ。必須性・accepted・rc は検査しない |

**成果物への影響:** 変わるのは future wrapper の成功集合だけで、published 集合、registry/loader の受理集合、現行 certified 選択結果・レポート参照は一切変わらない。

推奨: 本 wave の名乗りを「future certify wrapper の post-publish process-isolated gate」に限定する。registry admission、loader、consumer、final receipt の semantic gate 化は実装せず、明示した**裁定パッケージ候補**として返す。

### [所見 5] land しても [T-419] (iii) は閉じない。(iv) も独立に残る

根拠: plan は新しい certification job を走らせないと明記する（[s2-plan.md:135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:135)）。892707 は新 wiring を通っておらず final receipt もない。さらに brief は D191 が返した「別 process + 最終 receipt 束縛」を wave 対象と言いながら、final receipt 収集を scope 外にしている（[s1-brief.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-brief.md:10)、[s1-brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-brief.md:20)）。

(iii) を閉じる条件は少なくとも次の連言である。

- producer とは別の authority が exact subject/job identity と verifier identity を選ぶ。
- verifier/schema/predicate/policy/interpreter の immutable identity を記録する。
- verifier 非 0 が wrapper と scheduler の最終 rc に一致する。
- collector が v2 verdict を semantic に検査し、final receipt に必須束縛する。
- その wiring を通った新規 job と final receipt が実在する。post-hoc 892707 判定では代替しない。

(iv) は、94a4 を新 generation として登録・活性化し、`REGISTRY` の全 required entry が self-pass した後にだけ `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を空にできる（[test_env_contract.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_env_contract.py:840)）。活性化権限 T-529 は別前提である。

**成果物への影響:** active calibration は `753f…5a49`、contract は `e576…c01` のままで、certified 選択結果とレポートは自己不整合の既知例外を参照し続ける。

推奨: land 時の worklog は「別 process replay の機構を実装したが、実 job・final receipt・独立 authority がないため (iii) 未達」とする。(iv) と T-529 は裁定へ返す。

### [所見 6] `job-result/v2` の新 field は consumer 不在で、`overall_rc` という名前も強すぎる

根拠: collector が検査するのは `calibrate_rc` が整数であることだけである（[collect_receipt.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:140)）。`independent_verification_rc`、`overall_rc`、verification artifact の存在・accepted、scheduler `Exit_status` との一致は検査しない。manifest は存在する全ファイルを列挙するだけで、欠落しても通る（[collect_receipt.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:153)）。また job-result 作成後にも worktree cleanup があり、そこで失敗すれば記録済み `overall_rc=0` と実 shell rc が食い違う（現行順序は [certify_calibration.sh:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:752) と [certify_calibration.sh:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:772)）。

過去 artifact の実値は次のとおり。

- 867876: `pegasus-job-result/v1`, `calibrate_rc=0`。既存 final receipt の staging manifest は 64 件で verification は 0 件。
- 892707: `pegasus-job-result/v1`, `calibrate_rc=0`。final receipt なし。

collector を変更しないため 892707 の v1 収集互換性は壊れない。867876 は既に final receipt があり、既定 path への再収集は create-only で元から失敗する（[collect_receipt.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:191)）。

**成果物への影響:** verifier artifact が欠落・reject、または scheduler が失敗していても final receipt を作成でき、`overall_rc` を成功値として台帳へ取り込める。

推奨: P5 を維持するなら field を `pre_finalization_gate_rc` と呼び、final receipt 束縛を名乗らない。完全形には collector の exact v1/v2 union validation、v2 verification 必須化、subject/accepted/rc、`failure.json`、scheduler exit の相互照合が必要。

### [所見 7] 「receipt-only replay」と「いつでも再計算可能」は未成立

根拠: replay 手順は外部の現在版 `validate_calibration_v2` と `effective_clock_comparison_passes` を呼ぶ（[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:93)）。schema には関数名と tolerance 値しかなく、source commit、各 module blob hash、interpreter/version がない（[s2-plan.md:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:65)）。したがって自己完結なのは判定データであって判定実装ではない。また現行 receipt も published content-addressed bytes が残る限り、certify job を再走せず再評価できるため、brief の「現行は job 再走なしに再現不能」も過大である（[s1-brief.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s1-brief.md:38)）。

**成果物への影響:** 後日 predicate/schema が変わると同じ receipt が別 verdict になり、台帳の `accepted` を生成した実装を特定・再現できない。

推奨: [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:38) の schema に source commit、verifier/schema/policy/execution_guard の blob SHA-256、resolved Python path/versionを追加し、identity 不一致時は「historical verdict の再現不能」と返す。帯計算の再実装は不要。

### [所見 8] pin 閉包の調査は不完全で、activation 後に frozen floor protocol が壊れる

根拠: 94a4 の `.py` pin がないことと、`FROZEN_MANIFEST` に calibration path がないこと自体は正しい。しかし 753f は brief 記載の 2 ファイルだけでなく、`test_s8b_floor_campaign.py` と歴史的 Silo evidence にも pin されている（[test_s8b_floor_campaign.py:3247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_s8b_floor_campaign.py:3247)、[test_silo_ladder_rung1_evidence.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_silo_ladder_rung1_evidence.py:71)）。

さらに `FROZEN_MANIFEST` は `floor_protocol.json` 自体を凍結している（[test_frozen_artifacts.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_frozen_artifacts.py:43)）。その bytes は旧 calibration を含む contract hash `e576…c01` を pin し、floor validator は protocol hash を現在の `lookup(env_tag)` と比較する（[s8b_floor_campaign.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/s8b_floor_campaign.py:308)）。94a4 activation で active contract hash が変われば既存 frozen protocol は拒否される。

**成果物への影響:** 94a4 を活性化すると既存 floor protocol の受理集合が空になり得て、campaign 再開・ratified freeze・既存 certified report の参照鎖が切れる。

推奨: 本 wave では変更せず**裁定へ返す**。旧 protocol は `resolve_by_contract_sha256` で歴史的 generation を解決するか、新 contract 用 protocol generation を別発行するかを決める。凍結済み bytes の書換えは禁止。

### [所見 9] 中央 backfill は許容できるが、現 schema では事後判定であることを artifact 自身が証明しない

根拠: 892707 の `job-result.json` は `completed_epoch=1785983460` で、attempt/job-staging に verifier artifact はなく final receipt もない。中央 `verifications/` へ書けば終了済み job の namespace は変更しないため、元 job artifact の事後増補には当たらない。しかし予定 schema には verification 時刻、`post-hoc`/`in-job` 区分、origin job、元 job 完了時刻、final receipt 非束縛、verifier source identity がない（[s2-plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-iii/s2-plan.md:42)）。867876 の既存 final receipt も中央判定を manifest に含まない。

**成果物への影響:** レポートが中央 verdict を「892707 の実行時に通った gate」または「867876 final receipt に含まれる証拠」と誤参照でき、証拠の時系列が改変される。

推奨: 中央 artifact に `provenance.mode="post-hoc-backfill"`、origin job ID/completed epoch、verification epoch、`part_of_original_job=false`、`bound_by_final_receipt=false`、source/code identity を必須化する。future in-job artifact とは mode を分ける。

### [所見 10] T-272 の phase 記述は一部誤りだが、brief も T-272 全体を解消した証拠にはならない

根拠: [docs/phase3.md:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/docs/phase3.md:562) の「env_contract を含む 3.10+ module は certify 経路からすべて失敗」は、job 892707 の実値 `calibrate_rc=0` と source commit `c788abff…` に反する。同 commit の `calibrator.cli → execution_guard → env_contract` import は実在するため、brief の狭い訂正は正しい。一方、artifact は `python3 --version` を記録せず、1 job/1 node の成功は shell 3 本の version gate や node 間差を解消しない。新 verifier の Python 3.9 静的テストも runtime preflight の代替ではない。

**成果物への影響:** T-272 を閉じたと誤認すると、将来の compute node/interpreter drift で verifier が起動せず、verification artifact と certified job が欠落する。

推奨: `docs/phase3.md:562` は「env_contract import 不可」の断定だけを訂正し、裸 Python の version/capability gate 不在は残す。本 wave で扱わないなら裁定へ返し、Pegasus 実走成功を名乗らない。

## 総括

**NO-GO。** 現計画は process-isolated replay としては有用だが、「完全独立」「T-419(iii) 完了」「final receipt 束縛」は支持されない。  
最小の是正 3 点:

1. T-560 を上書きする明示裁定を得て、名称・worklog を「別 process replay」へ降格する。  
2. producer-controlled locator を廃し、subject/job/code/interpreter identity を独立束縛する。  
3. collector に v2 semantic validation と scheduler/final rc 束縛を入れ、新 wiring を通した job を収集する。  

登録・loader・consumer・(iv)・frozen protocol 移行は別の裁定パッケージとする。pytest、`run_tests.py`、`check_docs.py` は実行しておらず、本回答は静的読取りと既存 artifact 値の照合のみである。