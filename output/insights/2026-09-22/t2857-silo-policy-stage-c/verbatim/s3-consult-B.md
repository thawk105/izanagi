## 所見

以下、`brief`・`plan` は指定された `brief.md`・`codex/s2-plan.md`、`D2214` は指定された逐語、`設計` は `output/insights/2026-09-21/silo-function-synthesis-space/README.md` を指す。`C/`＝`orchestrator/campaign/`、`Q/`＝`orchestrator/tests/`。静的点検のみで、ファイル変更・build・pytest・計算投入は行っていない。

1. **must-fix — 計算表の単価が異なる仕事を表しており、投入総額が未確定。**
   根拠：`plan:458–480`、`brief:36`。T-2844 の 132 秒は stock・負例を含む **6 走の coverage job 全体**であり、136 秒は **787 passed の pytest 焦点走**である（`output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md:18,69,152`）。136 秒を新しい機構変異一ケースの単価にする根拠はない。plan は仮置きと断っているが、この表だけでは投入判断に使えない。
   **影響：** 計算レポートの総 node 時間と、投入前確認に提示する金額相当の資源量が変わる。
   **代案：** CCBench の負例・焦点 harness・機構変異、Python の焦点 test・検査器変異 matrix、受入を別行にし、build 再利用、120 秒 timeout、再走を含めて積み上げる。

2. **must-fix — 生死確認に「何が出れば次へ進むか」がない。**
   根拠：`plan:353–379` は四方策と stock の評価手順を定めるが、継続・停止の判定を定めていない。`brief:10` の build・verify・identity だけでは、複数 hook・状態という研究上の追加面が実際に使えるかを判断しきれない。`docs/dev-wave/core.md:60–63` は生死実験先行を要求する。
   **影響：** 同じ測定結果から、後続の D/E/F を進めるか止めるかが担当者次第になる。
   **代案：** C の「生」は、四方策の契約適合・build・legacy/性能構成 verify・honest identity・throughput 出力に加え、専用 probe による retry と成功通知後の状態継続の成立とする。必須方策や機構が成立しなければ修復し、許可範囲で成立しなければ後続を止める。**一走の性能差が小さいだけでは軸を死と判定しない。** 地形の判断は D に残し、C 成功から E/F へ自動移行しない。

3. **must-fix — 焦点試験と専用方策の成果物・依存関係が未割付。**
   根拠：C の所有表は四本の smoke 方策だけを列挙する（`plan:251–262`）。一方、最大待機、`UINT32_MAX`、状態の `epoch`、holder/releaser 制御を要求する（`:280–312,323–329`）。実 CC harness の初期化・link は未確認で、所有 path もない（`:510`）。さらに B の UBSan が C 所有の四方策を読む（`:245`）、C の smoke が B の検査器を読む（`:361`）。単純な「A→B/C」では実行まで独立しない。
   **影響：** C 出口の最大待機負例・状態寿命・再読込の証拠が欠落するか、別々に作った方策が異なるものになる。
   **代案：** C に焦点 harness の source/build 駆動と専用方策群の所有を明記する。最大待機の abort/lock 応答、retry 終了条件、clamp 正例、状態更新列を固定する。C は方策資材を先に供給し、B の UBSan と C の smoke は両者の実装完了後に統合実行する。

4. **must-fix — producer/consumer 契約一致の必須条件を、未決事項のまま実装へ渡している。**
   根拠：`D2214:45–48`、`設計:499–510` は着手前の接続仕様と検査器の一致を要求する。`plan:211,515,530` は無名仮引数を未決とし、接続仕様を固定する成果物・担当も示していない。
   **影響：** producer が合法として出す本文を consumer が拒否するなど、受理集合が実装子の判断で変わる。
   **代案：** 段4で無名仮引数の扱いを裁定し、既存設計への差分として B の契約表・fixture と一致させる。role 本体や IR renderer は作らず、将来の C++/IR producer が共有する出力契約だけを固定する。

5. **should — C が重く、共有 registry 更新まで一括すると実装上限のリスクが高い。**
   根拠：`plan:255–262,381–402,510–515`。C は十一枚の診断 patch、二 driver、実 CC harness、方策、test、多数の既存 registry を持ち、harness と評価 authorization に未確認が残る。B も型付き parser から UBSan まで大きい。
   **影響：** 途中終了時に patch・registry・期待集合の片側だけが揃い、受入不能または証拠不足になる。
   **代案：** C を「診断 patch・焦点 harness・coverage」と「smoke・既存 registry/meta-test 統合」に段階分割する。共有ファイルは後者だけが編集する。B は grammar と compile/UBSan を順次納品する。400 call・7200 秒に収まるという実測根拠はなく、上限超過を断定はしないが、C が最も危険である。

