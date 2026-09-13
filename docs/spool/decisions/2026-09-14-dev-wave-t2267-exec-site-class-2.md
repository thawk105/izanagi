---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2267-exec-site-class
seq: 2
---

## {{D:exec-site-classification-route-gap}}. 実行場所分類の経路不足を実測で確定し、対象限定の測定経路の可否を裁定へ返す

**決定 (1):** `docs/pegasus-runbook.md` §7.0 の実行場所分類について、D1938 が AI へ委任した対象の
**対象・入力・実行条件は確定した**。対象は `tools/t2216_backoff_walk_model.py`、明示入力は
5 files / 297,814 bytes、凍結設定は `REPETITIONS = 8` と `DURATION_US = 3_000_000.0` である。
凍結 `measured.json` は使い捨ての過去 wave job ディレクトリに完全一致 2 本が実在し、
3 者が独立に sha256 を照合した。**本走 argv は再現可能である。**

**決定 (2):** **対象の本走は分類しない。`unknown` を据え置く。** T-2216 model の凍結入力・本走 argv を
受け取れる認可済みの login dedicated-scope 経路が、調査した現行実装には無いためである。
認可済みの login bounded scope は `tools/run_tests.py` の pytest 経路と
`tools/check_ai_provenance.py` の履歴監査経路に実在するが、どちらも自分自身を再 exec する形で、
任意の実行体を受け取らない。`script_path` の内部 seam、変異 fan-out の command 引数、
compute の `generic`、user/mount namespace 隔離は、いずれも認可済み経路に数えない。
**「login dedicated-scope 経路は存在しない」という無限定の主張は採らない** — 段 3 の敵対レンズが
現物で反証した。判定は「調査した現行実装には無い」であり、静的検索を全実行面の不在証明にしない。

**決定 (3):** 既存 runner で得た bounded scope の `memory.current` 観測は
**§7.0 手順による実測ではない**ものとして記録する。sampler は scope 起動後に開始し、
ループ待機が 5 ms で、§7.0 の先行 sampler・間隔 ≪1 ms とは異なる。したがって
**certified peak を計算せず、欄も作らず、資源 class を変更しない。** 走ごとに付与予算が異なるため
「3 反復」とも書かない。runner が表示する予算は実効 `memory.max` の逐語観測ではなく、実効値は未取得とする。

**決定 (4):** 不足している実行経路は**成立条件の仕様としてだけ**書き、実装しない。仕様は
(a) 対象を現行実行体の本走に限定し凍結 bytes・argv・commit・依存版を記録できること、
(b) 全子孫を専用 cgroup に収め実効 `memory.max` と swap 制約を確認できること、
(c) 開始を取り逃さず charged memory を観測し測定範囲と失敗を記録できること、
(d) 7 項目を同じ 1 回の実行へ結び付け、0・欠測・cap 到達を軽量成功としないこと、
(e) 資源分類と性能測定を混同せず hook 拒否や未解析面を経由しないこと、である。

**決定 (5):** 次の 3 件をユーザー裁定へ返す。
(i) 対象限定の測定実行経路を作ってよいか。
(ii) 非 `tools/pegasus/` path の `local-ok` 登録が loader と hook の双方で拒否される制約の下で、
対象を測れたとして class をどう扱うか。
(iii) 凍結入力 bytes の保全先 — 使い捨ての job ディレクトリ外へ置くか、置くならどの provenance 規約か。

**理由:**

- D1938 は実行担当の変更であって、実装面の変更を一括承認したものとは読めない。
  同決定は「必要な実行経路は既存機構を優先し、人間専任の代わりとなる新たな承認儀式は設けない」と定め、
  §7.0 は「実行可能な経路が無ければ、その不足を AI の実装課題として特定する」と定める。
  本決定はその「特定」までを行う。
- D180 は測定専用 bounded surface の即時新設を却下し、admission registry の族再設計へ同梱すると定めた。
  対象限定であってもこの論点に触れるため、親の裁量では実施しない。
- D210 は上限付き実行を entry point の内側に閉じ、汎用 launcher を作らないと定めた。
  内部 seam の CLI 公開や任意 argv を bounded に流す launcher は、同決定が取り下げた設計と同型である。
- 測り方の差を書かずに小さい観測値を載せると、テスト scope の値で対象を軽い側へ倒せる。
  絶対規律 2 の直接適用として、測定方式の差と射程を逐語で残し、class は動かさない。

**却下した選択肢:**

- 担当が AI へ移ったことを根拠に class を `local-ok` へ倒す — 実測証拠を代替しない。
- 共有 cgroup の差分・per-process RSS・過去の非 canonical 測定 script を分類根拠にする — D1938 が禁じている。
- 別綴り・Codex 子・subprocess 越し・cgroup の直接作成で hook 拒否を回避して測る — 迂回であり採らない。
- 同じ実行をユーザー手番へ返す — D1938 が明示的に禁じた。返すのは経路新設の可否だけである。
- 凍結入力を repo へ複製して保全する — 複製先の provenance 規約を新設せずに置くと
  由来不明の凍結 bytes が増える。保全先自体を裁定項目にした。
