---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: dev-wave-t2207-closure-unresolved
seq: 1
title: [T-2207] D1539 を字義どおり入れると既存テストが 715 セル (12 sink) 赤になり、すべてを依頼の範囲内で消す案が組めないので実装せず一時停止した。同じ依頼の [T-2344]・[T-734]・[T-733] 部分は D2260 項 2 と逆向きのため実行せずユーザーに確かめる (docs のみ、branch worktree-dev-wave-t2207-closure-unresolved)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、2026-09-27 14:28 JST、逐語 = `output/insights/2026-09-27/t2207-closure-unresolved/verbatim/request.md`): source 閉包の系統として (1) [T-2207] D1539、(2) [T-2344] 次段と exact-85/96、(3) [T-734] と [T-733] の整理を 1 wave で。
  設計判断は {{D:t2207-hold-and-request-conflict}}、記録は同 insight の README。
- 起点 = local main `ad114fba0` (fresh worktree、開始 gate rc=0)。段 4 の後に main `294a8cb21`、記録の commit 前に `cc2e9672a` へ fast-forward した (どちらも自 commit 0)。
- **依頼と同日の裁定の食い違い:** 依頼の (2)(3) と [T-733] の整理は、D2260 項 2 (同日 07:52 JST) が名指しで止めた対象を逆向きに指示している。段 1 で見つけ、段 3 相談 B の反対 (後の直接依頼を「写し」と推測して無効扱いにできない) を受けて、
  実行しない根拠を「推測で選ばない」に改めた。依頼の起動直後 (14:28 JST の数分後) の ListAgents では開始から 3〜6 分の peer が 13 本いたが (逐語は insight の `verbatim/listagents-excerpt.md`)、依頼文の出所は確かめられなかった。
- [T-2207] の段 1 実測: 字義どおりの判定変更で 16 sink・929 セルが `proven-unreachable` から外れ、failure 715 (12 sink)・既存台帳による deferred 214。コード無変更の計算と一時実編集 (復元済み) で一致。
  「18 セル」は 2026-09-02 の s1 sink 1 本の数だった。段 2 plan が「P3 の stock JSON から任意 macro が入る」と書いた誤りは段 3 相談 A が訂正し、未閉包の具体的な入力列を示せたのは S1 の `prepare_cell_fn` 注入口だけと記録した (静的な穴、成果物影響の実証なし。他の sink も閉包を証明したわけではない)。
- 段 4 は「実装しない」(段 4→7→8→9)。実装面の差分 0 のため変異 matrix は免除。記録の事実確認に read-only レビュー 1 本 (NO-GO・must-fix 2・should 1) と焦点再レビュー 2 巡 (1 巡目 NO-GO・新規 must-fix 1・should 1、2 巡目 GO)。所見はすべて採用した。
- 受入 attempt 1 (tip `f853533e4`、15:31〜15:44 JST) は赤 1 件: `orchestrator/tests/test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union` が、
  別 session の worktree 登録 `.git/worktrees/t1983-t2223-b4-prereg-rulings/gitdir` の消失で `T810CoordinatorError: cannot read worktree registration: file is absent`。
  同じ時間帯にその wave が land した通知 (main `27baa1c26`) を受けており、撤去と重なったと見る。本 wave の差分は docs と insight だけで当該 test の到達範囲外なので非帰属と判定し、帰属の記録 commit の後の tip で受入を投げ直した。
- 工数: codex 子 6 本 (段 2 plan 1、段 3 相談 2、記録の事実確認レビュー 1、焦点再レビュー 2。いずれも read-only・medium)、Claude 子 1 本 (sonnet、wave 運用の記憶の要点抽出)。

## 次の一手差分

### 更新

- [T-2207] **P2・裁定済み (D1539) → 一時停止・再開条件待ち**: D1539 (動的入力の設定式では部分 inventory の不在を到達不能の証明に使わず `unresolved` へ倒す) は有効・未実装。
  字義どおりの実装は 16 sink・929 セルを `proven-unreachable` から外し、12 sink・715 セルが failure になる ({{D:t2207-hold-and-request-conflict}}、`output/insights/2026-09-27/t2207-closure-unresolved/README.md`)。
  再開は、判定変更と同じ wave で 12 sink それぞれの処置 (gate 被覆、macro 名の固定を検査が読める形にする、S1 は返却 genome と freeze cell の flag 一致の検査) を本題として行うことが認められたとき。
  期待値の反転・skip・理由のない台帳登録で緑にしない。
  base: 9060d6d046d4f4f8587ac6c096860e45e9d95db874e81e3af64954578285aa93
