<!-- ruleops-insight: {"authority":"none","default_effect":"no-state-change","schema_version":"ruleops-insight/v1"} -->
# T-1539 `output/insights/**` retention precheck

- audit pin: `402a5752b9cf59a769f5b5af17e56b67a68190f1`
- artifact class: derived-report
- state authority: none
- default effect: no state change
- 結論: 削除適格と立証済みの exact path は 0 件。母集合全体は未分類のため全 file を非変更とした。
- 削除・移動・gzip 置換・branch 操作・checker/script 追加: なし

## 1. 結論の読み方

本 precheck は「8,963 files がすべて retention 必須」とも、「技術的に削除可能な file が 0 件」とも
判定していない。現行の正本と実 control では機械的な削除適格性を成立させられないため、
ユーザー裁定どおり推測で削除せず止めた。正確な状態は次表である。

| 集合 | 件数 | 意味 |
|---|---:|---|
| audit pin の tracked regular blob | 8,963 | 棚卸し母集合 |
| RuleOps UTF-8 inventory items | 7,971 | 観測可能。削除分類済みではない |
| RuleOps `skipped_non_utf8` | 992 | path 非開示・未分類 |
| technical eligibility | unknown | 機械述語未実装、closure 未評価 |
| RuleOps ledger candidates | 0 | candidate package なし |
| authorized delete | 0 | `human_approved:false` |
| proven eligible exact delete paths | 0 | 実 DELETE control なし |
| action | 0 deleted / 0 bytes | NO_DELETE |

元裁定が測った commit `2379621cc325e5f470ca34664845c687dbd34507` は 8,928 files /
66,186,605 bytes だった。audit pin は 35 files / 1,032,788 bytes 増えて 8,963 files /
67,219,393 bytes である。filtered な RuleOps item 数を corpus 総量として使っていない。

## 2. 正本が許すこと

source artifacts:

- `docs/archive/worklog-phase3-0823-860.md` の [T-1539]
- `docs/decisions.md` D361
- `output/README.md` の proof chain と insights の寿命管理
- `docs/ruleops.md` の安全境界、retirement lifecycle、既知限界

D361 は、論文・現状把握・再現に使う receipt、測定結果、裁定 package、insight 等を tracked で
残す。`docs/ruleops.md` は RuleOps v1 を read-only inventory / draft / structural check に限定し、
age、size、参照数、state-authority marker だけで削除安全と分類すること、既存 insight の一括分類、
自動削除を認めない。`check` の成功は構造整合だけで、人間承認や削除安全ではない。

## 3. control

### KEEP control A — 0 byte の absence observation

次の exact path は Git の empty blob だが、削除候補ではない。

`output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260803T150807Z-5809d1d8d4d2f8c5/attempts/t361-flock/20260803T150808Z-t361-flock-a1-9060899fb1686d87/work/controller/raw/00001-rbudgetcheck-before-qsub.stderr.raw`

- Git blob: `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`, size 0
- SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `source-tree-inventory.json.gz` は相対 path、同 SHA-256、size 0 を記録する。
- `tracking-receipt.json.gz` は `work/` 付き exact path、同 SHA-256、size 0 を記録する。
- sibling の stdout と組になり、「stderr が無かった」という観測を保つ。

したがって 0 bytes、同一 blob、多数回出現という属性は単独では residue の意味を持たない。

### KEEP control B — 現行 phase の直接参照

`output/insights/2026-07-19_backlog-triage.md` は `docs/phase3.md` の T-014〜T-020、
T-021以降の複数項が発火述語の正本として直接参照する。literal hit は不完全な signal だが、
この direct consumer だけで削除不適格である。

### Active exclusion control

起動時に固定した Claude 7 / Codex 5 worktree を照合した。Claude の
`dev-wave-known-violation-review-20260823` は branch 固有 insight 11 committed + 3 dirty、
`dev-wave-t1484-floor-restart-registry` は 16 committed を持っていた。残る起動時10 worktreeは
その snapshot では branch 固有 insight 0だった。いずれも稼働所有物として候補母集合から除外した。

