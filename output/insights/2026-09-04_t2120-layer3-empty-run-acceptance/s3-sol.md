## 所見

1. 対象 (`orchestrator/campaign/trial_registry.py:5825-5840`, `:5935-5999`, `:6070-6104`; `orchestrator/campaign/autonomous_trial_completeness.py:1053-1067`, `:1130-1142`)

   何が問題か: brief と plan が想定する「campaign 付き admission 失敗 cell が鎖まで到達し、空走後の post-check で拒否される」経路は存在しない。受入可能な report は registered launch であり、その materialized failure cell は `assert_execution_digest_chain` 内で campaignless exact fallback ではない failure として `cell admission failure projection is not exact` により、鎖呼出し前に拒否される。したがって、`do_build=True` で `_fresh_layer3_for_comparison` を一度も通らず受領証発行へ達する report は現行コードに存在しない。

   裁定にどう効くか: 3 形の受理集合が既に閉じているという結論は正しいが、形 (2) の拒否経路と理由は誤っている。本 wave の plan を実装しても実効挙動は変わらず、D1460 の新しい実装とは数えられない。現行 scope のままなら「実装しない」が正しい裁定である。

   性質: real

   推奨する扱い: `s2-plan.md` の主案を採用せず停止する。先行する arm-digest 防壁の変更や順序変更まで広げない。

2. 対象 (`s2-plan.md:24-30`; `orchestrator/campaign/trial_registry.py:5999-6085`; `orchestrator/campaign/autonomous_trial_completeness.py:1130-1142`, `:4911-4926`, `:5002-5033`)

   何が問題か: 主案の returned-ID gate は現行の到達集合では恒真になる。campaign-backed failure は `:1137-1142` で先に拒否され、campaignless failure は受入の `:6080-6085` で先に拒否される。残る正常 campaign-backed cell は、鎖が正常 return するなら必ず `:5002-5033` の fresh rebuild と比較を通る。このため比較成功後に ID を追加する実装では、gate 到達時の期待 ID と返却 ID は必ず一致する。

   裁定にどう効くか: 「述語型と違って実体観測型なら現在の欠落を閉じられる」という plan の選択理由は成り立たない。正常 build を誤拒否するのは、追加忘れ、誤った ID の追加、比較成功前後の配置誤りなど実装バグがある場合だけで、正しく実装した gate は intended failure にも発火しない。

   性質: real

   推奨する扱い: 実体観測型を load-bearing gate として導入しない。正常例のテストで恒真 gate を固定することもしない。

3. 対象 (`s2-plan.md:32`; `orchestrator/campaign/trial_registry.py:5999-6050`; `orchestrator/campaign/autonomous_trial_completeness.py:1137-1142`, `:4911-4923`, `:5002-5033`)

   何が問題か: 対案の述語型も同じ先行防壁により候補集合が空になる。plan の記録位置 `:6022-6050` は digest-chain 成功後なので、campaign identity を持つ exact admission failure は既に存在できない。また将来 `:4911-4923` を変更して failure cell も `:5002-5033` で実体検証するようになれば、述語型は検証済みでも宣言だけを理由に誤拒否する。

   裁定にどう効くか: 述語型は現在は恒常的に不発で、将来は正常化された failure report を過剰拒否し得る。主案の代替にもならない。

   性質: real

   推奨する扱い: 対案も採用しない。

4. 対象 (`orchestrator/campaign/trial_registry.py:5999-6005`, `:6080-6094`; T-2075 insight `README.md:40-48`; `s2-plan.md:68-74`)

   何が問題か: 現行の materialized failure で最初に発火するのは post-check でも新規 hard failure でもなく、先行する `[terminal-completeness] [arm-digest-chain]` である。先行防壁を stub した人工経路なら、鎖の空 return 後に新規 gate が `:6086-6094` の post-check より先に発火し、例外で停止するため DW-M01 の単一理由性自体は保てる。しかし plan の負例は実 digest chain を残しているので、予定した empty-run message には到達しない。

   裁定にどう効くか: T-2075 が post-check を「効いている機構として数えない」とした判断は正しい。新規 gate も現行 tree では同じく機構として数えられない。

   性質: real

   推奨する扱い: 先行防壁を stub して新規 gate を到達させるテストは作らず、plan の負例を実装根拠にしない。

5. 対象 (`orchestrator/campaign/trial_registry.py:5537-5567`, `:5632-5648`, `:6010-6012`, `:6218-6220`; `orchestrator/tests/test_trial_registry.py:1651-1741`, `:2301-2359`)

   何が問題か: 変更前に受理され、plan の正しい実装後に拒否される report の全集合は空集合である。zero-cell は `:5557-5561`、完全 build 束の Layer 3 欠落は `:5632-5648`、campaignless failure は `:6080-6085`、materialized failure はさらに手前の digest chain で既に拒否される。`do_build=False` は `:6010-6012` で鎖を呼ばず、`no-build` reason を積んで受理される。

   裁定にどう効くか: 規律 2 の「緩めない」と D536 は破られない。一方、受理集合が一件も縮まず新規 failure も到達しないため、変更を D1460 の実装成果とは主張できない。

   性質: refuted

   推奨する扱い: 受理集合の変更は「なし」と記録し、これを実装採用の理由にはしない。

