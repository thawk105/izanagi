dev-wave 段 3 の read-only 境界で静的検査した。pytest、build、campaign、計算ノード実走は行っておらず、緑とは主張しない。

## 所見

### 1. **real** — 逆順 reseal は復旧可能だが、余分な歴史を残す

`reseal_protocol()` は process が見る current contract と HEAD gitlink から組を作るため、activation 前なら `(g1, 511c9538...)` を発行する。その直後は legacy g1 と新 g1 の 2 件が current に一致して resolver は `count=2`、activation 後は g2 一致が 0 件になる。正しい g2 reseal を追加すれば current resolver は復旧するが、誤った g1 record は残る。[s8b_floor_campaign.py:882-901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:882) [s8b_floor_campaign.py:936-960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:936) [s2-plan.md:135-156](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:135)

無視時の破損: resolver の current 一致件数が `1 → 2 → 0` となり床値 submit の受理集合が空になり、最終 repo に余分な g1/new-pin path が残る。

### 2. **refuted** — 「create-only だから機械的に取り消せない」は誤り

create-only は `os.link()` による同一 path 上書き防止であり、unlink は禁止していない。post-publish 検査失敗の例外も exact path の除去と commit 禁止を明示し、D444 も削除後の再発行を認めている。[s8b_floor_campaign.py:925-933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:925) [s8b_floor_campaign.py:1177-1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:1177) [decisions.md:18693-18700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18693)

commit 前なら復旧可能、commit 後は追加のみ運用上の正規 rollback ではない。段 2 はこの点を正しく反論したが、実施手順には「reseal が非 0 なら exact path を除去し、index を再検査し、commit しない」を明示すべきである。

無視時の破損: post-publish 失敗の残骸を commit すると protocol index の path 集合と組占有状態が恒久的に 1 件増える。

### 3. **real** — record/head 間は一様な停止ではなく split-brain

head pin は directory の最終 serial/hash と exact 一致を要求する一方、authority は process-local cache される。[env_contract_activation.py:408-421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract_activation.py:408) [env_contract.py:631-662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:631) [env_contract.py:690-700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:690)

| 状態 | authority 読込済み process | 新 process |
|---|---|---|
| record 2 発行後、head 1 | g1/serial 1 を継続 | tail 2 と head 1 不一致で拒否 |
| head 2 更新後、再起動前 | g1/serial 1 を継続 | g2/serial 2 |
| 全 process 再起動後 | 終了済み | g2/serial 2 |

公式 tool は「同一 commit」に加えて「全 process を再起動」と明記するが、段 2 は reseal 用の「新 process」確認しか手順化していない。[issue_env_contract_activation.py:27-33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:27) [issue_env_contract_activation.py:144-153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:144) [s2-plan.md:63-71](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:63)

無視時の破損: `AuthorizedContract` と execution receipt が同時刻に `serial=1/state=f780.../contract=e576...` と `serial=2/state=398b.../contract=1346...` に分裂する。

### 4. **real** — S1 単独は床値 admission 以外も縮退させる

environment contract は campaign ID に入らないため、同じ入力は g1 と g2 で同じ directory を選ぶ。[model.py:66-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/model.py:66) [ident.py:151-178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/ident.py:151)

一方、既存 `campaign.lock` は contract hash、activation tuple、`env_contract.py` を含む 14-path closure を束縛する。head 更新後、同じ ID の g1 campaign は resume を拒否され、current certified acceptance では `E1-stale` になる。[campaign_lock.py:27-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/campaign_lock.py:27) [ident.py:369-389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/ident.py:369) [artifact_admission.py:778-800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/artifact_admission.py:778)

historical 材料レポートは `HISTORICAL_RAW` なので再生成可能だが、receipt-bound certifying report は `CERTIFIED_ACCEPTANCE` で閉じる。[layer3_report.py:416-427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/layer3_report.py:416) [layer3_report.py:579-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/layer3_report.py:579)

無視時の破損: campaign ID は同じまま既存 g1 lock が resume 不可となり、certified view は E1 から受理拒否へ移り、新規 certifying report が生成されない。

### 5. **real** — 安全に分割できる commit 境界は 1 箇所だけ

最小単位は次である。

1. consumer 配線と committed-protocol 束縛だけを先行 commit。現行 g1 では resolver が legacy を exact 1 件返すため、論理上は挙動保存だが未実走なので緑とは断定しない。
2. `00000002.json`、head serial/hash、g2 versioned protocol、追従 fixture/test を同一 commit。

