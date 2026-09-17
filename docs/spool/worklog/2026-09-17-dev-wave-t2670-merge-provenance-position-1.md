---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2670-merge-provenance-position
seq: 1
title: [T-2670] 受入前 merge 段の全史 provenance 監査を merge commit の作成後へ移した — 取り込んだ main の commit と merge 自身を初めて選択集合に入れ、赤でも merge commit を保持する (コード + テスト + docs、branch dev-wave-t2670-merge-provenance-position、変異 matrix = baseline PASSED・負例 M1〜M4 4/4 KILLED 期待 node 完全一致・診断 pin M5 別枠・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼 (command 引数) は「[T-2670] (P1、裁定済み D2044 項 5 → 実装手番) `merge-history-provenance` 監査が
  `git merge --no-ff --no-commit main` と `git commit` の間にあり取り込んだ main の commit を選択集合に含めない。監査位置を
  取り込んだ変更を含める側へ動かし、中止・後始末 (merge_pending / abort) の契約も同じ変更単位で直す。説明文を実装へ合わせる
  案は採らない。着手直前の local main から fresh worktree。実装面は Codex author (D95)、変異事前登録 = 監査が取り込み分の
  違反を見逃す変異が KILLED、既存 test は正例維持。既知違反台帳の扱いは現行維持。規律 2 を緩めない。位置移動と契約修正だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2670-merge-provenance-position/README.md`。設計判断は
  {{D:merge-history-provenance-after-commit}}、失敗の型は {{F:merge-audit-before-commit-saw-nothing-new}} (F206 / F365 へ
  supersede 追記)。実装 commit `21e0bdc6b` (Codex author、2 file、+170/−68、fix 0 巡)。
- **設計の要点。** checker には HEAD 以外を pin する CLI が無く `--range` は authoritative でないため、同じ監査で被覆を
  広げる位置は `git commit` 後しかない。移設先は HEAD の pin 取得直後 (既存の HEAD 比較が監査を挟む)。赤でも merge commit を
  保持するのは、巻き戻しが捨てた commit を reflog に残し cleanup の喪失閉包 (D1233) が撤去を拒むため。保持される終端状態は
  変更前でも受入全走の後に land の監査で止まったときと同じで、本 wave は検出を受入投入前へ早めるだけ。
- **段 6 レビュー A が受理集合の変化を must-fix に挙げ、親が実 checker の probe で実測して意図した帰結として記録した。**
  (1) main にだけ違反 commit A → 旧位置 rc=0 (wave tip の 1 commit しか見ない)・新位置 rc=1 で A を名指し。(2) main が A の
  既知違反 entry を追加 → 旧位置は registry loader の index-vs-HEAD 照合で rc=2「index-only member does not match HEAD」
  (F206 再発 2026-09-01 の型、親が `--ff-only` で揃えてから再投入するしかなかった)・新位置は rc=0 (main の full 監査と同じ)。
  checker と台帳の規則は不変。code 変更は 0 で、D と F206 の supersede に明記した。
- **段 3 / 段 6 の real 所見は docs と裁定文の是正だけ**: D518 の誤引用 (→ D689 / D731 / D732)、選択集合は policy 自身を含む、
  監査赤後の manager の復旧手順 3 行、fake の順序 pin と意味的 kill の分離、M4 の追加と M5 の診断 pin 化、新規 subprocess の
  timeout、一時 message の削除は「試行」。設計 (巻き戻さない / commit-rev-parse 直後) は 4 レンズとも支持。
- **親の手順の誤り 2 件 (実害なし)。** (a) 必読資料の逐語 `D2044-item5.md` を awk で file 先頭から `### 項 5` に当てて別 D の
  項 5 を切り出した。plan 子が指摘し D2044 範囲内で切り直した (記憶「逐語射影は見出しで切り、直後に目視」の再発)。
  (b) 段 4 / 段 6 裁定 file の見出し時刻を推定で書いた。子の pid file の mtime と commit 時刻で実測して訂正した。
- 実走: 焦点走 f1 (login 自動判定 → 計算ノード、7 file) 1713 passed / 4 skipped (既存 hold) / 68.9 秒。実装 commit の full
  監査 11,076 件 新規違反なし (計算ノード)。受入全走は docs commit 後の最終 tip で land 前に 1 回。
- **変異 matrix (container worktree `.codex/worktrees/t2670-mutcontainer`、`run_tests.py` 3 file、計算ノード dispatch)。**
  probe 走 (8 request、全件 SURVIVED 登録で観測 node を収集) の後、本走 (22:38〜23:08) は baseline PASSED (88.5 秒)、負例 M1
  (監査を commit 前へ戻す、19 node) / M2 (監査削除、14) / M3 (監査赤を無視、4) / M4 (`merge_pending=False` を監査後へ遅らせる、5)
  すべて KILLED で期待 node と観測 node が完全一致 (matching 6/6)、等価 M0 (comment) SURVIVED、MISMATCH 0、TIMEOUT 0。
  M5 (stage 名だけ変更、4 node) は受理集合を変えないので診断感度 pin として別枠に記録し KILL に数えない。実 git 負例の赤理由は
  M1〜M3 が `assert ['run'] == []` (受入 command が投入された)、M4 が `stage=merge-abort rc=74 source_rc=128` (MERGE_HEAD 不在で
  abort が失敗) で、事前登録の予測と一致。順序 pin だけの赤は補助証拠として分けた。
- 段 8 (自己改善): 候補 2 件 (逐語切り出しの anchor ずれ、裁定 file の推定時刻) はいずれも既存の型なので新 F を作らず
  F511 / F1 の再発として failures fragment へ記録した。`docs/dev-wave/` 本文の変更なし (既存 memory と F で説明でき、予算も満杯)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 0、全段 `gpt-6-astra` / `medium`)。親の実測: 焦点走 1
  (計算ノード)、実 checker probe 1 (login、2 場面 × 4 監査)、変異 2 走 (probe + 本走、計算ノード)、provenance full 1 本、
  受入 1 回。

## 次の一手差分

### 完了

- [T-2670] 監査位置を `git commit` 後へ移し、中止・後始末の契約 (merge commit 保持・所有 lease 解放・受入 command 不投入) を
  同じ変更単位で定めた。実 git の負例と変異 matrix で被覆を示した。
  remaining: none
  base: eaec71a37b6ee58ef4f09a5d38d163606dd31a969e13945372c4bcf58fe8f13e
