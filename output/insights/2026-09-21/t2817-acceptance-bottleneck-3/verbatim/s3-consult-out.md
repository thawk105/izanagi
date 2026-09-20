## 所見

以下、`C` は `orchestrator/tests/conftest.py`、`A` は `tools/acceptance_shards.py`、`xdist/` は指定された site-packages 配下を指す。静的検査のみ実施した。

1. **主張：`schedule()` の完全な no-op 化は、collection 一致検査まで消す。重大度：高。**
   **根拠：** `xdist/scheduler/loadscope.py:207` の `add_node_collection()` は初期 worker 群を登録するだけで、初期群の一致検査は `schedule()` 内の358行で行う。検査本体409行は不一致を `pytest_collectreport` の failed として通知する。`dsession.py:306` がこの `schedule()` を呼ぶ。
   **親の記述との差：** (P2) の形では test を送らず終了できるが、「controller 照合」を含む受入相当の collection にはならない。不一致でも成功終了し得る。
   **修正案：** probe scheduler は既存の一致検査とその失敗通知を残し、配布部分だけを省く。全初期 worker の報告を待ち、一致成功を確認して終了する。

2. **主張：S1 でも controller の同期 memo prewarm が発火する。重大度：高。**
   **根拠：** `C:920`、`C:978` の通常 prewarm 条件は `collectonly` と consumer の有無を見ており、shard spec や `maxfail` を要求しない。`C:2618` の collection 通知 hook は、early job が無ければ `C:2681` で通常 prewarm を実行する。全 collection を保持する S1 は consumer を含む。
   **親の記述との差：** S1 は「xdist 起動＋collection＋照合」だけではない。S2−S1 は plugin の追加に加え、memo の**通知後同期実行から早期並走への切替**を含む。worker 出口時刻だけでは S1 の controller 側待ちを捕捉できない。
   **修正案：** S1 の通常 memo と S2/S3 の early memo を明示する。controller の collection 通知 hook 前後と、全 collection 登録・照合完了時刻を追加し、段差を複合条件の観測差として扱う。

3. **主張：現在の計時設計では、掲げた費用を同じ区間へ収められない。重大度：高。**
   **根拠：** ledger 読込は `C:2985` の `pytest_configure`、配送は `C:2584` の `pytest_configure_node`。前者は sessionstart より前である。JUnit の起点は `_pytest/junitxml.py:644`、終点は同647行以下。受入の collection 終点は `A:925` の trylast hook、worker 最大の採用は `A:1092`。
   また、probe と conftest の `pytest_collection_modifyitems` が共に `wrapper=True, tryfirst=True` なら、後登録の conftest が外側になる。probe の前後には conftest の hold 処理・suffix 除去・ledger 並べ替えの全体が入らない（`C:2256`、`C:2314`）。
   **親の記述との差：** 独自 sessionstart は JUnit 起点と厳密には同じでなく、`pre` の段差に controller の ledger 読込は入らない。modifyitems の wrapper 区間を並べ替え費用と読むこともできない。
   **修正案：** process 起動からの時間、実 JUnit 起点、worker collection 終点、controller 照合完了を別列にする。S2/S3 は shard plugin の実 timestamp も回収し、wrapper 時刻との差を残す。並べ替え費用を現在の modifyitems wrapper だけで独立同定しない。

4. **主張：S2/S3 の出力先を共用すると、反復が失敗する。重大度：高。**
   **根拠：** `A:131` の spec は `session_root/shard-0/report.json` を生成する。`A:239` は hard-link による create-only 書込みであり、`A:1188` の失敗は session の終了コードを変更する。test 0件でも sessionfinish はこの経路を通る。
   **親の記述との差：** (P2)/(P4) の「session_root は job dir」だけでは、S2/S3 と各反復が同じ report を作る。2本目以降が衝突する。
   **修正案：** `job-dir/<stage>/<replicate>/` を各走固有の session_root とし、JUnit・probe 出力も分ける。0件実行の report は診断成果物であり、受入完走の証明として扱わない。

