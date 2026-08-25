---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1594-nonattributable-landing
seq: 1
title: [T-1594] 非帰属の受入赤が出た wave の着地手順を正本化し、判定主体が道具から人間・AI へ移る境界を明示した (docs + コード、branch worktree-dev-wave-t1594-nonattributable-landing)
---

## 本文

- **着手の動機は正本の陳腐化だった。** `tools/dev_wave_wait.py` に `check_acceptance_reds` への
  参照は **0 件**で、D690 決定 2 の機械遮断は既に着地していた。ところが `DW-O18` は
  「rc=0+non-attributable-only は受理成功」と、**もう存在しない受理経路**を指し続けていた。
  セッションごとの手作業回避はここが温床だった。手順を書き足す前に、死んだ記述を消すのが本題だった。
- **判定主体の境界は「受入が赤で戻った時点」に置いた。** 待ち手は受領証を出さず赤を返すだけで
  帰属を判定しない。以後は人・AI が判定し根拠を worklog へ残す。分岐は 4 つ — 自分起因は直す /
  非再現なら受入を 1 回再走 (反復しない) / 再赤と決定的赤は main 既存の F を証拠に hold 登録 /
  F 不在・判定不能・原因未理解は除外せず停止。**受入の受理は `child-green` の 1 本のまま**で、
  絶対規律 2 の面は 1 bit も変えていない。
- **収容先は byte 予算に強制された。** `.claude/commands/dev-wave.md` は 9520/9520 で満杯、
  孤児 H2 検査と条件 dispatch 束縛が新節を塞ぐ。`DW-O18` 自体も L2 単節予算 1000 bytes に対し
  **ちょうど 1000 bytes** で、死んだ段落が空けるのは 279 bytes しかなかった。
  親が正式手順を起草すると **1193 bytes** 必要で入らなかった。段 3 の 2 レンズも独立に
  597 / 1214 bytes と見積り、**(P2) の素朴形は実測で反証された**。
- **解決は `DW-O18` / `DW-O26` の分割。ただし理由は byte の掻き集めではない。** 焦点走の構成規則
  (変更 test の単独走・新規 test のメタテスト・並行 wave の相乗り) は
  `DW-O26`「焦点走の consumer test 拡張」の主題そのもので、`DW-O18` にあったこと自体が
  元々の置き場所の誤りだった。実測は `DW-O18`=998、`DW-O26`=830 bytes。
- **F の循環は新機構を作らず fail-closed で断った。** `FlakyTestHold` は `docs/failures.md` に
  実在する F 番号を import 時に要求するが、F の採番は land の fold が行う。よって wave 内で
  新規 F を採って hold することはできない。手順を「main に**既にある** F を証拠にできるときだけ
  登録し、無ければ登録せず裁定へ送って停止する」と定めた。D662 決定 4/5 と整合し、
  受理集合を 1 bit も広げない。
- **段 6 の敵対レビュー 2 本が独立に同じ穴へ到達した。** 確定していた `DW-O18` は受入再走に
  上限も再赤時の停止も定めておらず、`child-green` を保ったまま「緑が出るまで回す」経路が
  開いていた。レンズ A は受理確率が反復回数とともに 1 へ近づく形で、レンズ B は
  single-file green / acceptance red 型のフレークが hold 分岐へ一度も入れず無限再走になる形で
  到達した。**本 wave が塞ぐつもりだった穴そのものを、自分で作っていた。**
  1 文の書き換え (`非再現なら受入を1回再走。反復しない。`) で両方を閉じた。
- **もう 1 件の blocker: 禁止語が backtick の有無で迂回できた。** 平文で書けば素通りする。
  平文 substring へ強化した。あわせて負の対照 M9 の文言が
  「非帰属の確認後に受理成功を記録する。」で、これは廃止した受理経路そのものと読め、
  **それを緑として固定してしまっていた**。受理条件に触れない中立文へ差し替えた。
- **合成 fixture の参照不足で焦点走が 315 件赤になった。** 正本へ新しい `D690` と
  `orchestrator/tests/flaky_test_holds.py` を書いた結果、`_build_min_repo()` にそれが無いため
  参照実在検査が毎回 2 件余分に発火し、finding 集合を厳密一致で検査する全テストが落ちた。
  **allowlist で免除せず fixture を足して直した。** 315 → 1 → 0 と実数で確かめた。
- **変異の単一理由性を 2 度破っていた。** M6 は合成 repo に `tools/check_acceptance_reds.py` が
  無いためパス実在検査が併発し、M3 は節が 988 → 998 bytes になったことで置換後 1010 bytes となり
  単節予算が併発した。前者は fixture 追加、後者は変異を削除形へ変えて閉じた。
  **親が全変異の変異後 byte を実測**し、超過が M3 だけであることを確かめた。
