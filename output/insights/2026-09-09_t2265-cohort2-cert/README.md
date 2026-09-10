# [T-2265] cohort 2 の seed 別実行体と 24 スレッド条件の直列性認証 — 11 group を認証し、ユーザー裁定で打ち切った

wave: `worktree-dev-wave-t2265-cohort2-cert`。実装 commit `1afc042072a082e02dd7a32685898bdbdafc736e`。
認証走行はこの commit から作った detached submit-tree で行った。

---

## 0. この wave が主張すること・しないこと

**主張する。** 事前登録した 12 seed のうち **10 seed の policy 2 実行体 (48 threads)** と、
**policy 1 実行体の 24 threads 条件** について、それぞれ 24 件の trace-enabled 走行が
verifier で certified serializable となり、anomaly を 1 件も観測しなかった。

**主張しない。**

- **「cohort 2 を認証した」とは書かない。** §1 が示すとおり、認証した実行体は cohort 2 が
  実際に走らせた実行体ではない。
- 残る 2 seed (slot 10 / 11)、policy 2 の 24 threads 条件、policy 0 の全条件は認証していない。
- 固定条件外への一般化、trace-disabled の性能値そのものの認証は行わない。

---

## 1. 最重要 — 認証した実行体は、試験データを出した実行体ではない

段 3 の敵対相談 (正しさ境界レンズ) が指摘し、親が現物で確認した。

認証経路は `genome_for(cell)` を既定引数で呼ぶ
(`tools/pegasus/probes/t2187_adaptive_const_probe.py`、`_certify_main` の build 部)。
したがって build される実行体は **`BACKOFF_TRACE=0` かつ `BACKOFF_TRACE_TERMINAL_US` の
terminal define なし**である。一方 cohort 2 の反実仮想試験は、割当列と terminal event を
記録するために **`BACKOFF_TRACE=1` + terminal define あり**の実行体で走っている
(`docs/backoff-counterfactual-cohort2-preregistration.md` §3)。

**この差は本 wave が作ったものではない。** 既存の認証経路がもともと持っていた性質であり、
前 wave の記録もこの軸に触れていなかった。本 wave はこれを名前を付けて記録し、
**新規に生成する claim 文へ build 条件を明記する形に変えた**。

**帰結:** 312 job を全部通していても「cohort 2 が走らせた実行体を認証した」とは書けなかった。
書けるのは「同じ cell 設定・同じ compile seed で、backoff 診断計装を入れずに build した
実行体を認証した」までである。

**計装入り genome を認証対象にする改修は本 wave では行っていない。** 受理形・claim・
絶対規律 1 の解釈すべてに関わるため、裁定パッケージ (§7) へ送る。

---

## 2. 実測した認証結果

1 group = 3 workload (rr5 / rr50 / rr95) x 独立反復 8 = **24 request**。
group receipt は 24 件すべてが terminal になったときだけ発行される。

| group (attempt) | threads | compile seed | certified / expected | anomaly | group receipt sha256 |
| --- | ---: | ---: | :---: | ---: | --- |
| `c2cert-p1-t24-a1` | 24 | 11400714819323198485 | 24 / 24 | 0 | `d3d5a838cdb0d2211723c08b994f9484c2d4a963af5d6c12b81f11fd1d1bec2d` |
| `c2cert-p2-seed00-t48-a1` | 48 | 14481721328008317845 | 24 / 24 | 0 | `2263f4ccd7aead09b88a41208c3b54a8f045187511d019db4f57cbe66c90a839` |
| `c2cert-p2-seed01-t48-a1` | 48 | 7453732891837486670 | 24 / 24 | 0 | `9234d8d4beaa1f88ecd030e6b0f09261b9b809cf0278d2d67402d1ad0798aba0` |
| `c2cert-p2-seed02-t48-a1` | 48 | 766609016836229506 | 24 / 24 | 0 | `c430fdfd24520e8fcd11a9bd9c9d06118ed4cedd488938c7589c571c190b143e` |
| `c2cert-p2-seed03-t48-a1` | 48 | 14479507243158715447 | 24 / 24 | 0 | `3c5b556cd65ab95dfd1d10096933cdb183b595fbaf7152ff8bd81e0256c72381` |
| `c2cert-p2-seed04-t48-a1` | 48 | 3736279228254271919 | 24 / 24 | 0 | `aaae992a03cd893c3f35e5e78f0f769531d3263ae28f16b72d059725441f9eae` |
| `c2cert-p2-seed05-t48-a1` | 48 | 6574519577559702715 | 24 / 24 | 0 | `99910e7a4c7c39f3281135bbd498a2e00397f0bee26293d622ff41761a98d248` |
| `c2cert-p2-seed06-t48-a1` | 48 | 15525319108568766040 | 24 / 24 | 0 | `6d62930ad90c26cef24b213d8ebff3926d1126a34850852d4d3828f7474ac7bb` |
| `c2cert-p2-seed07-t48-a1` | 48 | 13039315294558381935 | 24 / 24 | 0 | `5ea1e6f73f9366bea88859c2d1d2b94b851bf2c563936f0f8eb8ff1451efbe37` |
| `c2cert-p2-seed08-t48-a1` | 48 | 16889140200793892447 | 24 / 24 | 0 | `ba07bf28bdc9a6507528bc3054e3b51ceb36beb6ece977c48ea484e2a82788c1` |
| `c2cert-p2-seed09-t48-a1` | 48 | 15536816158447092057 | 24 / 24 | 0 | `a89335cb4fff711c732e3a4bcb5d970f4a37eac27262c5023f22fe8b68a46014` |

