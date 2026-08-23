# [T-1376] COMMIT receipt の ledger 単位訂正を stale-main から再開
- 目的: D729 の ledger 単位訂正済み成果を、進行した local main の監査・再受入後に land する
- 状態: 中断
- 最終更新: 2026-08-24 local main 再前進を resume gate が検出して停止
- 基準コミット: 828439188471b501eaba91118ae08dea0fc86338 (worktree: dev-wave-t1376-receipt-ledger-scope、作業 tree clean)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- 前回 handoff の段1〜8成果と旧受入結果を引き継ぎ、main `4b53d1b7` までを監査した。wave 所有 path
  との重複は `docs/decisions.md` だけで、D525 の限定訂正と後続 decision 追記は非競合だった。
- 固定 main `4b53d1b7` を merge commit `28b46036` で取り込んだ。resume gate は成功し、T-1286
  焦点走は 18 passed、`check_codex_agents.py` と `check_docs.py` は成功、spool dry-run は
  `status=planned`、全史 provenance は新規違反なしだった。
- 最初の再受入は、停止用 handoff が着地対象に残ることを投入後に検出し、receipt 発行前に中断した。
  fragment へ再開実績を吸収して handoff を削除した commit が `82843918`。この試行は受入結果に
  数えない。repo 外に `acceptance-child-3.log` だけが残り、receipt 3 は存在しない。
- clean tip `82843918` からの次の再投入直前、resume gate が local main の 8 commit 前進を検出した。
  waiter は即座に SIGINT で止め、`claimed_main=null`、receipt 4・log 4 とも不存在、lease は free。
- 現在の main は `e5b8153ac2023d4ecd083ed277417826cc4b4dfa`、wave は `82843918`、merge base は
  `4b53d1b7be45a97b8a55a3b64a6bee5902ae90e5`。新しい main 8 commit の変更 path と wave の
  net path の重複は、今回も `docs/decisions.md` だけ。内容の監査と merge は未実施。

## 未完の作業と次の一手 (具体的に)

1. fresh context で main `e5b8153a` 以後を再読し、8 commit の内容と D525 訂正との意味衝突を監査する。
2. 固定 SHA の wave-side merge を行い、resume gate、焦点走、Codex agent/docs/provenance 検査、
   spool dry-run を再実行する。
3. 本 handoff の内容を fragment へ吸収して削除・commit し、clean tip を確定してから canonical
   acceptance を再投入する。成功 receipt と exact audited commit 列で段9 land を再試行する。
4. 再開コマンド: `$dev-wave [T-1376] COMMIT receipt の ledger 単位訂正を stale-main から再開`。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- acceptance と同じ shell に resume gate を並べる場合、gate 非0で後続を止める必要がある。今回の
  command は後続へ進んだため即時中断した。次回は gate と投入を別 call に分ける。
- 停止用 handoff は最終 acceptance の tested tip に含めない。fragment へ吸収・削除した clean commit
  を先に作る。receipt 後の通常 docs commit を追加して埋め合わせない。

## dev-wave 改善候補

- なし。上の2点は `DW-STOP`、`DW-S07`、handoff README の既存契約で既に指示されている。
