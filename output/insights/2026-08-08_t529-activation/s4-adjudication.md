# 段 4 裁定 — [T-529] 活性化権限 (plan v2 と変異事前登録)

親が段 2 プランと段 3 の 2 レンズ (A/B とも NO-GO、must-fix 計 10 件) を裁定する。

## 親が独立に裏取りした実測 (段 4)

- **裏取り 1 (レンズ A 所見 6 は real)。** g1 hash を持つ tracked file は **5 件**で、親 brief の
  「4 件」は誤り。追加は
  `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/gap-result-receipt.json`。
  併せて**検索手法の欠陥を実測した** — 同じ hash を repo root (`.`) から
  `grep -rl` すると当該 file を落とすが、`git grep -l` と `grep -rl <部分木>` は拾う。再現性あり。
  以後この wave の pin 閉包は `git grep` を authority とする。
- **裏取り 2 (レンズ B 所見 3 は real)。** `t126_driver.py:496` は
  `env_contract.lookup(...)` の直後に `_fork_owned_process_group` で fork する。
  PID 束縛 receipt はこの経路で実際に発火する (恒真ではない)。
- **裏取り 3 (レンズ B 所見 3 の後半は real)。** `test_campaign.py:79` と
  `test_screening_driver.py:37` は **module 直下**で `lookup()` を呼ぶ。collection 時点で
  authority load が走るため、「import 時 I/O ゼロ」の検査は同一 process では無効。
- **裏取り 4 (レンズ A 所見 1 の反例は real)。** レンズ A が構成した aggregate-delta 誤実装は、
  deltas `(+2, −1)` に対し 3 条件すべてを外して accept する。プランのテスト表は
  この相殺ケースを負例に持たないため、[T-624] wave と同型の「検出力ゼロの gate」を land しうる。

## 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A1 | T-627 (c) の自己解除 | **real** | **採用 (親 P3 を維持)**。遷移述語は本 wave で実装しない |
| A2 | 一時 serial 2 は合成正例 | **real** | **採用**。正例は通常の unit test とし、DW-G04 発火証拠に数えない |
| A3 | trust root が loader に未結線 (suffix 注入 / tail rollback) | **real** | **採用・設計変更** (下記 plan v2 §3) |
| A4 | ever-active 全 entry の較正 eager 検証 | **real** | **採用**。current entry だけを load 時検証へ縮める |
| A5 | 「壊れるのは live admission だけ」は過度な一般化 | **real** | **採用**。影響表を層別に書き直す。silo は scope 外 |
| A6 | pin は 4 でなく 5 | **real** | **採用**。裏取り 1 のとおり訂正 |
| A7 | receipt が非 load-bearing | **real** | **採用・設計変更**。guard は receipt 経由で契約を解決する (下記 §5) |
| A8 | ever-active 限定の直接的な締出しは 0 件 | real (情報) | 記録のみ。A(b) は弱めない |
| A9 | 8c condition 12 は receipt を観測しない | real | **scope 外**。射程を明記して裁定パッケージへ |
| B1 | activation head が reviewed commit に未束縛 | **real** | A3 と同一。**採用** |
| B2 | receipt が全入口の最初の書込みへ届かない | **real** | **一部採用**。certified writer gate は本 wave、他入口は裁定パッケージ |
| B3 | PID 判定だけでは locked-mutex fork に耐えない | **real** | **採用**。`os.register_at_fork` で child 側を再初期化 |
| B4 | identity pin 閉包不足 + record 追加が歴史検証を壊す | **real** | **採用・設計変更**。record を path set に足さない (§3) |
| B5 | silo 歴史 evidence が将来の current g2 で壊れる | **real** | **scope 外**。g2 活性化の前提条件として裁定パッケージへ |
| B6 | テスト表が tail rollback / held-lock fork / 入口漏れを落とさない | **real** | **採用**。§6 のとおり強化 |
| B7 | repo root 解決の対応範囲が未定義 | real | **採用**。source checkout / worktree / source-stage に限ると明記 |
| B8 | lazy view の Mapping 契約テスト不足 | real | **採用**。`collections.abc.Mapping` として実装し互換テストを置く |
| B9 | 単位分割が成立していない | real | **採用**。第三案を縮小して採る (§7) |

refuted はゼロ。**親の provisional 裁定は (P1) 維持・(P2) 反証により撤回・(P3) 維持・(P4) 維持。**
親 brief の実測 3 (pin 4 件) は誤りとして訂正した。

## plan v2

### 1. データ層 (裁定どおり)

- `_build_registry()` の pegasus へ g2 を追加する。calibration ref =
  `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` /
  `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9`。
  g2 の `contract_sha256` は `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c`
  (親が実測済み)。g1 を `dataclasses.replace` して calibration ref だけを変える。