5. **主張：(P1) の全面省略は、依頼(1)を満たさない。重大度：高。**
   **根拠：** `T-2817-origin.md` は共有 base 構築・verify・copy を「計算ノードで取り直す」と指定する。D2148項6も共有準備の内訳調査を求める。D1936項35は実測の最大 worker を対象にせよという裁定で、指定成分の測定免除ではない。
   **親の記述との差：** N2 は分析の主役を変える根拠にはなるが、旧 tip の値による代用の根拠にはならない。最大 worker 上の新 node が共有準備と無関係であることも、この集計では示していない。
   **修正案：** 現行 key に適合した観測 probe による A 条件を最小1走追加する。L の内訳と最大 worker の実行列を別々に報告し、旧式を無理に一列へ足さない。

6. **主張：offline の並びから「O_max がどう変わるか」は決まらない。rank 再現も alphabetical 近似だけの問題ではない。重大度：高。**
   **根拠：** `rank_replay_v1.py.txt` は cost 順までで、`C:1786` の cardinality 順・48 partner 挿入を再現していない。`A:761` の保存 nodeid は group suffix を除去するため、`selected` の文字列だけでは runtime scope を再構成できない。実際には `C:2209` の real-repo suffix 除去例外もある。さらに `xdist/scheduler/loadscope.py:313` は worker の完了に応じて次 unit を配布する。
   **親の記述との差：** N3 の rank 差を「collection 順の近似差」と限定できない。(P3) の並べ替えだけでは、新しい worker 割当て・占有和を算出できない。
   **修正案：** N3 は既に書かれた「仮説」を維持し、rank 差の説明を訂正する。効果量を出すなら実行時間固定・配布規則を明示した model 値に限定し、未識別なら数値を置かない。8 node の複数走中央値による感度分析は D2107 の refresh 入力でも採用案でもないと明記する。

7. **主張：N4 の加法分解と N2 の「相方」には、残差と代表値の混同がある。重大度：中。**
   **根拠：** `A:1131` の `worker_occupancy.duration_s` は report duration の和で、worker の開始から終了までの実時間ではない。提示 JSON を再集計すると、各走の
   `W − O_max − pre − post` は **0.096〜4.450秒**残る。
   `shards-recent-v1.json` の pairing/shard-0 21件では `median(pre−memo_receipt_s)` は **4.607秒**で、brief の5.0秒と一致しない。また `median(O_max)=327.3` と `median(L)=233.7` の差は93.5秒であり、62.7秒は各走の差の中央値である。
   **親の記述との差：** `F = pre + post`、`O_max中央値 = L + 62.7` はそのまま等式にできない。v1 script の `P=O_max−L` は、別 worker 上の L に対する差なので「相方」ではない。
   **修正案：** 各走で `F=pre+post+残差` を閉じてから要約する。`P_L=O_L−L` と `O_max−L` を区別する。`pre−memo` は重複実行を含む差であり、collection の独立成分や削減可能量と呼ばない。

8. **主張：pairing property 群を「既定 on 後の同条件群」と一般化できない。重大度：中。**
   **根拠：** v1 は property 名の存在、v2 は worker property の存在で選別するだけで、SHA・投入条件・opt-in期間を照合しない。JSON には passed 件数や rank の異なる走がある。`shard0-pairing-v2.json` の `e637a58c.Omax_items` は failed-launch 194.8秒、floor 48.2秒、delegated 36.9秒であり、「150〜335秒の node を2〜3個」という全称にもならない。
   **親の記述との差：** 21/21 の観測自体と、「既定化後」「同一 tip」「同じ重い組合せ」という母集団の説明は別である。
   **修正案：** 当面は「保存資料中の property あり21 session」と限定する。既定化後を主張する場合だけ投入元・SHAを照合する。最大 worker の構成は全称を避け、実際の node 列で示す。

