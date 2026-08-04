結論は「条件付き可」です。静的検査のみで、pytest・ビルド・verifier は実行していません。以下で過去の実測値に触れる箇所は、brief／worklog の記録として記述します。

### 1. bare `!` と C++ の優先順位が一致しない【must-fix】

判定: real

根拠: 提案文法では `!` のオペランドに `<comparison>` 全体を置けます（[stage2-plan.md:61](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:61>)、[stage2-plan.md:66](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:66>)）。一方 C++ では `!` が `==`/`!=` より強く結合するため、DSL が `!(reason != kUnset)` と解釈する式を C++ は `(!reason) != kUnset` と解釈します。`IzanagiAbortReason` は scoped `enum class` であり（[patch:56](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:56>)）、bool へ暗黙変換できないため、allowlist 通過後にビルドエラーになります。挿入位置は生の C++ 代入文です（[patch:102](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:102>)）。

境界テストへ入れるべき最小の入力例:

```cpp
// reject: DSL では kUnset=True、C++ では enum への ! になりコンパイル不能
izanagi_gate_pass = !izanagi_abort_reason_ != IzanagiAbortReason::kUnset;

// accept
izanagi_gate_pass = !(izanagi_abort_reason_ != IzanagiAbortReason::kUnset);
```

`!` は意味空間の表現に不要なので、最も安全なのは削除です。残すなら比較の否定は必ず括弧付きに限定すべきです。

成果物への影響: 文法上は受理された候補がビルドで脱落し、試行台帳の拒否段階と候補成功率、ひいては選択機会と材料レポートが実装表記に依存して変わります。

### 2. 式内部の代入は、提案 EBNF を忠実に実装すれば受理されない

判定: refuted

根拠: 単独 `=` は実装全体の LHS 直後に一度だけ現れ（[stage2-plan.md:56](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:56>)）、比較演算子は `==` と `!=` に閉じています（[stage2-plan.md:69](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:69>)、[stage2-plan.md:73](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:73>)）。ただし対象変数は実際に mutable な `thread_local` なので（[patch:68](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:68>)）、lexer の許可 token 集合をそのまま式文法に流用すると危険です。

境界テストへ入れるべき最小の入力例:

```cpp
izanagi_gate_pass = ((izanagi_abort_reason_ = IzanagiAbortReason::kUnset) == IzanagiAbortReason::kUnset);
izanagi_gate_pass = izanagi_gate_pass = true;
```

どちらも文字 prefilter と固定 token lexerまでは通り、parser で `INVALID_GRAMMAR` にする必要があります。最初の例は既にプランにもあります（[stage2-plan.md:174](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:174>)）。

成果物への影響: parser が誤って代入式を許すと abort 要因を書き換えた候補が選択対象となり、選択結果・材料レポート・試行台帳が本来の abort 分類ではない実行を記録します。

### 3. C++ の配置場所から読める状態は abort reason だけではない

判定: real

根拠: hole は `TxExecutor::abort()` のメンバ関数内にあり、`pro_set_`、read/write/node 集合、`thid_`、`result_`、`quit_` などが可視です（[transaction.hh:33](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/include/transaction.hh:33>)、[transaction.hh:45](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/include/transaction.hh:45>)）。patch のコメント自身もこれらを明示禁止しています（[patch:90](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:90>)、[patch:93](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:93>)）。従って「場所自体が reason-only」ではなく、新文法が初めてその境界を機械化します。忠実な文法下では、副作用・統計依存・thread依存・ループ・制御移譲・非決定性はいずれも表現不能です。

境界テストへ入れるべき最小の入力例:

```cpp
izanagi_gate_pass = thid_;
izanagi_gate_pass = result_;
izanagi_gate_pass = FLAGS_clocks_per_us;
izanagi_gate_pass = rdtscp();
izanagi_gate_pass = true; pro_set_.pop_back();
izanagi_gate_pass = true; while (true) {}
izanagi_gate_pass = true; return;
```

すべて lexical または grammar reject とし、短絡枝の内側に置かれても全 AST の構文検査を先に完了させる必要があります。

