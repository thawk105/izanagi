# 段 6 焦点再レビュー

## 表 1: 段 4 裁定 (a)〜(h) と確定 scope

| 項目 | 判定 | 根拠 |
|---|---|---|
| (a) 代表 failure の nodeid・longrepr tail | closed | `orchestrator/tests/conftest.py:477-491`、`orchestrator/tests/test_pytest_failure_digest.py:267-285` |
| (b) 緑・skip・xfail・xpass・0 collected・worker の無出力 | closed | `conftest.py:333-342,648-676`、`test_pytest_failure_digest.py:510-594` |
| (c) 予算・省略会計・複数 source fixture | closed | `conftest.py:545-619`、`test_pytest_failure_digest.py:384-408` |
| (d) 実 conftest 自動 discovery E2E、実 nodeid、sentinel、全 account、relay 上限、cleanup | partial | `test_pytest_failure_digest.py:614-744`。一時 root の repo 外保証と conftest sha 検査が実効的でない |
| (e) relay limit の 3/4 束縛 | closed | `conftest.py:622-629`、`test_pytest_failure_digest.py:747-760` |
| (f) 通常例外 fail-open、BaseException、inner 例外優先 | closed | `conftest.py:648-700`、`test_pytest_failure_digest.py:763-895` |
| (g) consumer 三形と二行目 decoy | closed | `conftest.py:380-393`、`test_pytest_failure_digest.py:922-940` |
| (h) 実 relay 結合と境界条件 | closed | `test_pytest_failure_digest.py:943-1040`、`tools/pegasus/dispatch_compute.py:741-804` |
| 編集面を 2 ファイルに限定 | closed | `s4-adjudication.md:61-64`。現 `git status` も対象 2 ファイルのみ |
| `report.failed` 独立 stash | closed | `conftest.py:333-342` |
| wrapper の yield 境界・post-yield cleanup・return 不在 | closed | `conftest.py:678-700` |
| worker 無出力・failure 0 件で builder/writer 不呼出し | closed | `conftest.py:648-657,691-693` |
| 49,152 / 4,096 / 5,120 / 1,024 byte 契約 | closed | `conftest.py:294-299,494-515,545-619` |
| failure 後 lazy import、ImportError の限定 fail-open | closed | `conftest.py:622-676` |
| ASCII renderer、source/rendered 二重会計 | closed | `conftest.py:344-377,477-490` |
| 全物理行 `> ` prefix、`FAILED ` 無害化 | closed | `conftest.py:380-430` |
| 安定順・omitted manifest | closed | `conftest.py:449-542` |
| plain-runner `__main__` harness | closed | `test_pytest_failure_digest.py:1043-1044` |

## 表 2: fix 裁定 F1〜F11

| Fix | 判定 | 根拠 |
|---|---|---|
| F1 E2E oracle の実 `longreprtext` 化 | closed | `test_pytest_failure_digest.py:614-721,724-744` |
| F2 excerpt の行構造保持 | closed | `conftest.py:380-438`、`test_pytest_failure_digest.py:83-129` |
| F3 incremental 選択 | partial | block は各候補 1 回だけ `conftest.py:606-619`。ただし各候補で omitted manifest を再ソート・再ハッシュしており、全体は O(n) ではない `conftest.py:518-542,613-617` |
| F4 inner 例外優先順位 | closed | `conftest.py:680-700`、`test_pytest_failure_digest.py:852-895` |
| F5 ImportError 対象限定 | closed | `conftest.py:659-670`、`test_pytest_failure_digest.py:783-809` |
| F6 実 pytest 終了形 | closed | `test_pytest_failure_digest.py:510-594` |
| F7 二行目 decoy の consumer 検査 | closed | `test_pytest_failure_digest.py:922-940` |
| F8 relay 境界ケース | closed | `test_pytest_failure_digest.py:987-1040` |
| F9 テスト単独検出力 | closed | hash・stderr・excerpt・writer・動的予算を検査 `test_pytest_failure_digest.py:225-265,747-895` |
| F10 `pytest.main()` 再入 | partial | コメント訂正と現仕様回帰テストはあるが、stash の session 束縛化は未実装 `conftest.py:322-330`、`test_pytest_failure_digest.py:897-915` |
| F11 repo 外一時ファイル | partial | E2E の test tree・sidecar・basetemp は `tmp_path_factory` 配下 `test_pytest_failure_digest.py:614-679`。しかし repo 外の実効性を assert せず、`__pycache__` 経路も抑止していない |

2 巡目による F1〜F10 の明白な退行は確認できない。ただし F11 の変更で E2E の nodeid 期待値を一時 root 相対へ変更しており、実 acceptance の canonical root とは条件が異なる。

## 表 3: レンズ C / D の全 must-fix

