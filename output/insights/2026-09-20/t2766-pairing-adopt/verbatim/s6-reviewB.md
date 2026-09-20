## 所見

静的レビューの結論は **must-fix 1件、should 2件**です。実装の既定 on 化とテスト変更は概ね仕様どおりですが、集計器の入力契約は測定開始前に整合させる必要があります。pytest・変異・selftest はこのレビューでは実行していません。

位置の略記：`C` = `orchestrator/tests/conftest.py`、`T` = `orchestrator/tests/test_acceptance_schedule_order.py`、`A` = 指定された `probe/t2766_adopt_analyze.py`、`L` = 指定された xdist `loadscope.py`。

| # | 所見 | 位置 (file:line) | real/refuted | 重さ | scope | 根拠 | 提案 |
|---|---|---|---|---|---|---|---|
| 1 | 集計器が段4で指定した入力を受け付けない | `s4-ruling.md:25`、`A:277`、`A:419`、`A:936` | real | must-fix | 内 | 指定は `arm, tip_tested, started, finished, leaders_at_go, load1_at_go`。実装は `condition, tip_sha, submitted_at, finished_at, other_leaders, load1` を使用する。さらに `tip_after, verdict, dirty_lines_*, copy_ok, session_dir, env, pair_slot` と CLI の `--a-tips/--b-tips` が必要。指定どおりの入力では走が無効になり、時刻検査で例外終了する。selftest は実装独自の形式を生成するため、この不一致を検出しない | 親の入力生成と集計器を一つの明示した契約に統一し、その契約の最小入力を使った結合検査を追加する |
| 2 | 負荷・他 leader 数の欠落が有効走として通る | `A:277`、`A:495`、`A:701` | real | should | 内 | `other_leaders` と `load1` は表示時に `.get()` するだけで、欠落しても有効性に影響しない。段4の名称では値が存在していても表は `None` になる。selftest は両項目を常に投入している | #1 の統一時に必須観測項目を検査し、欠落を明示する。少なくとも欠落したまま条件差記録が完了したと扱わない |
| 3 | cardinality 検算の完全性には nodeid 一意性が必要 | `C:1787`、`C:1812`、`L:367` | real | should | 内（境界の明示） | 本番 helper は item リスト長、xdist は nodeid をキーとする辞書長を使う。異なる item が同一 nodeid を持つと両者の cardinality が異なる。下記の具体例では検算と identity guard が通っても実配布順が変わる。X1 からの既存境界であり、今回導入された回帰ではない | 「nodeid が一意な受入 collection」という同値性の前提を明記する。重複入力への対応拡張は別扱いとし、今回の採用に新しい gate を追加しない |
| 4 | hook 分岐の統合が selected・hold・marker・既存 property・identity を変更する | `C:1765`、`C:1822`、`C:2321`、`T:1931` | refuted | must-fix相当の疑義・不成立 | 内 | 選別・hold 処理・real-repo suffix 処理は変更されていない。pairing は scope 別 unit の置換であり、unit 内 item 順も保持する。既存 property には追記のみ。置換前後の identity multiset 検査も存続する | 修正不要。cardinality 不成立時の拒否は明示された仕様として区別する |
| 5 | controller／worker、無効化経路、空台帳、短 queue が退行する | `C:1824`、`C:1856`、`C:1886`、`C:1925`、`C:2333` | refuted | must-fix相当の疑義・不成立 | 内 | controller は worker 値 `""`、worker は `workerinput.workerid`。options／reordering が false なら呼ばれない。空台帳・known unit ゼロは従来どおり return。96 unit 未満では pairing helper が入力順を返し property を付けない | 「短 queue 無変更」は従来の duration sort まで無効になる意味ではなく、pairing による追加変更なしと読む |
| 6 | 旧 env gate が実装に残る／負例が自己比較になる | `T:1763`、`T:1841`、`tools/pegasus/dispatch_compute.py:118` | refuted | must-fix相当の疑義・不成立 | 内 | 隠し・ignore 対象を含む Python 検索で旧 env 参照は要求された負例の1か所のみ。通常検索の他の一致は前 wave の保存資料。負例4値は固定 `_PAIRING_B_UNITS` と literal property に照合し、実装の実行結果を期待値に再利用しない | 挙動上の env 非依存を検出できる。無影響な「読むだけ」の操作まで検出するテストではないが、現実装には読み取り自体がない |
| 7 | G8/G12 の変更が検出力を不当に落としている | `T:1169`、`T:1797`、`T:1842`、`T:1931` | refuted | must-fix相当の疑義・不成立 | 内 | G8 は恒等 seam を明記し、unknown の位置96・knownとの隣接・空台帳の key 計算禁止・置換ゼロを維持。G12 の旧 off 状態検査は既定 on の marker・identity・既存 property 保全へ移された。invalid token 拒否と enabled=False は撤去した機能の検査。固定順を本番 pairing helper から算出していない | 修正不要。G8 単体が pairing 配線を検査しない点は G12 が補う |
| 8 | witness が本番 helper の自己検証になっている | `A:7`、`A:62`、`A:92`、`A:137` | refuted | must-fix相当の疑義・不成立 | 内 | import は標準ライブラリのみ。selected と JUnit の被覆、runtime scope、台帳 cost を独立に復元する。rank の全被覆・一意対応、rank 48〜95 と partner 集合、head の cardinality別 cost 多重集合、partner cost 多重集合を検査する | 独立性は成立。ただし cost 比較は厳密一致ではなく `rel_tol=abs_tol=1e-9` の許容差付き |
| 9 | A property、tip、main 移動、判定枝の検査がない | `A:147`、`A:283`、`A:326`、`A:358`、`A:647`、`A:723`、`A:851` | refuted | must-fix相当の疑義・不成立 | 内 | A は property 0件を要求。tip は arm別の外部指定集合に照合し終了後 tip と一致を要求。`main_moved` は tested_main 同士の比較。判定は3有効対、全Δ正、中央値率10%で分岐し、無効対は同順序で再試行する。selftest に (i)/(ii)/(iii)、ゼロ、退行、反復不足、tip更新・誤arm・main移動の各検査が存在する | #1 を解消して利用する。許容 tip の Git 上の正当性自体は親が検証する契約 |
| 10 | author が pytest 成功を誤報している／親の焦点走が不足する | `s5-author.md:34`、`focus1-summary.txt:1` | refuted | must-fix相当の疑義・不成立 | 内 | author は pytest 全件を未実走と記載。親要約の11ファイルは対象2＋列挙されたメタテスト9を覆い、`1210 passed, 7 skipped, rc=0`。patch は repo 4ファイル、報告の5番目は別提供の集計器なので矛盾しない。dispatch 本体・対応テストは指定 main SHA と差分ゼロも確認できた | 焦点走の7 skip の内訳と変異結果は要約から確定できない。変異・実受入の成功には数えない |

