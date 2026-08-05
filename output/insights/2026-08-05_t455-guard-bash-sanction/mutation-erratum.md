# 変異 matrix と erratum — [T-455]

事前登録は `stage4-mutation-prereg.md`。本走は統合 commit `5084b1a` を含む HEAD `a922ca9` 上で行った
(`DW-O19`: 本走は統合 commit 後)。anchor (old 逐語) は最終 commit で再検証し、両変異とも repo 内 1 箇所
だけに一致することを確認した (`DW-M07`)。

runner は `python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q -rf`、
`--runner-mode dispatch`。login では pytest が hook に拒否されるため sanctioned な runner 経由で
計算ノードへ dispatch した。

## 結果

| 変異 | 期待 | 実測 | 判定 |
|---|---|---|---|
| M1-drop-fetch-sanction | KILLED / 2 node | KILLED / 同 2 node | **一致。単一理由性が成立** |
| M2-glob-sanction-all-pegasus (初回) | KILLED / 2 node | rc=1 だが赤 5 node | **MISMATCH (下記 erratum)** |
| M2-glob-sanction-all-pegasus-v2 | KILLED / 5 node | KILLED / 同 5 node | 一致 |

台帳は `mutation-ledger.json` (初回) と `mutation-ledger-v2.json` (再走)。初回の結果は消していない
(`DW-M02`: 初回結果は消さず erratum とする)。

## erratum — M2 初回の MISMATCH

**何が起きたか。** 事前登録では M2 の期待赤 node を 2 件
(`test_bash_login_fetch_third_party_does_not_sanction_siblings` と既存の
`test_bash_login_sanctioned_entries_are_exact`) とした。実測の赤は 5 件で、追加の 3 件は

- `test_bash_login_retokenizes_env_split_and_skips_exec_argv0`
- `test_bash_login_blocks_attached_and_bundled_python_modules`
- `test_bash_login_resolves_python_modules_to_exact_repo_paths`

だった。いずれも既存テストである。

**なぜ起きたか。** 事前登録の時点で M2 を「冗長 gate」と宣言してはいたが、**冗長の幅を過小に
登録していた**。`_is_sanctioned` の frozenset 照合を `tools/pegasus/` 前置照合へ退行させると、
sanctioned 判定を経由する既存 pin (module 解決の exact 性、env split の再トークン化、
attached / bundled module 形の拒否) が同時に崩れる。親は「新旧 2 つの control が反応する」としか
見積もっていなかった。

**どう扱ったか。** 期待 node を実測どおり 5 件へ直した v2 spec を作り、同じ HEAD で再走して
KILLED を得た。M2 は事前登録の宣言どおり、**新規テスト単独の検出力の証拠からは外す**
(`DW-M03`: 過剰決定なら冗長 gate と明記して単独変異の証拠から外す)。

**本 wave の検出力の証拠は M1 だけである。** M1 は事前登録した 2 node がちょうど赤になり、
それ以外の node は 1 件も赤にならなかった。すなわち「sanctioned 集合から当該 1 行が消えた」
という単一の理由で赤が説明でき、新規テストがその退行を確実に捕まえることが実測で示された。

**副産物として分かったこと。** 受理集合の過剰拡大 (pegasus 配下を一律許可) を検出する層は、
本 wave が足した control を含めて **5 層**ある。防壁のこの側面は薄くない。
