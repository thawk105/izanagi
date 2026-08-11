---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t750-freeze-v2-manifest
seq: 2
---

## {{D:pinned-literal-human-approval}}. 人間承認は pinned literal で表し、Git trailer を認可根拠にしない

**決定:** 「人間が承認した」ことを機械が読む必要がある箇所では、承認対象の bytes hash を
**production module 内の pinned literal** として置く。未承認のあいだ定数は `None` とし、
その状態ではあらゆる入力を fail-closed で拒否する。approval を発行する CLI・API・
`--approver` 引数・既定補完は作らない。Git の commit message・trailer
(非 merge commit や逐語 `AI-Agent: none` を含む) を承認の根拠にしてはならない。

**理由:**
- D86(8) は「認可の実体はユーザーの明示指示であり、submission artifact はその指示が実行された
  記録にとどまる。artifact の存在を認可の証明として扱ってはならない」と定めている。
  AI は自分で commit を作れるため、trailer を根拠にすると承認が恒真化する。
- pinned literal なら、AI が承認者になるには**人間がコード diff をレビューして定数を置く**しかない。
  これは v1 freeze の bytes 定数や env contract の reviewed golden と同じ既存パターンであり、
  新しい trust root を発明しない。
- `None` 既定により、承認前は機構全体が動かない。証拠が無い状態で先に進む経路が構造的に無い。

**却下した選択肢:**
- **Git trailer による承認** — 上記のとおり恒真化する。段 3 の敵対レンズが独立に指摘した。
- **approval record JSON の存在をもって承認とみなす** — 同じ主体が record も対象も書けるため、
  自己整合な偽物と本物を区別できない。
- **人間だけが保持する鍵による署名** — 方向としては正しいが、repo に鍵管理の trust root が無く、
  新設は D86 の再裁定を要する。恒久形の裁定はユーザーへ返す。

## {{D:manifest-choke-point-cell-product}}. 実行経路の gate は CLI でなく共有 verifier に置く

**決定:** 成果物の受理集合を狭める gate は、新設した CLI ではなく**実行経路が必ず通る共有
verifier** へ置く。oracle manifest では `verify_manifest` に cell-product 検査を置き、
schedule の holdout 集合が active freeze の holdout 集合と exact 一致すること、および
cell 集合が「全 holdout × 各 holdout の構成集合」の積と exact 一致することを要求する。
生成側の generic builder の受理集合は変えない。

**理由:**
- driver の `run-block` は任意の manifest path を受け取り共有 verifier へ通すだけであり、
  新設 CLI を経由しない経路が実在する。CLI 側にだけ gate を置くと**誰も通らない gate**になる。
- judge には部分的な product 検査があるが、holdout 間で構成集合が食い違う場合しか捕えない。
  全 holdout で一様に間引いた schedule は素通りし、judge が唯一の候補を最良と判定する。
  これは certified 選択の直接改変である。
- 検査を verify 側に置くと方向は受理集合の縮小のみになり、生成側 API の互換を壊さない。

**却下した選択肢:**
- **CLI にだけ置く** — 上記のとおり迂回される。
- **generic builder に置く** — 既存 programmatic caller の受理集合を狭め、互換を壊す。
- **judge の部分検査に任せる** — 一様な間引きを捕えない。

**併せて記録する失敗型:** 期待 cell 積を「与えられた schedule 自身」から導くと、
gate は**入力が名乗った範囲の中でしか完全性を要求しない**。積の定義域は必ず
authority 側 (この場合は freeze) から取る。本 wave の初版はこの形で、
holdout を丸ごと落とした manifest を受理していた。