## xdist の同値性と具体的な反例

**nodeid が一意なら同値です。** scope の初出順を維持する辞書に対して、両実装とも cardinality 降順の安定 sort を行います。本番 caller は scope ごとに一つの unit を作るため、検算が比較する scope 列も一意です。この前提では意図順を変える並べ替えをすべて検出します。

一意性を外すと次の fixture が反例になります。

- `u000`〜`u095` の96 unit を作り、各 unit を2 item とする。
- `u000` の2 item だけは別 identity・同一 nodeid。他の unit は各2個の異なる nodeid。
- unit cost を `960, 950, …, 10` とする。

helper の cardinality は全 unit が2なので、paired 順は `u000..u047, u095..u048` となり検算を通過します。item identity の多重集合も保存されます。しかし xdist は `u000` を辞書長1、他を2と数え、`u000` を末尾へ移します。

したがって、「すべて捕まえる」は一意な nodeid という前提付きです。この重複入力が現在の実受入に存在する証拠はありません。

## 変異の帰属

各対象は指定の関数内で一意です。M4/M5 は **該当 if ブロック全体の削除**として扱います。if 行だけの削除による構文エラーや無条件実行は別変異です。

| # | 所見 | 位置 (file:line) | real/refuted | 重さ | scope | 根拠 | 提案 |
|---|---|---|---|---|---|---|---|
| M1 | 固定 partner 列へ帰属できる | `C:1792`、`T:1820` | refuted（帰属不能の疑義） | must-fix相当の疑義・不成立 | 内 | cost は fixture 内で異なり、降順化すると期待した低 cost partner 列が変わる。正例 fixture は cardinality 検算で先に落ちない | 正例の partner 列不一致を kill 理由として記録 |
| M2 | head 幅47の境界差へ帰属できる | `C:1790`、`T:1817` | refuted（同上） | must-fix相当の疑義・不成立 | 内 | 48個目が `u047` から `u119` になり、最初の head assert で落ちる。cardinality は成立する | head assert の失敗を記録 |
| M3' | pairing 不発へ帰属できるが、kill は正例／JUnit だけではない | `C:1869`、`T:1867`、`T:1904` | refuted（同上） | must-fix相当の疑義・不成立 | 内 | 順序・property・cardinality拒否の各検査が失われる。JUnit test の最初の失敗は collection 順であり、XML property assertion まで到達しない | 下記10 nodeを期待集合とする。JUnit property 欠落への帰属は M5 で確認 |
| M4 | cardinality拒否の欠落へ帰属できる | `C:1812`、`T:1870` | refuted（同上） | must-fix相当の疑義・不成立 | 内 | `double_units=49` では pairing が不成立。検算を除くと wrapper が正常終了し、`pytest.raises` が失敗する | `DID NOT RAISE` を確認 |
| M5 | property付与欠落へ帰属できる | `C:1873`、`T:1829`、`T:1913` | refuted（同上） | must-fix相当の疑義・不成立 | 内 | pairing 順は維持されるため、正例の property assert と JUnit の property assert へ到達する | collection 順と子pytestの119 pass／1 skipが先に成立したことを確認 |

