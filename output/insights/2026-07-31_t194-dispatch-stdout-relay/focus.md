# [T-194] 段 6 焦点再レビュー (逐語) — fix 1 巡目後の独立検証

- 実行: claude / opus / 静的レビューのみ (pytest 未実走)
- 目的: fix 実装子の自己申告「F1〜F11 すべて closed」を独立検証し、`DW-O16` が要求する
  closed / partial / regressed 表を得る

## (1) 対応表

### F1〜F11 (親の fix 指示)

| ID | 判定 | 根拠 file:line | 備考 |
|---|---|---|---|
| F1 | **closed** | impl:641-642 (`except _SignalAbort: raise`) + impl:643-644 (`except Exception: continue`) / test:349-374 | **指示の字面どおりに実装していたら塞がらなかった**。`_SignalAbort ⊂ DispatchError ⊂ RuntimeError ⊂ Exception` (impl:100-107) なので `except Exception` へ「絞る」だけでは A-1 は残る。実装子は明示的な再送出枝を足しており、指示を正しく超過している。既存 signal 契約テスト (test:1034-1060) は qsub の `_capture` で中断するため record が両方 `None`、impl:1308 の中継は即 return で無影響 |
| F2 | **partial** | impl:627-640 / impl:542-560 / test:377-422 | 本線は実装・pin 済み。残穴あり → 新規回帰 R1 (must-fix)。告知 `_emit` (impl:631-635) が同じ broken pipe で失敗すると impl:638-639 が握り潰し、告知先 stream は devnull へ差し替えられない |
| F3 | **closed** | impl:536-539 / impl:611-614 / test:253-256 | 詐称不能性は完全。`str.splitlines(keepends=True)` は `\n \r \r\n \v \f \x1c-\x1e \x85    ` を分割するため、任意の consumer の改行集合の上位集合。よって中継本文の行は必ず prefix で始まる。test:256 の枠 end 出現数 1 の assert が単独 killer |
| F4 | **closed** | impl:601-610 / impl:615-618 / test:283-286, test:307-311 | 期待値は文字列厳密等値。nit: `relayed_size` は decode 済み text の byte 長、`source_size` はファイル byte 長なので `errors="replace"` 経由で数 byte ずれうる |
| F5 | **closed** | impl:34 / impl:581-585 / test:259-286 | 段 5 の「全量」テストは削除され 64 KiB 版に置換。裁定変更に由来する正当な更新 |
| F6 | **partial** | impl:1211-1213, impl:1249-1254, impl:1303-1308 | 3 経路とも原因行が中継より先。**しかし順序を pin するテストが 1 本もない**。infra テスト (test:451/463/475) は stdout の内容のみ、test:957-964 は stderr の内容のみ。中継を原因行の前へ戻す退行は無検出 |
| F7 | **closed** | test:913-923 (特に test:922) | impl:1254-1259 の削除を殺す |
| F8 | **closed** | test:942-964 | **kill を担うのは test:964 の `not in` 1 行だけ**。F6 が原因 print を中継の前へ動かしたため、test:959-962 は M8 下でも緑のまま。B-5 の assert 行粒度要求がここで load-bearing になった |
| F9 | **closed** | test:329-331 + test:276, test:303 | 定数と期待値が同時に動く経路を両側で塞いだ |
| F10 | **closed** | test:347, test:374 | |
| F11 | **closed** | test:451-460, 463-472, 475-485 (stdout のみ) / test:313-326 (stream 分離専用) | M4 は infra 3 テストを赤にしなくなり、単一理由性が回復 |

### A-1〜A-11 (レビュー A)

