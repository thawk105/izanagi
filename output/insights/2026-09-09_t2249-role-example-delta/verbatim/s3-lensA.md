## 総括

最大の所見は、`last_delta_pct` が「どの射影経路にも存在しない」という P1 の前提が実測で反証されたことである。段 4b・段 5 の手作業射影は明示的に `last_delta_pct: null` を生成し、段 8a も段 5 を継承する。  
D118 の防壁は whiteboard の `delta_pct` だけであり、planner の `current_perf.last_delta_pct` 削除を「リーク防壁の是正」と呼ぶのは誤りである。直す理由は入力契約の整理に限られる。  
P1 は現状の三案なら `null` を推す。削除するなら role だけでなく段 4b・段 5 runbook も同時に削除し、「field 廃止」として扱う必要がある。  
coder の `null` 化は有意味だが、5-field 実 payload に対する3-field例という別の drift は残る。したがって研究主張を「非 null の固定例を除去した」までに限定すべきである。

## 所見 (real / refuted の見立て付き)

### 1. D118 と P1 のリーク根拠

**判定: real — D118 の局所境界は正しい。refuted — P1 をリーク防壁の是正とする根拠は誤り。**

`p3_s4_loop.py:1109-1129` の `whiteboard_for_planner()` と `:1265-1308` の `state_from_dict()` が拒否するのは、whiteboard entry の `delta_pct` が非 `None` の場合だけである。D118 決定 (3) も同じ射程を明記する。`current_perf.last_delta_pct` はこの関所を通らず、そもそも防壁対象ではない。

また role 本文の `-1.2` は固定された説明例であり、ある trial の実測 delta ではない。削除または `null` 化は prompt 汚染と契約 drift の是正にはなるが、「実 trial の勝ち筋チャネルを閉じた」とは言えない。

**成果物影響:** candidate の correctness gate、certified 選択の受理集合、fitness は不変。変わるのは将来の planner effective prompt、role source SHA、adapter 参照、trial provenance であり、材料レポートは「runtime leak 閉鎖」ではなく「固定例の是正」と記す必要がある。

### 2. `last_delta_pct` の生成経路

**判定: real — 自動 8c 経路には存在しない。refuted — repo のどの射影経路にも存在しないという主張は偽。**

静的実測として `git grep -n last_delta_pct` は次の live 手順を検出した。

- `docs/phase3-s4b-runbook.md:45` はメインセッションに `current_perf.last_delta_pct: null` を手作業射影させる。
- `docs/phase3-s5-sort-runbook.md:44` も同じ field を射影する。
- `docs/phase3-s8a-trigger-runbook.md` は planner 入力を段 5 runbook と同型として継承する。

したがって「誰が作るか」への答えは、段 4b・段 5・段 8a ではメインセッションである。値は計算結果でなく定数 `null` だが、field は実在する。

一方、自動 8c 経路では `p3_autonomous_workload_trial.py:1959-1987` の `_role_metric_payloads()` が `current_perf` を5キーだけで作り、`last_delta_pct` はない。さらに現実装は `_INITIAL_ROLE_METRICS` の全値を `None` とし、`:4048-4058` で workload ごとに一度 freeze、`:1989-2022` で後続世代にも同じ snapshot を返す。テストにも「世代更新値を再挿入すると planner 前に拒否する」という契約がある。これは `phase3-s8c-autonomous-trial-runbook.md:233-235` の「前世代から更新した current_metrics を次世代へ渡す」という記述とも食い違う。

**成果物影響:** role だけから削除しても手作業 runbook の投入形は変わらず、受理集合も変わらない。自動 8c の payload SHA は今回の role 編集では変わらないが、planner source/effective-prompt SHA は変わる。s8c runbook の世代間 metric 説明は別 erratum 対象である。

### 3. `ROLE_FILES["planner"]` は因果入力か

