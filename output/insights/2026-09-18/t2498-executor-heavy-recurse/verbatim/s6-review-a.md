## 所見 (real / refuted、must-fix / nit / backlog、成果物影響、再現入力と実測)

**判定は NO-GO。must-fix は2件です。** 以下、A＝ALLOW、D＝DENY。`repo_root` は指定 worktree、特記のない site は `PEGASUS_LOGIN` です。比較した実体の Git blob は旧 `3b5f6b650`、新 `6f3cf381a` と一致しました。pytest は実行していません。

**1. real / must-fix：深い再帰が例外になり、hook 全体が既存拒否を許可へ反転する。**

対象：[guard_bash.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2498-executor-recurse/hooks/guard_bash.py:1308)。

再現 command は、次の式で生成する13,232文字の文字列です。

```python
command = "python3 " + "-m cProfile " * 1100 + "-m json.tool ; pytest -q"
```

| 検証 | 旧版 | 新版 |
|---|---|---|
| `decide(command, repo_root, site="PEGASUS_LOGIN")` | D：`pytest による test 実行` | `RecursionError` |
| 同じ入力の `main()`、site を LOGIN に固定 | 終了コード2 | **終了コード0、stderr空** |

`main()` はメモリ内の入力と site 固定で呼びました。command 自体は実行していません。

内側 token が減っても、Python の呼出しスタックは有限です。新しい再帰が後続 segment の検査前に例外を起こし、既存の例外処理がこの入力を許可します。したがって、`decide()` の正常戻り値だけを数えた反転検査では捉えられない、実入口での D428 後退です。

**DW-G05 成果物影響：旧版で拒否された後続 `pytest` が新版の hook では許可され、既存拒否集合が縮小する。**

深さ上限で検査を打ち切らず、明示的なスタック等で全層を検査できる構造が必要です。例外時に単純に全拒否するだけでは、深い軽量 command の過剰拒否が残ります。

**2. real / must-fix：script の名前・引数を residual 判定が重量実行と誤認し、裁定外の追加拒否を生む。**

対象：[guard_bash.py:1305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2498-executor-recurse/hooks/guard_bash.py:1305)。

| 再現 command | 旧→新 | 新版の拒否理由 |
|---|---|---|
| `python3 -m cProfile -- -m pytest` | A→D | baseline 重量対象 `pytest` |
| `python3 -m cProfile -o /tmp/x -- -m pytest` | A→D | 同上 |
| `python3 -m cProfile -- -W pytest` | A→D | 同上 |
| `python3 -m cProfile /tmp/safe.py -mpytest` | A→D | `interpreter argv の python3 -m pytest` |

後ろ2件は `PEGASUS_SUSPECT` でも A→D を直呼びで確認しました。

最初の3件は `--` 後の script、最後は `/tmp/safe.py` の引数です。抽出・round-trip 自体は正しいものの、合成後に既存 residual が script 引数を再解釈します。裁定§4は `-- -m pytest` を module 負例から明示的に除外しています。直接形にも同じ拒否があるという説明だけでは、今回新しく狭まる受理集合を「重量形のみ」と承認できません。

**DW-G05 成果物影響：重量 module を実行対象としていない script 形が新たに拒否され、反転検査の「全27件が重量形」という記録も不正確になる。**

§3の「同じ判定を再帰適用」と過剰拒否禁止の境界を解決し、この族の期待値を固定する必要があります。既存の直接形の拒否を緩める修正は D428 に抵触します。

**3. refuted / nit：通常深さでの既存拒否層の素通り、指定された ALLOW 正例の破壊。**

追加綴りを直呼びした結果です。

| command | 旧→新 |
|---|---|
| `python3 -Wignore -Xdev -mcProfile --outfile=tools/run_tests.py /tmp/safe.py` | D→D：出力先拒否 |
| `python3 -Wignore -Xdev -mcProfile -- tools/pegasus/exec_calibrate.py` | D→D：admission |
| `python3 -W ignore -X dev -mcProfile -mpytest --collect-only` | A→A |
| `python3 -m cProfile -m pytest --help` | A→A |
| `python3 -m cProfile --help tools/pegasus/exec_calibrate.py` | A→A |
| `python3 -m trace --report -f /tmp/counts tools/pegasus/exec_calibrate.py` | A→A |
| `python3 -m runpy tools/pegasus/exec_calibrate.py` | A→A |
| `python3 -m cProfile tools/run_tests.py` | A→A |
| `python3 -m cProfile /tmp/safe.py` | A→A |
| `python3 -m cProfile -m json.tool /tmp/a.json` | A→A |
| `python3 -m cProfile -m py_compile tools/check_ai_provenance.py` | A→A |
| `python3 -m cProfile -m timeit x` | A→A |

追加22 command は `OTHER` / `PEGASUS_COMPUTE` でも旧新版の結果が一致しました。通常の戻り値については、再帰が拒否理由を追加するだけで、元 segment の後続検査を許可として短絡しません。所見1の例外経路は別です。

**4. refuted / nit：round-trip 不一致、既存 targets の変化、列挙追加。**

