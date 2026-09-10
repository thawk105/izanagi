# 段 4 裁定 — [T-574]

親 (Claude) が段 2 プランと段 3 の 2 レンズを real/refuted・採否・scope 内/外へ裁定した。
**親が自分で裏取りした事実だけを根拠にする** (子の報告を額面で採らない)。

## 親が独立に裏取りした事実

| # | 主張 | 親の実測 | 判定 |
|---|---|---|---|
| V1 | `launch_validate` は live 実走の admission である | `s8b_oracle_driver.py:1066` が `run_block` 内で呼び、`_prepare_v2_execution` (`:737`) がその戻り値を `isinstance(LaunchValidatedFreeze)` で要求し、通過後に marker/WAL/予算を書く | **real** |
| V2 | silo `validate_current_bindings` は記録 hash を current と比較する第 5 層 | `silo_ladder_rung1.py:3534` で `binding["calibration"]["contract_sha256"] != contract.contract_sha256` を current lookup と比較 | **real** |
| V3 | その silo 検査は今日すでに赤 | 親が実走: `EvidenceFailure(reason_code='binding', detail='current binding mismatch: driver')` | **real** |
| V4 | publish 済み artifact に `env_contract.py` の旧 hash pin がある | `silo_ladder_rung1.json:67` = `88d557ba…`、`t419.../manifest.json:110,270` は role key `env_contract_sha256` で同値。現物 = `8d529822…` | **real (親 brief の誤り)** |
| V5 | `LaunchValidatedFreeze` は封印されていない素の frozen dataclass | `s8b_ratified_freeze.py:764-777` に seal 構造なし | **real** |

## 所見の裁定

| 所見 | 判定 | 採否 | scope |
|---|---|---|---|
| A-1 / B-1 — historical 化が live oracle admission へ漏れる | **real** (V1) | **採用** | 内 |
| A-2 — 記録 hash が「その世代が当時 active だった」証明なしに世代選択権限になる | **real** | 不採用 (実装しない) | **外** → 裁定パッケージ |
| A-3 / B-3 — P2 は正当な successor 上で current-bound 実装と観測的に区別できない | **real** | **採用 (保証範囲を縮小)** | 内 |
| A-4 — historical calibration bytes の保存元、C4 の `repo_root` 分裂 | **real** (前半)、**real だが独立** (後半) | 前半採用 (fail-closed 検査)、後半不採用 | 前半内 / 後半外 |
| A-5 — consumer-level fail-closed matrix 不足 | **real** | **採用** | 内 |
| A-6 / B-7 — 親 probe から 4 consumer 同型と一般化できない | **real (親 brief の誤り)** | **採用 (記述訂正)** | 内 |
| B-2 — silo verify-result という第 5 層が scope 判定から漏れている | **real** (V2/V3) | 不採用 (実装しない) | **外** → 裁定パッケージ |
| B-4 — 正例は public 経路で撃つ必要がある | **real** | **採用** | 内 |
| B-5 — P4 は linux-baremetal の resume availability を実際に失わせる | **real** | 不採用 (実装しない) | **外** → 裁定パッケージ |
| B-6 — DW-O09 の「0 件」は偽 | **real (親 brief の誤り)** (V4) | **採用 (記述訂正)** | 内 |

## 親 brief の訂正 (段 1 の誤り)

1. **C1〜C3 は「read-only 再検証」ではない。** `launch_validate` は read-only の report 経路
   (`s8b_oracle_report.py:1713`) と live 実走経路 (`s8b_oracle_driver.py:1066`) の**共用**である。
   brief の scope 表のこの分類は誤りであり、本裁定で入口分離へ差し替える。
2. **DW-O09 の判定を訂正する。** 正しくは「**本 wave が編集する 3 module
   (`s8b_ratified_freeze.py` / `s8b_oracle_report.py` / `s8b_floor_contract.py`) の旧 hash pin は
   0 件。ただし `env_contract.py` には publish 済み歴史 pin が存在する (V4) — 本 wave は
   `env_contract.py` を変更しない**」。
