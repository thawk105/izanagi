単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/fix-ruling.md` — **親の段 6 fix 裁定。fix の正本。ここに書かれていないものを足さない**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md` — 段 4 裁定 (fix-ruling が上書きした点はそちらが優先)
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/review-a.md` — 段 6 レビュー A (正しさ境界レンズ)
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/review-b.md` — 段 6 レビュー B (実効性レンズ)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py` — 実装対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py` — 実装対象
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/acceptance_duration_ledger.json` — 受入所要台帳 (更新対象)

## 作業 root

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a`

## 依頼

`fix-ruling.md` の §1 (F1〜F6) と §3 (テスト) を実装せよ。**§1 と §3 に書かれたものだけを直す。**
`fix-ruling.md` §2 の scope 外項目は実装しない。

## 所見の対応表を必ず返せ

レビュー A の must-fix 6 件とレビュー B の must-fix 4 件それぞれについて、
**closed / partial / regressed** のどれかと、その根拠 (file:line) を表で返せ。
表が無い報告は差し戻す。

## 編集してよい file (これ以外を 1 byte も変えない)

1. `orchestrator/related_work_search.py`
2. `orchestrator/tests/test_related_work_search.py`
3. `orchestrator/tests/acceptance_duration_ledger.json`

`tools/run_axis3_search.py` と `orchestrator/schemas/axis3_search_*.schema.json` 4 本は
bytes を変えてはならない。docs は 1 file も編集しない。commit もしない。

## 権限境界

- コードとテストだけを編集する。**docs 編集と commit は親の仕事である。**
- 凍結物 4 文書を 1 byte も変えない。
- **catalog bytes を変えない** (`7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`、
  2,818,599 bytes)。query ID 集合・語・10 枝・cutoff・`request_factory` state を変えない。
- 最小間隔を短くできる経路を作らない。
- `_probe_response` の「非 200 → `unavailable`」を緩めない。

## 既存テストの期待値について

**既存テストの期待値を変更してはならない。** 反転・緩和・skip・削除を禁じる。
赤になったら実装側が誤りである。期待値の側が誤りだと判断したら、実装を変えずに報告して止まれ。

**唯一の例外**は retry 境界のテストである。親が段 4 で「同一 stream の 4 回目を拒否」と裁定したのは
**登録より 1 回厳しすぎる誤り**だった。旧登録 §8.3 の逐語は
「**その各ページが最大 4 回 (初回 + 再試行 3) 送られる。**」である。
したがって retry 境界のテストは登録どおりの値へ直してよい。**これは親の裁定訂正に伴う変更であって、
実装を通すための緩和ではない。** それ以外の既存期待値
(`wire_attempt_count == 1929`、`blocked == 193`、`rows == 2122`、`len(transport.calls) == 1929`) は
1 つも変えない。

## 検査と報告の規律

- **緑を主張するときは実走した nodeid と範囲を必ず併記せよ。** 実走できなかったものは
  `closed` と申告せず「実装済み・未実走」と書け。
- **テストの実行方法:** この sandbox では `tools/run_tests.py` は使えず、
  `python -m pytest` は guard に拒否される。file 末尾の自走 harness を使え:
  `cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a && PYTHONPATH=. python3 orchestrator/tests/test_related_work_search.py`
- **テストを甘くして緑にしない。** fixture へ現行 hash を差し込む、揮発 payload を期待値へ
  焼き込む、といったことをしない。
- **機構の正例・負例は実体を名指しせよ。** レビュー A は「新設テストが `NonProductionTransport` の
  直接送信しか見ておらず、production 経路 (`LiveSearchSession`) を通していない」と指摘した。
  F4 のテストは production 経路を通せ。依存先を stub して機構を迂回した緑を作らない。
- **テストを新設・改名したら、その単位を縛る制約 meta-test を自分で洗い出して走らせよ。**
- **実時間 sleep を 1 秒も走らせるな。**
- 完了報告に、所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙せよ。

## 期待赤の事前指定

- 無し。**すべて緑であること。** それ以外の赤は回帰として報告せよ。

## 禁止

- `fix-ruling.md` §2 の scope 外項目の実装。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。
- commit、docs 編集、push。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 所見の対応表 (closed / partial / regressed)
## 実装した内容 (file:line)
## 実走したテスト (nodeid と結果)
## 波及可能性の静的列挙
## 未実装・未実走として残したもの
## 総括
