# 段 4 裁定 — dev-wave-t8b-restart-integration

親が段 3 の 2 レンズ (A = 正しさ境界 / B = 整合・実効性) の所見を real/refuted・採否・scope 内外へ裁定する。
両レンズとも **NO-GO**。BLOCKER は A が 6 件、B が 5 件。

## 裁定の結論

| 単位 | 裁定 | 理由 |
|---|---|---|
| **T-749** verify CLI | **実装する** (TOCTOU 硬化込み) | 所見は実装内で閉じる。受理集合は CLI に閉じ、oracle gate を変えない |
| **W-1** official 解禁 | **実装しない → 再裁定へ** | D86 §4 の中核前提 (機械的 admission が構成可能) が A-1/A-2/A-5 で崩れた |
| **W-3** freeze v2 producer | **実装しない → 再裁定へ** | producer identity (A-7) と budget authority (A-10) が未定。floor 値も不在 (A-12) |
| **W-4** oracle manifest CLI | **実装しない → 再裁定へ** | A-9 が certified 選択を直接改変する経路を示した。schedule authority が不在 |
| **R-4** toolchain (T-747) | **実装しない → 再裁定へ** | 段 1 実測 (M2/M3) + A-11 の訂正込みで返す |

`DW-S04`「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ。止めるときも親が
不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」に従う。親は W-1/W-3/W-4 を**不採用にしない**。

## 所見の裁定 (real / refuted)

### real・採用 (T-749 の実装へ反映する)

- **A-6 / B-5 (TOCTOU)**: real。`verify_receipt()` が canonical file を内部で再読するため、
  capture した bytes と receipt が判定した bytes が別物になりうる。
  → **採用**: CLI helper は raw bytes を一度 capture し、`verify_receipt()` 呼出し後に**同じ path を
  再読して bytes 同一性を要求**する。差があれば赤。`active-valid` で receipt と capture が不一致なら
  legacy fallback へ戻さず**即赤**。fallback 経路でも path を再読しない
- **A-6 後段 (adapter の非発火時 observation)**: real。mismatch 時に adapter を呼べば恒真化する。
  → **採用**: adapter は「active-valid かつ exact 一致」の場合にだけ呼ぶ

### real・scope 外 (裁定パッケージへ)

- **A-1 (固定 FD は spool 証拠にならない)**: real。BLOCKER。W-1 の中核機構が成立しない
- **A-2 (receipt が認可・revision authority に化ける)**: real。BLOCKER。D86(8) の禁止に抵触
- **A-3 (private core が public 13 seam 拒否を迂回)**: real。`_run_campaign_core` は `measure_fn` 等を
  受理し続ける。W-1 実装時に必ず同時に閉じる必要がある
- **A-4 (`VerifiedFreeze` が forgeable かつ document が mutable)**: real。既登録の [T-090] と同型
- **A-5 (admission が downstream proof chain から消える)**: real。BLOCKER。
  certificate v2 / journal / ratified verifier の拡張は D86(5) が明示的に先送りした項目
- **A-7 (producer identity を記録できない)**: real。transition table が `/generator/path` の変更を拒否する
- **A-9 (縮小 schedule で自明な winner)**: real。BLOCKER。certified 選択を直接改変する
- **A-10 (budget authority 不在)** / **B-10 (reviewed spec の権威不在)**: real。設計択一
- **A-12 (proof graph 上は独立でない)**: real。親の「contract hash に触れないから独立」は
  編集面の独立であって成果物依存の独立ではない。**親の裁定を訂正する**
- **B-1 (admission が claim より後)**: real。実コードで確認 (`acquire_claim` は claim を
  最初の副作用にする意図的設計)。W-1 実装時の必須要件
- **B-7 / B-8 / B-9 / A-8 (path containment・namespace)**: real。W-1/W-3/W-4 実装時に同時に閉じる

### real・親の実測の訂正

- **A-11 / B-12 (M4 の一般化しすぎ)**: real。**親の M4 を訂正した**。
  床値は `build_v2` を使い、その pre-image は cc/cxx と toolchain manifest hash を含むため保護されている。
  偽 hit の危険は legacy `cache_key` 経路に限られる
