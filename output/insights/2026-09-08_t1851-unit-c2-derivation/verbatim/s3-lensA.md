## 受理集合が広がる箇所

- blocker: 6-key から 7-key への置換は、拒否集合の単純な縮小ではない。例えば `expected_use_perf=False`、`reps=2`、`ScalePoint.throughputs=[100.0, 101.0]` で各 observation が次なら、現行 campaign は余分な key により両 rep を incomplete とするが、plan 後は両方 complete になる。

```python
{
    "rep_index": i,
    "returncode": 0,
    "counter_status": "not_required",
    "missing_perf_events": [],
    "perf_raw": {
        "LLC-load-misses": None,
        "LLC-loads": None,
        "instructions": None,
        "cycles": None,
    },
    "throughput": [100.0, 101.0][i],
    "execution_failure": False,
}
```

  現行 `s8b_floor_campaign.py:1947-1950` は exact 6-key 不一致として `throughputs=[] / rep_integrity_failures=2`。plan 後は `throughputs=[100.0,101.0] / rep_integrity_failures=0 / exec_failures=0` となり、有効 session へ到達できる。`s8b_floor_stats.py:487` も現行は exact-key error、plan 後は受理する。したがって「受理集合は広がらない」は反例で否定される。

- blocker: plan は `execution_failure=True` と成功情報の矛盾を schema error にしない。「valid evidence だが qualified rep ではない」としているため、`returncode=0`、有限 throughput、完備 counter と `execution_failure=True` の同居も受理される。現行では余分な 7 番目の key として拒否される。少なくとも `execution_failure is True => throughput is None` のような producer が実際に保証する関係を検査しない限り、caller が flag だけで `exec_failures` と除外理由を選べる。

- blocker: この変更を `FORMULA_ID="s8b-floor-stats/v2"`、result v4/v5、journal v3 のまま行う計画である。`s8b_floor_stats.py:16-19` は session validity も formula に含み、変更時は ID を改版すると明記する。同じ schema 名の下で旧 6-key を拒否し、新 7-key を受理するため、版境界が無い。

## exec_failures と rep_integrity_failures の分離の破れ

terminal evidence の既存不変式 `s8b_terminal_evidence.py:856` が分離を壊す。

具体例を `reps_expected=2` とする。

- rep 0: rc=0、throughput=100、`execution_failure=False`
- rep 1: rc=7、throughput=101、`execution_failure=False`
- counter は両方 `not_required`

plan の campaign/stats 導出は正しく `qualified=(100,)`、`exec_failures=0`、`rep_integrity_failures=1` になる。しかし terminal の式は `1 + 0 + 0 != 2` として、この正当な分離状態を拒否する。

さらに rep 1 の flag だけを `True` にすると、plan の導出は `exec_failures=1`、`rep_integrity_failures=1` となり、同式は `1 + 0 + 1 == 2` で通る。非 zero rc は実行例外ではないのに、flag が「qualified 列の穴を埋める数」として使われる。

従って plan のままでは、

- 非 zero rc
- counter 欠落
- その他の非 execution integrity failure

を sealed terminal へ運べない一方、偽の `execution_failure=True` なら運べる。契約 3 節の分離は end-to-end で成立しない。sink 長と各 rep の分類を直接検査するか、非 execution integrity failure の本数を別に扱う必要がある。

また `_derive_rep_integrity()` を 3 値から4値へ変える plan は、consumer の `s8b_terminal_evidence.py:1030` を列挙していない。ここは現在 `(_errors, integrity_failures, qualified)` の3変数で受ける。plan が挙げた snapshot 側 `:641`、stats verifier、resume だけでは返値変更の閉包が閉じない。

## 未信頼文字列の侵入経路

新 key に例外 message を載せない判断は正しい。静的に追った経路は次のとおり。

- runner が `str(exc)[:200]` を notes に入れる: `runner.py:966-980`、`:1171-1186`
- campaign が notes を session record へコピーする: `s8b_floor_campaign.py:6296`、`:6387`
- launcher の `failure.message` も外部例外文字列である: `s8b_floor_attempt_launcher.py:452`
- terminal evidence は notes と failure message を平文の判定入力にせず、`notes_sha256` と `failure_message_sha256` にだけ束縛する: `s8b_terminal_evidence.py:1270-1276`
- raw session 全体の digest にも入るが、これは文字列内容を意味として信頼する処理ではなく opaque な bytes 束縛である

`_count_exec_failures()` と唯一の呼び手を削除した後は、確認した計算経路に notes/message を解釈する consumer は残らない。ここは blocker なし。ただし診断 error に外部値の `repr` を入れる場合も、拒否文面だけに留め、理由分類や count へ再入力してはならない。

