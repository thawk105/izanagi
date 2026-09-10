判定は **NO-GO**。親の実走赤は実装会計ではなく E2E oracle の誤りですが、それ以外にも診断可読性、consumer 防護、例外境界、テスト検出力に未閉鎖があります。

## 1 — must-fix : 赤の `source_bytes` は実装が正しく、E2E oracle が xdist 復元後の `longreprtext` を誤モデル化している

(i) 主張

E2E は 96 件ではなく **24 件**です。算術は次のとおりです。

- payload: 16,384 bytes
- oracle: `"Failed: "` 8 bytes + payload = 16,392 bytes/件
- 実 report: worker banner 46 bytes + 改行 1 byte + payload = 16,431 bytes/件
- 差: `(46 + 1 - 8) × 24 = 39 × 24 = 936 bytes`
- oracle: `16,392 × 24 = 393,408`
- 実装: `16,431 × 24 = 394,344`

したがって `394344` が事実で、`393408` が誤りです。`936 / 96 = 9.75` なので「96件で936 bytes」という前提は算術的にも成立しません。

(ii) 一次資料

- case 数は `orchestrator/tests/test_pytest_failure_digest.py:419` の `case_count = 24`。
- oracle は同 `:481-486` で `"Failed: " + _e2e_message(case)` を source とする。
- 実装は `orchestrator/tests/conftest.py:424-426` で `report.longreprtext` そのものを UTF-8 会計する。
- pytest は `longreprtext` 生成時に `toterminal()` を呼ぶ: `_pytest/reports.py:103-115`。
- xdist controller は report に worker node を付ける: `xdist/dsession.py:326-329`。
- worker banner は `_pytest/reports.py:49-58,78-82`。
- `pytrace=False` は value style となり、`Failed: ` ではなく例外の文字列だけを出す: `_pytest/nodes.py:409-411`、`_pytest/_code/code.py:1111-1114`。
- 実走値は `t1.log:77-79`。banner の実在は `t1.log:14` および digest excerpt の `t1.log:88`。

(iii) 成果物への影響

裁定 (d) の「全 account 値を独立 oracle で厳密検算」が赤のままです。単に `source_bytes` を 394,344 に置換しても、各 report の `sha256` と `omitted_manifest_sha256` は worker id を含む実 source と一致せず、後続 assertion が赤になります。

(iv) 対処案

期待値を緩めず、各 case を処理した `gwN` をテスト側の独立 sidecar へ記録し、既知の worker banner、改行、16 KiB message から実 `longreprtext` を完全再構成してください。その source から byte 数・SHA-256・manifest を厳密計算します。

## 2 — must-fix : 段4 scope は大半が実装済みだが、E2E・実終了形・可読性・consumer 防護は partial である

(i) 主張

項目別対応は以下です。

| 段4確定項目 | 判定 | 根拠 |
|---|---|---|
| 編集面を2ファイルに限定 | closed | `git status` は `conftest.py` と新規 test file のみ |
| `report.failed` を独立 stash | closed | `conftest.py:332-340` |
| wrapper、post-yield `finally`、`return` なし | partial | 通常経路は正しいが、所見3の同時例外が未定義 |
| xdist worker 無出力 | closed | `conftest.py:610-611` |
| failure 0 で builder/writer 無呼出し | closed | `conftest.py:584-586,610` |
| 49,152 / 4,096 / 5,120 / 1,024 byte 予算 | closed | `conftest.py:294-299,534-558` |
| failure 後の lazy import | closed | `conftest.py:551-558,587-590`。ただし所見7あり |
| ASCII canonical rendererと二重会計 | closed | `conftest.py:343-376,506-527` |
| 人間へ診断本体を届ける | partial | 全改行を `\x0a` にし、4 KiB級の一行へ圧潰 |
| `> ` prefix と `FAILED ` 無害化 | closed（現形式） | `conftest.py:379-387`。将来の複数行には所見6 |
| xdist非依存安定順・manifest | closed | `conftest.py:398-423,467-491` |
| `__main__` harness | closed | `test_pytest_failure_digest.py:646-647` |
| (a) nodeid・tail | closed | `:210-227` |
| (b) 緑・skip・xfail・xpass・0 collected・worker | partial | synthetic reportだけ。0-collected subprocess は未実装 |
| (c) 飽和予算・厳密会計 | closed | `:318-342` |
| (d) 実 conftest E2E・厳密 oracle・cleanup | partial | oracle が実走赤。timeout branch も成功走行では未発火 |
| (e) relay limit の3/4束縛 | closed | `:514-519` |
| (f) fail-open・BaseException・inner exception | partial | 実 pytest rc と pluggy 経由を未検査。所見3 |
| (g) consumer 三形 | partial | 一行入力だけ。所見6 |
| (h) 実 relay 結合 | closed | `:602-643` |

