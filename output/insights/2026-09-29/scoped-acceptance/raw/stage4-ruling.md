# 段 4 裁定 — scoped-acceptance (plan v2)

読了: DW-S04、DW-G01〜G05、DW-M01 (段 4 直前に再読)。裁定 inbox 再走査: 2026-09-29-interactive-evolution-verdicts.md
(対話型 dev-wave の主経路化と speedup wave 群) は本 wave と矛盾しない。speedup md_2/md_5 は acceptance_shards.py・check_docs.py を
編集し、本 wave は両 file を編集しない (committed 他 branch・他 worktree の未 commit との重なり 0 件、23 時台に実測)。

## 新事実 (brief の前提を一部覆す)

- (F-a) login admission は同じ user の他 session で天井 15.0 GB を超えており (使用 17.0 GB)、148 node の走は gen_S へ dispatch した。
  縮小受入も平常時は計算ノードへ回る。**queue 待ちは消えない。** 効果は「走る量 (pytest 139 秒 vs 全受入)」「無関係な赤に当たる面」
  「再投入回数」から出る。md_1 の効果見込み「混雑に左右される全テスト待ちから外れる」は部分的にしか成り立たない。報告と insight に明記する。
  brief (P5) login 完結は refuted (目標から外す)。
- (F-b) 直近 80 land のうち知識面だけは 31 (39%)。内訳: spool/insight の新規追加だけ 11、insight の既存変更を含む 11、
  他の docs (phase3.md・paper-story・runbook 等) を含む 8、dev-wave 手順書 1。新規追加だけに絞る案 (s3c 代案) は 11/80 に縮む。

## 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| s2/s3c: 完了判定 (c) の pin 節改変は除外設計と矛盾 | real | 採用: (c) は許可 path に実際の検査違反を置き、分類通過後に選択 test か直接 gate が赤になることを実測 (壊れた spool frontmatter、LIVING_DOCS 内の許可 doc の壊れた参照は実測で確かめて選ぶ) |
| s3a/s3b: insights・docs の広い許可は reader 経由の門入力・見逃しを含む (B5 event、paper_story_a1_*、s1_known_axes_freeze、事前登録 6 件) | real | 採用: 下の「接頭辞・basename・dir 名の文字列一致」規則。production 一致は全受入、test 一致は選択 |
| s2 (P2) AST 全走査 / s3c: 重い・不完全 | real (過剰) | AST は不採用。`git grep -F` 相当の文字列一致を分類・選択の双方で毎回実行 (秒単位) |
| s3c 代案: 新規追加だけに絞る | 部分採用 | spool fragment は新規追加だけ。insight・docs は既存変更も許すが、文字列一致で参照される path は全受入 |
| s3b #1: 受領証の digest は実行の証明でない | real だが v5 と同じ信頼境界 | scope 外。分類と選択は land が再導出し受領証を信用しない。rc・log は v5 と同じ扱い。限界として insight に書く |
| s3b #2: 選択器の依存物 | refuted (条件付き) | 縮小受入の tip は分類上 tools/・orchestrator/ を変えないので tip の実行面 = tested main。選択器は stdlib のみで repo 内 import をしない (実装条件) |
| s3b #5: land の分岐は 7 箇所 (release 含む) | real | 採用: schema dispatch を単一入口に集約、全入口に正負例 |
| s3b #6 / s3c #5: forward-main 条件 | real | 採用 (D987 の拡張): 取り込んだ main と tested main で runner・分類選択器・縮小 launcher・直接 gate 2 本・conftest.py の blob が 1 つでも違えば再受入。test file の追加・変更だけでは再受入しない (D662 と同じ割り切り、限界に書く) |
| s3b #7: 本 wave 自身を全受入にする保証 | real | 採用: tools/ 等を含む tip の縮小受領証を land が拒否する負例を分類器と独立に置く |
| s3c #4: provenance 直接実行は land の DW-O25 関門と重複 | real | 採用: 直接 gate は check_docs と spool_fold --dry-run の 2 本。test_check_ai_provenance.py は固定集合に残す |
| s3c #6: DW-S04 文案が免除の否定になっていない | real | 採用: 対象ごとに分けた否定形 (下) |
| s3a: 直接 gate は growth hold の検出力を同値には補わない | real | 採用: insight に対象と欠落を明記、「全受入と同じ検出力」と書かない |
| s3a: fold 後の canonical の赤は縮小受入時点の検出ではない | real | 採用: land の fold gate に委ねると明記 |
| 親実測の一般化 (148 node/139 秒/天井 1 回) | real | 採用: 効果は同一 tip の同時刻対照で測り、queue・pytest・直接 gate を分ける |

