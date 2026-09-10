## must-fix

1. 焦点走の 3 件は実装誤りではなく、共有 fixture の更新漏れである。ただし現状は land blocker。

   - 根拠: 新しい P7 は checker 実行後に両 revision の `tools/run_tests.py` を `cat-file -t` と `rev-parse` で検査する (`tools/dev_wave_wait.py:2041-2065`)。一方、`_real_red_checker_repo` は checker と `unrelated.txt` しか commit せず、runner を作成していない (`orchestrator/tests/test_dev_wave_wait.py:2955-2996`)。焦点走も 3 件とも最初の runner `cat-file -t` で停止している (`focus1-for-review.log:49-59`, `105-115`, `166-176`)。
   - 判定:
     - `test_red_checker_blob_lookup_uses_hardened_git`: fixture 漏れ。
     - `test_red_checker_bootstrap_ignores_pythonpath_shadow`: fixture 漏れ。
     - `test_red_checker_executes_verified_snapshot_after_path_replacement`: fixture 漏れ。
   - 成果物影響: 受入全走が赤のままなので、certified 選択、レポート、台帳を land できない。
   - 具体的な直し方: `_real_red_checker_repo` の初回 commit に、独立 literal のパス `tools/run_tests.py` と固定内容を追加する。`DW._RUNNER_PATH` を fixture 作成にも流用すると誤った production 定数と共倒れするため避ける。tested main と tip でその blob が同一であることも fixture 内で明示 assert する。既存の PATH shim (`orchestrator/tests/test_dev_wave_wait.py:3205-3224`)、PYTHONPATH shadow (`3137-3152`)、working-tree checker 差替え (`3076-3099`) は変更しない。これなら hardened git、隔離 bootstrap、verified snapshot の各検出力を保ったまま runner gate だけ成立させられる。

2. M4 の waiter outer receipt 側は検出力ゼロであり、前後の層に mask されている。

   - 根拠: disjoint 述語は inner checker consumer (`tools/dev_wave_wait.py:2888-2893`)、outer receipt producer (`tools/dev_wave_wait.py:2647-2662`)、land consumer (`tools/dev_wave_land.py:704-706`) の 3 箇所にある。追加テストは inner を直接叩くもの (`orchestrator/tests/test_dev_wave_wait.py:2595-2608`) と land (`orchestrator/tests/test_dev_wave_land.py:913-922`) だけで、outer の `tools/dev_wave_wait.py:2660` を単独で殺すテストがない。
   - mask: 実 checker receipt に重複 nodeid を入れると inner が先に拒否するため、outer の disjoint を削っても到達しない。land も後段で同じ入力を拒否する。したがって M4 を一変異、一理由として扱えない。
   - 成果物影響: outer 防壁の脱落を見逃し、後に inner 側も drift した場合、同じ node が red と flake の双方に記録された受領証が発行され、台帳の分類と受理集合が不整合になる。
   - 具体的な直し方: `_red_check(red_nodeids=("a",), flake_nodeids=("a",))` を `_acceptance_receipt_bytes` へ直接渡し、outer receipt が拒否される専用テストを追加する。mutation matrix は inner waiter、outer waiter、land の 3 変異に分割し、それぞれ専用 nodeid を登録する。

3. 正例 2 の mixed case は実 producer と実 consumer の相互 pin になっていない。

   - 根拠: waiter の mixed 正例はテスト helper `_queue_checker` が inner receipt を合成している (`orchestrator/tests/test_dev_wave_wait.py:649-732`, `3505-3531`)。land 正例も `_non_attributable_payload` が outer receipt を合成する (`orchestrator/tests/test_dev_wave_land.py:425-454`, `979-999`)。実 producer の単独 flake bytes と単独 red bytesを実 consumer に渡す F366 pin は存在する (`orchestrator/tests/test_check_acceptance_reds.py:612-652`, `669-702`) が、red 1 件と flake 1 件を同時に生成する実 producer case は無い。
   - 成果物影響: 実 producer が mixed 入力時だけ一方の分類を落とす欠陥が入っても、受理済み flake または red が結果 JSONと台帳から消える。
   - 具体的な直し方: `CAR.main` に 2 node の実ログと node ごとの再走結果を与え、実際に書かれた `receipt.read_bytes()` を `json.loads` して `DW._red_check_payload_nodeids` へ渡し、`((red,), (flake,))` を独立 literal で assert する。既存の synthetic waiter/land 正例も残す。