record と head の分離 commit は loader を壊す。S1 と S2 の分離 commit は g2 protocol 0 件となるため、明示的な停止期間を認めない限り安全な中間状態ではない。[issue_env_contract_activation.py:30-33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:30) [decisions.md:19624-19633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19624)

従って「配線 + S1 + S2 を 1 commit」は可能だが必須ではない。「配線 commit」+「S1/S2 atomic commit」が最小で、配備時には campaign 停止と全 process 再起動も要る。

無視時の破損: record/head 分離では全新規 lookup が拒否され、S1/S2 分離では床値 submit 件数、pilot result、report、attempt ledger の新規件数が 0 になる。

### 6. **real** — g1→g2 で変わる値は次のとおり

| 面 | g1 | g2/final |
|---|---|---|
| active contract | `e576e9cd...c01` | `1346c20b...ad1c` |
| calibration path | `calibration-753f535a8d024727.json` | `calibration-94a4b79fa31bba3c.json` |
| calibration SHA | `753f535a...ce5a49` | `94a4b79f...5c5a9` |
| activation tuple | `1 / f7807285...3ed` | `2 / 398b1920...bed8` |
| protocol path | legacy `floor_protocol.json` | versioned `1346...--511c....json` |
| ccbench pin | `d706650c...0969` | `511c9538...06ec` |
| protocol SHA | `261cec1c...74aac` | `b10b91aa...fbbf13` |

g2 は `replace(g1, calibration_ref=...)` なので `clocks_per_us=2100` とその他の contract fields は不変である。[env_contract.py:253-286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:253) [00000001.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract_activations/00000001.json:1) [s2-plan.md:50-61](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:50) [s2-plan.md:77-83](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:77)

新しい床値走行では次も変わる。

- job result の `protocol_path` は versioned path になる。[floor_campaign.sh:1106-1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/floor_campaign.sh:1106)
- journal の `execution_receipt.contract_sha256` は g2、result/report の `ccbench_pin` と `protocol_sha256` も新値になる。[execution_guard.py:625-636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/execution_guard.py:625) [s8b_floor_campaign.py:5110-5148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:5110) [s8b_floor_campaign.py:5162-5192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:5162)
- holdout ledger key の `ccbench_pin` と evidence の `protocol_sha256` が変わるため、旧 pin の one-shot key とは別 key になる。[s8b_holdout_admission.py:868-898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_admission.py:868) [s8b_holdout_admission.py:952-980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_admission.py:952)

既存の certified winner、材料レポート、試行台帳 bytes はこの wave だけでは書き換わらない。専用 certified-selection consumer も未結線である。[layer3_report.py:535-546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/layer3_report.py:535) 新走行の `floors`、`session_median`、CV、valid/exclusion は実測値なので、静的に不変とも変化とも言えない。[s8b_floor_campaign.py:5092-5104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:5092)

無視時の破損: g1 の pin/hash/path を新成果物へ残すと binding gate が拒否し、逆に floor 数値まで不変と仮定すると未測値を certified 値として捏造する。

### 7. **real** — 単純な resolver 配線は admission を弱める

`_scan_floor_protocol_index_at_commit()` は legacy anchor だけを固定 commit から読む。versioned namespace は working tree の `iterdir()` と `read_bytes()` で読む。[s8b_floor_campaign.py:782-817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:782) [s8b_floor_campaign.py:819-869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:819)

さらに submit receipt は protocol path/hash を持たず、job の clean check は `output/` を全除外する。[floor_submit_receipt.py:13-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/floor_submit_receipt.py:13) [floor_campaign.sh:565-574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/floor_campaign.sh:565) 現 admission も resolver 後に working-tree bytes を読むだけである。[certified_writer_admission.py:178-224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/certified_writer_admission.py:178)

従って S2 後、current g2 と任意の 40-hex pin を持つ canonical な未 commit versioned file が exact 1 件なら、resolver authority になり得る。現在は holdout admission が固定 HEAD legacy blob と比較するため後段で止まるが、ここを supplied path の単純読みに変えると最後の committed boundary も消える。[s8b_holdout_admission.py:463-490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_admission.py:463)

必要なのは path 置換ではなく、resolver が選んだ record について HEAD の exact 100644 blob が存在し、record bytes/hash と一致する検査を admission、driver、holdout の全境界に置くことである。caller に path を選ばせてはならないという D460 も維持する。[decisions.md:19196-19213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19196)

