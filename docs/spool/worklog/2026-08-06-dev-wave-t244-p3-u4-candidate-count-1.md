---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t244-p3-u4-candidate-count
seq: 1
title: [T-244] P3 の member 行数と候補数を別 field へ分けた — 依頼の二択はどちらも配線待ちで実装不能と実測し、今 fireable な U-4 の核だけを実装した (コード + docs、受入 6779 passed / 20 skipped、変異 14/14 KILLED、branch worktree-dev-wave-t244-p3-u4-candidate-count)
---

## 本文

- **依頼の二択 (report v3 / origin-proofs sidecar) は、どちらもそのままでは実装できないと実測で
  判定した。** `campaign.reflux_origin_ledger` を import する production コードは存在せず
  (hit は自分のテストと過去 wave の使い捨て probe だけ)、sidecar の `batch_id` /
  `batch_commit_event_sha256` / `batch_seal_event_sha256` / `seal_state_commitment` と
  authority 系 5 field を埋める実 artifact path が無い。`DW-G04` の発火 gate を満たせない。
  report v3 (`origin_proof_ref`) は sidecar への参照なので同じ理由で成立しない。
  **この分割項のうち今 fireable な核である U-4 の記録形分離だけを scope にした** ({{D:u4-member-rows-vs-candidates}})。
- **段 3 の敵対 2 レンズが独立に NO-GO を返し、must-fix 9 件 (2 組は同一所見) を出した。**
  親は全件を real/refuted に裁定し、「実装しない」ではなく **plan v2 を確定して実装する**と決めた。
- **両レンズが逆方向を指した論点 1 件を親が設計として決めた。** レンズ A は「tombstone を含めて
  候補数を数える」前提で境界テストを求め、レンズ B は「tombstone は未実行行 (D166) だから
  含めると未実行候補で下限を満たせる」と警告した。**count を 2 つに分けて両立させた** —
  記録は全 member、下限 gate は非 tombstone に掛ける。
- **親 brief の provisional 裁定 P1 を段 2 の指摘で撤回した。** `QueryFloorConstraint` へ候補数下限を
  足す案は、query 数の式に直交する条件を混ぜ、複数 constraint に同じ下限を書いたときの実効値が
  暗黙に最大値になる。`BudgetPolicy` の単一 field へ変更した。
- **段 4 の裁定 T6 を、段 5 完了後に未見の新事実で撤回した。** 「`output/insights` の probe は
  歴史記録なので書き換えない」と裁定したが、追跡されたテスト `test_t244_p3_liveness_probe.py` が
  subprocess で probe を実行しており、前 wave の実装 commit `2dc107ce` も同じ理由で probe を
  更新していた。親が裁定前に確認していなかった事実である。probe を新 API へ追随させた。
- **段 6 のレビュー 2 本も独立に NO-GO で、must-fix が 11 件収束した。** 最重要は 2 件。
  (a) **既定値でも受理集合が縮んでいた** — 全 member が tombstone の batch は実行候補 0 なので
  既定の下限 1 を下回り、従来 certifiable だった origin を拒否していた。不変条件
  「既定で受理集合を狭めない」に反するため、実行候補 0 の batch を gate の対象外にした。
  (b) **旧 key 拒否の負例が旧形を再現しておらず**、新 key を残したまま `cardinality` を追加する
  だけだったため、旧-only alias を受理する変異が静的に生存すると判定された。
- **レビュー 2 本が逆を主張した 1 件も親が裁定した。** 拒否理由 anchor の不一致について、
  R1 は「実装の理由文字列を旧語彙へ戻せ」、R2 は「テストの期待文字列を新語彙へ更新せよ」と
  主張した。**テスト側を更新すると裁定した** — 語彙の是正が本 wave の scope そのものであり、
  実装へ旧語彙を残すのは目的に反する。fix 子へは「親が明示許可した唯一の期待値更新」と伝えた。
- **焦点再レビューは所見 11 件すべてを `closed` と判定し、fix による退行なしと結論した。**
  fix 前 snapshot との現物比較で、正例被覆の後退・無許可の期待値変更・gate 緩和による
  抜け道のいずれも認めなかった。
