# [T-619] 段1 brief — D230 統一述語を既定監査へ導入する

wave slug: `dev-wave-t619-provenance-unified-predicate`。worktree 基準コミット
`f5677a66a91474478b65fe178ba9ed2eeee1e6cc` (main, clean)。

## scope

`tools/check_ai_provenance.py` の既定監査 (`--range`/`--message-file` 未指定時の経路だけ) を D230
(`docs/decisions.md:10798`) の統一述語へ揃える。

```
applies_R(C) := C∈Anc(H) ∧ ( (∃p∈seeds(R): p∈Anc(C)) ∨ (¬∃p∈seeds(R): C∈Anc(p)) )
```

対象は (a) 選択集合 `_commit_range(None)`、(b) scope/implementation 層の epoch 適用 2 項目化、
(c) CAB 層の epoch 適用 2 項目化、(d) `H` (HEAD) を起動時に一度だけ解決し終了時 drift を rc=2、
(e) shallow/graft/replace/非一意 policy add を既定監査で rc=2 (現状無実装、新規)、(f) 既知違反台帳へ
`333605d6` を追加、(g) `docs/ai-provenance.md` + `docs/provenance/audit.md` の契約文改訂 (非遡及の
記述 4 箇所→統合 1 文、family net −168 bytes、`PR-A02` の記述更新)。
**明示 `--range` と `--message-file` 経路は 1 bit も変えない (裁定 5)。**

## 確定済みユーザー裁定

2026-08-07 /rulings 第 5 回、`docs/archive/worklog-phase3-0807-299.md:397-402` (entry 299)。
D230 の恒久形を 5 点で採用側に確定:
1. `333605d6` を既知違反台帳へ追加して緑を保つ (rc は新規のみ。T-614(`5ed3844f`/`12bac5b7`)・
   T-618(`2327210a`/`b4e7c47b`) と同じ整理形)。
2. 非遡及規定の改訂と等価縮約 net −168 bytes を許す。
3. forward correction の受理集合が strict 化することを受容。
4. legacy の scope/CAB/形式kind 違反に受け皿が無いことを受容 (D205)。**新規 ledger kind を作らない
   — 作れば D221 が却下した「防壁の恒久緩和の事後正当化」と同型になる。**
5. 明示 `--range` は lineage のまま残す。

## 実測で確認済みの前提 (2026-08-19、HEAD `f5677a66`。設計時 `bb824d8b`, 2026-08-07 から再検証、F1)

出荷済み関数を import する使い捨てスクリプトで直接実測した (`tools/check_ai_provenance.py` の
`_policy_commit`/`_scope_policy_commit`/`_implementation_policy_commit`/`validate_implementation_author`/
`_co_authored_by_findings`/`_known_violation_registry` を実呼び出し)。

- 4 層 epoch は不変: base `50c1ef4e`、scope `2f0245c1`、implementation `8c6d3f3b`、CAB `9b26b3bd`
  (CAB は `-S <needle>` の全履歴 pickaxe でも hit 1 件のみ、追加 seed なし)。
- base/scope 層は `--ancestry-path` count == plain range count (今日も差 0、4349/4349, 4227/4227)。
- implementation/CAB 層の gap は 12 日・数百 commit を経ても**設計時と完全に同一の 26 commit**
  (impl 2 件、CAB 24 件) — 新たな gap commit は増えていない。
- 26 件全部に `validate_implementation_author`/`_co_authored_by_findings` を実適用した結果、
  新規 finding は `333605d6` (missing-codex-author、
  `output/insights/2026-07-28_t142-review-verbatim/{count_abort_reasons,count_frontier}.py`) の
  **1 件だけ**。`6a9c97c4` は impl 対象 path 0 件で non-issue、CAB 24 件は全件 raw==parsed で
  finding 0。26 件はいずれも現行台帳 (42 entries) に未登録。
- `AI-Agent-Correction:` trailer を持つ commit は全履歴で `6d7141dc` の 1 件のみ (`git log --grep`)。
  裁定 3 の懸念 (correction candidate 増加) は base 層 gap=0 により**今日は完全な no-op**、将来への
  備えとして受容する設計。
