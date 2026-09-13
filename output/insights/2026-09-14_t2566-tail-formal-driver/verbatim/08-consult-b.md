## 所見

以下、`plan` は指定された `04-plan.md`、repo 内の相対パスは本 worktree を指す。静的検査と保存 bytes の検算のみ実施した。probe・pytest は未実行。

### B1 — real：投入・job・cohort 集約の入口が計画から抜けている

- **主張:** Python consumer を実装しても、既存の投入経路からは起動できない。「本走投入の唯一の blocker が外れる」とは言えない。
- **根拠:** `tools/pegasus/submit_b10_backoff_grid.sh:36` と `tools/pegasus/b10_backoff_grid.sh:186` は旧 3 run kind だけを受理する。job script の `:587` は `backoff_extended_sweep.py` を起動し、`:638,656` の完了確認も旧 stem を使う。plan `:7–26,41–43` は新 module と scheduler 情報取得を挙げるが、投入 script、CLI、三 campaign を集めて `analyze_cohort` を呼ぶ実行主体を割り当てていない。
- **壊れ方:** 新 run kind は shell 境界で拒否される。関数単位の五 probe が成功しても、三 job の実行・集約・完了成果物までつながらない。
- **深刻度:** **高。裁定パッケージ候補。** 本走の「実投入」は scope 外でよいが、専用投入/job wrapper、事前登録 commit の転送、三 campaign の report 集約入口を今回実装するか、次 wave の明示 blocker とするかを確定する必要がある。

### B2 — real：spec の因果的な利用を示す正の変異が無い

- **主張:** 設計上は spec を引数化しているが、予定された probe では「読んだだけ」を十分に排除できない。
- **根拠:** plan `:19–21,30` は spec 駆動を指定する。一方、条件 1 の `:142` は変異の拒否を確認するだけで、許容される変更によって測定引数・解析値が変わる正例を指定していない。現物では `runner.py:1097` 付近が flags を生成し、`pipeline.py:1355` 付近が `PerfConfig` の値を測定へ渡す。
- **壊れ方:** spec と固定値の一致を検査した後、固定値を使う実装でも、現行 spec の成功と変異拒否の双方を満たせる。解析閾値についても同様。
- **深刻度:** **中。** 試験用 spec の `execution.records` を変更し、同じ production 引数生成経路で `-ycsb_tuple_num` が変わる正例を追加する。解析では `variability.maximum_cv_exclusive` を変え、同じ観測の gate 結果が変わる正例が使える。登録済み文書の改変や変更条件での実計測は不要。

### B3 — real：親の三所有分割と plan のファイル配置が両立していない

- **主張:** 段 5 の所有と、loader binding を成立させる commit の実行主体を組み直す必要がある。
- **根拠:** brief `:45–46` は A＝consumer/hash、B＝整数保存・再計算、C＝driver/loader/report と分ける。plan `:15–26` は A と C の責務、整数再計算を同じ新 module に置き、`:129` はテストも一 file に集める。`docs/dev-wave/workers.md:20` は編集 path 所有を素集合にする契約。`docs/dev-wave/core.md:30` は commit を親の担当とする。
- **壊れ方:** 責務名だけで並列投入すると所有 path が重なる。また「編集後 commit してから焦点走」を子の義務として渡すと、子の commit 権限と衝突する。
- **深刻度:** **中。** ファイル所有を再分割するか依存順に直列化し、親が統合・commit した snapshot で焦点走する手順を明記する。段 6 の修正後も同じ手順が必要。

### B4 — real：焦点走の consumer 列挙には漏れがある

- **主張:** 「参照関係から得た焦点走」の列挙は完全ではない。
- **根拠:** `orchestrator/tests/test_screening_opt_in.py:31–34` は変更対象 `campaign/loop.py` の全文を読み、`ScreeningConfig` と `screening=` の不存在を検査する。この file は plan の焦点走一覧に無い。
- **壊れ方:** 新引数の配線・説明追加で文字列検査を壊しても予定の焦点走では捕まらない。
- **深刻度:** **低。** 必須登録簿への追加漏れではなく、既存 consumer test の実行漏れ。テストの期待値を緩めず対象へ加える。

### B5 — refuted：hash の混同と、代替 stdout の不存在

