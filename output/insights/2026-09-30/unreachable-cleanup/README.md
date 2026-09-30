# 到達不能 commit 238 件の仕分けと記帳 (2026-09-30)

依頼: `/work/1/SFC/tanab/tmp/unreachable-cleanup-2026-09-30/md_1.txt` (「未記帳 231」の仕分けと掃除)。
branch `worktree-dev-wave-unreachable-cleanup`。台帳正本は `docs/unreachable-object-ledger.md`。

## 結論

- 着手時 (19:08 JST) の監査で要確認は **238 commit**。19:11:01 JST に全件を
  `refs/rescue/unreachable-20260930/<oid>` で固定してから分類した (D1115)。
- 238 のうち **86 は既に台帳にあった** (D2200 項 2 の対象 = 9/21 掃除の `cleanup-20260921-*` 67 と
  監査のみの `audit-20260921-*` 19、すべて `pending`)。依頼の「231 件」は off 監査の要確認件数で、台帳照合前の数だった。
  **本当の未記帳は 152 で、全件が T-2638 の作業木残差 commit** (題名「実装子の作業木残差を記録」)。
- 台帳の遷移 (本 wave):
  - 新規 153 entry (未記帳 152 + T-2840 が指定した監査外の `b3de31e0`): `rescued` 23、`pending` 130 (捨て候補)、`reachable-again` 0。
  - D2200 項 2 の実行 (T-2829): `cleanup-20260921-*` 227 → `accepted-loss` (ユーザーが 9/21 に明示受容)、
    `audit-20260921-*` 21 → 現存 19 は `refs/rescue/cleanup-20260921-audit/<oid>` で `rescued`、**2 は `object-missing`**。
- `accepted-loss` は AI の判断では 1 件も付けていない (D2065)。捨て候補 130 は下の承認カードで人間の承認を待つ。

## 消えていた 2 object (実害)

`audit-20260921-bebeb887d48d…` と `audit-20260921-c2ae05befdbf…` は D2200 (9/21) で「救出」と裁定されたが、
救出 ref の作成 (T-2829) が 9 日間実行されず、その間に object が失われていた。台帳自身が示していた喪失下界
(loose mtime + 2 週間 = 9/23・9/21) を過ぎている。2026-09-30 19:2x JST と 21:43 JST の 2 回、`git cat-file` で不在。
9/21 bundle の祖先集合外で、repo 外に題名・path を残した監査出力は見つからなかった (`dev-wave-jobs` の grep は 30 分で打ち切り)。

## 手順

1. off 監査 (`--offrepo-scan off`、元 repo、19:08〜19:10 JST、rc=1): fsck 到達不能 2034、要確認 238 commit / 1197 対 (`evidence/audit-off.txt`)。
2. 固定 238 本 (`update-ref --stdin`、作成後に一覧と一致)。
3. **固定すると fsck が対象を到達可能と見るので、full 監査は複製で行った。** `git clone --mirror --shared` の複製を非 bare にし、
   自分の固定 ref 238 本だけを複製から消した。複製への off 監査が元 repo と完全一致 (2034 / 238 / 1197) したことで代役の忠実性を確かめた。
   複製への full 監査 (`--offrepo-scan full --offrepo-root /work/1/SFC/tanab/dev-wave-jobs`、19:12〜20:14 JST、3701 秒、rc=1):
   抑止 600 対、要確認 183 commit、repo 外候補の確認不能 2415 件 (抑止せず) (`evidence/audit-full-view.txt`)。
