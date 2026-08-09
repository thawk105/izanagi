静的読解のみで、pytest・checker・mutation は実行していない。結論は **NO-GO**。blocker は 3 件ある。

## M1〜M9 matrix は 7 kill / 2 未 kill

深刻度: must-fix

根拠: `s4-adjudication.md:128-146`、`orchestrator/tests/test_dev_wave_land.py:1242-1455,2304-2345`

| 変異 | 実際に赤になる nodeid / assert | 判定 |
|---|---|---|
| M1 receipt 呼出し削除 | `orchestrator/tests/test_dev_wave_land.py::test_provenance_gate_rejects_tip_nonzero_before_ff` — `test_dev_wave_land.py:1264` | kill |
| M2 rc=1 許可 | `...::test_provenance_receipt_rejects_each_bound_field` — `test_dev_wave_land.py:1325` | kill |
| M3 main checker 実行 | `...::test_provenance_gate_rejects_tip_nonzero_before_ff` — `test_dev_wave_land.py:1264` | kill |
| M4 tip 照合削除 | `...::test_provenance_receipt_rejects_tip_that_moves_during_audit` — `test_dev_wave_land.py:1351` | kill |
| M5 blob 照合削除 | 表面的には `...::test_provenance_receipt_rejects_each_bound_field` — `test_dev_wave_land.py:1325` | **有効な kill ではない** |
| M6 timeout 削除 | `...::test_provenance_subprocess_contract_and_exception_mapping` — `test_dev_wave_land.py:1375`（さらに `:1387`） | kill |
| M7 shell/string command | 同 nodeid — `test_dev_wave_land.py:1374`（さらに `:1385`） | kill |
| M8 recovery 条件反転 | 示せない | **kill されない** |
| M9 lock 内へ移動 | `...::test_provenance_audit_runs_before_global_lock` — `test_dev_wave_land.py:1287` または `:1288` | kill |

M5 の test は `checker_blob_sha="000..."` という `_audit_provenance_history()` が生成し得ない receipt を直接注入している。実 receipt は `receipt.tip_sha` と同じ commit から blob を取得し、lock 内でも tip 一致を先に要求するため、tip が同じなら blob も必然的に同じである。M5 は production の受理集合を変えない冗長比較であり、`DW-M03` の kill ではない。

M8 はさらに悪い。事前登録の「`active_plan is None` のときだけ関門」は、現実装 `tools/dev_wave_land.py:1930-1935` そのものである。逐語的に変異を当てても diff が生じない。意図が `is not None` への反転なら `test_dev_wave_land.py:1264` と `:2342` が赤になるが、事前登録どおりの M8 は equivalent である。

成果物影響: M5/M8 を「kill」と記録すると、変異台帳が実在しない検出力を証明し、provenance 赤 commit や赤 receipt の受理集合を安全と誤認する。

修正案: M5 は「開いた実行 bytes の blob hash 照合」へ再照準する。M8 は正確な old/new 条件を再登録し、段 4 erratum 後に matrix を再実行する。

## 実行した checker と receipt の blob は束縛されていない

深刻度: blocker

根拠:

- receipt の blob は HEAD tree から取得する: `tools/dev_wave_land.py:1264-1266`
- 実行するのは working-tree pathname: `tools/dev_wave_land.py:1270-1281`
- audit 後の検査は inode だけで bytes を見ない: `tools/dev_wave_land.py:167-193`
- wave clean 検査はさらに後: `tools/dev_wave_land.py:1903`
- checker 自身は live `HEAD` を後から解決する: `tools/check_ai_provenance.py:850-856`

dirty checker が残存すれば `_verify_wave_clean()` が捕まえる。しかし dirty checker が自分自身を同一 inode のまま HEAD bytes へ書き戻して rc=0 を返せば、

1. 実行された bytes は HEAD blob と異なる。
2. inode 検査は通る。
3. 後続 clean 検査も通る。
4. receipt には最初から HEAD blob が記録される。

同様に、監査中だけ HEAD を別 commit へ動かして元へ戻せば、checker は別履歴を監査しても receipt は元の tip を名乗れる。現テストは A→T の移動を残したままにする形しか扱わず、A→B→A を検出しない。

また receipt は checker 本体しか束縛せず、working tree から import する `site_policy` 等の依存閉包も束縛しない。

