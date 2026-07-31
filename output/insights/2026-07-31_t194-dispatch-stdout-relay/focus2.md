# [T-194] 段 6 焦点再レビュー 2 (逐語) — fix 2 巡目差分の独立検証

- 実行: claude / opus / 静的レビューのみ (pytest 未実走、AST 構文検査のみ = 両ファイル syntax ok)
- 2 巡目差分の同定: `git diff` は 1+2 巡目の合成なので、`focus.md` の 1 巡目行番号から差分を復元した。
  `_emit_relay_abort_notice` (impl:563-573) 挿入で `_relay_scheduler_logs` 本体が一律 +13 行ずれる事実と
  一致する。**2 巡目の実装差分は impl 側 2 件 (G1: impl:563-573 の新設と impl:643-647 の付け替え /
  G3: impl:651-657 の告知追加)、test 側 4 件 (新規 test:428-473, 476-506, 509-547 と assert 追記
  test:348-352, 588-590, 617-620, 1060-1062)** に限られる

## (1) G1 / G2 / G3 の判定

### G1 = closed (残余は診断面の pin 穴のみ)

- 実体: impl:563-573 `_emit_relay_abort_notice`、核は impl:568-569
  `except BrokenPipeError: _redirect_broken_stream_to_devnull(stream)`
- R1 の経路を逐語で追った: stdout record が None または中継成功 → index=1 (stderr) で EPIPE →
  impl:641 が stderr を devnull へ → impl:642 `notice_stream = streams[1 - index][2]` = `sys.stdout` →
  impl:643-647 → impl:567 `_emit` が再び EPIPE → **impl:568-569 が fd 1 を devnull へ差し替える** →
  impl:648 `break`。1 巡目はここで握り潰していた
- exit status 120 は塞がった。`BufferedWriter` は失敗した flush の未書き出し byte を保持するため、
  dup2 後の終了時 flush は devnull へ成功する。両 stream が同一 pipe でも、先に壊れた側と告知先の
  **両方**が差し替わるので残留 byte は残らない
- pin: test:428-473。test:462-473 が `os.open` / `os.dup2` / `os.close` の呼び出し**列**を厳密に固定して
  おり、片側だけの差し替えを殺す
- **残余 (nit / pin 穴)**: impl:642 の `1 - index` を `streams[1][2]` (常に stderr) へ変異させると
  全テストが緑のまま通る。既存 2 本の broken-pipe テストはどちらも index=0 で `break` するため index=1 の
  枝が未到達。R1 の鏡像ケース (stderr 先行破断 → 告知先 stdout) を通すテストが 1 本もない。
  exit-120 は再発しない (この変異でも壊れた側は差し替わる) ので **kill ではなく pin** → M16 提案

### G2 = closed

順序として pin されている。「両方出ること」だけの assert ではない — `str.index()` は非存在時に
`ValueError` を上げるので、存在検査と厳密順序検査を同時に満たす。

| infra 経路 | 原因行 (impl) | 中継 (impl) | 順序 pin (test) |
|---|---|---|---|
| A: compute-marker 欠落 / terminal handoff | 1225 | 1226-1231 | test:588-590 |
| B: receipt 永続化失敗 | 1262-1266 | 1267-1272 | test:1060-1062 |
| C: 外側 `except BaseException` | 1316-1320 | 1321-1326 | test:617-620 |

- 原因文字列の出所を裏取りした: `compute-marker-not-observed` を stderr へ出すのは impl:808-815
  `_print_terminal_handoff` **だけ**で、`_latch_submission_disabled` は何も印字しない。よって「中継を
  原因行の前へ移す」変異で index 大小が確実に反転する (先行する偽の一致が無い)
- accounting grace 経路 (test:593-602) には順序 assert が無いが、この経路は `DispatchError` 経由で
  site C に落ちるため test:617-620 で被覆済み。3 site すべて pin されている
