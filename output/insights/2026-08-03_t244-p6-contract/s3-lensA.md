結論は **NO-GO** です。P6 は現状、規律 3 を満たさないまま cap-lift の免罪符になり得ます。以下の成果物影響は、設計を将来実装・結線した場合を指します。本 wave 自体は設計のみなので、現時点の成果物値は変わりません。

## BLOCKER

### BLOCKER 1 — `P6=NA` が cap-lift を素通しし、P6 を永久に空約束にできる

**(a) 主張:** generalized cut を一件も導入しなければ P6 実装・正例・発火能力がなくても `NA` となり、cap-lift を止めません。`exact-only policy` は外部事実ではなく実装者が選べるため、reward hacking の逃げ道です。

**(b) 根拠:** D121 は exact-mask だけでは規律 3 を満たさないと断定しています (`docs/decisions.md:5819-5825`)。一方プランは `exact-only policy` を `P6NotApplicable` とし cap-lift の失敗に数えず (`s2-plan.md:123-128`)、さらに「installed generalized cut が無ければ P6=NA」としています (`s2-plan.md:361-373`)。trigger-gating は現状 NA (`:328-347`)、sort も witness 不在で適用不能 (`:349-359`) なので、現在の全具体軸で P6 の生きた適用例がありません。それでも「恒真な条項は 0 件」とする `:396` は成立しません。

**(c) 成果物影響:** `MAX_APPROVED_GENERATIONS` の受理集合が 1 世代から複数世代へ広がり、試行台帳に追加 query が入り、certified 選択値も追加探索によって変わり得る一方、proof chain は実体のない `P6=NA` を参照します。

**(d) 反証条件:** cap evaluator が「cut instance の有無」ではなく、P6 handler・全 witness-kind adapter・正負 calibration・未知 failure の fail-closed 動作が実装済みであることを必須 PASS にし、未実装・未対応を `NA` でなく `FAIL` にする状態表を示せば消えます。

### BLOCKER 2 — `P6Derived` は exact-cut の重複集約で、禁止集合に限れば効果がゼロ

**(a) 主張:** プランの P6 は構造化 anomaly から未実走範囲を導いていません。`B` の各 mask はすでに validation で qualifying red を実測済みなので、各 mask の exact cut が独立に追加されます。したがって P6 の一般化部分は受理集合を一つも追加で狭めません。

**(b) 根拠:** `S_e(M,R)` は試験済み mask だけを含み、未試験 mask を絶対に含めません (`s2-plan.md:176-190`)。座標 cut は全 universe `M=U`、すなわち全 32 mask の実走を要求します (`:192-206`)。enforcer は basis を無視して明示集合だけを使います (`:102-119`)。さらに validation 中の qualifying red は P6 の成否と独立に exact cut へ追加できると明記されています (`:414-420`)。よって P6 後の `B` は、exact-only で既に禁止される集合の部分集合です。draft v1 自身も既知 red の exact cut は規律 3 の還流ではないとしています (`README.md:144-155`)。

**(c) 成果物影響:** 候補受理集合 `U \ C` は exact-only と同じなのに、P6 status・proof chain・材料レポートだけが `Derived` へ変わり、cap-lift が可能になります。試行台帳には座標 cut 一件あたり最低 `32R` query が増えます (`s2-plan.md:273-281`)。

**(d) 反証条件:** `B \ C_exact` が非空、すなわち structured witness から少なくとも一つの未実走候補を sound に導ける証明、または exact-only では生じない次候補の admission 変更を示してください。単なる複数 exact cut の同一 class 集約は P6 PASS に数えない必要があります。

### BLOCKER 3 — variant 起因の integrity correctness failure を P6 から捨てている

**(a) 主張:** `lock_coverage_violations`、`write_intent_violations`、`permutation_violations` は verifier 自身が「variant が起こした CC 正しさ違反」と定義しているのに、プランは clean cycle 以外を非適用に落とします。optimizer は failure を cycle から integrity channel へ移すだけで P6 を回避できます。

