## 所見 1 — 段 2 プランは依頼を達成しない

**判定: real / 重大度: Critical**

現状は `_batch_oids` が全要求を一度に渡し、`_git` が 15 秒で `git-timeout` にする構造である。実際、同じ candidate が全走負荷下でここに到達して落ちている。段 2 案は要求を減らさず、並列化もせず、4 個の subprocess に順次分割したうえで同じ 15 秒締切を共有するだけである。process 起動と pack/index 再初期化が増えるため、速くなる証拠がないだけでなく遅くなる側の変更である。

さらに brief は「今日 reject される入力も同じく reject」と要求する一方、この candidate を成功させようとしている。wall-clock を受理条件に含める限り、これは文字どおり両立しない。両立方法は、負荷下で 15 秒未満になる実測済み高速化、実行環境の隔離、または timeout 方針の変更のいずれかであり、段 2 案はどれも立証していない。

根拠:

- `s1-brief.md:7-13,60-75`
- `s2-plan.md:28-44,97-109,240-254`
- `orchestrator/campaign/s8c_preregistration.py:87-94,880-901,1102-1113,1310-1327`
- `orchestrator/tests/test_s8c_preregistration_invariant.py:124-131`
- `acceptance-baseline.txt:124-225`
- 追加予定テストも fake Git と fake clock の検査だけで、負荷下の高速化は検出しない: `s2-plan.md:157-178`

**成果物影響:** 無視すると、段 8c の `condition_freeze_valid` は負荷時に `False`／`freeze_reason_code="git-timeout"` のままになり、受入全走も同 nodeid の `1 failed` を閉じられない。

## 所見 2 — (P1)(P2) は条件付きなら両立するが、その条件を満たす証拠がない

**判定: real / 重大度: High**

形式上の必要条件は次である。

```text
分割後の全 chunk 処理時間 + 追加 process 起動費
    < 15 秒
    <= 現在の単一 batch 処理時間
```

例えば単一 invocation に超線形な劣化があり、chunk 化による節約が追加起動費を上回るなら両立する。しかし現コードは既に `cat-file --batch-check` の batch mode で起動費を全要求へ償却している。段 2 案はこれを逐次 4 process に分けるので、上記条件は未証明である。

現在の裁定を維持するなら、まず捨てるべきは P1 の chunking である。そのうえで親は、P2 の「固定 15 秒」を C の bounded proportional budget に改めるか、固定 15 秒を守って D で未解決終了するかを選ぶ必要がある。P1 を実装してから受入で賭けるべきではない。

根拠:

- P1/P2: `s1-brief.md:68-75`
- 現在の単一 batch: `orchestrator/campaign/s8c_preregistration.py:1109-1113`
- 計画上の逐次 chunk と共有 deadline: `s2-plan.md:28-44,101-109`
- 計画自身も遅延可能性を認める: `s2-plan.md:238-244`

**成果物影響:** 条件未立証のまま進めると、段 8c の発効値は改善しないか、追加 overhead により以前より多く `git-timeout` となり、受入全走の緑率が下がり得る。

## 所見 3 — 親の実測からの一般化は成立しない

**判定: real / 重大度: High**

個別主張の判定は次のとおり。

- 「全走下で 15 秒を超えた」: **real**。これは warm 値からの推論ではなく、失敗逐語による直接観測である。
- 「2286 要求・1 path の 0.690 秒から、3 path は約 2 秒」: **refuted**。path ごとの tree walk、object/pack 状態、同一 process 内の cache 再利用を一定と仮定した未実測換算である。
- 「10,000 commit なら約 9 秒」: **refuted**。warm login node、単独 process、現 repo の pack/cache 状態を線形外挿しており、cold cache・計算ノード・共有 filesystem・48-worker 競合を含まない。
- 「作業量は履歴長に比例」: **条件付きのみ real**。実際の batch cardinality は `commits × paths` であり、generation が増えれば path 数も増える。さらに `_commit_graph`、namespace scan、blob batch は別の仕事である。
- 「`MAX_BATCH_REQUESTS=50_000` と固定 15 秒は論理的に自己矛盾」: **refuted**。件数 cap と時間 cap は独立した conjunct であり、50,000 以下を必ず完走させる契約はコードにない。ただし、現在の 6,861 要求ですら繰り返し落ちるため、運用方針としての不整合は real である。

