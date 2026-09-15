# 段 4 裁定 — [T-2563] 認定較正 walltime 式

## 0. 結論

**第 3 案を採る。数値は 1 つも変えない。凍結式の文面を実体に合わせ、保証しない範囲を
成果物の文面へ出す。** 段 2 plan・段 3 sol・段 3 luna が独立に同じ案へ収束した。

本 wave は **T-2563 を完了にしない。** 成果は「予約式の不整合と保証限界の明文化」であり、
D1936 項38 が求める「最大経路を収容する」再凍結は未解決のまま残す。
D1971 の「時間式再凍結を完了扱いにしない」をそのまま維持する。

## 1. 親の 2 案はどちらも撤回する

### (P1) 要求枠を 7200 → 10800 へ上げる — 撤回

- **S-1 / L-5 [real]:** D1971 の逐語「要求時間増加へ戻さず」を、短縮策撤回後の増枠の
  許可とは読めない。恒久禁止と決めつける必要もないが、**今回積極的に認める根拠にはならない。**
- **L-5 [real]:** 枠を広げると、旧窓で timeout していた実行が新窓で成功する。
  完了して受理される実行の集合は広がる。「受理集合不変」とは言えない。
- **絶対規律 4:** 3250 秒は kill-switch の上限和であって所要ではない。実測の計測前は
  35〜39 秒 (2026-09-11 の 991694 / 991727)。実績 186 秒の job のために共有クラスタへ
  3 時間を要求するのは無造作に大きい。

### (P1′) `required_s` を 6610 → 5590 (配分) へ再定義する — 撤回

- **L-3 [real / 決定的]:** `reservation_budget()` は `3190 + 360p`。
  `--start-records 500000 --max-records 16000000` は p=6 で必要値 5950。
  現行 R=6610 なら通り、P1′ の R=5590 では `reservation-mismatch` で落ちる。
  **P1′ は受理集合を狭める。** 親が検算して一致を確認した。
- **S-2 [real]:** D1986 項 3 / 9 / 10 の対象は T-1912 / T-2469 / T-2485 であり、前文は
  「各実装は名指しの変更に限定」と定める。**限界を明記する説明方針の前例にはなるが、
  `required_s` の意味を変える授権にはならない。** 親は D1986 を過度に一般化していた。

## 2. 親の実測のうち反証・限定された 2 件

- **S-6 / L-6 [real / must-fix]:** 親の「窓不足は fail-closed に失敗するので誤認定は
  生じない」は**成立しない**。CLI は `cli.py:1017` で accepted を決めた後、
  `candidate.json`(1023) → 材料レポート(1028) → `registered/`(1067) を書き、
  `return 0`(1100) まで進む。**公開(1067)と終了(1100)の間に outer timeout の TERM を
  受ければ、accepted な公開物が残ったまま wrapper が非ゼロ終了しうる。**
  `calibration_verify.py` も `collect_receipt.py` も wrapper の rc を必須にしていない。
  - **ただし限定する (両子が一致):** 計測完了前に打ち切られた実行を部分標本から
    新たに accepted へ組み立てる経路は無い。accepted 判定は計測終了後である。
    残るのは**中身の妥当な較正が、失敗記録の job から公開されうる**という帳簿上のずれ。
  - **既存の限界であり、本 wave が新設したものではない (L-6)。**
    scope 外なので gate は作らない。文面の包括保証を撤回し、記録へ残す。
- **S-5 / L-2 [real / must-fix]:** 3250 も 8840 も「timeout 指定値の部分和」であって
  job の実時間上限ではない。timeout の無い処理が実在する — `git status` (S:210/448/512/623)、
  `git worktree add` (S:626)、`/proc` 全走査 (S:698)、worktree 削除 (S:99/960)、
  receipt I/O と `fsync` (C:302-318)、submit receipt 待ちの最大 60 回 `sleep 1` (S:197-200)。
  **文面から「真値」「最大経路の上限」という語を外す。**

## 3. 採る所見 (real)・退ける所見 (refuted)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| P2-1 / L-1 | 計測前は 3230 でなく **3250** (perf 候補 2 件で version+smoke が最大 4 回) | real | 採用 |
| P2-2 | 過去 receipt を現行式で再計算する consumer は **0 件** (attempts 59 件実読、5 経路追跡) | real | 採用。親の未確認 1 件が閉じた |
| S-4 | 「現在 2 通り」は限定が要る | real (nit) | 採用。「comment と receipt の食い違いは消えたが実処理との不整合は残る」へ言い換える |
| S-8 | 186 秒・35〜39 秒・長時間 directive の前例は保証へ一般化できない | real (nit) | 採用。文面で保証根拠に使わない |
| L-8 | 親 G の `test_pegasus_policy_registry.py` 説明が誤り (key 存在検査でなく移設済み key 名の集合定義) | real (nit) | 採用。記録で訂正 |
| L-9 | CLI 式の `2*sweep_reps*120` は certify 実行では走らない**予約定数** (`sweep.py:295` が scale 測定前に return) | real | 採用。文面で由来を区別 |
| S-3 | 認定較正を一律に止める裁定は無い | refuted | 採用 (進んでよい) |
| S-7 / L-4 | 5590 で小さい要求枠が通る経路は現行 wrapper で反証 (`S:238` の実行時一致検査) | refuted | 採用。ただし L-3 により P1′ は別理由で撤回 |
| S-9 | 別 script に同型欠陥は確認できない | refuted | 採用。scope を広げない |
| L-7 | plan の B1 方針は循環検査でない | refuted | 採用 |
| P2-5 / S-10 | 「裁定へ更新が必要」「再凍結完了と呼べない」 | real | **完了と呼ばない点は採用。裁定へ返す点は不採用** — 親が第 3 案で決める |

