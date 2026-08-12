# 段 4 裁定 + プラン v2 — [T-783] + [T-747] (B)

親裁定。段 3 の 2 レンズは**いずれも NO-GO**。所見を real/refuted、採用/不採用、scope 内/外へ裁定し、
プラン v2 と変異事前登録を確定する。遷移は `4→5→6→7→8→9`（実装する）。

## 0. まず結論

**実装する。ただしプランを大幅に絞る。**

`DW-G04`（発火経路なしなら設計メモに留める）は本来なら停止条件だが、
**ユーザーはこの選択肢を見たうえで却下している** — 残余 wave の裁定パッケージ §4 S-4 は
選択肢 (a) 「W-1 が開くまで設計メモに留める (`DW-G04` の既定)」を明示提示し、ユーザーは (c) を選んだ。
その後 W-1 = [T-781] が保留終端になり、本 wave の command 引数で「本 wave で実装せよ」と指示された。
よって `DW-G04` はこの項目についてユーザー裁定で上書きされている。**再度返さない。**

一方、**裁定時点で未見の新事実**が 2 件あり、これらは `DW-S04` に従い実装せず再裁定へ返す
（親が不採用にするのではなく、ユーザー再裁定待ちへ戻す）。

## 1. 所見の裁定表

| # | 所見 | 判定 | 採否 | 根拠 |
|---|---|---|---|---|
| A-1 | authority から `module_list` を落とし、version を先頭行へ縮約している。穴は 2 件でなく実際は多い | **real** | **採用** | receipt に `module_list` は実在（`intelpython/2022.3.1`）。親が確認 |
| A-2 | P6「混用不可」は成立しない | **real** | **採用（P6 撤回）** | プラン自身も同じ結論。親も同意 |
| A-3 | attempt 脚は caller 注入値であり実測 provenance ではない | **real** | **不実装・再裁定へ返す** | official wrapper が非 default 引数を injection として拒否する（`:2763`）ため、配線は受理集合の設計判断になる。**裁定時点で未見** |
| A-4 / B2 | 新 report field は refreeze consumer の exact-key 検査で必ず拒否される | **real** | **不実装・再裁定へ返す** | `s8b_ratified_freeze.py` の `_MANIFEST_KEYS` / `_RESULT_KEYS` が exact。**裁定時点で未見** |
| A-5 | silo の dependency-pin predicate が変異未帰属 | **real** | **採用（変異 + テストを足す）** | A-3 で触る関数の中。安く閉じられる |
| A-6 / B7 | M-5 / M-6 / M-8 の一般化が過大 | **real** | **採用（brief を訂正）** | 親が bnode005 probe を確認。下記 §2 |
| B1 | pilot の発火 artifact path は実在しない | **real** | **採用（主張を撤回）** | `submit_floor.sh` に pilot 切替なし。親の brief の主張は refuted |
| B3 | S-2(a) の「手順書」側がプランに無い | **real** | **採用（段 7 で親が書く）** | runbook R-4 節へ逐語で書く |
| B4 | A-4 の official loader 所有境界が欠落 | **real** | **A-3 と同じ束で再裁定へ返す** | A-3 と不可分 |
| B5 | helper が floor / silo で同一受理集合でない | **real** | **採用（別 API に分離）** | 共通化のための共通化を避ける |
| B6 | scope 外に残る producer / consumer の列挙 | **real** | **裁定パッケージへ同送** | 実装しない |
| B8 | 三者照合結果が成果物から再検証できない | **real（moot）** | **A-3 と同じ束へ** | A-4 を実装しないので moot |
| A-7 | 手順書更新が段 5 所有一覧に無い | **real** | **採用** | docs は親が段 7 で書く（実装子は docs を触らない） |

## 2. 親 brief の訂正（レンズが正した親の主張）

- **撤回**: brief の発火経路節「A-2 の gate は pilot 床値 campaign で **runnable today**」。
  `tools/pegasus/submit_floor.sh` に pilot 切替は無く、投入 shell は official 固定。
  **今日走る床値 build の経路は存在しない。** 本 wave は「W-1 が開いた瞬間に効く束縛」を
  先に置くものであり、land 直後の発火はしない。
