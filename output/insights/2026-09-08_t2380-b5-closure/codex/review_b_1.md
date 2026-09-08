## 所見

`catalog.py` 自体には凍結契約との明白な不一致を見つけなかった。一方、独立 oracle の受理集合には実害のある穴があり、mutation 候補 #1・#7・#9 は位置指定を修正しないと帰属が成立しない。

`catalog.py` は `orchestrator/axis_b5_search/catalog.py`、`T` は `orchestrator/tests/test_axis_b5_search_catalog.py` を表す。

RB-01 — real、must-fix。独立 oracle の受理集合が不足している。

`T:474-475` の checked-in bytes 比較は、生成器と JSON を一緒に再生成した誤変更には効かない。この条件で、少なくとも次が緑のままになる。

| 緑になる破壊 | 捕まえるべき既存 test |
|---|---|
| `B5-Q2@arxiv` の `query_id` を別の一意な誤 ID にする。`T:350-355` は branch 順と ID の一意性しか見ない | `test_main_query_ids_order_and_cardinalities_are_exact` で全 query ID 列を検査 |
| Q2 以降の `term_groups` を、その `branch_id` の `block_ids` と不整合にする | 同 test で `branches` から導出した全 `term_groups` と照合 |
| OpenAlex Q2 だけ `{CUR}` を `%7BCUR%7D` にする。Q1 literal と control は無傷 | `test_openalex_q1_full_url...` を既存 node 内で全 OpenAlex query の template 関係まで検査 |
| DBLP の枝内部にある 2 record を入れ替える。件数、先頭、末尾、一意 request bytes は不変 | `test_dblp_cartesian_branch_counts...` で全 query ID の順序を照合 |
| DBLP の中間 record で `query_id`、`term_groups`、URL の対応だけを崩す | 同 test で全直積 record の三者対応を照合 |
| 中間 venue stream の `index`、`stream_id`、URL のいずれかを venue/year と不整合にする。`T:438-459` は全行では venue/year と ID 一意性しか見ない | `test_aux_venue_streams...` で全 272 entry を構造的に照合 |

一方、例示された `expected_cardinalities` の値変更は `T:338-349`、`shares_request_with` の全 `null` 化は `T:425-432`、venue 年の文字列化は `T:438-441` が捕捉する。`{CUR}` の一括符号化も Q1 と control literal が捕捉し、穴になるのは枝限定の破壊である。

推奨対応: node を増やさず、上表の既存 test に全 entry の独立な ID、group、template 対応を追加する。

成果物影響: catalog bytes は不変。test の受理集合だけが狭まり、誤った生成器と再生成 JSON の同時変更が赤になる。

RB-02 — refuted。repo 統合用メタテストは静的に通る。

- 自走 harness は `T:515-516` に `__main__` と `pytest.main` の両 signal があり、`test_plain_runner_coverage.py:25-41` の exact な字句要求を満たす。
- import invariant は全 Python を読むが、campaign 固有 shape は `orchestrator/campaign/` にだけ適用される (`test_campaign_import_invariant.py:1002-1044`)。legacy regex も裸の `campaign...` だけを対象とする (`:53-61`, `:538-679`)。`orchestrator.axis_b5_search` は違反しない。
- 台帳は `acceptance_duration_ledger.json:19749` で 19,745 node。新規 17 node は未登録である。既存 19,745 node が現在も収集されるという静的前提では、被覆率は `19745 / 19762 = 99.913976%`。閾値 90% (`test_acceptance_schedule_order.py:660-714`) を十分上回る。

推奨対応: この追加だけを理由とする台帳被覆の阻害はない。

RB-03 — refuted。CLI test は dispatch の cwd、`PYTHONPATH`、interpreter に依存して壊れない。

- `ROOT` は cwd ではなく `Path(__file__).resolve().parents[2]` から導出される (`T:17-24`)。
- 各 CLI subprocess は `sys.executable` と `cwd=ROOT` を明示する (`T:478-509`)。repo root が `-m orchestrator.axis_b5_search.catalog` の import root になるため、`PYTHONPATH` は不要。
- runner も pytest を `sys.executable -m pytest` で組み立て (`tools/run_tests.py:550-572`)、local child の cwd を repo root に固定する (`:2682-2699`)。
- compute dispatch は repo root へ `chdir` し (`tools/pegasus/dispatch_compute.py:1563-1596`)、同じ interpreter で runner を起動し、bound child の cwd も repo root に固定する (`:1162-1204`)。

