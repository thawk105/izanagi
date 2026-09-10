## 総括

BLOCKER 1 件, MAJOR 2 件, MINOR 0 件です. 現在の出力値そのものは裁定と整合しますが, false guarantee を許す検査穴が残っています.

事前登録変異は #1 から #6 まで静的には KILLED です. #7 の正例も受理経路は整合します. ただし pytest は環境制約に従い実行しておらず, green の実測ではありません.

## 所見

### BLOCKER 1: 未知 layer の完全性を主張しない検査は exact blacklist にすぎず, 実質的に無力

根拠: [test_hold_inventory.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:150) は 6 個の exact substring だけを禁止しています. 次の完全性主張を実際に同じ blacklist へ通し, match が空であることを確認しました.

```text
This inventory enumerates every hold layer, including layers unknown to the registry.
この出力は未知の層を含む保留層を漏れなく列挙する.
```

probe 結果は両方とも `matched=[]` でした. 現在の disclaimer は正しいものの, その後ろに上記を追加しても test は通ります. これは [s4-ruling.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/s4-ruling.md:54) の保証範囲制限を守れません.

成果物影響: Human と JSON が未知 layer まで網羅すると誤って主張する出力が受理集合へ入り, `completeness=registered-layers-only` と矛盾する保証が利用者へ渡ります.

推奨対応: blacklist を保証手段にしないでください. Human の固定 header と許可された line 構造を独立 expected value で exact 比較し, 未知 layer に関する自由文の追加を失敗させてください. JSON は top-level の `completeness` 以外に完全性を表す prose field を許さない構造検査が必要です.

### MAJOR 1: 出力する env と token が実際の release 条件に結合されていない

根拠: [hold_inventory.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:87) の `release.env`, `release.target`, `release.token` は出力値です. しかし test は release condition だけを hardcode し, [test_hold_inventory.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:84) では外部 allowlist に literal env が存在することだけを検査しています.

例えば `release.token` だけを `"wrong-token"` にする, または `release.env` と `release.target` だけを `"WRONG_ENV"` にする変異は全 test を通ります. [test_hold_inventory.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:130) は実際の status 判定を hardcode token で検査しますが, inventory が表示する token との一致を検査しません.

同じ問題が Pegasus bypass surface の `env`, `effect`, `target` にもあります. Test が固定するのは ID set と `classification` だけです.

成果物影響: 実際の受理集合は `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` のままなのに, inventory が別の env または token を解除口として表示し, 利用者の解除操作が成立しなくなります.

推奨対応: 次を source 定数を参照せず exact literal で固定し, 相互一致も検査してください.

```python
assert release["env"] == "IZANAGI_RUN_GROWTH_HELD_TESTS"
assert release["target"] == release["env"]
assert release["token"] == "explicit-user-command"
assert release["mechanism"] == "environment-exact-token"
assert bypass["env"] == release["env"]
assert release["env"] in TASKS["tests"].env_allowlist
```

Production release の `mechanism` と `target`, Pegasus surface の全 field も同様に exact pin するべきです.

### MAJOR 2: Human renderer は値の所在と順序を検査せず, JSON との乖離を許す

根拠: [hold_inventory.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:124) に対し, [test_hold_inventory.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:87) は大部分を `value in human` で検査します.

具体的には次の変異が生存します.

- `configured_status` と `effective_status` の 2 行を Human から削除する.
- field label を変更または削除し, 値だけを別位置へ置く.
- 全 layer と item の順序を変更する.
- 同じ文字列が別 field に存在することを利用し, 値を誤った layer または field に帰属させる.
- `hold_axis`, `correctness_gate`, `observed_seconds`, `collateral_note` の表示を削る.

JSON の equality は Human renderer を経由しないため, これらを検出しません.

成果物影響: JSON に正しい `effective_status` が残っていても Human では欠落または誤帰属し, 利用者が現在 held か released かを誤読します.

推奨対応: 独立 expected block と Human 全文を exact 比較してください. 可変 item 群についても layer 単位の line sequence を組み立て, label, 値, 帰属, 順序, item 数を比較する必要があります.

## Assert 監査

