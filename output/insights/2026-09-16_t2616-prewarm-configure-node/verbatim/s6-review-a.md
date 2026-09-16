## 現物で確かめた事実

対象は `7e52e2405`。以下は**静的読解による判定**で、pytest・変異試験は実行していません。必読9ファイルは読取り可能でした。変更・commit はありません。探索した `tools/selection_contract.py` は存在せず、実際の import 先 `orchestrator/test_selection_contract.py` を確認しました。

参照略号：

| 略号 | ファイル |
|---|---|
| C | [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/conftest.py) |
| R | [real_repo_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/real_repo_receipt_memo.py) |
| O | [sort_swo_oracle_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/sort_swo_oracle_receipt_memo.py) |
| T | [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_real_repo_serialization.py) |
| S | [s4-ruling.md](/home/SFC/tanab/.claude/jobs/774bd912/tmp/wave-artifacts/dev-wave-t2616-prewarm-configure-node/s4-ruling.md) |

外部ライブラリの行番号は `/home/SFC/tanab/.local/lib/python3.10/site-packages/` 配下です。

- **[refuted] 48 node による重複起動は、現在の xdist 経路では起きません。** `xdist/workermanage.py:97` は node を逐次 setup し、同:342 が同期的に configure hook を呼びます。C:2302 で job を保存してから thread を起動するため、次の node は既存 job を使います。再起動イベントも `xdist/dsession.py:146` の逐次処理です。一般の並行呼出しに対する排他はありませんが、その呼出し元は確認できません。**変異:** C:2267 を常に `job = None` にする。T:6025 の2回目 configure で marker 作成衝突または再起動を検出できます。

- **[refuted] 早期起動失敗が nonce の整合を壊す経路はありません。** C:2470、2489 の伝播が C:2491 の起動より前です。起動処理は nonce を変更せず、同期例外なら `xdist/workermanage.py:349` の workerinput 送信へ進みません。**変異:** R1 不成立の return を C:2470 より前へ移す。T:6122 の nonce assertion が落ちます。

- **[refuted] controller／非受入 worker の誤待機は確認できません。** C:2347 は `config.workerinput` の明示キーだけを見ます。controller に保存する job 属性や継承環境から待機しません。非受入 node には C:2490 がキーを配らず、C:2349 で戻ります。**変異:** 明示キー判定を外し、環境から cache path を組み立てて待つ。非受入 worker の通知前待機と controller の通知後 fallback が循環します。通知位置は `xdist/remote.py:257`、fallback は C:2558。

## 追加された 8 本が落とす変異 (1 本 1 行)

以下の「落とす」は読解上の予測です。

| 判定 | テスト | 具体的な変異と赤になる根拠 |
|---|---|---|
| [refuted] 恒真ではない | `test_early_memo_starts_before_worker_collection_notification` | C:2491 の早期起動を削除して collection 後 barrier に戻す → 通知呼出し T:6027 より前の `started.wait()`、T:6022 が失敗。 |
| [refuted] 恒真ではない | `test_early_memo_all_workers_wait_before_test_body_without_resolving` | C:2447 の worker 待機を削除 → reader が `_locked` に到達せず、T:6080 が失敗。 |
| [refuted] 恒真ではない | `test_early_memo_order_rejects_collection_barrier_mutant` | 呼び出す正例テストを即 return に骨抜き → T:6106 が期待する AssertionError が発生せず失敗。負例検証の検査であり、独立した本番順序 probe ではない。 |
| [refuted] 恒真ではない | `test_early_memo_parsed_narrowing_keeps_nonce_and_never_resolves` | C:2245 から `keyword` を除去 → job が announce され、T:6121 が失敗。ただし実 parsed option との対応には後述の穴がある。 |
| [refuted] 恒真ではない | `test_early_memo_publication_wait_is_explicit_bounded_and_fail_closed` | R:655／O:705 の `.failed` 優先検査を削除 → 本体を返し、T:6170 が期待する例外が出ない。 |
| [refuted] 恒真ではない | `test_early_memo_unlock_failure_never_publishes_ready` | R:503／O:523 の unlock 失敗送出を成功扱いへ変更 → T:6214 の終了処理が例外を返さず失敗。 |
| [refuted] 恒真ではない | `test_early_memo_stale_markers_are_pruned_except_current_job` | R:390／O:406 の `.pending` prune pattern を削除 → 古い marker が残り T:6241 が失敗。 |
| [refuted] 恒真ではない | `test_early_memo_close_failure_and_lock_contention_are_fail_closed` | R:510／O:530 の close 失敗送出を成功扱いへ変更 → T:6265 の終了処理が例外を返さず失敗。 |

