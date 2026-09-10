## 変更面

| file:line | 現行の形 | 変更後の形 | 理由 |
|---|---|---|---|
| [growth_test_holds.py:570-617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:570) | `PlainRunner` だけを閉じた literal として検証し、import 拒否は暗黙の固定動作 | `GuardMode = Literal["import-and-call", "call-only"]`、`_GUARD_MODES`、kw-only の `guard_mode: GuardMode = "import-and-call"` を追加。`plain_runner` 検査の直後に mode を exact 検証 | runner の種類と保留防壁の強さを直交させる。既存呼出は既定値により同じ分岐を通る |
| [growth_test_holds.py:640-655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:640) | 全 held 関数を wrap した後、pytest session・exact token・pytest 委譲でなければ import 拒否 | wrap 完了後、既存 import 判定の直前で `guard_mode == "call-only"` なら `function_names` を返す | return を wrap より前へ置くと held 呼出まで通るため、この順序を固定する |
| [test_growth_test_holds_contract.py:447-589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:447) | outer AST だけを見て、kwarg が `plain_runner` 1 個であることを要求 | 同じ parse tree から canonical self-load を判定し、非 self-load は現行 1 kwarg、self-load は順序も含め `plain_runner`, `guard_mode="call-only"` の exact 2 kwarg を要求 | 単純な `len(keywords) in (1, 2)` では未知 kwarg、重複、不要な緩和を受理する |
| [test_growth_test_holds_contract.py:622-680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:622) | 登録済み 13 held file の binding と runner を exact 検査 | 既存 loop に self-load と mode の整合を統合し、F351 型 f-string、foreign path、alias、未知 kwargの定数サイズ controls を追加 | 全 test file を新規走査せず、既存の held-file parse 面で選別条件を機械化する |
| [test_growth_test_holds_contract.py:592-620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:592)、[702-797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:702) | subprocess seam は opt-in 実行だけを実証 | signature/default/unknown literal を pin し、tmp synthetic held module を subprocess で importして、`IMPORT_OK` 後の held 呼出だけが拒否される正例を追加 | 実 registry を変えずに import 成功と body 未到達を別々に観測できる |
| `docs/spool/decisions/2026-08-17-dev-wave-t1226-hold-guard-callonly-1.md:1` | D360 は import 時と call 時の二層拒否を一律要求 | D360 の狭い例外、self-load 選別規則、default は二層、未知形は fail-closed、全 test scan 禁止を記録 | ユーザー裁定を canonical 台帳へ fold 可能な形で残す。形式は [decisions README:5-34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/docs/spool/decisions/README.md:5) |
| [test_s8b_floor_campaign.py:7896-7912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_s8b_floor_campaign.py:7896)、[test_check_docs.py:1934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_check_docs.py:1934) | 前者は nested f-string self-load、後者の 3 箇所は foreign file load | いずれも編集しない。前者を synthetic control の原型、後者を実 held negative control とする | registry の `count` と `key_sha256` を変えず、source SHA pin も動かさない |
| [hold_inventory.py:80-107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/tools/hold_inventory.py:80) | registry の node、件数、digest を射影 | 変更なし | mode は module binding の契約であり、hold row や解除口ではない |

## 契約

新しい署名は次で固定する。

```python
GuardMode = Literal["import-and-call", "call-only"]

def enforce_held_functions(
    namespace: MutableMapping[str, object],
    module_file: str | os.PathLike[str],
    *,
    plain_runner: PlainRunner,
    guard_mode: GuardMode = "import-and-call",
) -> tuple[str, ...]:
```

- runtime が許す literal は `"import-and-call"` と `"call-only"` の二つだけ。
- 既定値は `"import-and-call"`。既存呼出では mode 分岐が成立せず、[growth_test_holds.py:646-655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:646) の現行判定をそのまま通す。
- `"call-only"` でも [growth_test_holds.py:599-606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:599) の wrapper と exact token 判定は不変。
- repository 内の canonical binding では、明示的な `guard_mode="import-and-call"` は受理しない。既定形は kwarg 省略の一表記に固定する。

`_guard_binding_errors` の exact 述語は次の全条件の論理積とする。

1. unaliased import、全 call、top-level expression call が各 1 個。
2. positional args はちょうど `globals()` と `__file__`。
3. self-load なしなら keyword 名列がちょうど `("plain_runner",)`。
4. canonical self-load ありなら keyword 名列がちょうど `("plain_runner", "guard_mode")` で、mode 値は文字列定数 `"call-only"`。
5. runner は現行 3 literal の一つで、`_plain_runner_for_tree` の導出値と一致。
6. test 定義後、`__main__` guard 前という配置は不変。
7. 重複 keyword、逆順、`**mapping`、非文字列定数、未知 keyword、第三 positional argはすべて拒否。