推奨対応: なし。

RB-04 — refuted。provenance と docs の path・拡張子判定は予測可能である。

- 938,806 bytes の `docs/related-work/claim-survey/*.json` は `.py` 等の implementation suffix ではなく、`docs/` も implementation prefix ではないため実装面ではない (`check_ai_provenance.py:74-85`, `:1536-1549`)。
- `orchestrator/axis_b5_search/__init__.py`、`catalog.py`、新規 test は `.py` suffix だけで実装面になる。AI 関与 commit には Codex author が必要 (`:1552-1582`)。
- `check_docs.py` は手書きの `LIVING_DOCS` と `docs/phase3-s*-runbook.md` のみを本文検査する (`check_docs.py:124-169`, `:6668-6701`)。claim-survey JSON を再帰走査せず、939 KB という大きさも同 checker の違反条件にならない。

推奨対応: commit provenance では Python 3 file を実装面として扱う。JSON に対する `check_docs.py` の検査済み主張はしない。

## 変異候補の判定表

「単独の test」は primary node だけを selector で走らせる意味なら成立しうるが、17 node 全走で本当に一つだけ赤になるのは #12 だけである。bytes が変わる変異には通常 `test_checked_in_catalog_matches_rendered_bytes` も反応する。

| 所見 / 候補 | 実在位置と primary | 静的判定、単一理由性、推奨 |
|---|---|---|
| RB-05 / #1 `quote` → `quote_plus` | `_percent_encode`, `catalog.py:217-219`。primary `T:405-411` | real、must-fix。行 219 の名前だけを変えると import が無く `NameError` になり、期待した符号化変異ではない。`catalog.py:14` を `quote_plus as quote` にする exact 変異なら primary は赤。ただし arXiv、OpenAlex、control、checked bytes も赤で計 5 node。直接 oracle は既存 primary 内で `_percent_encode("a b") == "a%20b"` を先に検査する。 |
| RB-06 / #2 OpenAlex safe から comma を除く | `_percent_encode`, `catalog.py:217-219`。primary `T:396-402` | real。primary は full URL と生 comma の両方で赤。control と checked bytes も赤で計 3 node。既存 primary 内の直接 oracle `_percent_encode("a,b", preserve_comma=True) == "a,b"` が帰属を最も狭くする。 |
| RB-07 / #3 OpenAlex 複数語を quote | `_openalex_filter`, `catalog.py:236-247`。primary `T:396-402` | real。Q1 literal と `%22` 禁止で赤。複数語 control と checked bytes も拒否し計 3 node。既存 primary 内で `_openalex_filter` の最小 2 語入力を literal 比較するのが直接 oracle。 |
| RB-08 / #4 arXiv の `abs` quote を除く | `_arxiv_expression`, `catalog.py:222-233`。primary `T:387-393` | real。primary は赤だが arXiv control と checked bytes も赤で計 3 node。既存 primary 内で `_arxiv_expression` の singleton 入力を literal 比較する。 |
| RB-09 / #5 block 内を sort | `_term_records`, `catalog.py:190-194`、または `BLOCKS`, `:33-149`。登録 primary `T:387-393` | real。arXiv だけでなく blocks、OpenAlex、DBLP Q10、controls、checked bytes が赤で計 6 node。直接の primary は `test_blocks_match_frozen_terms_order_counts_and_disjointness` (`T:302-312`) に変更すべきで、arXiv literal は二次 kill と記録する。 |
| RB-10 / #6 `product` → `zip` | `_iter_main_queries`, `catalog.py:324-337`。primary `T:358-384` | real。primary は件数で赤になるが、全 query ID 数 (`T:335-355`) と checked bytes も赤で計 3 node。primary selector の枝別件数を帰属 oracle とする。 |
| RB-11 / #7 DBLP に Q3 を追加 | `DBLP_BRANCH_IDS`, `catalog.py:164-172`。消費位置 `:324-330` | real、must-fix。Q3 は 3 block なので `left_block, right_block = ...` が `ValueError` になり、件数 oracle へ到達しない。17 node 中 16 node が構築例外で赤になる。対象枝選択の変異には、既存の二項枝 Q10 を除くなど、構築可能な一箇所変異を使う。 |
| RB-12 / #8 `T01` → `T1` | `_term_id`, `catalog.py:177-180`。primary `T:315-323` | real。primary は赤。ただし DBLP bounds、arXiv `term_groups`、DBLP Q10 lookup、controls、checked bytes も赤で計 6 node。primary 内では doc 構築より先に `_term_id("T", 1)` の直接 assertion を置くと帰属が明確になる。 |
| RB-13 / #9 AND2023@dblp に year parameter | `_build_controls`, `catalog.py:393-409` と `_control_entry`, `:340-364` | real、must-fix。現在は「year parameter を足す」exact な式が指定されていない。例えば `control_id == "B5-CTL-AND2023@dblp"` のとき encoded q に `%20year%3A2023%3A` を加える、と位置と bytes を固定すれば `T:425-432` が赤になる。control literal と checked bytes も赤で計 3 node。 |
| RB-14 / #10 `range(1993, 2026)` | `_build_aux_venue_streams`, `catalog.py:413-428`。primary `T:435-459` | real。primary は長さで赤になり、checked bytes も赤で計 2 node。primary selector なら単一理由は年上限欠落に絞れる。 |
| RB-15 / #11 末尾 newline を除く | `render_catalog_json`, `catalog.py:466-470`。primary `T:462-471` | real。canonical test と checked bytes の 2 node が赤。primary 内の最初の literal bytes 比較だけで原因は末尾 newline に絞れる。 |
| RB-16 / #12 bytes 比較を JSON 比較にする | `_verify`, `catalog.py:473-478`。primary `T:489-499` | refuted。`json.loads(actual) == json.loads(rendered)` なら追加 newline を受理し、期待どおりこの 1 node だけが赤になる。欠損 file は既存 `OSError` 経路で rc=1 のまま。 |
| RB-17 / #13 等価変異 | `build_catalog_document`, `catalog.py:441-444` | refuted。具体位置は行 442 の `list(_term_records(block_id))` → `[*_term_records(block_id)]`。list の要素、順序、JSON bytes は同一で、17 node 全て SURVIVED が期待どおり。 |

