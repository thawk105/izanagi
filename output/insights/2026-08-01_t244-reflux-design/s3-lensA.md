結論は **NO-GO**。`4.585 bit/window` は全観測面の上界ではなく、campaign-global budget も現行実装・設計案のどちらでも回復不能性を示せていない。以下の成果物影響は、docs-only の本 wave 自体ではなく、この設計を根拠に D114 を解除した場合を指す。

## 所見 1 — “hidden” constraint が effective diff / SHA から復元でき、bit 上界は有限に閉じていない

**重大度: BLOCKER**

**根拠:**

- `s2-plan.md:15` は auditor に「machine が constraint を適用した実効 diff」を渡す。
- 同 `:42-46` は `E_t = P_t ∨ C_t` と固定 5-bit emitter を定義する。
- 同 `:150-153` は `raw IR SHA`、`effective IR SHA`、`constraint-added` の ID・旧新 commitment を WAL に残す。
- 一方、同 `:58` は低エントロピー constraint の SHA が辞書攻撃可能だと自ら認めている。5-bit IR はわずか 32 通りなので、unsalted `effective IR SHA` も同じく総当たりで完全復元できる。
- 現行コードでも auditor payload は `working_diff` 全文を受ける (`p3_autonomous_workload_trial.py:897-905`)。role の parsed 自然文は journal/report に残る (`:590-597`, `:722-758`)。
- auditor の `violations/nits/proposed_tests/uncertainty` に長さ上限はない (`auditor_gate.py:125-157`)。時刻も microsecond 精度文字列で記録される (`s8b_prediction_runner.py:206-207`)。プラン自身も timing・artifact size を閉じないと認める (`s2-plan.md:181-187,235-240`)。

観測可能量の会計は次になる。

| 観測面 | 容量 |
|---|---:|
| 固定 constraint 文・順序 | exact-byte pin が実在すれば 0 bit。現状その検査なし |
| effective diff / effective IR SHA | 32 状態、最大 5 bit/query。厳密な singleton probe でも membership 1 bit/query |
| constraint-added の存在 | 1 bit |
| opaque ID (`none` + 5 atom) | 最大 `log2(6)=2.585` bit。ID 生成規則は未定義 |
| constraint 件数・残予算 (`0,1,2`) | 各最大 `log2(3)=1.585` bit |
| accept/reject | 1 bit/query |
| planner の direction×magnitude | `log2(9)=3.170` bit/generation |
| seal 後 class (`none` + 5 atom) | `2.585` bit/window |
| stop/call topology、source ref、自然文、時刻、file size | 契約上の有限上界なし |

自然文・時刻を除いた五面だけでも、結合 alphabet は最大  
`5 + 2.585 + 1.585 + 1 + 3.170 = 13.34 bit/generation` を持つ。相関があるため実 entropy はこれ以下になり得るが、プランの `4.585 bit/window` は全観測面の上界ではない。現在証明できる上界は「未定義」である。

**成果物影響:** hidden mask を復元した generator が次候補を gate 探索向けに変え、certified winner と受理集合を変える一方、材料レポートは過小な disclosure 値を記録する。

## 所見 2 — 前 wave と同じ 9 記号符号化が、共有 provider 経由でそのまま成立する

**重大度: BLOCKER**

**根拠:**

- プラン自身が物理容量 `log2(9)=3.17 bit` を認め、「planner が failure を知らないから条件付き情報量 0」と仮定する (`s2-plan.md:48-64`)。
- しかし `run_trial()` は任意の `providers` を注入できる (`p3_autonomous_workload_trial.py:990-1004,1045-1050`)。`provider_kind` は実体照合なしで report label に写るだけである (`:722-729`)。
- default provider の session ID 重複集合も provider instance ごと (`claude_projected_provider.py:161,264-296`)。D106 も role 横断の再利用を拒否しないと明記する (`docs/decisions.md:4799-4805`)。
- coder は次世代でも `planner_direction={axis,direction,magnitude}` を受ける (`p3_autonomous_workload_trial.py:843-860`)。プラン v1 もこの 3 field を残す (`s2-plan.md:14`)。

攻撃は一意である。

1. generation 1 の auditor/shared provider が effective diff から `{none, 5 atom}` の 6 状態を得る。
2. generation 2 の planner がその状態を 9 通りの direction×magnitude に符号化する。
3. coder は一世代で `log2(6)=2.585 bit` の constraint class を完全復元する。前 wave の 4-class=2 bit より余裕がある。

「shared session なら fail-closed」はプランの一文 (`s2-plan.md:62`) に留まり、どの検査が赤くなるか定義されていない。

