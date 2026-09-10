# 段 1 brief — [T-529] 契約世代の活性化権限 (残り実装)

wave branch: `worktree-dev-wave-t529-activation` / 基準 commit: `6cc3e59a`
受入・実測環境: Pegasus (worklog が所在の正本、機体固有は `docs/pegasus-runbook.md`)

## scope (裁定済み。かっこ内は `DW-G05` 成果物影響 = 入れない場合の帰結)

1. **bootstrap fuse の除去** — `env_contract.validate_generations` の
   「2 世代目を拒否する」節を落とす (入れなければ較正を再取得しても registry へ載らず、
   certified 選択は永久に g1 較正の値で確定し続ける)。
2. **pegasus g2 の登録** — `_build_registry()` へ `calibration-94a4b79fa31bba3c.json`
   (accepted / `calibration/v2` / env_tag=pegasus / clocks_per_us=2100) の世代 2 を追加
   (入れなければ活性化権限は入力ゼロの機構になり、発火材料の実在を主張できない)。
3. **activation record** — 新 leaf に schema (`schema_version` / `activation_serial` /
   `previous_activation_state_sha256` / `active_contracts[env_tag,generation,contract_sha256]` /
   `activation_state_sha256`)、canonical bytes、hash chain、registry 整合の検証を実装し、
   初期 record (serial 1、両 env g1) を発行する (入れなければ「どの世代が active か」の正本が
   台帳に無く、レポートの数値がどの較正に属するか事後に監査できない)。
4. **active pointer の束縛** — `REGISTRY` / `lookup()` を `sequence[-1]` でなく
   activation record の `active_contracts` から導出する (入れなければ **項目 2 を入れた瞬間に
   g2 が黙って current になり**、committed floor protocol が live admission で拒否され、
   proof chain を張り替えないまま計測基盤が入れ替わる)。
5. **裁定 A(b) — ever-active 限定** — `resolve_by_contract_sha256` を activation chain 上で
   一度でも active だった hash に限定する (入れなければ「登録しただけで一度も活性化していない
   世代」の hash で書かれた成果物を歴史 lane が受理し、historical authority が registry
   台帳と同義になる)。
6. **receipt (裁定 2 の前者 = process-local)** — activation state の検証を process 内で
   一度だけ行い、`execution_guard.require_certified_writer_authorization` が
   その receipt (serial + state hash) を最初の書込み前に assert する (入れなければ
   certified sink は活性化状態を検証しないまま書き始める)。

## 確定済みユーザー裁定 (逐語は `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §30/§36/§38)

- A = (b) ever-active 限定 / B = (a) `DW-G04` 維持・合成正例を作らない / C = (a) writer 閉包は
  別タスク (= [T-609]、(306) で land 済み) / D = 各 env は据置または +1 / E = 述語を共有 leaf へ
  抽出し authority loader の load は **CLI 解析後へ遅延** する。
- 6 択一 (2026-08-06): trust root = レビュー済み commit と明示 / receipt は process-local
  (durable 化は別 wave) / **fuse 解除の前に履歴解決を配線** (= [T-615]、(291) で land 済み) /
  g1 は exact hash grandfather / silo 昇格入口は「未実装」と名乗る。
- [T-624] = D228 (全 env delta ∈ {0,1} かつ少なくとも 1 env が +1) を **規則として記録済み**。
  [T-627] = **述語の実装は実 schema 確定まで置く** (番号 delta 述語は検出力ゼロと実測済み、
  次点は generation と contract hash の同一入力束縛)。

## 不変条件

- env 固有 literal は `_build_registry()` の内部だけ (`test_env_contract.py` の AST 検査)。
- 規律 2/3: 活性化を通らない certified 書込みを増やさない。fail-closed を fail-open にしない。
- 凍結成果物の bytes を変えない。**active が g1 のままなら producer 出力 bytes は不変**
  (`DW-O10` はこの前提の上で適用外に落ちる — 前提が崩れたら段 4 で再評価する)。
