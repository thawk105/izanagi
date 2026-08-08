## 期待赤の予測

| 区分 | test file / node | 静的根拠 | 判定 |
|---|---|---|---|
| certified writer admission | [`orchestrator/tests/test_campaign.py:2656`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_campaign.py:2656) `test_p2_actual_floor_and_t126_admission_accept_valid_evidence` | [`certified_writer_fixtures.py:90`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/certified_writer_fixtures.py:90) が committed g1 floor bytes をコピーし、admission は現行 g2 と照合する | 期待赤。`blocked/pre-floor` |
| floor/prediction seal | [`orchestrator/tests/test_s8b_floor_campaign.py:3226`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_s8b_floor_campaign.py:3226) `test_real_seal_protocol_to_floor_official_core_e2e` | clone 側 HEAD の g1 protocol と、現行 lookup の g2 contract/calibration を比較する | 期待赤。ユーザー手番前の不整合 |
| pre-oracle head blob | [`orchestrator/campaign/s8b_prediction_runner.py:1564`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_prediction_runner.py:1564)–[`1570`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_prediction_runner.py:1570) | committed floor blob は g1、再導出値は g2。`pre_oracle_head` 比較で拒否される | 上記 E2E の期待赤。hermetic な拒否テスト自体は緑でよい |

T126 の protocol admission、env attestation、履歴 g1 golden、activation record 1 の検証は、活性化そのものが壊す面とは確認できない。T126 は code identity に `env_contract.py` を含むため series identity は回転するが、旧 series を継続しないことを明示検証する node は不足している。

## 所見

### D-1 — `must-fix`：create-only writer と退避手順が衝突している

根拠: [`s2-plan.md:241`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:241)–[`249`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:249) は tracked floor を `mv` するだけで、trap による復旧がない。writer は [`s8b_floor_campaign.py:656`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:656) の create-only である。

成果物影響: 発行失敗時に tracked floor が作業木から消え、floor artifact の参照・contract hash が欠落した状態になる。

修正案: 旧 bytes を検証済み backup へ copy し、create-only のための target 除去を trap 付きで行う。発行・検証・commit の全失敗経路で `HEAD` または backup から target を復元し、成功 commit 後だけ trap を解除する。

### D-2 — `must-fix`：失敗時停止が実行可能な手順として表現されていない

根拠: 裁定は一体の `bash -Eeuo pipefail` script を要求している（[`s4-adjudication.md:105`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:105)）。しかし原案は逐次コマンドで、[`s2-plan.md:228`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:228) の T080、[`s2-plan.md:256`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:256) の golden 検査、[`s2-plan.md:280`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:280) の staging が機械的に連結されていない。また golden 検査は SHA を表示するだけで、期待値との assert がない。

成果物影響: T080 または golden 条件が失敗しても古い／不正な floor bytes が staging・commit され、certified admission の受理集合が変わる。

修正案: `bash -Eeuo pipefail` 内で、T080 の rc、state、refusals、golden SHA、774 bytes、g1 hash 出現回数、変更 key 集合、cached path をすべて assert する。

### D-3 — `must-fix`：裁定された provenance 手順を満たしていない

根拠: 裁定は message file → `check_ai_provenance.py --message-file` → `git commit -F` → full-history audit を要求している（[`s4-adjudication.md:106`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:106)–[`107`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:107)）。原案は [`s2-plan.md:285`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:285) の `git commit -m` のみで、preflight と full audit がない。

なお `--message-file` は実在し、`AI-Agent: none` も人間のみの artifact commit として規約上許容される。問題は値ではなく、要求された検査工程の欠落である。

成果物影響: floor commit の provenance が wave の受理台帳・最終監査へ正しく登録されず、成果物の由来参照が不完全になる。

修正案: message file を作成し、`python3 tools/check_ai_provenance.py --message-file "$MSG"` を成功させてから `git commit --only -F "$MSG" -- ...`。直後に full-history audit を実行する。

