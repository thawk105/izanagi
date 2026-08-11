---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-testops-observation
seq: 1
title: TestOps 導入依頼は既存の task-run 台帳が契約どおり凍結された状態だと判明し実装しない裁定にした — 再開は D66 が予約したユーザー裁定事項 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-testops-observation)
---

## 本文

**ユーザー裁定 (wave 冒頭).** 依頼「TestOps をこのリポジトリに導入してください」の TestOps が
リポジトリ内で未定義だったため、段 1 前に scope を諮った。選択肢は (A) 自前のテスト運用観測層 /
(B) 外部 TestOps 製品 (Allure・Katalon 等) / (C) テスト選択・影響解析 / (D) 別の具体。
**ユーザーは (A) を選択**。(B)(C) は scope 外として扱った。

**実測で前提が覆った。** (A) に相当するものは既に実装済みで、かつ契約どおり凍結されていた。
機序・数値・逐語は `output/insights/2026-08-12_testops-observation/`。要点だけ再掲すると、
台帳には task run 10 件・event 69 件が残り最終 event は 2026-07-21T20:33:39Z、以後 21 日間
新規記録ゼロ。止めているのは final marker・max_task_runs 到達・max_days 超過の三重の構造的拒否で、
これは事故ではなく D66 の pilot 契約そのものである。

**段 3 の敵対相談は両レンズ独立で NO-GO。** blocker 計 10 件のうち親が 1 件を refuted とした。
refuted は「sidecar の I/O 例外が pytest の rc を壊す」で、conftest が 3 hook すべてを
`try/except Exception` で包んでいるため成立しない。子がこれを見落としたのは、親が読む範囲の
名指しに conftest を含めなかったためであり、子の失点ではない。

**親自身の実測でも 1 件出た。** 段 2 プランの既定記録先は `XDG_STATE_HOME` 未設定の実機で
home 配下に解決され、2026-08-03 / 08-04 のユーザー是正 (作業ファイルは `/work` 配下) に反する。

**「実装しない」と裁定した理由は 3 つで、いずれも親が単独で解けない。** (i) 観測の再開そのものが
D66 が明示的にユーザー裁定へ予約した事項であり、wave 冒頭の scope 選択は無期限 rollover の
承認ではない。(ii) 記録先の択一が threat model を変える — D66 は hash chain を作らない代わりに
tracked file の git 履歴を改竄検出の外部 anchor にしており、repo 外化はそれを失う一方、repo 内に
留めれば走行ごとの untracked が並行する全 wave の clean-tree gate を壊す。(iii) blocker 9 件を
安全に閉じるとプランの 142 行見積りが成立せず、D220 が過大として不採用にした水準へ近づくため、
規模自体が D205 の判断を要する。

設計判断は {{D:testops-observation-frozen-pilot}}。

## 次の一手差分

### 新規

- {{T:testops-observation-restart}} **P1・ユーザー裁定待ち**: テスト運用観測を再開するかを
  3 点セットで裁定する。Q1 = 再開の可否と形 (有界の次世代 pilot / 無期限の常設計装 / 再開しない)、
  Q2 = 記録先と改竄検出 anchor (repo 外の repo 兄弟 / repo 内 tracked / 両取り)、
  Q3 = 被覆する実行経路の定義 (`tools/run_tests.py` 経由のみ / conftest 計装で全 pytest)。
  親の推奨はいずれも第 1 案。選択肢の詳細と代償は
  `output/insights/2026-08-12_testops-observation/verbatim/s4-ruling.md` §3。
  裁定が (再開する) なら、同 insights が凍結した blocker 9 件と must-fix 11 件を閉じる plan v2 から
  実装 wave を起こす。
