静的レビューの結論は **NO-GO** です。指定資料・実装差分・束を読みました。焦点走の **2,732 passed / 14 skipped** は確認しましたが、以下の承認範囲・親手順・過剰検査の問題は残ります。追加実走・ファイル変更はしていません。

以下、`E/` は `output/insights/2026-09-22/t2797-effect-bundle/` を指します。

1. **must-fix — model の一致判定に、記録だけのはずの client version 検査が混入している。**

   **根拠:** `tools/b5_llm_round.py:444`、同 `:481`、`E/bundle/b5-llm-parent-template.md:29`、段4裁定 D-4。

   `version` が非空文字列でなければ `reasons` に追加され、`matches_expected = not reasons` によって系列停止へ接続される。例えば全 assistant の model が予定 ID と一致し、role も正しくても、user 行の `version: null` だけで停止する。一方、version field 自体が無ければ停止しない。これは exact model の確認に必要な最小条件ではなく、D-4 の「client の版は記録するだけ」とも一致しない。

   **最小修正:** version の形式異常は記録に残し、model 一致の停止条件から外す。model の欠落・不一致と、対象 role の同定に必要な確認は残す。

   **成果物への影響:** 放置すると、予定モデルで生成した系列まで client 記録形式を理由に score 欠測となり、比較が判定不能へ変わる。

2. **must-fix — 最終 critic の不一致について、束が成立しない停止結果を約束している。**

   **根拠:** `E/bundle/b5-llm-parent-template.md:35`、同 `:37`、`E/bundle/b5-effective-bundle.draft.json:134`、`E/README.md:81`、`orchestrator/campaign/b5_generator_contrast.py:808`、同 `:817`。

   B=10 到達、または A=30 到達となった評価でも template は critic を呼ぶ。しかし driver は slot 公開後、次の handshake を待たず endpoint 固定・score 計測へ進む。この critic で不一致を検出して親が閉じても、`proposal-wait-timeout` は発生せず、score が成立しうる。「どの role の不一致でも系列は欠測」という記述は強すぎる。

   **最小修正:** 次の生成入力へ還流する critic と、探索終了後の critic を区別し、proposal 停止で欠測にできる射程を明記する。全 role の不一致を規約不適合として扱う意図なら、その報告手順を既存の文書運用で明記する。driver に新しい待機 gate を足す修正は不要。

   **成果物への影響:** 放置すると、同じ model 不一致でも発生位置により score・report の判定が変わり、承認する失敗処理と実際の処理が食い違う。

3. **must-fix — 「後の main も可」が承認対象を広げている。**

   **根拠:** `E/bundle/b5-effective-bundle.draft.json:18`、同 `:150`、同 `:177`、`E/README.md:206`、事前登録 `docs/b5-generator-contrast-preregistration.md:559`。

   `target_commit_rule` は列挙した hash が同じなら後の main も許す形になっている。一方、親 template は path のみで `files_sha256` の対象外であり、settings も実ファイルの hash は列挙されていない。したがって列挙 hash を維持したまま、親指示を変えた後続 commit が条件を通りうる。「全列挙 file の一致」は承認した実験構成全体の一致ではない。

   **最小修正:** 後続 main を許す一文を削り、承認対象の land commit と、その承認に基づく発効 commit の固定 checkout に限定する。hash 網羅性を検査する新 gate は足さない。

   **成果物への影響:** 放置すると、承認後に変更された親指示・起動構成まで、同じ承認の対象として扱える。

4. **must-fix — 新設 process 目録テストは、束の完成に必要な検査を超える。**

   **根拠:** `orchestrator/tests/test_ccbench_spawn_sites.py:2853`、同 `:2854`、同 `:2873`、依頼 `request.md:10`、段4裁定 D-1。

   このテストは既存 `_PRODUCTION_DIRS` の対象外だった launcher へ新たな AST 走査を設け、`runner` の代入形・関数名・呼出し数を固定する。既存目録への必須追随ではなく、検査対象面の新設である。D-1 が認めた投入経路の最小実装・機能テストから、この構文上の閉集合検査までは導けない。

   **最小修正:** この新規テストを削る。registered の exact env／argv、dry-run の無副作用、途中投入失敗の機能テストは残す。

   **成果物への影響:** 放置しても束の値は改善せず、将来の等価な launcher 修正を拒否する検査契約だけが増える。

