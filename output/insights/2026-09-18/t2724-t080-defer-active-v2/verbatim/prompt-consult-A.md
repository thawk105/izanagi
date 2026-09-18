単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## レンズ A — 正しさ境界 (委譲 predicate の健全性・受理集合・規律 2 / 6・変異の帰属)

あなたは段 3 の敵対相談子である。段 2 の plan と親の段 1 brief の**両方**を攻撃する。plan を守らず、親の実測値とその一般化も検査対象とする。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s1-brief.md` — 親の段 1 brief
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s2-plan.md` — 段 2 plan
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/rulings-verbatim.md` — 確定済みユーザー裁定の逐語 (裁定控え、G wave fragment、D2120 項 2、D96、D95)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/g-wave-readme-sec4.md` — G wave の実測 (4 経路・production 波及)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/t080_freeze_migration.py` — `_capture_head` (637〜)、`_verify_holdout_live_scan` (2191〜2238)、`verify_receipt` (2284〜2394)、`static_gate_adapter` (2424〜2504) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_oracle_driver.py` — `_resolve_t080_receipt` 〜 `_t080_adapter_refusals` (166〜320)、`_gate_check_core` (400〜520)、`gate_check` (587〜676)、`run_block` (1280〜1420、1520〜1535) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_ratified_freeze.py` — 型定義 (751〜870)、`resolve_active_generation` (1317〜1416)、`_enumeration_digest` (1489〜1498)、`_launch_validate` 7〜8 段 (3498〜3575)、`launch_validate` / `reverify_published_freeze` (3577〜、grep) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_holdout_freeze.py` — `search_repository`、`_assert_search_pass`、`_assert_search_operational` (grep で位置を出す)、`enumerate_repository_files` (370 付近) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/CLAUDE.md` — 「絶対規律」節 (規律 2・3・6・7) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/dev-wave/mutation.md` — `DW-M01`、`DW-M03`、`DW-M04` だけ

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2` (chain 無し)。上記以外も repo 内を読んでよい。chain 有り木の現物は `git show 229982652:<path>` で読める (X1' の run_dir 5 file と G の世代文書、候補 X2 は無い)。git 読取りは自由。

**大きい file を全文 `cat` しない。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。

## 攻撃対象 (この順で)

1. **委譲 predicate は受理集合を「active v2 の full validation を通った木で層 2 の重複判定を委譲する」の 1 形だけ広げるか。** plan の 7 条件 (exact 型、`validation_root`、`activation_head` 三重一致、`resolve_active_generation` 再解決の一致、`search_digest` == `_enumeration_digest(root)`、凍結 doc 束縛、前後の不変) のどれかを外しても通る入力が無いか。特に: (a) `_assert_search_pass` が要求していた性質のうち、`launch_validate` の C2-4 完全一致 + `_assert_search_operational` + 陽性対照が**カバーしない**ものは無いか (両関数の現物を比較して差集合を列挙する)。(b) `validation_root` を `Path.resolve()` で束縛する案は symlink / bind mount / 同一 inode の別 path で破れるか、破れたときに何が通るか。(c) `_enumeration_digest` は名前集合だけ — 同名 file の内容交換 (report 取得後、receipt 再解決前) で層 2 が「hit を含む report」を「hit 無し」と誤認する経路は無いか (report は hit を持つ側なので誤認の向きを正確に書く)。(d) `resolve_active_generation` の再解決を predicate に入れる案と、型 + HEAD だけに依存する案の防御力の差を、具体的な攻撃入力 (dirty な namespace file、別世代の token、reverify 型) で比較する。
2. **報告保持 (report を `LaunchValidatedFreeze` に載せる) の是非。** `search_report` を型に載せると、その report は「v2 の `exempt_exact` を使った走査」の結果であり、T-080 の層 2 が従来見ていた「v1 prefix 除外の走査」と**列挙・除外集合が違う**。委譲時に凍結 doc の束縛 (rr80/rr20 集合、`match_convention`、`candidate_id`、`expressions`) を v2 report に掛けるのは意味的に正しいか。exempt_exact で除外された path に v1 走査なら hit していたものがあるとき、それを T-080 側が見逃す形にならないか (これが「走査免除の拡大」と同じ帰結にならないことを、`_active_chain_exempt_exact` / `_selector_evidence_exempt_exact` の現物で判定する)。代替 (自前で `search_repository(root)` を再走して束縛検査だけ行い、zero-hit だけ C2-4 に委ねる) と比べて、どちらが規律 2 に近いか。
3. **driver の呼出し順の代替案 (親の追加問い P3').** plan は「初回の委譲なし解決を維持し、launch 成功後に委譲付きで再解決」(履歴検査 3 回)。親の代替: `run_block` / `gate_check` の初回解決を launch 判定の後ろへ移し、v2 成功経路では token 付きで 1 回、`load_ratified_freeze` / `launch_validate` の失敗経路では token なしで 1 回、v1 経路では従来どおり 1 回 — 解決回数を 1 (campaign-start 前の再検査を入れて 2) に保つ。この代替で refusal の集約・fail-closed・`_t080_epoch_identity` の比較・`test_run_block_resolves_receipt_once…` の call_count 契約が壊れるか、壊れないなら plan の 3 回案より劣る点があるか。
4. **static_gate_adapter と v1 経路。** plan は adapter の independent 列にも同じ helper を適用する。adapter は v1 freeze の sha が receipt の holdout raw_sha256 と一致するときだけ発火する (`_t080_adapter_refusals:235〜`)。v2 実走では発火しないので、adapter への委譲追加は死に道か、それとも別経路 (`s8b_holdout_freeze.verify` の adapter 呼出し等) で生きるか。生きないなら足すべきでない (仮想リスク向けの追加は scope 外) — 判定せよ。
5. **test の切り離しが「赤を見た主体が入力 tree を変える」形にならないか。** 削除集合 S (official namespace 全体 + 候補 exact file) は走査結果と独立に宣言されているか。S を「hit した path」に合わせて広げる余地が plan に残っていないか。(i) の `_copy_git_visible_output` と (ii) の clone helper の削除が、既存の負例 (draft の zero-hit 検査、`clean_scan_digest` の拒否) の検出力を落とさないことをどう示すか。新負例 (合成 hit bytes を置いた clone で `clean_scan_digest` が拒否) は `_holdout_hit_text` が現行の検索式で必ず hit する保証があるか (陽性対照の意味)。
6. **変異の帰属 (DW-M01 / M03 / M04).** plan の m1〜m8 のそれぞれについて、同じ入力を拒否する層が前後・内側に無く赤理由が 1 つに絞れるかを現物で判定する。特に m6 (activation_head 比較) と m7 (列挙 digest 比較) は、`resolve_active_generation` の再解決 (条件 5) が同じ入力を先に拒否して冗長 gate になっていないか。冗長なら「単独変異の証拠から外す」か「fixture を単一理由へ差し替える」かを具体的に示す。
7. **親の brief の誤り。** P1〜P5 と不変条件の記述で、現物と食い違う点、一般化しすぎた点 (例: 「G の世代文書は除外内で hit しない」「A / X 前は必ず拒否」の根拠) を挙げる。

## 禁止

- file を作成・編集しない。git の状態を変えない。pytest を走らせない (静的検査でよい。走らせていない結果を緑と書かない)。
- 規律 2 を緩める提案 (走査除外・hold・test の変更、検査の削除、skip flag / env による免除) を代替案として出さない。
- gate・検査・台帳・tool の新設や一般化を提案しない。既存策と局所修正の範囲で答える。
- 三軸の値 (holdout の workload 定義) を出力に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ。

各所見は `A-<番号>` を付け、**must-fix / should / nit** に分類し、**放置時に成果物 (受理集合・certified 選択・oracle の gate 可否・land 集合) がどう変わるか**を 1 行で書く。示せない所見は nit とする。plan と brief の**どちら**への所見かを明記する。

節の順:

## 所見 (A-1 …)
## 報告保持 vs 自前再走 の判定
## P3' (解決 1 回化) の判定
## 変異の帰属表 (m1〜m8)
## brief と plan の食い違い
## 総括
