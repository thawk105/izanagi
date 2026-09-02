---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: worktree-dev-wave-t2166-floor-pair-driver
seq: 1
title: [T-2166] B-4 床値の対照対 driver を作った — 緑だった 110 件が守っていなかった穴を敵対レビューと変異が暴いた (コード + テスト + insight、branch worktree-dev-wave-t2166-floor-pair-driver、変異 22/22 KILLED)
---

## 本文

- 事前登録 §11.2 の測定計画を起動できる経路が現行の sanctioned CLI に無く、床値欄が埋まらないため
  測定を開始できなかった。凍結した測定手順 spec を読み、対照対と共通参照点を束縛し、
  `D = |gain_1 - gain_2|` とその上限を raw から再計算できる create-only 成果物へ出す driver を
  新設した (D1453)。**bench は 1 度も実走していない。性能値を新規取得していない。**
- **現物の校正成果物から「校正済み `PerfConfig`」を機械導出できないことが分かった。** 記録済み
  calibration は `records` (saturation 側)・`threads`・`clocks_per_us`・`workload` を持つが、
  `reps` と `extime` を持たず、`workload` も 3 key だけで `pipeline.PerfConfig` が厳密に要求する
  4 key 目 `ycsb_max_ope` を欠く。導出で埋めると `p2_2` の `REPS=5` / `EXTIME=3` や
  `ycsb_max_ope=10` が無裁定の既定値として密輸される形になり、これは §11.1 が名指しで禁じている。
  凍結 spec が 5 項目すべてを明示し、artifact から導ける項目だけを exact equality で照合する設計にした。
- **敵対レビュー 2 本が独立に、緑だった焦点走 110 件が守っていなかった穴を指した。** 最も重いのは
  測定実体の身元が callable の `__module__` / `__qualname__` の自己申告だった点で、両属性は
  書き換えられるため偽関数に本番と同じ名前を付ければ通る。対の両側へ同じ値を返せば `D = 0`、
  すなわち床値 0 が生成でき、tie 判定が消えて受理集合が最大に広がる。差し込み口自体を
  権威経路から除いて閉じた。ほかに、schema が正規値として許す `quality.status="rejected"` の
  校正を受理していたこと、校正の `saturation.records` と実測 `records` を比べていなかったこと、
  競合検知の argv が spec の自由 field で常に rc=1 を返す command により競合検査を恒久的に
  無効化できたこと、site 判定が証拠必須でなかったこと、finalizer が実行順と terminal を
  再検証していなかったことを real と裁定して直した。
- **証明していない 5 件は、新しい受領証・台帳・attestation を建てず「保証と書かない」方向で閉じた。**
  spec の凍結時期、測定認可、成果物の削除・改名の防止、標本の統計的独立性、strip 済み binary の
  trace 混入。いずれも §11.1 が凍結項目の決定主体をユーザーに置いており、AI が機構を起草すると
  役割分離を壊す。module docstring と summary 成果物の両方に明記した。
- **変異は probe → 期待確定 → 本走の 3 段で回した。** 期待ノードを推測で書くと KILLED と出ても
  どの機構が効いたか一意に言えないためである。probe (24 件、全件 SURVIVED 期待) で 3 件が生存した。
  うち 1 件は実欠陥で、参照成果物の宣言 sha256 の一致検査を取り除いても 139 件のテストが 1 件も
  落ちなかった。残る 2 件 (build receipt の `trace=false` と binary SHA) は冗長 gate で、
  driver が呼ぶ前に sanctioned な `s8b_binary_admission` validator が同じ入力を先に拒否する。
  実効 gate は validator 側であり、単独変異の証拠から外した (DW-M03)。
  fix 子は偽装テストを作らず file:line の根拠付きで「到達不能」と報告し、親が現物で裏取りした。
  本走は 22 件登録、**22/22 KILLED、期待ノード完全一致、MISMATCH と SURVIVED ともに 0**。
