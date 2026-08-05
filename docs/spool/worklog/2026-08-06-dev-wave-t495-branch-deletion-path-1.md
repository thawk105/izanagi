---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t495-branch-deletion-path
seq: 1
title: [T-495] ahead>0 ブランチの消去経路を特定した — 対話セッションの手動 -D で、ユーザー承認も内容検査も裁定も先行していた (docs のみ、branch worktree-dev-wave-t495-branch-deletion-path、実装差分がないため変異 matrix と受入全走は対象外)
---

## 本文

- **経路は特定できた。`codex/dev-wave-improve` (tip `77db32c`) を消したのは、対話セッションが
  `2026-08-03T14:12:08Z` (23:12 JST) に実行した `git branch -D` である。** 同一 command が
  削除前の tip SHA 記録・`Deleted branch codex/dev-wave-improve (was 77db32c).`・直後の
  `codex/*` 本数 0 を連続して残しており、因果は敵対レンズも崩せなかった。
  ユーザーの明示承認 (「どちらも『やっていい』」) はその **70 秒前** (`14:10:58Z`) にある。
- **起票時の前提「検査なしに消した」は誤りだった。** 削除セッションは 2 時間前に
  4 commit / 60 path の diffstat、main の path 不在、insight の branch 側 37 件 / main 側 38 件を
  実測したうえでユーザーへ報告している。さらに決定的なのは、**削除の 2 日前 (2026-08-01) に
  ユーザー裁定が「main を正本にする。この branch の実装 50 path は land せず廃棄する」と
  既に決めていた**ことである (一次資料 =
  `output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md`)。
  失格理由も FR-1 として記録済みで、`DispatchPolicy` が `policy_path` を含む frozen dataclass の
  ため同一 bytes の policy でも path が違えば `!=` になり、本番で submit も resume もできない。
  **これは事故ではなく裁定済みの廃棄の執行だった。**
- **候補として挙がっていた 2 経路はいずれも反証した。** `tools/dev_wave_land.py` に branch 削除経路は
  無く、正常 land の Git 呼び出しに `branch` / `update-ref` / `worktree` が現れないことは負例
  テストが固定している。`ExitWorktree{action:"remove"}` は
  `Worktree has N commits on <branch>. Removing will discard this work permanently.` で拒否する
  機械 gate を持ち、`discard_changes: true` の明示を要求する。当該 branch の worktree は
  旧 repo path 配下で既に消滅しており、そもそも対象外だった。
- **親 brief の断定 4 か所を段 3 の敵対レンズが是正した。** (a) 「唯一の経路」は言えない —
  同名 ref の再作成→再削除は同じ最終状態を作れ、branch 削除は当該 ref の reflog も消すため
  排除できない。正確には「直接観測された元 ref の削除経路」である。(b) 観測窓は
  22:58 JST でなく **22:55 JST 存在 → 08:07 JST 不在**。(c) 「コード 3 ファイル」は不正確で、
  現 main に無い path は **7 件**、内容差 16、同一 37。(d) 「拾う中身ゼロ」は言い過ぎで、
  accounting の `Group Name` 束縛だけは未移植のまま [T-222] が所有している
  (現 main の `_accounting_present` は Request ID / Started / Ended / Elapse しか検査しない)。
- **親の provisional 裁定 2 件も覆った。** (P1)「防壁が発火する余地はなかった」は誤りである。
  `77db32c` は削除の瞬間に現存 ref のどこからも到達不能になり、保護用の `rescue-t213` が
  作られたのは **32 時間 37 分後** (`2026-08-05 07:49:10 JST`) だった。到達性を見る防壁なら
  本件でも発火する。(P4)「未承認 0 件だから制度化不要」も成立しない — その母集団は
  残存 transcript に記録された実行だけで、手動 shell・別 clone・別ホスト・削除済み reflog・
  GC 後の object を覆わず、事故が古いほど証拠が消えるので欠測はランダムでもない。
  正しい裁定語は「却下」ではなく **「証拠不足で保留、rescue-first 案を保持」** である。
- **親の ExitWorktree 一般化は数値が不正確だった。** 「22 件すべてで警告が鳴った」の 22 は
  override 成功 call 数で、実際の count 警告は現 repo 5 件 (旧 repo 3 件を含めて 8 件) である。
  レンズ B が 8 件全数を追跡し、**いずれも tip が main と同一か ancestor = 偽陽性で、
  未 land 作業を救った例はゼロ**と実測した。警告疲労の懸念自体は崩れず、ある rulings session が
  初回警告の後に続く 17 worktree を最初から `discard_changes: true` で除去していた行動証拠も出た。