| ID | 判定 | 根拠 | 備考 |
|---|---|---|---|
| A-1 | closed | F1 と同じ | ただし A-1 注記の副作用は実際に生じる → R2 |
| A-2 | **partial** | F2 と同じ | R1 |
| A-3 | closed | F3 | |
| A-4 | closed | F4 | |
| A-5 | closed | 4 site すべてに killing test: impl:1213→test:460 / impl:1254→test:922 / impl:1262→test:249-256 ほか / impl:1308→test:472, 485 | |
| A-6 | 対象外 (親訂正) | s1-brief.md:56-60 / `tools/run_tests.py:903` を独立確認 (`sidecar=None`) | fix は run_tests.py を一切触っていない |
| A-6b | 対象外 (親訂正) | s1-brief.md:61-65 | 実装は訂正後の文言と一致 |
| A-7 | closed | F5 | |
| A-8 | **partial** | F6 | 実装済み・未 pin |
| A-9 | 対象外 (backlog) | impl:512-513 は未改変 | 意図せぬ改変なし |
| A-10 | 対象外 (backlog) | impl:1065, impl:1086 に中継なし | 両 site は収集開始前 (record は `None`)、HEAD と同数の `return INFRA_RC` 8 site を確認 |
| A-11 | **partial** | impl:643-644 | BrokenPipe 枝だけ告知。汎用 `except Exception` 枝は依然無音で、`begin` 枠だけ残り `end` 枠が出ない。test:334-347 は枠の対合を見ていない |

### B-1〜B-13 (レビュー B)

| ID | 判定 | 根拠 | 備考 |
|---|---|---|---|
| B-1 | closed | test:913-923 | |
| B-2 | closed | M6a/M6b に分割済み。両 site に別々の killing test | anchor 精度は要修正 |
| B-3 | closed | M7 は pin へ、M11 を追加 | 登録文言は依然不正確 |
| B-4 | closed | test:964 | |
| B-5 | 対象外 (nit) | assert 行粒度を採択済み | **F8/F10 の結果、必須度が上がった**。M1 下で test:347 が赤、M5 下で test:346 が赤 — 関数名粒度では両者が同一 node に潰れる |
| B-6 | 対象外 (nit) | test:463 / 475 とも impl:1308 のみ拘束 | 変化なし |
| B-7 | closed | F11 | |
| B-8 | closed | F9 | |
| B-9 | closed | F5 | |
| B-10 | closed | F3 | |
| B-11 | closed | test:347 | 残余: 汎用例外枝の無音 (= A-11 partial) |
| B-12 | 対象外 (backlog) | 全 fixture が 2 MiB 未満 | `omitted_bytes > 0` 経路と impl:603-606 の `max()` 枝はテスト到達不能のまま |
| B-13 | **解消 (副次)** | test:256 | T1 は枠 end 出現数の assert という固有 kill を獲得した。「kill を持たない」ラベルは撤回してよい |

## (2) 新規回帰の探索

### R1 (must-fix) 告知 stream 側の broken pipe が devnull 差し替えを受けず、exit 120 経路が残る

impl:627-640 — stdout が壊れた場合 `_redirect_broken_stream_to_devnull(sys.stdout)` は走るが、続く告知
`_emit` (impl:631-635) が**告知先でも** `BrokenPipeError` を起こすと impl:638-639 が握り潰し、告知先 fd は
差し替えられない。両 stream が同一 pipe の場合、`stdout record が空 or 中継成功 → stderr 中継で EPIPE →
告知を stdout へ → EPIPE → 握り潰し` の順で **fd 1 が未差し替えのまま `sys.stdout` のバッファに残留
byte が残る**。CPython の `flush_std_files()` は stdout の flush 失敗のみを exit status 120 に畳む。

**成果物影響**: 受入全走の process rc が child_rc から 120 に化け、`tools/run_tests.py:903` 経由で
`output/task-runs` の `exit_status` に偽の赤が記録される (F44 と同型の再発 — F2 が塞ごうとした当のもの)。

修正は 1 行: impl:638 の `except Exception:` を `except BrokenPipeError:` の先取りで分ける。

### R2 (nit / backlog) `_SignalAbort` 再送出の複合副作用 — receipt 二重化・中継二重化・「setup failure」誤ラベル

A-1 注記の経路は fix 後に実際に開通した。impl:1262 の中継が `_SignalAbort` を上げると:

1. impl:1269 の `except BaseException` が拾い `outcome` を `infra` へ書き換える
2. impl:1302 の `_persist_receipt` が O_EXCL で衝突し、fallback receipt を `kind: infra` で生成 —
   `receipt.json` の `kind: child` と矛盾する 2 通が残る
