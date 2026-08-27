---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: worktree-dev-wave-t1434-oracle-realdata
seq: 1
---

## {{D:t189-oracle-wiring-slice}}. task-specific oracle の実発火は限定 wiring slice と明示 profile で束縛する

**決定:** T-189 の task-specific oracle 束縛を実データで発火させる最小単位は、既存 task catalog の
実在 plan 2 行を持つ1つの wiring slice とする。slice は明示 CLI profileでだけ受理し、canonical bytes、
verifier tool bytes、manifest kind、許可 verb、catalog/evidence join、finding projectionをpinする。
組込みT-181 manifestは変更せず、従来の受理集合を維持する。

slice は§8の独立oracle ledger本体ではない。`oracle_content_review_status=not-established`、
`section8_complete=false`、task acceptance `unbound`、routing evidence `inconclusive`を固定する。
機械整合性、full CLIの`valid`、test緑を意味的受理へ射影しない。

**理由:**
- 組込みPOS/NEGは同じknown finding集合を持ち、task別集合とmanifest unionが同一なので、既存束縛は
  unionより狭い受理集合を一度も作らなかった。
- task catalogの実在2行はprompt、receipt、base commit、分類、fixed-state worklogへjoinでき、
  互いに素なfinding集合でaccept/cross-task rejectを作れる。
- profileをmanifest内fieldから推測すると、field削除によるdowngradeと、既存T-181拡張manifestの
  過剰拒否が同時に生じる。呼出側の明示profileなら両者を分離できる。
- D674の電力・外部custodian・署名見送りと、D767のacceptance unboundを動かさずに発火だけを示せる。

**却下した選択肢:**
- 組込みPOS/NEGのfinding集合を書き換える — 凍結されたT-181 provenanceとdigest連鎖を、発火目的で
  改変することになる。
- optionalな別verifierだけを置く — verifierを通さずmanifestとdownstream digestを再生成できる。
- 2 artifactの汎用generatorを新設する — finding内容の二重正本と生成順序の循環を増やす。
- sliceを§8 ledger完成またはtask acceptanceと扱う — 独立content reviewと意味的受理が未成立である。
- served-model attest、署名、汎用oracle platformまで広げる — 今回の発火確認に不要でD674の境界を越える。
