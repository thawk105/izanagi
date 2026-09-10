## 総括

plan v1 は正しさ境界を保存しない。**BLOCKER は 3 件**である。  
B1 の「per-run root は lock identity を分断する」という判断自体は正しいが、明示 `/tmp` と自動 Lustre root の混在でも同じ分断が起きる。  
さらに stable root 上の既存 stale prune が別ホストの live session を破壊しうる。  
B3 の real-repo lock 固定 `/tmp` と既存 fstype ガードは保存され、期待値の書換えや skip/deselect は計画されていない。  
B2 は復元設計が不足し、B4 は受領証の環境束縛不足、B5 は実受入 workload での発火証拠不足である。静的検査のみで、pytest や probe は実行していない。

## 所見

### [BLOCKER] B1 は半分だけ正しい。明示 `/tmp` と自動 Lustre の混在で ABA 防壁が分断される

- 場所: `plan-v1.md:281-286`, `plan-v1.md:336-345`, `plan-v1.md:353-364`, `orchestrator/campaign/patchharness.py:113-130`, `tools/mutation_harness.py:2869-2889`
- 内容: per-run root が同じ tree/repo の lock path を変えるという判定は正しい。しかし plan は明示 `TMPDIR=/tmp` を保存し、未設定時だけ stable Lustre root を使う。この二種類の session が同時に同じ tree/repo を触ると、片方は `/tmp/izanagi_apply_*.lock`、片方は Lustre 上の lock を取得し、互いを排他しない。これは現状で「未設定」と「明示 `/tmp`」が同じ `/tmp` lock を使う保証からの退行である。新設予定のテストも「同じ stable TMPDIR 同士」しか検査せず、この混在負例を KILL しない (`plan-v1.md:464-468`, `plan-v1.md:489-492`)。
- 成果物への影響: 同じ submodule の apply/build/revert または同じ repo の mutation が二重走行し、汚染 snapshot による false green/false red が land を通ると、後続の certified 選択、材料レポート、試行台帳の値と参照が別実行の状態へ結び付く。
- 提案: correctness lock の置き場を `TMPDIR` から分離し、明示 override の有無にかかわらず canonical repo/tree identity から一意に導く。`TMPDIR=/tmp` と auto Lustre の二 process を同時起動し、同じ lock identityまたは実排他になる混在負例を必須にする。

### [BLOCKER] stable root 上の stale prune が別ホストの live memo を破壊する