6. 対象 (`orchestrator/campaign/p3_autonomous_workload_trial.py:3042-3063`, `:3688-3716`, `:3820-3830`; `orchestrator/campaign/autonomous_trial_completeness.py:4815-5033`, `:5089-5096`)

   何が問題か: 鎖の戻り値追加が producer または standalone verifier の制御を変える経路はない。各呼出しは bare call で戻り値を捨て、producer は後続の journal hash 検査と report 書込み、standalone はそのまま終了する。鎖内の既存 `_fail` と `continue` も、局所 set の初期化、比較成功後の追加、末尾 return だけなら消えず順序も変わらない。なお producer の materialized failure cell が descriptor、binding、campaign identity を保持すること自体は `:3820-3830` と `:3042-3063` で確認できるが、registered producer は `:3688-3692` の digest chain で鎖前に拒否される。

   裁定にどう効くか: 戻り値追加単独は D1460 の producer・standalone no-touch 境界に反しない。ただし intended acceptance failure を到達させるために先行 digest gateを緩めれば、producer と standalone の共通 verifier を変えることになり D1460 に反する。

   性質: refuted

   推奨する扱い: 共有 verifier の既存拒否や順序は変更しない。到達性を作るための緩和も行わない。

7. 対象 (`orchestrator/campaign/paper_story_a1_paired.py:161-180`, `:2086-2103`, `:4379-4430`, `:7195-7219`; `orchestrator/tests/test_paper_story_a1_job_contract.py:386-409`)

   何が問題か: pin が live tree 追随型という主張は正しい。各実行の `expected_head` から blob OID と現在の working SHA-256 を生成し、同じ HEAD と working bytes に再照合する。ただし pin 対象は `trial_registry.py` だけで、`autonomous_trial_completeness.py` は `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` に含まれない。brief の「2 production module を bytes で pin」という表現は誤りである。

   裁定にどう効くか: commit 後の新 HEAD では binding が再導出されるため、今回の編集を固定 digest が妨げることはない。また autonomous module の変更を理由とする pin 更新も不要である。

   性質: real

   推奨する扱い: plan の `s2-plan.md:100-112` の補正を採用し、pin や凍結成果物は変更しない。

## brief と plan が正しかった点

- 受入集合が campaignless failure、campaign-backed admission failure、zero-cell の全形を既に拒否するという最終結論は正しい。
- zero-cell の最初の拒否位置を `trial_registry.py:5557-5561`、完全 build 束の欠落を `:5632-5648` とした plan の brief 補正は正しい。
- campaignless failure は実鎖を呼んだ後に `trial_registry.py:6080-6085` で拒否され、既存テストも `test_trial_registry.py:2330-2359` でその順序を固定している。
- `do_build=False` の受理と `"no-build"` reason は維持され、D536 を破らない。
- 正常 build は `autonomous_trial_completeness.py:5002-5033` の fresh rebuild と比較を通り、既存正例は `test_trial_registry.py:1781-1861` で鎖と fresh の実体到達を確認している。
- returned-ID を比較成功後だけ記録する設計は、単独の観測契約としては述語型より実行事実に近い。
- 戻り値を捨てる producer と standalone verifier の受理・拒否、発行順序は、戻り値追加だけなら変わらない。
- `assert_campaign_layer3_chain` の `:4877-4926` にある既存拒否と `continue` は、plan 記載どおりの局所変更なら一件も消えず順序も変わらない。
- post-check を独立した load-bearing 機構として数えないという T-2075 insight の判断は repo 実体と一致する。
- `test_trial_registry.py` には campaign-backed materialized failure の受入 fixture が現状存在しない。
- pin は固定 digest 型ではなく、実行時の HEAD と working tree に追随する。

## 総括

現行コードには、`do_build=True` の report が `_fresh_layer3_for_comparison` を一度も通らず受領証発行へ達する形は存在しない。brief の受理集合に関する結論は正しいが、campaign-backed admission failure が鎖後 post-check まで到達するという因果説明は誤りである。

主案と対案はいずれも先行する arm-digest 防壁により現行受入では実効不発となる。したがって段 2 plan は採用せず、「実装しない」が正しい裁定である。先行防壁の緩和や検査順序変更は D1460 の受入限定を越えるため行わない。

検査は静的に実施し、pytest その他の実走は行っていない。