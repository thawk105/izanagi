| 所見 | 判定 | 根拠の file:line | 判断 |
|---|---|---|---|
| LUNA-01 | closed（コード側） | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-rulings/s6-fix-ruling.md:5`; `orchestrator/tests/calibration_freeze_authority_contract.py:84-95` | M1〜M6 spec 復元は親手番であり、コード側の追加対応は不要。 |
| LUNA-02 | closed（コード側） | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-rulings/s6-fix-ruling.md:6`; `orchestrator/tests/calibration_freeze_authority_contract.py:532-537,594-600` | docs 照合と state pin により M3 が KILLED になる実態は維持。erratum は親手番で、コード変更不要。 |
| LUNA-03 | partial | `orchestrator/tests/calibration_freeze_authority_contract.py:63,273-281,299-340`; `orchestrator/tests/test_calibration_freeze_authority_contract.py:664-684` | 通常の HTML comment 隠蔽は閉じたが、code fence 内の opener を誤認して可視行を消し、緑になる構成が残る。追加 node も受理集合差ではなく診断差だけを検出する。 |
| LUNA-04 | closed | `orchestrator/tests/test_calibration_freeze_authority_contract.py:227-234`; `orchestrator/tests/calibration_freeze_authority_contract.py:496-508` | 陽性 node は snapshot pin と正しく分類された。production の拒否能力とは主張していない。 |
| LUNA-05 | closed | `orchestrator/tests/test_calibration_freeze_authority_contract.py:186-224` | projection node は fixture・manifest・定数の snapshot assertion と正しく分類された。 |
| SOL6-01 | closed | `orchestrator/tests/test_calibration_freeze_authority_contract.py:135-180,537-574,704-740` | 指摘された既存 node は期待値更新・等価再照準として「中立」に修正され、実態と一致する。 |

### FOCUS-01 / blocker

- **破れる具体構成:** §8.1 の現行行を、code fence 内の `<!--`、fence 外の変更済み Markdown 行、`-->`、旧 canonical 行の順に置く。除去前は変更行と旧行の重複で拒否されるが、除去後は regex が fence 内 opener から fence 外 closer までを削除し、旧行だけを抽出して `validate_repository` が緑になる。
- **根拠の file:line:** `orchestrator/tests/calibration_freeze_authority_contract.py:63,273-281,299-340,532-537`
- **成果物影響:** 可視設計に変更済み selection と旧 selection が併存する曖昧な文書を受理し、certified selection／レポートを旧 literal に束縛できる。

### FOCUS-02 / must-fix

- **破れる具体構成:** 追加 node と同じ「comment 内の旧 Markdown 行＋可視の変更済み Markdown 行」を使い、comment 除去を無効化する。除去前も duplicate ID で拒否、除去後も enum drift で拒否され、変わるのは診断理由だけである。
- **根拠の file:line:** `orchestrator/tests/test_calibration_freeze_authority_contract.py:124-132,664-684`; `orchestrator/tests/calibration_freeze_authority_contract.py:299-316,320-340,532-537`
- **成果物影響:** 受理集合を一件も変えない診断文字列差を mutation kill と誤認し、台帳・proof chain が comment 防壁の検出力を過大報告する。

## 受理集合再監査

comment を含まない現行設計文書では、除去前後で4抽出結果（row IDs、ruling IDs、selection enums、段 gate ID）はすべて同一だった。現行の権威箇所は `docs/calibration-freeze-authority-bundle-design.md:494-520,638-647`。

fix 前後の状態遷移は、文書変種を類型化すると全4類型である。

| 方向 | 類型 | 評価 |
|---|---|---|
| 通る→落ちる | comment 内だけに canonical literal を残し、可視側を非対応形式で変更 | 意図した縮小。元の LUNA-03 は閉じる。 |
| 落ちる→通る | comment 内の duplicate／decoy literal を無視し、可視 canonical 行だけを採用 | comment 非権威化に伴う意図内の拡大。raw 入力の受理集合が「縮小だけ」という説明は厳密には誤り。 |
| 通る→落ちる | 対応する `-->` のない `<!--`。code fence 内の文字列や単独 `<!-->` も含む | 意図外の縮小。抽出に無関係でも一律拒否する。 |
| 落ちる→通る | code fence 内 opener、または `<!-->` から後続 `-->` までを comment と誤認し、可視 drift を削除 | 意図外の拡大。FOCUS-01。 |

迂回別では、通常の入れ子隠蔽は旧行欠落で拒否された一方、無関係な `<!-- outer <!-- inner --> outer -->` 自体は stray `-->` を検査せず緑だった。単独 `<!-->` は fail-closed、後続に `-->` がある形は span 全体を除去して緑になり得る。code fence 内 opener は、未閉鎖なら拒否、fence 外 closer と組み合わせると緑で抜ける。

## 総括

NO-GO。通常の HTML comment 隠蔽は閉じ、現行文書の抽出結果も不変。  
ただし Markdown context を無視した除去により、fix 前に拒否された文書が緑になる blocker がある。  
追加負例も受理集合差を検出せず、診断差だけの mutation sensitivity である。  
blocker 1、must-fix 1。pytest は制約どおり再実走していない。