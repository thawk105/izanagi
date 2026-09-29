# 段 1 brief — output/ の低価値 file を HEAD から外す (dev-wave-output-pruning)

基準: local main 035fc11fa601547f5d68e54f5661c5daa70b93a5 (2026-09-29 14:37 JST)。依頼: /work/1/SFC/tanab/tmp/git-load-2026-09-29/md_1.txt

## 研究前進
土台 wave。止めている研究の実測: 2026-09-29 14:37 JST に並行 session の `git worktree add` 約 20 本が同時に走り各 13〜30 分 (load 47〜54)、
14:2x には git 54 本中 42 本が D 状態。wave 起動と掃除の git status が Lustre の metadata 待ちで詰まる。
最小差分: 追跡 file 35,128 (うち output/ 31,651・943 MB、output/insights/ 27,176) のうち参照されない機械出力を `git rm` で外す。
完了判定: 追跡 file 数の減少と、同時刻対照つきの `git worktree add` / `git status` 所要の前後比較を実測値で示す。

## scope
- 対象は output/insights/** だけ。output/env・campaigns・registry・reports・task-runs・s1-*・s6-*・s8*・t189-*・t080-* ほか insights 外は全部 D (残す)。
- 第 1 段で外すのは A (参照ゼロの機械出力・重複) と確信度の高い B (README 要約済みの生ログ) だけ。C は候補一覧と理由を一次資料に載せ、自信のあるものだけ外す。
- sparse-checkout・木の本数削減はしない (D2211 項 9)。履歴書き換えはしない (D577)。

## 確定済みユーザー裁定
- 2026-09-29 ユーザー: 「output/ 配下にある価値の低すぎるファイルは削除した方が良いのでは。例えば『これやってみたけどこうだった』というようなもの、claude / codex から見てその知識はなくても自明と思えるもの、そういうのは掃除しても良い」
- D577: 履歴保全。旧 D577 が `git rm --cached` を却下したのは当時の依頼が「削除ではなく」だったため。今回は削除がユーザー明示。
- D2211 項 9 (b)(c): sparse-checkout と木の本数削減は採らない。

## 不変条件
- (I1) 正しさゲートの材料 (verifier 入力・正例負例・受領証・事前登録・凍結・pin/sha256/blob id で束縛された file) は外さない (規律 2・3)。
- (I2) 外した file は「どの commit のどの path にあったか」を索引 1 本 (output/PRUNED-INDEX.jsonl) で引ける (規律 7)。過去の判定は無効にしない。
- (I3) テストを弱めて通さない。削除で落ちるテストは、前提を正しく直すか file を残すかを段 4 で裁定する。
- (I4) 実装面 (.py .sh .diff .patch ほか ai-provenance の実装面拡張子) は外さない (削除も実装面 diff になるため)。README.md は外さない。
- (I5) 並行 wave が編集中の path は外さない (branch diff と稼働木の未 commit を照合)。

## 成果物
- `git rm` した file (第 1 段)、output/PRUNED-INDEX.jsonl、必要な README 1 行追記。
- 一次資料 output/insights/2026-09-29/output-pruning/README.md (走査方法と件数、分類基準と件数、外した・残した・次段候補、効果実測、限界)。
- decisions fragment (整理方針・索引・ユーザー指示の引用)、worklog fragment (次段 item)。

## 分割方針
- 段 5a: Codex author 1 本が参照閉包の走査器と索引生成器を書く (repo 外で親が実行)。(P1) 走査は固定 commit の blob を読み作業木を stat しない。
- 段 3: read-only codex 2 レンズ (「消してよい」を攻める / 「消すと困る」を攻める) が走査結果と分類規則を攻撃する。
- 段 4: 親が裁定 → 親が `git rm` と索引・README を commit (output/ は実装面でない)。
- 段 6: read-only review 1 本 (一次資料の件数・不在断定の照合) + check_docs + 受入全走。
- 効果測定: login node で同時刻 ABAB (基準 commit と整理後 commit の `git worktree add --detach` と `git status`)、n=3。

## 受入・実測環境
受入は `tools/dev_wave_wait.py acceptance --lease-optional` (計算ノード)。効果測定は Pegasus login (pegasus02)、/work Lustre 上。混雑を明記。

## 攻撃対象の provisional 裁定
- (P1) 走査は固定 commit の blob を読む (作業木の stat を避ける)。
- (P2) 「参照」は full path・insight dir 相対 path・basename・sha256・git blob id・祖先 dir の path の 6 軸。generic な basename (複数 file が同名) の一致は弱い参照として別扱い。
- (P3) C (dir 丸ごと) は worklog だけから記録場所として引かれているなら C 候補に残せる。decisions / failures / paper-story / 論文稿から引かれていれば D。
- (P4) 第 1 段は 2026-09-26 より前に最後に変更された insight dir に限る (並行 wave との衝突回避)。
