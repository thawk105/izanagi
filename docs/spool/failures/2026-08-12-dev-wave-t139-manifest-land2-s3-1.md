---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t139-manifest-land2-s3
seq: 1
---

## 新規

### {{F:pending-rulings-invisible-on-unlanded-branch}}. 裁定待ちの実体が未 land branch にしか無く、収集の母集合から丸ごと落ちた [手順漏れ] [ドリフト]

- 事象: [T-139] land 2 session 2 が 2026-08-11 に裁定 5 問 (Q1〜Q5) を返したが、
  2026-08-12 の /rulings 12 束に T-139 は含まれず、canonical worklog (451) の `[T-139]` は
  (450) からの carry stub のままだった。session 3 は「未実装層を進める」指示で起動したが、
  命名された 5 層すべてが未裁定 Q1/Q2 の下流であり、着手不能と判定して停止した。
- 根本原因: 裁定パッケージ (`output/insights/2026-08-11_t139-manifest-land2-s2/package.md`) と
  それを指す worklog fragment の `更新` が、**未 land branch 上にしか存在しない**
  (`git cat-file -e main:<path>` が fatal)。**wave 側の記録は正しく書かれていた** —
  session 1 の fragment は `[T-139]` を `更新` して「ユーザー裁定 Q1〜Q4 待ち」と明記している。
  落ちたのは収集側の**母集合**であって wave の記録ではない。canonical worklog + `docs/archive/`
  だけを走査する限り、branch 上の fragment には grep も carry 鎖解決 script も到達できず、
  canonical の `[T-139]` は carry stub のままである。
  S6 (a) の「最終的に 1 回だけ land する」がこの不可視を構造化する —
  裁定が来るまで land できず、land できないため裁定待ちが見えない。
  F213 は収集**語**の穴だが、本件は収集**母集合**の穴で型が違う。
- 恒久対応: memory `pending-rulings-need-inbox-copy-and-ledger-update` (裁定パッケージを返して
  land しない wave は、fragment の `更新` だけで足りたと見なさず、`dev-wave-jobs/rulings-inbox/`
  へ repo 外の控えを置く)。本 session は控え
  `2026-08-12-t139-land2-s2-five-rulings.md` を作成した。共有 command への明文化は
  `docs/dev-wave/**` の byte 予算に当たるため、Q6 としてユーザー裁定へ返した。
- 再発検知: land しないと判明した session は、段 9 の前に inbox に当該 wave の控えがあることを
  照合する。fragment の `更新` の存在は**この検査の代替にならない** (本件で実際に存在した)。
