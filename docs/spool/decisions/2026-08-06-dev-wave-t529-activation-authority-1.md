---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t529-activation-authority
seq: 1
---

## {{D:activation-authority-blocked-on-historical-resolver}}. 活性化権限は historical resolver より先に実装しない

**決定:** 契約世代の活性化権限 (activation record からの権威導出と全入口の activation receipt) を
実装する前に、artifact に記録された contract hash から世代を解決する historical resolver と
versioned predicate dispatch を production consumer へ配線する。D176 の bootstrap fuse は
それまで外さない。活性化機構の設計案・入口同定・命名は
`output/insights/2026-08-06_t529-activation-authority/` へ凍結し、実装は保留する。

**理由:**
- committed floor protocol は現行 pegasus 契約の `contract_sha256` を固定しており、
  `s8b_floor_contract.validate_protocol` は artifact の値と
  `contract_sha256_lookup(env_tag)` の一致を fail-closed で要求する。
  `s8b_ratified_freeze` はその lookup に **current** の registry lookup を渡す。
  同型の current 比較は ratified freeze の journal / run-command 再検証と oracle report にもある。
  したがって 2 世代目を current にした瞬間、既存の certified floor / freeze / selector /
  oracle report が「過去には有効だったが current でない」という理由だけで解決不能になる。
  親が実測で確認した (protocol の hash と現行 lookup の hash が一致することを確認)。
- よって fuse を外しても較正の再取得は進まない。blocker が fuse から履歴解決の不在へ移るだけであり、
  活性化権限だけを先に入れても目的を達成しない。D176 自身が
  「履歴 resolver は production の消費者を持たない data 層の準備である」と限定していた。
- 活性化機構のうち今すぐ実装できる部分集合は、2 世代目を無条件拒否する実装と観測的に区別できない。
  正例 (正規 evidence を持つ有効な 2 世代目が current になる成功ケース) を書けないためである。
  区別できない実装を land すると、後続の読み手は活性化権限が実在すると誤読する。
  これは D176 が型分離を却下した理由と同型の「名ばかりの保証」である。
- 発火条件を満たす artifact path も計測 ID も現時点では書けない。2 世代目の取得は
  pin 済み依存 source の消失と source proof の欠落で塞がれている。
  条件付き機能の発火 gate (`docs/dev-wave/core.md` の `DW-G04`) は
  この場合「設計メモに留める」と定めている。

**却下した選択肢:**
- 活性化 record と権威導出だけを先に land し、入口 receipt を後続 wave へ送る —
  正例を書けないため永久 fuse 実装と区別できず、台帳に名ばかりの保証が残る。
- fuse を外して 2 世代目後の旧 artifact 拒否を受理縮小として承認する —
  certified 成果物の参照鎖を切る。承認されていない受理縮小である。
- 活性化 record の非偽造性を acquisition receipt の存在検査だけで担保する —
  同 receipt は自己申告値の schema であって publisher の実行を証明しない。
  trust root の定義は別途裁定が要る。

## {{D:env-contract-activation-naming}}. 活性化状態の識別子は `activation_serial` / `activation_state_sha256` を使う

**決定:** 契約世代の活性化状態を表す識別子は、単調増加整数を `activation_serial`、
活性化状態全体の hash を `activation_state_sha256`、直前状態の hash を
`previous_activation_state_sha256` とする。`migration_epoch` と `bundle_hash` は使わない。

**理由:**
- repo 内で `epoch` は unix 時刻の一義で使われている (qsub の submit 時刻、予約の deadline、
  収集の完了時刻、scheduler の開始時刻)。単調増加カウンタへ流用すると同名識別子が 2 義になる (D75)。
- `migration_*` は既存の freeze migration 識別子と近く、一回限りの移行を指す語として定着している。
- `bundle` は role bundle の hash と silo の raw bundle という別義が既にある。
- `state` は「全 env の active contract 集合と serial・直前 hash を含む状態」の hash であることを
  正確に表し、既存語の意味を増やさない。静的検索で 3 語とも既存衝突ゼロを確認した。
- 段 2 と段 3 の 2 レンズが独立に親の暫定命名を否定し、この案を支持した。

**却下した選択肢:**
- `migration_epoch` / `bundle_hash` — 上記のとおり既存 2 義を 3 義にする。
- 無修飾の `generation` を新 receipt の field 名に使う — 契約世代と LLM 提案世代が
  同一 document 内で無修飾に混在しうる。receipt へ直列化する段では
  `env_contract_generation` のように namespace を付ける。
