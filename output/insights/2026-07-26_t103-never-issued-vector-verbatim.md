# [T-103] never-issued × real-artifact vector — 逐語

本 wave の子出力と親の前提実測の**原文**である。編集は下記 defang だけで、
それ以外は 1 byte も変えていない。材料レポートは
`2026-07-26_t103-never-issued-vector.md`。

## defang 契約 (D88 (6) と同型)

holdout の未既知性検索は三軸 (rratio / skew / rmw) の canonical encoding が
**同一ファイル内で conjunction** した時に 1 hit と数える。レンズ A の所見 A-7 が
その 3 語を名指ししているため、逐語をそのまま凍結すると gate が自己発火する。

- 置換規則: 三軸 key 直後の半角 `=` を全角 `＝` へ 1:1 で置き換える (可逆)。
- 置換箇所数と、各原文の SHA-256・byte 数を下表に併記する。
- 置換後に conjunction 検索を実走し 0 hit を機械確認した (結果は材料レポート §検査)。

| 原文 | 生成元 | 原文 SHA-256 | 原文 bytes | defang 箇所 |
|---|---|---|---|---|
| `brief.md` | brief.md | `b42a65ef28eb99eb0538d0c72c68a0e481130fab352a21059f9604979c0015db` | 7188 | 0 |
| `probe-output.txt` | probe_never_issued.py の stdout | `b17d002327b1236435c49bfa96d9273b997ecb761e6f2da59fa9f17e009e8e10` | 1655 | 0 |
| `plan-v1.md` | gpt-5.6-sol / reasoning=max / sandbox=read-only | `20c6387de41c4200bfd8a5a88965e3185f7f0b556656732af8d8ed21865a28fe` | 15165 | 0 |
| `lens-a.md` | gpt-5.6-sol / reasoning=max / sandbox=read-only | `99d24c1747fa57282a6d6d54d1917c74159ae06b63515a58409e60f25b1962f9` | 12143 | 3 |
| `lens-b.md` | gpt-5.6-sol / reasoning=max / sandbox=read-only | `db0cf16a9e595f90abdc7dc043cb6a6719e4a24910e2ba02e589f90574090950` | 15002 | 0 |

defang 合計 = 3 箇所。

## 実行環境

- REPO = worktree `dev-wave-t088-floor-wrapper`、branch `worktree-dev-wave-t091-093-hardening`
- 基準 commit = `796262c` (作業ツリー clean、`git submodule update --init` 済み)
- `external/ccbench` = `d706650cdb31e442bef45b9b4216951d4fb40969`
- codex 子は 3 本とも `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`、
  いずれも exit code 0。prompt は job tmp の `prompt-*.txt` を原文とする。
- 親の probe は `python3 probe_never_issued.py`、rc=0。repo へは書き込んでいない。

---

## 親 brief (段 1) — `brief.md`

原文 SHA-256 = `b42a65ef28eb99eb0538d0c72c68a0e481130fab352a21059f9604979c0015db` / 7188 bytes / defang 0 箇所

````````text
# 段 1 brief — [T-103] never-issued × real-artifact refusal vector の新設

作業ツリー root (以後 REPO): /home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper
基準コミット: 796262c (branch worktree-dev-wave-t091-093-hardening、clean)

## 1. scope

[T-103] のみ。**テストのみ・本番コード 0 byte**。編集面は
`orchestrator/tests/test_s8b_oracle_driver.py` への純追加とする。新規ファイルは作らない。

## 2. 背景 (前 wave の経緯)

前 wave [T-092] が `test_real_freeze_gate_lists_floor_and_budget_null` の pre-R 分岐を削除した。
その分岐は「T-080 receipt が履歴に無い (never-issued) とき、実 artifact に対する legacy verifier 2 本の
拒否 + floor + budget = 4 件が gate に出る」ことを assert していた。post-R の現 repo では到達不能
だったため実効検出力の低下は 0 だが、敵対相談 A-6 が「never-issued 固定の別 node を実物 freeze に
対して撃つ」対案を出し、親が「検出力の追加であって保持ではない」として scope 外へ送った。
それが [T-103] である。

## 3. 段 1 前の前提実測 (実ファイルに対する実走。模擬・monkeypatch なし)

親が REPO 上で実際に走らせて得た値である。

実測 1 — 実 repo 現行 (post-R) に対し legacy verifier 2 本は **いまも赤**:
- `s8b_holdout_freeze.verify(REPO/output/s8b-freeze/holdout_freeze.json, root=REPO)`
  → `FreezeError: design_source sha256 不一致: recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae`
  (design_source = `docs/phase3-8b-descriptor-design.md`)
- `s1_known_axes_freeze.verify(REPO/output/s1-freeze/known_axes_freeze.json, source_resolver=lambda rel: REPO/rel)`
  → `FreezeError: source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py recorded=3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1 actual=8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311`

含意: **T-080 receipt は装飾ではなく受理そのものを担っている**。gate が active-valid で legacy を
迂回するから通っているのであって、artifact 自体は legacy 契約を満たしていない。

実測 2 — 既存テスト `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`
(`orchestrator/tests/test_s8b_oracle_driver.py:2394`) が
`_t080_stub_free_e2e_repo(tmp_path, issue_receipt=False)` を使い、never-issued × real-artifact を
**legacy verifier を stub せずに**撃っている。ただし
- (a) `design_source` と `generator` を**記録 bytes へ復元してから** `generator` を人工改竄する。
  よって自然 drift 由来の `design_source` 拒否はこの node では消えている。
- (b) known-axes 拒否は `known_prefix` による **prefix 一致のみ**。対象 path も recorded/actual も未 pin。

実測 3 — freeze 2 種が参照する source は実体 34 path / 合計 0.5 MiB。全て REPO 内に存在する。
fixture builder `_t080_stub_free_e2e_repo` (`:416`) は `orchestrator/` と `output/` を copytree し、
`docs/phase3-8b-descriptor-design.md` を含む required 集合を個別 copy し、
`external/ccbench` を submodule add して `known["ccbench_pin"]` へ checkout し、
builder 内で `basis_history.state == "never-issued"` を assert している。