(ii) 一次資料

裁定要件は `s4-adjudication.md:61-96`。実装箇所は上表のとおりです。圧潰された実出力は `t1.log:87-89` にあり、traceback、source、assertion がすべて一行の `\x0a` 列になっています。

(iii) 成果物への影響

nodeid と sentinel は機械的に到達しますが、改行・段落・traceback 構造を失った4 KiB一行は、人間が受入赤を原因帰属する用途には不十分です。裁定の「代表 failure の本体」と brief の「人間へ届く」は部分達成です。

(iv) 対処案

source newline を内容文字として生出力せず、論理行の区切りとして扱い、各物理行を必ず `> ` で frame してください。各行内部の非ASCII・C0・DEL・backslash escape、byte 会計、tail 選択は維持できます。

## 3 — must-fix : wrapper は通常時に inner 例外を伝播するが、post-yield の `BaseException` が同時発生すると元の inner 例外を置換する

(i) 主張

`finally` 内に `return` はなく、`except Exception` は `BaseException` を握りません。通常の inner hook 例外は確実に再送出されます。

ただし、inner 例外を `yield` へ throw した後、`finally` の `_emit_failure_digest()` が別の `BaseException` を投げると、Python の例外置換により元の inner 例外は失われます。現在の sentinel test は stash を空にしており、emitter を通らないため、この衝突を検査していません。

(ii) 一次資料

- wrapper: `orchestrator/tests/conftest.py:601-611`
- `Exception` のみを catch: 同 `:587-598`
- sentinel test は throw 前に stash を clear: `test_pytest_failure_digest.py:571-578`
- pluggy は inner の `BaseException` を保存し wrapper へ throw: `pluggy/_callers.py:126-139`
- wrapper 終了後に残った例外を再送出: 同 `:157-167`

(iii) 成果物への影響

pytest 本体または別 hook の本来の異常が、digest writer 中の KeyboardInterrupt/SystemExit等で置換され、exit reason と診断帰属が変わり得ます。

(iv) 対処案

非空 stash と emitter `BaseException` を組み合わせた pluggy 経由テストを追加し、例外優先順位を裁定してください。Python 3.10 では `BaseExceptionGroup` が使えないため、「inner 例外が既にある場合は digest を試みず元例外を維持」など明示的な規則が必要です。

## 4 — nit : module-level stash は逐次 session と xdist では安全だが、同一processの入れ子 session では外側 report を破壊する

(i) 主張

逐次 `pytest.main()` は configure/unconfigure の両方で clear されるため持越しません。xdist controller/worker も別processなので混線しません。

一方、外側 session に failure が蓄積した後、同じprocessで内側 `pytest.main()` を起動すると、内側 `pytest_configure` が同じ module global を clear します。内側終了時にも全体を clear するため、外側の既存 report が失われます。同時 session ではさらに競合します。

(ii) 一次資料

`_FAILURE_REPORTS` と clear は `conftest.py:322-329,606-607`。pytest は configure 時に hook を呼び、unconfigure を finally で呼ぶ: `_pytest/config/__init__.py:1202-1219`。

(iii) 成果物への影響