**成果物影響:** coder が非公開 constraint class を知って適応し、同一 budget 内の候補・certified 選択・WAL の proposal provenance が failure-blind という前提から外れる。

## 所見 3 — 単調集合の差分は 1 bit/query の membership oracle になる

**重大度: MAJOR**

**根拠:**

- `E_t=P_t∨C_t` (`s2-plan.md:42-45`) と `C_t⊆C_{t+1}` (`:201-218`) から、raw mask と effective mask の差はそのまま `r∈C_t` の判定になる。
- `constraint-added` event、旧新 commitment、constraint count も増加の有無を観測させる (`:147-155`)。

atom `r` だけを `false` にした singleton を出せば、`E_t[r]=1` なら constraint 済み、`0` なら未拘束である。既知 constraint を再度踏めば、`P_t≠E_t` 自体が 1 bit を運ぶ。二世代なら generation 1 の failure が永続 constraint になったかを generation 2 で復元できる。5 probe が許されれば全 5-bit mask を復元できる。

`Qmax=2` が本当に origin-global・無回復なら、前 wave の「既知 2 件で padding 後、3 件目を読む」攻撃は止まる。しかし止まるのは三件目であって、差分 1 bit/query が 0 になるわけではない。次の所見の回復経路が残る限り、5-probe 復元も残る。

**成果物影響:** constraint の存在を oracle として候補を最適化でき、受理集合を意図した探索制限ではなく constraint 探索結果に依存させる。

## 所見 4 — campaign-global budget は ID 変更・削除・分割で新品に戻る

**重大度: BLOCKER**

**根拠:**

| 回復経路 | 現行実装 |
|---|---|
| 別 run-root | no-build は `run_root/campaigns/<id>` を使うため即新品 (`p3_autonomous_workload_trial.py:779-783`) |
| 別 trial ID | `trial` は canonical preimage に含まれる (`ident.py:76-91`)。`_campaign_for()` も trial ID を投入する (`p3_autonomous_workload_trial.py:426-455`) |
| config 微修正 | `spec_content/search_tag/search_config/trial` のいずれかが変われば別 ID (`ident.py:76-103`) |
| programmatic 分割 | `drive/providers/preview` 注入と direct `drive_iteration()` は D114 の保証外 (`docs/decisions.md:5363-5375`) |
| checkpoint 削除 | `loop_state.json` が無ければ loader は `None` (`p3_s4_loop.py:421-427`) で、freshness gate は受理する (`p3_autonomous_workload_trial.py:196-206`)。WAL/lock の消費数は見ない |
| campaign 全削除 | lock/WAL とも local file。WAL は hash chain・真正性を持たない (`wal.py:14-15`) |

したがって親 brief の「budget を search_config に置けば campaign ID に束縛される」(`brief.md:45-49`) は、真正性の binding と総量 accounting を混同している。ID に束縛されるからこそ、ID を変えれば新品になる。

プランはこの点を `s2-plan.md:107-133` で正しく認識して上位 origin を提案するが、次が未定義である。

- `origin_layout` の一意な保存場所
- 同じ科学的 cell に複数 series ID を発行しない機械規則
- supersede/config 改訂をまたぐ累積予算
- registry の issuer/署名検証
- ledger 削除・rollback・inode 置換への外部 anchor

しかも「同一 UID の悪意ある caller から秘匿しない」「WAL は外部 anchor なしに全面改竄を防げない」を受容残余にしている (`s2-plan.md:186-187`)。programmatic split を攻撃モデルに含めながら、同じ caller に ledger rollback を許すのは自己矛盾である。

**成果物影響:** query 数を任意に増やせるため評価候補と certified winner が増減し、report の `budget.consumed`、台帳の slot 列、proof-chain source refs が実際の総探索量を表さなくなる。

## 所見 5 — 親 brief の三つの実測一般化がコードに反する

**重大度: BLOCKER**

**根拠:**

1. **「cross-generation チャネルは 2 本だけ」は偽。**  
   outcome から `current_metrics` が更新され (`p3_autonomous_workload_trial.py:951-953`)、次世代 planner の `current_perf/leading_indicators` (`:815-825`) と coder の `baseline` (`:843-860`) に入る。5 個の数値は丸められておらず、whiteboard とは別チャネルである。親 brief の断定は `brief.md:32-34`。