- 既存テストの期待値を変えない。受理集合の拡大・縮小は scope に書いた 2 方向だけ。

## 親の前提実測 (すべて本 worktree で実施、実編集 → `git checkout --` 復元、復元後 clean)

- **実測 1 (生死、`DW-G01`)** — g2 を実編集で追加し fuse を外すと import は成功し、
  `lookup("pegasus")` は g2 (`1346c20b5519be4b…`) を返す。94a4 の bytes sha256 は
  `94a4b79fa31bba3c725b…` で file 名の prefix と一致、`quality.status=accepted`。
- **実測 2 (壊れる面の同定)** — committed `output/s8b-freeze/floor_protocol.json`
  (recorded hash = pegasus g1 `e576e9cd…`) に対し、g2 が current の状態で
  **historical lane (`reverify_published_freeze`) は ACCEPT、current lane
  (`launch_validate`) は REJECT** (`FloorContractError: 記録 contract_sha256 が current
  contract と不一致`)。[T-615] の 2 lane 分離は効いており、壊れるのは live admission だけ。
- **実測 3 (pin 閉包、`DW-O09`)** — pegasus g1 hash を literal で持つのは 4 file:
  `output/s8b-freeze/floor_protocol.json`、
  `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` (成果物 2 件)、
  `test_env_contract.py:74,1138`、`test_s8b_floor_campaign.py:3253` (test 2 件)。
  `FROZEN_MANIFEST` (`test_frozen_artifacts.py`、23 件) は path 側で env_contract を
  持たない。role 名 key 側の pin は t419 probe manifest と silo evidence (実測済み、歴史 pin)。
- **実測 4 (seam の広さ)** — `lookup` 系の非 test 参照は 70 箇所。consumer を個別配線せず
  `lookup` 単一 seam を活性化束縛にするのが最小変更面。

## 親の provisional 裁定 (攻撃対象。段 3 は必ずこれ自身を攻める)

- **(P1) g2 は登録するが活性化しない。** 初期 activation record は serial 1・両 env g1 とし、
  `lookup` の返り値を今日と同一に保つ。根拠 = 実測 2。pegasus を g2 へ進める活性化は
  certified 計測の基盤較正を差し替える行為で、committed floor protocol を live admission から
  外す。これは親が独断で決める範囲を超えるため裁定パッケージへ返す。
- **(P2) 永久 fuse との区別は「実材料の serial 2 遷移を loader が受理すること」で示す。**
  合成 fixture ではなく registry に実在する g2 行から導出した record を正例に使う。
  `generation > 1` を無条件拒否する実装ではこの正例が落ちる。
- **(P3) D228 の遷移述語 (no-op 拒否) は本 wave では実装しない。** [T-627] の裁定 (c) に従い、
  本 wave は schema を確定してその前提を満たすところまでとする。ただし schema は
  次点 (b) (generation と contract hash の同一入力束縛) を実装可能な形にする。
- **(P4) loader は import 時に I/O しない。** 裁定 E の「load は CLI 解析後へ遅延」に従い、
  初回 `lookup` での遅延読込 + process 内 cache とする。読めない・壊れているは fail-closed。

## 成果物の形

`env_contract.py` の改修、新 leaf 1 本 (activation record 検証)、初期 record JSON 1 件、
発行 tool 1 本 (maintainer 明示実行)、`execution_guard` の receipt assert、対応 test。
docs は親が書く。

## 並列分割方針

単位 A = `env_contract.py` + 新 leaf + record + 発行 tool (所有: campaign/env_contract*.py、
新 record path、tools/)。単位 B = `execution_guard` receipt assert + 影響 test
(所有: campaign/execution_guard.py、tests/)。B は A の型に依存するため **逐次**とし、
A 完了後に所有パス限定 patch を展開してから投入する。