| 入力形 | self-load | 現行 | 変更後 | 判定理由 |
|---|---:|---:|---:|---|
| `plain_runner="manual"` | なし | 受理 | 受理 | 現行 canonical 形 |
| `plain_runner="manual"` | あり | 受理 | 拒否 | F351 を受入全走より前に止める |
| `plain_runner="manual", guard_mode="call-only"` | あり | 拒否 | 受理 | 今回だけ新たに受理する集合 |
| 同上 | なし | 拒否 | 拒否 | 不要な import 緩和を許さない |
| `guard_mode="import-and-call"` を明記 | 任意 | 拒否 | 拒否 | default は省略形だけ |
| mode が未知値、変数、重複、逆順、`**kwargs` | 任意 | 拒否 | 拒否 | closed contract を維持 |
| `plain_runner="call-only"` | 任意 | 拒否 | 拒否 | runner literal は増やさない |
| runner と `_plain_runner_for_tree` が不一致 | 任意 | 拒否 | 拒否 | [同:583-588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:583) を維持 |

自己読込検出は次の規則にする。

- 母集合は [同:447-448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:447) の登録済み held filename だけ。`test_*.py` glob は新設しない。
- outer AST では import alias map と一意な代入を追い、`spec_from_file_location` と後続 `exec_module`、`runpy.run_path`、exact な `exec(open(self).read())` 系について、path が `__file__` 由来かを判定する。
- subprocess の `-c` payload は、定数文字列または一意に束縛された `textwrap.dedent(...)` だけを解決する。`JoinedStr` の `{str(Path(__file__))!r}` を quoted sentinel に置換して nested AST を parse する。これで [test_s8b_floor_campaign.py:7896-7901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_s8b_floor_campaign.py:7896) を検出できる。
- loader path が `root/tools/spool_fold.py`、`root/tools/check_docs.py` である [test_check_docs.py:1934-1941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_check_docs.py:1934)、[3952-3960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_check_docs.py:3952)、[9760-9768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_check_docs.py:9760) は foreign と判定する。
- loader を含む nested source が静的に解決不能なら「self-load なし」には倒さず binding error とする。任意コードを評価して判定しない。
- 既存 meta-test が既に各 held file を読み AST 化しているため、tree と node 列を再利用する。追加の repo 列挙・file read は発生させない。

## テスト計画

この段では pytest は実行していない。実装段での nodeid 候補と変異対応は次のとおり。

| nodeid 候補 | 検査内容 | 落とす変異 |
|---|---|---|
| `test_growth_test_holds_contract.py::test_enforcement_signature_pins_independent_guard_mode_default` | kw-only 名、二 literal、既定値 `"import-and-call"` を固定 | kwarg 改名、runner literal への混入、default の `"call-only"` 化 |
| `...::test_guard_mode_rejects_unknown_literal` | runtime が未知文字列、bool、`None` を拒否 | `_GUARD_MODES` 検査削除、truthy 値の受理 |
| `...::test_guard_binding_requires_call_only_exactly_for_canonical_self_load` | 現行 exact binding、self-load + call-only、不要な call-only、未知・重複・逆順を表どおり検査 | `len(keywords) in (1, 2)` だけへの緩和、explicit default 受理、self-load と mode の非結合 |
| `...::test_self_load_detection_handles_subprocess_fstring_and_foreign_loader_paths` | F351 型 nested f-string、import alias、`test_check_docs` 型 foreign path controls | outer AST call だけを見る変異、API 名出現だけで発火する変異、alias 見落とし |
| `...::test_every_held_module_has_exact_top_level_guard_binding` 改訂 | 登録済み 13 file に条件付き exact 述語を適用 | 実 binding の追加 kwarg、未知 mode、配置・runner drift |
| `...::test_call_only_mode_allows_import_but_refuses_held_call` | synthetic registered filename を subprocess loader で読む。`IMPORT_OK` を確認後に held function を呼び、拒否 diagnostic と body marker 不在を確認 | import 拒否を残す変異、mode return を wrap 前へ移す変異、wrapper 削除、held body 実行 |
| 既存 `test_noconftest_bypass_is_refused_before_held_body`、`test_import_guard_rejects_nonempty_nonexact_release_token`、`test_plain_runner_bypass_is_refused_before_held_body` | mode 未指定の import 拒否を継続検査 | default 変更、default 経路まで call-only にする変異 |
| 既存 `test_all_registered_nodes_are_call_time_wrapped`、`test_exact_token_is_the_only_release_for_lightweight_body` | wrapper と exact token を継続検査 | call-only 時だけ wrapper を外す変異、token 比較の緩和 |
| 既存 `test_regular_pytest_path_keeps_single_hold_skip`、`test_plain_pytest_delegating_runner_is_not_over_rejected` | conftest 経路の受理集合不変 | mode 判定を pytest session 判定より広く誤適用する変異 |
| `test_inventory_count_and_key_digest_are_independently_pinned` と `test_inventory_projects_exact_registered_source_sets` | 59 node、既存 digest、13 held file を維持 | synthetic control を実 registry に誤登録する変異 |