## plan v2 (実装契約)

### 分類 (tools/scoped_acceptance.py、stdlib のみ、repo 内 module を import しない)

- 入力: repo、tested_main、tested_tip。差分は `git diff-tree -r -z --raw --no-renames --no-ext-diff --no-textconv <main> <tip>`。
- 許可 entry は次の全条件: status A または M、新 mode 100644 (M は旧も 100644)、object type blob、size ≤ 2 MiB、
  path は UTF-8・制御文字/`\`/空 component/`.`/`..`/先頭 `-` を含まない。それ以外は全受入 (理由つき)。
- 許可 path (閉じた列挙):
  1. `docs/spool/{worklog,decisions,failures}/*.md` の status A だけ (README.md は除外)。
  2. `output/insights/**` の拡張子 md/txt/csv/tsv/json/jsonl。
  3. `docs/**/*.md`。
- 除外 (許可 path 内でも全受入): `docs/dev-wave/**`、`docs/spool/` の上記以外、`docs/{worklog,decisions,failures}.md`、`docs/archive/**`、
  `docs/handoff/**`、`docs/skill-self-improvement.md`、`docs/ai-provenance.md`、basename に `preregistration`・`erratum`・`freeze` を含むもの。
- production 参照規則: 変更 path ごとに鍵 = {full path、docs/ または output/insights/ で始まる各祖先 dir (末尾 / なし)、basename、
  祖先 dir の名前のうち汎用語 (docs, output, insights, spool, worklog, decisions, failures, archive, README.md) と日付 (YYYY-MM-DD) を除いたもの}。
  tested_tip の tracked file のうち docs/・output/・external/ 配下と `*.md` を除き、test file (orchestrator/tests/ 配下と basename `test_*.py`) も除き、
  さらに直接 gate 2 本 (tools/check_docs.py、tools/spool_fold.py) を除いた file の本文に、いずれかの鍵が**引用符で囲まれた文字列の中の部分文字列**として
  現れたら、その path は正しさの門の入力とみなし全受入。一致の取り方は bytes の部分文字列で良い (過大除外は安全側)。
- 出力: eligible (bool)、理由列、entry 列 (status, mode, blob, path) とその canonical digest、規則版 `scoped-acceptance-rules/v1`。
- D95 実装面の判定は、許可 path が閉じた列挙なので追加の判定器は要らない (許可外は全部全受入)。

### 選択

- S1: `_REAL_REPO_NODE_INVENTORY` の全 node (conftest.py を AST でなく literal 抽出、抽出件数が 0 や重複なら fail-closed)。
- S2 固定 file: test_check_docs.py、spool fold の test file (実名を実装子が特定)、test_check_ai_provenance.py、test_real_repo_serialization.py、
  test_acceptance_schedule_order.py、DW-O26 の inventory 4 群 (test_campaign.py の certified-writer caller inventory node、test_official_perf_closure.py、
  test_p3_exploration_namespace.py、test_p3_b4_wiring_probe.py)。存在しない file は fail-closed。
- S3: test file (orchestrator/tests/**/*.py 等) の本文に、分類と同じ鍵のいずれかが引用符内部分文字列として現れる file 全体。
- S4: insight を 1 つでも変える場合、`"insights"` を文字列 literal として持つ test file 全体。
- 直接 gate: `python3 tools/check_docs.py`、`python3 tools/spool_fold.py --dry-run`。
- 恒久除外・loadgroup・growth hold の扱いは全受入と同じ意味にする (新しい hold・除外は足さない)。
- 出力: node/file 列の canonical 列と digest、直接 gate argv。

### 実行と受領証

- `tools/dev_wave_wait.py acceptance --scoped ...`。v5 経路・`tools/acceptance_launcher.py` は 1 byte も変えない。
- 縮小 launcher は新 file。launcher・分類選択器は tested main の blob を実行 (v5 の tested-main authority と同型)。
- 新 schema `dev-wave-scoped-acceptance-receipt/v1`: v5 の共通 field (wave・holder・tested_main/tip・fingerprint・env・child_rc=0・verdict=child-green・
  scheduler・log digest・waiter/launcher/runner の blob と実行 bytes) + classification 一式 + selection 一式 + 直接 gate 2 本の argv・rc=0・log digest +
  分類選択器と縮小 launcher の blob。赤なら受領証を出さない。
