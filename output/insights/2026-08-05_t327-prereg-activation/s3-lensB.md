判定は **NO-GO** です。必読 4 ファイルはすべて全文を読めました。read-only の静的レビューのみで、変更・pytest 実走は行っていません。

## 発火面の棚卸し

|層|いつ・何が発火させるか|実効性|
|---|---|---|
|判定器 / CLI|利用者が `check` を呼ぶとき|レポートと sealed 型を返すだけ。production enforcement ではないとプラン自身が認める。[s2-plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:35)|
|invariant test|pytest/dev-wave 実行時|repository 回帰は検出するが、実験起動時には発火しない。[s2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:263)|
|書込 hook|Claude の Write/Edit 時|誤操作抑止のみ。Bash/Codex を閉じず、正しさの層ではない。[s2-plan.md:195](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:195)|
|T-325 launcher|formal manifest を指定した起動時|committed manifest/registry と ancestry は見るが、T-327 judge は呼ばない。[p3_autonomous_workload_trial.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/p3_autonomous_workload_trial.py:622)|
|T-325 acceptance|利用者が `trial_registry accept` を手動実行したとき|6 report の集合は見るが `certifying=false`、arm は declared-only。[trial_registry.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:124)|
|材料レポート / certified 選択|発火元なし|T-327 receipt を必須消費する経路は計画されていない。|

## 所見

### 1. 判定器は formal 経路に一度も参照されず、自動発効が実効性を持たない

**主張:** P6 の CLI + test 限定では、「条件充足で自動発効」を実装したことにならない。しかもプランは T-325 land/rebase を待ってから述語を実装するため、同時編集衝突を根拠に結線を永久に後送する理由も消える。

**根拠:** [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:23)、[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:41)、[s2-plan.md:225](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:225)、[s2-plan.md:230](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:230)。T-325 launcher は ancestry だけを検査する。[trial_registry.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:904)、[同:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:936)

**具体的な反例または再現手順:** §5 未記入または C08 不一致の古い prereg commit を、measurement HEAD の祖先として manifest に記録する。manifest/registry を commit すれば T-325 launcher と acceptance は通るが、T-327 judge は false のまま一度も呼ばれない。

**重大度:** `blocker`

**成果物影響:** trial registry の受理集合は T-327 前と変わらず、材料レポート・certified 選択には T-327 activation receipt の参照自体が追加されない。

**提案修正:** T-325 land/rebase 後の統合単位を同 wave に追加し、formal launcher は `EffectivePreregistration` を必須取得、acceptance は measurement HEAD で再導出し、下流は receipt bytes を必須消費する。分割するなら、本 wave を「judge 部品のみ」と改名し、発効実装完了を主張しない。

### 2. 凍結されるのは JSON 契約だけで、実際に真偽を決める Python bytes が無保護

**主張:** §6 hash と evidence contract hash を固定しても、`effective()` や各 predicate の Python 実装を変更すれば gN 改訂なしに発効値を変えられる。文書・JSON・Python の三つが正本候補になり、JSON から実装が生成される構造でもない。

**根拠:** ledger が pin するのは三つの hash のみ。[s2-plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:73) 実判定は別 Python module に置く。[s2-plan.md:140](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:140)、[同:158](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:158) プランは raw checker bytes を明示的に pin しない。[s2-plan.md:304](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:304)

**具体的な反例または再現手順:** g1 と文書・contract JSON を不変のまま、`every(predicate.status == SATISFIED)` を `any(...)` に変更するか、C09 が常に `SATISFIED` を返すよう変更する。履歴検査の保護 hash は変わらず、同じ g1 で `effective=false→true` にできる。

**重大度:** `blocker`

**成果物影響:** 同一の freeze generation/hash のまま発効値が false から true へ変わり、結線後の trial 受理集合が拡大し、材料・certified 成果物が同じ凍結参照で異なる意味を持つ。

**提案修正:** predicate evaluator、evidence adapter、normalizer の H 時点 blob hash を gN に pin するか、contract から評価器を機械生成し、その汎用 interpreter bytes を独立 trust root で固定する。テストは pin の代替に数えない。

