---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2205-a5-measure
seq: 1
title: [T-2211] A-5 (D1100) 別 boot 再取得を 4 job 投入し、条件関門で止まることを実測した — 投入元は原因ではなく、次の層はユーザー裁定待ちだった (docs + insight、branch worktree-dev-wave-t2205-a5-measure、実装面の差分 0)
---

## 本文

- **依頼は実測だった。4 job を投入し、測定値は 1 つも取れなかった。** 4 job とも build でも
  測定でもなく、その手前の条件関門で `preprocess-failed` 7 件になり、経過 98〜101 秒で落ちた。
  詳細と一次資料は `output/insights/2026-09-02_t2211-a5-second-boot-measurement-attempt/README.md`。
- **[T-2212] の裁定待ちを尊重し、充足の判定はしていない。** 旧 `linux-baremetal` 値についても
  反証・無効化・再現失敗のいずれも主張していない。前 wave が凍結した受理規則をそのまま使った。
- **段 1 brief の (P1) が誤っており、対照で潰した。** 「job body の repo root 判定は directory
  だけなので隔離 worktree から投入できる」と書いたが、隔離 worktree では submodule 側で
  `git worktree list` が checkout ではなく gitdir を返す癖がある。原因である可能性を排除するため
  主 checkout から 1 回だけ対照を投入し、**同一の赤**を得た。投入元は原因ではない。
  login node では job と同じ二段の入れ子 worktree 生成が正常に成功することも実測した。
- **原因の帰属は、本 wave の実測中に main へ着地した `dev-wave-a2-condition-gate-patched-root` の
  解剖と同型だった。** 同 wave は同じ関門を 3 層に分けており、本 wave の赤はその第 2 層
  (owner TU の include chain が build 時生成の設定 header を要求するのに、configure しかしない
  関門の build tree にそれが無い) と同型である。**A-2 側の修正は A-2 の driver に入っており、
  A-5 が使う driver 経路には入っていない。**
- **第 2 層だけを直しても緑にならない見込みが高い。** その先の第 3 層
  (`preprocess-root-dependent-builtin`) は inert (stock) 比較で構造的に必ず赤になり、
  A-2 の裁定パッケージがユーザー裁定へ返している。**A-5 の分母はまさにその inert 比較である。**
  ただしこれは A-2 側の実測と構造の議論からの予測であって、A-5 の driver では未実測。
- **実装へ手を入れなかった。** 関門は正しさの防壁であり、通すためだけの修正が偽の緑を作りうる
  ことは A-2 の insight が教訓として明記している (絶対規律 2)。加えて第 3 層は受理集合に触るため
  裁定待ちであり、その手前で第 2 層だけを直すと決着後にやり直す差分になる。
- **job 単位の CPU 時間は取得できなかった。** この機体の `qstat` は完了 job の履歴を返さず
  (`-H` は無効 option)、job body も CPU 時間を記録しない。稼働中の CPU 列は依存 build が
  `-j 48` で走る最中に 1 秒未満のままで、子プロセスを集計していない。測定本体が 1 度も
  走っていないため、並列度を評価できる比はまだ存在しない。
- **投入器と job body 自体には欠陥が見つからなかった。** 4 job とも queue 待ちなしで別ノードへ
  落ち (4 ノード・4 boot)、契約検査を通り、失敗を receipt へ構造化して残し、scratch worktree の
  残骸も残さなかった。
- **子は起動していない。** 実装面の差分が 0 で、設計択一が割れず、受理集合を変えないため
  軽量版で通した。

## 次の一手差分

### 更新

- [T-2211] **P1・裁定待ちで滞留**: A-5 (D1100) の実測。投入器と job body は動くことを確認済みで、
  残る障害は driver 経路の条件関門である。順序は (1) A-2 裁定パッケージ「裁定してほしいこと 1」
  (inert 比較を関門でどう扱うか) の決着、(2) 決着に沿って A-5 の driver 経路へ関門文脈の
  build 時生成物を供給する修正を Codex 実装子で入れる、(3) 同じ投入器をもう一度 1 回走らせる。
  投入は repo 外の既存 directory を `--output-parent` に渡し、2 job が終わるまで branch へ
  commit しない。
  base: 2323f8187f2144cd529a6f9b0fb8a275bc623f98c0319ce5f3b0aac7e8969ba8
