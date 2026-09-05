結論として、現 plan のまま実装へ進むのは不可です。静的検査で blocker 4 件、must-fix 4 件、nit 1 件を確認しました。pytest は実行していません。

## blocker

### 所見 1 — proof と artifact header の自己整合が閉じていない

- (a) [実測] plan は `reported proof == live inspector proof` を要求しますが、proof の `freeze_sha256` / `protocol_sha256` と artifact top-level の同名 field の直接比較を定めていません。現行 pure verifier はこれらの header digest を値として参照しません。
- (b) [実測] [s2-plan.md:271](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:271)、[s2-plan.md:287](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:287)、[s8b_floor_stats.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:682)、[s8b_floor_contract.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:81)。
- (c) [推測] 放置時: live proof が campaign A を指したまま artifact header だけ campaign B の digest に変えた v5 を D1 verifier が受理し、レポート identity と台帳参照が分離します。
- (d) [推測] pure verifier で `proof.freeze_sha256 == artifact.freeze_sha256` と `proof.protocol_sha256 == artifact.protocol_sha256` を直接検査してください。schedule は artifact 内の唯一の申告値である proof field を、wrapper が外部 schedule から再計算した digest と比較すると明記し、header 単独改変の負例を追加してください。
- (e) [実測] 対応は P1。現行 producer を v4 のままにする判断は正しいものの、v5 契約の binding が未完です。

### 所見 2 — M14 は別世代台帳への差替えを殺せない

- (a) [実測] plan の binding 負例が「reported digest の差替え」だけなら、M14 の mutant は依然拒否します。freeze/protocol 差替えでは対象 path が不在、schedule 差替えでは同一 path の genesis binding 不一致になるためで、mutant が拒否しただけでもテストは緑です。
- (b) [実測] [s2-plan.md:288](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:288)、[s2-plan.md:388](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:388)、[s2-plan.md:437](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:437)、[s8b_attempt_registry.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:649)、[s8b_attempt_registry.py:793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:793)。
- (c) [推測] 放置時: 外部 context は A、artifact header/proof と実在する別 ledger は B、という入力で、M14 mutant が B を選んで D1 の受理集合を広げます。
- (d) [推測] 同じ shared root に A と B の両方の有効な v2 generation を作るテストが必要です。artifact/proof は B、wrapper の外部引数は A とし、正常実装だけが A を選んで拒否し、M14 が B を replay して受理する形にしてください。schedule 単独ケースは同じ freeze/protocol path の genesis を別 schedule にして、外部 schedule だけ A とします。
- (e) [実測] 対応は P2/P6。API 配置よりも、外部 context が generation 選択の唯一の権威であることの直接証明が不足しています。

### 所見 3 — read-only API の root 解決が未規定で、自然な実装が書込みを行う

- (a) [実測] 新 API は `repo_root` を受けますが、plan の replay 手順は既に得られた `root` から始まり、root の取得方法を定めていません。既存の自然な helper `_entry_paths()` は `provision_shared_admission_root()` と fsync を実行し、directory や lock inode を作成し得ます。計画済みの「write lock tripwire」だけではこれを検出できません。
- (b) [実測] [s2-plan.md:121](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:121)、[s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:157)、[s2-plan.md:367](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:367)、[s8b_attempt_registry.py:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:520)、[s8b_holdout_admission.py:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_admission.py:679)。
- (c) [推測] 放置時: verifier inspection が欠落 root、claim directory、lock inode を生成し、検査対象の共有 filesystem 状態を変更します。
- (d) [推測] `admission.shared_admission_root(repo_root)` を使い、既存 holdout inspector と同じ root/lock の lstat・symlink・path-kind 検査後に `_locked_readonly` へ入ることを固定してください。`_entry_paths` と `provision_shared_admission_root` の呼出しを失敗させる tripwire、および前後の tree bytes/inode 不変検査が必要です。
- (e) [実測] 対応は P2。公開 API の置き場所は妥当ですが、read-only 実装境界が未完成です。

### 所見 4 — D1340 の世代横断予算 replay が inspector から落ちている

- (a) [実測] plan は選択した current generation を `core.load_attempt_registry()` へ渡すだけです。`_registry_generation_paths_locked()` は他世代を regular file として読むだけで、JSON/chain/budget replay はしません。一方、既存 writer は `_load_other_generation_budget_counts_locked()` で他世代の count を seed してから current generation を replay します。
- (b) [実測] D1340 は [decisions-verbatim.md:147](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md:147)、plan は [s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:157)。実体は [s8b_attempt_registry.py:1392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1392) と [attempt_registry_core.py:1465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1465)。
- (c) [推測] 放置時: cap 10 に対して二世代へ各 6 start を置いた状態が世代単体では通り、freeze-wide では 12 の不正台帳を proofable として受理し、過剰試行由来の floor 値を certified 候補へ持ち込めます。
- (d) [推測] 同じ shared lock 内で他世代を全 replay し、その budget counts を `load_attempt_registry_with_budget_counts()` の current replay に渡してください。各世代が単独では cap 内、合計だけ cap 超過となる負例と、他世代の壊れた tail の負例が必要です。
- (e) [実測] 対応は P2。確定裁定 D1340 との不整合です。