3. **probe の射程を訂正する。** 実測したのは 2 leaf の counterfactual だけである。
   「floor / freeze / selector / oracle report がすべて落ちる」は D196 の文言の引き写しであり、
   selector と C2/C3 は親が測っていない。worklog では実測と推論を分けて書く。

## プラン v2 (実装するもの)

### 骨子 — 入口分離

`launch_validate()` は **current 束縛のまま一切変更しない**。live 実走 admission はここに残す。
read-only 再検証のために**別入口**を新設し、oracle report の呼び出しだけをそちらへ移す。

- 新入口 `reverify_published_freeze(ratified, root)` は `launch_validate` と同じ検査を
  historical resolver で行い、**`LaunchValidatedFreeze` とは別の frozen dataclass**
  (`ReverifiedFreeze`) を返す。
- 型分離の射程を誤解しない: V5 のとおりこの型は封印されておらず、**偽造耐性を主張しない**。
  効くのは「自分たちの consumer が黙って広がらないこと」だけである (`_prepare_v2_execution` の
  exact isinstance が historical token を拒む)。真の防壁は「driver が historical 経路を
  そもそも呼ばない」ことであり、型分離は多重防御にすぎない。docstring にこの限界を書く。

### 実装単位

| 単位 | 所有 file | 内容 |
|---|---|---|
| U1 | `orchestrator/campaign/s8b_ratified_freeze.py` | `_launch_validate` core (resolver 必須引数) + current 固定 wrapper `launch_validate` + historical wrapper `reverify_published_freeze` + `ReverifiedFreeze` 型。C1 helper で recorded hash を **1 回だけ**解決し、C2 (`_validate_journal`) / C3 (`_run_cmd_matches_portable_session`) / `_validate_result` / `_validate_axis_occurrences` へ同一 contract を必須引数で通す |
| U2 | `orchestrator/campaign/s8b_oracle_report.py` | `_receipt_expectations` を resolver 必須 seam にし、production caller (`:1365`) が `resolve_by_contract_sha256` を明示的に渡す。`:1713` の `launch_validate` 呼び出しを `reverify_published_freeze` へ差し替える |
| U3 | `orchestrator/campaign/s8b_floor_contract.py` | docstring の caller policy 明記と診断文の中立化のみ。API 不変 |
| U4 | `orchestrator/tests/` | 正例・fail-closed matrix・plumbing pin |

`env_contract.py` と `s8b_floor_campaign.py` は**変更しない**。fuse も触らない。

### 保証範囲の縮小 (A-3 / B-3 採用)

本 wave が land するのは **「記録された contract hash からの世代解決」と
「解決した世代の calibration の選択」**である。
**`versioned predicate dispatch` という語を成果物で使わない。** 理由: 正当な successor が
変えられるのは calibration path/sha だけなので (`is_valid_successor`)、`clocks_per_us` /
`numactl` / `attestation_mode` は世代間で必ず同値になり、C3 の current-bound 実装と
resolved-contract 実装は正当な世代では観測的に区別できない。区別できない保証を
台帳に書かない (D196 が却下した型)。
C3 の引数 test は「引数が load-bearing である」ことの**構造 pin** であって受理正例ではないと
test の docstring に書く。

### 受入・拒否の境界 (実装子への必須指示)

- 拡大するのは `reverify_published_freeze` と C4 の受理集合だけ。
- `launch_validate` / `s8b_floor_campaign` / `loop` / `pipeline` / `p3_s4_loop_trigger_gating` /
  `s8b_ratified_freeze:960` の受理集合は **1 bit も変えない**。
- 未知 hash・非一意 hash・cross-env・resolver が recorded と違う entry を返す場合・
  解決した世代の calibration が欠落 / hash 不一致の場合は、いずれも fail-closed。
  **current への fallback を書いてはならない。**

## 変異事前登録 (DW-M01 / B-057)

harness = `tools/mutation_harness.py`。各変異は単一理由であることを実装子が確認し、
親が段 6 で走らせる。