| 所見 | 判定 | 根拠 |
|---|---|---|
| C#1 E2E oracle | closed | `test_pytest_failure_digest.py:614-744` |
| C#2 excerpt 可読性 | closed | `conftest.py:380-438` |
| C#3 inner 例外優先順位 | closed | `conftest.py:680-700`、`test_pytest_failure_digest.py:852-895` |
| C#4 nested `pytest.main()` | partial | `conftest.py:322-330`、`test_pytest_failure_digest.py:897-915`。裁定どおり全面修正は scope 外 |
| C#5 実 TestReport 終了形 | closed | `test_pytest_failure_digest.py:510-594` |
| C#6 consumer 複数行防護 | closed | `conftest.py:380-393`、`test_pytest_failure_digest.py:922-940` |
| C#7 広すぎる ImportError | closed | `conftest.py:659-670` |
| C#8 変異の検出力・帰属 | partial | F9 は実装済みだが、M2/M7 の登録位置が一意でない `conftest.py:333-342,405-430` |
| D#1 E2E 赤 | closed | `test_pytest_failure_digest.py:614-744` |
| D#2 二次計算量 | partial | `conftest.py:518-542,606-619` |
| D#3 nested `pytest.main()` | partial | `test_pytest_failure_digest.py:897-915` |
| D#4 lazy ImportError | closed | `conftest.py:659-670` |
| D#5 relay 境界 | closed | `test_pytest_failure_digest.py:987-1040` |
| D#6 一行 excerpt | closed | `conftest.py:380-438` |
| D#7 単独で生存する欠陥 | closed | `test_pytest_failure_digest.py:225-265,763-895` |
| D#8 M7 の実在性 | partial | `if False` 変異は適用可能だが、`runtest` と `collect` の同形条件があり位置未確定 `conftest.py:333-342` |
| D#9 2 bytes の安全側余裕 | 裁定で scope 外 | `s6-lensD.md:99-107`。F1〜F11 に変更裁定なし |

## 1 — must-fix : F11 は repo 外書込みを実効保証していない

(i) `tmp_path` / `tmp_path_factory` の実体が `ROOT` 外であることを検査していない。E2E の subprocess は `cwd=ROOT` で動き、`PYTHONDONTWRITEBYTECODE` も設定されていないため、repo 内 `__pycache__` 生成経路が残る。`-p no:cacheprovider` は `.pytest_cache` だけを抑止する。

(ii) 一次資料: `test_pytest_failure_digest.py:453-498,510-579,614-679`、`tools/run_tests.py:875-878`。

(iii) 成果物への影響: `test_real_repo_serialization.py` の status 観測と競合し、F11 の潜在フレークを閉じられない。

(iv) 対処案: 一時 root の `resolve()` が repo 配下でないことを assert し、subprocess env に `PYTHONDONTWRITEBYTECODE=1` を設定する。外側の `--basetemp` も repo 配下拒否へ固定する。

## 2 — must-fix : conftest sha256 assert は陳腐化検査として恒真化している

(i) `_copy_real_conftest()` は実ファイルをその場でコピーし、その直後にコピー元とコピー先を比較している。コピー元を変更しても、変更後の内容を再コピーするため常に一致する。stale な固定コピーを検出する assert ではない。

(ii) 一次資料: `test_pytest_failure_digest.py:501-507`。

(iii) 成果物への影響: 「実 conftest と同じ hook 経路を通る」ことを保証したという F11 の根拠が弱く、古い fixture を使った E2E の恒真化を防げない。

(iv) 対処案: コピー内容の hash を実行前に固定した独立 sidecar／生成物と比較するか、コピー後に実 conftest の変更を注入する回帰検査を追加する。少なくとも「コピー直後の自己比較」は stale 検査として報告しない。

## 3 — must-fix : F3 は block 描画だけ O(n) で、選択処理全体は O(n) ではない

(i) block 描画回数の最悪値は `n` 回であり、旧実装の `n(n+1)/2` 回から改善している。しかし候補ごとに omitted 集合全体を sort・JSON 化・SHA-256 化しているため、最悪計算量は少なくとも O(n² log n) である。

(ii) 一次資料: `conftest.py:518-542,606-619`。検出用 counter は `test_pytest_failure_digest.py:411-432`。

(iii) 成果物への影響: 大量 failure 時の終了処理コストと walltime 超過リスクが残る。テストは block 再描画しか数えていない。

(iv) 対処案: 予算判定中は manifest hash を計算せず、固定長 placeholder でサイズ判定し、最終選択後に一度だけ manifest を生成する。

## 4 — must-fix : plain-runner の「repo root 不在」検査が実際には root で実行されている

(i) `sys.path` から root を除外しているが、空文字の path entry を残したまま subprocess を `cwd=ROOT` で起動している。Python の `-c` 実行では空文字が現 cwd を指すため、repo root は引き続き import path に入る。

(ii) 一次資料: `test_pytest_failure_digest.py:335-347`、`test_pytest_failure_digest.py:453-461`。

(iii) 成果物への影響: A10 の plain-runner 条件を実証しておらず、テスト名・コメントと実際の検査条件が乖離している。

(iv) 対処案: `_run_bounded_process()` に `cwd` 引数を持たせ、当該 probe は一時ディレクトリで起動し、`PYTHONPATH` も除去する。

## 5 — nit : M2/M7 の変異登録はまだ一意な一行変異になっていない

(i) M2 の「tail slice を head slice へ」は現コードに slice がなく、`reversed(value)` の一行変更では同じ意味の変異にならない。M7 は `report.failed` 条件が `conftest.py:334` と `conftest.py:340` に二箇所ある。M3 は期待赤になるが、consumer の抽出集合ではなく excerpt の literal assertion が主な検出経路である。

(ii) 一次資料: `s6-fix-rulings.md:123-135`、`conftest.py:333-342,405-430`、`test_pytest_failure_digest.py:922-940`。

(iii) 成果物への影響: M2/M7 を kill 済みと記録すると、実在・一意な変異に対する検出力証拠にならない。

(iv) 対処案: M2 は具体的な一行変異（例: `reversed(value)` を forward iteration に変更）へ再登録し、M7 は `runtest` または `collectreport` の対象行を明記する。実変異走行は親の受入工程で行う。

## 総括

判定は **NO-GO**。

未閉鎖の must-fix は次の 4 件。

1. F11 の repo 外書込み保証。
2. conftest コピー sha 検査の恒真化。
3. F3 の manifest 再計算による非 O(n) 性。
4. plain-runner root 不在検査の条件誤り。

加えて、M2/M7 の変異登録は修正してから検出力証拠として扱うべきである。実走は制約どおり実施していない。