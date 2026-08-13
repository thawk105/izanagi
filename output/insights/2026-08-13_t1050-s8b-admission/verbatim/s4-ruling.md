# 段 4 裁定 — [T-1050] S8b admission receipt 束縛

親 (Claude manager) が段 2 プランと段 3 レンズ A/B の所見を real/refuted・採用/不採用・scope 内/外に
裁定し、プラン v2 と変異事前登録を確定する。

## 0. 前提の再確認

- ユーザー裁定 (第 10 回 #2) は「起票」。正しさゲート側であり、粗い provenance 基準 (D320 系) の
  見送り対象ではない。
- ユーザーが指定した束縛の**境界**は「保存、resume、floor/manifest、oracle 実走直前まで」。
  実走後 (report / judge) はこの wave の境界の外である。
- ユーザーが明示した scope 外: schema 世代移行、旧 artifact の互換 loader、既存 artifact の遡及再取得。
  「勝手に実装せず、insight・handoff・worklog fragment に影響と推奨を返す」。
- 段 4 直前に裁定 inbox を再走査した。wave 開始後の更新なし。

## 1. 所見の裁定

| ID | 判定 | 採否 | scope | 根拠 |
|---|---|---|---|---|
| F-A1 / F-B2 (派生 receipt は自己整合にすぎない) | real | 不採用 (緩和は実装しない) | **scope 外** | 緩和には信頼根 (署名・issuer chain) の新設が要る。**[T-868] の既裁定 (2026-08-12)** が同型の問いに「署名方式と trust root は設けない。自己発行可能な性質は明示したまま受容する」と決めている。署名・束縛機構の新設を既定で見送るユーザー既定とも整合する。代わりに**保証名を狭めて明示する** (下記 2-c)。裁定パッケージへ返す。 |
| F-A2 (実走後 report/judge が store を再読しない) | real | 不採用 | **scope 外** | ユーザーの境界「oracle 実走直前まで」の外。裁定パッケージへ返す。 |
| F-A3 (`BuildResult` が admission 結合証跡を落とす) | real | 不採用 | **scope 外** | production の `build_fn` は official wrapper で固定されており、露出しているのは test seam。研究最優先・プロトタイプ基準に照らし、`buildcache.py` の production 変更は行わない。裁定パッケージへ返す。 |
| F-A4 / F-B4 (変異 (a) が exact-key 検査に先取りされる) | real | **採用** | scope 内 | 変異を 2 本へ分割する (M1: key 欠落 / M2: key 実在かつ無効)。 |
| F-A5 (変異 (c) の帰属が binary SHA 差で成立しない) | real | **採用** | scope 内 | 隔離入力を事前登録する (下記 4 の M4)。 |
| F-A6 (current policy の独立権威が無い) | real | **採用** | scope 内 | `build_admission.py` へ公開 policy resolver を置き、consumer は artifact を読まずに再構築する。 |
| F-A7 / F-B6 (`verify_floor_artifact` の権威不足・API 破壊) | real | **採用 (縮小形)** | scope 内 | 新必須引数を足さない。単体で検査できる範囲を無条件検査し、freeze entry 権威は ratified/holdout が持つと明記する。 |
| F-B1 (旧 portable artifact が全拒否される) | real | 不採用 (互換は実装しない) | **scope 外の影響報告** | tracked `output/s8b-freeze` の該当 0 件を実測済み。repo 外 run/resume artifact への影響は insight・handoff・worklog fragment へ返す (ユーザー指定どおり)。 |
| F-B3 (current policy 必須化が historical reverify と衝突) | real | **採用** | scope 内 | 経路で権威を分ける (下記 2-b)。report/judge は非接触とする。 |
| F-B5 (hash-only fixture が発行器を通らない) | real | **採用** | scope 内 | fixture を production issuer 由来の honest receipt へ。 |
| F-B7 (literal golden と将来 hash chain への波及) | real | **採用** | scope 内 | literal golden は新固定値へ更新。V1 trust root の path と SHA は書き換えない。 |
| F-B8 (部分書込み後の拒否で store が stale 化) | real | **採用** | scope 内 | `store_binaries` は 1 byte も書く前に全 record を preflight する。 |

## 2. プラン v2 の確定事項

### 2-a. (P1) の修正 — raw receipt コピーは不採用

親 brief の (P1) は「canonical admission receipt を exact-key field として持たせ、build 時に
receipt をコピーする」だった。段 2・段 3 の実測により、raw `build-admission/v1` は絶対パス
(`source_root`) を含み、その outer SHA も root 依存であるため、既存の「異なる root でも
production emitter の blob/tree/commit が同一」契約と両立しない。

**採用形**: 元の sealed `BuildAdmission` を発行時に完全検証したうえで、location である
`source_root` だけを除いた root 非依存の canonical 派生 receipt を永続化する。
source bytes digest、tracked diff、tracked paths、ccbench pin、policy、review input、cell、
binding、binary SHA は保持する。これは非同値な択一への差し戻しではなく、
コードで確認した実装不能性に基づく (P1) の具体化である。

### 2-b. 権威の経路分離 (F-A6 + F-B3)

- **live 経路** (build → store → portable projection → resume → floor 測定直前 → oracle 実走直前):
  `build_admission.py` の**公開 policy resolver** から現行 policy を独立に再構築し、receipt の
  `policy_sha256` と一致することまで要求する。**artifact 内の policy を期待値に使ってはならない**
  (恒真検査の禁止)。
- **historical reverify 経路** (published freeze の再検証): current policy 一致は要求しない。
  構造・exact key・canonical outer SHA・subject↔record 一致・freeze entry/binding 対応・
  cross-cell 整合だけを要求する。理由: policy は `CURRENT_PIN` から導出されるため、
  pin が進むと過去 freeze の再検証が原理的に落ちる。
- `s8b_oracle_report.py` と `s8b_oracle_judge.py` は**非接触**とする (境界の外)。

### 2-c. 保証名を狭める

この wave が保証するのは「**発行時に検証した admission の、保存から oracle 実走直前までの連続束縛**」
であり、「gateway が発行したことの暗号学的証明」ではない。docstring・insight・worklog に
この文言で書く。過大な保証名を書いてはならない (F-A1 の裁定に対応)。

[T-868] は同型の限界を機械可読な limitation 宣言 (`/limitations/...`) で明示している。ただし
その宣言経路は T-810 preregistration 族の機構であり、S8b portable record 側には**存在しない**
(`grep -rn "limitations/" --include=*.py orchestrator/campaign/` は 0 件)。DW-G04 に従い、
発火する既存 artifact path を書けない機構は新設せず、限界の記録は docstring・insight・worklog
fragment で行う。

### 2-d. 拒否する 4 型と発火層 (gate の禁止を署名で書く)

| 型 | 拒否する層 | 署名 |
|---|---|---|
| (a-1) receipt key 欠落 | portable exact-key 検査 | `set(record) != set(_PORTABLE_BUILT_KEYS)` |
| (a-2) key 実在・値が None / 空 / malformed | 新 validator の missing/structure gate | `validate_portable_binary_record()` |
| (b) receipt と record の不一致 | 新 validator の subject 照合 | `subject.binary_sha256 == record["binary_sha256"]` ほか |
| (c) 別 cell の valid receipt 組替え | 新 validator の cell/binding tuple gate | `(cell_id, holdout_id, configuration_id, entry_sha256, binding_sha256)` 完全一致 |
| (d) store bytes 差し替え | 発行時・store preflight・resume・測定直前・oracle 実走直前の bytes 再 hash | 既存 hash 検査を**残したまま** receipt subject と対応させる |

**通る正例**: fresh build → store → portable projection → resume → oracle pre-run を、
production issuer が発行した honest receipt で通す経路 (下記 3 の正例テスト)。

## 3. 実装 scope (段 5 の所有面)

production:

- 新設 `orchestrator/campaign/s8b_binary_admission.py` — 派生 receipt schema、発行器、exact validator、
  portable key 正本。
- `orchestrator/campaign/build_admission.py` — 公開 policy resolver の追加のみ (additive)。
  既存の発行・検証ロジックは変更しない。
- `orchestrator/campaign/s8b_floor_campaign.py` — 発行・搬送・store preflight・resume・測定直前。
- `orchestrator/campaign/s8b_floor_stats.py` — 縮小形の無条件検査 (新必須引数なし)。
- `orchestrator/campaign/s8b_ratified_freeze.py` — historical 経路の構造・subject・binding 検査。
- `orchestrator/campaign/s8b_holdout_freeze.py` — receiptless official result からの g1 candidate 生成を拒否。
- `orchestrator/campaign/s8b_oracle_driver.py` — `_prepare_v2_execution` で store 読込より前に検査。
- `orchestrator/campaign/s8b_materialization.py` — docstring 更新と helper 移設のみ。

**非接触**: `orchestrator/campaign/buildcache.py`、`s8b_oracle_report.py`、`s8b_oracle_judge.py`、
`output/s8b-freeze` の tracked bytes、V1 trust root の path と SHA。

test: 上記に対応する `orchestrator/tests/` 各 file と共有 fixture `s8b_v2_freeze_fixture.py`。

**分割方針**: 一枚岩 (単一 Codex author) とする。理由 = 新 leaf の API を他の全単位が消費し、
共有 fixture を 3 つ以上の test file が消費するため、存在しない API を凍結してからでないと
所有を素集合に割れない。

## 4. 変異事前登録 (DW-M01 — 単一理由性と帰属をコードで確認済み)

| ID | 型 | 変異 (production を 1 箇所だけ緩める) | 前後層の先取り確認 | 期待赤 |
|---|---|---|---|---|
| M1 | (a-1) | `_PORTABLE_BUILT_KEYS` から `"admission_receipt"` を除く | 除いた時点で key 欠落 record が受理される。他層は key 欠落を見ない | key 欠落を拒否するテスト |
| M2 | (a-2) | 新 validator の「receipt が None / 空」拒否分岐を受理へ反転 | key は存在するので exact-key 検査は発火しない (F-A4 の先取りを分離済み) | null/空 receipt 拒否テスト |
| M3 | (b) | `subject.binary_sha256` と record の equality 1 箇所を削除 | record・store・journal の SHA を揃えた入力では、この equality が唯一の semantic 差 | subject 不一致拒否テスト |
| M4 | (c) | cell/holdout tuple の完全一致 gate 1 箇所を削除 | **隔離入力**: binary・source・entry・binding が同一で `cell_id` / `holdout_id` だけ異なる 2 receipt。binary SHA 差で先取りされないことを入力側で保証 (F-A5) | receipt swap 拒否テスト |
| M5 | (d) | receipt subject と store bytes の対応検査 1 箇所を無効化 (既存の `actual != rec["binary_sha256"]` 分岐は残す) | 既存 hash 分岐を残すことで、新 gate 単独の検出力に帰属させる | store 差し替え拒否テスト (新 gate 側) |
| P1 | 正例 | 変異なし。受理集合を縮小する wave のため、**承認外の過剰拒否**を検出する正例を登録する | — | fresh build → store → projection → resume → oracle pre-run の正例が緑のまま |

harness は `tools/mutation_harness.py` を使う (DW-M05)。期待 node は fix 後の最終 commit で
再導出し完全集合とする (DW-M07/DW-M08)。

## 5. 成果物影響 (DW-G05)

未実装なら、admission を証明していない binary が同一 hash の store entry と record だけで
floor 測定値・floor manifest・oracle report の証拠鎖へ入る。実装後はその受理集合を拒否側へ狭める。
scope 外とした F-A1 / F-A2 / F-A3 を放置した場合の残余は、手書きの整合 artifact と
実走後の store 差し替えであり、これは裁定パッケージでユーザーへ返す。

## 6. ユーザーへ返す裁定パッケージ (段 7 で insight・handoff・worklog fragment へ)

1. 信頼根の不在 (F-A1/F-B2) — 保証は自己整合 provenance に留まる。署名/issuer chain の新設は
   既裁定と見送り既定に抵触するため実装しない。保証名を狭めて明記した。
2. 実走後の store 再検証 (F-A2) — report/judge は境界の外。塞ぐなら別 wave。
3. `BuildResult` の admission 結合 (F-A3) — production の build_fn 固定により実害は test seam。
4. 旧 portable artifact の拒否 (F-B1) — tracked repo 内は該当 0 件。repo 外の過去 run/resume store は
   再 build か破棄が必要。互換 loader・schema 移行・遡及再取得は実装していない。
5. `verify_floor_artifact` の残余 (F-A7) — 単体では freeze entry 権威を持たない。縮小形で明記した。
