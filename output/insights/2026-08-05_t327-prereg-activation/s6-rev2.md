テストは実行していない。以下は `git status`、全差分、指定ファイル、関連正本・全体走査規則を読んだ静的レビューである。指定一覧外に、新規 `output/s8c-preregistration/condition-freeze.v1.g1.json` も存在する。

## 所見

### 1. 任意の registry 注入で発効 capability を偽造できる

**主張:** `effective_at()` が caller 提供の `registry` を受け入れるため、正式 evaluator・証拠契約を迂回して全 C01〜C12 を `SATISFIED` にできる。さらに seal を持つ `_construct_effective` 自体も module global である。

**根拠:** 注入 registry は無条件で評価に使われる (`orchestrator/campaign/s8c_preregistration.py:1241-1267`, `:1293-1300`)。seal 付き constructor は module 属性として保持される (`同:230-236`)。テスト自身が偽 registry を定義し (`orchestrator/tests/test_s8c_preregistration_core.py:164-173`)、schema 不正な evidence contract (`同:89`) でも有効 capability を生成している (`同:524-532`, `:544-551`)。

**具体的な反例:** §5 を canonical JSON で埋め、g1 だけを用意して `effective_at(root, C, registry=_Registry(SATISFIED))` を呼ぶ。evaluator module や実証拠がなくても非 `None` が返る。別経路として、`effective=True` の `ActivationReport` を作り `_construct_effective(report)` を直接呼べる。

**重大度:** `blocker`

**成果物影響:** 将来 launcher がこの capability を信頼すると、12 条件を一件も実証していない trial が formal admission に入る。

**提案修正:** 公開 `effective_at()` から registry 注入を削除する。テスト用注入は capability を返さない private report helper に隔離する。formal consumer は Python オブジェクトの型を信用せず、信頼境界内で commit と証拠を再導出する。

### 2. SATISFIED 判定が実効保証ではなく、名前・文字列の存在検査になっている

**主張:** machine-checkable 6 述語は、dead code・no-op・文字列 tuple だけで green になる。JSON が約束する field、consumer、proof の意味は Python evaluator によって検証されていない。

