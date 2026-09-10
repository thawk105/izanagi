静的・read-onlyレビュー結果です。Web検索、pytest、build、qsub、実PBS、実計算ノード、pilot投入は未実施です。worktree差分はありません。A.1 の新規10 path/APIは、条件付き案どおり現物には未作成でした。

[B-01] 承認済み `submit_pilot` API と計画 API が別物

- 種別: 事実誤り
- 根拠: `s2-plan.md:11-13` は `submit_pilot(*, submission_id: str)`、`output/insights/2026-08-07_t139-mainrun-design/preregistration.md:374-412` は `submit_pilot(*, binding: PreregBinding)` と resolver 由来 binding を要求。`docs/decisions.md:12187-12204` は現行 export 禁止を明記。`orchestrator/preregistration/__init__.py:1-28` に gate API は存在しない。
- 成果物影響: `PreregBinding`、canonical ref、digest、祖先検査を経ないため、正当な admission 入力と durable intent が生成されず、受理集合は空のまま。
- 深刻度: blocker
- 提案: #4〜#6 と実 binding を同一 land で実装するか、代案2として `submit_pilot` を延期する。現在の P1 を production gate として land しない。

[B-02] DW-G04 の production caller が存在しない

- 種別: 発火せず
- 根拠: `s1-brief.md:53` は非 test caller 0件を実測。handoff:34 も投入経路ではない `publication/` の leaf import しかないと記録。`s2-plan.md:12-17,127-151` の caller は新規予定物であり、`tools/pegasus/admission_registry.json:160-164` は既存 a12 runner の登録である。
- 成果物影響: canonical release → `submit_pilot` → intent → qsub を起動する既存 artifact path／計測 ID がなく、`intent_ref`、`qsub_result`、attempt fragment は一度も生成されない。
- 深刻度: blocker
- 提案: 実在する canonical-main、alpha、a12 artifact を起点にした production invocation と、その submission ID の生成経路を明示するまで dormant と判定する。

[B-03] #4〜#6 の前段拒否が後段変異を先取りする

- 種別: 変異帰属不成立
- 根拠: `s2-plan.md:202-220` 自身が全入力で `A(x)=false`、定数 deny と正しい binding 検査を区別不能と認めている。`s2-plan.md:127-151` の intent、driver、preflight はその後段。`record-items-v2.md:470-476` は intent の qsub 前作成と attempt 被覆を要求する。
- 成果物影響: P07 intent、P08 qsub/preflight、P09 schedule に変異を入れても P04〜P06 が先に拒否し、受理集合・intent 被覆・qsub raw は変化しない。
- 深刻度: blocker
- 提案: 実 binding の正例を用意してから層ごとの mutation を行う。現状の「owned layer ready」は gate の検出力として数えない。

[B-04] a12 の pass を pilot readiness へ一般化できない

- 種別: 事実誤り
- 根拠: `stress_check_simulation.py:1-6,734-739` は admission gate ではなく、`pilot_ready=false`、残件 `[1,4,5,6,7,8,9]` と明記。a12 addendum:827-838,958-965 も cluster-level calibration を主張しない。artifact:1 は authoritative completed/pass だが、同じ claim_scope を保持している。
- 成果物影響: `verdict=pass` を #3 以上の認可根拠に使うと受理集合が過大になり、a12 の claim_scope・残件・pilot_ready の参照意味が壊れる。
- 深刻度: must-fix
- 提案: P03 は「tracked artifact の authoritative／completed／60 cells／exact Cartesian」の再導出に限定し、`pilot_ready` や calibration 完了を入力にしない。

[B-05] 親の一次資料で a12 状態が矛盾している

- 種別: 波及
- 根拠: `s1-brief.md:57-60,66` は handoff と artifact を一次資料として併記。handoff:28-36 は a12 実装・実行 0件、artifact:1 は completed/pass と記録している。
- 成果物影響: 同じ #3 evidence 参照が pass と未充足の両方になり、P03 の受理・拒否と evidence pointer が不安定になる。
- 深刻度: must-fix
- 提案: handoff を superseded と明記するか、canonical な一つの artifact/status へ統一する。gate は stale handoff を読まない。

[B-06] 代案2は D264 上は安全だが、発火しない

- 種別: 発火せず
- 根拠: `s2-plan.md:223-228` の `prepare_pilot_operational_assets` は `submit_pilot` を export しない。`docs/decisions.md:12187-12204`、`test_t139_preregistration_binding.py:904-916`、`test_t139_stress_check_simulation.py:21-26` の禁止名にも抵触しない。
- 成果物影響: schedule JSON、driver、collector は生成できても release、intent、受領証、受理集合には接続せず、mutation は単体テスト内でしか発火しない。
- 深刻度: must-fix
- 提案: 代案2を採るなら「operational preparation のみで未発火」と明記し、production caller と trigger ID ができるまで GO 判定・submit export・解除 decision を行わない。

