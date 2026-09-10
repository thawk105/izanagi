## 対応表

| 所見 ID | 判定 | 根拠 file:line | 残余 |
|---|---|---|---|
| A-1 / F-1 | closed | fixture は独立 literal の `tools/run_tests.py` を初回 commit に追加し、main/tip の blob 等値も検査する (`orchestrator/tests/test_dev_wave_wait.py:2955-3012`)。snapshot 差替え、PYTHONPATH shadow、hardened git の本来の検査は維持されている (`orchestrator/tests/test_dev_wave_wait.py:3092-3115`, `:3153-3168`, `:3221-3240`) | なし |
| A-2 / F-2 | closed | `ls-tree -z` の rc 非 0 は retryable、空出力は path 不在、構造不一致は恒久拒否として分離 (`tools/dev_wave_land.py:619-646`)。path 不在と Git 障害の release 契約も固定済み (`orchestrator/tests/test_dev_wave_land.py:1041-1098`) | なし |
| B-1 / F-1 | closed | A-1 と同一の共有 fixture 漏れ。runner の作成・commit・blob 等値検査が揃う (`orchestrator/tests/test_dev_wave_wait.py:2967-3011`) | なし |
| B-2 / F-3 | closed | outer producer 自身が sorted、unique、disjoint を検査する (`tools/dev_wave_wait.py:2644-2663`)。inner を経由せず重複集合を直接渡す専用 kill がある (`orchestrator/tests/test_dev_wave_wait.py:3879-3898`) | なし |
| B-3 / F-4 | closed | `CAR.main` が mixed receipt を実際に生成し、その `read_bytes()` を `json.loads` 後に実 consumer へ渡す (`orchestrator/tests/test_check_acceptance_reds.py:705-750`)。期待集合は変数再利用ではない独立 literal (`:751-754`) | なし |
| B-4 / F-5 | closed | 旧 65075 byte と新境界 65054 byteを別 literal で固定 (`orchestrator/tests/test_dev_wave_land.py:6809-6827`)。追加 field 30 byte、縮小 21 byte、旧入力 65556 byte超過、新入力と改行が 65536 byte丁度であることを主張する (`:6852-6859`) | 受理幅の 21 byte縮小は隠されず、明示された契約として残る |

## 新規所見

新しい must-fix、nit ともに見つからない。

`_runner_tree_entry` の分類は次のとおりで、いずれも fail-closed である。

- Git process・I/O 障害: `_git` が非 0 rcへ正規化し (`tools/dev_wave_land.py:388-403`)、retryable 拒否になる (`:632-633`)。
- path 不在: rc=0、空出力を `None` とし (`:634-635`)、呼出側が非 retryable で拒否する (`:754-756`, `:778-780`)。
- parse 失敗: exact binary formatに一致しなければ非 retryable 拒否 (`:636-646`)。
- 型違い: entry は構造化解析され、`non-attributable-only` では `blob` 以外を非 retryable で拒否する (`:786-805`)。
- 最終的な lease 向きは、恒久拒否なら解放可能、retryable なら保持となる (`tools/dev_wave_land.py:3401-3413`, `:3469-3472`)。

fixture への runner 追加は攻撃入力や判定 assert を変更していない。working-tree checker 差替えは blob SHAと分類を検査し (`orchestrator/tests/test_dev_wave_wait.py:3092-3115`)、PYTHONPATH shadow は実 consumer 完走を検査し (`:3153-3168`)、PATH shim は marker 不在まで検査する (`:3221-3240`)。検出力低下はない。

変更 5 file は AST 解析可能で、`git diff --check` も異常なし。skip、xfail、既存期待値の緩和は差分にない。既知の環境赤 `test_exploration_external_root_keeps_wave_clean` は `orchestrator/tests/test_dev_wave_land.py:6146` にあり、今回の変更箇所とは交差しない。成果物影響: 既知の 1 件以外に、受領証発行、land、lease 解放を新たに赤へする静的経路は見つからない。pytest は実走しておらず、緑は主張しない。

## 署名の再確認

1. runner blob 不一致禁止  
   待ち手は両 revision の SHA を比較して拒否する (`tools/dev_wave_wait.py:2041-2065`)。land は request の `tested_main` / `tested_tip` entry を比較する (`tools/dev_wave_land.py:778-802`)。

2. runner が blob 以外なら禁止  
   待ち手は `cat-file -t` の exact `blob` を要求する (`tools/dev_wave_wait.py:1962-1977`)。land も main/tip 双方を検査する (`tools/dev_wave_land.py:798-801`)。

3. checker node shape と rc pin  
   non-attributable は exact 3 fieldかつ `rerun_rc == 1`、flake は exact 5 fieldかつ 3 rcすべて 0 (`tools/dev_wave_wait.py:2851-2887`)。

4. sorted、unique、disjoint  
   inner consumer (`tools/dev_wave_wait.py:2888-2893`)、outer producer (`:2656-2662`)、land consumer (`tools/dev_wave_land.py:734-736`) の三層で成立する。

5. `non-attributable-only` の和集合非空  
   待ち手は両集合の和を要求し (`tools/dev_wave_wait.py:2644-2649`)、land も同じ条件を要求する (`tools/dev_wave_land.py:714-728`)。

6. `child-green` の両集合空  
   待ち手は `red_check is None` を要求して空集合を出力する (`tools/dev_wave_wait.py:2630-2643`, `:2718-2721`)。land は両集合の空を要求する (`tools/dev_wave_land.py:701-713`)。

7. v4 schema と exact field  
   waiter schema は v4 (`tools/dev_wave_wait.py:231`, `:2695-2722`)。land は exact field 集合と v4 値を検査する (`tools/dev_wave_land.py:70-97`, `:573-583`, `:674-700`)。

正例 1は、main/tip の runner blob が実際に異なる child-green を land できる検査で維持される (`orchestrator/tests/test_dev_wave_land.py:1002-1018`)。

正例 2は、waiter が red と flake を別集合で発行し (`orchestrator/tests/test_dev_wave_wait.py:3521-3546`)、land が別々に伝搬する (`orchestrator/tests/test_dev_wave_land.py:979-999`)。さらに実 producer bytesとの相互 pinも成立する (`orchestrator/tests/test_check_acceptance_reds.py:705-754`)。

## 総括

A の 2 件、B の 4 件はすべて `closed`。  
runner lookup の恒久拒否と retryable の向きは正しく分離されている。  
fixture 追加による hardened git、PYTHONPATH shadow、snapshot 差替えの検出力低下はない。  
64 KiB の 21 byte縮小と旧最大入力の超過は独立 literalで明示されている。  
親実測の既知環境赤 1 件以外に、新しい静的な赤経路は見つからない。