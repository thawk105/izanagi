## 所見

以下、`probe/` は指定された T-2817 job dir の probe、`site-packages/` は指定された Python 3.10 の実行環境を指す。静的検査のみで、テスト・計測・書込みは行っていない。

1. **主張:** 閉包式が入れ子区間の二重計上を排除しておらず、符号付き残差の基準では誤った分解も合格する。
   **根拠:** `tools/acceptance_shards.py:790`、`:901`、`:906`。`records_from_items` ⊃ `_canonical_item` ⊃ `resolve` であり、plugin hook 全体はこれら全部を含む。brief (P1) は `残差の median ≤ 閾値` とだけ定義している。
   **親の記述との差:** inclusive な関数時間をそのまま Σ に入れると過大計上になる。大きな負残差でも現基準を満たす。また worker median が閉じても、`W_w` を決める最遅 worker が閉じたとは限らない。
   **重大度:** 高。
   **修正案:** 加算するのは排他的区間だけとし、inclusive 時間は内訳として別掲する。`median(|残差_w|)` に変更し、全 worker の残差と `W_w` を決めた worker の残差も示す。2 秒／5% は診断上の許容値として使えるが、関数帰属の精度保証とは呼ばない。

2. **主張:** (P3) の短縮量に計器の影響が混入する。(P4) の「超えたら比と差だけ」は救済にならない。
   **根拠:** brief (P2) は S3-u＝基本計器、S3-cf＝関数計器＋memo 化、(P3) は `W(S3-u)−W(S3-cf)` を短縮量としている。
   **親の記述との差:** この差は memo 化と関数計器の二変更を含む。計器は呼出し回数・待ち・資源競合を変え得るため、絶対値を捨てても比・差の偏りは消えない。modify median の差だけでは最大到着時刻や `pre` の影響も評価できない。
   **重大度:** 高。
   **修正案:** 主比較を同じ関数計器の `S3-f − S3-cf` に置換する。S3-u は観測者効果の対照に限定し、modify の分布・`W_w`・`pre` を比較する。影響が大きければ「計装下の条件差」と報告し、無計装の短縮量へ外挿しない。

3. **主張:** memo thread 終了を公開時刻と同一視し、`ε ≤ 2秒` を既知の上限として扱う根拠がない。
   **根拠:** `orchestrator/tests/conftest.py:2431` で prewarm 後に `.pending` を unlink、`:2525` 以降で join・ログ出力を行う。worker は `real_repo_receipt_memo.py:630` の HEAD 取得、`:682` の排他的ロック付き読込を経て、`:701` で最大 10 ms sleep する。`probe/t2817_collection_stage_aggregate.py:207` の `pre_junit` は **max(cf_exit)−JUnit timestamp**。
   **親の記述との差:** thread 終了の監視には公開後処理と監視遅延が入る。10 ms は sleep 間隔であり、ロック待ち・cache 読込・scheduler 遅延の上限ではない。controller の通知受信・collection 照合はこの `pre_junit` の終点より後なので、同じ ε に無条件で含められない。
   **重大度:** 高。
   **修正案:** receipt／oracle 各 endpoint の正常復帰直後を取り、両公開完了の近似 M と barrier 終了を分ける。worker の待ち入口・出口、既存 cf_entry／exit を残し、ε は符号付き実測残差とする。「2秒」は事前の適合判定閾値に下げ、超過を式の不適合として報告する。

4. **主張:** 雛形の有効セル判定を流用すると、失敗セルから結論を出せる。
   **根拠:** `probe/t2817_collection_stage_aggregate.py:181`–`:192` は `complete` と JUnit 存在だけで `valid` を決める。`:205` の collection mismatch、`:222` の errors、rc は合否条件に入らない。runner の `t2817_collection_stage_probe.sh:179` は warm 以外の非ゼロ rc で停止しない。
   **親の記述との差:** brief の完了判定には関数内訳と byte 一致があるが、それ以前に「正常に完了した対象セル」の条件が欠ける。とくに反実仮想は待ちの timeout を生じ得る。
   **重大度:** 高。
   **修正案:** 既存集計の `valid` を、rc、48 worker の必要計時点、mismatch=false、probe／node error 無し、report と集合照合の成功を含む条件へ置換する。失敗 attempt は残し、正常セルの速度差に混ぜない。常設 gate の追加は不要。

