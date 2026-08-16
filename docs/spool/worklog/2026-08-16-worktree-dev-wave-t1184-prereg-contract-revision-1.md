---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: worktree-dev-wave-t1184-prereg-contract-revision
seq: 1
title: 8c 事前登録の証拠契約を第 3 世代へ改訂した — 恒真だった負の対照 6 件が発火するようになり、受理集合は 1 bit も広がらない (コード + テスト + docs + 凍結記録、branch worktree-dev-wave-t1184-prereg-contract-revision、変異 matrix = 6/6 一致)
---

## 本文

前 wave (580) が採番順序の閂で止め、D438 として実装形だけを land した改訂を実施した。
D439 形 1 (裁定を記録した決定が既に main へ着地している) に該当するため、第 3 世代の凍結記録は
`ruling_reference = D438` を引けた。前 wave の段 2 プラン・段 3 レンズ 2 本・段 4 裁定書を流用して
段 4 から再開した (読み込み契約の「変更面の骨格が同一」型)。

### command 引数の一次資料指定を親が訂正した

command は「前 wave の段 2 と段 3 が独立に列挙して 13 件で一致した nodeid 一覧を一次資料に使え」と
指示したが、**その 13 件は段 4 が不採用にした「条件 11 を充足側の終端へ動かす」案の前提で
数えられていた**。D438 決定 (1) は終端を動かさないと定めたので母集合が異なる。予測として使い、
確定は実測で採った。実際に赤になったのは 4 件で、13 件一覧が挙げた
`test_candidate_is_not_effective_and_has_zero_satisfied_predicates` は赤にならなかった
(充足を返す述語は 0 件のままであるため)。

### 段 6 の敵対レビュー 2 本がいずれも NO-GO を出し、2 件の must-fix を親が実測で裏取りした

- **契約の条件 11 が要求する証拠 field path 5 件のうち 4 件が、実装に存在しない識別子だった。**
  `grep -c` で `orchestrator/campaign/p3_autonomous_workload_trial.py` を数えると
  `MAX_APPROVED_GENERATIONS` は 3 件実在するが、`main.generation_cap` /
  `run_trial.generation_cap` / `_run_workload.generation_cap` /
  `_run_workload.critic_feedback_consumer` はいずれも **0 件**だった。実在するのは
  `args.max_generations`、keyword 引数 `generations`、`apply_critic_feedback` である。
  改訂前からある欠陥だが、そのまま第 3 世代として凍結すると**嘘の証拠要求を凍結する**ことになる
  ため実在名へ直した。
- **段 8c の運用 runbook が承認上限を 1 と現在形で記していた。** 実装は
  `MAX_APPROVED_GENERATIONS = 2` で、D410 本文は逐語で「D114 の承認上限 1 を 2 へ上げる」と定めて
  いる。runbook は 2 箇所で「上限 1」「2 世代で走らせない」「機構は未実装」と書いており、
  従うと `G=1` の系列が作られる。歴史記述は遡及改変せず、失効を明記する形で直した。

### 親が却下したレビュー提案

レンズ A は「評価器に予算 validator の実引数と consumer edge の AST 検査を足せ」と提案した。
指摘自体は real (実引数の定数化と内部 edge の切断は現行検査を素通りする) だが、**その検出を
評価器に持たせる案は D96 が名指しで却下済み**である — 「consumer 閉集合の AST 固定は構文形状しか
固定できない (`if False`・alias・`getattr`・例外握り潰しを見逃す一方、無害な refactor で偽赤になる)」。
前 wave の段 4 も同じ理由で終端の充足化を撤回している。6 評価器の終端が
「機械検査可能な充足証明が無い」のままであるのは、まさにその証明が機械検査できないことを
正直に表明しているからである。却下済みの決定を再び開かない。

### pin 閉包の取り残しは実走でだけ露見した

親 brief は「生きた契約 hash の pin は 2 箇所だけ」と実測して書いたが、**実際は 5 箇所**だった。
`test_evidence_contract_hash_accepts_non_path_controls` の 3 param が、生きた証拠契約の bytes を
改変してから hash する形で literal を持っており、**成果物 path 検索でも現在値検索でも見つからない**。
段 5 実装子・敵対レビュー 2 本のいずれも見落とし、計算ノードでの実走だけが検出した。
詳細と恒久対応は {{F:live-derived-hash-pins-invisible-to-search}}。

