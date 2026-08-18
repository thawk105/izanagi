## 所見

1. **[Critical] 公開端負例は serial L1 しか殺さず、xdist miss 専用の fail-open が生存する**

   `test_receipt_memo_public_endpoint_is_fail_closed_before_prewarm` は環境から `PYTEST_XDIST_TESTRUNUID` を削除して公開端を呼ぶため、検査するのは `cache-path-unavailable` の serial 分岐だけである（`orchestrator/tests/test_s8b_binding_driftguards.py:425-450`）。

   例えば公開 `real_repo_receipt()` に「`ReceiptMemoError` を捕捉し、xdist UID がある場合だけ `_PRODUCTION_RESOLVE(root=ROOT)` へ戻す」分岐を足すと、次がすべて緑のままになりうる。

   - 公開端負例は UID なしなので従来どおり例外になる。
   - L1〜L5 は private `_ReceiptMemo.get()` を直接検査しており、公開 wrapper の分岐を通らない（`test_real_repo_serialization.py:1336-1457`）。
   - 通常 xdist は cache が存在するため fallback が発火しない。
   - resolver caller AST は `_resolve_now()` という `ast.Name` だけを探し、`_PRODUCTION_RESOLVE`、別名、`getattr` を検出しない（同 `:1733-1757`）。

   実 probe でも、別名束縛、`getattr`、module attribute 経由はいずれも `_receipt_call_owners()` の結果が空集合になった。must-fix 2 の具体経路は serial については殺したが、公開端全体としては閉じていない。

   成果物影響: xdist cache miss・破損時だけ live working tree を再走査でき、certified 材料の値と参照 snapshot が走行順に依存する一方、通常全走は緑を主張できる。

2. **[Major] prewarm 例外伝播テストは実例外型を使わず、must-fix 6 を無効化しても緑にできる**

   実装の resolver、cache、lock 障害は `ReceiptMemoError` へ翻訳される（`orchestrator/tests/real_repo_receipt_memo.py:51-82,228-274,289-337`）。しかし hook 検査が投げるのは素の `RuntimeError("prewarm-red")` である（`orchestrator/tests/test_real_repo_serialization.py:1592-1607`）。

   hook を次のように退行させても、この検査は緑のままである。

   - `ReceiptMemoError` だけ捕捉して握り潰す。
   - その他の `RuntimeError` は伝播させる。

   実際の全 prewarm 障害だけが消され、テスト用例外だけは伝播する経路である。例外 object の同一性も検査していない。

   成果物影響: resolver/store/lock の原診断が消え、後続 consumer の `cache-missing` に化けてレポートと台帳の障害分類が誤る。

3. **[Major] `-p no:xdist` 負例の fake config は「未宣言 option」を再現していない**

   `_ReceiptHookConfig.getoption()` は、default 引数を省略しても未登録 option に `None` を返す（`orchestrator/tests/test_real_repo_serialization.py:1506-1514`）。実 `pytest.Config.getoption("testrunuid")` は、xdist option が未宣言で default もなければ `ValueError` を投げる。

   したがって実装から `getoption("numprocesses", None)` または `getoption("testrunuid", None)` の default を外しても、`no_xdist` 検査（同 `:1706-1721`）は緑のまま、実 `-p no:xdist` だけが configure 時に落ちる。must-fix 7 の現実装は正しいが、その回帰ゲートは実効的でない。

   成果物影響: xdist を無効化した正当な実行が collection 前に停止し、certified 選択・レポート・台帳が生成されない。

4. **[Major] lazy-import 検査は通常の `import` 文しか見ず、動的 eager import を許す**

   `_module_scope_receipt_imports()` が検出するのは `ast.Import` と `ast.ImportFrom` だけである（`orchestrator/tests/test_real_repo_serialization.py:1760-1785`）。実 probe では module scope の `importlib.import_module("orchestrator.tests.real_repo_receipt_memo")` が空集合として通過した。

   fake hook 検査も conftest のロード後に `_receipt_memo_module` を patch するため、ロード時点の動的 eager import は観測できない（同 `:1524-1590`）。外部 cwd 契約は、動的 import を `ModuleNotFoundError` だけ捕捉すれば維持できる。

   現差分自体は正しい。fresh conftest import では canonical/top-level memo module とも `sys.modules` に入らず、canonical module を事前 import した場合も同じ object を返し、top-level alias は作らなかった。しかしその性質を退行から固定できていない。

   成果物影響: consumer なし焦点走にも重い memo import が戻り、wall 比率超過によって wave が land 不能になり、成果物の確定が遅延する。

