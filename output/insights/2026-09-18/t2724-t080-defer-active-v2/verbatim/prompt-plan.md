単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s1-brief.md` — 親の段 1 brief (scope A/B/C、不変条件、provisional 裁定 P1〜P5、分割方針)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/rulings-verbatim.md` — 確定済みユーザー裁定 (裁定控え末尾「裁定」節、G wave の decisions fragment、D2120 項 2、D96、D95) の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/g-wave-readme-sec4.md` — G wave の実測 (X1' を含む木で 45 node が赤になる 4 経路の表、production への波及と機序)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/chain-land-readme-sec3-5.md` — 並行 wave の実測と裁定パッケージ §3 / §3.1 / §5 (test 切り離しの必須条件 (i)〜(v))
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/g-wave-failure-table.txt` — 45 node の nodeid と assertion 本文の集計
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/t080_freeze_migration.py` — 2,558 行。読むのは `_capture_head` (637〜)、`ReceiptResolution` の定義 (grep `class ReceiptResolution`)、`inspect_receipt_history` の戻り (grep)、`_verify_holdout_live_scan` (2191〜2238)、`_gate_check_call` (2241〜)、`verify_receipt` (2284〜2394)、`static_gate_adapter` (2424〜2504)、`main` の `verify` (2520〜2558) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_oracle_driver.py` — 2,058 行。読むのは `_resolve_t080_receipt` (166〜183)、`_make_gate_decision` (186〜204)、`_campaign_t080_value` (206〜218)、`_t080_epoch_identity` (220〜232)、`_t080_adapter_refusals` (235〜320)、`_gate_check_core` (grep `def _gate_check_core`、launch_validated を受ける部分 409〜500)、`gate_check` (587〜676)、`_gate_check_validated` (679〜703)、`run_block` の冒頭〜gate (1280〜1420) と campaign-start 前の再解決 (1520〜1535) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_ratified_freeze.py` — 3,707 行。読むのは `RatifiedFreeze` / `LaunchValidatedFreeze` / `ReverifiedFreeze` / `ActiveResolution` (751〜870)、`resolve_active_generation` (1317〜1416)、`load_ratified_freeze` (1418〜)、`_enumeration_digest` (1489〜1498)、`_launch_validate` の 7〜8 段 (3498〜3575)、`launch_validate` (3577〜3585) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_holdout_freeze.py` — 読むのは `EXCLUDED_PATHS` 等の定数 (41〜62)、`search_repository` (grep `def search_repository`)、`_assert_search_pass` (grep) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_floor_campaign.py` — 読むのは `_CHAIN_RECORD_PATTERNS` (310〜325) と `clean_scan_digest` (grep `def clean_scan_digest`、5520〜5640 付近) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_oracle_driver.py` — 6,838 行。読むのは `ROOT` (34)、`_git_visible_output_paths` / `_copy_git_visible_output` (780〜870)、`_build_t080_stub_free_e2e_repo` (1364〜1500)、その consumer 検査 (1280〜1362)、`_run` (2951〜2987)、`_run_with_real_manifest_gate` (2989〜)、`_never_issued_resolution` / `_fake_launch_validated` (grep)、`test_never_issued_generator_tamper_reaches_public_driver_gate_g7` (grep)、`receipt_memo.patch_driver_resolver()` の他の呼出し (3345、3459、3738、4216、4246、5160、5240) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_floor_campaign.py` — 15,964 行。読むのは `ROOT` (46)、`_clone_committed_head_with_ccbench` (2291〜2331)、`_remove_post_seal_floor_protocols_from_replay` (2332〜2350)、`test_real_seal_protocol_to_floor_official_core_e2e` (12072〜12200 付近)、`test_public_official_preflight_accepts_versioned_protocol` 〜 `test_public_official_preflight_rejects_legacy_byte_drift_after_capture` (15790〜15850) と、それらが共有する helper (grep `_official_preflight` / `bypass_drift_gate`) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/real_repo_receipt_memo.py` — 冒頭 docstring (1〜20) と `patch_driver_resolver` (grep) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/conftest.py` — 読むのは `_REAL_REPO_NODE_INVENTORY` の冒頭 (258〜262)、`RECEIPT_MEMO_CONSUMER_NODES` (712〜745) と `_prewarm_receipt_memo` (grep) の冒頭だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_real_repo_serialization.py` — `_RECEIPT_MEMO_CONSUMERS_GOLDEN` / `_RECEIPT_MEMO_OPTOUT_GOLDEN` (503〜540) と、それらを検査する test (grep `_RECEIPT_MEMO_CONSUMERS_GOLDEN`) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_t080_freeze_migration.py` — `_verify_holdout_live_scan` を扱う test (380〜410、497〜600、970〜990) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_ratified_freeze.py` — fixture helper (109〜260: `_base_repo` / `_add_generation` / `_approve_and_point` / `_valid_g1`) と `launch_validate` を通す test 1 本 (1530〜1545) だけでよい
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/growth_test_holds.py` — 185〜270 と 520〜550 だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/phase3-8b-restart-runbook.md` — §1.1 (122〜146) と §2 (148〜160) だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/spool/README.md` — 全文

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2` (local main `24ede1d11` と同一、chain 無し) とする。上記以外も repo 内を読んでよい。git の読取り (`git log` / `git show` / `git cat-file`) は自由。chain 有り木の現物は branch `worktree-dev-wave-t2724-freeze-g1-gen` tip `229982652` (X1' `cc82edc8c` の run_dir 5 file `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/{journal.jsonl,launch_certificate.json,manifest.json,result.json,result.md}` と G `32ba8cae4` の `output/s8b-freeze/holdout_freeze.v2.g1.json`、`output/s8b-freeze-budget-inputs/g1.json`) で、`git show 229982652:<path>` で読める。候補 X2 (`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) はこの branch に無い。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。

