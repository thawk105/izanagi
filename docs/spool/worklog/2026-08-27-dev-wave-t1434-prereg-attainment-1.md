---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1434-prereg-attainment
seq: 1
title: [T-1434] 事前登録文書の到達度記述を実装へ揃え、差し替え前から残っていた過大主張 5 件も直した (docs + 受入所要台帳、branch worktree-dev-wave-t1434-prereg-attainment、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **依頼の scope は「実態より低い記述の差し替え」だったが、実測すると過大主張の方が多かった。**
  台帳が名指ししていたのは (a) task manifest の CLI 入力口と (c) 費用の部分正規化計算が
  「未実装」と書かれたままである、という**過小**の 2 件だった。段 6 の敵対レビューが、同じ §5.2 の表に
  **差し替え前から**過大主張が 3 件残っていることを見つけた — `MODEL` 行 (schedule が
  `requested_model` を省略すると `MODEL` へ既定化されるので、schedule はまだ唯一の routing
  authority ではない)、`supervise_pair` 行 (block 検査は sol/luna 各 1 回を固定せず、
  `(arm, requested_model)` の組が 2 つ異なることしか要求しない)、`collect_run` 行
  (`collect-run` verb の `--expected-model` は既定値が `MODEL` のまま)。
  親が一次資料で全件裏取りして採用した。**過大主張の方が規律 2 に照らして危険なので、
  到達度 wave が見つけて放置する筋はないと裁定した。**
- **前 wave が残した文面案は誤っていた。** 台帳は「文面案は 2026-08-25 の insight のレビュー B
  逐語にある」と書いていたが、その案の「`render-prompt` は既定 manifest の provenance のみを読む」は
  現行実装では偽である。`render_prompt` は外部 manifest から task を選び、source session・rollout・
  prompt-source pin を入力決定に使う。段 2 の codex plan と親が独立に同じ結論へ到達したため、
  この案を採らなかった。**台帳が「文面案がある」と書いていても、案の中身は一次資料で検算が要る。**
- **既裁定の逐語を射影した子と、しなかった子で結果が割れた。** 段 2 の plan 子には D932 の逐語を
  渡さず、段 3 のレンズ B には渡した。plan 子が起草した §10 の規則文は D932 が言っていない
  分母規則 (`attempt_count` への算入) を新設しており、D932 を持っていたレンズ B が
  「越境」として must-fix で捕まえた。plan 子自身も「親は執筆前に D932 正本と逐語照合すること」と
  書いて補償していた。near miss。恒久対応は {{F:ruling-not-projected-to-plan-child}}。
- **段 6 の must-fix 6 件のうち 1 件 (§10 の fail-closed 文) は不採用にした。** 実装は全 slot
  `{null}` の schedule を price 未束縛として受理するのに、文は無条件に読める。real だが
  **到達度の記述ではなく規則文**であり、(a) ユーザーが固定した scope の外、(b) 段 3 レンズ B の
  「到達度に見せかけて意味規則を変えるな」という所見を段 4 で採用した以上ここで破るのは筋が通らない、
  (c) 誤りの向きが gate を実際より**厳しく**書く安全側である、という 3 点で次タスクへ送った。
- **DW-O09 の pin 閉包を docs path でも取った。** 対象文書を bytes pin する code / test / trust root は
  0 件 (`tools/` `tests/` `hooks/` の `grep -rl` が 0、repo 全体の `*.py` `*.json` `*.toml` `*.cfg` も 0)。
  `tools/check_docs.py` の `LIVING_DOCS` にも非収載。したがって certified な選択結果・レポート・
  台帳の**値は 1 つも動かない**。動くのは、この事前登録が要求する受理条件を次の実装 wave が
  正しく読めるかどうかだけである。
- **子は 5 本。** 段 2 plan 1 本、段 3 敵対相談 2 本 (過大主張レンズ / 越境・差し替え漏れレンズ)、
  段 6 敵対レビュー 1 本を `sandbox=read-only` で、受入台帳の修理を Codex `role=author`
  1 本を `sandbox=workspace-write` で走らせた。事前登録文書の本文は docs-only なので親が書いた。
  **author 子は Pegasus の `qstat` preflight が sandbox の socket 拒否で失敗し、テストを
  1 件も実走できなかった。** 子は緑を申告せず「親側で再実走が必要」と正しく報告し、親が実走した。
  所見は段 3 が must-fix 8 件、段 6 が must-fix 6 件 + should-fix 1 件で、**refuted はゼロ**。
  親は段 4 で A-04 (費用の失敗が certified `valid` を落とす) の射程をレンズ A より狭く直した
  — 例外を投げるのは malformed 入力だけで、token 観測不能は例外を出さない。これは D932 の
  但し書きに正確に一致する。
- **段 8 の自己改善は `DW-O02` の射影義務 1 件。** L1.5 の byte 予算が満杯 (9564/9566) だったため、
  追記ではなく同節の既存文を意味等価に縮約して収めた (744 → 731 bytes)。予算値は上げていない。
- **受入全走が非帰属の赤で戻り、その赤が repo 全体を塞いでいたので直した。** 1 件だけ赤で
  `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` の被覆率が
  15912/17700 = 89.898% と閾値 90% を割っていた (17638 passed / 61 skipped)。
  本 wave の `main...HEAD` は docs 12 file だけでテストを 1 件も追加していないため、
  collection は main と同一であり非帰属である。**しかし閾値を緩める選択は取らなかった** —
  F515 がこの gate を「台帳の陳腐化を検知する運用 gate も兼ねる」と明記して置いたもので、
  緩めれば規律 2 の違反になる。同じ赤を 1 時間前に別 wave が「台帳へ最小追加」で直した先例が
  あり、その commit に「丸ごと再生成したら別の不変条件を壊した」という教訓も残っていた。
  Codex `role=author` に実測 JUnit からの**追加だけ**をさせ、親が独立に検証した —
  既存 15944 件は削除 0 件・値変更 0 件、追加 1786 件、`nodeid_count` 17730、
  素の writer nodeid は不在のまま、`@real-repo` 付きの値は 0.19 のまま。
- **この修理で実装面の差分が入ったため、DW-S04 の変異免除は使えなくなった。**
  台帳の entry を 1 件変えても被覆率は 90% を大きく上回ったままで単一理由の赤にならないので、
  `DW-M01` に従って実効 gate へ照準し直し、writer nodeid の pin 2 件と `nodeid_count` の
  整合を対象にした。期待 node が未確定だったため全件 SURVIVED 期待の probe を先に回して
  観測 node を集め (`mutation-spec-probe.json`、erratum として保存)、確定版で本走した。
  **baseline PASSED、3/3 KILLED、SURVIVED 0、MISMATCH 0。** 3 変異とも失敗 node は
  `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` の 1 件だけだった。
- 焦点走 `orchestrator/tests/test_check_docs.py` = 567 passed / 3 skipped (rc=0)。
  `orchestrator/tests/test_acceptance_schedule_order.py` = 79 passed (rc=0)。
  `DW-O02` を編集したので同じ焦点走を編集後にもう一度回し、同じ 567 / 3 で緑を確認した。
  `python3 tools/check_docs.py` = 違反なし、`git diff --check` = 空。
  対象の事前登録文書を読む consumer test は 0 件だった。

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: (a) task manifest の CLI 入力口と
  (c) 費用の部分正規化計算を接続し、**2026-08-27 に事前登録文書 §5.2 / §5.3 / §10 の
  到達度記述を実装へ揃えた** (§13 / §14 / 総括 に複製されていた同じ到達度も同時に直した)。
  (b) adjudication 層の task-specific oracle 対応は §8 の独立 oracle ledger 待ちで scope 外。
  費用を gate へ接続する件は D932 が「記述統計として出し certified な判定を動かさない」と
  裁定済みで、**接続しないことが結論**である。残る未解決点は次のとおり。
  正規 receipt へキャッシュ書込の数量を保存し完全な費用を出すこと (receipt schema と
  price snapshot の新しい登録世代が要る)。`_certification_scope` を改訂して費用を
  certified field にすること。`SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。
  served model attest の不在。
  **到達度の張り替えで新たに実測した装置側の穴** — schedule が `requested_model` を省略すると
  `MODEL` へ既定化され、`collect-run` verb の `--expected-model` も既定値が `MODEL` のままで、
  schedule はまだ唯一の routing authority ではない。block 検査は sol/luna 各 1 回を固定しない。
  v3 schedule の task/arm 期待件数は manifest に独立登録されず schedule 自身から導出される。
  schema v2 と `schema_version` 欠落の schedule は `LEGACY_EXPECTED_SCHEDULE` 固定。
  standalone `verify-snapshot` は `--task-manifest` を持たない。
  base: e28c49680ecc0d4af30e2d7adf34398d15d9cd62d3cf5288940906c464851cbf

### 新規

- {{T:prereg-s10-null-price-rule}} **P2・新規**: 事前登録 §10 の「上記項目が欠落する場合、
  schedule を無効化する (fail-closed)」を、全 slot `{null}` の schedule を price 未束縛として
  受理する実装に合わせて限定する。docs のみ。段 6 の must-fix として real 判定済みだが、
  到達度記述ではなく規則文のため [T-1434] の wave では触れていない。
  誤りの向きは gate を実際より厳しく書く安全側であり、緊急ではない。
