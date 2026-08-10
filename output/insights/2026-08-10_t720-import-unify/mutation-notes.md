# 変異 spec の意図 (harness の exact key 要件から外した note)

- **M1**: R-A: campaign 本体へ legacy 絶対 import を再導入する。実行時は両形とも import 可能なので落ちず、静的検査だけが落ちる (単一理由性)
- **M2**: R-A の走査配線を切る。台帳との完全一致が stale で落ちる。fix6 の合成 repo 配線テストも同時に落ちるため両方を期待 node に登録する
- **M3**: R-B の走査配線を切る。bootstrap 規則の完全一致が落ちる。fix6 の合成 repo 配線テストも同時に落ちるため両方を期待 node に登録する
- **M4**: R-D の走査配線を切る。相対形規則の完全一致が落ちる。fix6 の合成 repo 配線テストも同時に落ちるため両方を期待 node に登録する
- **M5**: R-C の走査配線を切る。docs 規則の完全一致が落ちる。fix6 の合成 repo 配線テストも同時に落ちるため両方を期待 node に登録する
- **M6**: 除外判定を絶対 path の部分一致へ退行させる。現在の worktree の絶対 path に .claude/worktrees が含まれるため走査集合が空になり、生存検査が落ちる
- **M7**: 例外台帳を空にする。件数 pin が落ちる (RB-04 の恒真化を塞いだことの裏取り)
- **M8**: 直接実行 CLI から __package__ 代入を落とす。逐語 bootstrap の形が崩れて R-B が落ちる
- **M9**: R-A の module 名判定を campaign_* まで広げる。campaign_lock_test_support 等の別名が誤検出され、台帳との完全一致が unlisted で落ちる (過剰検出の防止が効いていることの裏取り)
- **M10**: docs runbook へ legacy 起動形を戻す。R-C が落ちる
- **M11**: campaign 本体へ <repo>/orchestrator の sys.path 挿入を再導入する。PATH_RULE が発火する。BOOTSTRAP_RULE と同じ nodeid が見る