3. impl:1308 で**同じログを二度目に中継**する (最大 128 KiB の重複)
4. impl:1308 の中継中に来た場合は `dispatch()` の catch に落ちて setup receipt +
   `Pegasus dispatch setup failure:` を出す — F8 が防ごうとした「原因の型がすり替わる」状態に、
   signal 経由の裏口ができた

**受理集合は動かない**: fallback / setup receipt を読む consumer は repo 全体で自テストのみ (grep 実測)。
rc は child_rc → INFRA_RC へ動くが、これは既存 signal 契約と整合する挙動であり、親の erratum 2 が
明示的に選んだ帰結。よって nit / backlog と自己申告する。ただし**この複合経路を通すテストは 1 本もない**
ことは記録すべき。

### R3 (問題なし) 計算量・メモリ

`_utf8_tail` は末尾から高々 `limit+1` 回 (65537) の 1 文字 encode。2 MiB text でも O(limit)。
`_prefix_relay_lines` は 64 KiB 以下に対して O(n) の list + join。全改行の最悪ケースでも 196 KiB。

### R4 (問題なし) request ID の出所

`_parse_request_id` は qsub の stdout、`_discover_request_id` は `qstat -f` の出力。いずれも scheduler
出力であり、子 pytest の `.o`/`.e` とは別経路。加えて impl:578 が `re.fullmatch(r"\S+", ...)` で再検証する。
Python の `\s` は Unicode 準拠で制御文字も空白扱いなので、**改行系文字は ID に一切入らない** = 枠行を
詐称できない。汚染源になっていない。

### R5 (問題なし) 64 KiB 切り詰めと DW-M08 の「失敗 node 名」

pytest の short test summary と結果行は出力の**末尾**。計算ノードの子は `tools/run_tests.py` →
`subprocess.call(pytest)` で、その後に大量出力する処理はない。よって末尾 64 KiB は失敗 node 名を保持する。
留保: 失敗が数百件を超えて summary 自体が 64 KiB を超えた場合、切り落とされるのは先頭側の失敗 node。

### R6 (nit) pytest process 自身の fd / capsys への副作用

- 実 `dup2` はテスト内で走らない — test:409-411 が mock 済み
- capsys 下では `sys.stdout` は `CaptureIO` で `fileno()` が例外を上げるが impl:551 が飲む。かつ
  `CaptureIO` は `BrokenPipeError` を発生させないので impl:627 枝自体に到達しない。**capsys 汚染・
  他テストへの波及なし**
- nit: test:405-411 の mock は stdlib モジュール実体を process 全体で差し替えている。ブロックは短く
  単一スレッドなので実害は薄いが、ブロック内で finalizer 由来の `os.close` が 1 回でも走ると
  test:416 の呼び出し回数 assert が flaky になる

### R7 (問題なし) 既存 905 行の期待値書き換え監査

test 側の削除行は 3 本のみ (signature 2 と fixture 1)。いずれも**assert の追加のみ**で、緩和は 1 件もない。
F5 が書き換えを許した「全量」期待テストは段 5 で新設されたもので HEAD の 905 行に含まれない
(HEAD の test は 905 行、現在 1168 行を実測)。**テストを甘くして緑にした箇所は検出できなかった。**

### R8 / R9 (nit)

- impl:640 の `break` は、stdout だけが壊れて stderr が健全な宛先でも stderr 中継を捨てる。F2 の
  「以降の中継を打ち切り」の字面どおりなので指示準拠だが、コストとして記録する
- 枠は生 `request_id` を、`_progress` は `normalized_id` を使う。同一 job log 内で ID 表記が 2 種になる

## (3) 変異登録 12 件の再検証