- **段 4 の変異事前登録に層の取り違えがあった (erratum)。** 段 4 で登録した M1〜M9 は
  テスト内の合成 fixture に対する負例を記述したもので、harness が production 実体へ注入する
  変異とは層が違う。production 層の変異 P1〜P9 を段 6 で追加登録した。初回登録は消さず残す。
- **変異の初回本走は baseline PASSED・KILLED 3 / MISMATCH 1 / SURVIVED 5 で、うち 4 件は mask だった
  (erratum、初回結果は消さない)。** 正本の必須文を壊す P5〜P8 が期待した
  `test_normative_exact_section_pins_accept_real_repo` は `GROWTH_TEST_HOLDS` に登録されており
  **既定 skip** である (解除はユーザー明示命令のみ)。`DW-M02` に従い実効 gate へ再照準し、
  **4 文をそれぞれ実 repo へ 1 件ずつ注入して `check_docs.py` を直接走らせたところ 4 件とも
  rc=1 で検出**し、いずれも `DW-O18` の exact 不一致として報告された (復元は全件 git 照合で確認)。
  **実 repo の正本改変を守る実効 gate は `check_docs.py` の直接実行であって pytest node ではない。**
  P1 の MISMATCH は親の期待集合の誤りで、実際には予測より 1 件多く 7 node を検出していた
  (予測外に raw HTML 拒否テストが落ち、pin 除去では落ちない正例テストを予測に入れていた)。
  期待集合を是正し、実効 gate が pytest node でない P5〜P8 を外した spec で再走した。
- **launcher が 2 度 `evidence_status=invalid` で成果物を不採用にした** (fix2 と fix4)。
  いずれも編集自体は tree に入っており、報告は artifact の `attempt-0001.output.md` から
  直接回収して内容を確認した。既知の握り潰された例外で、内容とは無関係である。
- **焦点走の対象が production consumer 集合より小さかった。** レンズ B の指摘で
  `test_s8c_preregistration_invariant.py` (`check_docs.main()` を直接呼ぶ) など 3 file を足すと、
  通過テストが 526 → 998 に増えた。`DW-O26` の要求どおり参照関係で引くべきだった。
- **待ち手を pid file 実在前に張って即戻る形を 1 度踏んだ** (`DW-C01`)。子は生きていた。
  張り直して回復した。あわせて焦点走の runner が login node の bounded local で
  `scope-outcome-cap-oom` を踏んで dispatch へ fallback した直後に落ち、
  計算ノード job 947272 を孤児化させた。終了を待ってから走り直した。
- 設計判断は {{D:non-attributable-landing-boundary}} と {{D:dw-o18-o26-split}}、
  失敗は {{F:synthetic-fixture-reference-closure}} に記録した。

- **変異の再走は baseline PASSED・4/4 KILLED・負の対照 1/1 SURVIVED・MISMATCH 0 で全件期待一致した。**
  P1 は是正した期待集合 7 node が的中した。
- **段 8 の自己改善は 1 件が予算で止まった。** 「予算に張り付いた対象への変異登録では変異後 bytes も
  層に数える」という恒久対応を `DW-M01` (L1) と `DW-M04` (L1.5) の双方へ統合しようとしたが、
  **L1 は 214 bytes、L1.5 は 213 bytes 超過**した。`docs/skill-self-improvement.md` は予算のための
  安全義務削除を禁じ、収まらなければ変更を止めて裁定へ返すと定めるので、正本統合は行わず
  failures 台帳の記載のまま {{T:mutation-byte-layer-doc}} として裁定へ送る。

- **本 wave が正式化した手順を、自分が最初の利用者として実行した。** 受入 1 回目は 13 failed
  (16372 passed)。assertion 本文と差分実体で判定した結果、12 件は既知の非帰属赤と逐語一致
  (`assert repo_before == _real_output_snapshot()`、差分は実 `output/` に `runs/` と
  `task-runs/reports` が増えた)、1 件は fd 番号の再利用テストだった。**単独再走 13 passed /
  24.37 秒で全件非再現**。手順どおり受入を 1 回だけ再走し、**1 failed / 16384 passed** になった。
- **再赤なので反復せず、main 既存の F480 を証拠に hold を登録した。** 赤は
  `test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`
  で、破れたのは `first.join(10)` 直後の `assert not first.is_alive()`。F480 が定める判定 3 点
  ((a) 単独走の緑 = **1 passed / 13.56 秒**、(b) 差分の到達不能性 = 本 wave の差分 6 file 中
  dispatch/pegasus 系 0 件、(c) 破れた assert が実時間の上界) をすべて実測で満たした。
