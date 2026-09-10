## RB-1

4 軸の権威である journal が admission root lock に参加しないため、`use()` の再検証と callback は原子的ではない。

[実測] `repetition` と `attempt_ordinal` は journal から読むが (`orchestrator/campaign/s8b_holdout_admission.py:4916-4950`)、既存コード自身が journal writer は root lock を取らないと明記している (`orchestrator/campaign/s8b_holdout_admission.py:4321-4324`)。実 writer も lock なしで append する (`orchestrator/campaign/s8b_floor_campaign.py:1593-1604,5924-5928`)。

具体的な壊れ方: 再検証後、callback 実行前または実行中に同じ attempt の重複 `session-start` が追記されても registry action は進み、canonical authorization を失った observation が残る。

深刻度: `blocker`

成果物への影響: registry が受理した observation と journal の権威が食い違い、後段 inspector が run を拒否して certified 選択・レポート・台帳参照が欠落する。

## RB-2

`use()` は既存 attempt registry の更新 API とそのまま組み合わせると同じ `ledger.lock` を再取得して自己 deadlock する。

[実測] `use()` は root lock の内側で callback を呼ぶ (`orchestrator/campaign/s8b_holdout_admission.py:5134-5143`)。registry の root は同じ shared admission root (`orchestrator/campaign/s8b_attempt_registry.py:462-473`) で、`_atomic_update()` も新しい fd から同じ lock を取る (`orchestrator/campaign/s8b_attempt_registry.py:984-1012`)。`_locked()` は再入可能 lock ではない (`orchestrator/campaign/s8b_holdout_admission.py:667-686`)。

具体的な壊れ方: `capability.use(action=lambda: begin_attempt_observation(...))` でも、registry transition 内から `use()` を呼んでも停止し、callback が戻らない。

深刻度: `real`

成果物への影響: 単位 A が lock-aware な内部更新 seam を新設せず接続すると observation row が作られず、certified レポートまで到達しない。

## RB-3

追加テストは cut-6 の実使用、retry slot の権威導出、root・generation・attempt・cell などの `use` 引数移植を検査していない。

[実測] 共通 helper は常に planned attempt と `attempt_ordinal=0` を作る (`orchestrator/tests/test_s8b_holdout_admission.py:2001-2034`)。cut-6 正例は capability の型と attempt ledger 不在だけを確認し、`use()` を呼ばない (`orchestrator/tests/test_s8b_holdout_admission.py:2159-2172`)。`use` 引数の負例は repetition と ordinal の 2 軸だけである (`orchestrator/tests/test_s8b_holdout_admission.py:2332-2351`)。

具体的な壊れ方: retry ordinal を常に 0 とする実装、cut-6 を使用時だけ拒否する実装、root・claim digest・attempt・campaign・cell の比較を落とした実装でも追加 35 node を通過できる。

深刻度: `real`

成果物への影響: retry/cut-6 の受理集合が縮小するか、別 root・generation・attempt の capability が受理され、registry と台帳の参照が誤束縛される。

## RB-4

marker shape と identity の parametrize 負例は、個別 gate ではなく同じ最終 dict 不一致だけで拒否される。

[実測] test は canonical path 上の disk marker だけを変える (`orchestrator/tests/test_s8b_holdout_admission.py:2195-2218,2252-2279`)。production は canonical helper に state 由来の `expected_marker` を渡し、tampered disk marker は最後の `disk_marker != canonical_marker` で一括拒否する (`orchestrator/campaign/s8b_holdout_admission.py:4975-5005`)。

具体的な壊れ方: schema・event・role 専用 gate が効かなくても最終 equality が残る限り全 case が成功し、変異の単一理由性を証明できない。

深刻度: `nit`

成果物への影響: 現実装の受理集合は変わらないが、拒否理由と mutation evidence の帰属が不正確になる。

## RB-5

実規模は段 4 の「旧見積もりの半分以下」を超えている。

[実測] 差分は production `+324/-1`、test `+404/-0`、合計 `+728/-1`、churn 729 LOC である。静的 AST 展開では test function 16、parametrize 込み executable node は 35。段 4 の半分以下という見積もりは 275–425 LOC、最大 32.5 node 相当である (`s4-adjudication.md:78-79`)。

具体的な壊れ方: author 報告の LOC 自体は正しいが、node 総数と裁定見積もり超過が報告されず、レビュー量の前提が外れる。

深刻度: `nit`

成果物への影響: certified 値や受理集合は直接変わらないが、受入時の scope・検証コスト評価が過小になる。

## RB-6

dispatch と import に関する実行報告には、射影された差分内の裏付けがない。

[実測] `rc=16`、`qstat -Q preflight rc=1`、targeted run、collect-only、module import、未起動 receipt の除去は author 報告だけに存在する (`artifacts/t2107-t1851-b1/s5-author.md:14,69-83`)。対応する log や receipt は射影されていない。HEAD、2-file status、AST parse、`git diff --check`、constructor 2 箇所は独立に再確認できた。

具体的な壊れ方: 実行要求が実際に dispatch されたか、module import が成功したかをこの review 材料だけでは再現・監査できない。

深刻度: `nit`

成果物への影響: 値や受理集合は変わらないが、pytest 0 node のため成果物を green として受理する根拠は増えない。

## Process-local state

[実測] `_cell_states` は `_CellState.token` を強参照し続け (`orchestrator/campaign/s8b_holdout_admission.py:468-475,513`)、削除経路がない。したがって token は GC されず、通常の `id()` 再利用は起こらない。仮に衝突しても `_cell_state()` の `state.token is admission` が拒否する (`orchestrator/campaign/s8b_holdout_admission.py:4232-4236`)。

fresh process では state が無いため拒否される。一方、fork child は `_cell_states` と seal をコピーするので PID 境界では拒否されない。PID-bound という契約は無いため独立所見にはしないが、厳密な same-process capability ではない。

## 反証材料なし

以下は現物と一致し、反証材料なし。

- 編集面は裁定どおり 2 file だけで、adapter・launcher・fixture・単位 A の file は未変更。
- `CellHoldoutAdmission(...)` は repo 全体で 2 箇所、位置引数 0、keyword 構築 2。
- field の fresh/resume と current/legacy inspector 射影は報告どおり。
- expected marker、canonical path、canonical reader、claim/main 再導出、generation identity は既存 helper を呼んでいる (`s8b_holdout_admission.py:4975-5002`)。
- `replace`、token の set/dict 要素化、reflection、pickle consumer は見つからず、既存 serialized bytes への流出も反証材料なし。
- pytest の実行済み nodeid は報告どおり 0 と扱う。本 review でも pytest は実走していない。

## 総括

blocker は 1 件、real は 2 件、nit は 3 件。

journal 由来の 4 軸を同一 lock 区間で保護できておらず、採用済みの原子性不変条件を満たさないため、このまま受入へは進めない。加えて単位 A への接続には、同じ root lock を再取得しない registry 更新 seam が必要である。