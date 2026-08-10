---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t139-producer-slice
seq: 1
title: [T-139] producer の vertical slice は通せず、承認 payload と参照束縛の純関数だけを land した — 承認済み 2 文書の矛盾と manifest の二段構成が塞いだ (コード + docs、受入 7876 passed / 20 skipped、変異 19 件 SURVIVED 0、branch worktree-dev-wave-t139-producer-slice)
---

## 本文

- **依頼された vertical slice は通していない。** 依頼は「受領証 → validator → 投入 script まで
  通し、pilot 投入可否の判定材料を返す」だった。**判定材料は返したが、slice は通していない。**
  段 3 の敵対レンズ 2 本と段 6 のレビュー 2 本 + 焦点再レビューが**すべて NO-GO** を返し、
  親は所見を全件 real と裁定した (refuted 0 件)。段 4 で scope を
  「承認 payload (docs) + 参照束縛の純関数 2 本」へ縮小した。
- **依頼文と既裁定の差を読み分けた。** 依頼の「validator」を
  受領証 schema validator と読み、適格性 validator (pairing・順序均衡・cluster 適格性の再計算) は
  裁定済みの段順序 (段 A producer → 段 B pilot → 段 C validator) に従い scope 外とした。
  **この読み分けは半分誤りだった** — 段 6 のレンズが、親が「適格性 validator の後置」と
  「correctness verifier の即時 gate」を混同していると指摘した。絶対規律 3 は verifier を
  毎 iteration 回すことを要求するので、correctness verifier は pilot と同じ単位に要る。親は撤回した。
- **承認済み 2 文書が直接矛盾する (新規発見)。** 追補 A の `a04` は
  「`a03` 不成立は preflight の観測窓を問わず性能測定の**開始後**の失敗へ写す」と定め、
  record-items は `post_performance_failure` に「marker の実在または性能 run の raw 痕跡の実在」を
  要求する。**preflight 最初の観測で落ちた attempt はどちらも持たない。**
  両文書とも一括承認済みである。受領証 schema の digest を固定するのは本 wave の責務だが、
  矛盾を残して固定すると**正当な失敗を記録できない schema が凍結される**。
  回避 2 案 (marker を先に作る / 開始前へ写す) はいずれも承認済み文書の違反であり、
  親が採れる範囲を超えるためユーザー裁定へ返す。
- **approval manifest は構造的に 2 回の land を要する。** 承認済み erratum は
  「resolver は manifest から `approval_fold_commit` と blob identity を取得する」を要求するが、
  manifest は自分自身の fold commit の SHA を literal で持てない。
  裁定記録は散文で blob digest を持たないため trust root にならない。
  そこで本 wave は承認 payload を先に fold し ({{D:t139-stage2-approval-payload}})、
  manifest は後続 wave がその子孫に置く。
- **`a13` の原子予約台帳が未実体化であることを確認した。** 実装・データとも 0 件で、
  追補 A はその実体化を producer 実装 wave の責務と明記する。
  当初 scope に入れたが、段 2 案の「固定 Git ref に置く」を敵対検証が反証したため撤回した —
  clone A と clone B が push せずにそれぞれ同じ `(family_root, ordinal)` を予約でき、
  各 local validator は重複なしと判定する。canonicality の置き場は設計択一なので裁定へ返す。
- **承認済み第 2 erratum が起草されていない。** 統計側の裁定で承認された
  「core §7 の較正義務を事前固定 stress check へ置換する erratum」の blob が存在しない。
  承認済み追補 A の `a12` 自身が「本 field は core §7 の義務を満たしたと扱ってはならない。
  本 wave はこの差を解消していない」と逐語で書いている。すなわち **core §7 の較正義務は
  現時点で誰も満たしていない状態で段階 2 が発効した。**pilot 投入可否の判定材料として返す。
- **親が一次資料から独立に検算した値は、段 2 の申告と全件一致した。**
  凍結 core (`F` 時点 450 行) の digest、erratum の 2 operation の対象行 digest 2 件、
  対象トークンの出現がちょうど 2 件であること、2 operation 適用後の合成 digest、
  承認済み 4 blob の digest、旧版追補 A の digest。手計算を trust root にしないため、
  同じ値を Codex 実装のテストで再現させた。
- **段 6 の fix 子の自己申告 4 件を焦点再レビューが覆した** (`closed` → 実際は `partial`)。
  実害があったのは Git 解決で、`GIT_DIR` 等を継承していたため
  **引数の repository_root とは別 repository の object database を読みうる**状態だった。
  既存 module が持つ環境 allowlist・top-level exact 検査・size 上限・
  shallow / replace refs / grafts の fail-closed へ揃えて閉じた。
  合成 digest の不一致例外が actual を表示していた点 (誤値で 1 度呼べば正解が得られる oracle) も
  同時に閉じた。
- **親の変異事前登録 9 件のうち 3 件が検出力の過大計上だった** (段 6 レンズが指摘)。
  要素数検査の削除は他の検査が同じ入力を拒否するため受理集合が変わらず単一理由帰属が成立しないので、
  冗長 gate として単独変異の証拠から外した。行束縛だけを壊す変異が未登録で生存する穴も塞ぎ、
  resolver 不在のため定義できない変異は**代用を作らず未登録のまま**にした。再照準後は 19 件。
