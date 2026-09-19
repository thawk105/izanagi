## 所見

以下、`C/V/F/R/A/P/T/O` は plan 冒頭のファイル略号を使う。静的検査のみで、pytest・性能測定・ファイル変更は行っていない。

1. **severity: must-fix — 対象: brief の受入配置前提、P6、U3/A・U4/T**

   **「real-repo 登録 node はすべて1 worker直列」は現 tree では成立しない。**
   [conftest.py:2161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-worker-time-trim/orchestrator/tests/conftest.py:2161) は `REAL_REPO_PROCESS_MEMO_NODES` 以外の `@real-repo` を除去し、`:2273` が collection 後段でこれを実行する。`:1783–1832` はその後の work unit を台帳時間で並べ替える。

   - T1259 は `:670–701` の例外集合に全30関数が入り、51 node が同一 group に残る。
   - codex_ab の `benchmark_snapshots` 直接 consumer は23関数・台帳29 node。その集合は例外に入らず、分散し得る。既定 hold 2 node を除けば27 node。
   - floor の snapshot 対象9関数・11 nodeは、この登録による同一 worker化の対象ではない。

   したがって、**T1259の跨 worker共有は重複構築を削れない一方、codex_abは削減候補になり得る**。48 workerという総数だけから構築回数を決めてはならない。台帳による module 間の並べ替えもあるため、worker IDに加え、fixture の実際の生成回数を記録する必要がある。

2. **severity: must-fix — 対象: U2、U3/A、U1 の削減式**

   **共有構築で消えた計算時間と、JUnitの worker経過秒は別である。**
   先例 `_T080SharedBases.get`（`test_s8b_oracle_driver.py:923–954`）は排他ロック内で構築する。他 workerの待機も setup/call時間に入る。

   U2の `15.6×(W−1)` は、少なくとも次の式に直す必要がある。

   ```
   純削減 = 省けた各workerのdigest時間
          − 共有構築の待機合計
          − 共有値の読込・公開・削除費
   ```

   仮に11 workerが同時に到着し、構築15.6秒を10 workerが丸ごと待つなら、名目156秒の削減は待機156秒で相殺される。現実の並行I/O競合によって結果は変わるが、**重複回数だけでは正の worker秒削減を保証できない**。

3. **severity: must-fix — 対象: U3/R の fixture設計**

   `R:58` の `_clean_runner_env` は function scopeで、function scopeの `monkeypatch` に依存する。plan の「module fixtureを `_clean_runner_env` に依存させる」をそのまま実装すると **ScopeMismatch** になる。

   最初は対象testのfunction fixtureで `R:81` の小repoを作るだけでよい。19 nodeで省く主費用は大repoのfingerprint約200秒であり、小repo構築を19回から数回へ減らすことは二次的である。module baseを採るなら、module構築のGit環境清浄化と、functionごとの `_REPO` 注入を分ける必要がある。

4. **severity: should — 対象: U1 の session共有必須という判断**

   `s8b_v2_freeze_fixture.py:92–129` はfork子を `os._exit` させるが、**disk memoが必要なことから、全worker共有＋flock＋最後の退出者削除が必須とは導けない**。親workerで所在を確保したworker専用disk memoも、子の終了を越えて再利用できる。

   コピー量は現物を数えた。保存されていた次の完成fixtureでは、

   ```
   /tmp/pytest-of-tanab/pytest-1967/popen-gw5/
     test_source_blob_mismatch_reje0/baseline/repo
   ```

   **280 regular files、1,138,165 bytes、symlink 0**。mutation側も280 files、1,138,130 bytesだった。内側ccbenchを含み、856 MBのScratchTreeとは約750倍違う。

   ただしこれは **F:1101の切断点そのものではなく、生成revisionも未照合の残存標本**。コピー費が十分小さい可能性は高いが、秒数の証明ではない。親は切断点で全file数・bytes・copy＋index refresh時間を測るべきである。

   worker専用memoの利得は概ね `Σ(Nkey−使用worker数key)×構築費`。48 workerでkeyが分散すれば利得が小さくなるため、「局所memoで大半が取れる」とも現時点では断言できない。まず両方式の構築回数を比較し、全worker共有の追加利得が小さければ削除する。

