2入力は読了。以下は read-only 静的レビュー（pytest 実走なし）。現時点の判定は **NO-GO**。

確認済みの非所見：

- `t080_freeze_migration verify --path ...` は実在する（`t080_freeze_migration.py:2102–2154`）。
- `test -t 0` は対話 TTY では機能するが、失敗時の停止制御は別問題。
- `AI-Agent: none` 自体は provenance 規約上有効。
- mutation argv の `--force-dispatch`、`--detached`、`-q -rf` は runbook と一致する。
- `conftest.py:43–96` の synthetic head=1 は意図的で、更新不要。`tools/` / `hooks/` 直下に独立テストはなく、実体は `orchestrator/tests/test_hooks.py`、`test_run_tests_*`、`test_queue_state.py`、`test_wave_land_window.py`、`test_mutation_harness.py`。

### B-1 — P1 の実 artifact admission が未証明

severity: must-fix

根拠: `s1-brief.md:7–15,60–62`、`s2-plan.md:5,52–59`、`silo_ladder_rung1.py:3517–3548,4821–4847`。計画のテストは committed evidence を deep-copy し、driver/policy/runtime を current に再束縛してから calibration だけ g1 に戻すため、実ファイルそのものの `verify-result` 通過を証明しない。

成果物影響: committed silo evidence の historical admission 集合は実際には拡大せず、certified 選択・silo report・受入台帳の「g1 evidence が g2 current で再検証可能」という参照が未成立のまま残る。

修正案: 「契約だけ historical 化する seam テスト」と明記して brief の成果物主張を縮小するか、実 artifact の全 binding drift を許容する historical 契約を別途定義し、どちらを採るか裁定する。

### B-2 — C の guard が fail-closed でない

severity: must-fix

根拠: `s2-plan.md:231–250,256–288`。`test`、T-080 verify、`mv`、照合、`git add` が独立行で、`set -e`、`|| exit`、trap がない。CLI 側の `isatty` / T-080 検査（`s8b_floor_campaign.py:622–645`）が失敗しても shell は後続へ進む。

成果物影響: T-080 不成立・dirty tree・floor 不在でも `git add` まで進み、`floor_protocol.json` の削除、旧値、未検証 g2 値を commit し得るため、floor SHA・FROZEN_MANIFEST・certified admission の参照が偽の緑になる。

修正案: `bash -Eeuo pipefail` の一括 script にし、各 guard を停止条件化する。commit 前に `git diff --cached --diff-filter=AM` と実 blob SHA を検査し、commit 後にも HEAD blob を再照合する。

### B-3 — `mv` 退避の失敗復旧がなく、DW-O11 に反する

severity: must-fix

根拠: `s2-plan.md:241–252`、`s8b_floor_campaign.py:655–679`、`docs/dev-wave/operations.md:65–68`。tracked floor を `mv` で外へ移し、freeze の post-write failure 時も writer は自動削除・復旧しない。計画には `trap`、`git restore`、復旧後再走がない。

成果物影響: 失敗後に tracked floor が欠落または失敗生成物のまま残り、再開時の FROZEN_MANIFEST 値、floor/oracle report、certified 選択の入力 bytes が旧値とも新値とも結び付かなくなる。

修正案: `mv` ではなく一意な backup への非破壊コピーを作り、失敗時は trap で `git restore --source=HEAD -- output/s8b-freeze/floor_protocol.json` と blob 照合を行う。既存 backup の上書きも禁止する。

### B-4 — C commit の provenance preflight が欠落

severity: must-fix

根拠: `s2-plan.md:282–288` は直接 `git commit --only -m ... -m "AI-Agent: none"` を実行する。一方 `docs/ai-provenance.md:80–84`、`docs/dev-wave/operations.md:90–97` は message-file → `--message-file` preflight → `commit -F` → full audit を要求している。checker は hook 自動実行ではない（`tools/check_ai_provenance.py:5–6`）。