| ID | 位置 | 変異 | 期待 | 期待赤 node |
|---|---|---|---|---|
| M1 | `s8b_ratified_freeze` historical helper | resolver 呼出しを `_env_contract.lookup(env).contract_sha256` へ戻す | KILLED | historical g1 正例 |
| M2 | 同上 | resolver 呼出しから `expected_env_tag=` を落とす | KILLED | cross-env 負例 |
| M3 | 同上 | 戻り entry の `contract_sha256 == recorded` 再検査を削除 | KILLED | dishonest-resolver 負例 |
| M4 | `launch_validate` wrapper | current resolver を historical resolver へ差し替える (= A-1 の漏れを再現) | KILLED | live admission 負例 |
| M5 | `s8b_oracle_report:1365` caller | resolver を current lookup 相当の wrapper へ差し替える | KILLED | C4 public 正例 |
| M6 | C2 の calibration 検査 | `AttestationError` を握り潰して `None` を返す | KILLED | calibration 欠落負例 |
| M7 | C3 `_run_cmd_matches_portable_session` | 渡された contract を無視して current lookup へ戻す | KILLED | C3 構造 pin unit |

**M7 の限界を事前登録する**: M7 が殺せるのは専用 unit だけであり、正当な successor を使う
統合正例では殺せない (A-3 の理由)。台帳では「構造 pin」と明記し、受理集合 kill と数えない。

**過剰拒否の正例 (DW-M01)**: 本 wave は受理集合を拡大する側だが、`launch_validate` の
受理集合を縮小していないことを固定するため、既存の g1/current=g1 の live admission 正例が
緑のままであることを変異 matrix の baseline に含める。

## ユーザーへ返す裁定パッケージ (scope 外 real 所見、実装しない)

| # | 択一 | 根拠 |
|---|---|---|
| R1 | **記録 hash を世代選択の権威にしてよいか。** (a) 登録済み registry に限定される現状を受容し「非偽造」を主張しない、(b) 活性化 record を先に実装する (D196 の順序を覆す)、(c) 外部 trust root を導入する | A-2。resolver が証明するのは形式・登録・一意性・env 一致だけで、「その世代が artifact 作成時に active だった」ことは証明しない。fuse が 1 世代を強制する間は発火しない |
| R2 | **silo `verify-result` は歴史 proof verifier か current 互換 verifier か。** (a) 歴史 verifier として resolver を配線する、(b) current 互換検査と明示し D196 の「全 certified 成果物を再検証可能」から除外する | B-2 + V2/V3。今日すでに `driver` binding で赤であり、放置すると意味が曖昧なまま残る |
| R3 | **世代更新を跨いだ resume を失ってよいか。** (a) current-only resume を正式仕様として availability loss を受容し回帰試験で固定する、(b) recorded contract を resume 実行辺まで伝播する別 scope を起こす | B-5。`linux-baremetal` は `allow_resume=True` (`env_contract.py:245`) であり、worklog 注記だけでは足りない |
| R4 | **真の versioned predicate dispatch を別途起こすか。** | A-3 / B-3。正当な世代遷移で観測差を作れる遷移規則と generation-aware dispatcher が要る。現 successor 規則では作れない |
| R5 | **historical calibration bytes の保存契約を作るか。** | A-4 前半の恒久版。今は「欠落なら fail-closed」で閉じるが、旧 path の削除を禁じる契約はない |
| R6 | **oracle report の `repo_root` 分裂を直すか。** `_receipt_expectations` は module 定数 `ROOT`、CLI は `--repo-root` を受ける | A-4 後半。既存欠陥で世代解決とは独立。本 wave では触らない |

## 成果物影響 (DW-G05)

- 実装する分: `reverify_published_freeze` と C4 の受理集合だけが広がる。既存 certified 選択・
  レポート・台帳の**値は変わらない** (production は g1 一本のため解決結果が current と同一)。
- 実装しない場合: 契約世代を進めた瞬間、oracle report の再検証が落ち、[T-529] の較正再取得が
  着手できないままになる。
- R1〜R6 を実装しない影響は上表の根拠列に書いたとおりで、いずれも本 wave の成果物の値を
  今日変えない。