実測 4 — 実 freeze は `floor=None, budget=None` の v1 であり、`gate_check` は `_gate_check_core`
経路 (`orchestrator/campaign/s8b_oracle_driver.py:340-420`) に入る。legacy 呼び出しは
`s8b_holdout_freeze.verify(Path(freeze_path), root=root)` (`:373`) と
`s1_known_axes_freeze.verify(known_path, source_resolver=lambda relative: root / relative)` (`:409-411`)。
`known_path` は freeze の `known_axes_freeze.path` を `_resolve_recorded_path(..., root=root)` で解決する。

`git submodule update --init` は実施済み (rc=0、external/ccbench = d706650)。

## 4. 不変条件 (破ってはならない)

1. 本番コード・schema・role・凍結成果物の bytes を 1 byte も変えない。受理集合は拡大も縮小もしない。
2. 既存テスト node を削除・弱体化・改名しない。g7 を含め既存 assert を緩めない。**純追加**である。
3. working tree bytes 由来で揮発する値 (`actual=` の sha256 など) を期待値へ literal 焼き込みしない。
   独立導出する。凍結 artifact 由来で安定な `recorded=` は literal pin してよい。
   根拠は同ファイル `_assert_refusal_reasons` の docstring。
4. `s8b_holdout_freeze.verify` / `s1_known_axes_freeze.verify` / `migration.verify_receipt` を
   mock・monkeypatch しない。**stub しないことが本 vector の要点**である。
5. 新規ファイルを作らない (既存テストファイルへの追加に限る)。
6. 期待値を production の返り値から組み立てない (恒真化の禁止)。独立 oracle から導出する。

## 5. 成果物の形 (provisional)

`orchestrator/tests/test_s8b_oracle_driver.py` へ新 node を追加する。

- **N1**: `_t080_stub_free_e2e_repo(tmp_path, issue_receipt=False)` の fixture に対し、
  **復元も改竄もせずそのまま** `driver.gate_check(freeze_path=root/HOLDOUT_REL, root=root)` を撃つ。
  期待 = refusal 4 件 (holdout design_source 不一致 / known source 不一致 / floor-null / budget-null)、
  `decision.allowed is False`、`decision.t080_freeze_migration_observation is None`。
  recorded は literal pin、actual は fixture 内ファイルから test 側で独立導出。
- **N2**: 実 repo (ROOT) の artifact に対し legacy verifier 2 本を直接撃ち、
  「post-R でも legacy は赤 = receipt が受理を担う」を固定する。

## 6. 分割方針

差分が単一ファイル・小規模なので段 5 の実装子は **1 本**とし、所有 =
`orchestrator/tests/test_s8b_oracle_driver.py` 全体。並列分割しない。
段 3 敵対相談 2 本、段 6 敵対レビュー 2 本は規定どおり。

## 7. 親の provisional 裁定 (攻撃対象。守る側に回らず攻撃せよ)

- **(P1)** g7 は自然 drift vector を被覆していない。したがって N1 は g7 の複製ではない。
- **(P2)** `_t080_stub_free_e2e_repo` は working tree bytes を複製するので、fixture 内の refusal
  payload は実 repo の実測 1 と同一になる。
- **(P3)** N2 は scope 内である (gate の挙動でなく artifact の性質の pin だが、
  N1 の前提「legacy は赤」を独立に固定する価値がある)。
- **(P4)** refusal 集合は `_assert_exact_refusals` で exact 4 件に固定できる。
- **(P5)** known-axes 拒否が `s8a_trigger_sweep.py` を最初に報告するのは freeze 文書の走査順に
  依存する実装詳細かもしれず、path の literal pin は brittle かもしれない。
- **(P6)** 本 wave は `DW-O09` (凍結 bytes の pin 閉包) 非発火と親は判断した。
  テスト純追加で凍結成果物の bytes を変えないため。

````````

---

## 親の前提実測 raw 出力 (段 1 前) — `probe-output.txt`

原文 SHA-256 = `b17d002327b1236435c49bfa96d9273b997ecb761e6f2da59fa9f17e009e8e10` / 1655 bytes / defang 0 箇所

````````text
fixture state: never-issued
verify_receipt state: never-issued
verify_receipt refusals: ()
observation: None
allowed: False
refusal count: 4
  REFUSAL: holdout-freeze-verify: FreezeError: design_source sha256 不一致: recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae
  REFUSAL: known-axes-freeze-verify: FreezeError: source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py recorded=3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1 actual=8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311
  REFUSAL: floor-null: freeze.floor が null
  REFUSAL: budget-null: freeze.budget が null
gate observation: None
design_source path: docs/phase3-8b-descriptor-design.md
  recorded: 1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d
  fixture actual: 5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae
  REPO actual:   5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae
known_axes drift 件数: 3
  DRIFT orchestrator/campaign/s8a_trigger_sweep.py recorded=3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1 actual=8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311
  DRIFT orchestrator/campaign/s6_sort_sweep.py recorded=0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2 actual=28270e905785c787f1eb74cebcf34f8feb98e1e7cec738dee14611c9ab3dad1a
  DRIFT orchestrator/campaign/p3_s4_loop_sort.py recorded=9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4 actual=0e716a6cda268e3d158774c344d002a8daf49fa7dd4ab9bbb1bb5c9e0d30d8b0

````````

---

## 段 2 codex プラン起草 — `plan-v1.md`

原文 SHA-256 = `20c6387de41c4200bfd8a5a88965e3185f7f0b556656732af8d8ed21865a28fe` / 15165 bytes / defang 0 箇所

````````text
結論は「2 node の純追加」で実装可能です。ただし (P1)、(P2)、(P5)、(P6) の説明は修正が必要です。以下の行番号は追加前の現行 tree を基準にしています。コード変更・pytest 実行はしていません。

## 1. 実装プラン

対象は [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1) のみ。本番コード、新規ファイル、既存 node には触れません。

### 1.1 共通の独立 oracle

`_BUDGET_REFUSAL` の直後、現行 `:901` に次の test-only literal と helper を追加します。

- design source:

  - path: `docs/phase3-8b-descriptor-design.md`
  - recorded: `1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d`