### 3. 8b を normative reference と言いながら、ratified authority ではなく旧 literal/source を再解釈する

**主張:** C01/C06/C07 は 8b 所有の holdout・規模・予算・floor を 8c 側で再判定するが、8b の active ratified generation へ束縛されていない。これは D124 の「8b が正本」を実質的に破る。

**根拠:** 8c 文書は要約が古くなっても 8b が勝つとする。[phase3-8c-preregistration.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:52) D124 も再掲禁止を明記する。[decisions.md:6073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:6073) 一方、C01 は `s8b_holdout_freeze.HOLDOUTS` と 1m/48 を使い、C06/C07 は §5 値を読む。[s2-plan.md:121](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:121)、[同:126](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:126) 8b の正式 consumer は `load_ratified_freeze` に統一されている。[phase3-8b-descriptor-design.md:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8b-descriptor-design.md:403)

**具体的な反例または再現手順:** 8b §8 に従い floor または holdout を再凍結・承認して active pointer を進める。8c judge は active generation hash を読まないため、旧値を green にするか、正当に承認された新値を赤にする。

**重大度:** `must-fix`

**成果物影響:** 承認済み 8b 改訂後、C01/C06/C07 の値と 6-cell 受理集合が正本から分岐し、材料レポートが古い 8b 世代を暗黙参照する。

**提案修正:** 8c は `8b_active_generation_sha256` だけを記録し、8b 所有値は公開 `load_ratified_freeze` から取得する。8c に残すのは generation/feedback、schedule、manifest binding など固有事項だけにする。

### 4. 凍結境界が逆で、発効ポリシーを除外しつつ D116 より広い事項を凍結する

**主張:** 自動発効式・approval 不要・改訂手続きを記す H3 は hash 対象外だが、§5 欄名と evidence contract は gN 対象になる。さらに D116 の「8c に凍結機構を導入しない」をどこまで新裁定が supersede するか明記されていない。

**根拠:** ユーザー裁定は条件文変更を改訂扱いにする。[worklog-phase3-0802-113-116.md:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0802-113-116.md:666) D116 は追加 freeze を明示的に否定する。[decisions.md:5494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:5494) プランは status paragraph と H3 を hash から除外する。[s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:64) その H3 を発効式へ全面置換する予定である。[s2-plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:188)

**具体的な反例または再現手順:** H3 の `AND` を `OR` にする、または「activate コマンドを追加で要求する」と書き換える。§6 conditions hash は変わらず g2 不要である。一方、条件文を変えず §5 欄名を整理しただけなら g2 が要求される。

**重大度:** `must-fix`

**成果物影響:** 同じ freeze generation が自動発効と明示承認の二つのポリシーを指し得る一方、§5 schema 整理では全 trial が一時失効し、材料・certified 成果物の参照意味が反転する。

**提案修正:** normative な発効式・no-approval・改訂規則を独立 canonical block として hash 対象にする。新 decision では D116(1)を条件意味論の凍結に限って supersede し、git ancestry、単一文書、Layer 3、8b freeze 非変更は維持すると逐語で境界を記録する。

### 5. C11 は「裁定文が存在する」だけで green になり、裁定内容の実装前提を検査しない

**主張:** T-324 の裁定は「budget=1 で走ってよい」ではなく、T-244、複数世代、critic 還流、標本設計を先行させるという禁止裁定である。archive hash だけで C11 を SATISFIED にすると、実行不能または禁止された prereg が発効できる。

**根拠:** プランは C11 を archive ruling hash だけで SATISFIED 候補とする。[s2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:131) 実際の裁定は budget=1 の正式系列を禁止する。[worklog-phase3-0803-122.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0803-122.md:8) D114 の上限 1 と三入口 gate は現役である。[decisions.md:5331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:5331)、[同:5384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:5384)

**具体的な反例または再現手順:** C01〜C10/C12 と §5 を将来埋めるが、`MAX_APPROVED_GENERATIONS=1` と critic 非還流を残す。計画どおりなら C11 は green なので `effective=true` になる一方、T-324 上は正式実走禁止である。

