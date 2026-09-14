必読6ファイルはすべて読めた。静的検査のみで、編集・実走はしていない。

以下、`T` は `orchestrator/tests/test_p3_autonomous_workload_trial.py`、`A` は `orchestrator/campaign/p3_autonomous_workload_trial.py`、`plan` は指定の `stage2-plan.md` を指す。行番号は現 checkout 基準。

## 検査 1 — 追加検査の発火可能性

**real：partial を返す実経路は存在する。status assert 自体は恒真ではない。**

`A:3410` の `providers["critic"]` が KeyError を送出すると、`A:3701` が捕捉し、`:3702` で fatal_error、`:3716` で supervisor-error を設定する。`:3724` で後続 workload を打ち切り、`:3762–3780` が partial を算出、`:3832` が fatal_error を report に格納する。pending entry は `:3429–3433` の finally で除去されるため、その残存を理由に report 構築前で必ず例外になる経路でもない。

**具体シナリオ：** plan の critic 欠落構成では、この partial が helper の complete 条件を破る。成果物への影響として、判定本体に検出力がないという批判は成立しない。ただし、新規負例の実際の返却・発火は親の実走で確認が必要。

## 検査 2 — 負例の機構強度

**real：判定本体の削除は守るが、本 test への接続削除は守らない。**

本 test の callee は `plan:26`、負例の callee は `plan:47` の、同じ module-level `_assert_role_sink_report_complete`。別実装や両層 stub ではない。helper 内の assert を消せば、`plan:43–47` は `DID NOT RAISE` になる。

しかし、**`plan:26` の呼出しだけを削除すると、負例は同じ helper を直接呼び続けて合格する。** 本 test は現状へ戻り、親の測定した正常32走も合格する。`plan:86` 自身がこの穴を認めている。

**成果物への影響：** 「検査を消したら赤」を本 test の検査接続まで含む保証として記録できない。`brief:72–73` の説明は、同一 callee で守れる範囲を広く書きすぎている。親の変異検証には、assert 本体削除と呼出し削除を別々に扱う必要がある。

**real：fatal 部分集合だけを拒否する弱化は生き残る。**

`plan:39` は fatal_error のある partial だけを使う。helper を「fatal_error がある場合だけ同じメッセージで拒否する」に弱めても、負例は合格する。一方、`A:3422–3425` の role-invalid は fatal_error を立てず、`:3768` によって partial になる。

**成果物への影響：** この負例が保証するのは少なくとも fatal partial の拒否であり、「原因によらず complete 以外を拒否する」判定全体の弱化耐性ではない。

## 検査 3 — 負例の report の出所

**real：report は実 producer 由来だが、本 test の実行構成とは異なる。**

`plan:38–50` は実 `A.run_trial()` の返値を加工せず使う。`_fake_drive` と `_fake_preview` は注入されるが、status 算出と report 構築は `A:3762`、`:3798` を通る。合成 dict で producer を迂回する欠陥はない。参照する status・fatal_error・cells の schema が変われば、成立条件の検査が赤になる。

**具体シナリオ：** producer の role-sink 用 drive 経路だけに不具合が入り、`_fake_drive` 経路が正常な場合、この負例では検出できない。

**成果物への影響：** 「実 producer の report を検査」は言えるが、「本 test の障害経路を再現」は言えない。

## 検査 4 — 名指された欠陥形との一致

**real：fatal_error 付き partial という形は覆うが、旧 test の誤受理再現にはならない。**

plan は親の P3 を変更し、`plan:37–39` で critic 欠落による fatal partial を選んでいる。したがって「role-invalid しか使わず fatal_error を覆わない」という欠陥はない。

ただし、critic 欠落を本 test に持ち込むと、**旧コードでも `T:1917` の `providers[role]` 参照で KeyError になる。** critic を存在させたまま呼出し前に失敗させても、payload 件数検査が落ちる。

**成果物への影響：** この負例だけでは、`brief:19–22` の「旧 test が受理していた走を新検査が拒否する」という受理集合の厳密な縮小を示していない。既存 payload・variant・WAL 検査を満たした後に fatal partial になる具体例の旧版／新版比較は未検証。

## 検査 5 — 恒真 assert の有無

**real：plan に恒真な追加 assert はない。ただし P1 の理由には適用範囲がある。**

`A:3765` は complete の必要条件を `fatal_error is None` とし、`:3832` は非 None の場合だけキーを追加する。したがって、現行経路で complete 検査を通った後の fatal_error 不在検査には独立した検出力がない。

**要検証・将来変更の具体シナリオ：** status 算出が fatal_error を見なくなり、supervisor-error 等の除外も緩められれば、complete と fatal_error が共存し、status 単独検査は通る。ただし `:3765` だけを削除しても、plan の負例は cell 数不一致と supervisor-error により partial のままである。

**成果物への影響：** P1 は現行 producer に対する判断であり、将来の不整合まで排除する保証ではない。この仮定だけを理由に追加 gate を要求する根拠もない。

## 検査 6 — 親 brief と親実測への攻撃

**real：「32 wire の一部しか回っていない report」という説明は構造と一致しない。**

`brief:7–8` に対し、本 test は `T:1901` 付近で wire ごとに独立した一 workload の `run_trial` を呼ぶ。32 wire の収集は `T:1962` の executor と後続件数検査が守る。

**具体シナリオ：** 31 wire しか収集しなければ、status 検査がなくても既存の件数検査で赤になる。

**成果物への影響：** 修正対象は各 trial の完了性であり、32 wire の収集漏れと混同すると、新規検査の効果を過大に説明する。

**real：pin 閉包の完了宣言は検索範囲を超える。**

`measurement.md:34` は test 名の文字列検索だが、`:46` と `brief:55–58` は pin が存在しないと断定している。`:51` は別 key の網羅検索をしていないと認めている。

**具体シナリオ：** test 名を含まず、ファイル全体の hash を固定する manifest があれば、この検索には出ない。

**成果物への影響：** pin の実在を確認したわけではないが、「pin 閉包確認済み」の証拠は不足する。

**要検証：正常走の実測から誤受理の存在は導けない。**

`measurement.md:24–30` が示すのは、測定した32 report が complete だったこと。`:84–85` は負例経路も未実走と明記する。

**具体シナリオ：** 試した fatal 障害がすべて既存 assert でも落ちるなら、baseline と新しい helper 負例が合格しても、旧 test の誤受理は未再現のままになる。

**成果物への影響：** baseline の到達可能性と、受理集合が真に狭まった証拠は分けて記録すべき。

## 総括

最大の穴は、**helper への接続を削除しても負例が合格すること**。次に、選んだ fatal partial は旧 test でも失敗する形なので、**親が主張する誤受理の再現証拠になっていないこと**。

実 producer の partial と fatal_error を使う点は静的に確認できた。しかし、現 plan の成功条件だけで「元の穴を再現し、再発防止まで機械で確認した」と閉じるのは過大評価になる。実走結果は主張しない。