**(b) 根拠:** プランの発火条件は `non-serializable`、integrity clean、cycle witness 必須で、`indeterminate integrity failure` を明示的に除外します (`s2-plan.md:312-326`)。sort の `permutation_violations` も適用不能としています (`:349-359`)。しかし verifier 正本は三カウンタを variant 起因の CC correctness violation と明記しています (`orchestrator/verifier/model.py:111-130`)。実 artifact にも `lockskip_single.lock_coverage_violations=1016002`、`erase_single.permutation_violations=249252` が存在します (`output/env/linux-baremetal/calibration/s3_lock_coverage.json:16-26`; `s5_permutation_coverage.json:16-25`)。

**(c) 成果物影響:** 該当 mask は禁止集合へ入らず再提案可能なままなので、試行台帳の query・停止理由・最終 certified 選択値が変わります。proof chain は既知の correctness red があるのに P6 を `NA` と記録できます。

**(d) 反証条件:** candidate-attributable integrity witness を closed union として P6 に含め、未知 witness kind は cap-lift `FAIL`、少なくとも exact cut は P6 予算と独立に追加される契約を示せば消えます。

### BLOCKER 4 — 親 (P1) は反証される。現行 hole は delay 以外の副作用を機械的に塞いでいない

**(a) 主張:** 親の「唯一の効果は backoff の有無」「到達可能な失敗は四種だけ」は偽です。現行機械 gate を通る一行で transaction procedure を変更でき、さらに canonical IR 化後も timing-mediated path は残ります。

**(b) 根拠:** hole は任意の一行代入です (`patches/silo-backoff-trigger-gating-variant.patch:86-110`)。parser が強制するのは物理一行だけ (`p3_autonomous_workload_trial.py:324-347`)、machine blacklist は五識別子だけで `pro_set_` を含みません (`axis_trigger_gating.py:53-64`; `p3_s4_loop_trigger_gating.py:112-124`)。diff quarantine も C++ 意味保証ではないと明記します (`diff_quarantine.py:14-22`)。

たとえば次は machine blacklist と一行 containment を通ります。

```cpp
izanagi_gate_pass = (pro_set_.empty() ? true : (pro_set_.pop_back(), true));
```

YCSB は procedure を `RETRY` の前に一度だけ生成し (`external/ccbench/include/ycsb.hh:102-108`)、abort 後は再生成せず `goto RETRY` します (`:149-155`)。従って上式は再試行 workload から操作を落とし、減らした transaction を commit・trace・throughput へ載せ得ます (`:161-167`)。auditor が拒否する期待はあっても、これは構造的不可能性ではありません。

副作用を canonical IR で閉じても、gate は spin の有無を変え (`patch:107-110`)、spin は global adaptive `Backoff_` を読みます (`external/ccbench/include/backoff.hh:44-107`)。直後の retry 時刻が変われば、concurrent lock/tid/node state を読む validation 分岐 (`transaction.cc:437-483`) が変わります。潜在バグが schedule-sensitive なら G2 または integrity red の発火に因果路があります。

**(c) 成果物影響:** 操作を落とした高 throughput の variant が serializable と誤認されれば、certified 選択値・Layer3 の commits/throughput・proof chain の trace 参照がすべて偽の workload を指します。timing 経路だけでも reject 集合と試行台帳が変わります。

**(d) 反証条件:** 自由 C++ を実際に廃止した canonical 5-bit parser/emitter、全 32 golden、workload-intent 完全性 verifier、および backoff timing を変えても correctness outcome が不変という形式証明または十分な反例探索を示せば消えます。

### BLOCKER 5 — exact-mask cut が P6 の発火・予算・crash 復旧に従属している

**(a) 主張:** exact-mask cut は source red の直後に独立・原子的に追加されるべきですが、プランでは P6 の結果式に内包され、P6 が発火しない場合と crash 時の遷移がありません。draft v1 §3.2 の三条件を保っていても、順序が弱くなっています。