成果物影響: provenance 違反を含む commit が rc=0 receipt を得て main に入り、その commit を参照するレポート・canonical 台帳・certified 証拠参照が正当化されたように見える。

修正案: 開いた FD の bytes を commit blob と監査前に照合し、その不変 bytes から実行する。checker へ expected tip を渡し、実行開始・終了および計算ノード側で同じ SHA を照合して、結果にも audited SHA を返させる。import 閉包も immutable checkout に固定する。

## active recovery は赤のまま新しい fold commit を admit する

深刻度: blocker

根拠:

- active plan は main の Git admin state からロードされる: `tools/dev_wave_land.py:1881-1888`、`tools/spool_fold.py:2008-2015`
- schema は payload hash を見るが provenance receipt や tested tip には束縛しない: `tools/spool_fold.py:1928-1993`
- `active_plan is not None` なら receipt 検査を飛ばす: `tools/dev_wave_land.py:1930-1935`
- main==tip を確認した後 `_fold_main_locked()` へ進む: `tools/dev_wave_land.py:1936-1984`
- 同関数は実際に `git commit` する: `tools/dev_wave_land.py:1672-1682`
- 新設テスト自身が `main_after != tip`、すなわち新 commit を証明する: `orchestrator/tests/test_dev_wave_land.py:2342-2344`

incoming wave tip の FF は行わないが、「新規 commit を一つも admit しない」という段 4・実装報告の署名は偽である。赤い full-history audit を無視したまま、canonical 台帳を変更する fold commit を作成して `landed` を返す。

成果物影響: provenance 赤の履歴上に worklog・decisions・failures・FOLDED receipt を変更する新 commit が作られ、台帳値と参照 SHA が増える。

修正案: initial FF 前の成功 receipt を durable transaction state に束縛し、recovery はその receipt を再検証してからだけ fold commit を許可する。receipt のない旧 state は自動 commit せず、rollback または人間裁定へ止める。

## checker の副作用で従来の拒否入力を受理できる

深刻度: blocker

根拠:

- checker 実行は全 main clean/collision gate より前: `tools/dev_wave_land.py:1863-1865`
- main clean は後: `tools/dev_wave_land.py:1898-1903`
- ignored target collision はさらに後: `tools/dev_wave_land.py:2094-2099`
- ignored path の拒否実装: `tools/dev_wave_land.py:845-865,898-929`

tip checker が main の ignored collision file を削除して rc=0 を返せば、旧実装なら `RC_DIRT` だった初期状態が新実装では `landed` になり得る。「tip helper 自体も同じことができる」は trust boundary の説明であって、この固定差分が land の受理集合を広げない証明にはならない。

成果物影響: ignored な生証拠・レポート材料が消えた後に同 path の incoming 内容が land し、台帳参照先と初期成果物が置換される。

修正案: checker を main/wave に書けない隔離環境で実行する。少なくとも audit 前後の main/wave fingerprint と collision 集合を比較し、変化があれば rc=29 で停止する。

## `already-landed` と recovery の既存意味は保存されていない

深刻度: must-fix

根拠:

- receipt 検査は通常の `locked_main == tested_tip` 分岐より前: `tools/dev_wave_land.py:1930-1935,2041-2066`
- bit-for-bit test は checker rc=0 の場合しか試さない: `orchestrator/tests/test_dev_wave_land.py:1784-1815`
- audit の bind/timeout 例外は active plan を読む前に即 reject: `tools/dev_wave_land.py:1260-1301,1863-1883`

active plan のない既着地 tip で checker が非0なら、従来の `RC_OK/already-landed` ではなく `RC_PROVENANCE/rejected` になる。また active recovery も、rc 非0は通る一方、checker 欠落・timeout・起動例外では `active_plan` を確認する前に止まり、部分台帳が固着する。

成果物影響: 同じ main SHA に対する status が `already-landed` から `rejected` へ変わり、supervisor の終端判定と fold・台帳回復可否が変わる。

修正案: ordinary already-landed と active recovery の意味を別々に裁定し、赤・checker欠落・timeout の各入力を追加する。既存 idempotency を守るなら、audit failure を一旦構造化して lock 内判定まで保持し、新規 FF の場合だけ rc=29 にする。

## fixture は大部分のテストを恒真化している

深刻度: must-fix