2. **「理由は 1 bit も渡らない」は射程過大。**  
   exact technical reason が planner/coder payload に直送されないだけで、whiteboard の `success|fail|rejected` は 3 状態で最大 `log2(3)=1.585 bit`。さらに critic は detailed digest を受け (`p3_autonomous_workload_trial.py:955-967`)、その関数である `reverse_recommended` が次 iteration の driver state/stop に効く (`:983`, `p3_s4_loop.py:673-683,744-749`)。

3. **「制約強制点が既に存在する」は偽。**  
   `check_syntax_contract()` は固定 5 識別子の blacklist にすぎない (`p3_s4_loop_trigger_gating.py:103-115,318-336`)。coder parser は任意の一行 C++ string を受理する (`p3_autonomous_workload_trial.py:261-284`)。positive 5-bit mask、`E=P∨C`、canonical emitter を強制する面ではない。プラン自身も将来 parser/emitter を別実装すると認める (`s2-plan.md:300-309`)。

コードが正しく、親 brief の一般化が誤りである。

**成果物影響:** 漏れている metrics/control channel と未実在の enforcement point が acceptance scope から落ち、将来の多世代 run の proposal、受理集合、材料レポートの disclosure 主張が不正になる。

## 所見 6 — D116 の主要保証には、破ったとき赤くなる検査がない

**重大度: BLOCKER**

**根拠:**

| 保証 | 現在実際に赤くなる場所 |
|---|---|
| generation `>1` 拒否 | 実在: `_validate_generation_budget()` を三入口で呼ぶ (`p3_autonomous_workload_trial.py:184-193,768,1008,1110`) |
| 既存 checkpoint 拒否 | 実在。ただし削除・race は非被覆 (`:196-206,783`) |
| 5 固定禁止識別子 | 実在: `check_syntax_contract()` |
| whiteboard field 名 / `delta_pct=None` | 実在: `p3_s4_loop.py:367-404`。ただし direction/magnitude/result の値域は未検査 |
| 固定 5-bit parser/emitter | 実装なし、検査なし |
| `C_t` 単調増加 | state 自体なし、検査なし |
| I/Q/K の原子予約・無返却 | primitive なし、検査なし |
| origin-global uniqueness | origin resolver/registry/ledger なし |
| planner/coder payload の failure 非干渉 | failure class を全反転して payload bytes 同一性を見る検査なし |
| binary API・固定 2 slot transcript | 現行 report は multivalued outcome/stop/role event を全文保持 (`p3_autonomous_workload_trial.py:711-758`) |
| commitment の辞書耐性 | nonce 生成・秘匿・照合規則なし |
| control WAL grammar | `reflux-control` は `WAL_STAGES` に存在しない (`model.py:20-32`) |
| shared provider/session 拒否 | 検査なし |
| 「abort reason を言うな」 | prompt のみ (`p3_autonomous_workload_trial.py:118-123`) |

`s2-plan.md:314-316` は将来テストファイルと話題を列挙するだけで、hidden-state 全変異に対する noninterference、ledger 削除、ID 重複発行、effective-hash 辞書攻撃を red にする predicate がない。

現行 report の `fresh_context/fixed_generations/performance_early_stop` 等が literal であることは runbook 自身も認めている (`docs/phase3-s8c-autonomous-trial-runbook.md:161-166`)。これらを D116 の証拠へ再利用すれば恒真保証になる。

**成果物影響:** 実装が設計から逸脱しても acceptance が通り、report/WAL に「budgeted」「hidden」「monotone」と記録しながら実際の受理集合だけが広がる。

## 所見 7 — 「単調」は固定 origin 内の構文集合についてだけで、semantic safety や campaign 横断ではない

**重大度: MAJOR**

**根拠:**

- プランの形式定義は `C_t⊆C_{t+1}` と mask 集合 `A(C)` だけ (`s2-plan.md:201-219`)。
- 実行時挙動の数学的単調性は証明しないと明記する (`:181-184`)。
- human が新 origin を発行すれば予算が新品になることも明記する (`:235-240`)。

したがって単調性が成立するのは「固定 universe・固定 emitter・固定 verifier policy・固定 origin 内の atom set」に限る。次では緩む。

- 新 campaign/origin/series ID
- role bundle、emitter、IR schema、verifier policy、environment contract の変更
- human intervention / registry 再発行
- supersede・migration
- checkpoint/control WAL の削除・rollback
- 同一 UID による hidden state 編集

また `A(C)` は verifier へ進める mask 集合であって、実際の certified 集合ではない。各 candidate の verifier が依然必須というプランの残余とも整合する。

**成果物影響:** campaign をまたいで受理集合が再拡大しても「単調」と表示され、異なる policy/origin の certified 選択や proof chain が比較可能であるかのように材料レポートへ混載される。

