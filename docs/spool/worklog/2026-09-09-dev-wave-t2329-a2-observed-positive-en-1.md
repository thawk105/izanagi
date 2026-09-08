---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2329-a2-observed-positive-en
seq: 1
title: [T-2329] A-2 正式 certification の結果節を英語稿にした — 対象は carry が指す reject 稿ではなく、取り直した attempt の observed-positive 稿である (docs のみ、branch worktree-dev-wave-t2329-a2-observed-positive-en、レビュー 2 レンズ・must-fix 0 件)
---

## 本文

- **ユーザー裁定で英語化の対象が carry の字面と入れ替わった。** carry ([T-2329]) は
  「A-2 outer `reject` の結果節 (`results/2026-09-04-a2-certification-reject.md`) を英語化する」と
  書いたままだったが、D1645 が「正しい identity で取り直した attempt が出るまで A-2 の結論を
  論文素材から外す」と定めており、その取り直しが attempt `t2364-20260907b`
  (`results/2026-09-07-a2-certification-observed-positive.md`、outer `observed-positive`) である。
  **英語化したのはこの observed-positive 稿である。** reject 稿 2 本 (2026-09-04 / 2026-09-07) は
  attempt `t2022-20260828c` についての事実であり、論文素材から外れているので英語化していない。
- **相談相手 (別系統モデル) の「対象は 2026-09-04 の reject 稿」という見立ては refuted。**
  carry の字面には忠実だが、carry が D1645 の後に更新されていないことに由来する。
  記録された carry より decision が優先する (F31)。
- **レンズ A (数値の逐語照合) が出した MISMATCH 1 件を refuted にした。** §3 の
  「this machine only」が単数形なのに一次資料は `bnode077` と `bnode085` の 2 host を記録している、
  という指摘。日本語稿の「この機体だけである」を逐語で写したものであり、2 host は
  provenance が `environment: "pegasus"` と記録する**同一環境の計算ノード**である。
  「these two recorded hosts only」へ直すと日本語稿より狭い限定になり、事実命題を足すことになる。
  **英語稿の契約は「事実命題を足さない」なので、原文の粒度を保つ方を採った。**
- **レンズ B (命題の増減) は must-fix 0 件。** 足された命題・落とされた命題・D12 逸脱・
  絶対規律 7 逸脱はいずれも「なし」。nit 1 件 (術語 `canonical admission records` を、
  fig6 の凍結済み英語 caption が使う `canonical condition-admission records` へ揃える) は採用した。
- **`docs/paper-story/README.md` の results 系列表へ 2 行足したのは親の判断である。**
  英語稿の登録に加えて、その出所である 2026-09-07 observed-positive 稿が**そもそも表に
  未登録だった**ため、入口から系列の実体を辿れない状態になっていた。README は「日付なしの入口」で
  あり、ポインタを実体へ追従させるのが本務なので、仮想リスク向けの新設ではなく既存台帳の実体追従
  として扱った。
- **変異事前登録は免除した。** 実装面 (コード・テスト・実行可能 script・機械設定) の差分がゼロで、
  触ったのは `docs/` 配下の Markdown だけである (D95 決定 2)。受入全走は免除していない。
- 工数: codex 子 2 本 (review 2 本、いずれも read-only・rc=0)。同一 worktree からの投入なので
  直列に流した。段 2・3 は軽量版により省略 (設計択一が割れず、正しさ防壁に触れず、受理集合を
  変えないため)。実装子は起動していない (docs-only)。

## 次の一手差分

### 完了

- [T-2329] A-2 正式 certification の結果節の英語稿を
  `docs/paper-story/results/2026-09-09-a2-certification-observed-positive-en.md` へ置き、
  results 系列表へ登録した。数値は一次資料 (`certification.json` / fig6 provenance /
  `raw-manifest.json`) から取り直して照合し、事実命題は足していない。
  remaining: none
  base: f8ed51fd8207adb8f50d2f0b60767abec54493b41c5ee7caf305b1d9d5c8b192

### 新規

- {{T:a2-condition-gate-limitation-review}} **P3・新規**: [T-2228] が A-2 経路の意味関門について
  結論を出したら、observed-positive attempt `t2364-20260907b` の限定 §3 第 4 項
  (条件関門について言えるのは「そう記録された受領証が束縛されている」ところまで) を見直すか判定する。
  判定が変わる場合だけ append-only で新しい日付の results file を足す。
  [T-2329] から切り離した項目であり、英語稿の着地は本項の結果を待たない。
