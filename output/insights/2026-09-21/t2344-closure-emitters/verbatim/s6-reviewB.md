## 所見 1: P2 の実測は、exact-85 の収載条件を満たす証拠にならない

**判定: real / must-fix**

**根拠:** `s4-ruling.md:36–47`、`stale-tree-locks.json`、`rulings-verbatim.md` の D1653・D2193・D2194 項4。

25本はすべて同じ pre-85 commit `11d46a74a` に由来する。同じ固定木による反復であり、exact-85 の並走木が land 後に lock を発行する独立した証拠ではない。また時刻は `mtime` であり、それだけでは発行時刻も確定しない。「増えうる」という機序は支持するが、「空白が再発する」「exact-85 にも要る」という断定は過剰である。

読める Git オブジェクトでは、確認時の `main=959c0f1ca`、`HEAD^=71e572b3c`、着手 commit `5efd69367` はいずれも85本。`exact85-reachable.json` も着手時の clean な木で capture 成功を記録している。したがって生成可能なソース木は存在する。しかし、その checkout が現在稼働し、land 後まで保持され、campaign を発行することは確認できない。他 checkout と `git worktree list` は読んでいない。

D2193 自体が corpus 条件を明記し、D2194 はそれを参照している。§2 の開示は未充足を隠してはいないが、親の優先解釈が既裁定から必然的に導けるように読ませる根拠部分は修正が必要。

**直し方:** 観測・生成可能性・将来予測・親の政策判断を分離する。corpus 条件より同 commit 収載を優先する扱いは、既裁定の当然の帰結ではなく、明示的な裁定パッケージ候補として示す。

## 所見 2: corpus 未確認の収載には、具体的な受理・保守上の費用がある

**判定: real / should**

**根拠:** `campaign_lock.py:775`、`artifact_admission.py:1093`、`test_artifact_admission.py:3832`、`s4-ruling.md:42–47`。

追加されるのは単一の ordered tuple だが、許可される lock が1本という意味ではない。記録 commit の85 blobと整合する合成 lockも、他の検査を満たせば歴史入口で読める。新設テスト自身が現行 fixture の map を85本へ投影して、この受理を確認している。

これは certified への抜け道ではない。一方、未確認の実在 corpusを理由とせず歴史型・scope・validator・テスト群を恒久保守し、「production に存在した grammar なら事前収載できる」という先例を作る費用はある。§2 の「非対称性」は収載しない側の費用に偏っている。

**直し方:** 合成入力を含む受理集合、専用実装の保守、corpus 条件への先例という3点を開示する。発行時刻を認証する新機構の追加は不要。

## 所見 3: 採用済みの「未検出」への訂正が元資料に残っていない

**判定: real / must-fix**

**根拠:** `s4-ruling.md` §1 の A-2・B-2、`measured-facts.md:60–69`、`brief.md:26` と P2。

裁定は走査条件付きの未検出へ限定すると決めたが、実測文書には「実在 corpus は着手時点で0本」「約8.5時間では0本」が残る。85-keyという件数分類も exact grammar の証明とは異なる。brief は、その同じ資料を「記録済み exact-85 lock」の根拠にしている。

**直し方:** 元資料に訂正または明確な失効注記を付ける。「指定走査で85-key v2は未検出」「exact照合済み corpusは未確認」とし、brief の成果物影響は条件文にする。

## 所見 4: DW-G05 の値への影響が不足している

**判定: real / should**

**根拠:** `brief.md`「scope」、`s4-ruling.md` §7、`artifact_admission.py:400`・`:1362`、`p3_b4_closed_critic.py:636`、D2081「保証しない範囲」。

scopeと新規E1だけでなく、変更した `artifact_admission.py` の bytesから求める admission receipt の `validator.sha256` が変わる。これは歴史 campaignを新たに読む場合にも及ぶ。B-4 projectionの材料にも同ファイルが含まれる。

未commitの11本に対する説明は、中央captureを通る起動・certified受理については正しい。ただし、編集された発行器自身を呼ぶ場合だけでなく、11本のどれかがdirtyなら中央受理が止まる。逆にB10 report分岐には今回のcapture拡張が掛からない。commit済みの変更を記録時bytesと同一にする要求は追加されていない。

**直し方:** 新規receiptのvalidator hashとB-4 projectionへの影響を追記し、dirty拒否を中央capture経路に限定して説明する。記録済み成果物の再生成は不要。