- known source:

  - path: `orchestrator/campaign/s8a_trigger_sweep.py`
  - recorded: `3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1`

helper は概念的に次の処理だけを行います。

```python
design_actual = hashlib.sha256((root / DESIGN_REL).read_bytes()).hexdigest()
known_actual = hashlib.sha256((root / KNOWN_REL).read_bytes()).hexdigest()

assert design_actual != DESIGN_RECORDED
assert known_actual != KNOWN_RECORDED
```

その後、prefix を含まない legacy の2メッセージを返します。recorded/path は test literal、actual は各 node が使う `root` の現物 bytes から計算します。

以下は使用禁止です。

- `decision.refusals` や捕捉した例外文字列から期待値を作る
- production の `_sha256`、`_verify_source`、`_iter_sources` を oracle として呼ぶ
- actual が literal 化されている既存 `_T080_REAL_REPO_SOURCE_GOLDEN`（`:90-169`）を流用する

`hashlib` は既存 import `:10` を使用します。

### 1.2 N2: real repo の legacy 2本を直接固定

関数名:

```python
test_real_freeze_legacy_verifiers_have_exact_natural_drift_t103
```

挿入位置:

- 既存 `test_real_freeze_gate_lists_floor_and_budget_null`（`:1370-1430`）の直後
- `test_t080_gate_hermetic_primary_states_exact` の decorator（現行 `:1433`）より前

使う既存要素:

- `REAL_FREEZE`（`:49`）
- `pytest.raises`（import `:23`）
- `migration.KNOWN_AXES_REL`（[t080_freeze_migration.py:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:35)）
- 1.1 の新しい独立 oracle

処理順:

1. `expected_holdout` と `expected_known` を、production 呼び出しより前に `ROOT` の bytes から構成する。
2. `driver.s8b_holdout_freeze.verify(REAL_FREEZE, root=ROOT)` を直接呼び、`FreezeError` を捕捉する。
3. `str(caught.value) == expected_holdout` を要求する。
4. `driver.s1_known_axes_freeze.verify(ROOT / migration.KNOWN_AXES_REL, source_resolver=lambda relative: ROOT / relative)` を直接呼ぶ。
5. こちらも例外文字列の完全一致を要求する。

期待する raw legacy メッセージは次の2件です。

```text
design_source sha256 不一致: recorded=1829af7f... actual={ROOT の design_source bytes を hashlib で計算}

source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py recorded=3e94735a... actual={ROOT の s8a_trigger_sweep.py bytes を hashlib で計算}
```

直前の既存 node が `migration.verify_receipt(root=ROOT).state == "active-valid"` と、public gate の refusal が floor/budget のみであることを固定しています（`:1378-1388`）。N2 と合わせることで「artifact 単体は legacy 赤だが receipt adapter 経由では受理される」を示せます。

legacy verifier、`verify_receipt` とも mock しません。

### 1.3 N1: never-issued × 無復元・無改竄の public gate

関数名:

```python
test_never_issued_unmodified_real_artifacts_have_exact_four_refusals_t103
```

挿入位置:

- 既存 `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`
  （`:2395-2444`）の直後
- `test_exit_code_priority_table`（現行 `:2447`）より前

使う既存 helper:

- `_t080_stub_free_e2e_repo`（`:416-599`）
- `_assert_exact_refusals`（`:190-197`）
- `_FLOOR_REFUSAL` / `_BUDGET_REFUSAL`（`:900-901`）
- 1.1 の独立 oracle

処理順:

1. `_t080_stub_free_e2e_repo(tmp_path, issue_receipt=False)` を1回だけ呼ぶ。
2. 返された fixture は一切書き換えない。
3. fixture 内の design source と known source の actual SHA-256 を test 側 `hashlib` で計算する。
4. production 呼び出し前に期待4件を組み立てる。
5. `driver.gate_check(freeze_path=root / migration.HOLDOUT_REL, root=root)` を呼ぶ。
6. 次を assert する。

```python
_assert_exact_refusals(decision.refusals, expected_four)
assert decision.allowed is False
assert decision.t080_freeze_migration_observation is None
```

builder 自身が receipt 発行前の commit で `inspect_receipt_history(...).state == "never-issued"` を要求しています（`:487-491`）。`issue_receipt=False` は receipt 発行用 subprocess の手前で返ります（`:493-495`）。

### 1.4 exact 4文字列の逐次導出

現行状態で期待する集合は次の4件です。

1. Holdout design source

```text
holdout-freeze-verify: FreezeError: design_source sha256 不一致: recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d actual={design_actual}
```

導出経路:

- holdout verifier は `design_source` を最初に検査: [s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_holdout_freeze.py:709)
- `_verify_source` が actual を worktree bytes から計算: `:653-659`
- raw エラー書式: `:660-662`
- driver が `holdout-freeze-verify: {type}: {message}` を付加: [s8b_oracle_driver.py:373](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:373)-`:377`

2. Known source

```text
known-axes-freeze-verify: FreezeError: source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py recorded=3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1 actual={known_actual}
```

導出経路:

- driver が freeze 内の known path を解決: `s8b_oracle_driver.py:402-410`
- `source_resolver=lambda relative: root / relative`: `:409-411`
- known verifier の raw 書式: [s1_known_axes_freeze.py:731](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s1_known_axes_freeze.py:731)-`:741`
- driver prefix: `s8b_oracle_driver.py:412-413`

3. Floor

```text
floor-null: freeze.floor が null
```

`freeze.floor is None` なら [s8b_oracle_driver.py:415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:415)-`:416` が追加します。

4. Budget

```text
budget-null: freeze.budget が null
```

同じく `:417-418` です。

never-issued は `ReceiptResolution("never-issued", (), None, head)` を返すため（[t080_freeze_migration.py:1640](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1640)-`:1642`）、receipt refusal は増えません。adapter も active-valid 以外では `None` を返し legacy へ委譲します（`s8b_oracle_driver.py:164-166`）。

`_assert_exact_refusals` は `len` と `set` の両方を比較するため、余分な refusal、欠落、同一 refusal の重複も検出します（`:190-197`）。

### 1.5 (P5): known-axes の走査順

