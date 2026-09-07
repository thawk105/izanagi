## 受理集合の変化

結論は、**public API の入力組 `(diagnostic_paths, preregistration_path)` として見れば受理集合は確実に変わり、追加側も削除側もある**、です。artifact JSON だけへ射影した受理集合は、プランどおり実装すれば v1 SHA のままで広がりません。

現行 v1 の経路は次のとおりです。

- 渡された事前登録 file の実 SHA を計算し、v1 literal と比較する。`backoff_counterfactual_analysis.py:570-573`
- その実 SHA を `_load_artifact(..., expected_hash=...)` へ渡す。`backoff_counterfactual_analysis.py:581-584`
- top-level の `counterfactual_preregistration` を照合する。`backoff_counterfactual_analysis.py:307-321`
- 全 18 row を `_validate_row` へ渡す。`backoff_counterfactual_analysis.py:326-336`
- **各 row でも実際に検査している。** `row.get("counterfactual_preregistration") != expected_hash` が拒否条件である。`backoff_counterfactual_analysis.py:257-258`

したがって「row ごとの検査がない」という抜けはありません。

v2 分割後に生じる集合差は以下です。

- 追加される入力: `(v1 SHA の artifact 群, v2 文書)`。現行 v1 なら文書検査 `:572` で拒否されるが、提案後は v2 文書検査と v1 artifact 検査を別々に通る。これは public API の受理集合の拡大である。
- 削除される入力: `(v1 artifact 群, v1 文書)`。現行は受理されるが、提案後は v2 文書 gate で拒否される。
- 過剰拒否: v2 発効後に exact axes で producer を動かすと、producer は現行文書の SHA を top-level に書き `t2187_adaptive_const_probe.py:2758-2784`、同じ値を各 row と journal に流す `:2797-2810,3447-3455,3494`。つまり正規の新規成果物は v2 SHA になるが、提案 analyzer は artifact を v1 固定で拒否する。

最後の点はプラン自身も「v2 artifact を受理してはいけない」としているため、12 件専用解析器なら意図的な狭さです。ただし draft §9 の一般的な「測定時点に発効していた版」を扱う説明 `prereg-v2-draft.md:55-59` とは一致しません。

## 恒真テスト

最も危険なのは `_synthetic_cluster` 型です。

- `_synthetic_cluster` は synthetic run を作った後、期待値を独立計算せず production の `_cluster_summary` をそのまま返す。`test_backoff_counterfactual_analysis.py:407-421`
- 後続テストも、その production summary の CI を production `_primary_decision` へ戻している。`:424-441`
- これは production 内部の自己整合性検査にはなるが、「v1 から v2 へ挙動が変わった」ことの独立 oracle にはならない。この型を新しい synthetic cluster test に再利用してはいけない。

`test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory` は名前より弱い設計です。

- 「v1 inconclusive」は production v1 を呼ばず、test-local の `any(window_commits == 0)` で判定する計画である。`s2-plan.md:67-70`
- したがって production v1 が違う挙動へ退行しても、この v1 側は赤にならない。
- 証明できるのは「fixture に test-local v1 述語を適用すると inconclusive」「現在の production v2 は confirmatory」の二点だけであり、production の before/after 回帰ではない。

実装由来の値を期待値へ戻している既存箇所もあります。

- 現行 `_write_artifacts` は文書の現在 SHA を読み、その値を fixture の top-level と row へ入れる。`test_backoff_counterfactual_analysis.py:141-180`。プランがこれを独立 v1 literal へ変える方針は必須である。
- analyzer fixture は seed、cell identity、workload flags、schema、cell order を production module から取得する。`:20,114-116,170-175`。これらの同時 drift は検出しない。
- legacy performance fixture は `probe.NOT_CERTIFIED` をそのまま期待 artifact に使う。`test_t2187_adaptive_const_probe.py:2008-2016`。constant と checker を同時変更すると後方互換テストが通るため、プランの test-local 旧文言 literal は必須である。
- producer の preregistration test は期待 path まで `probe.COUNTERFACTUAL_PREREGISTRATION` から取る。`:2079-2097`。producer の path 定数とテストを同時に変えた誤りは検出しない。

一方、予定された rebasing test が `seq/index/count` の逐語 tuple と手計算 estimate を使うなら、実装から値を取らないため有効です。`s2-plan.md:62-65`

## 変異の帰属

現在、予定された新規 node 6 件はいずれも未実装です。実在するのは `test_public_analysis_pairs_next_window_and_uses_equal_run_clusters` だけです。したがって mutation spec を test 追加より先に確定すると node 不在になります。