- **registry が親の言い換え署名を拒否した。拒否は正しい。** `failure_signature` は F 節の本文に
  (backtick 除去・空白正規化のうえ) 逐語で存在することを要求する。F480 節に実在する
  `assert not first.is_alive() and not second.is_alive()` へ差し替えて通した。
  **「main 既存の F を証拠にする」経路は、F の本文と署名の一致まで機械が検証する** —
  名ばかりの証拠では通らないことが実測で確かめられた。
- **契約テスト 2 件が「registry はちょうど 1 件」の pin で赤になった。** D662 決定 5 が
  「登録数が増えること自体は問題としない」と定め「新規登録に上限や事前承認を課す」案を明示的に
  不採用としているので、これは承認ゲートでなく保守 pin と裁定した。exact 比較を維持し既存 hold の
  per-field assertion を全部残したまま 2 件へ更新し、test 名も実体に合わせて改名した
  (焦点走 **27 passed / rc=0**)。

## 次の一手差分

### 完了

- [T-1594] 非帰属の受入赤が出た wave の着地手順を `DW-O18` の正本へ落とし、判定主体の境界を
  明示した。`DW-O26` へ焦点走の構成規則を移設し、`tools/check_docs.py` に全節 exact pin と
  operations 全体の禁止語検査を新設した。
  remaining: none
  base: 6b498cc702ab5a34976024b9a1815e6ddb65fa1af337b973870768f2ab0c3845

### 新規

- {{T:condition-18-dual-trigger}} **P1・ユーザー裁定待ち**: 受入を投入した context と赤を処理する
  context が別になると、`DW-O18` が一度も読まれない時系列が現行 dispatcher で成立する。
  修正案 `親のテスト・受入前と赤処理前` は現行 trigger より **3 bytes 短く**、入口の byte 予算を
  増やさない (段 3 レンズ B が実測)。**親が段 4 で使った「予算満杯だから二重点火できない」という
  理由は無効である。** 要るのは `CONDITION_TRIGGER_CONTRACT` の改訂と、現行 trigger を pin する
  既存負例テストの期待値変更で、後者があるため親裁定では動かさずユーザーへ返す。
- {{T:land-receipt-authenticity}} **P1・ユーザー裁定待ち**: `tools/dev_wave_land.py` の受領証は
  真正な launcher の発行物であることを証明する署名・nonce・fencing token を持たない。段 3 レンズ A が
  手書き JSON で `non-attributable-only` も**偽の `child-green`** も受理させる操作列を提示した。
  旧 verdict 分岐の削除だけでは閉じない。閉じるなら issuer provenance と anti-replay の設計が要る。
- {{T:f-preallocation-two-stage}} **P2・ユーザー裁定待ち**: 新規 F を要する決定的な非帰属赤に対し、
  「evidence 登録 wave → hold 登録 wave」の二段階を正式化するか、hold registry が spool fragment を
  証拠に取れるようにするか。本 wave は fail-closed 停止で回避したが、その分岐は塞がったままである。
- {{T:d690-five-minute-clock}} **P2・ユーザー裁定待ち**: D690 の 5 分が queue 待ちと pytest wall を
  含むのか、診断・登録の作業時間だけかを確定する。含むなら、`child-green` を維持したまま同一 wave が
  5 分で着地することは構造的に不可能である (受入本体だけで 5 分 41 秒の実測がある)。
  親は本 wave で D690 を再解釈せず、文言のまま正本へ書いた。
- {{T:flaky-hold-cause-semantics}} **P3・ユーザー裁定待ち**: `FlakyTestHold` の `cause` は非空しか
  検査されず、帰属 verdict・判断者・tested tip を束縛する field が無い。自分の差分が原因でも
  「資源競合」と書けば schema 上は通る。手順側の原因理解義務を機械強制と report してはならない。
- {{T:mutation-byte-layer-doc}} **P3・ユーザー裁定待ち**: 「予算に張り付いた対象への変異登録では
  変異後 bytes も赤理由の層に数える」を `DW-M01` / `DW-M04` へ統合しようとしたが、
  L1 が 214 bytes、L1.5 が 213 bytes 超過して収まらなかった (親が実測)。予算値の変更は
  自己改善の対象外で独立審査を要するため、正本統合は行わず failures 台帳の記載に留めた。
  同型は本 wave だけで 2 回発火している (変異 M3 と P7)。