- `tools/dev_wave_land.py`: schema dispatch は単一入口。全入口 (登録前検査・lock 内再検査・fold 後再検査・forward-main 比較・release authority) を通す。
  lock 内で tested_main..tested_tip の分類と選択を land 自身の module で再導出し、受領証と完全一致を要求。land の module blob と受領証の分類選択器 blob の
  一致も要求。不一致・eligible=false・実装面混入は拒否 (rc は既存の acceptance 拒否と同じ系)。v5 の検査は 1 行も緩めない。
- forward-main: 上の表の blob 集合が変われば再受入。

### 規模上限 (DW-S06-B が継承)

- 単位 A (tools/scoped_acceptance.py + orchestrator/tests/test_scoped_acceptance.py): 本体 ≤ 500 行、test ≤ 600 行。
- 単位 B (tools/dev_wave_wait.py・tools/scoped_acceptance_launcher.py (新)・tools/dev_wave_land.py・必要なら tools/run_tests.py、
  orchestrator/tests/test_scoped_acceptance_land.py (新)): 追加 ≤ 1,200 行 (test 込み)。
- 依存順: A → B (B は A の API を import する)。親は docs。

### 手順書 (親)

DW-S04 の該当文を次へ置換 (免除の否定、対象ごと):
「変異 matrix の免除は「実装しない」裁定済みかつ実装差分ゼロの wave だけ。受入全走の免除は、機械分類で知識面の許可差分に閉じ、
縮小受入の受領証が land の lock 内で再検証された wave だけ。それ以外に免除はない。実 repo を読むテストは段 7 の記録前に実走し、結果を worklog へ書く。」
runbook §7.3 に `--scoped` の起動例・適格性・直接 gate・dispatch 前提 (queue は残る)・赤時は受領証なし・forward-main の再受入条件を追記。
L1 予算は改訂後に check_docs で実測。

### 事前登録する変異 (位置は実装後に単一理由性を確認して確定、DW-M01)

