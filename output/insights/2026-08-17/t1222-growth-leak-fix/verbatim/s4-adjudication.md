# 段 4 裁定 — [T-1222] 成長比例の既知漏れ 4 件

親の裁定。2026-08-17 09:40 JST。段 2 プラン + 段 3 レンズ A / B + 親の一次実測に基づく。

## 総論

**段 2 プランは 4 提案中 3 つを却下する。** 両レンズが独立に NO-GO で一致し、親の実測がそれを
数値で裏付けた。本 wave が実装するのは**項目 3 の target 側 1 本**である。
項目 1 は欠陥なし、項目 2 と 4 は新事実つきでユーザー裁定へ返す。

## D463 が要求する成長率の実測 (親、`git ls-tree -r -l` を 4 時点へ適用)

| 入力集合 | 30 日前 (2026-07-18) | 現在 (2026-08-17) | 倍率 |
|---|---|---|---|
| `.claude/agents` | 13f / 84,264 B | 13f / 83,157 B | **1.0 (微減)** |
| `.codex/role-adapters` | 13f / 171,155 B | 13f / 172,000 B | **1.0** |
| `test_dev_waves_integration.py` | 不在 | 119,456 B (14 日前から不変) | **1.0** |
| `tools/task_runs` | 不在 | 7f / 138,785 B (14 日前から不変) | **1.0** |
| `docs` 全体 | 2,047,235 B | 14,999,488 B | **7.3** |
| `docs/archive` | 674,988 B | 9,979,917 B | **14.8** |
| commit 総数 | 487 | 4,192 | **8.6** |

**実際に成長しているのは項目 3 (docs) と項目 4 (commit 履歴) だけである。**

---

## 項目 1 — `neither` (欠陥なし)。実装差分なし。

**判定**: D463 の第 3 区分「比例だが設計上限のある固定用途集合」。テスト側にも対象側にも
是正すべき欠陥がない。

**根拠**:
- 上表のとおり、repo の docs が 7.3 倍になる 30 日間に role 定義 subtree は **13 file のまま、
  byte はむしろ微減**した。D463 が要求する「同一手続きで数えた実際の成長率」を満たす。
- テストは全 role に対する全称命題を検査しており、入力を縮めると未検査 role が生じる。
  production も manifest / Claude source / review ledger の全単射を fail-closed に検査する
  必要がある (`orchestrator/codex_roles/spec.py:500-548`)。
- 該当コストは実測で node 上位に 1 つも現れない (file 全体 41 passed / 5.46 秒、
  上位 8 件はすべて copytree 系の別系統)。

**親の (P1) は refuted**: 「非比例」という語は D463 の語義に反する。正しくは第 3 区分である。
両レンズが独立に同じ指摘をした。結論 (no-hold / no-edit) だけが real。

**対象 node 集合の訂正**: 権威ある閉包は先 wave の逐語
(`output/insights/2026-08-16_t1222-growth-hold-sweep/verbatim/s3-lensA.md:44-51`) にある 7 個
= `test_codex_agents.py:121-124, :127-150, :164-213, :216-230, :233-249, :511-519, :1300-1307`。
- **段 2 プランの列挙は誤り** (`:511-519` と `:1300-1307` を落とし、`:159-161` と
  `_fixture()` 使用の `:252-263` を入れている)。レンズ A・B が独立に指摘。
- **親が grep で数えた 9 個も誤り** (別集合)。grep でなく権威ある閉包を先に探すべきだった。

**処置**: コード変更なし。段 7 で worklog fragment に分類・根拠・訂正を記録する。
archive と既存 insight は改変しない (歴史記録)。

---

## 項目 2 — `test-side` の欠陥は実在。**本 wave では実装せず、ユーザー裁定へ返す。**

**判定**: テスト側の書き方が悪い。1 関数 (`_serve_child_main`) を呼ぶためだけに、
fresh subprocess が 2,726 行 / 119,456 B の test module 全体を package import している
(`orchestrator/tests/test_dev_waves_integration.py:2050-2058`)。

**ユーザー裁定へ返す理由 (DW-S04: 承認済み裁定は未見の新事実で止め、親は不採用にせず返す)**:

1. **比例軸の実測が 0.214 秒しかない。** module import 単独 = 0.229 秒、素の interpreter =
   0.015 秒。node 全体は 4.23 秒で、支配項は copytree / git / daemon / socket である。
2. **その入力集合は 14 日間まったく増えていない** (119,456 B で不変、`tools/task_runs` も 7f 不変)。
   D463 は「『file が増えれば増える』という論法だけでは第 3 区分と (b) を区別できない」と定める。
3. **検出力の証明が構造的に不能。** 期待赤 node を同 file に no-group で置くと
   `orchestrator/tests/test_dev_waves_isolation_contract.py:33-41, :102-126` の AST 伝播検査が赤。
   `xdist_group` を付けると D452 (c) で変異登録が無効。既存の
   `test_socket_roundtrip_works_beyond_108_byte_repository_path` (`:2165`) は `xdist_group` 所属。
