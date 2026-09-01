# [T-434] 段 4 裁定 — D1407 の二段束縛を実装できるか

基準 main `28ebff456b9f57a927854950b5030fa77aec6529` (wave 中に 0 commit しか進んでいない)。
段 2 プラン + 段 3 レンズ A / B。親はすべての所見を現物で照合した。
裁定 inbox 再走査: D1407 以降 (D1408〜D1420) に上限引き上げ・受領証・発効 commit を扱う新裁定は無い。

## 裁定 0 — 本 wave は実装しない (`4→7→8→9`)

**cap-lift 固有の topology 検査部品を単体で land しない。** 理由は独立に 4 本あり、いずれも
1 本で成立する。

1. **D1407 §1・§3 に正面から反する。** §1 は「内容 commit `G` が実装一式 (P6 の本体・
   calibration・admission 結線・受領証機構・新 manifest・全 consumer 結線) を導入する」と定め、
   §3 は「`G` と `A` は分割して main へ入れず、同一の land transaction で取り込む」と定める。
   cap-lift 固有の部品を先に land すると、後の `G` は「実装一式を導入する commit」ではなくなる。
   これはレンズ A が段 2 の論証を精密化した点である — 段 2 は却下選択肢への該当を主な根拠にしたが、
   より直接に反するのは §1・§3 の方である。
2. **D1407 の却下選択肢と同じ欠陥型である。** 「到達不能と承知で受領証の入口だけを land する —
   実正例を持たない枝を増やす」が逐語で存在する。提案部品は受領証を parse しないので
   字義上の「受領証の入口」ではないが、**呼び手が無く一度も評価されない**点で同型である。
3. **DW-G04 を満たせない。** 発火条件を満たす既存 artifact path も計測 ID も 1 件も書けない。
   レンズ B が識別子検索でなく性質で全件確認した — cap-lift 固有の認定記録 path も受領証 path も
   無く、`output/s8c-trial-registry/` 自体が存在せず、`CAP_LIFT_RECEIPT_*` は未使用の reason
   語彙だけで、`run_origin_trial` には repo 内の呼び手が無い。
4. **D841 (ユーザー裁定) の positive control 要求を満たさない。** 受領証と consumer 結線を
   伴わない部品を T-434 の実装成果として数えることはできない。D1407 は「D841 は不変」と明記する。

**実装面の差分はゼロ。** したがって変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 裁定 1 — 段 2 の「編集 file なし」は維持するが、その論拠は差し替える

レンズ A は「全面 NO-GO は強すぎる」として、`s8b_ratified_freeze` の Git query を
allowlist・exact-root・graft/replace/shallow 拒否の単一 primitive へ寄せる hardening を
代替単位として提示した。今日 `load_ratified_freeze` の production 経路から発火し、
受領証の入口ではなく、受理集合は同じか狭くなるだけである、というのがその論拠である。

**real と認めるが、本 wave では不採用 (scope 外) とする。**

- これは二段束縛の本題ではなく、**まだ誰も踏んでいない経路に対する防御的堅牢化**である。
  引数は「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と定める。
- 触る対象が s8b の governance module であり、受理集合を「狭くする」向きの変更を
  T-434 の名前で行うと、承認外の過剰拒否を T-434 の成果として台帳へ残すことになる。
- したがって**別タスクとして起票**し、そちらで DW-G05 の成果物影響と正例・負例を独立に立てる。

## 裁定 2 — real と認めた所見 (実装時に必ず効く)

| # | 所見 | 出所 | 判定 |
|---|---|---|---|
| R1 | 追加 path 集合を `{認定記録, 受領証}` と集合比較すると、2 引数が同一のとき 1 path へ縮退して通る | レンズ B M2 | **real**。distinctness を別に要求する必要がある |
| R2 | `_added_paths` は status `A` しか見ないため、追加された 2 件が symlink や gitlink でも通る。literal regular blob の確認が無い | レンズ B M2 | **real**。`s8c_acceptance_receipt.py:658-683` に tree type 検査の先例がある |
| R3 | 末尾空白付き `AI-Agent: none ` の負例は `test_trial_registry.py` の通常 helper では作れない。`--cleanup=verbatim` が要る | レンズ B M4 | **real**。`test_s8b_ratified_freeze.py` の `_commit_verbatim` が先例 |
| R4 | `trial_registry` 系と `s8b` 系の git 呼出しは同じ repository・graph を見ていない (環境 allowlist と config 無効化の有無が違う)。素朴に合成すると別 graph を混ぜうる | レンズ A must-fix 1 | **real**。実装時は git 呼出しを 1 本へ寄せてから合成する |
| R5 | commit の形だけでは発効を証明できない。`A` の発見、`A` が pinned HEAD の祖先であること、`A` の 2 blob と HEAD blob の一致が要る。exact `G` の直子だが main から到達しない dangling `A` が通る | レンズ A must-fix 3 | **real**。`trial_registry.py:1499` に先例がある |
| R6 | `AI-Agent: none` は人間性の機械的証明ではなく自己申告である | レンズ A must-fix 5 | **real**。親 brief の「AI は作れない」は機械的には偽 |
| R7 | 独立述語は 4 つでなく 3 群 (exact-parent / exact-additions / trailer)。exact parent set `{G}` は非 merge を論理的に含む | レンズ A nit 2 | **real**。親 brief の数え方が過大 |

## 裁定 3 — refuted / 訂正した所見

