---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-manifest-land1
seq: 1
title: land 1 を実行した — 再発行 record-items・受領証 schema・第 2 erratum と a13 予約 entry を承認 payload として fold した ([T-139]、docs のみ、実装面 0 byte、branch worktree-dev-wave-t139-manifest-land1)
---

## 本文

- **ユーザー裁定 S1〜S9 は全問が親推奨どおり確定した** (2026-08-11 /rulings、前エントリ)。
  第 2 波が「承認候補を直して返した」9 問がこれで閉じ、land 1 = 「main 取り込み → 受入全走 →
  land」だけになった。本エントリはその実行記録である。
- **第 2 波が停止した理由 (記録):** R1 (a) が認可したのは land の**順序**であって承認対象の
  **内容**ではなく、R1 の裁定時点で未見だった 7 事実が承認対象そのものを承認不能にしていた。
  `DW-S04` に従い親は不採用にせず、承認候補を承認可能水準へ直して再裁定へ返した。
- **最も重い新事実は「凍結 core が較正義務を 2 箇所に持つ」。** `較正` を含む行は 221 行 (§7) と
  **333 行 (§14 の `a12` 行、LF 込み `a7852ad9…9952`)** のちょうど 2 件で、第 1 波が起草した
  1 operation の erratum では置換後 core が「§7 = stress check、§14 = 較正」の二重状態になる。
  草案 erratum (`9eb96f88…885c`) と合成 digest `dfb821a5…678c` は**承認可能でない**。
  2 operation 版の合成は `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c`
  (適用順不変、置換後 core に `較正` 0 件)。親と段 3 の 2 レンズが独立に再現した。
- **草案には裁定外の受理拡大があった。** `pre_performance_infra_failure` を marker 不在だけで
  成立させており、追補 A `a04` が「開始後の失敗・置換しない」と定める attempt (性能 raw を持つ /
  `a03` 不成立) を予備置換可能にしていた。v2 で `a04` 準拠へ縮小した。
- **受領証 schema の dialect は環境実測で決まった** (S3 = draft-07)。この環境の `jsonschema` は
  3.2.0 で `Draft202012Validator` を持たず、repo の既存受領証 schema も draft-07 + `definitions`
  形式である。段 2 が置いた「2020-12 前提」は実測で否定された。
- **`a13` 予約 entry の具体値は本 wave の親 closure である。** S5 (a) は「予約 entry を land 1 の
  fold へ同梱する」と裁定し、第 2 波は「台帳 path・canonical bytes・append-only 検査の仕様は
  `record-items-v2.md` §6.7 が既に定めている」と書いていた。**実際に §6.7 が定めるのは
  validator が行う検査だけで、台帳 path・行の key 集合・serialization 規則を literal では
  定めていない。**定めないと 2 実装が同じ予約から別 digest を出し `reservation_entry_sha256` を
  独立再導出できないため、親が閉じて {{D:t139-record-items-and-second-erratum-approval}} の
  payload へ `alpha_reservation` として pin した (台帳 =
  `output/registry/t139-alpha-reservations.jsonl`、`family_root` = 事前登録承認の fold commit
  `F_e` = `dce4ae4f…2850`、`ordinal` = 1、行 142 bytes の
  `52ba3d2c86f7554d78433a1dec4f3364f1db2b8dd1e6aa0360f4428f93127cf3`)。
  **台帳は append-only で導入も exact 1 回であるため、この 1 行は事実上不可逆である。**
  `reservation_commit` は §6.7 (7) に従い validator が再導出するので pin しない (自己 hash 回避)。
- **land 1 の diff に実装面が 1 byte も無いことを機械確認した。** 許容 path は
  `output/insights/2026-08-11_t139-manifest-land1/**`、`docs/spool/{decisions,worklog}/2026-08-11-*`、
  および S5 (a) が追加を認めた予約台帳 1 file の 3 系統で、実行可能拡張子 0 件・実行 mode 0 件。
