## 総括

- 段 2 プランはこのままでは承認不可。複数の正しい測定から、値を見た後に `floor_result` を選ぶ経路が開く。
- D1124 が許したのは再測定であり、採用測定の事後差替えではない。T-1982 を後続に回すと、その間に正しさ境界が欠ける。
- 現行 attempt ticket の直接の出所は D434。D893 の T-469 機構は別件かつ実装待ちであり、P2 の帰属は誤り。
- 旧 schema reader の削除と全 source からの identifier 不在要求は、既存 proof chain を狭め得るため scope 外。
- 未知 role、freeze signature、gflags、保護比率 admission、canonical JSON、`O_EXCL` 自体の緩和は静的には見つからなかった。
- 親の択一は「選択世代を値を見る前に固定して同時着地」か「反復結果を T-1982 完了まで non-certifying にする」。
- read-only 制約に従いテストは実行していない。以下は静的判定である。

## 所見

### 1 反復可能化だけを先行すると best-of-N の re-freeze 経路が開く

- 成立条件: 同じ effect cell の official fresh 測定が複数完走し、値を見た後に candidate へ渡す `result.json` を選べること。
- 一次証拠: `orchestrator/campaign/s8b_floor_campaign.py:7060-7062` は eligible を mode・resume・seam だけから導出し、`orchestrator/campaign/s8b_holdout_admission.py:5060-5066` は指定 campaign の行だけを選ぶ。`orchestrator/campaign/s8b_holdout_freeze.py:1620-1636,1688-1725,1760-1763,1881-1885` は呼び手指定の `--floor-result` の値・path・hash を freeze へ載せる。
- 影響: 複数世代すべてが個別には正しい `eligible_for_refreeze=true` artifact となり、良い floor 値の結果だけを `floor_source` として proof chain に入れられる。selector basis 自体は floor を除外するため certified choice の値は直接変わらないが、re-freeze と report が参照する freeze hash・floor 値は変わる。`orchestrator/campaign/s8b_selector_freeze.py:299-335`
- 反証: 値の観測前に選んだ generation ID または selection receipt を `generate-v2-candidate` が必須入力として検査し、それ以外の反復結果を certifying consumer が拒否するソースが示されれば refuted。現行ソースには無い。

### 2 generation scoping は D893 を保った証拠にならない

- 成立条件: 異なる worktree・run root が同じ論理 attempt `cell_id::seqN` を別 `reservation_id` で予約でき、どちらの値も後段候補になれること。
- 一次証拠: attempt ticket は既に D434 が要求している。`rulings/D434.md:3-7,28-29`、`orchestrator/campaign/s8b_holdout_admission.py:1194-1202,3826-3869,3960-3970`。一方 D893 の T-469 は別の launch reservation/run nonce/tombstone 機構として実装待ちである。`docs/archive/worklog-phase3-0805-190.md:324-327`、`docs/archive/worklog-phase3-0825-954.md:130`
- 影響: プランどおり marker identity を generation digest に替えると、同じ論理 attempt を別世代で実行できる。これは D1124 の再測定には必要だが、所見 1 の選択穴と組み合わさると D893 が禁じた「複数実行先から良い値を選ぶ」構造になる。
- 反証: generation とは別に、値を見る前に固定された stable trial/selection ID があり、その ID の launch・terminal が全 run root 共通の消費台帳で一度だけ閉じる証拠があれば refuted。

### 3 旧 schema reader の削除は identifier closure ではなく proof chain の受理縮小になる

- 成立条件: 旧 v1/v2 claim を参照する floor_source または historical verification が存在する状態で、プラン `s2-plan.md:271,352-353` の「旧 live inspection 互換不要」を選ぶこと。
- 一次証拠: 現行 inspector は v1/v2 を別々の exact key 集合で検査する。`orchestrator/campaign/s8b_holdout_admission.py:5129-5203`。ratified consumer は選択済み `floor_source` の bytes を再取得し、同じ live inspector を必須実行する。`orchestrator/campaign/s8b_ratified_freeze.py:3080-3139,3227-3263`
- 影響: 過去 ledger bytes は残っても再検証不能になり、既存 proof chain の受理集合と report の参照可能集合が狭まる。全 source から `irreversible_pilot_approved` を消すテストも、正しい versioned historical decoder を誤って禁止する。
- 反証: 旧 schema を参照する ratified・candidate・report が一件もない実測と、将来も historical reader 不要という明示裁定が揃うか、旧 decoder を producer closure の不在検査から除外して exact reader を温存すれば refuted。

### 4 指定された他の正しさ防壁に明示的な緩和は見つからなかった