**(b) 根拠:** P6 発火条件には「十分な未予約予算」が含まれます (`s2-plan.md:316-324`)。一方 `budget-insufficient` は `P6NotDerived` code とされ (`:130-143`)、発火前に予算不足を除く定義と矛盾します。exact cut `{p}` の追加は `P6Derived/NotDerived/NotApplicable/ContractError` の結果式にしか現れません (`:398-412`)。source red → exact append → P6 pending → terminal の順序、次 generator query の停止、atomic WAL append は定義されていません。元 draft が列挙した「verifier red 後 constraint-added 前」等の crash windowも未解決のままです (`README.md:316-324`)。

**(c) 成果物影響:** crash、予算不足、adapter 不在で `{p}` が落ちると、受理集合に既知 red mask が残り、再 build・再 query が可能になります。Layer3 と proof chain から exact-cut source-ref が欠落し、試行台帳も分岐します。

**(d) 反証条件:** `qualifying abort` と exact-cut append を一つの回復可能な状態遷移にし、P6 eligibility/予算から独立させ、P6 terminal まで次 query を拒否する crash replay 表を示せば消えます。

### BLOCKER 6 — P6 validation transcript は trusted 内部に閉じず、critic と Layer3 へ流れる

**(a) 主張:** プランは P6 witness/matrix/cut を generator へ 0 bit としますが、validation run を通常 verifier/WAL に載せるため、既存 consumer が full witness と run topology を読みます。`control_events` を分離するだけでは、通常の validation `abort` record は消えません。

**(b) 根拠:** 各 validation run は通常 verifier を通り WAL source-ref を残します (`s2-plan.md:208-221`)。しかし現行 critic は全 `abort.payload.verify` から anomaly・integrity・stats を無差別に読み (`orchestrator/critic/digest.py:232-264`)、edge/key/version を自然文へ展開します (`:584-623`)。その digest は critic payload へ渡されます (`p3_autonomous_workload_trial.py:1480-1503`)。Layer3 も全 WAL record を variant 集約し、commit のないものを reject にします (`layer3_report.py:205-218`, `:438-467`)。これは `s2-plan.md:297-310` の「trusted machine 内部」「0 bit」と両立しません。

draft v1 §4②へ最低限追加すべき行は次です。

| 新しい観測面 | 容量・漏れる内容 | 必須の閉じ方 |
|---|---|---|
| P6 validation の通常 `abort` → critic digest | witness 全文 × 最大 `32R` run | attempt purpose を署名束縛し、探索 critic から閉集合 filter |
| validation attempt → Layer3 `variants/rejects` | mask ID、順序、件数、verdict、停止 topology | `validation_events` を一次配置し、選択候補集計から分離 |
| matrix/proof hash → provenance・auditor・公開 API | 5-bit domain では総当たり可能。座標なら最大 10 パターン | active window 中は非公開、不可逆 seal 後だけ公開 |
| artifact path/mtime/size/cache hit | 上界未定義の analog channel | OS principal・sandbox を含む observable-surface 閉包 |

**(c) 成果物影響:** critic の出力・停止判断・後続提案が変わり、試行台帳の順序が変わります。Layer3 では validation mask が phantom reject として候補数・reject 集合・source-ref bijection を変え、proof chain が探索と反実仮想を混同します。

**(d) 反証条件:** validation attempt に改竄不能な purpose tag を持たせ、critic・planner・coder・auditor・Layer3・公開 API の全 consumer で正負例付き非干渉検査を示せば消えます。

## MAJOR

### MAJOR 1 — 「同じ anomaly class」は「同じ理由」ではなく、粗い症状の衝突である

**(a) 主張:** normalizer は因果機序ではなく DSG の形を分類しています。同じ G2 topology が別原因で生じても同一 class になり、P6 PASS と coordinate basis を捏造できます。

**(b) 根拠:** normalizer は具体 key を捨て、version の絶対値も捨てます (`s2-plan.md:151-167`)。同プラン自身が `reasons[].type/key/u_ver/v_ver` から trigger bit は分からないと認めます (`:223-229`)。さらに validation plan の commit は「最初の validation result より前」でしかなく (`:214-216`)、source anomaly を見た後に `R`、seed、schedule を選べます。`R` と schedule policy は未定です (`:386-389`, `:506-509`)。

