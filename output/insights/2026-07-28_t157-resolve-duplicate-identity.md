# [T-157] `_resolve_duplicate` の identity 誤参照 — 封鎖と敵対レビュー記録

dev-wave (軽量版 + 敵対レビュー 2 本 + 焦点再レビュー、2026-07-28)。材料の出所 =
`output/insights/2026-07-28_t148-macro-context.md` §5 (T-148 段 6 レビュー B must-fix 5)。

## 1. 欠陥 (実測)

3 driver (`p3_s4_loop` / `p3_s4_loop_sort` / `p3_s4_loop_trigger_gating`) の `_resolve_duplicate`
(重複提案 = coder が既評価値を独立再提案 → run_campaign がリカバリ skip し summary.results が空)
が、`with applied(...)` の **revert 後**に `source_digest.resolve` を再実行していた。

- `applied()` の契約 (patchharness.py docstring): 「body 内で resolve を行うこと。revert は必ず
  resolve の後」— 3 driver ともこの契約に違反 (呼び出し点が with ブロックの外)。
- revert 後の tree からは stock token しか出ないため、重複解決は **stock id = 別 variant** の
  WAL を引く。backoff 版はさらに `ccbench_dir` 引数なし (共有固定パス参照) の二重欠陥。
  sort/trigger は `ccbench_dir=sub` こそ渡していた (2026-07-10 レビュー、D43) が「revert 後」
  は同型で、正しい tree の誤った時点を見ていた。

**成果物への実影響 (レビュー A-2 の訂正を反映した正確な範囲):**
- whiteboard / checkpoint: variant id は保持しない (abstract 化済み) — 誤 id の WAL 証拠で
  **成否 (success/fail) を誤分類**する汚染。
- trigger 系 provenance: entry に **誤った variant id がそのまま永続化**。
- critic digest: `make_critic_digest` は layout の WAL から直接構築し、重複解決の返り値を
  消費しない — **直接汚染なし** (T-148 insight §5 の「critic digest に誤参照が永続化」は過大)。

## 2. 封鎖 (実装)

再 resolve を修すのではなく **撤去**した。run_campaign (loop.py) は skip 判定時に正しい id を
applied 内で確定済み (`v = variant_id(g, src_tok)`) — これを新設 field
`CampaignSummary.skipped_variants` へ露出し、`_resolve_duplicate` は summary 由来 id だけを使う
(id 確定点の単一化、D23/D24)。identity_skipped (id 未確定 skip) は積まない → 成功を捏造せず
fail 側。sort/trigger の独自コピーは `_resolve_duplicate = L._resolve_duplicate` の alias に
単一実装化 (同型 3 連の再分岐を構造的に封鎖)。

却下した代替案: applied 内での再 resolve — id 確定点の二重化 (D23/D24 違反) を残す。

## 3. 敵対レビュー (codex gpt-5.6-sol high ×2 + 焦点再レビュー 1) と裁定

- **B-1 must-fix (real・採用、再レビューで partial → fix v2)**: poison テスト (resolve 非呼出)
  は、旧 (cfg, genome) signature ごと戻す忠実な回帰では side_effect 発火前に直呼び TypeError で
  赤くなる = **F28 型の偽 KILL**。fix v1 (co_names assert を同テスト末尾に追加) は焦点再レビューが
  partial と判定 — 直呼びの TypeError が先行し assert が評価されない。fix v2 = 構造的束縛を
  **独立テスト** `test_resolve_duplicate_structurally_free_of_resolver` に分離 (呼び出さず
  code object のみ検査 → どんな signature 回帰でも性質そのもので赤)。変異 M2 は二形で裏取り
  (§4)。
- **B-2 nit (real・採用)**: M1 の期待赤節点は 4 でなく 3 (`== []` assert は append 削除でも緑)。
- **A-1 must-fix (real・実装せず裁定パッケージへ)**: 修正は forward-only で、**過去に汚染された
  checkpoint / trigger provenance を移行も拒否もしない**。救済策 (移行 or fail-closed 版 gate) は
  既存成果物の受理集合を変える設計択一のためユーザー裁定へ (worklog 裁定パッケージ参照)。
  注: 汚染の実在が確認されているのは 2026-07-09 監査の backoff 段 4b iteration 2 の系譜のみで、
  whiteboard は成否分類のみ・誤 id の残存は trigger provenance に限る。
- **A-2 nit (real・採用)**: §1 のとおり docstring / 記録の過大説明を訂正。
- **A-3 nit (real・採用)**: D43 の「`_resolve_duplicate` に `ccbench_dir=sub` を渡す」が alias 化
  後は stale — D43 を正本として旧形を再導入すると再発するため erratum を追記 (同日 docs commit)。

## 4. 変異事前登録 v2 と結果

統合 commit 後に本走 (DW-O19)。各変異は単独適用 → 期待テスト赤 → 復元。

- M1: loop.py の `skipped_variants.append` 削除 → test_campaign の非空 assert 3 箇所が赤
- M2a (signature 保存形): `_resolve_duplicate` 内へ `from campaign import source_digest` +
  resolve 呼び出しを挿入 → poison テスト赤 (side_effect) + 構造テスト赤 (co_names)
- M2b (旧 signature 忠実回帰): signature を旧 (cfg, genome, ...) 形へ戻し resolve 参照を再導入 →
  **構造テスト単独で赤** (TypeError に依存しない semantic kill = B-1 の閉証)
- M3: `recs.get(STAGE_COMMIT)` → `recs.get(STAGE_COMMIT, {})` → empty-fallback テスト赤
- M4: sort の alias を局所 wrapper に置換 → alias 同一性テスト赤

(結果は worklog (34) に記録)

## 5. 残る穴 (正直に)

- 過去成果物の遡及救済は未裁定 (§3 A-1)。
- `skipped_variants[0]` は 3 driver の単一 genome 呼び出し前提。複数 genome の run_campaign
  呼び手が重複解決を導入する場合は対応付けの再設計が要る (現行呼び手に該当なし)。
- backoff_sweep.py の skip (screening 系、result is None) は別意味論で skipped_variants を
  積まない — 同名 field の二義化はしていないが、将来 screening 側で id が要るなら別 field。
