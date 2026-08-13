---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t907-t908-t910-acceptance-integrity
seq: 1
title: 受入 integrity 3 件を実装し、既知赤との非両立を裁定どおり checker 統合で解いた — 受領証の発行条件を「rc=0 または赤が全て非帰属」へ広げ、log hash を束縛した (コード + docs、変異 7/7 KILLED、branch worktree-dev-wave-t907-recovery)
---

## 本文

- **裁定の脅威モデルを段 4 で確定した。** [T-908] の起票理由は「2026-08-12 に待ち手を迂回して
  直接走した実例」であり、防ぐ対象は**事故**であって同一 Unix user による意図的偽造ではない。
  段 2 プラン自身も「receipt は同一 user に対する暗号学的 attest ではない」と認めた。
  この線引きを基準に敵対レビューの所見を裁き、**偽造対策にしか効かない機構は scope 外**として
  裁定パッケージへ返した (実装済みと書かない)。詳細は {{D:acceptance-authority-threat-model}}。
- **親裁定 1 件で段 2 プランを覆した。** プランは receipt 検証を `_locked_preflight` の前に
  置けと書いたが、既存の provenance 期待値 (rc 29) と両立しなかった。fix 子は規律どおり
  実装を変えず報告して停止した。親は「守るべきは receipt 無しに main を進めず成功も返さない
  ことだけで、provenance との前後関係は要求ではない」と裁定し、順序だけを緩めた。
  安全性はコードで確認した — `_verify_acceptance_receipt` は `tools/dev_wave_land.py:2525`、
  成功を返す全経路 (already-landed 2 箇所、ff-only merge、`_postcondition` の landed) は
  すべてその後で、`_locked_preflight` は拒否用 `LandResult` しか返さない。
- **敵対レビュー 2 本が blocker 5 件・must-fix 6 件を出し、real 分をすべて処理した。**
  採用したのは orphan temp receipt の land 拒否、`held-self → acquired` の ownership 遷移漏れ
  による lease 漏れ、submodule 未初期化の claim 前 fail-closed、TTL 再確認後の publish 窓の閉鎖、
  `PYTEST_ADDOPTS` 等による無実走 receipt の封鎖、`assume-unchanged` / `skip-worktree` への
  盲目の解消。refuted は 1 件 (receipt 検証順序、上記)。
- **変異が実在の検出力の穴を 1 件実証した。** 1 巡目 (baseline PASSED) で
  `--acceptance-receipt` を `required=False` にする変異が **SURVIVED** した。
  CLI テストが新 2 引数を両方省いており、`--acceptance-wave` の argparse rc=2 が先取りしていた。
  これはレビュー B が所見 RB5 で予告した穴そのもので、fix 3 巡目の再照準後もまだ開いていた。
  1 引数ずつ欠落させる形へ直して 2 巡目で KILLED になった。
- **変異 2 巡目 = baseline PASSED、10/10 KILLED、SURVIVED 0 / MISMATCH 0** (anchor `bb4767d3`)。
  ただし **M02 / M03 / M05 の失敗集合は 112 / 28 / 97 件と大きく、fake の event 列不一致が
  支配している。** これらは「その定数・呼び出しが load-bearing である」ことは示すが、
  「受理集合が期待方向へ変わった」ことの単一理由の証拠にはならない (`DW-M03` の冗長 gate 扱い)。
  **単一理由で検証できたのは M01 / M04 / M06 / M07 / M08 / M09 / M10 の 7 件。**
- **1 巡目の baseline は [T-892] の既知赤で FAILED になり、harness が production write を
  開始しなかった。** [T-892] の起票文が予告した事象そのものである。10 変異のいずれとも
  無関係な環境由来の赤なので、その 1 nodeid だけを `--deselect` して再走した
  (除外は 1 件のみ・期待 node と重複なし)。