成果物影響: trailer 自体は通っても、C commit の staged path に対する事前監査証拠がなく、最終 provenance 台帳・land acceptance の commit audit 参照が手順不備になる。

修正案: repo 外の message file を作り、`python3 tools/check_ai_provenance.py --message-file ...` を実行してから `git commit --only -F ...`、commit 後に full-history audit を行う。

### B-5 — land lease と tested-main の固定が工程にない

severity: must-fix

根拠: `s2-plan.md:312–328` に `wave_land_window.py claim/release`、`tested_main`、stale/busy 再走の記述がない。`docs/pegasus-runbook.md:739–764`、`docs/decisions.md:11172–11206` は lease 取得済みのときだけ受入を投入し、全終了経路で release することを要求する。land lock は受入窓を保護しない。

成果物影響: 他 wave が T-530 の都度 main land で main を進めた後、旧 main に対する受入結果を D tip の証拠として使い、受入台帳の tested-main・dispatch request・certified report の基準が最終 land と不一致になる。

修正案: 初回受入直前に main SHA を保存して lease を claim し、`state=acquired` の場合だけ mutation/full run/land を行う。stale/busy なら main 再取得・条件再評価・受入再走、全終了時に trap で release する。

### B-6 — B 時点の「受入不能」は宣言だけで、実行境界がない

severity: should

根拠: `s1-brief.md:82–83` は floor 再発行前の certified-writer admission が赤と述べるが、`s2-plan.md:303–328` には B 時点で許される検査、期待される赤、受入台帳への記録方法がない。`certified_writer_fixtures.py:110–112` は旧 floor bytes をコピーし、`certified_writer_admission.py:206–214` は current g2 と照合する。

成果物影響: B の g2 authority + g1 floor による期待赤を回帰赤または受入緑として扱い、certified 選択集合・report status・acceptance ledger の state を誤記録し得る。

修正案: pre-C の allowed checks と post-C acceptance checks を明示分離し、pre-C の admission failure は `blocked/pre-floor` として受入結果に算入しない。

### B-7 — T126 / P3 の「contract_sha256 非依存」が過度な一般化

severity: should

根拠: `s1-brief.md:54`、`s2-plan.md:127–134,323–324`。実 runtime は `t126_driver.py:496–515,531–545,873–877` で current contract を lookup/authorize し、`test_t126_qualification_driver.py:89` ほかも `authorize("pegasus")` を呼ぶ。`test_t126_pegasus_tools.py:1428–1447` の「activation record を code identity から除外」は runtime admission 非依存を意味しない。P3 tests も `test_p3_s4_loop_trigger_gating.py:680–808` で current lookup を行う。

成果物影響: g2 calibration `94a4...` / contract `1346...` を使う T126/P3 runtime admission が targeted acceptance から漏れ、certified T126 evidence・report の g2 実行性を証明できない。

修正案: T126 qualification driver と P3 gating tests を current-authority acceptance matrix に追加する。activation receipt を code identity から除外する契約と、runtime contract を使う契約を分けて記録する。

### B-8 — A/B の所有境界で driver test の所有が曖昧

severity: should

根拠: `s1-brief.md:71–74` は A=`silo_ladder_rung1 系`、B=`env_contract 系` とするが、`s2-plan.md:52–67,129` は A が `test_silo_ladder_rung1_driver.py` を編集し、B の g2 authority 影響も同ファイルの dynamic glob（`test_silo_ladder_rung1_driver.py:926–955`）に依存する。

成果物影響: `env_contract_activations/00000002.json` の runtime binding への包含証拠が A/B の patch 分割で欠落・重複し、silo certified binding と report の runtime module 集合が変わる。

修正案: `test_silo_ladder_rung1_driver.py` 全体を A 専有と明記し、B は `test_env_contract*.py` のみ編集する。g2 assertion が必要なら B 所有の activation test へ追加し、共有ファイル集合を handoff に固定する。