`s8a_trigger_sweep.py` が最初になる順序は次の通りです。

1. `verify` が JSON をロードし、その dict を並べ替えず `verify_document` に渡す（`s1_known_axes_freeze.py:785-791`）。
2. generator 検査を先に通す（`:721-727`）。
3. `_iter_sources` は dict に `sources` があれば、その list を list 順で先に yield する（`:682-691`）。
4. その後、dict の insertion order で子を depth-first に走査する（`:692-697`）。
5. freeze JSON は `entries` → `balanced` → `system_gate` の順であり、最初の `sources` list は [known_axes_freeze.json:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/s1-freeze/known_axes_freeze.json:29)-`:55`。
6. その list の先頭4件は現物と一致し、5件目 `:50-54` が `s8a_trigger_sweep.py` の旧 SHA です。

Python の dict insertion order と JSON list orderはいずれも決定的です。`_validate_schema` の set 比較（`:700-715`）も document 自体を再構成しません。したがって、固定された freeze bytes と現在の先頭4 source bytes に対しては `s8a_trigger_sweep.py` が決定的に最初です。

ただし、先頭4 source のどれかが将来 drift すれば最初の path は変わります。これは乱択による偽赤ではなく、legacy 診断の実際の先頭が変わった状態です。path を契約にしたくない場合の代案は、先頭5件を `(path, recorded literal)` の test-only tuple にし、test 側で最初の actual mismatch を選ぶことです。production の `_iter_sources` や例外出力から選んではいけません。

### 1.6 N1 と既存 g7 の差

| 観点 | 既存 g7 | N1 |
|---|---|---|
| fixture | 同じ never-issued builder | 同じ |
| fixture 変更 | design_source と generator を履歴 bytes に復元後、generator を人工改竄（`:2414-2419`） | 復元・改竄なし |
| holdout assert | 人工 generator refusal を exact（`:2420-2424`） | 自然 design_source refusal を exact |
| known assert | prefix だけ（`:2430-2439`） | path・recorded・独立 actual まで exact |
| 全体集合 | `len == 4` と known を除いた3件のみ exact（`:2438-2444`） | 4件すべて `_assert_exact_refusals` |
| allowed | `False`（`:2437`） | `False` |
| observation | assert なし | `None` を明示 |

したがって、制御フロー被覆としては実質的に大きく重複します。新規性は「自然 design drift」「known payload 全体」「observation」の3点です。完全な複製ではありませんが、まったく別の vector と呼ぶのも過大です。

### 1.7 fixture コスト

builder の既存 call site は6箇所です。

- `:603` — 1 node
- `:686` — 4 parameter node
- `:726` — 1 node
- `:814` — 3 parameter node
- `:839` — 1 node
- `:2396` — 1 node

したがって、全 collection では現在11回実行され、各 collected node は builder を1回呼びます。N1 追加後は12回、約9%増です。

静的な I/O 下限は以下です。

- `orchestrator/` + `output/`: 約31.4 MB、2,347 files
- submodule worktree: 約2.35 MB、405 files
- さらに `git add -A`、commit、receipt history 検査

`issue_receipt=False` なので receipt 発行 subprocess は走りません。単独 N1 はローカル SSD で概ね1〜5秒、遅い overlay/CI では10秒級を見込むのが妥当です。これは実測ではなく静的見積りです。N2 は2 verifier と2 hash が先頭 drift で停止するため、通常はサブ秒級です。

### 1.8 失敗モードと回避

- 偽赤: actual SHA の literal 化  
  → actual は各 `root` の bytes を `hashlib` で直前導出する。

- 偽赤: known のより前の source が drift  
  → path を厳密な診断契約とするなら意図した赤。any-source 契約にするなら、前述の test-only ordered literal tuple を使う。

- 偽赤: N2 実行中に ROOT が並行編集される  
  → actual 算出と verifier 呼び出しを隣接させ、親は安定した worktree で実測する。N1 は tmp fixture なので影響を受けない。

- 恒真化: production の例外や `decision.refusals` から expected を作る  
  → expected を production 呼び出し前に構築し、production helper は使わない。

- 恒真化: prefix だけで4件とみなす  
  → N1 は `_assert_exact_refusals`、N2 は例外全文一致。

- 既存 node への副作用  
  → monkeypatch、module global の書換え、ROOT への書込みを行わない。N1 の Git 操作は node 固有 `tmp_path` 内だけ。N2 は read-only。

## 2. (P1)〜(P6) の判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| P1 | 要修正 | 自然 design drift は g7 が消しているため差分は実在する。一方、never-issued builder・public gate・4件集約・floor/budget・`allowed=False` は `:2395-2444` と重複する。正確には「制御フローは実質重複、payload oracle は純増」。 |
| P2 | 要修正 | 現行 bytes では同一になるが、「copytree だから常に同じ」は強すぎる。通常 source は `:428-471` で複製される一方、ccbench は `:480-484` で recorded pin に checkout され、known generator は resolver ではなく module `ROOT` を読む（`s1_known_axes_freeze.py:724`）。N1 は fixture、N2 は ROOT から別々に actual を導出すべき。 |
| P3 | 妥当 | N2 は test file 内だけの read-only direct verificationで、本番・artifact bytes・受理集合を変えない。直前の real gate node `:1370-1430` と組み合わせることで receipt が受理を担うことを固定できる。 |
| P4 | 妥当 | 4文字列を独立構成すれば `_assert_exact_refusals` の `len + set`（`:190-197`）で exact 化できる。production 側も holdout、known、floor、budget を別々に1件ずつ追加する（`s8b_oracle_driver.py:373-418`）。 |
| P5 | 要修正 | 「非決定的かもしれない」は誤り。`_iter_sources` の depth-first insertion/list order（`s1_known_axes_freeze.py:682-697`）と固定 JSON 順により決定的。ただし先行 source の新規 drift に対する brittleness は別問題。 |
| P6 | 要修正 | 非発火という結論は妥当だが、「freeze bytes を直接変えない」だけでは一般には不十分。DW-O09 の発火条件は [operations.md:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/operations.md:54)-`:61`、F39 は file 集合も preimage になり得ると警告している。本計画では新規ファイルなし、既存 path のみ、追加文字列に holdout の三軸 canonical encoding もないため非発火、と補強すべき。 |

