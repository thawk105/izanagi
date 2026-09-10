静的レビューのみ実施し、pytest は実走していない。単独段 dispatch の射影外だった `test_pytest_collection_config.py`、`test_official_perf_closure.py`、`test_hooks.py`、runbook、凍結 manifest、driver ID oracle は直接読まず、段4裁定に再掲された検索結果までを根拠にした。

## 受入全走で失敗しうる経路

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| 新2 node は受入台帳にないが、未知 node を拒否する経路はない。両名の実検索は0件で、T316台帳の `test_eexist...` と `test_identity...` の間にも存在しない。 | refuted | [ledger:20370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/acceptance_duration_ledger.json:20370)、[ledger:20371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/acceptance_duration_ledger.json:20371)、[conftest.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1571)、[conftest.py:1631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1631)、[conftest.py:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1652) | 未知 node は既知 unit の既定 cost で並べられ、収集対象から落ちず、台帳だけを理由に受入失敗しない。 | 台帳追加は不要。 |
| 台帳自体は `schema_version=1`、`unit=seconds`、宣言22157件と実辞書22157件が一致する。 | refuted | [ledger:22161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/acceptance_duration_ledger.json:22161)、[conftest.py:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:1416) | 今回の非更新によって台帳文書全体が無効化される経路はない。 | なし。 |
| helper は `_` 始まり、追加 node は `test_` 命名、`_run()` より前にあり、plain runner にも含まれる。`os` と `subprocess` は標準ライブラリ群の順序に入り、どちらも使用済み。 | refuted。ただし射影外の収集 meta-test 本文との直接照合は未検証 | [test_t316_sandbox_probe.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:11)、[同:1406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1406)、[同:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1526)、[同:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1545)、[同:1560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1560) | 静的な命名・import・plain-runner 結線による失敗は見当たらない。 | なし。 |
| `git` が PATH にない環境では意図的に assertion failure になる。Gitの非0終了や60秒 timeout も捕捉されず node を失敗させる。 | real、環境条件付き | [test_t316_sandbox_probe.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1430)、[同:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1452)、[s4-adjudication.md:104](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:104) | 正規 runner の計算ノード側 PATH または Git が壊れていれば、束縛検査より前に受入が失敗する。これは段4で指定された fail-closed 挙動。 | 実装変更なし。正規 runner の Git 可用性を前提条件として扱う。 |
| [手順漏れ] helper 1回には60秒上限の Git 呼出しが5本あり、2 node 合計では個別上限の総和が600秒になる。conftest が記す受入 ceiling は5分であり、複数コマンドが上限直前で成功する環境には aggregate budget がない。 | real、条件付き。通常時の実時間は未検証 | [test_t316_sandbox_probe.py:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1452)、[同:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1493)、[conftest.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:925) | 極端に遅い一時 filesystem では、node 単体が受入全体の時間枠を消費しうる。 | 仮想 gate は追加しない。段6の正規受入で実時間が問題化した場合だけ timeout 値を裁定する。 |

## 並行実行と汚染

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| 新 node は conftest の real-repo inventory に存在せず、module-level `xdist_group` もない。したがって別 worker へ並列配置できるが、各 node の `tmp_path` と process 環境は worker ごとに分離される。同一 worker 内では test は逐次実行され、monkeypatch teardown が環境と hostname を復元する。 | refuted | [conftest.py:2041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:2041)、[test_t316_sandbox_probe.py:1406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1406)、[同:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1515) | PBS/Git環境変数や `socket.gethostname` が後続 test へ残る経路はない。 | xdist group 追加は不要。 |
| Git環境は最初の Git 起動前に削除・上書きされ、global/system config を遮断する。commit identity と署名抑止は `-c` の一回限りで、全操作は `git -C <tmp repo>`。 | refuted | [test_t316_sandbox_probe.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1410)、[同:1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1426)、[同:1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1466) | 親 worktree、Git global config、process cwd を変更しない。 | なし。 |
| [計測汚染] `Popen`、`os.chdir`、保持 fd は追加されていない。各 `subprocess.run` は同期実行かつ `capture_output=True` で、通常終了時に pipe を閉じる。空 template と `commit.gpgsign=false` で hook/gpg 子 process も抑えている。 | refuted | [test_t316_sandbox_probe.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1434)、[同:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1452)、[同:1471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1471) | 正常経路で Git process、pipe、cwd、永続ファイルが他 test に残る証拠はない。並列時の直接 Git process は新2 nodeぶんまで。 | なし。 |

