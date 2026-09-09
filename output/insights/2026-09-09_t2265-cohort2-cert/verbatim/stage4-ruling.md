# 段 4 裁定 — [T-2265] cohort 2 の seed 別実行体と 24 スレッド条件の直列性認証

段 2 プラン (`out/stage2-plan.md`)、段 3 sol (`out/stage3-sol.md`)、段 3 luna
(`out/stage3-luna.md`) を裁定した。親が独立に現物で確かめた項目は「親実測」と書く。

---

## R1. performance artifact 束縛 — **real、実機 blocker。設計をやり直す**

luna 1 / sol 3 / プラン裁定点 1。

**親実測。** `_certify_main` は `expected_repo_head = repo_head` (その走行の HEAD) を渡し
(`t2187_adaptive_const_probe.py:3188,3194`)、`_performance_artifact_identity` が
`document.get("repo_head") != expected_repo_head` で `performance-artifact-identity-mismatch` を
投げる (同 1997 行)。前 wave の performance 成果物は `repo_head 8bdf173cc` に束縛されており、
本 wave の commit とは必ず異なる。**そのまま投入すれば 312 job 全件が build 前に落ち、
成果物は 1 件も出ない。**

**裁定: 本 wave の認証 commit で trace-disabled の binding performance 成果物を作り直す。**
既存の `expected_repo_head` 検査は 1 文字も緩めない。

- p1 用 1 本 (seed 指定なし)、p2 用 12 本 (事前登録 seed 各 1 本) の計 **13 performance job**。
- いずれも `EXTIME=6`、`THREADS=24+48` で走らせ、24 と 48 の両 thread row を 1 本の成果物に持たせる。
- 規律 1 は守られる。performance job は trace-disabled build、認証 job は trace-enabled build の
  **別ビルド・別 run** である。本 wave はこの 13 本の性能値を研究上の主張に一切使わない
  (identity 束縛のためだけに作る)。

**却下: `expected_repo_head` を緩めて旧成果物を historical reference として通す案** (luna 1 の
第 1 推奨、プラン裁定点 1)。これは既存の exact 検査を弱める変異であり絶対規律 2 に反する。

**副次的帰結: sol 3 の懸念は R1 で消える。** seed X の認証が seed X の performance 成果物に
束縛されるので、`performance_artifact` field の意味は「同じ commit・同じ genome・同じ seed で
測った成果物」のまま保たれる。field 分割も schema 昇格も不要。

**追加の狭め (narrowing なので採用):** performance 成果物が**認証する thread 数の row を実際に
含む**ことを要求する。`_cell_identity` は thread を持たない (親実測) ため、現状では 24 thread の
認証が 48 thread だけの成果物に束縛できてしまう。

## R2. thread 軸は cell 別閉表にする — **sol 4 を採用、プラン裁定点 3 を却下**

`CERT_THREADS = (24, 48)` を 4 cell 全部へ開くと、依頼が要らない `tuned@24` と
`cw-as-dyn@24` が認証の受理集合へ入る。定数を 1 本にしたいという実装都合は、正しさ gate の
受理集合を広げる理由にならない。

**裁定: cell 別閉表。** `tuned` = {48}、`cw-as-dyn` = {48}、`cw-as-dyn-c2-p1` = {24, 48}、
`cw-as-dyn-c2-p2` = {24, 48}。

## R3. p2 の seed 閉表 — **legacy 分岐を作らない**

プラン裁定点 2 は「新規 request は seed 必須、既発行 receipt だけ legacy 分岐で再受理」だが、
sol 6 は「legacy を値の組で判定すると、後から作った同形 receipt も再受理され、台帳の
『既発行 receipt』参照が新規 artifact へ置換可能になる」と指摘した。これは real である。

**裁定: p2 の seed 閉表を `{事前登録 12 seed} ∪ {既定 seed 11400714819323198485}` の 13 値とし、
新規 request と published receipt 検証で同一の表を使う。`allow_legacy` 引数を作らない。**

- 既定 seed を残す唯一の理由は、既発行 `c2-p2-a1` receipt を再検証可能に保つことである。
  **既定 seed の実行体は cohort 2 が使う 12 本のどれでもない。** claim と insight にそう書く。
- p2 は seed 必須 (省略は `certification-step-policy-seed-missing`)。
- p1 / p0 / tuned / cw-as-dyn への seed は既存の `step-policy-seed-certification-conflict` のまま。
- 閉表外 seed は新設の `certification-step-policy-seed-mismatch`。

## R4. claim は検証済み軸からしか作らない — **sol 5 を採用**

**裁定: 順序を API で強制する。** raw literal 検査 → parse → singleton → cell 別閉表 membership を
完了して初めて凍結値 (`CertificationAxes` 相当) を構築し、claim builder は**その凍結値だけ**を
引数に取る。document の生値から claim を作れる signature にしない。row / group / published の
各 consumer も、document 値を同じ閉表で検証してから期待 claim を作る。

## R5. anomaly 空の要求 — **sol 2 を採用 (最小形)**

