# 段 6 裁定 — [T-2380] (2026-09-08 09:15 JST)

## レビュー A (凍結規則との byte 一致)

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| RA-01〜RA-03、RA-06、RA-07、RA-09 | refuted (一致) | — | — |
| RA-04 (`index` 値の表記が未登録) | real | **親裁定: 小文字 token `arxiv` / `openalex` / `dblp`** (部分登録 §3.3 の照合例 `@dblp` と §4.1 の control ID `@arxiv` / `@openalex` / `@dblp` の literal と同じ token)。bytes は変えない。2/2 に 1/2 §3.4 への erratum E-4 (読み 13) として記録 | 2/2 §3、E-4 |
| RA-05 (`year` の JSON 型が未登録) | real | **親裁定: JSON number**。bytes は変えない。E-4 (読み 14) | 2/2 §3、E-4 |
| RA-08 (renderer/CLI test 3 本の自己参照) | real、must-fix | 採用。凍結 catalog の SHA-256 literal と tracked bytes を oracle にする (fix 子) | test |

## レビュー B (test の実効性・変異・統合)

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| RB-01 (全 entry の構造対応が未検査) | real、must-fix | 採用。既存 4 test へ独立 literal 由来の完全列照合を追加 (node 数不変) | test |
| RB-02〜RB-04 | refuted | — | — |
| RB-05 (#1 は NameError になる) | real | 採用。#1 を import 行の `quote_plus as quote` へ変更 | spec-probe.json |
| RB-06〜RB-08、RB-10、RB-12、RB-14、RB-15 | real (帰属の指摘) | 直接 oracle の追加を fix 子に許可。harness は完全 node 集合で判定するので primary 指定は台帳の注記に留める | test、変異台帳 |
| RB-09 (#5 の primary は blocks test) | real | 台帳の注記 | 変異台帳 |
| RB-11 (#7 Q3 追加は構築例外) | real | 親 spec は当初から Q10 除去。plan 案は不採用 | — |
| RB-13 (#9 の bytes 未指定) | real | 親 spec は当初から `shares_request_with` → `None`。plan 案は不採用 | — |
| RB-16、RB-17 (#12、#13) | refuted (期待どおり) | #13 の等価変異位置は親 spec の `_json_term_groups` (`list(group)` → `[*group]`) を維持 | — |
| RB-18 (control の upper date が構造化されていない) | real、scope 外 | 裁定パッケージへ (後継 schema で `upper_date` 相当を足すか)。現行 11 field 閉集合は変えない | 最終報告 |

## 変異の本走計画

- probe: spec-probe.json (13 件、全 SURVIVED 期待) を commit 2 の HEAD に対して dispatch で走らせ、実 node 集合を集める。
- 本走: 観測 node を expected_nodes に写し、#1〜#12 は KILLED、#13 は SURVIVED 期待で spec-final.json を作り再走。MISMATCH 0 を要求。