- **撤回**: P6「cc と cxx が同一 toolchain 由来であることを固定する」。
  固定できるのは「**登録済み cc/cxx 対と一致すること**」までである。
- **訂正**: M-5 / M-6 / M-8 は login node 1 台の観測。compute について親が追加確認した事実は次。
  - bnode005 でも `gcc-13` / `g++-13` は**不在**（`t293-perf-site/0_881960.nqsv/probe.json`）→ M-5 の結論は補強される。
  - bnode005 の cmake は **`cmake version 3.25.0`**（登録値と一致）。
    **M-8 の「cmake を束縛すると恒真な赤」は login 限定の現象**であり、compute では成立しない。
  - **compute 側の `gcc` / `g++` の realpath と version は未確認のまま**。
    → 初回の実 run で gate が拒否する可能性がある。**その拒否は正しい fail-closed であって bug ではない**、
    と手順書へ書く。

## 2.5 「混用不可」の定義を一次資料で確定した（親の追加調査）

command 引数の「混用不可を機械検査で固定してください」の一次資料を最新まで辿った。

- **worklog 383（[T-747] 初回裁定 (a)）**: 「**既存 `linux-baremetal` 床値との混用は不可**
  （環境束縛量として Pegasus で新規取得）」。
- **worklog 403（[T-747] 再裁定 (B)、最新）**: 「toolchain 束縛は env contract へ field を足さず
  契約の外へ置く — contract 内 `calibration_ref` の実 calibration bytes（compiler path/version・
  build argv を保持、既に hash 束縛）を **derived toolchain authority** とし、
  attempt 実測値と `build_v2` toolchain manifest を照合する。…**toolchain 混用不可の趣旨は不変**。」

**したがって「混用」= 環境／世代をまたぐ床値の混用**であり、cc/cxx の対の混用ではない
（親の P6 が想定していた意味は誤り。§2 で撤回済み）。

**本 wave の gate はこれを機械的に固定する** — `contract.calibration_ref` の calibration に
`acquisition_receipt` が無い契約（= `linux-baremetal`）では **receipt 不在で fail-closed に拒否**し、
receipt がある契約（= `pegasus` gen1/gen2）では実 toolchain が**その世代の登録値と一致する場合だけ**
build を通す。これにより「linux-baremetal の較正で Pegasus の binary を作る」「別世代の較正で作る」は
いずれも build 前に止まる。**これが command 引数の要求に対する本 wave の直接の回答である。**

また [T-747] (B) が指定する authority の所在（`calibration_ref` の実 bytes = receipt、
env contract に field を足さない）と、本 wave の実装（§3）は一致している。
contract hash を変えないので 3 pin（発効記録・floor protocol・selector 予測封印）も生きる。

## 2.6 A-4 を返す根拠の一次確認（親が実コードで確認）

`run_campaign`（`s8b_floor_campaign.py:2763-2790`）の official injection 拒否は
**引数名を明示列挙した dict** である。したがって新引数 `attempt_toolchain` を足すと、
**列挙に加えない限り official injection guard を素通りする**。
つまり A-4 を素直に足すと「official 経路で caller が用意した toolchain 値を『実測』として
受理する」穴が開く。これは規律 2（正しさゲートを緩める変異を採用しない）に触れる。
列挙に加えれば、将来の正規 official は必須値を渡した瞬間に必ず赤になる。

**どちらも受理集合の設計判断であり、裁定時点（worklog 403）で未見である。**
よって `DW-S04` に従い親が不採用にせず、**新事実つきでユーザー再裁定へ返す**。

## 3. プラン v2（実装する範囲）

### 実装する

1. **A-1**: `s8b_floor_campaign.build_cells` の `:1079` / `:1095` の `DEFAULT_CC` / `DEFAULT_CXX` を
   `buildcache.compilers_for_current_site()` の解決値へ寄せる。**cell ループの外で 1 度だけ解決**し、
   `source_digest.resolve_evidence` と `build_fn` へ同じ値を渡す。
