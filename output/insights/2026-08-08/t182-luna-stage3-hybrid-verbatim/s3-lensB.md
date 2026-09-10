静的検査のみを行った。pytest / `check_docs.py` は実行していない。

### [BLOCKER] 段 3 は運用上の正しさゲートであり、全 luna 化は規律 2 違反になる

- 根拠: 規律 2 は最適化圧力による正しさゲートの弱体化を禁じる（[CLAUDE.md:67–71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/CLAUDE.md:67)）。正しさ防壁に触る段では独立敵対子を省けず（[core.md:11–15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/core.md:11)）、段 3 は brief・前提・scope・変異帰属を攻撃する義務を持つ（[workers.md:10–17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/workers.md:10)）。D207 も「検出力を下げる変更」を規律 2 の対象と明記する（[decisions.md:9901–9904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:9901)）。
- process 読みの論拠: 段 3 自体は reject を決めず、段 4 が裁定し段 6 に sol レビューも残るため、variant verifier とは異なる。
- gate 読みの論拠: 段 4 は「出なかった所見」を裁定できず、段 3 の scope 欠落は実装前に受理集合を決める。D207 は「後段が攻撃するから安全」という同型論を明示的に却下している（[decisions.md:9906–9909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:9906)）。
- 結論: repository の現行解釈では段 3 は正しさゲートの一部である。policy 根拠に使えない観察値と token 節約を理由に、既知の sol-only 所見を落とす全 luna 化は弱体化である。これは絶対規律なので、今回の条件付きユーザー裁定を waiver として land できない。
- 具体的な失敗経路: verifier 改修 wave で luna の共通盲点が scope 欠落を見逃す → 段 4 に所見が届かない → 段 6 でも回収されず fail-open 実装が land する。
- **成果物影響:** anomaly を持つ variant が reject から certified selected へ移り、材料レポートの proof 参照と試行台帳の受理状態が誤る。

### [BLOCKER] D207 の文字列上の対象外を、同じ危険を通す抜け道にしている

- 根拠: D207 の operative scope は確かに reasoning effort のみで（[decisions.md:9889–9895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:9889)）、A/B 装置も model を sol に固定する（[codex_reasoning_ab.py:43–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_reasoning_ab.py:43)）。model routing は別に T-184/T-189 が所有する（[phase3.md:722–733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/phase3.md:722)）。したがって「D207 が意図的に model を直接対象にしなかった」読み筋は成立する。
- しかし除外の帰結は自由変更ではなく、T-184/T-189 の別経路へ送ることだった。段 2 プランは D207 を根拠にせず、ユーザー裁定だけで luna を新しい機械 pin にする（[s2-plan.md:39–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:39)）。これは、A/B 未了時には既定を動かさないという D223 の fail-closed 理由（[decisions.md:10501–10508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:10501)）と逆向きである。
- 具体的な失敗経路: 今後「effort は D207 が禁止するが model/prompt/レンズ構成は名指しされていない」と分類するだけで、同じ検出力低下を観察値から採用できる先例になる。
- **成果物影響:** 品質を検証していない reviewer policy が機械的に固定され、将来 wave の欠陥見落としを介して certified 受理集合と proof chain が変わる。

### [BLOCKER] 91% は見落とし確率ではなく、P2「全部 luna」は導けない

