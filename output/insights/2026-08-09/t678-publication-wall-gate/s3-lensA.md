指定 4 資料はすべて全文読了しました。以下は静的検査のみで、テストは実走していません。結論は、現プランのままでは **NO-GO** です。

## 親実測の判定

### 所見 M1 — 狭い穴の実在は支持するが、「publication 完了後」の一般化までは支持しない

- **主張:** 親実測は単なる positive control ではありません。positive test を器にした一時 production 変異であり、「`_stage_receipt_write` 中の 4 秒が最終 admission に入らない」という狭い因果主張を支持します。一方、final path publication や 10〜20 秒級の実停滞までは証明しません。

- **根拠:** 現行の最後の latch は [production:1739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1739)、stage はその後の `:1758`、atomic create は `:1759` です。通常 accepted 経路は必ずここを通るため、stage 冒頭の 4 秒 sleep は launcher 内で実行されます。一方、対象 test の assert は outcome/rc/output 等だけで、外部実経過や receipt の `actuals.wall_clock_s` を検査しません（[test:1630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:1630)–1669）。

- **影響:** 「stage 後の再評価欠落」は real です。しかし `_stage_receipt_write` は temp を書いて削除するだけで、`os.link` / `os.replace` / directory fsync を実測していません。したがって「publication 完了後にも再評価できた／できない」の証拠や、実環境で 10〜20 秒停滞するという頻度の証拠にはなりません。

- **提案:** 段 4 では証拠を「prepublication staging delay の defect probe」と限定してください。親は変更後に stage、audit、link 前、directory fsync の各注入点を分けて実測すべきです。

## 1. 受理集合

### 所見 A1 — 「accepted 集合は狭まるだけ」は厳密には偽

- **主張:** P1′は二度目の receipt temp write を除去するため、I/O failure trace を含む受理集合では `not accepted / launcher error → accepted` の拡大が生じます。

- **根拠:** 現行は `_stage_receipt_write` が一度書く [production:1625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1625)–1628 に加え、`_atomic_create_json_reserved` がもう一度書きます（[production:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:445)–450）。P1′はこれを一度へ減らします（[plan:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:14)–25）。

- **影響:** `[構成例・未実測]` 最初の receipt temp write は成功し、現行の二度目だけ ENOSPC/OSError になる実行は、現行では rc=2 ですが、P1′では late latch が予算内なら accepted/rc=0 になります。冗長な失敗面の除去として合理的でも、brief の「狭まるだけ」([brief:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s1-brief.md:32)–34) とは両立しません。

- **提案:** 受理集合を「同じ外部 failure trace」まで含めるか、「publication I/O が成功した論理 job」に限るかを親裁定で明記してください。前者なら P1′は不変条件違反、後者なら brief の文言修正が必要です。

### 所見 A2 — 現時点の成果物影響は dogfood と将来配線に限定される

- **主張:** 欠陥は real ですが、現行 dev-wave 子成果の production 受理集合を直ちに変えている、という初版 brief の一般化は成立しません。

- **根拠:** brief 自身が production caller 不在を訂正しています（[brief:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s1-brief.md:67)–74）。静的な参照検索でも executable caller は対象 production 内部と対象 test 以外にありません。段 2 も同じ限定を記載しています（[plan:222](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:222)–239）。

- **影響:** 現在の直接影響は dogfood receipt の主張と、将来 `DW-O01` が launcher に集約された場合の受理条件です。現行 certified artifact が既に誤採用されているとは言えません。

- **提案:** 記録では「現行 production consumer の欠陥」ではなく「dogfood receipt の偽主張＋将来配線前の blocker」としてください。

## 2. create-only 不変条件

### 所見 A3 — happy path の N-3 は維持できるが、temp 所有契約が未確定

- **主張:** 指定順序どおりなら、receipt slot 予約→output 公開の N-3 と、完全 temp の `link/replace` による atomic visibility は維持できます。ただし例外時の temp 所有者がプラン内で二義的です。

- **根拠:** P1′は reserve を output より前に維持します（[plan:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:81)–99）。一方、helper は「現行どおり temp cleanup」とされる一方で、caller にも `finally` unlink を要求しています（同 `:47–58`）。launcher-error caller も明示 staging へ変わります（同 `:60–62`）。

