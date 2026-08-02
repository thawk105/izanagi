---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 1
title: 並行セッションの台帳衝突を spool + land lock 内 fold で機械化し、land blocker 2 件を閉じて land する — 親の裁定が 2 度広すぎて受入を赤にした (コード + docs、branch worktree-dev-wave-parallel-docs-spool、anchor commit 2743e0d、受入全走 = Pegasus gen_S 計算ノードで 5185 passed / 19 skipped)
---

## 本文

- ユーザー依頼「並行セッション開発で decision / 裁定 / failure / worklog が main merge のたびに
  衝突するのを解消したい」に対する実装。決定は {{D:parallel-doc-spool}} と
  {{D:dev-wave-budget-raise}}、失敗は {{F:guard-expectation-inversion}} と
  {{F:parent-ruling-forces-serial-only}}。
- **land blocker 2 件を閉じた (再開 wave)。** (1) worklog の ordinal namespace が 2 世代あり
  (2026-07-25 以前は日ごとに振り直す旧規約、07-26 の `(1)` から global 単調増加)、数値が衝突する
  ため fold が実 repo で必ず `status=invalid` になっていた。見出し日付による世代分離を入れ、
  **実装前 `invalid` → 実装後 `planned`** を実測した。(2) fold commit は main が wave tip の子に
  なるため supervised runner が拒否していた。receipt v2 (`fold_commit_sha` を required かつ
  nullable) と共有 verifier を入れ、`schema_v1.json` は 1 byte も変えずに閉じた。
- **欠番と日付非単調を不変条件にしなかった。** 実 corpus には過去に欠番が実在し、
  07-28 (42) の後に 07-29 (39)〜(41) がある。連続性・単調性を仮定した設計は実データで壊れる。
- **本 wave 最大の失敗は親自身の裁定だった。** 段 6 の受入が 2 度赤 (44 → 28 → 0) になったが、
  どちらも実装子の誤りではなく**親の裁定 §2.2(c) が広すぎた**ことが原因である。
  1 度目は「landed 区間は fold 所有 path に触れない」として **wave が自分の fragment を commit
  すること自体**を禁じ、2 度目は canonical 台帳への正当な書き込みを禁じた。
  最終形は「fold の**署名** (fragment の削除と `FOLDED.md` の変更) だけを禁止する」であり、
  fold は replay 防止のため必ずこの 2 つを行うので防壁は弱まっていない。
- **閉じていないものを閉じたと書かない規律を通した。** 段 3 の A-02 (fold commit の tree が
  fold 計画どおりかは検査していない) は本 wave では閉じず、
  `tools/dev_waves/git_state.py` に限界を明記し、comment・docstring・エラーメッセージ・
  テスト名のいずれにも「保証する」旨を書かないことを不変条件にした。親が機械走査で確認した。
- **親 brief が 4 点で反証された。** とくに archive ローテーションを scope 外とした判断が誤りで、
  spool 単独では実衝突が 15→12 件 (2 割減) にしか減らず、残る 18 file-instance の 94.4% が archive
  だった。直列 fold にローテーションを含めると **15→1 件**になることを段 6 レビューが独立に追認した。
  親の実測 3 件も過大表現だった (「25 本超」→ ちょうど 25/40、「毎回同じ 4 ファイル」→ 7/12、
  「86〜91%」→ 全 340 エントリの中央値は 35%)。
- **ユーザー裁定 2 件を取得した。** (1) docs 予算の引き上げ許可、(2) 段 3 が NO-GO を返した時点で
  3 択を諮り「land 統合まで実装」を選択。(2) により `tools/dev_wave_land.py` を scope へ編入した。
- **レンズ数と判定**: 段 3 = 2 レンズ (どちらも NO-GO、blocker 計 12)、段 6 = 2 レンズ
  (どちらも NO-GO、blocker 計 14)。**所見 36 件すべて real、refuted ゼロ。**
  修正巡回は `DW-O16` の上限 3 巡に対し 2 巡で閉じた。
- **先在欠陥を 1 件発見した。** 現行 active の次の一手 222 件と `docs/phase3.md` 見送り台帳 56 件が
  12 ID 重複しており (T-057/059/179–186/189/190)、D70 保存則が sink の和集合を見るため
  この 12 件の暗黙脱落を検出できない。今回の変更とは無関係で、親が独立に再現した。
- **親が自分の裁定の欠陥を 2 度作った** ({{F:parent-ruling-forces-serial-only}})。どちらも
  「fragment 側に全体状態の列挙を要求する」形の制約で、並行環境では原理的に成立しない。
