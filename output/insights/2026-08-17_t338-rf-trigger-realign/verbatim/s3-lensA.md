dev-wave 段 3 として静的検査のみ実施した。pytest・受入検査は実走しておらず、緑は主張しない。

### 所見 1 — P2 は D162 発火用 measurement の canonical 受理集合を、文言上は「attestation が無いが他三項を持つ計測」まで広げる

**自己判定: real**

旧条件は attestation を明示的に要求する一方、プランはこれだけを削除しながら受理集合不変を主張している。[docs/decisions.md:8051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:8051)、[s2-plan.md:57](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:57)、[s2-plan.md:104](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:104)

ただし T139 の intended measurement は pilot receipt であり、当該 receipt は環境証明を必須としている。[preregistration.md:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:260)、[preregistration.md:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:278)。さらにその record-items と schema は D282 で exact 承認済みである。[docs/decisions.md:12911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:12911)

したがって二択になる。

- D162 の measurement を D282 準拠 receipt に限定するなら、attestation は別面で必須なので削除は実効ゼロ。
- 限定しないなら、従来拒否された unattested measurement が発火証拠として新たに受理される。

プランはどちらかを固定していない。D162 の Python consumer が 0 件という M3 は、現時点の機械的受理が動かないことしか証明せず、canonical な発火証拠集合の不変を証明しない。

**成果物影響** — executable な certified 選択や材料レポートは直ちに変わらないが、D162 発火証拠の受理集合が広がり、従来不適格だった measurement を根拠に validator/consumer 実装へ進める。

**最小の是正案** — D162(ii) の評価領域を D282-pinned receipt と独立検証済み evidence に限定し、attestation は receipt/admission 側で引き続き必須と逐語で書く。unattested receipt を許す意図なら D282 との関係と受理集合拡大を明記し、「不変」の主張を撤回する。

### 所見 2 — 残る三項は intended receipt 上では必須 field なので恒真であり、pre-validator 段では producer の自己申告値なので正しさ gate になっていない

**自己判定: real**

T139 schema は `environment`、`measurement_checkout`、`dependency_pins` をすべて必須とする。[receipt-schema-v1.json:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:302)、[receipt-schema-v1.json:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:1220)。したがって schema-conformant receipt の集合では三項すべてが常に存在し、(ii) は何も拒否しない。

一方、schema 適合は受理ではなく semantic validator が必要だが、その validator は未実装である。[record-items-v2.md:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:739)、[record-items-v2.md:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:825)、[orchestrator/preregistration/__init__.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/preregistration/__init__.py:3)。D229 自身も producer が選べる入力集合は保証に対して恒真相当になると警告している。[docs/decisions.md:10767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:10767)

M4 の根拠である `contract.py` は明記どおり Pure T-126 contract であり、未実装の T139 pilot admission を強制する consumer ではない。[contract.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/qualification/contract.py:2)

**成果物影響** — producer が三つの field を置くだけで D162(ii) を通過でき、発火条件の拒否力が実質的に (i) と (iii) だけへ縮む。

**最小の是正案** — 三項を「存在」ではなく、独立 actor が raw から検証した exact 値として定義し、誤った env tag・checkout・pin が各々発火を止める負例を要求する。既存 verifier を指せない限り、P3 の「実装差分ゼロ」は撤回する。

### 所見 3 — P5 は D292 が未定義に保った pilot readiness を三条件の完全リストとして先取りし、しかも「記録項目確定」は D282 により既に完了している

**自己判定: real**

プランは三項を pilot readiness と断定する。[s2-plan.md:31](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:31)、[s2-plan.md:79](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:79)。しかし D292 は、実装・検証の実体を見るまで解除条件を定めないと明記し、その理由を「実装が合わないとき条件側を緩める圧力」としている。[docs/decisions.md:13583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:13583)、[docs/decisions.md:13594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:13594)。プラン自身も解除条件未定義・実装未完を認めている。[s2-plan.md:208](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:208)

また record-items と receipt schema は既に D282 の承認 payload に固定済みであり、「項目確定」を残件とするのは stale である。[docs/decisions.md:12911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:12911)

これは、ユーザー裁定済みという点では無断の reward hacking と異なる。しかし、実装前に都合のよい完全条件を固定する構造は D292 が禁じた型と同じである。

**成果物影響** — 後続 actor が三項完了を pilot 解除の十分条件と読み、別 canonical 解除 decision 前に pilot artifact・attempt 台帳を生成する余地が生じる。また承認済み receipt 項目を再裁定して受理集合を動かし得る。

**最小の是正案** — 三項を「非網羅的な実装 backlog。解除の必要条件でも十分条件でもない」と変更する。「記録項目確定」は「D282-pinned record-items/schema の producer・semantic validator 実装と exact enforcement」に置換する。

### 所見 4 — 「本 decision 自体が pilot を解禁する」という攻撃は、決定 (4) の文言が逐語で入る限り成立しない

**自己判定: refuted**

