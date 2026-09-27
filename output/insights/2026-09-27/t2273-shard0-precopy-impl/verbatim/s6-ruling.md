# 段 6 裁定 — [T-2273] 候補 (a) の実装 (2026-09-27)

入力: codex/s6-review-a-out.md (レンズ A、修正後 GO)、codex/s6-review-b-out.md (レンズ B = 過剰・削除、修正後 GO)。
統合 snapshot = s5-author-l.patch (wave 木 commit `677ea17b6`)。焦点走 focus-1 (tip `677ea17b6`、test_s8b_oracle_driver / test_real_repo_serialization / test_acceptance_schedule_order): 353 passed / 7 skipped / 失敗 0、Elapse 295 秒 (request 31264.nqsv)。skip の内訳は `-rs` 無しで未確認 → 次の焦点走で確認。全史 provenance: 12,970 件、新規違反なし。

## 所見の裁定

| 所見 | 裁定 | 扱い |
|---|---|---|
| B1 T1 が同じ node で hook を 2 回呼び、2 node 分の 1 回性を検証しない | real, must-fix | fix L: 同じ config・同じ testrunuid の別 `SimpleNamespace` 2 個で hook を呼ぶ |
| A1 `rmtree` 失敗が保存済みの生成エラーを覆う | real, should (成果物影響: 失敗時の赤の理由の表示だけ) | fix L: join・削除・生成エラーを個別に扱い、生成エラーを優先して伝播 (削除失敗は生成エラーが無いときだけ伝播)。数行に限る |
| A2 T1 が file mode を比較しない | real, should | fix L: signature に `stat.S_IMODE(st_mode)` を加える |
| A3 T1 は pytest が収集した module と別物になりうる | real (射程の限定) | 実装は変えない。本番 controller での import 成功と ROOT 一致は受入の実走 (写しが失敗すれば builder が赤) で確かめ、insight に T1 の射程を書く |
| A4 B の事前 collection file が無いと各走自身を基準にする | real, should | fix P: 系列投入前に `login-collection-A.log`・`login-collection-B.log`・`expected-added-nodes.json` を必須とし、B only − A only がその集合ちょうどであることを preflight で検査 |
| B「削れるもの」 | 削除候補なし (ROOT 一致検査は v2 明記、他は非同期経路に必要) | 変更なし |

## 変異 erratum (DW-M01、fix 前に登録)

- **E1 (M4 再照準):** 1 回性 guard (`if getattr(config, _T080_VISIBLE_OUTPUT_JOB_ATTR, None) is not None:\n        return`) の削除と `directory.mkdir(exist_ok=False)` → `exist_ok=True` の 2 置換を 1 変異とする。理由: 単独の guard 削除は 2 回目の mkdir 衝突 (FileExistsError) で落ち、spy 2 回の理由に届かない (実装子とレンズ A が独立に指摘)。期待 kill = T1 (実関数 spy の呼出し 2 回)。
- **E2 (M6 の形):** 「helper の初回呼出しで遅延起動」は helper に node が無く 1 置換で書けないため、「`pytest_configure_node` から `_start_t080_visible_output_snapshot(node)` の呼出しを外す」に替える (hook で起動しないという同じ欠陥)。期待 kill = T1 (a) (helper 前に `result.json` が現れない)。
- 他 (P0・M1・M2・M3・M5・M7) は登録どおり。置換文字列はレンズ A の再照準表を基に fix 後の実装で一意性を確かめて確定する。

## fix の分割

- fix L (author-t2273pi-impl の木で branch `fix-t2273pi-impl-1`): B1・A1・A2。所有 = `orchestrator/tests/conftest.py`、`orchestrator/tests/test_s8b_oracle_driver.py`。既存テストの期待値を変更しない。
- fix P (author-t2273pi-probe の木で branch `fix-t2273pi-probe-1`): A4。所有 = `probe-t2273pi/` だけ。
- 所有は素集合。

## 追補 (fix 後、追記直後の date 実測 16:15:35 JST)

- fix L = commit `6041d2f28`、fix P = probe/ (旧版 probe-v1/)。焦点走 focus-2 (tip `6041d2f28`、`-rfs`): 353 passed / 7 skipped / 失敗 0、Elapse 398 秒。skip 7 件は既存の成長 hold 6 件と toolchain 前提 1 件で、T1・T2 は skip されていない。
- 焦点再レビュー (codex/s6-focus-1-out.md、条件付き NO-GO): A1・A2・A4・B1 closed、A3 partial (受入の実走で確認する裁定は妥当、未完)。新所見 F1 (M4 が spy 以外で先に落ちうる)・F2 (M6 が 10 秒待機後に読取り例外で落ちる)。
- 変異 probe (dispatch、clone main = `6041d2f28`): P0 SURVIVED、M1〜M7 は登録どおりの node だけで落ちた (観測 node = 登録 node、完全一致)。最初の失敗行: M2 signature (bytes)、M3 signature (mtime)、M4 `result.json` の ok が False (2 本目の thread が同じ dir へ実関数で二重に複製して失敗)、M5 実関数 0 回、M6 `result.json` の FileNotFoundError (10 秒待機後)、M7 終了後の dir 残存、M1 helper 0 回 ≠ builder 1 回。
- **F1・F2 の裁定: real (落ちる assert の記述として) / must-fix としては refuted。** 各変異は 1 か所の変更で、同じ入力を拒否する別の層は無く、落ちた理由は変異が作った欠陥 (worker ごとの生成、hook で起動しない) そのもので診断文字列だけの赤ではない (DW-M03)。test の追加 assert は検査力を変えない nit として入れない。DW-O16 に従い親が変異の実測で閉じる。
- **erratum E3:** M4 (E1 の 2 置換) の kill は T1 の `result.json` ok 検査で起きる (登録の「spy 2 回」より前)。**erratum E4:** M6 (E2) の kill は T1 の `result.json` 読取り (FileNotFoundError) で起きる。期待 node は不変。
