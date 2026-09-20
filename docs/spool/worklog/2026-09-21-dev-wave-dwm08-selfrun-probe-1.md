---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-dwm08-selfrun-probe
seq: 1
title: 変異 probe の login self-run 手順を DW-M08 へ収容する依頼は D2195 (entry 1774) として着地済みだった — 未被覆 3 要素 (注入先・起動方法・復元後の `--porcelain` 空) と skip の名指しだけを純増として同節に収め、同節の空白・改行を詰めて L1.5 予算内 (上限不変) に収容 (docs のみ、branch worktree-dev-wave-dwm08-selfrun-probe)
---

## 本文

- ユーザー依頼 (2026-09-21、/dev-wave 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。台帳 ID 未起票。一次資料は
  `output/insights/2026-09-21/dev-wave-dwm08-selfrun-probe/README.md` (brief v1/v2・被覆表・レビュー逐語・裁定)、専用 handoff は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dwm08-selfrun-probe/handoff/` (背景 job 57f119fa、repo 外)。
- 起点 local main `5efd69367` (fresh worktree、開始 gate rc 0、07:35 JST)。軽量版 (段 2・3 省略、段 6 独立 read-only レビュー 1 + 焦点再レビュー 1)、
  docs-only で実装面差分ゼロ → Codex author なし (D95 docs-only 例外)、変異 matrix 免除 (DW-S04)、受入全走は免除しない。
- **段 1 の新事実 (承認前提を覆す):** 依頼の中核 (login self-run による期待 node 観測を DW-M08 へ) は同日 01:40〜02:24 JST に D2195 / entry 1774
  (commit 993d2fc5f / 6d600f0a6 / 618fb8501、記録 33de1a3ea) として着地済み。依頼文は先行 wave の依頼 (`dev-wave-wall-decomp/verbatim/origin.md`) と同型で、
  着地前に起票された写しと判断 (起票時点は証明していない)。実測値の出所は食い違う: 依頼文「20 変異 1 分」、D2195 理由「2 分」、fig13 job dir の mtime は
  `login_probe.py` 20:19:35 → `login-probe-2.log` 20:21:05 (差 90 秒、2026-09-20)。mtime 差は file 更新時刻の差で実行時間の上限ではなく、
  「1 分」「2 分」の算出由来も確認できない。統一しない。
- **被覆表 (段 1 → レビュー A で訂正):** 被覆済み = 変異ごとの注入・FAIL / ERROR の観測・正規化・sha256 照合 (DW-M08 + DW-O19)、`--collect-only` 同形式照合、
  node 抽出の一般契約 (F71)、dispatch final、parametrize・fixture・環境変数・import 副作用・対応不明の fallback、完全一致 / KILLED (不変)。
  未被覆 = (a) 注入先 (DW-M07 の source-repo と同じ commit への束縛)、(b) 起動方法、(c) 復元後の clean (DW-O19 の porcelain 空確認は変異前、bytes 照合は対象 file だけ)、
  (d) skip の名指し (規範上は「対応不明」に含意される具体例。`skiputil.skip()` は素の runner で `Skip(Exception)` を投げ、`except Skip` を持たない harness
  (`test_check_docs.py::_run`) では ERROR に数えられ pytest の SKIPPED と食い違う。`skipif` は mark を無視して実行。`--collect-only` 一致では検出できない。
  帰結は final の MISMATCH で偽 KILLED ではない。空振りの回数は未実測)。意図的に固定しない = 抽出 regex (harness ごとに FAIL 行の形が違う)、実測値 (D2195 理由が持つ)。
- **実装 (docs のみ):** commit 002f926f4 (DW-M08 の列挙に `skip`、+7 bytes) + 956cce1c9 ((a)「対象commitの木へ」(b)「`PYTHONPATH=. python3`の自走harness」
  (c)「sha256と`--porcelain`空も照合」、追加 65 bytes)。byte 予算は D782 手順 1 段目 (既存記述の削減) として DW-M08 内の CJK 隣接空白 58 bytes と段落内改行 6 bytes を
  同 file M05〜M07 と同じ詰め書きに揃えて捻出し、commit 2 の純増は 1 byte、累計 DW-M08 1170 → 1178。空白・改行を除いた差分は追加語 3 + 助詞 1 字
  (焦点 A が独立に再構成して一致)。L1.5 9681 → 9689 / 9696 (残 7)、L1 10623 / 10625 不変、上限不変、check_docs 違反なし。
  pin 追随は不要 (check_docs / test_check_docs は mutation.md を節 ID 在庫・dispatch 配置・層予算で束縛、DW-M08 本文の literal pin なし。3_750 / 25_200 は合成 fixture への assert)。
  完全一致要件 (F33)・KILLED 判定・DW-O19 の義務・規律 2 は不変。gate・台帳・新 D なし。
- **D2195 本文との差:** D2195 は fix 1 前の条件「FAIL + ERROR 集合 = `--collect-only` 集合」を保持し、着地した DW-M08 は「全 node の照合可能性」と
  「変異ごとの失敗観測」を分ける (段 6 レビュー A 所見 12)。canonical は追記のみなので D2195 は直さず、ここに相違を記す。D2195 を適用根拠に読むときは DW-M08 本文を正とする。
- 段 6: 独立レビュー A (real must-fix 2 / should 2 / nit 2 / refuted 5 / 判定不能 1) NO-GO (「純増は skip だけ」という完了判断に対して) → fix (親、docs-only、956cce1c9) +
  brief v2 → 焦点再レビュー A (DW-O16 対応表 12 行、closed 11 / partial 1) GO (手順の収容として、DW-M08 への追加訂正なし)。新規所見 should 1
  (mtime 差は実行時間の上限でない) / nit 2 は brief v2 の訂正節で採用。2 巡、3 巡上限内。
- 検査: check_docs 違反なし (3 回)、message-file 検査 rc 0 (2 回)、全史 provenance 監査 12262 / 12263 件 新規違反なし。
  受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ。
- 言わないこと: skip の名指しが final の空振りを何回防ぐかは未実測。self-run の所要「1 分」「2 分」はどちらも出所が別で、どちらかを正としない。
- 観察 (scope 外、記録のみ): `orchestrator/tests/README.md` 二重 runner は「`_run()` は skiputil.Skip (SKIP) を分けて数える」と書くが、`test_check_docs.py::_run` は
  `except Skip` を持たない (規約と実体の差、機械強制なし)。
- 工数: codex 2 本 (review 1・focus 1、gpt-6-astra、各 3〜4 分)、計算ノード job = 受入 1 走、login = 全史監査 2 回・check_docs 3 回・予算実測 script (job dir)。

## 次の一手差分

### 新規

- {{T:selfrun-harness-skip-contract}} **P3・新規**: 自走 harness の `Skip` の扱いが `orchestrator/tests/README.md` 二重 runner の規約 (skiputil.Skip を SKIP に数える) と
  file ごとに食い違う (`test_check_docs.py::_run` は `except Skip` なし)。DW-M08 の self-run 適用判定 (skip → dispatch probe) の負担を減らすには、規約どおり
  SKIP を数える harness へ揃えるか、`test_plain_runner_coverage.py` 型のメタテストで機械検査する設計が要る (gate 追加なので裁定パッケージ)。一次資料は
  `output/insights/2026-09-21/dev-wave-dwm08-selfrun-probe/README.md` §2・§10。