- byte 予算 (`tools/check_docs.py:203-208`, `PROVENANCE_FAMILY_BYTES=9000`):
  現在 `docs/ai-provenance.md`(6270B) + `docs/provenance/audit.md`(1346B) +
  `docs/provenance/correction.md`(1361B) = 8977B、slack 23B (設計時の 6B から拡大)。
  非遡及 4 箇所は逐語一致で現存確認済み、python で正確に byte 計測: 104+77+129+38=**348B**
  (design 時の記載と一致)。統合案 1 文 180B で **net −168B 再確認済み**、予算内に安全に収まる。

## 不変条件

- 正しさゲート: 統一述語は「lineage で不明な commit はデフォルトで**適用する**」方向 (strict化)
  にのみ動く。適用を緩める分岐を作らない (絶対規律 2)。
- 選択集合 (base 層) と適用述語は同一式になるのが設計の要点 — 実装がここで乖離したら bug。
- `IMPLEMENTATION_POLICY_NEEDLE`/`CO_AUTHORED_BY_POLICY_NEEDLE` の `docs/ai-provenance.md` 内
  出現回数 (現状各 1) を docs 編集で変えない。変えると pickaxe epoch 検出そのものがずれる
  (needle は非遡及 4 箇所とは別テキストで隣接するだけ、確認済み)。
- stale (rc=2) は新規違反 (rc=1) より優先する既存性質を保つ。
- `--message-file` 経路 (commit 前 preflight) は完全に無改修。

## 成果物の形

- **code+test**: `tools/check_ai_provenance.py` + `orchestrator/tests/test_check_ai_provenance.py` を
  Codex `role=author` の**単一実装単位**に (T-614/T-618 と同型。ファイル所有の自然な素集合分割が
  無い — 全変更が同じ epoch-resolution 機構を共有するため) **(P1、攻撃対象)**。
- **docs**: `docs/ai-provenance.md` + `docs/provenance/audit.md` (`PR-A02`) は親が docs-only 権限で
  直接編集する (凍結境界)。段4 裁定後・段6 review 対象に含め、段6 review 完了までに commit する
  **(P2、タイミングは攻撃対象)**。
- 既知違反台帳: `KnownViolationSpec("333605d680ec15f3f74b00e9e2746ae317b85dc5", MISSING_CODEX_AUTHOR,
  ruling=<entry 299 絶対参照>)` を1 entry 追加。
- decisions.md: 新 D (D230 実装済み化。fragment、段7)。

## 変更面アンカー表 (file:line は `f5677a66` 時点、現状 → 変更方針)

| file:line | 現状 | 変更方針 |
|---|---|---|
| `tools/check_ai_provenance.py:1364-1371` (`_commit_range`) | `rev_range is None` で `--ancestry-path` | plain `{policy}..HEAD` + `[policy, *plain]`。HEAD 明示解決を追加 |
| `tools/check_ai_provenance.py:1457-1523` (`_normal_commit_audit`) | `descends(scope_epoch)`/`descends(implementation_epoch)` 単項 | 2 項化: `descends(epoch) or not <epoch が commit の祖先>`。第2項は既定監査時のみ有効、`--range` 時は現行のまま — 呼び出し元からのフラグ配線が要る |
| `tools/check_ai_provenance.py:1389-1446` (`_Ancestry`/`_build_ancestry`) | `has_cab_policy` は「commit がいずれかの seed の子孫」のみ | 「commit がいずれの seed の祖先でもない」判定を追加 (seed 群 `bits` の union で O(1)、`policy_hits` は既に取得済み) |
| `tools/check_ai_provenance.py:2611-2618` (`main`, no-message-file 分岐) | HEAD 都度暗黙解決、shallow/graft/replace 検出なし | HEAD 一度解決 (`git rev-parse HEAD` を起動時 1 回)・終了時 drift rc=2・shallow (`--is-shallow-repository`)/graft/replace/非一意 policy add (`_policy_commit` の `-S` hit 数 >1) の rc=2 |
| `tools/check_ai_provenance.py:268-636` (`KNOWN_PROVENANCE_VIOLATIONS`) | 42 entries、`333605d6` 無し | `333605d6` の `KnownViolationSpec` を追記 (kind=`MISSING_CODEX_AUTHOR`、note 不要 — 種別が note 必須なのは `MALFORMED_AI_AGENT` だけ) |
| `docs/ai-provenance.md:6-7,17,29-31,48` | 非遡及を 4 箇所・348B で別々に記述 | 統合 1 文・180B (net −168B)、`IMPLEMENTATION_POLICY_NEEDLE`/`CO_AUTHORED_BY_POLICY_NEEDLE` 隣接テキストは非改変 |
| `docs/provenance/audit.md:15` (`PR-A02`) | 「導入 commit から `HEAD` までの欠落…導入前の欠落は legacy」(lineage 読み) | 統一述語の意味 (seed の祖先でない HEAD 到達 commit も対象) に揃えて更新 |

