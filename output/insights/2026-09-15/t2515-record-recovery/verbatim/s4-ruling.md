# 段 4 裁定・plan v2 — [T-2515] 未着地の研究記録の回収

段 2 plan rc=0 / 採用検査 rc=0。段 3 敵対 2 本 (sol=A 正しさ境界と台帳整合 / luna=B 回収の完全性と実効性)
とも rc=0 / 採用検査 rc=0。段 4 直前に main を再確認 — wave 起点 `0600887d9` から **0 commit**、
`docs/decisions.md` に更新なし。したがって wave 開始後に着地した新しい裁定は無い。

## 採用 (real)

1. **新規 F は 0 件。** 親 brief の (P1) は誤り。親が現物で裏を取った。
   - `F500` = 同一 script `certify_calibration.sh` が裸 `python3` を呼び 3.10 構文で落ちる型。
     既に 2026-09-10 の再発追記があるが、それは pristine source verifier の呼出しであり、
     本件の**条件関門**は同族の別呼出し・別観測。→ **F500 へ再発追記**。
   - `F766` = 根本原因 (1)「台帳を主題ではなくファイル名で引いて正しい族を見落とす」。
     → **F766 へ再発追記。根本原因 (2) の hold 登録循環は再現していないので書かない。**
   - 待ち手偽成功 → **F355 へ再発追記** (親の判断どおり。F817 は 2026-09-03 に F355 へ supersede 済み)。
   - `F934` → **限定 supersede 追記**。「認定経路で一度も実走していない」だけを訂正する。
     **拒否原因が解消したとは書かない。** 2026-09-14 の別 driver 再発はそのまま残る。
2. **期間の断定を証拠の範囲へ絞る (A2)。** 「認証経路が 3 週間死んでいた」とは書かない。
   書くのは (a) 最後に成功した認証が `892707.nqsv` (2026-08-06) であること、
   (b) 3.10 専用式が `3c9932591` (2026-08-20) で入ったこと、
   (c) 条件関門が全 driver へ義務化されたのが `0218acc61` (2026-09-01) であること、
   (d) 発見が 2026-09-10 であること、の 4 時点と、**その間に当該関門の実走記録が
   確認した認定 attempt に無かった**という限定した事実。
   「8-06 以降ずっと故障」「3 週間の連続実走不能」は**書かない**。
3. **旧変異 4 本を回収対象へ足す (B1)。親の監査の誤りを訂正する。**
   `mutation-spec-probe.json` / `mutation-report-probe.json` / `mutation-spec-final.json` /
   `mutation-report-final.json` は `repo_head=18704ae18` に束縛された当時の実測で、main の
   `35a740cd4` 束縛の再走版とは別命題である。**4 本とも blob が main に 0 件**であることを
   親が全数検索で確認した。`original-mutation/` として置く。
4. **旧 worklog fragment 固有の観測を追記節へ残す (B2)。** 後続裁定で覆った判断と新規 T は転載せず、
   観測と判断訂正だけを残す。対象は queue 待ち中の `timeout 900` 打ち切りと orphan hold 2 箇所、
   子への `--reasoning` 指定の rc=2、レビュー B の `### 総括` による採用拒否、
   子 worktree への git 拒否に対する全比較→複写→再比較、受入赤を「完全に非帰属」とした判断の訂正、
   既存 accepted 2 件の binary hash 不一致と source head 世代差の観測。
5. **焦点走の consumer を追加する (B3)。** plan の docs checker 経路に加えて、
   repo 全体走査の consumer を焦点走に含める — `test_s8b_repo_scan_invariant.py`、
   `test_s8c_preregistration_invariant.py`、`test_login_headroom.py`。
   **子は「違反は見つからない」と書いたが実走していない。親が実走して確かめる。**
6. **配置 (B)。** 当時の資料は既着地 topic `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` の
   下へ (`original-verbatim/` と `original-mutation/`)、本 wave 自身の記録は
   `output/insights/2026-09-15/t2515-record-recovery/` へ。D1941 と衝突しない。
7. **`## 次の一手差分` は本文も操作も空にする (B)。** 「操作なし」等の説明文を書くと
   `_parse_worklog_delta` が未解釈 content として拒否する。
8. **「accepted は現在も一切ない」と一般化しない (B)。** 2026-09-13 に rr95 の accepted 較正が
   取得されている (`calibration-5c836a22eff9ab40.json`)。当時 (2026-09-10) の 2 job が
   `admitted=false` で拒否されたこと**だけ**を書く。

## 不採用 (refuted)

- 「回収が拒否を成功へ読み替える」(A3) — plan は accepted 未取得を明記しており、
  `988706` / `988708` はいずれも `admitted=false` / shell `rc=2`。読み替えは無い。
- 「現行 main とのコード差分が未着地実装の証拠」(A4) / 「6 commit に未着地のコード変更が残る」(B5) —
  反例なし。専用関門の撤去は `b3c62ee7f` の後続変更、抽出境界の変化はその整合。
- 「既着地 directory への追加そのものが凍結違反」(B4) — 対象 topic を固定する manifest も
  exact member 集合も見つからなかった。D1941 も日付配下 topic への追加を禁じていない。

## scope 外の real 所見 (裁定パッケージ候補・実装しない)

- **F817 の帰属不整合 (A)。** 2026-09-03 に「以後この型は F355 へ追記する」と supersede されたのに、
  2026-09-08 の再発が F817 側へ書かれている。台帳の整理は本 wave の scope 外。
  今回の 2026-09-10 分を F355 へ置く判断は変わらない。
- **旧 worklog の工数の内訳不一致 (B)。** 「codex 子 9 本」と内訳合計 11 本が合わない。
  確定値として再掲せず、原文の不一致として扱う。

## 不変条件 (禁止署名と通る正例)

- **禁止:** 既着地 bytes を 1 byte でも変えること。対象は `job-evidence/` 7 file、
  `mutation-final*.json` / `mutation-probe*.json` 6 file、`recovery-verbatim/` 11 file、
  既存 `README.md` の 1〜86 行。
  **通る正例:** 既存 `README.md` の変更前 bytes が変更後の完全な prefix であること。
- **禁止:** 旧 decisions seq=1 / seq=4 の設計を現行の実装指示として再登録すること
  (D1936 項 6 / 項 43)。旧 worklog の新規 T 2 件を復活させること (D1936 項 46 / 項 47)。
  **通る正例:** 逐語 file の中にそれらが**歴史資料として**残り、追記節が
  「当時の判断であり後続裁定で覆った」と名指しで書いてあること。
- **禁止:** 関門・検査を弱める方向の記述、拒否を緑と読み替える記述 (絶対規律 2)。
  **通る正例:** 追記節が `admitted=false` と accepted 0 件を明記していること。
- **禁止:** 新しい gate・検査・台帳・一般化・コード変更・再測定・branch 削除 (依頼の明示 scope 外)。

## 変異事前登録

`DW-S04` により、**実装面 (D95 決定 2) の差分がゼロの wave は変異 matrix を免除する。**
本 wave の変更面は `output/insights/**` と `docs/spool/**` だけで、コード・テスト・
実行可能 script・機械設定を 1 つも変えない。したがって変異 matrix は**免除**。
**受入全走は免除しない。**

## 段 5・6 の扱い

実装面ゼロのため Codex 実装子は起こさない (D95 の実装面が無い)。docs-only 本文は親が書く。
段 3 の 2 レンズが plan を 2 件の real で訂正し、親がその現物を確認して採用したため、
段 6 の追加 review 子は起こさない (`DW-G05`: 示せない must-fix は起動しない)。