### 契約全条件の識別子実在走査 (副産物)

fix 子に契約の全条件について `.py` 証拠の識別子実在を走査させたところ、条件 2・3・4・5・6・7・8・
9・10・12 にも未実在識別子があった。ただしこれらは**未実装の将来機構を証拠として記す正常な形**で
あり (条件 5・6・7 は module 自体が未実在)、条件が未充足である理由そのものである。条件 12 の
名前不整合は事前登録文書 §6 が既に既知として明記している。条件 11 だけが「機構は実装済みなのに
契約が別名を書いていた」型であり、そこだけを直した。両者を機械で区別する検査は無く、
{{T:contract-identifier-existence-audit}} へ起票した。

### 変異 matrix と、変異では測れなかったもの

6 件すべてで期待と一致した (5 KILLED + 正例 1 SURVIVED)。wave 前の実コードの形
(全条件 `machine_checkable: false`) を撃つ変異を含む。契約 JSON を触る変異は生きた契約 hash の
pin 4 件を同時に落とすため、各変異固有の検出力は残りのノードで数えた (冗長ゲートの明記)。

**凍結チェーンのゲートだけは変異で測れなかった。** 当該テストは `pytest.mark.xdist_group` を持ち、
loadgroup 実行では FAILED 行の node ID に `@<group>` が付く一方、`--collect-only` の node ID には
付かない。変異 harness の node 正規化は `@<group>` を落とさないため、期待 node をどちらの空間で
書いても片側で必ず外れる (起動前検査で 1 度 `rc=2` で止まった)。runner 範囲から当該ファイルを
外して期待 node を範囲と対にし直し、凍結チェーンについては**直接の前後証拠**で代替した —
第 3 世代の記録を作る前の走行では当該テストが赤、作った後の走行では緑であり、
改訂と世代記録を別 commit に分けられないことがこの 2 点で実証されている。

### 受入直前の main 取り込みで、条件 12 に関する新事実 (D441) が入った

本 wave の記録 commit 後に main を再確認したところ 10 commit 進んでおり、そのうち D441 が
**条件 12 について本 wave 向けに書かれた実測**を含んでいた。同 D は逐語で「`machine_checkable` を
反転すると C12 は誤った診断を出す」「この値は契約を改訂する側が反転前に知る必要がある」と述べ、
却下選択肢では「本 wave で契約 JSON・評価器・凍結世代を改訂する — 稼働中の別 wave が同一面を
所有している」として改訂を本 wave の所有と明記している。

実測の内容は 2 点である。

- 反転後の条件 12 は `UNSATISFIED / environment-contract-consumer-absent` を返すが、この理由が
  指す 2 つの consumer は**実際には 8c で走っている** (別 module の別名経由)。したがって反転は
  単に赤を出すのではなく、**実在する強制を「不在」と誤って報告する**。
- 評価器の到達判定は同一 module 内の top-level 定義しか辿らないため、**正しく cross-module 実装
  しても条件 12 は永久に充足できない**。

**本 wave はこれを理由に D438 決定 (1) を一部不採用にはしなかった。** 同決定は条件 12 を名指しで
反転対象としており、`DW-S04` は「承認済み裁定を親が不採用にせず、新事実を添えてユーザー再裁定
待ちへ戻す」と定めている。D441 自身も反転を禁じておらず、警告として値を残している。
したがって D438 のとおり 6 条件を反転して land し、新事実は
{{T:c12-flip-emits-false-absence}} へ起票する。受理集合は反転前後で変わらない
(どちらも非充足) ため、この誤診断が certified 選択・材料レポート・試行台帳の値を変えることはない。
変わるのは診断の正確さであり、規律 3 の観点で本物の劣化である。

### 段 8 自己改善は予算で止めた (ユーザー裁定へ返す)

候補は 1 件 — 「段 4 裁定書は、後続 wave が流用してよい成果物と不採用案に属する成果物を分けて
書く。不採用案の前提で数えた件数・一覧を後続の一次資料にしない」。本 wave の 13 nodeid 一覧が
まさにこの事故であり、routing 先は `DW-S04` (段 4 裁定) が適切だった。
**しかし L1 の unique footprint 予算に余白がゼロで、190 bytes の追記が
`10815 bytes > 予算 10625 bytes` で赤になった。** 意味の合う L2 節も無い
(`DW-O12` は「裁定手順と実行手順の食い違い」が発火条件であり、裁定書の書き方ではない)。
自己改善契約の「予算に収まらなければ止めてユーザー裁定へ返す」に従い、実装せず
{{T:s04-adjudication-artifact-separation}} へ起票した。予算値の引き上げは提案しない。