## 所見 5: scope外の実装追加・局所追随漏れは壊せなかった

**判定: refuted / should相当の懸念、修正不要**

**根拠:** `impl-diff.txt` 全ハンク、commit `f605a7ba2`、`verify-impl.json`、独立したAST・旧ソース比較。

変更はproduction 3本とtest 6本だけ。新module、registry、実行時閉包計算、発行時bytes同一性検査の追加はない。追加validatorは裁定指定のexact-85専用実装である。`b10_backoff_shape_sweep.py`、`layer3_report.py` 本体、docsは不変。

要求された追随も確認できた。

- binding docstring 3箇所、fixture docstring、件数assert。
- s8b unavailable scopeの独立literal、`CURRENT_E0_EPOCH`。
- layer3の歴史85 param・固定epoch表・現行96 param。
- timeout 5箇所の960化、既存22本と新11本のdriftテストの維持。

数値85／163／78と関連symbolを探索した範囲で、残る関連値は歴史scope・歴史paramであり、現行consumerの追随漏れは見つからなかった。

**直し方:** 不要。旧63／62／24のvalidator・例外文面・scopeは不変。ただし「分岐も1文字不変」は厳密には違い、decoderの旧63先頭分岐は新85分岐挿入に伴い `if` から `elif` になっている。裁定表現は「既存条件式・本体・挙動不変」とすると正確。

## 所見 6: 保証の名乗りとD2081適合は壊せなかった

**判定: refuted / should相当の懸念、修正不要**

**根拠:** `artifact_admission.py:76–87`・`:125–136`、差分全体、commit `f605a7ba2` のメッセージ。

現行scopeは96／173／77、発見集合の定義、日付・commit・本版seed、集合外の除外、収載source bytesの例外を明記する。発行器名・追加内訳・実行時計算は含まない。歴史85 scopeは変更前の2定数と一致することを独立に確認した。

差分・追加test名・docstring・commit messageに「推移閉包が閉じた」という肯定的な保証拡張はない。`source-bound` 等の出現は否定・制限の説明である。

**直し方:** 不要。未収載77という限界を最終成果報告でも維持する。

## 所見 7: 「16秒以上」が過小だとは焦点走から立証できない

**判定: refuted / should相当の懸念。ただし追認は未了**

**根拠:** `s4-ruling.md` §6、`s3-lensB.md` 所見9、`focus-f1-summary.md`。

16秒以上は逐次durationの**増分**の初期見積り。焦点走の313.01秒は31ファイル全体の並列wallで、319秒はjob Elapseである。変更前の同条件baselineもなく、この比較で過小とは判定できない。

ただし外挿は63件時点のledgerに依存し、既存fixtureが85→96本へ大きくなる費用を未計上としている。16秒を代表値や受入wall予測として使う根拠もない。

**直し方:** 「部分外挿による下限寄りの初期見積り、未追認」とする。追認時は同条件の前後durationを比較し、並列wallとは分けて記録する。

## 所見 8: 焦点走の赤は0件。ただしskip説明が不正確

**判定: 赤の懸念は refuted／skip説明は real / should**

**根拠:** `focus-f1-summary.md`、`focus-f1.log` の結果行と `IZANAGI_GROWTH_HOLD_V1`。

生ログは **4441 passed、9 skipped、failed/errorなし**。要約記載のSHA-256とも一致した。赤の原因切り分け対象はない。本レビューではpytestを実走していない。

一方、「9件は既存の環境依存skip」という説明に対し、生ログには少なくとも5件の明示的なgrowth holdが記録されている。これは単なる環境依存ではない。またログ自身が受入全走ではないと明記している。

**直し方:** skipはholdを含む内訳に訂正する。焦点走の緑を、変異検査・受入全走の完了とは扱わない。

## 総括

**NO-GO：P2の根拠の一般化と、採用済み訂正が残る資料の修正が必要。**
最大のriskは、corpus未確認の例外判断が既裁定から当然に認められた先例として残ること。
実装のscope逸脱・局所追随漏れ・保証拡張は静的検査では壊せなかった。焦点走の赤は0件。
探索した `orchestrator/campaign/p3_b4_projection_contract.py` は不存在。停止せず、実在する `p3_b4_closed_critic.py` で参照を確認した。