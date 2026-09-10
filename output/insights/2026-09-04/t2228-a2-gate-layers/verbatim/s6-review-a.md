## 総括

1.

- 所見: must-fix は 4 件。実体通過、引数 binding、負例の検出力には反証なし。ただし M2、M4、M5、M7 は既存 test でも検出されるため、「新 test だけが検出する」という変異事前登録を満たさない。判定は NO-GO。
- 根拠 file:line: `s4-adjudication.md:101-117`、`orchestrator/tests/test_paper_story_a2_certification.py:62-121,437-497,565-925`
- 成果物への影響 1 行: 放置すると変異試行台帳が既存防壁を新規検出力として誤って参照し、この wave の追加保証を過大表示する。
- must-fix か nit か: must-fix 4 件。静的検査のみで、pytest 緑とは判定していない。

## 実体通過

1.

- 所見: 反証なし。record は monkeypatch 前に実 evaluator から生成され、exact `ConditionArmRecord` と issuer integrity を検査している。driver では保存済み alias の実 context と実 family を通し、record または admission を `SimpleNamespace` で偽装していない。`SimpleNamespace` は裁定で許可された genome のみに使用している。差し替えも指定された 7 leaf に閉じている。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:50-59,565-581,613-717,724-839,844-868,885-910`、`orchestrator/campaign/paper_story_a2_certification.py:655-695`
- 成果物への影響 1 行: certified receipt の record ID、admission、canonical JSON は実 family の判断を参照し、偽造 admission が受理集合へ入る経路を検出する。
- must-fix か nit か: 該当なし。

## 引数の exact 検査

1.

- 所見: 反証なし。両 stub は `captured` の同一性、期待 `DefineRequest` との完全等値、`cxx` を検査し、supply はさらに `cmake`、meaning は `declaration` を検査する。driver の meaning 呼出しには `cmake` 引数自体がないため、その stub に検査漏れはない。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:583-611,782-810`、`orchestrator/campaign/paper_story_a2_certification.py:618-667`
- 成果物への影響 1 行: `captured=object()` は `:788` または `:804`、`requested_value=defaults[macro]` は cell-1 の `:789` で落ち、別 tree・別値の record が certified receipt に結合される変異を防ぐ。
- must-fix か nit か: 該当なし。

## 負例の非恒真性

1.

- 所見: 反証なし。負例は `BACKOFF_FIXED` だけの単一 macro で、issued red と実 evaluator の green meaning を実 familyへ渡して `admitted is False` を直接確認する。その後の driver 例外と exact detail も別に検査している。admission 無視または例外握りつぶしでは context が正常 yield し、`pytest.raises` が失敗する。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:688-717,885-925`、`orchestrator/campaign/paper_story_a2_certification.py:669-695`、`orchestrator/campaign/condition_meaning_gate.py:3921-3947`
- 成果物への影響 1 行: red supply を無視した receipt、certified campaign、試行台帳への誤受理を検出し、拒否 detail の参照も保持する。
- must-fix か nit か: 該当なし。docstring も実 configure failure ではなく family/wiring 負例と正しく限定している。

## 変異の帰属

1. M1

- 所見: kill 自体には反証なし。ただし最初に落ちるのは直接の `negative_admission.admitted is False` だけであり、事前登録にある driver の `pytest.raises` は実行されない。
- 根拠 file:line: `s4-adjudication.md:109`、`orchestrator/tests/test_paper_story_a2_certification.py:885-901`
- 成果物への影響 1 行: 受理集合拡大は防げるが、試行台帳の kill point を二つと記録すると実際には未到達の driver assertion を参照する。
- must-fix か nit か: nit。kill point を `:888` の一つへ訂正すればよい。

2. M2

- 所見: 新 test の receipt 完全一致でも落ちるが、既存 test が先に helper source の `use_class="paper"` を固定しており、変更前 test file でも SURVIVED にならない。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:67-68,860-868`、`s4-adjudication.md:103-110`
- 成果物への影響 1 行: 放置すると試行台帳が、既存防壁による use class 保護を新 test 固有の admission payload 保護として誤記する。
- must-fix か nit か: must-fix。既存 test が生存する別変異へ再照準する必要がある。

