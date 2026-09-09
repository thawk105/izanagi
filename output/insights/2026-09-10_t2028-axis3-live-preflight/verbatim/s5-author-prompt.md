単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md` — **親の段 4 裁定とプラン v2。実装の正本。ここに書かれていないものを足さない**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/brief.md` — 親の段 1 brief (前提の訂正は plan-v2 §0 が優先する)
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md` — 段 2 プラン (file:line の下敷き。plan-v2 が上書きした点はそちらが優先)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py` — 実装対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py` — 実装対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/axis1_search/runner.py` — `HostLimiter` の移植元
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/acceptance_duration_ledger.json` — 受入所要台帳 (更新対象)

## 作業 root

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a`

## 依頼

`plan-v2.md` の §3 (3.1〜3.7) を実装せよ。§3 に書かれた 7 点だけを実装する。

## 編集してよい file (これ以外を 1 byte も変えない)

1. `orchestrator/related_work_search.py`
2. `orchestrator/tests/test_related_work_search.py`
3. `orchestrator/tests/acceptance_duration_ledger.json`

**`tools/run_axis3_search.py` と `orchestrator/schemas/axis3_search_*.schema.json` 4 本は
bytes を変えてはならない。** docs は 1 file も編集しない。commit もしない。

## 権限境界

- コードとテストだけを編集する。**docs 編集と commit は親の仕事である。**
- 凍結物 4 文書 (`docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md`,
  `2026-08-27-axis3-index-measurements.md`, `2026-09-01-axis3-search-amendment.md`,
  `2026-09-01-axis3-registration-preflight.md`) を 1 byte も変えない。
- **catalog bytes を変えない。** `build_axis3_catalog` の出力、query ID 集合、語、10 枝、
  cutoff (2026-12-31)、`request_factory` の state を一切変えない。
- 最小間隔を短くできる経路 (CLI option・環境変数・catalog 値・引数の既定値の緩和) を作らない。
- `_probe_response` の「非 200 → `unavailable`」を緩めない。

## 検査と報告の規律

- **緑を主張するときは実走した nodeid と範囲を必ず併記せよ。** 実走できなかったものは
  `closed` と申告せず「実装済み・未実走」と書け。
- **テストの実行方法:** この sandbox では `tools/run_tests.py` は使えず、
  `python -m pytest` は guard に拒否される。file 末尾の自走 harness を使え:
  `cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a && PYTHONPATH=. python3 orchestrator/tests/test_related_work_search.py`
- **既存テストの期待値を 1 つも変えてはならない。** 反転・緩和・skip・削除を禁じる。
  `wire_attempt_count == 1929`、`blocked == 193`、`rows == 2122`、`len(transport.calls) == 1929` は
  そのまま通ること。**赤になったら実装側が誤りである。** 期待値の側が誤りだと判断したら、
  実装を変えずに報告して止まれ。
- **テストを甘くして緑にしない。** fixture へ現行 hash を差し込む、揮発 payload
  (working tree hash・実時刻・host 名) を期待値へ焼き込む、といったことをしない。
- **機構の正例・負例は実体を名指しせよ。** 依存先を stub して「両層 stub で機構を通らない緑」を
  作らない。
- **テストを新設・改名したら、その単位を縛る制約 meta-test を自分で洗い出して走らせよ。**
  親の名指しを網羅と見なすな。
- **実時間 sleep を 1 秒も走らせるな。** fake clock と fake sleeper を対で差し替える。
- 完了報告に、**所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙**せよ。
- 実装前に、変更する述語の**現行の受理・拒否挙動**を明記せよ。指示外の受理集合変更をしない。

## 特に外してはならない実装点

`plan-v2.md` から再掲する。詳細は同文書を正とする。

1. **limiter が記録する「最終発行時刻」は `transport.send` を呼ぶ直前の実時刻**であること。
   `acquire` 時点の時刻にしてはならない (段 3 の A-R2)。
2. **待ち (sleep) は `begin_attempt` より前**であること。
3. **送信 (transport) 例外の経路でも `writer.materialize_pending_attempt()` を呼んでから
   送出**すること。現状は try の外なので bundle が再開不能になる (親の実測)。
4. **予算・締切の検査は状態を変えない形で `begin_attempt` の前**に置くこと。`consume` は
   現在位置のまま。
5. **`validate_preflight_report` が `observed_interval_seconds` の値を理由に
   `ContractError` を送出してはならない。** 通る正例をテストで固定せよ —
   同一 host の 2 件目の `observed_interval_seconds` が `44.87` (下限 45.0 未満) でも
   `validate_preflight_report` が正常に完了すること。
6. **`_validate_preflight_wal_attempt_sequence` は同一 stream の 4 回目の attempt を
   `ContractError("bundle_preflight_sequence", ...)` で拒否**すること (負例をテストで固定)。
7. **受入所要台帳を正本 producer で更新**すること。`0.0` の placeholder を書かない。

## 期待赤の事前指定

親の docs はまだ land していない。この時点で赤になってよいのは次だけである。

- 無し。**すべて緑であること。** 上記以外の赤は回帰として報告せよ。

## 禁止

- `plan-v2.md` §5 の scope 外項目 (pending intent の回復強度、body/wall-clock ceiling、
  resolver、control 評価器、DBLP 題名 lookup) の実装。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。
- commit、docs 編集、push。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 変更前の受理・拒否挙動
## 実装した内容 (file:line)
## 実走したテスト (nodeid と結果)
## 波及可能性の静的列挙
## 未実装・未実走として残したもの
## 総括