- 検査: 受入全走 **4907 passed / 19 skipped / 0 failed** (Pegasus gen_S 計算ノード、3 分 43 秒)、
  `check_docs.py` 違反なし、`check_codex_agents.py` 緑、provenance 監査 724 件違反なし。
  基準線 4811 に対し **+96 件が本 wave の新規テスト**で、既存分に回帰ゼロ。
- エージェント工数: codex 子 8 本 (プラン 1 / 敵対相談 2 / 実装 3 / 敵対レビュー 2)
  + fix 子 4 本。read-only 4 本は `reasoning=max`、workspace-write 7 本は `high`、
  軽微修正 1 本は `medium`。
- **codex 子はテストを 1 度も実走できなかった** (sandbox から計算ノードへ dispatch 不可の既知制約)。
  全子が「未実走」と正直に報告し緑を主張しなかった。テスト実測はすべて親が行い、
  **その実走が子の報告になかった赤を 3 度検出した** (150 件 / 4 件 / 11 件)。

## 次の一手差分

### 新規

- {{T:spool-fold-plan-verification}} **P2・新規 (本エントリ)**: fold commit の tree が fold 計画
  どおりであることを検査していない (段 3 の A-02)。現在の検査は commit の**形**と、landed 区間に
  fold の署名が無いことまでである。閉じるには checker が `plan_fold` を再計算して blob 単位で
  照合する必要があり、checker の read-only 軽量性という設計前提と衝突する。
  **保証していないものを保証すると書かない**規律は実装・テスト名まで通してある。
- {{T:spool-fold-crash-recovery}} **P3・新規 (本エントリ)**: fold 適用後・`git add` 前の SIGKILL は
  fail-closed で止まる (false green にはならない) が、transaction state が消えているため
  自動 rollback / resume ができず手動回復が要る (段 3 の A-07)。
- {{T:spool-mutation-attribution}} **P3・新規 (本エントリ)**: 事前登録した変異のうち
  N12 (冪等性)・N24 (fold rc 無視)・N25 (pending 0 件 postcondition) は、
  **単独理由で赤くなる anchor が実装に存在しない**ため本走から除外した。
  N12 は GC 後の 2 回目が fragment 0 件の no-op に落ちる、N24 は現行 API が rc でなく例外を返す、
  N25 は staged-path closure と commit 後検査が同じ入力を先に拒否する、が理由である。
  gate は存在するが**変異で検出力を示せない**状態であり、配線か変異定義のどちらかを直す。
- {{T:spool-canonical-write-gate}} **P1・新規 (本エントリ)**: 「wave は canonical を編集しない」を
  機械強制する。land が incoming audited range に canonical 3 台帳・archive・`FOLDED.md` の変更を
  含む場合を拒否し、導入 migration だけ exact commit/path/hash で許す。現状は文章だけで、
  直接編集すれば衝突削減 15→1 が遵守依存に後退する。
- {{T:spool-rulings-collection}} **P2・新規 (本エントリ)**: `/rulings` の収集経路に、現 branch の
  valid pending fragment を加える。記録先は spool へ変えたが収集側が canonical しか読まない。
- {{T:spool-completion-semantics}} **P2・新規 (本エントリ)・裁定待ち**: `完了` の終端性が
  「残件あり」「一部完了」の 2 語の不在でしか判定されない。`初期処置だけ終了。後続作業は明日行う。`
  は受理され、残件のある T が active から消える。構造 field (`remaining: none` 等) を必須化するか、
  意味判定を諦めて `更新` を既定にするかを決める。
- {{T:spool-receipt-hardening}} **P2・新規 (本エントリ)**: `FOLDED.md` receipt が frontmatter 込み
  raw bytes の hash なので、同じ本文を別 `seq` で再投入すると replay を素通りする。
  metadata と独立した canonicalized body digest へ変える。
- {{T:spool-authoring-cli}} **P2・新規 (本エントリ)**: `base:` の 64 桁 digest を人が再現する手順が
  docs にない (item 境界と末尾 LF 正規化が実装内だけ)。`spool new` / `spool base` /
  `spool check --plan` を提供する。
- {{T:spool-mutation-wiring}} **P3・新規 (本エントリ)**: 事前登録変異の一部が production 配線を
  検査していない。N09 は helper を直接呼ぶため呼出し行の削除を検知せず、land の N23〜N25 は
  fake fold module だけで real state/GC/resume 契約を通らない。
- {{T:deferred-active-id-overlap}} **P3・新規 (本エントリ)・裁定待ち**: active 222 件と見送り台帳
  56 件が 12 ID 重複し (T-057/059/179–186/189/190)、D70 保存則がこの 12 件の暗黙脱落を隠す。
  active と見送りのどちらを正とするかは意味判断のため機械では決められない。
