# 段 6 fix 裁定 — [T-574]

親がレビュー R1 / R2 の所見を real/refuted・採否・scope へ裁定した。
親が独立に裏取りした事実だけを根拠にする。

## 親が裏取りした事実

| # | 主張 | 親の実測 | 判定 |
|---|---|---|---|
| W1 | R1-1 の fail-open は本 wave が混入させた | `git show fac84353^:orchestrator/campaign/s8b_oracle_report.py` の同関数に**同じ `return None` 分岐が既に存在**する | **refuted (既存挙動)** |
| W2 | R2-5 の期待値弱体化は実在する | 親版は `{row["reason"] ...} == {"manifest contract_sha256 が registry contract と不一致"}` の集合完全一致。現行は部分一致へ緩和 | **real** |

## 裁定表

| 所見 | 判定 | 採否 | 備考 |
|---|---|---|---|
| R1-1 宣言済みだが不正な `run_contract` が legacy 扱いで receipt 検査を迂回 | **real だが既存挙動** (W1) | **不採用** | 修正は受理集合の**縮小**であり未承認。裁定パッケージ **R7** へ |
| R1-2 C4 が manifest 1 件を campaign 数だけ再解決 | **real** | **採用 (fix)** | 段 4 が自ら課した「1 回だけ解決」の違反。**受理集合と per-campaign の error 帰属は 1 bit も変えない**こと |
| R1-3 `_gate_check_core` に exact type 検査がない | **real** | **採用 (fix)** | 成果物影響は無い (nit) が、fail-closed 方向のみの小さい補強で A-1 の漏れ型を閉じる |
| R1-4 非一意 / dishonest は production artifact から到達しない | **real** | **採用 (記録の訂正)** | test docstring に「patch-only の構造防御であって artifact 負例ではない」と明記。変異の受理集合 kill に数えない |
| R1-5 周辺 docstring が旧経路を主張 | **real** | **採用 (fix)** | 共有 core の説明を中立化し、公式 CLI の記述を現物へ合わせる |
| R2-1 M3 が事前登録どおり殺せない | **real** | **採用 (fix + 変異再照準)** | 下記 |
| R2-2 C4 の assertion が空 rows で恒真 | **real** | **採用 (fix)** | 件数を先に固定してから status/reason を見る |
| R2-3 calibration 2 ケースが同一 mock error | **real** | **採用 (fix)** | temp repo の実 calibration を削除 / 改変する実ケースへ置換 |
| R2-4 public 正例の配線 pin は有効 | real (肯定) | 変更なし | 維持 |
| R2-5 既存期待値の弱体化 1 件 | **real** (W2) | **採用 (fix)** | **復元**であって新規の緩和ではない |
| R2-6 C3 構造 pin と禁止語は裁定どおり | real (肯定) | 変更なし | 維持 |
| R2-7 untouched consumer の回帰 test がない | **real** | **一部採用** | driver へ `ReverifiedFreeze` を渡す負例だけ採用 (R1-3 と同一 fix)。他の consumer への counterfactual matrix は scope 外 |

## fix 一覧 (F1〜F8)

| ID | 内容 | 受理集合 |
|---|---|---|
| F1 | C4 の resolver + calibration 解決を `build_observations` で**厳密に 1 回**行い、同一結果 (または同一 error) を全 `_assess_campaign` へ渡す。**per-campaign の error 帰属・rows の status/reason・terminal 異常時の early-return 挙動を 1 bit も変えない。** 2 campaign manifest で call count = 1 を固定する test を足す | 不変 |
| F2 | dishonest-resolver の負例を **same-env かつ recorded と異なる hash** の `GenerationEntry` を返す resolver で追加し、hash 再検査を通す経路を撃つ | 不変 |
| F3 | C4 の正例・拒否 matrix で、status/reason を見る**前に** `len(rows)` が 0 でなく期待件数と一致することを固定する | 不変 |
| F4 | reverify の `missing-calibration` / `calibration-hash-mismatch` を、temp repo の実ファイル削除 / bytes 改変で踏む実ケースへ置換する。置換できない場合は nodeid を `attestation-error` へ改名し、合成証拠である旨を docstring に書く | 不変 |
| F5 | `test_manifest_contract_sha256_mismatch_with_registry_is_protocol_violation` の reason 検査を、親版と同等の**集合完全一致**へ戻す (揮発値は焼き込まない) | 不変 |
| F6 | `s8b_oracle_driver._gate_check_core` の入口で `type(launch_validated) is LaunchValidatedFreeze` を要求し、`ReverifiedFreeze` を渡す拒否 test を足す | **縮小方向のみ** (historical token を拒否する。既存の正当な token は不変) |
| F7 | 共有 core の docstring を中立な full validation core の説明に直し、`s8b_oracle_manifest` の公式 CLI 記述を `reverify_published_freeze` へ更新する | 不変 |
| F8 | ambiguous / dishonest の test docstring に「patch-only の構造防御であり production artifact から到達しない」と明記する | 不変 |

F6 は受理集合を縮小するが、縮小するのは**本 wave が新設した historical token を live gate が受け取る**という、
land 前には存在しなかった組合せだけである。既存の正当な入力は 1 件も落ちない。

## 変異の再照準 (DW-M02 / DW-M04)

M3 は事前登録どおりでは殺せない (R2-1)。内側 (`s8b_ratified_freeze.py:2794-2799`) と
外側 (`同:2822-2826`) に同型の hash 再検査が二重にあり、片方を消しても他方が同じ理由で落とすためである。
DW-M02 に従い実効 gate へ再照準し、両層同時変異まで登録し直す。**初回登録は消さず erratum として残す。**

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M3a | 内側 (`:2794-2799`) | hash 再検査を削除 | **SURVIVED 期待** (外側が mask する。冗長 gate の証拠) |
| M3b | 外側 (`:2822-2826`) | hash 再検査を削除 | **SURVIVED 期待** (内側が mask する) |
| M3c | 内側 + 外側を累積適用 | 両方削除 | **KILLED 期待** (F2 の same-env/wrong-hash 負例) |

M1・M2・M4・M5・M6・M7 は初回登録のまま。M7 は構造 pin であり受理集合 kill に数えない (裁定済み)。
M3a / M3b の SURVIVED は equivalent mutant ではなく**冗長 gate**であり、DW-M04 に従い
mutated diff で注入実在を確認したうえで台帳へそう記録する。

## 追加の裁定パッケージ

| # | 択一 | 根拠 |
|---|---|---|
| R7 | **宣言済みだが不正な `run_contract` を legacy と見なす既存挙動を直すか。** (a) `run_contract` が完全に欠落する場合だけ legacy とし、field があるのに `env_tag` / `contract_sha256` が欠落・空・非文字列なら manifest-global error にする (受理集合の縮小)、(b) 既存挙動を正式仕様として明記し回帰試験で固定する | R1-1 + W1。`fac84353^` に同一の分岐が既存。contract / calibration / execution receipt の束縛なしに row が `completed` へ到達しうる |