5. **severity: should — 対象: U4/P の採用判断**

   `P:759/791/821` は **3＋3＋1＝7 tree**。段1の該当call合計は **43.38秒**（19.47＋19.35＋4.56）、台帳は **109秒**（45＋45＋19）。briefの「3×3 tree ≈20秒」は両方誤っている。

   3 nodeが別workerならmodule共有の削減は0。全て同workerでも理想上限は7→3 treeの4構築分で、pristine保持・copy・teardownが残る。しかも `P:782` は `validate_exact_replacements` を明示的に検査している。完成prepared treeの共有によって、この実行を消してはならない。

   **現在の配置で再利用が確認できなければ不採用**とし、session共有へ増築して追わない判断が妥当。

6. **severity: must-fix — 対象: P6、現存A/B script**

   親の [`ab_compute.sh`](/home/SFC/tanab/.claude/jobs/28fa456a/tmp/ab_compute.sh) は、planの「6 file同走」と異なり、各fileを別々に起動する。また、

   ```
   rm -rf /tmp/pytest-of-"$(id -un)"
   ```

   は当該run以外の残骸・並行作業まで削除し得る。run固有の `TMPDIR` と `--basetemp` 配下だけを片付ける形に変える必要がある。

   `PYTHONDONTWRITEBYTECODE=1` は**既存pycの読込みを禁止しない**。同サイズ・同mtimeのmutationには、各走の空の `PYTHONPYCACHEPREFIX` も必要。なお現scriptは実際には **AB / BA / AB** で、brief記載のABABABとも異なる。

7. **severity: should — 対象: U2の変異matrix**

   planの2変異は production `s8b_floor_campaign.py:7605,7611` のcertificate検査である。変更予定の `O:604–620` のcache条件・keyを直接攻撃しないため、両変異のkill集合一致だけでは共有digestの健全性を示せない。

   既存cache条件に対する「dirtyでもcacheを使う」「blob SHAをkeyから落とす」等を追加診断し、`C:1834,1901–2098` の同サイズ変更・復元・fallback検査が新旧で同じ失敗集合になることを確認する。新経路が自己検査から明示的に除外される設計なら、その経路の等価性確認も別途必要である。

## 受入下の削減見積り表

数値は削減保証ではなく、profile単価を使った上限・条件式。共有待機を必ず差し引く。

| 項目 | 段1見積り | 受入での見積り | 根拠 |
|---|---:|---|---|
| U1 emitter構築 | V全体825秒の一部 | key別の再構築数次第。`Σ(N−構築回数)×切断前費用 − copy/refresh/待機`。945秒全体を削減対象にできない | F:1085–1101、V:215。fork profileはwaitpid中心で構築内訳未取得 |
| U2 初回digest | `15.6×(W−1)` | 対象11 nodeだけならW≤11、名目上限156秒。48倍換算の733.2秒は不可。待機で0以下もあり得る | C:13795–14632、O:604–620 |
| U2 ignore解析 | 規則照会1.4秒/回の一部 | 未確定。1.4秒全体を削れない | O:144–180は解析のみ。Git照会・存在確認は残す |
| U3/R 小repo | 約200秒の大部分 | 19 nodeの大repo fingerprintを置換するため有望。単独profileの目安は19×7.4＝140.6秒から小repo費を引く。台帳544秒全体は不可 | R:1837、tools/run_tests.py:2540,2567 |
| U3/A snapshot共有 | setup134.65秒 | 既定active直接consumerは27 node。全て別workerなら最大27構築。base部分だけの名目削減は `3.4×(27−1)=88.4秒`。derive共有分はcopy後verifyを差引く | A:860–960、conftest.py:2161 |
| U4/P module共有 | brief約20秒 | 配置により0。最良でも7→3 tree、最大4構築分。台帳109秒全体は不可 | P:759,791,821 |
| U4/T session共有 | 単独setup約10秒 | **受入の重複構築削減は0**。現行group内でmodule templateを共有済み | T:73–97、conftest.py:670–701 |
| floor二乗回復 | 約90×5.8秒 | 本waveの局所fixture変更による主費用削減は見込めない | profile9.9秒中9.1秒がproduction回復 |
| codex verify | 46.2秒/代表node | 検証呼出しを維持する限り主費用は残る | Aのverify test、tools/codex_reasoning_ab.py:11646 |

## 削除候補

追加行数は実装前の設計概算であり、diff実測ではない。