- 成立条件: 実装がプランどおり `_key_fields`、holdout observation gateway、canonical reader/writer を変更せず、新 schema も同じ helper を通すこと。
- 一次証拠: 未知 role 拒否は `orchestrator/campaign/s8b_holdout_admission.py:730-748`、freeze signature exact 一致は `orchestrator/holdout_observation.py:360-384`、gflags・間接 flag 拒否は同 `:387-538`、保護比率の admission 要求は同 `:1155-1214` と `orchestrator/calibrator/runner.py:609-654` に独立している。canonical bytes と create-only は `s8b_holdout_admission.py:861-883,995-1029`。
- 影響: 上記 helper が温存されれば、未知 observation_role、signature 集合、gflags 型、`--flagfile`/`--fromenv`、保護比率、canonical JSON、`O_EXCL` の受理集合は変わらない。schema exact は所見 3 の version dispatch を維持する必要がある。
- 反証: 実差分でこれらの helper、呼出し順、または対応する負例テストが変更・削除されれば refuted。

### 5 generation claim の `O_EXCL` は標準経路では恒真に近い

- 成立条件: 各 fresh 予約が必ず新しい `reservation_id` を発行し、同じ ID で予約処理へ再入する公開・復旧経路がないこと。
- 一次証拠: プランは予約ごとに generation digest を作り、oracle/R33 では新しい reservation/transaction ID を発行するとする。`s2-plan.md:89-117,132-153`。現行 `_write_exclusive` は本当に `O_CREAT|O_EXCL` だが、共有 lock 内で呼ばれる。`orchestrator/campaign/s8b_holdout_admission.py:861-883,1380-1484`
- 影響: 「claim の `O_EXCL` が同一世代競合を守る」という assert は、新 ID を毎回 mint するだけなら通常入力で衝突せず、防壁の発火証拠にならない。非恒真なのは同じ generation の attempt marker 二重消費側である。
- 反証: exact に同じ reservation ID を二つの実行先から同時再生し、一方が claim `O_EXCL` で落ちるテスト、または crash recovery が同じ ID を再利用する実経路が示されれば refuted。

### 6 worktree 並行テストの反転だけでは選択防壁を代表しない

- 成立条件: `test_two_worktrees_parallel_fresh_runs_cannot_both_claim_the_same_keys` を「両方 admitted、24 rows」へ反転するだけの場合。
- 一次証拠: 現行テストは共有 root 上で二つの run を並行させ、結果が `admitted/refused` 一件ずつであることだけを固定する。`orchestrator/tests/test_s8b_holdout_admission.py:269-279`。プランの反転案は `s2-plan.md:242-243`。
- 影響: 台帳追記は固定できるが、同一 generation の排他、attempt の一回性、値を見た後の artifact 選択拒否は一つも固定しない。反転後に「D893 も維持」と一般化できない。
- 反証: distinct-generation admission、same-generation double consume 拒否、preselected result 以外の re-freeze 拒否を独立 nodeid に分割すれば refuted。

### 7 master-seed テストは effect-key 意味論を明示的に残す必要がある

- 成立条件: `test_protocol_master_seed_change_does_not_reset_cell_key` を単に「二回目が通る」期待へ変更し、effect digest の同一性を assert しない場合。
- 一次証拠: 現行テストは master seed だけを変えて二回目の拒否を要求する。`orchestrator/tests/test_s8b_holdout_admission.py:882-893`。protocol hash を effect key へ入れない理由は `rulings/D434.md:24-27`。プランは digest 同一の維持を文章では要求する。`s2-plan.md:244-245`
- 影響: protocol を effect key に混入させる変異でも二回目は通るため、観測履歴が同じ cell として集約されなくなる変更を見逃す。
- 反証: 旧・新予約の cell effect digest が exact に同じで、異なるのは generation digest だけと assert する独立テストがあれば refuted。

### 8 oracle の反転候補は正しさゲートを兼ね、production 代表性もない

- 成立条件: `test_oracle_admission_uses_verified_manifest_schedule_and_reps` の末尾だけを二回目成功へ変え、同じ一テストで済ませる場合。
- 一次証拠: 同テスト前半は verified manifest 由来 schedule coverage、reps allowance、ledger role、attempt 消費を固定し、末尾だけが再予約拒否である。`orchestrator/tests/test_s8b_oracle_driver.py:5702-5746`。production driver はその後に output-root 非依存 run marker で再走を拒否する。`orchestrator/campaign/s8b_oracle_driver.py:1238-1281,1518-1546`
- 影響: 直接 admission API の二回目成功を、oracle 測定全体の反復成功と誤認できる。またテストを削除すれば manifest/reps/role の正しさ防壁も同時に失う。前半、generation 再予約、production run-marker の三分割が必要。
- 反証: 三責務を別 nodeid で固定し、D1124 が oracle run marker も撤去対象とするか、D893 防壁として残すかを明示裁定すれば refuted。

### 9 変異候補 1 と 10 は帰属不十分で、legacy/R33 の復活変異が欠ける