## must-fix

### 所見 5 — N 行内改変の拒否理由が誤っている

- (a) [実測] prefix algorithm 自体は D1337 を満たしますが、plan は N 行内改変を「full replay の event hash だけが拒否」としています。`event_sha256()` は `event_sha256` 自身だけを除外し、payload、`event_index`、`previous_event_sha256` をすべて hash します。改変行以後の chain を再計算すれば full replay は成功し、元の `head_at_N` との比較が拒否する層です。
- (b) [実測] [attempt_registry_core.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:240)、[attempt_registry_core.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:246)、[attempt_registry_core.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:449)、[s2-plan.md:402](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:402)。
- (c) [推測] 放置時: 単純な「payload だけ変更」テストは緑でも、自己整合する別 prefix への再 chain 攻撃に対する proof-head gate の帰属が証明されません。
- (d) [推測] 二つに分けてください。未再計算改変は `_assert_chain`、genesis を含む改変後に N 以後まで全 hash を再計算した入力は `rows[N-1] == reported head` だけで拒否させます。
- (e) [実測] 対応は P2/P3。

### 所見 6 — P3 の到達可能な v2 行集合が狭すぎる

- (a) [実測] v2 reservation は `start` だけでなく `pre-observation-seal` も同時に追加します。さらに現行 test は v2 の `classification` と `observation-start` を production adapter 経由で生成しています。`record_attempt_recovery()` にも v2 拒否はありません。拒否されるのは terminal の二層だけです。
- (b) [実測] 親記述は [s1-brief.md:59](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md:59)、plan は [s2-plan.md:411](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:411)。現物は [attempt_registry_core.py:1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1615)、[test_s8b_attempt_registry.py:2977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:2977)、[s8b_attempt_registry.py:2305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2305)、[s8b_attempt_registry.py:2430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2430)。
- (c) [推測] 放置時: C が既存の classify/observe 経路を接続した後、未検査の正当 ledger を inspector が拒否するか、誤った N/head を返して producer finalization を停止させます。
- (d) [推測] 正例を genesis-only N=1、reservation 後 N=3、classification 後 N=4、observation 後 N=5、valid recovery 後の形まで広げてください。terminal は引き続き正例に入れません。
- (e) [実測] 対応は P3。P3 は却下です。

### 所見 7 — v4 の直接下層検査が D1522 を満たさない

- (a) [実測] v4 に `attempt_registry` を足すと、現行 verifier の既存 exact-key gate が既に拒否します。plan の新しい pure-verifier 負例だけでは下層 `_RESULT_V4_KEYS/result_keys_for_mode` を直接検査していません。また現行 contract test は `base = _RESULT_KEYS` を期待値にも使うため、base 自体への field 混入を独立検出しません。
- (b) [実測] [s8b_floor_stats.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:734)、[test_s8b_floor_contract.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_contract.py:366)、[s2-plan.md:379](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:379)、D1522 は [decisions-verbatim.md:202](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md:202)。
- (c) [推測] 放置時: v4 key set へ proof field を混入させる変異の拒否が上層 verifier にしか帰属せず、下層契約の受理集合拡大を恒真な経路で見落とします。
- (d) [推測] pilot/official/degraded の各 v4 key setを直接取得し、`attempt_registry not in keys` を literal で固定してください。v5 との集合関係だけでは不十分です。v4 正例対照と「v4 key setへ field追加」変異も登録してください。
- (e) [実測] 対応は P4。

### 所見 8 — 単位 C が supersede する pin の一覧がない

- (a) [実測] P1 は後続 C が `RESULT_SCHEMA` を v5 に変える前提ですが、plan は `test_s8b_floor_contract.py:180` を supersede 禁止とし、既存 pin は一つも supersede しないと記します。また二つの fixture は current `RESULT_SCHEMA` を動的に参照するため、C の切替時に proof のない v5 へ自動変質します。
- (b) [実測] [s1-brief.md:53](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md:53)、[s2-plan.md:353](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:353)、[s2-plan.md:358](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:358)、[s8b_v2_freeze_fixture.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/s8b_v2_freeze_fixture.py:340)、[test_s8b_ratified_verify.py:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_ratified_verify.py:460)。
- (c) [推測] 放置時: C の切替で malformed v5 fixture が発生し、D1341 の最終統合が赤になるか、fixture が proof のない v5 を正例として誤表現します。
- (d) [推測] 今のうちに移行表を固定してください。`test_s8b_floor_contract.py:180` は C で v5 へ supersede、`test_s8b_floor_stats.py:596` は legacy-v4 正例として維持、動的 fixture 二件は `LEGACY_RESULT_SCHEMA` へ固定するか D2 で v5 proof を組み立てるかを明記します。`test_s8b_floor_campaign.py:6552` は producer v5 正例へ追従させます。
- (e) [実測] 対応は P1。現 wave の v4 維持は採用できますが、最終切替契約は条件付きです。