5. **[Major] opt-out 2 関数だけの走行で「prewarm なし」を直接検査していない**

   現実装では opt-out 2 関数を consumer inventory から除外し、`memo_receipt=False` により production resolver を独立利用するため、静的な配線は正しい（`orchestrator/tests/test_s8b_oracle_driver.py:1969-1985,2510-2575`）。

   ただし inventory 検査は集合の比較だけで、opt-out 2 関数・3 node を `_receipt_memo_consumer_selected()` へ渡して lazy import/prewarm がゼロであることを検査しない。`_receipt_memo_consumer_selected()` に opt-out 名だけを追加する退行は、無関係 node を使う既存 lazy 負例（`test_real_repo_serialization.py:1580-1590`）にも inventory 比較にも検出されない。

   consumer と混走する場合は元から prewarm が一度走り、opt-out はその cache を使わず独立 resolver を呼ぶ。この相互作用自体は意図どおりである。穴は opt-out 単独選択時に限る。

   成果物影響: opt-out 単独走行が test fixture の stub 設置前に実 resolver を要求し、session error または不要な live scan によりレポートと台帳を失いうる。

6. **[Major] worker guard が二重化され、M9 の単一変異は mask される**

   worker 除外は hook 側（`orchestrator/tests/conftest.py:554-565`）と共通 helper 側（同 `:372-375`）の二箇所にある。どちらか一方だけを撤去しても、もう一方が worker prewarm を止めるため、fake hook と実 xdist 順序検査は緑のままである。

   現挙動は安全だが、段 4 の M9「workerinput guard を外すと worker 除外 meta-test が赤」は単一理由性を満たさない。両 guard の同時変異として再登録するか、能力境界を一箇所へ寄せない限り、SURVIVED/MISMATCH になる。

   また、worker trace、UID 上書き、identity split、公開 fail-open などの「合成負例」の多くは、SUT を変異せずローカル list/object/fake 関数を壊して assertion の向きだけを確認している（`test_real_repo_serialization.py:1612-1619,1696-1703,1723-1730,1814-1826`、`test_s8b_binding_driftguards.py:452-463`）。これらを mutation kill の証拠には数えられない。

   成果物影響: worker payer 防壁の検出力を実際以上に評価して land すると、将来の両層退行で xdist 全走が session error となり全成果物を失う。

7. **[Major] stale prune は lock file を残すだけで、別の生存 session の cache を保護しない**

   prune は current path 以外の古い `*.pickle` を、その cache に対応する lock の取得状態を調べず unlink する（`orchestrator/tests/real_repo_receipt_memo.py:171-187`）。検査は `.lock` ファイル自体が残ることしか確認しない（`test_real_repo_serialization.py:1478-1503`）。

   6 時間を超える session A の cache は、session B の prewarm から「別 current path」として削除できる。Linux では別ファイルである lock を保持していても pickle の unlink を防げない。A の遅い workerまたは再起動 workerは `cache-missing` になる。

   成果物影響: 長時間・並行 xdist session の一方が途中で fail-closed 停止し、その session のレポートと台帳が欠落する。

## must-fix 検証表

静的レビュー上の状態であり、pytest 実走結果ではない。

| # | 状態 | 根拠 |
|---|---|---|
| 1 | partial | 現実装は hook/helper の二重 guard で worker payer 0。ただし片側撤去が全検査で生存し、事前登録 M9 は単一変異で kill できない |
| 2 | partial | serial L1 の公開 `memo_resolver` 負例は有効。しかし xdist UID がある場合だけの公開 fail-open と `_PRODUCTION_RESOLVE`/別名/`getattr` 経路が生存する |
| 3 | closed | conftest と 2 consumer は canonical import。実 identity 比較と top-level alias 不在検査があり、現 module object は一致する |
| 4 | partial | 現実装の fresh/preloaded `sys.modules` 挙動は正しいが、動的 module-scope import を AST と fake hook が検出しない |
| 5 | closed | 任意 UID は SHA-256 名へ変換され、arbitrary UID の controller/worker round-tripと明示 UID 非上書きが検査される |
| 6 | partial | prewarm 呼出し位置は握り潰し外だが、負例の例外型が実際の `ReceiptMemoError` と異なり、型限定 catch が生存する |
| 7 | partial | 現コードは default 付き参照で正しいが、fake config が未宣言 option の `ValueError` を再現せず回帰が生存する |
| 8 | partial | `*.pickle` 限定と current path 除外は実装済み。だが「lock fileを削除しない」だけで、別 session の lock が保護する pickle を削除できる |

既存 assertion の差分は、追加が `assert` 77 個と `pytest.raises` 3 個、削除が `assert` 1 個だった。削除された一個は許可済み `test_receipt_memo_session_cache_round_trip_preserves_the_resolution` の「壊れた cache は `None`」を、構造化例外へ置換したものだけである。もう一つの許可済みテストは setup が prewarm 方式へ変わったが既存 assertion は不変だった。ほかに期待値の緩和・反転・skip・xfail・削除は見つからなかった。collection-only subprocess も、現差分では 2 consumer file の import/collection 中 resolver 0 回を直接検査している。

## 総括

**NO-GO。**

現実装の通常経路は概ね fail-closed だが、must-fix 2、6、7 は具体的な「退行しても全新設検査が緑」の経路を残す。must-fix 4 と opt-out 単独走行にも同種の検出穴があり、M9 は二重 guard に mask されて事前登録どおりの kill にならない。

pytest は実行していない。未コミット 5 file、+1219/-125 行を静的に監査し、read-only AST/import probeだけを行った。