## 3. 未解決の設計択一

1. known path を診断契約として `s8a_trigger_sweep.py` に固定するか、any-first-source 契約にするか。  
   T-103 が「現在の自然 drift vector の pin」なら literal path 固定を推奨します。一般的な legacy-red 保証なら ordered literal tuple 方式が適切です。

2. N1 の重量を許容するか。  
   g7 + N2 から論理的にはかなりの部分を合成できますが、自然 drift を public gate へ通した一体試験は得られません。親 brief の目的を維持するなら、約1回分の builder コストを受け入れて N1 を残すのが整合的です。

pytest は実行しておらず、緑とは判定していません。
````````

---

## 段 3 敵対相談 レンズ A (正しさ境界) — `lens-a.md`

原文 SHA-256 = `99d24c1747fa57282a6d6d54d1917c74159ae06b63515a58409e60f25b1962f9` / 12143 bytes / defang 3 箇所

````````text
NO-GO

pytest・変異実行はしていない。以下の KILL 判定はすべて静的な到達解析である。

### A-1 / blocker / 異常入力だけなので無条件拒否への退化を識別できない

根拠: `plan-v1.md:23-31,63-67,104-115`、`s8b_holdout_freeze.py:653-662`、`s1_known_axes_freeze.py:731-741`

期待値を `decision.refusals` や捕捉例外から作る直接的な恒真化はない。しかし両 node とも、事前に不一致だと確認した入力しか与えない。

具体的な失敗シナリオ:

- 入力: `design_source` が recorded と不一致。
- 変異: `s8b_holdout_freeze.py:659` を条件判定せず常に同じ `FreezeError` を投げる実装にする。
- 誤った結果: 一致する正当 artifact まで拒否する verifier に退化しても、N1/N2 の期待文字列は同じなので両 node は検出しない。

known 側も「`s8a_trigger_sweep.py` なら actual に関係なく拒否する」という退化で同様になる。既存の verifier 単体テストが一般的な無条件拒否を殺す可能性はあるが、新テスト固有の検出力ではない。

推奨対処: 段 4 でこの二 node を「受理条件の検査」ではなく「現在の負例の診断 payload 検査」と明記すること。受理条件まで主張するなら、matching positive control との対を必要とする。

### A-2 / blocker / exact path 固定は複数の偽赤を作る

根拠: `s1_known_axes_freeze.py:682-697,721-741`、`known_axes_freeze.json:29-54`、`s8b_holdout_freeze.py:709-711`、`holdout_freeze.json:5-15`

具体的な失敗シナリオ:

1. `orchestrator/campaign/axis_trigger_gating.py` に正当なコメント編集を加える  
   → known の先頭4件目が先に不一致  
   → legacy は依然正しく拒否し、gate の件数も4件のままだが、期待した `s8a_trigger_sweep.py` ではなくなり N1/N2 が失敗する。

2. `s1_known_axes_freeze.py` を正当に保守する  
   → module-level ROOT で generator hash が先に不一致になる (`:721-727`)  
   → source loop に到達せず、期待した known source refusal が消える。

3. holdout verifier の明示的な検査順を `design_source`→`generator` から逆にする  
   →受理集合は変わらないが、現在は generator も drift しているため generator refusal が先になる  
   → N1/N2 が失敗する。

4. `s8a_trigger_sweep.py` を recorded bytes に戻す  
   → known は次の `s6_sort_sweep.py` で依然拒否する  
   → 「legacy は赤」という目的は満たすのにテストだけ失敗する。

`_iter_sources` の順序は固定 bytes 上では決定的であり、乱択ではない。しかし「決定的」と「正しさ契約」は別である。現在の計画は `plan-v1.md:250-253` でこの択一を未解決のまま残している。

推奨対処: path を契約にしないなら、独立に求めた全 mismatch 候補のいずれか1件であることを検査する。path を契約にするなら、これは correctness ではなく「fail-fast 診断順」のテストだと明記する。未決のまま実装へ進めてはならない。

### A-3 / blocker / 自明な変異は既存テストが先に殺す

根拠: `s8b_oracle_driver.py:115-122,368-418`、`test_s8b_oracle_driver.py:1433-1481,2395-2444`

| 事前登録候補の変異 | 既存の静的 KILL |
|---|---|
| holdout legacy 呼出し `:373` を削除 | `test_t080_gate_hermetic_primary_states_exact:1461-1467` と g7 `:2438-2444` |
| known legacy 呼出し `:409-411` を削除 | 同上 |
| floor/budget refusal `:415-418` を削除 | real gate `:1382-1385`、primary states、g7 |
| `allowed=not merged` `:117` を退化 | g7 `:2437` ほか |
| refusal 時にも observation を漏らす `:119-122` | primary states `:1468,1471,1481`、stub-free B5 `:647` |
| never-issued 判定 `t080_freeze_migration.py:1640-1642` を変更 | builder の既存 assert `test_s8b_oracle_driver.py:487-491` |
| design source 比較を無効化 | `test_s8b_holdout_freeze.py:249-263,423-447` |
| known の一般 source 比較を無効化 | `test_s1_known_axes_freeze.py:142-155` |

新テスト固有になり得るのは、known refusal の `recorded=/actual=` suffix を落とす変異 (`s1_known_axes_freeze.py:740-741`) や `_iter_sources` の順序変更程度である。前者は診断 payload、後者は診断順であり、受理境界の correctness 変異ではない。

さらに、次の correctness 変異は計画した N1/N2 が殺せない。

- 変異: driver `:410` を `source_resolver=lambda relative: ROOT / relative` にして、呼出し側 `root` を無視する。
- N1: fixture と実 ROOT の `s8a_trigger_sweep.py` bytes が同じなので同じ refusal。
- N2: 初めから ROOT を使うので同じ refusal。
- primary states: verifier 自体を stub しているため引数を検査しない。
- g7: known source は変更していないため同じ refusal。

