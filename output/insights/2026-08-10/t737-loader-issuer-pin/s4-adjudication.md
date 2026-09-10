# [T-737] 段 4 裁定 — plan v2 と変異事前登録

レンズ A (gpt-5.6-sol、正しさ境界) / レンズ B (gpt-5.6-luna、scope・実効性) の所見 14 件を裁定した。
親は所見を鵜呑みにせず、争点はコードで再確認した (下記「親の再確認」)。

## 親の再確認 (子の申告でなく親が読んだ事実)

1. `env_contract.py:519-548 _load_authority_snapshot` は、`load_activation_state` を **先に**呼び、
   例外を `EnvContractError("activation authority 検証失敗: …")` に包む。
   `_verify_entry_calibration` の loop (`:535-542`) は **load が成功した後**にしか走らない。
   → **遷移違反の負例は、合成 registry でも calibration を一切要求せずに production loader を通せる。**
   A-01 の修正案は成立する。
2. `orchestrator/campaign/ident.py:211-223 _load_current_activation_state` と
   `:292-310 verify_recorded_activation_tuple` は、`env_contract` の wrapper を経ずに leaf を直接呼ぶ。
   前者は certified campaign lock の新規作成 (`:236`)、後者は既存 lock の再検証に使われる。
   → B-02 は real。これは選択肢 G が名指す 2 層とは別の **第 3 の production 経路**である。
3. `tools/issue_env_contract_activation.py:160-163` は `Path(__file__).resolve().parents[1]` を
   sys.path へ挿入する。`issuer.__file__` を tmp へ patch すると tmp path が sys.path へ残る。
   負例は publish に到達しないため `__file__` patch を必要としない
   (`repo_root` は `_activation_handoff` の `relative_to` でしか使われない)。

## 所見の裁定

| ID | 判定 | 採否 | scope | 対応 |
|---|---|---|---|---|
| A-01 / B-01 | **real・blocker** | 採用 | 内 | 層 1 の負例 2 本を `ec.current_activation_state()` 経由へ上げる。leaf 直呼びは廃止 |
| A-02 | real | 一部採用 | 内 | 負例では `issuer.__file__` を patch しない。正例のみ patch し `sys.path` を復元する。名乗りは「合成 registry を注入した `issuer.main()` の integration」とし E2E を名乗らない |
| A-03 | real | 採用 | 内 | 変異 matrix を「純増 (N≥4)」と「層到達 (N≤3)」に分ける。純増は N=4/8/64 だけを数える |
| A-04 | real | 採用 | 内 | 正例を loader 用と issuer 用の 2 nodeid に分割する |
| A-05 / B-07 / B-08 | real | 採用 | 内 | 記録側の是正。call site / test node / live pin / 歴史参照を分けて数える。「外部 pin 0 件」は「ファイル名を直接参照する pin は 0 件」へ限定する |
| A-06 | real | 採用 | 内 | frontier は「M=65 の fixture に対して N≤64」と限定して記録する。N≥65 は program-equivalent でなく fixture-equivalent |
| B-02 | **real** | **不採用 (scope 外)** | 外 | `ident` 経路は選択肢 G が名指す 2 層に含まれない。実装せず裁定パッケージでユーザーへ返す |
| B-03 | real・条件付き | 採用 (別形) | 内 | t720 の import 変更を先行条件にはしない。代わりに issuer node へ fail-closed guard を入れる (下記) |
| B-04 | real (計数) | 採用 | 内 | 合成 registry を module 単位で 1 度だけ構築する。増分時間は親が実測する |
| B-05 | real・将来 | 不採用 (scope 外) | 外 | 実 registry 成長時の追随は裁定パッケージへ |
| B-06 | real (誇張) | 採用 | 内 | DW-G05 の記述を「registry には存在するが承認済み transition ではない世代」へ是正する |

## plan v2 (確定形)

編集面は `orchestrator/tests/test_env_contract_activation.py` **のみ**。production 無編集。

### 合成 registry (module 単位で 1 度だけ構築)

