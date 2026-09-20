## 判定と範囲

**must-fix は2件です。opt-out 本体の E/L 経路は支持しますが、集計器の失敗分類と予算超過の扱いは修正が必要です。**

静的読解のみです。pytest・selftest・変異検査は実行せず、ファイルも書き込んでいません。以下、`analyze` は指定された `probe/t2700_ab_analyze.py`、`history` は `probe/t2700_history_estimate.py` を指します。

## must-fix

**A1 — treatment failure の検出先と診断文字列が実経路を取りこぼす。**

根拠：`analyze:127–133`、`real_repo_receipt_memo.py:89–118,687–699`、`sort_swo_oracle_receipt_memo.py:68–102,739–752`、installed `xdist/remote.py:118,129–133`、`xdist/dsession.py:220–236`、`_pytest/terminal.py:390–394,580–583`。

検出対象は E の stderr にある `memo publication timeout` または receipt の fail-closed prefix だけです。しかし、次の経路があります。

- worker の collection hook で発生した例外は、xdist が controller の `pytest_internalerror` に転送し、通常の terminal reporter が **stdout** に表示する。memo の例外生成自体は stderr に print しない。worker 側のログ出力は debug 条件付き。
- oracle の読後・待機ループの deadline 超過は、oracle 専用 prefix と JSON の `reason="publication-timeout"` を生成する。receipt prefix でも、空白区切りの `memo publication timeout` でもない。

そのため、保存済み `.o*` に診断があっても見落とし、さらに oracle 診断は `.e*` にあっても見落とします。`run-measure.sh:88,115–120` は stdout と child.log を保存しており、入力不足ではありません。

**成果物への影響：** E の介入関連失敗が `infrastructure`／`unknown` 等へ移り、腕別の失敗種別表が誤る。失敗総数の併記は残るため、成功対の Wilcoxon が直接変わる問題とは区別します。

**是正案：** witness 判定は receipt に対応する stderr のまま維持し、失敗診断は対応する stdout／stderr、複製欠損時の child.log も確認する。両 memo の実 prefix と `publication-timeout` を扱い、実診断形式の fixture を追加する。裁定の「stderr の文字列」という入力契約も実出力先に合わせて訂正する。

現 selftest `analyze:429` は、検出器が期待する空白区切り文字列を人工的に stderr へ直接書くため、この不一致を検査できません。

**A2 — 予算超過・目標達成後の失敗が符号検定へ入る。**

根拠：`analyze:288–320,334–335`、段4裁定の「超過走は表に残すが判定に使わない」。

対統計は `maximum` と `target` で制限されますが、失敗感度分析の wins／losses は **全 rows の無効走**から加算されます。`over_budget` と目標達成時点を参照しません。

例えば8対確定後、または20走上限後に L の失敗記録を追加すると、対表・主検定は同じまま、感度分析の E 勝数と片側 p が変わります。

**成果物への影響：** 事前登録上は判定対象外の走によって、失敗を含む符号検定の結論が変わる。

**是正案：** 最終採用対の完了時点と投入上限から解析対象窓を固定する。全投入の件数表は維持し、事前登録された感度分析には窓内だけを使う。目標達成後・上限後の失敗を追加しても検定結果が変わらない selftest を追加する。

## should

**A3 — slot 内の腕順は検査するが、slot の進行順を検査しない。**

根拠：`analyze:290–309`、段4裁定の固定投入順。

現実装は、隣接2走の slot が一致し、奇数 slot が E→L、偶数 slot が L→E なら採用します。slot 2 を先に完了し、その後 slot 1 を完了する入力も採用可能です。launcher も slot を引数として受け取り、進行順は保証しません。

**成果物への影響：** 事前登録と異なる時系列の対を、順序逸脱の表示なしに主対表へ採用する。

**是正案：** 現在の slot と取り直し状態を追跡し、未完了 slot を飛ばす投入・逆戻りを明示する。正常な取り直しと順序逸脱を別々に検査する。

**A4 — selftest は実関数を通すが、witness／時刻／隣接性の独立した検算が不足する。**

根拠：`analyze:383–479`。

合成ファイルを実 `inspect_run`／`analyze` に渡しており、検算器自体を stub してはいません。ただし、次は未被覆です。

- shard-1/2 に consumer がある L の1行要求。
- `[...]`／`@group` 付き consumer の正規化。
- hook 誤り、余分な witness、必要な witness の欠損。
- 異なる UTC offset で同一瞬間を表したときの H／D／tail の数値一致。
- 非隣接の有効走を飛び越して組まないことの独立した負例。

特に `438–447` の「無効走を飛び越さない」検査では、slot 1 が既に01/02で採用済みです。`used_slots` による除外でも通るため、隣接性だけの検査になっていません。

