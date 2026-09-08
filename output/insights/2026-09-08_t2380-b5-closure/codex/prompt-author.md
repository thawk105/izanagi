単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (後継凍結物 1/2、commit 済み。§3.1〜§3.4 が生成器の契約と、凍結文から一意に読めない箇所の親裁定。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。§3.1 の 85 語、§3.2 の 10 枝、§3.3 の規則 1〜7 と template、§3.5 の直積、§4.1 の control 14 本、§4.5 の venue 272 stream が入力。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/plan.md (段 2 の plan。関数構成・test 一覧の出発点。§3.4 の親裁定と食い違う箇所は §3.4 が優先。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis1_search/catalog.py と orchestrator/tests/test_axis1_search_catalog.py (先例。構造・直列化・test の書式と、test file 末尾の自走 harness の形の参考。import してはならない。読めなければ即停止)

## 役割と所有

あなたは dev-wave 段 5 の実装子 (Codex `role=author`) である。**次の 3 file だけを新規作成する。** 他の file は 1 byte も変えない。

- `orchestrator/axis_b5_search/__init__.py` (docstring のみ)
- `orchestrator/axis_b5_search/catalog.py` (生成器 + CLI)
- `orchestrator/tests/test_axis_b5_search_catalog.py` (test)

生成物 `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` は、あなたの CLI (`python3 -m orchestrator.axis_b5_search.catalog --output <その path>`) で**書いてよい** (test が tracked JSON との一致を検査するため)。親が同じ CLI で再生成して bytes 一致を確かめる。

## 契約 (後継凍結物 1/2 §3.1〜§3.4 の逐語が正本。ここは要約)

- 入力は凍結文の逐語だけ。network・時刻・環境変数・応答件数を入力にしない。`orchestrator.axis1_search` を import しない。
- 出力 bytes は `(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")`。
- top-level 11 field と entry の形、`term_groups` (group 内 OR、group 間 AND)、配列順、`schema_version`、`registration_blob`、`expected_cardinalities` の key は §3.2・§3.4 の項目 3〜6 のとおり。
- 単一 operand control は singleton block、`X OR Y` は 1 group 2 語、`X AND Y` は singleton group 2 個 (§3.4 項目 1・2)。`B5-CTL-AND2023@arxiv` は下限を保って上限だけ 2023 (項目 3)。`B5-CTL-AND2023@dblp` は `B5-CTL-AND@dblp` と byte 同一で `shares_request_with` を持つ。他は `null`。
- percent encoding は `urllib.parse.quote(value, safe="-_.~")`、OpenAlex の filter 値だけ `safe="-_.~,"` (項目 7)。DBLP の `q` は生の空白で連結して一度だけ符号化 (項目 8)。venue の `q` は literal `venue%3A<venue>%3A%20year%3A<year>%3A` で、DBLP URL 組立て関数は符号化済み `q` を受ける (項目 11)。
- `{POS}` / `{CUR}` は template 上の literal、`first_page_url` は POS=0 / `cursor=*` (符号化しない)。
- 語 ID は `<block 文字><2 桁 0 埋め>`。**語 ID を作る seam を 1 つの関数 (`_term_id(block_id, position)`) にする。**
- CLI: `--output PATH` と `--verify PATH` は排他かつどちらか必須。不一致・読取不能は rc=1。`--verify` は書き込まない。
- 期待 AST・期待 echo・anchor・引用/著者 stream・parser・schema・runner・seal API は作らない。

## test の契約

- 期待値は**凍結文由来の独立 literal** を test 側に置く。production の `BLOCKS` / `BRANCHES` / encoder / 生成 JSON から期待値を再構成しない (自己参照の恒真を避ける)。最低限、次を literal で持つ:
  85 語と block 所属・語順、10 枝の block 順、§3.3 の照合例 `B5-Q10@dblp/T01-O01` の完全 URL、arXiv `B5-Q1@arxiv` の完全 URL (語順・括弧・`abs:"..."`・日付節を含む)、OpenAlex `B5-Q1@openalex` の完全 URL (引用符なし・comma 非符号化)、control 14 本の完全 URL (singleton / OR / AND / AND2023 の 4 形と 3 索引)、venue stream の先頭 (`SIGMOD-1993`) と末尾 (`DISC-2026`) の完全 URL と stream ID。
- 件数 (10/10/1602/14/272、枝別 228/252/399/210/273/120/120)、6 block 互いに素・85 語、DBLP 1602 本の request bytes に重複なし、`B5-CTL-AND2023@dblp` の同一 bytes、`render` の決定性 (2 回一致・末尾 newline 1 個)、tracked JSON との bytes 一致、CLI `--output` の exact bytes、`--verify` が exact で rc=0・末尾に 1 byte 足した file で rc=1。
- 変異で赤になる構造にする: 語順を sort する変異は arXiv/OpenAlex の完全 URL literal で、`_term_id` の桁数変異は語 ID literal で、`product`→`zip` は枝別件数で、venue の年範囲変異は末尾 ID literal で、それぞれ**単独の test が**赤になること。
- 既存テストの期待値を変えない。テストを甘くして緑にしない。fixture に生成器の出力を写して期待値にしない。
- **test file には既存の test file と同じ形の自走 harness (`if __name__ == "__main__":`) を付ける** (`orchestrator/tests/test_plain_runner_coverage.py` が全 `test_*.py` に要求する。形は `test_axis1_search_catalog.py` 末尾を写す)。nodeid と parametrize の id は ASCII だけにする。
- 実走: `PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_catalog.py` (自走 harness) と `PYTHONPATH=. python3 -m orchestrator.axis_b5_search.catalog --verify docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` を実行し、結果を報告に書く。sandbox で実走できないなら「実装済み・未実走」と書き、最低限 test module を import して各 test 関数を直接呼び出して fixture が成立するか確かめ、さらに対象の検査を一時的に外して赤化するかまで確かめよ (`tmp_path` は `tempfile.mkdtemp()` で代用してよい)。走らせていない結果を書くな。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性 (`orchestrator/tests/test_plain_runner_coverage.py`、`test_acceptance_schedule_order.py` の被覆 gate、`test_campaign_import_invariant.py` の namespace 規則) を静的に列挙する。受理集合の変更はしない (本 wave は生成器の新設のみ)。

## 禁止

- **`git add` / `git commit` / `git stash` / `git checkout` など git の状態を変える操作を一切しない。commit は親が行う。**
- **docs を編集しない (`docs/handoff/` への file 作成を含む)。** 例外は上記の生成 JSON 1 file だけ。
- 上記 3 file + 生成 JSON 以外の file を作らない・変えない。`tools/`、`hooks/`、schema、README、既存 test に触れない。
- 外部 network を使わない。時刻・環境変数を出力に入れない。
- 新しい gate・検査・台帳・一般化を足さない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。作業ツリーに途中まで書いた実装が残ることは許される。

## 作成した file と関数
## 実走した結果 (nodeid と rc、または「実装済み・未実走」と直接呼び出しの結果)
## 凍結文・§3.4 と実装の対応で迷った点
## 波及可能性
## 総括