2. **A-2'**: 新規 pure module `orchestrator/campaign/toolchain_binding.py` に
   **floor 専用 API** を置き、build 前に fail-closed で照合する。束縛するのは次。
   - `receipt.toolchain.compiler_path` = build_argv の唯一の `-DCMAKE_C_COMPILER` = live cc realpath
   - build_argv の唯一の `-DCMAKE_CXX_COMPILER` = live cxx realpath
   - `body(receipt.toolchain.compiler_version)` = `body(live cc version)`
     — **先頭行だけでなく全文を比較する**。argv0 正規化は先頭行にのみ適用する（A-1 への対処）
   - `body(receipt.toolchain.cmake_version)` = `body(live cmake version)`（全文）
   - **(P7 新規)** `body(live cxx version)` = `body(live cc version)`
     — receipt に cxx version が無い穴を、**live 側の内部整合**で部分的に閉じる。
     A-2 が挙げた「同じ path に別 version の frontend」を殺す。
   - **receipt 不在は拒否**（`linux-baremetal` は fail-closed 側へ倒れる。production 影響なしを §4 で確認済み）
   - C / CXX の定義が 0 件または複数なら拒否（first-wins を作らない）
3. **A-2''**: `buildcache.build_v2` に **narrowing-only** の任意引数
   `expected_toolchain_manifest` を足し、`_toolchain_manifest` 実測との不一致を拒否する
   （gate と実 build の間の再観測 drift = TOCTOU を閉じる）。floor は必ず渡す。
4. **A-3**: silo ladder を helper へ寄せる。**silo の受理集合を 1 bit も変えない**。
   floor 用 API と silo 用 API を**分ける**（B5）。共有するのは
   `tool_version_body` と build_argv 抽出だけ。
5. **A-5**: silo の `registered_dependency_pins != dependency_pins` を殺すテストを新設する。

### 実装しない（`DW-S04` に従い新事実つきで再裁定へ返す）

- **A-4（attempt 実測値の脚）全体**。S-3 = (a) は裁定済みだが、次の 2 点は裁定時点で未見。
  1. official wrapper（`s8b_floor_campaign.py:2763`）が非 default 引数をすべて injection として拒否する。
     `attempt_toolchain` を通すには**この拒否集合を変える**必要があり、受理集合の設計判断である。
  2. attempt snapshot を PBS job ID / submission nonce / execution receipt / raw file hash へ
     束縛する設計が無く、現状のまま入れると **caller 注入値を「実測」と記録する恒真な緑**になる。
  → 裁定パッケージへ。**shell (`floor_campaign.sh`) は本 wave では 1 行も触らない。**
- **成果物（manifest / result）への binding report 追記**。S-2 の「成果物へ穴を明記」に相当するが、
  `s8b_ratified_freeze.py` の `_MANIFEST_KEYS` / `_RESULT_KEYS` が exact-key であり、
  追記すると **refreeze consumer が全件拒否**する。schema 改版と consumer 改修を同じ land に
  含める必要があり、裁定の scope を超える。→ 裁定パッケージへ。
  **穴の明記は手順書側（runbook）で果たす**（S-2 の「手順書」の脚は本 wave で閉じる）。

### 既知の穴（手順書へ逐語で書く。段 7、親）

`cmake_realpath` / `cxx_version` / `module_list` / 実行ファイルの bytes hash は**束縛しない**。
`cxx_version` は (P7) の live 内部整合で部分的にのみ塞がる。

## 4. 成果物影響（`DW-G05`）

- **A-1 だけ land**: 床値 build の受理集合が**拡大**し、認可外 compiler の binary が床値になりうる。**禁止**。
- **A-2' だけ land**: 受理集合不変（build は gcc-13 不在で従来どおり倒れる）。安全側。
- **両方 land（本 wave）**: 今日走る経路が無いため**受理集合の実効変化はゼロ**。
  W-1 が開いた時点で、認可外 toolchain の床値が fail-closed で拒否される。
- **linux-baremetal**: 拒否側へ倒れる。`output/s8b-freeze/floor_protocol.json` の `env_tag` は
  `pegasus` であり、linux-baremetal を指す凍結 protocol は存在しない（親が確認）。**production 影響なし**。

