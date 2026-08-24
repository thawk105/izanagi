# [T-1431] 変異 matrix 逐語 — floor sort_best 実効 masstree root 検査

対象 commit: `2aee918a8a73e6c1879a814f523a2c3f9cc1c27d`
harness: `tools/mutation_worktree.py` (固定 commit の使い捨て worktree) →
`tools/mutation_harness.py`
runner: `python3 tools/run_tests.py orchestrator/tests/test_buildcache_v2.py -q -rf --force-dispatch`
runner-mode: `dispatch` (計算ノード)
source-repo: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/mutation-source`
(主 worktree から独立に clone した木。共有木の観測点を分離するため)

## 経緯 — probe を先に回した理由

段 6 の敵対レビュー B が、事前登録した m03 / m04 / m05 は
**他層 (A/B 一致検査) に mask されて SURVIVED になる**と本走前に指摘した。
対象の検査を外しても、fixture の別の条件で拒否が残るためである。
`DW-M02` に従い実効 gate へ再照準し、fix 子に単一理由の negative 9 case を足させた。

そのうえで `DW-M07` / `DW-M08` に従い、まず全件 SURVIVED 期待の probe を走らせて
観測 node を集め、それを完全集合として登録し直してから本走した。

- probe spec: `mutation-spec-probe.json`
  sha256 `504dd1a8ade8464da922b2ed28ebe93e391706e15f3bd58d6850ab0f64f71697`
- 本走 spec: `mutation-spec-final.json`
  sha256 `9937edceaf09b4943489c3eef891b8d4b27cba4638b0fdfb2286ea9ffe1b1bd4`

## 本走結果

```
baseline: PASSED
KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0
completed 9 / matching 9 / recorded 9 / registered 9
```

期待 node は probe の観測集合と完全一致した。

| ID | 変異内容 | 期待 node 数 | 結果 |
|---|---|---|---|
| m01 | 生成 build system (B) の読み取りを消し A をそのまま返す | 9 | KILLED |
| m02 | `CMAKE_GENERATOR` の値照合を消す (存在だけ見る) | 2 | KILLED |
| m03 | 重複 key の拒否を消し先頭を採る | 3 | KILLED |
| m04 | 絶対 path 要求 (`os.path.isabs`) を消す | 4 | KILLED |
| m05 | 不正な SOURCE_DIR から BASE_DIR へ fallback する | 4 | KILLED |
| m06 | `realpath(A) == realpath(B)` の要求を消す | 1 | KILLED |
| m07 | 呼び手の `effective_root != expected_root` 拒否を消す | 1 | KILLED |
| m08 | 正例統制: 実環境形の cache を無条件で拒否する (過剰拒否) | 23 | KILLED |
| m09 | 旧 `masstree_SOURCE_DIR` を読む枝を足し、あれば優先する | 1 | KILLED |

## 単一理由性

m06 / m07 / m09 は期待 node がちょうど 1 件で、変異位置と赤理由が 1 対 1 に対応する。

m03 は fix で足した単一理由 negative 3 case ちょうどを落とす。
これらは重複した key の**先頭値が B の root と一致する**入力なので、
重複拒否だけが赤の理由になる。

m04 と m05 は「不正な値」という同じ族を扱うため node が 3 件重なるが、集合は異なる。

- m04 = {`invalid_source_does_not_fallback[empty]`,
  `invalid_source_does_not_fallback[relative]`,
  `relative_path_is_single_reason[base-dir]`,
  `relative_path_is_single_reason[source-dir]`}
- m05 = {`invalid_source_does_not_fallback[empty]`,
  `invalid_source_does_not_fallback[nul]`,
  `invalid_source_does_not_fallback[relative]`,
  `relative_path_is_single_reason[source-dir]`}

m04 だけが `[base-dir]` を、m05 だけが `[nul]` を落とすので、両者は識別可能である。

m01 と m08 は事前登録時に「blocker negative だけ」「positive 2 本だけ」と書いていたが、
段 6 レビューがどちらも過剰決定だと指摘し、probe の実測がそれを裏づけた。
本走では観測どおりの完全集合 (9 件 / 23 件) を登録している。
m08 は正例統制であり、受理集合を不当に縮める方向の変異を検出することが目的なので、
広い落下集合は設計どおりである。

## erratum

段 4 で登録した期待 node 集合のうち、m01 (「blocker negative だけ」) と
m08 (「positive control 2 本だけ」) は誤りだった。probe の観測で完全集合へ差し替えた。
初回登録は消さず本節に残す (`DW-M02`)。