同様に、{{F:live-derived-hash-pins-invisible-to-search}} の恒久対応も `DW-O09` へ書けなかった
(996 / 1000 bytes で余白 4 bytes)。**dev-wave docs の予算は、実測で得た 2 件の恒久対応を
いずれも受け入れられない状態にある。** 棚卸しは過去 2 wave が独立に「削除可能な節ゼロ件」を
実証しており、圧縮では空かない。

### 受入 1 回目はフレーク 1 件で緑を逃した

受入全走は `1 failed, 11589 passed in 157.48s`。赤は
`orchestrator/tests/test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release`
の 1 件で、checker は帰属と判定し受領証は発行されなかった。**本 wave はこのファイルを 1 行も
触っていない。** テストは待ち手の `main()` が失敗した後に SIGTERM handler が復元されたことを、
自プロセスへ SIGTERM を送って確かめる形で、期待 `[SIGTERM]` に対し実測は `[]` だった。
11,589 件の xdist 並列走行下ではシグナル配送が `finally` の復元より遅れうる。
`DW-O18` に従い単独走で実測したところ `1 passed in 2.50s` で再現しなかったため、
帰属せずフレークとして {{T:dev-wave-wait-sigterm-restore-flake}} へ起票し、受入を再投入した。

### 工数

Codex 子 4 本 (段 5 実装 467 秒 / 段 6 レビュー 2 本並列 452・399 秒 / 段 6 fix 445 秒)。いずれも
`gpt-5.6-sol` reasoning=high で受理検査 rc=0。**実装子と fix 子はどちらも `tools/run_tests.py` の
bounded local が cgroup を attest できず `rc=16` で止まり、pytest を 1 件も実走できなかった**
(F155 の既知事象)。テスト実走はすべて親が計算ノードへ回した。

## 次の一手差分

### 完了

- [T-1132] 証拠契約が 12 条件すべてを機械検査対象外と記していた件を直した。評価器を持つ 6 条件
  だけを機械検査対象とし、終端と充足可能集合は変えていない。恒真だった負の対照 6 件が
  発火するようになった。
  remaining: none
  base: 3d75352fdb8e891bcc599dd39d3308a1977f77b4f2a7a2c048929b618347d2b3
- [T-1133] 条件 11 の証拠を、作らないことが確定した 2 つの方針成果物から、承認上限定数・
  3 入口の予算 validator・閉じた第二層射影へ差し替えた。条件 11 は「証拠が欠けている」から
  「機械検査可能な充足証明が無い」へ移り、どちらも非充足であるため受理集合は広がらない。
  残余の「exact G=2 を要求する受入 consumer が無い」は [T-1185] が持つ。
  remaining: none
  base: 15ff44cf2b273ce88a1cd3d2304cf80bfb64c87ba799425c802a913441691856
- [T-1134] 条件 3 / 8 を、内容 commit と発効 commit を分ける二段束縛へ改めた。manifest は
  自己識別子も自身の digest も持たず、祖先代用の禁止は発効 commit の親集合の完全一致で維持する。
  互換 alias は残していない。契約と規範本文の形だけを直し、consumer 配線は [T-1187] が持つ。
  remaining: none
  base: 39a53490891423e93968591184c94d419869d04c301fa71c50be10cb15830fc7
- [T-1184] 証拠契約・規範本文・第 3 世代の凍結記録・境界テストを同一 commit で改訂した。
  受理集合は 1 bit も広がらない。変異 matrix は 6/6 一致。
  remaining: none
  base: 8eb3efbfe1a03ecbe0c16ab934999de4912e34f27e328671e4c0123ced8021d9

### 新規

- {{T:contract-identifier-existence-audit}} **P2・新規**: 証拠契約の全条件について、`.py` 証拠の
  `field_paths` / `reachable_from` が実在識別子かを機械検査する。本 wave は条件 11 の 4 件だけを
  直し、他条件の未実在識別子は「未実装の将来機構」として据え置いた。両者を区別する検査が無い
  ため、条件 11 型の食い違い (機構は実装済みなのに契約が別名を書く) が再び入っても気付けない。
