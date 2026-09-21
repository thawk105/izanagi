単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (provisional 裁定 (P1)〜(P6)、段 1 実測、不変条件、条件表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/s1-brief.md
- 段 2 plan (codex read-only の起草、全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/codex/s2-plan.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim-request.md
- 既裁定の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim/ の D16.md, D297.md, D579.md, D1603.md, D1686.md, D1687.md, D2114.md, D2150.md, D2153.md
- 親の実測 log (逐語): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/probe/p1-patch-merge.log, p2-d297-asis.log, p3-minimal-variant.log, p4-keep-line17.log, p5-proof-surface.log, p6-d297-clang.stderr.txt (script は同 dir)
- repo 内コード (read-only、worktree の path): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/ 配下の
  `external/ccbench/cc/mocc/transaction.cc`、`external/ccbench/include/trace.hh`、`patches/instr-mocc-lock-coverage.patch`、`patches/broken-mocc-*.patch`、
  `orchestrator/campaign/s3_mocc_lock_coverage.py`、`orchestrator/verifier/model.py`、`tools/check_trace0_preprocess_identity.py`、`orchestrator/tests/test_mocc_proof_surface.py`、
  `orchestrator/verifier/parse.py` (P / X 行の読み手)、`output/insights/2026-09-07/t2294-mocc-lock-instrumentation/README.md`

## 前置き — これは自分たちのコードの設計レビューである

研究用 repo (並行性制御の自動合成) で、MOCC の検証計装 (lock 被覆 X / permutation 保存 P、`#if TRACE` 内だけで有効) を、ベンチマーク submodule の
現行 pin の子 commit として載せる計画を点検してもらう。目的は、正しさ判定 (verifier の certified 判定) と観測者効果の分離 (TRACE=0 の性能 build が不変) が
計画どおりに保たれるかを、実装前に指摘することである。あなたは read-only の相談役で、実装・テスト実行はしない (書込可能 tmp が無いので静的読解でよい)。
**plan を守らせず点検せよ。親 brief の前提・file:line・親自身の実測値とその一般化も点検対象である。**

## レンズ A — 正しさ境界と観測者効果

次を点検し、所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 file:line・放置時に成果物 (certified 判定・材料レポート・試行台帳) の値や受理集合がどう変わるかを 1 行で書く。

1. 候補の中身 (P1) の意味論: `std::unordered_multiset<const void*>` の等値と D1686 の P の主張の同値、hash・`operator==` の性質、例外・alloc の挙動差、TRACE=1 build での `-Werror` 懸念、
   `<unordered_set>` を trace.hh 経由で得る依存の脆さ。対案 (vector + sort) の方が正しさ上よいか。
2. X の 3 検査点と P の検査が C でも同じ位置・同じ条件で発火するか (T-2294 の `#line` 復元点 17 / 990 / 991 / 1158 / 1169 / 1187 / 1195 との対応)。負例 4 本が C の上で「同じ理由で・一つの理由で」赤になるか (単一理由性)。
3. D297 検査の保証範囲: 親の probe (scratch clone の OID eb8dc6fe、GCC 11.4 / 12.3) が本物の C にそのまま一般化できるか。`#line` directive が TRACE=0 の正規化出力と include 活性に与える影響、
   16 context が mocc の実効構成を何種覆うか (t2756 §3.2)、clang 14 の未確認の扱い。検査器 (`tools/check_trace0_preprocess_identity.py`) を緩めずに済むか。
4. TRACE=0 の `.text` 一致を「規律 1 の証拠」として主張できる範囲 (等長 build dir、`__FILE__`、`#line` による `__LINE__` の保存)。driver 候補 mode の base / inst の取り方が観測者効果の検査として成立するか。
5. verifier の certification gate (model.py の proof-surface 判定) が C で真になることは「certified を名乗れる必要条件の一つ」に過ぎない。plan / brief が十分条件のように書いていないか。
6. 正例・負例の実走 (P2) の check key が入力由来か (定数 True で恒真化しない)、候補固有の束縛 key (tree 差分 1 path、blob 一致) が実際に歯を持つか。
7. plan の変異候補に、正しさ方向で抜けているもの (例: P 比較の恒真化、X 入口 predicate の CLL 条件削除、`#line` ±1) があるか。
8. plan が足した要素の正しさ上の必要性: hot 正負例 2 走 (hot-update-unlock を C で再立証する必要があるか)、`objcopy` による `.text` bytes 比較 (既存の正規化 objdump 比較との関係)、
   P の「同サイズの pointer 置換・重複数変更」を動的に立証していない点 (perm-erase は size しか壊さない) を本 wave で埋めるべきか、静的対照で足りるか。
9. plan は brief の 2 点を限定した (「現行 pin の mocc 結果は常に indeterminate」は広すぎる — BASE + 旧 patch の診断実走は certified 正例を持つ / p4 は TRACE=1 build の証拠ではない)。この限定の当否と、他に brief の言い過ぎがあるか。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 実行できない検査は「未実走・静的読解」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: must-fix / should / nit の一覧 (各 1 行)、(P1)〜(P6) への支持 / 反証、plan の修正要求の要約。