## padding 経路の倒れ方

padding が直ちに complete へ倒れる反例はない。`execution_failure=False` を追加しても `returncode=None` なので、`s8b_floor_campaign.py:1953-1954` が残る限り全 rep は integrity failure になる。perf 有りなら counter も incomplete である。

ただし blocker は残る。carrier が無い状態では「runner が例外を捕捉しなかった」とは観測できないため、`False` は成功既定ではなくても未観測事実の捏造である。例えば carrier 欠落、throughputs 空、notes が `"2/2 reps failed to execute"` の入力は、現行では `exec_failures=2 / launch_failure`、plan 後は padding の False により `exec_failures=0 / nonfinite_or_partial_output` へ変わる。valid にはならないが、proof chain に載せる terminal 事実と理由が変わる。

padding は exact 7-key の正常 carrier に昇格させず、schema 不備として拒否するか、明示的な unavailable projection として別扱いにすべきである。

## runner 2 入口の非対称

plan は親から後渡しされた二事実を独立に見つけている。

- `capture_measure_point()` の observation は `runner.py:990`
- `measure_point()` の observation は `runner.py:1203`
- campaign の live 経路は後者: `s8b_floor_campaign.py:7865,7871`
- launcher は前者: `s8b_floor_attempt_launcher.py:210-213,730`

従って「片方だけ直す」欠陥は plan 自体にはない。M1/M2 も入口別に置かれている。

一方、campaign の陽性対照は direct `measure_point()` しか通さず、capture 側は runner 単体試験だけである。両関数は別実装なので、同じ結果 schema を出すことを入口別の正例・負例で固定する必要がある。特に実 campaign の値が launcher の `private_rep_sink` へ入る経路は依然 0 件であり、direct 経路の receipt は launcher 側の値域供給を証明しない。

v1 の registry event key 集合については、plan の production 編集面に `s8b_attempt_profile.py` と `attempt_registry_core.py` が無く、`_S8B_EVENT_KEYS` と v1 terminal gate は静的には不変である。runner の nested observation が7-keyになることは、v1 event 自体の key 集合変更ではない。

## 恒真になる検査

plan の記述どおり「拒否した」「failure になった」だけを assert するなら、次は変更前でも通る。

- `test_exec_failures_and_rep_integrity_failures_remain_distinct`: 現行でも notes が空の非 zero rc は `exec_failures=0 / rep_integrity_failures=1` になる。structured flag を読んだ証拠ではない。
- `test_execution_failure_is_also_an_integrity_failure`: 現行 exact 6-key gate は `execution_failure` を余分な key として拒否するため、既に integrity failure になる。新しい `execution_failure is False` 条件の発火証拠にならない。
- `test_verify_rejects_non_bool_execution_failure`: 現行 stats は値型を見る前に、7番目の key 自体を exact-key error にする。特定の型 error と、valid bool の正例まで要求しなければ恒真である。
- `test_verify_rejects_exec_failure_count_mismatch_independently_of_integrity`: 現行では observation の余分な key が先に拒否する。exact-key gateを通過したことと count mismatch 固有の診断を固定しなければ新検査の証拠にならない。
- M10 の sealed-terminal 負例も、既存の repetition sum や launch-failure consistency が先に拒否し得る。新しい再導出 check が最初の拒否点であることを plan は要求していない。

M6/M8/M9 は、変更前に通る負例だけでなく「新しい前段を通り、対象述語だけを外すと受理される」入力を対で置く必要がある。

## 親 brief の誤り

- `s8b_floor_stats.py:63` は `PERF_EVENTS` であり、`_REP_OBSERVATION_KEYS` は `:64-67`。exact 比較は `:487` で、`:486` は `continue`。概念は正しいが file:line が1行ずれている。
- launcher が `capture_measure_point` を使う根拠として挙げた `s8b_floor_attempt_launcher.py:158-160` は `OpenedFloorAttempt` の field、`:435` は `_failure_evidence()` の引数である。実際の dependency は `:210-213`、呼出しは `:730`。
- `backoff_counterfactual_analysis.py:256-257/:322` は runner の rep observation consumer ではない。独立した diagnostic trace row の `rep_index` を検査しており、runner も `rep_observations` も参照しない。
- `floor_pair_driver.py:1794-1828` という範囲は途中で切れている。個別 key 検査は `:1832-1851` まで続く。exact key 等値ではないという結論自体は正しい。
- brief 5節の「`FROZEN_MANIFEST` は output 23 path の figure 束縛のみ」は誤り。`test_frozen_artifacts.py:48-49` は `output/s8b-freeze/floor_protocol.json` の digest を直接 pin している。formula/result semantics を改版するならこの凍結面へ到達する。
- 7対象 file の現 SHA-256を tracked tree 全体で検索した結果、whole-file hash hit 0 は確認できた。
- 凍結 fixture の observation 変更が oracle/freeze の既存 64hex literal へ伝播しない、という狭い結論は正しい。`_synthetic_floor_result()` を使う holdout freeze 側は manifest/result/journal digest をその場で再計算し、oracle driver/manifest/report は `fill()`、`budget()`、`per_pair_floor()` だけを使う。対象 production file の path/hash literal も4 consumerに無い。
- ただし pin 閉包全体は閉じていない。validity 契約を変えるのに `FORMULA_ID`、result schema、journal schemaを据え置く問題と、改版時に凍結 `floor_protocol.json` へ届く閉包を落としている。
- plan の「親は complete を `:1039-1045` とした」という異議は、現在の brief には当たらない。現在の brief は正しく `:1947-1950` を指しており、plan が古い版を攻撃している。