- **影響:** helper に入る前の monkeypatch/OSError では caller cleanup が必要ですが、helper に入った後は二重所有になります。既存 publication-failure test は helper を original 呼出し前に失敗させますが、temp 残骸を assert していません（[test:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2077)–2104）。部分 receipt が通常 final path に見える必要はありませんが、temp 漏れと ownership regression は未固定です。

- **提案:** 「helper は引き渡された temp の所有権を必ず消費する」か、「caller が最後まで所有する」の一方へ固定してください。link、replace_invalid、helper 呼出し前例外、link 後例外の各経路で temp 残骸を検査してください。

## 3. rc と receipt の整合

### 所見 A4 — publication commit 後の例外で `accepted receipt / process rc=2 / output 不在` を構成できる

- **主張:** P1の「atomic create 後は取り消せないので、その前に gate を置けば rc 整合が守れる」という論証は不完全です。atomic create 後にも例外を投げる操作が残っています。

- **根拠:** `os.link/replace` 後の parent fsync が失敗すると rollback を試みますが、その unlink 失敗は握り潰します（[production:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:452)–466）。さらに receipt 公開後、receipt lock の unlock/close が実行されます（[production:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:438)–442）。外側は例外時に output を消して launcher-error receipt を出そうとしますが、既存の完全 receipt は置換できず（`:429–436`）、その失敗を握り潰して元例外を rc=2 にします（[production:1813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1813)–1829）。

- **影響:** `[構成例・未実測]` accepted receipt の link は成功、parent fsync が失敗、rollback unlink も失敗すると、final path には accepted/launcher_rc=0 が残ります。fallback は output を削除し、receipt を上書きできず、process は rc=2です。lock unlock/close の失敗でも同型になります。

- **提案:** receipt visibility/durability のどこを commit point とするか先に裁定してください。完全 receipt が既に見える場合は、その receipt の rc と output を権威として保持する回復規則、または公開後例外を外部 rc へ昇格させない規則が必要です。post-link fsync failure、rollback failure、unlock failure の fault test を追加してください。

通常 flip 自体の真理値表は整合します。late latch は final attempt を `accepted=False`＋`limit_trigger=max_wall_clock_s` にし（[production:1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1594)–1617）、再構築後は `_writer_truth` が not_accepted/rc=1 を導出します（`:1328–1343`）。checker の not_accepted conjunct も top-level `output_sha256=None` を受理します（`:2123–2130`）。

## 4. flip 時の巻き戻し

### 所見 A5 — 正常 flip は整合するが、例外 fallback は durable rollback を担えない

- **主張:** P3の正常経路は、output unlink→parent fsync→flag false→receipt 再構築なら妥当です。しかし「途中例外は既存 cleanup が担う」という段 2 の主張は過大です。

- **根拠:** proposed 正常順序は [plan:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:90)–100です。既存 fallback は output を unlink して即 flag を false にするだけで、parent directory を fsync しません（[production:1777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1777)–1782）。

- **影響:** `[構成例・未実測]` 正常 flip の output unlink 後に `_fsync_parent` が失敗すると、flag は true のまま fallback へ入ります。fallback は FileNotFoundError を飲んで flag を false にしますが、削除の durability は再確立しません。ライブ filesystem 上の「output 不在」assert は通っても、crash durability の不変条件は固定できません。

- **提案:** fallback にも output parent fsync を入れ、成功後だけ flag を false にしてください。fsync 自体が失敗した場合の receipt 公開可否も親裁定が必要です。テストは unlink 呼出しだけでなく、fsync→flag 更新の順序を観測すべきです。

manifest は rollback してはいけません。session append は費消資源台帳として失敗時も保持する契約です（[production:1773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1773)–1776）。flip receipt の attempt/session と manifest membership は維持されます。既存 race test も敗者 session の保持を要求しています（[test:2302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2302)–2309）。

## 5. checker との整合

### 所見 A6 — schema v2 は通るが、新しい late gate は receipt に束縛されない