4. **修正が小さくない。** child 閉包は `_run_long_path_serve_harness` (`:1685`) →
   `_isolated_process_environment` / `_temporary_repo` / `_supervisor` /
   `_sandbox_permits_short_alias_bind` / `_ServeSelectProxy` / `daemon_mod` へ到達する。
   親が直接読んで確認した。レンズ A の「child-only closure は小さくない」は real。

**ユーザーへ問うこと**: 0.214 秒・入力不変・変異検証不能の 3 点を踏まえて、
この refactor (新 module 新設 + 大きな閉包の移動 + 別 file への期待赤 node 新設) を
打つ価値があるか。打つなら別 wave の scope として起票する。

**「保留」ではない。** node は既定で走り続け、検査は 1 つも消えない。

---

## 項目 3 — `target-side`。**本 wave で直す。**

**判定**: テスト対象 (`tools/check_docs.py`) の設計が悪い。同一 file を何度も読み直している。

**親の一次実測 (`_safe_read_text` を in-process で wrap して計数)**:

- `check_docs.main()` は **666 個の distinct file に対し 1,133 回**の `_safe_read_text` を呼ぶ。
- **467 file が 2 回**読まれる。総読取 19.9 M 文字のうち **7.1 M 文字 (36%) が重複**。
- `docs/archive` だけで 913 回 / 13.9 M 文字。
- 重複を除いた場合の実測: **4.822 → 4.147 秒 (削減 0.675 秒、14.0%)**、rc は 0 のまま。

**この修正が正しい理由**:
- **検出力が 1 ビットも変わらない。** 同じ file の同じ内容を 2 回読む代わりに 1 回読む。
  検査は全部そのまま走る。規律 2 に抵触しない。
- **成長軸に直撃する。** `docs/archive` は 30 日で 14.8 倍。削減量は corpus とともに増える。
- **テストを一切変更しない。** よって
  `test_s8c_living_doc_reference_negative_controls` は実 `check_docs.main()` を
  end-to-end で走らせ続け、**実 `main()` を既定で走らせる最後の node** という性質が保たれる
  (`test_check_docs.py::test_real_repo_clean` は台帳 `:479` で恒久保留済み)。
- reward-hack 面を開かない。monkeypatch を増やさない。保留を増やさない。

**段 2 プランの singleton 案は却下する**:
- 実測で `LIVING_DOCS` を 33 → 1 に絞っても **削減は 0.041 秒 (0.9%)** にすぎない
  (4.794 → 4.753 秒)。比例源は living-doc loop ではなく `main()` の他の全走査である。
  レンズ A R3 / レンズ B R4 と一致。
- さらにレンズ A R2 が real: singleton 化すると `assert injected` が
  「テストが与えた singleton を読んだ」だけの自己充足になり、
  「実 `LIVING_DOCS` が複数件のときだけ 8c 文書を `continue` する」という
  reward-hack 変異が緑で通る。これは規律 2 が禁じる形である。

**実装の制約 (段 5 の実装子へ渡す)**:
- cache は `_safe_read_text` の**呼び出し名前解決を壊してはならない**。
  `test_s8c_living_doc_reference_negative_controls` は `check_docs._safe_read_text` を
  monkeypatch で差し替え、その差し替えが `main()` から見えることを前提にしている。
  module global 経由の呼び出し形を維持すること。
- `findings` への副作用 (読取失敗・symlink・非 regular・不正 UTF-8 の finding) を
  重複除去で**取りこぼしてはならない**。同じ file の 2 回目の読取が finding を出す設計なら、
  cache は finding も再生する。
- `newline` 引数が異なる読取は**別物として扱う**こと (同 file でも `newline=None` と
  `newline=""` は戻り値が違う)。
- cache の生存範囲は `main()` 1 回の内側に限る。process 全体に持たせない
  (テストが同一 process で複数回 `main()` を呼び、file を書き換える場合に stale になる)。

**変異事前登録 (DW-M01)**:

| ID | 変異位置 | 変異内容 | 期待赤 (段 5 後に probe で完全集合を再導出) |
|---|---|---|---|
| M1 | 新設 cache の key | `newline` を key から落とす | `newline` 依存の検査を持つ node |
| M2 | 新設 cache | 常に初回 file の text を返す (path を key から落とす) | 多数の finding が湧き rc が変わる node |
| M3 | 新設 cache | finding 再生を省き 2 回目以降を無音にする | 読取失敗を検査する node |

- 単一理由性: M1〜M3 はいずれも「cache が誤った text / finding を返す」であり、
  前後に同じ入力を拒否する層は無い (cache は `_safe_read_text` の唯一の経路になる)。
- **期待赤 node は段 5 完了後に probe の実測から完全集合を再導出する** (DW-M08、
  archive 606 で初回登録 4 件中 3 件が MISMATCH だった前例に従う)。
