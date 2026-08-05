結論は **NO-GO**。指定ファイルはすべて読めた。指示どおり編集・テスト実行はせず、静的読解のみで判定した。

### R1-1 / blocker / acceptance が `launch_admission` を一切検証せず、U-4 を通っていない旧形式・別 trial の report を receipt 化できる

**根拠:** `orchestrator/campaign/trial_registry.py:2022-2032,2067-2088` は旧 top-level 3 field と workload/cell だけを照合し、`launch_admission` の存在・run-start との一致・再導出を見ない。正例 fixture 自体が同 field を持たないまま通る（`orchestrator/tests/test_trial_registry.py:161-205,220-271,413-425`）。これは exact 記録を要求した `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s4-ruling.md:26` に反する。

**失敗シナリオ:** launch admission のない six report/journal と、それらの hash に合わせた lifecycle rows → `assert_trial_registry_acceptance()` が誤受理し receipt を発行。

**成果物影響:** receipt の `trials[].report_sha256` と report/journal 参照集合へ、U-4・effective preregistration を通過していない成果物が入る。

**提案:** run-start/report 双方の `launch_admission` を必須・exact-key 化し、相互一致、`registered-effective`、manifest trial、campaign、workload、measurement HEAD、activation digest を acceptance で再導出する。欠損・片側改変・別 trial admission の負例を追加する。

### R1-2 / blocker / `_finish_trial` と lifecycle が再導出されていない copyable seal を authority として扱い、別 admission の report を生成できる

**根拠:** seal 検査は形状確認だけ（`orchestrator/campaign/trial_registry.py:1209-1250`）。`_finish_trial()` はそれを一度呼ぶだけで、`trial_id` / `selected` と admission を照合せず、`fatal_error` があれば worker scope を通らず report を書く（`orchestrator/campaign/p3_autonomous_workload_trial.py:1204-1213,1281-1339`）。`record_trial_start_once()` も再導出しない（`orchestrator/campaign/trial_registry.py:1434-1488`）。`dataclasses.replace` が seal を保持する脅威は public `run_trial()` のテスト自身が認識している（`orchestrator/tests/test_p3_autonomous_workload_trial.py:2791-2816`）。

**失敗シナリオ:** 同一 manifest の有効 admission A/B を得る → lifecycle start は B で記録 → provider-init failure の `_finish_trial(trial_id=B, selected=Bのworkload, launch_admission=A)` を直呼び → B の partial report に A の admission が刻まれる → R1-1 により誤受理。

**成果物影響:** receipt は trial B・arm B・campaign B を宣言する一方、参照 report の launch binding は A になる。

**提案:** `_finish_trial` に `run_trial` 発行の lifecycle/run-scope token を必須化し、trial/workload/admission hash を exact 照合する。seal 単独を信用せず、全 material consumer で manifest・registry・capability から再導出する。

### R1-3 / blocker / generic Layer 3 に裁定必須の `certifying_input:false` がなく、探索 run が通常材料と区別できない

**根拠:** 裁定は exploratory admission の検出と必須 field を要求する（`s4-ruling.md:26`）。実装は build cell から通常 `render()` を呼び（`orchestrator/campaign/p3_autonomous_workload_trial.py:1154-1179`）、`build_report()` は `acceptance_receipt:null` だけを書く（`orchestrator/campaign/layer3_report.py:476-493,558-565`）。schema 拡張にも `certifying_input` はない（同 `:194-220`）。

**失敗シナリオ:** `--allow-unregistered-exploratory` 付き build → `layer3_report.json` は生成されるが探索入力標識がない → generic material consumer が通常材料として誤受理。

**成果物影響:** Layer 3 材料レポートの受理集合から exploratory campaign が除外されず、WAL・性能値・artifact refs が正式候補と同形になる。

**提案:** exact launch mode を campaign lockまで伝播し、v3 schema に必須 `certifying_input` を追加する。generic reader と accepted entry の双方で `false` を拒否側へ送る。

### R1-4 / blocker / 既存の direct-worker 境界テストが早い scope 拒否へ置換され、T-276 gate の回帰を検出しなくなった

**根拠:** `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/integrated.diff:2390-2409` で `_run_workload` の direct compute-build が T-276 を返す assert を削り、scope 不在エラーへ変更している（現物 `orchestrator/tests/test_p3_autonomous_workload_trial.py:997-1015`）。また実際の `python -m ...trial_registry` は `python -c`＋activation monkeypatch に置換された（`integrated.diff:3697-3712`、現物 `orchestrator/tests/test_trial_registry.py:1034-1084`）。裁定は既存期待値の緩和を禁止する（`s4-ruling.md:63-64`）。

**失敗シナリオ:** `_run_workload()` の `_assert_build_transport_admitted()` を削除 → 新テストはその手前の scope 拒否だけを見て緑 → sealed scope 内の direct compute build が誤受理される。

**成果物影響:** T-276 transport admission のない campaign/WAL/Layer 3 測定が生成可能になる回帰を suite が見逃す。

**提案:** public gate から得た exploratory scope 内で `_run_workload` を直接呼び、引き続き T-276 を期待する。`python -m` の実 entrypoint テストも別に復元する。

