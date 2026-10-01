# 段 1 brief — B-4 床値 floor-pair の採用裁定 (md_3、2026-10-01)

- 研究前進: B-4 事前登録 §5 の 10 欄のうち floor 欄 (残 6 未記入の 1 つ) を閉じる土台。完了判定 = 採用裁定が D として記録され、
  採用時は §5 floor セルに集約 pin が入り、材料レポートの floor 経路が非 None を返す。B-4 の「未実走・記述統計へ限定」は不変。
- scope (依頼): D1641 決定 2 の採用裁定、採用時の §5 floor セル 1 つの記入、decisions / worklog fragment、submit-tree 撤去可否の記録。
- 確定裁定: D1641 決定 1〜3 (担当 3 者 = thawk105 名義で AI、採用裁定は測定後に AI が D として記録)、D1695 (n = 62)、
  D1974 (n と 24 h 分離は機械検査せず採用責任者の人手確認)、D2103 (floor セル読取の経路)。
- 実測済みの事実 (親):
  - 集約 artifact は実在・追跡済み・sha256 4896a1fd…dbdf 一致。6 窓とも terminal complete、62 標本、欠測 0。
    w1→w2 分離は約 231.6〜231.8 h。期待 spec 3 組は実 file と D2138 項 7 に全桁一致。floor = 0.09691 < 1。
  - **記入した木の焦点走で 36 赤** (verbatim/focus-with-entry.log、request 40678.nqsv)、記入を戻した木の基準走は
    4 file 259 passed (verbatim/baseline-without-entry.log)。原因: resolver が pin を見つけると spec を producer で再検証し、
    spec が束縛する追跡外 binary `output/env/pegasus/binaries/7cdf0dc3…` の lstat に失敗 → authoritative_floor_rejected →
    材料レポートが fail-closed。binary は checkout ごとの `place` が必要 (runbook、D2069 項 7)。
  - 赤の内訳: test_p3_b4_material_report 31、raw_record_producer 3、floor_artifact_issuer 1 (docstring「floor 登録 wave で更新する」の
    real-doc 不在 pin)、wiring_probe 1 (未 commit 差分を拾う型)。
  - submit-tree は既に存在しない (撤去済み)。
- (P1) 親の provisional 裁定・攻撃対象: **採用する (値 = 上の pin で確定) が、§5 セルへの記入は本 wave で行わない。**
  記入すると main の全 checkout で材料レポートと 36 test が binary 不在で赤/拒否になり、依頼の「docs のみ・計算 0・所有 = floor セル
  だけ」の範囲で直せない。記入は consumer 側 (test の実文書依存、または floor 消費時の binary 要求) を直す実装 wave の後、
  その wave が同じ commit で行う。
- (P2) 攻撃対象: 「採用」と「記入の保留」を分けることは D1641 決定 2 (「採用裁定 (成果物を §5 へ記入するか)」) と矛盾しない。
- 不変条件: 事前登録の他欄・凍結済み文面は変えない。規律 2 を緩めない (resolver の拒否を弱めて通す案は採らない)。
  仮想リスク向けの gate・検査・台帳を足さない。
- 成果物: decisions fragment (採否・理由・却下肢・floor_domain_error への影響・submit-tree)、worklog fragment、記録 insight。
- 分割方針: 実装面差分ゼロの軽量版。段 2・5・6 実装を省き、親裁定を read-only codex 2 レンズで攻撃させ、記録後に独立 read-only
  レビュー 1 本。実測環境: 焦点走は tools/run_tests.py の自動 dispatch (Pegasus 計算ノード)。
- DW-G05: 記入を強行すると材料レポート (Phase 3 主経路の片翼) が全 checkout で生成不能、main の受入が 36 赤。