- 根拠: T-182 は第二レンズ 1 箇所・単一 task・n=1 の比較にすぎない（[T-182 report:8–24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/output/insights/2026-07-29_t182-model-routing-shadow-pilot.md:8)）。10/11 は sol の所見を基準にした循環採点で、非盲検・事前登録なし・分散なし（[同:64–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/output/insights/2026-07-29_t182-model-routing-shadow-pilot.md:64)）。落とした 1 件は閉集合採点の選択バイアスそのものだった（[s4-adjudication.md:81–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/output/insights/2026-07-29_t182-model-routing-shadow-pilot-verbatim/s4-adjudication.md:81)）。
- `q=1/11` を各レンズの独立 miss 確率と仮定すれば全 luna の同時 miss は形式上 `q^k` だが、その独立性は全く測っていない。同一 model の系統的盲点なら `k` 本に増やしても miss は `q` 相当のまま残りうる。混成の miss は `P(M_sol ∩ M_luna)` で、これも数値化不能だが、観測上は相補的だった。
- 与件どおり luna-only が 2 件なら sol+luna の既知 union は 13 件、全 luna は sol-only 1 件を落とす。一方、凍結レポートは luna-only 1 件、もう 1 件は mini-only と記録している（[T-182 report:56–62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/output/insights/2026-07-29_t182-model-routing-shadow-pilot.md:56)）。どちらでも混成 union は単一 arm より広く、この件数不一致自体も解消が必要である。
- `k` 本中 `m` 本だけ luna にする混成なら、等負荷という仮定下で token 削減は概ね `31.6% × m/k`。2 本中 1 本なら約 15.8% を削減しつつ sol の既知能力を残せる。
- brief 自身も混成案を認識している（[brief.md:60–62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/brief.md:60)）。「置き換えてほしい」は全置換を許す読みはあるが、条件の主眼が能力維持と token 削減なら混成も同等以上に自然で、P2 は一意に導けない。
- DW-S04 へ返すべき未裁定事項は、全 luna 対混成、条件を満たしたと見なす証拠水準、T-184/T-189 の carve-out、要求 model だけで運用することの受容、runtime gate を今回追加するか、rollback の発火条件である（[core.md:72–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/core.md:72)）。
- **成果物影響:** 全 luna の共通盲点が gate 欠陥を落とすと、混成なら reject できた variant が certified 集合へ入る。

### [BLOCKER] 提案された model pin は文書だけを守り、実起動を luna にしない

- 根拠: 推奨案 A は O01 の見出しを「worker 節優先」に変えるだけで（[s2-plan.md:7–13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:7)）、実行雛形は引き続き `-m gpt-5.6-sol` である（[operations.md:6–12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/operations.md:6)）。汎用 launcher の default も sol のまま（[codex_worker_launch.py:2475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_worker_launch.py:2475)）。
- checker は `workers.md` の `codex \`slug\`` だけを抽出する（[s2-plan.md:28–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:28)。したがって canonical な luna 文を decoy として残し、同節へ `codex exec -m gpt-5.6-sol` を足しても `values == [luna]` で通る。同型の別表記 decoy は D223 で実際に一度 fail-open し、却下済みである（[decisions.md:10510–10517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/decisions.md:10510)）。
- M1〜M5 はすべて prose checker の変異で、実際の起動 model を sol にする変異を登録していない（[s2-plan.md:141–153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:141)）。これは実効 gate へ再照準せよという DW-M01/M02 に届かない（[mutation.md:5–14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/mutation.md:5)）。
- 具体的な失敗経路: `check_docs` は緑、workers は luna、起動者は O01 をコピーして sol を要求、worklog は段 3 を luna と記録する。
- **成果物影響:** 実際の reviewer 集合と記録が乖離し、欠陥見落としで受理集合が変わるうえ、材料レポートの model/provenance 参照が偽になる。

### [BLOCKER] F56 により「実際に luna で相談した」とは証明できず、変更後は misrouting 危険も増す

- 根拠: receipt の model は要求 slug の echo で served identity の attest ではない（[failures.md:1303–1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/failures.md:1303)）。launcher も receipt の `"model"` に `args.model` をそのまま書く（[codex_worker_launch.py:1401–1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/codex_worker_launch.py:1401)）。段 1 probe もこの限界を認めている（[brief.md:22–28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/brief.md:22)）。
- 示せるのは「luna slug を要求した」「rc=0」「model_calls/CLI token が非ゼロ」「出力 hash がある」までであり、served backend が luna だったとは示せない。worklog では `requested_model=luna / served_model=unknown` と書く義務がある。
- availability 面は probe により少し改善するが、attestation 欠落は不変。さらに現在は S03/O01 とも sol なので省略が一致する一方、変更後は明示 override を一度落とすだけで sol に戻るため、requested-model misrouting の危険は上がる。
- 具体的な失敗経路: requested slug または backend が想定外でも出力を luna 由来として裁定し、後から品質差・rollback 対象 wave を同定できない。
- **成果物影響:** 誤った model provenance を参照する proof chain と試行台帳になり、影響を受けた certified 選択を監査・再判定できない。