- **コスト (backlog)**: **F11 が部分的に退行した**。順序 assert は `captured.err` を読むため、infra テストが
  再び stream 対応表に結合した。M4 は 1 巡目後は test:323 の 1 node だけを赤くしたが、現在は
  test:588 / 617 / 1060 でも `ValueError` を起こし 4 node を赤くする。ただし file 順で test:313 が先に
  来るため harness が記録する第一失敗 assert 行は test:323 のまま。なお原因行は stderr 専用なので
  stdout 側では順序を観測できず、**G2 と F11 の両立は構造的に不可能**である。受容すべき設計上の
  トレードオフとして台帳に記録し、`DW-M08` の diagnostic 記録に M4 の赤 4 node を併記すること

### G3 = closed (ただし副作用で M12 の kill 証明が消えた → N1)

- 枠の対合: impl:628-631 が `begin` を出した後に例外が来ると impl:651-657 が告知を同 stream へ出す。
  test:476-506 が emit 列を厳密固定
- 告知自体が例外を投げても rc 不変: impl:572-573 が `Exception` を握る。test:334-352 は `_emit` を
  全呼び出しで `RuntimeError` にする mock なので告知も失敗する経路を通り、test:346 で `rc == 11` を固定。
  test:348-352 が告知の到達性を固定 (恒真化防止)
- `_SignalAbort` / `SystemExit` の伝播: impl:649-650 (loop 内)、impl:570-571 (告知内) で再送出、
  `SystemExit` は `BaseException` なのでどちらにも捕まらない。test:354-378 と test:509-547 が両方を pin
- nit: impl:628 到達前 (`_utf8_tail` 等) で例外が出ると `begin` 無しの告知が出る。`end` 行ではないので
  枠の偽対合は起きず、診断上の雑音のみ
- nit: 告知文に元例外の型・文言が入らない。1 巡目は完全無音だったので単調改善と判定する

## (2) 1 巡目 closed 項目の非破壊確認 — すべて維持

`git diff -U0` の削除行は test 側で 3 行のみ (signature 2 と fixture 1)。**assert の削除・緩和は 1 件も無い。**

| ID | 現行根拠 | 状態 |
|---|---|---|
| F1 | impl:649-650 `except _SignalAbort: raise` が**残存** (加えて impl:549-550 / 557-558 / 新設 570-571) / test:354-378 | 維持 |
| F3 | impl:536-539 / test:253-256 | 維持 |
| F4 | impl:610-623 / test:283-286, 307-311 | 維持 |
| F5 | impl:34-35 / impl:594-598 / test:329-331 | 維持 |
| F7 | test:1048-1062 | 維持 + 順序 assert 追加 |
| F8 | test:1103 | 維持 |
| F9 | test:330-331 | 維持 |
| F10 | test:347 + 新設 test:348-352 | 強化 |
| F11 | — | **部分退行** (G2 との構造的トレードオフ、backlog) |

## (3) 新規回帰の探索

- **再帰・二重呼び出し・無限ループ: 無い。** `_emit_relay_abort_notice` が呼ぶのは `_emit` と
  `_redirect_broken_stream_to_devnull` のみで、どちらも中継関数へ戻らない。loop は 2 要素 tuple 上の
  `for` で `break` / `continue` のみ。`streams[1-index][2]` が自分自身になるのは
  `sys.stdout is sys.stderr` のときだけで、その場合でも dup2 の二重適用は冪等
- **テスト実行時に実 fd を差し替える経路: 生じていない。** 新設 test:428-473 は `DC.os.open` / `dup2` /
  `close` をすべて mock 済み。capsys 下では `sys.stdout` が `CaptureIO` なので `BrokenPipeError` を
  発生させず該当枝に到達しない。**pytest 自身の出力は壊れない**
- **N3 (nit)**: `mock.patch.object(DC.os, ...)` は stdlib `os` モジュール実体を process 全体で差し替える
  (1 巡目 R6 で既出)。2 巡目でこの型が 1 本 → 2 本になり、新設側は `call_args_list ==` の完全一致
  assert なので、ブロック内で他所の `os.close` が 1 回でも走ると flaky になる。露出が倍
- **N4 (nit)**: test:477 が `parent_stdout = object()` を `sys.stdout` に差し込む。`_emit` が mock されて
  いる前提に依存しており、ブロック内で警告等が stdout へ書かれると `AttributeError` になる