- **変異は 19 件で SURVIVED 0。** 初回本走は baseline PASSED / 16 KILLED / 3 MISMATCH。
  MISMATCH 3 件はいずれも期待 node が発火したうえでもう 1 node も同じ単一理由で落ちた
  過剰決定であり、生存ではない。初回 spec と初回 ledger は変更せず、期待 node を実測へ合わせた
  erratum spec で 3 件を再走し 3/3 KILLED (期待一致) を得た。
- **受入全走は 7876 passed / 20 skipped / rc=0** (495.47 秒、計算ノード、tip は
  最新 main を取り込んだ merge commit `519d91e3`)。取り込んだ受入下限の改善により、
  直前の wave 群が記録した 1200 秒台から 500 秒台へ短縮された。
- **受入を走らせた tip と land する tip は異なる。** land 対象は本記録 commit を含み、
  差分は `docs/spool/` の fragment 3 枚と `output/insights/` の逐語だけ (docs-only、
  コードとテストの差分はゼロ)。**再走を免除した証拠** = その差分 path を読むテストは
  `test_check_docs` と `test_spool_fold` の 2 本であり、docs commit 後に
  `test_t139_preregistration_binding` と併せて再走して **481 passed / rc=0**、
  同時に `check_docs.py` rc=0 と `spool_fold.py --dry-run` rc=0 を得た。
- **記録した失敗 2 件はいずれも親と子の手順漏れである。**
  受入 lease の待ち手が JSON 出力を平文パターンで照合して取得済み lease を 2 時間見落とした件
  ({{F:lease-json-matched-as-plaintext}}) と、実装子が親の役割分担文書を自分への指示と読んで
  0 行で終わった件 ({{F:codex-child-reads-parent-protocol-as-own}})。
  後者は `rc=0` かつ出力検査も通っており、`git status` の照合だけが検出した。
- **段 8 の自己改善は予算で止まった。** 2 件の候補 (実装子へ立場を固定する 1 行と、
  親が編集 0 件を `git status` で照合する 1 行) はいずれも段 5 の worker 契約節が行き先だが、
  直前に land した読量 gate が同層を凍結しており**余白はゼロ**だった
  (追記後 10,044 bytes > 予算 9,566 bytes)。契約に従い予算値を上げず、変更を revert して裁定へ返す。
  事象と恒久対応そのものは失敗台帳側に残してある。

## 次の一手差分

### 更新

- [T-139] **P1・producer は未完成 (vertical slice 未通過)。ユーザー裁定 4 問待ち → 裁定後に「承認 manifest + producer 本体 → pilot」**:
  本 wave は承認 payload ({{D:t139-stage2-approval-payload}}) と参照束縛の純関数
  (erratum 適用・追補 A envelope parser・凍結 blob 読取) だけを land した。
  **投入 gate は実装していない** — `resolve_effective_preregistration` /
  `PreregBinding` / `submit_pilot` / `verify_receipt` は未実装で、export しないことを機械検査で固定した
  ({{D:t139-reference-binding-not-a-gate}})。**pilot は依然として投入不可。**
  裁定 4 問 =
  (Q-A) 承認済み 2 文書の矛盾 — `a04` は preflight の `a03` 不成立を `post_performance_failure` へ
  写すが、record-items は同 reason に marker か性能 run raw の実在を要求する。
  第三の分岐 (`a03` failure evidence + 対応する環境観測の実在) を認めるか。
  **受領証 schema の digest 固定はこの裁定待ち** /
  (Q-B) core §7 の較正義務が未達のまま段階 2 が発効している。承認済みの第 2 erratum を
  誰がいつ起草するか。それまで pilot を機械的に止めるか /
  (Q-C) `a13` の原子予約台帳の canonicality をどこに置くか (固定 Git ref は clone 間の
  二重予約を防げないと敵対検証が示した) /
  (Q-E) 段 8 候補 2 件を worker 契約節へ入れるか — 実装子へ立場を固定する 1 行と、
  親が編集 0 件を `git status` で照合する 1 行。同層の読量予算に余白がなく、
  予算を上げる変更は独立審査対象なので実装せず返す /
  (Q-D) 残りを 2 波に割るか 3 波に割るか。親の推奨は
  「本 wave (承認 payload) → Q-A〜Q-C の裁定後に manifest + 受領証層 + 投入・測定層を同一 land」。
  受領証層だけを先に land する分割は、実 producer 正例を持たないまま受理仕様だけを凍結するため採らない。
  本 wave が閉じられなかった既知の穴 = 合成 digest の trust root は caller supplied のまま /
  resolver 経由の fail-closed 変異は resolver 不在のため定義不能 /
  correctness verifier の即時 gate は pilot と同じ単位に要る。
  逐語 = `output/insights/2026-08-10_t139-producer-slice/`
  base: 736d7a56e7a31435e0c2fa860a9554e70f9728fc13b06fbbfb683f423370982e