推奨対処: 段 4 ではこの root-isolation 変異を事前登録し、fixture 側だけ bytes が異なる driver-level control を追加すること。二 node のままなら、変異目標を「known 診断 suffix の保持」に狭めるしかなく、receipt correctness の新規 KILL と称してはならない。

### A-4 / blocker / 「stub なし」は字面だけで、known verifier は実 repo に漏れている

根拠: `test_s8b_oracle_driver.py:428-495,523-534`、`s8b_oracle_driver.py:408-411`、`s1_known_axes_freeze.py:718-766`

`issue_receipt=False` は `test_s8b_oracle_driver.py:493-495` で、fixture module を import して `module.ROOT == root` を確認する subprocess より前に返る。したがって N1 の gate は親 process で import 済みの実 repo moduleを使う。

known verifier では:

- source records だけが注入 resolver を使う (`:729-741`)。
- generator は常に module-level `ROOT` (`:724`)。
- frozen head と ccbench の Git 検査も module-level `ROOT` (`:748-757`)。
- 最終 `build_document` も内部で実 repo の WAL・source・submoduleを読む (`:759-766`)。

具体的な失敗シナリオ:

- fixture 内 generator を欠落・改変させる
- N1 を実行する
- verifier は fixture generator を見ず実 repo generatorを読むため、その欠陥を見逃す

現状は source record 5件目で停止するため Git 検査と再構成まで一度も到達しない。「legacy verifier を stub しない」は関数差替えの意味では守られているが、「fixture に対する実 verifier」という核心は成立していない。

推奨対処:

- test-only 対処: fixture root を `sys.path[0]` に置いた隔離 subprocess で gate を実行し、builder の child と同様に全 module ROOT が fixture を指すことを assert する。
- 裁定パッケージ候補（本 wave scope 外）: `s1_known_axes_freeze.verify_document/verify` に完全な root context を導入し、generator・Git・ccbench・再構成をすべて同じ root に束縛する。本 wave で実装したふりをしてはならない。

### A-5 / must-fix / 親の実測説明は「現時点」なら合うが一般化が過大

根拠: `probe-output.txt:1-19`、`t080_freeze_migration.py:1640-1642`、`s8b_oracle_driver.py:368-418`

独立な静的照合結果は次のとおり。

- fixture never-issued、receipt refusal 0件、observation `None`: コード上成立する。
- 現在の gate refusal 4件: 成立する。legacy 2本はそれぞれ fail-fast で最大1件、さらに floor/budget が各1件。
- fixture と実 repo の表示された2 payload: 現在は同一。design と `s8a_trigger_sweep.py` が copyfile/copytree で同じ bytesになるため。
- holdout の JSON object 順への非依存: 狭い意味では正しい。named field を明示順で検査する。
- known drift「3件」: unique path 数なら正しいが、source record 数は12件である。`t080_freeze_migration.py:86-99` に同じ3 pathの12 repin cellが列挙されている。

ただし holdout には、表示された design drift のほか generator drift も存在する。`test_s8b_oracle_driver.py:178-181` が recorded `1910…`、actual `41c0…` を既に固定している。4 refusal は「潜在 drift が4個だけ」という意味ではない。

具体的な失敗シナリオ: design drift だけを直す  
→ holdout は generator drift でなお拒否  
→ gate は依然4件だが期待 payloadだけ変わる。  
親の「ちょうど4件」を underlying defect 数として扱うと誤った裁定になる。

推奨対処: brief の P2/P4 を「この snapshot の fail-fast 表示が4件」に修正し、known は「12 record / 3 unique path」、holdout は「少なくとも design と generator の2 field drift」と記す。

### A-6 / must-fix / N2 は live working tree の非原子的 sentinel

根拠: `plan-v1.md:63-67,227-228`、`s8b_holdout_freeze.py:658-662`、`s1_known_axes_freeze.py:735-741`

N2 は test 側で actual hash を読み、その後 verifier が同じ path を再読する。隣接させても snapshot や lock にはならない。

具体的な失敗シナリオ:

- test が expected hash を計算
- 並行セッションが対象ファイルを正当に更新
- verifier は新 bytes を読む
- verifier 自体は正しいのに expected と diagnostic actual が食い違って失敗する

また N2 は public gate ではなく、変わり続ける実 worktree の一時的性質を固定するだけである。テストファイルだけという byte scope には収まるが、安定した product invariant とは言い難い。

推奨対処: N2 を削り、N1 の隔離 snapshotだけに寄せる。残すなら exact current path ではなく「独立に確認した mismatch 候補のいずれか」という integration sentinel に格下げし、通常の hermetic unit 契約と分離する。

### A-7 / nit / 既存 node への間接副作用経路がある

根拠: `test_s8b_oracle_driver.py:428-445,602-839`、`t080_freeze_migration.py:1316-1320,1557-1560`

fixture は `orchestrator/` 全体をコピーして commit する。したがって追加するテストコード自体が、既存 `issue_receipt=True` の stub-free node が実行する holdout repository scan の入力になる。

具体的な失敗シナリオ:

- 同じテストファイルに `ycsb_rratio＝80`、`ycsb_zipf_skew＝0.9`、`ycsb_rmw＝0` の3 encodingを同居させる
- 既存 B5/F28 fixture がそのファイルをコピー
- draft の live scan が未知性 hit と判定
- T-103 と無関係な既存 node 群が失敗する

今回計画された hash/path/refusal literalsだけではこの conjunction は生じない。ただし N1 はさらに copytree、Git commit、submodule addを1回増やし、容量・timeout由来の偽赤面も広げる。

推奨対処: 新規コードに三軸 canonical encodingを同居させないことを実装レビュー項目に加える。fixture builder 自体は変更しない。

## 攻撃したが破れなかった点

- 期待値を `decision.refusals`、捕捉例外、production `_sha256/_iter_sources` から作る直接的な恒真化はない。
- `_assert_exact_refusals` の `len + set` は余分・欠落・重複を正しく検出する。
- 固定された freeze bytes 上の `_iter_sources` 順は決定的であり、乱択依存ではない。
- holdout の JSON key insertion order は検査対象 field の選択に影響しない。
- 現 snapshot では、fixture と実 repo の表示 payload 同一、および refusal 4件は静的に再確認できた。
- N1/N2 本体が legacy verifier や `verify_receipt` を mock/monkeypatchする計画にはなっていない。
- 純追加で module globalを書き換える案ではないため、既存 node への直接的な状態汚染は見つからなかった。
- g7 とN1は完全な複製ではない。g7 は復元後の人工 generator tamper、N1は自然 driftと exact known payloadを対象にする。
````````