**成果物への影響：** 上記検算が壊れても selftest が緑となり、誤った有効走・対を採用できる。

**是正案：** 未採用の新しい slot を使う独立ケースと、各 witness 条件・時刻指標の固定期待値を追加する。

## nit

**A5 — probe の隔離範囲を「resolver と path だけ」と説明するのは狭すぎる。**

根拠：`test_real_repo_serialization.py:6438–6452,6472–6485`。

実際には `_repo_head`、singleton、memo module accessor、`_real_repo_locks` も差し替えています。ただし hook、prerequisites、barrier、cache writer／reader は実物であり、今回の結線検査を無効にはしません。

**成果物への影響：** 現在の走表・対表・判定は変わらない。

**是正案：** 「実 cache 公開・読取りを検査するが、実 repo lock と実 resolver の統合検査ではない」と説明を修正する。

## E 不変と L 経路

**E の通常実行経路は不変と判定します。** 前提は裁定どおり、新しい config に対して configure が1回だけ走ることです。

| patch 面 | unset／空での判定 |
|---|---|
| 定数・helper追加 | env を読むが属性を付けず、例外も出さない |
| `pytest_configure` への追加 | 既存 helper の順序を保ち、その後の処理へ進む |
| `_early_memo_selected` の属性検査 | 属性がないため、従来の worker／shard／narrowing 判定へ進む |
| configure-node以後 | 起動、workerinput、待機、collection通知時の分岐に変更なし |
| allowlist追加 | 未設定なら request に追加されない。空なら明示空を運ぶ、意図された transport 差分 |

根拠：`conftest.py:2318–2354,2552–2583,2948–2970`。不正値の UsageError は両 nonce 設定後の try 内で発生し、既存 except が両方を復元します。worker にも属性は付きますが、起動は controller のみです。worker の待ちは属性ではなく workerinput の job key で決まります。

**L の同期経路は実在します。**

`_early_memo_selected=False` → 早期jobなし → workerinputにjob keyなし → `_wait_early_memo_job` 即return → controllerのcollection通知 → 同期barrier、という経路です。

根拠：`conftest.py:2438–2441,2582–2583,2612–2653`。consumer が両 registry とも不在なら prerequisites がともに False となり、timing が設定されず stderr 行も出ません（`2497–2507`）。これは集計器の shard-1/2 の期待と一致します。

installed `xdist/dsession.py:287–307` は hook 復帰後に collection を scheduler へ渡して schedule します。同一 HEAD・run ID・nonce、登録済み consumer、正常な公開という条件で、L の consumer が同期 writer より先に読む反例は見つかりませんでした。cache 消失や登録漏れまで保証する判定ではありません。

## test の結線と L 環境での隔離

L 正例 `test_real_repo_serialization.py:6488–6514` は、実 `pytest_configure` → 属性 → 実 `pytest_configure_node` → 実 collection通知hook → 実 barrier → 実 memo writer を通します。

- consumer ID は `file::function[case]@group` となり、`conftest.py:819–840` の実正規化を通る。prerequisites の assert に加え、両 resolver の呼出し・cache 実在・reader 成功も検査するため、自己検査だけではない。
- 両 `_session_cache_path` は全引数に既定値があり、引数なしで呼べる（receipt `149–168`、oracle `145–163`）。probe の env と HEAD によって writer と同じ path になる。
- 新規 reader を生成して `get()` するため、writer の process cache を返しただけではない。calls 不変は再解決がないことを検査する。
- barrier は join 後に `sys.stderr` へ print するため、`capsys.readouterr().err` と整合する。

E 負例 `6517–6533` は `mock.patch.dict(os.environ)` 内で key を pop し、空ケースだけ空を設定します。外側の L token から隔離されています。実 job を join し、両 resolve と公開ファイルを確認しており、選択判定だけのテストではありません。

既存 test の L 環境での判定は次のとおりです。

| test | 判定と理由 |
|---|---|
| `starts_before_worker_collection_notification` | 維持。synthetic config は configure を通らず属性なし |
| `all_workers_wait_before_test_body_without_resolving` | 維持。同じ synthetic 起動と明示workerinputを使う |
| `order_rejects_collection_barrier_mutant` | 維持。再compile対象は `pytest_configure_node`。起動anchorは一意のまま |
| `parsed_narrowing_keeps_nonce_and_never_resolves` | 維持。属性なしで既存 narrowing／worker guard を検査 |
| `narrowing_destinations_match_real_parser` | 維持。属性なしで parser結果を検査 |
| `success_checks_shared_deadline_after_io` | 維持。明示job pathで待機を検査し、opt-out属性に依存しない |

