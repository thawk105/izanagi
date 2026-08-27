## 総括

最重所見は、14.0秒の全 suite subprocess collect を行う G6 が無 lock・衝突辺なしで残り、parent writer と排他されないことです。  
加えて Git common-dir の解決自体が旧 key 取得前に実行され、lock identity の読取りにも無保護区間があります。  
長寿命 fixture の loadgroup は統合されておらず、静的な最長直列鎖は引き続き83.5秒です。  
ただし「選択・marker・期待値は不変」という実装子申告は差分と一致しません。pytest は実行していません。

## 所見

### 1. BLOCKER: 3本目の全 suite collect node が排他閉包から漏れている

- **所見:** `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` は実 root を渡して全 suite を subprocess collect しますが、`REAL_REPO_ACCESS_BY_NODE` に存在しません。したがって parent writer との対は、同一 worker、flock、同一 shard のどれでも排他されません。実装子が挙げていない consumer test でもあります。

- **根拠 file:line:** [s5-integration-snapshot.patch:382](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:382) の実呼出し、[conftest.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:341) と [conftest.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:480) の正本に当該 node がなく、lock 適用は [conftest.py:2001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:2001) の map 登録 node に限られます。台帳値は [acceptance_duration_ledger.json:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/acceptance_duration_ledger.json:145) の14.0秒です。

- **成果物影響:** 14秒の inner collection が parent EX fixture と重なると、G6 の marker／collection report、pytest rc、failures が実行順で変わり、certified 選択結果の検査が非決定になります。

- **提案:** H6 を「2 node」から「3 node」へ訂正し、G6 を parent SH として inventory、独立 golden、nested-collection mutation に追加してください。`test_acceptance_schedule_order.py` を変更 consumer として焦点検査対象にも加えるべきです。

### 2. BLOCKER: common-dir resolver が両 lock の外で実 repo を読む

- **所見:** `_real_repo_lock_paths()` は Git common-dir を解決してから、返した旧、新 path を取得します。したがって新 reader の `git rev-parse --git-common-dir` と、既に lock を保持している parent／CCBench writer の対には排他機構がありません。「旧 holder が新 acquisition を阻止する」テストも、path 関数を事前に mock するためこの順序を検査していません。

- **根拠 file:line:** Git subprocess は [conftest.py:1042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:1042)、旧、新 path の先行解決は [conftest.py:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:1128)、最初の flock はその後の [conftest.py:1255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:1255) です。裁定は旧、新の固定順取得を要求しています（[s4-adjudication.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s4-adjudication.md:53)）。

- **成果物影響:** resolver が競合中の Git metadata を読んで失敗すれば pytest error／rc が変わり、誤った identity を得れば異なる common key で本体を実行して certified 結果が競合順依存になります。

- **提案:** 少なくとも同一 worktree の移行互換について、旧 path を算出して取得した後に common-dir を解決し、新 key を取得してください。さらに「旧 EX holder 中は common-dir resolver が呼ばれない」順序検査を追加してください。sibling worktree 間で resolver 自体まで守る必要があるかは、D1008 の保証文に明記が必要です。

### 3. 実装子の「選択・marker・期待値不変」申告は実物と不一致

- **所見:** collection は新しい通常 test 1本と9 parametrized instance、計10 node 増えています。既存11 nodeの xdist marker も変わり、既存期待値も少なくとも2箇所変更されています。skip の追加・削除は差分上ありません。

- **根拠 file:line:** 新規1 nodeは [s5-integration-snapshot.patch:866](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:866)、9 instance は [同:880](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:880)。marker は resource登録5 nodeと campaign 6 nodeで変更されています（[同:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:31)、[同:418](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:418)）。既存期待値は G6 と lock取得回数で変更されています（[同:388](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:388)、[同:743](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-integration-snapshot.patch:743)）。不変申告は [s5-author.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s5-author.md:63) です。

- **成果物影響:** certified collection／selection digest と期待 terminal count は少なくとも10 node分増え、11 nodeの shard assignment 入力も変わります。「不変」とした最終レポート値は事実と一致しません。

- **提案:** 指示済み gate の追加自体は戻さず、最終報告を「skip は不変、collection は10 node拡大、marker／配置と一部期待値は意図的に変更」と訂正してください。

### 4. 所要は83.5秒の直列鎖を越えていないが、lock追加費用は台帳から秒換算できない

- **所見:** fixture scope 変更による生成回数の増加はありません。invariant は1 moduleで1回、predicate candidate はconsumerが1本なので function化後も1回、scan は6 consumerを同一 workerへ寄せるため最大複数回から1回へ減ります。既存2 groupは別のままで、campaign groupも別です。