`_run_live` は対象 ROOT を `PYTHONPATH` に含め、子pytestが本番 conftest を import する構造です。静的には別コードへの固定参照による mask は見つかりません。ただし独立 clone 上の実際の import 先と最初の失敗理由は、親の変異ログで確定してください。

## 総括

**must-fix：1件。should：2件。** must-fix は集計器と段4の入力契約不一致です。

- M1：静的帰属成立。固定 partner 列の不一致。
- M2：静的帰属成立。head の48個目の不一致。
- M3'：静的帰属成立。既定 pairing 不発。JUnit node はまず collection 順で落ちる。
- M4：静的帰属成立。cardinality 負例の `UsageError` 不発。
- M5：静的帰属成立。順序検査通過後の property 欠落。

M3' の kill 予測 node 集合は、次の **10 node** です。全行に `orchestrator/tests/test_acceptance_schedule_order.py::` を前置します。末尾 `[]` は空文字パラメータです。

```text
test_g12_pairing_queue_and_all_item_witness
test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[t2766-min-cost-partners]
test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[off]
test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[0]
test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[]
test_g12_cardinality_infeasible_fails_closed
test_g12_collection_is_worker_count_independent
test_g12_live_junit_witness_includes_skips_and_execution_worker
test_g12_holds_shard_selection_and_real_repo_suffix_survive
test_g12_real_distribution_second_unit_counterexample
```

**受理集合不変の結論：仕様で要求する cardinality 不成立時の拒否を除き、既定 on 化による selected・hold・group・unit 境界・marker・既存 property・item identity の変更は静的に認められません。**