成果物への影響: これらが一つでも通ると、fairness・実行中の fitness・workload 自体に適応した候補が選ばれ、選択結果と材料レポートの比較対象が変質します。

### 4. `2^7` 方策をすべて表現できるという主張は正しい

判定: refuted（意味空間が狭まるという懸念を反証）

根拠: enum は `kUnset` を含む8値です（[patch:56](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/patches/silo-backoff-trigger-gating-variant.patch:56>)）。`kUnset=True` を固定したうえで、残る7値のうち真にする集合を等値比較の `||` で列挙すれば、全 `2^7` 写像を構成できます。これは D48 の reason-only 契約とも一致します（[decisions.md:1749](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/decisions.md:1749>)）。ただし「固定された一ビルドにおける reason→bool 写像」という意味であり、環境依存の `constexpr` 表記まで維持する主張ではありません。

境界テストへ入れるべき最小の入力例:

```cpp
// 7値すべて false
izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset;

// 7値すべて true
izanagi_gate_pass = true;

// semantic reject
izanagi_gate_pass = izanagi_abort_reason_ != IzanagiAbortReason::kUnset;
```

加えて、7値の全128部分集合を機械生成し、独立な truth-table と checker 結果を照合すべきです。

成果物への影響: 128写像を網羅する回帰があれば方策欠落による選択バイアスはなく、欠落があれば特定の候補だけが選択空間から消えます。

### 5. token 内空白と longest-match の境界テストが不足している【must-fix】

判定: real

根拠: 文法は token 間の space/tab を許すため（[stage2-plan.md:53](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:53>)）、`IzanagiAbortReason :: kUnset` は DSL と C++ の双方で有効です。一方 `: :` は二つの token であり無効です。プランは「原文を正規化しない」「2文字 punctuator を先に読む」と正しく規定していますが（[stage2-plan.md:107](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:107>)、[stage2-plan.md:112](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:112>)）、境界 matrix に split punctuator が明記されていません（[stage2-plan.md:161](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:161>)）。

境界テストへ入れるべき最小の入力例:

```cpp
// accept
izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason :: kUnset;

// reject: whitespace を削除してから lex してはならない
izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason : : kUnset;
izanagi_gate_pass = izanagi_abort_reason_ = = IzanagiAbortReason::kUnset;
izanagi_gate_pass = izanagi_abort_reason_ ! = IzanagiAbortReason::kLockConflict;
izanagi_gate_pass = true & & true;
izanagi_gate_pass = true | | false;
izanagi_gate_pass = tr ue;

// reject: maximal-munch の余剰 token
izanagi_gate_pass === true;
izanagi_gate_pass = true &&& true;
izanagi_gate_pass = true ||| false;
```

有効な `==`、`!=`、`&&`、`||`、`::` それぞれの positive も、単文字 token より先に読まれることを固定すべきです。

成果物への影響: 空白結合を誤ると C++ ではコンパイル不能な式を checker が受理し、逆順 lex では正当な候補を落として試行台帳と選択母集団を変えます。

### 6. 列挙された C++ 字句迂回には、許可文字＋固定語彙を越える漏れは見つからない

判定: refuted

根拠: ASCII の限定文字を先に検査し、word を `[A-Za-z_]+` の maximal-munch と完全一致で閉じるため（[stage2-plan.md:107](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:107>)、[stage2-plan.md:112](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:112>)）、alternative token は未知 word、digraph/trigraph・行継続・コメント・literal・UCN・属性・directive は許可外文字になります（[stage2-plan.md:115](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:115>)）。GNU系の `$` 識別子や predefined macro も、それぞれ許可外文字／未知 word です。

境界テストへ入れるべき最小の入力例:

```text
izanagi_gate_pass = $x;
izanagi_gate_pass = @x;
izanagi_gate_pass = __TIME__;
izanagi_gate_pass = __COUNTER__;
izanagi_gate_pass = __attribute__;
<U+FEFF>izanagi_gate_pass = true;
izanagi_gate_pass<U+00A0>= true;
izanagi_gate_pass = true;<VT>
```

