---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-p5-u1-drive-preview
seq: 2
title: [T-244] D121 P5 U-1 を実装した — claude-headless の run_trial が explicit keyword の drive / preview 注入を拒否し、既存 2 テストは module seam へ移行 (コード + docs、branch worktree-dev-wave-t244-p5-u1-drive-preview)
---

## 本文

- **U-1 の実装 wave。** 裁定の正本は worklog の /rulings 記録 (U-1〜U-3) で、設計判断は
  {{D:u1-driver-injection-rejection}} に記録した。U-2 (未予約 token) は並行 wave が再設計中の
  P3 origin ledger の予約 receipt に依存するため scope 外、U-3 は「要求しない」裁定で実装なし
- **段 3 の敵対 2 レンズが親 plan の中核を 2 点で覆した。** (i) 移行先の module 属性 seam は
  拒否対象の explicit keyword と同能力を同一 process 内で持ち、sentinel も introspection で
  持ち出せる — 名乗りを「public run_trial の explicit keyword admission の縮小」へ限定し、
  残存経路は機械対策を装わず docs へ全列挙する方針に変えた。(ii) 状態付き str subclass が
  provider 判定を選別的に迂回できる — exact 型検査を gate 前へ追加した (D114 の int subclass
  先例)。brief の実測 2 件も訂正された (P5-1 境界テストの実所在、fixture 注入の call 数)
- **段 6 の敵対レビュー 2 本が境界テストの穴 3 種 (do_build=True 経路、preview 非 callable、
  敵対的 __eq__ による識別弱体化) と、変異登録の期待 node 不整合・mask (M9/M10/M11) を検出した。**
  fix で負例 5 種と復元 identity assert を追加し、変異 spec は runner scope を
  test_role_session_isolation.py 単独に固定して全 13 変異の期待赤集合を実 nodeid で網羅登録した。
  焦点再レビューの対応表は closed 11 / partial 2 / regressed 0 (partial は docs 列挙と本記録で閉じた)
- **変異 matrix (M1〜M13、spec sha256 f61e179b…) は 13/13 KILLED、期待赤集合と完全一致。**
  anchor = 実装 commit と main merge 後の 9fa82ef、runner scope =
  `test_role_session_isolation.py` 単独 (baseline 36 passed)、harness = `tools/mutation_harness.py`
  (dispatch mode)。M9/M10 の期待集合は速記の「単一 node」でなく実挙動から網羅導出した値
  (7 / 16 node) で登録し、そのとおり赤になった。M11 は「解決の遅延」の忠実な textual 変異が
  構成できず **M5+M6 同時の両層変異へ事前再照準** (DW-M02) して kill を確認した。
  台帳 = 同 insight dir の `mutation-ledger.json`
- **受入 (2026-08-04、worktree `dev-wave-t244-p5-u1-drive-preview`):** main 864613d 取り込み後の
  tree (merge 9fa82ef) で `tools/run_tests.py` 全走 = **5555 passed / 19 skipped / 0 failed**
  (計算ノード dispatch 887793.nqsv)。`check_ai_provenance.py` full 監査 = 違反なし (887808.nqsv)。
  `check_docs.py` = 違反なし。最終の local main 取り込み (e849c83 → merge 68dd30d) 後は
  docs 検査と対象 4 test file (= 224 passed) を再走して閉じた。走行中に Pegasus バッチ系が
  約 1 時間全 queue INA で停止し (gen_S 230 QUE / RUN 0)、回復後に変異・受入を実施した
- **段 8 の自己改善候補 1 件は docs/dev-wave 予算 (25,200) が塞いだ (25,196 で残 4 bytes、
  (150)(169)(170) と同型の 4 例目)。** 候補 = DW-M05 へ「harness の --spec / --out は試験対象
  checkout の外に置き、台帳は本走後に insight へ複写する」の 1 行 (本 wave で preflight abort を
  1 回踏んだ。handoff の再開手順に書いた repo 内 path のままでは起動できない)。解決経路は
  [T-328] 裁定 (c) の [T-313] 先行のため実装せず記録のみ
- 工数: codex 子 6 本 (plan 1 / 敵対レンズ 2 / 実装 1 / fix 1 / 焦点再レビュー 1)。
  実装 commit 5df1f9c、local main 864613d の取り込み merge 9fa82ef

## 次の一手差分

### 更新