**(c) 成果物影響:** 禁止集合自体は既知 exact reds のため増分ゼロでも、`witness_class_id`、coordinate basis、cap PASS、Layer3 の機序参照が別原因を同一視した値へ変わります。

**(d) 反証条件:** source query 前に R・seed・schedule・coordinate hypothesis を凍結し、normalization が固定 origin 内の因果機序に対して十分統計量である証明、または独立 holdout で原因同一性を識別する契約を示せば消えます。

### MAJOR 2 — 単調性条項が proof 欠落時と origin 変更時に破れる

**(a) 主張:** 一度導入した generalized cut の proof が欠落した場合に cut を不採用にすると、受理集合が再拡大します。また verifier/emitter/environment 変更時の cut migration 規則がありません。

**(b) 根拠:** プランは削除・弱化禁止を述べる一方 (`s2-plan.md:414-417`)、直後に「proof が破損・欠落した generalized 部分だけを不採用」とします (`:419`)。pre-install と post-install の区別がありません。draft v1 は単調性が固定 origin/emitter/verifier policy 内だけで、migration・rollback 等で緩むと明記しています (`README.md:176-191`)。`P6Derived` 出力には `origin_id` しかなく、manifest/emitter/verifier/environment の各 hash が直接束縛されません (`s2-plan.md:104-116`)。

**(c) 成果物影響:** post-install proof 欠落で受理集合が `U\(C∪B)` から `U\C` へ広がり、以前 reject された候補が再び試行台帳へ入ります。逆に stale cut を新 emitter へ持ち越せば、安全な候補を除外して certified 選択値を変えます。

**(d) 反証条件:** atomic two-phase install、導入後の proof 欠落は origin 全体 seal、cut key に immutable origin-manifest/verifier/emitter/environment hash を含め、変更時は必ず新 origin とする遷移表を示せば消えます。

### MAJOR 3 — WAL field の二義化を直した代わりに、cross-record binding が新たに曖昧

**(a) 主張:** `anomalies` の名前分離はされましたが、`certified`、`serializable`、verdict、env-tag の参照先と cross-record equality が閉じていません。自己ハッシュは真正性も与えません。

**(b) 根拠:** field 表には `verify_done` count と abort witness はありますが、`verify_done.payload.verdict/certified` と `abort.payload.verify.certified/serializable` の別名がありません (`s2-plan.md:28-47`)。それにもかかわらず照合条件は裸の `certified=false`、`serializable=false` を使います (`:49-57`)。実 producer では前者は `verify_done.payload.certified`、後者は `abort.payload.verify.*` です (`orchestrator/campaign/pipeline.py:778-807`)。`WalAbortRecordRef` は payload hash・ordinal・variant を持つだけで env-tag を持たず (`s2-plan.md:30-31`)、payload hash は record の外側や WAL 全体を認証しません。draft も外部 anchor なしの全面改竄を認めています (`README.md:341-344`)。

**(c) 成果物影響:** 異なる attempt/env の `verify_done` と `abort` を splice して偽の `P6Derived` を作ると、禁止集合、cap 判定、Layer3 source-ref、proof chain がすべて偽 record を指します。

**(d) 反証条件:** 全 field を stage-qualified 名で閉じ、verdict/certified/count/workload/env/attempt/admission receipt の cross-record equality を検査し、full canonical record hash・WAL admission receipt・外部 anchor まで束縛すれば消えます。

### MAJOR 4 — 再導出が次 iteration より前に消費される保証がない

**(a) 主張:** P6 は大きな offline batch として定義されていますが、source red 後に generator/caller を停止し、P6 terminal を次の variant admission の前提にする順序がありません。規律 3 の「毎 iteration の次の一手」が後付け検査へ退化できます。

