単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b

**あなたの編集対象 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b` である。**
他の worktree の path を書き換えてはならない。

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (**親の段 4 裁定。実装契約の正本**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/author_a_2.md (**単位 A の境界契約。dataclass・error code・関数 signature・fixture 一覧**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/parent-measurements.md (親が実測した応答 header の事実)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md (親の段 1 brief)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (部分登録。§3.3、§4.1、§5.1、§5.3 が入力)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (閉包登録 1/2。§2.4)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md (閉包記録 2/2。§1.2 の 16 anchor 表、§2 の表 B、§4 の表 C)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis_b5_search/parsers.py (単位 A の成果。**これを import して使う**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis_b5_search/catalog.py (凍結生成器。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/axis1_search/validator.py と runner.py (**写経元として読むだけ。import してはならない**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b/orchestrator/schemas/axis1_search_page_evidence.schema.json (schema の書式の先例)

## 役割

あなたは dev-wave 段 5 の実装子 (単位 B) である。軸 B5 文献調査実行器の
**registration preflight・live preflight・leaf runner・schema・統合 test** を書く。

## 所有 path (これ以外を編集してはならない)

- `orchestrator/axis_b5_search/preflight.py` (新規)
- `orchestrator/axis_b5_search/runner.py` (新規)
- `orchestrator/axis_b5_search/anchor_registry.json` (新規)
- `orchestrator/axis_b5_search/__init__.py` (既存。必要なら公開 re-export を足す)
- `orchestrator/schemas/axis_b5_search_page_evidence.schema.json` (新規)
- `orchestrator/schemas/axis_b5_search_live_preflight.schema.json` (新規)
- `orchestrator/schemas/axis_b5_search_registration_seal.schema.json` (新規)
- `orchestrator/tests/test_axis_b5_search_executor.py` (新規)

**編集してはならないもの:** docs 配下の全て、`catalog.py`、`parsers.py`、単位 A の fixture と test、
`orchestrator/tests/acceptance_duration_ledger.json` (親が別途行う)、`orchestrator/axis1_search/**`、その他の既存 file。
**commit してはならない。** git の状態を変える操作をしてはならない。外部 network を使ってはならない
(名前解決も HTTP request も禁止)。

## A. registration preflight (`preflight.py`)

部分登録 §5.3 の network-zero preflight。**checked-in の hash 表を信頼根にしない。** git の commit tree と
worktree の bytes を突き合わせる。

1. `verify_registration(registration_commit, *, repo_root, git_backend=None) -> RegistrationResult` を作る。
   **軸 1 の `verify_registration` とは別 API である** (軸 1 は `registration_commit, catalog_path, registration_paths` の
   3 位置引数を取り、seal record を返さない)。写経は git blob 比較の考え方だけにする。
2. 検査するもの:
   - `registration_commit` が 40 桁の小文字 16 進で、HEAD と一致する。
   - 束縛対象 path が worktree で clean (変更も untracked も無い)。
   - **directory exact file set 検査**: `orchestrator/axis_b5_search/`、B5 の schema 3 本、
     `orchestrator/tests/fixtures/axis_b5_search/` (再帰) の実 file 集合が、commit tree と worktree で
     **完全一致**する。**余分な path があれば拒否する** (集合が部分集合でも通してはならない)。
   - 各 path の mode と bytes が commit の blob と一致する。
   - catalog JSON は追加で 2 つを検査する: file bytes の SHA-256 が
     `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f` と一致すること、および
     `catalog.render_catalog_json()` の出力と byte 一致すること。
3. 束縛対象 path (コードと登録値):
   - `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md`
   - `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md`
   - `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md`
   - `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json`
   - `orchestrator/axis_b5_search/` 配下の全 file (directory exact set)
   - B5 の schema 3 本
   - `orchestrator/tests/fixtures/axis_b5_search/` 配下の全 file (directory exact set)
   `test_axis_b5_search_executor.py` と受入所要台帳は実行時の意味論ではないので束縛対象に**入れない**。
4. 成功時に schema-valid な **seal record** を返す。record は各 path の git blob・mode・byte 数・SHA-256、
   `registration_commit`、および **`seal_scope`** を持つ。`seal_scope` には
   **この seal が leaf 実行器の範囲に限られ、checkpoint / resume を後で足すと runner の bytes が変わるため
   暫定であること**を機械可読な形で書く (例: `"leaf-executor-provisional"` と、含まれない層の列挙)。
   **seal record 自身の hash を record へ書いてはならない** (自己参照の禁止)。
5. **network-zero を構造化する。** 失敗時は transport を生成する前に返す。

## B. anchor registry と live preflight (`anchor_registry.json`、`preflight.py`)

1. `anchor_registry.json` に閉包記録 §1.2・§2 表 B・§4 表 C を転記する。16 anchor それぞれについて
   `anchor_id`、`slot`、`doi` (**主キー**)、`arxiv_id` (nullable。`G2-08` だけ `1710.11258`)、
   `openalex_work_id`、第一著者 A-ID、最終著者 A-ID、`member_indexes` を持つ。
   **`G2-08` の主キーは DOI `10.1137/17M1154679` である。`1710.11258` は arXiv lookup の鍵であって主キーではない。**
   member の exact set は閉包登録 §2.4 (a) のとおり:
   - OpenAlex 16 件 (全 anchor)
   - arXiv 1 件 (`G2-08` のみ)
   - DBLP 13 件 (`G1-01`、`G2-04`〜`G2-08`、`G3-01`〜`G3-07`)。非 member は `G2-01`〜`G2-03`
2. `build_lookup_request(...)` は閉包登録 §2.4 (b) の 3 形**だけ**から URL を作る。
3. `classify_lookup_response(...)` は 3 値を返す。**判定順序が正しさに効く。**
   - **OpenAlex: status を先に見る。404 なら content type を見ずに `非収録`。** 親の実測では
     OpenAlex の 404 は `text/html` を返す (`parent-measurements.md` §2)。順序を逆にすると、
     登録どおりなら `非収録` の応答が `不達` に化ける。
   - arXiv: 200 かつ `feed/entry` 1 件で `収録`。200 かつ `opensearch:totalResults` が 0 かつ entry 0 件で `非収録`。
   - DBLP: 200 かつ `application/json` かつ `result.hits.hit` に当該 DOI を持つ record があれば `収録`。
     200 かつ `application/json` かつ `result.hits.@total` が 0 なら `非収録`。
   - `不達`: 通信失敗、timeout、上記以外の status、期待外 content type (anti-bot challenge の HTML を含む)、整形不能 body。
   - **content type の比較は media type だけで行い、parameter を無視する。** arXiv は
     `application/atom+xml; charset=utf-8` を返す (親の実測)。
   - **3 値のどれにも当たらない応答を 3 値へ丸めてはならない。** 例: DBLP が 200・`application/json`・
     `@total > 0` だが該当 DOI が無い場合。これは `unclassified` として記録し、観測した形をそのまま残す。
4. `evaluate_live_preflight(...)` は exact 30 member (16 + 1 + 13)、重複なし、欠落なしを検査し、
   **1 件でも `不達` / `非収録` / `unclassified` があれば `passed=False`、`axis_status="未完走"`、
   `may_start_run=False`** を返す。`収録` を見て member を足したり外したりする API を作ってはならない。
5. **timeout・User-Agent・request 間隔は既定値を持たせない。** 呼び手が明示引数で与える。
   与えられた値は live preflight record へ逐語で記録する。**実行器が値を発明してはならない。**
6. **W-ID の drift は記録するだけで、追加の阻止 gate にしない。** record に
   `registered_openalex_work_id` と `observed_index_work_id` を並べて持たせる。
   登録された述語は 3 値だけであり、登録に無い阻止条件を足さない。

## C. leaf runner (`runner.py`)

1. 定数 (凍結文から逐語転記し、この bytes を registration preflight が seal する):
   - `PAGE_SIZE = {"arxiv": 200, "openalex": 200, "dblp": 100}`
   - `POSITION_PARAMETER = {"arxiv": "start", "dblp": "f"}`
   - `PAGINATION_KIND = {"arxiv": "offset", "openalex": "cursor", "dblp": "offset"}`
     (**位置 parameter 名と pagination の種別を混ぜないこと**)
   - `RETRY_DELAYS_S = (3.0, 6.0, 12.0)`、`MAX_RETRIES = 3` (初回発行 + 再試行 3 回 = 最大 4 attempt)
   - host と path の exact 3 組: `export.arxiv.org` + `/api/query`、`api.openalex.org` + `/works`、
     `dblp.org` + `/search/publ/api`
2. **本走 request の発行は fail-closed とする。** 凍結文が定めていない運用値
   (期待 content type の exact 集合、timeout、User-Agent、request 間隔、retry 対象の失敗集合、redirect の扱い)
   を既定値で埋めてはならない。本走の発行を試みたら `UnregisteredRunPolicyError` を上げ、
   **未登録の項目名を機械可読に列挙して返す。** これは意図した設計である。
   **6 条件の評価そのものは、保存済み応答に対して完全に実装しテストする。ここが本 wave の実体である。**
3. `resolve_leaf(catalog, leaf_id)` は `queries` / `controls` / `aux_venue_streams` の exact 1 件だけを解決する。
   ID が無い・複数に現れる・index と host が矛盾するときは発行前に拒否する。
4. `build_request(leaf, page_number, position)` は catalog の `request_template` の placeholder 置換だけを行う。
   - arXiv / DBLP: `{POS}` を固定 step の位置で置換 (arXiv 0,200,400…、DBLP 0,100,200…)。
     **実要素数から次位置を作ってはならない。**
   - OpenAlex: `{CUR}` を初回は符号化しない literal `*`、2 ページ目以降は前ページの `meta.next_cursor` を
     percent encoding して置換する。**初回に `%2A` を使ってはならない。**
   - 置換後、placeholder 以外の byte が template と同一であることを再検査する。
   - page 0 の URL が catalog の `first_page_url` と byte 一致することを要求する。
5. **6 条件の評価** (部分登録 §5.1)。親の裁定で次のとおり確定している。
   - **条件 1 (解釈照合):** arXiv / DBLP は percent decode 1 回・連続空白の縮約・arXiv の角括弧と
     二重引用符の差だけを許容して比較する。OpenAlex は `meta.x_query.oqo` の構造比較で、
     **兄弟要素の順序だけ無視**し、多重度・入れ子・深さ・`join`・field の有無と型・`get_rows == "200"` を保存する。
     `and` / `or` 以外の `join`、未登録 key、想定外の型、同一 object 内の重複 key は fail-closed で `否`。
     `oql` の生文字列は証拠として保存するが判定に使わない。
   - **条件 2 (連続性):** **位置の連続性だけを見る。** 実要素数を条件 2 で見てはならない。
     arXiv は 0 から 200 刻み、DBLP は 0 から 100 刻み、OpenAlex は前ページの `next_cursor` との連鎖。
   - **条件 3 (宣言と実数の一致):** 実要素数は container の要素数だけ。非最終ページは要求件数と一致。
     最終ページは offset 系で `位置 + 実要素数 == 宣言総件数`。
     **OpenAlex は cursor なので位置を加算できない。非最終は `actual_count == 200`、
     終端は `next_cursor` の不在で判定する。** 総件数との照合は条件 5 が担う。
     **`capacity_echo` (`itemsPerPage` / `meta.per_page` / `@sent`) は証拠として記録するだけで、
     判定に使ってはならない。** 最終ページで宣言 page size と実要素数の一致を要求してはならない。
   - **条件 4 (主キー重複なし):** 索引固有 work ID がページ内・ページ間で重複しないこと。
     **重複 occurrence 自体は台帳に残す。**
   - **条件 5 (総数一致):** unique record 数が宣言総件数と一致。OpenAlex は cursor 終端までの
     distinct `results[].id` を `meta.count` と照合する。総件数がページ間で変わったら
     **その query を page 0 から 1 回だけ再走**し、2 走目も変われば `未完走`。**再走を連鎖させない。**
   - **条件 6 (正常終端):** 最終ページの HTTP status 200、content type が期待どおり、
     最終 URL が要求 URL と同一 host、総件数 field の存在。全ページの status・content type・
     最終 URL・応答 byte 数・全 response header (同名の重複を落とさない)・body の SHA-256 を保存する。
   - 0 件そのものは走行無効の理由にしない。
6. **DBLP の cutoff:** parser が運ぶ `included_by_cutoff` と `requires_ruling` を leaf の台帳へそのまま流す。
   raw occurrence を 1 件も消さない。cutoff 外の record も台帳に残す。
7. **軸全体の状態を返す公開 API を作ってはならない。** `完走` / `RW3` / 軸の成熟度を返す関数を置かない。
   返せるのは leaf 単位の 6 条件の可否と証拠だけである。
8. **control leaf について「発火」を返してはならない。** control は request の完走値だけを持つ。
   部分登録 §4.1 の集合関係と §4.3 の包含 control の評価は本 wave の scope 外である。
   型として「request の完走」と「control の発火」を分け、後者を出せないことを構造で示す。
9. production 入口は、**自ら registration preflight を実行し、durable で schema-valid な live preflight record を
   読んで exact 30 member と同じ registration seal を照合する。** bool や record を注入する引数を
   public API に置いてはならない。注入は test-only の private seam に限る。

## D. schema (3 本、draft-07)

`page_evidence`、`live_preflight`、`registration_seal` の 3 本。上の A〜C が保存する field をすべて型づける。
軸 1 の schema は書式の先例として読むだけにする。

## E. test (`test_axis_b5_search_executor.py`)

- A〜C の契約それぞれに、受理の正例と拒否の負例を対で置く。
- **規律 2 の負例を必ず置く:**
  - 条件 3 で `capacity_echo` を実要素数の代わりに使うと通ってしまう入力を、`actual_count` では正しく拒否する test。
  - 最終ページで宣言 page size と実要素数が食い違う**正常な部分ページ**が、条件 3 を通る test。
- 次の振る舞いには**必ず単独で赤になる test** を置く (親が変異で殺す対象である):
  1. OpenAlex の初回 cursor が literal `*` であること
  2. OpenAlex 期待 AST の多重度が保存されること
  3. live preflight が 1 件でも `不達` なら開始不可を返すこと (29 `収録` + 1 `不達` の構成)
  4. 総件数 drift を最終ページの値で受理しないこと
  5. 本走発行が `UnregisteredRunPolicyError` で止まること
  6. seal の directory exact set が余分な file を拒否すること
  7. DBLP の cutoff 判定
  8. 3 値に入らない応答を `unclassified` にすること
  9. OpenAlex の判定順序 (404 を content type より先に見ること)
  10. `G2-08` の主キーが DOI であること
  11. retry delay が `(3.0, 6.0, 12.0)` であること
- 期待値は凍結文の逐語からの独立 literal で書く。**production 関数の出力・fixture の `len()` から期待値を作らない。**
- **現行 hash を fixture へ差し込んで緑にしない。揮発する payload (working tree hash・時刻・host 名) を期待値へ焼き込まない。**
- 末尾に自走 harness を置く: `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))`

## 実走のしかた (単位 A の失敗を繰り返さないこと)

**この sandbox では repository の dispatcher (`tools/run_tests.py`) は `rc=16` で失敗する。**
`python3 -m pytest` は guard に拒否される。**自走 harness を使うこと。**

```
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-b
PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_executor.py -q
```

`orchestrator/tests/test_plain_runner_coverage.py` も同じやり方で走らせ、新規 test file が
自走 harness の契約を満たすことを確かめる。**緑を主張するときは実走した nodeid と範囲を必ず併記する。**
実走できなかったものは「実装済み・未実走」と書き、`closed` と申告しない。

## 報告

- 完了報告に、**所有外の caller・共有 fixture・consumer test への波及可能性**を静的に列挙する。
- 指示外の受理集合の変更をしない。変更が要ると判断したら実装せず報告に書く。
- 未登録の運用値を既定値で埋めた箇所が 1 つでもあれば、正直に報告へ書く。

## 禁止

- 出力に結合文字 U+0300〜U+036F を使わない。
- 新しい gate・検査・台帳・一般化を、所有 path の外へ足さない。
- 検索語彙・ブロック所属・枝・cutoff・control anchor・補助探索範囲・完走述語を緩めない。
- 本 wave で live preflight を実行しない (外部 request を 1 本も出さない)。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## registration preflight
## live preflight と anchor registry
## leaf runner
## schema
## 実走した test
## 未登録の運用値の扱い
## 波及可能性
## 未実走・未実装
## 総括