- `_script_executor_targets` は表選択部分の共通化だけで、残りの処理は不変。固定 seed の追加 **5,577入力で返り値の差0件**。
- 抽出成功 **2,569入力で round-trip 不一致0件**。`--`、空文字、空 rest、先頭 `-`、密着形を含めました。
- `python3 -mcProfile -mpytest` は3 token→3 token。**生 token 数の厳密減少は成立しません**が、毎回元引数の真の suffix へ進むため、解析上の無限循環は見つかりませんでした。実装上のスタック枯渇は所見1です。
- `python3 -mcProfile -- -` と `python3 -m cProfile -- -X dev` は `decide()` で A→A。
- multi-target の対照 `python3 -m pydoc -w tools/pegasus/exec_calibrate.py` は A→A。
- 提示された差分に module／option の列挙追加、allowlist 反転、multi-target 集合変更、docs 変更、無関係な本文変更はありません。

## 反転検査の allow→deny 全件照合

親の JSON にある **54件を直呼びで再確認**しました。以下27 command は LOGIN / SUSPECT 共通で、すべて A→D です。

| # | command | 裁定との照合 |
|---|---|---|
| 1 | `python3 -m cProfile -m pytest -q` | §2一致 |
| 2 | `python3 -mcProfile -mpytest -q` | §2一致 |
| 3 | `python3 -m cProfile -o /tmp/p.out -m pytest -q orchestrator/tests/test_hooks.py` | §2一致 |
| 4 | `python3 -m profile -m pytest -q` | §2一致 |
| 5 | `python3 -m pdb -m pytest -q` | §2一致 |
| 6 | `python3 -m trace --trace --module pytest -q` | §2一致 |
| 7 | `python3 -m runpy pytest -q` | §2一致 |
| 8 | `python3 -m cProfile -m cProfile -m pytest -q` | §2一致 |
| 9 | `python3 -m cProfile -m cmake --build build` | §2一致 |
| 10 | `python3.10 -Bm profile -s cumulative -m pytest` | §2重量族、§4綴り差 |
| 11 | `python3 -m pdb -m _pytest.main` | 同上 |
| 12 | `env FOO=1 nice -n 0 python3 -m cProfile -m pytest` | 同上 |
| 13 | `bash -lc 'python3 -m cProfile -m pytest -q'` | 同上 |
| 14 | `python3 -m cProfile -m pytest tools/check_ai_provenance.py` | §4の借用負例 |
| 15 | `python3 -m coverage run -m pytest -q` | §2一致 |
| 16 | `python3 -m coverage run --branch -m pytest` | §2重量族、§4綴り差 |
| 17 | `python3 -m coverage run -m pytest.__main__` | 同上 |
| 18 | `python3 -m cProfile pytest -q` | §4の script 負例 |
| 19 | `python3.10 -Bm profile -s cumulative -m pytest -q` | §2重量族の綴り差 |
| 20 | `python3 -m coverage run --branch -m pytest -q` | 同上 |
| 21 | `python3 -m coverage run -m pytest.__main__ -q` | 同上 |
| 22 | `python3 -m pdb -m _pytest.main -q` | 同上 |
| 23 | `env FOO=1 nice -n 0 python3 -m cProfile -m pytest -q` | 同上 |
| 24 | `python3 -m cProfile -- -m pytest` | **所見2：script 形の過剰拒否** |
| 25 | `python3 -m coverage run --rcfile=tools/run_tests.py -m pytest` | 内側 pytest。§3に整合 |
| 26 | `python3 -m cProfile -m ycsb_silo.exe` | §2個別記載なし。既存重量判定の再帰適用として§3に整合 |
| 27 | `python3 -m cProfile -m perf stat` | 同上 |

## 反転検査 corpus に無い綴りの追加提案 (command と期待判定)

以下は tests と runner の文字列定数に存在しないことを確認しました。site は `PEGASUS_LOGIN`。期待値は修正後の受入条件です。

| command | 期待 | 現在の実測 |
|---|---|---|
| `"python3 " + "-m cProfile " * 1100 + "-m json.tool ; pytest -q"` で生成 | D、例外なし | `decide()` 例外、`main()` は0 |
| `python3 -m cProfile -- -W pytest` | A | D |
| `python3 -m cProfile /tmp/safe.py -mpytest` | A | D |
| `python3 -Wignore -Xdev -mcProfile --outfile=tools/run_tests.py /tmp/safe.py` | D | D |
| `python3 -Wignore -Xdev -mcProfile -- tools/pegasus/exec_calibrate.py` | D | D |
| `python3 -W ignore -X dev -mcProfile -mpytest --collect-only` | A | A |
| `python3 -m coverage.__main__ run --module=pytest --collect-only` | A | A |

深い入力は runner の静的抽出が400文字超を除外するため、生成ケースとして明示的に追加してください。

## 判定 (GO / NO-GO と理由)

**NO-GO。**

深い入力で実入口の deny→allow が再現し、D428を満たしません。また、反転一覧には裁定で重量 module 形から除外された script 形の追加拒否が含まれます。両件の解消と期待値の固定が必要です。

## 総括

通常深さの主要な ALLOW 正例、targets の互換性、round-trip、差分の範囲は確認できました。しかし、**再帰例外による許可への後退と、script 引数由来の過剰拒否の2件が着地を阻みます**。検証は静的確認・`decide()` 直呼び・メモリ内の `main()` 呼び出しのみで、ファイル変更と pytest 実行はしていません。