- [T-244] **P1・P3+P4 実装 wave 起票可 (U-A〜U-G / W1〜W5 裁定済み)。P5 は U-1 実装済み、残余は U-2 のみ**:
  **P4**: D153 の設計択一 5 件は 2026-08-04 の /rulings で **W1〜W5 全件が推奨どおり裁定済み** —
  W1 実装先 = P3 実装 wave 内で第一級 batch event として設計 / W2 member identity =
  query/replicate ordinal 込み / W3 結果は evidence digest へ束縛 / W4 abort 時は tombstone で
  公開 transcript 長を固定 / W5 origin-total は ledger 計数 + authority receipt 由来 policy のみ
  受理 (class referent の検証は P7 consumer 側の義務)。独立 leaf 実装の差し戻し理由
  (二重実装 / 非発火 prototype / member identity 未定) は D153。
  **P4 実装・充足は実装 wave 完了まで名乗らない。**
  逐語 = `output/insights/2026-08-04_t244-p4-batch-freeze/`。
  **U2**: D150 が「実装が無いゆえの非適用」を cap-lift の失敗と定め、
  択一 3 の既裁定により **P4 を条件付き義務から無条件義務へ移した** (無条件義務は
  P1・P2・P3・P4・P5・P7・P9・P10 の 8 件)。条件付き義務は P6 だけになり、非適用は
  `NOT_IMPLEMENTED` = 失敗 / `NOT_CLAIMED` = 免責の 2 語に固定した。状態の分類 (事実) と
  承認の可否 (判断) を分け、認定基準が無い間は状態を再分類せず承認を保留する。
  **V1 (`NOT_CLAIMED` の射程 = global 免責か per-run gate か) は P6 実装の裁定と同時に決める**
  (2026-08-04 /rulings で既定方針を追認済み)。V2=[T-433]、
  V3=[T-434]、V4=[T-435] を前提として追跡する。
  **前提条件 10 件のうち満たされているのは P10 (予算値・origin authority・軸 (iii)) の 1 件だけ。**
  **P1**: `orchestrator/campaign/reflux_ir.py` (固定 5-bit IR・正準 wire codec・正準 C++ emitter) と
  独立 golden 32 点、テストを land した。**production へ wiring しないため候補表現は閉じておらず、
  受理集合は任意の 1 行 C++ のまま**で production 到達性はゼロである。次段は wiring wave
  (自由 `implementation` の拒否、wire→mask→predicate の唯一経路化、raw mask と source digest /
  variant ID の束縛、WAL/provenance/report での同束縛、binding 欠落 artifact の proof chain からの拒否)
  で、**受理集合の縮小なので D96 手続が要る**。
  **P5**: provider 注入の拒否と role 間 session 共有の拒否 (D148) に加え、**U-1 を実装した** —
  正式経路の `run_trial` が explicit keyword の `drive` / `preview` 注入を artifact 作成前に
  拒否し ({{D:u1-driver-injection-rejection}})、これに依存していた transport テスト 2 件は
  module 属性 seam へ移行、provider kind は exact plain str に限定した。拒否は explicit keyword に
  限り、sentinel 持込み・module 再束縛・wrapper / partial・事後判定は保証外のまま
  (「P5 第 1 要件を閉じた」とは名乗らない)。**P5 の残余は U-2 (未予約 token) だけ**で、
  P3 実装 wave の予約 receipt に依存する (自前 token は発明しない)。U-3 は「要求しない」裁定で終結。
  **P3**: (165) の裁定パッケージは 2026-08-04 の /rulings で **U-A〜U-G 全件が親推奨どおり
  裁定済み** — U-A origin_id を authority manifest digest へ束縛 / U-B cell key で同一 cell の
  2 件目を拒否 / U-C authority root 単一固定 (注入は test fixture に限る) / U-D batch 第一級 /
  U-E committed bytes 照合 (static authority record と mutable runtime head の分離込み) /
  U-F floor 必須化 / U-G 充足は producer 結線と P7 まで含めて数える。
  **P3+P4 の実装 wave を起票できる** (変異事前登録候補 6 件と W2〜W5 の設計指定を
  同 wave の設計入力にする)。
  一次控えは rulings-inbox 2026-08-04。
  **cap-lift は依然 FAIL** で D114 の上限 1 も不変。P2 / P7 / P9 は未着手。
  逐語は `output/insights/2026-08-04_t244-p1-ir-emitter/`、
  `output/insights/2026-08-04_t244-p5-injection-gate/`、
  `output/insights/2026-08-04_t244-p5-u1-drive-preview/`、
  `output/insights/2026-08-04_t244-u2-na-bifurcation/`、
  `output/insights/2026-08-04_t244-p4-batch-freeze/`
  base: 0187542fc54a8ebb94db12c72c97c2d8fbbeba6ca129e385be91d63d29ed4af8

### 見送り追記

- [T-290] 2026-08-04 の U-1 実装で public run_trial の explicit keyword 注入部分は消化 (直接反復は D114 のとおり保証外のまま)。
