## 所見

1. **blocker — series key 変更が mixed-generation genesis の受理を広げる。** `plan-v1.md:58,81,102`、`orchestrator/campaign/attempt_registry_core.py:483-503,726-734`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1323-1349`  
   全 slot の世代一致は writer にしか置かれていない一方、reader は任意の committed JSON を replay する。series key に世代を加えると、同じ既存 series に generation 13/14 の `attempt_index=0` を各1件置いた形が別 series として通り、production selector も世代を選別しない。v3 の全 reader に root-wide な単一世代検査を置く必要がある。  
   放置時: v2 で拒否された重複 series が load、compatibility、launch 層で受理され、formal 発行前に別世代 slot を実行できる。

2. **must-fix — high-level issuer に「全 unit 消費」の受理穴があるという前提は誤り。** `plan-v1.md:14-16,140,155`、`orchestrator/campaign/trial_registry.py:1622-1639,3495-3535,5685-5686,5737-5739,6112-6119`、`orchestrator/campaign/autonomous_trial_completeness.py:2886-2911,3215`  
   outer acceptance は既に、6 report、manifest の exact trial 集合、genesis の6 initial unit、各 report に対応する一意の terminal を合成検査する。accepted report の status は `complete` または `partial` に固定され、terminal は `observed` または `terminal-failure` になる。新 helper が純増するのは、production caller の無い lower-level formal API の無 report 経路と拒否理由であり、outer receipt の受理集合ではない。  
   放置時: 成果物が新しい best-of-N 防壁を追加したと誤記され、実際には既存拒否の別実装だけになる。

3. **must-fix — `prereg_generation` 欠落を世代選別の実在経路とする根拠がない。** `orchestrator/campaign/trial_registry.py:798-810,1437-1462,1492-1509,3455-3494,4046-4063`、`orchestrator/campaign/s8c_preregistration.py:1957-1961`  
   generation は manifest の `prereg_commit` から一意に再導出され、その manifest bytes と genesis は P/C に束縛済みである。別 generation は manifest hash、P/C、canonical genesis のいずれかを変え、現行 formal path で拒否される。明示 field は D1269 の表示上の実験単位にはなり得るが、新しい意味束縛とは立証されていない。  
   放置時: 冗長 field を足して同一 repo の穴を閉じたと報告する一方、実在する独立 repo 境界は変わらない。

4. **must-fix — `not-consumed` を混ぜた high-level 正例は到達不能。** `plan-v1.md:117,154,178`、`orchestrator/campaign/attempt_registry_core.py:977-983`、`orchestrator/campaign/p3_autonomous_workload_trial.py:4163-4174`、`orchestrator/campaign/trial_registry.py:3540-3548`  
   `not-consumed` は `report_sha256=null` が必須だが、report status `partial` は `terminal-failure` を要求し、formal report 照合は report hash の一致も必須とする。既存分岐を保ったまま `not-consumed` が receipt 発行へ到達する正例は作れない。  
   放置時: 正例が失敗するか、通すために既存 status/hash 拒否を弱めて受理集合を広げる。

5. **must-fix — v2 read/replay 保持には schema 分岐の改修が不足している。** `plan-v1.md:51-52,62`、`orchestrator/campaign/trial_registry.py:2288-2292,2321-2335`  
   現行コードは「schema が current なら v2、そうでなければ v1」と分岐する。current を v3 に替えるだけでは v2 receipt を v1 key set と legacy 意味で検査し、既存 v2 artifact を拒否する。schema ごとの明示 map が必要である。  
   放置時: 読取用に残すとした v2 の参照可能集合が失われる。

6. **must-fix — classification receipt 内の新 field を capability と照合する計画がない。** `plan-v1.md:52,60`、`orchestrator/campaign/trial_registry.py:2303-2331`  
   receipt に `prereg_generation` を足しても、現在の verifier は receipt と classification row の同 fieldを比較しない。capability digest は正しい generation を束縛していても、receipt 自身には別値を記録できる。field を置くなら exact 一致を要求し、置かないなら digest からの導出値だと固定すべきである。  
   放置時: 同一 receipt が generation 13 の capability digest と generation 14 の表示値を同時に持って検証を通り、参照が二義化する。

7. **nit — 新しい空集合拒否は integrated formal 経路では到達しない。** `plan-v1.md:98,102,158`、`orchestrator/campaign/attempt_registry_core.py:496-497,726-734`  
   helper は strict replay 後に呼ばれるため、空 genesis は既存 core で先に拒否される。helper 単体の負例は恒真防止の防御的テストとしては有効だが、production gate の発火証拠にはならない。  
   放置時: 受理集合は変わらないが、新 gate が production で空集合を拒否したという説明だけが不正確になる。

8. **blocker — 「下流」が receipt verifier を含むか未確定である。** `plan-v1.md:108,148,168`、`orchestrator/campaign/s8c_acceptance_receipt.py:45-87,1151-1160`  
   案が効くのは outer receipt の発行時だけであり、receipt schema は attempt registry の path、prefix、slot projection、generation を持たない。後続 verifier は manifest、trial registry、lifecycle しか再検査できない。  
   放置時: 発行時検査は増えるが、後続 consumer が predeclared receipt の全列挙と消費を独立検証できないまま「下流を実装済み」と扱われる。

## プラン v1 の判定

作り直し。series key による受理拡大と、到達不能な `not-consumed` 正例がある。  
既存 high-level completeness、generation の既存導出束縛、issuer と verifier の境界を分けて再設計する必要がある。

## 親 brief の誤り

- P1 は誤り。条件凍結 record は generation の出所で、slot/count の正本は manifest、P側 genesis、C binding の合成である。`orchestrator/campaign/s8c_preregistration.py:81-98`、`orchestrator/campaign/trial_registry.py:122-126,743-790,1451-1462`
- P2 は誤り。ただしプラン v1 の「明示 field 欠落が残存経路」という置換も未立証である。`orchestrator/campaign/trial_registry.py:1492-1509,2510-2561,3455-3494`
- P3 は `observed`、`terminal-failure`、`retryable-failure` の区別までは正しいが、`not-consumed` を formal receipt 発行可能な final consumption とした部分が現行契約と合わない。`orchestrator/campaign/attempt_registry_core.py:952-983`、`orchestrator/campaign/trial_registry.py:3540-3548`
- P4 は支持できる。既存 g1..g13 を変更せず、activation report から generation を取得できる。`orchestrator/campaign/s8c_preregistration.py:1957-1961`
- A3 の root exact key 集合は不完全な記載で、schema、event、freeze、manifest、chain fields を落としている。`orchestrator/campaign/trial_registry.py:140-171`
- A7 と A9 の現物自体は正しいが、「専用関数がない」ことから「outer acceptance に全件保証がない」への一般化が誤り。`docs/phase3-8c-preregistration.md:497-501`、`orchestrator/campaign/trial_registry.py:5685-5686,5737-5739,6112-6119`
- A1、A2、A4からA6、A8は現物と一致した。A10 も filesystem listing では一致したが、不存在のため file:line 根拠なし。
- DW-G05 の「certified 選択」への即時影響は誤り。receipt は常に non-certifying で、certifying consumer は存在しない。`orchestrator/campaign/s8c_acceptance_receipt.py:420-428`、`orchestrator/campaign/layer3_report.py:682-703`

## 裁定へ返すべき項目

- D1269 の「下流」を outer issuer までとするか、`verify_acceptance_receipt` の独立再検査まで含めるか。
- `not-consumed` を report の無い最終消費として formal acceptance 可能にするか。可能にするなら既存 report-count、status、hash 契約の改訂が必要。
- 「承認 artifact」を P/C で固定された事前登録 artifact と読むか、人間承認 authority と読むか。後者は現行の発効設計と衝突する。`docs/phase3-8c-preregistration.md:300-315`
- production genesis producer が0件のまま library APIだけを production 実装と数えるか。`plan-v1.md:126-146`
- `replicate_index>0` と独立 clone/repository を今回閉じないこと。前者は現行受理集合を広げ、後者は repository 単位の保証を超える。`orchestrator/campaign/trial_registry.py:3504-3509,4457-4461`

## 総括

プランは D539 の独立期待値と空集合防御の方向自体は守っている。  
`prereg_generation` は LLM の `generation` / `source_generation` と別名で、直接の名前衝突は見つからない。  
一方、series key の変更は reader 側の単一世代検査なしでは受理集合を広げる。  
outer issuer の全6 unit消費は既に合成的に強制されており、純増という説明は成立しない。  
検査が新たに効くのは lower-level formal APIと発行時だけで、receipt verifier、certifying consumer、独立 repository には効かない。  
pytest は実行しておらず、以上は静的検査による判定である。