## pin 閉包

壊しうる既存検査・golden・meta-test は次で閉じる。

- Registry exact pins: [test_growth_test_holds_contract.py:39-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:39)、[261-290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:261)、[396-412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:396)。`count=59`、key SHA、row SHA、collateral notes は変更しない。
- Held filename golden: [同:622-637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:622)。`test_s8b_floor_campaign.py` は追加しない。
- Binding/runner meta-tests: [同:466-589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:466)、[622-680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:622)。
- Runtime guard meta-tests: [同:683-715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:683)、[731-763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:731)、[799-920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:799)。
- Collection acceptance: [conftest.py:321-333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/conftest.py:321)、[616-620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/conftest.py:616)、[1000-1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/conftest.py:1000)。mark/unmark と exact opt-in は不変。
- Inventory projection/golden: [hold_inventory.py:80-107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/tools/hold_inventory.py:80)、[test_hold_inventory.py:375-430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_hold_inventory.py:375)、[524-570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_hold_inventory.py:524)。schema・layer fields・node set・digest は無変更。
- 現行 default binding 13 面: `test_campaign_import_invariant.py:1707-1708`、`test_check_docs.py:9986-9987`、`test_codex_reasoning_ab.py:7081-7082`、`test_env_attestation.py:1359-1360`、`test_real_repo_serialization.py:33,1670`、`test_ruleops.py:3455-3456`、`test_s1_known_axes_freeze.py:25,678`、`test_s1_measurement_freeze.py:23,322`、`test_s8b_binding_driftguards.py:536-537`、`test_s8b_holdout_freeze.py:1961-1962`、`test_s8b_oracle_driver.py:5294-5295`、`test_s8b_protocol_builder.py:41,1865`、`test_s8b_repo_scan_invariant.py:54-55`。全て mode 無指定のまま受理されなければならない。
- Path 検索で、`test_check_docs.py` は [tools/codex_reasoning_ab.py:89-101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/tools/codex_reasoning_ab.py:89) に source SHA pin を持つ。negative control のために同 file の binding を編集してはならない。
- `growth_test_holds.py`、`test_growth_test_holds_contract.py`、`hold_inventory.py` 自体の live source-byte pin は検索上なし。歴史記録と `output/insights` は実効 pin ではない。

## リスク

- **P1 は賛成。** `plain_runner` は [test_growth_test_holds_contract.py:466-505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:466) が実行形から導出する値であり、`"call-only"` を混ぜると別軸が衝突する。`guard_mode` の閉じた enum がよい。
- **P2 は条件付き賛成。** 「self path を loader へ渡す」意味上の限定は正しいが、outer AST の call だけを見る実装には反対する。[test_s8b_floor_campaign.py:7896-7912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_s8b_floor_campaign.py:7896) の nested source まで二段 parse する必要がある。
- **P3 は賛成。** [test_growth_test_holds_contract.py:766-797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:766) の tmp module と [592-615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:592) の subprocess seam で十分。実 registry 追加は不要かつ禁止。
- 実装前の択一は、未知の動的 loader path を「非 self」とみなすか、選別不能として拒否するか。後者を採る。誤拒否は局所的だが、前者の誤受理は受入 lease を再び失う。
- call-only は module の top-level 実行を許す。比例コストが held function／fixture 内にあり、import-time side effect にないことを候補選別文にも加えるべきである。
- wrapper は [growth_test_holds.py:640-644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:640) で canonical global 名を差し替える方式である。guard 前に元関数を別名へ退避する file は call-only 候補にできない。この条件も decisions fragment に明記する。
- detector は既存 held-file AST 面へ統合する。全 test file scan や API 文字列 grep を別 node として足す案は、repo 成長比例と `test_check_docs.py` 偽陽性の双方により却下する。

## 総括

P1 の独立 `guard_mode` を採り、既定は現行と同じ `"import-and-call"` に固定する。  
新たに受理する binding は、canonical self-load を持つ file の exact `guard_mode="call-only"` だけである。  
検出は登録済み held file の既存 AST pass に統合し、nested subprocess source まで安全に二段 parse する。  
正例は synthetic module + subprocess で import 成功と held body 未到達を同時に証明する。  
registry、inventory、13 個の現行 binding、count と digest は一切変更しない。