- 場所: `plan-v1.md:361-366`, `orchestrator/tests/real_repo_receipt_memo.py:375-402`, `orchestrator/tests/real_repo_receipt_memo.py:546-578`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:394-417`, `orchestrator/tests/sort_swo_oracle_receipt_memo.py:571-610`
- 内容: plan は root 全体を消さない一方、既存 6 時間 prune に後始末を任せる。しかし各 prune が保護するのは自 session の `current_path` だけである。receipt memo は別 live session の JSON を消し、sort memo は別 live session の JSON と `.lock` の両方を消す。共有 root への移動により、従来は別ホストから到達不能だった prune が cluster 全体へ届く。特に open 中の lock file を unlink すると、同名の新 inode が作られて lock identity まで分断される。既存テストは current key と receipt lock の保護しか検査しておらず、別 live key を検査しない (`orchestrator/tests/test_real_repo_serialization.py:3698-3718`)。
- 成果物への影響: 長時間 session の worker が cache missまたは別 lock inodeを掴んで fail-closed red になり受入受領証が失われるか、snapshot の単一性が壊れてレポートや選択の参照 epoch が混在する。
- 提案: age だけで共有 namespace を消さない。session leaseを導入するか、対象 lock の nonblocking exclusive acquireとlive判定を通した keyだけを削除する。別ホストの live keyを保持したまま pruneする正例と、live JSON/lockを消す変異の負例を追加する。

### [BLOCKER] Lustre 上で必要な POSIX 保証を得たことを示す gate が不足している

- 場所: `plan-v1.md:382-387`, `plan-v1.md:505-510`, `orchestrator/tests/real_repo_receipt_memo.py:352-366`, `orchestrator/campaign/wal.py:2157-2180`, `orchestrator/qualification/atomic_publish.py:74-100`, `tools/task_runs/ledger.py:1223-1318`
- 内容: plan の実 filesystem gate は fstype と同一 root の `flock` が中心で、二 host probeさえ「可能なら」である。ところが一時 root 上では `os.replace`、`O_CREAT|O_EXCL`、file/dir `fsync`、`os.link`、即時の存在可視性が正しさ契約を担う。repo にはこれらを load-bearing と明記した filesystem selfcheckまであるが、選定 rootへ適用する計画がない。親の probe が示す `O_EXCL=ok` も単一 hostであり (`brief.md:140-155`)、rename、link、directory fsync、別 clientからの可視性は未証明である。確認できた mmap は匿名 mmap なので本変更の影響外である (`orchestrator/campaign/sort_swo_oracle.py:1170-1173`)。
- 成果物への影響: create-only claimの二重成功、atomic publishの部分可視化、fsync済み台帳の消失が起きると、certified 選択、レポート、台帳の値そのものが二重化または欠落する。
- 提案: final rootで二 host必須の capability gateを行う。少なくとも flock、同名 O_EXCL競争、temp-writeからrename/linkしたexact bytesの即時可視性、file/dir fsync、unlink後のlock identityを正負対照付きで検査し、1件でも不成立なら実装を停止する。

### [MAJOR] B2 の復元は必要だが、configure 失敗時の rollback が計画に無い

- 場所: `plan-v1.md:336-345`, `plan-v1.md:432-448`, `orchestrator/tests/conftest.py:2502-2523`, `orchestrator/tests/conftest.py:2903-2959`, `orchestrator/tests/test_growth_test_holds_contract.py:1572-1591`, `orchestrator/tests/test_pytest_failure_digest.py:953-967`
- 内容: 同一 process内の nested `pytest.main()` は実在する。envの不在/空/値と `tempfile.tempdir` cacheを復元する方針は正しい。一方、policy適用後に既存 configure処理が失敗した場合、現行 except は memo nonceしか復元しない。plan は復元先を `pytest_unconfigure` としており、configure途中の失敗でも必ずそこへ到達することを証明していない。
- 成果物への影響: 内側 pytest の失敗後も外側 process の TMPDIR/cache が変わると、後続テストのlock、WAL、snapshotが別rootへ移り、受入結果集合と成果物参照が実行順依存になる。
- 提案: mutation直後から同じ `pytest_configure` の exceptでrollbackし、`pytest_unconfigure` の最内 finallyでも冪等復元する。policy後の各configure処理を故障注入する負例、unconfigure内側例外の負例、不在/空/明示値/cache済み値の正例を追加する。

### [MAJOR] B4 の閉集合確認は正しいが、TMPDIRを受領証が束縛しないことは権威上の欠落である

- 場所: `tools/acceptance_launcher.py:53-60`, `tools/acceptance_launcher.py:194-201`, `tools/dev_wave_wait.py:458-470`, `tools/dev_wave_land.py:138-143`, `tools/dev_wave_land.py:984-1003`, `plan-v1.md:313-323`
- 内容: `env_projection` が4 fieldだけで TMPDIRを含まないという読解は正しい。しかし本変更後は site、明示 override、fstypeにより同じ tested tipでも一時 filesystemが変わる。plan はcontroller logへ markerを出すが (`plan-v1.md:428-435`)、receipt verifierはそのmarkerの存在や内容を検査しない。`log_sha256` がbytesを間接束縛しても、受入権威はどのfilesystem regimeを受理したか解釈できない。
- 成果物への影響: 同じenv projectionで `/tmp`、Lustre、compute ambientの走行がすべて受理可能となり、certified結果やレポートから実際に使われた正しさregimeを再現・比較できない。
- 提案: login collectionと各実行shardについて、effective realpath、fstype、originを構造化binding reportまたはreceiptへ入れ、land側で必須検査する。少なくとも必須markerをparseしてreceiptへ投影し、marker欠落変異をKILLする。

### [MAJOR] B5 はlogin collectionで形式上発火しうるが、実受入workloadへの発火証拠が無い

- 場所: `brief.md:180-207`, `brief.md:213-224`, `brief.md:288-303`, `plan-v1.md:368-376`, `plan-v1.md:395-402`, `orchestrator/tests/conftest.py:805-813`
- 内容: 既存artifact pathとrequest IDはloginで全件collect-onlyした後にcomputeへdispatchする形を示すが、TMPDIR未設定とsibling root Lustreまでを同じartifactで示していない。さらにcollect-onlyではmemo prewarmが明示的に無効で、full testのtmp_path、WAL、memo workloadはcompute側にあり、planはcomputeを変更しない。planのK=1 login-local 6走は実運用の549 session中549 sessionがdispatchだったregimeと異なる。
- 成果物への影響: 実受入では費用の大部分が移動しないまま、非実運用regimeのwall値が改善レポートへ入り、採否と台帳の性能記録が実際の受入形を参照しなくなる。
- 提案: 発火条件3点とeffective root markerを記録する既存形のartifact IDを先に作る。実default dispatch形でどのphase、process、fsync countが移動したかを示せないなら、「受入全走の高速化」としては不採用にする。

### [MAJOR] stable root の異常終了 residue と共有quotaの寿命設計が閉じていない

- 場所: `plan-v1.md:361-366`, `plan-v1.md:505-510`, `orchestrator/campaign/patchharness.py:362-378`, `orchestrator/tests/test_s8b_oracle_driver.py:912-923`
- 内容: 正常終了時の個別cleanupはあるが、SIGKILLやhost障害では実行されず、root全体も意図的に削除しない。planはpeakとresidueを「測る」とするだけで、累積上限、回収権威、live判定を定義していない。node-local容量問題が共有user quota全体の問題へ拡大する。
- 成果物への影響: residue蓄積でENOSPCになると、現在greenの受入がredとなり、受領証、レポート、台帳の新規生成がcluster全体で停止する。
- 提案: per-session ownership metadataと最大寿命を持たせ、live lockを取得できたsession residueだけを回収する。quota headroomを毎走preflightし、異常終了を繰り返す負例で上限が保たれることを示す。

### [OK] B3 の real-repo P/S lock は TMPDIR移動の影響を受けない

- 場所: `orchestrator/tests/conftest.py:918-924`, `orchestrator/tests/conftest.py:1044-1069`, `orchestrator/tests/conftest.py:1105-1124`, `tools/acceptance_shards.py:74-84`, `plan-v1.md:296-300`
- 内容: lock directoryはliteral `/tmp` で、legacy/common-dir lockの双方がそこから導かれる。cross-host shard間はlocal flockではなくallocator conflict edgeが担当する。`tools/mutation_worktree.py` のwrapper lockも`--out` siblingでTMPDIR非依存である (`tools/mutation_worktree.py:192-219`)。
- 成果物への影響: この面ではreal-repo reader/writer排他、受理集合、certified値、レポート、台帳参照はいずれも変わらない。
- 提案: planどおりliteral `/tmp` exact pinと、TMPDIR変異をKILLする既存経路の負例を残す。

### [OK] 既存fstypeガードと受理集合同値性の計画は弱体化していない

- 場所: `orchestrator/tests/test_real_repo_serialization.py:516-540`, `orchestrator/tests/test_real_repo_serialization.py:5246-5297`, `orchestrator/tests/test_real_repo_serialization.py:5315-5390`, `orchestrator/tests/test_real_repo_serialization.py:5510-5617`, `plan-v1.md:303-311`, `plan-v1.md:450-460`
- 内容: 拒否集合はtmpfs族のままで、`tempfile.gettempdir()`と継承envのTMPDIRの両方を検査する。明示TMPDIRだけ赤にする枝、ambient defaultだけskipする枝も変更対象にしていない。Lustre positive controlの追加は既存期待値の書換えではない。planにはskip、deselect、削除も無く、collection digestとred/skip集合の完全一致gateがある (`plan-v1.md:389-408`, `plan-v1.md:494-503`)。
- 成果物への影響: この部分単独ではtmpfs退行の歯、受理集合、certified値、レポート、台帳参照は保存される。
- 提案: 既存positive/negative/load-bearing controlsを無変更で残し、Lustre controlは追加だけにする。`test_acceptance_nproc_study.py:1469-1472`, `:1592-1596`, `:1873-1885` の明示的な `/tmp` 契約もambient期待値と誤認して書き換えない。

## 親 brief への反証

P2「TMPDIRの移動は受理集合を変えない」は成立しない。親自身がlock到達範囲を攻撃点として認識しているが (`brief.md:77-87`)、実際には明示 `/tmp` とauto Lustreの混在で同一hostのABA防壁まで分断され、共有pruneが別hostのlive sessionへ届く。

P1の一般化も親brief自身の後半で反証済みである。最初の値はpegasus02一機種、loadavg 7.4から19.1、合成100 fsync/processの測定に限られる (`brief.md:19-36`)。実受入はlogin単一process collectionとcompute shardに分かれ (`brief.md:180-207`)、compute 48並列の測定結果が出るまで裁定禁止と明記されている (`brief.md:209-224`)。したがって29秒差を受入全走へ写す根拠にはできない。

## 見落としたかもしれないこと

- pytest自身のshared basetemp numbered-directory生成、lock、stale cleanup実装はrepo外なので直接監査していない。stable root共有ではここも別hostのlive directoryを消さないことを確認する必要がある。
- Lustreのcluster-wide semanticsは親briefに記録されたmount optionと単一host probeだけを根拠にした。二host実測は行っていない。
- 静的検査のみであり、pytest、filesystem probe、性能測定は実行していない。