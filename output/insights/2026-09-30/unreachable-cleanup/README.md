# 到達不能 commit 242 件の仕分けと記帳 (2026-09-30)

依頼: `/work/1/SFC/tanab/tmp/unreachable-cleanup-2026-09-30/md_1.txt` (「未記帳 231」の仕分けと掃除)。
branch `worktree-dev-wave-unreachable-cleanup`。台帳正本は `docs/unreachable-object-ledger.md`。

## 結論

- 着手時 (19:08 JST) の監査で要確認は **238 commit**。19:11:01 JST に全件を
  `refs/rescue/unreachable-20260930/<oid>` で固定してから分類した (D1115)。記帳後の照合 (22:12 JST) で、着手後に別 session の
  掃除で到達不能になった T-2638 残差 **4 件**が新たに出たので、同じ手順で固定・記帳した (計 242)。
- 238 のうち **86 は既に台帳にあった** (D2200 項 2 の対象 = 9/21 掃除の `cleanup-20260921-*` 67 と
  監査のみの `audit-20260921-*` 19、すべて `pending`)。依頼の「231 件」は off 監査の要確認件数で、台帳照合前の数だった。
  **本当の未記帳は 152 (+ 後発 4) で、全件が T-2638 の作業木残差 commit** (題名「実装子の作業木残差を記録」)。
- 台帳の遷移 (本 wave):
  - 新規 157 entry (未記帳 152 + 後発 4 + T-2840 が指定した監査外の `b3de31e0`): `rescued` 65、`pending` 92 (捨て候補)、`reachable-again` 0。
  - D2200 項 2 の実行 (T-2829): `cleanup-20260921-*` 227 → `accepted-loss` (ユーザーが 9/21 に明示受容)、
    `audit-20260921-*` 21 → 現存 19 は `refs/rescue/cleanup-20260921-audit/<oid>` で `rescued`、**2 は `object-missing`**。
- `accepted-loss` は AI の判断では 1 件も付けていない (D2065)。捨て候補 92 は下の承認カードで人間の承認を待つ。

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
4. 分類 (一回限りの tool、Codex author・fix が job dir に作成・repo 外): 要確認 pair ごとに blob OID を main の全 blob と照合し、
   path の最初の成分が main の最上位の名前にあるか (repo 本体か scratch か) と、scratch 側の中身が出力物か
   (拡張子 pdf・png・svg・csv・tsv・md・patch・diff、`*.provenance.json`、途中に `out` dir) で分けた。
   区分と件数は `evidence/plan2-summary.md`、全件は `evidence/plan2.json` (初版 `plan.json` / `plan-summary.md` は下の再判定前)。
   - `rescue-body` 23 → `rescued`: main に無い中身が `tools/` か `output/` にある。
   - `rescue-scratch-output` 40 → `rescued`: main に無い中身に、scratch 側の研究出力物 (図・provenance・表・patch・README) がある。
   - `discard-scratch` 59 → `pending`: main に無い中身が scratch 側の script・起動器・設定 (`.py` 73・`.sh` 9・`.json` 5・`.conf` 1 対) だけ。
   - `discard-landed` 30 → `pending`: 全対が抑止 (repo 外の控えを main の文書が参照) 26、中身が main に同一 bytes・削除だけ 4。
   - `discard-extra` 1 → `pending`: `b3de31e0` (T-2840)。
   - 後発 4 件 (`evidence/round2/`): repo 外走査は行わず、固定 4 本だけを消した別の複製への off 監査 (22:2x JST、要確認 71 = 喪失受容 67 + 4) で分類した。
     抑止が付かないので救出が増える側に寄る。`rescue-scratch-output` 2・`discard-scratch` 2。
   - 捨て候補のうち救出 commit の祖先に入るものは 0 (初版の判定で確認。捨てれば実際に失われる)。
5. 着地判定器 (`check_branch_landed.py`) は実走していない。新規 entry は `assessment_verdict=indeterminate` とし理由に明記した
   (audit-20260921 の先例)。`assessment_report_sha256` は分類に使った監査 stdout の sha256。

## 段 6 レビュー (独立 read-only 1 本) と裁定

- real・採用: 初版の規則 (scratch はすべて捨て候補) が、研究図・provenance・比較表・patch を持つ commit を捨て候補に入れていた
  (例 `58c35f73…` の `scratch/out/fig8_*.pdf`)。区分 `rescue-scratch-output` を足し、記帳済み 40 件を `pending` → `rescued` へ遷移した
  (初版 commit で `pending` として記帳された状態からの遷移で、台帳の遷移契約どおり)。
