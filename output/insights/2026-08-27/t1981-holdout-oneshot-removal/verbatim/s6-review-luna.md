## 総括

- 判定は要修正。既知の2回帰を除く production code の新規 must-fix は見つからなかった。
- 消費済み36 ledger行・228 markerとの共存、および最初の floor attempt までの新 namespace 分離は静的に成立する。
- floor予約 API、caller、shellの呼び出し規約は一致している。
- R33 pin対象4ファイルは無変更で、指定2ファイルの hash も一致した。
- ただし現行運用文書が削除済み flag を要求し、記載どおりの再投入は qsub 前に必ず失敗する。
- pytest・qsubは実行していない。AST、`bash -n`、`git diff --check`のみ確認した。

## must-fix

### 1 正規の投入手順が削除済み承認 flag を要求している
- 位置: `tools/pegasus/README.md:226,241-247`; `docs/phase3-8b-restart-runbook.md:235-237`
- 何が壊れているか: 文書どおり `submit_floor.sh --confirm-irreversible-pilot-holdout` を実行すると、`submit_floor.sh:42-69` の引数解析が unknown argument として rc=2 で拒否する。
- 成果物影響: submission receipt、PBS job、新 measurement-generation ledger行、attempt行、再測定 resultが一件も生成されない。
- 直し方: 実投入コマンドを引数なしの `tools/pegasus/submit_floor.sh` に統一し、不可逆承認・env伝播・nonce照合の説明を削除する。

## nit / backlog

- `orchestrator/tests/acceptance_duration_ledger.json:9442-9516,11480,11748,12084-12093` に削除・改名済み nodeid が残る。scheduler hintなので実効性は壊さないが、新 nodeidの実測更新時に整理すべきである。`test_real_repo_serialization.py` には今回追随すべき列挙は無かった。
- `s8b_oracle_n_pilot.py:2884-2910` と `tools/pegasus/submit_oracle_n_pilot.sh:11,152` は依然として confirmation を実行前 gate にしている。R33 hash pinによる意図的 scope外だが、裁定文の「何も gate しない引数」という説明は caller全体には成立しない。
- `s8b_attempt_registry.py:55-68,1458-1499` は旧 `consumed/` と旧 marker schemaだけを読む。現在 production から接続されていないため今回の floorを止めないが、role adapter再接続前には新世代対応が必要である。
- `s8b_oracle_driver.py:1092-1117,1494-1523` には holdout予約より上流の永続 G12 one-shot claimが残る。直接予約 API の反復テストは通っても、同一 campaign identity の完全な oracle driver再実行はここで拒否される。独立した正しさ gateか、D1124の撤去対象かは別裁定が必要である。
- 実装子A/Bの報告について、ソースと矛盾する記述は見つからなかった。実装子B自身も未更新文書と duration ledger を未完として報告している。

## 所見ゼロだった検査面

- 実台帳をread-onlyで再導出し、旧 ledger 36行すべてが現 `_key_fields` を通り、旧 floor marker 96件すべてが exact claim・ledger・filenameへ戻ることを確認した。残る旧 n-pilot marker 132件はfloor current scanの対象外である。
- `finalize_floor_holdout_admissions()` は旧 ledger行を履歴として読み飛ばす一方、新行だけを世代 digestで索引する (`s8b_holdout_admission.py:1602-1649`)。
- 最初の attempt回復走査は `measurement-generation-consumed/` と同 schemaのattempt行だけを見る (`:4635-4684`)。旧96 markerは衝突入力にならない。
- 経路は `submit_floor.sh:621-635` → `floor_campaign.sh:1179-1230` → `s8b_floor_campaign.py:8366-8397` → 予約・finalize `:7646-7660` → `campaign-start` `:6276-6299` → attempt消費 `:5730-5756` / `s8b_holdout_admission.py:4086-4129` と接続している。
- 一回性以外の停止点は、submit側のsource/clean/policy/scheduler/third-party gate (`submit_floor.sh:145-516`)、job側のreceipt/source/allocation/build/protocol gate (`floor_campaign.sh:216-1228`)、driver側のprotocol/freeze/durable-root/build/perf/live-admission gate (`s8b_floor_campaign.py:6945-7693`) に残る。旧12 claim・旧96 markerはこれらの入力ではない。
- floor callerから削除済み keywordは消え、callee署名と一致した。変更禁止の `s8b_oracle_n_pilot.py:2943-2952` が渡す承認引数は `s8b_holdout_admission.py:3293-3316` が互換受理する。
- `s8b_oracle_n_pilot.py` は `d447688a39734a292cf5710dbd4656320c45be846b13a995278e083b403a4ab1`、`oracle_n_pilot.sh` は `566698b3a833224488dd4d0c3be0515dd812b75003f3f08f947e37aebfc50ad9`。指定4ファイルの `git diff` は空だった。
- floor shellには承認 flag・env・既定値・`qsub -v` appendの残存も、削除に伴う未定義参照も見つからなかった。

## 判定できなかった点

- 既知のresume修正は現在の差分へ未適用なので、「同じ測定世代を再利用する」実装が別 campaign runまで再利用・拒否しないかは未確認。安全条件は `resume=True` かつ campaign、run path、protocol、freeze、manifestがexact一致するときだけ再利用し、freshまたは別 campaignでは必ず新世代を発行することである。
- pytest、driver実走、qsub、最初の実 attempt、96 session完走、finiteな `result.json.floors` は確認していない。