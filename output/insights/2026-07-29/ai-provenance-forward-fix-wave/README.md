# [T-187] `6b64d21` AI provenance forward-only 是正

## 結論

対象`6b64d21753d2cfc790f80caba29df7a40fef3072`は共有済み2-parent mergeなのでrewriteしない。
strict descendant 1件の固定`AI-Agent-Correction`で、対象のmissing findingだけを相殺する。
件名`Merge branch ...`自体は違反ではなく、問題は必須`AI-Agent` trailerの欠落である。

## 回収した観測

- 元eventの構造化field: product=`claude`、model=`claude-opus-5`、effort=`xhigh`
- 行為裁定: role=`integrator`。merge前にmain進行と番号衝突を検査し、統合を選択したため
- correctionから除外: `scope=main-sync`は後日の分類で、元観測ではない
- event行SHA-256:
  `6bd12c991bd1f2918e49e149e7dea53b1c1c567df5d71e04b587550a25de069f`
- session IDはtracked evidenceへ残していない
- `MERGE_RC=0`は`git merge ... | tail`の`tail` rcなのでGit成功証拠ではない。merge成立は
  約5秒後の2-parent objectで確認した

exact payload:

```text
AI-Agent-Correction: target=6b64d21753d2cfc790f80caba29df7a40fef3072; product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
```

## 受理契約

checkerは次の連言時だけ対象missing findingを除く。

1. raw物理1行、隔離canonical parse、通常final blockがすべてexact
2. selected revision setにtargetとcorrectionが各1件
3. correctionがtargetのstrict descendant
4. targetが実際に`AI-Agent` missing
5. correction commit自身が通常監査green

一般registry、環境変数、Git config、CLI免除はない。他commit、CAB、scope、Codex-author findingは
保持する。targetを含まない`OLD_HEAD..HEAD`はcorrection初回伝播の権威にせず、target-inclusive
rangeまたは既定full-historyを使う。

## mergeとD95

targetの通常`diff-tree` pathは空、全parentと異なるpath集合はdocs 3件、per-parent unionは実装面を
含んだ。全parentとの差分積をpreflight/historyで共通化し、sideから持ち込まれただけの実装を当該
merge actorの新規authoringと数えない。積集合は手動conflict resolutionの証拠ではなく、
role=`integrator`はmerge前の判断から裁定した。

## dev-wave裁定

- branch上では`T-186` / `D100`として記録したが、main側の先行採番と衝突したためland時に
  `T-187` / `D101`へ振り直した。既存commit件名は履歴非改変のため元番号を保持する
- main統合後の全履歴監査がlocal-only T-180記録`cb79147`のprobe ShellにCodex authorがない
  別違反を検出。ユーザー承認後、Codex authorが最終bytesへ実際に寄与した`677c32a`へrewriteした
- 再構成統合commitは`226f7fd`。統合後finalは`3892 passed, 18 skipped in 252.36s`、
  関連250 passed、full-history provenance 541件green
- Stage 2 plannerの旧復元値は一次証拠不足でNO-GO。採用していない
- Stage 3 adversarial review 2本もplan v1をNO-GO
- Stage 6 review 2本はblocker 7件を返した。親裁定後にfix 2巡、focused re-review 2本で
  code blocker 0・GO
- 親の関連test: `116 passed in 4.80s`、py_compile/diff check rc=0
- commit後の変異: outcome-changing 9/9 KILLED、structural/diagnostic pin 2/2検出、
  survivor 0、正制御3件green。復元後source SHA-256はcommitと一致
- 最終受入: `3807 passed, 18 skipped in 242.42s`、関連test再実行`116 passed in 4.54s`、
  docs / Codex agents / diff check / full-history provenanceがgreen
- 変異の事前登録と再登録は`s4-adjudication-plan-v2.md`と`s6-review-adjudication.md`
- machine-readableな変異結果は`mutation-ledger.json`
- fix前snapshotを各fix投入前に固定し、修正範囲の照合に使用した（中間patch自体は正本へ採用しない）
- correct evidence=`s1-recovery-evidence.md`、最終裁定=`s6-review-adjudication.md`

中間prompt、run log、旧値を持つ棄却planner草案は正本へ採用しない。