- **N5 (backlog、R2 の拡張)**: impl:651 の `except Exception:` ハンドラ内から `_emit_relay_abort_notice` が
  `_SignalAbort` / `SystemExit` を上げうるようになった。1 巡目の汎用枝は裸の `continue` で絶対に
  送出しなかった。よって「中継 I/O 失敗 (rc 中立) の直後にシグナルが来ると rc が child_rc → INFRA_RC に
  化ける」複合経路が新たに開いた。R2 と同型で既存 signal 契約とも整合するため本 wave では受容するが、
  **R2 の記述に「告知中のシグナル」も含める**必要がある

## (4) 変異登録 M1〜M13 の最終確認

| # | 適用位置 (現行 impl) | anchor の一意性 | killing test (第一失敗 assert 行) | 判定 |
|---|---|---|---|---|
| M1 | 1275-1280 を削除 | ○ | test:251 | pin ○ |
| M2 | 1279 → `successful=True,` | ○ | test:282 | pin ○ |
| M3 | 594-598 の三項式 | ○ | test:305 | pin ○ |
| M4 | 587 行全体 | ○ | test:323 (以後 588/617/1060 も赤) | pin ○ (単一理由性は退行) |
| M5 | **651-657 を削除** | **✗ erratum の anchor が失効** (N2a) | test:346 (rc 11→16) | kill ○ |
| M6a | 1226-1231 (字下げ 20) | 字下げ込みで ○ | test:587 | pin ○ |
| M6b | 1321-1326 (字下げ 8) | 字下げ込みで ○ | test:602 | pin ○ |
| M7 | 1275-1280 を 1259 の前へ移動 | ○ | test:570 | pin ○ |
| M8 | 968-969 を 1159 の直後へ移動 | ○ | test:1103 | kill ○ |
| M9 | 1267-1272 (字下げ 12) | 字下げ込みで ○ | test:1059 | pin ○ |
| M10 | 35 または 597 | ○ | test:283 / test:331 | pin ○ |
| M11 | M5 ∧ M7 | 上記に従う | test:346、receipt すり替えは test:572-574 | kill ○ |
| M12 | 649-650 (字下げ 8) | **✗ 字下げ必須が新発生** (N2b) | **無い — SURVIVED** | **kill ✗ (N1)** |
| M13 | 640-648 (字下げ 8) | **✗ 字下げ必須が新発生** (N2b) | test:421 | **kill ✗ → pin (N2c)** |

### must-fix

**N1. M12 (signal 再送出枝の削除) を殺すテストが 2 巡目で消滅した。**
1 巡目の汎用枝は `except Exception:` + `continue` だったので、再送出枝を削ると `_SignalAbort` が
握り潰され `pytest.raises` が落ちた。2 巡目では汎用枝が `_emit_relay_abort_notice` を呼び、その中の
impl:570-571 が `_SignalAbort` を再送出する。test:354-378 の mock は全呼び出しが同じ例外を上げるため、
M12 を入れても告知経路から `_SignalAbort` が伝播し緑のままになる。full-dispatch の signal 契約テスト
(test:1173-1199) は qsub の `_capture` で中断するため record が両方 `None` で即 `continue`、これも無影響。
**成果物影響**: 変異行列に M12 = SURVIVED が載り、「signal 伝播の fail-closed を pin 済み」という台帳
記載が空証明になる。実害側では、中継中の SIGTERM が握り潰されて dispatcher が `child_rc` を返す退行が
無検出になり、`tools/run_tests.py:903` 経由で `output/task-runs` の `exit_status` に中断走行が偽の緑 (0)
として記録されうる。
**修正 (テスト 1 本)**: mock を「最初の `_emit` だけが上げる」形にした派生テストを 1 本足す。M12 下では
告知が成功して `continue` し正常帰還するので `pytest.raises` が落ちる = kill 成立。

**N2a. M5 の anchor が失効した。** erratum は「`except Exception:` + `continue` の対」を anchor に
指定したが、2 巡目後は `except Exception:` に続くのが `_emit_relay_abort_notice(` で、`continue` は
離れた。`except Exception:` の直後が `continue` である site は**現在ゼロ**。
**修正**: anchor を **字下げ 8 の `except Exception:` (impl:651)** とする (4 空白は 551 / 572、
12 空白は 559、8 空白は 651 のみで一意)。変異は handler 全体の削除。