API境界として `None`、`bytes`、list は `INVALID_TYPE`、Python の lone surrogate `"\ud800"` は例外を外へ出さず fail-closed にすべきです（公開結果型は [stage2-plan.md:31](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:31>)）。

成果物への影響: fail-closed が保たれれば変化はなく、Unicode encode例外などで checker 自体が落ちると拒否記録のない試行中断が台帳へ生じます。

### 7. bare `!` を直した後の `kUnset` 評価器には、他の C++ 不一致は見つからない

判定: refuted

根拠: 葉は bool literal と scoped-enum の `==`/`!=` だけで、優先順位は `!`、`&&`、`||` の順です（[stage2-plan.md:59](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:59>)）。副作用や例外を起こす葉がないため、eager と短絡の値は一致します。ただし C++ との対応を明確にするため evaluator は短絡実装とし、短絡前に入力全体の parse を完了させるべきです。Python `eval` を使わない方針も妥当です（[stage2-plan.md:51](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:51>)）。

境界テストへ入れるべき最小の入力例:

```cpp
// accept
izanagi_gate_pass = true || false && false;
izanagi_gate_pass = !!true;
izanagi_gate_pass = !(izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict);

// UNSET_NOT_TRUE
izanagi_gate_pass = !true;
izanagi_gate_pass = !(true || false);
```

成果物への影響: bare `!` 以外で評価順を正しく実装すれば変化はなく、誤実装時は候補の false accept／false reject がそのまま選択母集団と台帳に反映されます。

### 8. 上限値は妥当だが、カウント定義と判定順が未固定

判定: real

根拠: 上限は 4096 byte／512 token／深度64です（[stage2-plan.md:111](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:111>)）。正例最長は379 byte（[positive-controls.txt:5](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:5>)）。8 member 全列挙の canonical 式も静的計数で497 byte／50 tokenなので、全128方策に十分な余裕があります。緩めではありますが、空白・冗長 `!`・括弧による資源消費を有限化する意味はあります。

境界テストへ入れるべき最小の入力例:

```python
"izanagi_gate_pass = true;" + " " * 4071   # 4096 byte: accept
"izanagi_gate_pass = true;" + " " * 4072   # 4097 byte: RESOURCE_LIMIT

"izanagi_gate_pass = " + "!" * 508 + "true;"   # 512 token: accept
"izanagi_gate_pass = " + "!" * 509 + "false;"  # 513 token: RESOURCE_LIMIT
```

括弧は64重を accept、65重を reject とします。token数は「空白とEOFを除く lexical token数」、深度は「同時に開いている `(` の最大数」、byte数は正規化前ASCII入力、と明記すべきです。判定順も `type → raw size → character → token count → parse/depth → semantic` に固定してください。

成果物への影響: 境界定義が環境や実装で揺れると同じ候補の受否・reason_code が変わり、試行台帳の再現性と材料レポートの候補数がずれます。

### 9. `pro_set_.pop_back()` に対して trace/verifier は workload 縮小を検出しない

判定: real

根拠: procedure は retry 前に一度生成され（[ycsb.hh:102](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:102>)）、同じ vector を retry ごとに再走査します（[ycsb.hh:108](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:108>)、[ycsb.hh:117](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/include/ycsb.hh:117>)）。`abort()` は read/write/node集合だけを消し、`pro_set_` は消しません（[transaction.cc:27](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/transaction.cc:27>)）。trace はcommitした実際の read/write集合しか出力せず（[transaction.cc:594](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/external/ccbench/cc/silo/transaction.cc:594>)）、verifierの `Txn` に予定 operation 数はありません（[model.py:37](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/verifier/model.py:37>)）。integrityにも `FLAGS_ycsb_max_ope` との照合はありません（[model.py:132](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/verifier/model.py:132>)）。

境界テストへ入れるべき最小の入力例:

```cpp
izanagi_gate_pass = true; pro_set_.pop_back();
```

checker negative に加え、verifierの限界を固定する characterization として、read/writeを持たない単独commit trace `C 0 0 1 1` の扱いも明記すべきです。

成果物への影響: これを許すと競合retryだけ操作数が減り、実際より高いthroughputの候補が選ばれて、選択結果・材料レポート・台帳が別workloadの測定になります。

