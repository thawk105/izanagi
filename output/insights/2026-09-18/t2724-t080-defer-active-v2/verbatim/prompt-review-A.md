単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## レンズ A — 正しさ境界のレビュー (委譲 predicate・driver 呼出し順・受理集合・規律 2 / 6・変異の帰属)

あなたは段 6 の敵対レビュー子である。実装 commit `7a763575f` (wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2`、基点 main `24ede1d11`、chain 無し) を、段 4 裁定の確定仕様に対して攻撃する。Codex author の報告と親の実測 log も検査対象とする。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s4-adjudication.md` — 段 4 裁定 (確定仕様、変異事前登録 m0〜m11)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s5-author-1.md` — Codex author の最終報告 (「実装済み・未達」の申告を含む)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s3-a.md` — 段 3 レンズ A の所見 (A-1 鮮度、A-2 帰属表、A-3 adapter、A-6 走査範囲)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/rulings-verbatim.md` — 確定済みユーザー裁定の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-1.log` — 親の焦点走 (chain 無し木 7a763575f、7 file)。末尾の集計と `FAILED` 行を見る
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-chain-1.log` — 親の焦点走 (chain 有り scratch `897224a9f` = 7a763575f + G wave tip 229982652 の merge、7 file)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-nochain-2.log` — 親の consumer 回帰 (chain 無し木、変更 production を参照する test file 群)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/focus-base-failed-nodes.txt` — 修正前 chain 有り木の 45 赤 node (対照)

差分は wave worktree で `git show 7a763575f` / `git diff 24ede1d11 7a763575f -- <path>` で読む (13 file、+623/−142)。現物は同 worktree の path を `grep -n` / `sed -n` で 200 行以内ずつ読む。**親が実行済みの分担**: patch の展開と commit、runbook の docs 編集 (未 commit、レビュー対象外)、修正前の対照走 (45 赤) と P3 gate-check (chain 無し 2 件 / chain 有り 4 件)。Codex author は pytest を走らせられない (sandbox) ので、報告の「未実走」は怠慢ではない。

**大きい file を全文 `cat` しない。**

## 攻撃対象 (この順で)

1. **委譲 predicate (`t080_freeze_migration._holdout_layer2_delegation`) が s4 の 7 条件を全部、現物どおりに課しているか。** 条件の 1 つを外しても通る入力、`except Exception: return None` が握り潰す例外の向き (通常検査へ戻るだけで受理を増やさないか)、`_assert_holdout_report_bindings` を token の ratified doc と入力 doc の両方に掛けているか、`ReverifiedFreeze` / subclass / duck 型の拒否、`validation_root` の resolve 比較、`resolve_active_generation` の 4 要素比較、`_enumeration_digest` 比較。
2. **driver の呼出し順 (P3')。** `gate_check` と `run_block` の全 return 経路で receipt が 1 回解決されているか (解決を省いた早期 return は無いか)、v2 成功経路だけ token 付きか、v1 経路で token が渡らないか、campaign-start 前の `launch_validate` 再実行 → 3 要素一致 → 委譲付き再解決 → `_t080_epoch_identity` 比較の順序と refusal prefix、新しい refusal return を増やしていないか (15 return pin)、`_t080_adapter_refusals` / `_gate_check_core` に token が転送されていないか。
3. **受理集合の差分。** 変更後に受理されるようになる入力集合が「active v2 の直前の full validation を通した同一 root / HEAD / 世代の木で、receipt 層 2 の zero-hit 判定だけを C2-4 に委ねる」の 1 形だけか。それ以外に受理が広がる経路 (test 側の登録簿変更・fixture 変更を含む) が無いか。走査除外・hold・allowlist・G / chain の bytes が 0 byte か (`git show --stat 7a763575f`)。
4. **A-1 (鮮度) の実装。** campaign-start 前の再 launch が本当に新鮮な走査を含むか、gate 時 token と fresh token の一致検査 (`ratified.sha256` / `activation_head` / `search_digest`) の後に fresh token で再解決しているか。gate 後・campaign-start 前に namespace 外の合成 hit を置くと拒否される経路を test (`test_t080_delegated_campaign_start_rejects_late_hit`) が本当に通るか (fixture が実 `launch_validate` を通しているか、代役に落ちていないか)。
5. **test 切り離しが規律 2 に触れないか。** 削除集合 S が走査結果と独立に宣言されているか (`_copy_git_visible_output` と floor の削除 helper の現物)、既存負例 (draft zero-hit、`clean_scan_digest` 拒否、hash drift、`bypass_drift_gate`) の検出力が落ちていないか、新負例が実 `clean_scan_digest` / 実 draft を通り report の hit を確認しているか、`_run` の合成 resolution 化で失われる契約 (active-valid の observation を WAL へ載せる契約は opt-out 2 関数に残るか)。
6. **変異の帰属 (m0〜m11) の実装後判定。** author の anchor 表に対し、各変異が単一理由で赤になるか、mask する後段比較が無いか (m6 は outer HEAD 比較だけを外す置換で `validation_head == _capture_head(root)` を残す、m7 は namespace 外 file、m3 は `if not delegated:` の zero-hit 省略)、kill を観測する test が実機構 (代役でない) を通るか。冗長 gate があれば「単独変異の証拠から外す」対象を名指す。
7. **焦点走 log の赤の帰属。** `focus-nochain-1.log` / `focus-chain-1.log` / `focus-nochain-2.log` の FAILED を、実装差分起因 / test 側の fixture 起因 / 非帰属 (環境) に分類し、fix 指示を file:関数 粒度で書く。chain 有り木で残る赤があれば、45 node の対照 (`focus-base-failed-nodes.txt`) と照合して「解消 / 残存 / 新規」を表にする。

## 親の一次判定 (攻撃対象。誤りなら指摘せよ)

焦点走の実測: chain 無し木 = 1086 passed / 9 failed / 11 skipped、chain 有り木 = 1085 passed / 10 failed / 11 skipped。修正前 45 赤のうち 44 は chain 有り木で緑になり、残る 1 は `test_real_seal_protocol_to_floor_official_core_e2e` (`clean_calls == [expected_clean_digest]*2` の不一致 — clone に残る G の世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json` を production の `clean_scan_digest` は chain record として path + sha256 を digest に含めるが、test 側の `expected_clean_digest` は `frozen_paths` だけを allowlist に入れるため)。両木共通の新規赤 9 = (a) 8 本の接続系 test が `_build_t080_active_v2_repo` → `build_production_emitter_g1` の build seam (`test_s8b_ratified_freeze.py:520` `compiler_input_rel = "fixture.txt"`) で `external/ccbench/fixture.txt` を実 ccbench clone に探して `FileNotFoundError` (接続 fixture は `_make_fixed_ccbench` を使わないので固定 file が無い)、(b) 既存 `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` が `refused` — campaign-start 前の `launch_validate` 再実行が floor artifact を disk から再読して swap を観測するため、E3b / A3-6 (launch 済みの同一 object だけを使い disk を再読しない) の契約と衝突。親の fix 方針: (b) は再 launch をやめ、artifact を再読しない**走査だけの再検査** (`s8b_ratified_freeze` に token を受ける helper: HEAD / resolve 済み root 一致 → `_assert_no_untracked_symlink` → `_active_chain_exempt_exact` + `_selector_evidence_exempt_exact` で exempt を再導出 → 前後 `_enumeration_digest` 一致かつ token の `search_digest` と一致 → `search_repository` → `_assert_search_operational` → per-holdout `conjunction_hits` が token の `search_report` と完全一致) を campaign-start 前に置き、通れば gate 時 token で委譲付き再解決 + epoch 比較する。(a) は build seam の `compiler_input_rel` を接続 fixture から指定可能にし、実 ccbench 内の実在 file を渡す (test 側のみ)。この方針の穴 (走査だけの再検査で失う保証、E3b との整合、m11 の照準変更) を指摘せよ。

## 禁止

- file を作成・編集しない。git の状態を変えない。pytest を走らせない (親の log を根拠にし、走らせていない結果を緑と書かない)。
- 規律 2 を緩める提案 (走査除外・hold・test の緩和、検査の削除、skip flag / env 免除) を代替案として出さない。既存 test の期待値を変える fix を提案しない (期待値が誤りなら実装を直す案を書く)。
- gate・検査・台帳・tool の新設や一般化を提案しない。
- 三軸の値 (holdout の workload 定義) を出力に逐語で書かない。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ。

各所見は `RA-<番号>` を付け、**must-fix / should / nit** に分類し、**放置時に成果物 (受理集合・oracle gate 可否・certified 選択・land 集合) がどう変わるか**を 1 行で書く。示せない所見は nit。fix 指示は file:関数 粒度で、変更してよい範囲と変更してはならない範囲 (既存 test の期待値) を分けて書く。最後に **GO / NO-GO** を 1 語で書く。

節の順:

## 所見 (RA-1 …)
## 受理集合の差分 (現物)
## 変異の帰属表 (m0〜m11、実装後)
## 焦点走の赤の帰属と fix 指示
## 総括