| 案 | 削減／追加行数の目安 | 新しい失敗の形・判断 |
|---|---|---|
| T1259 session共有 | 0秒／約70–120行 | lock・残留dir・寿命管理だけ増える。削除 |
| Pの跨worker共有への拡張 | 未確定／100行以上 | prepared状態漏洩、cleanup、pristine管理。削除 |
| U1全worker共有を最初から必須化 | worker専用案との差分未確定／管理部約80–140行 | forkによるlock所有権、途中失敗、終了順。worker専用disk案約30–60行と比較してから |
| Rのmodule base管理 | function構築との差分は小さい／約30–60行 | ScopeMismatch、環境汚染。まずfunction小repo案約10–25行 |
| U2 digest共有 | 名目0–156秒から待機等を控除／約80–140行 | dirty誤判定、部分公開、cache読込失敗。正の純利得がなければ削除 |
| Aの完成素材共有 | 符号未確認／約120–200行 | 絶対path、submodule gitdir、oracle再束縛。copy＋再verify込みで採否判断 |

flockを使うだけで直ちにscope外ではない。しかし、汎用cache API・複数helper共通の寿命管理・新conftest機構へ広げれば「新framework」に踏み込む。production修正、新gate、group変更、launcher変更は本waveでは採らない。

「残る律速」への反証結果は次のとおり。

- **floor二乗回復**：代表profileのsubprocessは18回・0.03秒、fsyncは0.06秒。authority構築を共有しても主要9.1秒は消えない。
- **floor clone＋scan**：`C:15749–15760` のcloneは型(iv)の候補であり、完全に対象外とは言えない。ただしscan26.8秒は残る。profile全体39.3秒との差12.5秒にも他費用が含まれ、copyは無料でない。「copy≈clone」は未測定として訂正する。
- **codex verify**：判定memoは不可。`A:1678` のmanifest構築はpath/hash連鎖を持つため、無条件コピーも不可。構築部分が全く削れない証明ではないが、46.2秒のverifyを削減額に入れない判断は正しい。
- **Pのrun_tests subprocess**：`P:1141–1185` は別tree内のmutationを別interpreterで読み、rcと「1 failed, 7 passed」を検査する。親processでの `pytest.main()` はimport済みmodule・plugin・環境を共有し、同じ検査ではない。不採用は妥当。
- **T1259**：今回は無変更でよい。ただし台帳550秒を「飽和が原因」と断定する証拠はない。

## A/B と変異の実行案

A/Bはledger・scheduler・hold条件を固定し、6 fileを一度に渡す。最小3対なら **AB / BA / AB**、順序を完全に均衡させるなら4対 **AB / BA / BA / AB**。双方の予備走を除外してから測る。

以下は親が計算ノードで使う一時scriptの骨格であり、repoへ追加するlauncherではない。

```python
import json, os, pathlib, shutil, subprocess, tempfile, time

# A/B: 共通production revision、許可されたtest/helper差分だけのworktree
roots = {"A": pathlib.Path(A), "B": pathlib.Path(B)}
files = [f"orchestrator/tests/{name}" for name in SIX_FILES]
results = pathlib.Path(RESULTS)
results.mkdir(parents=True, exist_ok=True)

def run(label, side):
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="trim-ab-", dir="/tmp"))
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_XDIST_TESTRUNUID", None)
    env.update(
        TMPDIR=str(scratch),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPYCACHEPREFIX=str(scratch / "empty-pycache"),
        IZANAGI_TASK_RUN_AUTO_RECORD="0",
    )
    command = [
        "python3", "-B", "tools/run_tests.py", *files,
        "-n", "12", "--dist=loadgroup", "-p", "no:cacheprovider",
        "--basetemp", str(scratch / "pytest"),
        "-o", "junit_duration_report=total",
        "--junitxml", str(results / f"{label}-{side}.xml"),
        "-q", "-rN",
    ]
    started = time.monotonic()
    with (results / f"{label}-{side}.log").open("w") as log:
        rc = subprocess.run(command, cwd=roots[side], env=env,
                            stdout=log, stderr=subprocess.STDOUT).returncode
    test_wall = time.monotonic() - started
    # ここで scratch のbytes・file数・残留共有dirを記録する。
    shutil.rmtree(scratch)  # 自分が作成したrun rootだけ
    record = dict(label=label, side=side, rc=rc, test_wall=test_wall,
                  wall_with_cleanup=time.monotonic() - started)
    with (results / "runs.jsonl").open("a") as out:
        out.write(json.dumps(record) + "\n")
    if rc:
        raise RuntimeError(record)

for side in ("A", "B"):
    run("warmup", side)
for pair, order in enumerate(("AB", "BA", "AB"), 1):
    for side in order:
        run(f"pair-{pair}", side)
```

