# [T-2566] 段 4 裁定 — real/refuted、採否、scope、プラン v2、変異事前登録

裁定時点の local main = `a551cdd30` (wave 開始時から動いていないことを確認済み)。
裁定 inbox の再走査 = `docs/decisions.md` の該当 D を再読。wave 開始後の新しい裁定は無い。

## 1. 所見の裁定

| # | 出所 | 判定 | 採否 | scope | 根拠 |
|---|---|---|---|---|---|
| A1 | consult A | **real** | 採用 (must-fix) | 内 | 五 probe の成功は、正常な 3 campaign が非 `invalid` に到達することを含意しない。T-2500 は同型の到達不能欠陥を自分で作り込んだ実績がある |
| A2 | consult A | **real** | 採用 (親の資料訂正) | 内 | 親の実測前提が最初の cell の値を走全体へ一般化していた。型契約として転記されると正常な整数表記 throughput を拒否しうる |
| B1 | consult B | **real** | **一部採用・一部 scope 外** | 下記 | 投入 shell と job script は旧 3 run kind しか受理せず、新 run kind は shell 境界で拒否される |
| B2 | consult B | **real** | 採用 (must-fix) | 内 | spec を「読んだだけ」でも拒否側の変異試験は通る。spec の値を変えたら挙動が変わる正例が無い |
| B3 | consult B | **real** | 採用 (分割の組み直し) | 内 | 親の 3 所有分割は責務名で切っており、プランの file 配置と重なる。commit は親の担当なので子に渡せない |
| B4 | consult B | **real** | 採用 (焦点走へ追加) | 内 | `orchestrator/tests/test_screening_opt_in.py` が `loop.py` の全文を読む。焦点走の列挙から漏れていた |
| B5 | consult B | **refuted** | — | — | hash の分離と代替 stdout の実在は、consult B と**親が独立に**現物で確かめて一致した |
| 段2-1 | plan | **real** | 採用 | 内 | 探索成果物に生 stdout は無い。親も検索して 0 件を確認済み |
| 段2-2 | plan | **real** | 採用 | 内 | `run_campaign` に correctness workload を渡す引数が無い。親が signature を読んで確認済み |
| 段2-3 | plan | **real** | 採用 | 内 | `test_campaign.py` の 2 つの exact Counter が親の列挙から漏れていた。親が現物で確認済み |
| 段2-4〜7 | plan | **real** | 採用 | 内 | manual-build 在庫の一般化、runner の片側アンカー、契約 loader 対象の不足、同居関係文書の扱い。consult A / B も独立に支持した |
| 段2-8 | plan | **real** | 採用 (言い方の是正) | 内 | 「唯一の blocker が外れる」は過大。B1 と併せて是正する |

### B1 の分割

**scope 内として実装する:** 新 module 自身の CLI 入口 (`main()`)、campaign 設定生成、loader、
`analyze_cohort`、report materializer。これらは §8.2 が要求する report schema と成果物 stem を
発行する主体であり、A1 の正例を組むためにも必要である。

**scope 外として裁定パッケージへ返す:** `tools/pegasus/submit_b10_backoff_grid.sh`、
`tools/pegasus/b10_backoff_grid.sh`、job script の完了確認が新 run kind と新 stem を受理するための
配線と、3 job の成果物を 1 cohort として集める投入側の入口。理由は次の 3 つ。

- 依頼は「本走の投入はこの wave では行わない」と明示している。投入経路の配線は投入の一部であり、
  受理集合を変える shell 境界の改造を、投入しない wave で実測なしに足すのは `DW-G04` に反する
  (発火条件を満たす計測 ID を brief に書けない)。
- 投入 shell は既存 3 系列が現に使っている経路である。**既存 3 系列の受理集合を変えない**という
  不変条件に最も近い面であり、変えるなら独立の設計と変異が要る。
- これを残しても §8.1 の 5 件の充足判定は変わらない。5 件はいずれも Python 側の consumer・保存・
  発行・記録の性質だからである。

**したがって親は「本走投入の唯一の blocker が外れる」とは書かない。** 正しい言い方は
「§8.1 の 5 件が外れ、残る blocker は投入経路の配線 1 件になる」である。これを段 7 の記録と
次の一手へそのまま書く。

## 2. プラン v2 — 段 2 プランからの差分だけを書く

段 2 プラン (`04-plan.md`) を base とし、次を上書きする。それ以外はプランのとおり。

1. **`analyze_cohort` の正例を受入条件に入れる (A1)。** production writer が発行した
   3 campaign 分の完全な入力 (3 workload × 8 genome × 性能 5 rep × 正しさ 5 本) を組み、
   `analyze_cohort` が**非 `invalid` の verdict を literal で返す**ことを検査する。
   さらに次の 2 つの変異がこの正例を落とすことを確認する — (i) verdict を常に `invalid` にする変異、
   (ii) 3 job の同一性条件へ workload 座標を加える変異 (T-2500 型)。
   **この正例は「CV gate を通る cohort」を構成する必要がある。** 保存済み T-139 stdout の
   R01〜R05 は throughput が 76 万〜1071 万と散らばるので、cohort の正例には使えない。
   保存経路の実測 (条件 2) と cohort の正例 (A1) は別の入力で組む。
