## 所見

| id | 対象 | 主張 | 根拠 | 確信度 | 推奨 |
|---|---|---|---|---|---|
| F1 | A の `.gz` | **44 file は同じ root の README に実体名が記されている。** 多くは README が圧縮前の名前を書き、走査器が `.gz` との対応を拾えなかった。うち 42 file は README に `.gz` 付きの名前がない。 | A 全件の `root/README.md` に対し、basename から `.gz` を除いた文字列を照合する `python3` 読取で **44 file／17 root**、完全名一致は **2 file**。例: `2026-08-13/t907-recovery/README.md:28,34`、`2026-08-13_t1014-t1001-guards/README.md:10`、`2026-08-10_t673-d-guard-measurement/README.md:50,52`。`scan_refs.py:156-184` は実 basename との一致を要求する。 | 高 | README が非圧縮名で示す `.gz` を D。走査時にこの別名も解決する。 |
| F2 | A の spec・ledger | 「未参照」は正しさ材料でないことを意味しない。変異の期待集合と結果台帳を A が含む。 | A 全件の path と展開内容を調べる `python3` 読取で、`spec-*` **6 file**、`ledger-*` **14 file**。`t907-recovery/README.md:28-34` は spec と生台帳を明示し、`t1062-acceptance-scheduler/README.md:8-20` は各 spec の期待集合を別物として説明する。 | 高 | spec・ledger とその結果を root 単位で D。 |
| F3 | A の正例・負例と計測 | verifier の検出力を示す注入例まで A に入っている。 | A の `t2854-v3-existence/measurements/` は **6 file**（`classes.jsonl` を同 prefix で計数）。`README.md:71-72` が実 trace の正例と注入した違反例、`:82` が対照計時 2 本を根拠にする。 | 高 | 当該 root の measurements を D。 |
| F4 | A の正規化記録・受領材料 | 復元手順、提出履歴、予約情報を機械出力というだけで外せない。 | A の `verbatim-normalization.json` **5 file**、`t2211-a5-second-boot-resubmit` の failure／reservation／submit **5 file**、`t2581-k2-pin/evidence` **2 file**（`classes.jsonl` の path 計数）。`t2581-k2-pin/README.md:74` は compute-result と reservation を証拠として挙げる。 | 高 | `verbatim-normalization`、reservation、submission、pin evidence を D。 |
| F5 | 走査形式 | 別名、波括弧による名前の束、`before/after` の共有 prefix を解決しない。A に実害がある。 | `scan_refs.py:13-15,156-184`。`t2854-v3-existence/README.md:71-72,82` の `{1,2}`／`inj{1,2}` は A の **6 file**に対応。`t2563-calibration-runtime/README.md:51` の `before/after/original-file-times.json` は A の **2 file**に対応。 | 高 | これらを明示的に展開して再走査し、未解決の束表現は D に倒す。 |
| F6 | 走査の限界 | 大文字 hash、文字列連結、binary 内の参照は走査対象外になり得る。ただし、これらが A の特定 file を指す実例は今回確認できていない。 | `scan_refs.py:14-15` は小文字 hex のみ、`:156-184` は連続 token のみ、`:142-145` は NUL を含む blob を飛ばす。`summary.json` の `binary_skipped` は **87**、`gz_exceeded` と `gz_failed` はともに **0**（各 field を `python3` で読取）。連結 path の実例は `test_codex_reasoning_ab.py:128-145` にあり、その root は A **0 file**。 | 中 | A との対応が立つまでは件数を断定せず、動的 reader の root 保護を続ける。 |
| F7 | ignore_sources 8 本 | migration plan は過去の全件 inventory として無視する判断に一定の根拠がある。一方、layout-index 6 本は現行 README からたどれる生証拠の案内であり、C 扱いは危険。 | A への参照元を `refs.jsonl` で計数: migration plan は R1 **35**、R3 **108**、R5 **98**、R5t **1**。t1539 README と layout-index 6 本から A への hit は **0**。`output/insights/README.md:79-84` が raw 6 ページへリンクし、`layout-index/raw-1-1.md:1-` が証拠へリンクする。 | 高 | migration plan の ignore は維持可能。layout-index root は D。 |
| F8 | 動的 reader | 指定資料に列挙された固定読取・glob・pin の root に A はない。 | `classes.jsonl` を `2026-08-04_wave-a-campaign-transport-smoke`、`t1969-axis1-search-execution`、headline preregistration、`t2797-b5-contrast`、`t2746-k2-loop-round2`、mocc、t139、s8b など **15 pattern**で照合する `python3` 読取: A **0**、該当行はすべて D。これは列挙された pattern の範囲での確認。 | 高 | 現行の root 保護を維持。 |
| F9 | 索引 | `path`・blob・size・基準 commit が正しく記録されれば、規律 7 の「どの commit のどの path」は引ける。ただし README への一行追加だけでは、古い README が指す現行 path の意味は修復されない。 | `build_index.py:38-42` は基準 commit を各行に記録し、`:45-74` は削除集合と blob を照合する。`t907-recovery/README.md:28-34` などは削除後も旧名を指す。 | 高 | 索引に `git show <commit>:<path>` の復元方法を記し、残す README の証拠参照には索引経由の案内を付ける。 |

