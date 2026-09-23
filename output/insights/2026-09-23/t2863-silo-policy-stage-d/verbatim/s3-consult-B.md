静的検査のみ。ファイル変更・テスト・計算投入はしていない。以下、`C/`＝`orchestrator/campaign/`、`Q/`＝`orchestrator/tests/`。

### B1・must-fix・二値が答える問いを親 brief まで揃える

**対象:** brief [brief.md:5](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/brief.md:5)、同:15。plan [s2-plan.md:103](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:103)、同:151、252–255。

**内容:** 得られる二値は「固定した16点で、所定の除外条件と再測条件を満たす床超点を観測したか」である。関数単位の空間全体に地形が存在するかの二値にはならない。plan は「なし」を限定しているが、brief の研究前進・完了判定には反映されていない。

「あり」も静的5／10 µsだけで成立しうるため、状態・要因依存・複数hookを使う探索やLLMの必要性までは示さない。逆に「なし」でも、lock待機は全点0、retry閾値は4固定、成功時の状態はresetなので、未探索部分は大きい。

**放置時の影響:** 同じ測定結果が、関数空間全体の否定やLLM継続の根拠に過大解釈される。

**推奨:** brief の研究前進と完了判定を plan:252 の限定に合わせる。後段への二値には固定の射程説明を添え、未完了・判定不能の `null` を「なし」に変換しない。空間拡張や追加計測で今回の問いを膨らませる必要はない。

### B2・should・全床超点の再測を完走する必要はない

**対象:** plan [s2-plan.md:249](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:249)、同:251、312、343。brief:15。

**内容:** 存在判定なので、別jobで1点が全条件を再現した時点で「あり」は確定する。「1点の再測失敗で他点まで否定できない」という plan:343 は正しいが、そこから全候補の再測完走は導けない。

**放置時の影響:** 初走で多数が床を超えるほど、確定済みの二値に寄与しないbuild・verify・benchが増える。

**推奨:** 初走の該当点を事前固定のID順で再測し、最初の再現で終了する。再測job内の基準は共有し、各候補の両verifyと5 repは維持する。「なし」には全該当点の再測完了が必要とする。新しい探索・スケジューラは不要で、既存の候補ループの停止条件で足りる。

### B3・should・対照の重複が二値に不要な既存変更を生む

**対象:** brief [brief.md:14](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/brief.md:14)、同:16。plan:187–190、223、265。

**内容:** 二値の分母は `abort0` だけである。軸OFFの2対照を両jobで繰り返すことは、その二値の要件ではない。stockは手順書§3-Dとの対応、flagoptは既知最良との差を見る報告上の価値があるが、「骨格コスト」の純粋な分離にはならない。plan:341の訂正は妥当である。

特にflagoptを残すためだけに、`C/silo_policy_coverage.py:372` のbuild flags選択を変更し、`Q/test_ccbench_spawn_sites.py:2935` の382行pinを追随させることになる。

**放置時の影響:** 初走は19 unique caseに対して22 case実行となり、判定外の比較のために既存build経路の変更と回帰確認が増える。

**推奨:** 3対照を残すなら、`abort0` は各job、stockとflagoptは片方のjobで各1回として初走20 caseにする。両軸OFF対照はそのjob内の参考比較として別掲する。さらに本題だけへ絞るならflagoptを今回から外す裁定を提案する。これなら `stock_backoff` 追加と、それに伴うpin追随も不要になる。

### B4・should・本文入力の小変更は局所化より小さいが、build一般化は別判断

**対象:** plan [s2-plan.md:183](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:183)、同:257–276。brief:12、19。

**内容:** 「新moduleに閉じれば小さい」とは限らない。比較結果は次のとおり。

| 案 | 実際の差分・波及 |
|---|---|
| `_source(body=...)` の追加 | `C/silo_policy_coverage.py:546–565` の既存checkout・patch・4段検査・書込み照合をそのまま利用できる。変更位置はbuild sinkより後なので、これ自体は382行pinを動かさない。 |
| 新moduleにsource準備を複製 | 同:548–564の処理を重複保守する。`prepare_policy()`を利用できても、patch順序と書込み照合の責任が新たに生じる。 |
| flagopt用のbuild処理を新設 | 同:362–387のconfigure・gate・buildを複製し、sink／materializerの追随範囲を増やす。既存引数の小変更より大きい。 |

既存登録は `C/materializer_admission.py:103` のbuild helperに付いている。driver追加だけを理由に新しい登録やbuild wrapperを設ける必要はない。

**放置時の影響:** 既存ファイルを触らないことを優先すると、実装総量と登録簿の変更が逆に増える。

**推奨:** `_source` の本文引数は採用する。flagoptを残す場合だけ狭い `stock_backoff` 引数を追加する。任意Genome・任意flags・新build wrapperへの一般化は行わない。既存登録の説明文修正と新規登録を混同しない。

### B5・should・偶数／奇数分割はM因子とjobを完全に重ねる

**対象:** plan [s2-plan.md:128](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:128)、同:223。