- **主張:** この二つの疑いは現物により反証された。
- **根拠:** plan `:16,18` と「hash 定義」「marker 抽出」は raw bytes と Git object ID を分離している。独立抽出結果も一致した。指定 T-139 file は実在し、提示された四値が一致した。
- **壊れ方:** 当該プラン記述には確認できなかった。
- **深刻度:** **無し。** 実装後の適合確認は別途必要。

## hash 定義の検算

対象は `docs/b10-backoff-static-tail-preregistration.md`。

| 項目 | 実測結果 |
|---|---|
| 完全な開始 marker 行 | 452 行、1 件 |
| 完全な終了 marker 行 | 976 行、1 件 |
| 除去する fence | 453 行と 975 行 |
| hash 対象の JSON | 454–974 行、末尾 LF を含む |
| raw file 内の byte 範囲 | **`[33673, 60884)`**、0 起点・終端排他 |
| 抽出長 | **27211 bytes** |
| 改行・parse | CR 0 件、末尾改行 1 個、UTF-8 JSON として parse 成功、top-level 17 section |

検算値：

```text
document_blob_sha256
8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a

spec_sha256
08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef

HEAD の Git blob ID（別物）
6eb354afd5119d487470cd60d0972f5806caeb42
```

`splitlines(keepends=True)` による行単位抽出と、marker/fence の byte offset による直接 slice を独立に作り、**bytes 完全一致**を確認した。plan の `extract_spec_bytes(raw)` の記述と一致する。

先例 `b10_backoff_shape_sweep.py:358` の regex は CRLF を許し、capture の外で JSON 終端改行を消費する。これを転用すると今回の定義と一致しない。plan は転用を明示的に禁じており、この攻撃は refuted。

## 登録簿の数え上げ

既存 driver の path 検索と、registry／呼出し識別子の検索を実施した。

| 登録・検査面 | 判定 |
|---|---|
| `_REVIEWED_PERF_FILES`、`_REVIEWED_PREDICATES`、guard 群 | plan に計上済み。新関数の実 call site 確定後に件数照合が必要 |
| `test_campaign.py` の二つの Counter と総数 pin | 計上済み |
| `MACHINE_CALLERS` | 計上済み。`test_p3_build_authority_cli.py:1203` は generator receipt の文字列も要求する |
| manual-build 在庫 | 新 module が `--build` を含まなければ変更不要。現物 `:1217` は AST でなく全文の文字列検索なので、コメントに書いても対象になる |
| spawn Counter 群 | 計上済み。Git／scheduler の実 subprocess 呼出し箇所数で登録する。「機能が二つ」と「call site が二つ」は別 |
| Layer3 の payload 閉包 | 計上済み。新 `reps` を旧 schema の受理対象外にする方針も明記済み |
| `acceptance_duration_ledger.json` | 計上済み。成功 JUnit 後の更新という順序も妥当 |
| 同居関係文書 | `docs/test-environment-coincidence-ledger.md:326` は過去 wave の先送り一覧。新 module の常設登録簿ではない |

**別の引き方で確認したもの：**

- hash／golden の構文検索で `test_backoff_extended_sweep.py:2010` の凍結 tree 全 bytes の SHA-256 pin を確認した。今回の予定変更先とは別で、更新不要。
- `test_official_perf_closure.py:602` は別テストの AST から `expected_inventory` を抽出する。plan が関数名・変数名・Counter 構造を維持する必要がある。
- `test_layer3_report.py:993` 以降の AST 検査は plan に計上済み。
- `test_real_repo_serialization.py:52,1580` と `conftest.py:647` に実 repo 使用 node の独立 golden／登録がある。plan は前者を実行対象に含めるが、新 probe の資源使用分類までは指定していない。実 repo を使う試験の実装に応じて確認する対象であり、現段階で必須追加とは断定しない。
- 全文文字列検査から、所見 B4 の consumer 漏れを確認した。

追加の**必須 production 登録簿の漏れ**や、今回編集する file 全体を固定 SHA-256／固定行番号で pin した未計上テストは、今回の検索では確定できなかった。未実装 module の最終 call site 閉包まで確認済みとはしない。

## probe が production 経路を通るかの判定

