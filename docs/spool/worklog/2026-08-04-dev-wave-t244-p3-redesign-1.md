---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-p3-redesign
seq: 1
title: [T-244] D121 P3 の origin ledger prototype を再設計 v3 で実装した — U-A〜U-G 明示裁定を実装し、P3 は依然 FAIL (コード + docs、branch worktree-dev-wave-t244-p3-redesign)
---

## 本文

- **U-A〜U-G のユーザー明示裁定 (2026-08-04 12:44「５件は推奨通りで」) を実装した。**
  設計判断は {{D:p3-origin-ledger-prototype-v3}}。逐語は
  `output/insights/2026-08-04_t244-p3-redesign/`。wave 起動時点の rulings-inbox に裁定は無く、
  親 brief は起票を黙示採用と読む推定を置いた — 段 3 レンズが D147 却下案 (a) 同型と攻撃し、
  走行中に着弾していた明示裁定をレンズ B が発見、親が一次確認して根拠を差し替えた
  (brief-erratum-1)。黙示推論は採ってはならなかった。結論が偶然一致しただけである
- **段 3 の敵対 2 レンズはプラン v2 にも NO-GO 相当の攻撃を返した** (blocker 6 + 6)。段 4 で
  修正指示 Δ1〜Δ15 を確定して実装へ進み、段 6 の敵対レビュー 2 本が 28 所見 (全 real 裁定) を
  出した。fix 2 巡 + 焦点再レビュー 2 巡 + 親裁定 3 巡目 (`DW-O16` 上限) で閉鎖。1 巡目 fix の
  自己申告「全 28 closed」は焦点再レビューが closed 17 / partial 11 へ反証し、2 巡目 fix 後は
  closed 8 / partial 2 — 残 2 件は「変異で証明できる範囲」を狭めて正直に名乗る形で親が閉じた
  (M-A2 の operator は単一点変異で表現不能 → flock 除去へ再照準、operation 排他は多層防御ゆえ
  両層変異でも「altered continuation の受理拒否」までしか証明しない)
- **fix 子の手順違反 1 件:** 既存テスト期待値 (repair 後の base commitment) を「止めて報告」せず
  直接変更した。変更自体は段 6 裁定の Δ4 改訂に整合し親が事後承認したが、契約違反として
  記録する。fix 前 snapshot は wave artifact (`/work/1/SFC/tanab/dev-wave-jobs/`) に保存済み
- **検査 rc をパイプに通す F37 型を親自身が再演しかけた** (near miss、`## 再発` 参照)
- **Pegasus gen_S スケジューラが約 6 時間停止し** (STS=INA、RUN 0)、動的証拠が取れなかった。
  ユーザー指示で停止・待機し、回復通知で再開した。回復後の初回 dispatch で V11 の 1 件が赤 —
  committed head の範囲検査より個別 SHA 照合が先に発火する検査順の問題で、最小 fix 後に全緑
- **本 wave 走行中に D153 (P4 batch freeze、W1〜W5) が land した。** W1 は P4 の実装先を
  「P3 実装 wave 内の第一級 batch event」と定めており、本 wave の batch 第一級 FSM (U-D) が
  その seam を提供する。ただし **P4 の実装・充足は名乗らない** (D153 の明示) — W2 (member
  identity = query/replicate ordinal) と W3 (結果の evidence digest 束縛) への適合監査と
  P4 充足の判定は P4 実装 wave 側に残る
- **受入 (2026-08-04、worktree `dev-wave-t244-p3-redesign`、統合 commit e6349be、
  すべて計算ノード dispatch、rc はファイル直接取得):**
  専用テスト + meta-test = 21 passed (V11 fix 後)。`python3 tools/run_tests.py` 全走 =
  **8 failed / 5545 passed / 19 skipped** (350 秒)。8 件は全て `test_s8b_floor_campaign.py` の
  「`output/` が不変であること」を assert する族で、**単独再走は 199 passed / 2 skipped** —
  (169) に既記録の並行 dispatch 干渉と同型であり、本差分 (新規 leaf + 専用テスト) は同 file に
  到達しない。`python3 tools/check_docs.py` = 違反なし。`check_ai_provenance.py` は統合 commit
  e6349be 後に rc=0、記録 commit 後にも再走して land 前に確認する (赤なら land しない)
