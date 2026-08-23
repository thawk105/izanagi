# [T-1376] COMMIT receipt の一回限り保証を ledger 単位へ限定
- 目的: D729 を適用し、COMMIT receipt の保証記述を現行実装どおり ledger 内 exactly-once に限定する
- 状態: 作業中
- 最終更新: 2026-08-24 段1 brief
- 基準コミット: 768e9fe62e6fecd50280bd95771159947e08c4d8 (worktree: dev-wave-t1376-receipt-ledger-scope)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- main、branch、全 handoff、T-1520 の committed 差分を照合した。T-1520 は
  `tools/dev_wave_*`、関連テスト、`docs/dev-wave/operations.md`、専用 spool fragment を所有し、
  本 wave の裁定・証拠記述面とは非重複。相手 branch は変更しない。
- D729、worklog entry 874 の [T-1376]、発見時の archive entry 660、FOLDED の
  `receipt-cross-layout-single-use`、D525、T-1286 の裁定・証拠資料を照合した。
- inline probe で同じ lock bytes を 2 layout root へ配置し、同じ verifier 発行 live receipt object と
  同じ operation・variant・workload・payload・sink・lock context を再発行せず両 WAL へ渡した。
  layout と ledger だけが異なる条件で同じ receipt ID が各 WAL で 1 回ずつ受理され、同一 WAL の
  2 回目だけ `commit receipt was already consumed by this WAL` で拒否された
  (`layout_a_rows=1`, `layout_b_rows=1`, `receipt_ids_equal=true`)。
- `DW-O08` を適用し、専用 worktree の submodule 初期化を完了した。凍結 bytes は変更しない。
- 段2 plan は D729 を重複起票したため採用せず、段3の2レンズで差し戻した。段4は既存 D729 を
  authority とし、D525、entry 622 の T-1286、entry 660 見出し・本文の3面だけを近接訂正した。
- repo 全体検索では、今回の3訂正面のほかに entry 616 の未裁定な起票文、T-1286 の brief・plan・
  review verbatim、T-080 等の別 receipt 契約、FOLDED provenance key が hit した。前者は当時の
  問題提起、後二者は別契約または履歴資料であり、現行 cross-layout 保証ではないため保存する。
- T-1520 の branch 差分を再照合し、今回の3訂正面・handoff・worklog fragment と file 単位で
  非重複であることを確認した。
- 関連焦点走 `python3 tools/run_tests.py orchestrator/tests/test_t1286_commit_receipt.py -q` は
  18 passed。受入全走とは扱わない。
- 段6焦点再レビューは A1-A6/B1-B6 の全所見が `closed`、`partial` / `regressed` は0。
  blocker なしと判定した。

## 段1 brief

- scope: COMMIT receipt の「一回限り」を ledger 内 exactly-once とする D729 の記述是正だけを行う。
- 確定裁定: cross-layout 一意性は主張せず、外部 registry その他の外部状態を新設しない。
- 不変条件: verifier 発行、lock/payload/sink 束縛、flock 下の同一 ledger 消費済み集合走査を変えない。
- 不変条件: 正しさ gate と receipt 受理条件を 1 bit も変更せず、規律2を緩めない。
- 成果物: stale な保証記述の docs-only 訂正、T-1376 完了を記す worklog fragment、本 handoff。
- canonical 3 台帳は spool/fold 契約を守り直接編集しない。歴史的 verbatim の改変可否は段2・3で攻撃する。
- 全 layout 横断 registry、schema、実装、テスト、gate の新設は scope 外。必要性は insight/handoff のみ。
- 並列分割: docs-only の単一変更面。実装 author は不要。正しさ主張に触るため read-only plan と
  敵対相談で変更面・履歴不変性・過大主張の残存を独立検査する。
- 成果物影響: 放置すると同じ receipt が 2 layout で通る実装に対し cross-layout 一意性を読める
  stale な保証が残り、proof chain と作業台帳が実装より強い性質を主張し続ける。

## 未完の作業と次の一手 (具体的に)

1. 段7記録後検査、段8、段9を閉じる。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- canonical 3 台帳の既存 bytes 不変が既定だが、D729 と今回のユーザー指示は既存の裁定文・台帳記述を
  訂正することまで明示する。本 wave はこの具体的な上位指示に必要な語句限定だけを例外として扱う。
- `verbatim/` は歴史資料であり、stale な問いを直すために元裁定 bytes を黙って書き換えてはならない。

## dev-wave 改善候補

- なし