**打ち切った group** (ユーザー裁定による停止時点の状態):

- `c2cert-p2-seed10-t48-a1` — 結果 22 / 24、受領証なし
- `c2cert-p2-seed11-t48-a1` — 結果 9 / 24、受領証なし

受領証は `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/certify/<attempt>/group-receipt.json`。
集計は `receipt-summary.json`。

**実行体の相異。** 11 group の `genome` はすべて異なり、それぞれ自分の
`BACKOFF_STEP_POLICY_SEED` を含む。group 内では `genome` は単一である。
**すなわち 10 本の seed 別 policy 2 実行体は実際に別物として build されている。**

---

## 3. 走行前に見つけて潰した実機 blocker

段 3 の実行可能性レンズが指摘し、親が現物で確認した。

認証は、束縛する performance 成果物の `repo_head` が**その認証走行の HEAD と一致すること**を
要求する (`_certify_main` が現在の HEAD を `expected_repo_head` として渡し、
`_performance_artifact_identity` が exact 一致を求める)。前 wave の performance 成果物は
別 commit のものだった。**そのまま投入していれば 312 job 全件が build 前に落ち、
成果物は 1 件も出なかった。**

既存の一致検査は 1 文字も緩めていない。代わりに本 wave の commit で
**trace-disabled の束縛用 performance 成果物を 12 本作り直した**
(`izanagi-job-evidence/dynamic-backoff/perf/c2cert-1afc042072a0-seed{00..11}/`)。
絶対規律 1 の分離は保たれている — 認証は trace-enabled build、束縛用 performance は
trace-disabled build の別 run であり、本 wave はこの 12 本の性能値を主張に一切使っていない。

投入前に、成果物が `_performance_artifact_identity` を通ることを login node で offline に
確認した (p1 / p2 x 24 / 48 threads の 4 通り、failures=0)。

---

## 4. 実装したこと

`--mode certify` の受理形へ 2 軸を足した。受理形は exact な閉表のまま広げている。

- **thread 軸は cell 別閉表。** `tuned` と `cw-as-dyn` は 48 のまま、cohort 2 の p1 / p2 だけが
  24 と 48 を取る。段 2 プランは 4 cell すべてへ 24 を開く案だったが、依頼が要らない cell まで
  受理集合を広げる理由がないので却下した。
- **p2 の seed は事前登録 12 値 + 既定 seed の 13 値だけ受理する。** p2 では seed 必須。
  p1 / p0 / tuned / cw-as-dyn への seed は従来どおり拒否する。
  値の形で legacy を判定する分岐は置かず、新規 request と published receipt 検証で同じ表を使う。
- **claim は検証済み軸からの exact な閉写像。** 既存 4 軸 (tuned@48 / cw-as-dyn@48 /
  c2-p1@48 既定 seed / c2-p2@48 既定 seed) は現行 literal を 1 文字も変えずに返す。
  新しい軸だけが実 thread 数・実 seed と §1 の build 条件を書いた文を返す。
- **performance 束縛を実 seed へ通し**、認証する thread 数の row が実在することも要求する。
- **認証結果に anomaly が残っていることを明示的に拒否する。**
  これまで `_validate_target` は verdict と certified は見ていたが `anomalies` が空であることを
  要求していなかった。