### [SHOULD] 記録案は条件付き裁定を「ユーザー裁定だけ」に洗浄してしまう

- 根拠: 計画は worklog に部分採用、decision にユーザー裁定、rollback を書くのみ（[s2-plan.md:134–139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:134)）。しかし worklog はレンズ数、real/refuted 数、重要所見、一次資料ポインタを要求する（[worklog.md:22–26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/worklog.md:22)）。decision は理由と却下案を残す契約である（[decisions fragment README:16–25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/spool/decisions/README.md:16)）。
- worklog / decisions に追加すべき項目:
  - ユーザー裁定の「91%・30%ならば」という条件全文。
  - T-182 が `eligible_for_t184_policy=false` であること、既知の sol-only miss と相補所見。
  - 全 luna・混成・T-189 待ちの三案と、誰がどれを却下したか。
  - D207/D223 の理由との関係、T-184/T-189 を supersede するのか carve-out するのか。
  - 各段 3 run は requested luna / served unknown であること。
  - 本レビューのレンズ数、real/refuted 件数、最重要所見、逐語へのポインタ。
  - 与件の「luna-only 2」と凍結台帳の「luna 1 + mini 1」の erratum または解消。
- 具体的な失敗経路: 後続者が新しい luna pin、T-182 の 91%、新 decision を並べ、「妥当な比較に基づく採用」と誤読する。
- **成果物影響:** model policy の根拠参照が誤って proof chain/試行台帳へ伝播し、再評価すべき certified 集合を特定できなくなる。

### [BLOCKER] rollback は将来 policy の一部しか戻さず、元の証拠状態へ戻せない

- 根拠: rollback 案は S03 と checker pin を sol に戻す一方、O01 は変更しないとしている（[s2-plan.md:136–139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:136)）。しかし採用案自身が O01 見出しを変更する（[同:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/s2-plan.md:9)）。また canonical decisions/worklog は append-only で既存 bytes を戻さない（[spool README:101–110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/spool/README.md:101)）。
- これは将来の規範 model を sol に戻すことはできるが、byte-exact な旧状態、既に luna 名義で行ったレビュー、そこから派生した段 4 裁定・実装・成果物は戻さない。
- 完備した rollback には、発火条件、O01 を残すなら「policy-only rollback」とする射程、後継 decision による supersede、worklog 記録、待機中 job/出力の invalidation、影響 wave の棚卸しと必要な再レビューが要る。
- 具体的な失敗経路: docs pin だけ sol に戻し、過去の luna 名義の所見・裁定・land 済み実装を安全済みと残す。
- **成果物影響:** rollback 前に誤受理された variant と不正 proof 参照が certified 集合・材料レポート・試行台帳に残留する。

### [BLOCKER] DW-G05 の「成果物を直接作らない」は影響否定になっていない

- 根拠: brief は段 3 が成果物値を直接作らないとする（[brief.md:49–54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t182-luna-stage3/brief.md:49)）。DW-G05 が求めるのは「直接 producer か」ではなく、放置時に値・受理集合・参照がどう変わるかである（[core.md:65–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/docs/dev-wave/core.md:65)）。
- 具体的な反例: proof-chain consumer を追加する wave で、段 3 が「未存在 proof を accepted とする fallback」を見落とす → plan v2 がその層を scope 外にする → 実装が land → campaign で anomaly variant が certified になる。
- 「段 6 の sol が後で見る」は保証にならない。段 6 は既に縮小された plan/scope を前提にしうえ、D207 が同じ後段依存論を却下している。
- **成果物影響:** `reject/tie` が `selected` に変わり、材料レポートが存在しない・不十分な proof を参照し、試行台帳が誤って accepted を記録する。

## 総括

BLOCKER は **7 件**。最も危険なのは、policy 根拠に使えない T-182 の 91% と token 節約を使い、必須の正しさゲートを全 luna に同質化する規律 2 違反である。  
**NO-GO** — 全 luna 化を止め、混成を含むユーザー再裁定、実起動への requested-model binding、F56 限界を含む正直な記録と完全な rollback 契約が揃うまで land してはならない。