## 所見

| id | 対象 | 主張 | 根拠・計数範囲 | 確信度 | 推奨 |
|---|---|---|---|---|---|
| O1 | D 上位 40 root | README を読んでも、**root 単位で確信を持って B に追加できるものはなかった**。数値が要約済みでも、生ログが判定の証拠、事前登録の対象、または別資料の参照先になっている。 | `by_root.tsv` を D 件数順に並べた上位 40 root の `README.md` を基準 commit から読取。例: [t2033 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-output-pruning/output/insights/2026-08-29_t2033-axis1-retake/README.md:13) は `bundle/` を「判定に使った唯一の走行」とする。 | 高 | `b_roots` へ一括追加しない。 |
| O2 | `remaining-references:output-same-root` の生ログ | 候補数と削除可能数は異なる。上位 40 root で同一 root と許容 docs category だけを理由に残る file は、例として t2380 に 49、t2700 に 27、t2826 に 10 件ある。ただし t2380 の `resolve/*.meta.json` は凍結結論の取得証拠、t2700 の走別記録は対比較の検算材料である。 | `classes.jsonl` を上位 40 root に限定し、`remaining-references` の category 集合が `output-same-root,docs/worklog,docs/spool,docs/other` の部分集合である行を計数。各 root の [README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-output-pruning/output/insights/2026-09-20/t2700-prewarm-ab/README.md:1) と照合。 | 高 | 理由だけで B にしない。 |
| O3 | 保護 regex | root 名に含まれる語が、その下の無関係な全 file に波及する。`certif` による D 190 件中 179 件、`witness` 232 件中 197 件、`provenance` 211 件中 177 件は、**root より下の相対 path 自体にはその語がない**。同様に `oracle` は 118 件中 113 件。これらは過剰保護の上限であり、削除可能件数ではない。 | `classes.jsonl` の最初に適用された `protect_path_regexes:<語>` を数え、`path[len(root):]` で再照合。例: `certif` は `aggregate-uncertified.json.gz` にも一致する。 | 高 | 保護を root 名と file 名で分けて再分類する。 |
| O4 | 同一 blob | 重複は大きいが、件数の大半は守るべき証拠の内部にある。全 27,176 target で同一 blob 群は 1,005 群、余剰 path は 5,462 件。最大群は t361–t362 の 0 byte raw 2,118 件で、事前登録が evidence 全体を対象にする。 | `classes.jsonl` を `blob` で group 化し、各群の `len−1` を合計。事前登録の「保存 evidence 全体で出現 0 件」は [verdict-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-output-pruning/output/insights/2026-08-16_t402-flock-execution-host/verdict-preregistration.md:24)。 | 高 | blob 重複だけを削除理由にしない。 |
| O5 | t2033 / OpenAlex mirror | 自 root の manifest だけが hash を持つ場合でも、現依頼の「sha256 束縛 file は外さない」に該当する。t2033 は `R4` が 2,120 件。 | `classes.jsonl` の root 別理由を計数。t2033 [README:35–36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-output-pruning/output/insights/2026-08-29_t2033-axis1-retake/README.md:35) は file ごとの SHA と manifest の digest を明記。 | 高 | 外すにはユーザー裁定が要る。manifest を残したまま対象だけ消す案は不可。 |
| O6 | t2817 / t2243 | 別 insight の `probe-ledger.md` が原本 path を列挙している。README の数値要約だけでは参照閉包を置換できない。 | root 別 `strong_categories` は t2817 が 739 件、t2243 が 368 件 (`classes.jsonl` 集計)。参照元は `output/insights/2026-09-21/login-check-count-wall/verbatim/probe-ledger.md`。 | 高 | 台帳の意味と検算手順を変更する別裁定なしに外さない。 |

## b_roots 候補