5. **主張:** `os.times()` の値を関数自身の user／sys と読むのは帰属過剰になる。
   **根拠:** brief scope・(P1) は process CPU を関数区間へ割り当てる設計。T-2817 README §4 は process 群の sys を関数へ帰属していない。
   **親の記述との差:** worker の execnet IO thread 等の CPU も区間中に加算される。逆に `RUSAGE_THREAD` は main thread の CPU を測れ、関数実行の帰属に近いが、process 群の sys 総量と同じ測定量ではない。
   **重大度:** 中。
   **修正案:** 大区間の入口・出口で `resource.getrusage(RUSAGE_THREAD)` を取り、process CPU は別列として保持する。5万回の canonical／resolve 呼出しごとには CPU syscall を足さず、resolve は回数・wall、CPU は正規化の各 pass 等の大区間までと明記する。

6. **主張:** 「path 文字列ごとの memo 化は同値」という断定と、byte 一致の取得方法が未確定。
   **根拠:** `/usr/lib/python3.10/pathlib.py:1077`–`:1089`、`tools/acceptance_shards.py:762`–`:793`、`:1013`–`:1035`、`:1160`–`:1188`。
   **親の記述との差:** 非 strict resolve は毎回 filesystem を観測するため、path／symlink／cwd が動く一般の場合に memo 化と同値ではない。一方、別表記の alias を各々実 resolve すれば、同じ canonical nodeid に対する既存の重複拒否は維持できる。report に `selected_digest` という field はなく、report 全体の byte 比較も時刻・path 差で成立しない。
   **重大度:** 中。
   **修正案:** 「固定した collection 中の、成功した実 resolve 結果の再利用」に限定する。全 worker の `izanagi_acceptance_shard` payload の両 digest と、gw0 の `records`／`selected`、report の `observed_universe`／`selected` を同じ canonical serialization で照合する。これは観測標本の一致であり一般的同値証明ではない。

7. **主張:** memo 待ちの外乱機序は、まず cache の配置と実際のロック経路で限定すべき。
   **根拠:** `probe/t2817_collection_stage_probe.sh:14`、`:118` は cell の `TMPDIR` を node-local に置く。`real_repo_receipt_memo.py:144` はそこを cache root にする。writer は `:597` で resolver と store を同じ排他的ロック内に置き、reader は `:469` で非 blocking flock を再試行する。T-2817 README §1.1 も `/scr` を明記する。
   **親の記述との差:** この雛形では「48 worker の `.pending` poll が Lustre metadata を増やす」とは言えない。公開前の待ちの多くが flock 再試行になる可能性もある。ただし早着した worker の CPU／local IO、resolve 削減による Lustre 負荷低下が M を変える可能性は残る。
   **重大度:** 中。
   **修正案:** TMPDIR と実 memo path の配置を各セルで記録し、M の開始・公開完了・worker 待ちを併記する。各セルの M で max 式の整合は検査できるが、「memo を固定した worker 短縮の純効果」や M の変化原因までは識別できないと限定する。

8. **主張:** session 作成時刻だけでは、他 wave の collection との重複を検出できない。
   **根拠:** brief (P5)。T-2817 README §8 は順序反転を外乱除去の証明としない。
   **親の記述との差:** cell 開始前に作られた session が cell 中に collection を始める場合を取り逃す。逆に session 作成だけでは実行開始を示さない。client stats と同一 node の `others=0` でも、他 node／他ユーザーの MDS 負荷は排除できない。
   **重大度:** 中。
   **修正案:** session 作成を候補抽出に使い、既存 JUnit 開始時刻と report の collection 終了時刻等で区間を照合する。区間が取れなければ「重複不明」とし、対比較の片側を取り直す場合は対全体を同順序で一度だけ再測定する。再度重なれば結論を限定する。

