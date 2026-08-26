---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1380-prereg-artifacts
seq: 1
title: [T-1380] 事前登録 artifact の発行は導出の権威が実在せず、既裁定 3 件の着手順序にも抵触する (docs のみ、実装面の差分ゼロ、branch worktree-dev-wave-t1380-prereg-artifacts、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- 依頼は「正式実験系列を止めている事前登録 artifact 3 件を発行する。裁定 D1077 で
  『設計文書を権威とし、そこから機械的に導出した値として発行する。導出であることを
  機械で照合できる形にする』と確定済み」だった。**発行しないと裁定した。**
  段 2 プラン、段 3 の敵対相談 2 本、親の独立実測が、互いに独立に同じ結論へ到達した。
  詳細と逐語は `output/insights/2026-08-27_t1380-prereg-artifacts-blocked/`。

- **依頼の前提を 3 つ訂正した。** (1) 依頼が「稼働中」とした
  `worktree-dev-wave-t1858-chain-shared-setup` は既に land 済みで、名指しされた 2 test file への
  編集は衝突しない。(2) **不在なのは 3 件ではなく 4 件である** —
  `attempt-registry.jsonl` (genesis) も不在で、binding の必須 field
  `attempt_registry_initial_sha256` がこれを指し、loader は内容 commit `P` に置かれた
  genesis blob の hash 一致を要求する。(3) 3 件を発行しても 12 述語のうち動くのは C05 だけで、
  C03 と C08 の評価器は artifact bytes ではなくコード形状を見る。

- **導出の権威が実在しない。** `s8c_schedule.validate_authority` が要求する 18 field のうち
  3 件が実運用の値と型・意味で矛盾する — `leakproof_context` は実運用では文字列だが
  schedule は JSON object を要求し、正式初期状態の `whiteboard` は空配列だが
  schedule は非空を要求し、`descriptor_binding` は arm ごとに異なるが schedule は
  全 cell 共通の単一 mapping を要求する。加えて production の権威解決関数は
  **無条件に例外を送出**し、authority は 1 つも存在しない。段 3 レンズ B が台帳を遡り、
  18 field の schema を導入した D530 が裁定したのは「caller 供給・閉じた key 集合・型・
  非空性」までで、**field 名と型対応は実装著者の選択**だと確かめた。schema 導入時のテストは
  production と異なる fixture 値を使っていた。

- **`campaign_id` / `freeze_id` / genesis の slot 集合も一意に決まらない。**
  `campaign_id` は実行 site から再計算して exact 一致を要求されるが正式 site が未確定、
  `freeze_id` はどの digest を使うかの規則が不在、slot 集合は反復数が事前登録 §5 の
  未記入欄で 8b が「値は凍結しない」と明記している。genesis は create-only かつ
  freeze ごとに唯一なので、**濃度を発明して発行すると誤った割当へ恒久的に束縛される。
  発行しないより悪い。**

- **本 wave の最も重い発見は、既裁定 3 件との抵触である。** D549 (2026-08-19) は
  `schedule.v1.json` の commit を「配線と権威の実体供給が完了する別 wave (T-1380) まで
  scope 外」とし、却下した選択肢に「暫定 authority で実装する — **段 3 の敵対相談 2 本が
  独立に不採用を推奨した**」と記している。D959 (2026-08-26) は manifest・二段束縛 record の
  不在と schedule authority の無条件 raise を上流条件に**従属する下流症状**と位置づけ、
  **順序を入れ替えて先に解除してはならない**と定める。D992 (2026-08-26) は
  共有批准凍結が active になるまで着手しないと定め、実測では
  `load_ratified_freeze()` が `[no-active]` を返し前提は未充足である。
  **D1077 の本文にも、それを記録した worklog の 1 行にも、これら 3 件への言及が無い。**
  2026-08-19 の敵対相談 2 本と 2026-08-27 の敵対相談 2 本が、互いを知らないまま
  4 本とも同じ答えを出した。

- **親の当初の value 主張を取り下げた。** 親は独立 probe で「schedule を足すと C05 が
  `EVIDENCE_UNDEFINED / schedule-schema-absent` から `UNSATISFIED /
  schedule-consumer-unreachable` へ進み SATISFIED は 0 のまま」と実測し
  (12 述語のうち差分は C05 の 1 行だけ)、これを値打ちとして brief に書いた。
  **段 3 レンズ A が正しく攻撃した** — 評価器は artifact を decode しないので
  1 byte の blob でも同じ遷移が起きる。遷移は正当性の証拠にならず、
  gap ledger が「schema は成立した」と誤読される危険すらある。

- **peer の中継裁定を裏取りして断った。** `/rulings` セッションから「B-4 事前登録 §5 の
  実行責任者欄を本 wave の変更単位で記入してほしい。裁定本文は着地済み」という依頼が来たが、
  local main の `docs/decisions.md` に当該裁定は無く、worklog は同じ指名を**未了の人間手番**と
  記していた。加えて当該セルは `実行責任者・開始時刻` の 2 項目が同居しており、
  §6 前提条件 1 が「§5 の全欄が記入済み」を要求するため、**実行責任者だけ書くと
  開始時刻が未確定のまま関門を通る。** 実測を添えて返したところ、peer は両方の指摘を認め、
  「着地済み」は同 branch 由来の別 2 件についての記述であり実行責任者の裁定は
  どの台帳にも未着地だと訂正した。

- 本 wave は実装面の差分がゼロのため変異 matrix を免除した (`DW-S04`)。受入全走は実施した。

- **受入全走は 17700 件中 1 件だけ赤で、land できていない。** 落ちたのは受入所要台帳の
  被覆率 gate で、実測は 15912 / 17700 = 89.898305% (閾値 0.90 を 18 node 分だけ割る)。
  本 wave は docs のみでテスト node を 1 件も足しておらず、この赤へ差分から到達しえない。
- **hold 登録では逃がさなかった。** F515 が同 gate を「台帳の陳腐化を検知する運用 gate も
  兼ねる」と明記しており、hold は真の陳腐化信号を握り潰す。また hold registry は
  flake 用の field (緑観測・緑走行回数・赤観測) を要求するが、本件は決定的赤で
  flake ではない。偽の記録を作らない判断をした。
- **一度「両立不能」と判断しかけ、実測で覆した。** 受入走行の JUnit から台帳全体を
  再生成すると被覆率は 99.994350% へ回復するが、
  `test_t1574_changed_suite_ledger_node_delta_is_exact` が固定する 12 の所要値と
  8 suite の node 集合 identity が全て壊れる。ここで「どちらの gate も緑にできる中身は無い」と
  結論しかけたが、**現 collection にあって台帳に無い 1787 node のうち 1725 node は
  凍結対象の 8 suite の外**にあり、そこだけを足せば被覆率は 99.64% へ戻り凍結部分は
  1 byte も動かないことを実測した。全体再生成は revert し、部分更新で着地させた。
  数値は {{F:pinned-suites-freeze-part-of-a-living-ledger}}。
- Codex author への指示では、閾値を下げる・gate を skip する・`xfail` を付ける・
  hold へ登録する・gate 自身を編集する、を個別に禁止し、編集可能 file を台帳 1 件へ限定した。
  子はこれを守り、両立不能を発見して報告した。

## 次の一手差分

### 更新

- [T-1380] **P1・ユーザー再裁定待ち**: 3 artifact の発行は、導出の権威が実在しないため
  現状では実行できない。核心の 1 問は「D1077 は D549 / D959 / D992 の着手順序規定を
  上書きする意図だったか」である。択一は (B 推奨) D992 の順序どおり共有批准凍結の発効を
  先に片付けて本件は保留、(A) 正式 site・trial id 規則・master seed 規則・freeze id 規則・
  18 field の canonical projection・反復数・attempt 数・retry 理由の exact 集合を
  一括裁定する、(C) schema の次世代を設計して site 別 identity と genesis の実 parse を
  schema へ持たせる、の 3 つ。A と B は排他ではない。逐語と根拠は
  `output/insights/2026-08-27_t1380-prereg-artifacts-blocked/`。
  base: 43398e1da55eb495a2bfdc52665ef7f0ecb274e8575444276637defa763d54cf

### 新規

- {{T:prereg-binding-genesis-unparsed}} **P2・新規**: 事前登録 binding の検証器が attempt 台帳の
  genesis を parse しない。hash 一致だけを見て台帳 loader へ通さないため、内容 commit の
  canonical path に任意 bytes を置きその digest を binding に書けば受理される。
  塞がないと、正しい slot 集合を持たない台帳で正式起動が受理されうる。
- {{T:effective-commit-singleton-diff}} **P2・新規**: 発効 commit が発効束縛 record **だけ**を
  導入したことを production が検査していない。親集合の exact 一致は検査するが変更 path 集合を
  見ないため、同じ commit で別 artifact や規範変更を導入しても受理される。
  設計が定める二段束縛の受理集合より実装の方が広い。
- {{T:manifest-schema-lacks-replicate-count}} **P2・新規**: manifest schema が 8b の要求する
  「cell ごとの反復数」を持たない。key 集合は trial id・arm・holdout・campaign id・世代数だけで、
  反復単位対比の判定に必要な反復数を manifest 側から復元できない。
  schema を広げない限り、正しい manifest は発行できない。
- {{T:paper-story-b3-layer-note}} **P2・新規**: 論文 §8 B-3 の「どちらの経路も事前登録 artifact
  3 件の不在に阻まれている」に、D959 の層の記述を併記する。事実としては正しいが、
  単独で読むと「3 件を作れば進む」と誤読され、実際には下流症状であることが伝わらない。
- {{T:ruling-conflict-scan-before-issuing}} **P2・新規**: 裁定を確定する前に、同じ主題の
  既裁定を主題語で全文検索して抵触を洗い出す手順を、裁定を作る側の command へ足す。
  本 wave の D1077 は D549 / D959 / D992 と着手順序で抵触するが、裁定本文にも記録にも
  言及が無く、抵触は着手した wave が 2 時間かけて発見した。手順が無いと、
  既裁定と衝突する裁定が台帳に載り、それを実行しようとした wave が空振りする。
- {{T:ledger-pin-scope-ruling}} **P2・ユーザー裁定待ち**: 受入所要台帳の一部だけが
  T-1574 の exact pin で凍結されており、その 8 suite の entry は今後も更新できない
  ({{F:pinned-suites-freeze-part-of-a-living-ledger}})。本 wave は凍結対象外の 1725 node を
  足して被覆率を回復させたが、凍結部分の陳腐化は分母が大きいうちは検出されない。
  pin の対象を所要値と node 集合から delta の向きだけへ絞るかは受理集合の変更であり裁定が要る。
- {{T:gate-direction-conflict-detector}} **P2・新規**: 同じ artifact を対象にする gate を
  新設するとき、既存 gate と要求の向き (凍結か追随か) が逆でないかを機械検査する仕組みが無い。
  本件は受入が赤になって初めて表面化した。
