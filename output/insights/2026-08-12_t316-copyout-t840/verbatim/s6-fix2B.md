実装と静的診断は完了しました。ただし Pegasus dispatch が pytest 起動前に `qstat -Q preflight rc=1`（runner rc=16）で停止したため、全所見を `partial（実装済み・未実走）` と判定します。docs・commit・所有外ファイルは変更していません。

## 総括

| 所見 | 判定 | 根拠 |
|---|---|---|
| H-1 AST 静的回避 | `partial` | import 由来 binding の非 `Call.func` load を taint 化し、文字列 binding を固定点追跡。[test_p3_build_authority_cli.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:285)、[同:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:326)、[同:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:569) |
| H-2 M11 | `partial` | prefix・nested synthetic source を実 matcher に投入。[test_p3_build_authority_cli.py:676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:676) |
| H-3 leaf 偽陽性 | `partial` | leaf 名単独判定を廃止し、import 由来 binding / campaign-module re-export に限定。同名 local function の正例を追加。[test_p3_build_authority_cli.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:434)、[同:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:848) |
| H-4 AST audit 費用 | `partial` | 静的 helper 実走は 474 files / 16,031,411 bytes / **10.438875 秒**。pytest node は未実走。[test_p3_build_authority_cli.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:617) |

H-1 の6パターンは、静的 matcher 上では次の扱いになりました。ただし pytest 未実走のため所見自体は `partial` です。

- import alias・多段 name alias: alias assignment の非-call loadと、最終 call のexact allowlist不一致で拒否。
- `(helper,)[0]`: tuple格納時のloadを拒否。
- `{"x": helper}["x"]`: dict格納時のloadを拒否。
- `pass_helper(helper)`: 引数渡しのloadを拒否。
- `globals()["add_coder_build_authority_argument"]`: authority-sensitive globals lookupとして拒否。
- 変数化したmodule名・attribute名: 文字列固定点から `import_module` / `getattr` を解決し拒否。

完全動的な文字列、`eval` / `exec`、外部注入値、monkeypatchされたimport/builtins、非Python issuerは閉じていません。この限界をmodule docstringへ逐語的に列挙し、主張を縮めました。[build_admission.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:5)

変更前後の挙動は以下です。

- 変更前: tuple/dict格納、引数渡し、globals lookup、変数経由dynamic import/getattrがclosure auditを通過。
- 変更後: 上記は補助AST auditで拒否。exact allowlistedな直接 `Call.func` は従来どおり受理。
- 無関係な同名local functionはauthority callとして扱わない。
- runtime admission、登録済み6 entrypoint、red/kickoff、receipt/WAL/cache/COMMIT/freezeの受理挙動は変更していません。

M11は、実 matcherでは両decoyが `(actual=1, expected=0)` になります。`path == relative_path` をprefix一致へ置換した静的対照では両方とも違反が空になり、変わる理由はpath照合だけでした。したがって単一理由性は静的には確認済みですが、mutation harness本走は未実施です。

検査状況:

- 追加・変更した9 test関数の直接静的診断: 成功。ただしpytestの緑には数えていません。
- repository-wide helper直接診断: inventory一致、authority violation 0、star import 0、registered call 6。
- 履歴走査なし。`git ls-files` 1回とtracked sourceのread/parseのみで、`git log`は経路にありません。
- `git diff --check`: 成功。
- T-841対象のschema定数、`_ADMISSION_KEYS`、`_new_policy()`、`derive_build_admission()`、validatorはHEADとAST同一。
- 焦点9 node、repository-wide audit node、collectionはいずれもpytest起動前にrunner rc=16。したがって緑のnodeidはありません。

313 passedを壊していないと考える静的根拠は、今回のproduction変更がmodule docstringのみであること、T-841対象ASTがHEADと同一であること、現行474 sourceのexact inventoryが一致すること、既存期待値を緩和せずdecoyを実 matcherへ強化したことです。ただし実走できていないため、313 passedの維持は主張しません。