- **段 2・段 3 はいずれも NO-GO だった。** 段 3 のレンズ 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`) は
  blocker 11 件 / 8 件を返し、親は refuted 2 件 (再発行版の暗黙参照という一般論、
  「1 wave に必ず収まらない」の証明)、残りを real と裁定した。親の (P2)・(P3)・(P6) は撤回した。
- 変異 matrix は免除した (diff に実行可能コード・テスト・gate が 1 行も無く、kill を観測する面が
  無い)。代わりに敵対レビュー 2 本 + 焦点再レビュー 1 本を凍結対象へ当てた。
  **焦点再レビューの対応表は closed 30 / partial 6 / regressed 0、独立再計算 7/7 一致**で、
  凍結前に直すべきとされた 3 件 (§7.1 の件数条件、算術誤記の記述、erratum blob の manifest pin) は
  親が全件対応した。
- **レビュー C は 1 回目に必読資料欠落で fail-closed した** — land 1 branch は local main から
  分岐しているため、第 1 波の未 land 草案が worktree に存在しない。repo 外へ写して再投入した。
  正しい fail-closed であり所見ではない。
- **pilot は投入していない。** 投入 API は 1 つも実装されておらず D264 の非 export が機械固定して
  いる。land 2 の層 (manifest / resolver / writer / 台帳 / submit / driver / collector / consumer) は
  1 つも実装していない。見積りは production 7,600 行 + test 7,820 行、PBS 9〜11 割当て。
  land 2 の必須要件 7 件は `package.md` §S7 に名指しで記録した。
- **受入全走は 2 度必要になった。** 1 走目は main `0c336b8e` を取り込んだ tip で
  **8427 passed / 20 skipped / 557.96 秒 / rc=0** (計算ノード dispatch、request 901498.nqsv)。
  ところが 9 分 17 秒の走行中に local main が 3 commit 進んで ff-only が成立しなくなり、
  取り込み直して再走した。**受入 lease の待ち手は「最後の `HEAD..main` 再検査から受入 command
  起動までの間」の race しか閉じておらず、走行中に main が進む race は閉じていない。**
  受入 1 走が約 10 分ある以上、並行 land が多い時間帯では常態的に起こる。
- **段 8 の改善候補 3 件は `docs/dev-wave/**` の L1.5 予算に入らないため編集せず返した**
  (実測 9508 bytes / 予算 9566 bytes = 余裕 58 bytes)。S9 = (a) の裁定に従い、予算の独立審査を
  {{T:dev-wave-docs-budget-review}} として起票する。

## 次の一手差分

### 更新

- [T-139] **P1・land 1 を実行済み (2026-08-11) → 残りは land 2 (manifest + producer + pilot) のみ**:
  再発行 record-items (`record-items-v2.md`)・受領証 schema (`receipt-schema-v1.json`)・
  第 2 erratum (`erratum-core-s7-stresscheck-v2.md`) の承認 payload と `a13` 予約 entry を
  同一 fold で main へ入れた。以後の T-139 approval manifest は本 fold commit を
  `approval_fold_commit = F_r` として literal で持ち、resolver は manifest を信用する前に
  `F_r` の `docs/decisions.md` から payload を読んで三つ組集合・erratum 順序・合成 digest・
  保証境界の exact 一致を要求する。**land 2 は branch `worktree-dev-wave-t139-manifest-w2` を
  継承し、S6 (a) に従って複数 session に跨ってよいが land は最後に 1 回だけ**。
  land 2 の必須要件は `output/insights/2026-08-11_t139-manifest-land1/package.md` §S7 の 7 件
  (台帳 → manifest の第 1 矢印、`PATH` 差し替え、symlink/TOCTOU、correctness anomaly の構造化
  還流、変異の単一理由帰属、`a05` の build 再利用、`b03`) で、`DRAFT_ERRATUM_PATH` は承認 path
  へ差し替える。公表 core の C-1〜C-5 と追補 B 第 5 案不採用は裁定済み (段階 2 の再提出へ)。
  **本走投入は段階 2 の再提出後まで依然不可**
  base: c842e39b69aa3015f907b4fc9be64262acb49c3b0f4a585d5fdc48cc2249540c

### 新規

- {{T:dev-wave-docs-budget-review}} **P2・新規・ユーザー裁定 S9 (a) による起票**:
  `docs/dev-wave/**` の L1.5 読み込み予算 (実測 9508 / 9566 bytes、余裕 58 bytes) を独立に審査し、
  第 2 波が実測した手順改善 3 件を収容できるようにする。3 件は (1) 段 5 の子が読む正本を親が
  稼働中に編集して子の出力が旧版基準になった (`DW-O02` 行き) / (2) prompt の必読 path が子の
  worktree に無くレビューが fail-closed して 1 巡を空費した (`DW-O02` 行き) / (3) file 選択走が
  `from tests import` の import path を確立せず偽赤を出す (`DW-O18` 行き)。
  **予算値の引き上げは自己改善に含めない規律**であり、dev-wave 系への外出しは D94 で却下済み
  なので、陳腐化した既存節の特定と等価縮約が審査の対象になる。
  正本 = `output/insights/2026-08-11_t139-manifest-land1/package.md` §S9
