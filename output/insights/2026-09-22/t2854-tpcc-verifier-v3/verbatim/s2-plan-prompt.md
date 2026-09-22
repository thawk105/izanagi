単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (provisional 裁定 (P1)〜(P7)、不変条件 1〜9、変更面の実アンカー表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-brief.md
- 依頼文と並走 wave の返信の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/verbatim/request-t2854.md
- 段 1 の pin 閉包検索の結論: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s1-closure.md
- 設計 (投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/output/insights/2026-09-21/tpcc-trace-certification-design/README.md の §3.1〜§3.3、§6.1、§7.1
- repo 内コード (read-only、投入先 worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3/ 配下の
  `orchestrator/verifier/parse.py`、`orchestrator/verifier/model.py`、`orchestrator/verifier/dsg.py`、`orchestrator/verifier/core.py`、
  `orchestrator/verifier/report.py` (編集禁止、読むだけ)、`orchestrator/verifier/__init__.py`、`orchestrator/verifier/cli.py`、
  `orchestrator/tests/test_verifier.py`、`orchestrator/campaign/campaign_lock.py` (CONTRACT_LOADER_RELATIVE_PATHS)

## 前置き — これは自分たちのコードの実装計画の起草である

研究用 repo (並行性制御の自動合成) の trace verifier (直列化可能性の検査器) に、TPC-C 用の trace 形式 v3 を読ませる計画を起草してほしい。
v3 は C 行が 10 token (末尾に nS・nQ・取引種別)、R/W/X 行が表番号 (table) を持つ。verifier は今、key の hex 文字列だけで版列と依存辺
(ww/wr/rw) を束ねているので、表だけが違う同じ key bytes (例: Warehouse(1) と Item(1)) を同じ object と取り違える。これを
(table, key) 単位にし、cycle (anomaly) の各理由に表、cycle の節点に取引種別を載せる。YCSB 用の v2 (C 7 token) は受理・拒否・判定・
出力 bytes をまったく変えない。あなたは read-only の起草役で、実装・テスト実行はしない (書込可能 tmp が無いので静的読解でよい)。
予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 起草してほしいこと (file:line 粒度)

1. **identity の表現 (P5)**: object 経路 (parse._parse_file → _LegacyTrace → dsg.DSG(txns) の _build / _add_read_edges / _add_ww_edges / _reasons) と
   compact 経路 (parse._parse_file_to_columns の token interning → dsg._build_compact_packed / _build_compact_tuple / _edge_candidates_for_task) の
   両方で、v3 の (table, key) を 1 object として扱う具体の表現を 1 案に決めよ (例: 列に table を足す / v3 だけ合成 token を interning する /
   identity を tuple にする)。v2 の内部 map・辺の追加順・witness の選択順・notes 文言が 1 byte も変わらないことを、どの行を触らないかで示せ。
   `_packed_read_position` と `_PackedVersions` / `_PackedProducer` の Mapping 互換 view も対象。
2. **parse の v3 分岐 (P1〜P4)**: `_parse_file` の C/R/W/X/I/E/P/A 各分岐の変更、run 内 schema 固定の実装位置 (単一 file 内、compact の親 merge
   `_merge_issues_and_winners`、legacy の `_finish_legacy_parse`、`_raise_parent_file_error` の再走査との整合)。P/A 行だけの file や空 file の扱い。
   worker が per-file に schema を返し親が混在を拒否する場合、ParseError の優先順位 (sorted path 順) が既存テストどおり保たれるか。
3. **model の変更 (P6)**: Read/Write/Txn/EdgeReason/CycleEdge/Anomaly のどれに何を持たせるか。基底 dataclass に field を足すと repr / eq を
   固定する既存 test が赤になりうるので、repo 全体の tests で `repr(`・`str(`・`==` による Read / Write / Txn / Anomaly / CycleEdge の固定を
   grep で実測し、hit を path:line で列挙したうえで、派生型か別構造かを決めよ。
4. **anomaly への表・取引種別の付与と出力点 (P6)**: `_reasons` / `anomalies` で表・取引種別を復元する方法と、report.py を編集せずに v3 の構造化出力を
   返す関数の置き場 (core.py / model.py などの既存 module、新 module は不可 = brief 不変条件 7)。関数の返す dict の形を書け。
5. **X/I の tuple と core.py の notes**: `lock_coverage_violations` / `write_intent_violations` の要素 (txid, key, reason) と core.py の
   `for t, k, r in ...` の unpack。v3 で表をどう持たせ、v2 の notes 文言を変えないか。
6. **consumer の静的列挙**: `parse_trace_dir`、`Txn`、`Read`、`Write`、`EdgeReason`、`Anomaly`、`_CompactTrace`、`_ParsedFileColumns` を
   orchestrator/ と tools/ で使う箇所を列挙し、変更の波及 (赤になる所・意味が変わる所) を書け。
7. **テスト計画**: test_verifier.py に足す test 関数の名前と中身 (合成 fixture は既存 `_tmp_trace` 形)。最低限: v3 の正常系が object / compact
   (packed と tuple の両方、workers=1 と複数) で同じ結果、表だけ違う同一 key が別 object (辺集合で確認)、NewOrder / Order の同一 key、
   v3 の cycle の anomaly に表・取引種別、v2 / v3 の混在拒否 (同一 file と file 跨ぎ)、C の token 数 (5・6・8・9・11) の拒否、table / tx_type の
   範囲外・非整数、W op の不正、nS/nQ≠0、v3 frame 内の v2 形の R/W/X、X/I の v3 形、宣言件数の不一致と E の欠落 (v3)。
   既存テストの期待値は変えない。
8. **変異の候補**: 実装後に「効いているか」を挙動で確かめる変異を 6〜10 個 (例: v3 で table を identity から落とす、混在検査を外す、
   tx_type の範囲検査を外す、compact 経路だけ table を落とす)。各変異を殺す test を名指しせよ。
9. **規模**: 変更行数の見積り (file ごと) と、実装子 1 本で足りるか。

brief の provisional 裁定 (P1)〜(P7) と不変条件は起草の前提だが、誤り・穴・過剰を見つけたら根拠 file:line つきで指摘してよい (段 3 で攻撃される)。

## 出力形式

Markdown。節は「1. identity の表現」〜「9. 規模」、その後に「brief への異議」、最後に `## 総括` (5〜10 行、決めた案の要点と未決事項)。
各主張に根拠の file:line を付けよ。推測は推測と明記せよ。
