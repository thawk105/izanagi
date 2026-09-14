## 総括

A は、**fixture の入力膨張と、並列走での memo hit 0 回**を特定した。古い約36MBに対し、実測 tip のコピー元は tracked 分だけで約640MBある。ただし288〜310秒の操作別内訳は未特定。  
B は、**result 公開後の directory fsync**と、隔離 supervisor が回収しない孫 process が有力な調査先。T080 の後始末を48本と数えるのは誤りで、当該走は11本。  
C は、「毎走全部」の一般的な緩和を承認した空白ではない。条件付き実行・定期走への移行は逐語上の未裁定部分だが、現行の全集合検査を変更するには人間裁定が要る。  
D の最大の実損は pytest 後の終了待ちで、996124 では少なくとも**2,328秒**。修正箇所はまだ確定していない。  
資料の「終了後約76秒」は誤り。生データでは**開始側55.74秒、dispatch 49.17秒、実行313.61秒、終了側20.01秒**。  
検査を変えずに5分へ入ると、現時点で秒数まで裏付けられる短縮案はない。

## A. 15〜22 秒と 290〜310 秒の差の行き先

**36MBの仕事を同じ条件で20秒から300秒へ遅くした、という比較ではなかった。**

`git log -S` で説明の導入を確認した。commit `6d3f2d21a`、2026-07-26 の本文は、次の条件を明記している。

> 「1 回 15.5 秒」  
> 「コピーは 0.3 秒 (実測、tmpfs)」  
> 「実測 (ログインノード、単一 process、`-k t080` の 14 本): 155 秒 → 69 秒」

現行の [helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:868) はこの数字を保持している。一方、Git tree の blob サイズ集計は以下だった。これは再測定ではなく、記録済み tree の棚卸しである。

| コピー元 | 2026-07-26：件数／bytes | 実測 tip `abbef52d`：件数／bytes |
|---|---:|---:|
| `orchestrator/` | 248／5,077,675 | 1,029／38,569,275 |
| `output/` | 1,846／19,349,699 | 21,959／601,328,932 |
| 合計 | 2,094／24,427,374 | 22,988／639,898,207 |

コピー元の tracked blob は**件数11.0倍、bytes26.2倍**。実測 tip の `output/insights` が18,199件／396.2MB、`output/env` が3,246件／195.4MBを占める。`.git`、submodule、untracked、生成物を含む完成 fixture の実サイズとは区別する。

実装の費用経路は次のとおり。

- [1001行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:1001)：`orchestrator/` 全体をコピー。
- [819行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:819)：Git-visible な `output/` をコピー。tracked はもちろん untracked regular file も対象。
- 同 file 1064行：`git submodule add`、1069行：`git add -A`、1070行：commit。
- [1189行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:1189)：子 Python で draft、validate、finalize、verify、public gate。
- [904行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:904)：さらに完成 base を各 node へ実体コピー。

膨張した入力はコピー後も費用になる。[migration の検索呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/campaign/t080_freeze_migration.py:1889) は全 repository を再検索する。draft 後、明示 validate、finalize 内の validate、finalize 後だけで、この検索を**少なくとも4回**呼ぶ。実検索は [s8b_holdout_freeze.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/campaign/s8b_holdout_freeze.py:618) で対象 file ごとに存在確認・読出し・decode を行う。

過去にも同型があり、commit `b08ce1aaf`、2026-07-27 は ignored build cache のコピーを修正している。現行 [857行の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:857) は、その時点で15〜22秒が121.7秒へ増えたと明記する。ただし今回確認した600MBは tracked 分であり、その修正では除かれない。

**当該1走の build／copy 回数**

[consumer 固定テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:908) と呼出し引数から、正常 consumer は6 function／11 node、key は5種類。

| key の相違点 | node数 | 当該走の build数 |
|---|---:|---:|
| 全引数既定 | 7 | 7 |
| `distinct_basis_blob=True` | 1 | 1 |
| `r_trailer="AI-Agent: codex"` | 1 | 1 |
| `extra_r_path=True` | 1 | 1 |
| `issue_receipt=False` | 1 | 1 |
| **合計** | **11** | **11** |