## login node と計算ノード

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| ambient hostname 差は helper が `probe.socket.gethostname` と nodefile を同じ固定名にするため結果へ入らない。conftest の site fixture は `site_policy.socket` だけを差し替えるので競合もしない。 | refuted | [conftest.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:239)、[test_t316_sandbox_probe.py:1511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1511)、[同:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1515) | login/compute の hostname だけを理由に正負例が変わる経路はない。 | なし。 |
| `TMPDIR` は conftest が上書きせず、`tmp_path` の配置は runner 環境に従う。`/scr`、`/tmp`、Lustre のいずれでも通常の mkdir/write/Git が使えれば意味は同じだが、無効な `TMPDIR`、容量不足、権限不足、Git不在では失敗する。 | real、環境条件付き | [conftest.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:9)、[同:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/conftest.py:24)、[test_t316_sandbox_probe.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1432) | 正規 runner の node-local temp/Git 前提が違えば、host固定とは別に受入結果が変わりうる。 | コード側の場所分岐は追加しない。runner の既存 temp/Git 契約に従う。 |
| [テスト代表性] この2 node は Python preflight の比較先を検査する unit test であり、実 PBS spool、shell先行関門、計算ノード上の命令実行までは代表しない。 | real、既知限界 | [s4-adjudication.md:14](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:14)、[s5b-author-out.md:24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:24) | 今回の成果物が証明するのは preflight 時点の spool と worktree `.pbs` の bytes 一致までで、実行命令列の同一性ではない。 | 既知限界として維持。追加の統合 test を本 wave に混ぜない。 |

## consumer 波及

波及は次の3経路である。

- probe の bytes変更 → Git blob/self hash変更 → 将来 receipt の `.py` hash変更 → admission、driver ID、performance inventory、hooks/runbook 投影。
- 比較先変更 → `main()` / `run_probe()` / PBS job bodyからの preflight → 受理・拒否結果と receipt 発行。
- test 2 node追加 → collection node数変更 → duration ledger schedulerとcollection meta-test。

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| `test_official_perf_closure.py`、`test_hooks.py`、runbook、凍結 manifest、driver ID の独立 oracleを含め、旧 `.py` bytesまたは旧blob hashへの固定参照が原因で実際に失敗する consumer は、射影内証拠では無し。親の repo 全体検索は旧SHA-256・旧blob SHAとも0件、凍結 test のT316参照も0件としている。 | refuted。ただし各 consumer 本文の直接確認は未検証 | [s4-adjudication.md:20](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:20)、[同:38](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:38)、[同:40](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:40)、[同:24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:24) | 既存 checked-in oracle、hooks、docs、manifestを今回のbytes変更だけで更新する根拠はない。将来 receipt の `.py` hashだけは新bytesになる。 | consumer更新なし。 |
| 既存receiptでは spool hashと `.pbs` hashが既に同値であり、今回変更したのは比較対象の選択であって hash key 集合ではない。 | refuted | [s4-adjudication.md:42](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:42)、[s5-impl.diff:193](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:193) | 過去 receipt の意味やschemaを壊さず、正しい `.pbs` spoolの将来実行だけが訂正される。 | 既存receiptの書換え不要。 |