## 5. 変異事前登録（`DW-M01`）

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」ことを実装後に確認してから本走する
（`DW-M07`）。受理集合を**縮小**する wave なので、**過剰拒否を検出する正例**も登録する。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M01 | floor gate の cc realpath 比較 | 比較を恒真 `True` へ | KILLED |
| M02 | floor gate の cxx realpath 比較 | 比較を恒真 `True` へ | KILLED |
| M03 | floor gate の cc version body 比較 | 全文比較を**先頭行のみ**へ弱める | KILLED |
| M04 | floor gate の cmake version body 比較 | 比較を恒真 `True` へ | KILLED |
| M05 | (P7) live cxx ↔ live cc version 整合 | 比較を恒真 `True` へ | KILLED |
| M06 | build_argv の C/CXX 抽出 | 複数定義の拒否を `next()` の first-wins へ | KILLED |
| M07 | **`_bind_current_toolchain` の `if calibration is None:` 分岐**（helper 側ではない） | 拒否をやめ `return {}` で素通りへ | KILLED |
| M08 | `build_cells` の site 解決 | `compilers_for_current_site()` を `DEFAULT_CC/CXX` へ戻す | KILLED |
| M09 | `build_v2` の `expected_toolchain_manifest` 照合 | 不一致 raise を削除 | KILLED |
| M10 | silo の `registered_dependency_pins` 比較 | 比較を恒真 `True` へ | KILLED（A-5） |
| M11 | silo の `tool_version_body` 呼び出し | argv0 除去をやめ逐語比較へ | KILLED |
| **M12（正例）** | floor gate 全体 | 登録値と完全一致する正常入力 | **SURVIVED 期待なし＝通過を確認**（過剰拒否検出） |

M12 は「gate を厳しくしすぎて正規入力まで落ちていないか」を見る正例であり、
`DW-M01` の「承認外の過剰拒否を検出する正例」に相当する。**kill を数えない**。

**M07 の照準を実装後に修正した（`DW-M01` の「前後に同じ入力を拒否する層が無いこと」検査）。**
実装の `_bind_current_toolchain` は `calibration is None` のとき、helper を
`receipt_toolchain=None` で呼んで False を確認してから raise し、
False でなくても別の raise に落ちる。つまり **helper 側の None 分岐を変異させても
挙動は変わらず、診断文字列しか変わらない**（`DW-M03` により kill にしない）。
実効 gate は `_bind_current_toolchain` の `if calibration is None:` 分岐そのものなので、
M07 はそちらへ再照準した。`VerifiedCalibration.calibration` は legacy schema
（= `linux-baremetal`）のとき構造上 `None` になることを親が確認済み
（`calibration_verify.py:59-61`）。

## 6. 段 5 の所有分割（素集合）

- **単位 A**（先行）: `orchestrator/campaign/toolchain_binding.py`（新規）、
  `orchestrator/campaign/silo_ladder_rung1.py`、`orchestrator/tests/test_toolchain_binding.py`
- **単位 B**（A 完了後）: `orchestrator/campaign/buildcache.py`、
  `orchestrator/campaign/s8b_floor_campaign.py`、`orchestrator/tests/test_buildcache_v2.py`、
  `orchestrator/tests/test_s8b_floor_campaign.py`

`tools/pegasus/floor_campaign.sh`、`orchestrator/tests/test_pegasus_floor_tools.py`、
`orchestrator/tests/test_s8b_materialization.py`、`s8b_ratified_freeze.py`、
`env_contract.py`、calibration JSON、`FROZEN_MANIFEST` は**どちらも所有しない**（A-4 と report 追記を
落としたため触る必要が無い）。

## 7. 裁定パッケージへ返す項目（段 7 で起草）

1. **S-3 の attempt 脚を実 provenance にするか** — official injection 拒否集合の変更と、
   PBS job / nonce / receipt / file hash への束縛が必要。
2. **floor artifact schema と refreeze consumer** — `build_toolchain_binding` を
   top-level 必須にするなら manifest / result の schema 改版 + `s8b_ratified_freeze` の
   独立照合 + manifest ↔ result ↔ calibration 一致検査を同じ land に含める必要がある。
3. **完全な toolchain identity** — cxx version / bytes hash / cmake path / module_list を
   authority に足すには calibration 再発行（S-2 (b)）が要る。
4. **scope 外に残る producer / consumer**（B6 の表）。
5. **[T-748] W-2** — 投入不可の実測 3 点と、W-1 保留終端との関係。