## 4. plan v2 — 実装面 (Codex `role=author`、D95)

**変える:**

1. `tools/pegasus/certify_calibration.sh` 冒頭 comment (6-11 行)。
   - `build_cap(CCBench=900 + gflags=60 + glog=120)(1080)` が名乗る内訳は実体と違う
     (gflags は 3 command で 180、glog は 3 command で 360、CCBench は 2 command で 1800、
     copy 360 / pristine 検証 120 / probe 240 / qstat 30 / hash+nm 120 / perf 40 は項に無い)。
     **値 1080 は据え置き**、名称と説明を「逐次上限ではなく予約配分の項」へ改める。
   - 計測前の timeout 指定値の和が **3250 秒**であること。
   - `3250 + 4990 + 600 = 8840 > 7200` であり、**最大経路の完遂を保証しない**こと。
   - 8840 自体も timeout の無い処理を含まない部分和であること (2 節の列挙)。
   - 打ち切られた attempt は計測未完了なら accepted を新たに作らないが、
     **公開後に TERM を受けた場合は accepted な公開物が残りうる**こと (既存の限界)。
   - CLI 予約項の `2*sweep_reps*120` は certify 実行では走らない予約定数であること。
2. `walltime_formula` 文字列 (771-775) に同じ限定を入れる。
   `finalize_reserve(600)` の token 形は残す (B6 が正規表現で拾う)。
3. `orchestrator/tests/test_pegasus_tools.py` の逐語 pin (212-216 付近) を新しい文字列へ差し替える。

**1 bit も変えない:** `frozen_required_s` の値 6610 と代入式、`#PBS -l elapstim_req=02:00:00`、
`calibration_v1.json` と `policy.json` の `certify_walltime(_s)`、`finalize_reserve_s=600`、
各 command の `timeout`、標本数 (points 5 / sweep_reps 3 / noise_reps 10)、cooldown の閾値・
間隔・回数・上限、`orchestrator/calibrator/cli.py` 全体、過去 receipt
(`output/env/pegasus/calibration/attempts/**`)。

**作らない:** 新しい gate・検査・台帳・framework・互換層・一般化。他 job script への波及。

## 5. 変異事前登録 (B-057)

本 wave の production 変更は receipt へ凍結される**記述文字列**であり、受理集合を変えない。
したがって `DW-M08` に従い、下記はすべて **kill ではなく diagnostic sensitivity pin** として
別枠に記録する。**変異 kill を実証したとは報告しない。**

| ID | 位置 | 変異 | 期待赤 (単一理由) |
|---|---|---|---|
| M1 | `certify_calibration.sh` `frozen_required_s` の代入式 | `1080` → `1081` | 代入式の逐語 pin |
| M2 | `certify_calibration.sh` `walltime_formula` | 限界説明の 1 節を削除 | formula の逐語 pin |
| M3 | `certify_calibration.sh` 冒頭 comment | `finalize_reserve(600)` → `finalize_reserve(599)` | `formula_reserves == {600}` の検査 |
| M4 | `certify_calibration.sh` `walltime_formula` | 合計 `=6610` → `=6611` | 合計値の逐語 pin |
| M5 | `certify_calibration.sh` PBS directive | `02:00:00` → `03:00:00` | PBS と policy の照合 |
| M6 | `calibration_v1.json` | `certify_walltime_s` 7200 → 7000 | `_hms_seconds` 換算一致 |

**新旧両走 (`DW-M08`):** M2 を変更前 HEAD 版へも走らせ、**旧 pin が検出しないこと**を示す。
これが「新しい文面が実際に守られているか」の唯一の検出力の証拠になる。

各変異は実装後に、同じ入力を拒否する層が前後にも内側にも無く赤理由が 1 つに絞れることを
確認する。絞れないものは登録から外し、実効 gate へ再照準する。

## 6. 残す未解決 (worklog の次の一手へ持ち越す)

- **T-2563 本体:** 最大経路を収容する再凍結は未解決。閉じるには要求枠を 8840 秒以上へ
  上げるユーザー裁定が要る。上げない場合、完了の定義を「文面の整合と限界の明示」へ
  狭める裁定が要る。**どちらも本 wave では決めない。**
- **公開後 TERM の帳簿ずれ (S-6 / L-6):** 既存の限界。gate は作らない。記録に残す。