- `validate_generations()` から bootstrap fuse の分岐を落とし、構造検査だけを残す。

### 2. activation record (schema は段 2 案を採用、遷移述語は入れない)

- 格納先 `orchestrator/campaign/env_contract_activations/NNNNNNNN.json`。
- exact key = `schema_version` / `activation_serial` / `previous_activation_state_sha256` /
  `active_contracts` / `activation_state_sha256`。行要素は
  `env_tag` / `generation` / `contract_sha256` の 3 key のみ。
- canonical: `sort_keys=True, separators=(",",":"), ensure_ascii=True, allow_nan=False`、
  state hash は自身を除く 4 key の canonical JSON の SHA-256、file bytes は full record の
  canonical JSON + LF。**初期 record の state hash は
  `f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed` (親が一次計算で一致確認)。**
- 検査する不変条件: exact key / 型 (bool 拒否) / hex64 / `env_tag` 昇順・重複なし /
  **全登録 env と exact 同一集合** ([T-628] の env 集合固定) / 各行が
  `(env_tag, generation) → contract_sha256` として registry と exact 一致 / serial 連番 /
  filename と serial の一致 / predecessor hash の連鎖 / symlink・非 regular file の拒否。
- **世代 delta の述語 (D228 の no-op / skip / downgrade 拒否) は実装しない。** [T-627] の
  裁定 (c) が生きており、schema が確定した事実は本 wave の worklog で報告して
  ユーザー再裁定へ返す。裏取り 4 のとおり、拙速な形は検出力ゼロの gate を残す。

### 3. trust root の結線 (A3 / B1 / B4 への設計解)

段 2 案 (directory を読むだけ) と両レンズの manifest 案の代わりに、**head pin を Python 側に置く**。

- `env_contract.py` に `_ACTIVATION_HEAD_SERIAL: int` と
  `_ACTIVATION_HEAD_STATE_SHA256: str` の 2 定数を置く。
- loader は chain 終端の serial と state hash がこの定数と **exact 一致**することを要求し、
  head を超える余分な record file の存在を拒否する。
- 理由: (i) hash chain は head を固定すれば全 record bytes を暗号学的に束縛するので、
  tail 削除も suffix 注入も head 不一致で落ちる。(ii) `env_contract.py` は **既存の
  source binding の検査対象** (`certified_writer_preflight` は import 済み Python module の
  bytes を receipt の commit と照合する) であり、JSON を対象外にしている穴を追加機構なしで塞ぐ。
  (iii) identity pin へ record を 1 件ずつ足す必要が消えるため、B4 の
  「record 追加のたびに旧 series preimage が検証不能になる」が構造的に起きない。
- **自己 hash 参照ではない** (F36 非該当) — 定数は record の hash であって
  `env_contract.py` 自身の hash ではない。

### 4. lazy authority (P4 / B3 / B7 / B8)

- import 時は `GENERATIONS` の構築・構造検証・hash index 構築までとし、I/O をしない。
- `REGISTRY` は `collections.abc.Mapping` を実装した lazy view を `MappingProxyType` で包む。
  初回アクセスで authority を 1 度だけ load する。
- **較正検証は load 時には current 行 (= active generation) だけにかける** (A4)。
  歴史 entry の較正は `resolve_by_contract_sha256` が解決した entry についてだけ検証する。
- repo root は `__file__` 基準 + sentinel 検査で解決し、cwd から導出しない。
  対応範囲は source checkout / worktree / source-stage と明記する。installed copy は対象外。
- cache は lock + PID 束縛に加え `os.register_at_fork(after_in_child=...)` で
  child 側の lock・cache・receipt を再初期化する。

### 5. receipt (A7 / B2)

- receipt は `activation_serial` / `activation_state_sha256` / 発行 PID / process seal を持つ。
- **guard は `lookup()` を呼び直さず、receipt が指す state から契約を解決する。**
  これにより stale / forged / fork 継承 receipt が受理結果を実際に変える (裏取り 2 の
  T126 fork 経路で発火する)。
- 検査順は既存 5 条件の型検査 (条件 1) の直後・registry 同値 (条件 2) の直前に置く。
- **本 wave が主張する射程**: certified sink (`pipeline.evaluate` → `execution_guard`) の
  最初の書込み前に activation state が検証されていること。floor / oracle driver / selector /
  T126 の fork child / PBS wrapper への receipt 配線は**本 wave の scope 外**であり、
  「全入口が activation receipt 済み」とは名乗らない。

### 6. テスト (B6 の指摘を反映)

段 2 表を基礎に次を必須で足す・直す。

