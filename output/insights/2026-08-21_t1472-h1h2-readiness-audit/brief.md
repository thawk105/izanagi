# 段1 brief — T-1472 formal H1/H2 workload campaign readiness audit

**scope**: H1/H2 (rr80/rr20 × on/off/swapped, 8b-descriptor-design.md 発効 2026-07-16) 正式実験の
起票可否を現行コード・decisions・worklog・receipt と照合し、欠落を blocker table として
`output/insights/2026-08-21_t1472-h1h2-readiness-audit/README.md` へ出す。**zero-diff** —
実装面ゼロ、approval bytes 生成・裁定代行・実験起動・結果推測は禁止。Rule 2 と登録済み条件は変更しない。

**確定済みユーザー裁定/事実 (直接一次資料で確認済み)**:
- 2026-07-16 承認: H1=rr80/H2=rr20 (skew=0.9,rmw=0,1m/48thr)、on/off/swapped 定義 (8b §3-4)。
- 2026-08-10 scope-B 裁定: 8b 再開/floor実測/oracle実走は Q3 ガード (ノード単独性・T-139 pilot/本走中は
  キュー投入控え・裁定帯域は T-139 優先) 下でのみ許可。
- 2026-08-18 再凍結 (8b §10, D496 系): floor 判定方式を「対象別 floor 超過」から「同一 campaign 内
  paired 差分統計」へ変更。**仕様のみ発効、判定器/attempt registry/judge の実装は別 wave 待ち
  (epoch境界、8b§10.6・8c-prereg§本文で明記)。**
- 2026-08-20 T-425 再監査 (worklog archive-731、一次資料 = insights/2026-08-20_t425-dependency-reaudit):
  「公式 H1/H2 起票は T-424/T-272 要求閉包 or D145決定5再訪、かつ rr80/rr20 較正登録 (human lockstep)
  まで不可」——この結論は当日時点で不変と明記。between_run_floor.py の code-only 準備のみ独立着手可。
- 8c-preregistration.md §6/§7 (現物, 第8世代 s8c-decider/v4): 12前提条件のうち機械的に「充足」を
  返す評価器経路が**1本も無い**。§5 の実走前必須記入欄9項目中8項目が未記入 (検定4点のみ記入済み=
  no_hypothesis_test)。**§7 末尾が「本節の起動形は現時点の production では実行可能ではない」と明記。**
- D356 (2026-08-13): oracle spec の人間承認は機械強制されていない。機械が確認できるのは
  「人間が staged diff を review した」までであり、それ以上を「機械確認した」と書いてはならない。

**不変条件**: 絶対規律 (特に1-3)、Rule 2、登録済み preregistration 条件・凍結を一切変更しない。
このwaveは調査・記録のみ。人間の lockstep (rr80/rr20較正登録、D145再訪、T-424/T-272閉包など) 完了は
別wave/別セッションの責務。

**成果物の形**: (1) `README.md` — blocker table (項目×現状×根拠file:line×次の一手) を主体とする本体。
(2) `verbatim/s2-plan.md`, `s3-lensA.md`, `s3-lensB.md` — codex 記録。(3) `s4-adjudication.md` — 親裁定。
docs-only, 実装面ゼロ。

**並列分割方針・(P1)**: 実装面が無いため段5/6 Codex実装子は不要 (DW-C00 docs-only 子ゼロ可)。
段4で「実装しない」裁定なら `4→7→8→9`。**(P1: provisional)** 段2 codex plan + 段3 敵対2レンズ
(sol/luna) は DW-C00 の軽量化免除 (正しさ防壁/受理集合非該当) が形式上成立しうるが、T-425 前例
(同型 docs-only 依存監査で実際に codex plan+consult が親の見落とし複数を検出) に倣い**実施する**。
理由: 本監査の結論が正式実験起票という不可逆性の高い人間判断を左右するため、追加コストを払う。

**(P2: provisional 暫定結論、攻撃対象)** H1/H2 正式実験は現時点で起動不可能 — 8c-preregistration.md
自身の明記、12条件中充足を返す経路ゼロ、8b floor 判定方式が仕様のみ発効で実装待ち、が根拠。

**(P3: provisional)** T425/T972(×2)/T1371/T1438/T1458 は全て稼働中または未クローズ (ListAgents実測+
worklog次の一手(795)持ち越し) であり、H1/H2前提コンポーネント (floor/oracle-prewarm/official-run-root/
noncertifying-consumer/perf-preflight-receipt) の実装作業と重複する。command 指示どおり実験を
起動しない (そもそも本waveはread-only監査であり起動権限を持たない)。

**(P4: 未確認事項、blocker table に「要再確認」として明記)** T-139 の pilot/本走の現在状態と、
scope-B 裁定 fragment (2026-08-10-rulings-20260806-a-38, commit 051551dd) の land 状況は、
fork 側の環境障害により未確認のまま。
