---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-paper-story-a2-cert-20260824
seq: 1
title: paper-story A-2 の P2-4 同一 workload certification driver を実装し監査した (コード + docs、branch worktree-dev-wave-paper-story-a2-cert-20260824、計測は未実施)
---

## 本文

- 本 wave は 2026-08-24 08:19 に段 1〜4 まで進んだ後、Codex 利用上限で中断していた。ユーザーが
  Codex を再ログインしたため利用上限は解消していたが、段 4 裁定 #11 の先行条件「A-1 が local main
  へ land するまで A-2 の author / qsub を起動しない」が残った。
- A-1 wave は land せず放棄されていた。生存 process 0、job dir の最終更新以降 7 時間超の無活動、
  段 6 focus は must-fix 4 件で NO-GO、worktree に未 commit 4 file、実装 commit は main の非祖先。
  待っても先行条件は充足しないため、段 4 へ巻き戻して #11 を再裁定した。改訂後は「A-1 が非活性で
  あることを投入直前に確認したうえで A-2 は独立進行」とし、実測した共有編集面は admission registry
  1 file だけだったので追記のみに限定した。A-1 の worktree・branch・未 commit 差分には触れていない。
- 裁定 inbox の再走査で D751 (TRACE=0 前処理同一性検査の 3 穴) を確認した。当該 checker の
  consumer は MoCC pilot とその test だけで本 wave の証拠経路に配線が無く、非拘束と実測した。
  A-2 の compile-out 証拠が同一性検査を経ない source-routed 証拠に留まる事実は成果物へ明記する。
- A-1 が段 6 focus で晒した must-fix 4 件 (trace0 argv の exact 束縛、qsub submission の実証拠化、
  durable 測定 root の固定、completion marker の atomic publish 内包) は同型の成果物で同じ穴が
  開くため、A-2 の実装要件として事前登録してから実装子を起動した。A-1 のコードは取り込んでいない。
- Codex 実装子・fix 子はいずれも test を 1 件も実走できなかった。sandbox が scheduler への
  socket を作れないためで、親環境では同じ照会が成功する。子は規定どおり「実装済み・未実走」と
  申告し、実走はすべて親が行った。
- 敵対レビュー 2 本 (正しさゲートと証拠鎖 / 実環境と証拠の実証性) はいずれも NO-GO で、重複を
  除いて 15 件を採用した。とくに重かったのは、公式 build に必須の toolchain manifest を渡して
  おらず全 cell が build 前に落ちること、および実 producer が run command を**文字列**で
  記録するのに consumer が list を前提としており実測が成功しても証拠を読めない不一致だった。
  どちらも親が上流実装を直接読んで裏取りした。
- 焦点再レビューはさらに 4 件を検出した。うち 1 件は成果物が未観測の legacy workload を
  observed と称する内部矛盾で、絶対規律 3 に直接掛かるため field を落とした。
- 期待 argv 文法の置き場所は設計上の分岐になったため親が裁定した ({{D:a2-expected-argv-grammar-lives-in-policy}})。
  guard 回避に見える形をしているので、焦点再レビューで名指しの攻撃対象に指定し、
  「検出力は維持されている」との判定と file:line 根拠を得たうえで採用を確定した。
- scheduler の request 消滅形式はレビューが「未確認」としたため親が login node で実測した
  ({{D:a2-scheduler-absence-form-is-observed-not-assumed}})。実装は実形式を拒否する条件を
  持っており、計算資源を消費する前に修正できた。
- 変異は 12 件を事前登録した。probe を全件 SURVIVED 期待で回して観測 node を集めたところ 2 件が
  生存し、いずれも検出漏れではなく冗長層による mask と判明した。DW-M02 に従い両層同時変異へ
  再照準して裏取りし、初回の単層 SURVIVED は erratum として残す。pin された source を変異させる
  2 件は kill 集合が 28 node に膨らむが、意図した node は両方とも含まれており、残りは
  contract-loader drift の波及である。
- **計測は実施していない。** 本 wave は監査済みの driver・job body・検査を land するところまでで、
  4-cell の実走は land 済み実装に対する別 wave が所有する。

- 段 8 の自己改善は候補 3 件を裁定し、**いずれも本文編集を見送った**。(1) contract loader が pin する
  source を編集した未 commit 状態では焦点走が大量の setup error になる (本 wave で 85 件実測)。
  (2) 新規 production file を足す wave は consumer 拡張だけでは閉じた inventory 群を取り切れず、
  全走でしか閉包が決まらない (同 5 件を 3 巡に分けて踏んだ)。(3) 小さい fix でも完了報告が
  出力検証の最小 bytes を満たす必要がある (462 bytes で不採用 1 件)。(1) と (2) を該当 leaf 節へ
  統合しようとしたところ、片方は単節予算 1000 bytes を 199 bytes 超過し、もう片方は節全体が
  exact 契約で pin されていた。自己改善契約は予算を上げる変更を独立審査対象と定めるため、
  予算内へ意味等価に収める案が無い時点で編集を止め、裁定パッケージとしてユーザーへ返す。
- 中断前の wave が記録していた候補「必須 worker の利用枠を高コストな段の前に確認する preflight」は、
  本 wave の実測で否定的な材料が出た。利用上限の表示は分単位で陳腐化し (13:22 の監査が示した
  復旧予定は 2 分後に反証された)、preflight が返す値も同じ性質を持つ。実装せず候補のまま残す。

## 次の一手差分

### 新規

- {{T:a2-certification-campaign-run}} **P1・新規**: land 済みの A-2 driver で 4-cell certification を
  実走する。投入直前に scheduler と CCBench の占有、および A-1 の非活性を再確認する。
  full-scale trace を縮小せず、資源・timeout・trace 完全性のいずれかが欠ければ当該 cell を
  indeterminate として記録する。
- {{T:a2-legacy-workload-argv-observation}} **P2・新規**: legacy correctness の workload argv が
  既存 pipeline の記録に残らないため、成果物は「独立に観測されていない」と明記している。
  観測を得るには pipeline の記録面を広げる必要があり、本 wave では proof-chain 一般改訂として
  scope 外とした。観測を足すか、明記のまま確定させるかを決める。
