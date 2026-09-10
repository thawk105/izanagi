# 段 6 敵対レビュー — レンズ C（挙動の正しさ）

静的検査のみ。pytest・CLI process は実走しておらず、緑／赤の実績は主張しない。以下の「検出可能」はコード上、その assertion が失敗条件に到達するという意味である。

## 1. status 判定

### C1 — R2 の実装順序は正しいが、順序を固定するテストが不足 — **限定付き**

実装は、collector の `SystemExit`／例外を `error` にした後、`model_calls == 0`、打切り・issues、`complete` の順で評価している。[tools/collect_wave_usage.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:109) [tools/collect_wave_usage.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:116) [tools/collect_wave_usage.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:121) [tools/collect_wave_usage.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:134)

具体例:

- `--max-files 0` は helper parser を通るが、ledger の `_max_files()` が `SystemExit(2)` にし、helper は `error` にする。[tools/collect_wave_usage.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:50) [tools/claude_session_ledger.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:97)
- `root_missing`、`exit_code=2`、両 model call が 0 の report は `missing` になる。これは collector が report を返したケースなので、R2 の「missing を incomplete より先にする」に合致する。
- 正規の ledger report では、両 model call が 0 なのに `complete` となる入力は構成できない。

ただし、現テストは「0 call・issues なし」と「非 0 call・issues あり」を別々にしか検査していない。[test_collect_wave_usage.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:57) [test_collect_wave_usage.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:138) `0 call + issues/limit` の fixture がないため、missing と incomplete の順序を逆転させても検出できない。

**成果物影響:** R2 違反が land し、欠測が `incomplete` として恒久記録される。

### C2 — `observed_zero` は廃止済み。ただし非 synthetic 全ゼロ usage は `complete` になり得る — **限定付き**

`observed_zero` 相当の status field はなく、grep hit は否定 assertion のみだった。`synthetic_zero_usage_excluded` は除外件数であり、正常なゼロを示す field ではない。

一方、`model="<synthetic>"` 以外の usage 四区分がすべて 0 の record は妥当な int として受理され、`model_calls` が 1 増える。[tools/claude_session_ledger.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:357) [tools/claude_session_ledger.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:761) その結果、token 合計 0 の report が `complete` になり得る。

これは literal な R2（model call 0 を欠測とする）には違反せず、既存 ledger の受理規則でもあるため、本 wave の must-fix にはしない。

**成果物影響:** upstream が壊れた非 synthetic 全ゼロ usage を出した場合に限り、保存される観測値が偽になり得る。

## 2. `--cwd-under`

### C3 — 指定された文字列境界と AND 条件は実装どおり — **refuted**

`cwd == p or cwd.startswith(p + "/")` がそのまま実装され、`--cwd-contains` が先に不一致を返すため両者は AND になる。[tools/claude_session_ledger.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:511)

- p の末尾 `/` は `Path` 化で通常除去される。
- 相対 p は parser が拒否する。[tools/claude_session_ledger.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:109)
- symlink spelling、大小文字違い、相対 cwd は false negative、すなわち `missing` 側へ倒れる。
- AND と `...-fix` 除外はテストされている。[test_collect_wave_usage.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:340)

**成果物影響:** なし。

### C4 — 文字列境界は filesystem 境界ではない — **限定付き**

p が `/w/wave`、record.cwd が `/w/wave/../other` の場合、prefix 条件を満たして取り込まれる。p 自身に `..` がある場合も正規化されない。さらに p が `/` の場合、子は `"//"` で始まらないため一致しない。

ただし R3 は filesystem canonical containment ではなく、この文字列条件を明示的に要求しているため、裁定を越えた must-fix にはしない。

**成果物影響:** `..` を含む cwd が transcript に現れた場合、保存される観測値が偽になり得る。

## 3. 非 gate

### C5 — import error は `main()` より前に process を非 0 終了させる — **real / must-fix**

