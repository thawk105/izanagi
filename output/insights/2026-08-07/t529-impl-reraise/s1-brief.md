# 段 1 brief — [T-529] 実装の再起票 (A〜E 裁定済み、[T-607] 従属同梱)

wave branch: `worktree-dev-wave-t529-impl-reraise` / 基準 commit: c9990bc2 (段 1 時点で worktree clean)
起動引数: `[T-529] 実装の再起票 — A〜E 裁定済み ((284))。[T-607] を従属で同梱`

## 確定済みユーザー裁定 (worklog (284)、逐語 = rulings-inbox §36)

A = (b) historical authority を activation chain 上で ever-active な hash に限定 /
B = (a) `DW-G04` は上書きせず、正規 g2 を取得できるまで発火正例は設計メモに留める /
C = (a) shell wrapper の pre-write は certified writer 閉包の新規タスクへ送る /
D = 世代遷移は「各 env は据置または +1」/ E = 述語を共有 leaf へ抽出し authority loader の
load は CLI 解析後へ遅延する。[T-607] は T-529 に従属 (単独 wave を立てない)。
6 択一の既裁定 (D176/D196/D197/D215) は不変。

## 段 1 の前提実測 (親が本 worktree で実施。すべて read-only)

| # | 実測 | 根拠 |
|---|---|---|
| 1 | registry は **1 env あたり 1 世代**しか無い (`linux-baremetal` g1 `1b2ee853…` / `pegasus` g1 `e576e9cd…`) | `python3 -c` で `env_contract.GENERATIONS` を列挙 |
| 2 | ゆえに「registry にある hash」の集合と「現に active な hash」の集合は**今日は同一**である | 実測 1 の帰結 |
| 3 | D176 fuse は import 時に 2 世代目を無条件拒否する (`validate_generations`) | `env_contract.py:316-327` |
| 4 | `reverify_published_freeze` は production から呼ばれる経路を持つ (`s8b_oracle_report.main` の `report` sub-command、`OfficialManifest` 分岐) | `s8b_oracle_report.py:1749-1757` |
| 5 | しかしその手前の `load_ratified_freeze` が `no-active` で落ちる。`output/s8b-freeze/` に `holdout_freeze.v2.g*.json`・`approvals/`・`active/` が **1 件も無い** | `ls output/s8b-freeze/`、`s8b_ratified_freeze.py:1256` |
| 6 | v2 の approval / active pointer record は導入 commit が **非 merge かつ `AI-Agent: none` 逐語**であることを要求する = **人間 commit でしか発行できない** | `s8b_ratified_freeze.py:537-549` (`_assert_user_commit`) |
| 7 | C(a) が外へ出した 2 入口は現状のままである。floor は driver の stdout/stderr/launch marker を書いた後に Python を起動し、T-126 は `.git` を持たない source stage から driver を起動する | `tools/pegasus/floor_campaign.sh:880-896`、`tools/pegasus/t126_qualification.sh:734-740` |
| 8 | 正規 g2 は `calibration_ref` の path/sha256 の対だけを変える非同一 successor でなければならない | `env_contract.py:202-228` (`is_valid_successor`) |
| 9 | `output/insights/*` の sha256 は**意図的に pin されていない** (新規 insights の追加は golden を動かさない) | `orchestrator/tests/s1_expected_goldens.py:10-12` |

## 親の provisional 裁定 — いずれも攻撃対象

- **(P1) 本 wave に実装面 scope は無い。** D215 の保留解除条件は 2 本 (発火正例が書けること /
  入口面が Python 層に閉じること) だが、裁定 B(a) が前者を維持し、C(a) が後者を新規タスクへ
  外へ出した。よって A〜E の裁定は**設計を確定させたが保留は解除していない**。
- **(P2) A(b) は今日 observationally vacuous である。** 実測 1・2 より ever-active 集合 =
  current 集合であり、`_resolve_historical_contract_sha256` の受理集合は 1 要素も変わらない。
  実装しても「無条件 pass」と区別できない。
- **(P3) [T-607] の blocker は [T-529] の env 契約活性化ではない。** 実測 5・6 より、
  塞いでいるのは v2 freeze の approval/pointer が**人間 commit を要する**ことであり、
  env 契約の世代活性化を実装しても `no-active` は解消しない。従属裁定の前提に修正が要る。
- **(P4) 本 wave の実行可能な成果物は docs のみである。** すなわち (i) A/D/E の設計メモ凍結
  (B(a) が明示的に命じた帰結)、(ii) C(a) の新規タスク起票、(iii) (P3) を反映した [T-607] 項の訂正。

## 不変条件 (緩めない)

- 規律 2・3 は不変。D176 fuse は外さない。`generation > 1` の受理を今 wave で作らない。
- コード差分ゼロを保つ。受理集合・certified 選択結果・proof 参照・凍結 bytes を 1 つも変えない。
- 「活性化権限が実在する」と読める記述を台帳へ残さない (D176/D196/D215 が却下した失敗型)。
- 合成 g2 (temp commit / module 属性 patch) を発火証拠として記録しない (B(a))。

## 成果物影響 (`DW-G05`)

- (P4)(i)(ii)(iii) を実装しない場合: certified 選択結果・レポート・試行台帳の**値・受理集合・
  参照はいずれも変わらない**。変わるのは、正規 g2 到来時に設計を 3 度目に再導出する費用と、
  [T-607] 項が誤った依存を指し続けることだけである。**ゆえに (P4) は `DW-G05` の基準では
  nit/backlog 相当であり、これを根拠に追加の review wave を起こさない。**
- 逆に活性化権限を今 wave で部分実装した場合: 受理集合は変わらない (fuse 維持のため) が、
  台帳に「永久 fuse と区別できない保証」が残る。これは D176/D215 が明示的に却下した失敗型。

## 段 2・3 に問う唯一の論点

**裁定 A〜E と D215 のもとで、今日 発火正例を書ける実装可能な部分集合は存在するか。**
存在するなら file:line 粒度で示せ。存在しないなら (P1)〜(P3) のどこが正しく、どこが誤りかを
file:line で示せ。親の一般化が段 3 で覆るのは直近 3 wave 連続であり、(P1)〜(P4) は
すべて反証されうる前提として扱うこと。

## 分割方針

段 2 = plan 子 1 本 (read-only)。段 3 = 敵対 2 レンズ (A: 正しさ境界と裁定整合 / B: scope 被覆と
実装可能性)。実装面が生じた場合に限り段 5 の Codex 実装子を立てる (親は実装面を直接編集しない)。
実装面が生じなければ `4→7→8→9`。
