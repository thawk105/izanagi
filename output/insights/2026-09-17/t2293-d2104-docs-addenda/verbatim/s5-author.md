## 総括

- 指定の2ファイルのみ編集。両 literal は正本と完全一致する **995 bytes**。
- M2: `F不在は登録せず裁定送り、` → `真に決定的な不安定testはその1件のpin更新を個別に諮り、`
- M11: `停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。` → `停止条件外は治すか上記の制限内で投げ直しwaveを止めない。`
- `check_docs.py`: **rc=1、想定の1件のみ**。
- 自走 harness: **rc=1、開始前に拒否**。passed/failed 集計なし。
- 実装済み・テスト未実走。補助のメモリ内変異検査は成功。

## 変更点

- `tools/check_docs.py:605`: `DEV_WAVE_DW_O18_SECTION_LITERAL` を正本の bytes へ更新。
- `orchestrator/tests/test_check_docs.py:166`: 合成 fixture を同じ bytes へ更新。
- 同ファイル `:9484`: byte 数 assert を997から995へ更新。
- 同ファイル `:9582` / `:9639`: M2 / M11 の needle を指定どおり更新。期待 finding・rc・case 集合は変更なし。

## 検査結果

`python3 tools/check_docs.py` は rc=1。出力全文：

```text
check_docs: 1 件の違反
  - docs/dev-wave/operations.md: 可視 H2 節 'DW-O18 — テスト cwd と非帰属赤の着地' の節全体が exact 契約と不一致 — sections=1
```

`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_check_docs.py` は rc=1。`GrowthTestHoldBypassRefused` が `test_check_docs.py::*` を実行開始前に拒否しました。`N passed, M failed` 行・個別 failed nodeid はありません。

代替の test module import も同じ理由で拒否され、指定の3呼出しは未実走です。

補助検査として `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools:. python3 -` から既存 `_check_exact_visible_h2_section` を直接実行しました。正本入力は finding 0件、M2削除・M11削除はそれぞれ想定 finding 1件。変異はメモリ内だけで行い、source literal の不変を確認しました。これは既存 test nodeid の成功を意味しません。

正本の `len(read_bytes())` と、ASTから取得した両定数の `len(value.encode("utf-8"))` はすべて995。bytes の等値も確認済みです。M1・M2・M3・M4・M7・M10・M11・M12 の needle は新文言内に各1回でした。

`git diff --check` は rc=0。差分は指定2ファイルのみです。

## 波及

- `DEV_WAVE_EXACT_VISIBLE_SECTIONS`（checker `:651`）経由で、exact節検査（`:6156`）の期待本文が変わります。
- `_build_min_repo` の描画経路（test `:1040`）から、共有の合成 operations 本文へ反映されます。
- `test_normative_exact_section_contract_is_handwritten_and_complete`、DW-O18／DW-O26 の合成正例、非帰属赤の変異検査が影響範囲です。
- `tools`・`orchestrator` 内の検索では、変更定数の直接参照はこの2ファイル内でした。

## 未了・懸念

既存 hold により harness と指定テストは未実走です。親環境での実走・全走が必要です。docs は変更せず、親による改訂適用待ちです。commit および禁止された git 操作は実行していません。