repo-local import は module import 時に実行されるが、非 gate の例外捕捉は `main()` 内にしかない。[tools/collect_wave_usage.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:7) [tools/collect_wave_usage.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:22) [tools/collect_wave_usage.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:218)

`orchestrator.campaign.site_policy` または `tools.claude_session_ledger` の import が失敗すると、`sys.exit(main())` に到達せず通常 rc=1 になる。

**成果物影響:** 非 gate を破って wave が止まる。

### C6 — helper 自身の実 process rc=0 を固定するテストがない — **real / must-fix**

新テストはすべて `USAGE.main(argv)` の直接呼出しである。subprocess に言及するテストも、製品コードが subprocess を使わないことを AST で調べるだけで、helper CLI を起動していない。[test_collect_wave_usage.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:157)

既存の実 process test は `claude_session_ledger.py` 用であり、helper は対象外である。[test_claude_session_ledger.py:1328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_claude_session_ledger.py:1328)

argparse、collector 例外、`--out` 検査、書込み、`os.link` の通常の `Exception` はコード上 `main()` が 0 にする。`KeyboardInterrupt` を捕捉しないのはR5どおりである。

**成果物影響:** process 境界の非 gate 回帰が検出されず land し、wave が止まり得る。

## 4. atomic publish

### C7 — dangling symlink の `--out` は create-only を迂回する — **real / must-fix**

`_validated_out()` は CLI で指定された path を `resolve()` し、その解決先を publish に渡す。[tools/collect_wave_usage.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150)

具体例として、既存の `/outside/usage.json` が、まだ存在しない `/outside/new.json` への symlink なら、指定宛先の directory entry は既に存在するにもかかわらず、コードは `/outside/new.json` へ publish する。R5 の「宛先が存在すれば `os.link` が失敗する」を満たさない。既存出力テストは regular file のみで、この入力を固定していない。[test_collect_wave_usage.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:219)

**成果物影響:** create-only 規約違反が land する。

### C8 — 通常の atomicity は成立 — **refuted**

temp は out と同じ parent に作られるため別 filesystem にはならない。完全書込み・flush・fsync・close 後に hard link し、通常例外時は finally で temp を削除する。[tools/collect_wave_usage.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:159)

regular destination が存在すれば元 artifact は不変。書込み途中の例外では link 前なので壊れた artifact は公開されない。SIGKILL または temp unlink 自体の失敗なら temp が残り得るが、壊れた正式 artifact は公開されないため nit とする。

**成果物影響:** なし。

## 5. ログインノード fail-closed

### C9 — `PEGASUS_SUSPECT` と判定証拠欠落が fail-open — **real / must-fix**

helper が停止するのは `is_pegasus_login(site)` の場合だけで、その他は collector を実行する。[tools/collect_wave_usage.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:190) [tools/collect_wave_usage.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:198)

site policy は判定不能を `PEGASUS_SUSPECT` にする経路を持つが、`is_pegasus_login()` はそれを拒否対象にしない。[site_policy.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:37) [site_policy.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:75) 同じ policy の `refuses_heavy_work()` は login と suspect の両方を拒否している。[site_policy.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:83)

また、hostname が `pegasus02` でも NQSV 証拠を取得できなければ `OTHER` となり、helper は収集を走らせる。[site_policy.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:42)

現テストは正確な `PEGASUS_LOGIN` 一値しか試していない。[test_collect_wave_usage.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:238)

**成果物影響:** 未分類 tool をログインノードで走らせる規約違反が land する。

## 6. collector の後方互換

### C10 — schema v2 と既存 report 出力の変更は見当たらない — **refuted**

`collect_report()` 抽出による実質変更は、新しい `cwd_under` 引数の伝播と、render 前に `CollectionResult` を返す分離である。[tools/claude_session_ledger.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:936) schema は引き続き 2 で、`cwd_under` を schema v2 内へ追加していない。[tools/claude_session_ledger.py:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:859)