2. **spec の因果を示す正例を入れる (B2)。** 試験用 spec の `execution.records` を変えると、
   同じ production の引数生成経路を通って CCBench の `-ycsb_tuple_num` が変わることを示す。
   解析側は `variability.maximum_cv_exclusive` を変えると、**同じ観測**に対する gate の結果が
   変わることを示す。登録済み文書は変えない。実計測もしない。
3. **条件 2 の注入点を固定する (B からの具体化)。** 実 `measure_point` に、保存済み stdout を返す
   薄い `subprocess_runner` を渡す。`run_once` や `measure_point` の**戻り値そのものを合成しない**。
   deferred 側は `text=False` に合わせて bytes を返し、`.open()` まで通す。
   `test_campaign.py` の実 verifier fixture は `measure_point` を fake に置換しているので、
   **条件 2 の保存経路の証明には流用しない** (条件 4 の参考にはしてよい)。
4. **焦点走へ `orchestrator/tests/test_screening_opt_in.py` を加える (B4)。** 同 test は
   `loop.py` の全文を読んで `ScreeningConfig` と `screening=` の不存在を検査する。
   **期待値を緩めない。** 新引数の名前がこの検査に抵触しないことを実装側で担保する。
5. **契約 loader の記述を厳密化する (B の指摘)。** `verify_live_contract_loader_binding` が
   照合するのは binding に記録された commit の blob であって、常に HEAD ではない。
   親の手順は「実装 → 親が統合 commit → その commit を base に焦点走」とする。
6. **段 5 の所有を file path で切り直す (B3、下記 §3)。**

## 3. 段 5 の所有 — file path の素集合で切る

**第 1 波 (並列 2 子、所有 path は素集合)**

- **子 A (author):** `orchestrator/campaign/b10_backoff_static_tail_formal.py` (新規) と
  `orchestrator/tests/test_b10_backoff_static_tail_formal.py` (新規) **だけ**。
  spec consumer、2 つの hash、格子再計算、campaign 設定、driver 入口、loader、`analyze_cohort`、
  report materializer、5 条件の probe、A1 の正例と 2 変異、B2 の正例を持つ。
- **子 B (author):** `orchestrator/calibrator/benchparse.py`、`orchestrator/calibrator/runner.py`、
  `orchestrator/campaign/pipeline.py`、`orchestrator/campaign/loop.py`、
  `orchestrator/tests/test_layer3_report.py` **だけ**。整数 parser の新設、rep ごと整数カウンタの
  opt-in 保存、`reps` conditional key の追加、correctness workload の転送配線を持つ。

**第 2 波 (単独、第 1 波の統合 commit 後)**

- **子 C (author):** `orchestrator/tests/test_official_perf_closure.py`、
  `orchestrator/tests/test_p3_build_authority_cli.py`、
  `orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/test_campaign.py`、
  `orchestrator/tests/acceptance_duration_ledger.json` **だけ**。実 call site が確定した後に
  exact 閉包の登録簿を更新する。**件数は実装の現物から数える。推定で埋めない。**

親は各波の後に統合 commit を作り、その commit を base に焦点走を回す。子は commit しない。

## 4. gate の禁止と、通る正例 (署名で書く)

この wave が新設する gate の禁止を、署名で書く。**各禁止に、通る正例を 1 つ添える。**

- `parse_preregistration(raw: bytes) -> StaticTailSpec` は、marker 対が 1 組でない bytes、
  fence を除いた残りが JSON として parse できない bytes、§5 の top-level section 集合と
  一致しない document を**拒否する**。
  **通る正例:** `docs/b10-backoff-static-tail-preregistration.md` の現物の raw bytes。
- `load_preregistration(repo_root, commit) -> PreregistrationBinding` は、canonical path 以外、
  symlink、指定 commit の blob 内容と作業木 bytes の不一致、祖先でない commit を**拒否する**。
  **通る正例:** repo root と、この文書を含む commit。
- 性能 observation の受理は、`reps` が 5 本ちょうどで `rep_index` が `0..4` の重複なし全数、
  `abort_counts_` と `commit_counts_` が非負整数で和が正、`throughput_tps` が有限かつ正、
  `reps[i].throughput_tps == tps[i]` をすべて満たすときだけ成立する。
  **通る正例:** 保存済み T-139 stdout を注入して production writer が発行した 5 rep の記録。
- 正しさの受理は、採用 attempt に束縛された `verify_done` が 5 本あり、全件 `certified is True`、
  anomaly 0 件、`payload.workload.tag` が探索の値と一致するときだけ成立する。
  **通る正例:** 実 verifier に `g1_serial` trace fixture を 5 回通して発行した 5 本。
