単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1

**あなたの編集対象 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1` である。**
他の worktree の path を書き換えてはならない。

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage6.md (**親の段 6 裁定。この fix の正本**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (段 4 の実装契約。継承する)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/parent-measurements.md (親の実測)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md (**条件 1 の OpenAlex 節の正本。§3**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/axis1_search/catalog.py (**登録構造と同じ形の期待 oqo を作っている先例。325-353 行。import してはならない**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/axis_b5_search/ の全 file
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/tests/test_axis_b5_search_parsers.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/tests/test_axis_b5_search_executor.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/tests/fixtures/axis_b5_search/ の全 file
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1/orchestrator/schemas/axis_b5_search_*.schema.json

## 役割

あなたは dev-wave 段 6 の fix 子である。段 6 裁定の must-fix (production 7 件・test 8 件) と
受入所要台帳の更新を行う。**所見が file を跨いで絡むため、1 単位が B5 の全 path を所有する。**

## 所有 path (これ以外を編集してはならない)

- `orchestrator/axis_b5_search/parsers.py`
- `orchestrator/axis_b5_search/preflight.py`
- `orchestrator/axis_b5_search/runner.py`
- `orchestrator/axis_b5_search/anchor_registry.json`
- `orchestrator/axis_b5_search/__init__.py`
- `orchestrator/schemas/axis_b5_search_page_evidence.schema.json`
- `orchestrator/schemas/axis_b5_search_live_preflight.schema.json`
- `orchestrator/schemas/axis_b5_search_registration_seal.schema.json`
- `orchestrator/tests/test_axis_b5_search_parsers.py`
- `orchestrator/tests/test_axis_b5_search_executor.py`
- `orchestrator/tests/fixtures/axis_b5_search/**`
- `orchestrator/tests/acceptance_duration_ledger.json` (**下記 3 の手順でだけ触る**)

**編集してはならないもの:** docs 配下の全て、`catalog.py`、`docs/related-work/claim-survey/*.json`、
`orchestrator/axis1_search/**`、その他の既存 file。**commit してはならない。**
git の状態を変える操作をしてはならない。外部 network を使ってはならない。

## 1. production の must-fix (7 件)

段 6 裁定の表をそのまま実装する。要点だけ再掲する。

- **F1:** worktree の directory 走査から `__pycache__` directory と `*.pyc` を除く。
  `.gitignore` の 2 行目が `__pycache__/` である。commit tree 側には元から現れない。
  **これは親が実 repo で実走して見つけた欠陥である。** 現状では一度でも import した環境で
  `registered_path_set_mismatch` になり、gate が構造的に通らない。
- **F2:** arXiv の日付 delimiter 正規化を、`[...]` と `"..."` の balanced な 2 形だけの照合にする。
  開始と終了が混在する形 (`submittedDate:"1991 TO 2026]` など) を不一致にする。
- **F3:** **修正先は fixture と test であって builder ではない。**
  条件 1 の OpenAlex 節は `2026-09-02-axis1-search-amendment.md` §3 を軸 B5 へそのまま当てる規則で、
  その登録構造は
  `{"get_rows": ..., "filter_rows": [{"column_id": ..., "value": ...}, {"join": "or", "filters": [...]}]}`
  である。`runner.py` の builder はこの形で正しい。単位 A の合成 fixture が使う
  `{"title_and_abstract.search": "backoff"}` の直接 key 形が誤りなので、fixture を登録構造へ直し、
  test の期待も揃える。
  **`get_rows` は軸 B5 の登録どおり文字列 `"200"` のままにする。軸 1 の `"works"` へ寄せてはならない。**
- **F4:** `B5-CTL-AND2023@openalex` の期待 AST の cutoff を、この control だけ凍結 literal `"2023-12-31"` にする。
  **catalog は変更しない。**
- **F5:** live preflight の集約器を production の公開面から外し、test-only の private seam にする。
  loader は、各 `収録` が status・media type・transport error 不在・索引別の観測形と整合することを確かめる。
- **F6:** `catalog` / `parsers` / `preflight` / `runner` の `__file__` が `repo_root` 配下の対応 path と
  一致することを seal 成功条件にする。
- **F7:** live schema に複製された `registration_seal` 定義を standalone schema と同じ制約へ揃える。
  **production の出力は変えない。**

## 2. test の must-fix (8 件)

段 6 裁定の T1〜T8 をすべて実装する。とくに次を守る。

- **期待値は凍結文の逐語からの独立 literal で書く。** production builder の出力・fixture の `len()`・
  実装の定数から期待値を作らない。
- **機構の正例は実体を名指しする。** 依存先を stub で置き換えて production の経路を通らない test にしない。
- T2 と T5 と T6 は、それぞれ **fake root を通さない・`run_leaf` を通す・transport seam を通す**ことが要点である。
- T7 は 6 条件すべてを通る統合正例にする (現状の fixture は page 0 に対して `startIndex` が 2 なので条件 2 で落ちる)。

## 3. 受入所要時間台帳

**最後に一度だけ**、次の JUnit から正本 producer で追加する。

```
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1
python3 tools/update_acceptance_duration_ledger.py --add-only /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/junit-b5.xml
```

この JUnit は fix 前の 54 node のものである。**fix で test を増減させた場合は、
台帳を更新せずにその旨を報告せよ。** 親が JUnit を取り直してから更新する。
**手書きの秒数を書かない。`0.0` の placeholder を入れない。**

## 4. 禁止 (段 5 の実装子契約を継承する)

- **既存 test の期待値を変更しない。** 反転・緩和・skip・削除を禁じる。赤なら実装側が誤りである。
  期待値の側が誤りだと判断したら、実装を変えず報告して止まれ。
- テストを甘くして緑にしない。fixture へ現行 hash を差し込まない。
- 期待値へ揮発する payload (working tree hash・時刻・host 名) を焼き込まない。
- 指示外の受理集合の変更をしない。
- 検索語彙・ブロック所属・枝・cutoff・control anchor・補助探索範囲・完走述語を緩めない。
- 軸全体の完走・`RW3` を返す API、control の「発火」を返す API を作らない。
- 新しい gate・検査・台帳・一般化を所有 path の外へ足さない。
- 外部 network を使わない (名前解決も request も禁止)。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 5. 実走のしかた

**この sandbox では `tools/run_tests.py` は `rc=16` で失敗し、`python3 -m pytest` は guard に拒否される。
自走 harness を使うこと。**

```
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix1
PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_executor.py -q
PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_parsers.py -q
PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py -q
```

**緑を主張するときは実走した nodeid と範囲を必ず併記する。** 実走できなかったものは
「実装済み・未実走」と書き、`closed` と申告しない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## production の修正
## test の修正
## 台帳
## 実走した test
## 波及可能性
## 未実走・未実装
## 総括