### R1-5 / must-fix / receipt が可変 append-only ledger 全体の hash を固定するため、正常な後続 append だけで既存 receipt が永久失効する

**根拠:** issuer は registry/lifecycle 全 bytes の hash を格納する（`orchestrator/campaign/trial_registry.py:2151-2158`）一方、verifier は現在の全 bytes と exact 比較する（`orchestrator/campaign/s8c_acceptance_receipt.py:498-507`）。registry は後続 manifest を正式に許す（`orchestrator/tests/test_trial_registry.py:464-481`）。lifecycle snapshot は flock なしで読み（`orchestrator/campaign/trial_registry.py:1839-1854`）、receipt 作成は後段 `:2163` である。

**失敗シナリオ:** manifest A を accept・receipt commit → manifest B を登録、または別 trial lifecycle を追記 → A receipt の検証が hash mismatch で誤拒否。snapshot と exclusive-create の間に追記されれば、receipt は生成時点から無効で再発行もできない。

**成果物影響:** 有効 receipt 集合が `{A,B}` ではなく後から追記された最後のものだけになり、A の report/journal 参照が消費不能になる。

**提案:** mutable ledger は `{prefix_length,prefix_sha256}` で束縛し、現在 bytes がその prefix を保持することを検証するか、receipt ごとの immutable snapshot を作る。snapshot と発行の間は安定した ledger lock を保持する。

### R1-6 / blocker / receipt verifier は producer acceptance を証明せず、manifest すら再 hash しないため、任意の self-consistent receipt を Verified capability にできる

**根拠:** parser は field の字句形状だけを検査する（`orchestrator/campaign/s8c_acceptance_receipt.py:207-333`）。verifier は receipt の HEAD 一致後、registry/lifecycle/report/journal を hash するだけで、`manifest_path`、trial universe、registry introduction、lifecycle/report 意味関係を検証しない（同 `:492-507`）。正例テストは実際に `{"fixture":"registry"}` 等の任意 bytes で通る（`orchestrator/tests/test_s8c_acceptance_receipt.py:62-120,160-168`）。

**失敗シナリオ:** 任意の六 report/journal、任意 registry/lifecycle を置いて hash を計算 → well-shaped な non-certifying receipt を作って commit → `verify_acceptance_receipt()` が誤って `VerifiedAcceptanceReceipt` を返す。正規発行後に manifest だけ差し替えても通る。

**成果物影響:** verified receipt の参照集合へ、registry acceptance を一度も通っていない report/journal が入る。現 v1 は `certifying=false` のため accepted Layer 3 自体はなお拒否されるが、receipt trust boundary は成立していない。

**提案:** manifest を含む全参照を receipt 導入 commit の tracked bytes と照合し、pure な acceptance verifierを issuer/consumerで共有する。exact H1/H2×arm 集合、registry/lifecycle/report の意味的 cross-binding も再検証する。

### R1-7 / must-fix / lifecycle start 後の例外範囲が terminalizer に覆われず、通常の I/O 失敗で trial が start-only のまま永久消費される

**根拠:** start は `orchestrator/campaign/p3_autonomous_workload_trial.py:1840-1847` だが、run-root 作成、journal 構築、transport、run-start append は outer `try` より前（同 `:1848-1917`）。例外 terminalization は `_finish_trial` 周辺だけ（同 `:1947-1978`）で、成功 terminal append 自体も catch 外（同 `:1979-1985`）。ledger append は partial write 後の復旧を持たない（`orchestrator/campaign/trial_registry.py:1414-1423`）。

**失敗シナリオ:** start 成功 → `run_root.mkdir()` の競合、run-start journal の disk-full、または terminal append の I/O failure → terminal 不在/半端行 → 再走は start-once で拒否され、acceptance も terminal 不在で拒否。

**成果物影響:** lifecycle 台帳に修復不能な start-only trial が残り、その manifest の receipt 集合が恒久的に空になる。

**提案:** start 直後から全処理を最外 terminalization 境界で覆い、捕捉可能な失敗は indeterminate terminal にする。部分行を識別できる framing/checksum と、削除を伴わない明示的 recovery 手順を定める。

### R1-8 / must-fix / lifecycle と receipt の一回性は現在 inode/path にしか効かず、削除・再作成で best-of-N に戻せる

**根拠:** flock は ledger 本体 inode に掛かり、path 再確認は書込み前だけ（`orchestrator/campaign/trial_registry.py:1393-1403,1414-1423`）。start-once は現在 bytes のみ（同 `:1469-1474`）。receipt の `O_EXCL` も現在 path の存在だけを見る（同 `:1915-1924`）。registry と異なり lifecycle/receipt の導入・削除履歴検査はない（対照: 同 `:1794-1836`）。

**失敗シナリオ:** batch A を実行・receipt 作成 → lifecycle、run roots、receipt を削除 → 同じ trial IDs で batch B を再実行 → 良い方に合わせて ledger/receipt を再作成し commit → current-HEAD verifier は通る。