## nit

### 所見 9 — brief の実測件数に誤りと曖昧さがある

- (a) [実測] `result_keys_for_mode()` の call expression は 22 でなく 12、production 3、test 9 です。`RESULT_SCHEMA` raw word は production 7 file、test 5 fileです。このうち意味的な S8B 閉包は production 5 file、test/support 4 fileで、production 2 fileとtest 1 fileは同名衝突です。
- (b) [実測] 誤記は [s1-brief.md:64](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md:64) と [s1-brief.md:86](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md:86)。plan 自身の訂正 [s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:28) は正しいです。
- (c) [実測] 放置時: 成果物の値や受理集合は変わりませんが、fanout と所有面の根拠が再利用時に誤読されます。
- (d) [実測] brief を plan の実数へ訂正してください。`output/` の実 artifact JSON に v4 は 0 件で正しい一方、v4 文字列自体は tracked 文書 6 file にあるので「result JSON bytes 0 件」と限定すべきです。v5 `attempt_registry` を持つ JSON は 0 件です。
- (e) [実測] 対応は P4。実アンカー表の symbol 行番号は全件一致し、`_measurement_generation_* :900-1136` も実定義 :923-1054 を包含していました。

## 反証しなかった点

- [実測] D1337 の中心手順、すなわち full live replay 後の `len(rows) >= N` と `rows[N-1].event_sha256` 比較は正しいです。壊れた N 以後の tail を拒否し、正当 append を許し、`reported` 欠落や `N > len(rows)` を skip する経路も plan にはありません。
- [実測] v2 terminal は core validator と adapter 入口で引き続き二層拒否され、plan は E1/E2 や `finished_at` の実装を本 wave に混入させていません。
- [実測] producer v4 維持と v5 別名定数は、unlanded checkpoint と D1341 の両立形として正しいです。
- [実測] brief/plan は v5 gate の production 呼び手が 0 件であること、C/D2 が未実装であることを明記しており、「現在効いている」との誤表示はありません。D1342 に反する最終発行層の再検査も提案していません。

## 裁定パッケージ候補

### 所見 10 — coverage API の exact signature を C より先に固定できない

- (a) [実測] plan の将来 API は `prefix_rows` だけから `(campaign_run_id, manifest_sha256, run_relpath, attempt_id)` を抽出する形ですが、現行 terminal row の認証 key にこの4 fieldはありません。C の terminal 証拠契約が先という確定順序とも逆です。
- (b) [実測] [s2-plan.md:294](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:294)、[s8b_attempt_profile.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:445)、[a2beta-README.md:103](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a2beta-README.md:103)。
- (c) [推測] 放置時: D2 が identity を producer 自己申告から補うか全 v5 を拒否し、coverage の全単射または受理集合が変わります。
- (d) [推測] 今は意味要件だけ残し、exact signature は固定しないでください。C が terminal rowまたは認証済み claim joinとして4軸 identity を提供した後、その normalized projection を D2 が受ける形に決めるべきです。
- (e) [実測] 対応は P6。単位 C/D2 の裁定候補で、本 wave の実装対象外です。

### 所見 11 — D1533 の非保証範囲を成果物へ載せる所有者がない

- (a) [実測] D1533 は削除・改名・別 path 再作成を防がないことを成果物へ明記すると定めますが、exact 7-field proof と C への handoff にその出力先がありません。現行 source docstring の注意書きは成果物上の明記ではありません。
- (b) [実測] [decisions-verbatim.md:246](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md:246)、[s2-plan.md:138](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:138)、[s2-plan.md:327](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md:327)、[s8b_floor_stats.py:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1045)。
- (c) [推測] 放置時: v5 report が ledger の削除後同一 bytes 再作成まで防ぐ証明だと誤読され、台帳参照の保証範囲が実体より広く表示されます。
- (d) [推測] 単位 C の `result.md` に固定文を出す所有を明記してください。JSON field が必要なら D1 の exact key 契約へ影響するため、実装前に別途決める必要があります。
- (e) [実測] 対応は P1。単位 C の成果物契約候補です。

## 総括

- blocker: 4 件。proof自己束縛、別世代攻撃検査、read-only root、D1340 replay。
- must-fix: 4 件。再chain負例、P3値域、v4下層直接検査、C移行pin。
- nit: 1 件。裁定パッケージ候補: 2 件。
- P1: 条件付き。v4据置は採用、v5 binding・移行pin・D1533 handoffを補正。
- P2: 条件付き。API配置は採用、read-only取得と世代横断replayを補正。
- P3: 却下。classification、observation、recoveryまで到達可能。
- P4: 採用。ただし件数訂正とv4 key下層直接検査が必要。
- P5: 採用。追加負例を含めても提示された40〜70 node帯には収まる見込み。
- P6: 条件付き。2実装子のfile所有は妥当だが、修正版signatureを先に固定すること。
- pytest未実走。HEAD `50dbf9158`、worktree cleanを静的確認。