- 24 件揃った後の group 検証失敗を握り潰さず、`group-failure-<attempt>.json` へ理由を残す。
- `--threads` / `--step-policy-seed` の option 重複を拒否し、seed の raw literal が正規十進で
  あることと、thread の raw literal 検査が parse より先に効くことを要求する。

焦点走 + consumer 走: **805 passed / 1 skipped (rc=0)**。

---

## 5. 撤回した裁定 — group 内の binary 同一性検査

段 4 では「1 group の 24 row が `binary_sha256` と `build_cache_key` の singleton であること」を
要求すると裁定した (R6a)。段 6 のレビュー 2 本が独立に、`build_cache_key` は job ごとの
build context / admission identity から算出されるので **24 job で必ず異なる**と指摘した。

`docs/dev-wave/operations.md` の `DW-O13` は「field の実在では足りない。その field が実環境で
取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」と定めている。
**値域を実測していない述語だったので撤回した。**

**その後の実測が撤回の正しさを裏づけた。** 発行された group receipt では、
1 group 24 row の `binary_sha256` が**すべて異なる** (24 distinct)。`build_cache_key` も 24 distinct。
**撤回していなければ、11 group すべてが受領証を発行できなかった。**

**この事実自体が知見である。** CCBench の build は job を跨いで byte 再現しない。
したがって「同じ実行体である」ことを `binary_sha256` で語ることはできない。
group が束縛しているのは `genome` と source identity であって、単一の binary ではない。
§2 の実行体相異の確認も `genome` で行っている。

---

## 6. 変異検査

事前登録は段 4 (`verbatim/stage4-ruling.md`)。本走は実装 fix 後の最終 commit で anchor と
期待 node を再検証してから行った。**9 KILLED / 1 SURVIVED (登録済み) / MISMATCH 0 /
期待 node 完全一致。**

| id | 変異 | 結果 |
| --- | --- | --- |
| `m1-axes-layer-only-masked` | `CertificationAxes.__post_init__` の p2 seed membership を消す | **SURVIVED (登録)** |
| `m1a-contract-seed-table-open` | `_certification_contract` の p2 seed membership を消す | KILLED |
| `m1b-both-layer-seed-table-open` | 上記 2 層を同時に消す | KILLED |
| `m2-tuned-thread-widened` | `tuned` の thread 閉表へ 24 を足す | KILLED (4 node) |
| `m3-claim-accepts-unvalidated-axes` | claim builder の型検査を消す | KILLED |
| `m4-target-anomalies-not-required-empty` | anomaly 空の要求を消す | KILLED |
| `m5-pbs-certify-drops-seed-forward` | PBS の certify 側 seed forward を落とす | KILLED (2 node) |
| `m6-perf-binding-uses-default-seed` | performance 束縛を既定 seed 比較へ戻す | KILLED |
| `m7-group-axes-allow-mixed` | group の軸 singleton を緩める | KILLED |
| `m8-perf-binding-drops-thread-row` | performance 束縛の thread row 実在検査を消す | KILLED |

### 6.1 probe が暴いたこと (erratum。初回結果を消さずに残す)

初回 probe (`mutation-probe-spec.json` / `-report.json`) で **m1 が SURVIVED した**。
原因は等価変異ではなく**二層 mask** である。p2 seed の membership 検査が
`CertificationAxes.__post_init__` と `_certification_contract` の両方にあり、
片方だけを壊してももう片方が同じ入力を拒否する。

`DW-M02` に従って実効 gate へ再照準し、probe2 (`mutation-probe2-*`) で m1a (契約層のみ) と
m1b (両層同時) の観測 node を採り、本走で両方 KILLED を確認した。
**初回の m1 は本走の spec にも SURVIVED として残してある** — 消すと「片側だけ壊しても
気づけない」という事実が台帳から消えるためである。

---

## 7. scope 外と裁定したもの (ユーザーへの裁定パッケージ)

1. **計装入り genome の認証** (§1)。認証する実行体を試験の実行体に一致させる改修。
   受理形・claim・絶対規律 1 の解釈に関わるため本 wave では行っていない。
   **これを閉じない限り、認証の射程は常に「試験の隣」である。**
2. **既発行 group receipt の再受理が exact でない** — D1656 が「直さず非保証として明記する」と
   既に裁定している。本 wave は受理形を 2 cell から広げたので**露出は増えた**。