- **`docs/dev-wave/**` は land の receipt 契約を収容できなかった。** 実測: `DW-O23` (L1) へ
  最小 3 行を足すと予算を 229 bytes 超過、`DW-O25` (L2) は exact 契約で pin 済み・単節上限
  1,000 に対し 1,462 bytes、新規 L2 節は entry の条件表に参照が要るが
  `.claude/commands/dev-wave.md` は 9,500 bytes ちょうどで**余白 0**。
  ユーザーの既裁定に従い上限は上げず、運用の正本である `docs/pegasus-runbook.md` §7.3 だけを
  更新した。`DW-O23` 側の欠落で起きるのは rc=2 の明示的な失敗であって静かな誤結果ではない。
  収容先は {{T:dev-wave-docs-land-receipt-contract}} へ起票した。
- **`tools/dev_wave_wait.py producer` の fail-open を 5 回実測した。** 投入直後に張った
  待ち手が、`.done` も成果物も無く producer が生存しているのに出力ゼロ・rc=0 で即座に返る
  (02:44 / 03:12 / 03:55 / 03:58 / 04:14 JST)。毎回「成果物実在 + `.done` + producer 死」の 3 点照合で
  検知して張り直したため進行には影響しなかったが、これは本 wave の主題 (受入 gate の
  fail-closed 化) と同型の欠陥である。{{T:waiter-producer-completion-fail-open}} へ起票した。
- **段 8 の自己改善候補は 4 件で、routing 先は 2 つに分かれた。** 待ち手の fail-open は
  同型再発なので新規 F を作らず F24 へ追記した。残る 3 件 —
  (i) 逐次 2 単位の段 5 は単位 1 を commit してから単位 2 を投入する、
  (ii) 同一ファイルへ大きく積む author 単位は `--max-model-calls` の既定 100 では足りない、
  (iii) 後続段の必読には「存在が保証される成果物」だけを挙げる (SIGTERM で死んだ子の報告を
  必読にすると後続が連鎖 fail-closed する。本 wave の段 6 レビュー 2 本が実際にこれで空振りした) —
  は `docs/dev-wave/**` の既存 leaf 節へ統合すべきだが、**収容余地が無いことを byte で実測した**
  (上記のとおり L1 は 229 bytes 超過、L2 は pin + 単節上限、command は余白 0)。
  予算は上げない方針なので、本項の実測として残し、収容は
  {{T:dev-wave-docs-land-receipt-contract}} と併せて裁定する。
- **段 5 の子が 1 本 model call 上限 (既定 100) で SIGTERM され、完了報告を残さず落ちた。**
  単位 2 は待ち手 +503 / land +259 / テスト +1,189 行の規模だった。単位 1 を commit せずに
  単位 2 を積んだため、同じ未 commit 差分に両者が混ざって切り分け不能になった。
  snapshot patch (110,577 bytes) で保全し、継続 fix 子で完遂した。
- **検査結果。** 焦点走 269 passed / 1 failed (`test_exploration_external_root_keeps_wave_clean`
  = [T-892]、焦点走限定・本差分と無関係)。provenance 全史監査 3,074 件・新規違反なし。
  `check_docs` 違反なし。
