---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1574-t1529-t1495-swo-isolation
seq: 2
---

## 新規

### {{F:dead-store-elimination-vacuous-negative}}. memory 保護の負例を非 volatile の書込みで書き、compiler が store を消して保護を一度も踏まなかった [恒真ゲート]

- 事象: read-only 化した arena へ 8 つの allocation class から書き込む負例を作ったが、
  最初の class で「拒否されなかった」と落ちた。保護が効いていないように見えた。
  親が repo 外 probe で切り分けたところ、arena は確保され、要素も vector の領域も arena 内にあり、
  それでも非 volatile の書込みだけが通っていた。volatile 経由に変えると
  復元あり・復元なしのどちらも拒否された。
- 根本原因: 負例が `const auto saved = t; t = <別値>; t = saved;` の形で、
  `t` は volatile でない通常の lvalue だった。書いた直後に元の値へ戻すため、
  `-O1` の compiler は両方の store を dead store elimination で除去できる。
  除去されると保護された page へのアクセスが一度も発生せず、comparator は正常終了する。
  **負例が緑でも赤でも、保護を検査していない。**
- 恒久対応: memory 保護を掛ける負例は、compiler が除去できない store で書く
  ({{D:swo-isolation-boundary}} の実装では volatile pointer 経由)。
  8 class それぞれについて、保護ありは fault、保護を外す fault injection では PASS と
  clean matrix 一致になることを対で実測して残す。
- 再発検知: 保護を 1 箇所だけ壊す positive control を負例ごとに置き、
  期待値が反転しない負例を恒真として扱う。

### {{F:vendored-gitignore-drops-required-fixture}}. 上流 tree を逐語 vendor したら上流の .gitignore が必須 file を無視した [手順漏れ]

- 事象: masstree の pin 済み source 99 file を test fixture として repo へ取り込んだ際、
  上流の `.gitignore` に `/config.h` があるため `git add` では `config.h` が index に入らなかった。
  `config.h` は autoconf の生成物で上流では untracked だが、fixture としては必須である。
  実装子が commit 直前に気づき、親が `git add -f` で取り込んだ。
- 根本原因: 上流 tree を丸ごと取り込む設計は上流の ignore 規則も一緒に取り込む。
  取り込み先での必要性と、上流での追跡対象かどうかは別である。
- 恒久対応: manifest の全 entry が `git ls-files` で追跡されていることを要求する検査を置く
  ({{D:swo-dependency-manifest-location}} の fixture 検証器)。
  これが無いと fresh clone や再 vendor で静かに欠落する。
- 再発検知: fixture manifest と git 追跡集合の exact 一致を検査に含める。
  file 集合の過不足の両方向を赤にする。

### {{F:identity-churn-over-determines-mutation-kill}}. contract identity の変化がどの変異も kill するため、機構 gate が発火したかを覆い隠した [恒真ゲート] [計測汚染]

- 事象: 事前登録した 13 変異の probe を実走したところ全件 KILLED だった。
  しかし内訳を分けると、`orchestrator/campaign/sort_swo_oracle.py` を 1 byte でも変えると
  `TU_TEMPLATE_SHA256` から `ORACLE_CONTRACT_ID` が変わるため、identity を pin した
  11 node がどの変異でも落ちていた。この 11 node を引くと、
  fd の object identity 検査を外す変異 (MUT-5) は機構固有の落ち先を 1 つも持たなかった。
  **kill されているのに、その変異が狙った機構は何も検査していなかった。**
- 根本原因: 中央 producer の source が contract identity に入る設計では、
  identity pin が事実上すべての変異に対する冗長 gate になる。
  変異結果を件数だけで読むと、実効 gate の不在が見えない。
- 恒久対応: 機構の異なる変異どうしの共通部分を identity churn 集合として取り、
  各変異の観測 node からそれを引いた残りを機構固有として数える。
  機構固有が 0 件の変異は mask とみなし、実効 gate へ再照準する (`DW-M02`)。
  本 wave では MUT-5 に対して実経路の fd boundary rejection を固定する検査を新設した。
- 再発検知: 変異台帳へ「観測 node 数」だけでなく「機構固有 node 数」を併記する。
  機構固有 0 件の変異を KILLED として数えない。

## 再発

### F457

- **再発: 2026-08-25** — 本 wave の焦点走で `test_s1_direct_comparison.py` が
  `official output_root は repository 外でなければならない` で 21 件赤になった。
  `/tmp/.git` は 8 月 23 日 10:04 作成の空 directory として実在し、`rmdir` 後は 97 passed になった。
  **今回わかったのは 2 点ある。** (1) 計算ノードへ dispatch した走行でも同じ `/tmp` を見るため、
  この誤検出は login node 固有ではない。(2) 除去してから **約 30 分後に再作成されていた**
  (10:30 頃に除去、10:54 に再作成を実測)。
  既存記述は「14.5 時間存在し続けた」という長寿の観測だったが、短時間で復活する挙動も起きる。
  どちらの読み方も固定できないため、**長時間の受入全走はこの窓に掛かりうる**前提で扱う。
