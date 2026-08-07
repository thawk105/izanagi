判定は **NO-GO** です。以下は静的検査結果で、pytest・実走は行っていません。

### B-1 — must-fix：P6 は現装置では実行不能なのに、合成 E2E へ置換されている

- **成果物影響:** 歴史 wave を一度も受理できない装置でも「生死確認済み」とされ、protocol・材料レポートの準備完了集合が広がる。
- **再現・確認:** P6 は歴史的な段 2 入力の snapshot 検証を先行条件にしています。[brief.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:67) しかし現 `build_snapshot()` は `CASE_HASHES` の POS/NEG 以外を拒否し、[codex_reasoning_ab.py:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1277) CLI も POS/NEG しか表現できません。[codex_reasoning_ab.py:5208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:5208) 一方、プランは「合成 E2E で足りる」と置換しています。[s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:9)
- **最小修正:** 実装を「family snapshot だけ」→指定した歴史 wave の実 artifact/hash による dogfood→緑なら protocol/endpoint 実装、の二段階にする。赤なら P6 どおり後半を止める。

### B-2 — must-fix：新 ledger は実 dev-wave の producer に結線されていない

- **成果物影響:** `must_fix.initial_unique_count`、`fix_cycles`、全 attempt 資源が実 job と無関係な手書き JSON でも成立し、certified 選択と材料レポートが偽装可能になる。
- **再現・確認:** プランは worker launcher receipt を取り込むとします。[s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:55) 現行 dev-wave の正本は launcher ではなく、直接 `codex exec` を起動し `.done` と exit code だけを見ます。[operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/operations.md:8) `codex_worker_launch.py` の production caller は repo 内に存在せず、receipt の field も `wave_id` ではなく `manifest_wave_id` です。[codex_worker_launch.py:1415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_launch.py:1415) また固定 max reader が必要なのに、現 DW-S06-A は reasoning を規定していません。[workers.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:46)
- **consumer 棚卸し:** 機械 consumer はテストの直接 import だけです。[test_codex_reasoning_ab.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:58) 実 rollout fixture は環境不在時に skip します。[test_codex_reasoning_ab.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:252) 他の production tool consumer はゼロで、README・phase・archive worklog は人間向け narrative consumer です。[phase3.md:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/phase3.md:696)
- **最小修正:** 実 subprocess supervisor/dispatcher を scope に入れ、dispatch・完了・retry・統合・再レビュー時に create-only event を自動発行させる。手動 `register-wave-event` は正本にしない。
- **docs 予算:** 現在は **25,187 / 25,200 bytes、残り13 bytes**。上限は [check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:254) です。プランの「docs 変更ゼロ」[s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:157) 自体は予算内ですが、必要な producer 契約を省いています。安全義務を削らず T-597 と合わせて空きを作る裁定パッケージが必要です。

### B-3 — must-fix：hash chain が自己申告 field の真実性・完全性を証明しない

- **成果物影響:** finding の実在・役割・世代・fix dispatch を偽っても endpoint 値と certified 選択を変更できる。
- **再現・確認:** 新 schema は最終 `artifact-index`、`blind-adjudication`、`cycle-ledger` だけで、個々の reader 原票や supervisor event を持ちません。[s2-plan.md:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:95) `source_span_sha256` には artifact 内の byte 範囲がなく、`dw_g05_impact` の閉じた schema もありません。[s2-plan.md:96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:96) hash chain は「登録後に bytes が変わらない」だけで、欠落・虚偽登録を検出しません。現 legacy は少なくとも reader×packet の全組を原票から照合しています。[codex_reasoning_ab.py:5109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:5109)
- **最小修正:** supervisor が job/event 集合を生成し、実 filesystem・receipt 集合との双方向一致を取る。reader ごとの append-only 原票、ゼロ finding の完了 receipt、artifact ID＋byte offset から再計算する span hash、閉じた G05 schemaを持たせ、集計済み件数の入力を禁止する。

### B-4 — must-fix：harm と incomplete の decision table が矛盾している

- **成果物影響:** candidate の CRITICAL/HIGH harm が `reject` でなく `decision=null` へ洗い流され、材料レポートの安全判定値が変わる。
- **再現・確認:** hard harm は一件で reject と規定されています。[s2-plan.md:177](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:177) 停止規則も candidate reject とします。[s2-plan.md:194](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:194) ところが変異テストは harmful campaign でも decision を null にする仕様です。[s2-plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:236) また initial count は `resolution=="resolved"` だけ数えるため、[s2-plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:112) unresolved harm が低い件数へ消える実装も可能です。これは危険結果を「無効試行」にした F93 と同型です。[failures.md:2265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:2265)
- **最小修正:** `noninferiority_decision` と `safety_decision` を分離する。incomplete は前者を null にしても、検証済み hard harm は後者を必ず `candidate_reject` にする。unresolved finding はゼロへ除外せず endpoint を null/上界扱いにする。

### B-5 — must-fix：外部署名に独立 trust root がなく、freeze 全体を再発行できる

