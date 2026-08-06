---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t244-p3-u8-critic
seq: 1
title: [T-244] critic 後置 (U-8) を実装した — 3 anchor のうち実在する Layer 3 admission だけへ後置し、新 event・版上げ・新上限はいずれも不要と実測した (コード + docs、受入 7078 passed / 20 skipped、変異 7/7 KILLED、branch worktree-dev-wave-t244-p3-u8-critic)
---

## 本文

- **裁定 U-8 の 3 anchor のうち、8c に実在するのは Layer 3 admission だけだった** (段 1 実測)。
  ledger seal は D201 が結線しないと裁定済み、proof 書き込みは前 wave が却下済みで、
  いずれも本 wave の射程外である。設計は {{D:critic-after-cell-admission}}。
- **codex 起草プランの 3 提案 (新 journal event・schema 版上げ・新 generation 上限) を段 4 で全部落とした。**
  敵対 2 レンズが独立に NO-GO を返し、同じ最安案へ収束した。親の追加実測で、
  **新定数を足さなくても多世代は既に fail-closed** (journal 順不一致を完了性検査が report publish 前に
  止める) と確認できたことが決め手である。
- **実装子が仕様の矛盾を 3 回検出して fail-closed で停止した。**
  (1) 既存の直呼びテストが用意しない材料を実 finalizer が要求する、
  (2)「既存テストの期待値を変えるな」が裁定済みの挙動変更を機械的に阻む、
  (3) 親が「全 workload 実行後にまとめて」と書いたが、段 4 の実測は「workload ごと」だった。
  **(3) は親の記述ミス**である。3 回とも指摘は妥当で、いずれも訂正して再投入した。
  (2) は「どのテストのどの行をどう追随させてよいか」を名指しで許可する形で解消した
  (検査点は 4 個から 6 個へ増え、緩和ではなく強化になっている)。
- **変異の事前登録が狭すぎて初回は MISMATCH だった。** 7 変異すべてが赤くなった (kill は成立した) が、
  「赤くなる node は各 1 件」と登録したのに実際は 2〜30 件だった。規約どおり初回結果を erratum として
  凍結し、期待 node を実測集合へ訂正して再走し 7/7 KILLED を得た。変異内容は 1 byte も変えていない。
  正例 (承認外の過剰拒否を検出する変異) は既存正常系 30 件を赤にした。
- **ログインノードでの pytest が実行基盤の attest 失敗で 2 回落ちた。** 同じコマンドを計算ノードへ
  回すと完走する。既知事象と同型のため実装差分へ帰属させていない。以後の実測はすべて計算ノードで行った。
- 段 6 のレビュー 2 本が返した must-fix 4 件と、焦点再レビューが返した新所見 1 件を fix 2 巡で全 closed。
  **最後の 1 件は「守っているつもりで守れていない」型**だった — admission decision を消す変異が、
  後始末の推測経路で復元されて生存していた。
- scope 外の real 所見 3 件を裁定パッケージとしてユーザーへ返す (下記「更新」項に記載)。
  逐語は `output/insights/2026-08-07_t244-p3-u8-critic-after-admission/`。
- **段 8 の自己改善は候補 2 件とも実装せず裁定へ回した。**
  (i)「裁定が挙動を変える wave では、追随してよい既存期待値を親が名指しする」を worker 契約へ
  足す案は、実装子権限と「既存期待値を変えない」防壁に触れるため契約上ユーザー裁定へ送る。
  (ii)「期待 node は exact 集合であり、生存のない MISMATCH は変異を変えず実測集合へ訂正して
  初回を erratum として再走する」を変異契約へ足す案は、**docs 予算に収まらなかった** —
  当該 file の残余は 76 bytes、`docs/dev-wave/**` 全体の残余は **13 bytes** で、
  意味を保った縮約では入らない。予算値の引き上げは通常の自己改善に含めない規約のため、
  編集せず候補として返す。

## 次の一手差分

### 更新

- [T-244] **P3 の 8c 結線は発火経路が無く実装不能と実測 (D201)。U-10 は批准済み (値確定、発行は 3 条件成立後)。
  U-8 は実装済み ({{D:critic-after-cell-admission}})。P2 は critic 境界の pseudonymization まで。
  P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **U-8: 2026-08-07 に実装済み** — 8c 自律 trial の critic 呼び出しを workload ごとの
  cell Layer 3 admission 確定後へ後置した。**U-8 は完了していない** — ledger seal・proof 書き込み・
  proposal と raw response の seal 後公開はいずれも未実装で、critic は依然 seal より前に metrics を
  受け取る。名乗ってよいのは「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission
  確定後へ後置した」までである。
  **本 wave が返す裁定パッケージ 3 件**: (i) U-8 の残余 (ledger seal / proof 書き込み /
  seal 後公開) をどの順で起票するか、(ii) generation 上限を上げる将来の裁定は、後置により
  多世代 journal 順が完了性検査と食い違い fail-closed になる事実を前提にし、
  critic の還流をどう成立させるかを同時に裁定する必要がある、
  (iii) `partial` trial と positive な Layer 3 材料の quarantine 境界 (本 wave 前からの既存条件)。
  **U-10: 2026-08-06 に批准済み** — 択一 8 件 (甲 1・2・3・5・6・8 / 乙 4 / 丙 7・丙-較正) と
  値を推奨どおり確定:
  `imax=4 / qmax=68 / kmax=1 / batch_member_row_count_min=2 /
  batch_distinct_candidate_count_min=1 / floor=(base 1, per_round 32, rounds 1, evidence_min 0)`、
  `F=33`。`R=1` は形式下限であり科学的十分性は主張しない。**逸脱 2 点も是**: 較正を根拠に
  使わない起草を是とし、**authority record の実発行は「V-2 evidence 正本 + producer topology +
  許可された実行経路」の 3 件成立後の人間承認 provisioning で行う** — それまで本番 authority は
  entry 0 のまま。正本 = `output/insights/2026-08-06_t244-u10-budget-values/README.md`。
  **値の批准は結線の許可ではない** — D201 の 3 阻害要因は 0/3 件しか解けず、次に起票できるのは
  結線の実装 wave ではなく設計 wave である。
  **今 fireable な分割 wave は ever-issued cell 台帳 (U-3) のみ**になった (critic 後置は本 wave で完了)。
  U-7 は確定済み (Pegasus で新規測定)。
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影済み (D192)。
  名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  U-1〜U-3 の完了は名乗らない。
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: d6494f8d580c39b8f658d3f171d2c61cf237eea56f93ec3511ee741d54a717d9