- **`git branch -D` を止める機械防壁は repo 内に存在しない。** ただし機序は親の当初の説明と違う。
  `hooks/guard_bash.decide('git branch -D <名>')` は `(True, '')` を返すが、それは `branch` が
  `_GIT_READ_SUBS` にあるからではなく、**防護パス語を含まないコマンドが `decide()` の fast path で
  即許可されるから**である。集合から `branch` を外しても直らない。
- **実装しないと裁定した。** 根拠は 3 つ — (1) [T-495] の起票文が「防壁の要否と形を裁定へ返す」と
  定めている、(2) `DW-G03` の独立 2 例が無い (両レンズとも 2 例目を見つけられなかった)、
  (3) 実効性のある防壁は repo / harness / 環境の 3 owner に跨り、repo 層だけを実装して
  「branch 削除を保護した」と書くのは実装したふりになる。`reference-transaction` hook が最も
  広い設置面だが `.git/config` は tracked でなく、dev-wave の helper は
  `core.hooksPath=/dev/null` を明示するため repo 内から強制できない。
- **事後検知の穴を確定させた。** [T-494] の `tools/audit_dangling_commits.py` は main に land 済み
  (`cc1c2af4`) だが、検出できるのは「新規 path が main と全 branch tip の tree に無い」場合だけで、
  既存ファイルへの編集のみ・削除・同名別内容・GC prune 後はいずれも検出できない。
  呼び出し口は `/cleanup-branches` の 1 か所だけで定期実行ではない。
- **一律の ref 削除禁止は採れない。** `tools/codex_reasoning_ab.py` が隔離 snapshot の sealing で
  正当に `update-ref -d` と prune を行うため、保護は canonical common-dir の `refs/heads/*` に
  絞る必要がある。supervised dev-wave (`tools/dev_waves/git_state.py`) は Git allowlist に
  branch 削除 API を持たず既に閉じている。
- **裁定パッケージ 3 件をユーザーへ返す。** (1) 防壁を作るか (何もしない / rescue-before-delete を
  repo 層に置く / 事後監査を blob 比較へ強める)、(2) harness 層・環境層を別 owner の課題として
  起票するか、(3) `rescue-t213` の処遇 (親の推奨は [T-222] が `Group Name` 束縛を main へ
  入れ終えるまで保留)。逐語と根拠は `output/insights/2026-08-06_t495-branch-deletion-path/`。
- 実装差分がないため、変異事前登録 (`DW-M01`) の対象は無く、変異 matrix と受入全走は対象外である。
- **段 8 の自己改善は候補 1 件で、doc 編集はしなかった。** worktree 隔離セッションで複合 Bash が
  guard に拒まれる既知候補が本 wave でも 3 回発火した (`cd` + for ループ、`$( )` command
  substitution、process substitution)。置き場である `DW-O20` は
  `docs/dev-wave/**` の合計上限 25200 に対し実測 25137 = **残り 63 bytes** しかなく、
  最短の日本語 1 文でも入らない。予算引き上げは提案せず、[T-432] へ発火実績として記録するに留める
  (件数は増やさない — 既存 4 件のうちの同一候補の再発火である)。
  もう 1 件、「起票文の前提が推測由来なら一次控えの留保ごと遡る」は `DW-S01` の
  「既存 docs は一次資料と一致するまで根拠にしない (F1)」が既に覆っており、契約の欠落ではなく
  親の適用漏れなので doc は変えない。
- 段 3 のレンズが親の起票前提そのものを覆した点は、新規 F を採らず **F1 の再発**として記録した
  (一次資料に当たらず周辺記述から転写する型。今回は「起票者の見立て」が起票文で確定事実へ変わった)。

## 次の一手差分

### 完了

- [T-495] 消去経路を特定し、防壁の要否と形を裁定パッケージとして返した。経路は対話セッションの
  手動 `git branch -D` で、ユーザー承認・内容検査・2 日前のユーザー裁定がすべて先行していた。
  起票時の前提「検査なしに消した」は誤りだった。
  remaining: none
  base: 9f851e4bbe60de9f21e5f47f40212dedc2fd690ff7caa81101d48df657a55961
