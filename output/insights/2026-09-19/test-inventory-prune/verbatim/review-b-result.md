## 所見

以下、`R` は `output/insights/2026-09-19/test-inventory-prune/`。静的レビューのみ実施した。

1. **real / must-fix — (D) の確定件数に、純粋な pin でない検査が混入。**
   **位置:** `R/README.md:12`、`:97`、`:105`。
   **根拠:** 「純粋な pin は16関数」とする一方、確認済み一覧には実挙動との混在を含む。特に `orchestrator/tests/test_plot_b10_static_tail_formal.py:414` は、成果物の存在、production の `validate_repo_closure`、caption の整合を検査し、固定 literal への exact pin ではない。一次資料 `R/verbatim/plan-result.md:340` も「literal hash 固定だけではない」と明記する。放置すると、裁定用レポートの確定件数・分類対象が誤る。
   **推奨処置:** 「純粋な pin」「pin と実挙動の混在」「Dでない」を関数単位で整理し、確定件数を更新する。テストは保持する。

2. **real / should — pin 先の一部が説明名に留まる。**
   **位置:** `R/README.md:89`、`:91`、`:94`、`:95`、`:104`。
   **根拠:** 「relay limit 定数」「publication family root・ledger kind・schema」等は意味の説明であり、正確な定数名ではない。実際には `orchestrator/tests/test_pegasus_dispatch_compute.py:663` の `DEFAULT_SUCCESS_RELAY_LIMIT_BYTES` 等まで特定できる。
   **推奨処置:** 既存表に正確な定数名・資料 path を記す。hash 群はその定義箇所への参照でよく、新しい台帳は不要。

3. **real / should — scanner の確認範囲から suite 全体へ結論を広げている。**
   **位置:** `R/README.md:14`。
   **根拠:** 「この test suite には……機械的に落とせる重みはほとんど無い」は、候補の意味確認を超える。`:126`〜`:132` に取りこぼしが明記され、実際に相談Bで追加5件が見つかっている。
   **推奨処置:** 「今回抽出・意味確認した候補から確定した削除は6 node」に限定する。wall 短縮・検出力の一般保存については、`:24`、`:78`、`:145` で適切に否定されている。

4. **real / should — DW-G05 の裁定済み文言が成果物本文に反映されていない。**
   **位置:** `R/verbatim/brief.md:16`、`R/verbatim/adjudication.md:21`、`R/README.md:10`。
   **根拠:** 裁定 #13 の新文言は裁定逐語にあるが、README に成果物影響の1行がなく、brief 逐語は旧表現のまま。
   **推奨処置:** 逐語は保存し、README に #13 の「重複6 node の台帳換算 worker 秒」「earliest-eligible 選択違反 / value-literal 帰属」を含む1行を追記する。

5. **refuted / should — 追加5件の削除漏れ・既存候補の不当な保持。**
   **位置:** `orchestrator/tests/test_p3_s4_loop.py:3238`、`:3258`、`R/README.md:46`、`:57`、`:58`。
   **根拠:** 指定関数1件と4 row・対応idはすべて削除済み。残存側の同値入力と包含する assertion は同ファイル `:1908`、`:3244` にある。B1保持理由も `R/verbatim/plan-result.md:28`〜`:34` と一致し、候補の位置は inventory と判定表から追跡できる。
   **推奨処置:** 削除集合を維持する。追加削除は不要。

6. **refuted / should — 要求外の機構追加・scanner 限界の隠蔽。**
   **位置:** `R/README.md:124`、`:139`、`author-final.patch:1`。
   **根拠:** 基底との差分は指定テスト2ファイルの削除だけ。scanner は逐語資料として保存され、実行機構や新gateは追加されていない。通常関数とparametrizeの包含、別decorator間の実効入力、合成fixture抑制、`production_targets` 未解決はすべて明記されている。
   **推奨処置:** 現状維持。

7. **refuted / should — 数値の母数混同・worker時間を実測改善として表示。**
   **位置:** `R/README.md:20`、`:30`、`:35`、`:119`。
   **根拠:** 391／363／333／30の対象範囲、collection 25,381、台帳24,379、対象分15,587.593秒を区別している。台帳を直接再集計し、総和17,958.848秒、削除6 nodeの33.005秒、差引17,925.843秒を確認した。worker時間は台帳換算と明記されている。
   **推奨処置:** 現状維持。削除後collection数25,375が差引計算なら、その旨を添えると時点がさらに明確になる。

## GO/NO-GO

**NO-GO — 削除差分は妥当だが、(D) 裁定パッケージの確定分類・件数を修正してから成果物を確定する。**

## 総括

追加5件を含む6 nodeの削除に、削除不足・要求外の実装は確認しなかった。必要なのは報告の局所修正であり、追加scanner・gate・テスト削除は不要。pytest・変異は再実行しておらず、実行結果は提示資料との照合に限る。