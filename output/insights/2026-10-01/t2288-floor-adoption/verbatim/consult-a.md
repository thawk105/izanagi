## 所見

1. **real / must — 受理条件「全充足」は、親の数値確認だけでは証明できない。**
   brief の「各窓62標本・欠測0・分離約231時間・floor < 1」は、親の報告を前提に数値条件へ適合する。しかし、期待 spec の現在の hash 一致は、**結果を見る前の選定**と**事前登録の対象集合との意味的一致**を証明しない。D1974 はこの二点も機械保証の外に置く。D1641 の同一候補・事前無作為化・probe/journal 等も、`terminal complete` だけへ還元できない。条件違反を発見したという意味ではなく、全充足という結論の根拠が射影資料では不足している。
   根拠：[D1974:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/D1974.md:23)、[D1641:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/D1641.md:16)、[issuer の非保証:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:48)。

2. **real / must — 「全 checkout で36件が binary 不在により赤」は過大な一般化。**
   記入→集約再構成→spec再検証→binary `lstat` 失敗→レポート拒否、という因果はログとコードが支持する。ただし集計は **34 failed＋2 errors**。少なくとも wiring の1件は別原因で、提供ログは25件の詳細を省略しているため、残り全件の原因も個別には確証できない。基準走259 passedも、焦点走の1258 passed＋36赤と同一母集団の対照ではなく、両ログは受入全走でない旨を明記する。また binary 配置済み checkout まで拒否するとする根拠はない。
   根拠：[焦点ログ:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:136)、[集計:248](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:248)、[省略件数:987](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:987)、[基準ログ:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/baseline-without-entry.log:1)。

3. **refuted / should — wiring を「未commit差分を拾う型」とする判断は正しい。**
   ログ内のテスト本文は `git status --short` から `output/` 外の変更を集め、許可する二つの Python ファイルとの包含関係を検査する。実際の余剰は事前登録文書であり、floor の値や binary を検査していない。したがって、この1件を登録後の clean main に残る失敗として数えるのは誤り。
   根拠：[焦点ログ:581](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:581)。

4. **refuted / should — binary 不在の拒否は、現行実装の契約から逸脱した偶発的な欠陥ではない。**
   集約 loader は出所から再構成し、期待 spec を producer で読み直す。その producer は binary の実在・非symlink・hash を束縛するため、拒否は実装どおり。ただし、**D1974／D2103 が「材料レポート閲覧時にも binary が必須」と明示裁定した、とまでは言えない**。D2103 は loader への委譲を定める。依存を再設計する余地と、現行検証を勝手に省略してよいことは別である。
   根拠：[D2103:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/D2103.md:15)、[集約再構成:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1275)、[spec再検証:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1059)、[binary束縛:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/floor_pair_driver.py:1136)。

5. **real / must — 記入後の影響は、pin の受理／拒否を分けて記録すべき。**
   binary 不在で拒否される場合は、`authoritative_floor_rejected` により**評価器を呼ぶ前に生成停止し、分析 verdict 自体が出ない**。§11.0追記の「resolver が拒否しても floor 不在を渡す」は現行コード・テストと不一致である。検証を通る場合は exact `Fraction` が評価器へ渡り、floor欠落による `floor_domain_error` 固定は解消する。ただし、特定の成功 verdict、§7.1四分類の実効化、B-4実走済みを意味しない。
   根拠：[§11.0追記:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/prereg-s5-floor-s11_0.md:68)、[生成器:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_material_report.py:212)、[拒否時テスト:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_material_report.py:1129)、[present時の主張範囲:891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_material_report.py:891)。

6. **real / must — P2だけでは、今回の依頼を完了扱いできない。**
   D1641の「採用裁定（成果物を§5へ記入するか）」は、裁定と記入を同一wave・同一commitで行うとまでは明記しない。したがって延期自体を直ちに矛盾とは断定しない。しかし今回の依頼は「採用なら…記入する」、brief自身の完了条件も「pin記入＋非None」である。**測定成果の受理・pin固定と、§5登録未完了を区別し、後者を完了として閉じないことが必要。**
   根拠：[D1641:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/D1641.md:8)、[依頼:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/request-md_3.txt:14)、[brief:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/s1-brief.md:3)。

7. **refuted / should — 記入延期だけをHARKingとする根拠はない。**
   D1641は測定後の採用裁定を明示的に予定する。統計関数・対象集合・pinを固定したまま、接続上の問題で登録を延期することは、結果に合わせた仮説・分析方法の変更とは異なる。ただし後から値や集合を選び直さないことが前提。§0については射影の「floor欄だけでは発効しない」という記述と整合するが、**§0・§1本文は射影に含まれず、両節への全面的な適合までは確認不能**。
   根拠：[材料:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/w2-adoption-material.md:12)、[事前登録抜粋:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/prereg-s5-floor-s11_0.md:74)。

8. **refuted / should — floorセルだけで「有効登録」と「現行テスト維持」を両立する回避策はない。**
   既存 binary の `place` は測り直さずに当該不在原因を除く候補なので、レポート接続に必ずコード変更が必要という断定は強すぎる。しかし配置しても、実文書について `resolver(...) is None` を要求するテストは有効pinと両立しない。D2103自身が登録waveでの更新を予定している。`未記入`維持は未登録、別表記・注記付きpinは拒否または依頼不充足になる。**必要なのは少なくともテスト更新を扱える作業範囲であり、binary検証の緩和が必須とは限らない。**
   根拠：[place手順:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/runbook-binary-place.md:5)、[実文書テスト:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:826)、[D2103:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/D2103.md:59)、[resolver:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1523)。

## 総括

**NO-GO（現状のP1・P2の説明と完了扱い）。記入保留という実務判断自体は支持する。**
受理条件の人手確認根拠を補い、「全checkout・36件がbinary原因」を限定し、拒否時はverdict生成前の停止と訂正する。
測定受理・pin固定と§5登録未完了を明記し、必要なテスト更新と実行環境の扱いを含む後続作業へつなぐ。