worker の名前との対応表は成果物にない。ただし**11件が互いに別 worker だったことは時間から確定できる**。

- [shard-0 の junit.xml](/work/1/SFC/tanab/.izanagi-acceptance-shards/2f9872c56f62324056496756037371b4/shard-0/junit.xml) では、10件が287.973〜310.177秒、残る1件が69.788秒。
- 最小の2件でも357.761秒あり、全 worker の実行窓313.609秒を超える。同じ worker がこの2件を順次実行する割付は成立しない。
- したがって process 内 memo の共有は起きず、**build 11回、memo hit 0回、完成 base の copytree 11回**。
- build 内の2本も含めると、対象 consumer に由来するトップレベル `copytree` 呼出しは**33回**。境界拒否テストは build 前に止まり、この数を増やさない。

呼び手にも追加費用がある。例えば `ccbench-current` は [1459行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:1459) 以降で held／released の検証と submodule 変異を行う。303.810秒の正例も helper 後に複数回 verify／gate を実行する。**JUnit の node 所要を helper 単体の所要とは呼べない。**

TMPDIR についても資料の引用範囲が不十分だった。[conftest.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/conftest.py:12) は、計算ノード bnode041 の `/tmp` が **xfs**、5.6倍差は **pegasus02 の測定**と明記する。当該走は bnode061 で、ログの fixture path は `/tmp/pytest-of-tanab/...`。bnode061 の filesystem と当時のI/O待ちは未確認なので、5.6倍を転用できない。

**判定：入力膨張と memo 不発は特定済み。約280秒の操作別配賦は未特定。検出力を維持したまま除去できる欠陥だとも、本質的に300秒必要だとも、まだ断定できない。**

## B. job が終わらない経路の候補

**最初に疑う箇所は、JSON公開後にも残る fsync である。**

1. **result 公開後の directory fsync**

   [_write_result_replace](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/dispatch_compute.py:660) は、677行で `os.replace`、679行で `_fsync_dir` を呼ぶ。[765行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/dispatch_compute.py:762) の `os.fsync` には timeout がない。

   従って、**完全な result.json が読めても、この関数が戻ったとは言えない**。CPUが増えない観測とも矛盾しない。ここで停止した証拠はまだない。

2. **隔離 supervisor が待つのは直接の子だけ**

   [bootstrap 316行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/dispatch_compute.py:313) は `waitpid(child_pid, 0)` だけを行う。[_run_isolated_child](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/dispatch_compute.py:1080) の unshare は user／mount namespace で、PID namespace や子孫全体の終了処理を持たない。

   したがって直接の runner が終了しても、残った孫 process をこの関数は回収しない。result の正常な `stage="child"`／`child_rc=1` は、その経路を排除しない。

   一方、`communicate()`、status pipe 読出し、supervisor の `waitpid` 自体で停止した場合は**最終 result 公開より前**になる。当該最終 result がある事実と分ける必要がある。

3. **T080 の atexit と xdist teardown**

   [895行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_s8b_oracle_driver.py:895) の `rmtree` 登録は当該走で11回。48 worker 全員ではない。

   旧説明で仮に48本なら1.728GB／約110,400 file。今回はコピー元の規模から、11 base だけでも約7GB／約25万 file級に `.git` 等が加わる。削除秒数は metadata I/O の実測なしには算定できない。

   さらに「worker atexit は controller の JUnit 出力後」とは一律に言えない。実行時に束縛された xdist は、[sessionfinish で teardown](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:95) し、[10秒 timeout](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/workermanage.py:44) で gateway 終了を待つ。[execnet](/home/SFC/tanab/.local/lib/python3.10/site-packages/execnet/multi.py:229) は timeout 後に直接の gateway process を kill する。workerfinished 通知と process 終了も別である。

   atexit は終了側20秒の候補だが、**数十分の残留を単独で説明した証拠はない**。孫やI/O停止が残る経路との照合が必要。

