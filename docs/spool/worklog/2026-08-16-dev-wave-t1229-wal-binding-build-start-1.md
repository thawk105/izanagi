---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1229-wal-binding-build-start
seq: 1
title: build_start を欠く WAL の中断理由を構造化して上へ返す — 真因が KeyError に化ける経路を塞いだ (コード + テスト、branch worktree-dev-wave-t1229-wal-binding-build-start、変異 6/6 KILLED、焦点走 109 passed)
---

## 本文

**閉じたものを先に書く。** 本 wave が閉じるのは `_wal_binding_commitment` が
`build_start` 不在で素の `KeyError` になる 1 点だけである。`build_start` を書かずに
abort する経路そのもの (`loop.py` の例外隔離) は**直していない**。
[T-1174] の numactl 矛盾も直していない — 本 wave が変えたのは、それが起きたときに
真因が読めるようになる点だけである。

- **親の実測が前提を裏付けた。** worktree 上で
  abort レコードだけを持つ records を `_wal_binding_commitment` へ渡すと
  `KeyError('build_start')` になり、
  abort の理由が 1 文字も出ないことを再現した。**build_start が欠ける経路は 1 本に特定できた** —
  `orchestrator/campaign/loop.py` の `except Exception` は `STAGE_ABORT` だけを書き
  `build_start` を書かない。`pipeline.py` の `_prebuild_abort` と通常経路は
  必ず `build_start` を emit するので、不在はこの経路に限られる。
  leg A の連鎖 (numactl 必須 `ValueError` → `eval-exception` abort → `KeyError`) は
  これで全部つながった。
- **成果物影響を具体的な field まで辿った。** supervisor の汎用 catch は
  例外の型名と文字列をそのまま journal の `supervisor-error` 事象と `cell["error"]` へ焼く。
  直す前にそこへ入っていた値は `type="KeyError"` / `message="'build_start'"` であり、
  真因は report にも journal にも残っていなかった。
- **段の実行形は軽量版とした** (段 2 plan / 段 3 consult を省略)。受理集合を縮小も拡大もせず、
  成功経路の戻り値は従来と同一で、変わるのは既に例外で落ちている経路の落ち方だけだからである。
  ただし段 6 の敵対レビューは 2 本とも実施した — 実害がありうる唯一の形が
  「fail-open を作ってしまう実装」だからである。
- **敵対レビュー 6 所見のうち 3 件を real、3 件を refuted と裁定した。**
  real はいずれも**テストの検出力**の欠陥で、実装本体の誤りではなかった。
  (i) 空 records への fail-open 変異が新テストを 1 本もすり抜ける、
  (ii) 正常経路の monkeypatch が variant 引数を捨てるため「WAL から別 attempt を読む」変異を
  検出できない、(iii) 正常経路 fixture が過剰決定で、fail-open 変異の赤が
  専用例外の不在ではなく属性欠落に帰属してしまう。fix 子が 3 件とも closed にした。
- **棄却した所見 3 件と、その根拠。**
  (a)「abort の reason/error が report へ無制限に漏れる」→ 同じ値は既に WAL の
  abort payload に記録済みで新しい信頼境界の越境ではなく、transport 由来の秘密は
  既存の redaction が伏字にする。理由を隠すことこそ本 wave が直している欠陥なので nit へ降格した。
  (b)「redaction のせいで真の理由が report へ届かない」→ **refuted**。親が実コードで確認し、
  伏字対象は transport endpoint 値と PBS ジョブ ID だけで、対象の abort reason は素通りする。
  もう 1 本のレンズも独立に同じ結論を出した。同じレビューが (a) と (b) を同時に主張しており、
  両立しない。
  (c)「commitment key 欠損の分岐は実経路で発火しない」→ **real だが欠陥ではない**。
  `wal.records_by_stage` は `validate_trigger_bindings` を先に走らせるため、
  commitment key を欠く `build_start` は `AttemptTopologyError` で先に落ちる。
  分岐とテストは helper の局所契約の防壁として残し、テストにその旨のコメントを入れた。
  **実経路で発火すると読める記述はしていない。**
- **変異は 6 件登録し 6/6 KILLED** (SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、baseline PASSED、
  `repo_head=5052e579`)。期待 node は初回で完全一致し、probe / erratum は要らなかった。
  **うち真の kill は 3 件だけである** — fail-closed を fail-open へ倒す変異 (不在時に
  ダミー 64 hex を返す / 正常経路と duplicate 経路をそれぞれ未検証 commitment へ差し替える)。
  残る 3 件 (例外文字列から abort 情報を落とす / 直接 indexing へ戻す / 内側 key の分岐を消す) は
  受理集合を変えないため、`DW-M08` に従い**診断シグナルの感度 pin として別枠に数える**。
  6 件を一括で「受理集合を守った KILLED」と読める書き方はしない。
- **過剰拒否の正例変異は登録していない。** 本 wave は受理集合を縮小しないため
  `DW-M01` の正例登録要件が非該当であり、過剰拒否の証拠は焦点走 109 passed と受入全走に置いた。
- **`docs/failures.md` への新規エントリは見送った。** 「真因が汎用例外に化けて隠れる」型に
  当てはまる型タグが既存の語彙に無く、新語の追加は docs 予算方針に反するため。
  同型の族記録は [T-1175] のエントリが持っている。
- **login node の bounded local が構造的に使えなかった。** `tools/run_tests.py` を素で
  2 回投入していずれも rc=16 (`bounded scope の memory.max / memory.oom.group を
  走行中に attest できない`)。これはテスト結果ではなく実行基盤の失敗なので、
  焦点走・変異走ともに `--force-dispatch` で計算ノードへ回した。
- **Codex 工数** (receipt.json、全件 accepted / attempt 1)。

| 段 | model / effort | wall (s) | model calls |
|---|---|---|---|
| 5 実装 | gpt-5.6-sol / high | 449.3 | 37 |
| 6 レビュー A | gpt-5.6-sol / high | 441.2 | 29 |
| 6 レビュー B | gpt-5.6-sol / high | 401.8 | 32 |
| 6 fix | gpt-5.6-sol / high | 275.2 | 21 |

## 次の一手差分

### 完了

- [T-1229] `_wal_binding_commitment` の `build_start` 不在を専用の構造化例外へ変え、
  variant・実在 stage 集合・abort の reason / error / build_attempt_id を
  文字列と属性の双方に載せて上へ返すようにした。呼び出し 2 箇所から variant を渡す。
  fail-open は作らず、下流の 64 hex 要求も成功経路の戻り値も変えていない。
  remaining: none
  base: bbdb89e83b16a057f218643226eebaa4a1356e906a7255cefe6ef76b4127e128

### 新規

- {{T:wal-abort-without-build-start}} **P3・新規**: `loop.py` の例外隔離経路が
  `STAGE_ABORT` だけを書き `build_start` を書かないこと自体の是非。本 wave は
  読み手側の診断可能性だけを直し、書き手側は触っていない。`build_start` を捏造すると
  replay / admission の topology を壊すため、書くとすれば別 stage か tombstone の設計が要る。
- {{T:supervisor-error-structured-fields}} **P3・新規**: supervisor は例外の
  `type` と文字列だけを journal / report へ焼くため、本 wave が例外へ載せた
  構造化属性 (abort reason、実在 stage) は機械 consumer から prose 解析でしか読めない。
  journal event schema へ独立 field を足すかの裁定が要る (受理集合の変更を伴う)。
