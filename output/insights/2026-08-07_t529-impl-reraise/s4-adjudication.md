# 段 4 裁定 — [T-529] 実装の再起票

基準 commit: c9990bc2。段 2 は **NO-GO**、段 3 レンズ A は **NO-GO 同意 (ただし根拠を訂正)**、
段 3 レンズ B は **YES (E の共有 leaf 抽出は実装可能)** で割れた。親が裏取りして裁定する。

## 親が独立に裏取りした実測 (すべて本 worktree、read-only)

| # | 実測 | 手段 |
|---|---|---|
| A | 94a4 の file sha256 = `94a4b79f…5c5a9` (content-address 一致)、`env_tag=pegasus`、`schema=calibration/v2`、`quality.status=accepted` | `probe_cal2.py` |
| B | 94a4 を指す prospective g2 は `is_valid_successor(g1, g2) = True`、`contract_sha256 = 1346c20b5519be4b…` | 同上 |
| C | `load_verified_calibration` は g1(753f) も g2(94a4) も **ACCEPT** する | 同上 |
| D | 計測 job `0:892707.nqsv` の `calibrate_rc = 0` | `job-result.json` |
| E | `_runtime_module_paths` は**明示列挙の閉じた集合**で、`env_attestation.py` を含む | `silo_ladder_rung1.py:254-271` |
| F | `V2_ENV_NEUTRAL_MODULES` も明示列挙で `env_attestation.py` を含む | `test_env_contract.py:82-97` |
| G | T-126 の identity path 集合は `env_contract.py` を含むが `env_attestation.py` を**含まない** | `qualification/contract.py:50-66` |

## 所見の裁定

### real (採用)

- **R1 (レンズ A M1、レンズ B、段 2 と一致)。`DW-G04` の「発火条件を満たす artifact path も
  計測 ID も書けない」は反証された。** 実測 A〜D より、path =
  `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`、
  計測 ID = `892707.nqsv` を今日 brief に書ける。D196 の理由 (b) と D215 の同一条文は
  **事実認定が古い**。**採用。段 7 で decisions へ supersede を記録する。**
- **R2 (レンズ A M2)。ただし「loader が通る = 正規 publisher を通った」は成立しない。**
  loader が外部検証するのは path 封じ込め・bytes SHA・schema・env・clock・policy までで、
  `publish.json` / job-result / self-comparison / final receipt は読まない。
  schema は `quality.status=rejected` 自体を許し、production loader に `accepted` の明示検査が無い。
  **採用。「正規 g2」ではなく「レビュー済み commit が束縛する prospective g2 素材」と書く。**
- **R3 (レンズ B 1、レンズ A は否定せず)。裁定 E の前半 (述語の共有 leaf 抽出) は
  活性化の発火から独立に実装できる。** 現在の依存辺は `env_attestation → env_contract` で、
  `env_attestation` 側の `_env_contract` 使用は loader の型注釈・型検査だけである。
  既存の負例 (SHA 不一致 / policy 不一致 / duplicate key / env・clock 不一致 / repo escape) が
  そのまま leaf に当たるため、**恒真実装では通らない。採用 = 本 wave の唯一の実装 scope。**
- **R4 (親の実測 E・F)。新 leaf は identity 閉包と AST 閉包へ入れなければ穴になる。**
  `_runtime_module_paths` は明示列挙であり、較正検証の意味論を持つ module がそこに無いと
  silo evidence と T-126 が「検証コードを pin していない」状態になる。**採用。**
- **R5 (レンズ A M3-5)。A(b) を将来実装するとき、`s8b_oracle_report.py:1640` の
  raw `resolve_by_contract_sha256` 直接使用が迂回として残る。** freeze 再検証側だけ直しても
  observation 側に穴が残る。**採用。設計メモへ記録 (本 wave では実装しない)。**
- **R6 (レンズ B 3)。裁定 D の文言「各 env は据置または +1」だけでは全 env 据置の
  no-op record を拒否できない。** 前 wave の s4 表は no-op を明示的に問題としていたので、
  文言と意図に差がある。**採用。ユーザー再裁定へ返す (親が独断で条件を足さない)。**
- **R7 (レンズ A S1、レンズ B 4、親 (P3) の訂正)。[T-607] の従属裁定は維持できない。**
  env 契約の世代活性化と freeze v2 の active pointer は別機構である。ただし blocker は
  「人間 commit 1 つ」ではなく「AI が発行する candidate generation + 運用上人間専有とした
  `AI-Agent: none` の approval/pointer」という chain である。機械が保証するのは
  非 merge かつ逐語 `AI-Agent: none` までで、人間性やレビュー済みであることではない。
  **採用。段 7 で worklog の [T-607] 項を訂正する。**
- **R8 (レンズ A M1、レンズ B 6)。裁定 C(a) の「新規タスク」は [T-609] として既に存在し、
  差分は 0。** **採用。重複起票しない。**

