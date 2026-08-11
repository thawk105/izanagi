---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t817-verifier-epoch
seq: 1
title: [T-817] は実測で前提が覆り実装しない裁定にした — 突き合わせ対象は 0 件でしかも健全に作れず、除外の面は裁定の 8 倍広い (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t817-verifier-epoch)
---

## 本文

裁定 [T-817] (a) 条件付きの実装 wave。裁定文自身が課した条件「実装 wave はまずログ残存率を実測して
から設計する」を実行した結果、**裁定時点で未見だった事実が 4 件出たので、実装せずユーザー再裁定へ
返す** (DW-S04 の「親が不採用にせず新事実付きで戻す」)。段 4 で「実装しない」と裁定し `4→7→8→9`。
CCBench・既存 WAL・凍結成果物はいずれも 1 bit も変えていない。

**新事実 1 — 突き合わせ対象は空。** 既存 WAL 30 本の 459 committed attempt (P2-2 は 24) のうち、
対応する ccbench stdout が残るものは **0 件**。`output/` 全走査 10,291 ファイル中の実 stdout 193 件は
**全件が別 producer** (t141 較正 / silo_ladder_rung1 raw bundle / t139 probe / t155)。
`izanagi-jobs` も 0 件。**git 全史でも `output/campaigns` 配下に stdout 系 path は存在しない。**
機序は `pipeline._run_trace` が `capture_output` の stdout をその場で parse して捨て、trace_dir が
使い捨てであること — 消えたのではなく**保存経路が無い**。

**新事実 2 — 突き合わせは、ログが残っていても健全に作れない (最も重い)。** WAL と stdout を
「同じ run」だと束縛する値がどこにも記録されていない。WAL の `trace_bin` は 16 桁の表示用 prefix で、
実装自身が identity 検査に使うなと明記している。よって同伴 receipt を作っても
**同じ binary の別 run の stdout を組んだ receipt が通る**。[T-756] が blocker として捕らえた
「同じ run の保存済み witness を使っていない」と同型で、作れば規律 2 に反する経路を自作することに
なる。しかも実 corpus では 1 件も発火しない恒真な gate になる。裁定文の「再実行なしで突き合わせ
可能」という前提が成立しない。

**新事実 3 — 除外の面が裁定の想定より広い。** 旧 certified / 旧 fitness を読んで winner や certified
集合を作る生きた経路が 8 つ以上ある。とくに `p2_2_report` と `critic/digest` は **`certified` を
一度も見ず** committed + median だけで winner を選ぶ。`s1_known_axes_freeze` は P2-2 の argmax を選び、
その検証テストは実 repo に対して `build_document()` を走らせる。replay/guided だけに gate を置くと
レポートが旧 winner を出し続け、成果物間で受理集合が食い違う。**敵対レンズ 2 本が独立に同じ
取り残しを発見した** (DW-G03 の独立 2 例が成立)。

**新事実 4 — 識別子が衝突する。** `verifier_policy_sha256` は未実装の設計語ではなく
`reflux_origin_ledger.py` の実装済み field (origin / cell identity の導出に使われる)。段 2 プランは
これを未実装と誤認していた。ユーザーが本 wave に設定した停止条件「識別子の設計が衝突したら止めて
報告」に該当する。

**副産物 — epoch を入れる土台は既にある。** `campaign.lock` v2 の authority は enforcement source
closure 8 path の blob SHA-256 を記録しており、その中に witness gate 本体が住む `pipeline.py` が
含まれる。名前が付いていないだけで、v2 lock の campaign は verifier policy 相当のコード bytes が
既に campaign 単位で pin されている。歴史 campaign の lock は v1 でこれを持たない。

**親自身の誤りを敵対検証が 6 件訂正した。** (P1) 「現行 certified 選択 = replay/guided」は狭すぎた /
(P2) 「不在 = 歴史保存」は identity 全体には成立しない / (P3) 記録の形からの epoch 導出は payload
偽造に弱い / (P4) 提案機構は実 corpus で永久に発火せず synthetic fixture だけが非恒真性を装う /
M5 「凍結 producer は走らせない」は誤りで検証テストが実 repo で再構築する / N1 の除外単位は
verify 記録 571 ではなく committed attempt 459。**両レンズとも NO-GO、refuted 所見はゼロ。**