## 裁定 R1〜R8 との照合 (項ごとに満たす / 満たさない)

| 項 | 判定 | 根拠・暴く変異 |
|---|---|---|
| R1 | **[real] 満たさない** | C:2244 の option 名に誤りと不足があります。`failedfirst=True`、`stepwise=True`、選択を縮める `override_ini` が通過します。**入力変異:** T:6114 の `("ff", True)` を `("failedfirst", True)` に変更。T:6121 が失敗します。 |
| R2 | **[refuted] 満たす** | C:2470〜2489 で nonce／台帳を伝播後、C:2490 で選択判定。**変異:** 発火条件による return を伝播前へ移す → T:6122 が失敗。 |
| R3 | **[refuted] 満たす** | marker は C:2295、thread 起動は C:2332。identity は C:2343、明示待機は C:2348。R:655／O:705 は failed 優先、retry は `_locked` の外。**変異:** failed 検査を削る → T:6170 が失敗。 |
| R4 | **[refuted] retry の待ち予算は満たす** | 定数は R:54／O:46 の120秒、C:2358 の deadline を両 memo で共有し、R:652／O:702 でも上限を縮めます。**変異:** 定数を130秒へ変更 → T:6178 が失敗。I/O 全体の実 wall の上限を実測した結論ではありません。 |
| R5 | **[unknown] 充足未確認** | S:126、127、132 が要求する新規赤0件・canonical 最遅 wall・300秒未満は、この静的レビューでは確認できません。**入力変異:** 赤0件・最遅301秒の結果を完了扱いする。S:132 に違反します。 |
| R6 | **[refuted] 指定された変異検出を満たす** | T:6022 が通知前の resolver 到達を要求。**変異:** C:2491 を削除し旧 barrier に戻す → 同 assertion が失敗。 |
| R7 | **[refuted] 差分上は満たす** | T の変更は335行追加のみ。既存 guard pin は T:4886、4 key pin は T:4866、空 stderr pin は `test_run_tests_task_run.py:902` に残っています。**変異:** timing payload に key を追加 → T:4866 が失敗。 |
| R8 | **[unknown] 実測条件は充足未確認** | C:2308 は consumer 不在でも起動します。S:167 の shard 別 wall 確認は未検証です。**変異:** consumer 不在 shard の resolver に遅延を追加。最遅 shard の交代を受入実測で検出する必要があります。 |

## 恒真・過剰 stub の疑い

- **[refuted] M-3 が新しい正例を素通りする、という疑いは反証できます。** T:6019 の configure 後、T:6022 を通るまで collection callback は一度も呼ばれません。起動を旧 barrier へ戻すと `started` を立てる実行主体がなくなります。**変異:** C:2491 の起動削除。正例は意味のある順序 assertion で赤になります。

  負例テスト T:6093 は、その変異を内部注入し、**正例が赤になったことを捕捉して自身は緑になる**構造です。外部から同じ行を削除すれば負例テスト自身も T:6100 の anchor 不一致で赤になりますが、その構文的な赤を R6 の検出証拠には数えません。

- **[refuted] stub の数だけを理由に、cache 公開・待機検査を恒真とは判定できません。** T:5970 の `_repo_head`、T:5972 の `_cache_path_for`、T:5979 の `_resolve_now` は実体へ委譲しない stub です。一方、memo の writer/getter、JSON store/load、cache の `flock` は実体を通ります。T:6059 の `_locked` は実体へ委譲する観測 wrapper です。**変異:** `.failed` 優先検査を削除 → T:6170 は実 reader の成功を検出して赤になります。

- **[real] repo lock の検査は、この8本では迂回されています。** T:5984 は `_real_repo_locks` を `nullcontext` に置換しており、観測 wrapper ではありません。cache lock の実行を、repo lock の実行証拠にはできません。**変異:** C:899／958 の repo lock を `nullcontext` に変更。この8本の観測は変わりません。これは検査範囲の穴であり、現実装が repo lock を欠いているという指摘ではありません。