---

## 段 3 敵対相談 レンズ B (整合・実効性) — `lens-b.md`

原文 SHA-256 = `db0cf16a9e595f90abdc7dc043cb6a6719e4a24910e2ba02e589f90574090950` / 15002 bytes / defang 0 箇所

````````text
NO-GO

2 node のまま進める費用対効果は成立していない。N1 を軽量 fixture へ置換し、N2 を落とし、価値主張を「受理集合の保護」から「legacy 診断 payload の固定」へ縮めるべきである。

### B-1 / blocker — 既存被覆との重複が大きく、N2 は N1 に対して限界検出力がない

**根拠:** [test_s8b_oracle_driver.py:1370](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1370)、[同:1433](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1433)、[同:2371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:2371)、[同:2395](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:2395)

| 既存 node | 既に固定済みの assert | N1/N2 に残る差 |
|---|---|---|
| `...public_driver_gate_g7` | 同一 builder、never-issued、実 legacy verifier、4件、generator 全文、known 1件、floor/budget、`allowed=False` | N1 は holdout の自然 `design_source` 全文と known 全文だけ |
| `...primary_states_exact` | never-issued→legacy 委譲、exact 4件、observation `None` | N1 は stub を実 verifier に置き換えるだけ |
| `...real_freeze_gate...` | real ROOT、active-valid、floor/budget exact、`allowed=False`、observation `None` | N2 は receipt が迂回した legacy 例外を直接観測するだけ |
| `...legacy_generator..._b7` | `_verify_source` の generator 改竄例外全文 | N1 は design で先に停止するため generator 検出は増えない |

**N1 の新規検出力（1行）:** 無改変コピー上の holdout が最初に `design_source` で倒れることと、既に g7 が実発火している known 拒否の全文 payload を固定する。

**N2 の新規検出力（1行）:** baseline 比では real ROOT 上の二つの「最初の legacy 例外全文」を固定するが、N1 も採るなら production 変異の kill set は実質 N1 の部分集合であり、増えない。

**失敗シナリオ:** verifier の同じ書式・走査順変更で N1/N2 が同時に落ちる。N2 は原因局在化には役立つが、新しい退行を捕捉していない。

**推奨対処:** public gate 一体試験を残すなら N1 だけにする。P1 の「自然 design drift は g7 未被覆」は狭くは正しいが、P3 の「N2 が独立検出力を持つ」は退ける。

### B-2 / blocker — 「receipt が受理を担う」は実際の gate 判定と矛盾する

**根拠:** [brief.md:31](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/brief.md:31>)、[plan-v1.md:77](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/plan-v1.md:77>)、[s8b_oracle_driver.py:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:111)、[同:415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:415)、[test_s8b_oracle_driver.py:1378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:1378)

active-valid receipt は legacy 2拒否を消すが、real v1 freeze には必ず floor/budget の2拒否が残る。既存テスト自身も `not decision.allowed` を要求している。独立した read-only 直接呼出しでも、real gate は `allowed=False`、refusal は floor/budget の2件だった。

| 成果物 | T-103 対象変異で変わるか |
|---|---|
| certified 選択・受理集合 | 変わらない |
| 材料レポート | 生成経路に到達しない |
| proof chain / verdict | 変わらない |
| 試行台帳・WAL | gate 後なので作られない |
| 実際に変わる値 | standalone gate の `refusals` 診断文字列だけ |

**失敗シナリオ:** legacy 2呼出しが消えても、現物 freeze は floor/budget で拒否されたままで、campaign も試行も一件も増えない。T-103 は診断退行を捕捉するが、成果物受理の退行は捕捉していない。

**推奨対処:** wave の価値を「receipt が受理を担う」ではなく「never-issued 時の legacy 診断 ABI を固定する」に縮める。受理集合への実効性を求めるなら production policy の裁定が必要であり、本 wave の scope 外候補とする。

### B-3 / must-fix — 全層 scope は入っていない。ただし自然 drift 経路では下流が到達不能

**根拠:** [t080_freeze_migration.py:1640](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1640)、[同:1851](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/t080_freeze_migration.py:1851)、[s8b_oracle_driver.py:1040](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:1040)、[同:1211](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_driver.py:1211)、[s8b_oracle_report.py:238](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_report.py:238)、[同:1653](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_oracle_report.py:1653)

| 層 | T-103 の扱い |
|---|---|
| receipt history / `verify_receipt` | N1 内で間接呼出しのみ。state の直接 assert はない |
| standalone driver gate | N1 の対象 |
| `run_block` campaign-start / result | scope 漏れ |
| WAL・budget ledger | scope 漏れかつ本 vector では到達不能 |
| report の never-issued 歴史照合 | scope 漏れ |
| judge・材料・proof chain | report row の間接 consumer。直接 T-080 consumer ではない |
| floor protocol 凍結 | active-valid 必須の別 consumer。既存 inactive receipt テストあり |

既存 suite には mocked receipt による campaign 伝播テストと report テストがあるが、report 側は autouse monkeypatch で Git 履歴から隔離されている（[test_s8b_oracle_report.py:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_report.py:74)）。

**失敗シナリオ:** `_campaign_t080_value`、campaign-start WAL、report の歴史再照合が壊れても N1/N2 は通る。

**推奨対処:** 実装したふりをせず、次を別の裁定パッケージ候補にする。

1. real never-issued Git 履歴→`run_block` campaign-start/result/WAL の test-only 統合。
2. driver 生成 WAL→real history を使う report→judge の test-only 統合。
3. never-issued を成果物選択へ影響させるべきかという production policy。これは明確に scope 外。

### B-4 / must-fix — 重量見積りは一部正しいが、N1 にその重量は不要

**根拠:** [test_s8b_oracle_driver.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:428)、[同:442](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:442)、[同:480](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:480)、[plan-v1.md:198](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/plan-v1.md:198>)