- head 不一致系: **tail rollback** (末尾 record 削除) と **valid suffix 注入** を独立 node で。
- import 時 I/O ゼロは **fresh subprocess** で測る (裏取り 3 により同一 process では無効)。
- **別 thread が lock を保持したまま fork** する決定的テスト。
- 統合テストは `REGISTRY` / resolver を直接 monkeypatch せず、
  **record directory と head 定数と cache clear だけ**を操作する。
- 既存の historical テストの call-count / object 伝播 / no-fallback / 拒否理由の assert を保持する。
- 「実 g2 の serial 2 を loader が受理する」テストは置くが、**`DW-G04` の発火証拠ではなく
  通常の回帰テストである**と test の docstring に明記する (A2)。

### 7. 実装単位 (B9 の第三案を縮小)

- **単位 1** — `env_contract_activation.py` (pure leaf) と leaf 専用 test。
- **単位 2** — `env_contract.py` (g2 登録 / fuse 除去 / head 定数 / lazy view / ever-active)、
  初期 record、`tools/issue_env_contract_activation.py`、authority 統合 test。単位 1 に依存。
- **単位 3** — `execution_guard.py` の receipt 解決と、certified writer 経路の test。単位 2 に依存。
- **単位 4** — identity pin 閉包 (`qualification/contract.py` の code identity へ activation leaf・
  `calibration_verify`・`execution_guard` を追加、silo runtime binding、T419 dirty scope) と
  既存 test の追随。単位 2・3 に依存。

依存が一直線なので**逐次投入**とし、各単位の完了後に所有パス限定 patch を次単位へ展開する。

## 変異事前登録 (`DW-M01`)

実装後に anchor (old 逐語) を再検証してから本走する (`DW-M07`)。各変異は
「同じ入力を拒否する層が前後に無い」ことを実装完了時にコードで確認し、確認できないものは
登録から外して実効 gate へ再照準する。

| ID | 変異位置 (意図) | 期待 kill | 単一理由性の確認事項 |
|---|---|---|---|
| M1 | loader の head serial 一致検査を無効化 | tail rollback test | head 検査以外に serial 終端を見る層が無いこと |
| M2 | loader の head state hash 一致検査を無効化 | suffix 注入 test | 同上 |
| M3 | predecessor hash 連鎖検査を無効化 | chain 切断 test | head 検査に mask されないこと (中間 record 改変で head も動くため、**mask 前提**として両層同時変異を登録する) |
| M4 | `active_contracts` と registry の `(env,generation)→hash` 照合を無効化 | 不整合 record test | schema 検査で先に落ちない fixture であること |
| M5 | env 集合 exact 一致 ([T-628]) を無効化 | env 追加/削除 record test | 昇順・重複検査に mask されないこと |
| M6 | `resolve_by_contract_sha256` の ever-active 限定を外す | 未 active g2 の拒否 test | registry index 検査より後段にあること |
| M7 | `REGISTRY` を `sequence[-1]` へ戻す | activation 追従 test | lookup 以外に current を決める層が無いこと |
| M8 | guard の receipt 解決を `lookup()` 直呼びへ戻す | forged/stale receipt test | 条件 2 の registry 同値検査に mask されないこと |
| M9 | fork 後 cache 再初期化を外す | held-lock fork test | PID 判定だけでは落ちないこと |
| M10 | 較正検証を current 行から全 ever-active へ広げる | 歴史 entry 欠落時の current 受理 test | A4 の受理集合を pin する (逆方向変異) |

**正例 (受理集合を縮めすぎていないことの検出)**: 初期 record (serial 1、両 env g1) が
受理され `lookup("pegasus")` が g1 を返すこと、および実 g2 の serial 2 chain を
loader が受理すること。この 2 件は全変異走行で緑を保つ。

## 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **pegasus g2 をいつ活性化するか。** 実測: 活性化した瞬間、committed floor protocol は
   live admission から外れる (historical 再検証は通る)。前提条件として silo 歴史 evidence の
   historical 解決化 (B5) と floor protocol の再発行が要る。[T-139] 本走の基盤に触れる。
2. **[T-627] の遷移述語をどの形で実装するか。** 本 wave で schema が確定したので停止条件は
   解消するが、番号 delta の形は検出力ゼロ (今回も相殺ケース `(+2,−1)` の反例を実測)。
   次点 (b) の「generation と contract hash の同一入力束縛」で再裁定を求める。
3. **receipt を全入口へ配線するか。** PBS wrapper と writer は別 process のため、
   「receipt と writer が同一 process」の解釈では現構造で実現不能 (レンズ B)。
   durable receipt (別 wave) と併せて設計択一が要る。
4. **8c condition 12 の射程。** 現状 `EVIDENCE_UNDEFINED` で発火しない。activation receipt を
   C12 の証拠と名乗るなら condition-freeze の新世代が要る。