**根拠:** 例えば C10 は field 名文字列と `read_and_verify_bytes` 呼出名だけを見る (`orchestrator/campaign/s8c_preregistration_evidence.py:481-495`)。JSON は「全 byte stream を読み直し formal acceptance 前に束縛する」と要求する (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:336-375`)。ところが green fixture は field 名の tuple と no-op 関数だけで (`orchestrator/tests/test_s8c_preregistration_predicates.py:229-246`)、テストはこれを `SATISFIED` と認定する (`同:382-396`)。C04/C09 も同型 (`同:199-227`; evaluator `:435-460`)。

三重正本は、文書の12条件 (`docs/phase3-8c-preregistration.md:101-127`)、JSON の `field_paths/reachable_from/consumer_requirement`、Python の hard-code evaluator (`orchestrator/campaign/s8c_preregistration_evidence.py:586-596`) に分裂している。JSON の詳細は parse・保持されるだけ (`同:205-260`) で、個別 evaluator はその宣言内容を消費しない。

**具体的な反例:** `verify_s8c_cross_binding()` 内に必要な12文字列を置き、`if False: read_and_verify_bytes()` を追加する。実 byte は一切読まず、acceptance も強制しないが C10 は green になる。同じ手口で crash handler や Layer 3 gate も恒真化できる。

**重大度:** `blocker`

**成果物影響:** 残りの述語が green になった時点で、proof chain・crash・cross-binding が未実装でも発効レポートが true になり得る。

**提案修正:** JSON を evaluator の実入力にし、宣言した全 field/path/entrypoint が検査されたことを機械照合する。単なる AST 名探索ではなく、production entrypoint の戻り値・例外経路・byte dereference を実証する負例を置く。少なくとも dead branch、no-op、未使用文字列を green にしない反例を追加する。

### 3. g2 以降の「人間裁定必須」は、裁定 ID の文字列があれば通る

**主張:** 人間が変更を承認したことではなく、canonical ledger のどこかに `T-N` / `DN` が出現することしか検査していない。

**根拠:** 親裁定は g2 以降に人間 ruling を必須とした (`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s4-ruling.md:25`)。実装は単語境界 regex で全 ledger blobを検索し、1 hit で成功する (`orchestrator/campaign/s8c_preregistration.py:968-995`)。テスト fixture も任意の一行を追記するだけである (`orchestrator/tests/test_s8c_preregistration_core.py:149-153`)。

**具体的な反例:** 正しい worklog entry に「`T-999` は未裁定／却下」と書き、条件を弱める g2 の `ruling_reference` を `T-999` にする。regex は hit し、g2 は有効と判定される。

**重大度:** `blocker`

**成果物影響:** 人間未承認の条件緩和が正規世代として受理され、同じ ledger から発効集合を拡大できる。

**提案修正:** 構造化された裁定 record を定義し、`approved` 状態、対象 generation、旧新 protected hash、裁定主体を exact に検証する。単なる本文 token 検索を authorization に使わない。

### 4. invariant test は commit 前に必ず赤になり、dev-wave の順序とデッドロックする

**主張:** 段6の受入は commit 前なのに、新規 invariant は worktree/index ではなく `HEAD` に g1 と全 wave file が存在することを要求する。

**根拠:** 実装子は commit しない (`docs/dev-wave/workers.md:26-30`)。段6で親が受入を再走する (`同:64-67`) 後、段7で commit する (`.claude/commands/dev-wave.md:50-52`)。しかし invariant は `HEAD` の freeze を検証し (`orchestrator/tests/test_s8c_preregistration_invariant.py:64-75`)、全新規 path が `HEAD` にあることを要求する (`同:109-113`)。

**具体的な再現手順:** 現状の差分を `git add -A` しても `HEAD` は `23e4363` のままである。この状態で親が段6受入を実行すると、g1 は `HEAD` に存在せず `freeze-missing`、さらに `WAVE_REQUIRED_PATHS <= head_paths` も不成立になる。commit しない限り green にならない。

**重大度:** `blocker`

**成果物影響:** 親は「受入済み commit」を作れず、未検査 commit を作るか dev-wave 状態機械を破るかの二択になる。

**提案修正:** staged/worktree 差分から一時 repository に candidate commit を合成して履歴検査する。commit 後 invariant は段7の別検査に分け、段6の full suite が未 commit 差分でも成立するようにする。

### 5. `effective_at(C)` は C の evaluator を実行せず、履歴再評価と CLI import が不安定

**主張:** 文書は「C 時点の git blob だけ」と主張するが、実装は現在 checkout の Python module と現在の core を実行する。evaluator 更新後は旧 C を再評価できず、import 名が異なると型も二重化する。

**根拠:** 文書の約束は `docs/phase3-8c-preregistration.md:141-143`。実装は C の evaluator blobを読む一方、実際には live module を `importlib` でロードし (`orchestrator/campaign/s8c_preregistration.py:1183-1217`)、その module object を実行する (`同:1221-1229`)。evidence 側も import 名に応じて別 core を読み得る (`orchestrator/campaign/s8c_preregistration_evidence.py:18-21`) が、結果は現 core の nominal class でなければ拒否される (`orchestrator/campaign/s8c_preregistration.py:1163-1179`)。green predicate テストは production default 経路でなく registry を直接呼ぶ (`orchestrator/tests/test_s8c_preregistration_predicates.py:59-61`, `:382-396`)。

**具体的な反例:** C1 の後に evaluator module を正当に更新し、現在 checkout から `effective_at(C1)` を呼ぶ。live bytes と C1 blob が違うため全件 `ERROR` になる。逆に core だけ変更すると evaluator blob 比較は通り、同じ C1 が新しい core 意味論で再評価される。`__main__`／`campaign.*`／`orchestrator.campaign.*` の混在では別 `PredicateResult` class が生じ、同様に全件 ERROR となり得る。

**重大度:** `must-fix`

**成果物影響:** 過去の有効 prereg commit が checker 保守後に拒否されたり、同じ C の発効意味が caller の checkout により変わる。

**提案修正:** C の隔離 checkout から evaluator と依存 core を一体で実行するか、versioned interpreter trust root を固定する。少なくとも default API と実 CLI の green E2E、後続 evaluator/core commit から旧 C を再評価するテストを追加する。

### 6. 事前登録した最重要変異 `all → any` がテストに殺されない

**主張:** 親が要求した `test_effective_requires_all_twelve` が存在せず、`all()` を `any()` に変えても新規テスト集合は赤にならない。

**根拠:** m01 は明示的に登録されている (`/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/s4-ruling.md:71-74`)。実装の conjunction は `orchestrator/campaign/s8c_preregistration.py:1275-1279`。core test は12件すべて同じ非充足 status のケースしか持たず (`orchestrator/tests/test_s8c_preregistration_core.py:486-501`)、正例も12件すべて SATISFIED である (`同:524-532`)。

**具体的な反例:** `all(...)` を `any(...)` に変更する。全件 false の各テストは引き続き false、全件 true は引き続き true、現行 repo の zero-satisfied invariant も false のままである。

**重大度:** `must-fix`

**成果物影響:** 将来最初の1述語だけが green になった時点で、不完全な preregistration が effective になる回帰を受入 suite が見逃す。

**提案修正:** 「1件 SATISFIED + 11件非充足」と「11件 SATISFIED + 各 status の1件非充足」を明示的に false とするテストを追加する。

### 7. §5 の「記入済み」は `null` や `"未記入"` でも通る

**主張:** canonical JSON であれば意味的な空値をすべて `FILLED` と分類するため、placeholder 検査を code span で迂回できる。

**根拠:** raw placeholder を先に見るが、その後は canonical JSON かしか検査しない (`orchestrator/campaign/s8c_preregistration.py:585-604`)。文書は全欄が placeholder でない記入済み値であることを要求する (`docs/phase3-8c-preregistration.md:137-139`)。テストは裸の `未記入` と arbitrary text だけで、canonical `null`・空値・placeholder string を扱わない (`orchestrator/tests/test_s8c_preregistration_core.py:297-306`)。

**具体的な反例:** 9欄をすべて `` `null` ``、または `` `"未記入"` `` で埋める。いずれも canonical JSON なので全件 `FILLED` になる。

**重大度:** `must-fix`

**成果物影響:** budget、floor、manifest、seed、環境が実質空でも「§5 記入済み」として発効式の一項を通過する。

**提案修正:** 欄ごとの型・必須 field・非空条件を schema 化する。少なくとも `null`、空文字列・空集合、placeholder 相当文字列を拒否する負例を追加する。

### 8. 祖先関係について文書内・D116・JSON が矛盾している

**主張:** §1 は発効 commit が結果 commit の祖先であることを要求する一方、新規文は「祖先であることではない」と否定する。C08 の証拠契約も ancestry 検査を要求している。

**根拠:** 祖先要件は `docs/phase3-8c-preregistration.md:27-29` と前提条件8 (`同:118`)。新規文は `同:35-37`。D116 も ancestry を正本とする (`docs/decisions.md:5499-5502`)。JSON C08 は acceptance で ancestry verification を要求する (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:268-301`)。