### refuted / 不採用

- **段 2 の「実装可能な部分集合は 1 つも無い」は過大。** R3 が反例である。
  段 2 は E を活性化全体と束ねたが、共有 leaf 抽出は fuse・入口被覆から独立している。
- **レンズ B の「D も純 data-layer 述語として実装候補」は不採用 (scope 外)。**
  R6 のとおり裁定文言に穴がある状態で predicate を land すると、
  「no-op を拒否する保証がある」と誤読されうる弱い gate を台帳へ残す。ユーザー再裁定後に実装する。
- **A(b) の実装は不採用 (scope 外)。** 2 レンズとも一致して、production 結線には
  activation chain が要る。今日結線しても実測 (registry 1 世代/env) より受理集合は
  1 要素も変わらず、無条件 pass と区別できない。

## 親の provisional 裁定の帰趨

| | 判定 |
|---|---|
| (P1) 実装面 scope 無し | **誤り。** 理由の前半 (発火正例なし) は R1 で反証、後半 (D215 の入口面) は正しいが、E の独立部分集合 (R3) を落としていた |
| (P2) A(b) は今日 vacuous | **維持** (狭義に正しい)。ただし「ゆえに発火素材も無い」への一般化は誤り |
| (P3) T-607 の blocker | **核心は維持、表現を訂正** (R7) |
| (P4) 成果物は docs のみ | **誤り。** R3 の実装面がある。(ii) 新規起票は R8 により不要 |

## 裁定 — 本 wave の scope

**実装する (単位 1 のみ):** 裁定 E の前半。較正 bytes の検証述語
(path 封じ込め・bytes SHA・schema・env・clock・policy) を `env_contract` を import しない
共有 leaf module へ抽出し、`env_attestation.load_verified_calibration` を型境界 wrapper として
委譲させる。新 leaf を `_runtime_module_paths` と `V2_ENV_NEUTRAL_MODULES` へ加える。

- **成果物影響 (`DW-G05`):** 較正の受理集合・certified 選択結果・proof 参照は**不変**である。
  変わるのは silo evidence の `runtime_modules_sha256` の**値**である (閉包に 1 module 増える)。
  実装しない場合、活性化 loader を作る次 wave で `env_contract` 初期化中に部分初期化の
  `env_attestation` へ到達して import が失敗し、activation 参照が 1 件も発行できない
  (前 wave の裏取り 1)。
- **実装しない (scope 外、設計メモと裁定パッケージへ):** E の後半 (CLI 解析後への load 遅延 —
  authority loader が未実装のため対象が無い)、A(b) の結線、D の遷移述語、fuse の除去、
  入口 receipt、activation chain。

## 変異事前登録 (`DW-M01`)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」ことを実装子の diff で確認してから走らせる。

| # | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | 新 leaf の bytes SHA 照合 | 比較を恒真化する | KILLED | 既存 SHA 不一致テストが唯一この層で落ちる (`test_env_attestation.py` の SHA 不一致例) |
| M2 | 新 leaf の path 封じ込め検査 | repo escape を許す | KILLED | repo escape 負例が他層に無い |
| M3 | 新 leaf の env_tag 照合 | 照合を外す | KILLED | env 不一致負例が唯一この層 |
| M4 | 新 leaf の clock / policy 照合 | 照合を外す | KILLED | clock/policy 不一致負例が唯一この層 |
| M5 | `env_attestation` の wrapper 委譲 | leaf を呼ばず旧経路へ戻す (委譲を外す) | KILLED | 委譲固定テストが唯一この層 |
| M6 | `_runtime_module_paths` | 新 leaf を閉包から外す | KILLED | 閉包網羅テストが唯一この層 |

**受理集合を縮小しないため、過剰拒否検出の正例は「g1(753f) と prospective g2(94a4) の
双方が leaf を ACCEPT で通る」1 本を登録する** (親の実測 C と同値、テストとして固定する)。

## ユーザーへ返す裁定パッケージ (scope 外の real 所見)

| # | 事項 | 親の推奨 |
|---|---|---|
| 甲 | **D の文言の穴 (R6)。** 「各 env は据置または +1」は全 env 据置の no-op record を受理する | 「全 env の delta ∈ {0,1} かつ少なくとも 1 env の delta == 1」へ条件を足す |
| 乙 | **D196/D215 の理由 (b) の supersede (R1)。** 発火正例素材は実在すると事実認定を更新するか | 更新する。ただし「正規 g2」ではなく「prospective g2 素材」と書く (R2) |
| 丙 | **[T-607] の従属先の訂正 (R7)。** 従属先を T-529 から「freeze v2 の candidate + 人間 approval/pointer」へ変えるか | 変える。T-529 の活性化では `no-active` は解消しない |
| 丁 | **94a4 の登録・活性化をいつ行うか。** 残る hard blocker は [T-609] の入口閉包の完了である | T-609 完了後に独立 wave。本 wave では登録しない |