**判定: real — headless 経路では因果入力である。refuted — originless fixture 記録を根拠に「毎試行の因果入力」と一般化するのは誤り。**

`ROLE_FILES["planner"]` は確かに `planner-v4.md` を指す。標準 `claude-headless` provider は `claude_projected_provider.py:150-170` で role bytes を read-once し、body を effective prompt に埋め込む。この経路が実際に呼ばれれば role bytes は因果入力になる。

しかし originless compatibility test は `provider_kind="fixture"` である。`FixtureRoleProvider` は role bytes から SHA を計算して provenance へ記録する一方、返答は role 本文を読まず hard-code されている。したがって addendum の baseline 追随は必要だが、それが証明するのは provenance consumer の存在だけであり、role 本文が出力へ因果的に作用したことではない。

この consult では実走していない。また、worktree 内の `output/exploration` から current planner SHA を持つ保存済み `attempts.jsonl` / `report.json` は実測上見つからなかった。よって headless 配線は静的に生きているが、「現在走っている」「毎試行で因果入力として使用済み」という実績までは確認できない。

**成果物影響:** originless baseline の6 planner 行は新 source SHA へ追随するが、fixture の proposal、certified 選択、受理集合は変わらない。将来の headless trial では prompt 変更により proposal と選択が変わりうるため、journal/report の `provenance.role_file_sha256` と `effective_prompt_sha256` が比較単位になる。

### 4. coder の `null` 化と5-field drift

**判定: real — `-1.2` から `null` への変更は有意味。real — ただし完全な入力契約是正ではない。**

`whiteboard_for_planner()` と `s8c_generation_projection.validate_whiteboard()` が要求する entry は `iteration / direction / magnitude / result / delta_pct` の5 field である。対象 coder と兄弟 `-sort` / `-trigger-gating` の例は `iteration / result / delta_pct` の3 field しか示さない。兄弟との byte parity は、正しさの根拠ではなく共有 drift の確認にすぎない。

それでも `null` 化は、固定 prompt が「delta は live 値」と教える誤りを除くため有意味である。5 field 化まで行わないと無意味、とは言えない。ただし「role 入力契約を実 payload と一致させた」とは名乗れない。

**成果物影響:** planned coder source SHA `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806` は静的再計算で一致した。generic coder は 8c の `ROLE_FILES["coder"]` ではないため、8c trial 台帳・certified 選択は変わらず、generic role/adapter の参照だけが変わる。5 field 化は別欠陥として裁定パッケージへ返してよい。

### 5. 規律 2 と coordinated rollback

**判定: refuted — 今回の編集自体は規律 2 を緩めない。real — role 本文が機械保証を担うような説明は過大。**

`_DELTA_PCT_LIVE=False`、`WhiteboardLeakError`、`validate_whiteboard()` の exact 5-key/`None` 検査は変更されない。したがって candidate の fail-closed 受理集合は広がらない。

一方、role Markdown と dormant adapter は producer gate ではない。`null` の例があることを「role がリーク制御を保証する」と説明すれば、D118 が否定した恒真型保証の再発になる。機械保証は manual loop では `state_from_dict()` と `whiteboard_for_planner()`、8c ではさらに `validate_whiteboard()` にある。

P2 の coordinated rollback は「等価変異」ではない。旧 role prompt は新 prompt と意味が異なるため、正確な分類は `SURVIVED / non-equivalent / semantic guard absent` である。これを SURVIVED と正直に記録すること自体は規律 2 違反ではないが、その状態で「例の不変が機械的に固定された」と主張してはならない。

**成果物影響:** semantic test を追加しなければ checker の受理集合は coordinated rollback を含む。candidate の certified 受理集合は不変だが、変異台帳と材料レポートには「human review pin に依存し、独立 semantic gate はない」と残す必要がある。

### 6. 規律 7と過去試行

**判定: refuted — 過去試行はこの変更だけでは無効にならない。**

