# 段 4 裁定 — dev-wave-t750-freeze-v2-manifest

親が段 3 の 2 レンズ (A = 正しさ境界 / B = 整合・実効性) の所見を real/refuted・採否・scope 内外へ
裁定し、プラン v2 を確定する。**両レンズとも NO-GO** (BLOCKER は A が 4 件、B が 3 件)。

## 段 4 で親が追加実測した 4 点 (裁定の根拠)

- **N-1**: `s8b_holdout_freeze.verify()` を実 repo に対して直接呼ぶと **今すでに RED** であり、
  理由は generator ではなく **`design_source sha256 不一致`** (`docs/phase3-8b-descriptor-design.md`
  の drift、`verify_document:716` が `:718` の generator 照合より前に落とす)。
- **N-2**: `s8b_oracle_judge.py:194-203` に **部分的な product 検査が既に存在する**
  (`expected-product` = configuration 集合が holdout 間で不一致なら拒否)。
  ただし**全 holdout で一様に 1 configuration へ間引いた schedule は通る**。
- **N-3**: `s8b_oracle_driver.py:1119-1129` の `run-block` は **任意の `--manifest` path** を受け取り、
  `verify_manifest` に通すだけである。**choke point は CLI ではなく `verify_manifest`**。
- **N-4**: `verify_manifest` は既に `freeze_document` を受け取り、`_holdout_configuration_ids`
  (`:530-559`) で各 holdout の構成集合を読んでいる。既存 manifest テストの `CONFIGURATION_IDS`
  (`test_s8b_oracle_manifest.py:26-29`) は実 freeze の `variant_binding.entries` と **完全一致**する
  (実測: 両 holdout とも 6 構成が exact 一致)。

## 所見の裁定

### real・採用 (実装へ反映する)

- **A-1 (Git trailer は人間認可の証明にならない)**: real。プランの「非 merge commit +
  逐語 `AI-Agent: none` を承認根拠にする」形は D86(8) に抵触する **恒真化**である。
  → **採用 (ただし直し方は親が差し替える)**。承認 authority を **module 内の pinned literal**
  (`V1_FREEZE_SHA256` / reviewed golden と同型) にする。**未承認のうちは定数を `None` にし、
  CLI・producer は fail-closed で止まる**。AI が承認者になるには**コード diff を人間が
  レビューして定数を置く**しかなく、自己生成 JSON では通らない。approval 発行 CLI・
  `--approver`・既定補完は実装しない。
- **A-5 (新 writer は堅いが旧 writer から canonical namespace へ到達できる)**: real。
  → **部分採用**。新設経路 (v2 candidate writer / manifest CLI writer) は
  dirfd + `O_NOFOLLOW` + `O_EXCL` + 候補 root 限定で閉じる。**旧 API
  (`generate --output` / `write_manifest`) の受理集合は狭めない** (不変条件 1 と衝突するため。
  残余は裁定へ)。
- **B-4 (`measurement_closure` の commit/handoff 契約不足)**: real。
  → **採用**。producer は closure を自ら再導出し、**generation commit へ入らない closure が
  あれば candidate を作らない** fail-closed とする。
- **B-8 (P5 の所有が素集合でない)**: real。
  → **採用**。`test_s8b_ratified_freeze.py` は **単位 B の所有**と明示する。
  共有 fixture (`s8b_v2_freeze_fixture.py`) は**単位 A / B の並列投入前に親が直列で確定**する。
- **B-9 MINOR (M-4 / M-5 の一般化が過大)**: real。→ **採用 (親の実測を訂正)**。
  M-4 は「**approved-manifest builder CLI が不在**」に限定する (driver / report / judge の CLI は実在)。
  M-5(ii) は「**全 product への拘束が不在**」に再定義する (judge に部分検査あり = N-2)。

### real・親の実測の訂正 (自分の M-1 を直す)

- **A-4 (同一 module の編集と v1 受理集合不変は両立しない)**: **機序は real、結論は refuted**。
  親の M-1 は「T-080 受領証が generator sha を metadata-only で受理済みだから」と書いたが、
  実際に direct `verify()` を守っているのはそこではない (N-1)。**direct 経路は
  `design_source` の drift で既に RED** であり、本 wave の編集の前後で受理集合は
  ∅ のまま変わらない。tmp root を使う既存テストは doc 側に自 root の generator sha を
  記録するため自己整合が保たれる。→ **不変条件 1 は成立する**が、根拠は M-1 の記述ではなく N-1。