**受入全走を実施した (DW-S04 の「受入全走は免除せず」に従い、静的な免除論で済ませなかった)。**
1 走目は受入 lease を 7200 秒取得できず `claim-timeout` rc=70 (保持者が 3 回交代する競合)。
待ち上限を 21600 秒へ延ばした 2 走目で取得し、待ち手が local main を取り込んだうえで実走した。
結果は **8832 passed / 20 skipped / 0 failed** (565.77 秒、計算ノード dispatch、request 903942)。
`python3 tools/check_docs.py` と全史 provenance 監査も緑。実装差分はゼロで、変更した tracked file は
`output/insights/2026-08-11_t817-verifier-epoch/**` と本 fragment だけである。

**段 8 の自己改善は予算に阻まれて実装しなかった。** 実測した候補 = codex 子の job-id は prompt 内容
由来なので、親の誤りで入力を欠いた無効走を投入し直すとき、出力ファイル名だけ変えても同じ job-id に
なり artifact 衝突で起動しない (本 wave で実測: 同一 prompt + 別出力名 → 同一 id、prompt 変更 →
別 id)。DW-O01 へ 1 行統合したが `dev-wave/**` の L1.5 footprint が 9855 > 9566 bytes で赤になったため
revert した。予算上限の引き上げは自己改善に含めない規律なので、候補としてここに残す。

裁定パッケージ = `output/insights/2026-08-11_t817-verifier-epoch/verbatim/ruling-package.md` (4 問)。
親の推奨は Q1 = (a) を専用 wave で、ただし除外を「certified を名乗る受理集合」に限定 /
Q2 = 突き合わせ機構は作らない / Q3 = `campaign_verifier_epoch` を v2 lock の既存 authority へ束縛 /
Q4 = S8b・guided WAL・P2-2 の admission 上の位置づけを別 T へ。

## 次の一手差分

### 更新

- [T-817] **P1・ユーザー再裁定待ち (新事実 4 件、実装 wave が実測して返した)**:
  ログ残存率は **0/459** (P2-2 は 0/24) で裁定 (a) の条件節は空集合。さらに WAL と stdout を
  same-run と束縛する値が存在しないため、**突き合わせ機構はログが残っていても健全に作れない**
  (作れば規律 2 に反する経路の自作 + 恒真な gate)。「現行 certified 選択」の実体は replay/guided では
  なく**生きた 8 経路**で、`p2_2_report` と `critic/digest` は `certified` を見ずに winner を選ぶ。
  識別子 `verifier_policy_sha256` は Reflux で実装済みのため衝突する。
  4 問の裁定パッケージ = `output/insights/2026-08-11_t817-verifier-epoch/verbatim/ruling-package.md`。
  実装差分ゼロで CCBench・WAL・凍結成果物は不変
  base: 5aabc00795adb37d165e2968561891a2d0555b3f9327f8a330315358f2c6a2a4

### 新規

- {{T:trace-stdout-same-run-nonce}} **P2・新規 (本 wave の副産物、[T-817] Q2 (c) と対)**:
  今後の run について、WAL と ccbench stdout の双方へ共通の execution nonce を出し、stdout を
  耐久保存する。過去へは遡及できないが、「保存済み witness を同一 run と証明できない」負債の
  再発を止める。[T-817] の Q2 で (c) が採られた場合の実装本体でもある
- {{T:verifier-epoch-consumer-inventory}} **P2・新規 ([T-817] Q1 の前提)**:
  旧 certified / 旧 fitness を読む生きた consumer 8 経路 (`replay` / `guided` / `search_baselines` /
  `p2_2_report` / `critic.digest` / `s1_report` / `s1_known_axes_freeze` / `layer3_report` /
  `s8b_oracle_report` / `s8b_oracle_judge`) について、それぞれが「certified を名乗る受理集合」か
  「歴史解析の生値表示」かを分類する。[T-817] Q1 (a) の scope 確定に必要
