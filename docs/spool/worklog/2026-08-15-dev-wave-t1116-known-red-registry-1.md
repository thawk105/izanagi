---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1116-known-red-registry
seq: 1
title: 批准済み既知赤 registry は現 repo に trust root が無いため成立しないと実測で確定し、非帰属判定の実行体が wave tip 側にある現行の穴を特定した — 敵対 2 レンズが独立に NO-GO (docs のみ、branch worktree-dev-wave-t1116-known-red-registry)
---

## 本文

- 起点は 2026-08-15 の /rulings 全件束 (authority: ユーザー、控え =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-15-rulings-full-33rulings.md`)。
  [T-1116] = 択 (c) 批准済み既知赤 nodeid の registry を併設する、[T-1055] = 択 (b) registry +
  receipt へ nodeid を明記する。裁定には**「registry は『批准済み』であることを機械が確認できる
  形にし、任意の nodeid を後から足せる fail-open な逃がし道にしないこと (規律 2)」**という
  拘束が付いていた。
- **この拘束が現 repo では成立しないことを実測で確定し、実装せず裁定へ返した。**
  段 2 プランと段 3 の敵対 2 レンズが**独立に NO-GO**。親は各主張をコードで検算し、
  すべて成立することを確認した。`DW-S04` に従い親は不採用にせず、新事実を添えて再裁定へ戻す。
- **人間だけが動かせる trust root が repo 内に 0 件である。** `verify-commit` / `verify-tag` /
  allowed-signers は存在せず、git 呼出しに現れる gpg 関連は `--no-gpg-sign` /
  `commit.gpgsign=false` すなわち署名を無効化する向きだけだった。
- **書込みを禁止している機構は `hooks/` subtree だけである。** `hooks/guard_write.py` の
  拒否対象に `tools/` 配下は含まれない。`tools/check_codex_hooks.py` の pinned path 群は
  working bytes と HEAD blob の drift を検査するもので、**書込み禁止機構ではない。**
  「先例の registry は codex 子から書けない」という**親 brief の前提は誤りだった**
  (段 2 が倒し、親が実コードで検算)。
- **`refs/remotes/origin/main` も trust root にならない。** ローカル ref なので
  `git update-ref` による移動と実際の push を暗号学的に区別できない。加えて実測時点で
  `origin/main = a2cb460d`、`main` は **92 commit 先行**しており、
  1 回の push が全 entry の一括承認になる。
- **本 wave の主産物は別の所見である — 非帰属判定の実行体は wave tip が握っている
  ({{D:acceptance-red-check-interpreter-is-tip-bound}})。** 待ち手は wave working tree の
  `tools/check_acceptance_reds.py` を起動し、受領証へ束縛する blob sha を `tested_tip` から採る。
  land も `tested_tip:tools/check_acceptance_reds.py` としか照合せず、**`tested_main` 側の
  checker blob と比べる検査は 1 件も無い。** land の protected path は handoff と
  control container だけで `tools/` 配下を gate しない。
  → **wave は自分の tip の checker を書き換えるだけで自分の赤を非帰属に分類させ land を通せる。
  これは本 wave が新設する穴ではなく現行の穴であり、registry の有無と無関係である。**
  probe worktree が tested main に作られることは被験体を固定するだけで、判定者を固定しない。
- **段 3 が出した突破手順 2 件は親の検算でいずれも成立した。** (i) 2 wave 突破 — wave A で
  将来壊す exact nodeid を登録して緑で land し、wave B でその node を壊す。tested main 束縛は
  同一 wave の後付けしか防がない。(ii) 同一 wave 突破 — registry JSON を一切変えず tip の
  loader を「空 registry から active entry を合成する」実装へ変える。待ち手と land は
  blob identity しか照合しないので矛盾を検出できない。
- **D316 が waiver を却下した 3 理由は、registry 形でも 3 件とも生きていた**
  ({{D:known-red-registry-has-no-trust-root}})。(i) 赤を直さず迂回する形そのもの、
  (ii) 件数上限は snapshot 上限にすぎず再登録・交換を禁じていない、(iii) 批准 field を書くのは
  AI 自身。2026-08-15 裁定は最新の authority としてこれを覆したが、拘束文が (iii) を
  名指ししており、その (iii) が設計で潰せなかった。
- **[T-1055] の「receipt へ nodeid を明記する」は既に実装済みだった。** 受入受領証
  `dev-wave-acceptance-receipt/v3` は `red_nodeids` を持ち、land が非空・重複なし・整列を
  検査している。registry が入らない限り追加すべき field は無い。**依頼の純増分は
  「registry 由来 nodeid を非帰属と区別して書く」に縮み、registry が止まったため 0 になった。**
- **親の誤りを 2 件、子とレンズが倒した。** (a) 不変条件 I2 が自己矛盾していた
  (「読めない registry を空として通してはならない」と「無い・空・読めないで今日と完全に同一」は
  両立しない。空 registry でも単独再走 rc=1 は非帰属なので「全件 attributable」も誤り)。
  正しい形は「不存在または valid-empty は既存分類を保存、存在するが読取不能・不正なら
  probe より前に判定不能」。(b) 「今日と 1 bit も変わらない」は受理集合・分類・rc について
  正しいが、receipt schema を上げれば receipt bytes は必ず変わる。両者を分けて書くべきだった。
- **段 3 が減じた所見も 1 件ある。** レンズ B は「schema を v3→v4 へ上げると並行 wave の v3
  受領証が land で拒否される」を blocker としたが、受入受領証は tested main / tested tip に
  束縛されており main が進んだ時点でどのみち無効化される。版上げ固有の追加被害は
  「main 取り込み前に land しようとした wave」に限られるので blocker には数えない。
- **変異は事前登録していない。** 実装差分ゼロで受理集合が変わらないため `DW-S04` の免除に
  該当し、かつ段 3 が「実装前の時点で単一理由性を確認できた候補は 0 件」と判定した。
  `DW-M01` は確認できない変異を登録しないと定める。将来の実装 wave が使えるよう、
  段 2 の変異候補 6 件と段 3 の単一理由性所見を insight へ保全した。
- **ユーザーへ返す問は 3 つ** (控え = `rulings-inbox/2026-08-15-t1116-known-red-registry-no-trust-root.md`)。
  (1) 「批准済み」の定義 — 外部 trust root を導入するか / 弱く再定義して 2 wave 事前登録が
  残ることを受容するか / registry を採らず [T-1116] の別択へ戻るか。
  (2) 非帰属判定の実行体を tested main へ束縛するか (親の推奨は先にこちらを塞ぐこと。
  この穴が開いている限りどんな registry も意味を持たない)。
  (3) [T-1055] を [T-1116] へ併合してよいか。
- **段 8 の改善候補は 1 件で、予算で塞がれたため実装しなかった。** 本 wave で実際に効いた手順
  (裁定された択が過去に却下されていないか機構名で台帳を検索し、却下理由を不変条件へ写す) を
  `DW-S01` へ 1 行足そうとしたが、**実編集して測ると L1 unique footprint が
  10,745 bytes > 予算 10,625 bytes** で赤になった。L1 は余白ゼロである。
  意味等価な縮約もできず、話題の合う L2 節も無い。契約どおり変更を止めて `git checkout --` で
  復元し、[T-1100] が記録した予算閉塞へ委ねる。**同型の閉塞はこれで 3 例目である**
  (エントリ 557 が 2 例目)。予算値の引き上げは提案しない。
- 材料の正本 = `output/insights/2026-08-15_t1116-known-red-registry/`
  (段 2 プランと段 3 の 2 レンズの逐語)。
- エージェント工数: codex 子 3 本 (plan 1・consult 2)。すべて `check_codex_output` 受理。
  子は 3 本とも read-only sandbox で pytest を実走できず、いずれも非実走を正しく申告した。
  実測はすべて親が行った。

## 次の一手差分

### 更新

- [T-1116] **P1・要裁定 (2026-08-15 に択 (c) で裁定済みだが前提が実測で覆った)**:
  非帰属 checker は単独再走が緑 (`rerun_rc=0`) の赤を帰属に分類して land を止める。
  受入は 48 worker の分散走、再走は単独 node 走なので同時実行由来のフレークは構造上
  再現しえない。2026-08-15 に択 (c) (批准済み既知赤 nodeid の registry を併設する) で
  裁定されたが、**その拘束「批准済みであることを機械が確認できる形にする」が現 repo では
  成立しないことを実測した** — 人間だけが動かせる trust root が 0 件、書込み禁止は
  `hooks/` subtree だけ、remote-tracking ref はローカルで移動可能。
  D316 の却下理由 3 点が registry 形でも 3 件とも生きている。
  再裁定の択は (1) 外部 trust root を導入する、(2) 「対象 wave より前から main に存在する
  entry」を批准と弱く再定義し AI による 2 wave 事前登録が残ることを明示的に受容する、
  (3) registry を採らず別択 ((a) 再走 N 回 / (b) 差分到達可能性を入力に足す / (d) 現状維持) へ戻る。
  **親の推奨は、先に新規項の実行体束縛を塞いでから (2)。**
  成果物影響 = 未裁定のままだと、受入が rc=1 になった wave は正しく非帰属でも受入と checker の
  時間を捨てて land できず、非帰属受理の機構が実運用へ到達しない。
  base: a9d5fbb08f38520c993d1d75675dd22283a4552741b0ff17b948b6ce0320ecab

- [T-1055] **P2・[T-1116] に従属**: 受入受領証への既知赤 nodeid 明記。
  2026-08-15 に択 (b) (registry + receipt へ nodeid を明記する) で裁定されたが、
  **後半は既に実装済みだった** — `dev-wave-acceptance-receipt/v3` が `red_nodeids` を持ち、
  land が非空・重複なし・整列を検査している。純増分は「registry 由来 nodeid を非帰属と
  区別して書く」だけであり、registry が [T-1116] で止まったため実装対象は 0 になった。
  2026-08-13 の裁定 (「(b) の変形 = checker 統合」) による実装と end-to-end 試験の緑は
  そのまま有効で、残件だった「実受入で赤が出たときの非帰属受理を 1 度観測する」は
  [T-1116] の帰属誤判定によって到達できていない。
  本項を [T-1116] へ併合してよいかを裁定へ問う。
  成果物影響 = [T-1116] が解けない限り本項は単独で前進しないので、併合しないと
  未閉鎖の P1 が 2 件に見え続ける。
  base: 64b8ff4c6929f19e73dc840d94cca42f0b316d0d04d86615f80bdfd26d9d60a7

### 新規

- {{T:acceptance-red-check-interpreter-tip-bound}} **P1・新規・要裁定 (2026-08-15 実測)**:
  **非帰属判定の実行体が wave tip 側にあり、その権威が tested main へ束縛されていない。**
  待ち手は wave working tree の `tools/check_acceptance_reds.py` を起動し、受入受領証へ
  束縛する blob sha を `tested_tip` から採る。land の受入受領証検証も
  `tested_tip:tools/check_acceptance_reds.py` としか照合せず、`tested_main` 側の checker blob と
  比べる検査は 1 件も無い。land の protected path は handoff と control container だけで
  `tools/` 配下の内容を gate せず、監査は commit 列の provenance を見るもので差分の意味を見ない。
  したがって **wave は自分の tip の checker を書き換えるだけで自分の赤を非帰属に分類させ、
  land を通せる。** probe worktree が tested main に作られることは被験体を固定するだけで
  判定者を固定しない。塞ぎ方の候補は「checker の実行体を tested main の blob から取り出して
  走らせ、tip 版と差異があれば判定不能とする」。代償は checker 自身を直す wave で修正が効くのが
  次 wave からになること (運用上は既にそう扱われている)。
  成果物影響 = 未対処だと、land gate の受理集合を守る判定そのものを被判定側が差し替えられる
  状態が続き、[T-1116] でどんな批准機構を設計しても registry を経由せず同じ救済ができる。
