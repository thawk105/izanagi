---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t987-oracle-spec-design
seq: 1
title: 8b oracle spec の事前登録は n を導出できないと確定し、承認 trust root を別 wave と 1 決定へ合流させた — 敵対 2 本が親の n 導出を非同定性で倒した (docs + insights のみ、branch worktree-dev-wave-t987-oracle-spec-design)
---

## 本文

[T-987] の設計 3 点 (canonical path 設置形 / contract test の「承認済み 1 件」形改訂 /
事前登録値の候補導出) を執行した。**docs + insights のみで実装差分ゼロ。**
`output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` へ 1 byte も書かず、
`APPROVED_SPEC_SHA256` は `None` のまま、contract test も `SCHEMA_VERSION` も機構 C1〜C6 も
変更していない。

- 成果物 = `output/insights/2026-08-16_t987-oracle-spec-prereg/`
  (`package.md` = 裁定パッケージ、`contract-test-revision.md`、`preregistration-values.md`、
  `verbatim/` に子出力 3 本と親の独立見解)。
- 設計判断は {{D:oracle-n-not-derivable-from-a12}} と {{D:widening-split-from-narrowing}}。

**先行 wave が同射程を既に納品していた。** 起動時の F35 照合で、[T-499] 後継 wave
(archive worklog entry 511) が producer 設計・D302 判断・承認パッケージ草案を
`output/insights/2026-08-12_t499-spec-producer-design/` へ納品済みであり、その Q1〜Q4 が
未裁定のままだと判明した。段 3 luna はさらに「本 wave の付加価値は過大評価」と指摘し、
親はこれを採用して新規差分を 3 点に限定した。**canonical path の設置形は再発明せず、
現 HEAD との照合結果 (意味は一致、file:line anchor のみ陳腐化) だけを成果物に残した。**

**親の n 導出は段 3 が非同定性で倒した。** 親は brief で「a12 stress-check の J∈[4,13] が
安全域を与え、精度係数 q(J)/√J の平坦化点が n=8」と起草したが、次の順で全部倒れた。

- 親自身が子出力を読む前に第 1 段の訂正を出した — a12 が模擬する判定式は
  `mean - q*sqrt(s/J) > 0` だが、配線されている `judge_oracle` の集約は median of medians +
  float 完全一致 argmax であり、同関数の docstring 自身が「集約規則は未再凍結」と宣言している。
- 段 2 がより強く倒した — **a12 の `J` は t139/a11 study の cluster 数**であって oracle の
  replicate 数ではなく、その選択規則は当該 study の検出力基準
  (`J = min{ j in {4..13} : L_j^cert >= 0.80 }`) である。同一視する一次資料は無い。
- 段 3 sol が代替の較正導出も倒した — 親の `1.253*sigma/sqrt(n)` は iid 単一標本中央値の
  漸近式で、実 estimator は reps=5 の内側 median の外側 median という二段推定、
  certified 条件が使うのは on と off の**差**である。較正は rr50・120 秒 noise run の
  within-run CV で、対象 (rr20/rr80・extime=5) の between-run 分布ではない。
  **同じ仮定の変奏で必要な n が 7 から 14 まで振れることを算術で示した。**
- 親は n=8 の推奨を撤回した。承認パッケージに書いたのは費用点 (12 cell × n × 5 rep × 5 秒、
  n=8 で 40 分) と、n を導出可能にするために要る pilot の仕様だけである。

**親 brief の実測 M4 も誤りだった。** 「U は J とともに単調増加」は cell 単位で成り立たず
(W1/H は J=9→10 で低下、W2/G は J=12→13 で低下)、親が取った per-J 最大値でも J=13 で下がる。
正しくは「全域で α₁ の 15.6% 以下」である。値表の `clocks` と `env_tag` を
「ユーザー承認」に分類したのも誤りで、前者は env 契約が固定し後者は ratified freeze から継承される。

**承認 trust root は独立 2 例が揃ったので 1 決定へ合流させた。** 親は
`verify_external_authority` / `AuthenticatedApproval` 相当の実装が `orchestrator/` 配下に 0 件、
署名 trust root (`gpg.format` / `user.signingkey` / `gpg.ssh.allowedSignersFile`) も全て不在だと
実測した。**同時期に別 wave ([T-1116]) が独立に同型の欠陥を実測しており、本 wave の受入直前に
land した (entry 561)。** `DW-G03` の独立 2 例が成立したため、entry 511 の Q2 を独立の問として
再提示せず、T-1116 問 1 の第 2 consumer として付記した。承認手番を 2 回に割らない。

**段 3 sol が本 wave の contract test 設計そのものも倒した。** 親案と段 2 案の
「`X0 ⊊ X` は拡大だけ」は誤りで、no-follow 全 entry 比較への置換は空 subdirectory・
directory symlink・FIFO を新たに拒否する**縮小**を同時に含む。規律 2 が求めるのは
広げる範囲の明示なので、未裁定の縮小を混ぜると承認範囲が事後に判別できなくなる。
親は設計を純拡大案 (B1) と拡大+縮小案 (B2) に分割した。
段 2 が挙げた正例も倒された — `PIN_GATE_SPEC_RAW` は configuration が 2 件しかなく、
`build_approved_manifest` の freeze product 検査で落ちる。**正例は active freeze・実 run
contract・全 12 cell binding に束縛された production 相当の witness だけを数える**ことにした。