**重大度:** `must-fix`

**成果物影響:** generation=1 の trial が formal ledger に入り得て、材料レポートが単発応答を workload 特化 search の証拠として参照できてしまう。

**提案修正:** g1 前に条件 11 を改訂し、少なくとも cap lift、三入口境界、critic→次世代 consumer、generation/feedback/sample plan の事前登録と hash binding を機械証拠に含める。裁定文 hash は補助証拠に留める。

### 6. `H` 固定と live Python import が両立しておらず、dirty source で証拠を偽装できる

**主張:** 判定は起動時 HEAD `H` を固定する一方、C01 は通常 import した live `_campaign_for/_perf_for/_descriptor_for` を実行する計画である。loaded source bytes が H の blob と一致するという条件がない。

**根拠:** H は一度だけ捕捉するとする。[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:28) C01 は live helper を実行する。[s2-plan.md:121](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:121) T-325 の HEAD 解決も `rev-parse HEAD` のみで dirty source を拒否しない。[trial_registry.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/orchestrator/campaign/trial_registry.py:582)

**具体的な反例または再現手順:** HEAD は変更せず、worktree の `_perf_for` だけ 1m/48 を返すよう未 commit 編集して CLI を実行する。通常 import なら C01 は green になるが、ActivationReport の `observed_head` は編集前 commit のままである。

**重大度:** `must-fix`

**成果物影響:** 同じ observed HEAD/activation commit から異なる predicate 値が出て受理集合が広がり、材料レポートの code/evidence 参照が実行 bytes と一致しない。

**提案修正:** probe 対象コードを H の git blob から解析するか、H の隔離 checkout から import する。最低限、各 loaded module の `__file__` bytes と H blob の一致を検査し、その blob ID を receipt に記録する。

### 7. parent→child 規則と merge 上の generation 導入規則が両立しない

**主張:** 「保護 hash が変わった各 parent→child で同じ child に gN を追加」と「gN の導入 commit は一意な non-merge」を同時に要求すると、正当な二親 merge を定義できない。

**根拠:** generation 導入を一意・non-merge とする。[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:92) 直後に全 parent→child edge で同一 child の gN 追加を要求する。[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:93)

**具体的な反例または再現手順:** A(g1) から B(doc変更+g2) と C(無関係変更) を分岐し、B を C へ merge して M を作る。C→M では保護 hash が変わるが、g2 の一意な導入 commit は B であり M ではない。M を導入扱いにすれば non-merge 条件と衝突する。

**重大度:** `must-fix`

**成果物影響:** 通常の land merge 後に `condition_freeze_valid=false` となり、正当な全 trial が拒否され、材料・certified 成果物から prereg 参照が脱落する。

**提案修正:** commit ごとの `(protected_hash, generation_hash)` 状態遷移として定義する。merge は両親同状態、または一方の状態が他方の履歴上の後継で tree がその後継と一致する場合だけ受理し、相互に異なる改訂は fail-closed にする。

### 8. T-325 が既に返した三つの残余を、sealed-type gate 一件へ潰している

**主張:** launcher gate を足すだけでは、canonical manifest/registry authority、同一 trial の一回性、acceptance receipt の下流消費が閉じない。これらは T-325 自身が具体的な攻撃経路として記録済みである。

**根拠:** caller が後発 manifest だけを選べる。[T-325 worklog:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/docs/spool/worklog/2026-08-04-dev-wave-t325-trial-registry-1.md:67) 同一 trial を複数 run root で回せる。[同:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/docs/spool/worklog/2026-08-04-dev-wave-t325-trial-registry-1.md:75) acceptance は手動で receipt consumer がない。[同:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t325-trial-registry/docs/spool/worklog/2026-08-04-dev-wave-t325-trial-registry-1.md:79) プランの後続は sealed-type gate だけである。[s2-plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:307)

**具体的な反例または再現手順:** M1 を登録後に放棄して M2 を作り、同じ trial ID を二つの run root で実行する。良い性能の6 reportだけを M2 に対して `accept` すれば、trial ID 集合は exact のまま性能値を best-of-N できる。