## A から外すべきもの

以下の件数は**重複を含む群別件数**であり、合計してはならない。母数は `classes.jsonl` の `class=="A"` を `python3` で計数した **131 file／38 root**。各 blob を `git cat-file --batch` で読み、`.gz` を展開して内容を点検した。

- README が圧縮前の basename で示すもの: **44 file／17 root、計数**。F1 の別名参照を解決するまで D。
- `spec-*`・`ledger-*`: **20 file、計数**。変異の期待集合と結果台帳。
- `t2854-v3-existence/measurements/`: **6 file、計数**。正例、注入負例、対照計時。
- `verbatim-normalization.json`: **5 file、計数**。原本との対応・復元規則。
- `t2211-a5-second-boot-resubmit` の failure／reservation／submit: **5 file、計数**。提出・失敗の一次記録。
- `t2581-k2-pin/evidence/` の compute-result／reservation: **2 file、計数**。pin の証拠。
- `t2563-calibration-runtime/{before,after}/original-file-times.json`: **2 file、計数**。README の束表記が指す比較入力。

残余を削除可能と認定するには、少なくとも README の別名・束表記を解決した再分類が必要である。

## B / C にしてはいけない root

`by_root.tsv` の file 数上位 **40 root** と `c-pool.tsv` の先頭 **60 root**を確認した。前者は A **22**／D **11,808 file**（同 TSV の数値列を集計）。以下の `docs` 件数はそれぞれ `git grep -n -F '<root末尾名>' 035fc11fa601547f5d68e54f5661c5daa70b93a5 -- docs` の行数であり、別表記による言及は含まない。

- `output/insights/layout-index` — **docs 0 行**でも `output/insights/README.md:79-84` から raw 6 ページへリンクされる現行索引。C にすると導線が切れる。
- `output/insights/2026-09-16/b7-three-run-materials` — **docs 94 行**。`docs/archive/worklog-phase3-0916-1531.md:3` が paper-story の統制稿の材料として位置付ける。
- `output/insights/2026-09-14/paper-story-20260914` — **docs 4 行**。`docs/archive/worklog-phase3-0914-1485.md:53` は成果物と生証拠の置場と明記する。
- `output/insights/2026-09-17/paper-story-20260917` — **docs 3 行**。`docs/archive/worklog-phase3-0917-1587.md:58` は成果物と生証拠の置場と明記する。
- `output/insights/2026-09-08/t2327-s1-sort-contract-binding` — **docs 5 行**。`docs/archive/worklog-phase3-0908-1359.md:1,25` に oracle 契約への束縛と変異結果がある。
- `output/insights/2026-09-02/t2102-b4-reference-tps-domain` — **docs 8 行**。`docs/archive/worklog-phase3-0902-1177-1178.md:438,802` は実測と裁定の全文をこの root に置く。
- `output/insights/2026-09-17/t2750-component-granularity` — **docs 3 行**。`docs/archive/worklog-phase3-0917-1621.md:9,42` は実装しない設計判断の一次資料を指す。
- `output/insights/2026-08-13/t907-recovery` — **docs 6 行**。加えて `README.md:28-34` が確定 spec と生台帳を指す。A の 4 file も D に戻す。

## 規則の修正案

`config-v4.json` への保守的な追加例。README の別名解決と束表記の走査修正を行った後、再分類してから縮める。

```json
{
  "protect_path_regexes": [
    "(^|/)(spec-[^/]*|ledger-[^/]*|verbatim-normalization\\.json|submission-ledger\\.jsonl)$",
    "(^|/)(reservation|compute-result)\\.json$",
    "/t2854-v3-existence/measurements/"
  ],
  "protect_root_names": [
    "layout-index",
    "t907-recovery",
    "t1014-t1001-guards",
    "t1062-acceptance-scheduler",
    "b7-three-run-materials",
    "paper-story-20260914",
    "paper-story-20260917",
    "t2327-s1-sort-contract-binding",
    "t2102-b4-reference-tps-domain",
    "t2750-component-granularity"
  ]
}
```

これは**既存配列に追加する断片**である。`t1014-t1001-guards` と `t1062-acceptance-scheduler` は root 名が実際には日付を含む旧形式なので、実装時は `protect_roots` に完全 path を置くか、実際の末尾名へ直す必要がある。最優先の規則修正は、`.gz` 別名と `{1,2}`・`before/after` 表記を解決し、README が指す file を D にすること。

## 総括

現行 A **131 file**を削除候補として確定することには反対する。README の別名参照 **44 file**、変異 spec・台帳、verifier の正例負例が含まれる。動的 reader の既知の保護 root は今回の照合範囲では A **0**だった。索引方式自体は復元条件を満たせるが、分類を直してから削除集合を作り、残る README の証拠参照を索引へ接続すべきである。