- **refuted: 段 2 の file:line 引用。** `MAX_APPROVED_GENERATIONS` は 144 行 (段 2 の 139 行は
  `ROOT` の宣言)、予算比較は 506 行、manifest の exact 2 述語は 771 行で診断文字列は 772 行
  (段 2 の 743 行は `_parse_trials` の宣言)。親の実測が現物と一致する。両レンズが独立に追認した。
- **refuted: 段 2 の負例表の「rename 検出時: `R`」。** 既存 `_added_paths` は `-M` を渡さないため
  `R` は出ない。親が repo 外の使い捨て repo で、レンズ B が repo 内の実 rename commit で
  独立に実測し、どちらも `A` + `D` になった。`diff.renames=true` を `-c` でも repo config でも
  与えても変わらない。**この負例は削除負例と同じ理由に退化する冗長 gate である。**
  同様に mode 変更のみの負例も内容変更と同じ `M` で、独立 gate ではない。
  `--no-renames` を足す必要も無い (plumbing は config で rename 検出に切り替わらない)。
- **訂正 (親 brief):** 「`reflux_formal_consumer` は `P6Unavailable` で無条件停止」は不正確。
  前段の条件が失敗すれば `FormalContractRejected` になり、**全前段を通過したときだけ**
  `P6Unavailable` になる。design-v3 の表現を引き写した親の誤りである。
- **訂正 (親 brief):** 「`A` は人間の commit であり AI は作れない」は機械的には偽 (R6)。
  正確には「AI が書いてはならない (provenance 規律)。機械的に防いではいない」。
  結論は変わらない — 本 wave が `A` を作ることはできない。

## 裁定 4 — 本 wave が新たに確定した事実 (次の実装 wave への引き継ぎ)

1. **topology の実装差分は当初の見積りよりはるかに小さい。** D1407 が `A` に要求する述語は
   既存の 2 module にすべて相当物がある。
   - 非 merge と親集合 exact `{G}`: `trial_registry.py:1243` `assert_effective_commit_exact_parent`
     (root・merge・別親・非 canonical 引数・query 失敗・graft・replace ref を拒否)
   - 追加 path が exact で他 status ゼロ: `s8b_ratified_freeze.py:607` `_added_paths` +
     `:1273` `_verify_pairing`
   - `AI-Agent: none` 逐語 1 本: 同 `:546` `_is_none_commit` (raw 行 byte 一致 + parse 値 exact の二重)
   - `G != A`: 同 `:1284`
2. **exact-parent 側の負例は既に実 git で網羅済み。** `test_trial_registry.py` の
   同関数を呼ぶ 9 箇所が root・別親・merge・非 canonical 引数・parent query 失敗・graft file・
   replace ref・measurement HEAD 祖先要求を覆う。**実装時に親集合側の負例を足す必要は無い。**
   新規に要るのは exact-additions と trailer を cap-lift の主体へ当てる分、および R1・R2・R5 の分だけ。
3. **正例は stub 無しで書ける。** `test_s8b_ratified_freeze.py:92,100,107,286` に
   `_commit` / `_commit_raw` / `_commit_verbatim` / `_commit_exact` があり、
   実 repo に実 commit を作って exact path 集合まで検査する作法が確立している。
4. **blocker の持ち主は [T-941] P6 実装 wave である。** `docs/phase3.md:1118` が
   「機械実装は [T-941] P6 実装 wave の所有」と明記し、T-941 は起票以来未実施
   (`docs/archive/worklog-phase3-0812-489.md:649`)。T-434 は T-941 に順序依存する。

## 裁定 5 — ユーザーへ返す裁定パッケージ

親は代行しない。次の 3 件を返す。

- **U1 (順序の解除): [T-941] P6 実装 wave を起動するか。** T-434 の実装は T-941 に順序依存する。
  あわせて T-942 の V-11「**P6 の実装と認定をどの wave が所有するか**」が
  `docs/archive/worklog-phase3-0812-489.md:654` でユーザー裁定待ちのまま残っている。
  D156 と phase3.md は既に T-941 の所有と書いているので、V-11 は済んでいる可能性が高い。
  **済なら V-11 を閉じ、未済なら所有を確定してほしい。**
- **U2 (D1407 の逐語の曖昧さ): `G` は単一の導入 commit か、累積 tree の tip か。**
  D1407 §1 は「内容 commit `G` が実装一式を**導入する**」と単数で書く。実装一式は 1 回の
  差分に収まらない規模なので、開発中の作業 commit を認定前に 1 本へ squash するのか、
  「`G` は累積 tip でよく、全 ancestor と `A` を同一 transaction で land する」と読むのかで
  手順が変わる。段 2 と両レンズが独立にこの曖昧さを指摘した。**現裁定からは前者しか導けない。**
- **U3 (scope 外の real 所見): s8b の Git trust boundary 共通化を別タスクとして起票するか。**
  レンズ A が指摘した実在の差分 (R4) で、今日の production 経路から発火する。
  本 wave では「仮想リスク向けの堅牢化は scope 外」として不採用にした。

## 変異事前登録 (DW-M01)

**実装面の差分がゼロのため変異 matrix は免除される (DW-S04)。** 受入全走は免除しない。

次の実装 wave のための負例候補は、段 2 の表から冗長 gate 2 件 (rename、mode-only) を除き、
R1 (2 path の同一性)・R2 (symlink / gitlink)・R5 (dangling `A`) を加えたものとする。
今回は登録せず、実行可能とも記録しない。
