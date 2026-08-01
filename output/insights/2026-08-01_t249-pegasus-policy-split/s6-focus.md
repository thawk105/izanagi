| ID | 判定 | 根拠 |
|---|---|---|
| C-1 | closed | calibration policy の leaf symlink を両 shell が拒否する。[certify_calibration.sh:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:110)、[submit_certify.sh:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:56) |
| C-2 | not-adopted | 親裁定どおり runtime の型・process-substitution rc は未修正。[s6-fix-prompt.txt:53](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s6-fix-prompt.txt:53) |
| C-3 | closed | certify の文字列 7200 秒と `_s` を直接比較する。[test_pegasus_tools.py:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:153) |
| D #1 | partial | direct literal read の positive control はあるが、列挙済みの回避形は残る。[test_pegasus_policy_registry.py:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:319)、[同:426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:426) |
| D #2 | closed | directory・symlink・special entry を flat-layout 違反として拒否する。[test_pegasus_policy_registry.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:402) |
| D #3 | closed | registry 読取前に registry・policy directory の全 component と containment を検査する。[test_pegasus_policy_registry.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:61)、[同:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:346) |
| D #4 | closed | `git ls-files -z` の decoded exact set membership に変更済み。[test_pegasus_policy_registry.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:46)、[同:378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:378) |
| D #5 | closed | C-3 と同じ相互一致 assert が M6 を kill する。[test_pegasus_tools.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:157) |
| D #6 | regressed | 元の task-handle 過剰拒否は閉じたが、同じ shared handle の再束縛まで shadowing 扱いして見逃す。[test_pegasus_policy_registry.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:112) |
| D #7 | not-adopted | 所在 inventory なので dead file は意図的に許容。[s6-fix-prompt.txt:56](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s6-fix-prompt.txt:56) |
| F1 | closed | 3 組の相互一致と、非空の既存 600 秒 oracle 束縛がある。[test_pegasus_tools.py:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:134)、[test_pegasus_floor_tools.py:317](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_floor_tools.py:317) |
| F2 | closed | rc 非 0・decode 失敗は例外で赤、path は canonical 化後の exact membership。[test_pegasus_policy_registry.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:46) |
| F3 | closed | nested directory と全 special entry を拒否。[test_pegasus_policy_registry.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:402) |
| F4 | closed | `lstat`・symlink component・strict resolve・repo containment を registry 読取前に確認。[test_pegasus_policy_registry.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:61) |
| F5 | closed | C-1 と同じ。共有 `policy.json` の既存検査は不変。 |
| F6 | partial | 親裁定どおり best-effort への限定と positive control まで。[test_pegasus_policy_registry.py:426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:426) |
| F7 | regressed | D #6 と同じ新規 false negative がある。 |

## partial / regressed / 新規所見

### D #1 / F6 — partial（裁定どおり）

場所: [test_pegasus_policy_registry.py:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:217)、[同:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:319)

攻撃入力は引き続き `KEY = "certify_walltime_s"; p[KEY]`、文字列結合、`Path("tools") / "pegasus" / "policy.json"`、jq 変数展開、suffixless executable。docstring はこの非網羅性を正しく限定し、positive control は恒真ではない。

**成果物影響:** task policy 更新後も shared 旧値を読む consumer が残り、PBS request、receipt、reservation deadline と certified 受理集合を分離しうる。

最小 fix（別 scope）: shared policy read を閉集合 accessor に集約する。scanner 継続なら各回避形の positive mutation を追加する。

### R-1 — D #6 / F7 の regressed

場所: [test_pegasus_policy_registry.py:96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:96)、[同:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:112)、[同:129](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:129)

攻撃入力:

```python
with open(sys.argv[1]) as handle:
    with handle as handle:  # file.__enter__ は同じ shared file object を返す
        policy = json.load(handle)
        print(policy["certify_walltime_s"])
```

nested `with` が同名を bind しただけで body を走査せず、外側ではそこで `break` するため finding は空になる。fix 前は outer `ast.walk()` がこの `json.load(handle)` を拾っていた。[integration snapshot:255](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s6-integration-snapshot.patch:255)

通常の直接形 `with open(shared) as handle: policy=json.load(handle); policy["certify_walltime_s"]` は、call 登録から root 伝播まで到達するため依然検出される。[test_pegasus_policy_registry.py:243](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:243)、[同:260](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:260)