根拠:

- warm 測定と外挿: `s1-brief.md:34-47`
- 要求数は積: `orchestrator/campaign/s8c_preregistration.py:1102-1113`
- path 数は generation 数に依存: `orchestrator/campaign/s8c_preregistration.py:1317-1326`
- 履歴走査は別 operation: `orchestrator/campaign/s8c_preregistration.py:1063-1099`
- 直接の 15 秒超過: `acceptance-baseline.txt:124-225`

**成果物影響:** この外挿で budget/chunk 幅を決めると、過小なら発効判定と受入赤が残り、過大なら根拠なく wall-clock gate の受理範囲を広げる。

## 所見 4 — 代案 B は test fixture hardening ではなく、test 経由の production gate 緩和である

**判定: real / 重大度: Critical**

どちらか一方に倒すなら、**B は抜け道である**。

[T-327] の 180 秒は、候補 commit を作るテストローカル `_git_text`、特に `git add -A` の fixture 構築にだけ使われる。production validator の timeout を選べるようにはしていない。一方 B は、production の公開 `validate_condition_freeze_at` に caller-controlled timeout を追加する。既定値が 15 のままでも、`validate_condition_freeze_at(repo, commit, timeout=10**9)` で wall-clock guard を迂回できる。内容・hash・generation guard までは無効化しないが、「15 秒を超えたら fail-closed」という資源防壁は失われる。

検出力も落ちる。

- `test_candidate_freeze_matches_contract_and_generation_chain` は現在、実 repo を production 既定値で成功させる唯一の直接 assert である。180 秒を渡せば、production の 15 秒が実 repo で機能するかを検出しなくなる。
- `test_candidate_is_not_effective_and_has_zero_satisfied_predicates` は代替にならない。`_activation_report_at` は `git-timeout` を捕捉して `condition_freeze_valid=False` に変換し、同テストはもともと `effective is False` を期待しているため、production timeout が起きても緑になり得る。
- core の timeout テストは人工的な `TimeoutExpired` が `git-timeout` へ写ることしか確認せず、実 repo が 15 秒で完走することを検査しない。

根拠:

- T-327 型の test-local timeout: `orchestrator/tests/test_s8c_preregistration_invariant.py:28,43-64,76-100`
- F57/T-327 の記録: `docs/failures.md:1349-1362,1387-1395`
- 現在の production signature: `orchestrator/campaign/s8c_preregistration.py:1310-1313`
- timeout を無効状態へ変換する経路: `orchestrator/campaign/s8c_preregistration.py:1544-1549,1576-1587`
- 検出を失う nodeid: `orchestrator/tests/test_s8c_preregistration_invariant.py:124-161`
- 補償しない nodeid: `orchestrator/tests/test_s8c_preregistration_invariant.py:190-203`
- 模擬 timeout テスト: `orchestrator/tests/test_s8c_preregistration_core.py:947-984`

**成果物影響:** B では受入全走を緑に見せながら、同じ commit の production 発効判定は `condition_freeze_valid=False`／`effective=False` のままという不一致を作れる。

## 所見 5 — C は形式上 gate 緩和だが、段 2 案より整合した解決候補である

**判定: real / 重大度: High**

C は「既存 gate を一切緩めない変更」ではない。要求数 `R` に対して `B(R)>15` となる領域では、従来 15 秒で拒否された実行が成功するため、wall-clock 受理集合は明確に広がる。したがって「`MAX_BATCH_REQUESTS` との自己矛盾を直しただけ」として無裁定で入れてはならない。

一方、段 2 が C を退けた直接理由――「履歴が長いほど旧 15 秒 gate を緩める」――自体は事実だが、そこから chunking を採る結論は成立しない。固定 15 秒を守って赤を閉じる性能証拠がない以上、正しい帰結は段 4 への政策差し戻しである。

C は次の条件なら最も防御的である。

- budget は caller 引数にせず、実要求数から内部で一意に算出する。
- 旧 logical invocation 全体に 1 deadline を置く。
- `MAX_BATCH_REQUESTS` 相当点で絶対時間 cap を設ける。
- rate は warm 0.690 秒の線形外挿で決めず、cold/contended compute 条件から事前裁定する。
- invariant テストは引数を渡さず production と同じ計算式を通す。

