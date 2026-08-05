---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t244-p2-noninterference
seq: 1
title: [T-244] P2 の critic 境界へ campaign-local pseudonym を入れた — 19/19 KILLED で漏洩チャネル 10 本の閉鎖を実測し、名乗りは pseudonymization までに留める (コード + docs、受入 6681 passed / 20 skipped、変異 19/19 KILLED、branch worktree-dev-wave-t244-p2-noninterference)
---

## 本文

- **段 3 の敵対 2 レンズが独立に NO-GO を返し、段 2 プランの中心設計を 4 点否定した。** 親は全 19 所見を
  real/refuted に裁定し、「実装しない」ではなく **scope を縮小して実装する**と決めた ({{D:critic-candidate-label-projection}})。
  否定された 4 点は (a) 到達不能な fixture と fake renderer で baseline-red を人工生成していた、
  (b) 公開入力に候補依存の実行結果を入れる循環定義、(c) 射影を opt-in にしたため現役 consumer
  7 箇所が生 ID のまま残る、(d) 「origin scope の不透明 ID」は authority が空のため実装不能。
- **(d) について親は停止せず、実装可能な読みを採った。** authority が `origins: []` である事実は
  裁定より前の worklog に既記録で、`DW-S04` が停止を許す「裁定時点で未見の新事実」に当たらない。
  campaign-local pseudonym として実装し、**U-1 の完了は名乗らず**解釈の確定を裁定パッケージへ返した。
- **親 brief の前提実測 M2 が 2 点誤っており、段 2 と段 3 が独立に是正した。** verify-abort 節を
  screening と誤記し、liveness `extra` の `build_attempt_id` と
  `build_admission_receipt_sha256` という識別子チャネル 2 本を棚卸しから落としていた。
  実装はレンズ B の棚卸しに従っている。
- **段 4 裁定のうち 1 件を段 6 で実測により撤回した。** 「対応する `BUILD_START` の無い非空候補 ID を
  例外で拒否する」と裁定したが、これは public な exploratory / custom drive 経路の受理集合を狭め、
  既存 `test_claude_transport.py` 3 件を `complete` → `partial` に落とした。親 brief 自身の不変条件
  「現行の受理集合を狭めない」に反するため、候補非依存の固定 sentinel への射影へ変更した。
- **段 6 のレビュー 2 本も独立に NO-GO で、must-fix が 7 件収束した。** 最重要は
  **「意図して開示する情報」の除外が行の見出し一致で理由・証拠を無条件に削除する実装になっていた**こと。
  これでは証拠欄に候補由来の値を流す漏洩が起きても検査は緑のままである。除外を宣言駆動へ直し、
  **証拠欄へ候補由来値を入れると赤くなる負例**を置いた。これがこの検査が恒真でない唯一の証拠である。
- **fix は 5 巡かかった。** 赤の推移は 3 → 13 → 2 → 2 → 0 で、13 への増加は consumer 回帰 2 file を
  検査範囲へ加えたためである。第 1 巡が既存 2 テストの正例被覆を後退させており (F80 再発)、
  受入が緑のままだったため実走では気づけず、**焦点再レビューが現物比較で検出した**。最小巡で戻した。
- **変異は事前登録 19 件で、本走は 19/19 KILLED・node 完全一致・SURVIVED 0。**
  初回走行は 10 件が MISMATCH だったが、すべて actual ⊋ expected で**親の登録が狭かった**側の誤りである
  (F87 再発)。初回台帳は消さず erratum として残した。静的レビューが「帰属不成立」と疑った
  M15 (IR 変更検出器の golden 項) は、実測で狙いどおり golden 側の検査が落ちると確認できた。
- **名乗りの上限を段 4 で先に固定した。** 名乗ってよいのは campaign-local pseudonymization、
  宣言済み declassification を除いた critic sink 等価性の regression 検査、auditor 開示の自己申告
  annotation、IR emitter・golden の変更検出 ID まで。**origin-scope ID・non-interference・
  indistinguishability・P2 の充足・cap-lift・build 経路の閉鎖・proof chain 保全・U-1〜U-3 の完了は
  名乗らない。** 前 wave の real 所見のうち production 側の evidence 経路・payload 外観測・
  terminal report 経路は open のまま残る。
- **scope 外の real 所見を裁定パッケージ 5 件として返す。** いずれも本 wave の裁定の外側にあり実装していない。
- 受入全走は Pegasus 計算ノードで **6681 passed / 20 skipped** (request 892239.nqsv、1032.67s)。
  焦点 9 file は fix 後 615 passed / 0 failed (request 892135.nqsv)。
  変異は固定 HEAD `9b687e68` に対して走らせ、走行後の作業ツリー復元も確認した。
- 逐語と台帳は `output/insights/2026-08-06_t244-p2-noninterference/`。

## 次の一手差分

### 更新

- [T-244] **P2 は critic 境界の pseudonymization まで実装済み。ただし U-1〜U-3 の完了は名乗らない。P3 は U-5 の ledger 成分まで実装済みで本番 provisioning は U-10 未決。P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影し、
  critic-facing API では射影を必須にして production の全 consumer を移行した
  ({{D:critic-candidate-label-projection}})。auditor 開示は sunset 条件つきの自己申告 annotation として
  会計し、IR emitter と 32 golden の複合 digest を checkout 限定の変更検出 ID として production 定数に置いた。
  role payload の schema 版を上げた (report 版は据え置き)。宣言済み declassification を除いた
  critic sink 等価性の regression 検査を新設し、非空虚性の負例を同時に置いた。
  **名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  U-1〜U-3 の完了は名乗らない。** 残る open は production の diff-quarantine evidence が
  候補由来の短縮 hash を載せる経路、payload 外の観測面、terminal report 経路である。
  **裁定パッケージ 5 件を返す** (U-1 の解釈確定、declassification の gate 化と report v3、
  IR identity の artifact 搭載、liveness `extra` の閉集合化、critic CLI の diff-quarantine 欠落)。
  **P3**: reservation FSM を実装した (D189)。予算消費点が
  `BatchCommitted` 受理時から予約受理時へ移り、予約が必須、放棄は無返却で forfeit へ計上、
  予約中 origin の復旧面を公開、query / iteration partition を全受理枝で検査、
  codec feasibility を 4-frame へ更新。受入 6647 passed / 20 skipped、変異 7/7 KILLED。
  **U-5 は未完である** — (c) の caller 制御流は本番 authority entry を要し、U-10 未決のため
  D183 が禁じている。**この依存は分割一覧に未記載だった (裁定パッケージで返す)。**
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。予約は候補生成回数を束縛せず、束縛するのは commit できる
  member 行数と予算 counter だけである。**予算 feasibility の包絡線が狭まったので、
  U-10 の予算値裁定はこの新包絡線を前提にする必要がある。**
  **次は** report v3 / origin-proofs sidecar (U-4 の field 分離を含む) / completeness /
  critic 後置 (U-8) / ever-issued cell 台帳 (U-3) を D96 の同一変更単位で分割 wave として起票する。
  1 wave にまとめない。U-7 は確定済み (cygnus 再測定はせず Pegasus で新規測定)。
  **U-10 (予算値 Imax/Qmax/Kmax/Bmin/floor tuple) は依然 authority 発行の裁定待ちで、
  これが決まるまで本番 authority へ entry を 1 件も書かない。**
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: 96033dd68bccfe865d4ecd029baa390fe8ef70e93444fcca6f48a058955c81e8