- `_PIN_ENV_COUNT = 65`、env_tag は `pin-env-000`〜`pin-env-064` (ゼロ埋めで sorted 最後が `064`)。
- `ec.GENERATIONS["linux-baremetal"][0].contract` を基礎に `dataclasses.replace` で
  `env_tag` と `calibration_ref` だけを変える。全 env に g1/g2、最後の env だけ g3。
- `ec.validate_generations()` を factory 内で通す (fixture 自身の前提検査)。
- catalog は production `_build_registered_contract_catalog` と同じ変換で作る。
- **`functools.lru_cache` 等で 1 度だけ構築し、node ごとに作り直さない** (B-04)。

### 層 1 (production loader) — 負例 2 本、入口は `ec.current_activation_state()`

`_use_authority` と同じ seam (`_ACTIVATION_DIRECTORY` 絶対 path、head serial、head hash、
`_clear_authority_cache_for_tests`) に加えて `ec.GENERATIONS` と
`ec._REGISTERED_CONTRACT_CATALOG` を差し替える。

1. `test_production_loader_rejects_generation_skip_at_last_of_65_envs`
   serial 2 は先頭 64 env が g1→g2、最後だけ g1→g3。
   `ec.EnvContractError` を expect し、message に `activation authority 検証失敗` と
   `exactly +1` と `pin-env-064` と `g1 -> g3` を要求する。
2. `test_production_loader_rejects_invalid_successor_at_last_of_65_changed_envs`
   serial 2 は 65 env 全部 g1→g2。`ec.is_valid_successor` を
   「最後の env_tag のときだけ False、他は元の実装」に patch する
   (`_is_valid_activation_successor` は patch しない)。
   `ec.EnvContractError` に `successor でない` と `pin-env-064` を要求する。

### 層 2 (発行 tool) — 負例 2 本

3. `test_issue_main_rejects_generation_skip_at_last_of_65_envs_without_publishing`
4. `test_issue_main_rejects_invalid_successor_at_last_of_65_changed_envs_without_publishing`

- monkeypatch は `ec.GENERATIONS` / `ec._REGISTERED_CONTRACT_CATALOG` /
  `ec.current_activation_state` / `ec._ACTIVATION_DIRECTORY` (tmp の絶対 path)、
  P 負例のみ `ec.is_valid_successor`。**負例では `issuer.__file__` を patch しない。**
- `SystemExit.code == 1`、stderr の逐語、`tmp authority / "00000002.json"` 不在を assert。
- **fail-closed guard (B-03):** `main()` 呼び出しの前に
  `sys.modules["campaign.env_contract"] is ec` を assert し、呼び出しの後に
  **実 repo の `orchestrator/campaign/env_contract_activations/` の entry 名集合が
  呼び出し前と一致する**ことを assert する。issuer が別 module object を掴んで
  実 authority へ publish した場合に、黙って通さず赤で止める。

### 正例 2 本 (A-04 により分割)

5. `test_loader_leaf_accepts_65_env_plus_one`
   — 入口は `activation.load_activation_state` (leaf)。65 env 全部 g1→g2 が受理される。
   **production loader 層の M=65 正例は作らない** (65 本の合成 calibration 成果物が要るか、
   `_verify_entry_calibration` を patch して correctness gate を迂回することになるため)。
   production loader 層の過剰拒否は、実 2 env の既存正例 (`:1471` 系) が担う。
   この限定を worklog へ書く。
6. `test_issue_main_accepts_65_env_plus_one_and_publishes`
   — `issuer.main()` が rc=0 で `00000002.json` を publish する。ここだけ `issuer.__file__` を
   tmp へ patch し、**node 終了時に `sys.path` を元へ復元する** (A-02)。同じ実 authority guard を張る。

### 名乗り (誇張しない)

- 層 1 = production loader (`ec.current_activation_state()`) を**負例で**通した。正例は leaf 止まり。
- 層 2 = 合成 registry を注入した `issuer.main()` の integration。production authority を含む E2E ではない。
- `ident` 経路 (certified lock) は**未被覆**。裁定パッケージへ返す。

