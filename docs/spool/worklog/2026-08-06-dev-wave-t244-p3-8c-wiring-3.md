---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t244-p3-8c-wiring
seq: 3
title: [T-244] P3 の 8c 結線は発火経路が無いと実測し、実装せず択一 5 件を返す — batch は最低 2 行を要求するが 8c の 1 世代は 1 実行しかしない (docs のみ、branch worktree-dev-wave-t244-p3-8c-wiring、実装差分がないため変異 matrix と受入全走は対象外)
---

## 本文

- **依頼 (前エントリの「次は 8c への wiring」) は、そのままでは実装できないと実測で判定した。**
  発火条件を満たす既存 artifact path が無く、`DW-G04` の gate を満たせない。前エントリが
  origin-proofs sidecar と report v3 を却下したのと同型の判定である ({{D:s8c-wiring-not-fireable}})。
  **U-6 の裁定を親が不採用にしたのではない** — `DW-S04` に従い、裁定時点で未見だった新事実を
  付けてユーザー再裁定待ちへ戻す。
- **最も効いた新事実は「batch は最低 2 member 行を要求する」ことである。** 予算 policy の parser が
  値域自体を 2 以上に閉じているため、どの authority 値を選んでも 1 行の batch は作れない。
  一方 8c は 1 世代につき harness を 1 回しか呼ばず、承認上限は 1 世代のままである。
  台帳に記録されていたのは 2 つの下限どうしの大小関係だけで、下限 2 そのものは未記録だった。
- **`--no-build` の harness は実行せず dry-pass を返す。** seal の outcome 語彙は 3 値に閉じ、
  未実行行以外は evidence digest を必須とするが、現行 harness の戻り値にその正本が無い。
  よって結線しても書けるのは未実行行だけで、sealed query counter は 0 のままになる。
  **「oracle query を予算で束縛した」とは名乗れない。**
- **敵対 2 レンズが独立に NO-GO を返し、must-fix が 11 件出た。両者は結論の向きが逆だった。**
  片方は「実装せず設計メモへ戻せ」、もう片方は「member 行数・束縛・crash 回収を再設計せよ」と
  主張した。**親は前者を採った** — 後者の再設計を全部行っても束縛の供給経路は生まれず、
  発火 gate は依然不成立だからである。後者は発火 gate を担当していないレンズであり、
  矛盾ではなく担当外である。再設計要件 8 件は再起票時の必須要件として全件保存した。
- **提案された seam には公開の抜け道があった。** fixture caller が束縛だけを渡して ledger client を
  省略すると、既定解決で本番 ledger に落ちる。module 再束縛も private sentinel も要らない。
  さらに束縛が campaign / launch admission と結ばれておらず、正規 scope 内に未束縛の第二権限を
  持ち込める。本番 authority が空なのは一時的な覆いにすぎない。
- **親の暫定裁定 6 件のうち 4 件を撤回し 1 件を部分撤回した。** 撤回したのは (a) 1 候補 1 行という
  batch 形 (受理集合の外) (b) harness 実行を oracle query と一般化した点 (c) 「例外なら予約放棄」
  (候補確定後は放棄が受理されない) (d) 発火経路の主張。部分撤回は seam の形である。
  **軽量版にしなかった判断だけは維持した** — 軽量版なら段 2・3 を省き、4 件のいずれも land 前に
  見つからなかった。
- **親の前提実測に 2 件の誤りがあり、レンズの指摘で訂正した。** 早期 break は 5 経路でなく 6 経路
  (critic 不正も break する)。生死実験の receipt は 8c caller の生死ではなく、手書き probe が
  event を直接 commit したものである。後者は親が根拠として過大に使っていた。
- **既存の失敗型の再発を 1 件記録した。** 検査の有無は確かめたが閉じた値域の列挙を確かめない、
  という前提実測の型である。前回は実装子が、今回は敵対レンズが land 前に差し戻した。
- **裁定パッケージ 5 件を返す。** いずれも本 wave の裁定の外側にあり実装していない。
- **段 8 の自己改善は候補 2 件。1 件は実施し、1 件は見送った。** 実施したのは上記の再発追記である。
  見送ったのは「発火経路を段 1 で書くとき、その経路を起動する caller が repo 内に実在するかを
  確認する」手順を reference へ足す候補で、理由は 2 つ。**同型欠陥が独立 2 例に達していない** —
  前エントリは段 1 の時点で書けないと判明して scope を縮めており、書いたうえで敵対レビューに
  撤回されたのは今回が 1 例目である。加えて dev-wave reference の残予算は **13 bytes**
  (25,187 / 25,200) で、意味を保った追記が入らない。**予算を上げる変更は自己改善に含めない。**
  段構成・実装子権限・正しさ防壁・裁定境界・予算のいずれも変更していない。
- 全履歴の provenance 監査は **1530 件・違反なし**。
- 逐語と裁定は `output/insights/2026-08-06_t244-p3-8c-wiring/`。

## 次の一手差分

### 更新

- [T-244] **P3 の 8c 結線は発火経路が無く実装不能と実測。U-4 の記録形分離まで実装済みで、
  本番 provisioning は U-10 未決。P2 は critic 境界の pseudonymization まで。P4 は ledger 側適合、
  P5 残余は U-2、未着手は P7・P9**:
  **P3**: **8c への結線は実装していない** ({{D:s8c-wiring-not-fireable}})。理由は 3 つで、
  (i) 束縛を供給する経路が無い (本番 authority は空、CLI に引数無し、headless は caller 注入を拒否、
  非本番 store seam は private のみ) (ii) 予算 policy の parser が batch の member 行数の下限を
  値域ごと 2 以上に閉じており、1 世代 = 1 実行の 8c と噛み合わない (iii) `--no-build` の harness は
  dry-pass を返し、seal の 3 値 outcome のうち未実行行以外に必要な evidence の正本が無い。
  **前エントリまでの P3 実装状況は不変**である — count 3 種の分離と
  `BudgetPolicy.batch_distinct_candidate_count_min` (既定 1) による per-batch 検査まで (D198)。
  **裁定パッケージ 5 件を返す** — (V-1) 結線の発火経路をどう作るか (推奨: U-10 裁定まで設計メモ)
  (V-2) seal の result evidence の正本を誰がいつ決めるか (推奨: U-10 と同じ authority 発行の面)
  (V-3) 1 世代 1 実行と最低 2 行の不整合をどう解くか (推奨: 同一 wire を R 回測る実行形。
  ただし実行時間が R 倍) (V-4) 束縛の発行主体 (推奨: launch admission が発行する capability)
  (V-5) 予約・候補確定後の crash 回収と receipt 喪失の照合。
  **これが決まるまで 8c 結線を再起票しない。** 前エントリの順序どおり sidecar / report v3 /
  completeness も起票しない。**今 fireable な分割 wave は critic 後置 (U-8) と
  ever-issued cell 台帳 (U-3) の 2 本**で、D96 の同一変更単位として別々に起票する。1 wave にまとめない。
  U-7 は確定済み (cygnus 再測定はせず Pegasus で新規測定)。
  **U-10 (予算値 Imax/Qmax/Kmax/Bmin/floor tuple) は依然 authority 発行の裁定待ちで、
  これが決まるまで本番 authority へ entry を 1 件も書かない。**
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影済み (D192)。
  名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  U-1〜U-3 の完了は名乗らない。前 wave の裁定パッケージ 5 件は依然ユーザー判断待ちである。
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: 10fd8324b57c19f5e6df1bb2a06e753a02a5089a8ab9570815f3cbf9f49de599