**具体的な反例:** 結果 commit R を先に作り、その後の非祖先 commit C で§5と全機構を整えて `effective_at(C)=true` にする。新規文だけを読めば R が C を参照して受理できるが、D116・§1・C08 では拒否される。

**重大度:** `must-fix`

**成果物影響:** 後付け preregistration を trial ledger が受理するかが、どの正本を読んだかで反転する。

**提案修正:** 「C で effective であること」と「C が measurement HEAD／結果 commit の祖先であること」の両方を必須にする。「ancestry だけでは不足」と書き直す。

### 9. D116 を supersede しないまま、D116 が禁じた freeze ledger を D116 の名で導入している

**主張:** 現行 canonical decision は8cへの凍結機構導入を明示的に禁止するが、新文書は hash 世代台帳を「凍結」として導入し、しかも D116 を根拠として掲げる。

**根拠:** D116 は「凍結機構を導入しない」「git の再実装は冗長」とする (`docs/decisions.md:5494-5502`)。8b freeze の新規輸入も否定する (`同:5515-5517`)。改訂文書は hash 世代台帳を導入 (`docs/phase3-8c-preregistration.md:4-7`, `:145-154`) し、docs 地図は D116 と T-327 の併記でこれを正本化する (`docs/README.md:20-22`)。D124 はなお authority 未定としている (`docs/decisions.md:6073-6076`)。