RB-05 成果物影響: accepted catalog bytes と test 受理集合は不変。mutation が `NameError` ではなく符号化規則を攻撃するようになる。

RB-11 成果物影響: accepted catalog bytes と test 受理集合は不変。mutation の赤理由が構築例外から DBLP 対象枝の欠落へ変わる。

RB-13 成果物影響: accepted catalog bytes と test 受理集合は不変。mutation bytes と期待される赤集合だけが一意になる。

## 裁定パッケージ候補 (scope 外)

RB-18 — real。catalog は主 query の期待 AST と DBLP echo を独立導出する最低限の材料を持つが、control の日付 AST は完全には構造化されていない。

- `blocks` は term ID と語、`branches` は block 構造、`queries.term_groups` は具体的 operand を持つ (`catalog.py:441-450`)。DBLP echo はこれらと凍結済み token 分割規則から request bytes を写さず導出できる。
- しかし `B5-CTL-AND@arxiv` と `B5-CTL-AND2023@arxiv` は同じ `term_groups` を持つ (`catalog.py:376-390`) のに、期待 upper date は 2026 と 2023 で異なる。top-level `cutoff` は 2026 だけで (`:440`)、control entry に構造化された upper date は無い (`1/2:271-276`)。
- 現行閉集合のままなら、将来実行器は exact な `control_id` から 2023 規則を独立に割り当てる必要がある。request URL から日付を逆算してはならない。
- self-describing な後継 schema を望む場合だけ、control の `upper_date` 相当が裁定候補になる。現行 11 field 閉集合への追加は本 wave では行えない。

## 総括

静的結論は「catalog 実装は凍結契約に適合、test は must-fix」である。特に全 query と全 venue entry の構造対応を独立に検査しておらず、生成器と JSON を同時に誤更新できる。mutation は #1、#7、#9 の exact な位置・bytes を修正する必要がある。自走 harness、campaign namespace、受入被覆、compute dispatch、provenance、`check_docs.py` との統合には阻害を認めない。

ファイル変更、git 操作、pytest 実行、外部通信は行っていない。