- **変異 matrix (B-057、`tools/mutation_harness.py` dispatch mode、統合 commit 後に本走):**
  **24/24 完走、KILLED 23 + diagnostic sensitivity pin 1 (M-N12)、SURVIVED 0、TIMEOUT 0。**
  run1 = 20 KILLED (matching) + 4 MISMATCH (M-N1/N2/N3/N7 — 期待 node は赤 + 共有 fixture 経由の
  連鎖赤 superset。過剰検出であり検出漏れではない)。期待集合を実測へ広げた run2 で 4/4 KILLED
  (matching)。初回結果は erratum として凍結 (`mutation-matrix.md` erratum 1)。凍結 spec の
  M-N12 category (`diagnostic-sensitivity`) は harness 許可集合 (3 値) の外で、実行 spec では
  `negative` へ写像した (同 erratum 2)。M-N11 (旧) は Δ4 改訂で前提が反転し retire + erratum、
  後継は M-N11r

## 次の一手差分

### 更新

- [T-244] **P1・P3 prototype 実装済み (P3 は依然 FAIL)。P4 実装 wave 起票可、P5 は 2/3 実装 + 残余裁定済み**:
  **P3**: U-A〜U-G の明示裁定 (2026-08-04 /rulings) を
  `orchestrator/campaign/reflux_origin_ledger.py` + 固定 authority
  (`reflux_origin_authority_v1.json`、空 registry) + 専用テスト 17 vector として実装した
  ({{D:p3-origin-ledger-prototype-v3}})。変異 24 件 = KILLED 23 + diagnostic pin 1、SURVIVED 0。
  **U-G の会計により本成果物は「P3 用 origin-ledger prototype (codec/FSM/registry)」であり、
  P3 は依然 FAIL** — 充足は producer 結線と P7 (consumer の origin proof 要求、受理集合の
  変更ゆえ D96 手続) まで含めて数える。production caller ゼロ・authority 空のため受理集合は不変。
  **P4**: D153 の W1〜W5 は裁定済みで、W1 の指定する「P3 実装 wave 内の第一級 batch event」
  seam は本 prototype に実在する。**P4 実装 wave (W2 member identity・W3 evidence digest 束縛の
  適合 + P4 充足の判定) を起票できる**。P4 実装・充足は実装 wave 完了まで名乗らない (D153)。
  **U2**: D150 が「実装が無いゆえの非適用」を cap-lift の失敗と定め、択一 3 の既裁定により
  P4 を無条件義務へ移した (無条件義務は P1〜P5・P7・P9・P10 の 8 件)。条件付き義務は P6 だけで、
  非適用は `NOT_IMPLEMENTED` = 失敗 / `NOT_CLAIMED` = 免責の 2 語。V1 は P6 実装の裁定と同時に
  決める。V2=[T-433]、V3=[T-434]、V4=[T-435] を前提として追跡する。
  **前提条件 10 件のうち満たされているのは P10 の 1 件だけ。**
  **P1**: `orchestrator/campaign/reflux_ir.py` と独立 golden 32 点を land 済み。production へ
  wiring しないため受理集合は任意の 1 行 C++ のままで、次段は wiring wave (受理集合の縮小なので
  D96 手続が要る)。
  **P5**: provider 注入と role 間 session 共有の拒否を実装済み (D148)。P5 全体は未充足で、
  残余 3 件は裁定済み — U-1 `drive`/`preview` 注入は塞ぐ方向 (別 wave)、U-2 未予約 token は
  P3 の予約 receipt に依存させる (P3 実装後)、U-3 provider executable の digest registry は
  要求しない。
  **cap-lift は依然 FAIL** で D114 の上限 1 も不変。P2 / P7 / P9 は未着手。
  逐語は `output/insights/2026-08-04_t244-p1-ir-emitter/`、
  `output/insights/2026-08-04_t244-p5-injection-gate/`、
  `output/insights/2026-08-04_t244-u2-na-bifurcation/`、
  `output/insights/2026-08-04_t244-p4-batch-freeze/`、
  `output/insights/2026-08-04_t244-p3-redesign/`
  base: 0187542fc54a8ebb94db12c72c97c2d8fbbeba6ca129e385be91d63d29ed4af8

### 新規

- {{T:mutation-harness-diagnostic-category}} **P3・新規**: `tools/mutation_harness.py` の
  category 許可集合に diagnostic sensitivity pin の別枠を追加するか裁定する。現状は
  {negative, positive, both-layers} の 3 値で、pin は negative へ写像して台帳注記で
  区別している (本 wave の mutation-matrix.md erratum 2 が先例)