- **主張:** field 集合と literal を変えなければ、既存 schema v2 receipt と新しい flip receipt は静的には validator を通せます。しかし accepted receipt は late gate の時刻を記録しないため、checker は新保証を検証できません。

- **根拠:** `actuals.wall_clock_s` は `_receipt` 呼出し時に確定します（[production:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1397)–1399）。P1′はその receipt を audit/stage した後に latch し、flip しなければ staged bytes をそのまま公開します（[plan:83](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:83)–99）。checker は保存済み `actuals.wall_clock_s <= limit` だけを見ます（[production:2105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:2105)–2122）。

- **影響:** late latch を誤って削除しても、receipt は schema-valid のままです。また brief の「accepted receipt の `actuals.wall_clock_s` と limit が矛盾する」という説明（[brief:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s1-brief.md:60)–63）は成立しません。accepted validator は数値超過を拒否するため、実際の欠陥は「stage/publication 時間が actuals に入っていない」ことです。

- **提案:** P2は「literal 互換を保つ代わりに late admission は self-asserted で checker から独立検証不能」と明記してください。late gate を schema に束縛したいなら schema v3 の別裁定が必要です。ただし gate 時刻を bytes に入れた後の再 staging には再帰的な残余が生じるため、まず保証の commit point を定義すべきです。

既存実 receipt は closed field 集合と literal が不変なので、`_validate_receipt` の schema 面では将来も互換です（[production:1951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1951)–2039）。ただし完全な `check-receipt` 成功は executable、manifest、sealed artifacts の現存にも依存するため、静的検査だけで「将来も rc=0」とは断言できません。

## 6. 恒真な保証・テスト検出力

### 所見 A7 — 新規2 node は静的には変更前赤だが、要求全体を固定しない

- **主張:** 指定どおり実装されれば、新規 node 1 と node 2 は変更前 production では赤になる構造です。一方、正常 positive test は production 無変更でも緑になる正の対照です。新規2 node だけでは P1′の順序・exact temp reuse・例外整合を十分に固定しません。

- **根拠:** 現行は stage 後に latch がないため node 1 の期待 rc=1 と食い違い、receipt 向け `_write_json_temp` は2回なので node 2 の期待1回と食い違います（[plan:168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:168)–203）。`test_positive_p1_normal_job_is_accepted` は既存の正の対照であり、変更前赤を主張するテストではありません（同 `:205–207`）。

- **影響:** 次の壊れ方は提案2 nodeをすり抜けます。

  - `[構成例・未実測]` audit を late latch の後へ移す。stage-delay node は flip し、write-count node も1回なので通るが、audit 停滞は再び accepted になる。
  - `[構成例・未実測]` staged temp を別 primitive で二つ目の temp へコピーしてから公開する。`_write_json_temp` の呼出回数は1でも、late gate 後の二度目 I/O が復活する。
  - `[構成例・未実測]` `args.output_published_by_run=False` を省く。提案 node は Namespace を取得する仕組みがなく、output 不在だけでは flag を観測できない。
  - post-link fsync、rollback failure、lock release、replace_invalid flip は未被覆。

- **提案:** node 2 は call count ではなく、「stage が返した同一 Path/inode が reserved helper へ渡された」ことを観測してください。audit-delay flip、replace_invalid flip、helper 呼出し前例外、post-link fault、fallback fsync順序を追加してください。変更前赤・変更後緑は親が実測するまで主張不可です。

## 7. 依頼文言との差

### 所見 A8 — P1′は「publication 完了後」ではなく「最後の可逆な prepublication 点」

- **主張:** 段 2 は依頼を満たしていません。満たすのは output publicationと exact receipt staging 後、receipt publication 前の再評価です。

- **根拠:** 段 2 自身が final path 公開後の再評価は不可能と認めています（[plan:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:27)–41）。late gate 後の残余は次のとおりです。

| 残余区間 | production 根拠 |
|---|---|
| latch return から syscall 呼出しまでの Python 実行・deschedule | `_latch_final_job_limit` 後に helper 呼出し |
| `os.link` / `os.replace` 自体 | [production:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:452)–457 |
| final path 可視化から durability 確定まで | `published=True` 後の `:458` |
| parent directory の open/fsync/close | [production:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:319)–325 |
| staged temp cleanup | `:468–472` |
| receipt lock unlock/close | `:438–442` |
| `_run_supervised`→`_run`→`main`→process exit | `:1762`, `:1805–1812`, `:2583–2591` |

