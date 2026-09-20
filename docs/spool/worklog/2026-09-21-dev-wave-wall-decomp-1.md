---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-wall-decomp
seq: 1
title: dev-wave 1 本の所要を直近 landed 12 wave の job dir から段別に分解した — impl 7 本では未分類残差 28% > 変異 probe+final 19〜24% > codex 子 16〜17% (受入は docs wave で門番待ち 48 分)、変異 probe の login self-run と final 待ちの段 7 前倒しを DW-M08 / DW-M05 へ収容 (docs のみ、branch worktree-dev-wave-wall-decomp)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。台帳 ID 未起票。一次資料は
  `output/insights/2026-09-21/dev-wave-wall-decomp/README.md` (brief・実測表・相談・裁定・改訂・裁定パッケージ)、専用 handoff は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wall-decomp/HANDOFF.md` (job dir に解析 script と 12 wave の mtime 写し)。
- 起点 local main `285477c00` (fresh worktree、開始 gate rc 0)。軽量版 + 診断 wave の最小 (段 3 相談 1・段 6 独立 read-only レビュー 1 + 焦点再レビュー 1)、docs-only で
  実装面差分ゼロ → Codex author なし (D95 の docs-only 例外)、変異 matrix 免除 (DW-S04)、受入全走は免除しない。
- **段 1 実測 (12 wave = impl 7 / docs 5、2026-09-20 21:18〜09-21 00:21 JST 着地):** 合計 平均 154 分 (65〜215)、impl 170 分、docs 131 分。
  加法分解 (配賦 2 通り) で上位は (1) 子も走も動いていない未分類残差 28%、(2) 受入 = 門番/claim 待ち 15% + 走 13% (docs wave は門番待ち平均 48 分、最大 99 分;
  terminal-postcheck rc=70 の再走 4 回、[T-2273]+[T-2817] の領分で測るだけ)、(3) 変異 probe+final 12〜15% (impl 7 本では 19〜24% で codex 子 16〜17% より上、順位は配賦に依らない)。
  変異は 1 attempt 53 秒 (qsub→ノード開始 20 秒 + ノード上 27 秒 + 後処理 6 秒、pytest 21 秒) で、t2804 final の wrapper 1753 秒 = attempt 1487 + 隙間 111 + 外側 155、pytest 合計は 17%、
  qsub→ノード開始の代理区間 ≥ 5 分が 84 job 中 8 件 (計 63 分、M12 1 本で wrapper の 39%)。
  **この待ちは dispatch receipt に見えない** (D805 が pre-running を RUN へ正規化、queue_wait_s は中央値 5.2 秒) — peer session (job monitoring investigation) の同時刻の観測と一致、帰属は仮説。
- 段 3 相談 A (codex read-only): real must-fix 8 / should 7 / refuted 3 / 判定不能 1。must-fix 8 を全採用 (S1 の台帳訂正、残差の呼称、非加法と順位の配賦依存、PRR の誤記、self-run の適用条件、
  DW-M05 削減の取り下げ、「後は結果値と commit だけ」の撤回、効果算術)。「親は待つだけ」は撤回 (final 中に login 監査あり)。
- **実装 (commit 993d2fc5f + fix 1 6d600f0a6 + fix 2 618fb8501、docs のみ):** DW-M08 に「期待 node は login self-run (変異ごとに注入 → 自走 harness の FAIL / ERROR を観測・正規化 →
  DW-O19 で復元し sha256 も照合) か初回と明記した dispatch probe で集め、erratum・再登録後に dispatch final を走らせる。適用は自走の全 node が `--collect-only` と同形式で照合でき
  login 実行が許される file に限り、pytest 専用 allowlist・parametrize・fixture (conftest / autouse)・環境変数・import 副作用への依存や対応不明は dispatch probe へ戻す」({{D:mutation-probe-login-selfrun}})。DW-M05 末尾に「final の待ちは job dir で確定済み本文と検査の準備に
  充てる (未測定欄・placeholder 禁止)」(CLAUDE.md 作業の進め方 9 の dev-wave 固有の具体化)。byte 予算は D782 手順 1 段目 (tool / CLI が強制する説明句 11 か所の削減) で
  L1.5 9693 → 9681 / 9696、上限不変、義務・停止条件・pin 文は保持 (DW-M05 の独自 harness 同等検査は削らない)、check_docs 違反なし。
- 効果見積り (条件付き、本 wave では実測しない): (a) probe 実施 impl 6 本の probe wall 平均 20.7 分に対し fig13 の self-run は 2 分 (1 file の実績、全 test への適用可能性は未確認)。
  (b) final 終了→受入投入の直列区間 impl 7 本平均 8.3 分のうち準備可能分を 3 分へ寄せられれば 5.7 分 / wave (3.4%)、3 分は未実測。
- 裁定パッケージ候補 (insight §8、実装しない): 変異 job の batching (固定費 28% + 外れ値露出、harness の構造変更)、receipt への qsub→ノード開始の記録 (可視化)、受入門番の緩和 (docs wave 48 分、
  ユーザー裁定事項)、terminal-postcheck の再走 (受入要件)、撤去の占有走査 (1 本 1 分)、dispatcher poll (final あたり 2 分、却下候補)、焦点走の wall と test 時間の差 (上限例)、
  land window 300 秒 (T-2803 が手当て済み、次 wave で再測)。
- 観察: t2344 は fix ごとに別木 3 本 (DW-S05-A「fix は同木で branch」からの逸脱、撤去 +2.5 分)。段 7 記録の前倒しを t2344 は probe 中に既に部分実施。
- 段 6: 独立レビュー A (real must-fix 3 / should 8 / nit 1 / refuted 3 / 判定不能 2 + 削減 11 句の個別判定) NO-GO → fix 1 (適用条件を「全 node の照合可能性」と「変異ごとの FAIL / ERROR 観測」に分離、
  erratum・再登録と「変更前 HEAD 版」を復元) + 記録訂正 → 焦点再レビュー A (DW-O16 対応表、派生値は原データから再計算で一致) NO-GO 残 3 件 (probe 経路の明示・§9 の値なし参照・削減 (8) の説明)
  → fix 2 と記録訂正で親が閉じた (2 巡、3 巡上限内。根拠は insight §10)。
- 検査: check_docs 違反なし (3 commit)、message-file 検査 rc 0、全史 provenance 監査 12182 / 12183 / 12184 件 新規違反なし (login 14〜17 秒 = T-2803 の warm 化)、焦点走 test_check_docs.py
  (login bounded local は cap-oom で dispatch へ退避) 14042.nqsv 580 passed / 3 skipped wall 57 秒、14110.nqsv 580 passed / 3 skipped wall 17 分 40 秒。**14110 は qsub 01:59:36 → ノード開始 02:16:25 の
  16 分 49 秒を qstat が PRR と表示し、dispatcher log は RUN、receipt は queue_wait_s 5.2 秒** — 段 1 の推定 (D805 の正規化で待ちが receipt に見えない) を本 wave 内で receipt 付きで追認 (insight §4)。
  受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し受領証は job dir と land の記録が持つ。
- 言わないこと: 12 本は同じ夜の連続帯の標本で別日を代表しない。成分は並走で重なるので成分の削減がそのまま合計の削減にならない。qsub→ノード開始の代理区間を PRR と断定しない。
- 事故 (自分起因、実害なし): handoff と brief の時刻を推定で書き (01:47 / 01:50 / 01:30)、mtime と date で訂正した (記憶 timestamps-from-date-or-mtime の再発、F 起票なし)。
- 工数: codex 3 本 (consult 1・review 1・focus 1、gpt-6-astra)、計算ノード job = 焦点走 2、login = 全史監査 3・解析 script 10 本 (job dir、sha256 は insight verbatim/scripts.sha256)。

## 次の一手差分

### 新規

- {{T:mutation-job-batching}} **P2・ユーザー裁定待ち**: 変異 final の 1 dispatch job = 1 変異 (t2804 final で attempt 代表値の和 33.5 秒 / attempt、pytest は wrapper の 17%、qsub→ノード開始の代理区間への露出 N+2 回) を、1 job で baseline + N 変異を順次 apply / restore する形へ変えるか。harness の receipt 束縛 (1 job = 1 変異) の構造変更で、DW-M05 / M07 の契約と fail-closed を保つ設計が先。一次資料は `output/insights/2026-09-21/dev-wave-wall-decomp/README.md` §4・§8。
- {{T:dispatch-receipt-prerunning-visibility}} **P2・新規**: dispatch receipt の queue_wait_s が NQSV の pre-running を含まず (D805 の正規化)、qsub→ノードで script 開始までの待ち (84 job 中 8 件 ≥ 5 分、計 63 分) が receipt に見えない。request.json と compute-visible.json の mtime 差を receipt の field として記録する設計 (正規化は変えない)。peer session の観測と本 wave の検算 (同 README §4、`verbatim/prr_check.txt`) が一次資料。