call site 6箇所、parameter 展開後11実行、N1 後12実行、builder cohort 比 +9.1% は正しい。

一方、親の「31.4 MB・2,347 files」は ignore 前の全ファイル集計で、実際の copytree payload ではない。静的列挙では以下だった。

- `output`: receipt 除外後 1,842 files / 19,256,257 bytes
- `orchestrator`: `__pycache__`・`*.pyc` 除外後 247 files / 5,050,725 bytes
- required 再copy: 35操作 / 580,673 bytes
- ccbench worktree: 405 files / 2,351,698 bytes

追加1回は約27.24 MBのファイル書込みに加え、同程度のsource read、`git add -A`による再読、commit/object、履歴検査を行う。親の「1–5秒、overlay 10秒級」は未実測の推測で、静的検査からは保証できない。

**失敗シナリオ:** 無関係な `output/` 追加、cache、権限、容量、submodule 状態で診断テストが遅延・失敗する。

**推奨対処:** `_t080_repo(tmp_path, receipt="never-issued")`（[同:376](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:376)）を使い、artifact 2件と参照source集合だけをコピーする。source は約0.5 MiBで、現行 first mismatch への到達に全 `output/`、全 `orchestrator/`、submodule add は不要。同じ public gate・実 verifier・no mock を維持できる。

### B-5 / must-fix — 正当な強化や修復を赤にする brittle な契約である

**根拠:** [plan-v1.md:27](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/plan-v1.md:27>)、[同:171](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/plan-v1.md:171>)、[s1_known_axes_freeze.py:682](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s1_known_axes_freeze.py:682)、[同:731](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s1_known_axes_freeze.py:731)

正当な赤化要因は少なくとも次の通り。

- 先頭4 source の一つが drift し、最初の path が変わる。
- verifier が fail-fast から全 drift 集約へ強化される。
- design/s8a source が recorded bytes に戻り、legacy artifact がより適合する。
- 診断文言に reason code や path 情報が追加される。
- N2 の期待 hash 算出と verifier 呼出しの間に ROOT が編集される。
- legacy freeze の正当な廃止・再凍結で literal が更新される。

特に `assert actual != recorded` は「legacy が修復されるとテスト失敗」という逆向きの圧力を作る。重い一体試験が無関係変更でも落ちると、担当者が exact assert を prefix 化・削除する誘因になる。

**推奨対処:** mismatch を一つに隔離した最小 fixture にする。known の自然 verifier 発火は g7 の prefix+件数で既に担保されているため、T-103 は未被覆の design-source だけを追加する。全文を公開 ABI にするなら、その判断を明記してから pin する。構造化 reason の新設は production 変更なので別裁定候補とする。

### B-6 / must-fix — 実測値は再現したが、親の意味付けと P2 は過大

**根拠:** [probe-output.txt:1](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/probe-output.txt:1>)、[brief.md:24](</home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t103/brief.md:24>)、[s1_known_axes_freeze.py:724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s1_known_axes_freeze.py:724)

独立に確認できた値は以下のとおり。

- legacy 2本の例外型・全文・hash は親値と一致。
- known の unique drift path は3件で一致。最初の4 source は一致し、5件目が `s8a_trigger_sweep.py`。
- holdout は design と generator が drift、known artifact raw は一致、floor/budget は `None`。
- R 導入 commit、R raw SHA、artifact raw SHA、ccbench HEAD は親値と一致。
- read-only 公開呼出しで receipt は active-valid、real gate は floor/budget だけを持つ `allowed=False`。
- never-issued fixture の4件は、builder のreceipt除外・検証順・hashから静的に再導出できる。

ただし P2 の「copytree だから同一」は一般保証ではない。known generator/head/ccbench の一部は fixture resolver でなく module `ROOT` を読む。現状同じ payloadになるだけで、fixture の完全 hermetic 性から導かれるわけではない。

また `probe-output.txt` は command、rc、commit、環境タグを持たず、「raw 出力」としての再現性は弱い。

**失敗シナリオ:** module ROOT とfixture bytesが分岐しても、「copytreeだから同一」という説明が誤った oracle を正当化する。

**推奨対処:** P2 を「現行 bytes と pin の下で一致」と限定し、probe には実行command・rc・HEADを添える。受理に関する意味付けは B-2 のとおり修正する。

### B-7 / nit — 配置は妥当、命名は由来規約と実体がずれる

**根拠:** [test_s8b_oracle_driver.py:602](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:602)、[同:812](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:812)、[同:2371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:2371)、[同:2395](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_oracle_driver.py:2395)

`_b5/_f28/_b7/_g7` は過去の敵対所見・裁定由来の識別子として使われている。同ファイル内で `_t103` へ名前空間を切り替える説明はない。また N1 の fixture は ROOT の「real artifact」そのものではなく、新規Git repoへコピー・再配置したものなので `unmodified_real_artifacts` は誤読を招く。

**失敗シナリオ:** 将来の担当者が ROOT 直接テストと hermetic copy テストを名前から区別できない。

**推奨対処:** 2本残すなら `_t103_n1/_t103_n2` とし、N1 は `copied_legacy_artifacts` と呼ぶ。挿入位置自体は、N2をreal gate直後、N1をg7直後とする案で整合している。

## 攻撃したが破れなかった点

- g7 が design/generatorを復元後にgeneratorだけを改竄し、known artifactは未変更という親の比較は正しい。
- 「自然 design drift」は既存 g7 に存在せず、N1 に狭い純増検出力はある。
- `_assert_exact_refusals` の `len + set` は欠落・余分・重複を検出できる。
- never-issued が legacy verifier へ委譲される production 結線は実在する。
- 現行 bytes では fixture とROOTの二つの refusal payload は一致する。
- source 34 path / 約0.5 MiB、builder 6 call site / 11実行という親の数え方は正しい。
- 現行 JSON 順では `s8a_trigger_sweep.py` が決定論的に最初のknown mismatchになる。
- 提案された二つの挿入位置は局所的なテスト配置として妥当。

pytest は実行しておらず、テスト結果の緑・赤は判定していない。
````````
