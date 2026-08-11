## 所見

### 1. BLOCKER — holdout 全体の欠落を cell-product gate が受理する

根拠: `orchestrator/campaign/s8b_oracle_manifest.py:1031-1036` は期待セルを freeze 全 holdout ではなく `schedule_holdouts` から生成する。さらに `:1055-1058` も schedule 内 holdout だけを execution snapshot の対象にする。任意 manifest を受ける実経路は `orchestrator/campaign/s8b_oracle_driver.py:1124-1128`。新テスト `orchestrator/tests/test_s8b_oracle_manifest.py:289-322` は全 holdout を残した configuration subset しか攻撃していない。

**成果物影響:** rr20 を丸ごと落とし、rr80×全 configuration だけにした manifest が通るため、report の `expected_cells` から rr20 が消え、judge の winner／certified 選択が不完全な観測集合から決まる。

直し方:

- `schedule_holdouts == set(freeze["holdouts"])` を先に要求する。
- `expected_cells` は freeze の全 holdout から生成し、holdout 欠落の negative test を追加する。

### 2. MAJOR — measurement closure が captured HEAD でなく dirty worktree bytes を記録する

根拠: `orchestrator/campaign/s8b_holdout_freeze.py:1311-1317` は `_blob_at_head()` の戻り値を捨て、path の HEAD 実在だけを確認した後、worktree を再読してその hash を採用する。`frozen_at_head` は `:1341-1343` で先に捕捉される。`orchestrator/tests/test_s8b_holdout_freeze.py:887-907` は tracked file を commit せず変更し、その dirty hash を採る挙動を正例として固定している。

**成果物影響:** candidate の `measurement_closure[].sha256` が `frozen_at_head:path` の blob hash から worktree hash へ変わり、candidate が指す commit と proof closure が不一致になる。後段で未同梱なら ratification が止まり、同梱すれば altered closure が台帳参照になる。

直し方:

- `_blob_at_head()` が返した bytes を hash 入力にする。
- worktree bytes も読むなら HEAD blob との完全一致を要求し、dirty なら candidate を拒否する。現行正例テストは拒否期待へ反転する。

### 3. MAJOR — `None` pin の変異テストが受理集合を検査していない

根拠:

- Budget test `orchestrator/tests/test_s8b_holdout_freeze.py:753-767` は missing root／missing inputs を与えている。しかも production の `None` gate は `orchestrator/campaign/s8b_holdout_freeze.py:1145-1147` と `:1334-1339` の二重であり、一方だけの変異では同じ理由で拒否され続ける。
- Spec test `orchestrator/tests/test_s8b_oracle_manifest.py:883-893` は `not-json`、`:1012-1027` は spec 自体を設置していない。`orchestrator/campaign/s8b_oracle_spec.py:158-165` の分岐を緩めても別の拒否へ先取りされ、診断文字列だけが変わり得る。

**成果物影響:** この fixture のままでは pin gate が将来 fail-open しても変異を kill した証拠にならず、未承認 budget／schedule が candidate に入り、ledger 上限・観測セル・certified winner を変え得る。

直し方:

- pin 以外は完全に正当な fixture を用意し、`None` の一点だけで出力が拒否されることを検査する。
- Budget の authority check は一箇所へ集約するか、二重 gate を同時に外す事前登録済み変異で受理集合の変化を確認する。

### 4. MAJOR — v2 専用 eager import が v1 import 境界と process global state を変える

根拠: `orchestrator/campaign/s8b_holdout_freeze.py:36-39` が v1 API の import 時にも v2 専用 module を無条件 import する。特に `env_contract` は `orchestrator/campaign/env_contract.py:367-371` で import-time validation を実行し、`:560` と `:573` で process-wide fork callback を登録する。

保護対象関数と `TOP_LEVEL_KEYS`／`GENERATION_SCHEMA_FIELDS` の AST は HEAD と一致したが、module の import 成否・副作用は一致していない。