- **変異 harness の wrapper は本走・probe とも走行後に rc=125 を返した** (共有木の観測 bytes が
  変化した)。変異自体は固定 commit の使い捨て worktree で 24/24・22/22 完走しており台帳は完全である。
  親は自分の wave worktree が走行前後で変更ゼロであることを独立に確認した。走行中に他の稼働 wave が
  共有木を動かしたためと見ており、wrapper が主張できなかったのは「全窓にわたって共有木が不変だった」
  ことだけである。
- **main 取り込み直後に在庫検査が 1 件赤になった。** 新設した production file が、perf に触れる
  production file の literal な在庫に載っていなかった。同じ型の赤を別 wave が同日 main の commit
  `7648070b1` で閉じており、その方針 (在庫へ追加し、走査述語と判定は変えず、自動生成にもしない) に
  揃えた。子が他の在庫も洗い出し、process 起動 site の在庫にも 3 件 (read-only な Git 問い合わせ 2 つと
  固定 pgrep probe) の登録が必要だと判明した。受入全走の前に閉じた。
- 段 2 プラン、段 3 敵対相談 2 本、段 5 実装、段 6 レビュー 2 本と fix 4 巡、変異 2 台帳の逐語は
  `output/insights/2026-09-02_t2166-floor-pair-driver/`。
- fix 子の 1 回目は upstream の "Selected model is at capacity" で成果物ゼロのまま 22 秒で終了した。
  prompt の内容問題ではないことを receipt と events で確認し、`--job-id` を変えて再投入した。

## 次の一手差分

### 完了

- [T-2166] 対照対 driver / adapter を新設した。凍結 spec loader、決定的な測定計画、
  前後 probe、create-only 成果物、`D` と上限の純関数までを実装し、変異 22/22 KILLED で
  機構の実効性を裏取りした。実走は床値発効の凍結項目確定と測定認可の後に限る (D1453)。
  remaining: none
  base: 8cdd78953a2f5a8da2810848e76b3768ef4846d8c7d89c6150e3f67c40ab5e67

### 新規

- {{T:floor-spec-freeze-evidence}} **P2・ユーザー裁定待ち**: 測定手順 spec の凍結を誰がどう
  証明するかを決める。現案は spec の path と期待 hash を同じ呼び手が渡すため、HEAD tracked で
  あること以上の凍結証拠が無い。§11.1 の freeze commit・承認者・凍結項目 12 行の裁定と一体で決める。
- {{T:floor-measurement-authorization}} **P2・ユーザー裁定待ち**: 測定認可を機械で要求するかを
  決める。`--execute-window` は認可の受領証を要求しない。要求する設計にするなら、受領証の発行主体・
  束縛する項目・一回限りの消費を凍結が定める。
- {{T:floor-artifact-immutability}} **P2・ユーザー裁定待ち**: 成果物の不変性をどこまで求めるかを
  決める。現案は「同じ path が残る間の再作成」だけを防ぐ。削除・改名・別 path での選別再走を
  防ぐには、成果物とは別の権威に attempt を予約する必要がある。
- {{T:floor-sample-independence}} **P2・ユーザー裁定待ち**: 標本の独立性の規則を決める。
  同一 window 内の連続標本を独立な機会として数えるか、1 window 1 標本に制限するか、最小間隔を置くか。
  §11.2 はユーザー決定事項としている。driver は window / campaign を記録するだけで判定しない。
- {{T:calibrated-perfconfig-producer}} **P3・ユーザー裁定待ち**: 完全な `PerfConfig` 成果物の
  producer を作るかを決める。現物の calibration は `extime` / `reps` / `ycsb_max_ope` を持たない。
  本 driver は spec の明示で埋めるが、校正の権威を artifact 側へ移すなら別作業になる。
- {{T:floor-upper-statistic-id}} **P2・ユーザー裁定待ち**: 上限統計の exact な関数を決める。
  本 wave は §5.1 の規範 (保守側 = 最大) の機械化 2 件 (`sample_max/v1` と
  `max_over_closed_strata/v1`) だけを閉じた登録簿に置いた。分位・信頼水準・許容限界の規則を
  採るなら、ID と入力単位を凍結が定める。