1. `analysis_events = events[1:]` を `events` へ戻す

   - (a) rebasing test は、最初に raw event0 を受けるため赤になる見込み。
   - (b) zero scan も同じ変数を使うため、seq0-zero test も赤になる。二つの意味が一変異に結合しており、後者だけでは位置除外への帰属が不鮮明。
   - (c) 予定された二 node は現在不在。
   - 修正: M1 の期待 node は、全 commit が正である rebasing test 一つに限定する。

2. `outcome_count` を raw event 数へ戻す

   - (a) 記録 membership が `count` の不一致を直接検出するなら赤。
   - (b) 他 gate より前に literal tuple がずれるので帰属は良好。
   - (c) rebasing node は現在不在。

3. raw zip を enumerate 後に `seq != 0` で filter

   - (a) 最初の membership index が 1 になるので赤。
   - (b) pair 自体は event1/event2 から始まるため、直接検出される差は index rebasing だけで帰属は良好。
   - (c) rebasing node は現在不在。

4. zero scan を raw events へ戻す

   - (a) raw event0 の zero で `window_commits_zero` になり、v2 confirmatory assertion が赤。
   - (b) zero scan は log 計算より前なので `backoff_counterfactual_analysis.py:389-401`、算術例外ではなく該当 gate に帰属する。
   - (c) seq0-zero node は現在不在。test-local v1 oracle 自体はこの変異を検出しない。

5. zero scan を selected current のみに狭める、または削除する

   - (a) 最後の following event に zero を置けば赤にはなる。
   - (b) ただしその zero は後の `math.log(following_rate/current_rate)` に入り `math domain error` となる。`:397-402`。期待 assertion ではなく算術例外で kill され、「残存全 event scan」の帰属が弱い。また「狭める」と「削除」は別変異である。
   - (c) seq>=1-zero node は現在不在。
   - 修正: 二変異へ分割する。直接 `_run_difference` を呼び、zero を最後の event に置き、その直前 pair を membership から外す。baseline は全 event scan で inconclusive、変異は安全な selected pair だけを計算して assertion で赤になる。

6. v2 文書比較を v1 定数へ取り違える

   - (a) v2 文書を使う既存 public positive tests は事前登録 gate で赤になる。
   - (b) 改名予定の file-bound test は、現在の設計 `test_backoff_counterfactual_analysis.py:462-470` のままなら、実 SHA の literal 照合と「1 byte 変更版の拒否」しか行わない。変異でも変更版は拒否されるため、この node は kill しない。
   - (c) 改名 node は現在不在。public positive node は実在。
   - 修正: file-bound test 内で未変更 v2 文書を使った positive public call も要求するか、期待 node を public positive node だけにする。

7. artifact pin を v2、または `{v1,v2}` へ変える

   - (a) v2-only なら通常の v1 fixture が top-level gate で赤。両版受理は実装位置次第で生存する。
   - (b) top-level `:318` と row-level `:257-258` の二重 gate がある。top-level だけ `{v1,v2}` に広げても all-v2 artifact は row gate で拒否され、予定した negative test は緑のままになる。帰属は壊れている。
   - (c) artifact-bound node は現在不在。通常 public nodes は実在。
   - 修正: top-level widening は「top=v2、全 row=v1」、row widening は「top=v1、対象 row=v2」で別々に変異・検査する。v2-only 取り違えも widening と分ける。

8. analysis version を `/v1` のままにする

   - (a) public test に独立 literal `/v2` assertion を追加すれば赤。
   - (b) 単一出力 field なので帰属は良好。
   - (c) public node は実在するが、現在は `analysis_version` assertion がない。`analysis_version` の production 出力は `backoff_counterfactual_analysis.py:673-677`。

9. mode-specific `not_certified` を片側で壊す

   - (a) 診断・性能を独立 literal で比較すれば両方赤にできる。
   - (b) 「診断を旧文言へ戻す」と「性能へ診断文言を書く」は別変異であり、一件に束ねると帰属が曖昧。module 定数を期待値に使うと性能側は恒真化する。
   - (c)予定 node は現在不在。
   - 修正: M9a/M9b に分割し、両期待値を test-local literal にする。

## 副題 not_certified

この producer の field を実際に判定へ使う production consumer は二つです。

- `_performance_artifact_identity`: performance kind と旧文言を exact 比較する。`t2187_adaptive_const_probe.py:1765-1775`
- 旧 T-2187 performance plot loader: performance kind と旧文言を exact 比較する。`plot_t2187_adaptive_consts.py:336-345`。provenance にも同じ旧文言を書く。`:988-1006`

関連テストは以下です。

