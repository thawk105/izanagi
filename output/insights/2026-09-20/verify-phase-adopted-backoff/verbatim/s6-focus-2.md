## closed 表 (2 巡目)

略号：P＝[paper-story README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/docs/paper-story/README.md)、I＝[記録 insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/output/insights/2026-09-20/verify-phase-adopted-backoff/README.md)、R＝[results 稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md)、W＝[worklog fragment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff/docs/spool/worklog/2026-09-20-dev-wave-verify-phase-adopted-backoff-1.md)。

| 件 | 1 巡目の残る指摘 | 親の 2 巡目対応 (file と節) | 再計算した値 | 判定 | 残る指摘 |
|---|---|---|---|---|---|
| A4 | P の B-8 見出しが未修正で、対応記録と不一致 | P stale 注記4項目目を「関連する追加検証が得られた」に訂正。B-8 の取得済み判定は次版へ留保 | — | **closed** | なし |
| A6 | 重複と worker 停滞仮説が残り、削減は一部のみ | I §10 A6 に「nit、部分適用」の親裁定と維持理由を明記。R §0.3／§4 の構成を維持し、仮説の原因未確定は I §7 項7・R §4 項3にも明記 | — | **closed** | なし。要求は所見への処置の明示であり、削減の全適用ではない |
| A7 | 4063 S を runner job wall と誤記 | I §7 項9・§10 A7、R §4 項9、W 段6で dispatch と runner の計時を区別。上限保証未実装の限定を維持 | runner **4057.876347018 s ≈ 4057.876 s**、dispatch **4063 S**。上限式 **8760 s > 7200 s** | **closed** | なし。上限保証の実装完了を意味しない |
| B2 | 根拠のない「file の mtime は22:20」 | I §10 B2・R §2から削除。作成時刻は自己記載「22:2x JST」に限定。I §5.2・R §3.1のイベント区別と erratum を維持 | 新規再計算なし | **closed** | なし |
| B3 | P に「校正18走」「限定8件」が残存 | P results 表2026-09-20行を「校正18記録（実走16）」「限定9件」に訂正 | 文書内計数：校正12完走＋4未完走＋2未実走＝18記録、実走16。本走込み66記録・実走64。R §4は9項 | **closed** | なし |
| B5 | 出所説明と独立照合済みの区別が不足 | I §10 B5に未照合事項(a)〜(d)を明記。stdout未保存・再現command・旧値の転記元・起点SHAと背景job識別子の出所を記載 | 再実行・独立照合はしていない | **closed** | 処置上はなし。列挙された事項の独立照合は未了のまま |

A7 の根拠は指定の [job.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/calib/fixed-10-write-heavy/job.json) と [dispatch log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/A-fixed-10-write-heavy.log)。request は **10869.nqsv**。

依頼文の計算方法には補足が必要である。`total_wall_s` は存在せず、`stage_wall_s` の和は **4057.564132967 s**。**4057.876347018 s** は `t_end_monotonic − t_start_monotonic` で再計算でき、`job_wall_s` と一致する。段別時間の和とは約 **0.312214051 s** 異なる。

## 1 巡目 closed 7 件の非退行

- A1：**壊れていない**。I §6.3・§10の二版のSHAと判定条件不変の説明を維持。
- A2：**壊れていない**。候補ごと判定集合30件、未完走2件・未実走1件を維持。
- A3：**壊れていない**。適格集合・共通部分 `{3}`、timeout／kill／未実走の区別を維持。
- A5：**壊れていない**。source identityは候補ごと9 job、toolchainは18 jobの範囲を維持。
- A8：**壊れていない**。指定文書の修正に性能比較・過去判定変更への拡張はない。
- B1：**壊れていない**。I §5.3の訂正済みCPU時間とuser／user＋sysの区別を維持。
- B4：**壊れていない**。合計消費12,778／12,473 Sと、本走のみの予算判定を維持。

## 文書間の整合

**なし（指定範囲）。** W の runner wall **4057.9 s** は、I・Rの **4057.876 s** を小数1桁に丸めた値。dispatch **4063 S** との混同も解消している。

## GO / NO-GO

**GO。** 残件6件はすべて closed。1巡目 closed 7件にも退行は認めず、計13件 closed。本判定は指定された段6の文書修正に対するもの。

## 総括

6件とも、1巡目の残る指摘への処置を確認した。
A6は理由付き部分適用、B5は未照合事項の明示として閉じる。
A7は一次資料のjob全体時間とdispatch時間を区別して検算した。
ファイル変更・テスト・測定は行っていない。