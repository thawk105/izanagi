# 段 1 brief — [T-1239] 取り残し branch の着地判定を機械検査にする

- wave: dev-wave-t1239-branch-landing-check
- worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check
- base main: c83b5b2c (依頼文の 003c0499 から前進済み。以後 c83b5b2c を base とする)

## 確定済みユーザー裁定

2026-08-25 /rulings 全件で [T-1239] は択 (a) 採用。取り残し branch の着地判定を機械検査にする。
判定材料は 3 点 — (i) patch の指紋、(ii) branch 名のタスク ID による台帳・アーカイブ検索、
(iii) 内容の逐語照合。branch の削除はユーザー指示があるときだけ行い、本 wave は削除候補の
一覧と根拠を出すところまで。

正本は D720 (取り残し branch の回収は「未着地」だけでなく「現況で妥当」を land 条件とする)。
D720 の条件 1 (未着地) だけが本 wave の機械化対象で、条件 2 (現況で妥当) は機械化しない。

## scope (in)

- S1. `tools/check_branch_landed.py` を新設する。branch を受け取り D720 条件 1 を機械判定する。
- S2. S1 のテストを新設する。
- S3. 未マージ 20 branch へ S1 を実行し、判定表を worklog へ記録する。
- S4. 孤立 spool fragment のうち未 fold のものを fold できる形へ運ぶ。
- S5. 無占有の codex child worktree 残骸を撤去する (branch は消さない)。
- S6. 削除候補 branch の一覧と根拠を報告する (削除しない)。

## scope (out)

- branch の削除そのもの。D720 条件 2 の機械化。cleanup-branches skill 本文の改訂 (段 8 で判定)。

## 成果物影響 (DW-G05)

- S1/S2 を実装しない場合: 取り残し branch の着地判定が人手のままになり、削除の可否が
  「誤削除で commit を到達不能にする」か「取り残しを見落とす」のどちらかに倒れる。
  実測で 3 層すべてが独立に判定を反転させる例が現存する (下記)。
- S3 を欠く場合: 判定器を作っても現物へ当てておらず、削除候補の根拠が台帳に残らない。
- S4 を欠く場合: 未 fold の fragment 5 本が canonical 台帳へ入らないまま孤立し続け、
  worklog / decisions / failures の 3 台帳がその期間の記録を落とす。
- S5 を欠く場合: `.codex/worktrees/` の残骸が land 検査の child 認識に残り、
  持ち主に関係なく全 wave の land を止める型 (rc=21) の材料が積み上がる。
- S6 を欠く場合: ユーザーが削除を裁定する材料が無い。

## 不変条件

1. **判定は fail-closed。** 曖昧・照合不能は `landed` と言わず `indeterminate` を返す。
   「まだ着地していない」と「着地したか判定できない」を出力上で区別する (D719 の精神)。
2. **patch-id 単独を landed の十分条件にしない。** この機体の git は 2.34.1 で
   `git patch-id --verbatim` が無く、空白差を無視する (D731)。
3. **path と行数の一致は着地の証拠にしない** (D720)。fold 後に main から削除される
   spool fragment がこの型で誤判定される実例が現存する。
4. branch を削除しない。他 session 所有の worktree・branch を変更しない。
5. `.git/info/exclude` を触らない。共有 main の `git status` に出る
   `?? .codex/worktrees/` の 1 行は変異 harness の観測対象であり、消してはならない。
6. 実装面 (tool・テスト) は Codex `role=author` が書く。親は直接編集しない。

## 既存被覆 (性質で検索した結果) と純増検出力

対象の性質は「branch を受け取り、その内容が既に main へ入っているかを判定する」。

- `tools/audit_dangling_commits.py` — 到達不能 commit の**新規ファイル追加**だけを見る。
  branch を受け取らず、既存ファイルへの変更・削除・同名別内容・gitlink 更新は検出対象外。
