# blocker 修正 (案 5) の段 6 裁定

レビュー A (22 node の保証) と B (負例・変異・受入) はいずれも rc=0、`check_codex_output.py` 緑。

## 両レビューが一致して否定したこと

- **新たな恒真化は無い** (A-02 refuted)。M3 系の mode / HEAD / extra / missing / focus と
  recursive submodule の性質は、失われた content 差に依存していない。
- **fixture 分割は案 5 の範囲内** (A-C01 refuted)。module fixture 全体を skip にしていない。
- **不在 / 重複 / SHA 不一致の分離は正しい** (A-S01 refuted)。それぞれ skip / `RC_SESSION` /
  `RC_SNAPSHOT` へ分かれる。親も独立に分岐を追って同じ結論を得た。
- **新しい時限装置は増えていない** (B-T01 refuted)。**登録簿の破損も無い** (B-W01 refuted)。

## must-fix

### BF-01 (blocker) — fail-closed の負例が変異で赤にならず skip になる

`test_historical_rollout_preflight_duplicate_is_red` と
`test_historical_rollout_preflight_sha_mismatch_is_red` は、どちらも skip する側の
`_require_historical_rollouts` を呼ぶ。事前登録した変異 B2 / B3 (skip 条件を重複・破損まで
広げる) を入れると、`pytest.raises` の内側で `pytest.skip` が上がり、node は失敗ではなく
**skip** になる。**fail-closed が壊れたことをこの負例は検知できない** (B-M02 / B-M03)。

親も実装を読んで独立に確認した。**保証が形だけになる型であり、必ず直す。**
負例を skip しない `_resolve_required_historical_rollouts` へ向け直し、
あわせて skip 経路そのものの正例を 1 つ新設する (負例を下位へ移すとラッパーが無検査になるため)。

## 採用しない (記録する)

| ID | 出所 | 判定 | 扱い |
|---|---|---|---|
| A-01 | レビュー A | real | portable POS は `PATCH_PATHS` と numstat が NEG と同一になり、実 POS rollout 由来の内容保証を失う。**失効による正直な coverage 喪失**であり、この修正が作った欠陥ではない。新規 T (原本が別媒体に在れば復元) が引き取る。 |
| A-03 | レビュー A | real | supervisor / replay 系が production default POS spec でなく test-local spec を通るため統合保証が弱い。同上、失効の帰結。新規 T が引き取る。 |
| S-02 | レビュー A | real | historical gate が 5 label 一括のため、node が不要な label の欠落でも skip する。**5 label が同時に失効している現状では観測可能な差が無い。** 細分化は新規 T へ。 |
| R-01 | レビュー A | real | preflight resolver と production resolver が「canonical 名 1 件 + 別名 identity duplicate 1 件」で食い違う (test は赤、production は受理)。**全 5 件が失効している現状では発火しない。** 一本化は新規 T へ。 |
| R-02 | レビュー A | real | 複数 label が同一 session ID を持つ manifest で label mapping が上書きされる。現行 manifest では発生しない。新規 T へ。 |
| P-01 | レビュー A | real | 固定 path pin の削除と default POS spec から portable spec への意味変更。裁定 (案 5) が意図した変更であり、記録する。 |
| B-P01 | レビュー B | real | portable fixture が source repo の submodule 実体化状態に依存する。**「どの環境でも緑」とは主張しない。** 本 wave の受入は submodule 初期化済みの worktree で測る。 |
| B-A01 | レビュー B | real | 26 entry の再配線は静的には全件成立。**全走緑は実測でのみ確定する。** 親が受入で測る。 |
| B-A02 | レビュー B | real | 28 と 26 の差 2 件は junit で `IZANAGI_GROWTH_HOLD_V1` により既に skip されていた node。**親が junit を直接読んで確認済み。** 新たな skip ではない。 |
| B-W02 | レビュー B | 未確認 | 外部 meta registry への新設 3 node の波及。親が受入全走で観測する。 |

## 親の自己訂正

親は「test 側の照合再実装と production 側に食い違いは無い」と報告したが、**不完全だった。**
照合述語 (`_matching_required_session_ids` と `_rollout_matches_session`) は等価だが、
**その周囲の候補選択が production の pinned-label 経路と食い違う** (R-01)。
述語だけを比べて「食い違い無し」と結論したのは検査範囲の取り違えである。

## 変異事前登録の更新

- B1 / B4 は成立する (B-M01 / B-M04)。
- **B2 / B3 は BF-01 の修正後に anchor を取り直す。** 修正前の形では KILLED にならないため、
  修正前の spec で本走してはならない。
- 期待 node の完全集合は probe で集める (DW-M07)。