**成果物影響:** receipt の status・report hash・journal参照を初回から選択済み batch へ差し替えられる一方、台帳は start-once に見える。

**提案:** stable lock/CAS と削除不能 tombstone を用い、lifecycle/receipt にも registry 同等の導入一意性・削除履歴検査を要求する。worktree/clone 横断は U-D の後続範囲として分離してよい。

### R1-9 / must-fix / runbook に新 gate と receipt を通る実行可能な運用手順がない

**根拠:** 三つの起動例すべてが opt-in を欠く（`docs/phase3-s8c-autonomous-trial-runbook.md:63-70,76-83,95-102`）一方、既定は false（`orchestrator/campaign/p3_autonomous_workload_trial.py:2021-2025`）で gate は拒否する（`orchestrator/campaign/trial_registry.py:1101-1105`）。外部 output root も正式に記載される（runbook `:139-142`）が、receipt issuer は report/journal を repository-relative に限定する（`orchestrator/campaign/trial_registry.py:2119-2124`）。receipt 手順自体もない。

**失敗シナリオ:** runbook 3.1 をそのまま実行 → artifact 作成前に U-4 誤拒否。外部 output root の formal resultを accept → repo-relative 化で誤拒否。

**成果物影響:** 文書どおりの通常運用から report・lifecycle terminal・receipt が生成できない。

**提案:** exploratory 例に明示 flag を足し、formal は manifest/effective/start/accept/receipt commit/独立 verify の実在手順を追加する。外部成果物には content-addressed な正規 ingest 手順を用意する。

### R1-10 / should / `s8b_floor_campaign --mode pilot` は現在も通常運用で H1/H2 を U-4・lifecycle 外から観測できる

**根拠:** pilot は受理され、official だけが拒否される（`orchestrator/campaign/s8b_floor_campaign.py:197-214,3420-3429,3470-3499`）。freeze 由来 workload をそのまま実測へ渡す（同 `:610-628,2102-2108`）。段4でも U-B として明示的に scope-out された（`s4-ruling.md:37`）。

**失敗シナリオ:** pilot で rr80/rr20 を先行観測 →候補や manifest を調整 → 後から formal trial を一回だけ実行。

**成果物影響:** 将来の certified 選択値が、台帳外の先行 holdout 観測後に選ばれた候補へ偏る。

**提案:** freeze-derived workload を実測へ渡す共通下位境界に admission/lifecycle を置く。それまでは pilot artifact を formal input から機械的に隔離する。

### R1-11 / should / distinct manifest を複数登録して receipt を選ぶ U-A best-of-N はそのまま残る

**根拠:** registry は manifest hash、trial ID、campaign ID の重複だけを拒否し、異なる集合の併存を許す（`orchestrator/campaign/trial_registry.py:439-453`）。後続 manifest の共存は正例（`orchestrator/tests/test_trial_registry.py:464-481`）、receipt path は manifest SHA ごと（`orchestrator/campaign/trial_registry.py:1908-1910`）。段4 U-A の明示 scope-out（`s4-ruling.md:36`）。

**失敗シナリオ:** N 個の異なる manifestを登録・実行 → N 個の結果から良い manifest の receiptだけを選ぶ。

**成果物影響:** 将来の certified report/arm 選択が一つの事前固定集合ではなく N 回中の選択結果になる。現 v1 は全件 non-certifying なので現在の certified 集合は空のまま。

**提案:** approval artifact が固定する `(generation, holdout, arm, replicate_slot)` を実験単位にし、全 slot・全 receipt の列挙を下流で必須化する。

### R1-12 / should / holdout 名は現在一致するが、freeze の完全条件は gate・acceptance に束縛されていない

**根拠:** gate の集合は `{rr80,rr20}` のみ（`orchestrator/campaign/trial_registry.py:52-58`）。freeze はさらに skew/rmw/1M records/48 threads を持つ（`orchestrator/campaign/s8b_holdout_freeze.py:58-75`）が、acceptance は workload名・rratio・campaign ID しか比較しない（`orchestrator/campaign/trial_registry.py:2067-2084`）。段4 U-C/U-F の scope-out（`s4-ruling.md:38,41`）。

**失敗シナリオ:** 後続 wave で rr80/rr20 名だけを P3 に追加し、現行 100k/4 条件で実行 → 名・rratio が一致するため凍結 H1/H2 として誤受理。

**成果物影響:** report の性能値が freeze の 1M/48 条件ではないのに、receipt の holdout 参照は H1/H2 になる。

**提案:** freeze document SHA と完全な workload spec を admission、campaign identity、実行引数、report、acceptanceへ一貫して束縛する。

## 総括

**NO-GO — blocker 5件。**

一方、現在の CLI は大文字・空白を lower/strip し、freeze の `HOLDOUTS` と `DERANGEMENT` のキー/値も現状は `rr80` / `rr20` なので、別表記による P3 の測定到達は見つからなかった。`require_effective_preregistration()` の型・commit・再計算 effective・digest の4検査にも fail-open はなく、`_construct_effective` を直接呼んでも再計算不一致で落ちる。`certifying=true` も v1 parser・issuer・下流拒否により現実装では到達不能である。