影響テスト (grep 済み、既存。網羅は段2 codex の責務): `test_history_gate_starts_at_policy_epoch_and_
rejects_followup`(724)、`test_cab_policy_is_detected_on_range_from_separate_lineage`(868)、
`test_scope_epoch_anchor_occurs_exactly_once_in_entry`(3832)、`test_implementation_policy_epoch_is_
pinned_in_this_repo`(3845)、`test_ancestry_bitset_matches_merge_base_oracle_for_every_pair`(5693)、
`test_ancestry_pickaxe_mask_matches_per_commit_oracle`(5742)、known-violation 系 (1329-3715 に多数)、
`test_forward_correction_ancestry_still_uses_merge_base`(5824)。

## 成果物影響 (DW-G05)

未実装なら epoch 適用の非対称 (26 commit) が塞がらず、将来同型の side-branch merge が無審査で通る
(D230 の理由そのもの)。台帳追加 (点1) を伴わずに統一述語だけ先行させると `333605d6` が新規違反化し
既定監査の full 監査が rc=1 に落ち、`DW-O17`/`DW-O25` の land 前提が壊れる — **統一述語と台帳追加は
同一 commit (または同一 land 前 provenance 監査に含まれる連続 commit 列) でなければならない。**

## 一次資料 (段2 codex へ絶対パスで渡す。全文複製しない)

- `/work/1/SFC/tanab/izanagi/output/insights/2026-08-07_t619-provenance-range-permanent-design/README.md`
  — 統一述語の導出・4層実測 (設計時点)・却下案の理由。
- 同 `s4-adjudication.md` — 段3 の A1-B7 所見と裁定済み設計 v2 の全文 (再訪不要、確定前提として使う)。
- `/work/1/SFC/tanab/izanagi/docs/decisions.md:10798` (D230 決定文)。
- `/work/1/SFC/tanab/izanagi/docs/archive/worklog-phase3-0807-299.md:397-402` (5点裁定、entry 299)。
- T-614 commit `5ed3844f`+`12bac5b7`、T-618 commit `2327210a`+`b4e7c47b` — 台帳追加の実装形の先例。
- 本 brief 自身: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t619-provenance-unified-predicate/brief.md`

## 攻撃対象 (段3 レンズへの指示。P1-P2 以外にも探せ)

- (P1) 実装単位を分割しない判断。
- (P2) docs 編集のタイミング (段4後・段6 review 完了まで)。
- (P3) HEAD pin・shallow/graft/replace 検出の判定条件は本 brief では要件のみ — 正確な git plumbing
  (どのコマンドで shallow/graft/replace を検出するか、`_policy_commit` の非一意判定の実装位置) は
  段2 が file:line で確定させる。
- forward correction (`PR-C01`/`PR-C02`) との相互作用 (裁定3, A2) が本当に無改修で済むか
  (base 層 gap=0 の今日は no-op だが、コードパス自体に epoch 依存の分岐が紛れ込んでいないか)。
- **scope 外・触らない**: `_scope_policy_commit` の `-S "scope="` 非一意性 (design B2)、
  `_build_ancestry` の pickaxe argv ARG_MAX / bitset scaling (design B4) — 既存の潜在欠陥として
  design 時に新規タスクへ起票済み (`docs/spool/FOLDED.md:476` 系譜、T-620/T-621 相当)。本 wave で
  fix しない。scope/CAB/形式kind 用の新規 ledger kind も作らない (裁定4)。