補足条件：

- `TMPDIR`外の固定scratch rootがあれば事前に所在を確認し、当該runの生成物だけを追跡する。
- ScratchTreeだけで **856 MB×12＝10,272 MB、28,158×12＝337,896 files**。shared base、pytest保持物、内側process分をさらに加える。開始・終了の空きbytes/inodeと実際のpeakを残す。
- page cache dropはしない。予備走は「完全cold」化ではなく、開始条件の偏りを減らすものと記す。
- file別・6 file合計のsetup/call/teardown秒、外側wall、cleanup込みwall、共有構築数・copy数・待機秒を残す。
- 3対の対差は中央値・全値・幅を示す。3対全て同符号でも、独立対の両側符号検定はp=0.25であり、強い統計的主張はできない。差が振れ幅以下なら「未分離」と報告する。
- **12 workerの比率を48 workerへ外挿しない。** 受入receiptの配置・fixture生成回数と整合させる。

台帳再生成は、許可された6 file＋helperを越え、`conftest.py:1783` の順序と `tools/acceptance_shards.py` の割付入力も変える。**本waveのA/B中・実装commitでは更新しない。** 全走receiptを保存し、別の台帳更新として扱う。

変異費用は段1の外側wall（V75、C115、R25、A58、P72秒）で概算すると：

| 対象 | 変異数 | 修正前後の両走 |
|---|---:|---:|
| U1/V | 3 | 450秒 |
| U2/C | 2 | 460秒 |
| U3/R | 2 | 100秒 |
| U3/A | 2 | 232秒 |
| U4/P | 2 | 288秒 |
| **合計** | **11** | **1,530秒＝25.5分** |

無変異の新旧controlを各file一回加えると **37分**。F・holdout・oracleの互換確認、追加cache変異、A/B、受入全走は別費用であり、mutationが早期失敗する分は事前に割り引かない。

最小構成は、採用を **U1＋U3/R** に絞れば、提案済み5変異の両走550秒＋control200秒＝**12.5分**。各変異の新旧pairを小さい実験単位に分ける。U2/A/Pを変更するなら対応matrixを復活させ、予想kill nodeだけへの縮約で「file全体のkill集合一致」と報告してはならない。

queue状態・job walltimeは未確認。親は投入前に確認し、待ち時間を上記実行時間と区別する。全実験を長時間の単一jobへ詰め込む案は、逐語の時間規律との整合を先に解決する必要がある。

## 親 brief への所見

- **受入groupの説明が古い。** `conftest.py:2201–2220` だけでは、後段のsuffix除去を見落とす。
- **codex setup「13 worker」は誤り。** durationsには10.88–11.35秒のsetupが12行、合計134.65秒ある。
- **floorは9関数・11 node。** `C:14597` の3-way parametrizeを展開すると、planの9組とdurationsの11 nodeは矛盾しない。公式testのsnapshot呼出しは実行数で22回。
- **Pの対象費用は約20秒ではなく43.38秒、treeは9本でなく7本。**
- **builderの決定性実測は未成立。** `stage1p/profile_g1.log` はmachine-pin不一致で最初の構築中に失敗している。2回のHEAD一致・bytes一致の根拠にはできない。
- **台帳と現collectionが異なる。** floorは台帳528 node、段1は532 node。対象6 fileの台帳合計は5,722.041秒だが、同一node集合・同一fixture実装の比較とみなしてはならない。
- **T1259の550秒の原因は未同定。** 台帳はphase別でなく、現行module fixture＋groupと単独12秒から「単一worker直列＋飽和」とは結論できない。
- **P2不採用はplanが正しい。** module baselineへの置換は変更の帰属だけでなく、後続testの成功・失敗条件も変える。

## 総括

最優先は受入group前提の訂正と、共有待機を含む削減式への修正。
U3/Rは小repoのfunction構築から始め、U1はworker専用disk memoと全worker共有を比較する。
T1259共有は削除、P共有は実配置で再利用がなければ削除。
U2/Aは構築回数ではなく、copy・再verify・待機・cleanup込みの純利得で採否を決める。
現時点では、受入48 workerで削れる秒数の確定値はない。