**(b) 根拠:** 証明義務は validation mask の事前 commit と transcript 再計算を定義します (`s2-plan.md:208-221`) が、source failure → `P6_PENDING` → 次 query block → terminal の状態遷移はありません。全 32 mask × R の batch と予算だけが規定されています (`:260-293`)。発火しない場合も `NA` で進めます (`:361-373`)。

**(c) 成果物影響:** P6 完了前に生成された候補は古い禁止集合で受理され、試行台帳の順序・query 数・最終 certified 選択が変わります。後から proof を付けても、その proof から次手へ至る因果 edge は存在しません。

**(d) 反証条件:** source red 直後に origin を `P6_PENDING` として admission 閉鎖し、P6 terminal と cut append の後だけ次 query を許す状態機械、および次候補が更新後 `C` を実際に消費した proof edge を示せば消えます。

## MINOR

### MINOR 1 — M5 の「入力 0 件」は三 campaign の測定値から母集団全体へ一般化している

**(a) 主張:** 三つの autonomous loop で 9 件すべて serializable だったことは、その三 artifact の事実です。「実 campaign 由来入力は存在しない」という一般命題にはなりません。

**(b) 根拠:** brief は三 campaign のみを根拠に 0 件としています (`brief.md:52`)。静的 inventory では `output/campaigns/*/runs/wal.jsonl` は 30 本あり、たとえば trigger sweep の `balanced-c2d838b8` に 19、`read-heavy-8a237e8c` に 20、`write-heavy-a81ec3d8` に 18 件の `verify_done` があります。今回の全 30 本の静的 census では、構造化 non-serializable witness は依然 M2 fixture 一件だけでした。従って現 snapshot の値は反証できませんが、親の測定設計はその結論を証明していません。

**(c) 成果物影響:** 母集団外の real red が一件見つかれば trigger-gating は `P6NotApplicable` から発火対象へ変わり、禁止集合・validation refs・proof chain・試行台帳が変わります。

**(d) 反証条件:** 対象 artifact universe、campaign/stage/workload/env の閉集合、検索 digest、除外理由を manifest 化し、その集合全体でゼロを示せば消えます。

## 総括

最も重い所見は次の三つです。

1. generalized cut を作らなければ `P6=NA` となり、P6 の実装も発火能力もないまま cap-lift できる。
2. P6 の `B` は validation で既に exact-cut 化される mask だけなので、受理集合への限界効果がゼロなのに `Derived` と名乗れる。
3. variant 起因の integrity correctness failure を非適用へ捨て、sort を含む実在 failure channel が P6 を回避できる。

親 brief の (P1)〜(P4) への評価は以下です。

| provisional | 評価 | 根拠 |
|---|---|---|
| P1 | **反証** | 現行一行 C++ は `pro_set_` 等への副作用を機械的に塞いでいない。canonical IR 後も backoff→retry→validation の timing causal path が残る |
| P2 | **反証** | 外側 protocol の抽象化は可能でも、実契約は clean DSG cycle 専用。sort の variant 起因 integrity witness を扱えず、trigger の永久非適用も P1 反証により成立しない |
| P3 | **判断保留** | 現行 edge witness から mask 座標を静的一意に導けない点は支持する。しかし静的 proof mode の原理的不可能性は示されておらず、プラン自身も概念上可能と認める (`s2-plan.md:231`) |
| P4 | **支持** | repo 内に draft v1 の byte pin は見つからず、新規 directory で一次資料を保持する方針は妥当。なお「ポインタ一行追記」は byte 変更なので「改変しない」と同義には書けない |

この設計は、少なくとも BLOCKER 1〜6 が閉じるまで**採用してはなりません**。特に `MAX_APPROVED_GENERATIONS = 1` を維持すべきです。現案を採ると、正しさ verifier 自体は多くの red を reject し続けても、「規律 3 を満たした」という governance proof だけが先に成立し、cap、proof chain、材料レポート、試行台帳が実体より強い主張を行います。

検査は read-only の静的検査のみです。pytest・build・実測は実行しておらず、緑とは報告しません。