### real・scope 外 → 裁定パッケージへ (`DW-S04`。親は不採用にしない)

- **A-2 / B-1 (A-9 は generic 経路で迂回でき、approved CLI は誰も呼ばない)**: real。**BLOCKER**。
  N-3 のとおり choke point は `verify_manifest` である。
  **本 wave は choke point 側の最小封鎖だけを実装する** (下記 plan v2 の B-1) が、
  **manifest schema へ `spec_sha256` を持たせて driver / report / judge 全層で
  approved spec を再検証する案は scope 拡大** ([T-782] で不採択となった (a) 側) のため
  実装せず、新事実つきで裁定へ返す。
- **A-3 (budget approval が ratified proof chain から消える)**: real。**BLOCKER**。
  v2 schema・transition table・equality chain のどこにも budget authorization の edge が無い。
  構造化 field の追加は **transition table の変更**を伴い、不変条件 3 に抵触する。
  → 実装せず裁定へ返す (択 = v2 schema へ `budget_authorization` を追加 / `refreeze_note` の
  監査文字列に留める / 世代交代 [T-657] と合流させる)。
- **A-5 残余 (旧 writer の任意 path 受理)**: real。旧 API を狭めると v1 受理集合が変わる。→ 裁定へ。

### refuted / 不採用

- **A-1 の直し方「人間だけが保持する鍵による署名」**: 方向は real だが、本 repo に
  鍵管理の trust root は存在せず、新設は D86 の再裁定を要する。**本 wave では不採用**
  (裁定パッケージの択として返す)。
- **B-3 (A-12 により production candidate は作れない)**: **partial・不採用**。
  「実 floor result が無い」は事実だが、**ユーザー裁定が「実走データ生成は W-1 の決着まで
  synthetic fixture のみ」と明示的に受諾済み** (worklog 405)。synthetic 限定であることを
  理由に実装を止めるのは、裁定済み前提を親が覆すことになる。
- **B-6 / B-7 (driver→report→judge の実経路テスト / 変異の単一理由)**: 方向は real。
  実経路テストは A-2/B-1 が裁定されるまで対象が確定しないため、**本 wave の変異は
  choke point (`verify_manifest`) と producer 側に限定**して単一理由性を確保する (下記 `DW-M01`)。

## プラン v2 (実装するもの)

### 単位 A — W-3 freeze v2 g1 candidate producer (`s8b_holdout_freeze.py`)

段 2 プラン §単位 A をそのまま採る。ただし次を差し替える。

- **budget 承認 authority を pinned literal にする** (A-1 の裁定)。
  `BUDGET_APPROVAL_SHA256: Optional[str] = None` を module 定数として置き、
  producer は「定数が `None` なら **`budget-approval-not-ratified` で fail-closed**」とする。
  非 `None` のときだけ、固定 path の approval record raw bytes の sha256 と定数の exact 一致を
  要求し、さらに `approval["budget"]` と入力 budget の **canonical bytes 完全一致**を要求する。
  **Git commit message / trailer を承認根拠にしない** (段 2 プラン `:41` `:245` を破棄)。
- `measurement_closure` は producer が再導出し、closure の各 path が
  captured HEAD の blob として存在しなければ candidate を作らない (B-4)。
- 出力 gate は段 2 プラン `:153-165` の `SafeA` 署名をそのまま採用する。
  **通る正例 = `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` 1 件のみ。**

### 単位 B — choke point 封鎖 + reviewed spec + manifest CLI

- **B-1 (新規・最重要): `verify_manifest` へ cell-product 検査を足す。**
  schedule の cell 集合が **`{(h, c) | h ∈ freeze.holdouts ∩ schedule.holdouts,
  c ∈ _holdout_configuration_ids(freeze, h)}` と exact 一致**しなければ拒否する。
  これは **`build_manifest` ではなく `verify_manifest`** に置く (N-3 の choke point)。
  N-4 のとおり既存テストの構成集合は実 freeze と完全一致するため、正当な manifest は通る。
  **これは [T-782](b) の文言 (CLI が hash 照合するだけ) を超える追加である。**
  理由 = (b) の機構だけでは A-9 (certified 選択の直接改変) が閉じないことを N-2/N-3 で実測したため。
  方向は **受理集合の縮小のみ**で、fail-open 方向の変更を含まない。段 7 で明示的に記録し、
  裁定パッケージにも「事後承認を求める項」として載せる。