- **成果物影響:** 結果観測後に margin・n・arm map・campaign ID を別鍵で再凍結し、非劣性 decision を差し替えられる。
- **再現・確認:** 公開側へ署名公開鍵自身を置き、[s2-plan.md:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:165) freeze はその署名を読むだけです。[s2-plan.md:217](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:217) 公開鍵 fingerprint の外部 pin、append-only campaign registry、first-receipt の外部保管がありません。`--require-no-run-receipts` に探索 root すらなく、[s2-plan.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:203) caller が空の場所を見せれば恒真です。現実装も same-owner advisory に留まります。[codex_reasoning_ab.py:4853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4853)
- **最小修正:** ユーザー承認済み公開鍵 fingerprint と create-only campaign registry を protocol 外へ置き、`campaign_id + protocol SHA + first prelaunch root` を外部署名する。鍵差替え、全 chain 削除後の再 freeze、別 directory の既存 receipt を負例にする。custodian 未提供なら「実走不可」の裁定パッケージとして止める。

### B-6 — must-fix：legacy と generic の dispatch 境界が未定義

- **成果物影響:** T-181 の受理集合・rc が変わるか、逆に family/producer 欠落の新 manifest が T-181 として黙って通る。
- **再現・確認:** 旧 CLI は引数なしで T-181 とし、[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:32) `_replay_manifest()` には新たに `producer_kind` dispatch を入れる計画です。[s2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:66) しかし既存 manifest には `producer_kind` も family もありません。[manifest.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/manifest.json:1) 欠落を legacy とみなせば新 schema が fail-open、必須化すれば legacy 回帰です。また現コードには explicit empty `spec={}` が既定へ戻る `spec or default` があります。[codex_reasoning_ab.py:1366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1366) 既存 test は任意 spec 差込みも使用します。[test_codex_reasoning_ab.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:917)
- **最小修正:** legacy public entrypoint・manifest schema は一切 generic resolver を通さない。新 command は exact schema/version/family/producer/protocol を全必須にし、missing/null/empty/mixed schema を拒否する。`x or default` を使わず `is None` で分ける。各 registry 値には同値でない sentinel と lookup-result-discard 変異を置く。F69 の既知再発型です。[failures.md:1607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:1607)

### B-7 — should-fix：未認証 T-181 の全結果を “golden” 化する

- **成果物影響:** `experiment_complete=false` の resource ledger・manifest hash が期待値として固定され、材料レポートへ再利用される未認証台帳の範囲が曖昧になる。
- **再現・確認:** プランは `t181-legacy-golden.json` に「現在の incomplete result」まで literal 収録します。[s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:79) 現集計は incomplete 時も resource ledger を残し、[codex_reasoning_ab.py:4136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4136) テストもそれを期待します。[test_codex_reasoning_ab.py:2145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2145) 実際、過去 worklog は `aggregate-uncertified.json` の資源値を再集計済みです。[worklog-phase3-0801-81-82.md:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/archive/worklog-phase3-0801-81-82.md:96)
- **最小修正:** fixture は `t181-uncertified-regression` とし、sidecar に `certification=false / decision=null / allowed_use=byte-regression-only` を固定する。generic analyzer・protocol prior・case registry がこの fixture/T-181 family を入力に取れない負例を置く。legacy byte 比較自体は維持してよい。

### B-8 — must-fix：P3/D207 を守る production adoption latch がない

- **成果物影響:** 将来 `workers.md` の段2/3を high に変えても検査が通り、D207 endpoint 未取得のまま production review の受理集合が広がる。
- **再現・確認:** D207 は A/B だけが引下げを決めると規定します。[decisions.md:9891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9891) 現既定は [workers.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:7) と [workers.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:12) に prose であるだけです。`check_docs.py` は節名集合を検査し、reasoning 値を pin しません。[check_docs.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:376) 現 apparatus test の唯一の関連 assert は、逆に tool 内へ max literal を置かないことだけです。[test_codex_reasoning_ab.py:2986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2986)
- **最小修正:** 今回は `check_docs.py` と対応 test で DW-S02/S03 の `reasoning=max` を exact pin する。将来の変更は、外部 anchor 済み campaign の全 endpoint・`experiment_complete=true`・採用 decision とユーザー裁定を伴う別 wave だけが解除できるようにする。既定 effort は変更しない。

### B-9 — must-fix：変異 test の kill 帰属が成立していない

- **成果物影響:** resolver・schedule・harm gate を削除しても別層の拒否でテストが緑になり、不正 schedule/decision が certified 集合へ入る。
- **再現・確認:** 全変異を「正例＋一 field 負例を public CLIへ」としています。[s2-plan.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:223) しかし #1 は parser と resolver を一つの変異に束ね、parser の拒否が resolver fallback を隠します。[s2-plan.md:227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:227) #10 も endpoint 欠落と harm を一つに束ねるため、無関係な欠落で null になっても緑です。[s2-plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s2-plan.md:236) 現 fake E2E は同じ production 関数で manifest を生成して同じ production verifierへ戻します。[test_codex_reasoning_ab.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:541) 先行 focus もこれを自己追認と判定済みです。[focus1.md:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/focus1.md:127)
- **最小修正:** parser/resolver、closure/schedule、incomplete/harm を別変異にする。各 test は exact reason に加え、対象 downstream の呼出し回数・副作用を pin し、対象 gate を外したときだけ受理または decision が反転することを要求する。実 wave 形の tracked literal fixture を独立 producer で用意する。F28/F150 型の再発防止が必要です。[failures.md:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:466)

## 総括

must-fix は **8件**、should-fix は1件です。  
このプランを現状のまま実装してはいけません。  
特に live producer 結線、外部 trust root、D207 adoption latch は装置ファイル外の scope であり、段4で裁定パッケージ化が必要です。  
それらを閉じるまで成果物は「schema 試作」であって、実 campaign を判断可能にする装置ではありません。