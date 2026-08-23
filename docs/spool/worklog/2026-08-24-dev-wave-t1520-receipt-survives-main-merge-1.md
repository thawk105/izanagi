---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1520-receipt-survives-main-merge
seq: 1
title: [T-1520] 受入受領証を衝突なき main 前方取り込みで無効にしない実装を入れ、検査手段を実測で選び直した (コード+テスト+docs、branch worktree-dev-wave-t1520-receipt-survives-main-merge、変異matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- D689 の実装。受入 1 回のあと、衝突のない main 前方取り込みを何回行っても受領証が生き続ける。
  設計判断は {{D:forward-merge-replay-instrument}} と {{D:forward-merge-accepted-shape}}。

- **D689 の実装条件 3「受領証へ取り込んだ main SHA の列を追記」は、額面どおりには実装できない。**
  受領証を著すのは tested main 側の blob から実行される launcher であり、新しい版の launcher は
  main へ着地するまで実行されない。受領証の schema を上げると、自分の受入は旧版の受領証を出し、
  自分の land がそれを拒否する。**自分の変更が自分の着地を塞ぐ。**
  親はこれを実測 (schema v5 が入った 3 commit は launcher の新設と同時で、
  main に launcher が無い場合だけ通る bootstrap 経路を使っている) したうえで、
  受領証の bytes を変えず land が git から列を導出して結果 JSON と本エントリへ記録する形を採った。
  **この読み替えが D689 の射程内かは段 3 の攻撃対象に据え、両レンズとも射程内と判定した。**

- **段 2 の plan が採った検査手段は、実データで成立しなかった。** 親が main の実履歴にある
  正当な取り込み (`f3c27afb`、衝突なし) で実走したところ、`git diff-tree --raw` の byte 比較は
  6 record 中 1 record が不一致になり拒否された。不一致は main と wave の両方が触った
  `docs/dev-wave/operations.md` で、`git diff` の生 byte 比較も同じ理由 (index 行の blob OID が
  両側とも変わる) で不一致になる。多数の wave が触る file では稀ではないため、
  そのまま実装すると律速はほとんど解けなかった。
  この機体の git 2.34.1 の patch-id は空白を無視する (`--verbatim` は 2.39 以降) ため、
  代替にもできない。親が隔離再演を実走して同じ実例で tree OID の完全一致を確認し、採用した。

- **段 3 の 2 レンズが独立に同じ安全性後退を検出した。** 前方取り込みの初段が
  tested main に束縛されておらず、tested main の祖先から分岐した commit を main に据えると
  受入でテストしていない系統を着地できた。従来経路は「main が tested main を含む」ことを
  要求しており、新しい経路だけがこの保護を落としていた。段 6 の fix で閉じた。

- **親の規律違反 2 件。** (1) 起動を拒否された codex 子の `.done` を削除して同じ artifact path で
  投げ直した (`DW-O01` は再利用を禁じている)。拒否の原因は解消済みで走行は健全だったが、
  以後の再投入は新しい path を使う。(2) 変異 matrix の走行中に段 7 の fragment を worktree へ書き、
  harness を untracked file 検出で止めた。**同じ turn の中で「走行中に tree へ書かない」と
  自ら明示した直後の違反**である。

- 子の工数: 段 2 plan 1 本、段 3 consult 2 本、段 5 author 2 本、段 6 fix 2 本、
  段 6 review 2 本。**codex 子は 1 件も pytest を実走できていない** (sandbox が socket を
  拒否するため計算ノードへ dispatch できず、login 側も slice が上限近く)。
  テストの実測はすべて親が計算ノードで行った。

- 非帰属の赤 1 件を `--deselect` で外した。詳細と申し送りは {{F:truncated-ruling-projection}} と
  同じ fragment の F57 再発に書いた。

- **docs/dev-wave/** の byte 予算に headroom が無い** (baseline がちょうど上限)。
  契約へ 1 語足すたびに既存文の縮約が要る。今回は同節内で意味等価な縮約 4 箇所と相殺した。
  予算値の見直しは自己改善の範囲外 (独立審査対象) なのでユーザー裁定へ返す。

## 次の一手差分

### 完了

- [T-1520] 受領証が main 前方取り込みを跨いで生き残るようにした。
  受領証の schema・argv・tested main/tip は不変で、受理集合が広がるのは
  「衝突なき前方取り込みだけからなる子孫」の 1 方向のみ。
  検査は隔離した機械 merge の再演と tree OID の完全一致で行う。
  段数上限 8、初段の tested main 束縛、merge 設定の全 origin 拒否で受理形を縛った。
  remaining: none
  base: 7911aa4b469945f0b539666ce2e382184aa69ab8a0b51eaeb856025a931eccdc

### 新規

- {{T:campaign-guard-file-set-flake}} **P2・新規 (2026-08-24、変異 baseline で摘出)**:
  `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
  file 集合に依存して落ちる。10 file 走 (1676 item) では緑、2 file 走 (327 item) では赤で、
  どちらも同じ計算ノードへ dispatch している。赤の本文は
  `orchestrator/campaign/execution_guard.py` の `CertifiedWriterAuthorizationError`
  「Pegasus compute では receipt state 内で一意な required authorization_contract だけを受理する」。
  `REAL_REPO_SERIAL_NODES` 未登録。**編集面** = 当該テストと campaign 側の
  authorization receipt state の解決経路。**成立条件** = file 集合を変えても結果が変わらないこと。
  変異 harness の baseline を止めるため、根治するまで `--deselect` が要る。

- {{T:devwave-docs-budget-ceiling}} **P2・新規・ユーザー裁定待ち (2026-08-24)**:
  `docs/dev-wave/**` の L1 byte 予算に headroom が無く、baseline がちょうど上限に張り付いている。
  新しい契約を 1 語足すだけで超過し、既存文の意味等価な縮約と相殺しなければ通らない。
  縮約は毎回意味を落とす危険を伴う。**予算値を上げる変更は通常の自己改善に含めないと
  定められている**ため、裁定を仰ぐ。**選択肢** = (a) 予算値を上げる、
  (b) L2 へ落とせる節を洗い出して L1 を減らす、(c) 現状維持で縮約を続ける。

- {{T:forward-merge-e2e-eight-stage}} **P3・新規 (2026-08-24、段 6 レビューが指摘)**:
  段数上限ちょうどの前方取り込みを、topology 検査だけでなく land の端から端まで
  (再演・lock・provenance・ff-only・fold・通知 JSON) 通す正例を足す。
  現行の上限内テストは topology helper の返値までしか見ていない。