4. 64 KiB 境界テストは fixture を 32 byte 縮めて緑を買っており、旧境界を保存していない。

   - 根拠: 差分は `acceptance_red_nodeids` の長さを 65075 から 65043 へ縮めてから新 field を追加している (`s5.diff:440-446`)。現テストは縮めた入力で 65524 byte を確認するだけである (`orchestrator/tests/test_dev_wave_land.py:6742-6789`)。consumer の上限は 64 KiB 固定 (`tools/wave_land_window.py:34`, `881`)。
   - 成果物影響: 以前は通知へ渡せた長い land 結果が `land-json-rejected` になり、land 済み main の参照通知が欠落する受理集合縮小を見逃す。
   - 具体的な直し方: 旧 65075-byte fixture を復元して赤を再現し、上限値を緩めずに旧入力を収める production 表現を設計する。現 schema で不可能なら、縮小を「保存」と偽らず、受理集合縮小を許すかを裁定へ戻す。fixture の短縮だけで閉じてはならない。

## 変異別の検出力表

| 対象 | 殺すテスト、または判定 |
|---|---|
| M1 | `orchestrator/tests/test_dev_wave_wait.py:2520-2527,2566,2575-2581` |
| M2 | `orchestrator/tests/test_dev_wave_wait.py:2528-2534,2567,2575-2581` |
| M3 | `orchestrator/tests/test_dev_wave_wait.py:2543-2546,2569,2575-2581` |
| M4 | inner waiter: `orchestrator/tests/test_dev_wave_wait.py:2595-2608`; outer waiter: **無し**; land: `orchestrator/tests/test_dev_wave_land.py:856,913-922` |
| M5 | waiter: `orchestrator/tests/test_dev_wave_wait.py:3479-3502`; land: `orchestrator/tests/test_dev_wave_land.py:952-976` |
| M6 | `orchestrator/tests/test_dev_wave_wait.py:2760-2773` |
| M7 | `orchestrator/tests/test_dev_wave_land.py:1041-1059` |
| M8 | waiter: `orchestrator/tests/test_dev_wave_wait.py:2776-2795`; land: `orchestrator/tests/test_dev_wave_land.py:1062-1086` |
| M9 | v3: `orchestrator/tests/test_dev_wave_land.py:758,773,823-827`; field 欠落: `757,811-812,823-827` |
| M10 | flake-only: `orchestrator/tests/test_dev_wave_land.py:952-976`; mixed: `979-999` |
| 正例 1 | 実 blob 差を持つ land 正例: `orchestrator/tests/test_dev_wave_land.py:1002-1018`; waiter serializer 正例: `orchestrator/tests/test_dev_wave_wait.py:3863-3884` |
| 正例 2 | synthetic waiter: `orchestrator/tests/test_dev_wave_wait.py:3505-3531`; synthetic land: `orchestrator/tests/test_dev_wave_land.py:979-999`; 実 producer mixed 相互 pin: **無し** |

M1〜M3、M5〜M10 は対象変異を入れれば、静的には記載テストが受理または拒否の反転を検査する。診断文字列だけを見ているものではない。M4 だけは登録位置が複数層なのに outer waiter の単独 kill がない。

## nit

1. F366 の単独 branch pin は正しい。実 producer `CAR.main` の書込 bytesを `read_bytes` し、`json.loads(raw)` を実 consumer `DW._red_check_payload_nodeids` に渡している (`orchestrator/tests/test_check_acceptance_reds.py:568-594`, `628-652`, `681-702`)。期待 node shape も独立 literal であり、producer helperとの共倒れではない。

