## trace 有効の 12 構成は提示差分どおりではコンパイル不能

- 深刻度: blocker
- 根拠: `plan-v2.md:121-172` は `izanagi_backoff_trace_assigned_invert` を代入・参照するが宣言も 0 初期化も示していない。追加先の既存 trace local 群にも存在しない (`patches/cicada-adaptive-dynamic.patch:273-285`)。したがって policy 0/1/2 × step_adapt 2値 × dyn_ceiling 2値の trace=1、計12構成で未宣言識別子になる。post-B の hunk 文脈自体は `patches/cicada-adaptive-dynamic.patch:11,28,61-63,118-119,134-137,313-358` と一致し、計画された C に include 追加もない。trace=0 側では origin と LCG member の前処理 guard は適切で、追加の未使用変数・符号比較問題は静的には見当たらない。
- 成果物影響: 24構成 compile の半数が成立せず、patch C は受理不能になる。

## policy 2 は割当 bit と実際の一歩が一致しなくても全テストを通り得る

- 深刻度: blocker
- 根拠: policy 2 の唯一の実装系列 pin は `test_policy_two_assignment_sequence_is_exact` (`plan-v2.md:484`) で、他の exact transition は policy 0/1 用 (`plan-v2.md:481-483`)。例えば記録する LCG bit は正しいまま反転条件を `== 0` にする変異は、16 bit pin、24 compile、policy 1 の遷移、synthetic parser test をすべて通り得る。parser の再検算も realized=1 の場合だけで、assigned=0 の安全域で推奨方向へ動いたことは検査しない (`plan-v2.md:244-250`)。
- 成果物影響: forward/invert 層が逆または混成になり、次 wave の「同一 pre-state の一歩」という中心命題が偽の割当で測定される。

## A+B+C を全 mode に強制しながら旧 prereg と schema v2 を再利用している

- 深刻度: blocker
- 根拠: plan は `_patch_stack_identity` と `_applied_patch_stack` を無条件 A+B+C にする (`plan-v2.md:380-403`)。この stack は certification と performance の両方で適用される (`tools/pegasus/probes/t2187_adaptive_const_probe.py:2678-2679,3048-3049`) 一方、旧 prereg は不変扱い (`pin-closure.md:26`, `plan-v2.md:588`)。さらに現在の4 schema はすべて v2 (`t2187_adaptive_const_probe.py:49-54`) で、テストも v2 を pin したまま (`test_t2187_adaptive_const_probe.py:1595-1599`) だが、plan は patch identity、12 field、event keys、directional strataを変更しても version bump を計画していない。A+B 導入時には schema を v2 にした前例もテスト内に明記されている (`test_t2187_adaptive_const_probe.py:85-94`)。
- 成果物影響: 旧 A+B artifact と新 A+B+C artifact が同じ schema 名を持ち、旧 prereg が凍結していない source stackを prereg済みとして受理できる。

## C++ emitter と Python parser が結合試験されていない

- 深刻度: must-fix
- 根拠: v1/v2混在拒否、summary版一致、seq連続、tsc単調性の設計自体は明確である (`plan-v2.md:244-250`; 現行検査は `t2187_adaptive_const_probe.py:868-922`)。しかし parser test は手書き文字列を使い (`plan-v2.md:506,513`)、遷移 driver は実際の `IZANAGI_BACKOFF_TRACE` stdout を明示的に捨てる (`test_dynamic_backoff_transitions.py:546-554`)。C++側が summaryだけ v1、field順序違い、field名違いを出しても compile と synthetic parser test は緑になり得る。
- 成果物影響: wave は受理されても最初の実測で trace 全体が parse不能になり、診断 artifactを生成できない。

## 図生成器の閉包は expected_stack 以外にも欠けている

- 深刻度: must-fix
- 根拠: pin 閉包は `expected_stack` だけを列挙する (`pin-closure.md:13`)。実物には固定 `TRACE_CELLS`、`CELL_CONFIGS`、`CONFIG_FIELDS`、`CELL_FORMAT_FIELDS` がある (`tools/plotting/plot_dynamic_backoff.py:71-95`)。新しい `cw-as-dyn-p0/p1/p2` は exact diagnostic grid で拒否される (`plot_dynamic_backoff.py:474-482,552-582`)。新 event 三項目と directional strataも `_parse_event` と `_parse_trace_run` が捨てる (`plot_dynamic_backoff.py:409-448,517-549`)。また provenance は A/B hashを手動列挙しており、plan が追加する C hash の伝播指示がない (`plot_dynamic_backoff.py:1397-1400`; `plan-v2.md:444-450`)。
- 成果物影響: 次 wave の反実仮想 trace は既存図生成器に受理されず、仮に旧 cellで通しても新しい層別と C の明示 provenanceが消える。

## 二層 exact gate の逐語同一性を直接検査するテストがない

