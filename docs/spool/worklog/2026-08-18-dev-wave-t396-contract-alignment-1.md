---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t396-contract-alignment
seq: 1
title: sort coder 契約の執行主体を分け、bounded loop の固定を外した — 段 2 の「禁止文を gate の言葉へ書き直す」案は禁止を 1 つ落としていた (コード + テスト + 機械設定、branch worktree-dev-wave-t396-contract-alignment、変異 matrix = baseline PASSED・5/5 KILLED・SURVIVED 1 は事前登録・MISMATCH 0)
---

## 本文

- **裁定 4 件のうち実装が要ったのは A と B だけだった。** 起動前の実測で、C
  (verifier の予定操作数検査) は既に [T-1148] として entry 568 で起票済み、D (段 8 の
  gate inventory) は見送り確定と判明した。C を再起票していれば二重在籍になっていた。
- **段 2 プランの置換案を段 3 敵対レビューが反証し、親が設計ごと差し替えた。** 段 2 は禁止 5 bullet を
  「機械執行される項目」「auditor が拒否する残余」へ**書き直す**案を出したが、レンズ A が
  (i) 書き直しの過程で「内部で処理された例外送出」の禁止が消えている、
  (ii) 第 3 bullet の「説明を `justification` へ置く」義務を機械執行と誤分類している、
  (iii) 「auditor が拒否する」は auditor の checklist に結線されておらず謳うだけの保証である、
  の 3 件を must-fix にした。親はこれを全件採用し、**禁止 5 bullet を 1 byte も変えずに残して
  執行範囲を後置する**形へ変えた。この形なら「禁止を撤回しない」が diff で機械的に保証される。
- **親自身の所見を 1 件足した。** 段 2 案の残余記述は「有限 oracle が観測しない形」という
  回避の境界条件を逐語で書いていた。これは D48 の偵察 firewall と衝突するため、
  執行の粒度 (完全 / 部分 / なし) までに留め、境界条件は書かないと裁定した。
- **親の段 1 前提を 2 件撤回した。** (P1)「契約 5 項目はいずれも未執行」は粗すぎた
  — 原子的義務の粒度では完全執行 4・部分執行 4・非執行 2 である。複合 bullet の中の
  原子的義務を bullet 5 件と同一視したことが段 2 の誤りの原因でもあった。
  (P3)「adapter は親が代行して書く」は D95 決定 (3) に反しており撤回した。
  brief が権限根拠に挙げた D149 決定 6 は無関係で、段 2 と段 3 レンズ A が独立に反証した。
- **ユーザー裁定 (2026-08-18): codex sandbox が `.codex/` を read-only にする件へ waiver を承認。**
  実装子は `OSError: [Errno 30] Read-only file system` を実測して D95 どおり fail-closed 停止した。
  親は代行せずユーザー裁定へ返し、承認を得て D105 の waiver 経路で renderer 出力を適用した。
  reason ident は `codex-sandbox-readonly-dotcodex`、ratified は 2026-08-18。
- **waiver を機械会計させるため commit を 2 本に分けた。** 段 6 レンズ 2 が
  「checker は commit 内に Codex author が 1 人でもいると先に成功し、waiver を適用済みと数えない」
  ことを `check_ai_provenance.py` の実装から指摘した。実装面 3 枚 (codex author) と
  adapter 1 枚 (親 author + waiver) を分けた結果、`implementation-author-waived=1` として
  実際に発火・計上された。1 commit のままなら親が書いた事実は機械証明できなかった。
- **段 6 レンズ 2 は変異 spec も 3 件反証した。** `file-stdio` の identifier 削除は対象が非一意で
  専用 probe を持つのは `read` だけであること、M1/M3/M4 の期待 node は先に別層が拒否するため
  primary kill の帰属が誤っていることを指摘した。全件採用し、probe 走で観測集合を集めてから
  完全集合として再登録した。
- **pin は bytes の同一性しか証明しない。** 禁止 bullet を 1 行削り、source pin と adapter を
  整合させて再承認すると、byte parity・exact-once・source hash・semantic digest がすべて再び整合する。
  これを変異 M6 として登録し、**SURVIVED を期待値として事前登録し、本走で実際に生存した**
  (3 枚の anchor がいずれもちょうど 1 回一致しており、等価変異ではなく本物の残余である)。段 3・段 6 の
  2 レンズと段 2 が独立に「禁止文の保持を意味で守る test は実在しない」と結論している。
  checker の緑を意味の証明として報告してはならない。