親 brief の M1 は誤りで、禁止は D291 の状態値と D292 の解除権威にも存在する。[s1-brief.md:23](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s1-brief.md:23)、[docs/decisions.md:13470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/docs/decisions.md:13470)。段 2 はこの誤りを検出し、`pilot_submission = forbidden`、別 canonical decision 必須、当該 decision に投入権限なし、を明記する設計へ修正している。[s2-plan.md:5](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:5)、[s2-plan.md:73](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:73)

ただし report の `forbidden` は hard-coded diagnostic であり、投入 gate そのものではない。[report.py:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/publication/report.py:229)。禁止維持の根拠は decision 本文と D292 である。

**成果物影響** — 決定 (4) がそのまま入れば、pilot・main の禁止状態、submission authority、certified 選択は変わらない。

**最小の是正案** — 必須修正は無し。ただし「pilot 投入の可否を切り離す」[s2-plan.md:70](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:70) は、「将来の解除 decision が公表層完了を必要条件としない。現在の状態遷移は無い」に狭める。

### 所見 5 — P3 の「コード差分ゼロ」は正しいが、M5 と「挙動・成果物も不変」という一般化は false

**自己判定: real（非 blocker）**

path 検索に加えて D162・D291 の identifier 検索も実施した。D162 の executable Python 参照は 0 件だった。現在の `docs/decisions.md` 読取経路は次のとおり。

| consumer | 読取境界 | 追記の影響 |
|---|---|---|
| [publication/report.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/publication/report.py:75) | `HEAD:docs/decisions.md` の D291 後続節 | 新 D が `decision_ids` に追加される |
| [tools/check_docs.py:5233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/tools/check_docs.py:5233) | worktree の現行台帳 | known-D 集合が増え、新 D 参照を受理する |
| [tools/spool_fold.py:2315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/tools/spool_fold.py:2315) | 現行 canonical 台帳 | 次の D 採番・重複検査・append bytes が変わる |
| [s8c_preregistration.py:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/campaign/s8c_preregistration.py:1381) | 各 generation 導入 commit の台帳 | 既存 generation には影響無し |
| [approval_d291.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/publication/approval_d291.py:21)、[approval_payload.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/preregistration/approval_payload.py:17) | 固定 commit blob | HEAD 追記の影響無し |

テスト群は上記経路の consumer だが production admission ではない。`codex_reasoning_ab.py` は固定比較資材、`p3_s4_loop_trigger_gating.py` は情報源 metadata、`git_state.py` は変更可能 path の allowlist であり、HEAD decision 内容の semantic consumer ではない。段 2 は report の ID 追加を後半では正しく認めている。[s2-plan.md:163](/home/SFC/tanab/.claude/jobs/3142a409/tmp/dev-wave-t338/s2-plan.md:163)

**成果物影響** — deny-only report の参照列、docs 参照の受理集合、将来の D 採番が変わる。certified 選択・材料レポート・proof chain の値は変わらない。

**最小の是正案** — 「実装コードと研究成果物は不変。変わる executable output は report の `decision_ids` と台帳管理結果だけ」と主張を限定する。

### 所見 6 — 前向き追記が D291 の固定 payload bytes を変える経路は無い

**自己判定: refuted**

resolver は commit `b13b7ea840ad51199f40b3a534c9d1cdb422af2e` と blob SHA-256 `3d2cd5dc...c2b8` を固定する。[approval_d291.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/publication/approval_d291.py:21)。`read_pinned_blob` は worktree path を開かず、固定 commit の object を SHA 検証して読む。[blobref.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/preregistration/blobref.py:111)。`operational_state_on_fold` も独立 digest で固定される。[approval_d291.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t338-rf-trigger-realign/orchestrator/publication/approval_d291.py:139)

静的照合では `git show <固定commit>:docs/decisions.md | sha256sum` が定数と exact 一致した。HEAD blob object は別 object であり、resolver は読まない。

**成果物影響** — D291 payload、承認 role、値射影、`pilot_submission` の resolver 値は不変。

**最小の是正案** — 無し。report の HEAD scan 変化だけを D291 payload 変化と混同しない。

### 所見無し

- D229 の `producer → pilot → validator/consumer → 本走` 順序を維持すること自体: 無し。
- P1 の文限定 forward supersession 手法自体: 無し。D291 bytes を変更しない。
- P4 の T338/T339 ownership 統合: レンズ A 上の所見は無し。
- M2・M6・M8・M9 の狭い実測値: 無し。M3 は狭くは正しいが安全性の一般化だけ所見 1、M4 は T126 に限り正しいが T139 への一般化を所見 1・2、M5 は所見 5 のとおり限定が必要。
- 現在の executable pathによる certified 選択・材料レポート・proof chain の即時変更: 無し。

## 総括

**NO-GO。** 最も重いのは所見 1 である。attestation 削除は、D282-pinned receipt を評価領域とするなら恒真な重複削除、そうでなければ D162 発火証拠の受理拡大になる。プランはこの二択を解消せず「受理集合不変」としているため、正しさ境界を静かに緩めないことを証明できていない。