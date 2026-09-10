# [T-1851] 段 4 裁定 — A2β は実装しない (ユーザー裁定待ち)。main 取り込みだけを積む

2026-09-04。branch `worktree-dev-wave-t1851-unit-a`、main 取り込み後 tip `7771c9e65`。

## 結論

**本 wave は E1 / E2 を実装せず、`4→7→8→9` とする。** 段 2・3 の codex 子は起動していない
(段 1 の brief 前実測で停止条件が成立したため、`DW-S01` の「確認前に子を起動しない」に従った)。

## 所見の裁定

| # | 所見 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 引数の「E3 必須 (v2 profile が 5 箇所で全拒否)」 | **refuted (既済)** | 継承 tip `520b1ddba` は A2α (`69497db66`〜`9df7105f6`) を含み、`_assert_profile()` は schema identity で分岐する exact validator になっている。A2α README と変異台帳 (21/21 一致) が一次資料 |
| 2 | 引数の「E4 (v2 mutation / capability 消費 / claim v3 / v2 resume)」 | **refuted (構造面は既済)** | 同上。A2α が path の世代分岐 11 呼出し、create-only publish、claim v3、capability 消費、v2 resume を積んだ |
| 3 | 引数の「境界 signature は固定済み」で E1 を着手できる | **real だが着手不能** | A1' 裁定 3 節の signature は固定済みだが、A2α の 3 者 (plan / レンズ A / レンズ B) が独立に「その signature では承認済み要求 (生の事実からの再導出) を実装できない」と結論し、補正の 3 択を裁定パッケージ 1 としてユーザーへ返した。`docs/decisions.md` (D1622 まで) に裁定は無い。`DW-STOP` の「ユーザー裁定待ち」に該当 |
| 4 | E2 (理由語彙 4 語) を単独で active 化する | **不採用** | A1' 裁定が「E1 の validator と同じ commit でしか active にしない」と定めており、E1 が止まれば E2 も止まる。literal 候補 4 語は A2α README 14 節に置いてあり、裁定不要で確定してよい |
| 5 | 裁定パッケージ 3 (v2 の分類 claim / 回復行の capability 束縛) を親裁定で決める | **不採用** | 受理面の変更にあたり、A2α 段 4 が「境界の範囲に留め、囲むかは裁定へ返す」と決めた (A2α decisions fragment)。親が覆さない |
| 6 | main 取り込みに Codex author の合成監査を発火させる | **不発火** | main が単位 A の編集面 4 file と consumer 2 file を 1 file も変えておらず、実装面で両親のいずれとも異なる file が無い (`git diff --name-only 36406d376 main` と branch 側の集合の交差 = `docs/dev-wave/operations.md` のみ)。`docs/ai-provenance.md` の実装面契約と `DW-O17` の発火条件を満たさない。合成の意味的健全性は焦点走 (1,720 passed / 5 skipped / rc=0、計算ノード) と受入全走で実測する |

## 変異事前登録 (DW-M01)

実装面の差分 0 (merge 以外) のため `DW-S04` により変異 matrix を免除する。受入全走は免除せず実走する。

## ユーザーへ返す裁定パッケージ

A2α README 13 節の 3 件を、そのままの文面で再提示する (本 wave で新しい選択肢は増えていない)。

1. **E1 の境界 signature を補正してよいか。** (推奨) 起動層が生の事実を snapshot して発行する
   evidence-bound handle を第 9 の境界として追加し、resume 可能な durable evidence digest も持たせる /
   (代案 a) 2 つの sealed API へ `probe_outcome` 等の keyword-only 引数を直接足す /
   (代案 b) 境界を変えず E1 を単位 C と同じ変更単位へ送る (D1530 の形)。
   併せて `record_sealed_classified_failure_terminal()` は呼び手 0 件であり、単位 C で呼び手を
   名指しできるか API を落とすかを land 前条件にする。
2. **E1 の分類 policy の権威をどこに置くか** (`expected_use_perf` の束縛先、`probe_outcome` の
   計測前 probe の扱い、`repetition_evidence` を到達可能にする起動層 sink の変更単位)。
3. **v2 の分類 claim / 回復 row を marker capability で囲むか。**

裁定 1 で (代案 b) を選ぶ場合、単位 A の残りは無く、次段は B2 / D1 / C / D2 になる。
裁定 1 で (推奨) か (代案 a) を選ぶ場合、A2β = E1 + E2 (+ 第 9 境界) を次 wave で積む。

## 補足: 引数の前提が古かった経路

A1' の job dir handoff (`/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/handoff.md`) は
A1' 終了時の「次の一手 = A2' (E1〜E4)」のまま残り、A2α wave はこれを更新していない
(A2α の状態は branch の README と worklog fragment にだけある)。次 wave の引数はこの handoff を
根拠に起草されたため、既済の段を必須と書き、裁定待ちを着手可能と書いた。
`DW-S01` の brief 前実測が検出し、子の起動前に止めた。
