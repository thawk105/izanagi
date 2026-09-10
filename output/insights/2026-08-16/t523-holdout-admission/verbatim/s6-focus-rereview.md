# 焦点再レビュー

## 1. 対応表（review_a 1-8 / review_b 1-8 の 16 件）

| 所見 | 判定 | 根拠（file:line） |
|---|---|---|
| review_a 1 公開 issuer | partial | 公開 issuer は削除されたが、receipt 作成・token 発行 callable は private 名として直接 import 可能で、durable 台帳を検証しない。`orchestrator/holdout_observation.py:8-11,236-299,343-348` |
| review_a 2 gflags TOCTOU | closed | `run_once` 冒頭で tuple 化し、gate と実行 command の双方へ同じ snapshot を渡す。`orchestrator/calibrator/runner.py:417-428` |
| review_a 3 pilot callable seam | closed | public wrapper が 12 callable seam を列挙し、core 進入前に拒否する。`orchestrator/campaign/s8b_floor_campaign.py:4163-4180` |
| review_a 4 core の gate seam | partial | 指摘された四つの gate seam は削除された。一方、直接 import 可能な core は `measure_fn` と二つの resolver seam を保持し、外部 measure には observation token を渡さない。`orchestrator/campaign/s8b_floor_campaign.py:3260-3274,4217-4226` |
| review_a 5 token 再利用 | closed | token は発行 signature と残回数を identity state に保持し、各 `run_once` で lock 内消費する。回数は canonical protocol の `reps` 由来。`orchestrator/holdout_observation.py:294-338`、`orchestrator/campaign/s8b_holdout_admission.py:647-655,1021-1029` |
| review_a 6 backoff 直接経路 | partial | `profile_point` は build 前に保護比率を拒否するが、実 spawn 関数 `_profile_run(binary, workload, tmp)` 自体は任意 workload で直接 import 呼出し可能。`orchestrator/campaign/backoff_profile.py:107-112,140-145` |
| review_a 7 spawn meta-test | partial | `rglob` と実行ファイル変数名非依存は実装済み。ただし認識 API は限定表で、`os.posix_spawn` 等を追加しても inventory に入らない。`orchestrator/tests/test_ccbench_spawn_sites.py:138-148,237-249` |
| review_a 8 実結線テスト不在 | closed | campaign fixture は実 claim・ledger・ticket 経路へ移り、別途 canonical authority から `run_once` までの E2E がある。`orchestrator/tests/test_s8b_floor_campaign.py:426-435`、`orchestrator/tests/test_s8b_holdout_admission.py:462-559` |
| review_b 1 公開 issuer | partial | review_a 1 と同じ。公開属性は消えたが、private receipt creator が実質的な無台帳 issuer になっている。`orchestrator/holdout_observation.py:236-299,343-348` |
| review_b 2 ratio 字句別名 | closed | ASCII canonical unsigned decimal と uint64 範囲を要求し、`+80`、`080` 等を spawn 前に拒否する。`orchestrator/holdout_observation.py:189-217` |
| review_b 3 claim の早期不可逆消費 | partial | claim は多くの preflight 後へ移ったが、`runner.run()` 内の live admission、host provenance、process identity より前に不可逆作成される。`orchestrator/campaign/s8b_floor_campaign.py:3651-3708,4726-4778` |
| review_b 4 pilot が official key を消費 | closed | exact bool の明示承認を要求し、claim と ledger に記録する。CLI flag も存在する。`orchestrator/campaign/s8b_floor_campaign.py:4244-4252,5178-5181`、`orchestrator/campaign/s8b_holdout_admission.py:754-756,834-839` |
| review_b 5 resume 自己申告 | closed | caller の journal bool・manifest hash は API から除去され、canonical run directory の実 manifest・journal・terminal 状態を読む。`orchestrator/campaign/s8b_holdout_admission.py:474-553,595-621` |
| review_b 6 freeze_io consumer 赤 | closed | consumer は private core と実 authority へ移され、元の clocks／NUMA assert は維持された。`orchestrator/tests/test_s8b_freeze_io.py:383-448` |
| review_b 7 spawn meta-test | partial | review_a 7 と同じ。提示された nested／`exe`／attribute 形は捕捉するが、全 process-launch API の閉包ではない。`orchestrator/tests/test_ccbench_spawn_sites.py:138-148,275-292` |
| review_b 8 proof chain E2E 不在 | closed | canonical protocol／freeze bytes、claim、admission ledger、attempt marker、`run_once` spy を一つのテストで結線した。`orchestrator/tests/test_s8b_holdout_admission.py:462-559` |