根拠: `orchestrator/tests/test_dev_wave_land.py:119-137,1242-1455`

共有 fixture の checker は常時 rc=0 なので、既存テストは関門呼出しの有無を観測しない。新設テストでも次は land wiring を削除しても緑のままである。

- `test_provenance_gate_accepts_tip_zero_and_lands`
- `test_provenance_receipt_rejects_each_bound_field`（内部 helper の直接テスト）
- `test_provenance_subprocess_contract_and_exception_mapping`（同上）
- `test_active_transaction_recovery_completes_with_provenance_red`

関門を通る／通らない差を実際に観測するのは、主に非0負例 `:1264`、lock marker `:1288`、tip move `:1351`、missing/symlink `:1451-1454` である。matrix 全体として M1 は検出するが、個々の正例・helper test を「発火証拠」と数えてはいけない。

成果物影響: helper 単体の assert を land 関門の発火証明と誤記すると、変異台帳と受入報告が実際より強い保証を主張する。

修正案: test ごとに「wiring」「helper semantics」「正例」の役割を明記し、M5 は到達可能な race fixture、M8 は正確な条件変異へ置換する。

## 例外・FD cleanup は完全ではない

深刻度: must-fix

根拠:

- `_bind_provenance_checker()` は `BaseException` を cleanup 後そのまま再送出: `tools/dev_wave_land.py:1253-1257`
- audit/receipt は `Exception` と `KeyboardInterrupt` しか変換しない: `tools/dev_wave_land.py:1290-1301,1328-1339`
- `land()` 最上位は `_Reject` のみ捕捉: `tools/dev_wave_land.py:2156-2167`
- `close()` は非 idempotent かつ最初の close 失敗時に次の FD を閉じない: `tools/dev_wave_land.py:195-197`

通常経路では close は一度だけで、明白な二重 close はない。しかし `SystemExit` / `GeneratorExit` は `_Reject` へ畳まれず最上位へ漏れる。さらに最初の `os.close()` が失敗すると `tools_fd` cleanup を飛ばす。

成果物影響: CLI が JSON rejection を出さず異常終了し、land status が台帳・supervisor上で不明になる。長寿命 caller では FD 枯渇により後続 land も停止し得る。

修正案: binding を idempotent な context manager にし、各 FD を独立した `try/finally` で閉じて `-1` へ更新する。監査境界では捕捉可能な全 `BaseException` を rc=29 へ構造化する。

## receipt が束縛する tree の範囲

深刻度: must-fix

`_head()` は commit object ID を返すため、同じ SHA が同じ superproject treeを表す点自体は成立する。ただし「checker がその SHA を監査した」という前提が上記 live-HEAD 問題で成立しない。

また、

- 非 ignored untracked と submodule dirt は後続 clean gateで拒否される。
- ignored file は clean gateに入らず、commit treeにも land対象にも入らないが、checker実行には影響できる。
- gitlink OID は superproject treeに含まれる。
- submodule内部の commit履歴・working-tree bytesは provenance audit対象外で、land後の別 postcondition/synchronization対象である。

成果物影響: receipt を「実行環境・submodule内容まで同一」と解釈すると、レポートやcertified参照が実際には束縛されていない内容へ拡張される。

修正案: receipt の保証文を superproject commit tree に限定し、実行環境fingerprint・expected HEAD・submodule同期証拠は別fieldとして明示的に束縛する。

## 総括

(a) **blocker あり、3件**。

1. 実行したworking-tree checker／live HEADとreceiptが食い違っても通る。
2. active recoveryが赤receiptを無視して新しいfold commitをadmitする。
3. checker副作用により旧実装が拒否した初期状態を受理できる。

(b) M1〜M9のうち、dev-waveのkill意味論で **killされない変異は M5、M8**。M5は到達不能receiptによる見かけの赤、M8は現実装と同文のequivalent変異である。

(c) 親が裁定すべき択一:

- **A（推奨）:** NO-GO。段4へ差し戻し、実行bytes＋audited SHAの束縛、recovery receipt、M5/M8再登録、already-landed契約を修正してから再レビューする。
- **B:** このままlandし、保証を「協調環境でのbest-effortな非0読み違い防止」に縮小する。ただし「監査したtreeとlandするtreeは同一」「M1〜M9 kill」「active recoveryは新commitをadmitしない」は撤回が必要。