9. **主張:** 新事実の一部と成果物の位置付けに、測定条件を越えた読みがある。
   **根拠:** brief「研究前進」、N1・N2・N5。T-2617 §3.2、T-2817 README §6・§8。`/usr/lib/python3.10/posixpath.py:428`、`:453`。
   **親の記述との差:** 単独 process 値と48並列値は「食い違い」ではなく条件が異なる既存観測。N2 の約12 syscall は通常の component 経路の概算で、symlink 展開や Lustre RPC 数と一致しない。ledger 変更は選択集合が**変わり得る**根拠であり、実際に変わった証拠は集合照合が必要。
   **重大度:** 中。
   **修正案:** 新規量を「同一 tip・48 worker の関数内訳、resolve 回数／wall、計装下の条件差、公開時刻と待ち」に限定する。開始 gate の as-of と各 cell の実行時刻を分け、T-2825 land 後の別 tip の最終受入は参考観測とする。旧値・旧裁定は無効化しない。

## 反実仮想セルの判定

**(c) 条件付きで scope 内。** 起動引数に「worker 側の短縮量と pre の変化を別々に測る」が残り、D1936 項35も効果の先行測定を求めている。
ただし、probe 内の一条件による診断に限定し、縮約方式の採用・恒久実装・一般的同値性の主張へ進まないことが条件。repo code を変更しないことだけでは十分ではない。
測定は同計器の S3-f／S3-cf で行い、集合一致と実 resolve への委譲を維持する。T-2617 §4 の字句化とは別物であり、既裁定の撤回を提案しない。
この限定を満たせなければ、関数時間は「観測費用」としてだけ報告する。関数時間から実際の worker 短縮量や Δpre を測ったことにはできず、その依頼部分は未達と明記する。

## 測定行列と計時点の修正版 (差分だけ)

- **(P1) hook 差し替えを具体化する。** module global の helper 差し替えは有効である（`acceptance_shards.py:901`–`:919`）。hook 本体は `get_hookimpls()` から対象を特定し、既存の `argnames`・順序・`wrapper`／`hookwrapper` を保って `HookImpl.function` だけを委譲関数へ差し替える。`pluggy/_callers.py:93`–`:121` は保存済み argnames による位置引数呼出しなので、この方法と整合する。追加セルなし。

- **conftest の前後段は generator の実行区間で取る。** `next()` から最初の yield までを前段、`send()`／`throw()` から終了までを後段として、戻り値・例外を伝播する。`_ensure_flaky_test_holds_loaded` と `_validate_real_repo_shard_state` の入口だけでは前段終端が取れず、その間に内側 hook 全体が入る（`conftest.py:2254`、`:2321`–`:2336`）。generator の生成時間だけを測る wrapper は不可。1 worker あたり数回の境界追加で、所要増は小さい。

- **conftest の特定は登録済み module を使う。** pluginmanager の登録名は conftest の絶対 path（`_pytest/config/__init__.py:741`、`:783`）。登録一覧の `__file__` と対象 path を照合し、別名 import はしない。初期 conftest は `pytest_configure` より前にロードされる（同 `:1576`、`:1605`、`:1205`）ため、probe configure で helper と collection hook を包める。

- **閉包の区間を追加する。** `last_itemcollected → modify 呼出し入口`、modify の各 impl／wrapper 前後段、`modify 出口 → cf_entry` を外側の排他的区間とする。最初の区間には itemcollected の残り、最後の module と祖先の collectreport、`check_pending()` が入る。最後には collection cache の解放が入る（`_pytest/main.py:869`–`:879`、`:1023`–`:1037`）。collectreport は既存末尾区間の内訳として集約し、item ごとのログ出力はしない。

- **他 plugin は実登録を列挙して測る。** mark の deselect 処理（`_pytest/mark/__init__.py:282`）、xdist の group suffix 付与（`xdist/remote.py:236`）、各 `pytest_deselected` を含める。terminal／JUnit に存在しない modify impl を仮定しない。`pytest_deselected` は選択区間の内訳であり、別加算しない。低頻度 hook の境界追加なのでセル追加不要。

