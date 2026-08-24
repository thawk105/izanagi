# [T-1611] 8c terminal 理由一致関門
- 目的: 事前分類受領証の failure reason と terminal の再走理由を exact 一致検査し、次の正式 8c 利用前の関門を閉じる
- 状態: 作業中
- 最終更新: 2026-08-24
- 基準コミット: 618c9236c843ef9689a10679cc50e0fc95339c49 (worktree: dev-wave-t1611-terminal-reason-match)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- クラス3起動順、D741、archive entry 882 の T-1611、paper story §8 B-3、T-1593/T-1480/T-1484 の編集重複を確認した。
- T-1593/T-1480 は main に吸収済み。T-1484 の指定4ファイルは main と byte 同一。T-1480 の現行所有2ファイルは本件と非重複。
- 同時発生した別 T-1611 worktree は相手側が実装前に撤去し、現在の T-1611 所有は本 worktree だけである。
- 段2 planと段3敵対相談2本を完了し、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1611-terminal-reason-match/s4-adjudication-plan-v2.md` に親裁定を固定した。
- terminalだけのstrict化は不十分と裁定し、forward-only formal reserve・terminal・acceptanceの3境界をstrictにする。C03 evaluatorは編集しない。
- 現行partialのclassification=None→terminal=`producer-failure`はexact不一致としてfail-closedにし、新field/status/reasonを足さない。

## 未完の作業と次の一手 (具体的に)

1. D95 の隔離 Codex author に plan v2 の production/testだけを限定投入する。
2. 段6の敵対レビュー2本、fix、事前登録7変異、関連テスト、canonical acceptanceを完了する。
3. 段7記録、段8自己改善、段9 landを完了する。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- 既存成果物と T-1505 の8c互換 facadeは遡及変更しない。新しい版境界だけで strict 化する必要がある。
- scope外の事前登録12条件は状態報告だけとし、本 wave で evaluator 登録・充足化・正式証拠生成を行わない。
- C03は旧compat sinkを要求するため、本変更後にUNSATISFIEDへ変わりうる。dead旧callやevaluator改変で緑へ戻さず、状態だけ報告する。

## dev-wave 改善候補

(段8で候補または「なし」を一度だけ確定する。)