- 通る正例: 無変異の `python3 tools/check_docs.py` が rc=0 であること。

**成果物影響 (DW-G05)**: 直さない場合、受入全走の wall に載る `check_docs` 系のコストが
docs corpus とともに 14.8 倍/30 日の率で伸び続ける。受入は全 land の関門なので、
land 頻度が repository の成長に張り付く。certified 選択・レポートの数値は変わらない。

---

## 項目 4 — 直さない。**受理集合の変更を伴うため、新しいユーザー裁定へ返す。**

**判定**: 「target 側の設計が悪い」ではない。**その全史走査が保証そのものである。**

**決定的な根拠 (親が実コードで確認)**:
`orchestrator/tests/test_check_ai_provenance.py:2446-2492`
`test_known_violation_off_head_policy_guard_is_stale_rc2` は、policy 導入 commit が
HEAD から到達できない orphan HEAD の木で、

- `provenance._implementation_policy_commit() is None` であること、
- `main(["--range", f"{target}^!"]) == 2` (fail-closed) であること、
- stderr に `reason=policy-epoch-not-visible non-authoritative-invocation` が出ること

を固定している。**段 2 プランどおり selected commit の祖先閉包から epoch を探すと、
epoch が発見されてこの防壁が発火せず、rc=2 が rc=0 へ反転する。**
レンズ A R1 / レンズ B R5 が独立に指摘し、親が該当テスト本文を読んで確認した。
レンズ A はさらに、同型の fail-open が過去に一度作られて却下された経緯
(`docs/archive/worklog-phase3-0807-289.md:20-27`) を挙げている。

**補足の却下理由**:
- memoize では比例が消えない (`_audit_history` は 1 監査につき 1 回ずつしか呼ばない。
  `tools/check_ai_provenance.py:1605-1606`)。
- resolver の引数化は、zero-argument の既存 monkeypatch
  (`test_check_ai_provenance.py:3660-3661` の `lambda: None`) を `TypeError` で壊す
  (レンズ B R6、親が該当行を読んで確認)。
- 「selected が 1 件なら selected、複数なら HEAD」という分岐は、同じ target に対し
  件数だけで rc=0 / rc=2 が変わる二重判定を作る (レンズ B R5)。
- 実コストは 0.17 / 0.24 秒、git 単体 0.034 秒 (history 4,192 commit)。
  D451 の「0.13 秒の軸のために防壁を消す取引は成立しない」の裏返しである。

**ユーザーへ問うこと**: off-HEAD 呼び出しの権威境界 (非権威な履歴からの監査を rc=2 で拒む)
を維持したまま全史走査の費用を除く設計はあるか。無いなら、この 2 node の比例は
「保証の対価」として台帳へ記録し、以後の棚卸しで再提案しない形にしたい。

---

## 段 3 所見の real / refuted 一覧

| 出所 | 所見 | 裁定 |
|---|---|---|
| A-R1 / B-R5 | 項目 4 が off-HEAD fail-closed を rc=0 へ反転 | **real / blocker。項目 4 を不採用** |
| A-R2 | 項目 3 singleton が `assert injected` を自己充足化し reward-hack を通す | **real / blocker。singleton 案を不採用** |
| A-R3 / B-R4 | 項目 3 singleton は比例源を除去しない | **real。親が実測 (削減 0.9%) で確認** |
| A-R4 / B-R3 | 項目 2 の変異 anchor が退行を観測できない / D452 と isolation 検査に同時抵触 | **real / blocker。項目 2 を裁定へ返す根拠** |
| A-R5 | 項目 4 wrapper は revision の受領しか検査しない | **real。ただし項目 4 不採用により moot** |
| A-R6 / B-R1 | 「7 node」の集合が誤り | **real。権威ある閉包で訂正済み** |
| B-R2 | `neither` を「非比例」と記録すると分類が混線 | **real。第 3 区分として記録する** |
| B-R6 | resolver 引数化が zero-arg monkeypatch を壊す | **real。項目 4 不採用の補強** |
| B-R7 | 費用対効果の軸が逆転 | **real。項目 3 へ集中する根拠** |
| A / B | 親の単独走秒数を受入 wall へ加算できない | **real。worklog では単独走と明記する** |
| A | 項目 1 の `.claude/agents` は過去に 11→12→13 と増えた | **partial。30 日窓では不変。第 3 区分の判定は変わらない** |

## scope 外の real 所見 (実装しない、起票のみ)

- `tools/hold_inventory.py` の bypass 台帳誤報 (archive 606 が既に記録)。
- 成長比例テストの母集合が閉じていない件 (段 2 の全件走査が `module.func(ROOT)` 形を落とす)。

## 段 5 の分割

実装単位は 1 本のみ。

- **実装子 1**: `tools/check_docs.py` の重複読み除去。編集面は `tools/check_docs.py` のみ。
  テストは変更しない。