**新規の機構所見は 3 件。** (1) spec 層が単一 block 契約 A3-3 を検査せず、複数 block spec は
承認を通過して manifest 生成で初めて落ちる (承認手番と durable pin を消費してから失敗する)。
(2) `env_contract.py` に pegasus generation 2 が存在するが activation は generation 1 のみで、
spec が pin する `contract_sha256` は activation 世代の進行で失効する。
(3) floor の除外理由 4 件の oracle への流用は意味の継承が未成立で、oracle validator は
形式検査しかしていない。

**本 wave が返す「今決める価値のある問」は 1 件だけである。** `ccbench_pin` の二択は
[T-750] (floor v2 実凍結) が [T-987] を待ち、[T-987] の値が [T-750] の目的で決まるという
デッドロックの結び目になっている。他の値は先行 blocker (active ratified freeze 不在、
`holdout_freeze.json` の `floor`/`budget` が null、trust root 不在) が解けるまで承認しても効かない。

**受入全走は 1 回目が F57 の再発で赤になり、非帰属を実測してから取り直した。** 待ち手の
非帰属 checker は `test_codex_worker_launch.py` の 12 node と
`test_dev_wave_wait.py::test_public_main_real_signal_releases_lease` の計 13 件を
`attributable` と分類したが (rc=70)、本 wave の差分は docs 10 file のみで launcher 実装へ
到達しえない。同 2 file の単独再走 (計算ノード、request `912484`) は 400 passed / 1 failed で
**帰属された 13 件は 1 件も再現せず**、落ちた 1 件は 13 件のいずれでもない別 node だった。
`DW-O18` により帰属しないと裁定し、F57 へ再発として記録した。
**隣で別 wave の codex 子が稼働していた点が過去の再発と違い、同時失敗数が 1 件から 13 件へ
跳ねた初の観測である。** なお受入の起動前 rc=2 が 2 回あり、原因は入れ子 submodule
(`external/ccbench/third_party/shirakami` とその配下) の未初期化だった。テストは 1 件も
走っていない。`--init --recursive` で解消した。

**工数。** 段 2 プラン子 (codex sol/max) 1 本、段 3 敵対 2 本 (sol / luna、いずれも max)。
いずれも read-only sandbox、`check_codex_output.py` rc=0。実装子は起こしていない。
変異 matrix は `DW-S04` により免除 (「実装しない」と裁定済み・実装差分ゼロ)。

## 次の一手差分

### 更新

- [T-987] **P1・設計完了、ユーザー裁定待ち**: 設計 3 点は
  `output/insights/2026-08-16_t987-oracle-spec-prereg/` に納品した。実装差分ゼロ。
  **ユーザーへ返す問は 1 件** — 8b oracle 本走の目的を (a) 現凍結 floor と比較する
  (`ccbench_pin = d706650c…`) か (b) 現 gitlink で floor を再測定して v2 を作る
  (`ccbench_pin = 511c9538…`) か。親推奨 = (b)。これが [T-750] とのデッドロックの結び目である。
  **`n` は導出不能と確定した** — a12 は別 study の規則であり、較正からの導出も非同定
  (同じ仮定の変奏で 7〜14 に振れる)。導出には {{T:oracle-n-derivation-pilot}} が要る。
  承認 trust root は [T-1116] 問 1 の第 2 consumer として合流させ、独立の問にしない。
  contract test 改訂は純拡大 B1 と拡大+縮小 B2 に分割済みで、実装は trust root 決定と対で行う。
  除外理由の floor からの流用は未承認のまま残る。
  base: 719eef9a280ad190c6728d50d2e8c6ecf3df6d27b936767f57c880b05a6562c5

### 新規

- {{T:oracle-spec-single-block-gate}} **P2・新規 ([T-987] 段 3 の real 所見)**:
  spec 層で単一 block 契約 (A3-3) を発火させる。`validate_reviewed_spec` は
  `build_schedule` を呼ぶだけで `_validate_schedule` を通さないため、複数 block の spec は
  承認を通過し manifest 生成で初めて落ちる。schedule validator を共有公開関数化して
  spec 承認前に呼び、2 block の canonical spec が承認前に落ちる負例を追加する。
  下流が fail-closed なので誤選択には至らず、欠陥は承認整合性と可用性に限定される。
  実装面につき Codex author。
- {{T:oracle-n-derivation-pilot}} **P2・新規 ([T-987] で n が導出不能と確定したため)**:
  8b oracle の `n` を統計的に導出可能にする pilot を設計・実施する。
  Pegasus・rr20/rr80・extime=5・対象 configuration で outer trial median の between-run および
  paired 差の分布を取得し、誤選択率または検出力の目標を**事前固定**してから n を導出する。
  現状 between-run の実測は linux-baremetal の rr5/rr50/rr95・extime=3 しか無く、
  per-pair floor の実値も未確定 (`holdout_freeze.json` の `floor` が null) である。
  集約規則そのものが未再凍結である点も先に解く必要がある。