6. **should — tokenizer 新設の理由に、既存 token の後段検査で済むものが混ざる。**
   根拠：`plan:176–187`。既存 `_tokens()` は識別子・数値・punctuator の文字列を保持する（`C/backoff_hole_grammar.py:413–439`）。代替綴り、`__`、`::`、suffix が token 化できること自体は再利用不能の理由ではなく、後段で拒否できる。位置情報の不足は実在する（同 `:404,424,439`）が、詳細な offset/line/column は今回の必須成果ではない。
   **影響：** 重複した字句実装の差が将来の受理集合を変え、検証・保守範囲が増える。
   **代案：** まず既存 tokenizer＋この軸だけの字句フィルタを候補とする。部分言語を扱う parser/type checker は新設が必要。独自 lexer を採る場合も位置情報だけを理由にせず、既存方式で満たせない契約を限定して示す。汎用 tokenizer framework の新設は不要。

7. **should — brief のアンカー説明と機械保護の断定を修正する。**
   根拠：`brief:32` は lockskip を「内側」とするが、patch は `for (;;)` の直前に `continue` を入れる（`patches/broken-silo-lockskip-validation.patch:5–20`、`T:158–160`）。また hunk 行番号のずれだけでは適用不能にならず、既存の適用は通常の `git apply`（`C/patchharness.py:204–211`）。`brief:26` の hook 拒否も今回の実測証拠はない。
   **影響：** 不要な負例 patch の作り直し、または実証されていない保護への依存を招く。
   **代案：** plan の「骨格が hunk 文脈を変えるため norw/lockskip を更新」に訂正する。early-unlock は厳密適用結果で判断する。計算ノードで実行する方針と、hook が実際に拒否するという主張を分ける。

8. **should — docs の新しい表は忠実だが、周辺の旧限定が残る。**
   根拠：`docs/axis-onboarding.md:247–255` の第3列は `設計:487–495` を実質的に保持し、justification の扱いと planner 例外（`:202–205`）も `D2214:39–43` に合う。一方、`:234` の「第3列の追補は本注記のみ」、`:342` の auditor/digest 照合「コード片軸のみ」は、新しい表と読み合わせると不整合になる。
   **影響：** 後続 E の担当者が参照箇所によって auditor/digest 適用対象を違って解釈する。
   **代案：** 前者は「trigger-gating についての追補」と限定し、後者は関数群軸の LLM 由来候補も含むよう局所修正する。第3列や planner 例外の撤回は不要。

## 削れる項目と足りない項目

依頼と C 出口の対応は概ね揃っている。

| 必須項目 | 割付 | 判定 |
|---|---|---|
| 骨格・API・軸定数、出口6の identity 群 | A | 揃っている |
| 型付き構文検査・単独 TU・契約負例 | B | 契約の未決事項を閉じる必要あり |
| 検査器自己試験・UBSan 一回、出口9 | B | C 所有方策との依存を明記 |
| 三 hook・上限・再読込・prefix unlock・要因、出口8 | C | harness と専用方策の割付不足 |
| 三負例×二方策、出口7 | C | 最大待機方策の実体を固定 |
| 八機構変異 | C | 上限削除を非検出対照とする扱いは正しい |
| 手書き方策の生死確認 | C | 継続・停止条件が不足 |

削減・再利用の推奨は次のとおり。

- **patch 適用・復元、trace/verifier、評価本体は再実装しない。** `patchharness.applied` は適用から復元まで排他する（`:247–263`）。coverage driver の既存パターンと `pipeline.evaluate` を薄く組み合わせればよい。
- **TU compile の前例は駆動方法を再利用する。** sort oracle の compiler command は CC/masstree を前提とするため、そのまま転用できない（`C/sort_swo_oracle.py:2538–2546`）。専用の小さい TU builder は必要だが、共通 compiler framework は不要。
- **UBSan 専用 production module は必須ではない。** C 段一回の test/harness に寄せ、compile module の小さい内部 helper を使えば module を一つ減らせる。結果分類のための汎用台帳は作らない。
- **三個の新 macro＋既存負例 macro 再利用案は支持する。** inventory test は macro ごとの登録 patch が使用 patch 集合に含まれることを検査しており、一 macro 一 patch を要求していない（`Q/test_ccbench_spawn_sites.py:2888–2901`）。八 patch 共通 macro は静的には成立しうる。各ケースの source/patch digest と実分岐の証拠は必要。
- **登録追加を一律に scope 外とはしない。** 既存閉集合に新しい実在の macro・build sink を加える局所更新は必要。ただし新しい reject 分類、汎用 admission 層、台帳、GeneratorId の追加は必要性未確認のまま増やさない。
- **E 段への直接越境は確認しなかった。** `plan:391` の `test_p3_s4_loop.py` 更新は patch inventory の追随であり、探索 driver 配線ではない。grammar のローカル `rule_id` も新しい pipeline reject 理由とは区別できる。
- **同一 submodule の実測は直列にする。** 所有する編集 path が別でも、適用先は共通である。B/C の並行執筆と、patch 適用・評価の並行実行は別問題。

## 計算の見積りの検算

算術そのものは正しい。