canonical acceptance 内で入れ子 `pytest.main()` が実際に呼ばれる経路は未確認です。したがって現時点では nit ですが、「pytest.main() の再入でも安全」という `conftest.py:324` の全称コメントは偽です。

(iv) 対処案

session/plugin instance 単位の collector に移し、controller とworkerごとに所有させてください。少なくともコメントを「逐次再入」に限定し、nested re-entry の回帰テストを追加します。

## 5 — must-fix : 緑時無出力の実装経路は正しいが、(b) テストは実 TestReport の終了形を固定していない

(i) 主張

実コード上の挙動は次のとおりです。

| 終了形 | `_FAILURE_REPORTS` |
|---|---|
| pass | 空 |
| skip | `outcome == skipped` のため空 |
| xfail | skipping plugin が `skipped` へ変えるため空 |
| non-strict xpass | `passed` へ変えるため空 |
| strict xpass | `failed` のため1件入る |
| 0 collected | reportなし、空。exit code 5でもdigestなし |
| 成功 `--collect-only` | failed collect reportなし、空 |
| collection error付き `--collect-only` | failed `CollectReport` が入る |
| `-x` | 停止原因となったfailed reportは既にlogreport済みなので入る |
| report前の `INTERNALERROR` | 空 |
| failure後の `INTERNALERROR` | 既存failure分だけ入る |

`report.failed` は表示カテゴリではなく、単純に `outcome == "failed"` です。

(ii) 一次資料

- `report.failed`: `_pytest/reports.py:147-160`
- xfail/xpass outcome変換: `_pytest/skipping.py:276-312`
- `-x` 停止時も unconfigure へ到達: `_pytest/main.py:315-372`
- 実装 guard: `conftest.py:332-340,584-586,610`
- 現テストは label だけ異なる `failed=False` の `SimpleNamespace`: `test_pytest_failure_digest.py:258-266`

(iii) 成果物への影響

例えば収集条件を `report.failed or hasattr(report, "wasxfail")` に壊すと、実 xfail と非strict xpassでdigestが出ますが、現在の9テストはすべて緑のままです。緑走行の1 byte不変条件をテストが保護していません。

(iv) 対処案

pass、skip、xfail、non-strict xpass、0 collected、`--collect-only` を小さい subprocess pytest で実行し、実 `TestReport` と最終 stdout の完全無出力を検査してください。

## 6 — must-fix : consumer 防護は現在の一行 renderer では成立するが、複数行化に対して非合成的である

(i) 主張

現出力は一物理行だけで、先頭の `> ` は `_strip_relay_prefix` に剥がされないため偽nodeを作りません。しかし将来 newline を復元し、最初の行だけに `> ` を付けると、二行目の `FAILED a.py::b` は `_failed_nodes` に抽出されます。

現在のテストは source が単一行の `FAILED ...` だけで、この破壊を検出しません。さらに M3 の `> `→`| ` は、同時に存在する `! FAILED` 無害化のためconsumer上は依然安全で、テストは literal `> ! FAILED` assertion によって赤くなるだけです。

(ii) 一次資料

- consumerはANSIと任意個の `|` だけを剥がす: `tools/mutation_harness.py:791-795`
- その後、物理行先頭の `FAILED ` をnodeとする: 同 `:816-831`
- rendererは全文に一度だけ `> ` を付ける: `conftest.py:379-387`
- consumer testのdecoyは一行: `test_pytest_failure_digest.py:586-599`

(iii) 成果物への影響

所見2の可読性修正や将来のrenderer変更により、mutation harnessが存在しない失敗nodeを生成し、mutationのkill判定を誤ります。裁定A7が防ごうとした直接の成果物汚染です。

(iv) 対処案

fixtureを `"header\nFAILED decoy.py::test_fake"` にし、raw／1段／2段relayすべてで偽nodeが出ないことを検査してください。renderer側は各物理行へ個別に `> ` を付与し、各行のprefix付与後にconsumer testを通します。

## 7 — must-fix : 広すぎる `except ImportError` は dispatch module 内部の破損まで無言で握り潰す

(i) 主張