- **変異は事前登録 13 件に、段 6 の実測所見から 1 件 (全 tombstone batch を gate 対象へ戻す
  過剰拒否検出) を足して 14 件。本走は 14/14 KILLED・SURVIVED 0・baseline 緑。**
  初回走行は 5 件が MISMATCH だったが、**すべて親が登録した期待 node が実測とずれていた**側の
  誤りで、変異自体はいずれも検出されていた (F87 再発)。初回台帳は消さず erratum として残した。
- **変異走行中に docs を書いてツリーを汚し、自分で気づいて撤去した。** harness は untracked を
  検出して中止するため、記録は走行完了後に置いた。2 走目は `--out` が既存で起動時に停止したので、
  出力先を変えて走らせ直した (どちらも計算資源は消費していない)。
- 受入全走は Pegasus 計算ノードで 2 回。実装 + main `23cc93d6` 取り込みの tip `16cfdc6d` で
  **6779 passed / 20 skipped** (request 892689.nqsv、1363.20s)、記録と段 8 を載せた tip
  `53e1c3ce` で **6779 passed / 20 skipped** (request 892718.nqsv、868.79s)。
  land 直前の tip はこの記録訂正 commit 1 本だけ先へ進んでおり、docs のみで
  `tools/check_docs.py` と fold dry-run を直接緑にして閉じた。
  焦点走行は fix 前 3 failed / 41 passed (request 892393.nqsv)、fix 後 48 passed / 0 failed。
  変異は同じ tip `16cfdc6d` に対して走らせ、走行後の作業ツリー復元も確認した。
- **名乗りの上限を段 4 で先に固定した。** 名乗ってよいのは ledger の記録形における
  member 行数・凍結候補数・実行候補数の分離と、authority が下限を明示したときの
  certifiable `OriginSealed` 受理での per-batch 強制まで。**P3 / P4 の充足・軸 (iii) の
  anti-oracle・origin-proofs sidecar・report v3・completeness・U-1〜U-3 の完了・
  物理 query 数の証明・production provisioning は名乗らない。**
- **裁定パッケージ 4 件を返す。** いずれも本 wave の裁定の外側にあり実装していない。
- 逐語と台帳は `output/insights/2026-08-06_t244-p3-u4-candidate-count/`。

## 次の一手差分

### 更新

- [T-244] **P3 は U-4 の記録形分離まで実装済み。U-5 は ledger 成分のみ、本番 provisioning は U-10 未決。P2 は critic 境界の pseudonymization まで。P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **P3**: origin ledger の member 行数と候補数を別 field へ分けた ({{D:u4-member-rows-vs-candidates}})。
  count は `member_row_count` / `distinct_candidate_count` (全 member) /
  `sealed_distinct_candidate_count` (非 tombstone) の 3 つで、いずれも ledger 導出である。
  `BudgetPolicy.batch_distinct_candidate_count_min` (既定 1) を足し、certifiable `OriginSealed` の
  受理で **batch ごとに実行候補の相異数**を検査する。実行候補 0 の batch は gate 対象外。
  既定では受理集合を変えず、狭まるのは authority が 2 以上を明示した場合だけである。
  受入 6779 passed / 20 skipped、変異 14/14 KILLED。
  **予算 codec の包絡線がさらに狭まったので、U-10 の予算値裁定はこの新包絡線を前提にする必要がある。**
  **依頼にあった report v3 と origin-proofs sidecar は実装していない** — ledger に production
  consumer が無く、sidecar の batch / seal / authority field を埋める実 artifact path が存在しない。
  **次は** 8c への wiring (これが済むまで sidecar / report v3 / completeness は起票しない) /
  critic 後置 (U-8) / ever-issued cell 台帳 (U-3) を D96 の同一変更単位で分割 wave として起票する。
  1 wave にまとめない。U-7 は確定済み (cygnus 再測定はせず Pegasus で新規測定)。
  **U-10 (予算値 Imax/Qmax/Kmax/Bmin/floor tuple) は依然 authority 発行の裁定待ちで、
  これが決まるまで本番 authority へ entry を 1 件も書かない。**
  **裁定パッケージ 4 件を返す** (sidecar / report v3 の配線待ち、`sealed_queries` 等
  origin-level row counter の改名、候補数下限の IR 空間上限検査、狭まった予算包絡線)。
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影済み (D192)。
  名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  U-1〜U-3 の完了は名乗らない。前 wave の裁定パッケージ 5 件は依然ユーザー判断待ちである。
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: 055052387902ac279e98f4dd84e2097e07cd4412f1db5d589d36a781fcc57687