- **[real] `publication-regressed` は production 経路で到達不能です。** C:2361／2362 は新規 instance に対して一度だけ `get(early_job=...)` します。集合は R:421／O:436 で空、追加は成功して return する直前の R:684／O:737。したがって、その同じ instance が集合を読む R:661／O:711 に再到達しません。T:6168〜6175 だけが同じ reader を再利用しています。**変異:** `_early_ready_paths` の追加と判定を削除。本番挙動は変わらず、T:6175 だけがその防壁の消失を訴えます。

  ただし、**本体消失への fail-closed がすべて失われるわけではありません。** 新規 reader や通常 consumer が本体不在を読む場合は R:667／O:717 の `cache-missing`、failed は R:655／O:705 で拒否します。

## 見落としている退行

- **[real] R1 の `--ff` 検査は、存在しない parsed 属性を検査しています。** `_pytest/cacheprovider.py:489` の destination は `failedfirst`。C:2245 の `ff`／`last_failed` では拾えません。`--last-failed` は同:482 の `lf` なので、こちらは閉じています。**入力変異:** T:6114 の `ff=True` を実 parser と同じ `failedfirst=True` にする。早期 job が発火します。なお通常の `--ff` は並べ替えですが、R1 は明示的に除外を要求しており、さらに `--ff --lfnf=none` は履歴が空なら同:406〜409 で全件 deselect します。

- **[real] `--stepwise`／`--sw-skip` による narrowing が漏れます。** `_pytest/stepwise.py:30` は `stepwise`、同:55 は skip 指定から同属性を有効化し、同:170〜172 が前回失敗位置より前の item を除外します。C:2244 に該当属性がありません。**入力変異:** suite root・spec を維持し `stepwise=True` と有効な前回失敗履歴を追加。collection は縮むのに早期起動します。

- **[real] `-o` による collection 選択変更も漏れます。** `_pytest/helpconfig.py:115` の parsed 属性は `override_ini`。`-o python_files=test_selected.py` は `_pytest/python.py:199`、`-o python_functions=test_selected` は同:355、388 で選択を縮めます。C:2260 と C:1925 のどちらも拒否しません。**入力変異:** 全 suite の argv に `-o python_files=test_selected.py` を追加。R1 の全 suite 判定は真のままです。

- **[refuted] 指定された9項目について、空値の truthiness による実 narrowing の取り逃しは確認できません。** `-k ''`／`-m ''` は `_pytest/mark/__init__.py:209`／257 自身が選択変更なしとして戻ります。`--deselect=` は空文字ではなく `['']` となり truthy なので拒否されます。ignore 系も append 型です（`_pytest/main.py:163`、169、175）。**入力変異:** `--deselect=` を与える。全 node に一致する危険な空 prefix でも gate は閉じます。

- **[refuted] `PYTEST_ADDOPTS`／ini addopts 経由の、列挙済み selector は閉じます。** `_pytest/config/__init__.py:1523`、1560 が parse 前に追加するため、`keyword`、`lf`、`deselect`、`ignore` 等は C:2260 で検出されます。**入力変異:** argv を suite root のまま `PYTEST_ADDOPTS='--deselect=orchestrator/tests/'` にする。parsed `deselect` が truthy となり起動しません。上記の属性名不足は別問題として残ります。

## 総括

**[real] R1 は未充足です。** 実 parser の `failedfirst`、`stepwise`、選択を縮める `override_ini` を通す経路があります（C:2244、T:6114）。まず `ff=True` を `failedfirst=True` に置き換える入力変異で、追加検査と実 parser のずれを露出できます。

**[real] `publication-regressed` は、本番では働かない防壁です。** C:2361 の instance 使い捨てにより、状態追跡を削除しても本番挙動が変わりません。テストだけの再読成功を本番保証に数えるべきではありません。

**[refuted] R6 の主たる検査は恒真ではありません。** 早期起動を削って collection 後へ戻す変異は T:6022 で落ちます。R5／R8 の受入・時間条件については、静的読解から合格とは判定できません。