`_load_failure_digest_budget()` の import 中に起きた任意の `ImportError` が無条件で無言returnされます。`tools` 自体がplain runnerから見えない場合だけでなく、`dispatch_compute.py` またはその依存先の壊れた import も区別されません。

検出経路はあります。新規 E2E はdigest marker不在で赤になり、予算束縛テスト `:514-519` とrelay結合テスト `:602-605` は直接importで赤になります。しかし実failure sessionのdigest機構自身は何も知らせません。

(ii) 一次資料

`conftest.py:551-558,587-590`。無言化を明示的に期待するテストは `test_pytest_failure_digest.py:534-539`。

(iii) 成果物への影響

診断中継が必要な壊れた全走で、診断機構まで無言で消えます。E2Eの赤は存在を検出しても、そのE2E failure自身の詳細がrelayから切れる可能性があり、自己診断になっていません。

(iv) 対処案

`ModuleNotFoundError` の `name` を検査し、plain runnerでの対象module不在だけを無言fail-openにしてください。module内部の別 `ImportError` はexit codeを変えず、既存の一行ERROR経路へ送ります。

## 8 — must-fix : M1〜M7の静的検算ではM3が意味的に弱く、M6は非一意、M7は現コードへ一行適用不能である

(i) 主張

read-only制約により実変異は走らせていません。コード到達上の判定は以下です。

| 変異 | 静的判定 |
|---|---|
| M1 | 赤。ただし (c) は固定 `DIGEST_BUDGET` を直接渡すため緑で、赤は主に (e)。段4の「(c),(e)」帰属は誤り |
| M2 | (a),(d) がtail sentinel消失で赤 |
| M3 | (g) は赤だが、consumer抽出ではなく `"\n> ! FAILED "` literal assertionで赤。実consumerは `! ` により依然安全 |
| M4 | (c) の厳密 account が赤 |
| M5 | controllerでdigest不在となり(d)赤、worker出力でも(b)赤 |
| M6 | `:591` または `:596` を変えれば(f)赤。ただし `:573` も `except Exception` であり、ここをOSErrorへ変えても現テストは緑。変異位置が非一意 |
| M7 | 現hookはconfig/statsを受け取らず、`stats["failed"]` への一行置換を構成できない。事前登録どおりの赤は未立証 |

また、次の破損は9テストすべてを通過します。

- `if report.failed or hasattr(report, "wasxfail"):` として実xfail/xpassを誤収集する。
- runtest failureのcategoryを常に `"failed"` とし、setup/teardown errorを誤会計する。
- sourceの論理改行を物理改行へ戻す一方、最初の行だけに `> ` を付ける。二行目decoyを既存consumer testは検査しない。

(ii) 一次資料

変異登録は `s4-adjudication.md:109-131`。対応テストは `test_pytest_failure_digest.py:210-342,491-599`。複数の例外catchは `conftest.py:571-598`。

(iii) 成果物への影響

段6の「所見ゼロは変異で裏取りする」条件を満たせません。特にM7は登録patch自体が現実装へ対応せず、M3はconsumer安全性ではなく表記literalを検査しています。

(iv) 対処案

M1の期待赤を(e)へ訂正し、M3を二行目decoyの抽出集合で判定し、M6の正確な行と例外経路を指定してください。M7は現実装に適用できる具体的patchへ再登録し、実TestReportのxfail/xpass/setup/teardown変異も追加します。

## 総括

must-fix は以下です。

- E2E oracleをxdist復元後の正確な `longreprtext` に直す。実装会計は変更しない。
- excerptを人間が読める行構造にし、全物理行へ `> ` を付ける。
- inner hook例外とdigest側`BaseException`の衝突時優先順位を決め、pluggy経由で固定する。
- 緑・skip・xfail・xpass・0 collected・collect-onlyを実pytest終了形で検査する。
- consumer testへ二行目`FAILED` decoyを追加する。
- `ImportError` fail-openを対象module不在に限定する。
- M1/M3/M6/M7の変異登録を現コードに一致させ、実際の検出理由を固定する。