provisional 裁定では次の判定になる。

- P1 は誤り。direct `measure_point()` が値を作ることは、別実装の `capture_measure_point()` を通じて launcher がその値を受け取ったことを含意しない。production caller 0 のままなので、契約9節の launcher gate への「実値域供給」は証明されない。
- P2 は runner の実 observation については正しいが、carrier 欠落 padding へ一律適用して False を作る部分は誤り。
- P3 は正しい。notes regex は helper と唯一の呼び手ごと除去すべきである。
- P4 は正しい。両入口を直す必要があり、plan も両方を列挙している。

## 過去の型の再発

- F280: 「拒否しか増えない」という単調性主張を反例探索なしで置く型。exact 7-key の具体例が今回の反例。
- F366 / F856: producer schema を広げた際の nested exact consumer 取り残し。plan は stats gateを発見したが、`_derive_rep_integrity()` の返値 consumer `s8b_terminal_evidence.py:1030` を落とした。
- F571: key の穴を塞いだだけで到達性を証明したと読む型。7-key gateが揃っても、terminal の本数式が非 execution integrity failure を拒否する。
- F608 / F806: 同じ規則の複数実装を一つの変異で代表する型。campaign、stats、terminal に対して矛盾 observation を同じ具体値で別々に通す必要がある。
- F879: 読み手に見えない情報を代理値で埋める型。carrier 欠落を `execution_failure=False` とするのが該当する。
- F900: 負例が対象述語へ届く前に別 gate で拒否される型。M6/M8/M9 が現状この形。
- F759: 文書と実装の不一致を受理集合拡大で解消する型。同じ formula/schema 名のまま7-keyを受理する案が再発する。
- F732: 同じ値域を複数 module が独立実装して食い違う型。二つの runner入口と campaign/stats/terminal の flag 解釈に共通する。

## blocker と nit の仕分け

blocker:

- exact 7-key 化による具体的な受理集合拡大
- formula/result/journal を改版しない semantic drift
- terminal repetition sum による二量の再結合
- `execution_failure=True` と成功 throughput の矛盾を受理すること
- carrier 欠落を `execution_failure=False` で埋めること
- `_derive_rep_integrity()` 返値変更の consumer `s8b_terminal_evidence.py:1030` 取り残し
- P1 の「launcher へ実値域を供給済み」という未成立な完了主張
- M6/M8/M9 の前段拒否による恒真化

nit:

- stats の2箇所の1行ずれ
- launcher dependency の誤った引用行
- `floor_pair_driver` の引用範囲不足
- `backoff_counterfactual_analysis.py` を rep observation consumer とした誤分類
- plan が current brief ではなく旧版の `:1039-1045` 引用を攻撃していること

確認できた非 blocker:

- runner の2入口と stats exact gateは plan が独立に発見済み
- notes/message は regex削除後、判定入力に残らない
- padding は現条件のままなら valid/complete にはならない
- fixture変更は oracle/freezeの既存64hex literalへ伝播しない
- v1 registry event key集合は planの変更面から静的に不変

## 総括

この plan はそのまま実装へ進められない。最大の破れは、7-key化を同じ schema/formula 名の下で受理集合拡大として行うことと、terminal の本数式が `exec_failures` を全ての欠格repの代理にして二量を再結合することである。

必要なのは、版境界の裁定、`execution_failure` と他 field の整合条件、padding の fail-closed 化、terminal のrep分類式の再設計、全 `_derive_rep_integrity()` consumer の再列挙、および新述語へ実際に到達する正例・負例である。

静的読解と grep のみを行った。file作成・変更、pytest実行は行っておらず、テスト緑は主張しない。