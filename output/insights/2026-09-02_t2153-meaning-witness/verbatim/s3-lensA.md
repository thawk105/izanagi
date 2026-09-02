## 所見

1. **重大度: BLOCKER**  
   **問題:** marker は切り出した条件式が 1/0 で真偽を変えることしか示さず、選択枝の意味を独立期待値と照合しない。例えば `#if IZANAGI_BREAK_PERMUTATION` の本文を `volatile int izanagi_noise = 1;` に置換しても、supply 差、selected=1/0、completed=1/1 がすべて green になり、positive control は何も壊さない。  
   **根拠:** `out/s2-plan.md:70-74,83`。既存 BACKOFF witness は選択だけでなく stock 本文を独立に検査する (`orchestrator/campaign/condition_meaning_gate.py:2018-2028`)。D1242 も独立期待 bits との比較を根拠としている (`rulings-verbatim.md:17-18`)。さらに対象を外側の `#if 0` で包み、別位置に `int noise = SORT_VARIANT;` を置けば supply は差分あり、切出し witness は green、実 owner TU の対象枝は常時不達になる。  
   **成果物影響:** 誤った macro が `unestablished_meaning_macros` から消え、certified 選択・材料レポート・台帳が、意味を持たない枝を green record として参照する。  
   **是正案:** kind ごとに独立な意味契約を設ける。固定 positive control、attribute、REPORT は期待本文または構造を検査し、SORT は EVOLVE-BLOCK との束縛と限定した主張を持たせる。実 owner TU の前処理文脈を保持できないなら、runtime meaning は `unestablished` のままにし、別の compile-time selection 証拠として記録する。

2. **重大度: BLOCKER**  
   **問題:** `MEANING_SUPPORTED_MACROS` の拡張だけで旧 `MeaningWitnessDeclaration` の受理対象も広がり、新 macro を BACKOFF_FIXED decoder で green にできる。これは D1242 が却下した復号器の流用そのものである。  
   **根拠:** 旧 declaration は集合への所属しか検査しない (`condition_meaning_gate.py:379-388`)。評価側は同型 declaration を受けると request macro に関係なく BACKOFF source と decoder を使う (`:2062-2092`)。CLI も集合所属後に旧 declaration を構築する (`:2593-2604`)。計画は集合拡張と型分岐を書くが、旧型を `BACKOFF_FIXED` に再閉包する手順がない (`out/s2-plan.md:75-76`)。  
   **成果物影響:** 従来 CLI/schema が拒否した `SORT_VARIANT` 等の旧型 declaration が受理され、別 macro の観測を参照する偽 green record により未確立一覧が縮む。  
   **是正案:** `MeaningWitnessDeclaration` と旧 evaluator を `macro == "BACKOFF_FIXED"` に固定する。CLI の `--meaning-case` も同 macro だけに閉じ、新型は registry factory 以外から発行させない。旧型で `SORT_VARIANT` を渡す負例を必須化する。

3. **重大度: BLOCKER**  
   **問題:** REPORT witness の companion は実 build の引数ではなく gate 内で再注入されるため、実 build に RUNG1 が無くても witness と supply が RUNG1=1 を観測できる。  
   **根拠:** companion は `DefineSpec` から request へ自動追加される (`condition_meaning_gate.py:150-154,606-615`)。ladder driver は実引数を列挙するが、REPORT=1 のとき RUNG1=1 の実在を要求せず (`silo_ladder_rung1.py:2094-2117`)、両 macro を base args から除去して gate に再構成させる (`:2130-2167`)。計画も両ケースへ companion を強制するだけである (`out/s2-plan.md:73`)。  
   **成果物影響:** REPORT だけを渡した実 build が admission を通り、ladder の材料レポートと台帳が、実際には footer を compile-in していない build を green record ID で参照できる。  
   **是正案:** driver 境界で実 `CMAKE_CXX_FLAGS` に REPORT=1 と RUNG1=1 が各一度あることを先に要求する。meaning argv は registry の別値ではなく、検証済み request の effective companions からのみ作り、evidence/schema に exact companion 集合を束縛する。

4. **重大度: MUST-FIX**  
   **問題:** `IZANAGI_BREAK_TRIGGER_MISATTR` の除外理由は誤りで、defined/undefined は契約の読み替えではなく実 build の対である。現行 gate の default=0 は `#ifdef` の両側を真にするため、静的には meaning 以前に supply が identical/red になる。  
   **根拠:** patch は `#ifdef` (`broken-silo-trigger-misattr.patch:9`)。実 build は positive control のときだけ `-D...=1` を追加する (`s8a_trigger_coverage.py:181-199`) が、gate request は default=0 とする (`:99-114`)。計画の「undefined は D1404/D1405 違反」という記述は `out/s2-plan.md:105,151`。D1404 は実 build 引数を変えないことを要求する (`rulings-verbatim.md:82-89`)。  
   **成果物影響:** 現状の s8a 材料は「未確立」ではなく gate 拒否になり得る。definedness witness を採れば新規 green は 14 件、残りは 7 件となるため、計画の 14/22 と除外台帳の値も変わる。  
   **是正案:** `default_value=None` の definedness witness として実 build 対を表現するか、本 wave では「別 witness kind が必要」として正しく繰り延べる。どちらを採るか裁定対象にする。

