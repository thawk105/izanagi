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

- **初の実測帰属: 2026-08-17 (本 wave の受入全走 request `914871`、bnode004、48 worker)。**
  **本エントリ 20 回以上の再発で初めて、落ちた瞬間の判定材料が保存され、機序が確定した。**
  同走で 3 件が落ちた (12203 passed / 3 failed / 95 skipped / 116.98 秒)。
  3 件とも本 wave が触っていない既存 node で、`DW-O18` により帰属しない。
  退避 bundle は本走で自動生成され、**3 件すべてに receipt・sidecar・attempt stream が揃った**
  (`critical_set_complete=true`)。逐語は
  `output/insights/2026-08-17_t190-launcher-failure-artifact/first-real-bundle/`。

  | worker | nodeid の述語 | attempt 1 preflight | attempt 2 preflight | 強制停止 | receipt 公開 / wall 予算 |
  |---|---|---|---|---|---|
  | gw27 | `FileNotFoundError` (attempt-0002.output.md 不在) | 0.343 秒 | **1.053 秒** | SIGTERM 1.054 → SIGKILL 1.109 | 2.625 / 3.0 秒 |
  | gw33 | `assert False is True` | 0.285 秒 | **1.042 秒** | SIGTERM 1.043 → SIGKILL 1.100 | 2.456 / 3.0 秒 |
  | gw47 | `assert 'max_attempts' == 'max_model_calls'` | 0.292 秒 | **1.105 秒** | SIGTERM 1.106 → SIGKILL 1.163 | 2.647 / 3.0 秒 |

  **確定した機序:** 3 件とも同一である。retry の attempt 2 で preflight が
  attempt 1 の **3.6 倍前後 (1.04〜1.11 秒)** に膨らみ、
  fixture の `--evidence-grace-s 1.0` を**食い切る**。child が rollout evidence を出す前に
  evidence deadline が満了するため `evidence_forced_stop=true` となり、launcher 自身が
  SIGTERM → 約 57 ms 後に SIGKILL を送って attempt を殺す。
  `limit_trigger` はどの attempt でも立たない (**全 snapshot が `conditions_met: []`**) ので
  `_writer_truth` は `max_attempts` へ落ち、各テストが期待した終端状態と食い違う。

  **この帰属が覆した既存の見立ては 2 つある。**
  - **wall clock は律速ではない。** 3 件とも receipt 公開が **2.46〜2.65 秒**で、3.0 秒予算に
    0.35〜0.54 秒の余裕を残している。F285 の「予算 3.0 秒の縁に常時張り付いている」は
    走 A (`limit_trigger=max_wall_clock_s` 21 件) で観測された**別の sub-mode** であり、
    F57 族の唯一の機序ではない。**本エントリが 2026-07-30 から
    「3 秒超過そのものを根本原因と断定しない」と留保してきたのは正しかった。**
  - **`-9` 型の終了は外部 kill とは限らない。** 本件は
    `termination_initiated_by_launcher=true` と送信 signal 2 本が記録されており、
    **launcher 自身の強制停止**だと確定できる。F285 が「原理的に事後判定できない」とした
    区別が、launcher が元々持っていた情報を記録するだけで付いた。

  **後続への含意:** fixture harden は **wall (`3`) ではなく evidence grace (`1.0`) が対象**である。
  ただし本 wave では変えない (D249 の順序と、絶対規律 2 の「予算拡大は根拠を得てから」)。
  「なぜ retry の preflight だけが 3.6 倍になるか」(`_attempt_loop` 冒頭の
  codex executable 再 hash と hook 再検証の I/O が疑わしい) は未分離で、
  これを詰めてから予算値を決めるべきである。