- **B が失う検出力は 5 parameter で、受け皿は無い。** production の `coder_effect_gate.py` は
  変更していないので現在の受理集合・certified 選択・材料レポートの値は不変で、失うのは
  「将来 bounded / range-for / data-dependent loop を誤って拒否する回帰」の検出だけである。
  これは裁定 B が明示的に選んだ未定義化であり、テストを甘くして緑にしたのではない。
- **対応表の射程は live `CoderProposalSort` build 経路に限る。** S6 sort sweep は固定候補で
  SWO oracle を呼ばず、freeze 再実体化は `prepare_cell` で quarantine と oracle を再実行する。
  全 sort materialization へ一般化してはならない (段 3 レンズ A 所見 4)。
- **セッション異常: codex の上流障害が 2 つの表層症状で出た。** 13:01 JST に段 3 の子 2 本が
  `401 Unauthorized` の連打で rc=1・出力 0 bytes で即死した。`codex login status` は
  "Logged in using ChatGPT" のままだった。同時間帯に並行 wave [T-688] は同じ障害を
  usage limit のメッセージとして観測している。症状で「認証失効」と「枠切れ」を判別できない。
  詳細は {{F:codex-upstream-two-symptoms}}。
- **job-id は prompt の内容 sha256 である。** 再投入で prompt をファイル名だけ変えても
  job-id が同じになり `既存の完全な receipt は上書きできない` (rc=2) で止まる。
  prompt 本文を 1 行でも変える必要がある。並行 wave へも共有した。
- **エージェント工数**: codex 子 8 本 (plan 1・consult 2 + 失敗 2・author 2・review 2)。
  plan と consult は `reasoning=max`、author と review は `high`。
  consult は sol / luna の 2 lane。失敗 2 本は上記の上流障害によるもので出力 0 bytes。
- 設計判断は {{D:contract-enforcement-split}}。
- 正本 = `output/insights/2026-08-18_t396-contract-enforcement-split/README.md`

## 次の一手差分

### 完了

- [T-396] ユーザー裁定 A/B を実装した。A = closed-region 契約の禁止 5 bullet を無変更で残し、
  機械 gate が拒否する項目・部分的にとどまる項目・検査しない項目を後置で明示した。
  B = bounded / data-dependent loop の受理を固定していたテストを削除し未定義へ戻した。
  C は [T-1148] として起票済みのため再起票せず、D は見送り確定で D344 も覆していない。
  remaining: none
  base: 5524333245585d6f16a37b408b9aae2e32e4927c85e412ce205953ace27f0e57

### 新規

- {{T:auditor-residual-wiring}} **P2・新規・ユーザー裁定待ち ([T-396] 段 3 レンズ A 所見 2/3 から分離)**:
  sort の closed-region 残余 (型/関数の追加、bounded loop、潜在 throw、説明配置、
  有限観測を抜ける非決定性) を auditor の入力と checklist へ結線する。
  現状 `.claude/agents/auditor.md` の入力に sort closed-region 契約は含まれず、
  checklist もこれらを拒否規則として持たない。**これを閉じるまで、契約文へ
  「残余は auditor が拒否する」と書いてはならない。**本 wave は sort role 1 枚だけを触る
  裁定だったため実装しなかった。
- {{T:contract-prohibition-semantic-test}} **P2・新規・ユーザー裁定待ち ([T-396] 段 6 レンズ 2 と変異 M6 から分離)**:
  role 契約の禁止集合が縮んでいないことを意味で守る検査を設計する。
  現行の pin (source sha256・adapter byte parity・exact-once) は bytes の同一性しか
  証明せず、禁止を 1 行削って pin を整合再承認すれば全検査が緑のまま通る。
  変異 M6 が SURVIVED でこれを実証した。
- {{T:codex-sandbox-dotcodex-writable}} **P3・新規・ユーザー裁定待ち ([T-396] の waiver から分離)**:
  Codex 実装子が role adapter を書けるようにする経路を検討する。
  codex の sandbox が repo 内の `.codex/` を read-only でマウントするため、
  Claude role source を触る wave は毎回 D105 waiver を必要とする。
  恒久解が要るか、waiver の反復運用で足りるかを裁定する。
