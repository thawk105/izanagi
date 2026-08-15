---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1128-floor-same-root
seq: 3
---

## 新規

### {{F:ruling-implication-written-as-equivalence}}. 裁定文が片方向の含意を「同値」と書き、忠実な実装が 79 件を赤にした [誤前提] [手順漏れ]

- 事象: (2026-08-16) 段 6 fix 契約で親が「新しい private field の存在を
  `configuration_id == "sort_best"` と**同値**にする」と書いた。fix 子は書かれたとおり
  双方向の同値を実装し、計算ノードの焦点走で **79 件**が赤になった。うち **78 件**は同一行
  (`... は sort_best と同値でなければならない`) から出ており、原因は 1 本だった。
- 根本原因: 親が意図していたのは片方向の含意 (「field があるなら sort_best」) だが、
  逆向き (「sort_best なら field がある」) まで要求する語を選んだ。当該 field の注入は
  production の sort 経路が走るときだけ起きるので、pilot・注入 build seam・base 未使用の run では
  `sort_best` record が field を持たないのが正常であり、同値要求はそれらを全部拒否した。
  **同じ wave のレビューが「受理集合の過剰縮小」として潰した型を、親自身が別の場所で作り直していた。**
- 影響: fix 1 巡 (子 1 本 + 計算ノードの焦点走 6 本) を丸ごと消費した。
  実装子は指示に忠実であり、子側の欠陥ではない。
- 恒久対応: 裁定文で受理・拒否の条件を書くときは、**含意の向きを 2 文へ分解して書く** —
  「X があって非 A なら拒否する」「A で X が無くても拒否しない」。
  本 wave の第 2 巡 fix 契約 §2 がその形の実例である
  (逐語 = `output/insights/2026-08-16_t1128-floor-same-root/verbatim/`)。
- 再発検知: 裁定文に「同値」「iff」「と一致すること」が現れ、
  受理側の反例 (条件を満たすが field を持たない正常な入力) が 1 つも書かれていないこと。

### {{F:unbound-name-nameerror-masquerades-as-expected-code}}. 未束縛の名前による NameError が総括捕捉へ落ち、期待値と偶然一致して偽の緑になった [テスト代表性] [恒真ゲート]

- 事象: (2026-08-16) 失敗注入テストの fixture が `buildcache.MasstreeFetchContentError` を
  raise していたが、その test module には `buildcache` という名前が一度も束縛されていなかった。
  raise は `NameError` になり、production の総括 `except Exception` に落ちて
  `...-base-failed` へ分類された。`[configure]` / `[target]` パラメータは期待値と違うので赤になったが、
  **`[base]` パラメータは期待値がまさに `base-failed` だったため緑のまま通っていた。**
- 根本原因: fixture が意図した層に届いていないのに、期待値との偶然の一致で緑が出る形だった。
  段階別の例外分類は production 側では正しく書かれており、
  その分類を通る経路を fixture が一度も踏んでいなかった。
- 影響: 「prebuild の base 失敗が閉じた detail code へ変換される」という保証が、
  実際には一度も検証されていなかった。同 wave の焦点再レビューは同型の過剰決定を
  もう 1 件 (期待 node が後段 gate に決定されている) 指摘している。
- 恒久対応: 失敗注入の負例では、**注入した例外の型が production の意図した `except` 節に
  実際に入ったこと**を検査に含める。本 wave の第 3 巡 fix は
  `[configure]` / `[target]` / `[base]` の 3 パラメータが**それぞれ別の例外型と
  別の detail code** を通ることを固定した。
- 再発検知: 負例が緑なのに、期待する detail code が production の総括 `except` の値と
  同じであること。fixture が参照する名前が test module で束縛されているかの確認。

### {{F:dev-wave-waiter-returns-success-without-artifact}}. 待ち手が成果物・`.done` 不在かつ生産者生存のまま rc=0 で終了した [観測] [完了誤認]

- 事象: (2026-08-16) 背景 job の待ち手 `tools/dev_wave_wait.py producer` が、
  **3 回連続で**成果物ファイルも `.done` も存在せず、`--pid-file` の生産者 process が
  生存している状態で rc=0・出力ゼロで終了した。同じ wave の先行 6 本では正常に待っていた。
- 根本原因: 未特定。待ち手の出力が空で、判定の根拠が残らない。
  本 wave では原因究明より作業続行を優先した。
- 影響: 通知だけを信じていれば、未生成の成果物を「完了」として読みに行き、
  変異台帳が欠けたまま先へ進んでいた。実際には 3 点照合 (成果物実在・`.done`・生産者死)
  で毎回 fail-closed に検出できた。
- 恒久対応: **待ち手の rc=0 を完了の根拠にしない。** 成果物実在・`.done` の内容・
  `--pid-file` の pid が死んでいることの 3 点をすべて確認する。
  3 点が揃わなければ待ちを張り直す。本 wave は 3 回目で
  `.done` 出現までブロックする自前の待ちへ切り替えた (無出力・周期報告なし)。
- 再発検知: 待ち手が数秒で rc=0 を返し、出力が空であること。