- **影響:** `[構成例・未実測]` max wall=3秒、t=2.99秒で late latch が成功した直後に process を20秒 descheduleし、t≈23秒で link/fsyncすると、receipt は accepted/rc=0のまま publication が完了します。提案2 nodeもこの遅延点を注入しないため赤になりません。残余は10〜20秒に限定されず、任意に長くなり得ます。

- **提案:** 段 4で、依頼を「exact receipt bytes の file fsync までを含む、最後の可逆点での再評価」へ正式に狭めるか、create-only/schema/commit protocol を再設計してください。文言を変えずに P1′を「publication 後」と記録してはいけません。

## 裁定パッケージ候補（scope 外だが real）

### C1 — output publication 自体の例外で orphan/partial output が残る

- **主張:** `_atomic_publish` は final output path を直接作って書き、例外時 rollback をしません。

- **根拠:** [production:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:487)–503。`output_published_by_run=True` は helper が正常 return した後です（`:1734–1735`）。

- **影響:** `[構成例・未実測]` write/file fsync/parent fsync が失敗すると flag は false のままなので fallback は消さず、launcher-error receipt と partialまたは完全 output が併存します。

- **提案:** 本 waveへ広げないなら、output atomicity/rollback の独立裁定候補として起票してください。

### C2 — KeyboardInterrupt/SystemExit は receipt rc と process rc を分離する

- **主張:** BaseException cleanup は launcher-error/rc=2 receipt を書いた後、KeyboardInterrupt/SystemExit を再送出します。

- **根拠:** [production:1813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1813)–1828。`main` はこれらを catch しません（`:2582–2587`）。

- **影響:** `[構成例・未実測]` receipt は launcher_rc=2でも、OS process rcは130や任意の SystemExit codeになります。

- **提案:** interrupt 時に receipt を発行しない、または発行後は process rc=2へ正規化する、の択一を別裁定にしてください。

### C3 — staged temp を Path で保持する間の置換窓

- **主張:** P1′は完全 temp を Path として返し、late latch 後に path-based `link/replace` します。同一 UID の別 process による置換を束縛しません。

- **根拠:** [plan:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s2-plan.md:56)–58 と [production:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:452)–456。

- **影響:** `[構成例・未実測]` stage 後、link 前に temp path を unlink/recreateまたは内容変更されると、audit/stage済みでない bytes が final pathへ出る可能性があります。

- **提案:** directory を trusted single-writer 境界と明記するか、open fd/inode/hash の再束縛を別 hardening として裁定してください。

## 親が実測すべき項目

すべて `tools/run_tests.py` 経由で行うべきです。

- 新規2 nodeの変更前赤・変更後緑と既存 positive node。
- stage と audit の各4秒実 sleepで、rc=1、not_accepted、output不在、保存 actuals>limit。
- staged Path/inode がそのまま atomic helperへ渡ること。
- replace_invalid=True の通常 accepted と late flip。
- post-link fsync失敗、rollback unlink失敗、lock unlock失敗時の final receipt・output・process rc。
- flip後の fallbackで output parent fsyncが flag falseより先であること。
- temp残骸を、正常・flip・helper呼出し前例外・launcher-errorの全経路で検査。
- 新旧 schema v2実 receiptの `_validate_receipt` と、必要 artifactが揃うものの `check-receipt`。
- target file直列、関連回帰、標準受入全走。

## 総括

- 最重所見1: P1′は publication 後ではなく prepublication gateで、後段停滞は任意長のまま acceptedになり得る。
- 最重所見2: post-commit例外で accepted receipt・process rc=2・output不在の矛盾を構成できる。
- 最重所見3: accepted receiptの actuals は staging前の値で、checkerは新しい late gateを検証できない。
- 通常 flip の truth table、top-level output hash、manifest保持は、計画どおりなら整合する。
- 判定: **NO-GO**。依頼文言の正式な縮約、commit後例外規則、temp/rollback契約と fault testの追加後に再審査すべきです。