5. **should — 費用の「最大」「実消費は増えない」は、模型より強い。**

   **根拠:** `E/README.md:162`、同 `:174`、同 `:178`、`E/bundle/b5-effective-bundle.draft.json:105`。

   23,400 s は「30機会を各780 s」とした試算であり、登録した1機会2,700 sからの最大値ではない。「親待ち最大」は「780 s/機会を仮定した A=30 の試算」に直せる。また、k を上げれば、従来の walltime で打ち切られた job が長く走る場合の実 Elapse は増える。「予約だけ」は無条件には成立しない。

   **最小修正:** k=3・40倍という推奨値は維持可能。上記の限定を明記し、「同じ処理が旧 walltime 内に完走する場合、予約増だけでは実 Elapse は増えない」とする。新しい費用 gate は不要。

   **成果物への影響:** 放置すると、680.7 h の承認が、実際より広い待機・失敗シナリオを覆うと読まれる。

6. **should — draft JSON の N1 要約が初回 attempt と retry を混同している。**

   **根拠:** `E/bundle/b5-effective-bundle.draft.json:176`、`E/README.md:144`、同 `:147`。

   JSON は到達すれば一律に「B が1少なくなる」とするが、README は初回 attempt に限定し、retry の skip は `submitted_once` により B を保持すると説明する。README 内の「通常運用では到達しない」は fresh layout 等の前提が明記されており、この限定付き主張への攻撃は不成立。

   **最小修正:** JSON に初回 attempt の条件と retry の例外を写す。N1 の新しい拒否・台帳・report 検査は足さない。

   **成果物への影響:** 放置すると、束単体から読む B 計上の契約が実装・README と異なる。

7. **nit — schedule の同一検査を二重に実行している。**

   **根拠:** `orchestrator/tests/test_b5_contrast_launch.py:347`、同 `:350`。

   `_assert_registered_order_balance` が2 nodeで同じ schedule に対して実行される。MA6 が「LLM4本」では検出できない事情は理解できるが、同じ検査の重複は不要。

   **最小修正:** 4本の検査と6順序・先後均衡の検査を各1回残し、MA6 の検出先を後者へ対応付ける。

   **成果物への影響:** 束・台帳・判定は変わらず、重複した検査と保守対象だけを減らせる。

## 総括

- **NO-GO。** must-fix は **1：version の余分な停止条件、2：最終 critic の帰結、3：後続 main への承認拡張、4：process 目録検査の新設**。
- **削れるもの:** version 異常による系列停止、後続 main の包括許容、新設 process 目録テスト、schedule 検査の重複。
- **残す最小:** registered の purpose／cohort 接続、schedule と stage 投入、D2217 の式の適用、prompt 生成・hash 記録、固定知識射影、必要な model 同定・不一致処置、親 template、これらの機能テスト。
- **攻撃不成立 — launcher の新承認 gate:** checkout・出力分離・freshness の確認は既存 pilot 契約の展開であり、承認情報や新しい認可判定を要求していない。
- **攻撃不成立 — model 不一致停止そのもの:** §4.1 の固定モデル構成を守る処置として必要性はある。ただし所見1・2の過剰条件と射程誤記は除く。
- **攻撃不成立 — 従量課金への切替:** `ANTHROPIC_DEFAULT_OPUS_MODEL` はモデル選択の対応変数であり、認証情報・接続先の指定ではない。この変数自体が課金経路を切り替えるという攻撃は成立しない。template も APIキー・token・代替providerを禁じている。[公式モデル設定文書](https://code.claude.com/docs/en/model-config#environment-variables)
- **攻撃不成立 — rep 1 の一般化・旧 insight の改変:** README は53 sessionの感度分析に限定し、D28との違い、旧結論の訂正を明記している。旧 insight を書き換える提案は不要。
- **攻撃不成立 — 作り直し:** Tier0・node-local lock・D2217 の式は再設計されていない。1系列1親、p=4、2,700 s、fresh context、助言禁止も文書上維持されている。
- **攻撃不成立 — 焦点走を受入全走と偽る主張:** README は焦点走として記載しており、提示ログもその範囲を裏付ける。