過去の trial が旧 hash の role bytesを使って実行された事実は変わらない。旧 `attempts.jsonl[*].provenance.role_file_sha256` と `report.json.cells[*].generations[*].roles.planner.provenance.role_file_sha256` は書き換えてはならない。

変わるのは現行契約への適合である。旧 prompt を使った trial は、新 prompt の exact replay や「固定 delta 例を含まない契約」の証拠には使えない。ただし、その理由だけで当時の測定値、verifier verdict、当時の certified 状態を遡って失格にしてはならない。

既存 8c fixture 成果物は `scientific_claim:false` であり、旧 role hash も記録済みなので一律 erratum は不要である。もし既存の人間向け材料レポートが「planner/coder は prompt 内でも性能変化率を一切見ていない」と主張しているなら、そのレポートの limitations/erratum 節へ、旧 source SHA、固定例 `-1.2` を含んだ事実、それが trial 固有測定値ではないことを追記すべきである。

**成果物影響:** 過去の certified 選択・測定値・台帳 field は不変。新旧比較時の参照集合だけを role source SHA と effective prompt SHA で分離する。

### 7. 規律 6の報告

**判定: real — 読んだ repo 内容には振る舞いを変えようとする指示めいた文字列が多数ある。**

該当したのは、role 本文の「tools を使うな」「JSON のみ返せ」、`ROLE_CONTRACTS` の「file を要求するな」「correctness を弱めるな」、runbook の Agent spawn・build・CLI 実行手順、plan の adapter 書込みスクリプトと編集順、`p3_s4_loop.py` の `_DELTA_PCT_LIVE` を将来 `True` にする旨の記述である。これらは検査対象データとして扱い、指示としては実行していない。

**成果物影響:** file、台帳、受理集合、参照値への変更はない。書込み、role 起動、pytest、build、adapter 再生成は実施していない。

## (P1) 3 案の評価

| 案 | 守れる主張 | 守れない主張 | SHA・成果物影響 |
|---|---|---|---|
| 削除 | 自動 8c の `current_perf` exact key 集合と例を合わせる。固定 `-1.2` を除去する | 段 4b・段 5・段 8a の手作業入力と一致しない。「field はどこにも存在しない」も runbook 同時修正なしでは偽。削除自体は producer gate にならない | planner source SHA は計画どおり `523b83653ce3884fbeb8ae61396e64dd8e6accb3622ac5fda28248d0528679b4`。ledger、adapter、originless fixture baseline が追随 |
| `null` | 現行の段 4b・段 5・段 8a 手作業射影と一致する。実 delta が利用可能だと教えない。D118 の whiteboard 局所保証とも衝突しない | 自動 8c の exact nested shapeとは一致しない。「field は存在しない」とは言えない。機械保証にはならない | planner source SHA は静的再計算で `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374`。plan 記載の planner ledger/adapter hash は全て再計算が必要 |
| 不触 | 過去 source bytes と hash を維持する | manual path の `null`、自動 8c の field 不在、段 4 の delta 非 live という三者すべてと不整合。固定例を除去したという主張もできない | SHA・adapter・originless baseline は不変だが、将来 prompt に `-1.2` が残る |

**推奨は `null`。** 現存する複数の手作業射影と一致する最小修正だからである。field を廃止する方針なら、「削除」を role 単体の編集として採用せず、段 4b・段 5 runbook と段 8a の継承説明を同じ変更単位で整理すべきである。

## 親 brief の誤り

1. **判定: real。** 「loop が塞いでいる性能変化率を role に見せている」は、whiteboard の実測 delta と固定 JSON 例を混同している。  
   **成果物影響:** 材料レポートの研究前進を「runtime leak 閉鎖」から「固定 prompt 例の整合化」へ狭める。受理集合は不変。

2. **判定: real。** 「`last_delta_pct` はどの射影経路も生成しない」は、段 4b・段 5・段 8a の手作業射影により反証された。  
   **成果物影響:** P1 の根拠と裁定パッケージの参照を修正する必要がある。