**N2b. M12 / M13 の anchor に字下げ指定が必須になった。**
`except _SignalAbort:` は 1 巡目 3 site (549 / 557 / 649) が 2 巡目で 570 が増え、**549 と 570 は字下げ 4 で
byte 一致**する。M12 は字下げ 8 を明記すれば一意。`except BrokenPipeError:` は 1 巡目 627 のみが
2 巡目で 568 (字下げ 4) が増えた。M13 は字下げ 8 を明記すること。

**N2c. M13 は kill ではなく pin である。** impl:640-648 を削除しても
`BrokenPipeError ⊂ OSError ⊂ Exception` なので汎用枝が拾い、告知先が同じ壊れた stream になり
impl:568-569 がそれを devnull へ差し替える。**exit-120 の穴は再発しない**。失われるのは `break` と
健全な側への告知だけで、rc も受理集合も動かない。killing test は test:421 で成立するので SURVIVED には
ならない。
**成果物影響**: 台帳が「exit-120 の fail-closed を殺す変異を保持している」と主張する一方、実際にその穴を
再現する変異は未登録のまま (→ M14)。

### 追加登録の提案

| # | 変異 | site / anchor | 種別 | killing test |
|---|---|---|---|---|
| M14 | 告知先 broken pipe の devnull 差し替えを撤廃 | impl:569 (字下げ 8、双子は impl:641) → `pass` | **kill** | test:462-465 |
| M15 | 汎用例外枝の切断告知を撤廃 | impl:652-656 を削除し `continue` だけ残す。anchor は impl:654 まで含める (字下げ 12 の `_emit_relay_abort_notice(` は 643 / 652 の 2 site で 2 行目まで byte 一致) | pin | test:348 |
| M16 | 告知先 stream の選択を固定化 | impl:642 → `streams[1][2]` | pin | **現状 killer 無し** (要テスト 1 本) |
| M17a/b/c | 中継を原因行の**前**へ移す (G2 の実体) | a: 1226-1231 を 1225 の前 / b: 1267-1272 を 1262 の前 / c: 1321-1326 を 1316 の前 | pin | a: test:588 / b: test:1060 / c: test:617 |

M14 は R1 をそのまま再開通させる (rc が child_rc → **120** に化け、`output/task-runs` の `exit_status` に
偽の赤が入る)。M17 は現行登録が M6a/M6b/M9 の**削除**しか持たず順序性そのものを撃つ変異が無いため、
G2 の証明に必須。

### 集計の更新提案

- **kill**: M5 / M8 / M11 / M14 の 4 件 (+ N1 のテストを足せば M12 が 5 件目)
- **pin**: M1 / M2 / M3 / M4 / M6a / M6b / M7 / M9 / M10 / M13 (格下げ) / M15 / M16 / M17a-c = 15 件
- harness は第一失敗を **assert 行**粒度で記録すること (erratum 6) が引き続き前提。M4 が 4 node を、
  M5 が 3 node を赤くする件は `DW-M08` の diagnostic 欄に併記が要る

## まとめ

- **自己申告「G1 / G2 / G3 すべて closed」は 3/3 で正しい。** 3 件とも実装は真に穴を塞いでおり、
  順序 pin は恒真化していない。テストを甘くした箇所・削除された assert は 1 件も検出できなかった
- **must-fix は 4 件、いずれもコードではなく検証側**: (N1) M12 の killer 消滅、(N2a) M5 anchor の失効、
  (N2b) M12 / M13 の字下げ指定漏れ、(N2c) M13 の kill → pin 格下げと M14 の新規登録
- **コード側の must-fix はゼロ。** 1 巡目の R1 (exit 120) は完全に閉じた
- 特筆: 2 巡目の G3 は正しい修正だが、**同じ修正が M12 の kill 証明を静かに無効化した**という
  「fix が変異検出力を食う」型の副作用を生んでいる。fix 後に変異登録を再検証する `DW-M07` の必要性が
  ここで実証された
- backlog 追加: F11 の部分退行 (G2 との構造的トレードオフ)、R2 の適用範囲拡大 (告知中のシグナル)、
  `os` モジュール process 全体 mock の露出倍増 (R6 の拡張)