9. **主張：`--maxfail=1` は成功走では使えるが、「他の効果は無い」は強すぎる。重大度：中。**
   **根拠：** `C:1886`、`C:1913` は ledger 読込・並べ替えを止め、pairing property も止まる。一方 `C:2368` は maxfail を見ず、early memo 条件を変えない。`xdist/dsession.py:411` は test failure だけでなく collection failure にも maxfail を適用する。
   代替は `--no-loadscope-reorder`（`xdist/plugin.py:143`、`C:1908`）。ただしこれも ledger と並べ替え・pairing をまとめて止める。
   **親の記述との差：** 「ledgerだけ」の切替ではなく、失敗時の停止挙動も変わる。
   **修正案：** 診断では `--no-loadscope-reorder` を候補にし、成功 collection の比較に限定する。どちらを採っても S3−S2 は読込・配送・worker 検証・並べ替え・property 付与と、その並走への影響を含む複合差と書く。

10. **主張：比較単位と反復の限界を先に固定する必要がある。重大度：中。**
    **根拠：** T-2243 §1/§3 の18.4秒は独立 process の wall median で、cohort wall も別にある。(P2) の S1 は worker 終点の最大であり、起点も違う。T-2243 §8 は順序反転2走を時間変動の検出に限定している。
    **親の記述との差：** S1−S0 をそのまま xdist の純増と呼べない。S2 の各 worker の入口／出口差は各自の待ちであって、controller の memo 所要や shard wall への寄与ではない。
    **修正案：** S0 に共通起点から全 process の collection 終了までの cohort 指標を追加し、従来 median は参照列に残す。worker ごとの入口・出口を保持し、`max(出口)−max(入口)` と各 worker の待ちを区別する。順序反転は page cache・Lustre 外乱を除去した証明には使わない。

11. **主張：(P4) の読取り専用条件と同 checkout 参照には、具体化が足りない。重大度：中。**
    **根拠：** `C:2572`、`C:2685`、`C:2788` は `IZANAGI_TASK_RUN_SIDECAR` があれば記録経路へ進む。memo cache は `real_repo_receipt_memo.py:136`、`sort_swo_oracle_receipt_memo.py:132` により TMPDIR 系へ置くが、read lock は `C:1038` の固定 `/tmp` に作られる（`C:1226` は `O_CREAT`）。`test_s8b_oracle_driver.py:970` は collection 時にも TMPDIR 下の共有 base 管理領域へ参加する。
    また (P4) の直接 `python3 -m pytest` による温めは、提示された AGENTS.md の「pytest は run_tests.py 経由」に反する。
    **親の記述との差：** `PYTHONDONTWRITEBYTECODE` と cacheprovider 無効化だけでは全出力先を固定できない。README追加後の受入は同じパスでも Job A と同じ SHA・可視 output 内容とは限らず、memo identity も変わる。
    **修正案：** sidecar を解除し、auto-record を無効化、TMPDIR・JUnit・ログを走別に固定する。温めは runner 経由で行う。Job A と参照受入の間に成果物・commitを挟まないか、挟むなら同条件参照とは呼ばない。

## (P1) の判定

**(c) 条件付き。現状の全面省略は不可。**
N2 により「Lが wall を決める」という旧前提は外せるが、名指しされた base／verify／copy の再測定まで省略できない。
最小構成は、現行 pairing 条件の **Aのみ1走**を別計算ノードで観測し、同 tip 実受入1走の shard 層と併記する。中央値・改善効果は主張しない。
probe は5要素 key の実際の集合と呼出し契約に適合させ、4要素×5 key の固定期待を残さない。T-2786 §6が示す、合成 fixture だけで計器の妥当性を確認する失敗を繰り返さない。
旧 `7975385b5` の結果はその tip の命題として保持し、新測定で無効化しない。

## 測定行列の修正版 (差分だけ)