## 2. 是正が開けた新しい穴

### 所見 1: private receipt は権限境界になっていない

- severity: must-fix
- 攻撃シナリオ: caller が `_new_durable_attempt_consumption_receipt()` を直接呼び、canonical freeze の mapping とともに `_issue_holdout_observation_admission_from_receipt()` へ渡す。その token で rr80／rr20 を実行でき、cell claim、admission ledger、attempt marker は一件も作られない。
- 根拠: receipt creator は I/O や durable marker を検査せず登録する。issuer も mapping の集合一致と receipt identity だけを見る。テスト自身が同じ無台帳発行を helper として使用している。`orchestrator/holdout_observation.py:236-299,343-348`、`orchestrator/tests/test_holdout_observation.py:47-58`
- 成果物影響: 「台帳を通さずに実測できない」という中心主張が supported public API 限定へ縮退し、実測数と台帳行数が一致しない。
- 提案: underscore を authority にせず、issuer 自身が canonical durable marker／attempt ledger を検証するか、主張を明示的に「private Python API を呼べない caller」に限定する。

### 所見 2: private core の外部 measure が token と reps を迂回する

- severity: must-fix
- 攻撃シナリオ: `_run_campaign_core(..., measure_fn=attacker)` を直接呼ぶ。各 attempt の marker は一件消費されるが、callback 内で ccbench を任意回数直接 spawn し、選別した値を `ScalePoint` として返せる。外部 callback には回数制 token が渡らない。
- 根拠: ticket は callback 前に消費されるが、token を渡すのは `pass_observation_to_internal_measure=True` の場合だけ。private core は外部 `measure_fn` と resolver seam を受理する。`orchestrator/campaign/s8b_floor_campaign.py:3260-3274,4217-4226,4690-4717,4751-4757`
- 成果物影響: attempt ledger 一行に対し任意数の生観測を取得し、その選別値を通常の `result.json`／`result.md` へ載せられる。
- 提案: production artifact を publish する core では internal token-aware measure を固定する。注入可能 harness は非 publish 経路へ分離する。

### 所見 3: pilot 承認 flag が公式 wrapper に結線されていない

- severity: must-fix
- 攻撃シナリオ: 標準 PBS wrapper を通常どおり起動する。wrapper は新 flag を渡さないため CLI が claim 前に拒否し、正規 pilot を一件も実行できない。
- 根拠: CLI は承認 flag を必須化しているが、wrapper の argv は `--mode pilot --protocol ...` のまま。既存テストもその古い argv を exact に固定している。`orchestrator/campaign/s8b_floor_campaign.py:4248-4252,5178-5181`、`tools/pegasus/floor_campaign.sh:962-965`、`orchestrator/tests/test_pegasus_floor_tools.py:1030-1036`
- 成果物影響: 標準投入経路から floor result と台帳を生成できない。
- 提案: wrapper／submit 層へ人間が明示設定する承認入力を追加し、設定時だけ flag を伝播する。無条件付与はしない。

### 所見 4: claim 後にも失敗可能な非計測処理が残る

- severity: must-fix
- 攻撃シナリオ: claim と admission ledger の作成後、`_validate_live_admissions`、host provenance、process identity のいずれかが失敗する。pilot で journal がまだ存在しなければ resume は不可能で、fresh 再試行も既存 claim に拒否される。
- 根拠: claim／finalize は `runner.run()` 前だが、live admission と provenance は `runner.run()` 内で後から実行される。docstring の「全ての非計測 preflight 後」と一致しない。`orchestrator/campaign/s8b_floor_campaign.py:3651-3708,4239-4241,4726-4778`
- 成果物影響: 未測定の通常失敗だけで 12 cell の一回性 key が失われ、floor artifact を生成できなくなる。
- 提案: claim 後の全失敗状態を確実に resume 可能にする run-intent／journal を先に fsync するか、残る非計測検査を claim 前へ移す。

### 所見 5: 現存する `_profile_run` が meta-test の安全説明と一致しない

