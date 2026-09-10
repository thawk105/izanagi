# [T-721] source closure の enforcement 閉包拡張 — 逐語と変異台帳

wave: `dev-wave-t721-source-closure` / branch `worktree-dev-wave-t721-source-closure`
受入全走: tip `654a199a`、7958 passed / 20 skipped / rc=0、486.74 秒。

## この束が残す事実

1. **裁定 (b) を実装しても「certified 経路が source-bound」は名乗えない。**
   段 3 レンズ A が file:line で反証した。`pipeline.py` は verifier / calibrator / buildcache /
   build_admission / source_digest へ、`execution_guard.py` は env_attestation / site_policy へ
   判定を委譲しており、閉包 8 path はこれらを含まない。逐語は `verbatim/s3-lens-a.md` の A-01。
2. **停止点は certified sink の支配点ではない。** `pipeline.evaluate` と低層 WAL writer は
   `ident` を通さずに書ける (A-02)。実在の別経路は S8b oracle driver。
3. **閉包拡張は開発中の tree に副作用を持つ。** 閉包メンバー 1 本が未 commit なだけで共有
   v2 fixture の生成が落ち、gate を検査していない 16 の consumer が偽の赤になる。
   親の実測は clean 16 passed → dirty 6 failed で、赤 6 件すべて fixture 生成側だった。
4. **事前登録した変異が SURVIVE することをレビューが先に当てた。** M4 (live 検証の disk 比較を
   無効化) は、live drift テストが `ensure_campaign_identity` 経由だったため先行する capture に
   masked されていた。直接 live 検証を呼ぶテストを足して再走し KILLED になった。
   逐語は `verbatim/s6-review-1.md` の D-01、結果は `mutation-ledger.json`。

## ファイル

- `mutation-spec.json` — 事前登録 9 変異 (kill 7 + 過剰拒否の正例 2)。
- `mutation-ledger.json` — 最終 commit `fdda5d38` での本走。KILLED 4 / MISMATCH 5 / SURVIVED 0。
- `mutation-ledger-run1.json` — fix 1 巡目直後 (`7ab58c29`) の初回走行。`DW-M02` により消さずに残す。
  結果は最終走と同じ (KILLED 4 / MISMATCH 5 / SURVIVED 0)。
- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対 2 本、段 4 裁定、段 5 実装報告、
  段 6 レビュー 2 本・fix 2 本・焦点再レビュー。

## MISMATCH 5 件の読み方

MISMATCH は「事前登録した期待 node は**全件落ちた**うえで、他の node も落ちた」厳密な superset で
あり、gate の弱さではなく親の事前登録が狭すぎたことによる。5 件すべてで欠落 (期待したのに
落ちなかった node) は 0 である。焦点再レビューが expected / observed を独立に再照合している
(`verbatim/s6-refocus.md` の FR-03)。**MISMATCH を KILLED へ読み替えてはならない。**