- 深刻度: must-fix
- 根拠: Python の map-based exact OR と PBS の exact OR は受理域を緩めず、片方だけ変更すれば PBS 前段または Python 後段で新 literal が拒否される (`plan-v2.md:292-314,353-367`)。ただし計画されたテストは Python と PBS を別々に検査するだけ (`plan-v2.md:508-510`) で、`COUNTERFACTUAL_TRACE_CELLS_TEXT.replace(",", "+") == COUNTERFACTUAL_TRACE_CELLS_RAW` の逐語比較がない。
- 成果物影響: 二層の片方に一文字 drift が入ると、計画上は正例の反実仮想 traceが到達不能になる。

## CMake consumer test は default 変更にも universal definition 削除にも歯がない

- 深刻度: must-fix
- 根拠: static test は既定0と universal definition 行を逐語検査するため M1/M2 を殺せる (`plan-v2.md:454-457`)。一方 consumer test は明示 policy 2 の `Genome.flags` を見るだけで、CMake configureも `ccbench_universal_definitions` も通らない (`plan-v2.md:457-459`; 現行 CMake伝播位置は `patches/cicada-adaptive-dynamic.patch:19-32`)。従って M2 を consumer系も殺すという記載 (`plan-v2.md:535`) は誤りで、M1も consumer側では検出されない。単純な出現回数検査なら、行を function 外へ移す変異も残る。
- 成果物影響: CMake実配線の証拠は単一の文字列検査に依存し、mutation matrixが主張する冗長性を持たない。

## 変異 matrix は冗長 gate を過大計上し、重要な無歯変異を落としている

- 深刻度: must-fix
- 根拠: M2 の consumer冗長性は成立しない。M8 の「24 compileも赤になり得る」は意味変異が warningを生む場合だけで gateではない (`plan-v2.md:541`)。M17 は Python/PBSそれぞれ別の mutation siteであり、片側変異に対して冗長ではない (`plan-v2.md:550`)。M18 は stack、plot、registryを一候補に束ねた複合変異で、確実な冗長性は registry欠落に対する exact集合と件数 pinだけである (`test_condition_meaning_gate.py:2397-2416,2504-2506`)。確実な複数 gate は M7 の clamp/ceiling-shrink、M13 の magnitude/clamp/shrink、registry側 M18。無歯候補には「LCGを gradient=0、推奨差分0、clamp時だけ進めない」および「trace=0の policy 1/2だけ診断名を残す」がある。前者の特殊入力は要求されず (`plan-v2.md:210,484`)、後者の preprocess testも3 policy全件を要求していない (`plan-v2.md:489`)。
- 成果物影響: 機序を壊す変異が生存し、段6の mutation結果から実装の意味保存を結論できない。

## 親の pin 閉包とゲート入力表には現物との不一致がある

- 深刻度: must-fix
- 根拠: `pin-closure.md:1,11` は廃止済みの `BACKOFF_INVERT_STEP` を新 define/defaultとして記録し、plan自身が訂正している (`plan-v2.md:5-9`)。同閉包 `:15` は testの1643行を PBS文字列 pinとするが、現物は `"${BACKOFF_TRACE_ARGS[@]}"` の存在しか見ていない (`test_t2187_adaptive_const_probe.py:1632-1645`)。また `gate-input-measurement.md:18-20` は raw args と parsed値を同じ値として記載するが、現物では argsは文字列、`cells/workloads/threads` は tupleで別々に比較される (`t2187_adaptive_const_probe.py:2495-2507`)。12 field到達不能、PBS colon数、既存 literal、patch A SHA、LCG先頭16 bitの値自体は現物と一致した。
- 成果物影響: 閉包をそのまま実装指示に使うと誤った default keyと存在しない PBS coverageを採用し、raw/parsed二重検査を落とし得る。

## 12 field の identity衝突は閉じるが receipt波及はゼロである

- 深刻度: nit
- 根拠: plan の key-presence規則は、11 fieldと明示 policy 0 の12 fieldが同じ Cellになる経路を閉じている (`plan-v2.md:266-273`)。12 field identityが実際に届くのは row payloadと同じ rowを保存する journalの2面 (`t2187_adaptive_const_probe.py:3139-3179`)。`_cell_from_document` のproduction callは certification row/groupだけ (`t2187_adaptive_const_probe.py:1782,2121`) で、certification contractは既存5/11 fieldの `CERT_CELLS`しか受けない (`t2187_adaptive_const_probe.py:986-1000`)。従って receiptへの新 field波及は0面である。
- 成果物影響: 現 wave の受理域は変わらないが、12 fieldがcertification receiptまで保護されたという説明は過大になる。

## 総括

blocker は3件ある。  
最重は `assigned_invert` の宣言欠落で、提示差分どおりなら24構成中12構成がコンパイル不能になる。  
policy 2 の割当と実動作の未結合、A+B+Cと旧 prereg/schema v2の衝突も測定命題を壊す。  
post-B hunk文脈、include不変、v1/v2混在拒否の設計自体には追加 blockerを認めなかった。  
read-only静的検査のみで、pytestや実コンパイルは実走していない。