- real・採用: 承認カードが類型 A の損失を過小に説明していた。下のカードを中身の種類別に書き直した。
- real・nit: 初版で救出した 23 件は `pending` を経ずに `rescued` で追記された。最終の台帳値は同じで、成果物影響が無いので直さない。
- refuted: D2065 違反 (AI 判断の `accepted-loss`)、台帳の field 破損、P1 (複製での full 監査)・P2 (T-2829・T-2840 の同時実行) の食い違い、
  件数・sha256 の食い違い、入力内の指示めいた文字列。

## 救出した 65 件 (価値あり・判断不能)

- B-5 本走の投入 script `output/insights/2026-09-23/t2797-b5-main-run/scripts/` (`calibration.sh`・`llm_parent_driver.py`・
  `setup_submit_tree.sh`・`submit_registered.py`) を含む 7 commit。`output/insights/2026-09-23/t2797-b5-main-run/` は
  dir ごと main に無く (2026-09-30 時点、`git log --all` でも残差 commit にしか現れない)、これらの commit が唯一の所在である。
- `tools/t2273_replica_*`・`tools/t2273lc_ab_analyze.py`・`tools/t2826_*`・`tools/t2817_probe_plugin.py`・`tools/login_check_*`・
  `tools/gate_wait_probe.py`・`tools/pegasus/*silo_policy_recon*`・`tools/dev-wave-probe/t2858_shape_probe_job.sh` を含む 16 commit。
- scratch 側の研究出力物を含む 42 commit (後発 2 を含む): fig8 再確認の図と provenance (`scratch/out/`)、Cicada・Silo の改変 patch
  (`md32-scratch/*.patch`・`genopt_gl_scratch/patches/`)、各 probe の README と結果表など。

## 承認カード — 捨て候補 92 件の一括喪失受容 (ユーザー手番)

authority: none / default_effect: no-state-change (承認されるまで何も消えない)

| 類型 | 件数 | 代表例 | 捨てた場合に失うもの |
|---|---|---|---|
| A. 子 worktree の script・起動器・設定だけの残差 | 61 | `.cicada-launcher/launch_cicada_run.py`、`t2851_anchor_smoke.py`、`probe-t2273is/t2273is_ab_analyze.py`、`scratch-liveness/launch_lock_order_liveness.py` | main へ land されなかった probe・起動器・解析 script (`.py`・`.sh`) と設定 (`.json`・`.conf`)。図・表・patch・README は含まない (それらを持つ commit は救出済み)。**実装を含むもの**: `scratch-output-pruning/` の `build_index.py`・`classify.py`・`scan_refs.py`・`selftest.py` (5 commit。名前から `output/insights/2026-09-29/output-pruning/` の索引作りに使った実装と見られるが未確認。同 insight に方法の記述はあり、コードは main に無い) |
| B. 中身が main か repo 外の控えに残る | 30 | `.cicada-launcher/launch_cicada_run.py` の一版 (repo 外の控えを main が参照)、`tools/strip_claude_session_trailers.sh` (削除だけ) | commit という形 (履歴・題名) だけ。bytes は main か、main の文書が参照する repo 外 path にある |
| C. amend 前の reflog 専用版 | 1 | `b3de31e0` (T-2344) | 後継 `ae0764eae` が main にあり、38 file 中 33 が同一・2 件は fold 済み fragment・3 件は着地版が後の修正を含む差 |

- 日付は 2026-09-19〜09-30。現在はすべて `refs/rescue/unreachable-20260930/<oid>` で固定中で、失われない。
- 承認されたら: 92 entry を `accepted-loss` にし (`resolution_note` に承認の所在)、固定 ref 92 本を外す。
  以後の消去は git の自動掃除に任せる (gc・prune は実行しない)。
- 一部だけ救出したい場合 (例: 類型 A のうち `scratch-output-pruning/` の 5 commit): 指定された oid を `rescued` にし、固定 ref をそのまま救出 ref として残す。

## 監査の限界

- 分類の「main に無い」は blob OID の完全一致だけを見た。改名・部分一致・gzip 化は見ていない (D2065 と同じ限界)。
- 「出力物」は拡張子と path の形だけで判定した。script の中に結果が埋め込まれている場合は捨て候補側に残る (カードで開示した)。
- full 監査は repo 外候補 2415 件を確認不能として抑止しなかった。抑止が増える方向の見落としであり、救出を減らす方向ではない。
- 複製 repo は元 repo の worktree HEAD と index を根に持たない。元 repo の off 監査と完全一致したことで対象集合への影響が無いことを確かめたが、
  一般には到達不能集合を大きく見せる方向に働く。
- 記帳後も、並走 wave の掃除で新しい到達不能 commit は出続ける。本 wave が閉じたのは land 直前の照合時点の集合である。