[B-07] a09 generator の seed／byte 規約が実装可能な粒度で固定されていない

- 種別: 事実誤り
- 根拠: `s2-plan.md:110-119` の seed は `7df15572...b2615d` と省略。実値は addendum-a-reissue:573-601 の64文字 lowercase hexで、seed は raw bytes ではなく ASCII hex として連結する。
- 成果物影響: seed encoding または preimage の扱いが変わると block 順、156 semantic block、pilot slot 1〜8、operational digest、schedule FileRecord の sha256 が変わる。
- 深刻度: blocker
- 提案: full seed、ASCII、末尾 newline なし、lowercase hex、`dec(j)`、raw digest sort を実装契約へ逐語で移す。

[B-08] operational JSON の transport contract が不足している

- 種別: 変異帰属不成立
- 根拠: `s2-plan.md:121-123` は `authority="operational-only"` と `operational_schedule_digest` のみ固定。JSON の exact key、配列順、UTF-8／LF、digest 対象 bytes は未固定。canonical 側の規則は `record-items-v2.md:638-647` に別途存在する。
- 成果物影響: 同じ semantic tuple でも transport bytes と FileRecord digest が変わり、renderer の変異と実行時の差異を帰属できない。
- 深刻度: must-fix
- 提案: operational JSON 専用の canonical serialization を定義し、canonical `schedule_sha256` とは別物であることを docstring・intent・collector field 全てに固定する。

[B-09] durable intent の「認可成功後」は承認済み契約ではない

- 種別: 事実誤り
- 根拠: `s2-plan.md:217-218` は最終 admission 成功後に intent を作ると解釈。`record-items-v2.md:461,470-471` が明記するのは qsub より前・以後上書き不可だけで、認可との前後関係は書いていない。core:372-386 も intent 順序を定めていない。
- 成果物影響: intent の作成時点が変わると、拒否 submission の intent、qsub failure row、attempt exact coverage、`intent_ref` の受理集合が変わる。
- 深刻度: must-fix
- 提案: 認可成功 → intent → qsub の順序を新たな承認済み契約として明記する。§4.13からの導出だと主張しない。

[B-10] `FileRecord` と結果型の共有 API が現物にない

- 種別: 見積り
- 根拠: `s2-plan.md:41-57` は `FileRecord` を使うが、対象範囲の既存定義にはない。唯一確認できる `orchestrator/campaign/t810_validator.py:58-70` の `FileRecord` は mode、inode、ctime 等を含む別型である。
- 成果物影響: intent、handoff、qsub raw、failure pointer の wire shape が統一されず、collector と writer の受理・digest 判定が一致しない。
- 深刻度: must-fix
- 提案: T139 用型の定義場所、全フィールド、serializer を明示し、producer／driver／collector が同じ型または明示的 adapter を使う。

[B-11] qsub seam 以外のテスト注入境界がない

- 種別: 発火せず
- 根拠: `s2-plan.md:14,16-17,127-140` で明示される注入 seam は `dispatch_pilot` の `run_command`。既存の `dispatch_compute.py:1305,1477-1505` には同 seam がある一方、計画の `submit_pilot(submission_id)` と `collect_pilot(submission_id)` は repository／intent root／attempt root／clock を受けない。既存 collector は `collect_receipt.py:183-205` のように Path を明示的に受ける。
- 成果物影響: intent durability、O_EXCL、12-key collector、failure pointer を安全な fixture で発火できず、global path monkeypatch か実 worktree 依存になり、qsub を叩かない実効テストにならない。
- 深刻度: must-fix
- 提案: repository／artifact store／clock／writer／command runner を注入可能にする。`run_command` seam は維持し、既存 stress test の内部 monkeypatch pattern を pilot 境界へ持ち込まない。

[B-12] Pegasus の既存固定テストへの波及を落としている

- 種別: 波及
- 根拠: 新規4実行体は `s2-plan.md:14-17,184-185` に追加予定。`orchestrator/tests/test_hooks.py:1708-1752` は expected class、`:2413-2424` は registry の完全一致、`:2838-2862` は `tools/pegasus` の再帰 inventory と registry key の完全一致を要求する。
- 成果物影響: 4 path を追加して `test_hooks.py` の期待集合を更新しなければ、registry schema test と execution inventory test が赤になり、site/class の受理集合も未定義になる。
- 深刻度: blocker
- 提案: `test_hooks.py` の expected classes／entries を同じ land で更新し、`test_check_docs.py` を含む全 test grep の結果を再確認する。未実走なので緑とは報告しない。