2. 偽緑監査:
   - M1〜M10 のテストに production 受理述語を monkeypatch して通すものは見当たらない。
   - F366 の `node_runner` は外部実行 seam であり、consumer 述語の迂回ではない (`orchestrator/tests/test_check_acceptance_reds.py:608-622`, `665-679`)。
   - 診断のみの pin もない。waiter は例外発生、land は `RC_AUDIT` と main 不変、正例は実際の受理と集合伝搬を検査する。
   - ただし 64 KiB テストは `_patched_land_attr` で land 自体を置換している (`orchestrator/tests/test_dev_wave_land.py:6791-6796`)。対象が出力境界なので置換自体は妥当だが、入力短縮は妥当でない。

3. grep による既存 pin 棚卸し:
   - outer receipt exact field pin: production 1 箇所 (`tools/dev_wave_land.py:74-97,581`)、テスト 1 箇所 (`orchestrator/tests/test_dev_wave_wait.py:1807-1815`)。両方更新済み、取り残し 0。
   - active schema literal: v4 は production 2 箇所、正例 test 3 箇所。v3 の実行可能コード内 1 件は意図した拒否ケース (`orchestrator/tests/test_dev_wave_land.py:773`) で、取り残し 0。
   - `LandResult` exact equality は 2 箇所で、双方 `acceptance_flake_nodeids=()` 済み (`orchestrator/tests/test_dev_wave_land.py:3938-3960`)。取り残し 0。
   - JSON byte 境界 pin は 1 箇所で、更新はされているが must-fix 4 のとおり検出力が後退。
   - 共有 fixture は `_Repo`、`_non_attributable_payload`、`_queue_checker`、`_checker_execution_events`、`_red_check`、`_real_red_checker_repo` の 6 箇所を確認し、取り残しは `_real_red_checker_repo` の 1 箇所。
   - canonical docs には v3 literal が 1 件残る (`docs/decisions.md:16631`)。裁定 R-5 が更新を要求している (`s4-adjudication.md:45-47`) が、これは親の段 7 docs 作業として land 前に閉じる必要がある。

4. 成長比例コストは見当たらない。追加ケースは固定 node 数、固定 commit 数、固定 file 数の一時 repoであり、履歴、台帳、実 repo file 数に比例する新走査を追加していない。F366 の 3 相互 pin も各 1 receipt の固定コストである。

5. 受入全走への静的波及:
   - 共有 `_real_red_checker_repo` の呼出しは 4 件 (`orchestrator/tests/test_dev_wave_wait.py:3080,3106,3141,3209`)。このうち full verifier を通る 3 件が今回の赤で、bootstrap exit-code 単体は runner gate へ進まない。
   - `_queue_checker` の既存全 call site は新しい runner lookup の期待列を共有する (`orchestrator/tests/test_dev_wave_wait.py:649-732`)。negative fixture の一部は `runner_gate=False` で前段拒否を保っている。
   - `test_check_acceptance_reds.py` は新たに `dev_wave_wait.py` を import するため、waiter の import-time 回帰が checker test 全体へ波及する (`orchestrator/tests/test_check_acceptance_reds.py:17-29`)。
   - conftest、pytest plugin、新規 test file、改名は差分にない。5 file 外で変更モジュールを実行 import するテストも grep 上はなく、`test_check_docs.py` 等の参照は文書文字列の meta-testに限られる。
   - land の plain runner は `test_` callable と `_plain_cases` を列挙する (`orchestrator/tests/test_dev_wave_land.py:6837-6855`)。追加 parametrized case は `_plain_cases` に反映済み (`830-832`, `925-927`)。

## 総括

land 前の must-fix は 4 件である。  
焦点走の 3 赤は production 欠陥ではなく、runner blob を欠く共有 fixture の更新漏れである。  
M4 outer waiter は単独検出力が無く、正例 2 も実 producer の mixed bytes pin が欠ける。  
F366 の単独 red、flake、attributable 相互 pin 自体は実 bytes と実 consumer を接続している。  
64 KiB 境界は fixture 短縮による偽緑で、旧受理集合を保存していない。  
pytest と変異は実走しておらず、緑は主張しない。