| 投入前条件 | 判定 |
|---|---|
| **1：consumer 発火** | `load → parse → config → driver 測定直前境界` は妥当。ただし B2 の正の変異が不足。測定引数への到達を確認し、設定 dict の表示だけで終了させない |
| **2：整数保存・再計算** | **計画された経路なら通る。** `runner.run_once:663` の subprocess 境界から、`:712` 付近の stdout parser、`measure_point:1160` 付近、`pipeline._run_bench:1299`、`:1485` の writer まで到達できる |
| **3：出所導出** | **成功側の試験 campaign が必要、という plan は正しい。** production writer の lock/WAL を実 admission・replay・raw 行対応付けに通す。探索 WAL は formal loader の拒否側と mode 比較側に限定する |
| **4：五本の正しさ記録** | **計画された経路なら通る。** `_execute_verification_repetition:483` は実 verifier を呼べる。`:2098` が各 verify を emit、`:2153–2156` が反復と即時 reject を実装する |
| **5：mode 記録・比較** | 条件 4 の新規発行記録を使えば妥当。探索の `legacy` を読むだけでなく、本走 loader/report まで五本すべてを追う必要があり、plan はこれを指定している |

条件 2 の実入力は確認済み：

```text
output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log
SHA-256:
739755560fbc6bff2fcd14cd84db37e65b7af1ba1618c392db50f9f1de8e5ef0

13行 abort_counts_:  24435129
15行 commit_counts_: 2270481
18行 abort_rate:     0.9150
21行 throughput[tps]:756827

整数比 = 0.914981121944041
```

隣接する R02–R05 も実在し、両整数カウンタと throughput を持つ。ただし throughput は約 76 万〜1071 万と大きく異なる。**五入力の保存成功を、CV gate を通る cohort の成功と混同しないこと。**

投入方法は、実 `measure_point` に保存 stdout を返す `subprocess_runner` を渡す薄い adapter を使える。`run_once` や `measure_point` の戻り値そのものを合成してはいけない。deferred 側は `text=False` に合わせて bytes を返し、`.open()` まで通す。

条件 4 の参考 fixture `test_campaign.py:5998` は実 verifier を使うが、同 helper は `:6037` 付近で **`measure_point` と `remeasure_until_stable` を fake に置換する**。条件 4 の参考にはなるが、そのまま条件 2 の保存経路の証明に流用できない。

## 親 brief と実測前提への反証

- **探索の生 CCBench stdout を使えるという前提は未成立。** 許可された explore root の `abort_counts_|commit_counts_` 検索は 0 件。job の `.stdout` は存在するが、必要な整数カウンタを含む保存 stdout は確認できない。plan の入力補強は正しい。
- **「WAL 行の key は四つだけ」は字義どおりには誤り。** balanced WAL の実 key は `env_tag,payload,stage,ts,variant` の五つ。payload を除く四座標、という限定なら正しい。
- **`tps` が浮動小数五件という記述は正確でない。** 保存 JSON の最初の配列は `[3958382,3752160,3727702,3692363,3695293]` という整数。数値配列という主旨には影響しない。
- **確認できた一致:** WAL 25 行、五 stage 各 5 件、bench payload 14 key、verify payload 9 key、mode `legacy`、最初の verify の commits `630878`／aborts `240566`、最初の bench の丸め率 `0.6869` は一致した。
- **runner アンカーが片側という plan の指摘は正しい。** `capture_measure_point:803` と通常の `measure_point:1064` は別実装。
- **manual-build の一般化と同居関係文書の扱いについても plan が正しい。** 根拠は上の登録簿表のとおり。
- **loader binding の説明にも厳密化が必要。** `verify_live_contract_loader_binding:535` が照合するのは、常に HEAD ではなく **binding に記録された commit** の blob。HEAD と作業木の一致を要求するのはその直前の binding 作成経路。新規試験用 binding を commit 後に作る手順は妥当だが、古い binding は commit しただけでは更新されない。
- **現在の識別子出現数は 0 ではない。** 事前登録自身に加え、`docs/archive/worklog-phase3-0910-1418.md:673–674`、過去レビュー成果物にも出現する。一方、今回の検索で同名の production 実装・既存 report schema 定義は見つからず、実行上の衝突という疑いは refuted。
- **「唯一の blocker」は過大。** B1 の未配線に加え、実投入時の環境・cohort・時間契約は五 probe の成功からは導けない。

## 総括

hash の区別と marker 抽出は、現物の bytes で一致した。  
代替 T-139 stdout は実在し、提示された四値も正しい。  
五 probe は production 経路を通せる設計だが、実行済みではない。  
投入/job/cohort 集約の入口は未割当であり、裁定パッケージ候補として残す。  
spec の正の変異、段 5 の path 所有・親 commit 手順、焦点走の consumer 漏れを修正すべきである。  
実装・編集・commit・性能測定は行っていない。