| # | 適用位置 (fix 後) | 一意性 | killing test | kill/pin の妥当性 |
|---|---|---|---|---|
| M1 | impl:1262-1267 | ○ | test:249-256, 280-286, 304-311, 322-326, **347**, 442-448 | pin。**T5 も赤になる**点は matrix に反映が要る |
| M2 | impl:1266 → `True` | ○ | test:280-286 | pin |
| M3 | impl:581-585 の三項式 | ○ | test:304-311 | pin |
| M4 | impl:574 の行全体 | ○ (裸の `sys.stderr` は他所に多数) | test:323-326 | pin。F11 により単一理由性が成立 |
| M5 | impl:643-644 | **✗ 違反** | test:346, 442 | kill (rc 11/12 → 16) |
| M6a | impl:1213-1218 (字下げ 20) | 要注意 | test:460 | pin |
| M6b | impl:1308-1313 (字下げ 8) | 要注意 | test:472, 485 | pin |
| M7 | impl:1262-1267 を impl:1246 の前へ移動 | ○ | test:444 | pin (格下げ妥当) |
| M8 | impl:955-956 を impl:1148 の直前へ**移動** | 要注意 | **test:964 のみ** | kill (原因が setup failure へすり替わる) |
| M9 | impl:1254-1259 (字下げ 12) | 要注意 | test:922 | pin |
| M10 | impl:34 または impl:584 | ○ | test:283-286 (+ impl:34 なら test:331) | pin |
| M11 | M5 ∧ M7 | 上記に従う | test:442, 446 | kill |

### 是正が要る点 (must-fix、いずれも登録側)

1. **M5 の anchor `except Exception` は一意でない。** fix 後の中継領域だけで 4 か所 (impl:551, 559, 638,
   643)。`except Exception:` + `continue` の対 (impl:643-644) を anchor にしなければ、harness は
   `_redirect_broken_stream_to_devnull` 内の枝を潰して SURVIVED を記録する。
   **成果物影響**: 変異行列が M5 を偽 SURVIVED または誤 site の kill として台帳に載せ、fail-closed
   検出力の証明が空証明になる (`DW-M04` 違反)
2. **M6a / M6b / M9 の 3 呼び出しは字下げを除いて byte 一致。** 引数まで同一 (`successful=False,`) で、
   先行空白を含めない anchor は 3 か所にマッチする。anchor に字下げを含める旨を登録に明記すること
3. **M8 は「削除」ではなく「移動」。** 単純削除すると impl:1174 の読み出しで正常経路まで
   `UnboundLocalError` になり、B-4 が固定したかった経路とは別の (はるかに検出しやすい) 変異になる
4. **M11 の期待文言が不正確。** 「receipt が永続化されないまま rc が動く」は誤り — impl:1302 で
   receipt.json は書かれる。書かれる内容が `kind: child` から**偽の `kind: infra` へすり替わる**のが
   実害で、test:446 がそれを捕まえる。kill 判定自体は成立するので文言だけ訂正すればよい
5. **fix で新設された最重要 2 経路に変異が登録されていない。**
   - impl:641-642 (`except _SignalAbort: raise`) — 削除すると A-1 が完全再発。killing test は
     test:349-374 に実在。**M12 として登録すべき**
   - impl:627-640 (BrokenPipe 枝) — 削除すると F2 が丸ごと消える。killing test は test:377-422 に実在。
     **M13 として登録すべき**
   **成果物影響**: 変異行列が「中継の fail-closed 挙動を全経路検査した」と主張する一方、signal 伝播と
   broken-pipe 打ち切りという最も危険な 2 経路が未変異のまま台帳に載る
6. **B-5 (assert 行粒度) は nit ではなく前提条件に格上げすべき。** M1 と M5 はいずれも test:334-347 を
   赤にするが、赤になる行が test:346 (rc) と test:347 (到達性) で異なる。M8 に至っては test:964 の
   1 行だけが kill を担う

## まとめ

- **自己申告「F1〜F11 すべて closed」は 9/11 で正しい。** F2 と F6 は partial。実装 11 件のうち偽の緑は
  1 件もなく、テストを甘くした箇所も検出できなかった
- **must-fix はコード 1 件 (R1) と登録 5 件**
- **特筆すべき良い判断**: F1 の指示は字面どおりでは A-1 を塞げなかった (`_SignalAbort ⊂ Exception`)。
  実装子が `except _SignalAbort: raise` を足して超過対応しており、かつ test:349-374 で `_SignalAbort` と
  `SystemExit` の両方を pin している。harness が「F1 = `except Exception` があること」で検証すると
  壊れた実装を通してしまうので、検証条件は test:349-374 の存在にすること
- **F3 の詐称不能性は完全** — `splitlines` の分割集合が任意の consumer の上位集合であること、
  request ID が scheduler 由来かつ二重検証であることを追跡確認した。規律 6 の要求は満たされている
