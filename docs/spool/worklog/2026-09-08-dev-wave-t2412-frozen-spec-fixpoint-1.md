---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2412-frozen-spec-fixpoint
seq: 1
title: [T-2412] 凍結 spec loader の hash 不動点を閉じ、D1774 の祖先関係へ合わせる (コード + テスト、branch worktree-dev-wave-t2412-frozen-spec-fixpoint)
---

## 本文

- **不動点は実 git で再現した。** base commit を `provenance.source_commit` に書いた spec を
  commit すると HEAD は別 SHA になる。bytes 一致は成立するが `source_commit == HEAD` は成立せず、
  commit しなければ `git show HEAD:<spec>` が落ちる。どちらか一方しか満たせない。
- **既存テストがこれを見られなかった理由。** `_install_git` が `subprocess.run` を差し替え、
  `rev-parse HEAD` を定数に、`SOURCE_COMMIT = HEAD` に固定していた。模擬では両条件が常に同時成立する。
  D1774 の理由欄が指摘したとおりで、本 wave はその指摘を実測で確認した。
- **段 1 で承認済みユーザー裁定を引かなかった (規律違反)。** 依頼文と insight の一次資料だけを見て
  brief を書き、`docs/worklog.md` の T-2412 項と D1774 を読まなかった。段 4 で「唯一の親 +
  spec 1 path 差分」という**裁定より狭い形**を自分で裁定し、段 5・6 でそれを実装・検証してしまった。
  段 7 の記録に入る直前、台帳の base digest を取るために main の worklog を読んで気づいた。
  詳細は {{F:approved-ruling-not-read-in-stage1}}。
- **狭い形は実害がある。** freeze commit の後に 1 つでも commit が乗ると spec が二度と load
  できない。本 wave の最中だけで local main は 8 commit 進んだ。T-2412 が閉じようとしている失敗
  (spec が使えない) を作り直すことになる。D1774 に合わせて祖先関係へ直した ({{D:frozen-spec-ancestor-binding}})。
- **捨てた実装も証拠として残す。** 狭い形は敵対レビュー 2 本と変異 9 件で検証済みで、保証は祖先形より
  強い。採否はユーザーの判断であり、逐語・変異台帳・敵対レビューを
  `output/insights/2026-09-08_t2412-frozen-spec-fixpoint/` に残して裁定へ返す。
- **敵対レビューの所見 (祖先形へ移る前に閉じたもの)。** blob 検査が symbolic `HEAD:` を使い後から
  解決する HEAD と別 commit を指しうる点は real で、`loaded_head` を 1 回だけ解決して spec・
  calibration・build receipt の全 blob 比較をその OID へ束ねた。これは祖先形でも残している。
- **refuted 1 件。** 「台帳の所要値が実走に結び付いていない」— レビュー子は実装子の報告 (dispatch
  障害で未実走) しか射影されておらず、親が 209 件緑の JUnit から `update_acceptance_duration_ledger.py
  --add-only` で登録した事実を持っていなかった。
- **受入台帳の欠落を発見した。** `test_floor_pair_driver.py` は 209 node すべてが受入所要台帳に
  未登録で、本 wave が 10 node 足した時点で被覆が 89.962% と 90% 閾値を割った。同 file 全件を登録した。
- **子の工数。** codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 4 のうち fix は 4 本)。
  実装子・fix 子はいずれも sandbox から `run_tests.py` が rc=16 で pytest を実走できず、
  緑の確認はすべて親が行った。

## 次の一手差分

### 更新

- [T-2412] **P1・実装済み・ユーザー裁定待ち**: D1774 の祖先関係で不動点を閉じた。
  実装は branch `worktree-dev-wave-t2412-frozen-spec-fixpoint`。
  狭い形 (唯一の親 + spec 1 path 差分) を採るかの再裁定を返す — 保証は強いが freeze commit の
  後続 commit で load 不能になる。
  base: ed38c9598e0172ed8340e53ec52777476b689bf4576a01de24fe971080cee406

### 新規

- {{T:floor-spec-issue-replace-objects}} **P3・新規**: 凍結 spec の全 git object query へ
  `--no-replace-objects` を付けるかを裁定する。`refs/replace` があると記録 OID と検証対象が
  ずれる。本 wave では仮想リスク向けの検査追加として scope 外にした。
- {{T:floor-summary-loaded-head-crosscheck}} **P3・新規**: issuer が `summary["loaded_head"]` を
  検証せず成果物へ転記している。load 済み spec の `loaded_head` と突き合わせるかを裁定する。
  本 wave 以前からある形で、production への比較追加は新設 gate のため scope 外にした。