- producer test の performance fixtures 5 箇所は現状ほぼすべて `probe.NOT_CERTIFIED` 由来。`test_t2187_adaptive_const_probe.py:95-105,898-910,1217-1227,2008-2016,2306-2315`
- plot test は独立 literal を持つ。`test_plot_t2187_adaptive_consts.py:17-22,103-106,280-281`

その他の `not_certified` hit は別契約です。

- T-2216 model と plot は独自 schema・異なる文字列を使う。`t2216_backoff_walk_model.py:35-42,1428-1434`、`plot_t2216_backoff_walk.py:35-38,292-305`
- dynamic-backoff plot の `NOT_CERTIFIED` は provenance 用の日本語 notice で、入力 artifact の同 field は読まない。`plot_dynamic_backoff.py:58-64,1497-1499`
- `test_empty_trace_indeterminate_not_certified` は test 関数名であり、producer field の consumer ではない。`test_verifier.py:336-342`

凍結済み成果物への影響は次のとおりです。

- 12 診断成果物: analyzer の top-level exact fields `backoff_counterfactual_analysis.py:307-319` と row validation `:230-285` に `not_certified` はない。文言を変えなくても、変更後の検査によって拒否される経路はない。
- 凍結性能成果物: 旧文言を 1 byte でも変えると `_performance_artifact_identity` と plot loader の双方で拒否される。性能文言を不変にする必要がある。
- producer code の SHA 自体は変わるが、performance identity consumer は recorded driver SHA の形式だけを検査し、現在の driver bytes との一致は要求していない。`t2187_adaptive_const_probe.py:1807-1823`

ただし `_artifact_contract_metadata` に `not_certified` を追加すると、現在 exact dict を要求する tests がそのままでは赤になります。

- 非 counterfactual の performance/trace metadata 期待値: `test_t2187_adaptive_const_probe.py:1968-1985`
- counterfactual exact axes の期待値: `:2079-2097`

本 wave の scope には**入れない**判断を推奨します。理由は、12 件の解析結果を一切変えず、凍結済み診断 bytes の欠陥も直せず、効果が将来の producer 出力だけだからです。本題とは異なる test 更新と mutation 帰属が必要で、プランの「独立 commit」だけでは scope 混入のリスクを消せません。

## pin 閉包の抜け

現物で数えた結果は以下です。

- `izanagi-backoff-counterfactual-analysis/v1` は repo 内 3 箇所。
  - live 定義 1 件: `backoff_counterfactual_analysis.py:15`
  - 歴史成果物 1 件: `output/insights/2026-09-07_t2265-backoff-itt/analysis-result.json:2`
  - 歴史 verbatim 1 件: `output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:232`
- live consumer が `analysis_version` を比較する箇所は 0 件。production は値を返すだけである。`backoff_counterfactual_analysis.py:674`
- `acceptance_duration_ledger.json` に `orchestrator/tests/test_backoff_counterfactual_analysis.py::` で始まる node ID は **0 件**。プランの断定は正しい。
- 同台帳の `test_empty_trace_indeterminate_not_certified` は別 test であり、本件の hit ではない。`acceptance_duration_ledger.json:19373`

path、旧 SHA、test filename、analyzer filenameでも追跡しました。

- live pin は analyzer の v1 SHA と test golden の二箇所。`backoff_counterfactual_analysis.py:17-19`、`test_backoff_counterfactual_analysis.py:21-23`
- test filename の他 hit は `docs/failures.md:1957-1967` の事故記録と、前 wave の歴史的 mutation spec/report 群だけ。live role key、node key、golden registry は見つからない。
- analyzer filenameの他 hit も同じく歴史記録と前 wave output であり、live dispatch key は見つからない。
- 行番号を焼き込んだ本件の live literal は見つからない。前 wave の verbatim/mutation output 内の行番号は歴史記録であり更新対象ではない。

whole-file hash について、brief の説明は一部誤っています。`tools/check_docs.py` は cleanup-branches skill だけでなく、`.claude/commands/cleanup-branches.md` も別 SHA で固定しています。

- skill hash: `tools/check_docs.py:743-745,6535-6544`
- command hash: `tools/check_docs.py:751-753,6546-6554`

本件 preregistration 文書の whole-file hash pin はありませんが、「skill だけを対象」は現物と一致しません。

## test 追加の副作用

analyzer test file には、すでに自走 harness があります。

- `_run()` は `pytest.main([__file__])` を呼ぶ。`test_backoff_counterfactual_analysis.py:529-530`
- `__main__` はその返値で終了する。`:533-534`

producer test にもあります。`test_t2187_adaptive_const_probe.py:2566-2571`

plain-runner メタテストの要求は次のとおりです。