- `analyze_cohort` は、3 campaign の CCBench source digest・toolchain・環境契約・較正 identity・
  事前登録の 3 つの hash・動作点 literal が一致し、workload 名の集合が
  `write-heavy` / `balanced` / `read-heavy` を重複なく過不足なく覆うときだけ非 `invalid` を返す。
  **通る正例:** §2 の 1 で組む 3 campaign の完全な入力。

## 5. 変異事前登録 (DW-M01)

実装前に登録する。各変異は位置を 1 箇所に固定し、赤理由が 1 つに絞れることを実装後に確認する。
確認できない変異は登録を取り下げ、実効 gate へ再照準する。期待 node は完全集合として、
段 6 の fix 後 anchor で再検証してから本走する。

| ID | 位置 (実装後に確定) | 変異内容 | 期待 |
|---|---|---|---|
| M1 | 新 module の spec 抽出 | fence 除去を 1 行分ずらす | KILLED — `spec_sha256` が登録値と不一致になる |
| M2 | 新 module の hash 計算 | `document_blob_sha256` に Git blob ID を代入する | KILLED — raw bytes の SHA-256 と不一致 |
| M3 | 新 module の解析入力 | 再計算の代わりに `leading_indicators.abort_rate` を使う | KILLED — 丸め値が解析へ入る |
| M4 | 新 module の正しさ受理 | 5 本要求を 1 本以上へ緩める | KILLED — 規律 2 の弱体化 |
| M5 | 新 module の cohort 同一性 | 同一性条件へ workload 座標を加える | KILLED — A1 の正例が `invalid` になる |
| M6 | 新 module の verdict | verdict を常に `invalid` にする | KILLED — A1 の正例が落ちる |
| M7 | 新 module の spec 消費 | `execution.records` を spec から読まずコード定数にする | KILLED — B2 の正例で引数が変わらなくなる |
| M8 | `pipeline.py` の payload 組立 | `reps` の要素から `abort_counts_` を落とす | KILLED — 保存経路の検査 |
| M9 | `pipeline.py` の opt-in | opt-in 無しでも `reps` を常に付ける | KILLED — 既存 3 系列の payload key 集合が変わる |
| M10 | `runner.py` の整数取得 | 失敗 rep の初期値 `None` を成功値として運ぶ | KILLED — 型・範囲検査 |
| M11 | `benchparse.py` の整数 parser | 小数表記を受理する | KILLED — 字句形式の検査 |
| M12 | `loop.py` の correctness 転送 | 転送をやめて既定 1 回に戻す | KILLED — 1 cell 5 本が出なくなる |

**両層変異 (mask の裏取り、DW-M04):** M4 と M12 は「5 本」を別の層で守る。片方だけ変異させて
SURVIVED なら、両層同時変異まで裏取りして mask を確かめる。期待は両層同時変異で KILLED。

**受理集合を縮小しない wave なので過剰拒否の正例は登録しない** — 本 wave は新しい受理集合を
**追加**するだけで、既存 3 系列の受理集合を縮小しない。これが成り立つことは M9 が守る。

## 6. 親の資料訂正 (A2、B の厳密化)

`02-measured-premises.md` を次のとおり訂正する。実装子へはこの訂正後の版を渡す。

- 走行記録 1 行の exact key 集合は `env_tag, payload, stage, ts, variant` の **5 件**。
  「4 件」は payload を除いた envelope 側の座標という限定でだけ正しい。
- `tps` の最初の配列は `[3958382, 3752160, 3727702, 3692363, 3695293]` という**整数表記**で
  保存されている。「浮動小数」と型契約に書かない。
- `leading_indicators.abort_rate` の `0.6869` と正しさ counter の `630878 / 240566` は
  **最初の cell の値**であって走全体の値ではない。balanced の 5 cell の代表 abort 率は
  `[0.6869, 0.0404, 0.211, 0.0145, 0.0268]`。
- 契約 loader の束縛対象には `orchestrator/calibrator/runner.py` も含まれる。照合先は
  binding に記録された commit の blob であって、常に HEAD ではない。
- 条件 2 の入力は探索成果物ではなく
  `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log` 系列を使う。
  親が実在と 4 値 (abort `24435129` / commit `2270481` / 印字率 `0.9150` /
  throughput `756827`) を確かめた。

## 7. scope 外として返すもの (裁定パッケージ候補)

1. **投入経路の配線 (B1)。** 新 run kind と新 stem を受理する投入 shell・job script・
   3 job の cohort 集約入口。**これが残る唯一の blocker**である。次の一手へ独立項目として書く。
2. 本走の実投入そのもの。
3. `tools/check_docs.py` への事前登録本文検査の追加 (裁定項45 で見送り済み。蒸し返さない)。
