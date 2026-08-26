---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 10
---

## 新規

### {{F:fold-carry-recursion-depth}}. 台帳の成長だけで fold が再帰上限に達し、全 wave の受入が止まった [ドリフト] [恒真ゲート]

- 事象: main 単独で受入の実台帳検査が `RecursionError: maximum recursion depth exceeded` で
  赤になった。`tools/spool_fold.py` の `substantive_digest` が worklog の carry 鎖を
  自己再帰で遡っており、carry stub が世代を重ねた結果 Python の既定再帰上限を超えた。
  **flaky ではなく、台帳が伸びるほど確実に踏む。** 全 wave の受入が同じ赤で止まった。
- 根本原因: 深さが台帳データの世代数に比例する再帰。**越えた窓は 2026-08-27 06:21〜06:51 の
  fold commit 4 件の中で、その窓で fold の実装は 1 行も変わっていない。**
  つまりコード変更を伴わずに、データの成長だけで越えた。30 分・fold 4 回で越えたので、
  余裕はほとんど残っていなかったことになる。
- 恒久対応: 末尾呼び出し 1 箇所を `while` へ写し、深さを O(1) にした。4 つの拒否条件
  (carry-cycle / item 不在 / ordinal 一意性 / 過去参照でない) は順序も Issue 本文も不変。
  **再帰上限の引き上げは採らなかった** — 対症療法であり、台帳が伸びればまた越えるためである。
- 再発検知: `orchestrator/tests/test_spool_fold.py` の実台帳複製系
  (`test_failure_supersede_real_*_is_byte_exact`、
  `test_n37_real_repo_canonical_family_requires_archive_active_history`) が、
  実 canonical を複製して byte 完全一致を検査する。深さが O(1) になった後は
  データ成長で再発しない。

### {{F:red-signature-varies-with-stack-consumption}}. 同一原因の受入赤が走らせ方で件数を変え、node ID 一致の登録が原理的に使えなかった [恒真ゲート] [テスト代表性]

- 事象: 上記の再帰上限赤について、並行セッションは 3 件、こちらは 4 件を観測した。
  同じ木・同じ原因である。**再帰上限は「呼び出し側がどれだけスタックを消費したか」で
  決まるため、上限に達する場所と顕在化する node 集合が走行ごとに変わる。**
  例外の traceback も `re.finditer` の内部や `flags.value` の property 呼び出しなど、
  上限に達した瞬間にたまたま実行中だった場所を指す。**再帰の主体は traceback の底に出ない。**
- 根本原因: 赤の signature (node 名・例外位置) を同一性の代理に使うと、
  資源上限型の失敗では代理が原因と 1 対 1 に対応しない。
  **顕在化する集合が動くものを、complete node ID の literal 比較で登録することはできない。**
  3 件を登録した翌日に 4 件目が出て、また受入が止まる。
- 恒久対応: 資源上限型は登録でなく構造修正で閉じる
  ({{F:fold-carry-recursion-depth}} の恒久対応)。
- 再発検知: 赤を「非帰属」「既知」と判定する前に、
  **本文 (assertion 文字列・例外種別) まで読んで根本原因を特定する**規律
  署名の見た目が一致しても、本文が違えば別の原因でありうる。逆も同じで、
  本文が同じなら node 名が違っても同一原因でありうる。**束ねる単位は本文である。**

### {{F:non-attributable-receipt-path-is-unwired}}. 受入の非帰属受領証は land 側も launcher 側も受理するのに、待ち手が該当欄を空に固定して発火しない [恒真ゲート]

- 事象: main 単独の決定的な赤を抱えたまま land する正規経路として
  `verdict = "non-attributable-only"` の受領証が設計されている。
  `tools/dev_wave_land.py` はこの verdict を受理し、`tools/acceptance_launcher.py` は
  `child_rc == 1` と `red_check` の dict を受け付ける。
  **ところが `tools/dev_wave_wait.py` の受領証生成が `red_check` を無条件に `None` と
  書き込む。** そのため `child_rc != 0` は必ず `runner result is not receiptable` で落ち、
  この経路は**構造的に一度も発火しない。**赤を分類する checker も使用停止済みである。
- 根本原因: 受理側 (land・launcher) と生成側 (待ち手) の契約が食い違ったまま残った。
  受理側だけを見ると経路が生きているように読める。
- 恒久対応: **本 wave では直していない。**発火しない事実を台帳へ記録し、後続の修理項目とする。
  当座は、決定的な main 側の赤は構造修正で閉じるほかない。
- 再発検知: 「機構が在る」ことの確認を受理側の実装だけで済ませず、
  **生成側が実際にその値を作りうるか**まで辿る。
  受理条件が書かれていることは、その条件を満たす入力が作られることを意味しない。

### {{F:frozen-artifact-records-a-closure-that-later-shrank}}. 凍結成果物が記録した閉包の説明文字列が、閉包の縮小で現行と食い違った [ドリフト]

- 事象: enforcement source closure の批准突き合わせを廃止して閉包が 25 path から 24 path へ
  減った結果、`campaign_verifier_epoch` の `identity_scope` 説明文字列が変わり、
  凍結成果物 `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json` が
  記録している文字列と食い違って検査が赤になった。
  **epoch の値そのもの (`E0` / `v1-authority-absent`) は 4 campaign すべてで不変**であり、
  計測の実体も受入判定も変わっていない。変わったのは説明文字列だけである。
- 根本原因: 検査が**凍結側の記録と現行コードからの再導出を等値比較**していた。
  凍結成果物は生成時点の世界を記録したものであり、閉包が正当に変われば両者は別の epoch の
  記述になる。等値比較は「閉包が永久に変わらない」ことを暗黙の前提にしていた。
- 恒久対応: 現行側と凍結側を**それぞれ独立の完全一致 golden** として固定した。
  現行の admission view は 24 path の文字列と厳密に一致すること、凍結 provenance は
  生成時の 25 path の文字列と厳密に一致することを、別々に検査する。
  **任意の旧文字列を許す互換分岐にはしていない。**凍結 3 点 (PNG / PDF / provenance JSON) の
  bytes は変更していない。
- 再発検知: `orchestrator/tests/test_s1_9pair_figure_provenance.py` が両側を別々に固定する。
  現行側が変われば現行 golden で、凍結側が変われば凍結 golden で落ちる。
  どちらの方向にも発火するので恒真ではない。