## 背景 (親の実測、brief と同じ)

T-080 (v1 移行 receipt) の解決 `verify_receipt` は holdout を読めた場合に `_verify_holdout_live_scan` で `_assert_search_pass` (zero-hit) を要求する。v2 の `launch_validate` は closure 由来の occurrence から期待集合を導出し、全走査との完全一致 (C2-4) を要求する。X1' (official 床値 run_dir) を含む木では live scan が 3 path で hit し、receipt は `invalid`、driver の `_make_gate_decision` が refusal を無条件集約するため、A / X で g1 を active にしても oracle gate は refuse される。同じ木で受入の非 held 45 node が赤になる (4 経路)。ユーザー裁定 (codex 2 レンズ一致、委任) は択 A・設計 A-3: receipt の履歴・静的検証・epoch 束縛・refusal 集約・invalid 拒否は維持し、承認済み active v2 の full launch validation が同一 root / HEAD / 世代で成功した場合に限り、未知性層 2 (zero-hit 判定) をその完全一致検証へ委譲する。未発効の木 (A / X 前) と official clean scan (`clean_scan_digest`) は従来どおり拒否。走査除外・hold・chain と G の bytes は不変。同じ wave で 4 経路 45 node の test を実 root から切り離す (負例を残し、期待値を緩めない)。Codex author (D95)、新 D + 境界 test + 変異 matrix + 段階別 preflight 文書 (D96)。

親の session は worktree 隔離下にあり、bash guard が「他 worktree への `git -C`」「複合 shell」を拒否する。`output/s8b-freeze/` 配下への Write / Edit は hook が拒否する。

## この段の仕事

**file:line 粒度の実行計画**を起草する。brief も誤りうるので、P1〜P5 を現物で検算し、ずれは明示する。

計画に含めるもの:

1. **委譲 predicate の署名と置き場 (現物の行で根拠)。** `verify_receipt(*, root, path, launch_validated=None)` のように引数を足す形か、`_verify_holdout_live_scan(root, holdout_doc, *, delegate_to=None)` に足す形か、別関数 `_holdout_layer2_delegation(...)` を挟む形か。発火条件 (P1) の各項を現物 field で検算: `LaunchValidatedFreeze.activation_head` と `_capture_head(root)` の比較、`search_digest` と `_enumeration_digest(root)` の比較 (列挙集合の digest は同一 root・同時点でしか一致しないか、走査中に file が増減した場合どうなるか)、「同一世代」を何で束縛するか (`resolve_active_generation(root).generation_sha256 == launch_validated.ratified.sha256` を再解決するか、それとも呼出側が同じ root の `load_ratified_freeze` から得た object であることを型と head で足りるとするか — 費用と防御力を比較)。委譲時にも凍結 doc と live report の束縛 (rr80/rr20 集合、`match_convention`、`candidate_id`、`expressions`) を維持する実装 (P2: 自前で `search_repository(root)` を再走するか、`LaunchValidatedFreeze` に report / hit を載せるか — 後者は `ReverifiedFreeze` と `_launch_validate` の `result_type` に波及する。費用 (走査 1 回の実測所要は G wave で 407 秒 / receipt 解決 1 回、run_block 内で走査が何回になるか) と型の波及を数える)。refusal 文字列の互換 (`holdout-freeze-verify: [holdout.unknownness_layer2] …` の prefix / reason は変えない)。`static_gate_adapter` の independent 列 (2490) に同じ条件を適用する形。委譲したことを `ReceiptResolution` / observation / held_checks のどこに記録するか (記録しないなら理由)。
2. **driver の呼出し順 (P3) の現物検算。** `gate_check` (587〜) と `run_block` (1280〜) が receipt を v2 処理に先立って解決する現状で、`launch_validate` 成功後に委譲付き resolution をどう得るか (再解決 = git subprocess 数百本の再実行か、静的検査結果を再利用して層 2 だけ差し替えるか)。`_t080_epoch_identity` の campaign-start 前比較 (1527〜1535) が委譲の有無で変わらないこと。`_gate_check_core` (409〜500) の `launch_validated` 経路と `_t080_adapter_refusals` (235〜) が委譲付き resolution を受けても壊れないこと。v1 freeze path の `gate_check` (非 v2、`_gate_check_core` へ直行) では委譲が発火しない (= runbook P3 の v1 `gate-check` は chain 有り木で従来どおり拒否する) ことを明記。
3. **境界 test の設計 (file:関数名、fixture の作り方)。** 正例: active v2 + `launch_validate` 成功 + 同一 root/HEAD で receipt が `active-valid` になる。負例: (a) 未発効 (A / X 無し) + hit → `invalid` (`holdout.unknownness_layer2`)、(b) active v2 だが `launch_validate` 失敗 (closure 不一致) → 委譲せず従来拒否、(c) `activation_head` が root の HEAD と違う validated object → 委譲せず、(d) 別 root で得た validated object (列挙 digest 不一致) → 委譲せず、(e) 型が `LaunchValidatedFreeze` でない (`ReverifiedFreeze`、duck-typed 偽物) → 委譲せず、(f) 委譲時も凍結 doc と live report の束縛違反 (expressions 差替え) は拒否。fixture: T-080 receipt を持つ合成 repo (`test_t080_freeze_migration.py` の `_build_*` / `test_s8b_oracle_driver.py` の `_build_t080_stub_free_e2e_repo`) と v2 A / X の合成 (`test_s8b_ratified_freeze.py` の `_valid_g1` 系) をどう組み合わせるか、費用 (秒) の見積り、両方を 1 repo に載せられない場合の代替 (predicate 単体 test + driver e2e の分離)。`DW-O14`: 検査対象の機構を構成する呼出し (`search_repository`、`_assert_search_pass`、`launch_validate`) は monkeypatch しない。
4. **4 経路 45 node の切り離し (file:line と削除集合の宣言)。** (i) `_copy_git_visible_output(ROOT, …)` (1385) と `_git_visible_output_paths` に「official namespace `output/env/pegasus/calibration/s8b-floor-official/` 配下と候補 `output/s8b-freeze-candidates/` 配下だけを外す」を入れる形 (走査 hit を見て削除対象を増やさない、候補 dir の無条件削除もしない、変更前後の差分が宣言集合だけであることの検査)。同 fixture の consumer 検査 (1280〜1362) と `test_s8b_oracle_driver.py` 内の他の `_copy_git_visible_output` 呼出し (1688、1714) への影響。(ii) `_clone_committed_head_with_ccbench` (2291) の clone から同じ集合を `git rm` + commit で外す形 (`_remove_post_seal_floor_protocols_from_replay` と同型)、5 node の期待値が変わらないこと、`test_real_seal_protocol_to_floor_official_core_e2e` の `HEAD^ == source_head` assertion (12118) が commit 追加でずれる点の扱い、新 負例「chain 有り tree の `clean_scan_digest` 拒否」(official だけ / 候補だけ / 両方) を clone 上に synthetic な official run_dir / 候補 file を置いて作る形 (chain の bytes は使わない: 三軸語を含む合成 hit text は `s8b_v2_freeze_fixture._holdout_hit_text` を使う)。(iii) `_run` (2951) の memo を合成 resolution へ置換する形 (P4)、`RECEIPT_MEMO_CONSUMER_NODES` / `_RECEIPT_MEMO_CONSUMERS_GOLDEN` / `_REAL_REPO_NODE_INVENTORY` の追随 (29 node がどの分類から抜けるか、prewarm が空振りにならないか、opt-out 2 node と driftguards 4 node は残るか)。(iv) g7 test の exact refusal 集合。各経路で「chain 無し木」と「chain 有り木 (`229982652` merge)」の両方で緑になることの静的根拠。
5. **変異 matrix の候補 (負例が捕まえるべき弱体化)。** (m1) 完全一致を包含に緩める、(m2) receipt refusal を無視する、(m3) 承認前 (未発効) に委譲する、(m4) 検索規約 (`match_convention` / `expressions`) の照合を削る、(m5) campaign-start 前の再検査を削る、(m6) `activation_head` 比較を削る、(m7) 列挙 digest 比較を削る、(m8) test 側で search 拒否を外す (負例 (a) と `clean_scan_digest` 負例が失敗すること)。各変異を捕まえる test 名を対応付ける。
6. **runbook §1.1 / §2 P3 の段階別 preflight の文案 (差分)。** chain 無し main = rc=2 かつ拒否 2 件 exact (実測済み)、chain + G 発効前 = rc=2 かつ 4 件 (G wave 実測: receipt 層 2 + v1 verify + floor-null + budget-null)、発効後 (v2 freeze path で `gate-check`) = 設計上の期待で未実測と明記。「`holdout-freeze-verify:` が混ざったら本物の破損」の文をどう限定するか。
7. **分割と所有 (author 1 本か 2 本か)。** 同一 file を 2 子で触らない前提で、A = production 2 file + `test_t080_freeze_migration.py` + `test_s8b_ratified_freeze.py`、B = `test_s8b_oracle_driver.py` + `test_s8b_floor_campaign.py` + conftest / serialization 登録簿、の分け方の可否 (driver e2e の境界 test を B の file に置くなら A→B 直列)。新規 test file を作る場合に当たる pin (`test_plain_runner_coverage` の allowlist、`test_ccbench_spawn_sites` の lineno pin) の有無。
8. **受入で赤になりうる test の列挙。** 変更する production 2 file と test 4〜5 file の consumer (間接参照まで 2 段)、`test_real_repo_serialization.py` / `conftest.py` の inventory・golden、`test_s8b_binding_driftguards.py` の memo test、`test_frozen_artifacts.py` / B-4 静的 inventory の module 数 pin、`check_docs.py` の literal pin (runbook を編集した場合)。
9. **fragment の骨格。** 新 D (実装形: predicate の署名、発火条件、負例、到達範囲 = production では A / X 後まで正例に到達しないこと) と worklog fragment (T-2724 / T-2776 の更新)。G wave fragment の slug を `{{D:}}` 参照しない (fold 順が逆)。
10. **リスクと未確定点。** 走査費用 (run_block で走査が 2 回になるか)、`search_digest` の TOCTOU 窓、`_enumeration_digest` が ignored 領域をどう扱うか、chain 有り木での焦点走の作り方 (scratch merge の branch 名と worktree)、t2627 wave (`docs/pegasus-runbook.md`) との衝突無し確認。

## 禁止

- file を作成・編集しない。git の状態を変える command を打たない。pytest を走らせない (書込可能な tmp が無いので静的検査でよい)。走らせていない結果を緑と書かない。
- 走査除外 (`EXCLUDED_PATHS`、`exempt_exact` 導出)・growth hold・allowlist・chain と G の bytes・A / X の作成・`clean_scan_digest` の緩和・`_make_gate_decision` の集約・`_campaign_t080_value` の拒否を変える案を計画に入れない (規律 2)。skip flag・環境変数・引数で層 2 を無条件免除する案を入れない。
- gate・検査・台帳・tool の新設、一般化、互換層を計画に入れない (依頼が scope 外と明示)。既存策と局所修正を優先する。
- 三軸の値 (holdout の workload 定義) を出力に逐語で書かない。`output/s8b-freeze/holdout_freeze.json` への参照で示す。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 前提の検算 (P1〜P5)
## 委譲 predicate の署名と置き場
## driver の呼出し順
## 境界 test の設計
## 4 経路の切り離し
## 変異 matrix の候補
## runbook 段階別 preflight の文案
## 分割と所有
## 受入で赤になりうる test
## fragment の骨格
## リスクと未確定点
## 総括