### B-9 — mutation の排他・queue・実 detached 実行が未定義

severity: must-fix

根拠: `s2-plan.md:201–222,325–326` は queue_state を表示するだけで、停止 queue 時の分岐、他 child/acceptance の停止、復帰待ちを定義しない。`mutation_harness.py:1819–1835` の flock は同じ mutation harness 同士だけを排他し、`mutation_harness.py:1895–1896` の `--detached` は自己申告フラグに過ぎない。runbook の queue 制約は `docs/pegasus-runbook.md:311–316`、`774–783`。

成果物影響: queue 停止時の dispatch、別 acceptance、別 child の tree read/write が重なり、T660 ledger の `KILLED/SURVIVED/PARSE_ERROR` と復元 SHA が混在した偽の mutation report になる。

修正案: child/background の終了を確認した critical section を作り、queue unavailable なら投入せず停止する。`--detached` だけでなく外部 wrapper/qsub と `.done`/rc polling を用い、ledger 完了・復元・HEAD blob一致後にのみ次の受入へ進む。

### B-10 — T660 mutation が DW-M08 の検出力を閉じていない

severity: must-fix

根拠: `s2-plan.md:147–151,177–194` の `expected_nodes` は production tail-deletion node 一つだけで、追加する `test_empty_chain_rejection_is_distinct...` は mutation spec に含まれない。`docs/dev-wave/mutation.md:49–57` は test strengthening に新テストと変更前 HEAD テストの双方を要求する。

成果物影響: mutation ledger は production node の kill しか証明せず、empty-chain の理由分離と新旧 test の検出差を表す expected node・受理集合・report reference が欠ける。

修正案: empty-chain node 用の mutation/diagnostic ledger を追加し、変更前 HEAD 版と candidate 版を同じ変異入力で比較する。serial-only の `SURVIVED` は kill 集計から分離する。

### B-11 — D tip-only land と mutation ledger の記録規約が衝突

severity: must-fix

根拠: `s2-plan.md:206–222,309–328` は mutation ledger を repo 外に出したまま `D tip` を land する設計だが、`docs/dev-wave/operations.md:106–112` は mutation 後の raw ledger を後続の記録 commit に置くことを要求する。

成果物影響: ledger を外部に残せば land 後の acceptance report が再現不能になり、記録 commit を追加すれば tested tip が D から変わるため、D tip の mutation/provenance 参照が不一致になる。

修正案: D を candidate とし、mutation 後に ledger SHA・spec SHA・tested main/tip を記録する E commit を作って E tip を唯一 land 対象にする、または外部台帳を正式成果物として固定 SHA 付き handoff に明記し、D tip-only の意味を再定義する。

### B-12 — `isatty` と `AI-Agent: none` は人間性の証明ではない

severity: should

根拠: `s8b_floor_campaign.py:608–616` は isatty を actor 認証でないと明記し、`hooks/README.md:53–57` も hook と `AI-Agent: none` は human-only の機械証明にならないとする。計画は `s1-brief.md:20–24`、`s2-plan.md:285–288` で user commit を信頼根拠としている。

成果物影響: floor artifact の「人間が再発行した」という provenance は自己申告に留まり、certified 選択・floor report の信頼境界が暗黙の運用依存になる。

修正案: C を明示的に「外部 human trust boundary」として扱い、機械認証とは主張しない。人間性が必要条件なら、repo 外の署名済み user receipt 等を追加する。

## 総括

NO-GO。must-fix は B-1〜B-5、B-9〜B-11。  
主因は P1 の実 artifact 未証明、C の削除・偽 commit 経路、lease 不在、mutation 証拠と D tip の矛盾。  
should は B-6〜B-8、B-12。  
再レビュー条件は、C の transactional recovery、provenance preflight、lease/land 固定、mutation critical section、P1 の受理意味論確定。