**内容:** 表のID順では最下位bitがMである。偶数／奇数indexへの分割は、一方を全点5 µs、他方を全点10 µsにする。L因子によるjob分離を避けながら、M因子では同じ問題を作っている。同jobの `abort0` は共通の速度差を扱えても、nodeと方策の相互作用まで除去しない。

**放置時の影響:** Mに偏ったjob差が初走の床超判定と再測対象の選別に混ざる。

**推奨:** 例えば `L xor S xor R xor M` で8点ずつ割れば、各jobで各因子が4点ずつになる。固定ID表の変更だけで済み、乱択器や追加計測は不要。二値目的なので因子効果の推定まで追加しない。

### B6・must-fix・P6は実測単価ではなく、投入用の総額も未完成

**対象:** brief [brief.md:17](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/brief.md:17)。plan:286–312、344–346。

**内容:** 793秒はbalancedの5 caseとjob準備を含む総Elapseである。`C/silo_policy_coverage.py:52–55` はrratio 50、同:719–727には準備用stock buildがある。したがって「160秒／方策＋rep追加分」はwrite-heavyの観測単価にならない。planの訂正は正しい。

現案の規模は初走22 case＋再測最大17 case＝39 caseであり、さらにjob準備、焦点走、受入、変異がある。plan:312はこれらを後で積み上げるとしているが、変異の回数・対象と修正再走の扱いは未提示である。2job化自体はnode時間を減らさない。

**放置時の影響:** 「約1 node時間」の初走換算がタスク総額に見え、再測や試験を含めた投入判断を誤る。

**推奨:** **投入前のmust-fix**として、P6の「単価」を撤回し、用途・回数・出所・未測定部分を分けた総額を出す。初走、最大再測、必要な焦点走、受入、変異、修正再走の枠を含める。C段の骨格負例・機構変異全体をD段で再演する必要はない。5 repの追加指定時間は初走全体でも264秒なので、まず対照重複と不要な再buildを削る方がよい。

### B7・should・IR契約の試験は残し、同じ全点検査の重複を減らす

**対象:** plan [s2-plan.md:73](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:73)、同:159–175、278–284。

**内容:** min/max・飽和加減算・有界shift・深さ4・node64・状態4 fieldは設計§5の契約なので、16点が使わない演算を理由に実装や基本境界試験を削るのは不適切である。一方、次は整理できる。

- 全点TU compileを通常testと正式検査で実行し、未使用引数のcompileをさらに別立てする。
- 深さ上限で探索を打ち切れるのに、循環検出を独立した一般機構として作る。
- 既存の4段検査自身の自己試験を、新driver側にも展開する。

`C/silo_policy_compile.py:114–117` にgrammar→compileの入口、同:158にUBSan harnessがある。既存の4段検査と本文一致は `Q/test_silo_policy_coverage.py:498` で検査している。

**放置時の影響:** 新しい意味の検証より、同じcompileと検査器の再確認に実装・試験時間を使う。

**推奨:** 全点grammar/TU検査は1つのparameterized testを正式検査にも利用し、未使用引数の確認をそこへ統合する。UBSanは既存harnessで正式1回。状態更新・飽和・shiftは描画結果の意味を確かめる小さい有限例を残す。driver testは本文が既存入口を通ること、verify失敗時の停止、5 rep、集計境界に絞る。

### B8・should・結果schemaは凍結記録に留め、将来のIR交換形式へ育てない

**対象:** plan [s2-plan.md:222](/home/SFC/tanab/.claude/jobs/8c90adaa/wave/s2-plan.md:222)、同:228–243、324–330。

**内容:** subset実行と計測なしのaggregateは分割・再測に必要であり、2 mode自体は過剰ではない。ただし `factors`・`ir`・`ir_id`・`body_sha256`・`space_version`・`canonical_ir()`を独立した正本として扱うと、今回は使わないIR入出力契約の維持が始まる。

**放置時の影響:** 固定16点の偵察が、将来のLLM×IRや比較試走向けのschema設計へ膨らむ。

**推奨:** 固定case定義と描画本文を一度凍結し、各runはcase IDと本文hashで参照する。既存のsource evidence・build receipt・verify結果・生repを保存し、中央値と二値はaggregateで導出する。IRのJSON入力、復元、schema移行、汎用候補登録は今回作らない。

## 総括

**NO-GO（現briefの研究主張と投入見積りについて）。**
- must-fix B1: 二値を固定16点・所定条件下の観測へ限定し、親briefまで揃える。
- must-fix B6: 793秒を方策単価にせず、試験・変異・最大再測を含むタスク総額を投入前に示す。
- IR契約・両verify・5 rep・別job再測は維持してよい。
- 主な削減先は、成功確定後の再測、軸OFF対照の重複、検査の重複である。
- `_source(body=...)` は局所複製より小さい。flagopt対応の既存変更は対照を残す裁定と分ける。
- 偶数／奇数分割は修正する。新しいgate・台帳・一般化は不要。