根拠：同ファイル `550–557,6558–6799`。新しい属性経由テストだけで全既存testを証明するわけではありませんが、上記各経路の読解も整合します。

## env 配線と変異帰属

env は静的には全段成立します。

`run_tests.py:1290–1304` の環境コピー → `dispatch_compute.py:3695–3698` の存在判定による空文字採取 → `_job_run:1844–1845` の overlay → `run_tests.py:1509–1532` の shard child環境コピー → 通常のlocal xdist worker継承、という経路です。

新test `test_pegasus_dispatch_compute.py:6748–6782` は request生成と child overlay をそれぞれ実処理で検査します。fix1 の別requestは、stub schedulerが既に作るresultとの衝突を避けます。ただし、同一requestを端から端まで流す検査ではなく、同じenvironment契約の二段検査です。

確認した exact比較は明示 `environ` を渡しており外側tokenを拾いません。`hold_inventory` は既存2キーの transportを検査し、allowlist全体の旧集合を要求しません。pytester／実configure呼出しについても、今回確認した範囲で L token による赤の経路は見つかりませんでした。全受入の実証とは区別します。

| 変異 | 静的なkill帰属 |
|---|---|
| M1 | E負例 unset／empty。最初の helper=False assert で落ちる。configure結線まで到達してのkillではない |
| M2 | L正例の実configure後の属性assert |
| M3 | L正例で実configure-nodeがjobを起動し、workerinput不在assertに違反 |
| M4 | exact pinとrequest伝播test両ケース。伝播testはrequest比較で落ち、overlay段には到達しない |
| M5 | 不正値testの `pytest.raises` 不成立 |
| M6 | L正例の属性assertに加え、不正値testも `pytest.raises` 不成立 |

**M1〜M6すべて指定行への帰属は可能です。** 両層stubで対象が消える構造ではありません。ただし、M6の期待nodeをL正例だけで完全集合と扱うのは誤りです。M4もtoken／emptyの両nodeが対象です。

`_load_suite_conftest` はディスク上の `HERE / "conftest.py"` を別moduleとして読むため、裁定どおり独立cloneのそのファイルを変異させる必要があります。実際のkill全集合・baselineとの差分は、未実施の変異probeで確定してください。

## 集計器・履歴見積り・焦点走

集計器の通常の有効走検査は、rc、前後SHA、dirty、複製状態、env、3 shardのreport条件、timeline、offset付きtimestamp、selected集合digest、時刻非重複、job番号とstderr名、witnessを実装しています（`analyze:116–195,262–289`）。consumer正規化 `52–54` は現conftestと一致します。

Wilcoxon `208–235` は、今回の最大8対では平均順位を2倍整数化し、0差を除外して全符号を列挙します。登録された反例の片側p **17/64、14/64、1/64、1/16** と判定は整合します。m=0も判定不能です。selftestはこの部分を実関数で検査します。

timestampはoffsetを必須にしてepochへ変換します。SHA256SUMSも実際に再計算し、junit／report／対応stderr／stdoutの掲載を要求します。ただし receipt はlauncherがmanifestへ入れず、集計器も必須hash対象にしません。また receipt の終端状態・child rcは検査せず、job番号だけを参照します。「receipt内容全体まで独立に検算済み」とは報告できません。

`history:34–60,63–104` は shard_count=3、pytest_rc=0、timelineとoffsetを検査し、除外理由・日付範囲・分布を出します。Eはstderr mtimeで直近N件を選んでから適格性を検査する方式で、その標本選択も出力注記に明示されています。現在の成功対解析とは別の、仮説形成用資料として整合します。

`focus/focus2.log:32` は **1043 passed、1 skipped、failed 0、error 0、114.43秒**。赤のnodeidはありません。child rc=0とclean sweepも確認できます。末尾の `recording-unavailable:series-invalid` は記録診断で、pytest失敗ではありません。このlog自体は非受入形と明記しており、3 shardのE/L全走を証明するものではありません。

## 総括

- **must-fix：2件。** treatment failureの取りこぼし、超過走の符号検定混入。
- **E不変：支持。** 1 config／1 configureの通常経路で挙動・例外・nonce復元順序は整合。空envのrequest掲載は意図された差分。
- **L経路：成立。** 同期公開が配布に先行し、consumer不在なら両memoともprewarm・witnessなし。
- **env全段：静的に成立。** 空overlayも成立。全受入での実証は未確認。
- **M1〜M6：全て静的帰属可能。** M6には不正値testの追加killがある。期待node全集合は変異実走で確定が必要。
- **集計器の検算：部分承認。** 主検定・通常入力検算は整合するが、失敗分類と解析対象窓を修正するまで最終集計の承認はできない。