4. 分類 (一回限りの tool、Codex author が job dir に作成・repo 外): 要確認 pair ごとに blob OID を main の全 blob と照合し、
   path の最初の成分が main の最上位の名前にあるか (repo 本体) で分けた。区分と件数は `evidence/plan-summary.md`、全件は `evidence/plan.json`。
   - `rescue-body` 23 → `rescued`: main に無い中身が `tools/` か `output/` にある。
   - `discard-scratch` 99 → `pending`: main に無い中身がすべて最上位の probe / scratch dir (子 worktree の未追跡物)。
   - `discard-landed` 30 → `pending`: 全対が抑止 (repo 外の控えを main の文書が参照) 26、中身が main に同一 bytes・削除だけ 4。
   - `discard-extra` 1 → `pending`: `b3de31e0` (T-2840)。
   - 捨て候補 130 のうち救出 23 の祖先に入るものは 0 (捨てれば実際に失われる)。
5. 着地判定器 (`check_branch_landed.py`) は実走していない。新規 entry は `assessment_verdict=indeterminate` とし理由に明記した
   (audit-20260921 の先例)。`assessment_report_sha256` は full 監査 stdout の sha256。

## 救出した 23 件 (価値あり・判断不能)

- B-5 本走の投入 script `output/insights/2026-09-23/t2797-b5-main-run/scripts/` (`calibration.sh`・`llm_parent_driver.py`・
  `setup_submit_tree.sh`・`submit_registered.py`) を含む 7 commit。`output/insights/2026-09-23/t2797-b5-main-run/` は
  dir ごと main に無く (2026-09-30 時点、`git log --all` でも残差 commit にしか現れない)、これらの commit が唯一の所在である。
- `tools/t2273_replica_*`・`tools/t2273lc_ab_analyze.py`・`tools/t2826_*`・`tools/t2817_probe_plugin.py`・`tools/login_check_*`・
  `tools/gate_wait_probe.py`・`tools/pegasus/*silo_policy_recon*`・`tools/dev-wave-probe/t2858_shape_probe_job.sh` を含む 16 commit。

## 承認カード — 捨て候補 130 件の一括喪失受容 (ユーザー手番)

authority: none / default_effect: no-state-change (承認されるまで何も消えない)

| 類型 | 件数 | 代表例 | 捨てた場合に失うもの |
|---|---|---|---|
| A. 子 worktree の scratch・probe 残差 | 99 | `md32-scratch/launch_promo_confirm.py`、`genopt_gl_scratch/*.py`、`t2872_probe/scratch/*.cc`、`.cicada-launcher/` | 終わった wave の子 worktree に残った未追跡の probe script・scratch 出力・起動器。main へ land されなかった試行の中間物。記録 (insight・worklog) は main にある |
| B. 中身が main か repo 外の控えに残る | 30 | `.cicada-launcher/launch_cicada_run.py` (repo 外の控えを main が参照)、`tools/strip_claude_session_trailers.sh` (削除だけ) | commit という形 (履歴・題名) だけ。bytes は main か、main の文書が参照する repo 外 path にある |
| C. amend 前の reflog 専用版 | 1 | `b3de31e0` (T-2344) | 後継 `ae0764eae` が main にあり、38 file 中 33 が同一・2 件は fold 済み fragment・3 件は着地版が後の修正を含む差 |

- 日付は 2026-09-19〜09-30。現在はすべて `refs/rescue/unreachable-20260930/<oid>` で固定中で、失われない。
- 承認されたら: 130 entry を `accepted-loss` にし (`resolution_note` に承認の所在)、固定 ref 130 本を外す。
  以後の消去は git の自動掃除に任せる (gc・prune は実行しない)。
- 却下・一部救出の指示なら: 指定された類型・oid を `rescued` にし、固定 ref をそのまま救出 ref として残す。

## 監査の限界

- 分類の「main に無い」は blob OID の完全一致だけを見た。改名・部分一致・gzip 化は見ていない (D2065 と同じ限界)。
- full 監査は repo 外候補 2415 件を確認不能として抑止しなかった。抑止が増える方向の見落としであり、救出を減らす方向ではない。
- 複製 repo は元 repo の worktree HEAD と index を根に持たない。元 repo の off 監査と完全一致したことで対象集合への影響が無いことを確かめたが、
  一般には到達不能集合を大きく見せる方向に働く。
