---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: t575-silo-promotion-consumer
seq: 1
---

## {{D:silo-promotion-consumer-absent}}. 確認した静的参照閉包では silo ladder 証拠の適格性昇格 consumer は不在であり、ability-probe writer を「silo 昇格入口」に数えない

**決定:** 基準 commit `75bea8e5f` で確認した静的参照閉包では、silo ladder の characterization 証拠を
検査・発行する consumer は実在するが、**その証拠を研究目標・回復計測・通常 pipeline の適格性へ
昇格させる consumer は不在である**。したがって契約世代の活性化権限が数える入口集合へ
ability probe の writer を「silo 昇格入口」として置かず、その結線をもって昇格入口を守ったと報告しない。
判定対象は適格性への昇格に限る。**silo の書込み入口そのものは実在するので、入口調査から silo を外さない。**

**判定の射程 (これ以上を主張しない):**

- 「不在」は**適格性への昇格**についてのみ言う。証拠の受理・公開・再検証・射影除外・依存取得の
  各 consumer は実在する。これらを「何も無い」と読んではならない。
- 確認したのは、既存 ledger・artifact schema・識別子・公開 helper・CLI・登録表から到達する
  静的参照閉包である。任意の別名や汎用プログラムによる読取りまで含めた不存在は証明していない。
- D196 の保留理由をそのまま現在の blocker として再掲しない。historical resolver の配線充足は
  D215 が別途記録しており、残る理由はそちらが正本である。

**理由 (実測、基準 commit `75bea8e5f`):**

- **producer に適格な成果物を出す枝が無い。** `orchestrator/campaign/silo_ladder_rung1.py:4960-4964`
  は発行 document の `classification` を `evaluation_role="ability_probe"` /
  `research_goal_eligible=False` / `recovery_measurement_eligibility=False` のリテラルで固定する。
  再読側の `orchestrator/campaign/silo_ladder_rung1.py:1273-1278` も同値を要求する。
- **ladder driver は自身の用途を raw 側と宣言している。**
  `orchestrator/campaign/condition_meaning_gate.py:3478-3480` の
  `_PROMOTION_USE_CLASSES` は `certified-selection` / `floor` / `oracle` / `paper` の 4 つで、
  ladder driver は `orchestrator/campaign/silo_ladder_rung1.py:2236-2237` で
  `use_class="raw-measurement"` を渡す。**これは用途の宣言であって、機械的な昇格禁止ではない** —
  同 gate の受理判定 (`orchestrator/campaign/condition_meaning_gate.py:4098-4103`) は
  supply が green・meaning が非 red かだけを見ており、raw と promotion で分岐しない。
  昇格用途を渡す production の call site は oracle に限らず、
  `orchestrator/campaign/p3_s4_loop.py:441` の `certified-selection` や
  `orchestrator/campaign/paper_story_a2_certification.py:784` の `paper` などが実在する。
  不在判定の根拠は、この宣言だけでなく下記の classification と参照経路の調査を合わせたものである。
- **ledger 側の consumer は負制約であって昇格権威ではない。**
  `orchestrator/campaign/silo_ladder_rung1_contract.py:517-518` は entry 数が 1 でないことを違反として
  記録し、`:539` 以降は既存 entry の非適格値を exact に要求する。
  `orchestrator/campaign/projection_guard.py` の射影除外も、ability-probe 指定から**拒否**を作る側である。
  これは D162 決定 (7) が ledger の 3 適格性 field について既に述べたことと同じ向きだが、
  本判定は **ledger を経由しない経路** (成果物 classification、condition gate の use class、
  materializer 登録、共有依存 helper、shell/PBS writer) まで広げて確認した点が異なる。
  D162 決定 (7) だけでは本件は閉じない。
- **silo 側の書込み入口は実在する。** `tools/pegasus/silo_ladder_rung1.sh` は Python driver より前に
  ディレクトリを作り、`tools/pegasus/submit_silo_ladder_rung1.sh` は submission 領域と submit receipt を
  書く。これらは ability evidence の生成経路であって昇格ではない。両者を混同すると、
  昇格入口数の訂正が書込み入口の過少計上へ変わる。
- **探索範囲。** `docs`・`orchestrator`・`tools`・`hooks`・`src`・`patches`・`AGENTS.md`・
  `CLAUDE.md`・`README.md` に加え、`output/` 配下の現用 README も読んだ。
  記録された検索 argv は `docs/archive/**` を除外し、段 3 の一方のレンズは `output/insights/**` も
  除外している。凍結された裁定資料は逐語を別途射影して読んだ。
  この除外条件の下で、本判定を追記する前の時点では `silo 昇格入口` の完全一致は 0 件だった
  (本 D と同 wave の記録自体が、以後この語を現行側へ持ち込む)。
  完全一致 0 件だけでは意味的同値の不在を導けないため、`admit` / `accept` / `qualify` /
  `register` / `enroll` / `graduate` / `elevate` / `採用` / `格上げ` / `本採用` / `正式化` と
  silo・ladder・rung の同一行検索、および shell・PBS・CMake・Makefile の識別子検索を併せて行った。

**却下した選択肢:**

- **証拠の受理・公開を昇格と数える** — `classification` は非適格のまま固定され、ledger の
  `pipeline_eligible` も変わらない。公開でファイルが参照可能になることを適格性の獲得と
  同一視すると、ability evidence の生成を昇格入口の実装として数えることになる。
  これは「ability probe を結線して昇格入口を守ったと報告しない」という既裁定に直接反する。
- **「昇格 consumer は 0 件」と無限定に書く** — 検査・公開・再検証の consumer は実在する。
  無限定の否定は、後の読み手が「silo には何の受理機構も無い」と読む余地を残す。
- **D162 決定 (7) を転用して本件を閉じたことにする** — 同決定の対象は ledger の 3 適格性 field を
  昇格権威として読む consumer であり、ledger を経由しない経路は射程外である。
- **昇格 consumer を新設する、または適格性 sidecar を置く** — 本判定の依頼は既存 consumer の同定と
  文言の訂正であり、昇格機構の新設は scope 外である。D18 は inert patch の昇格を人間判断と
  定めている。現在の発火条件が充足しているかどうかは本判定では測っていない。
- **入口登録制度・恒久監査・一般化した検査を足す** — 本判定は 1 件の不在確定であり、
  同型欠陥が独立に 2 件再現した事実は無い。