3. **`trace_dir` の consumer** — row の `trace_directory` が group root の子であることを要求せず、
   published receipt の値をそのまま `shutil.rmtree` へ渡す。同じく D1656 の射程。
4. **未認証のまま残る範囲** — policy 2 の seed slot 10 / 11 (48 threads)、
   policy 2 の 24 threads 全 12 seed、policy 0 の全条件。

---

## 8. 打ち切りの経緯 (ユーザー裁定)

312 job のうち **285 件が certified、11 group が受領証発行**まで進んだ時点で、ユーザーが
費用対効果を理由に停止を指示した。親は次を根拠として同意し、残作業を投入しなかった。

- §1 のとおり、312 job を完走しても「cohort 2 を認証した」とは書けない。
- backoff は Silo の validation 経路に触れない。13 通りの backoff 設定を認証しても、
  第三者が受け取る保証は 1 通り認証した場合とほとんど変わらない。
  認証は「同じプロトコルを違うスケジュールで再サンプリングする」形になっている。
- 対象の効果量 (推奨方向の実用優越 +4.900%) に対して 312 job は釣り合わない (絶対規律 4)。

**実行した停止手順:** 待ち手を停止し、queue に残っていた自分の認証 job **19 件を qdel** した
(`qdel.log`)。停止後の実測でキュー内の自分の job は 0 件。波 3 (policy 2 x 12 seed x 24 threads、
288 job) は 1 件も投入していない。

**次に正しさへ資源を使うなら**、サンプルを増やす方向ではなく、
**backoff の patch が validation 経路に触れていないことをコードで示す方向**を勧める。
読者にとっての保証はそちらの方が強く、計算 job を要しない。

---

## 9. 段 3 と段 6 の敵対検証が見つけたもの

### 9.1 段 3 (プラン起草の後)

- **実行可能性レンズが §3 の実機 blocker を見つけた。** 投入前に見つけたので job を 1 件も
  無駄にしていない。
- **正しさ境界レンズが §1 の射程の穴を見つけた。** 親 brief の完了判定を狭めた。
- 同レンズが、`_validate_target` が anomaly 空を要求していないこと (§4)、
  段 2 の thread 軸 4 cell 開放が過剰であること (§4)、
  値の形で legacy を判定する分岐が抜け道になること (§4) を指摘した。すべて採用した。
- 実行可能性レンズが job 数の数え直しを行い、親 brief の数を訂正した (§10)。

### 9.2 段 6 (実装後)

- **レビュー 2 本が独立に §5 の到達不能述語を指摘した。** 親の実測がその正しさを裏づけた。
- **レビュー B が親の投入 script の欠陥 4 件を見つけた。** 特に「performance 走行の grid に
  `none` と stock control が必須」を見落としており、そのままなら 12 job 全部が落ちていた。
  他に古い成果物の再利用、pilot の引数契約、再投入時の結果分類。すべて親が直した。
- レビュー A が claim の生成が `tuned` / `cw-as-dyn` の literal まで変えていることを指摘した。
  段 4 の不変条件「既存 2 cell の束縛を 1 文字も変えない」への違反であり、fix で閉じた。

---

## 10. 親の記録の訂正

- 段 1 brief の「完全被覆 600 job」は policy≠0 に限った数であり、cohort 2 全体ではない。
  正しくは、1 identity x thread 条件あたり 24 job として
  policy≠0 の完全被覆は新規 600 job、cohort 2 の全実行体 x 全 thread 条件は新規 648 job
  (総証拠 672 job) である。
- 段 1 brief の「D1852 の却下理由は費用だけ」は不正確だった。D1852 は
  「認証の射程を広く書くことは絶対規律 2 に対する直接の緩み」も理由に挙げている。
  ユーザー直接指示が上書きしたのは費用判断だけである。
- 段 4 裁定 R1 は binding performance job を 13 本としたが、実際は p1 と p2 の row を同じ
  job に含められるため **12 本**で足りた。
- 段 4 裁定 R6(a) は §5 のとおり撤回した。
- 段 4 裁定 R15 の「24 threads で abort 0 / edges 0 になり reject されうる」懸念は、
  pilot の実測 (`c2cert-p1-t24-a1` write-heavy slot0、txns 2,229,457、edges 21,984,539) で
  否定された。

---

## 11. 逐語

段 1 brief、段 2 プラン、段 3 相談 2 本、段 4 裁定、段 5 実装報告、段 6 レビュー 2 本と
fix 2 本は `verbatim/`。変異の spec と report は本 dir 直下。