### D-4 — `must-fix`：T-530 未 land のまま activation-only を land する経路が残っている

根拠: 現行 campaign identity は environment contract hash を含まない（[`orchestrator/campaign/ident.py:3`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/ident.py:3)–[`5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/ident.py:5)）。WAL COMMIT payload も contract hash を含まない（[`orchestrator/campaign/pipeline.py:1020`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/pipeline.py:1020)）。残課題は [`docs/archive/worklog-phase3-0808-306.md:352`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/docs/archive/worklog-phase3-0808-306.md:352)–[`359`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/docs/archive/worklog-phase3-0808-306.md:359) にも明記され、別 branch の `ec530e9b` に未 land 実装がある。

成果物影響: g1 時代の WAL terminal COMMIT／campaign identity を g2 実行が再利用・skip でき、certified selection と ledger が異なる contract の成果物を受理する。

修正案: T-530 の contract hash binding を land 候補へ含めるか、この wave の land を明示的に T-530 完了後まで blocking にする。g1 WAL を g2 で再利用した場合の拒否テストを追加する。

### D-5 — `must-fix`：ユーザー手番後の land 対象と再検証 tip が曖昧

根拠: [`s4-adjudication.md:117`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:117)–[`130`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:130) は再開後の受入・変異・記録を示すが、tested main/tip、floor commit、activation record、T-530 dependency を含む最終 candidate の固定方法がない。さらに旧原案の A/B/C/D 分割（[`s2-plan.md:298`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:298)–[`313`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s2-plan.md:313)）は、裁定の「一つの実装単位」と整合しない。

成果物影響: g2 authority のみ、または floor／mutation ledger を欠く tip を land し、live admission と予測 seal の不整合、または受入台帳欠落を残す。

修正案: floor commit 後に clean tree、C commit SHA、activation record、tested main SHA を固定し、関連 acceptance・mutation・provenance checks を再実行する。その exact tip を `tools/dev_wave_land.py` の lease 保持下で land し、全終了経路で lease を解放する。

### D-6 — `should`：T126 の series identity 回転を受入成果物で直接固定していない

根拠: 裁定は T126 の series identity 回転を要求している（[`s4-adjudication.md:128`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:128)–[`130`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:130)）。実装上、code identity は [`orchestrator/qualification/contract.py:38`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/contract.py:38)–[`65`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/qualification/contract.py:65) により `env_contract.py` を含み、series は回転する。ただし旧 series を継続しないことを比較する受入 node が見当たらない。

成果物影響: 実行値は回転しても、受入台帳に「旧 series 不継続」の証跡が残らず、既存 qualification artifact の再利用を見逃す可能性がある。

修正案: pre/post の series identity を比較し、旧 series の継続・再利用を拒否する named acceptance test と P3 gate 記録を追加する。

## 横断検索と境界確認

- g1 contract hash、g1 calibration path、head=1、record 1 は、genesis・履歴 golden・synthetic fixture として保持されている箇所が中心で、活性化後に更新すべき stale production reference は確認できない。
- `test_t419_probe_causality.py` は record 1/2 を扱う形へ更新済み。
- T126 の required identity path に activation record 自体を含めないのは、環境契約コード identity と activation ledger を分離する設計として妥当。
- docs 未編集、commit なし、floor 未接触、production 変更は `env_contract.py` の head 定数・state hash の2行のみ。裁定の権限境界は現時点で守られている。
- golden は独立検算結果が一致: SHA `c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d`、774 bytes、g1 hash 出現1回。

## 総括

NO-GO。  
Must-fix: D-1 create-only と復旧設計、D-2 fail-fast/assert 欠落、D-3 provenance preflight 欠落、D-4 T-530 binding 未解決、D-5 land tip 固定不足。  
floor 未再発行による期待赤は確認でき、活性化固有の追加赤は静的には確認できない。  
ユーザー手番後は、floor commit・T-530依存・T126 series 回転を含む再受入後にのみ land 可。