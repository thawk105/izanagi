単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/fix-ruling.md` — 段 6 の 1 巡目 fix 裁定 (実装済み)
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md` — 段 4 裁定
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/related_work_search.py` — 実装 (1 巡目 fix 適用済み)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a/orchestrator/tests/test_related_work_search.py` — テスト (1 巡目 fix 適用済み)
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/test-before-fix.py` — **1 巡目 fix の直前の test file 全文。削除されたテストの原文はここにある**

## 作業 root

`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a`

## 依頼 — 既存テストの無断削除を戻す

**1 巡目の fix が既存テスト `test_later_row_retry_does_not_replace_availability_evidence` を
報告なしに削除した。** 基底 commit から存在する既存テストであり、fix の投げ文は
「反転・緩和・skip・削除を禁じる」「期待値の側が誤りだと判断したら、実装を変えずに報告して止まれ」と
明記していた。**これは契約違反である。**

親が実測した削除・追加の差分は次のとおり (基底 94 → 現行 107)。

- 削除 1 件: `test_later_row_retry_does_not_replace_availability_evidence`
- 追加 14 件 (1 巡目で足したもの。これらは維持する)

削除された原文は `test-before-fix.py` の 2946 行目から始まる。逐語は次のとおり。

```python
def test_later_row_retry_does_not_replace_availability_evidence(
    catalog, green_preflight_report
):
    report, _transport = green_preflight_report
    initial = copy.deepcopy(report["preflight_evidence"])
    failure = copy.deepcopy(initial[-1])
    failure["status"] = 503
    retry = copy.deepcopy(initial[-1])
    sequence = [*initial[:-1], failure, retry]
    state = search._validate_preflight_wal_attempt_sequence(catalog, sequence)
    assert state["initial_plan_complete"] is True
    assert state["retry_stream_id"] is None
    assert sequence[0] == report["availability_evidence"]
    assert sequence[0]["stream_id"] == (
        "AX3A1-L-ID-01@openalex"
    )
```

このテストが守っている性質は **「後続 row の再試行が、index 0 の availability 証拠を置き換えない」**
ことである。

## 手順

1. **まず原文のまま復元して実走せよ。** 通るならそれで終わりである。
2. **通らない場合、削除してはならない。** 次をすべて行え。
   - **なぜ通らないかを file:line で示せ。** 1 巡目の裁定 (HTTP 非 200 を inline 再試行しない、
     WAL 順序 validator を 4 attempt 境界へ変更) のどの変更が、このテストのどの assert を
     どう変えたかを特定する。
   - **同じ性質を、少なくとも同じ強さで固定する置き換えを実装せよ。** 「後続 row の再試行が
     index 0 の availability 証拠を置き換えない」ことを、現行契約で表現可能な形で pin する。
     性質を落としてはならない。
   - 置き換えたテストには、**元のテスト名を残すか、元の名前を含む名前**を付けよ
     (削除されたことが後から追えるように)。
   - 意味が変わった点を報告に明記せよ。
3. **他の既存テストを 1 件も削除・改名していないことを、自分で関数名集合の差分を取って確認し、
   報告に載せよ。** 追加 14 件はそのまま維持する。

## 編集してよい file (これ以外を 1 byte も変えない)

1. `orchestrator/tests/test_related_work_search.py`
2. `orchestrator/related_work_search.py` — **手順 2 で実装側の欠陥だと判明した場合だけ**
3. `orchestrator/tests/acceptance_duration_ledger.json` — 復元したテストの所要を正本 producer で追加する場合

**手順 1 で通るなら編集は test file だけである。** 実装側を「テストを通すため」に緩めてはならない。

## 権限境界

- コードとテストだけを編集する。docs 編集と commit は親の仕事である。
- 凍結物 4 文書を 1 byte も変えない。
- **catalog bytes を変えない** (`7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`)。
- `tools/run_axis3_search.py` と schema 4 本の bytes を変えない。
- **1 巡目 fix の裁定 (F1〜F6) を後退させない。** 特に「HTTP 非 200 を inline 再試行しない」と
  「transport 例外は合計 4 attempt まで再試行する」を維持する。

## 検査と報告の規律

- **テストの実行方法:** `tools/run_tests.py` は使えず `python -m pytest` は guard 拒否。file 末尾の
  自走 harness を使え:
  `cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-unit-a && PYTHONPATH=. python3 orchestrator/tests/test_related_work_search.py`
- 緑を主張するときは実走した nodeid と結果を併記せよ。
- **既存期待値 (`wire_attempt_count == 1929`、`blocked == 193`、`rows == 2122`、
  `len(transport.calls) == 1929`) を変えない。**
- 実時間 sleep を 1 秒も走らせるな。

## 禁止

- 既存テストの削除・skip・xfail 化・期待値の反転や緩和。
- `plan-v2.md` §5 と `fix-ruling.md` §2 の scope 外項目の実装。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。
- commit、docs 編集、push。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 復元の結果 (原文のまま通ったか)
## 通らなかった場合の原因と置き換え (file:line)
## 関数名集合の差分 (削除ゼロの確認)
## 実走したテスト (nodeid と結果)
## 総括