| id | 変異 | 殺すはずの test (実装後に nodeid 確定) |
|---|---|---|
| MS1 | 分類: production 参照規則を外す | 門入力の doc が全受入になる test |
| MS2 | 分類: 許可 path 判定で tools/*.py を許す (拡張子検査を外す) | 実装面 1 file 混入の test |
| MS3 | 分類: status D/R/T・mode・symlink の拒否を外す | raw metadata の test |
| MS4 | 選択: S1 (inventory) を外す | 選択集合の test |
| MS5 | 選択: 祖先 dir 接頭辞の鍵を外す | B5 型 (dir 定数連結) の選択 test |
| MS6 | land: lock 内の再導出を外し受領証の分類を信じる | 実装面混入 tip の縮小受領証拒否 test |
| MS7 | land: forward-main の scoped blob 比較を外す | drift test |
| MS8 | launcher: 直接 gate の rc 検査を外す | 直接 gate 非 0 で受領証を出さない test |
| MS9 | land: v5 の exact field 検査に scoped field を許す | v5 と scoped の取り違え test |

正例 (過剰拒否の確認、DW-M01 受理集合縮小側): docs だけの tip の縮小受領証が land を通る test、v5 の既存正例が引き続き通る test。

### 実物確認 (親、段 6〜7)

独立 clone (共有 repo 外、main = 統合 commit) で: (a) 許可 docs/insight/fragment だけの tip を縮小受入 → land 成功、
(b) 同 tip に tools/*.py を 1 file 足した tip の縮小受領証を land が拒否 (分類で全受入判定、または受領証不一致)、
(c) 許可 path の検査違反 (壊れた spool frontmatter 等) で縮小受入が赤・受領証なし。効果: (a) の tip で縮小受入と全受入を同時刻に投入し、
queue・pytest・直接 gate を分けて記録。計算は合計 2 node 時間未満の見込み。

### 追記 (段 5 投入前、親)

- 単位 A と B は 1 つの Codex 実装単位 (worktree `scoped-acc-author`、branch `scoped-acc-author`) にまとめる。理由: B は A の API を import する直列依存で、
  Lustre 上の worktree 作成が 1 本 30 分超 (本 wave で実測 約 35 分)。所有 path は A∪B、規模上限は A・B それぞれの上限を合算して継承する。

## 段 6 裁定 (fix1、2026-09-30 00:1x JST)

レビュー r1・r2 と親の実測 (probe/classify-real.txt: 実在の知識面 land 10 件が 10/10 全受入、probe/classify-refined.txt: 絞った鍵で 5/10 縮小可)。

| 所見 | 判定 | 対応 |
|---|---|---|
| r1#1 引用文字列走査が `'` で対応ずれし参照を見逃す (must-fix) | real | 照合を file 全体の bytes の部分文字列に変える (分類・選択とも)。`"insights"` 規則は `b'"insights"'` または `b"'insights'"` の部分文字列 |
| r2#1 + 親実測: basename README.md・入れ物 dir・汎用 dir 名で過剰除外、実在 land 0/10 (must-fix) | real | 鍵の規則を下の v2.1 に置換 |
| r1#2 MS5 test が単一理由でない | real | MS5 を「dir 鍵の層 (祖先 path 鍵と dir 名鍵) を外す」に再定義し、test は変更 file の path・basename を含まず dir だけを参照する test file を選ぶ例 |
| r1#3 MS6 test が land の tools/ 検査で先に落ちる | real | tools/ 差分のない適格 tip で受領証の分類・選択を偽装し、再導出だけが拒否理由になる test を足す |
| r1#4 MS9 test が authority kind で先に落ちる | real | v5 の正しい値に揃え、余分な scoped field だけで拒否される test にする |
| r1 変異の実効性: T status の独立例なし | real (nit) | type change (blob→symlink) の例を足す |
| r2#2 固定集合が大きい / r2#3 新 test の合成 repo 構築 | 保留 | 親の所要実測で判断 (固定集合は検出力の代替を示さない限り削らない) |

### 鍵の規則 v2.1 (分類・選択で共通)

変更 path p ごとに鍵集合:
- p (full path) は常に鍵。
- basename は、汎用語集合 {README.md, index.md} と日付 (YYYY-MM-DD) でなければ鍵。
- `docs/spool/` 配下: 上の 2 つだけ (入れ物 dir は鍵にしない。入れ物を列挙する reader は fold・check_docs・spool_fold の直接 gate と land の fold gate が担う)。
- `output/insights/<日付>/<slug>/...`: 深さ 4 以上の祖先 path (`output/insights/<日付>/<slug>`、その下の dir) を鍵にし、深さ 4 以上の dir 名のうち汎用語 (GENERIC) と日付でないものを鍵にする。
  `output/insights`・`output/insights/<日付>` は鍵にしない。
- `docs/<x>/...`: 深さ 2 以上の祖先 path (`docs/<x>` 以下) と、その dir 名 (GENERIC 以外) を鍵にする。`docs` は鍵にしない。
- 照合: production candidate・test file の blob 全体の bytes に鍵が部分文字列として現れたら一致 (引用符・コメントを区別しない)。
- 限界 (insight に書く): 入れ物 dir (`docs/spool/*`、`output/insights`、`output/insights/<日付>`、`docs`) を列挙する reader は鍵で拾わない。

### 事前登録 (fix1 の real 所見、DW-M01)

| id | 変異 | 殺すはずの test |
|---|---|---|
| MF1 | 照合を引用文字列内だけに戻す | コメントに `don't` を置いた後の path 参照を見逃さない test (分類・選択) |
| MF2 | basename の汎用語除外を外す | insight の README.md だけの tip が適格になる test |
| MF3 | spool の入れ物 dir を鍵に戻す | `"docs/spool/worklog"` を持つ production file があっても fragment 追加が適格になる test |

## 段 6 裁定 (fix2、2026-09-30 00:4x JST)

焦点再レビュー (codex/s6focus-out.md) の対応表: r1#1・r1#4・T status・焦点走 1 の land 4 件は closed (焦点走 2 = b58ee226a で 5,353 passed / 0 failed で実走確認)。
焦点走 1 の wiring_probe 1 件は親の未 commit docs が原因で d37c18fe3 以後は解消 (焦点走 2 で緑)。r1#2 (MS5) は再定義後の変異で判定する。
r1#3 (MS6 が lock 前後どちらの検証か) は、変異が lock 前・lock 内の双方が呼ぶ `_verify_scoped_acceptance_static` の再導出そのものを外すので単一理由として足りる (refuted)。
r2#2・r2#3 (所要) は親が効果の実測で測る。

新たな所見 (入れ物 dir を列挙する reader を鍵で拾えない) は real。親の実測:
- 入れ物そのものの文字列 (`"output/insights"`、`"insights"`、`"docs/spool"`、`"spool"`) を持つ production file は 7 本 (tools/check_docs.py、tools/spool_fold.py、
  tools/dev_wave_land.py、tools/scoped_acceptance.py、tools/audit_dangling_commits.py、orchestrator/campaign/layout.py、orchestrator/campaign/p3_b4_wiring_probe.py)。
  layout.py の "insights" は campaign root 内の dir、p3_b4_wiring_probe.py は特定の insight dir を部品連結で読む、audit_dangling_commits.py は既定で docs/spool を除外する開発道具。
- **実在の穴:** p3_b4_wiring_probe.py は `output/insights/2026-08-27_t1769-b4-wiring-probe` (深さ 3 の「日付_slug」dir) を部品連結で読むが、v2.1 は insight の鍵を深さ 4 からしか作らないため見逃す。

対応 (fix2):
1. insight の鍵: 深さ 3 以上の祖先 path と dir 名を鍵にする。ただし最後の要素が純粋な日付 (YYYY-MM-DD) の祖先 path とその名、GENERIC の名は鍵にしない。
2. 入れ物 reader の点検済み一覧 (上の 7 本、定数で閉じた列挙)。変更に insight を含むとき、一覧外の production candidate が insight の入れ物文字列
   (引用符 2 種 × `output/insights`・`output/insights/`・`insights`) を部分文字列として持てば `container-reader:<file>` で全受入。spool も同様
   (`docs/spool`・`docs/spool/`・`spool`)。
3. 選択 S5: 変更に spool fragment を含むとき、`docs/spool` を部分文字列として持つ test file を全部選ぶ。

事前登録 (fix2):
| id | 変異 | 殺すはずの test |
|---|---|---|
| MF4 | insight の深さ 3 の鍵を外す (最小深さを 4 に戻す) | `"output" / "insights" / "2026-01-01_slug"` を部品で持つ production file があると、その配下の変更が全受入になる test |
| MF5 | 入れ物 reader の点検済み一覧の検査を外す | 一覧外の production file が `"insights"` を持つと insight 変更が全受入になる test |
| MF6 | 選択 S5 を外す | spool fragment 追加で `docs/spool` を持つ test file が選ばれる test |

## 段 6 裁定 (fix2 後の焦点再レビュー、2026-09-30 00:56 JST)

焦点走 3 (88fa8f1f1): 5,359 passed / 10 skipped / 0 failed (pytest 165.16 s)。焦点再レビュー 2 (codex/s6focus2-out.md): fix2 対応 1 closed、残りは partial。
残る指摘 (下位の入れ物 path `"docs/spool/worklog"`、分割文字列、純粋な日付 dir を列挙する reader) を現行 tree で数えた:
- `tools/dev_waves/git_state.py` の `_pending_fragment_paths` が `docs/spool/{worklog,decisions,failures}` を列挙する。wave の未 fold fragment を数える開発道具で、
  正しさの門ではない。その test (test_dev_waves_git_state.py、test_dev_wave_land.py、test_check_docs.py) は `docs/spool` を含み S5 で選ばれる。
- `orchestrator/campaign/paper_story_a1_paired.py` の `"output/insights/2026-09-13/"` は文字列連結で特定の事前登録 insight を指し、slug が鍵に入るので捕まる。
  純粋な日付 dir を列挙する production reader は現行 tree に無い。
判定: 実害の実例なし (DW-G05)。fix は 3 巡上限のうち 2 巡で閉じ、残りは insight の「限界」に書く (入れ物の下位 path・分割文字列・日付 dir を列挙する reader は
分類で拾わず、test 側は S4/S5 の文字列選択と実 repo 読み一覧に頼る)。MS5・MS6 の partial は、変異が dir 鍵の層全体と lock 前後が共有する再導出関数を外すので登録どおりに判定する。

## 段 6 裁定 (変異 probe 後、fix3、2026-09-30 01:0x JST)

変異 probe (mutation/mutation-probe-results.json、初回と明記した dispatch probe、全件 SURVIVED 期待で観測 node を収集): baseline 64 passed / 6.24 s。
15 変異中 14 が赤 (観測 node を final spec の期待にする)。**MS8 (launcher の直接 gate rc 検査を外す) は生存。** 原因は mask:
`test_gate_failure_leaves_no_receipt` は launcher 全体を合成環境で走らせ、MS8 下でも後段の起動が別理由で失敗して「rc≠0・受領証なし」のまま緑になる。
実効の門は `_gate` の rc 検査そのもの (land の gate_results 検査は launcher が rc=0 を書くと効かない) なので、MS8 を `_gate` 直接呼び出しの単一理由 test へ再照準する (DW-M02)。
fix3 (test 追加のみ): orchestrator/tests/test_scoped_acceptance_land.py に、`tools/scoped_acceptance_launcher.py` の `_gate` を rc=1 の argv で呼ぶと ValueError、
rc=0 なら rc 0 と sha256 の log digest を返す test を足す。既存 test と実装は変えない。