無視時の破損: 未 commit の任意 pin が `protocol.ccbench_pin`、`protocol_sha256`、binary identity、result、holdout ledger key に流入する。

### 8. **real** — shell だけの変更では T-419 (3) は閉じない

shell を versioned path に変えると driver の current 契約検査は通るが、holdout authority は legacy HEAD blob と supplied g2 protocol を比較して拒否する。その拒否は run directory、binary store、manifest の作成後である。[floor_campaign.sh:954-986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/floor_campaign.sh:954) [s8b_floor_campaign.py:5556-5587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:5556) [s8b_floor_campaign.py:5750-5855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:5750) [s8b_floor_campaign.py:6043-6067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:6043)

現在の pilot を閉じる最小 scope は、committed record 検査、shell、driver の caller-path 再検証、holdout admission の 4 面。将来の official/refreeze まで開くなら `s8b_holdout_freeze.py` も versioned result を読む必要がある。[s8b_holdout_freeze.py:1293-1309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_freeze.py:1293) [s8b_holdout_freeze.py:1328-1348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_freeze.py:1328) `prediction_runner` と ratified selector path は historical pre-oracle evidence なので一括置換してはならない。[s8b_prediction_runner.py:1542-1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_prediction_runner.py:1542) [s8b_ratified_freeze.py:2677-2679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:2677)

静的見積もりでは中規模の複数 file 変更である。commit-bound resolver、shell argv、driver mismatch、holdout proof chain は temp Git repo と stub driver/subprocess で検証でき、計算ノードは必須でない。[test_pegasus_floor_tools.py:2285-2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_pegasus_floor_tools.py:2285) [test_s8b_holdout_admission.py:656-753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_holdout_admission.py:656) ただし PBS、実機 attestation、実 build、実測 happy path を「運用確認済み」と名乗るには計算ノード実走が必要である。

無視時の破損: g2 run directory、binaries、manifest だけが作られた後で holdout claim/ledger、result.json、report.md、attempt 台帳が欠落する。

### 9. **refuted** — activation の較正 3 面が必然的に弱まる経路はない

successor artifact は content-address path、acquisition receipt/quality、effective-clock self-consistency を検査する。発行時 predicate はさらに current clock method を検査し、CLI は候補を含む chain 全体を検証してから書く。[env_contract.py:443-497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:443) [env_contract.py:524-544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:524) [issue_env_contract_activation.py:195-219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:195)

段 2 の genesis-only fixture 方針も、g2 を active に変えた後の never-active 陰性を消さずに保存する設計であり妥当である。[s2-plan.md:91-101](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/artifacts/s2-plan.md:91)

ただし versioned protocol は `FROZEN_MANIFEST` 対象外で、履歴不変検査は ratified closure に入った時だけ適用される。従って「追加のみだから履歴ゲートと自動的に両立」は言い過ぎである。[decisions.md:19585-19594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19585) [s8b_ratified_freeze.py:981-1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:981)

無視時の破損: 較正値には直ちに破損はないが、新 protocol の削除・再導入履歴を既存凍結 invariant が常時検査しているという誤った provenance 主張が残る。

### 10. **real** — 親の library 実測から「実装後も緑」は一般化できない

`_validated_activation_successor_method()` が確認するのは構造と較正 artifact 3 面までである。[env_contract.py:500-511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:500) この実測は次を捉えていない。

- 未 active 世代に対する current clock-method 比較。
- record chain/head pin、create-only write、同一 commit。
- process cache と全 process restart。
- resolver の exact-one と committed versioned blob。
- shell、driver、holdout authority の同一 protocol 束縛。
- 実行時 probe による execution receipt。[execution_guard.py:605-638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/execution_guard.py:605)

したがって実測は「g2 calibration bytes が successor 候補として受理可能」の証拠に限定され、wave 全体の成功証拠ではない。

無視時の破損: activation record は作れても head load、protocol resolution、execution receipt、result/report/ledger のいずれかが欠落し得るため、「実装後緑」という判定値自体が偽陽性になる。

## 総括

最も危険なのは、versioned protocol を現 resolver が working tree から読み、job clean check が `output/` を除外する点である。  
T-419 を単純な path 置換として実装すると、未 commit の pin/protocol を live admission authority に昇格させ得る。  
record/head/protocol 発行前に、選択された versioned blob の HEAD 束縛を admission・driver・holdout の全境界へ通す必要がある。