## 所見 8 — translator は「失敗理由」を constraint 化せず、失敗候補の差分を no-good cut にしている

**重大度: MAJOR**

**根拠:**

- 規律 3 は、pass/fail でなく構造化した「なぜ」を次 variant の入力に要求する (`CLAUDE.md:71-74`)。
- verifier は実際に cycle/edge/reason を構造化する (`orchestrator/verifier/report.py:15-39,42-75`)。
- しかしプランの constraint atom `r` は「last certified frontier から true→false にした唯一の bit」で決まり、条件は verifier red と anomaly の存在までである (`s2-plan.md:93-103`)。anomaly の edge/reason が `r` を示すこと、または `r` を戻すと同じ anomaly が消えることを要求していない。

従って機械的に証明されるのは「この singleton relaxation を含む candidate が red だった」だけで、「r が failure reason だった」ではない。安全側に探索を狭める no-good cut としては成立するが、failure-reason translator や causal constraint と呼べない。

**成果物影響:** unrelated な anomaly でも atom が永久禁止され、安全だが有望な候補が受理集合から消え、certified winner と材料レポートの「なぜ棄却したか」が誤帰属になる。

## 所見 9 — control WAL の原子性と seal の自己参照が未定義

**重大度: MAJOR**

**根拠:**

- `slot-reserved → query-bound → constraint-added → query-result → tombstone → origin-sealed` は別 record として設計されている (`s2-plan.md:147-157`)。
- 現行 `wal.append()` の flock は一 record の append だけを覆う (`wal.py:283-378`)。counter、hidden C、query result、seal を一トランザクションにしない。
- WAL は hash chain/真正性を持たない (`wal.py:14-15`)。
- `origin-sealed` record 自身に「control WAL bytes/SHA」を入れる案 (`s2-plan.md:155`) は、SHA が seal record を含むのか直前 prefix だけか未定義。前者なら自己参照 hash、後者なら byte cut/ordinal の明記が必要である。
- `records_by_stage()` は last-wins なので control ledger に使えない (`wal.py:586-601`)。プランは順序 validator を提案するが、crash prefix ごとの回復規則を定義していない。

例えば verifier 完了後・`constraint-added` 前に crash すると、slot は消費済みなのに constraint は失われる。逆順なら constraint は増えたのに公開 `query-result` がない。この差を resume 時にどう一意に畳むかがない。

**成果物影響:** `budget.consumed`、constraint state、WAL event count、seal SHA、source refs が互いに食い違い、台帳から certified 選択の完全な proof chain を再構成できない。

## 総括

**(a) 判定: NO-GO**

**(b) BLOCKER: 5 件**

1. effective diff/低エントロピー SHA と未閉包の出力面により、`4.585 bit/window` は上界でない。
2. shared/injected provider が 6-state failure class を planner の 9 記号で一世代伝送できる。
3. trial/config/checkpoint/ledger を変えれば budget を回復でき、campaign-global accounting が成立しない。
4. 親 brief の channel 数・reason bit・既存 enforcement point の三前提がコードで反証された。
5. D116 の主要保証に、逸脱時に実際に赤くなる machine check がない。

**(c) 設計を救う最小変更**

文言修正では足りない。最小の protocol 変更は次の不可分な組である。

1. 軸 (iii) を任意補強でなく必須にし、`Qmax=2` の raw candidate を最初の verifier 結果より前に一括凍結する。
2. origin seal までは effective diff/IR SHA、constraint ID・件数、残予算、source ref、自然文、call/stop topology を全 untrusted role から遮断する。32 canonical emitter は事前監査し、runtime auditor に hidden mask を見せない。
3. budget/C は trial・run-root・config 名から独立した canonical scientific-series key により、削除・rollback できない外部 append-only authority へ置く。certified 経路では injected provider、direct driver、未予約 token を拒否する。
4. 全 failure class と hidden state を反転して planner/coder payload bytes が同一になる noninterference 検査、および trial/config変更・checkpoint/WAL削除・並行 race・第三 query が必ず赤になる境界検査を受入条件にする。
5. translator は当面「failed-singleton no-good cut」と正確に名乗り、構造化 anomaly と atom の causal mapping が機械実証されるまで「failure reason constraint」と呼ばない。

これらが実装・変異検査されるまで、D114 の `MAX_APPROVED_GENERATIONS=1` を維持すべきである。read-only の静的監査のみで、pytest・build・`check_docs.py` は実行しておらず、検査が緑という主張はしていない。