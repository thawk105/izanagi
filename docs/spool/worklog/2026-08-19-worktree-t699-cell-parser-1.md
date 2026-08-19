---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: worktree-t699-cell-parser
seq: 1
title: T-699 (入口 command の参照 cell を完全な grammar で full-match させる) を実装・検証したが、8c preregistration の batch 上限超過で land が構造的に塞がれていると判明した (コード + テスト、branch worktree-t699-cell-parser、変異 matrix = baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 9段フルで進めた。理由: `tools/check_docs.py` の docs 構造検査 (正しさ防壁) に触れ、
  受理集合を変える変更だったため DW-C00 の「独立の敵対検証子を省かない」条件に該当した。
- 段2 codex plan が brief の実測誤り (「43 cell・条件26件・注釈6件」) を file:line で訂正した
  (実際は42cell・条件25件・注釈5件。DW-O07 は既裁定で削除済み)。
- 段3 敵対相談2本のうち1本 (レンズA) が real 所見を出した: plan の grammar は括弧注釈
  (ANNOT) の文字クラスが広すぎ、注釈内に backtick 付き偽装 group や無 backtick の raw path・
  「の全節」を埋め込む型を単体では拒否できなかった。段4裁定で ANNOT から backtick を除外し、
  旧 raw-path 検査・「の全節」検査を削除せず維持する3層設計へ修正した。
- 段3 の codex 子2本 (レンズA/B) は初回・2回目とも `rc=1・model_calls>0・実出力あり` なのに
  launcher の rollout evidence 検証が invalid と判定し不採用になった。原因は
  `orchestrator/tests/test_check_docs.py:4965-4976` の意図的な非NFC/BOM test fixture
  (`test_placeholder_guard_digest_line_boundary_contract`) を子が自発的に読んでしまったこと。
  prompt に読取範囲の明示制約を追加した3回目で解消した。
- 段5実装後、親(自分) が `tools/run_tests.py` で焦点走を実走し3件の赤を検出。うち2件は
  親自身の裁定の誤り (`_dispatch_tables` の `structure_errors` は複数エラーでも1 finding に
  集約されるため、violation count は 1→2 でなく1のまま据え置くべきだった)、1件は fix子の
  anchor 推測ミス。fix2巡で解消し、458 passed / 0 failed を確認した。
- 段6敵対レビュー2本 (実装差分そのものが対象) は5項目中4件 refuted・1件は命名 nit のみ
  (real所見なし、追加fixなし)。
- 変異 matrix は自前で `mutation-spec.json` を3回作り直した。1回目は pytest collection の
  非ASCII文字が dispatch relay 経由で `\uXXXX` の逐語エスケープとして出力される仕様を
  知らず expected_nodes の文字列が一致しなかった。2回目は M02 (fullmatch検査の無効化) が
  `test_dev_wave_dispatch_rejects_backtick_in_annotation` も同時に kill することを見落とし
  MISMATCH になった (両テストとも唯一 fullmatch 層だけが検出する cell を使うため、
  論理的に正しい追加 kill だった)。3回目で baseline PASSED・2/2 KILLED・SURVIVED 0・
  MISMATCH 0 を確認した。
- 統合 commit (`7147bf91`) を作り、`check_ai_provenance.py` 全史監査は新規違反なしを確認した。
- 受入全走で `--merge-message-file` の事前preflight (rc=2 未作成) →
  merge-message-provenance (rc=70、実装面 path を merge するのに Codex `role=author` trailer
  が無かった。DW-O17「実装面pathが両親と異なればCodex`role=author`へ」に従い追加) の2段階で
  躓いた後、merge (`eff98184`) 自体は成功し `python3 tools/run_tests.py` (13251 passed) も
  走ったが、`status=attributable-red` で {{F:s8c-batch-limit-blocks-any-merge}} を発見した。
  T-699 の変更内容と無関係な Phase3 8c preregistration の batch 上限をリポジトリ成長が
  わずかに (50017 対 上限50000) 超えており、main への divergence を merge するあらゆる
  wave の受入が構造的に赤くなる状態だった。fork で先例を調査したが同型の記録は無く、
  新規 finding と判断した。
- 上記理由で一旦 land を進められず、branch `worktree-t699-cell-parser` へ commit まで
  留め置いて中断した。ユーザーから「最新 main でも状況は変わらないか」と問われ再確認した
  ところ、別 wave が commit `4cc60864` で該当箇所 (履歴長比例のコスト) を根本修正済みと
  判明したため、同じセッション内で worktree を作り直し受入から再開した。

## 次の一手差分

### 更新

- [T-699] **P1**: `tools/check_docs.py` の入口 command 参照 cell grammar 修正は
  実装・段6敵対レビュー2本 (real所見なし)・変異 matrix (2/2 KILLED, MISMATCH 0) まで完了した。
  branch `worktree-t699-cell-parser` に commit 済み (`7147bf91`、main 取り込み後
  `eff98184`)。{{F:s8c-batch-limit-blocks-any-merge}} により受入・land が構造的に塞がれている
  ため、その解消を待って次 wave (fresh context) で受入以降を再開する。
  base: 9d6e25d0d83f55a191a0f9469b387f63c7f35585ca28b5c74b09c252cca9b552