5. **重大度: BLOCKER**  
   **問題:** factory を配線する consumer が網羅されておらず、同じ macro が driver ごとに green と unestablished に分裂する。逆に計画対象の `s8a_trigger_coverage.py` は新規 13 件を一つも扱わないため、その編集は一覧を縮めない。  
   **根拠:** 計画の配線範囲は `out/s2-plan.md:77-79`。未配線は `backoff_sweep.py:131-149`、`screening_driver.py:173-176`、`p3_s4_loop_sort.py:130-134`、`s6_sort_sweep.py:231-235`、`paper_story_a2_certification.py:555-580`、`tools/pegasus/probes/t1683_rr5_cost_probe.py:167-175,203-206`、CLI `condition_meaning_gate.py:2593-2604`。s8a が扱うのは除外予定の `BACKOFF_TRIGGER_GATING` と MISATTR だけ (`s8a_trigger_coverage.py:150-165`)。  
   **成果物影響:** S1/S8b では SORT_VARIANT が green でも、sort loop・sort sweep・screening の台帳では同じ request が未確立のままになる。BACKOFF_NOINLINE も paper と cost probe に残り、成果物全体の未確立一覧は計画どおり縮まらない。  
   **是正案:** factory-supported request を発行する全 call site を閉包として列挙し、全て配線する。凍結・承認済み driver を直接変更できない面は repin せず、後継発行か「その成果物では未確立を維持」の裁定パッケージへ分離する。

6. **重大度: MUST-FIX**  
   **問題:** 「compile-time selection 限定」という境界が schema と文言へ落ちていない。現状の arm、reason、module 文言では positive control の動的 anomaly まで確立したように読める。  
   **根拠:** record は `runtime-meaning` / `green` / `declared-meaning-observed` となる (`condition_meaning_gate.py:2131-2135`)。module は meaning arm が runtime semantics を供給すると記す (`:2-15`)。計画は `positive-control-branch` 等の名前と hash を追加するだけ (`out/s2-plan.md:43,74`) で、境界明記は未解決事項に留まる (`:150,153`)。また配線後も `DRIVER_INTEGRATION = "none"` の更新手順がない (`condition_meaning_gate.py:173`)。  
   **成果物影響:** admission 値が同じでも、材料レポートと台帳の green record が「異常発火を確認済み」と誤読され、proof kind と参照先の主張範囲が一致しない。  
   **是正案:** evidence に固定語彙の `claim_scope` を追加し、proof kind と reason を compile-time conditional selection に限定する。positive control は「anomaly 未検査」を構造化して残し、module 文言、driver integration、成果物表示も同時に更新する。

## 親 brief の誤り

1. P1-b の「健全に観測できる」は、切り出した predicate の真偽についてだけ成立し、枝本文や実 owner TU の選択については成立しない (`handoff.md:106-110`)。
2. P1-c の「第一群は 11 件」は誤りで、MISATTR は 1/0 witness にならない。ただし実際の対は defined/undefined なので、単純な除外理由も誤りである (`handoff.md:111-112`)。
3. P1-d の「S1 一関数で足りる」は誤りであり、計画自身も訂正している (`handoff.md:113-114`, `out/s2-plan.md:149`)。
4. `capture_define_inputs` が patch 適用済み source を保証するという一般化は誤りである。`stock_root` は任意で、同一拒否は渡された場合だけである (`handoff.md:71-74`, `condition_meaning_gate.py:545-578`)。各 driver の適用位置は別に証明する必要がある。
5. `SS2PL_WFG_DIAG` が「5 箇所」という実測は誤りである (`handoff.md:82`)。`ss2pl-lock-protocol-study.patch` には同 macro を含む追加条件指令が静的に 63 行あり、単一枝 witness を除外する結論自体は維持されるが根拠値が違う。
6. 起動時の worktree 数・重複 0 と compiler 実測は再実測していない。今回確認したのは指定資料と repo の静的内容だけであり、pytest と compiler witness は実走していない。

## 見落とされた層

- 公開 API/CLI の declaration dispatch と旧型の閉包。
- generic screening の raw evidence。
- `backoff_sweep` を共有する profile/repro 系と、paper A2、T1683 cost probe の BACKOFF_NOINLINE evidence。
- P3 sort loop と S6 sort sweep の certified/raw SORT_VARIANT evidence。
- module doc、proof kind、reason code、claim scope、driver integration、材料レポート表示。
- 裁定パッケージ候補は、compile-time selection を D1403 の meaning green と認めるか、MISATTR の definedness witness を本 wave に含めるか、凍結・承認面には後継発行を作るかの 3 件である。これらは裁定前に実装や repinをしてはならない。

## 総括

BLOCKER は 4 件。  
marker 観測だけでは、計画が成果物から除く「意味未確立」を置換できない。  
旧 declaration、companion、consumer 閉包を修正し、主張境界を裁定してから再レビューが必要である。  
このプランのまま実装してはならない。