**具体的な反例:** auditor A は D116 に従い g1 を非 canonical な追加 freeze として拒否し、auditor B は T-327 実装に従い有効 generation とする。同じ tree の発効妥当性が二値になる。

**重大度:** `must-fix`

**成果物影響:** `condition-freeze.v1.g1.json` の正当性と activation report の受理可否が canonical decisions 間で一意に決まらない。

**提案修正:** land 前に新しい D を記録し、D116 のどの決定をどの範囲で supersede するか明記する。git ancestry、8b freeze 非変更、Layer 3 の残余は維持すると境界を固定し、docs 地図も新 D を参照する。

### 10. 現行 HEAD の診断12件を丸ごと期待値に焼き込んでいる

**主張:** literal hash・日付・行番号は新規テストに見当たらないが、現在の capability 不在状態と reason code 全12件を snapshot expectation にしている。

**根拠:** fixture は現 HEAD の evidence path を複製する (`orchestrator/tests/test_s8c_preregistration_predicates.py:64-84`)。その結果を exact dictionary で固定する (`同:96-115`)。

**具体的な反例:** 独立 T-325 が空でも正規な `trial_registry.py` を導入すると、C02/C03/C08 は「capability absent」から「proof undefined」へ変わる。SATISFIED は依然0件でもテストは赤になる。

**重大度:** `should`

**提案修正:** 安全 invariant「SATISFIED 0件」と、個別 reason の対象テストを分離する。全12件の gap ledger を意図的に固定するなら、base commit／依存 wave と更新契約をテスト名・README に明記する。

## 静的に確認した非回帰

- `tools/check_docs.py` の差分は `LIVING_DOCS` 1件追加だけ (`tools/check_docs.py:33-68`)。既存 byte・最長行予算 (`同:168-202`, `:2460-2700`) と dispatch／節／孤児検査 (`同:3015-3113`) は弱化されていない。8c は path・行番号・D参照検査へ実際に入る (`同:3202-3268`)。
- §6 の12条件本文 `docs/phase3-8c-preregistration.md:101-127` は `git diff --unified=0` 上変更なし。条件9・12の古い診断も裁定どおり未修正。
- `FROZEN_MANIFEST` は辞書自身の exact 23件だけを照合する (`orchestrator/tests/test_frozen_artifacts.py:125-153`) ため、新規 g1 pathでは壊れない。
- provenance は commit の全変更 path を列挙し (`tools/check_ai_provenance.py:598-631`)、新規 `.py` と `orchestrator/` JSON を実装面として拾う (`同:541-566`)。
- 未既知性走査は tracked と untracked の通常ファイルを列挙し (`orchestrator/campaign/s8b_holdout_freeze.py:179-212`)、除外は `output/s8b-freeze/` だけ (`同:32`, `:232-233`)。新規 s8c namespace は走査対象である。
- pytest-only allowlist の3件 (`orchestrator/tests/README.md:161-163`) は、全 `test_*.py` を列挙する meta-test (`orchestrator/tests/test_plain_runner_coverage.py:44-86`) と整合している。
- U-1〜U-5 の production 結線・外部 anchor・同時改変・hidden pilot・一回性を実装したという偽装参照は見つからず、文書も未結線・外部を明記している (`docs/phase3-8c-preregistration.md:156-159`, `:182-201`)。U-7 に送った条件文も不変。ただし U-6を含む将来 green 判定の実効性は所見2のとおり不足する。

## 総括

- **判定: NO-GO**
- **blocker: 4件**
- blocker は capability 偽造、恒真化できる predicate、人間裁定の token-only 認証、commit 前受入のデッドロック。
- must-fix は5件、should は1件。
- 親が最初に直すべき点は、段6で candidate commit を検査できるよう HEAD 固定 invariant を解消すること。
- 続いて registry 注入を capability 経路から除去し、default evaluator の green E2E と混合 status の conjunction 負例を作ること。
- テスト、`check_docs.py`、provenance 監査はいずれも実行しておらず、green とは報告しない。