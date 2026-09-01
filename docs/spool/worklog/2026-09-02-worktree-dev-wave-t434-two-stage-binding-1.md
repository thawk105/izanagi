---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: worktree-dev-wave-t434-two-stage-binding
seq: 1
title: [T-434] 二段束縛の実装差分は 3 群まで小さいと確定したが、順序が塞がっていて land できない (docs のみ、branch worktree-dev-wave-t434-two-stage-binding、実装面 0・変異 matrix 免除)
---

## 本文

- D1407 に従って発効の二段束縛を実装しようとした wave。**実装しないと裁定した** ({{D:cap-lift-topology-not-landed-alone}})。
  先行 wave と同じ結論だが、根拠と得られた事実が違う。先行 wave は「実装不可」を 3 本の理由で
  述べたが、本 wave は**実装差分そのものは小さいと実測で確定**したうえで、**塞いでいるのは
  順序であり、その持ち主が別タスクである**ことを特定した。
- **段 2 が挙げた「却下選択肢への該当」より、D1407 決定 (1)・(3) への抵触の方が直接的である。**
  部品を先に land すると、後続の内容 commit が「実装一式を導入する commit」でなくなる。
  段 3 のレンズが段 2 の論証を精密化した。
- **実装差分は 3 群まで縮んだ。** 発効 commit へ要求する述語は、親集合 exact 一致・追加 path が
  exact で他 status ゼロ・`AI-Agent: none` の逐語ちょうど 1 本・内容 commit との非同一性の
  いずれも既存 2 module に相当物がある。親集合側の負例は実 git で既に網羅済みで足す必要が無い。
  正例も既存の作法で依存先を stub せずに書ける。独立述語は 4 つでなく 3 群 (親集合 exact は
  非 merge を含む)。
- **塞いでいる順序の持ち主を特定した。** `docs/phase3.md` が意味的充足契約の機械実装を
  P6 実装 wave の所有と明記しており、その wave は起票以来未実施である。本件はそこに順序依存する。
  あわせて 8c 結線の裁定パッケージに残る「P6 の実装と認定をどの wave が所有するか」が
  ユーザー裁定待ちのまま残っている。決定と phase doc は既に所有を書いているので、
  済んでいる可能性が高い停止項である。
- **素朴な実装が踏む欠陥を 5 件、実装前に確定した。** 追加 path の集合比較が 2 引数同一で
  1 path へ縮退する / 追加 status しか見ないため symlink と gitlink が通る / 末尾空白付き
  trailer の負例は既定 cleanup に落とされるため verbatim 指定が要る / 2 系統の git 呼出しが
  同じ repository と graph を見ていない / commit の形だけでは発効を証明できず発効 commit の
  到達性と blob 一致が要る。
- **冗長 gate を 2 件、実測で除外した。** 追加 path 判定は `diff-tree` に rename 検出を
  渡さないため、rename は追加と削除に分解され削除の負例と同じ理由で落ちる。config でも
  切り替わらないことを親が repo 外の使い捨て repo で、レンズが repo 内の実 commit で
  独立に実測した。mode 変更のみも内容変更と同じ理由である。
- **自分の言明を 2 件訂正した。** (i) `AI-Agent: none` は人間性の機械的証明ではなく自己申告で、
  判定器は message の raw 行と trailer parse しか見ない。正しくは「AI が書いてはならない
  (provenance 規律)。機械的に防いではいない」。結論は変わらない。
  (ii) 意味的充足契約の consumer は「無条件停止」ではなく、前段が失敗すれば別の拒否になり、
  全前段を通過したときだけ未充足で止まる。親が先行設計の表現を引き写した誤りだった。
- **段 2 の file:line 引用は一様に信頼できなかった。** 承認上限定数・予算比較・manifest の
  exact 述語の 3 件が現物とずれており、親の実測が正しいことを段 3 の両レンズが独立に追認した。
  一方で同じ子の他の引用は一致していた。子の引用は個別に検算してから採用する。
- codex 子 3 本 (plan 1 本 read-only、consult 2 本 read-only、いずれも reasoning=xhigh)。
  3 本とも rc=0、`check_codex_output.py` rc=0。逐語は
  `output/insights/2026-09-02_t434-two-stage-binding-adjudication/verbatim/` に置いた。
- 実装面の差分はゼロ。機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変。
  変異 matrix は免除、受入全走は免除せず本エントリの記録 commit の tip を land gate として投入する。

## 次の一手差分

### 更新

- [T-434] **P1・発効 topology 確定済み (D1407)・実装は順序待ち**:
  2026-09-02 の wave で「部品だけを先に land しない」と裁定した ({{D:cap-lift-topology-not-landed-alone}})。
  **実装差分そのものは 3 群 (親集合 exact / 追加 path が exact で他 status ゼロ /
  `AI-Agent: none` 逐語 1 本) まで縮み、いずれも既存機構に相当物がある。**
  親集合側の負例は実 git で既に網羅済みで足す必要が無く、正例も依存先を stub せずに書ける。
  **残る blocker は意味的充足契約の本体実装で、その所有は [T-941] にある。** T-434 は
  [T-941] に順序依存する。実装時に踏む欠陥 5 件と、除外してよい冗長 gate 2 件は
  `output/insights/2026-09-02_t434-two-stage-binding-adjudication/README.md` が正本。
  ユーザー裁定へ返した 3 件 — [T-941] を起動するか、D1407 の内容 commit が単一の導入 commit か
  累積 tip か、共有 git 信頼境界の統一を別タスクとして起票するか — も同 README の裁定パッケージ節。
  base: 2242efe2c465e42f9c757edad1412f3282dc813ea2fe66581bb508823bd6b020
- [T-941] **P2・T-434 の順序上の前提であることが判明**:
  2026-09-02 の T-434 wave が、本 task の未実施が T-434 の実装を塞いでいる唯一の順序依存で
  あることを確定した。`docs/phase3.md` は意味的充足契約の機械実装を本 task の所有と明記している。
  あわせて 8c 結線の裁定パッケージに残る「P6 の実装と認定をどの wave が所有するか」が
  ユーザー裁定待ちのままだが、決定と phase doc は既に本 task の所有と書いており、
  済んでいる可能性が高い。着手前にその停止項を閉じる。
  base: c8679d641751fecc8477cf516a623f257b8932c255ddc9cf9a26df11ee3f57b4

### 新規

- {{T:s8b-git-trust-boundary}} **P3・新規**: 凍結解決系と試行台帳系の git 呼出しが同じ
  repository と graph を見ていない。前者は環境 allowlist と global/system config 無効化を
  持たず、replace 無効化だけを指定する。今日の production 経路から発火する実在の差分で、
  受理集合は同じか狭くなる。T-434 の段 3 レンズ A が指摘したが、本題の実装ではない
  防御的堅牢化のため T-434 の scope 外とした。起票の可否はユーザー裁定へ返している。
