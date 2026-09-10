# 段 6 fix (2 巡目) 報告

## 1. 6 所見の対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1 | closed | [tools/check_branch_rescue.py:1042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1042)、[test_check_branch_rescue.py:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:871) |
| A3 | closed | [tools/check_branch_rescue.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:228)、[test_check_branch_rescue.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:1113) |
| A8 | closed | [tools/check_branch_rescue.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1159)、[test_check_branch_rescue.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:1040) |
| A9 | closed | [tools/check_branch_rescue.py:756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:756)、[test_check_branch_rescue.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:1070) |
| B3 | closed | [test_branch_rescue_ledger.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_branch_rescue_ledger.py:25)、[test_branch_rescue_ledger.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_branch_rescue_ledger.py:151) |
| A4 | closed | [tools/check_branch_rescue.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:643)、[tools/check_branch_rescue.py:1402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1402)、[test_check_branch_rescue.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:931) |

変更した既存期待値は m25 のみです。

- 旧: rc=0
- 新: promisor missing issue により rc=2
- 根拠: 追補 2 §1 の「storage を分類できない場合は indeterminate、rc=2」と今回の A1/A3 裁定

pytest は child 未起動のため、上表の closed は実装と負例の静的確認による判定です。green は申告しません。

## 2. A1 / A3(b) の missing object 経路をどう fail-closed にしたか

候補 branch reflog と撤去 worktree HEAD reflogの各 OIDについて、`cat-file` が `missing` を返した場合に `removed-reflog-object-missing` issueを記録します。

missing OID は正側へ投入しませんが、issue が `affects_completeness=true` のため snapshot は不完全となり、最終 rc=2 になります。commit と判定できた OID だけを従来どおり正側へ投入します。

## 3. A3(a) wrapper の interpreter をどう固定したか

`sys.executable` を `Path.resolve(strict=True)` で絶対化し、その path を shebang へ直接埋め込みました。空白を含む shebang 非互換 path は拒否します。

実 Git も `shutil.which()` の結果を symlink 解決した絶対 path に固定し、wrapper はその path を `execv` します。`/usr/bin/env python3` は廃止しました。

## 4. A8 / A9 の例外集約

- A8: snapshot canonical JSON を `ensure_ascii=True` に変更しました。surrogate を ASCII escapeへ変換するため、`UnicodeEncodeError` 自体が発生せず、Git が扱える非 UTF-8 ref は rc=0 の正常経路を維持します。
- A9: timestamp 変換時の `ValueError`、`OverflowError`、`OSError` に加え、expiry 加算・UTC直列化時の `OverflowError` と `ValueError` を `reflog-parse-error` へ変換し、rc=2 に集約しました。

## 5. B3 の fence 除外

可視 Markdown 抽出で、CommonMark の backtick fence と tilde fence の両方を追跡します。開始 marker と同じ文字で、開始以上の長さを持つ終了 marker までの内容を除外します。

## 6. A4 の絶対期限 parse

有効な ISO dateまたは datetime を先に厳格検証し、その後 Git の read-onlyな `rev-parse --since=<value>` で実際の cutoff timestamp を取得します。

loose object の mtime と cutoff を比較し、absolute期限を `determinate` として算出します。不正な日付や非 ISO 値は従来どおり `conservative-floor` です。契約文書も [unreachable-object-ledger.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/docs/unreachable-object-ledger.md:86) に反映しました。

## 7. 追加した負例と、それが殺す欠陥

- A1: candidate reflog-only commit の loose object を実際に欠落させ、issue、snapshot不完全、rc=2を要求。
- A3: promisor remote にだけ missing commit を残し、子 checker が環境変数を外して wrapper Git を起動。任意 PATH の `python3` trap未実行、missing issue、rc=2、object DB byte不変を要求。
- A8: byte `0xff` を含む loose refを作り、start/end snapshot digestとJSON出力まで通してrc=0を要求。
- A9: timestamp自体は有効だが30日加算がoverflowするreflogを作り、`reflog-parse-error` とrc=2を要求。
- B3: `~~~` 内だけに成立条件を満たす偽 bulletを置き、execution edge不成立を要求。
- A4: `gc.pruneExpire=2030-02-01` を設定し、`determinate` とabsolute専用basisを要求。

各負例が旧欠陥で失敗することは静的に確認しました。pytestによる動的確認は下記のinfra障害で未実施です。

## 8. closed 14 件を壊していないことの確認方法

- `git status --porcelain=v2`: unstaged変更は指定された4 fileだけ。
- `git diff --check`: rc=0。
- 3 Python fileのAST parse: `ast-parse: ok`。
- 既存期待値を変更したのは、実 missing fixtureへ作り直したm25だけ。
- A2/A5/A6/A7/A10からA14、B1/B2、親D2の実装・期待値は変更していません。
- `check_docs` はrc=0。
- U+0300からU+036Fのscanは `combining-scan: ok`。
- `git add`、commitは行っていません。

pytest未実走のため、closed 14件の動的regression確認は親で再実走が必要です。

## 9. 実走結果

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/4aeb74d7b0cab799d56c9f2ac86f6b3f/receipt.json へ保存しました (child rc=16)
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

rc=16。test childは起動していません。

```text
$ python3 tools/run_tests.py orchestrator/tests/test_branch_rescue_ledger.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/ba7efc772677258d9fd667e770297bf1/receipt.json へ保存しました (child rc=16)
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

rc=16。test childは起動していません。`--force-dispatch` の再試行も同じpreflight障害でした。生成されたreceiptは4 file制約へ戻すため除去しました。

```text
$ python3 tools/check_docs.py
check_docs: 違反なし
```

rc=0。

## 総括

未closedだった6所見の実装と負例を、指定された4 fileだけで修正しました。docs checker、AST、差分検査は成功しています。pytestはPegasus dispatch infrastructure failureにより一件も実行されていないため、親で対象2 test fileを再実走してから統合してください。commitとstagingは行っていません。