| Test line | 赤くなる破壊または残存穴 |
|---|---|
| 22 | `layers` を list 以外へ変更 |
| 24 | production または test layer の削除, 追加, ID 変更 |
| 25 | 同じ ID の layer を重複追加 |
| 43 | layer 共通 field の削除 |
| 46 | production inventory の check ID を削除または追加 |
| 47 | production count を source pin と違える |
| 48 | count と出力 check ID 数を違える |
| 49 | sha256 を source pin と違える |
| 50 | sha256 を出力 check ID の実 digest と違える |
| 55 | test `node_ids` を source set と違える |
| 56 | test count を source cardinality と違える |
| 57 | test `holds` の node ID set を違える |
| 61 | schema literal を変更 |
| 62 | completeness literal を変更 |
| 63, 66 | release condition literal を変更 |
| 70 | bypass ID の削除, 追加, 変更 |
| 73 | plain runner surface の任意 field を変更 |
| 81 | Pegasus surface classification を変更 |
| 84 | dispatch allowlist を破壊すると赤いが, inventory の env 変更では赤くならない. MAJOR 1 |
| 92, 123, 152, 156 | 対応 format の `main()` return code を変更 |
| 95 | Human から production check ID を全出現箇所ごと削除 |
| 97 | Human から test node ID を削除 |
| 99-101 | item reason, ruling, release condition を全出現箇所ごと削除 |
| 103, 107, 109, 112, 115 | 対象値を Human 全体から削除すると赤いが, field の誤帰属は通る. MAJOR 2 |
| 116-121 | 固定 bypass 文言または disclaimer を削除 |
| 125 | JSON dispatch, serialization, field projection を expected inventory と違える |
| 126, 127 | bypass ID を raw JSON text から消す encoding 変更 |
| 133-147 | production status, configured status, env 未設定, exact token, invalid token の各分岐を変更 |
| 154, 168 | Human または JSON から `registered-layers-only` を削除 |
| 167 | 禁止した exact phrase を追加すると赤いが, 同義表現は通る. BLOCKER 1 |

## 変異事前登録 7 件

| # | 静的判定 | 赤くなる node |
|---|---|---|
| 1 | KILLED | `test_inventory_projects_exact_registered_source_sets`, helper の layer ID set 比較 |
| 2 | KILLED | `test_inventory_projects_exact_registered_source_sets`, `node_ids` または `holds` の exact source set 比較 |
| 3 | KILLED | `test_effective_status_tracks_exact_test_opt_in`, exact token 設定後の released assertion |
| 4 | KILLED | Inventory からの削除は `test_inventory_projects_exact_registered_source_sets`. Human のみの削除は `test_main_dispatches_human_and_json` |
| 5 | KILLED | `test_main_dispatches_human_and_json`, JSON parse と expected equality |
| 6 | KILLED | `test_inventory_projects_exact_registered_source_sets`. 現状は [freeze_verification_hold.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/campaign/freeze_verification_hold.py:64) の import invariant が先に collection error とし, それを除いても test line 63 が失敗 |
| 7 | 静的に受理経路あり | 4 test node の current literal と分岐は整合. pytest 未実行 |

#2 は inventory projection だけを壊す登録として KILLED です. `GROWTH_TEST_HOLDS` source 自体を変更した場合に inventory が追随するのは snapshot 契約どおりです. Production check ID source は [freeze_verification_hold.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/campaign/freeze_verification_hold.py:39) の count と digest でも固定されています.

## Source 非変更と副作用

- Scoped `git status` では新規 2 ファイルだけが untracked で, production/test source 2 ファイルには staged, unstaged とも diff がありません.
- [hold_inventory.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:13) は `held_marker()` を import せず, 呼び出しもありません.
- Production layer は `sorted(HELD_CHECK_IDS)` と `dict(REASON)` で copy を作ります. Source の frozenset と MappingProxyType を変更しません.
- Test layer が受け取る inventory は [growth_test_holds.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/growth_test_holds.py:215) が毎回作る新規 dict, list, `asdict` row です. Source 台帳 object を変更する path はありません.
- `_test_effective_status()` は env を読むだけです. env の設定, hold 解除, source 編集, 新しい実効 release path は行いません.
- `main()` の副作用は stdout への出力だけです.

pytest は実行していません. 実行したのは read-only の scoped git 確認, Pegasus allowlist の 1 箇所 grep, blacklist 回避文言の軽量 probe だけです.