## 変異事前登録 (DW-M01 / DW-M04 / DW-M08)

anchor はいずれも `orchestrator/campaign/env_contract_activation.py` に 1 箇所 (grep -c で確認済み)。

- 量化点 G: `    for successor in successor_rows:` (`:275`)
- 量化点 P: `    for predecessor, successor in changed:` (`:300`)
- 過剰拒否: `        if successor.generation != predecessor.generation + 1:` (`:285`)

**単一理由性の確認 (DW-M01):** 合成 record の g3 は catalog に登録済みなので
`validate_activation_records` の registry 照合 (`:384-393`) では拒否されない。env 集合も catalog と
exact 一致する。したがって負例が赤くなる理由は transition gate だけである。

### spec A — 新 pin の検出力 (runner argv = 新 6 node、commit = fix 後の統合 commit)

| id | 置換 | 期待 | expected_nodes |
|---|---|---|---|
| G-N1 | `successor_rows[:1]` | KILLED | 負例 4 本 (loader G/P、issuer G/P) |
| G-N4 | `successor_rows[:4]` | KILLED | 同上 |
| G-N8 | `successor_rows[:8]` | KILLED | 同上 |
| G-N64 | `successor_rows[:64]` | KILLED | 同上 |
| P-N1 | `changed[:1]` | KILLED | P 負例 2 本 (loader P、issuer P) |
| P-N4 | `changed[:4]` | KILLED | 同上 |
| P-N8 | `changed[:8]` | KILLED | 同上 |
| P-N64 | `changed[:64]` | KILLED | 同上 |

G 縮退が P 負例も殺すのは cross-kill (最後の changed row 自体が作られない)。
P 縮退は G 負例を殺さない (+1 逸脱は G の loop で捕まる)。

### spec C — 過剰拒否の正例 (runner argv = 正例 2 node のみ、commit = 同上)

| id | 置換 | 期待 | expected_nodes |
|---|---|---|---|
| OVERREJECT | `!= predecessor.generation + 1` → `!= predecessor.generation` | KILLED | 正例 2 本 |

runner argv を正例 2 node に絞るのは、負例側の赤理由が message match 経由で過剰決定になるのを
避けるため (DW-M03 の単一理由性)。

### spec B — 変更前 HEAD 版テストの検出力 (runner argv = 同ファイル全体、commit = `7a84b638`)

| id | 置換 | 期待 | expected_nodes |
|---|---|---|---|
| G-N4 | `successor_rows[:4]` | SURVIVED | (空。DW-M08 の field 契約) |
| G-N64 | `successor_rows[:64]` | SURVIVED | (空) |
| P-N4 | `changed[:4]` | SURVIVED | (空) |
| P-N64 | `changed[:64]` | SURVIVED | (空) |

これで **純増検出力 = N ∈ {4, 8, 64} (一般に 4 ≤ N ≤ 64)** を実測で示す。
N ≤ 3 は既存 77 node が既に殺すため純増ゼロであり (A-03、`:571` `:921` `:939` `:966`)、
新 node の赤は「新しい層でも発火する」層到達の証拠としてのみ記録する。

## 裁定パッケージ候補 (実装せずユーザーへ返す)

1. **[B-02] `ident` 経路が未被覆。** `ident.py:211` / `:292` が leaf を直接呼び、certified campaign
   lock の新規作成と再検証に使われる。選択肢 G は「2 層」としか言わないため本 wave では実装しない。
   放置すると、量化縮退が入ったときに campaign.lock の activation tuple が承認外 transition へ
   束縛され、`admission_status="admitted"` の受理集合に入りうる。
2. **[A-01 の残余] production loader 層の M>N 正例が無い。** 65 本の合成 calibration 成果物を作るか、
   `_verify_entry_calibration` を patch するかの択一。後者は correctness gate の迂回になる。
3. **[B-05] 実 registry が 3 env 以上へ育ったときの追随。** 合成 65 env の pin は壊れないが、
   実件数依存の縮退 (`[:len(GENERATIONS)]` 等) は素通りする。