| plan の項目 | 検算 | 単価の評価 |
|---|---:|---|
| J1：六負例 | 6×132＝792 秒 | 132 秒は旧 coverage job 全体。ケース単価として未較正 |
| J2：八変異＋正例 | 9×136＝1,224 秒 | 136 秒は pytest 焦点走。機構試験への転用は裏付けなし |
| J3：四方策＋stock | 5×217〜510＝1,085〜2,550 秒 | B-5 由来のシナリオ値。新軸の上下限ではない |
| J4：受入一回 | 900 秒 | 0.25 h の元となる全 job Elapse が必要 |
| 小計 | 4,001〜5,466 秒＝1.111〜1.518 h | **総額ではない** |

B-5 の 217 秒は lock 待ち推定を差し引いた値で、待ちがほぼない七 session の直接実測は499〜510秒である（`output/insights/2026-09-20/t2797-b5-contrast/README.md:195–197`）。受入の最近の参照は三 shard の **test 実行区間**343/188/137秒で、合計668秒＝0.186 hだが、これは job Elapse 合計とは限らない（T-2844 README `:161`）。0.25 h を否定はできないが、確定単価にもできない。

追加計上が必要なのは以下である。

- Python の関連焦点走。
- 実 CC 焦点 harness の build と各ケース。J2 に含めるならケース対応を示す。
- 検査器の四変異と、dev-wave 変異 matrix の baseline・probe・final。
- clamp/prefix-unlock の timeout 待ち。各一回でも実行部分に約240秒必要で、build・verify 周辺費は別。既に単価へ含めた分との二重加算は避ける。
- 不正 flags。本文では四境界を挙げる一方、見積り追記は二 build（`plan:427,469`）。採用数を一致させる。
- 実施する受入再走、setup/cleanup、品質再測定。既存 `evaluate` の既定 `bench_max_rounds` は3（`C/pipeline.py:2594`）。
- ノード確保中の待機。投入前の queue 待ちと区別する。

**2 node 時間未満とは判定できない。** 小計上側から残る余地は1,734秒しかない。旧受入換算1.14 hへ置換すれば、小計だけで2.001〜2.408 hとなる。逆に旧 driver 全体の単価をケースごとに掛けているため、J1などには過大評価の可能性もある。

したがって「必ず超える」とも断定せず、**現計画では2 h超を含む未確定見積り**と判定する。今回の依頼は閾値によらず投入前確認を明示しているため、総額を埋めてから確認する必要がある。

## brief と plan の前提の判定

| 前提 | 判定 | 理由 |
|---|---|---|
| P1：A→B/C | **要修正** | 編集所有は分離可能。ただし方策はC→B、検査器はB→Cの依存があり、実行まで独立ではない。Cの段階分割を推奨 |
| P2：専用 module・API単一正本 | **要修正** | 軸定数・型付きparser・API単一正本は妥当。lexer全面新設とUBSan module独立は最小とは未証明 |
| P3：二file骨格patch・PIN不動 | **real** | 提案の挿入箇所はOptions.cmakeとtransaction.ccに収まる。実適用・OFF identityは未実測 |
| P4：三段積み重ね・必要な負例だけ更新 | **要修正** | 方針は妥当。lockskip位置の説明が誤り。行番号差ではなく変更後のhunk文脈で判断する |
| P5：既存condition gate登録 | **要修正** | 登録は既存inventory上必要。二辞書だけでなくsite数・sink/meta-testも追随。共有三macro案は成立可能 |
| P6：八機構変異、上限削除は非検出 | **real** | 設計§3.3と一致。ただし八ケース＝八jobではなく、専用方策・焦点走・対照の費用は別途整理 |
| P7：四方策＋同job stockで生死確認 | **要修正** | 評価再利用・性能の比較主張をしない方針は妥当。継続条件、既存authorizationの具体経路、driverの規模を固定する |
| P8：親の実測単価を使用 | **要修正** | 132/136秒の実績は確認できるが用途が異なる。受入0.25 hのElapse根拠と未包含jobを補う必要がある |

docs commit は、指定された第3列と planner 例外について**採用可能**。逐語の短縮・具体化は D2214 の意味を保っており、C 実施済みとも主張していない。所見8の周辺文言だけを局所修正すればよい。

## 総括

**推奨：adopt_with_conditions。** 実装の大枠は依頼・D2214・C出口6〜9に整合する。
must-fix は以下の四点。

1. 用途の異なる単価を分離し、焦点走・変異matrix・timeout・受入再走込みの総見積りを確定する。
2. 生死確認の継続・停止条件を明記し、一走の性能差を軸の生死や優劣の証拠にしない。
3. 実CC焦点harness・専用方策の所有pathと、B/C間の資材・実行依存を固定する。
4. 無名仮引数を含むproducer/consumer契約を実装前に一致させる。

共有registryの局所更新は必要だが、新しい一般gate・台帳・E段配線は不要。
計算は2 node時間未満と確認できず、確定見積りを示して投入前確認を取る。