### 10. 当該変異を入れた実 run の verifier が実際に認証するか

判定: 未確認

根拠: 現行 plan 自身が「緑のままになり得る」はコードからの推論で、verifier実測ではないと明記しています（[stage2-plan.md:18](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:18>)）。空でないclean traceならcertifiedとなる実装です（[model.py:185](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/verifier/model.py:185>)）が、特定runに別のcycleやintegrity違反が出ないことまでは静的に保証できません。

境界テストへ入れるべき最小の入力例: 親実測では上記 `izanagi_gate_pass = true; pro_set_.pop_back();` を組み込んだrunについて、throughput・commit当たりR/W数・verifier verdictを同時取得する必要があります。

成果物への影響: 実runが認証されなければ「必ず検査を通る」という攻撃実証は弱まりますが、workload縮小をtrace schemaが直接検査しない設計問題は残ります。

### 11. checked-in freeze と live source を結ぶ回帰テストが欠けている

判定: real

根拠: frozen manifest がpinするのは2つのJSON自身のbytesだけです（[test_frozen_artifacts.py:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_frozen_artifacts.py:38>)、[test_frozen_artifacts.py:125](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_frozen_artifacts.py:125>)。known-axes test はlive sourceから文書を再生成して自己検証し（[test_s1_known_axes_freeze.py:103](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s1_known_axes_freeze.py:103>)）、direct-comparisonの多くのtestは verifier を no-op 注入しています（[test_s1_direct_comparison.py:125](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_s1_direct_comparison.py:125>)）。`check_docs.py` は意味的freeze照合器ではなく（[check_docs.py:2](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/tools/check_docs.py:2>)）、land時foldも同checkerを呼ぶだけです（[dev_wave_land.py:1437](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/tools/dev_wave_land.py:1437>)）。hookの保護対象にもこのaxis sourceはありません（[hooks/README.md:48](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/hooks/README.md:48>)）。したがって repo scan／docs／fold／hooks は一般的なsource sha drift防壁ではありません。

また記録上は「全緑」ではなく、5430 passedに既存1 failedを伴います（[docs/worklog.md:366](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/worklog.md:366>)）。

境界テストへ入れるべき最小の入力例: checked-in `known_axes_freeze.json` を読み、`source_resolver` で末尾へspaceを1 byte加えた一時 `axis_trigger_gating.py` を返し、`source sha256 不一致` を要求するtest。measurement freezeからの経路も同様に1本必要です。

成果物への影響: source driftが通常suiteを通ってlandし、S1開始時になって初めて拒否されると、選択結果は生成されず、材料レポートと試行台帳の作成が運用途中で停止します。

### 12. 「source sha pin はどこでも発火しない」という一般化は誤り

判定: refuted

根拠: `s1_known_axes_freeze.verify_document` は全sourceを実ファイルとsha照合します（[s1_known_axes_freeze.py:731](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_known_axes_freeze.py:731>)、[s1_known_axes_freeze.py:739](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_known_axes_freeze.py:739>)）。measurement verifierもknown-axes verifierを呼び（[s1_measurement_freeze.py:407](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_measurement_freeze.py:407>)）、production direct-comparison loaderは既定でそれを実行します（[s1_direct_comparison.py:119](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:119>)、[s1_direct_comparison.py:130](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_direct_comparison.py:130>)）。正しい一般化は「通常suiteがchecked-in freeze対live sourceを検査していない」であって、「pin自体が不発」ではありません。

境界テストへ入れるべき最小の入力例: production loaderへno-op verifierを注入せず、前項の1-byte source driftを与え、campaign開始前の拒否を確認するtest。

成果物への影響: productionでは凍結結果が黙って別実装へ置換されるのではなく実行が止まるため、誤った一般化は材料レポート上の障害説明と再現手順を誤らせます。

### 13. 既存 `test_ruleops.py` failure のT409無関係という切り分け

判定: refuted（切り分けが不当という懸念を反証）