- {{T:stale-generation-cap-in-design-docs}} **P2・新規**: `docs/phase3-8c-wiring-design.md` と
  `docs/phase3.md` が承認上限 1 を現在形で残している。D410 が 2 へ上げているため、後続の
  consumer 実装者が旧上限で作ると exact `G=2` の試行が入口か受入で拒否される。歴史記述を
  遡及改変せず supersession 注記を足す。段 6 のレンズ B が scope 外の裁定パッケージ候補として提示。
- {{T:machine-evaluator-absent-reason-code}} **P3・新規**: 評価器を持たない条件を
  `machine_checkable: true` にすると、原因は評価器 registry の欠落なのに
  `commit-blob-read-error` と報告される。専用の閉じた reason code を足す。前 wave の段 4 が
  起票のみと裁定し、本 wave でも段 6 の両レンズが独立に指摘した。受理集合は変わらず診断のみ。
- {{T:c12-flip-emits-false-absence}} **P1・新規・ユーザー裁定待ち**: 条件 12 は機械検査対象に
  なったが、返す `environment-contract-consumer-absent` が指す 2 consumer は実際には 8c で
  走っており、**実在する強制を「不在」と誤って報告する** (D441 決定 (4) の実測)。さらに評価器の
  到達判定は同一 module 内しか辿らないため、正しく cross-module 実装しても条件 12 は永久に
  充足できない (同決定 (2))。本 wave は D438 決定 (1) が条件 12 を名指しで反転対象としているため
  親判断で外さず、新事実を添えて返す。択一は「条件 12 を機械検査対象から戻す」「評価器の到達
  判定を cross-module へ広げる」「契約から allocation 節を外す」で、D441 決定 (7) が
  3 番目で消える保証を列挙している。受理集合はどの案でも変わらない。
- {{T:s04-adjudication-artifact-separation}} **P2・新規・ユーザー裁定待ち**: 段 4 裁定書に
  「後続 wave が流用してよい成果物」と「不採用案に属する成果物」を分けて書く義務を置く。
  routing 先は `DW-S04` だが、L1 の unique footprint 予算に余白がゼロで 190 bytes の追記が
  赤になった。意味の合う L2 節も無い。**dev-wave docs の予算は、本 wave が実測で得た
  恒久対応 2 件をいずれも受け入れられない状態にある** (もう 1 件は
  {{T:derived-hash-pin-closure-lint}})。予算値の引き上げは提案しないため、
  空け方 (機械検査への置換、節の再編、別 reference の新設のいずれか) の裁定を求める。
- {{T:derived-hash-pin-closure-lint}} **P2・新規**: 成果物を加工してから hash した pin を
  機械で列挙する検査を置く。{{F:live-derived-hash-pins-invisible-to-search}} の恒久対応は
  現状 memory 止まりである。`DW-O09` へ書けなかったのは同節が 996 / 1000 bytes で
  余白 4 bytes しかなく、既存行の圧縮が dev-wave docs の exact pin を壊すためである。
  節予算を増やさずに機械化する形を設計する。
- {{T:dev-wave-wait-sigterm-restore-flake}} **P3・新規**: 受入待ち手の
  `test_public_main_failure_restores_handler_without_release` が全走 (11,589 件、xdist) で
  1 回落ち、単独走では通った。自プロセスへ送った SIGTERM の配送が `finally` の handler 復元より
  遅れると空リストになる形である。**受入全走 1 本を無駄にする**ため、配送を待ってから
  assert する形へ直すか、シグナル経路を使わない検査へ置き換える。
- {{T:mutation-expected-node-xdist-group-space}} **P3・新規**: 変異 harness の期待 node は
  `--collect-only` の空間で検査され、実際の照合は FAILED 行の空間で行われる。
  `pytest.mark.xdist_group` を持つテストは後者にだけ `@<group>` が付くため、**その node を
  期待 node に書く手段が無い**。本 wave は runner 範囲から当該ファイルを外して回避したが、
  xdist group を持つ検査は変異で測れないまま残る。正規化を揃えるか、別の照合空間を定める。