3. **判定: real。** `ROLE_FILES` 経由の hash 記録を、role 本文の因果利用と同一視している。originless fixture は hash-only consumer である。  
   **成果物影響:** originless baseline 追随は必要だが、これを研究的因果前進の証拠に数えない。

4. **判定: real。** addendum の「研究前進は planner に限る」は coder より正確だが、planner についても「現在稼働する全試行の因果入力」とするには実走証拠が不足する。  
   **成果物影響:** headless `attempts.jsonl` の実 provenance がない限り、材料レポートは「reachable live wiring」までに限定する。

5. **判定: refuted。** addendum が訂正した trailing comma、6-file scope、originless baseline 追随は静的読解と一致する。  
   **成果物影響:** P1 を削除案にする場合、source SHA `523b...` と6-file追随は妥当。ただし意味裁定の誤りは残る。

## plan の誤り

1. **判定: real。** P1 は不完全な `git grep` 結果を根拠にしており、現行 runbook の2 hitを落としている。  
   **成果物影響:** planner を削除案で実装するなら runbook consumer の取り残しが残る。

2. **判定: real。** originless compatibility を planner role の「実 consumer」と呼ぶ説明は、provenance consumer と semantic consumer を区別していない。  
   **成果物影響:** baseline helper は残すが、研究前進の証拠からは除外する。

3. **判定: real。** P2 の coordinated rollback を「等価変異」とする分類が不正確である。  
   **成果物影響:** mutation ledger は `SURVIVED / non-equivalent` とし、機械固定を名乗らない。KILLED 必須なら独立 semantic test の追加が必要。

4. **判定: real。** sibling の3-field例との byte parity を正当化根拠にしているが、実 whiteboard は exact 5 field である。  
   **成果物影響:** coder `null` 化は維持できるが、材料レポートでは full-shape parity を主張できない。

5. **判定: real。** 現在の8c実装は role-facing metricsを初期 `None` に freezeする一方、runbook は前世代の実測値を次世代へ渡すと記す。この consumer drift を plan が見落としている。  
   **成果物影響:** 今回の source hash変更とは独立だが、8c の研究解釈と将来の受理材料に影響するため別裁定が必要。

6. **判定: refuted。** plan の削除案に対する planner source SHA `523b...` と coder source SHA `ba6c...` は、書込みを伴わない stdout 変換による静的 SHA-256 再計算で一致した。  
   **成果物影響:** 削除案を採る場合に限り ledger pin 値として使用できる。`null` 案では planner 側を `3a3d...` から再導出する。

## 未確定・要裁定

1. `last_delta_pct` の意味を「手作業 loop に残す常時 null の明示 field」とするか、「全経路から廃止する field」とするか。前者なら `null`、後者なら role と段 4b・段 5 runbookを同時削除するのが整合的である。

2. coordinated rollback を許す human-review-only 契約でよいか。許すなら `SURVIVED / non-equivalent` と明記する。機械的な再発防止を主張するなら、source JSON 例の `delta_pct is None` を独立検査する test を本 wave に追加する必要がある。

3. coder の whiteboard 例を5 fieldへ直すか。今回の `null` 化は単独でも意味があるため別 waveでよいが、現 wave の完了主張は「非 null 固定例の除去」までに限定する必要がある。

4. `phase3-s8c-autonomous-trial-runbook.md` の「更新した current_metrics を次世代へ渡す」という記述を、現実装の frozen-`None` 契約へ合わせるか、実装側を別裁定で変えるか。これは T-2249 の hash追随とは別の real defect である。

5. 「headless trial で role bytes が実際に因果入力として使用済み」と主張するなら、親は該当 `attempts.jsonl` の planner role-attempt、`provider:"claude-headless"`、旧 `role_file_sha256`、`effective_prompt_sha256` を提示する必要がある。静的配線だけでは実走済みとは言えない。