- **受入全走 = 1 failed / 10,363 passed / 65 skipped** (115.84 秒、tested tip `dbf32a64`、
  待ち手経由、2026-08-13 04:19 JST)。唯一の赤は
  `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  で、**main 単独で決定的に再現する**ことを親が独立に実測した
  (`validate_condition_freeze_at(repo, d864fd4b)` → `PreregistrationError [octopus-merge] d1de13ad`)。
  本 wave の差分とは無関係である。
- **本 wave は land しない。** 受入 command が rc≠0 だったため、裁定どおり **receipt は
  発行されなかった** (gate は設計どおり動作した)。しかしこれにより、
  **[T-908] (a) の実装と 2026-08-13 の既知赤裁定が両立しないことが実証された** —
  main に既知赤がある間、どの wave も receipt を作れず land できなくなる。
  これは第 8 束の [T-908] 裁定時点で未見の相互作用なので、`DW-S04` に従い親は不採用にせず
  ユーザー再裁定へ戻す。詳細と選択肢は {{T:acceptance-receipt-vs-known-red}}。
  lease は待ち手が終端で release 済み (lease directory が空であることを実測)。

### 裁定後の回収 (2026-08-13 08:11〜、別 context、branch `worktree-dev-wave-t907-recovery`)

- **ユーザー裁定 (第 9 束 #1) は「(b) の変形 = checker 統合」だった。** 批准済み既知赤 registry は
  作らず、receipt の発行条件を「rc=0 **または**非帰属 checker 緑」へ拡張する。あわせて
  #9 [T-1019] = 待ち手の receipt へ log hash 束縛 (checker 自身が受入走を所有する案は不採用)、
  #10 [T-1020] = 新規機構を作らず本 wave の land で閉じる、が確定した。
- **取り残し branch を 1 回の merge で回収した。** land 前に blob 照合で二重採番を防いだ
  (`_verify_acceptance_receipt` / `_acceptance_receipt_preflight` は main に 0 件、
  3 fragment も未 fold)。連鎖 merge を避けたのは fold 形状検査 (F265 / F266) 対策である。
- **裁定を機械語へ落とす際に、親が段 4 でコード実測により fail-open を 1 件摘出した。**
  `tools/check_acceptance_reds.py` の `rc == 0` は 2 つの意味を持つ —
  `status = "non-attributable-only"` (赤が全て非帰属) と `status = "green"`
  (log から赤 nodeid を 1 件も取り出せなかった) である。後者は「非帰属だった」ではない。
  受入 command が非 0 で終わったのに赤 nodeid が 0 件になる経路 (collection error /
  internal error / crash / xdist worker の異常終了) は実在するので、裁定文の「非帰属 checker 緑」を
  `rc == 0` だけで実装すると**崩れた受入が受領証を得る**。
  受理は `checker_rc == 0` かつ `status == "non-attributable-only"` のときだけとした。
- **敵対レビュー A が同型の穴をもう 1 段深く出した (blocker)。** 赤の非帰属は
  「走行が崩れたこと」を説明しない。pytest が summary まで出したあとに wrapper が
  signal・後段 gate で落ちても、log 中の赤が全て非帰属なら receipt が出てしまう。
  親が実測で裁定根拠を取った — `tools/run_tests.py` の main は
  `return subprocess.call(cmd, cwd=_REPO)` で pytest の rc をそのまま返し、
  テストが落ちた走行は rc=1 である (焦点走で 4 failed の走行が rc=1 を返した実測)。
  `run_tests.py` 自身の失敗は `_DELETION_GATE_RC = 13` / `_PEGASUS_DISPATCH_RC = 16` など
  1 以外なので、**受理を `child_rc == 1` ちょうどへ狭めた**。
- **敵対レビュー B が NO-GO を出し、blocker 3 件・must-fix 5 件のうち real 分をすべて処理した。**
  採用 = runbook の受入例が新引数を欠く (親が docs で修正)、test consumer の不整合、
  log 全量のメモリ読込 (1 MiB chunk 化)。
  **本 wave では実装せず限界として記録した 3 件** = checker に timeout が無い /
  checker 実行中の lease heartbeat が無い / checker を専用 process group で起動しない。
  いずれも倒れる向きは fail-closed であり、値の決定には裁定が要る。{{T:acceptance-red-check-robustness}} へ起票した。
- **非帰属受理経路が実物で成立することを end-to-end で実証した。** 合成の既知赤を作り、
  **実 waiter → 実 checker → 実 land** を通す試験が緑になった (焦点走、計算ノード)。
  ただし**実受入データでの検証は未達**である — 本 wave の受入が rc=0 で終われば
  `child-green` 経路しか通らず、非帰属経路は [T-1027] (checker が実 log で rc=2) の land 後に
  しか実データで確認できない。「実データで 1 回通した」とは書かない。
- **変異 = baseline PASSED、7/7 KILLED、SURVIVED 0**、うち 6 件は期待完全集合と exact 一致。
  N2 のみ 1 件差で、その差分はフレークだった (下記)。
  「checker が緑と言った判定を受け入れる」変異は単独では殺せない — 受領証を作る手前に
  「赤 nodeid が 1 件以上ある」二層目があるためで、`DW-M04` に従い両層同時変異として登録した。
- **待ち手 signal handler 復元テストのフレークを 2 例実測した。** 変異 2 巡目で
  `test_signal_after_core_success_uses_restored_real_handler` が `tools/dev_wave_land.py` だけを
  変異させた N5 の失敗集合に現れ、3 巡目では
  `test_public_main_failure_restores_handler_without_release` が N2 の集合から消えた。
  **land のみの変異が待ち手の signal テストを落とすことは構造上ありえない**ので、
  帰属させずフレークとして {{T:waiter-signal-handler-test-flake}} へ起票した。
- **待ち手 producer の fail-open は本 context でも 3 例再発した** (09:12:29 / 09:17:29 / 10:19:43 JST)。
  通算 8 例。毎回 3 点照合で検知して張り直したため進行への影響はない。
- **受入全走を 3 回投入し、3 回とも同じ構造で fail-closed した。本 wave は land しない。**
  (10:15:27 / 10:22:57 / 10:33:42 JST、tested tip `11032ea5`、tested main `a2c42574`)
  3 回とも受入 command が rc=1 (赤 1〜2 件) で終わり、**設計どおり非帰属経路へ入って
  checker が起動し**、その checker が rc=2 (判定不能) を返したため
  `acceptance-red-check rc=70` で受領証が出なかった。**gate は裁定どおり動作している。**
- **checker が rc=2 になる機序を実データで特定した。これは [T-1027] とは別の欠陥である。**
  `tools/check_acceptance_reds.py:277` の collect 段は `timeout: float | None = 120.0` を既定に持つが、
  この collect は `--force-dispatch` で計算ノードへ投入されるため、queue 待ち + job 起動 + 実行が
  120 秒を容易に超える。3 回とも `TimeoutExpired ... timed out after 120.0 seconds` だった
  (対象は `test_codex_worker_launch.py` 2 回、`test_dev_wave_wait.py` 1 回)。
  単独再走側 (同 `:471`) は `timeout=None` なので、**collect 段だけが締まりすぎている**。
  [T-1027] は nodeid の exact 一致の話であり、本件は timeout の話で、両方直らないと
  非帰属経路は実運用に到達しない。{{T:acceptance-red-check-robustness}} へ追記した。
  これは段 6 の敵対レビュー B が blocker B-02 / must-fix B-05 で予告した面であり、
  **静的レビューでは出ず、親が実データで走らせて初めて出た** ([T-1028] の趣旨の実例)。
- **受入の赤はすべてフレークで、本 wave の差分に帰属しない。** 1 回目の 2 件
  (`test_codex_worker_launch.py::test_parallel_jobs_preserve_both_manifest_entries` と
  `test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler`) は
  単独再走で **2 passed**。3 回目の 1 件は
  `test_dev_wave_wait.py::test_signal_after_core_success_uses_restored_real_handler` で、
  本日 4 例目の signal handler フレークである。
  後者が差分由来でないことは変異 2 巡目が示している — **`tools/dev_wave_land.py` だけを
  変異させた N5 の失敗集合に現れた**のであり、依存関係上ありえない。
  混雑も実測した (10:23:59 JST に codex 関連 35 process、うち [T-1027] を直している wave 自身の
  fix 子が稼働中)。

## 次の一手差分

### 完了

- [T-907] 走行後に `postrun-clean` / index flag 検査 / 走行前後の tree fingerprint 比較を足した。
  child rc が非 0 でも必ず走り、木が変わっていれば rc=70 が child rc に優先する。
  fingerprint は HEAD SHA / clean status / binary diff / recursive submodule status を
  label と byte 長つきで SHA-256 に入れた自己完結実装。変異で KILLED を確認済み。
  remaining: none
  base: 9eb93a3c673bdff1c5eb8413ca68df4c3d3ab45fd70c3c320ceaebb2b0032bf5
- [T-908] 待ち手経由だけを権威ある dev-wave 受入と定義した。待ち手が repo 外へ closed JSON の
  receipt を発行し、`tools/dev_wave_land.py` が必須 consumer として検証する。欠落・不正・
  予約 temp 名前空間・束縛不一致は rc=23 で main を 1 bit も変えず拒否し、`already-landed` も
  通さない。逃がし道は作っていない。`run_tests.py` 側への同等 gate は裁定どおり不実装。
  remaining: none
  base: f2aaabe1257417ddc985a8b083c8e18732fc500be10d7d9bd40879cbb46b104e
- [T-910] `output/env/pegasus/floor/job-staging/` を ignore し 88 file を index から外した
  (disk bytes は全 file sha256 一致で保持)。`attempts/submissions/` の 51 file は tracked のまま
  (index は byte 単位で不変)。受入の clean 述語を `--untracked-files=all` へ強めた。
  remaining: none
  base: 531003015c3ad665b6bf7a01a038e50074f9ebc9b2c32bfba20305895f298e1c
- [T-1019] 待ち手が受入 child の stdout/stderr を必須 `--log-file` へ自分で捕獲し、その bytes の
  SHA-256 を receipt へ束縛するようにした。親が渡した既存 log は受け取らない (これが
  「任意の過去 log を渡せば非帰属判定を素通りできる」穴を閉じる)。checker は待ち手が
  その log に対して起動し、checker receipt の `log_sha256` / `wave_tip` / `tested_main` /
  `schema_version` / 全 node の `classification` を照合してから受理する。
  裁定どおり「checker 自身が受入走を所有する」形は採らなかった。
  remaining: none
  base: b19aa1f977aac69b103f64e503edf2d56a212629d269ed86365021f31d0c2300
- [T-1020] 裁定どおり新規機構は作らず、land 側は #1 が要求する照合だけを足して閉じた。
  `_verify_acceptance_receipt` が `verdict` で分岐し、`child-green` では checker 系 5 field が
  すべて null かつ `child_rc == 0`、`non-attributable-only` では `child_rc == 1` かつ
  `checker_rc == 0` かつ `checker_blob_sha` が `<tested_tip>:tools/check_acceptance_reds.py` と
  一致することを要求する。`LandResult.as_json()` へ `acceptance_verdict` と
  `acceptance_red_nodeids` を足し、**どの赤を非帰属と判定して land したか**を残す。
  これが registry を作らずに裁定 (b) の眼目を満たす部分である。
  ただし残るのは land 結果 JSON であって canonical 台帳ではない (job directory の JSON を
  失うと対象 nodeid を再構成できない)。
  remaining: none
  base: 988f9395dc05bb1de3482eead8123ccb99ccb4de214fb103a946f1a5f33efa15

### 更新

- [T-892] **P3・優先度を上げる (2026-08-13 実測)**: 本 wave の変異 1 巡目で、
  この赤が **baseline を FAILED にして harness の production write を止めた**。
  起票文が予告した「変異 harness の baseline が緑にならず部分集合の変異検査が原理的に
  回せない」が実際に発火した。回避には当該 nodeid の `--deselect` が要る。
  base: 36552692c4d9ef25f8d79a7510a198fa85ae8ffafa8e72bea5739b12b1bad8f5

### 新規

- {{T:acceptance-receipt-vs-known-red}} **P1・新規・ユーザー裁定待ち (2026-08-13 実測)**:
  **[T-908] (a) の実装と 2026-08-13 の既知赤裁定が両立しない。** 前者は「受入 command が
  rc=0 でなければ receipt を出さない、逃がし道を作らない」で、後者は「既知の赤で受入を
  止めてはいけない、記録に残して land してよい」である。main tip に既知赤がある間
  (`test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`、
  4 親 octopus merge `d1de13ad` 由来、`d864fd4b` 単独で決定的に再現)、
  **どの wave も receipt を作れず land できなくなる**。本 wave の受入
  (1 failed / 10,363 passed / 65 skipped) がこれを実証した。
  選択肢: (a) 既知赤を解消する修正 (`_assert_history_transition` の n 親一般化) を先に land し、
  receipt 契約はそのまま発効させる。(b) 批准済み既知赤 nodeid の registry を作り、
  失敗集合がその部分集合なら receipt を発行して**赤の nodeid を receipt へ明記**する
  (未知の赤は従来どおり fail-closed、CLI flag は作らない)。(c) [T-908] の land 必須化を
  取り下げ、待ち手 receipt の発行だけを実装して consumer は後続裁定へ送る。
  **親の推奨は (b)** — (a) は既知赤が再発するたびに fleet が止まる構造を残し、
  (c) は「記録不可」が機械で担保されない。(b) は fail-closed を保ったまま、
  批准という人間の判断を機械が読める形に落とす。
  **裁定は 2026-08-13 第 9 束 #1 で「(b) の変形 = checker 統合」に決した** — registry は作らず、
  受理条件を「rc=0 または非帰属 checker 緑」へ拡張する。本 wave で実装・land 済み。
  **実装は完了しているが、本 wave は land できていない。** 2026-08-13 の受入 3 回
  (10:15 / 10:22 / 10:33 JST、tested tip `11032ea5`) がいずれも rc=1 の赤 (すべてフレーク) を
  引き、非帰属 checker が rc=2 (collect 段の 120 秒 timeout) を返して receipt が出なかった。
  **gate は裁定どおり動作しており、止めているのは checker 側の 2 つの欠陥である** —
  [T-1027] (nodeid の exact 一致) と {{T:acceptance-red-check-robustness}} (collect の timeout)。
  **land の再開条件** = 両方が main へ着地したうえで受入を 1 回通すこと。
  branch `worktree-dev-wave-t907-recovery` tip `11032ea5` に全成果が保全されている。
  成果物影響 = 未 land のあいだ [T-907] / [T-908] / [T-910] / [T-1019] / [T-1020] の実装が
  main に入らず、受入 integrity の穴と既知赤による fleet 停止が両方残る。
- {{T:waiter-producer-completion-fail-open}} **P2・新規**: `tools/dev_wave_wait.py producer` が、
  `.done` も成果物も存在せず producer が生存している状態で、出力ゼロ・rc=0 で即座に返る
  ことがある。2026-08-13 に 5 回実測 (02:44 / 03:12 / 03:55 / 03:58 / 04:14 JST)。
  親が 3 点照合 (成果物実在 + `.done` + producer 死) で検知して張り直したため実害は出ていないが、
  待ち手を信じる呼び手は「子が成功した」と誤認する。成果物影響 = 子の成果物なしで次段へ進み、
  context 無しの出力をレビュー結果と数える経路が開く。
  **回収 context でさらに 2 例 (09:12:29 / 09:17:29 JST)。通算 7 例で、うち 1 例は
  投入 31 秒後だった。**
- {{T:acceptance-red-check-robustness}} **P1・新規 (実データで 3 回再現、非帰属経路の実運用を止めている)**:
  **最優先は collect 段の timeout である。** `tools/check_acceptance_reds.py:277` の collect は
  `timeout: float | None = 120.0` を既定に持つが、この collect は `--force-dispatch` で
  計算ノードへ投入されるため queue 待ち + job 起動 + 実行が 120 秒を容易に超える。
  2026-08-13 の受入 3 回 (10:15 / 10:22 / 10:33 JST) すべてで
  `TimeoutExpired ... timed out after 120.0 seconds` により rc=2 となり、
  非帰属判定が得られず receipt が出なかった。単独再走側 (同 `:471`) は `timeout=None` なので、
  **collect 段だけが締まりすぎている**。[T-1027] (nodeid の exact 一致) とは別の欠陥で、
  **両方直らないと非帰属経路は実運用に到達しない**。
  以下は段 6 レビュー B が予告した残り 3 件 (本 wave 不実装)。
  (i) checker 全体に timeout が無く、赤の単独再走が hang すると
  receipt が出ないまま待ち続ける。(ii) checker 実行中に lease の heartbeat が無く、
  赤が複数あると最終確認までに TTL 2,400 秒を使い切りうる (受入全走 18〜21 分 + checker の
  dispatch 複数回)。(iii) checker を専用 process group で起動しないので、中断時に
  probe worktree や登録情報が残りうる。
  **3 件とも倒れる向きは fail-closed** (receipt が出ない) なので受理集合は緩まないが、
  「誰も何もできない状況」を作りうる点で本 wave の主題と同型である。
  timeout 値・heartbeat の主体・TTL 意味論はいずれも裁定が要るので本 wave では実装せず、
  runbook へ既知限界として明記した。(iii) は前 wave が A6 で scope 外に裁定した面と同一。
  成果物影響 = 未実装のままだと、赤が多い wave は正しく非帰属でも受入と checker の時間を
  捨てて land できない。
- {{T:waiter-signal-handler-test-flake}} **P2・新規 (2026-08-13 実測 2 例)**:
  `test_dev_wave_wait.py` の signal handler 復元テストが変異 harness の走行間で揺れる。
  2 巡目では `test_signal_after_core_success_uses_restored_real_handler` が
  **`tools/dev_wave_land.py` だけを変異させた N5 の失敗集合に現れ**、
  3 巡目では `test_public_main_failure_restores_handler_without_release` が N2 の集合から消えた。
  land のみの変異が待ち手の signal テストを落とすことは依存関係上ありえないので、
  変異へは帰属させずフレークとして扱った。F57 族 (受入全走フレーク) と同じ面かは未確認。
  成果物影響 = 変異 matrix の期待完全集合が走行ごとに揺れ、exact 一致契約 (`DW-M08`) が
  フレーク由来の MISMATCH を出して検出力の判定を曇らせる。
- {{T:dev-wave-docs-land-receipt-contract}} **P3・新規**: [T-908] の land 契約
  (必須 2 引数・rc=23・`already-landed` も通さない・逃がし道なし) を `docs/dev-wave/**` へ
  収容できなかった。実測は本文のとおりで、L1 は 229 bytes 超過、L2 の `DW-O25` は exact pin +
  単節上限、新規 L2 節は command の余白 0 で参照を足せない。予算は上げない方針なので、
  収容先の設計 (どの節を縮約するか / L2 の節分割をどう変えるか) を別途裁定する。
  成果物影響 = 未収容のままだと、runbook を読まない land 呼び手が rc=2 の理由を辿れない。
- {{T:mutation-fake-event-overdetermination}} **P3・新規**: `test_dev_wave_wait.py` の
  fake effects は期待 event 列を固定するため、共有定数や共通呼び出しを変異させると
  失敗集合が 100 件級に膨張し、変異の帰属が単一理由にならない (本 wave の M02 / M03 / M05 で
  112 / 28 / 97 件を実測)。実 Git を使う negative test へ再照準する形が要る。
  成果物影響 = 変異 matrix が KILLED を報告しても、その gate の実効検出力を証明できない。