監査中に全 registry は 34 worktreeへ増え、branch 固有 insight pathも30から31へ動いた。
これは非原子的な単発 scan を将来の削除根拠にできない実測である。今回は削除をしないので、
起動後に増えた worktree の artifact 内容を読まず、retention 判断もしなかった。

### DELETE control — 不成立

現 corpusでは、調べた editor/cache/temp basename が0、trackedな非圧縮pathと同名`.gz`の併存が0、
RuleOps production candidateが0だった。実在する exact DELETE control は得られなかった。

過去のT-201 commit `114c5c4dfc8e723d2af3e577bf45f28305144c56`は、981 sourceを同数の
決定的gzipへ置換した可逆なretentionであり、内容廃棄controlではない。T-403 commit
`772456feb1f71a6137058dd5e87262c7c51678bc`はinsight内でD 3 / A 6 / README M 1を同時に持つ。
内容を本waveのscopeで再判定していないため、「後続版を伴う履歴上の変更」とだけ扱い、
安全な廃棄前例とは数えない。全履歴の廃棄例を網羅したという主張もしない。

## 4. 将来必要な条件

これは実装済みretention規則ではない。次の全条件が揃ったときだけ、別waveで機械判定可能性を
再評価できる。

1. pinned HEAD内のrepository正本、または正本が明示委任したtracked producer schema/READMEが
   定義するresidue class。
2. 現HEADに実在し、そのclassへ到達するexact DELETE controlと、同じpath固有適格性述語で
   falseになるexact KEEP control。
3. candidateのmode、path、blob、bytes、HEAD pin。
4. docs、worklog、decisions、failures、paper、code/test、manifest、receiptのreference closure。
5. source、derived report、receipt、ledger、raw/verbatim、failure、erratum単位のartifact closure。
6. manifest entryのpath、digest、sizeとtracked blobの一致。
7. 全worktreeの開始snapshotと終了snapshotのpath/HEAD一致。不一致なら結果を破棄して再走査する。
8. 上記stable scanを分類直前と削除直前の2回行い、branch unique commit差分とdirty/untrackedを除外する。
9. RuleOps package、独立review、人間承認、削除直前のpackage再生成。

package authorizationはpath固有の技術適格性と別gateにする。`human_approved:false`をpath述語へ混ぜて
全件falseにする判定はcontrolの識別能力を示さない。

## 5. 再現

主要値は次の既存toolで再現した。audit pinの値と、record commit後のpost-record検査を混ぜない。

```bash
git rev-parse HEAD
git ls-tree -rzl 402a5752b9cf59a769f5b5af17e56b67a68190f1 -- output/insights
git ls-tree -rzl 2379621cc325e5f470ca34664845c687dbd34507 -- output/insights
python3 tools/ruleops.py inventory --kind insight
python3 tools/ruleops.py check
git diff-tree --no-commit-id --name-status -r 114c5c4dfc8e723d2af3e577bf45f28305144c56 -- output/insights
git diff-tree --no-commit-id --name-status -r 772456feb1f71a6137058dd5e87262c7c51678bc -- output/insights
git worktree list --porcelain
```

0 byte / duplicate groupの補助観測は、1,693 zero paths、75 duplicate groups / 3,550 pathsだった。
これらは分類権威に使わず、実KEEP controlを含むため単独削除signalにならないことだけを確認した。
補助集計のone-off helperはtracked checkerとして残していない。実DELETE controlがなくtrue側を実証
できないため、persistent checker/scriptを作るとDW-O13の到達値条件を満たさず、D95のauthorを
起動しても検出力を示せない。

## 6. scope外へ返したもの

- T-1547の内容確認、status変更、大規模sampleの移行
- branch/worktreeの削除
- active artifactの内容とretention判断
- paper figure/table、裁定/失敗参照、raw/verbatimの個別retention判断
- 非UTF-8 992 pathsの内容分類
- 新checker/script、RuleOpsの受理集合変更、既存insightの一括移行

このprecheckは上記を完了扱いにしない。