- **collection_finish の順序を保存する。** `-p` は初期 conftest より先に登録され、同じ `tryfirst` wrapper は後登録が外側になる（`pluggy/_hooks.py:451`–`:473`、`_callers.py:93`）。現在の conftest finish は通常 hook なので probe wrapper 内だが、実登録の外側 wrapper 前段があれば `cf_entry` 前に数える。xdist の送信（`remote.py:257`）は通常 impl として cf 内、controller の受信・照合は別区間とする。

- **resolve は案(a)を採る。** 元の `Path.resolve` を保存し、thread-local の canonical 実行中フラグで計時・memo 対象を限定する。フラグは `finally` で復元する。これなら実戻り型を保ち、`Path.cwd().resolve()`、spec 解決、conftest の growth hold resolve（`:2292`）を対象外にできる。案(b)の subclass は resolve／relative_to の戻り型まで変わり得るため不要。

- **自己費用は回数と分けて報告する。** 約5.3万 resolve なら入口・出口の時計読取りは約10.6万回／worker。仮に追加費用が1呼出し1～10 µsなら約0.05～0.53秒／workerであり、これは見積りであって実測値ではない。canonical wrapper 等の費用も別に加わる。実際の観測者効果は S3-u／S3-f で見る。

- **(P2) warm を比較条件から外す。** 開始時の warm 1走＋5条件各2走＝11セルに明確化する。逆順の最後の warm は温めの役割を持たない。S2-f は依頼の S2／S3 内訳比較に必要。S1 は既存の段差を同 tip で確認する補助として残せるが、純粋な plugin 費用の対照とは呼ばない。新規セル追加なし。

- **主比較・共通計器を変更する。** S3-f／S3-cf を短縮量の主比較、S3-u／S3-f を観測者効果の比較とする。公開完了・worker 待ちの少数の境界は両者へ共通に追加し、「S3-u は旧計器と完全同一」という名称説明を修正する。順序反転2走は記述的診断には使えるが、外乱除去や効果確立の証明には使わない。

- **書込み先の既存設定を明文化する。** cell ごとの session_root と create-only report（`acceptance_shards.py:239`、`:1188`）、node-local TMPDIR、`PYTHONDONTWRITEBYTECODE=1`、`-p no:cacheprovider`、task-run 自動記録停止を維持する。memo cache／lock／pending の生成は既存動作として残す。計測中の checkout／`output/` 書込みは行わず、結果転記は計測後とする。

## 見つからなかったこと

- `records_from_items`／`allocate`／`_canonical_item`／`_records_payload`／`_digest` の呼出しを確認したが、module 属性の差し替えを迂回する束縛は見つからなかった。
- `_validate_real_repo_shard_state`、suffix strip、reorder、hold 処理を検索したが、brief が依頼の名指し対象そのものを落とした箇所は見つからなかった。
- pluggy の `HookImpl` と `_multicall` を確認したが、既存 metadata と generator protocol を維持する委譲差し替えを妨げる実行上の障害は見つからなかった。
- 雛形の `schedule` は collection 一致検査と失敗通知を残す（`t2817_probe_plugin.py:201`–`:215`）。受理集合・hold・verifier を省略する変更は見つからなかった。
- pyc、cacheprovider、TMPDIR、task-run 記録、report 出力を検索した範囲では、雛形の設定を維持した場合に checkout への新規計測書込みを要求する箇所は見つからなかった。
- N1 の履歴差分・実選択集合、N5 の現在の T-2825 稼働状態は今回の静的コード確認では独立検証していない。brief の記載を確認済みの現況とは扱わない。

## 総括

重大度「高」は **4件**。判定は **修正後 GO**。
最重要は、短縮量を **S3-u − S3-cf から、同計器の S3-f − S3-cf へ変更すること**。
併せて排他的な閉包式、公開時刻と ε の定義、失敗セルの除外条件を実測前に確定する必要がある。
セル追加は不要。得られる結論は固定標本・計装下の診断に限定し、短縮実装の採用効果や旧裁定の撤回へ広げない。