**重大度:** `must-fix`

**成果物影響:** trial ledger の ID 集合を変えずに採用性能値を差し替えられ、材料レポート・certified 選択は caller が選んだ manifest/receipt だけを参照する。

**提案修正:** 次の三件を別々の裁定パッケージとして返す。

1. effective prereg + generation から自動導出する canonical manifest/registry head。T-325 推奨の approval record は採らない。
2. launch reservation、run nonce、terminal tombstone を持つ consumption ledger。
3. manifest/registry/report/journal hash を含む acceptance receipt と、Layer 3・certified 選択での bytes 必須消費。

### 9. 改訂対象の 8c 正本文書が `check_docs.py` の走査外

**主張:** `phase3-8c-preregistration.md` は今後も改訂される living normative document なのに、`LIVING_DOCS` に入っていない。このため追加する path・D番号・行番号参照の腐敗を `check_docs.py` が見ない。

**根拠:** `LIVING_DOCS` には 8b はあるが 8c はない。[check_docs.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/tools/check_docs.py:33) 参照検査はこの列挙だけを回る。[check_docs.py:3201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/tools/check_docs.py:3201) プランは 8c に新しい参照と契約を追加する。[s2-plan.md:177](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:177)

**具体的な反例または再現手順:** 一時 checkout で 8c 文書だけに `docs/does-not-exist.md` または `phase3-8b-descriptor-design.md:999` を追加し `check_docs.py` を実行する。現在のループでは当該文書を読まない。

**重大度:** `should`

**提案修正:** 8c を `LIVING_DOCS` に追加し、不在 path・腐敗行番号を 8c から検出する負例テストを加える。

### 10. brief の「pin ゼロ」は結論は正しいが、DW-O09 が要求する証明を満たしていない

**主張:** 今回の key/role-name 側再検索では現 checkout に 8c document の別 pin は見つからず、結論自体は支持された。しかし brief が記録したのは path の `*.py` 検索と FROZEN_MANIFEST だけで、規定上は不十分である。

**根拠:** brief の調査記録。[brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:46) DW-O09 は generator source、key→path、role-name key、review ledger まで検索し、path hit 0 を結論にしないよう要求する。[operations.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/dev-wave/operations.md:46)

**具体的な反例または再現手順:** path を直接持たず、役割 key から canonical path を解決する ledger は `grep "<document path>" --include=*.py` では発見できない。今回その実在は確認されなかったため、隠れ pin があるとは主張しない。

**重大度:** `should`

**提案修正:** brief に path 検索・role/key 検索・generator/source pin 検索の query と分類結果を追記し、「0」の根拠を再現可能にする。

## 攻撃したが所見にしなかった点

- `approve` / `activate` / `revoke` を設けず、`prepare-revision` は条件変更時だけなので、現プラン単体には承認セレモニーの別名復活はない。[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:28)
- tracked/untracked 全通常ファイルを走査し、s8c namespace を除外しない実 repository invariant を残す設計なので、未既知性検査の汚染には検出経路がある。[s8b_holdout_freeze.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:179)、[s2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:263)
- 文書確定後に g1 を生成する順序自体は鶏と卵を避けている。[s2-plan.md:230](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:230) 問題は順序ではなく、所見4のとおり発効 H3 が凍結対象外な点である。
- 既存 `FROZEN_MANIFEST` は exact 23 件で、計画も変更しない。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/tests/test_frozen_artifacts.py:38)、[s2-plan.md:218](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s2-plan.md:218)

## 総括

- **判定: NO-GO**
- **blocker: 2 件** — production consumer 不在、実行意味論の bytes 未凍結。
- 親が最初に裁定すべき点は、P6 を撤回し、T-325 land 後の launcher・acceptance・receipt 消費まで T-327 に含めるかである。
- 次に D116 の限定 supersede 範囲を明記し、8b authority・自動発効・条件改訂の三境界を固定する必要がある。
- GO 条件は blocker 2件と must-fix 6件の設計修正後、g1 発行前に同じレンズで再レビューすることである。