- **B-11 (M1 の閉包不足)**: real。**親の M1 を訂正した**。gcc-13 は module/spack/conda には無いが、
  apt の PPA に候補が存在し (root 必要)、コンテナ経路も残る。「物理的に閉じている」は言い過ぎ
- **A-11 後段 (calibration からの derived toolchain 束縛)**: real かつ**有用**。
  contract の `calibration_ref` は既に hash 束縛されており、その実 calibration bytes は
  gcc path/version と build argv を保持している。これを derived toolchain authority として使えば
  **contract hash を変えずに toolchain を束縛できる**。→ 裁定パッケージの択 (B) を具体化する

### refuted / 不採用

- **B-14「wave を分割すべき」**: 方向は real だが、本裁定で実装が T-749 1 件へ縮むため解消済み
- **B-13「W-2/W-5 の実装・preflight は前進できる」**: partial。compiler binding の設計は前進できるが、
  それ自体が R-4 の再裁定対象であり、先回り実装は `DW-S04` に反する。**不採用**

## プラン v2 (実装するもの = T-749 のみ)

`orchestrator/campaign/s8b_holdout_freeze.py` に CLI 専用 helper を追加する。
`verify()` / `verify_document()` / `generate` / `search` は 1 byte も変えない。
`t080_freeze_migration.py` と `s8b_oracle_driver.py` は編集しない。

### gate の署名 (禁止を署名で書く)

CLI `verify` が **T-080 例外を適用してよいのは、次のすべてが成り立つときだけ**である。

1. 対象 path が非 symlink の regular file であり、canonical active path と exact 一致する
2. 対象 bytes を一度 capture した
3. `verify_receipt()` が `active-valid` を返し、refusal が空である
4. capture した bytes の sha256 が receipt の固定値と exact 一致する
5. `verify_receipt()` 呼出し後に同じ path を再読した bytes が capture と exact 一致する

1〜5 のいずれかが崩れたら例外を適用しない。
`active-valid` かつ 4 が崩れた場合は legacy fallback へ戻さず**即赤**とする。
`never-issued` のときだけ既存 `verify()` へ委譲する。

**通る正例 (1 件)**: 現行 repo の `output/s8b-freeze/holdout_freeze.json` に対する
`verify` が rc=0 を返すこと (現在は恒常的に rc=1)。

## 変異事前登録 (`DW-M01`)

実装前に登録する。各変異は単一理由性をコードで確認してから登録する。

| ID | 変異 | 期待 |
|---|---|---|
| MU-1 | `active-valid` かつ capture と receipt が不一致のとき即赤にする分岐を、legacy fallback へ戻す形へ反転 | KILLED (新規 negative test) |
| MU-2 | canonical path exact 一致の検査を撤去 | KILLED (alternate path に同 bytes を置いた negative test) |
| MU-3 | `verify_receipt()` 後の再読・bytes 同一性検査を撤去 | KILLED (TOCTOU test) |
| MU-4 | `never-issued` のとき `verify()` へ委譲せず無条件で緑を返す | KILLED (未受領 drift が赤のままであることの test) |
| MU-5 (正例) | 実 repo の holdout に対する CLI verify | 変異なしで rc=0 (過剰拒否がないことの正例) |

`DW-M03` に従い、診断文字列だけの赤は kill に数えない。

## 成果物への影響 (`DW-G05`)

- **T-749 を実装しない場合**: 再開手順のたびに単体 verify CLI が恒常的に赤を返し、
  本物の freeze 破損と区別できない。生死判定が oracle gate-check 1 本に依存し続け、検出力を失う
- **W-1/W-3/W-4 を今 実装した場合** (実装しない理由): 恒真な admission が official の受理集合を
  ∅ から非空へ広げ、wrapper を経ない起動が作った floor 値が freeze v2・oracle レポート・
  certified 選択へ流入しうる。**規律 2 に正面から抵触する**

## 段 5 の分割

実装子は **1 本のみ** (T-749)。所有 = `orchestrator/campaign/s8b_holdout_freeze.py` と
`orchestrator/tests/test_s8b_holdout_freeze.py` (存在すれば)。並列分割は不要。