4. **dispatcher の return 後**

   [_job_run:1669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/pegasus/dispatch_compute.py:1669) の後は `main` から終了へ進む。実ジョブの [dispatch.sh](/work/1/SFC/tanab/.izanagi-acceptance-shards/2f9872c56f62324056496756037371b4/shard-0/dispatch/shard-0/dispatch.sh) は末尾が `exec` で、後続 shell 処理はない。dispatcher 本体に明示的な thread 作成／atexit 登録は見つからなかった。import 先まで含めた停止原因は未特定。

次の再発時に必要なのは新しい gate ではなく、**停止中 process の読取り**である。

- `result.json` の `stage`、`child_rc`、`hostname`、`pbs_jobid` と更新時刻。
- PBS の Accumulated CPU Time、Elapse、および `ps` の PID／PPID／SID／STAT／WCHAN／args。
- 生存 PID の `/proc/<pid>/syscall`、`stack`、`fd`、`status`、`cgroup`。fsync 中なら FD の行先が submission directory か確認する。
- 各 thread の `/proc/<pid>/task/<tid>/wchan`。join／futex 待ちとI/O待ちを分ける。
- 孤児が残る場合、その namespace の `/proc/<pid>/mountinfo`。TMPDIR の filesystem もここで確認する。

## C. 既裁定が塞いでいるもの / 空白

**D1620：時計の定義だけから、集合変更の許可は導けない。**

> 「canonical 起動 (Pegasus login、K=3、command 既定の worker 数)」  
> 「最遅 shard の wall (collection 開始から teardown 終了まで)」

この時計は可変集合にも数学的には適用できる。ただし本文は集合を減らす許可を与えていない。さらに D711 は逐語で、

> 「`Σ selected_i == U`、各 count = 1」  
> 「全 shard で `finished_i == selected_i`」

を要求する。**現行の全 collection `U` の一部を走ごとに省いて、同じ受入として扱う経路は塞がっている。** 条件付き実行を認める新しい受入定義は人間裁定の対象。

**D1908：「毎回全 pytest」を追加した裁定ではない。**

> 「受入前に `--repo` を取る checker を叩く義務を `DW-O26` へ足す」

焦点走が参照関係から checker 系 test を拾えない穴への対処である。「repo全体」は checker の走査対象を指す。全テストの毎走義務や、その解除はこの裁定から導けない。

**D1728：禁止理由は、縮小集合による自己証明。**

> 「同じ縮小集合による自己証明」  
> 「費用は正しさ防壁を弱める理由にならない」

直接の対象は collection の自 shard 絞り込み。ただし、縮めた集合から期待値も作って完全性を主張する一般の設計にも、この理由は該当する。あらゆる条件付き実行を逐語で永久禁止した裁定ではないが、

> 「独立な全体集合から導いた期待割付を供給する設計」

が再訪条件で、独立機構の新設も当時却下されている。**費用増加だけでの再訪は塞がっている。**

**D747：削除以外の頻度変更は、列挙して却下していない。**

> 「『価値の低いテストを削除して受入を速くする』は採らない。削除 0 件で閉じる。」

毎走から外す、条件付きにする、定期走へ移す、という文言はない。ただし「書かれていない＝承認済み」ではない。D690 も、

> 「緑のテストの退役はこの決定の対象外」  
> 「別経路 (人間裁定と commit)」

と明記する。**頻度変更は未裁定の空白として提示できるが、自律採用できない。**

加えて D1919 の却下は、

> 「oracle を fixture から test 本体へ移す — 検査の実行回数と適用対象が変わる。」

である。build を跨 worker で共有して production verifier の実行回数まで減らす案も、本依頼の制約下では短縮案に含めない。

## D. 価値を落とさない安い手

**割付と時間分解の前提を二つ訂正する。**

[問題の G6 テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_acceptance_schedule_order.py:720) は、

> `Historical name: process memo and fixture groups stay distinct work units.`

と明記する。名前が古い。worker 単一 unit の束縛は既に解かれている。残る同一 shard の束縛は D1594／D1618 が定めた **跨ホストで local flock が効かない問題への対処**で、緩められない。