- **S0：** 従来の process wall median／cohort wallに、全 process の collection 完了までの共通起点指標を追加する。追加走なし。
- **S1〜S3：** scheduler の一致検査を保持し、test 配布だけを停止する。controller の通知 hook 前後・照合完了を追加する。
- **S1：** 「通常 memo prewarm あり」と改称する。S2との差を plugin単独費用として扱う記述を削除する。
- **S1/S2：** `--maxfail=1` は `--no-loadscope-reorder` への置換を候補とする。どちらも ledger＋並べ替え＋pairing の一括切替であることを明記する。
- **S2/S3：** session_root・JUnit・TMPDIR・出力を各走固有にする。shard plugin が記録した collection timestamp を直接回収する。
- **全段：** process wall と JUnit/pre 区間を分ける。S3−S2 に controller configure 中の読込を含める分析には process 側の計時を使う。
- **追加：** 現行 key 対応の A replica を別 node に1走。準備・回収込み **概算15〜30分、queue待ち別**。依頼(1)の不足を補い、複数ノードへの条件分割も満たす。L/P腕やrefresh実施は追加しない。
- **参照受入：** Job A 後の1走は維持するが、その間の測定対象変更を避ける。順序反転2走は記述的反復に限定する。

## 見つからなかったこと

- **test無配布で正常終了できない欠陥は見つからない。** `dsession.py:165`→`:424` の shutdown、`remote.py:171` の終了標識、`dsession.py:193` の worker回収、`:70` の session終了へ進む。空のworkqueueでは `has_pending` も偽となる。問題は所見1の照合欠落である。
- **S1のhold完全性検査を壊す箇所は見つからない。** `C:2152`、`:2231`、`:2618` を確認した。完全 collectionを保持し、継承した `numnodes` を使えば、worker検査とcontroller検査を維持できる。
- **collection_finish入口をmemo待ち前に置けない問題は見つからない。** `C:2550` は通常hookなのでwrapperが外側に入る。ただし入口／出口差は待ちだけでなくhook全体である。modifyitemsの同順位wrapper問題とは異なる。
- **workeroutputの回収時点に問題は見つからない。** `remote.py:142` がsessionfinish後に送信し、`workermanage.py:418` が `node.workeroutput` を設定してから、`dsession.py:201` がtestnodedownを呼ぶ。
- **pairingのworker propertyを「割付予定worker」とする根拠はない。** `C:1874`、`:2340` と `test_acceptance_schedule_order.py:1801` を確認した。各worker自身のIDを持つitemの実行report由来なので、JUnitから実行workerを読む方法は妥当。
- **ledger書込み、hold／verifier変更、probeのrepo内配置の提案はbriefに見つからない。** `_validate_real_repo_shard_state` はstate検査であり書込みではない。所見11の出力環境は別途固定が必要。
- **終了後10秒の原因は特定できない。** shutdown、`A:1097` のreport作成、`C:3381` のmemo終了、共有baseのatexit cleanup（`test_s8b_oracle_driver.py:925`）、JUnit書出しが候補。ただしJUnitのWはprocess終了までではなく、unconfigure・atexit・外側terminate猶予を一律に含むとは言えない。`run_tests.py` に `_terminate` の定義は見つからず、10秒をその猶予とする根拠もない。原因追跡の追加走は不要。
- **既存被覆は新規成果に数えない。** 固定費はT-2710 §4、base内訳はT-2786 §4、早期memo機序・効果はT-2700/D2185、plugin CPU費用はT-2617の引用、独立collection差はT-2243、ledger乖離はD2107の既測。本waveの追加量は、現行tipの再測定と同jobで計時区間を揃えた段階差に限られる。

## 総括

重大度「高」は **6件**。判定は **修正後 GO**。現briefのまま実測へ入るべきではない。
最重要は、**S1にも同期memo prewarmがあり、予定した段差の帰属と計時点が対応していないこと**である。
schedulerの照合維持、走別出力先、計時区間の訂正、(P1)の最小測定追加を投入前に確定する。
成分を一意に分離できなければ、複合差と未識別量を明記して閉じる。実装・refresh・10秒の原因追跡へ広げる必要はない。