- **根拠 file:line:** group別台帳値は candidate 83.5秒（[ledger:14215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/acceptance_duration_ledger.json:14215)）、predicate 52.001秒（[ledger:14339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/acceptance_duration_ledger.json:14339)）。campaign のmarked 6 nodeは合計0.004秒（[ledger:1887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/acceptance_duration_ledger.json:1887)）、同 file 全体は0.092秒です。別 group維持は [s4-adjudication.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s4-adjudication.md:80)、K4は [acceptance_shards.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/tools/acceptance_shards.py:77) です。

- **成果物影響:** 静的 critical path は `max(83.5, 52.001, 0.004) = 83.5秒` のままです。一方、現行 full selectionでは概算164 resource acquisitionごとに Git subprocess 1回、flock 2回、計164 subprocess／328 flockが発生します。この追加秒数は旧台帳に存在せず、5分上限のレポート値は親実測まで未確定です。

- **提案:** `campaign=0.09秒` は「file component全体0.092秒」と「runtime loadgroup 0.004秒」に分けて記録してください。両 keyは共有deadlineなので待ち時間が単純2倍にはならない点も明記し、親実測で common-dir subprocess込みの wall を確認してください。新設10 nodeは台帳未登録で、静的に確定できる所要は `legacy-key` branch の0.05秒 sleep以上だけです。新しい全 suite collect 呼出し自体は追加されていません。

### 5. D1008 の lock identity 文は decision fragment で supersede が必要

- **所見:** D1008 の「repo root realpath由来」から、canonical keyをresourceごとの Git common-dir realpathへ変更しています。これは sibling worktree 排他を強める意図的変更なので、上記BLOCKER修正後は実装停止理由ではなく記録必須事項です。同一 host・同一 filesystemという保証範囲は維持されています。

- **根拠 file:line:** common-dir hashは [conftest.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:1113)、保証範囲は同ファイル1118行、変更裁定は [s4-adjudication.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1886-realrepo-closure-split/s4-adjudication.md:41) です。

- **成果物影響:** decision fragmentを残さないと、最終レポートが示す lock identity と実装が食い違い、後続 wave が旧 root-key 契約へ誤って戻す可能性があります。certified node集合を直接変える所見ではありません。

- **提案:** 「D1008 の lock-path導出文を、canonicalはresource Git common-dir realpath、移行中はlegacy worktree-root keyも旧、新順で併取、保証範囲は同一host／filesystem、と supersedeする」と記録してください。

## 排他対応表

同一資源の R/R は結果変更を生まないため、少なくとも一方が W の対を同値類で網羅しています。

| 競合対 | shardを跨ぐ配置 | 同一host内の実排他 | 判定 |
|---|---|---|---|
| `real-repo` CCBench reader ↔ 同 group CCBench writer | `real-repo` 同一 shard | CCBench SH/EX flock。process memo 4本だけは加えて同一 worker | 閉じる |
| campaign scan P/S reader ↔ real-repo S writer | K4 edgeで同一 shard | CCBench SH/EX flock | 閉じる |
| invariant／predicate candidate P writer ↔ real-repo P reader | K4 edgeで同一 shard | parent EX/SH flock | 閉じる |
| candidate P writer ↔ snapshot／scan P reader、candidate writer相互 | K4 edgeまたは同 file component | parent EX/SH flock | 閉じる |
| controller prewarm P reader ↔ candidate P writer | consumer fileが`real-repo` componentへ接続しK4 shardへ配置 | parent SH/EX flock | 閉じる |
| 各長寿命 fixture内のconsumer相互 | fixture別 loadgroupで同一 worker | fixture寿命中のSH。setup WはEX | 閉じる |
| G6 nested collection P reader ↔ candidate P writer | edge／groupなし | lock stampなし | **未排他** |
| common-dir resolver reader ↔既存 P/S writer | shard配置だけでは排他にならない | resolver時点では旧、新とも未取得 | **未排他** |
| 別hostの独立 runner invocation相互 | 同一 shard保証なし | `/tmp` flock無効 | D1008の保証外 |

## 既裁定との確認

- 裁定§2は維持されています。`s8c-preregistration-candidate`、`s8c-predicate-snapshot`、`campaign-repository-scan` は別 runtime groupで、unionはshard componentだけです。
- `tools/run_tests.py` のworktree blobとHEAD blobはともに `b1b1b374dbd68bd3c7b5e8087b04db2fda5e9769` で、1 byteも変わっていません。D838適合です。
- duration ledgerもHEADと同じblobで、D1052どおり分析用途のままです。単純なresource node所要総和は `266.320 + 23.618 = 289.938秒` と83.5秒を越えますが、直列鎖ではないためcritical path値には使えません。
- allocatorのK許容値は [acceptance_shards.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/tools/acceptance_shards.py:380) の `{2, 3}` のままで、D1103のK=3条件を変更していません。
- pytest、collect-only、実測は実行しておらず、緑とは記録しません。