[B-13] U1・U2・U4 の file ownership が素集合ではない

- 種別: 見積り
- 根拠: `s1-brief.md:134-142` は U1 を `orchestrator/preregistration/` 全体、U2 を `tools/pegasus/` とする。一方 `s2-plan.md:13,277` は U2 に `orchestrator/preregistration/pilot_schedule.py`、`:180,279` は U4 に同 directory の `__init__.py` を割り当てる。
- 成果物影響: schedule contract、package export、D264 test の merge 順が衝突し、schedule digest または export 集合を片方の patch が失う。
- 深刻度: must-fix
- 提案: directory 所有ではなく file 単位で再分割し、`pilot_schedule.py` の所有者を明示する。U4 の `__init__.py` と固定 test 更新は最後に統合する。

[B-14] 既存 Pegasus 資産との重複実装リスク

- 種別: 見積り
- 根拠: `s1-brief.md:51`、`s2-plan.md:140,190-193`。`dispatch_compute.py:350-365,1305,1477-1505` は qsub command runner・argv・raw capture の既存境界。`collect_receipt.py:33-64,107-125` は strict loader／FileRecord pattern だが、現行 final receipt schema。`qualification/submission.py:143-164` は short-write／fsync 済み。
- 成果物影響: qsub ID、raw stdout/stderr、durable intent の書式を二重実装すると、attempt の `qsub_result.raw`、intent sha、failure pointer が経路ごとに不一致になる。
- 深刻度: must-fix
- 提案: qsub は既存 `CommandRunner`／境界を共通化し、durable writer は既存 protocol を再利用・factor する。`collect_receipt` は loader 部分だけ参考にし、allocation null を許す T139 exact-12 collectorとしては再利用しない。a12 PBS は site/header のみ再利用する。

[B-15] `admission_registry.json:160` は新規挿入箇所ではなく既存 a12 entry

- 種別: 事実誤り
- 根拠: `s2-plan.md:184` は `admission_registry.json:160` に新規4実行体を登録するとするが、現物の `tools/pegasus/admission_registry.json:160-164` は `run_t139_a12_stress_check.py`。`tools/pegasus/README.md:17` は手順表の見出しであり、pilot entry の位置ではない。
- 成果物影響: 行番号依存の patch では既存 a12 entry の重複・欠落を起こし、registry と execution inventory の受理集合が不一致になる。
- 深刻度: nit
- 提案: JSON key 単位で4 pathを追加し、README は実行体名・site・手順を明示する。行番号を実装契約にしない。

R2確認: `s2-plan.md:121-123` は `t139-a09-operational-schedule/v1`、`authority="operational-only"`、`operational_schedule_digest` のみを指定し、`schedule_sha256`、canonical TSV、157行表を明示的に除外しています。したがって、計画文面上の R2(a) 違反は確認していません。ただし新規 schedule／collector 実コードが未作成のため、docstring と受領証への実際の書き込み経路は未検証です。

Scope監査: approval manifest、D308機械執行、`qualification/submission.py` の修正、`main_submission`、semantic validator、pilot実走投入を除外する記述は `s1-brief.md:18-27` と `s2-plan.md:188-194` にあり、scope逸脱は確認していません。逆に、既存 caller と `test_hooks.py` の取り込みが scope内の欠落です。

判定: NO-GO

- 承認済み `PreregBinding` に到達できず、P04〜P06 の前段拒否が後段変異を隠す。
- production caller／DW-G04 発火点がなく、intent・qsub・collector成果物を生成できない。
- 代案2は D264-safe でも dormant な operational preparation に留まり、land2 の実効性を満たさない。

## 総括

静的・read-only の敵対レビューだけを実施した。  
Web検索、pytest、build、qsub、PBS、計算ノード実走は行っていない。  
pilot投入も行っていない。  
現行 worktree の差分はゼロである。  
P1 の `submit_pilot` 署名は承認済み core 契約と一致しない。  
#4〜#6 が未実装のため、最終 admission の正例を作れない。  
production caller と具体的な DW-G04 trigger が存在しない。  
a12 artifact は完走を示すが、pilot readiness や calibration 完了は示さない。  
a12 handoff と現行 artifact の状態記述も一致していない。  
a09 の R2 operational-only 方針は計画上守られている。  
ただし a09 の seed と transport bytes の契約は補強が必要である。  
intent の認可前後関係は承認済み文書からは導けない。  
Pegasus の新規実行体は既存固定テストへ波及する。  
U1、U2、U4 の所有境界も素集合ではない。  
以上により、今回の land 2 / Q4 scope は NO-GO である。