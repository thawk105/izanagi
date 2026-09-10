# 段 6 裁定追補 4 — 焦点再レビューの裁定と fix-4 (回帰修復のみ) の scope

焦点再レビューは NO-GO。所見は**すべて real** と裁定する (refuted 0)。
ただし `DW-O16` の「fix は 3 巡を上限」に達しているため、**新規 scope の fix は行わない。**
例外として、**fix 巡が自ら作り込んだ内部矛盾 (回帰) 2 件だけ**を fix-4 で修復する。
それ以外は親が裁定して閉じ、残余は段 7 で「未達」として記録し後続タスクへ送る。

## fix-4 で直す回帰 2 件 (これ以外は触らない)

### R-1. coordinator が生成する PBS script が wrapper を起動できない

生成 script は `exec python3.10 …/wrapper.py` だが wrapper CLI は `--request` 必須。
現行の正例そのものが argparse error で落ち、preflight が 1 件も生成されない。
さらに `publish_wrapper_request()` は qsub 後にしか判明しない identity を要求するため
qsub 前に呼べない。

**裁定する契約:** wrapper request を**静的部分と runtime 部分に分離**する。

- 静的 request (slot 計画・prereg projection・policy digest・runner policy digest) は
  **qsub 前**に coordinator が create-only で publish し、manifest へ digest を束縛する。
  PBS request ID・hostname・CPU allocation を**含めない**。
- 生成 script は `--request <静的 request の絶対 path>` を渡す。
- runtime identity (PBS request ID・実 hostname 等) は node 側が **node event へ**書く。
  静的 request を書き換えない。

### R-2. node の repo-absence false 固定を ready barrier が必ず拒否する

fix-2 が「node からは証明できないので false 固定」にした一方、coordinator は
`package_repo_free` 等が true でなければ `preflight_failed` にする。正規 wrapper の
preflight が必ず cancel される。

**裁定する契約:** repo 不在は **node の自己申告を合格条件にしない**。

- coordinator は node の当該 boolean が false であることを**正常**として扱う
  (true を要求しない。true を申告してきたら逆に拒否する — 証明不能な肯定だから)。
- 代わりに coordinator 側の root 外部性検査 (既存) と、node event の limitations に
  `repository_absence_not_proven_from_node` が**宣言されていること**を合格条件にする。
- `git_ancestor_absent` のように node がローカルに実検査できる項目があるなら、その項目だけは
  実検査結果を使ってよい (実検査の有無を子が実装で確認し、報告に書く)。

## 親が裁定して閉じる残余 (fix しない。段 7 で「未達」として記録)

| 所見 | 裁定 | 理由 |
|---|---|---|
| 焦点 #3 任意 wrapper の qsub (A-2/A-8/B-4 の partial) | **real・未達** | wrapper path/hash を凍結 package の実 bytes へ束縛するには、package staging と build manifest の実装が要る。本 wave の scope 外 (§9.1 の builder 側)。 |
| 焦点 #4 偽 git identity での repo 外判定迂回 (A-7 partial) | **real・未達** | live git common-dir を effect 前に取得する形へ変えるのは coordinator の入力契約変更。fix 3 巡を超える。 |
| A-1 partial (guard/budget receipt を実 producer・実 ledger bytes へ未束縛) | **real・未達** | producer の production 結線が要る。焦点 must-fix 4。 |
| B-3 regressed → R-1 で部分修復、残りは未達 | **real・部分** | R-1 で正例経路の起動は通す。guard/budget producer の結線は未達。 |
| executable forbidden-name の被覆縮小 | **real・nit** | 実装は全 fragment を拒否する。単独変異で殺せないだけ。段 7 に記録。 |

## 段 7 で必ず書くこと (親の義務)

- **§9.1 item 1 は充足していない。**(a)〜(g) の機構は実装したが、
  **coordinator → script → wrapper → coordinator の production 正例経路は 1 本も通っていない。**
- 未達 must-fix 7 件 (焦点レビューの優先順) をそのまま後続タスクの起票内容にする。
- 変異 matrix の結果と、テスト弱体化ゼロ・10 変異 KILLED (静的判定) の事実。