- severity: must-fix
- 攻撃シナリオ: `_profile_run(binary, {"ycsb_rratio": "80", ...}, tmp)` を直接 import 呼出しする。`profile_point` の gate を通らず直接 spawn する。
- 根拠: `_profile_run` は caller workload をそのまま command に入れる一方、allowlist は「public profile paths が拒否する」ことだけを安全根拠にする。`orchestrator/campaign/backoff_profile.py:107-112`、`orchestrator/tests/test_ccbench_spawn_sites.py:39-40,295-335`
- 成果物影響: claim／attempt ledger が空の holdout profile 観測が成立する。
- 提案: gate を `_profile_run` 自体へ置くか、当該 spawn を gateway へ移す。

## 3. 主張と実体の食い違い

1. 下流拒否の非主張は実体と一致する。`result` に admission ledger の digest や claim identity は含まれず、verifier との結線もない。`orchestrator/campaign/s8b_floor_campaign.py:3910-3948`  
   ただし、この限界は module docstring や生成 `result.md` に書かれていない。

2. 将来 producer の機械封鎖を主張しない方針に対し、meta-test の「new launch must be classified before this test can pass」は強すぎる。認識 API の限定表外なら通過する。`orchestrator/tests/test_ccbench_spawn_sites.py:54-56,138-148`

3. 未 commit ledger 削除への非保護が書かれていない。module docstring は claim を “one-shot authority” と呼ぶが、同一権限による削除を防ぐ authority ではない。`orchestrator/campaign/s8b_holdout_admission.py:2-7`

4. 独立 clone 間の一回性は実装されていない。`--git-common-dir` により共有されるのは「一つの repository の worktree」だけで、この範囲自体は正確。`orchestrator/campaign/s8b_holdout_admission.py:183-200`  
   独立 clone 除外は docstring に明記すべきである。

加えて、private Python hook を呼べるコードを保護対象外とする新しい限界は `holdout_observation.py:8-11` にだけ書かれている。これは ruling_v2 §2 の四項にない重大な保証縮小であり、D／worklog への明記か実装修正が必要である。

## 4. 既存テストの弱体化

静的差分では、既存 test function、`assert`、`pytest.raises` の削除、skip／xfail の追加、期待値反転は確認しなかった。多数の成功テストは public wrapper から private core helper へ移ったが、claim／ledger／ticket は実実装を通しており、単純な no-op 化ではない。

ただし、次の問題がある。

### 所見: 合成 fixture の識別性が一部失われている

- severity: should
- 攻撃シナリオ: production neutral 表との混同が起きても、production と同じ rr80／rr20 を使う consumer fixture が通過する。
- 根拠: 主 fixture は要求どおり rr79／rr23 のまま。`orchestrator/tests/test_s8b_floor_campaign.py:78-94`。一方、別の合成 `test_s8b_freeze_io` fixture は元の rrX から rr80／rr20 へ変更されている。`orchestrator/tests/test_s8b_freeze_io.py:229-247`
- 成果物影響: synthetic authority と production neutral 表の誤結線に対する識別力が弱くなる。
- 提案: 当該 fixture も rr79／rr23 にし、private signature source を明示して consumer 契約を検査する。

また、標準 wrapper の既存テストは承認 flag が無い argv を exact に期待しており、新しい production 要件との統合不整合を検出できない。`orchestrator/tests/test_pegasus_floor_tools.py:1030-1036`

親報告の 979 passed／11 skipped は再走していない。このレビューでは静的検査結果のみを述べている。

## 5. 残る must-fix

- private receipt creator による無台帳 token 発行を閉じる。
- private core の external measure から publishable artifact を生成できる経路を閉じる。
- `_profile_run` 自体を保護する。
- claim 後の非計測失敗を resume 可能にする。
- pilot 承認を標準 wrapper へ明示的に伝播できる運用経路を実装する。
- ruling_v2 §2 の四限界と private Python hook の追加限界を D／worklog／利用者向け出力へ記録する。

## 総括

NO-GO。公開 issuer、ratio 字句別名、公開 callable seam、resume 自己申告など主要な所見は閉じた。  
しかし private receipt から台帳無し token を発行でき、private core と `_profile_run` に実測迂回が残る。  
claim 後失敗による一回性 key の不可逆焼失と、標準 PBS wrapper の承認 flag 未結線も成果物生成を阻害する。  
親の全走成功は尊重するが、これらは現在のテスト集合が検出していない静的な proof-chain／統合欠陥である。