## scope 逸脱とプラン v2 照合

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| 名前付き `_RUNTIME_PBS_RELATIVE_PATH` を tuple 直前に追加。 | refuted | [s5-impl.diff:184](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:184) | 指定どおり比較対象を名前で束縛する。 | なし。 |
| tuple 3番目だけを定数参照へ置換し、値と順序を維持。 | refuted | [s5-impl.diff:185](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:185) | bound path集合は不変。 | なし。 |
| `repo_pbs` の参照先を新定数へ訂正。 | refuted | [s5-impl.diff:193](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:193) | 本題の `.py` 対 `.pbs` 取り違えを訂正。 | なし。 |
| 例外文言、hash key集合、他関門は変更していない。 | refuted | [s5-impl.diff:199](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:199) | consumer schemaと診断感度を維持。 | なし。 |
| 保証範囲commentは追加していないが、段4では任意。 | refuted | [s4-adjudication.md:74](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:74) | 成果物影響なし。 | なし。 |
| helper は `_run()` の直前。 | refuted | [test_t316_sandbox_probe.py:1406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1406)、[同:1560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1560) | plain runnerを保ったままfixtureを共有。 | なし。 |
| 指定13 Git変数を削除し、global/system config、identity、署名、templateを隔離。 | refuted | [test_t316_sandbox_probe.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1410)、[同:1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1466) | ambient Git設定によるfixture変形を抑止。 | なし。 |
| Git 5呼出しすべてに `-C` と `timeout=60` がある。 | refuted | [test_t316_sandbox_probe.py:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1452)、[同:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1493) | cwd汚染と無期限停止を抑える。 | aggregate budgetの条件付き所見のみ前節参照。 |
| 5 path は相異なるbytesで、`.py != .pbs` とclean statusをassert。 | refuted | [test_t316_sandbox_probe.py:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1436)、[同:1507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1507) | 変異M1/M2の単一理由性を保つ。 | なし。 |
| spool/nodefileはrepo外、hostnameとnodefileは一致、job IDは規定文字集合内。 | refuted | [test_t316_sandbox_probe.py:1509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1509)、[同:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1513)、[同:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1518) | 前段関門による偽の失敗理由を排除。 | なし。 |
| expected rootと関数引数は同じresolve済み `repo_root`。 | refuted | [test_t316_sandbox_probe.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1432)、[同:1520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1520)、[同:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1533) | root-location gateの混入を防ぐ。 | なし。 |
| 正例はdictとspool/`.pbs`両hashを検査。 | refuted | [test_t316_sandbox_probe.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1526) | 正しい比較対象とreceipt値を固定。 | なし。 |
| 負例はspoolを`.py` bytesへ変え、例外型と完全一致文言で受ける。 | refuted | [test_t316_sandbox_probe.py:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1545) | 比較消去M3と診断変更M4を露出。 | なし。 |
| Git不在をskipせずassert。 | refuted | [test_t316_sandbox_probe.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1430) | runner前提違反を明示的に失敗させる。 | なし。 |
| 既存test/helper/`_run_injected`/旧monkeypatchは差分上変更なし。 | refuted | [s5-impl.diff:15](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:15) | 既存oracleへのscope波及なし。 | なし。 |
| 禁止対象は変更されず、差分の file header は許可された2件だけ。追加の `GIT_DEFAULT_HASH=sha1` はtest-localでmonkeypatch復元され、本題のfixture決定性の範囲内。 | refuted | [s5-impl.diff:1](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:1)、[同:176](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:176)、[test_t316_sandbox_probe.py:1428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1428) | production挙動や禁止成果物を変更しない。 | なし。 |
| [ドリフト] shell `BOUND_PATHS` に `condition_meaning_gate.py` がなく、同fileがPython側dirty検査前にimportされうる既知問題は残る。ただし段4が本waveのscope外と明示したため、プランv2の実装漏れではない。 | real、scope外・裁定候補 | [s4-adjudication.md:53](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:53) | dirtyなcondition gateが両束縛関門より先に実行されうる。今回の`.pbs`比較訂正では解消しない。 | 段4記載の(a) shell束縛へ追加、(b) import遅延、(c)既知限界化から別裁定。本waveでは変更しない。 |

## 実装子報告の裏取り

| 所見 | real か refuted か | 根拠 file:line | 成果物影響 | 提案 |
|---|---|---|---|---|
| 「編集は許可された2 fileだけ」は、渡された実装差分について確認できる。 | refuted | [s5-impl.diff:1](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:1)、[同:176](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:176) | 禁止fileへの差分混入はない。 | なし。 |
| 「commit/add/stash/branch操作なし」は、段5後のgit log/status/reflogやtool記録が射影されていないため裏取り不能。ソース内の `git add` / `git commit` はtmp fixture repoへの実行であり、この主張とは別。 | 判定不能、未検証 | [s5b-author-out.md:9](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:9)、[test_t316_sandbox_probe.py:1459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1459) | 開発worktreeの履歴操作有無はこのレビュー成果物から証明できない。 | 親が保有する段5のgit監査結果で確認する。 |
| 「制約meta-test全182 nodeがrc=0」は、報告の内訳 `3+24+79+76=182` までは確認できるが、実行logが射影されていないためrcは裏取り不能。 | 判定不能、未検証 | [s5b-author-out.md:18](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:18) | collection・台帳・schedule meta-testの実成否は実装子の自己申告に依存する。 | 段6の正規受入結果を正本にする。 |
| [手順漏れ] repository全体受入とM1〜M5が未実走なのは事実だが、段4はこれらを段6へ割り当てているため実装子の手順漏れではない。 | refuted | [s5b-author-out.md:24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:24)、[s4-adjudication.md:128](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:128) | 段5成果物の欠落ではないが、wave完了判定はまだできない。 | 段6で予定どおり実施。 |

## 総括

scope内の機能欠陥、台帳拒否、xdist汚染、consumerの固定hash破損は静的証拠からは見つからない。

real所見は次の4点である。

- Git/PATH/TMPDIRのnode別前提が壊れた場合の意図的な受入失敗経路。
- Git呼出しの個別timeout総和が5分ceilingを超えうる条件付き時間予算リスク。
- 実PBS統合を代表しない既知の[テスト代表性]限界。
- `condition_meaning_gate.py` の先行importという既知の[ドリフト]。これはscope外裁定候補であり、今回の実装漏れではない。

実装子の「2 fileだけ」は差分から確認できた。一方、履歴操作なしとmeta-test 182 nodeのrcは、射影された証拠だけでは未検証である。