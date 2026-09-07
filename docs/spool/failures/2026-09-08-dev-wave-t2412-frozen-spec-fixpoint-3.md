---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2412-frozen-spec-fixpoint
seq: 3
---

## 新規

### {{F:approved-ruling-not-read-in-stage1}}. 承認済みユーザー裁定を段 1 で引かず、裁定より狭い形を実装した [手順漏れ]

- 事象: dev-wave `t2412-frozen-spec-fixpoint` の段 1 で、依頼文と insight の一次資料だけを読んで
  brief を書き、`docs/worklog.md` の T-2412 項と `docs/decisions.md` の D1774 を引かなかった。
  D1774 は「HEAD が `source_commit` の**子孫**であること」を要求していたが、親は段 4 で
  「HEAD が唯一の子であり、かつ差分が spec 1 path だけ」という**より狭い**形を自分で裁定し、
  段 5 の実装、段 6 の敵対レビュー 2 本と変異 9 件まで進めてしまった。段 7 の記録で台帳の
  base digest を取るために main の worklog を読んで初めて気づき、fix 2 本で作り直した。
- 根本原因: 依頼文が一次資料として insight の README を名指ししていたため、それを読めば十分だと
  判断した。DW-S01 の「brief 前に承認済み裁定と引数の前提を実測する」を、依頼文が指す資料の
  確認だけで済ませた。**課題 ID (T-2412) が与えられているのに、その ID を台帳で引かなかった。**
- 恒久対応: {{D:frozen-spec-ancestor-binding}} で裁定に合わせて作り直した。段 1 の brief 前に、
  依頼が課題 ID を含むなら `docs/worklog.md` の当該項と、そこが指す D 番号を必ず引く。
  worktree は wave 開始時点で止まるため、この lookup は land 先の local main の現物に対して行う
  (台帳の base digest を取る手順と同じ)。
- 再発検知: 狭い形を実装した段 4 の裁定文にも、敵対レビュー 2 本にも、変異 9 件にも、
  裁定との食い違いは現れなかった。**子は親が射影した資料しか見ないため、親の資料選択の誤りは
  子の敵対レビューでは検出されない。**検出したのは台帳の base digest 取得という無関係な作業である。
  段 1 の資料選択そのものを検査する機構は無い。