- `tools/dev_wave_land.py` / `tools/dev_waves/git_state.py` — fold 済み判定 (FOLDED.md の
  `content_sha256`) と ff 連鎖検証を持つが、いずれも **land する側**の検査であり、
  「landしていない branch が既に着地済みか」を問う入口が無い。
- `git cherry` は patch-id 1 層だけで、上記の不変条件 2・3 に当たる。

純増検出力 = 「branch 単位で、patch-id・FOLDED.md hash・逐語内容の 3 層を合成し、
3 値で返す入口」。既存のどれも branch を入力に取らない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 判定を 3 値 (`landed` / `not-landed` / `indeterminate`) にする。**
  実測根拠: `worktree-workload-policy-hint-impl-unitB` の
  `orchestrator/tests/test_reflux_originless_compatibility.py` は、単一行の巨大な
  originless baseline を書き換える。この 1 行は main では別の値へ再生成済みで、
  blob 一致もせず逐語一致もしない。しかしこれは「未着地」ではなく「この層では照合できない」。
  2 値にすると誤って未着地と報告する。
- **(P2) 合成規則を file 単位の選言、branch 単位の連言にする。**
  branch が触る file ごとに (a) blob が main のいずれかの commit に存在、
  (b) spool fragment なら FOLDED.md に `content_sha256` が存在、
  (c) branch が追加した行が main tip の当該 file に逐語で存在 — のいずれかが成立すれば
  その file は landed。全 file が landed なら branch は landed。1 つでも not-landed があれば
  branch は not-landed。not-landed が無く indeterminate があれば indeterminate。
- **(P3) 材料 (ii) 台帳・アーカイブ検索は補助証拠に留め、単独で判定を決めない。**
  branch 名のタスク ID で worklog / archive / decisions を検索した hit は
  出力の `evidence` へ載せるが、`verdict` を動かさない。理由: 台帳の記述は
  「その task をやった」であって「この branch の内容が着地した」ではない。
- **(P4) S5 の撤去範囲を `.codex/worktrees/` の detached HEAD child 15 本に限る。**
  `.claude/worktrees/` 側の無署名 lock 2 本 (`dev-wave-t1484-floor-restart-registry`、
  `dev-wave-t1675-official-floor-path`) は branch を保持しており、
  かつ後者は 2026-08-25 20:16 と直近のため、撤去せず報告に回す。

## 実測 (base c83b5b2c、2026-08-25)

- worktree 総数 42。未マージ (ahead>0) branch 20 本、うち worktree 非保持が 9 本 (依頼と一致)。
- 3 層がそれぞれ実データで判定を反転させる:
  - patch-id が `-` (landed) でも未 fold fragment を持つ:
    `worktree-rulings-20260818-floor-measurement` (fragment 2 本のうち 1 本が FOLDED.md に無い)。
  - patch-id が `+` (not landed) でも FOLDED.md に hash がある:
    `worktree-t1458-side-ccbench-provenance-fix` (`5aca1641…`)。
  - patch-id が `+` でも blob / 逐語で着地済み:
    `worktree-workload-policy-hint-impl-unitB` (9 file 中 4 file が main tip と同一 blob)。
- `worktree-workload-policy-hint-impl-unitB` と `unitC` は同一 commit `500f47a6` を指す重複。
- 未 fold の孤立 fragment 5 本: cleanup-branches-20260825 の 2 本、roadmap-workload-hint の 2 本、
  rulings-20260818-floor-measurement の 1 本。
- `.codex/worktrees/` の 15 本と `.claude/worktrees/` の無署名 lock 2 本は
  `check_worktree_occupancy.py` で全て `status=unoccupied` (scanned=2297)。

## 並列分割方針

段 2 は plan 1 本。段 3 は 2 レンズ (sol / luna) の敵対相談。段 5 は実装子 1 本
(tool + テストは同じ編集面で分けられない)。段 6 はレビュー 2 本 + fix。
S3〜S6 の運用操作は親が段 6 以降に実施する。