3. M3

- 所見: 反証なし。`admission` key の削除は正例 receipt の辞書完全一致 `:860-868` で落ち、射影内の既存 test に同じ payload assertionはない。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:860-868`、`orchestrator/campaign/paper_story_a2_certification.py:686-695`
- 成果物への影響 1 行: admission のない材料 receipt が作られ、certified 選択の根拠参照が欠落する変異を新 test が検出する。
- must-fix か nit か: 該当なし。

4. M4

- 所見: 新 test の exact substring でも落ちるが、既存 `_assert_condition_gate_rejection` が warning detail の存在を既に要求しているため新 test 固有ではない。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:500-562,912-916`、`s4-adjudication.md:103-112`
- 成果物への影響 1 行: detail 脱落自体は既存防壁で拒否される一方、試行台帳の新規検出力という参照は誤りになる。
- must-fix か nit か: must-fix。既存 assertion が殺さない formatter 変異へ再照準する必要がある。

5. M5

- 所見: 事前登録と二重に不一致。既存負例が `BACKOFF_NOINLINE` の欠落で既に落ち、さらに新 test の最初の失敗は最終 call count ではなく、cell-1 の `BACKOFF_FIXED` を cell-0 の `BACKOFF_NOINLINE` と照合する request equality である。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:559-562,784-794,869-883`、`s4-adjudication.md:113`
- 成果物への影響 1 行: 試行台帳が既存の macro 欠落防壁を新規 call-count 防壁と誤認し、実際の赤理由も誤った assertion を参照する。
- must-fix か nit か: must-fix。既存 test が生存し、想定 assertion で落ちる変異へ再登録が必要。

6. M6

- 所見: 反証なし。cell-0 は値が既定値と同じため通るが、cell-1 `BACKOFF_FIXED=10` で期待 request と不一致になり、supply stub の exact assertion が落とす。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:583-593,646-672,782-794`、`orchestrator/campaign/paper_story_a2_certification.py:618-629`
- 成果物への影響 1 行: requested value を default へ取り違えた record が certified receipt に載り、選択結果の測定値参照がずれる変異を検出する。
- must-fix か nit か: 該当なし。

7. M7

- 所見: 新 test の `len(receipts) == 2` でも落ちるが、既存の multiple-cells test が `len(receipts) == len(genomes)` を要求しているため変更前 test fileでも検出される。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:437-497,847-856`、`s4-adjudication.md:103-115`
- 成果物への影響 1 行: cell 欠落は既存防壁で拒否される一方、試行台帳が新 test だけの検出力として記録すると参照関係が虚偽になる。
- must-fix か nit か: must-fix。既存 test が生存する別の multi-cell wiring 変異へ再照準する必要がある。

## 甘さと差分範囲

1.

- 所見: 新 test には compiler 不在時の `pytest.skip` が一つある。xfail はなく、期待 status・reason は exact 値で固定され、実測に合わせて赤を緑へ下げる処理はない。
- 根拠 file:line: `orchestrator/tests/test_paper_story_a2_certification.py:574-580,620-643`
- 成果物への影響 1 行: compiler のない実行面では全変異の検出信号が消えるため、試行台帳は親の本走が SKIP でないことを明示的に確認する必要がある。
- must-fix か nit か: nit。親が投入済みの本走結果で非 SKIP を確認する条件付き。

2.

- 所見: 反証なし。揮発 job payload の焼き込みはなく、`/scratch`、`abc1234`、fixture manifest は leaf 引数検査用の合成値である。既存 helper、既存 test、pin、fixture の変更もない。
- 根拠 file:line: `s5-diff.patch:1-5,165-285,374-376`
- 成果物への影響 1 行: 過去の certified 選択結果、材料レポート、試行台帳の値や参照は変更されない。
- must-fix か nit か: 該当なし。

3.

- 所見: 反証なし。差分は `orchestrator/tests/test_paper_story_a2_certification.py` への追加だけで、production 差分はゼロ。
- 根拠 file:line: `s5-diff.patch:1-5,374-376`
- 成果物への影響 1 行: production の受理集合と既存成果物の値は不変で、変更対象は検出力だけに閉じている。
- must-fix か nit か: 該当なし。