- **B-2: reviewed spec schema + validator** を新 module `s8b_oracle_spec.py` に置く。
  段 2 プラン §単位 B/C の schema をそのまま採る。承認は **pinned literal**
  (`APPROVED_SPEC_SHA256: Optional[str] = None`) とし、`None` のあいだは
  `no-approved-spec` で fail-closed。approval 発行 API を作らない。
- **B-3: manifest CLI `build-approved`** を `s8b_oracle_manifest.py` へ足す。
  argv の値入力は `--output` だけ。`--schedule` / `--freeze` / `--campaign-id` /
  `--approver` / `--root` 等は parser に登録しない (指定時 argparse rc=2)。
  現状は `no-active-ratified-freeze` (rc=2) で止まる。

## `DW-M01` 変異事前登録

各変異は**位置が一箇所**であり、**同じ入力を拒否する層が前後に無い**ことを実装時にコードで確認して
から登録する (確認できなければ登録せず実効 gate へ再照準する)。

| ID | 変異 | 期待 |
|---|---|---|
| MU-1 | `verify_manifest` の cell-product 検査を撤去 | KILLED (全 holdout 一様に 1 configuration へ間引いた schedule の negative test。N-2 より judge の `expected-product` は一様 subset を捕えないので単一理由) |
| MU-2 | candidate 出力 gate の canonical namespace 拒否を撤去 | KILLED (`output/s8b-freeze/holdout_freeze.v2.g1.json` を渡す negative test) |
| MU-3 | candidate 出力 gate の `O_NOFOLLOW`/`O_EXCL` を通常 `open("x")` へ戻す | KILLED (symlink parent / 既存 leaf の negative test) |
| MU-4 | budget と approval の canonical bytes 比較を数値比較へ緩める | KILLED (`100` 対 `100.0` の negative test) |
| MU-5 | `BUDGET_APPROVAL_SHA256 is None` の fail-closed 分岐を「照合を飛ばして通す」へ反転 | KILLED (未承認のまま candidate を作れないことの test) |
| MU-6 | `APPROVED_SPEC_SHA256 is None` の fail-closed 分岐を同様に反転 | KILLED (CLI が `no-approved-spec` を返すことの test) |
| MU-7 | floor result の `eligible_for_refreeze is True` 要求を撤去 | KILLED (pilot / false の negative test) |
| MU-8 (正例) | 変異なしで既存 manifest happy-path 群 | 緑のまま (cell-product 検査の過剰拒否がないことの正例) |

`DW-M03` に従い、診断文字列だけの赤は kill に数えない。

## 成果物への影響 (`DW-G05`)

- **B-1 を実装しない場合**: 全 holdout で 1 configuration・`n=1` の manifest が
  `verify_manifest` を通り、report の `expected_cells` がそれだけになり、judge が
  唯一の候補を `unique-best` にする。**certified 選択の winner が直接変わる。**
- **A の budget 束縛を pinned literal にしない場合**: 自己生成した approval JSON で
  任意の budget が「承認済み」となり、ledger の reservation 上限と観測集合が変わる。
- **A-2/A-3 を今 実装した場合** (返す理由): manifest schema と transition table の変更は
  driver / report / judge / ratified verifier の全 consumer と凍結契約に波及し、
  [T-782] で不採択となった scope 拡大と、不変条件 3 の破棄を伴う。

## 段 5 の分割

B-8 (所有が素集合でない) の裁定を、直列化ではなく**所有の割り当てで**閉じる。
共有 fixture は**単位 A の単独所有**とし、単位 B は同 file を編集しない (既存 API の import は可)。
これで直列前置きが不要になり、2 単位を並列投入できる。

- **単位 A**: `orchestrator/campaign/s8b_holdout_freeze.py` +
  `orchestrator/tests/test_s8b_holdout_freeze.py` +
  `orchestrator/tests/s8b_v2_freeze_fixture.py` (**A の単独所有**)
- **単位 B**: `orchestrator/campaign/s8b_oracle_spec.py` (新規) +
  `orchestrator/campaign/s8b_oracle_manifest.py` +
  `orchestrator/tests/test_s8b_oracle_manifest.py` +
  `orchestrator/tests/test_s8b_ratified_freeze.py`
  (`s8b_v2_freeze_fixture.py` は **import only、編集禁止**)
