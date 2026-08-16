---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t190-failure-artifact
seq: 3
---

## 新規

### {{F:launcher-stop-reason-unobserved}}. 終了主体を記録しない計装が、「送る前に送ったことにする」形で自分の目的を偽った [恒真ゲート]

- 事象: F285 は `codex_exit_code=-9` が外部 SIGKILL と識別不能であることを
  「原理的に事後判定できない」限界として記録していた。本 wave はこれに対し
  「launcher は自分が TERM/KILL を送ったかを知っている」という観測を入れた。
  実装子は `termination_initiated_by_launcher` を `_terminate` **呼出しの前**に `True` にした。
- 根本原因: 実 signal は process group が生きているときにしか送られない。
  limit を検出した直後に child が自然終了すると、forced-stop 分岐へは入るが signal は 0 本になる。
  この実装では `initiated_by_launcher=true` かつ `signals_sent=[]` が記録される。
  **「launcher が停止させた」と読める記録が、実際には何もしていない run に付く。**
  分離したかった 2 つの状態 (外部 kill / launcher 自身の強制停止) のうち、
  外部 kill 側が launcher 起因として誤記録されるので、計装の目的そのものが達成されない。
- **見つけ方が本質である。** 静的な段 3 敵対相談ではこの欠陥は出なかった。
  実装後の段 6 敵対レビューが、フラグの代入位置と signal の実送信位置を突き合わせて
  初めて検出した。**「観測量を足した」ことと「その観測量が意味どおりである」ことは別**であり、
  後者は実装差分を見ないと確かめられない。
- 恒久対応: フラグを状態として持たず `bool(termination_signals_sent)` から導出する property にした
  (`tools/codex_worker_launch.py` の `AttemptDiagnosticsState`)。代入経路を消したので
  「送っていないのに true」が構造的に作れない。
  加えて、forced-stop 分岐へ入ったが signal 0 件のとき `False` であることを要求する
  production 経路の負例テストを置き、変異事前登録の M11 として
  「常に `False` にする」変異が KILLED になることを確かめている。
- 再発検知: `grep -n "termination_initiated_by_launcher\s*=" tools/codex_worker_launch.py` が
  0 件であること (property 化されていれば代入は存在しない)。
- 近縁: F285 (launcher の wall 予算に余裕がなく判定情報が保存されていない)、
  F57 (全走でだけ落ちる失敗)。

### {{F:diagnostic-monkeypatches-shared-module-global}}. 診断のための observer 注入が共有 module global を書き換えていた [資源競合]

- 事象: signal 送信を観測するため、実装が `_worker_module.os` を process-global に置換し
  `finally` で復元する形を採っていた。lock も呼出し単位の注入も無かった。
- 根本原因: 同一 interpreter で 2 つの forced stop が並行すると、
  後発が先発の wrapper を包み、先発が途中で素の `os` に戻す。
  後発の signal が未記録になり、後発の `finally` が先発の wrapper を再配置するため、
  **以後の launcher の signal が別 run の sidecar へ誤帰属する。**
  termination helper が参照する `os` も実行途中で入れ替わる。
- **診断計装が並行実行の正しさを壊す**という型であり、
  「観測は無害」という前提が成り立たない例である。
- 恒久対応: module global の置換を廃止し、必要な観測を launcher 内へ局所化した。
  `grep -n "_worker_module\.os\s*=" tools/codex_worker_launch.py` が 0 件であることを
  実装後に確認している。並行 forced stop で signal 帰属が混ざらないことを要求するテストを置いた。
- 再発検知: 上記 grep が 0 件であること。および同一 interpreter で
  2 つの forced-stop run を並行させる帰属テスト。
- 近縁: {{F:launcher-stop-reason-unobserved}} (同じ計装で見つかった別の欠陥)。

## 再発

### F57

- **再発ではなく恒久対応の第 1 手を着地させた: 2026-08-17 ([T-190] 実装 wave)。**
  本エントリが 2026-07-30 から「恒久対応は失敗 artifact 保存による原因分離」と書き続けてきた
  対象を実装した。**F57 は閉じない。** 本 wave が達成したのは
  「次回再発を観測可能にした」ところまでで、実 bundle を得て原因を帰属するのは後続である。
  - 記録される観測量: latch の全成立集合とその判定点の実測値 (elapsed・model calls・token・各 limit)、
    evidence 強制停止、`residual=None` の 4 出所、phase 別時刻 10 点、
    launcher 自身が送った signal。いずれも既存 receipt では表現できなかった。
  - **本エントリと F285 が言う「pytest tmp が終了時に失う」は実機序として不正確だった。**
    `--basetemp` は設定されておらず pytest は最後の 3 セッションを保持する。
    login で走れば残る。**計算ノードでは `/tmp` が node-local で job 終了とともに消える**ため、
    受入全走の失敗 artifact だけが失われていた。退避先は共有 FS でなければ意味がない。
  - **F285 の「予算の縁に常時張り付いている」は failure 側 21 件だけの分布から導いたもので、
    green 側の余裕は未測定である** (F285 §5 が自認している)。整合する仮説であって実証ではない。
    次に実 bundle が取れたら、green 走の `wall_clock_s` 分布と併せて判定する。
  - 予算是正 (fixture harden) は行っていない。D249 の「計装が先、予算拡大は実 artifact の後」に従う。
  - 恒久対応は引き続き原因分離であり、[T-190] も本エントリも open のままとする。
