単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## 焦点再レビュー (fix-1〜3 統合後の全体、1 本)

あなたは段 6 の焦点再レビュー子である。段 6 レビュー A / B の所見 (RA-1〜6、RB-1〜8) と親の fix 指示 (F1〜F10、G1〜G4、H1〜H3) に対する fix-1 (`02a43dd58`)・fix-2 (`7c007333b`)・fix-3 (`8b8bb96f2`) の対応を、**所見ごとに closed / partial / regressed** で判定する。表なしで root cause が閉じたと判定しない (DW-O16)。親が書いた派生値 (件数・「全部」「だけ」の量化) は原データから再計算して照合する。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s4-adjudication.md` — 段 4 裁定
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-review-a-1.md` — レビュー A
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-review-b-1.md` — レビュー B
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s6-fix1-findings.md` — 親の fix-1 指示 (F1: 段 4 の A-1 実装形を改める裁定を含む)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s6-fix2-findings.md` — 親の fix-2 指示
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s6-fix3-findings.md` — 親の fix-3 指示
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-fix1.md` — fix-1 の報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-fix2.md` — fix-2 の報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s6-fix3.md` — fix-3 の報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-5.log` — fix-3 後の chain 無し木 (7 + 22 file)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-chain-4.log` — fix-3 後の chain 有り木 (7 file)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-chain-3.log` — fix-2 後の chain 有り木 (接続正例が緑、lock deadline の INTERNALERROR は冒頭)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-base-failed-nodes.txt` — 修正前 chain 有り木の 45 赤

差分は wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2` で `git diff 24ede1d11 8b8bb96f2 --stat` / `git diff 24ede1d11 8b8bb96f2 -- <path>` (全体) と `git show 02a43dd58` / `7c007333b` / `8b8bb96f2` (fix ごと) で読む。現物は `grep -n` / `sed -n` で 200 行以内ずつ。**親が実行済み**: patch の展開と 4 commit、焦点走 (親 log)、runbook の docs 編集 (未 commit、対象外)。fix 子は pytest を走らせられない。

**大きい file を全文 `cat` しない。**

## 検査項目 (この順で)

1. **対応表。** RA-1〜6 / RB-1〜8 / F1〜F10 / G1〜G4 / H1〜H3 の各項を closed / partial / regressed に分類し、根拠 (file:関数 と log の該当行) を付ける。
2. **F1 の裁定 (campaign-start で再 launch も再走査もしない) の実装が、E3b (disk-swap test) と `[changed|missing]` / `late_hit_file` の両方を満たすか** を現物と log で確認。予備の refusal 経路 (`fresh_validated` 系) が残っていないか、15 refusal-return pin と解決回数 2 が維持されているか。
3. **接続 fixture (shared-base 5 要素 key)**: 旧 4 要素 key の digest が不変か (既存 stub-free e2e の base が変わらない)、`active_v2_base` の除外集合が basis commit 前に適用されるか、copy の独立性、consumer pin 20 node の数え方が正しいか、登録簿 (conftest / serialization) から接続 9 node を外し seam 負例だけ残した状態が、実際の実 root access と一致するか (`root=ROOT` を渡す test を全部列挙して検算)。
4. **両木の緑 / 赤**: `focus-nochain-5.log` と `focus-chain-4.log` の FAILED を帰属し、修正前 45 node が chain 有り木で全部緑かを `focus-base-failed-nodes.txt` と照合。INTERNALERROR (lock deadline) が消えたか。
5. **受理集合の最終差分**: 段 5〜fix-3 を通しで、意図した 1 形 (active v2 の直前の full validation を通した同一 root / HEAD / 世代の木で receipt 層 2 の zero-hit 判定を C2-4 へ委譲) 以外に受理が広がる経路が無いか。走査除外・hold・allowlist・G / chain の bytes が 0 byte か (`git diff 24ede1d11 8b8bb96f2 --stat`)。
6. **変異の帰属 (m0〜m10、m8b / m11 除外後)**: anchor が現物で一意か、各 kill を観測する test が実機構を通るか (fix-3 後の test 名で)。
7. **残る懸念**: test 時間 (接続 fixture の base 1 回 + copy、`--durations` の値)、RB-6 の登録解除が孕む risk、その他。

## 禁止

- file を作成・編集しない。git の状態を変えない。pytest を走らせない。
- 規律 2 を緩める提案、既存 test の期待値を変える提案、gate・検査・台帳の新設や一般化の提案をしない。
- 三軸の値を出力に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。所見は `RR-<番号>` を付け must-fix / should / nit に分類し、成果物影響を 1 行で書く。最後に **GO / NO-GO** を 1 語で書く。

節の順:

## 対応表 (所見 ID → closed / partial / regressed、根拠)
## F1 と E3b の整合
## 接続 fixture と登録簿
## 両木の赤の帰属と 45 node の照合
## 受理集合の最終差分
## 変異の帰属表
## 所見 (RR-1 …)
## 総括