- `__main__` より後ろに `_run(`、`pytest.main` などの signal が必要。`test_plain_runner_coverage.py:25-41`
- harness がなく、README allowlist にもない `test_*.py` を拒否する。`:60-74`
- harness を持つ file が allowlist に残ることも拒否する。`:77-86`

今回は既存 file への追記なので、新規 file 起因の meta-test 赤はありません。

ledger 欠落も admission failure ではありません。lookup は未登録 node に `None` を返す。`conftest.py:1534-1554`。unknown unit は既知 cost 由来の値で並べ替えられる。`:1594-1626`。0 件という台帳確認と整合します。

残る受入全走の静的な赤経路は副題側です。`_artifact_contract_metadata` の返却 key を増やしながら `test_t2187_adaptive_const_probe.py:1968-1985` の exact dict を更新しなければ、既存 test が失敗します。プランは `:2079` 付近しか名指ししておらず、この既存二 assertion を落としています。

pytest は実行していないため、どの検査も「緑」とは判定していません。

## 親 brief の誤り

- **受理集合不変の表現が過度です。** brief は分割を「受理集合を広げない」不変条件下に置く `s1-brief.md:53-58,72-75` が、public tuple では `(v1 artifacts,v2 doc)` が新規受理される。artifact projection だけに限定して書く必要がある。
- **pin 説明が誤っています。** 「whole-file SHA は cleanup-branches skill だけ」`s1-brief.md:94-95` に対し、実装は command file も別 SHA で検査する。`tools/check_docs.py:751-753,6546-6554`
- **prereg v2 草稿は内部矛盾しています。** 草稿は「§7 の位置除外一つだけ」「推定対象は一字も変えない」とする `prereg-v2-draft.md:5-7` 一方、現行 §4 は明示的に `i=0,...,m-2` を推定対象とする。`backoff-counterfactual-preregistration.md:112-121`。さらに plan 自身は §4 と §6 の改訂を要求する。`s2-plan.md:118-120`。草稿 A/B/C だけを凍結すると、文書内で §4 と §7 が食い違う。
- **DW-O10 は write path の説明としては正しいが閉包が不足しています。** 将来 producer が v2 SHA を記録する `s1-brief.md:99-103` のに、提案 analyzer は v1 artifact だけを受理する。将来値を「正しい」とするなら、同じ解析器では過剰拒否されることも併記が必要です。
- P3/P4 の実装方向は壊れていません。生 trace の `seq` は位置と一致するよう検査される `backoff_counterfactual_analysis.py:130-164` ため `events[1:]` は exact な位置除外になり、zero scan をその残存列へ限定すれば raw event0 だけが外れます。
- P5 の性能文言不変も必要です。性能 identity が exact 旧文言を要求するためです。`t2187_adaptive_const_probe.py:1765-1775`
- P6 は確認不能です。一次資料が示すのは残り二件の `seq=10/11` までで、どの workload/thread 層かは示していません。`origin-verbatim.md:13-18`。禁止された12成果物を開いていないため、v2 主判定が equivalent か inconclusive かは未解決です。

## 総括

- **must-fix: v2 草稿へ §4 の推定量と §6 の time-block rebasing を明記する。** 直さないと文書上の `Y[r,0]` と実装上の最初の `(event1,event2)` が食い違い、推定値と層 membership の参照が変わる。
- **must-fix: 「受理集合不変」を artifact projection に限定する。** 直さないと、新規受理される `(v1 artifacts,v2 doc)` と拒否へ移る v1文書・将来v2 artifact が隠れる。
- **must-fix: M6 の file-bound test に未変更 v2 文書の positive call を置く。** 直さないと v1/v2 定数取り違えでも指定 node が赤にならず、文書 SHA の参照先を誤って帰属する。
- **must-fix: M7 を top-level gate と row gate に分割する。** 直さないと片側の `{v1,v2}` widening が冗長 gate に遮られ、artifact 受理集合を広げる変異が生存する。
- **must-fix: M5 と M9 の「または」を別変異にする。** 直さないと算術例外または反対側の mode assertionが kill 原因になり、zero scan 範囲や文言選択の変更箇所を一意に参照できない。
- **real: row-level preregistration SHA gate は存在する。** この検査を維持すれば top-level だけを書き換えた artifact は受理されない。
- **real: analyzer test の自走 harness と ledger には追加作業不要。** 余計に触ると test file の実行参照や acceptance 順序だけを不要に変える。
- **scope判断: `not_certified` 副題は本 wave から外す。** 入れると将来診断文言と producer test 期待値が変わる一方、12凍結成果物の値は直らず、本題の解析受理集合には影響しない。
- **未解決: seq10/11 の二件が主層にあるか。** 成果物を開いていないため、最終 `decision` が `equivalent` か `inconclusive` かは静的読解では決められない。