**親実測。** `_validate_target` (1851-1889 行) は `certified_serializable == 1`、
`non_serializable == 0`、`indeterminate == 0`、`verdict == "serializable"`、`certified is True`、
`integrity.clean is True` を要求するが、**`result["anomalies"]` が空であることは要求していない。**
一方 positive control (1781-1792 行) は anomaly が非空 G2 であることを要求する。

**裁定: `_validate_target` に `result.get("anomalies") == []` を 1 つ足す。負例テスト 1 本。**
これはユーザー指示「anomaly が出た cell は即 reject」と、本 wave が 13 回書く claim
「anomaly を 1 件も観測しなかった」の機械的な裏付けそのものであり、仮想リスク向けの gate 追加には
当たらない。**層をまたぐ anomaly_count field の新設はしない** (それが過剰版)。

## R6. 12 本が本当に別 binary であること — **luna 5 を採用 (二段)**

**裁定 (a) job 内:** 1 group の 24 row が `binary_sha256` と `build_cache_key` の singleton で
あることを要求する (既に要求済みなら追加しない)。
**裁定 (b) group 間:** 12 group の `binary_sha256` が相異なることは、**親が段 7 の記録時に
13 本の published receipt を突き合わせて確認し、insight に 12 個の hash を逐語で書く。**
新しい台帳・gate は作らない (ユーザーの scope 外指示に従う)。相異ならなければその範囲を
「認証できた」と書かない。

## R7. 認証する genome と試験が使った実行体の差 — **sol 1: real。本 wave では直さず明記する**

**親実測。** 認証は `genome_for(cell)` を既定引数で呼ぶ (3330 行) ので
`BACKOFF_TRACE=0`・terminal define なしの実行体を build する。cohort 2 の試験走行は
`BACKOFF_TRACE=1` と `BACKOFF_TRACE_TERMINAL_US=5000000` の実行体で行われた。
**したがって本 wave が 312 job を通しても「cohort 2 が実際に走らせた実行体を認証した」とは
書けない。** 認証できるのは「同じ CC 設定・同じ seed で、backoff 診断計装を入れずに build した
実行体」である。

**裁定:**
- 新規に生成する claim 文へ `BACKOFF_TRACE=0`・terminal define なしの build であることを**明記する**
  (主張を狭める方向なので採用する)。
- insight の「覆えていない範囲」に diagnostic genome 軸を書く。
- **診断計装入りの genome を認証対象にする改修は本 wave では行わず、裁定パッケージでユーザーへ返す。**
  受理形・claim・規律 1 の解釈すべてに関わり、ユーザー指示の「本題の認証走行と記録だけ」を超える。

## R8. 再投入の意味論 — **luna 7 を採用 (親側の運用)**

**裁定:** 投入 script の再投入規則を次に固定する。コード (probe / pbs) は変えない。

- 結果 file が**欠落しているだけ**なら、同じ attempt でその slot だけ再投入してよい。
- 結果 file が存在して `rejected` なら、その attempt を保存し、**新しい attempt id で 24 件全部を
  再投入する。** attempt id は `-a1` / `-a2` の連番を持つ。
- 24 件が certified なのに group receipt が無い場合は、原因を記録して裁定へ回す
  (書き込みを伴う finalize-only 経路を新設しない)。
- attempt 番号・qsub job id・失敗理由・判断を job dir の台帳 file へ逐次書く。

## R9. queue 上限 — **luna 8 を採用。投入 script は親が書く**

placeholder のままでは `set -e` 下で最初の group 投入直後に止まる。

**裁定:** 自分の live job (Q/H/R) を数えて閾値以下になるまで待つ実装を入れる。閾値は
**同時滞留 48 job** とし、変異走行・受入走行が同じ queue へ出すなら計数に含める。
投入 script・待ち手は job dir に置き**親が書く** (`DW-C01` の runner/launcher `.sh` 外出しと
前 wave の慣行に合わせる)。repo 内の実装面 (probe.py / .pbs / tests) は Codex `role=author` が書く。

## R10. job 数の数え直し — **luna 9 を採用。brief の数を訂正する**

1 identity x thread 条件あたり 24 job。

| 射程 | group | job |
| --- | ---: | ---: |
| 本 wave の認証走行 (波 1 = p2 x 12 seed x 48t、波 2 = p1 x 24t) | 13 | **312** |
| 本 wave の binding performance 走行 (R1) | — | **13** |
| policy≠0 の完全被覆 (p1 x 2 + p2 x 12 x 2 = 26 group) のうち新規 | 25 | 600 |
| cohort 2 の全実行体 x 全 thread 条件 (p0 x 2 + p1 x 2 + p2 x 24 = 28 group) のうち新規 | 27 | 648 |

既発行 `c2-p2-a1` (既定 seed @48) は 12 本のどれでもないので差し引けない。
brief の「完全被覆 600」は policy≠0 に限った数であり、cohort 2 全体ではない。成果物には
3 段全部を書く。

## R11. trace_dir の consumer と rmtree — **既存裁定により本 wave の scope 外**