また [allocate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/acceptance_shards.py:321) は `weight=len(nodeids)`。7794／7793／7792という件数は均等だが、秒数は均等化していない。

| 案 | 見積り秒 | 根拠の実体 | 規律2・3に触れない理由 |
|---|---:|---|---|
| B の終了残留を修正 | 996124で**少なくとも2,328秒の待ち**が対象。修正後の短縮は未確定 | pytest完了04:40:31→最後の観測05:19:19。result後fsync／残留processを要特定 | 判定・attestation・fsyncを省かず、正常終了できない原因を直す |
| 完成 base のコピーを、対応filesystem上で独立inodeの reflink にする | **未算定**。11回、コピー元約7GB級のデータ複製が対象 | helper 904行。元の0.3秒はtmpfs実測で現条件へ転用不可 | 全bytes、symlink、metadata、破壊的変異の独立性を維持。全verifyを同じ回数実行 |
| 実効TMPDIRが遅いdiskなら、速い局所diskへ置く | **未算定**。5.6倍の転用不可 | conftest 12〜27行。当該bnode061のmount情報未取得 | fsyncを維持し、tmpfs禁止も守る。検査対象・回数を変えない |
| 同一K=3、同一file/group閉包のまま所要で配分する | node時間・残余固定の模型では**最大約3.43秒** | 実行窓313.609−最長node310.177。仕事量均等化だけでは最長nodeが残る | 全集合、fixture scope、RW lock、shard affinityを維持。I/O競合低下による追加効果は未測定 |

**「56%を33%にすれば約100秒縮む」とは言えない。** 仕事量下界は `13075/48=272.4秒` から `23461.8/144=162.9秒` へ下がる計算だが、当該走には310.177秒の単体が残る。負荷低下で単体自身が縮む効果は別途測る必要がある。

**K上限は、単なる未実装だけではない。** 初期実装 `532635b45` が2／3を受理値にし、現行 [launcher:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/tools/acceptance_launcher.py:324) も runner binding のKを1／2／3に限定する。D1103 は当時の根拠を、

> 「K=3 で既に単体テストの床に達している」

と説明する。さらに D1620 が canonical の **K=3を明記**する。K増加をそのまま同じ5分達成として採用できない。物理的に4台を使えないという資源上限は確認していない。

**49.17秒の所在は controller の collection受領～初期dispatch区間。** 現行 [conftest:2325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/conftest.py:2325) と2343行が receipt／oracle environment の prewarm を呼ぶ。D1830 と配線は整合するが、全49.17秒を prewarm と確定する開始終了記録はない。削除・検査後送りは提案しない。

**終了後は20.01秒。** [report.json](/work/1/SFC/tanab/.izanagi-acceptance-shards/2f9872c56f62324056496756037371b4/shard-0/report.json) の境界とJUnitのtimestamp／timeから再計算した。内容は xdist shutdown 等の候補までで未特定。controller の [pytest_unconfigure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/conftest.py:3040) による memo 終了を、そのままJUnit内の20秒へ加算することもできない。

## E. 読めなかった file / 確かめられなかったこと

- 必読2 file は読めた。書込み・pytest・再測定は行っていない。
- 探索した `tools/dev_wave_acceptance_receipt.py` は存在せず読めなかった。実在する `acceptance_launcher.py`、`dev_wave_wait.py` 等へ追跡した。
- T080 のコピー、Git、各scan、呼び手のverify別の秒数は記録されていない。**入力増大だけで全超過秒数を説明したとは主張しない。**
- 当該bnodeのfilesystem、I/O待ち、停止中process／thread、残留孫の有無は未確認。
- 11件の具体的な `gwN` 対応は未記録。ただし互いに別 worker であることとbuild回数は上記の時間制約から確定した。
- 996191の個別成果物は未照合。Bの具体的なresult／PBSログ照合は996124について行った。
- measurements §6 の「最小268.9秒」と「57走すべて300秒以上」は矛盾する。後者を結論の根拠に使っていない。
- 5分達成に必要な短縮量と、候補の実効短縮量は未だ結び付いていない。**検査集合や検証回数を減らして、その不足を埋める判断はしていない。**