**成果物影響:** 正当な refactor 形で frozen shared 値の live read を再導入でき、task policy 更新時に receipt・deadline・台帳と scheduler request を食い違わせうる。

最小 fix: 同名かどうかではなく binding provenance を追う。少なくとも context expression が同じ shared handle 自体なら provenance を維持し、この攻撃を positive control に追加する。

## 不採用所見の残存射程

C-2 の `"certify_walltime_s": "7199"` は、F1 の `7200 == "7199"` が偽になるため pytest 層では赤になる。`"7200"` でも型が異なるため同様で、`finalize_reserve_s: "600"` も `{600} == {"600"}` が偽になる。[test_pegasus_tools.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:157)、[同:164](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:164)

ただし shell 本体には厳密型検査も producer rc 捕捉もない。[certify_calibration.sh:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:114) は行数 `>= 12` だけ、[submit_certify.sh:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:60) も process substitution の rc を見ない。したがって pytest gate を経ない実行では数字文字列を `int()`／Bash 算術が受理し、改行注入による producer 失敗の偽成功も残る。これは親裁定どおり別 ID の残余であり、本 wave の fix 要求にはしない。

D #7 は consumer 不在なら成果物影響がなく、追加実害は確認できない。

## closed 判定の焦点裏取り

- F1: `7200 → 7199` は certify 相互一致 assert で確実に赤。smoke と floor の `_s` 単独 drift も同じ比較へ到達する。reserve は `formula_reserves` の非空 assertと exact set 比較があり、[certify_calibration.sh:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:11)・[同:593](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:593) の独立した 600 秒へ束縛される。恒真・空集合ではない。

- F2: `check=True` なので `git ls-files` の rc は握り潰さない。UTF-8 decode 失敗も false green ではなく例外になる。`./`・末尾 `/` は `relative != parsed.as_posix()`、大文字小文字差は exact set membership で拒否される。[test_pegasus_policy_registry.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:48)、[同:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:380)

- F3/F4: `tools`、`pegasus`、`policies`、registry leaf の順で `lstat` し、例外・strict resolve 失敗・containment 失敗はいずれも registry 読取前の `pytest.fail` へ入る。nested/special entry も明示拒否される。

- base `7b24f81` との `git show` 比較では、既存 project/queue/nodes/header/envelope assert の削除・xfail 化はない。floor fixture は新 policy を明示コピーし、calibration fixture は既存 `copytree(TOOL_DIR)` で包含する。[test_pegasus_floor_tools.py:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_floor_tools.py:169)、[test_pegasus_tools.py:1056](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:1056)

- protected-path diff は rc 0、`policy.json` SHA-256 は `b1c42e…961ac` のまま。

## M1〜M7 の kill 可否

| 変異 | 静的判定 | 根拠 |
|---|---|---|
| M1 | KILL | calibration entry 削除で `registered != discovered ∪ legacy`。[registry test:414](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:414) |
| M2 | KILL | tracked direct file が `discovered` だけに増え closed-set mismatch。 |
| M3 | KILL | registry の exact path が tracked set から消え finding。[registry test:420](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:420) |
| M4 | KILL | leaf symlink を component scan と `lstat` の双方が拒否。[registry test:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:389) |
| M5 | KILL | 現行 heredoc の shared argv → shared handle → `p["certify_walltime_s"]` を検出する。[registry test:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:319) |
| M6 | KILL | `02:00:00 → 7200` と 7199 の比較が失敗。期待 node は `test_pbs_directives_match_shared_and_calibration_policies`。 |
| M7 | SURVIVE | direct regular tracked file を sorted 登録すれば、flat closure・exact membership・surface 検査をすべて満たす。F7 回帰は consumer のないこの正例へ影響しない。 |

## 総括

- 静的判定は closed 11 件、partial 2 件、regressed 2 件、not-adopted 2 件。
- F1〜F5 は要求された攻撃に対して閉じており、M1〜M6 は KILL、M7 は SURVIVE の見込み。
- C-2 の数字文字列は F1 pytest では赤だが、shell runtime の型・rc 問題は裁定どおり残る。
- F7 は元の過剰拒否を閉じた一方、同一 shared handle の nested 再束縛を見逃す新規回帰を導入した。
- この回帰には成果物影響があり、nit ではない。
- pytest は一切実行しておらず、緑は主張しない。
- 判定: **NO-GO**。