これなら内容・size・hash・generation の検出力は落とさず、時間防壁も有限のまま保てる。

根拠:

- 固定値と上限: `orchestrator/campaign/s8c_preregistration.py:87-94`
- workload cardinality: `orchestrator/campaign/s8c_preregistration.py:1105-1113`
- C の不採用理由: `s2-plan.md:97-109`
- brief の現行不変条件: `s1-brief.md:58-63`

**成果物影響:** C を裁定対象に戻さず退けると、段 8c の正しい候補が負荷依存で `git-timeout` となる状態と、受入全走の再発赤が残る。

## 所見 6 — D は帰属判断として正しいが、修正案としては不成立

**判定: real / 重大度: High**

`DW-O18` は「今回の無関係な差分の回帰ではない」と分類する規則であって、既知の赤を放置して完了扱いする規則ではない。再発回数の増加は二方向に働く。

- **強めるもの:** 個々の wave 差分への非帰属、F57 型の共有資源競合という分類。
- **弱めるもの:** 「今回も記録だけでよい」という判断。反復により偶発的単発ではなく、受入と発効判定の恒常的な可用性欠陥である確率が上がっている。

したがって D は、固定 15 秒を変更する権限が得られない場合の正直な停止案としては成立する。しかし「すべて直す」「受入全走を緑にする」を達成したとは記録できない。

根拠:

- `DW-O18`: `docs/dev-wave/operations.md:99-104`
- 同一 s8c node の反復: `docs/failures.md:1387-1412,1426-1437,1464-1475,1510-1525`
- F57 は未閉鎖: `docs/failures.md:1489-1492`
- T-553 は族としての修正を要求: `docs/archive/worklog-phase3-0806-248.md:360-363`

**成果物影響:** D を選ぶと段 8c は負荷時に `freeze_reason_code="git-timeout"` のまま、受入全走も次回以降 `1 failed` が再発し得て、緑は保証されない。

## 総括

### (i) GO / NO-GO

**NO-GO。段 2 プランを段 5 へ渡してはならない。**  
chunking が全走負荷下で 15 秒未満になる証拠がなく、プラン自身が依頼達成不能と認めている。段 4 へ差し戻し、timeout 方針を裁定し直す必要がある。

### (ii) 4 案の推奨順位

1. **C — 条件付き第 1 推奨**

   caller-controlled seam を作らず、production/test 共通の bounded budget として設計できる。  
   ただし固定 15 秒の明示的な政策変更なので、brief の不変条件を親が撤回してから進める。

2. **D — 第 2 推奨、停止案**

   防壁も検出力も壊さず、未解決を未解決のまま正直に返せる。  
   依頼と受入緑は達成しないため、完了ではなく裁定待ち終端に限る。

3. **段 2 プラン — 第 3 位**

   15 秒 cap は維持するが、逐次 process 増加が赤を閉じる証拠がなく、むしろ悪化し得る。  
   fake clock の追加テストが緑でも、依頼の load-dependent failure には何も証明しない。

4. **B — 最下位**

   test fixture ではなく production validator に長時間実行 capability を足し、public gate を迂回可能にする。  
   受入を緑に見せつつ production 発効値を false のまま残せるため、防御目的では最も危険である。

### (iii) 親が裁定すべき択一

- 「受理集合」は内容上の semantic input だけか、wall-clock を含む運用結果か。後者なら赤閉鎖との同時達成は不可。
- 固定 15 秒を絶対維持して D で停止するか、C の capped proportional budget を明示的に採用するか。
- public `validate_condition_freeze_at(timeout=...)` seam を禁止するか。推奨は**禁止**。
- chunking は全走相当の contention 条件で速度改善を実測してから再提案させるか。推奨は**実測前には不採用**。
- C を採る場合、budget の基準を request 数だけにするか、input bytes 等も含めるか、および絶対 cap を何秒にするか。

`dev-wave` 段 3 契約に従い、plan だけでなく親 brief・親実測の一般化も攻撃対象に含めた。静的レビューのみで、pytest は実行しておらず、緑は主張しない。