**成果物影響:** v2 専用依存の import-time 例外や platform 非対応で、従来の v1 `generate`／`verify`／T-080 経路まで import 不能となり、v1 の受理集合が実質的に空になる。

直し方:

- `env_contract`、floor modules、launch-cert helper は v2 関数内で遅延 import する。
- v1 API を v2 dependency の import 失敗下でも import・実行できる静的／subprocess regression test を置く。

### 5. MAJOR — canonical bytes の新規 assert が production serializer と自己参照している

根拠:

- `orchestrator/tests/test_s8b_holdout_freeze.py:818-820` は writer 出力を同じ production `_canonical_bytes()` で再計算して比較するため、serializer 自体を壊しても両辺が同時に変わる。
- Spec fixture は `orchestrator/tests/test_s8b_oracle_manifest.py:190-195` で production `_canonical_bytes()` から raw を作り、production validator も `orchestrator/campaign/s8b_oracle_spec.py:72-76,178-180` で同じ serializerを使う。したがって key 順・separator・非 ASCII escape の同時 drift は通る。
- 一方、schedule hash は `orchestrator/tests/test_s8b_oracle_manifest.py:50-55,154-161,864-880` の独立 literal であり、ここは自己再計算ではない。

**成果物影響:** spec/candidate の exact bytes と SHA-256、ひいては manifest・台帳の参照 hash が意図せず変わってもテストが緑のままになり得る。

直し方:

- 非 ASCII、key 順、`100`／`100.0`／`1e2`、末尾 LF を含む独立 raw bytes literal と独立 SHA-256 literalを置く。
- production serializer を期待値生成に使わない。

### 6. MINOR — `-0.0` が budget として受理され、意味と bytes identity が分裂する

根拠: `orchestrator/campaign/s8b_holdout_freeze.py:1128-1140` は負値を `< 0` だけで拒否するため `-0.0` が通る。`:228-236` の canonical JSON は `-0.0` を保持し、`:1365-1366` はその bytes identity で approval と比較する。新テスト `orchestrator/tests/test_s8b_holdout_freeze.py:829-846` は `100`／`100.0` のみを検査している。

**成果物影響:** ledger 上はゼロと同じ budget なのに freeze の `budget` bytes と `floor_budget_snapshot_sha256` は `0`／`0.0` と別値になり、同一予算の proof identity が分岐する。

直し方:

- float の zero は符号 bit が負なら拒否するか、ゼロを整数 `0` へ正規化する。
- total／per-holdout 双方に `-0.0` の拒否テストを追加する。

## 確認できた防壁

- `BUDGET_APPROVAL_SHA256 is None` と `APPROVED_SPEC_SHA256 is None` の production 経路は、現実装では入力にかかわらず拒否する。環境変数や CLI 引数による解除面もない。
- 全 holdout を残した一様 1-configuration schedule は新 `verify_manifest` gate に到達して拒否され、正当な全積 manifest は同 gate を通る。
- SafeA は絶対 path、`..`、末尾 slash、symlink parent、既存 leafを拒否し、dirfd を保持して traversal／write している。事前設置 hardlink leaf も `O_EXCL` で拒否される。
- 新規テストの書込み先は tmp root 内。実 repo の `output/s8b-freeze/` を作る経路は静的には見つからなかった。
- pytest は指示どおり実行していない。親実測の 179 passed は上記の静的な受理集合欠陥を閉じない。

## 判定

**NO-GO**

## 総括

BLOCKER は、manifest から holdout 全体を落としても choke point を通過できる点である。  
closure の HEAD 束縛、v1 import 不変性、pin 変異 fixture、canonical bytes fixture に MAJOR が残る。  
SafeA と `None` pin の現 production 拒否自体には直接の fail-open は見つからなかった。  
BLOCKER／MAJOR の修正後、欠落 holdout と有効入力上の pin 変異を含む焦点再レビューが必要である。