sol 10 の後半 (`trace_dir` が group root の子であることを要求せず、published receipt の値を
`shutil.rmtree` へ渡す) は real だが、**D1656「認証 probe の既発行 group receipt 再検証と trace
削除の閉包は直さず、非保証として明記する」が既に裁定している。** 本 wave は受理形を広げるので
**露出は増える**。その事実を insight に書き、修正は裁定パッケージへ残す。sol 10 前半
(命令注入面) は refuted。

## R12. 波 3 と完了判定 — **sol 8 を採用。完了判定を層別表にする**

波 1+2 だけでは、支えられるのは policy 2 の 12 seed における 48 thread 層 (主層 write-heavy と
副次 balanced / read-heavy) と、p1@24 の認証経路だけである。**policy 2 の 24 thread 副次 3 層は
未認証のまま残る。**

**裁定:** 完了判定を boolean にせず層別 coverage 表にする。波 3 (p2 x 12 seed x 24t、288 job) は
波 1+2 が緑で queue に余裕があれば投入し、走らせた範囲だけを認証済みと書く。

## R13. D1852 の上書きは部分に限る — **sol 9 を採用。brief を訂正する**

brief の「D1852 の却下理由は費用だけ」は不正確だった。D1852 は
「認証は正しさの主張なので、射程を広く書くことは絶対規律 2 に対する直接の緩みになる」も理由に
挙げている。**ユーザー直接指示が上書きするのは費用判断 (「312 job は現実的でない」) だけである。**

段 7 で起こす新 D は D1852 の**部分 supersede** とし、次を残す: 射程を広く書かない、新軸は
exact 閉表、不要な cell へ広げない、成果物は層別 coverage で書く。

## R14. 予算と時間 — luna 4 を採用 (refuted だが運用条件つき)

内側予算の和 7440 秒 < outer 8100 秒。**`qsub -l elapstim_req=02:15:00` の override を必ず付ける**
(PBS header 既定は 40 分で、落とすと driver が 8100 秒あると誤認したまま 2400 秒で殺される)。
seed 別 build は per-job 予算を増やさず build 回数を増やすだけ。

## R15. 24 thread の未実測停止条件 — luna 3 を採用 (pilot で開ける)

24 thread で競合が下がると `target-abort-empty` (`abort_count_stdout > 0`) または
`target-edges-empty` (`stats.edges >= 1`) で reject されうる。実測がない。

**裁定: pilot を先に 1 本通す。** 波 2 (p1@24) の最終 group の実 row 1 件を先行投入し、
certified で返ってから残り 23 件を流す。追加 job を使わずに 24 thread 経路の生死を確認できる。
波 1 も同様に 1 group の 1 slot を先行させる。

## R16. luna 2 (24 thread で terminal が出ない) — **refuted**

`COHORT2_BACKOFF_TRACE_TERMINAL_US` は `--backoff-trace` の診断走行だけに効き、certify とは
排他である。group receipt の `terminal_requests` は backoff terminal event ではなく
「24 件の request が終端状態になった」という別概念。認証の受理集合に影響しない。

---

## 実装単位

**1 unit 直列** (プランの結論を採用)。probe.py / .pbs / test file が同じ閉表を共有し、
所有を素集合にできない。Codex `role=author` 1 本。

## 変異事前登録 (DW-M01)

実装後に位置と単一理由性を確認してから本走する。期待 node は実装後に完全集合として確定する。

| # | 変異位置 | 変異内容 | 期待 |
| --- | --- | --- | --- |
| M1 | p2 seed 閉表 | 閉表を「任意の uint64 を受理」に緩める | KILLED (閉表外 seed の負例) |
| M2 | cell 別 thread 閉表 | `tuned` の閉表へ 24 を足す | KILLED (過剰 widening の負例) |
| M3 | claim builder | document の生値から claim を作る順序へ戻す | KILLED (軸検証前 claim 生成の負例) |
| M4 | `_validate_target` | R5 で足す anomaly 空検査を消す | KILLED (anomaly 非空の負例) |
| M5 | `.pbs` certify 分岐 | `--step-policy-seed` の forward を落とす | KILLED (PBS 閉表の負例) |
| M6 | performance 束縛の seed | 実 seed でなく既定 seed と比較する形へ戻す | KILLED (seed 束縛の負例) |
| M7 | group 軸 singleton | 24 row の seed / thread 混在を許す | KILLED (混在 group の負例) |
| M8 | performance 束縛の thread | R1 で足す thread row 実在検査を消す | KILLED (thread 束縛の負例) |

## 段 5 以降の順序

1. 段 5 実装 (Codex author 1 unit) → 段 6 敵対レビュー 2 本 → fix → 変異 matrix → 受入全走。
2. 統合 commit。detached submit-tree をその commit で作る。
3. **13 本の binding performance job** を投入 (trace-disabled)。成果物が
   `_performance_artifact_identity` を通ることを親が login node で offline に確認する。
4. 波 1・波 2 の pilot 各 1 件 (R15) → 通れば残りを group 単位で投入 (R9 の滞留上限つき)。
5. 収集 → 段 7 記録 (層別 coverage 表、12 binary hash の相異確認、覆えていない範囲)。