根拠: 対象testは実repoに対して `ruleops.py inventory` を subprocess実行します（[test_ruleops.py:1709](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/tests/test_ruleops.py:1709>)）。現実装は対象blobをUTF-8 strict decodeし、非UTF-8なら `non-utf8` を送出します（[ruleops.py:642](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/tools/ruleops.py:642>)、[ruleops.py:665](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/tools/ruleops.py:665>)）。worklogは原因blobがT409以前のmainにあり、関係ファイルに触れていないと記録しています（[docs/worklog.md:366](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/worklog.md:366>)、[docs/worklog.md:596](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/docs/worklog.md:596>)）。静的にはT409との因果経路はありません。

ただし「このnodeidなら何でも既存赤」と扱うと、同じtest内の新しい早期失敗を隠せます。nodeidだけでなく `non-utf8`、対象path、可能ならblob digestまでbaseline signatureとして固定すべきです。

境界テストへ入れるべき最小の入力例: 一時repoの `output/insights/x/raw.bin` を `b"\xff"` とし、現行baselineなら `RuleOpsError.reason == "non-utf8"` を要求するtest。

成果物への影響: 切り分け自体は選択結果を変えませんが、広すぎるfailure waiverは新しい台帳／材料生成系の退行を既存赤として見落とします。

### 14. `s8a_trigger_sweep` と `s1_direct_comparison` の現行canonical入力は壊れない

判定: refuted

根拠: sweep generatorは必ず `kUnset` の等値比較から始め、許可memberを `||` で足すだけです（[s8a_trigger_sweep.py:215](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:215>)、[s8a_trigger_sweep.py:221](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s8a_trigger_sweep.py:221>)。回収済みtrigger正例9件も同形式です（[positive-controls.txt:1](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:1>)、[positive-controls.txt:41](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:41>)）。壊れるのはS1 test内のLF付きsynthetic入力で、プランも意図的な境界変更として認識しています（[stage2-plan.md:190](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:190>)）。

境界テストへ入れるべき最小の入力例:

```text
accept: "izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset;"
reject: "\nizanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset;\n"
```

全 `candidates()` 出力をcheckerへ通すproperty testも維持すべきです。

成果物への影響: 現在の凍結選択やsweep候補は変わりませんが、LFや非canonical表記を使う外部・synthetic callerはbuild前syntax rejectとして台帳へ記録されます。

### 15. `s1_verify_extime_calibration` の最終materializerが配線対象から漏れている【must-fix】

判定: real

根拠: プランが列挙する既存別経路はs8a sweepとs1 direct comparisonだけです（[stage2-plan.md:150](</work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:150>)）。しかしextime calibrationもs8a generatorからpredicateを構築し（[s1_verify_extime_calibration.py:186](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:186>)）、`_build_target` がそれを `write=True` で直接materializeします（[s1_verify_extime_calibration.py:329](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:329>)、[s1_verify_extime_calibration.py:335](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:335>)）。通常の `main` は上流のfreeze照合を通るため現時点のCLIは保護されています（[s1_verify_extime_calibration.py:403](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-evolve-hole-allowlist/orchestrator/campaign/s1_verify_extime_calibration.py:403>)）が、sink自身の不変条件がなく、直接呼出や将来のrefactorで迂回できます。

境界テストへ入れるべき最小の入力例:

```cpp
izanagi_gate_pass = true; pro_set_.pop_back();
```

これを `target["gate_predicate"]` に入れて `_build_target` を呼び、quarantineのwrite・build・source変更のいずれにも到達しないことを確認すべきです。

成果物への影響: calibration経路で不正predicateがmaterializeされるとverifier時間見積りと構成provenanceが汚れ、後続の試行台帳・材料レポート・選択予算に波及します。

## 総括

- 文法設計は採用可能か: 条件付き可
- must-fix の件数と最重要 1 件: 3件。最重要はbare `!`をDSLでは比較全体の否定、C++ではscoped enumへの否定として解釈する優先順位不一致
- 親 brief で誤っていた点: Dの「pinは発火しない」はtest coverageに限る説明で、production verifierまで含めると過大。「全スイート緑」とAの「verifier緑を実測」は現briefの事実ではなく、旧「後続transactionまで恒久」「trigger正例26件」はbrief内で既訂正済み