text render と JSON の sort/separators/newline は従来どおりである。[tools/claude_session_ledger.py:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:797) [tools/claude_session_ledger.py:1061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:1061) `--help` は新 option 追加により意図的に変わる。

**成果物影響:** なし。

## 7. M1〜M9 の静的検出力

| 変異 | 静的判定 | 根拠 |
|---|---|---|
| M1 | 検出可能 | zero fixture の `files_scanned=9` なので `complete` へ変わり assertion が失敗条件に到達する。 |
| M2 | 検出可能 | limit 以外の理由がないため、分岐削除で `complete` になる。 |
| M3 | 検出可能 | `seen.index("--cwd-under")` が成立しなくなる。[test_collect_wave_usage.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:112) |
| M4 | 検出可能だが過剰決定 | fake collector の call count と AST の subprocess/json.loads/import 検査が同時に反応し得る。単一理由性は弱い。 |
| M5 | **不十分** | collector 例外 artifact の code は `None`。直接 rc へ差し替えると public `main()` assertion は失敗するが、`sys.exit(None)` は process rc=0。collector が `exit_code=2` を返す実 process fixture がない。 |
| M6 | 検出可能 | regular existing file が truncate/overwrite され、byte equality が崩れる。 |
| M7 | 検出可能だが範囲不足 | exact login 分岐の削除は status assertion が検出するが、SUSPECT/OTHER の fail-open は検出しない。 |
| M8 | **検出不能** | `forbidden_collect()` の `AssertionError` は `_collect()` の `except Exception` に飲まれ、期待どおり `error` artifact ができるため全 assertion が成立する。[test_collect_wave_usage.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:261) [tools/collect_wave_usage.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:141) |
| M9 | 検出可能 | `.../izanagi-fix` が余分に数えられ、期待 2 call が崩れる。 |

### C11 — M8 の fallback 禁止テストは実装の誤りを隠す — **real / must-fix**

例外を「呼ばれなかった証拠」としているが、製品コードがその例外を正規の `error` に変換するため、実際には collector を呼んでもテストが通る構造である。call counter を別に持ち、0 を直接 assert する必要がある。

**成果物影響:** 全 project fallback という規約違反が land する。

### C12 — M5 は public 関数の値しか固定せず、非 gate の process 性質を固定しない — **real / must-fix**

collector が report と `exit_code=2` を返す fixture、および helper を subprocess で起動して returncode 0 を検査する fixture がない。

**成果物影響:** 非 gate を破る変更が land し、wave が止まり得る。

## 8. 既存テストの弱体化

### C13 — 既存期待値の変更・緩和・skip はない — **refuted**

`test_claude_session_ledger.py` の差分は末尾への 39 行追加だけで、既存 assertion の変更はない。[test_claude_session_ledger.py:1347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_claude_session_ledger.py:1347) 新 test file に skip/xfail もない。

**成果物影響:** なし。

## 総括

**判定: NO-GO**

must-fix:

1. `PEGASUS_SUSPECT` および login 判定証拠欠落を collector 実行へ倒さない。
2. repo-local import error を process rc=0 の捕捉境界内へ入れ、helper 自身の subprocess test を追加する。
3. dangling symlink の `--out` を既存宛先として拒否し、create-only を lexical destination に対して守る。
4. M8 を call counter で修正し、collector 未呼出しを直接固定する。
5. `0 model call + issues/limit` で missing 優先を固定する。
6. collector `exit_code=2` を使い、実 process の非 gate を固定する。

見送り可:

- 非 synthetic 全ゼロ token usage。literal R2 と既存 ledger 受理規則の範囲内。
- `cwd` の `..`、symlink spelling、大小文字、p=`/`。文字列境界という段4裁定を越える変更になるため、必要なら別裁定。
- SIGKILL／temp unlink 失敗時の temp 残存。正式 artifact の破損公開経路ではない。