- 成立条件: 新実装で `existing` が generation claim だけを指し、identifier 不在テストが複数 file 全体を走査し、legacy/R33 の cross-generation consume テストを追加しないこと。
- 一次証拠: 候補 1 は削除後の旧 `:1391` 分岐だけを「復活」と書くが、旧 effect claim を `existing` へ再収集する変異を定義していない。候補 10 は全 identifier の source 不在検査で、正しい historical decoder も落とす。`s2-plan.md:275-313`。legacy と R33 の marker は現行 `orchestrator/campaign/s8b_holdout_admission.py:3367-3371,3613-3621,3720-3729`。
- 影響: 候補 1 は branch だけ戻しても legacy fixture を見ず kill されない可能性がある。候補 10 は落ちても単一変異への帰属がない。legacy n-pilot marker を effect digest に戻す変異と、R33 marker/claim digest を generation 非依存に戻す変異は、計画中の同世代二重消費テストでは殺されない。
- 反証: 実 mutation patch が旧 effect-path scan まで含むこと、absence scan を live producer に限定すること、legacy/R33 で二世代を予約して同じ論理 attempt を双方 consume する nodeid と kill receipt が示されれば refuted。

## 親 brief への所見

- **P1 は不成立。** `:1391-1394` だけを外して旧 claim を再利用すると、旧 run identity 比較 `orchestrator/campaign/s8b_holdout_admission.py:1411-1448` と fresh ledger 再利用拒否 `:1553-1599` で止まる。新 generation 化は必要だが、選択側の固定と同時でなければならない。
- **P2 は結論の一部だけ正しい。** 旧 96 floor marker は再測定を実際に止める。`docs/archive/worklog-phase3-0826-965.md:14-16`。ただし current attempt ticket の出所を D893 とするのは誤りで、直接の設計根拠は D434。D893/T-469 は別層の実装待ちである。
- **P3 は live producer closure に限れば妥当だが、historical schema literal まで消すのは過大。** `brief.md:46-47` と `s2-plan.md:269-271` の identifier 不在要求は、versioned exact reader を例外にしなければ proof chain を壊す。
- **P4 の実 qsub 方針は必要だが受入条件が不足。** 共有 git dir の exact pathと、投入直前に current 12 effect digest が既存 12 claim と完全一致することを receipt に残す必要がある。単に `already consumed` が出ないだけでは key drift でも通る。
- **P4 の過去投入に関する推論は誤り。** `evidence-failed-resubmit.md:34-39` は evidence root から main worktree と断定するが、`tools/pegasus/submit_floor.sh:557-560` の式は任意の `/work/1/SFC/tanab/<clone>/.git` でも同じ `/work/1/SFC/tanab/izanagi-job-evidence` を返す。削除済み checkout の git-common-dir は未確認である。
- **不変条件列挙は不足。** `brief.md:20-27` には schema exact、canonical bytes、保護比率 admission、`O_EXCL` create-only、historical version dispatch が明記されていない。一般句「正しさゲート」だけでは mutation/test ownership が定まらない。
- **成果物影響の説明は不正確。** `brief.md:32-34` の「certified 選択の下界比較」は、`orchestrator/campaign/s8b_oracle_judge.py:452-464` が floor を入力にも tie-break にも使わず、selector basis も floor を除外するため裏付けられない。正確には「v2 freeze の生成・oracle launch・proof-chain 確定が止まる」である。`orchestrator/campaign/s8b_oracle_driver.py:516-519`
- **`evidence-consumed-cells.md` が直接裏付けるのは snapshot 時点の 12 floor claim、36 claim 合計、228 marker 合計まで。** 同文書 `:27-31` は 228 件を role 別に分けず、6 key の値も列挙しないため、「96 floor marker」「次回投入と exact 同一 key」は同文書だけから一般化できない。
- **`evidence-failed-resubmit.md` は 350 秒後の driver rc=1 は裏付けるが、exact な `already consumed` 例外は記録していない。** stdout/stderr が消失したと同文書 `:30-33` にある。exact 原因は二次記録 `docs/archive/worklog-phase3-0827-1029.md:7-14` とコード推論に依存する。
- **`evidence-deadlock.md` の resume 不成立は採取時点の run directory 不在を支持する。** 一方 fresh 必敗の一般化には、投入時の 6-field digest と既存 claim の exact 一致、および同 checkout が共有 admission root を見ていた証拠が不足する。
- **T-1981 と T-1982 の順序は不変条件と衝突する。** `docs/archive/worklog-phase3-0827-1029.md:933-943` は反復撤去後に選択防壁を棚卸しするとするが、D1124 は選択・再凍結・差替え禁止を「変えない」としている。棚卸しは land 後ではなく、少なくとも certifying consumer の遮断と同時でなければならない。

## 判定できなかった点

- プラン記載の新 nodeid と generation schema はまだ実装されていないため、変異 2〜9が実際に記載 nodeid だけで kill されるかは未確認。特に 6・7 は「二世代の双方で同じ論理 attempt を consume」する fixture 内容が必要。
- 旧 v1/v2 floor claim を参照する現存 ratified artifact の件数は、射影資料に inventory がないため未確認。したがって所見 3 の即時実害件数は判定できない。
- 親の live 台帳の raw bytes、claim filenames、role 別 marker 一覧は射影されていないため、12/96 件と current protocol の digest 一致を独立再計算できなかった。
- テストは一件も実行しておらず、緑とは報告しない。