| root | 外せる file 数 | README の要約 | README が引く原本・判断 |
|---|---:|---|---|
| `output/insights/2026-09-20/t2700-prewarm-ab` | **0 件を推奨**。同一 root 等だけが分類理由の機械 file は計数 27 件 | 7 対の wall 差、中央値 +33.5 秒、片側 p=0.0078、E/L の失敗数を本文に記録。 | `analysis/`、`runs/`、`series/` を対比較の証拠として引く。`runs/*/artifacts.txt` も走の所在を示すため、27 件をそのまま B にできない。 |
| `output/insights/2026-09-21/t2825-ledger-refresh-ab` | **0 件を推奨**。同条件の分類行は計数 13 件 | 3 対の差と台帳再生成後の被覆を本文に記録。 | `ledger-evidence/removed.txt`、`ledger-evidence-land/dropped*.txt`、検算ログを個別に引く。凍結 entry と再生成値の照合材料を残す。 |
| `output/insights/2026-09-08_t2380-b5-closure` | **0 件を推奨**。同条件の分類行は計数 49 件 | README は凍結の三点を説明する。 | 49 件の多くは `resolve/*.meta.json`。取得元と候補の検証材料なので、単なる実行雑音と扱えない。 |

計数は `classes.jsonl` の各 root で、理由が `remaining-references:` で始まり、category が `output-same-root`・`docs/worklog`・`docs/spool`・`docs/other` だけの行に限定した。**上位 40 root から、現時点で設定可能な高確信度の `b_roots` は空**とする。

## c_roots 候補

| root | file 数 | 判断 | docs からの参照 |
|---|---:|---|---|
| `output/insights/2026-09-18/t2447-lens-p2-p6` | `c-pool.tsv` 上で 21 件 | **低確信度の次段候補**。実際の規則は `docs/dev-wave/` に収容済みで、root の大半は相談・レビューの逐語と再掲である。ただし [README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-output-pruning/output/insights/2026-09-18/t2447-lens-p2-p6/README.md:14) には採否理由と検査値があり、「自明」とは断定しない。 | `git grep -n 't2447-lens-p2-p6' 035fc11fa601547f5d68e54f5661c5daa70b93a5 -- docs` は **5 行**。主な hit は `docs/archive/worklog-phase3-0918-1651.md:1,4` の記録場所、残りは worklog 1 行と spool 2 行。decisions・failures・paper の hit はこの 5 行内では 0。 |

C を root 丸ごと削除することは、brief の I4「README.md は外さない」と両立しない。候補化するなら README を残した file 単位の次段検討となる。上表の root も第 1 段の削除は推奨しない。

## 規則の修正案

現行 `classify.py` は regex を **全 path** に適用する。まず root 以下の相対 path を別に判定できるようにした上で、次の設定に移す案である。`protect_relpath_regexes` は現行分類器には未実装なので、この断片をそのまま v4 config に投入してはならない。

```json
{
  "protect_path_regexes": [
    "(^|/)README\\.md$",
    "(^|/)(CMakeLists\\.txt|Makefile|GNUmakefile|pyproject\\.toml|pytest\\.ini)$",
    "(^|/)campaign\\.lock$|(^|/)wal\\.jsonl$",
    "\\.sha256$|\\.sig$",
    "^output/insights/2026-09-03_"
  ],
  "protect_relpath_regexes": [
    "prereg|pre-registration|preregistration",
    "freeze|frozen",
    "receipt",
    "manifest",
    "certif",
    "oracle",
    "witness",
    "provenance",
    "mutation",
    "(^|/)(trace|traces)(/|[._-])|anomal|verifier|serializ",
    "golden|fixture|(^|/)(positive|negative)[-_]control"
  ],
  "b_roots": [],
  "c_roots": []
}
```

これは**再分類用の案**であり、直ちに削除を許可する案ではない。相対 path 化で新たに候補となる file は、R4/R5、強い参照、test・道具の動的読取、事前登録による dir 全体の束縛を改めて照合する必要がある。正しさ材料を取りこぼさないことは、今回の理由別集計だけでは証明できない。特に t361–t362 evidence と OpenAlex mirror は regex に頼らず、それぞれ事前登録と hash で D に固定する。

## 総括

過剰保護の明確な箇所は、保護語が **root 名から全子 file へ波及する規則**である。一方、今回調べた上位 40 root には、高確信度で `b_roots` に追加できる塊は見つからなかった。大きな削減余地である hash 束縛の mirror、t361–t362 evidence、台帳に列挙された t2817 / t2243 は、現依頼の条件を越えるためユーザー裁定が要る。第 1 段は既存 A に留め、保護規則を狭めた再分類結果を次段の file 単位審査に回すのが妥当である。