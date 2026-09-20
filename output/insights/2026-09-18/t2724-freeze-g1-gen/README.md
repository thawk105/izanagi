# [T-2724] 凍結 v2 g1 の世代導入 commit G を Codex author が作った — 候補 bytes を変えずに X1' の子として導入し、批准側の構造・内容検査を A / X 無しで実測、承認 A と pointer X は人間手番として手順を残す

wave `dev-wave-t2724-freeze-g1-gen`、base = local main `d2ebef7a407dc6be61622ed596cf08b8b518f606`
(2026-09-18 06:21 JST 時点)。G は branch `freeze-g1-gen-t2724`、wave branch `worktree-dev-wave-t2724-freeze-g1-gen`。
裁定の根拠は D2120 項 2 (b) と D2098 理由節。実装面 (`orchestrator/` `tools/` `hooks/` `.github/` `.codex/`
`external/` `patches/`) の差分はゼロ (段 7 で `git diff --name-only <base>..HEAD` により実測)。

**何をしたか。** 前 wave ([T-2724] 候補生成、`output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/`) が保存
branch `freeze-g1-chain-t2724` に置いた候補 X2 `4d8fb93b7` の bytes を、Codex author が X1' `cc82edc8c`
(候補の `frozen_at_head`) を親とする新 branch 上で世代文書 `output/s8b-freeze/holdout_freeze.v2.g1.json` として
書き、親が commit した。それが世代導入 commit **G = `32ba8cae45001697f050bee377413153e6d798a5`** である。
G は未発効 — `output/s8b-freeze/approvals/` と `active/` は作っていない。発効に要る承認 A と active pointer X
は起草時点では provenance 規約上 AI が作れない人間 commit であり、その手順を §5 に残す (2026-09-20 13:2x の
ユーザー裁定で AI 委任へ改訂され、同日 A `a3bf67a8c` / X `70e87c9c9` として実施済み — §5 冒頭の改訂注記)。

## 1. 入力と出所

| 項目 | 値 | 出所 |
|---|---|---|
| 候補 (X2) | `4d8fb93b7c8d5466e9ad91b1bc5b600a2fdd7ac8:output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、blob `15861416f37f08ba72fac0c69b65c1505296ec88`、20,737 bytes、sha256 `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06` | 前 wave insight §3 と一致 (親が blob を読み直して実測)。**裁定済み X2 の bytes を変更せず採用した**のであって、producer からの再生成・生成過程の再現ではない (段 3 A-6) |
| X1' | `cc82edc8c9f90a9ee659c2d27f71b75b19a56490` = 候補の `frozen_at_head`。official 床値 result (run `20260916T111925Z-2c8cf9be`) の 5 file + budget 入力 `output/s8b-freeze-budget-inputs/g1.json` | 保存 branch `freeze-g1-chain-t2724` |
| 候補 header (親の実測) | `schema_version` `8b-holdout-freeze/v2`、`generation_number` 1、`supersedes_sha256` `315b1eb8…` (v1 固定 hash)、`env_tag` `pegasus`、`measurement_closure` `[]`、`floor_protocol.path` = 版付き protocol、`floor_source.path` = result.json | job dir `candidate_header_probe.py` |
| main の状態 (着手時) | P `3b0b75496` は main 祖先、X1' / X2 は main に無い。世代文書 path は全 ref 履歴に一度も無い (`git log --all --full-history -- <path>` 空、段 3 A-1 が再確認) | 親と段 3 の実測 |
| 並行 wave | `worktree-dev-wave-t2724-freeze-g1-chain-land` (D2120 項 2 (a) の chain 取り込み) が branch tip `b227d0d91` (旧 main + X2 の merge) まで進行、本 wave の段 6 時点で未 land | `git worktree list`、`git log` |

## 2. G の作成と実測

- **書込み経路。** `hooks/guard_write.py:314-321` は `output/s8b-freeze/` への Write / Edit / apply_patch を拒否する。これは
  hooks README (150 行、343 行) と runbook W-3 が「誤操作抑止であって認証防壁ではない」「Bash 経路は開いている」と
  明記する面で、発効の真正性は Git の topology と trailer が担う。Codex author は cwd = G 用 worktree
  (`.codex/worktrees/t2724-g1-gen`、HEAD X1') で `git cat-file blob 15861416… > output/s8b-freeze/holdout_freeze.v2.g1.json`
  により書いた (段 5、rc=0、model call 8、114 秒)。段 3 レンズ A の判定: 「既裁定 (D2120 項 2 (b)、runbook W-3) に
  基づく固定 bytes 導入の限定操作として許容。Bash 面一般の書込み許可とは解釈しない。hook の無効化・難読化・
  `none` 偽装・A / X 代行は伴わない」。guard_bash の静的判定は wave 木・G 用木の両方、5 綴りで一致 (True) したが、
  実 executor の自動発火の証明ではない (A-7)。
- **author の自己検証** (`artifacts/…/s5-author.md`): sha256 一致、`git hash-object` == `15861416…`、20,737 bytes、mode 644、
  `cmp` 無出力、header 3 field 各 1 hit、`git status --porcelain` は当該 1 行のみ。commit・add はしていない。
- **commit (親、`run-g-commit.sh` を G 用木で detach 実行、`g-commit.log`)**: `git add` → staged `A` 1 件 (index mode
  100644、blob `15861416…`) → `check_ai_provenance.py --message-file` rc=0 → `git commit -F g-message.txt` →
  **G `32ba8cae45001697f050bee377413153e6d798a5`**、`rev-list --parents` = (X1',)、`diff-tree --name-status` = `A` 1 件、
  `ls-tree` = `100644 blob 15861416…`。G 用木の checker で `--range HEAD~1..HEAD` rc=0 (計算ノード dispatch、request 4992.nqsv)。
- **trailer**: `AI-Agent: product=codex; model=gpt-6-astra; reasoning=medium; role=author; scope=generation-document` (launcher
  receipt の `recorded_model` / `recorded_effort`、`effort_authority=docs`) と `AI-Agent: product=claude; model=claude-opus-5-1m;
  reasoning=xhigh; role=manager; scope=wave-manager`。`none` 行なし。本文に三軸 literal・防護 path・`none` の逐語 trailer 形は書いていない。
- **merge (wave 木)**: `git merge --no-ff --no-commit freeze-g1-gen-t2724` → staged `A` 7 件 (X1' の 6 file + 世代文書)、
  未解決 0 → `merge-message.txt` (Claude integrator) preflight rc=0 → **merge commit `88d02046644acff922937f2c5c10cbf10da2413b`**
  (親 = `d2ebef7a4`、G)。merge 後 `git status --porcelain --untracked-files=all -- output/s8b-freeze` 空。

## 3. 批准側の検査 (H = wave 木 `88d020466`、A / X 無し)

read-only probe (`evidence/g1-gen-probe.json`、job dir `g1_gen_probe.py`。`s8b_ratified_freeze` の関数を個別に呼ぶ。
production の `ActiveResolution` は構築せず、V2 だけ `generation_number=1` の probe 専用 namespace を渡した)。

| 検査 | 関数 | 結果 |
|---|---|---|
| namespace の全 commit 履歴不変・導入一意 | `_commit_graph(H)` (11,548 commit)、`_immutable_introductions`、`_unique_introduction` | 導入 commit = G ただ 1 つ (merge commit は G を持つ親があるため導入に数えない、`RF:511` の全親 absent 条件) |
| 世代導入 commit の provenance | `_assert_candidate_commit(G)` | ok — 非 merge、`_is_none_commit` False、parse 上の AI-Agent 値 2 行 (上記) |
| G の diff | `_added_paths(G)` | 追加 = 世代文書 1 path、その他 0 |
| 文書の構造 | `_parse_generation_document(raw, 1)` | ok、sha256 `7e1114…`、20,737 bytes |
| V1a 親 == `frozen_at_head` | `_parents_of(G)` | (X1',) 一致 |
| V1b source blob (`frozen_at_head` の blob) | `design_source` / `generator` / `known_axes_freeze` | 3 件とも sha256 一致 |
| V1c | `env_contract.lookup("pegasus")` | ok |
| V1d closure (G tree 実在 + sha256 + H tree + worktree == H blob + 履歴不変) | `_closure_entries` = `floor_protocol` (版付き protocol、導入 `f1500108f`) と `floor_source` (result.json、導入 X1') | 2 entry とも全条件 true、protocol は strict parse ok |
| g1 の floor 投影 | `_project_floor_for_freeze(floor_source)` の canonical bytes == `generation.floor` | 一致 |
| V2 transition (v1 → g1、F5 JSON Pointer 完全列挙) | `_verify_chain_transitions` | ok |
| V3 層 1 (snapshot 再計算) | `_verify_snapshot_layer1` | ok |
| namespace dirty | `_assert_namespace_clean` | ok |
| production 入口 | `resolve_active_generation` / `load_ratified_freeze` | いずれも `RatifiedFreezeError reason=no-active` (構造検査の終端 `RF:1358` まで到達、A / X が無いので期待どおり) |

合格範囲は「構造 + V1a〜V1d + floor 投影 + V2 + V3 層 1 の**個別関数診断**」であり、批准・発効の成功ではない
(段 3 A-3 / B-4)。probe は不一致を boolean / 文字列で出力するだけで exit code を失敗にしない診断 script であり、上の表は
出力 JSON を親が目視で読んだ結果である (段 6 RA-5)。「G が不正なら必ず落ちる verifier」ではない。V1d の「worktree == H blob」は checkout 依存で、受入対象の wave 木で測った値である。

**三軸走査** (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、wave 木、`evidence/search-projection.json`):
rc=1、hit は両 holdout とも X1' の run_dir 3 path (journal / manifest / result) だけ。世代文書は `EXCLUDED_PATHS`
(`output/s8b-freeze/` prefix) の内側で非 hit、`launch_certificate.json` / `result.md` / budget 入力も非 hit。陽性対照
188 hit / 10 path。X2 (候補) が H に入れば candidate path が加わり各 4 path になる (段 2)。検索式と三軸の値は本資料に
複製しない。

## 4. 新事実 — X1' を含む木では受入全走が赤になり、oracle の gate も閉じる (D2120 項 2 (a)(d) の裁定時に未見)

前 wave の一次資料 §8 と `package.md` (d) は、chain が main に載ると赤になる test として growth hold 中の 2 本を記録したが、
hold 外で実 root を読む test と production gate への波及を列挙していなかった。D2120 項 2 (d) はその材料で裁定された。段 1 で
親は held の 2 本 (`test_s8b_holdout_freeze.py::test_verify_cli_accepts_active_t080_receipt_exact_match` /
`::test_verify_direct_cli_accepts_active_t080_receipt_exact_match`、`growth_test_holds.py:263-268`) を純増として足したが、段 3
レンズ B (B-2) が「実 root の output を fixture へ複製する test」「実 committed HEAD を clone する test」を静的に指摘し、
親が merge 後の wave 木で実走して確定した。

**焦点走** (`tools/run_tests.py`、計算ノード dispatch request 5001.nqsv、log 末尾 07:10 JST、`evidence/focus-1-summary.txt`、
node ごとの assertion 本文は `evidence/failure-table.txt`): `test_s8b_oracle_driver.py` / `test_s8b_floor_campaign.py` /
`test_s8b_ratified_freeze.py` / `test_s8b_holdout_freeze.py` / `test_frozen_artifacts.py` / `test_s8b_oracle_manifest.py` で
**45 failed / 967 passed / 11 skipped** (422.9 秒)。赤は `test_s8b_oracle_driver.py` 40 node + `test_s8b_floor_campaign.py` 5 node
で、いずれも growth hold 外。45 node の assertion 本文 (計算ノード側の完全出力 `izdw-88fde1a490.o5001` から node ごとに最初の
`E` 行を取った) は次の 4 経路に分かれ、いずれも X1' の run_dir 3 file (journal / manifest / result) の三軸 hit (§3 の走査と同じ
3 path) に帰着する:

| 経路 | node 数 | 代表 nodeid | 機序 (現物) と assertion 本文 |
|---|---|---|---|
| (i) T-080 fixture の draft live scan | 10 | `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`、`test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[4 param]`、`test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5`、`test_t080_full_valid_history_defects_have_one_baseline_reason_f28[3 param]`、`test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28` | `_copy_git_visible_output(ROOT, …)` (`test_s8b_oracle_driver.py:1385`) が実 root の git-visible な output を複製し、subprocess 内の draft (`t080_freeze_migration._draft_reconstruct_holdout` → `search_repository` → `_assert_search_pass`) が `FreezeError: rr80: holdout hit 3 件 …` で落ちる (traceback に `search_assertion(report)` と `"holdout": _draft_reconstruct_holdout(` が各 10 回) |
| (ii) 実 HEAD clone の official clean scan | 5 | `test_real_seal_protocol_to_floor_official_core_e2e`、`test_public_official_preflight_accepts_{versioned,legacy}_protocol`、`test_public_official_preflight_rejects_{resolved_protocol_byte_drift,legacy_byte_drift_after_capture}` | `_clone_committed_head_with_ccbench` (`test_s8b_floor_campaign.py:2291`) が実 HEAD を clone し、`clean_scan_digest` (`s8b_floor_campaign.py:5622` 経由) が `launch certificate: clean scan 拒否: rr80: holdout hit 3 件` (3 node)。byte-drift の負例 2 node は期待する drift 拒否より先に clean scan 拒否が出て文言不一致 |
| (iii) driver `run_block(root=ROOT)` の T-080 receipt 解決 | 29 | `assert 'refused' == 'completed'` 7、`DID NOT RAISE OracleDriverError` 6、`assert 'refused' == 'error'` 4、`probe_perf_availability … Called 0 times` 3、`KeyError: 'events'` 2、`'refused' == 'protocol_violation'` 2、`'refused' == 'budget_exhausted…'` 1、`status: refused` 1、`DID NOT RAISE WalAppendError` 1、CLI rc `2 == 1` 1、`DID NOT RAISE OSError` 1 | `_run` (`test_s8b_oracle_driver.py:2951`) は `_gate_check_validated` を allowed=True に置換したうえで `driver.run_block(root=ROOT)` を呼ぶ。driver は T-080 receipt を実 root で解決 (`_resolve_t080_receipt` → `verify_receipt`、`receipt_memo` で process 内共有) し、gate の後の `_campaign_t080_value(t080_resolution)` (`s8b_oracle_driver.py:206-218`、`:1411`) が `state=invalid` (refusals 非空) を `OracleDriverError` にし、`run_block` は `{"status": "refused", …}` を返して budget / marker / WAL / evaluate に到達しない。契約 test はそこで期待する status・例外・呼出しを得られない |
| (iv) 公開 driver gate の v1 verify | 1 | `test_never_issued_generator_tamper_reaches_public_driver_gate_g7` | 公開 `gate_check` の refusals に `holdout-freeze-verify: FreezeError: rr80: holdout hit 3 件` が加わり、期待する exact refusal 集合と不一致 |

10 + 5 + 29 + 1 = 45。(iii) の 29 node は clean な木での対照走をしていない — 帰属は「同じ memo の実 root 解決が `state=invalid`
であること (下の probe と P3)」と「`run_block` が `_campaign_t080_value` で拒否を返す経路 (現物)」の読解による。**確認した走査
refusal はすべて X1' の 3 path に由来する。** G の世代文書は `EXCLUDED_PATHS` の内側で走査 hit を増やさず (§3)、
`resolve_active_generation` は `no-active` のまま (§3)、`clean_scan_digest` の allowlist も世代文書名を chain record として受理する
(`s8b_floor_campaign.py:318-319` `_CHAIN_RECORD_PATTERNS`、`:5481`) — ただし「G が全 test に無影響」は対照走なしでは主張しない。

**production への波及 (親の実測):**

- 実 root の T-080 receipt 解決 `t080_freeze_migration.verify_receipt(root=wave 木)`: **`state=invalid`**、refusal
  `holdout-freeze-verify: [holdout.unknownness_layer2] FreezeError: rr80: holdout hit 3 件: [journal / manifest / result]; rr20: 同`
  (job dir `t080_receipt_probe.py`、login node、407 秒、held_checks 3)。
- runbook §2 **P3 `gate-check --freeze output/s8b-freeze/holdout_freeze.json`: rc=2、`allowed=false`、refusals 4 件** =
  上の receipt refusal、`holdout-freeze-verify: FreezeError: …` (v1 `verify` の live scan)、`floor-null`、`budget-null`
  (`evidence/p3-gate-check.log`、log 末尾 07:25 JST)。runbook 140 行は「`holdout-freeze-verify:` で始まる拒否が混ざったら本物の
  破損」と読む条件を置いており、前 wave の P3 (拒否 2 件 exact) から変わった。
- 機序 (段 6 レビュー A が現物で検証): (a) `s8b_oracle_driver._make_gate_decision` (`:187-204`) は receipt 解決の `refusals` を
  無条件に merge し `allowed = not merged` とする。(b) `verify_receipt` は holdout を読めた場合に `_verify_holdout_live_scan`
  を呼び、`_assert_search_pass` (zero-hit) を要求する (`never-issued` は早期 return、hold による省略は無い)。(c) v2 の
  `launch_validate` (`s8b_ratified_freeze.py:3511-3548`) は closure 関連 artifact の occurrence から期待集合を導出し、全走査との
  完全一致を要求する (C2-4)。(d) `gate_check` (`:599`) と `run_block` (`:1318`) は v2 処理に先立って receipt を解決し、active v2
  による skip は無く、`run_block` はさらに `_campaign_t080_value` で invalid receipt を拒否する。**したがって現行 receipt・実装・
  hit を保ったまま A / X を追加しても、X1' を含む checkout では driver の gate は refuse される** (コード上の帰結。A / X 後の
  実測ではない)。T-080 (v1 移行 receipt) の live scan が zero-hit を要求し、v2 世代の closure hit を期待集合とする
  `launch_validate` と矛盾する、という構造の問題である。

**帰結:** D2120 項 2 (a) 択 1 (chain を main へ) を実行すると、受入全走が赤で land できず (本 wave と並行 wave (a) の
両方)、仮に載せても oracle は動かない。(a)+(b) だけでは 8b oracle 実走に到達しない。本 wave は **受入全走を投入せず、
land せず**、G を branch に保全して正式停止し、裁定パッケージ (`package.md`) を返す。test を弱めず (規律 2)、hold・除外は
変えていない。並行 wave (a) の session へは同じ事実を data として 1 回送った (07:26 JST、`SendMessage` の結果 success)。
再発防止は F862 の再発として failures 台帳へ記録し、memory
`~/.claude/projects/-work-1-SFC-tanab-izanagi/memory/chain-consequence-enumerate-real-root-consumers.md` (本 wave で作成) に
「凍結 / official 成果物を入れる帰結は ROOT 参照から列挙し、その木で 1 本実走してから裁定材料にする」を置いた。

## 5. 承認 A → active pointer X の手順 (2026-09-20 13:2x の裁定で AI 委任へ改訂。実施済み)

**改訂 (2026-09-20、[T-2724] wave `dev-wave-t2724-ax-delegated`):** 本節は起草時 (2026-09-18) には「人間手番 — AI は作らない」
だった。ユーザー裁定 2026-09-20 13:2x が D2120 項 2 (b) と D2174 項 4 を supersede し、A / X は AI が作ることになった
(決定台帳の同 wave fragment を参照)。批准側の attestation は「逐語 `AI-Agent: none`」から「記録済みの委任裁定 + `AI-Agent` trailer
ちょうど 1 行 (逐語 none または provenance 規約に適合する構造化 trailer)」へ改めた (`_assert_user_commit`、同 wave の実装 commit)。
実施形: 手順 2 と 4 の record は Codex author が同じ script 形で書き、commit は親 (Claude manager) が機械的に代行、message は
本文 + 空行 + Codex author の構造化 1 行 (`Co-Authored-By` 無し)。実施結果 = 承認 A `a3bf67a8c` (approval sha256 `3787d97b…`)、
active pointer X `70e87c9c9` (pointer sha256 `577537e2…`)、手順 6 の loader は JSON 1 行 (generation 1、sha `7e1114…`)。
一次資料は `output/insights/2026-09-20/t2724-ax-delegated/README.md`。以下の手順 1〜6 は実施の形として残す (「人間が」と
ある箇所は委任後は AI が実施する。手順 3 / 5 の trailer は「逐語 `AI-Agent: none`」ではなく規約適合の構造化 1 行)。

hook の Write 拒否は人間性の証明ではなく誤操作抑止である (hooks README)。以下は
**§4 の裁定 (`package.md`) が決着し、G と X1' を含む branch が main (または oracle を走らせる branch) に載った後**に、
その checkout の root で実行する。A と X の間に他の commit を挟まない。

1. 前提: `git status --porcelain --untracked-files=all` が空、`git merge-base --is-ancestor 32ba8cae45001697f050bee377413153e6d798a5 HEAD`
   と `git merge-base --is-ancestor cc82edc8c9f90a9ee659c2d27f71b75b19a56490 HEAD` がともに rc=0 (rc=1 は非祖先、それ以外は実行エラー)。
2. approval record を作る (canonical JSON = `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`、
   末尾改行なし。keys は `generation_sha256` / `approver` / `approved_at` / `scope` の 4 つちょうど。filename は generation の sha256)。
   `approver` は承認者の識別子 (下の例の `"user"` は起草時の形。委任後の実施では
   `user (delegated to AI by user ruling 2026-09-20 13:2x JST; supersedes D2120 item 2(b) and D2174 item 4)` を書いた)、
   `approved_at` は実際の承認時刻 (UTC、`YYYY-MM-DDTHH:MM:SSZ`)、`scope` は慣例値 `s8b-holdout`
   (test fixture `test_s8b_ratified_freeze.py:169-173` の値。批准側は値の書式を検査しない)。`output/s8b-freeze/` への Write は
   hook が拒否するので人間自身の shell / python で書く:

   ```bash
   python3 -B - <<'PY'
   import hashlib, json
   from datetime import datetime, timezone
   from pathlib import Path
   gen = Path("output/s8b-freeze/holdout_freeze.v2.g1.json")
   gen_sha = hashlib.sha256(gen.read_bytes()).hexdigest()
   assert gen_sha == "7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"
   doc = {"generation_sha256": gen_sha, "approver": "user",
          "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "scope": "s8b-holdout"}
   raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
   path = Path("output/s8b-freeze/approvals") / (gen_sha + ".json")
   path.parent.mkdir(parents=True, exist_ok=True)
   with path.open("xb") as f: f.write(raw)
   print(path); print("approval_sha256=" + hashlib.sha256(raw).hexdigest())
   PY
   ```
3. commit A: `git add -- output/s8b-freeze/approvals/7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06.json`、
   `git diff --cached --name-status` が `A` 1 件だけ。repo 外の message file (例 `/tmp/t2724-approval-message.txt`) の中身は
   本文 1 行 + 空行 + `AI-Agent` trailer ちょうど 1 行 (起草時は逐語 `AI-Agent: none`。委任後の実施では Codex author の
   構造化 1 行 `AI-Agent: product=codex; model=…; reasoning=…; role=author; scope=approval-record`) だけ
   (他の `AI-Agent` 行・`Co-Authored-By` は書かない)。
   `python3 tools/check_ai_provenance.py --message-file <file>` rc=0 → `git commit -F <file>`。確認:
   `git rev-list --parents -n 1 HEAD` (親 1 件)、`git diff-tree --no-commit-id --no-renames --name-status -r HEAD` (`A` 1 件)、
   `git show -s --format=%B HEAD`。A の SHA を控える。
4. pointer record を作る (keys `generation_number` / `path` / `sha256` / `parent_active_sha256` / `approval_sha256` ちょうど、
   genesis なので `parent_active_sha256` は JSON `null`、`approval_sha256` は **approval bytes** の sha256、filename は
   **pointer 自身の canonical bytes** の sha256):

   ```bash
   python3 -B - <<'PY'
   import hashlib, json
   from pathlib import Path
   gen_path = "output/s8b-freeze/holdout_freeze.v2.g1.json"
   gen_sha = hashlib.sha256(Path(gen_path).read_bytes()).hexdigest()
   assert gen_sha == "7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"
   approval_sha = hashlib.sha256((Path("output/s8b-freeze/approvals") / (gen_sha + ".json")).read_bytes()).hexdigest()
   doc = {"generation_number": 1, "path": gen_path, "sha256": gen_sha,
          "parent_active_sha256": None, "approval_sha256": approval_sha}
   raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
   ptr_sha = hashlib.sha256(raw).hexdigest()
   path = Path("output/s8b-freeze/active") / (ptr_sha + ".json")
   path.parent.mkdir(parents=True, exist_ok=True)
   with path.open("xb") as f: f.write(raw)
   print(path)
   PY
   ```
5. commit X: 表示された path だけを `git add`、message file は A と同じ形 (本文 + `AI-Agent` trailer ちょうど 1 行。委任後は
   `scope=active-pointer` の構造化 1 行)、preflight rc=0 →
   `git commit -F`。確認: `git rev-list --parents -n 1 HEAD` の親が **A ちょうど 1 件**、diff が `A` 1 件、
   `git status --porcelain --untracked-files=all -- output/s8b-freeze` が空。
6. 検証 (repo 外の script、H = 実行時の HEAD)。次を `/tmp/verify-t2724-active.py` に保存し、repo root で
   `python3 -B /tmp/verify-t2724-active.py "$PWD"` を実行する。rc=0 で JSON 1 行が出れば批准成功、例外なら
   `RatifiedFreezeError.reason` を記録する。

   ```python
   import json, sys
   from pathlib import Path
   root = Path(sys.argv[1]).resolve()
   sys.path.insert(0, str(root))
   from orchestrator.campaign import s8b_ratified_freeze as M
   resolution = M.resolve_active_generation(root)      # 構造 (record / 履歴 / 承認連鎖 / pointer)
   ratified = M.load_ratified_freeze(root)             # 内容 (V1a〜V1d / 投影 / V2 / V3 層 1)
   assert resolution.generation_number == ratified.generation_number == 1
   assert resolution.activation_head == ratified.activation_head
   assert resolution.generation_sha256 == ratified.sha256
   assert ratified.sha256 == "7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06"
   print(json.dumps({"head": resolution.activation_head, "generation_commit": resolution.generation_commit,
                     "generation_sha256": ratified.sha256, "approval_sha256": resolution.approval_sha256,
                     "pointer_sha256": resolution.pointer_sha256}))
   ```

   その後 `python3 tools/check_ai_provenance.py` (全史監査、計算ノードへ dispatch されうる。rc=16 は dispatch 失敗)。

失敗の読み方: A だけの時点で `no-active` は未発効として期待どおり、X の後の `no-active` は失敗。`generation-commit-*` (G の
provenance)、`history-mutated` / `multiple-introduction` (namespace の履歴)、`frozen-at-head-mismatch` (V1a)、`closure-dirty`
(V1d、作業木 ≠ H)、`floor-source-projection-mismatch`、`approval-commit-diff` / `pointer-commit-diff` (A / X の diff が 1 file
でない)、`pointer-approval-parent` (X^ ≠ A)、`user-commit-trailer` (`none` 逐語でない) はそれぞれ別の拒否理由で、reason 名で
直す場所が決まる。provenance checker の rc=16 は dispatch 失敗であって監査結果ではない。**loader 成功は批准の成功であって、
oracle 実走の全条件ではない** — §4 の T-080 receipt live scan の矛盾 (裁定で択 A 系を採り production 側の整合が着地して
いれば解消) と W-4 の spec 承認 (T-750 P-1) が残る。

## 6. 到達範囲と非保証

- G は作成済み・merge 済み・**未 land**。A / X・approvals/・active/ は作っていない。批准の完全経路 (`load_ratified_freeze` 成功)
  は A / X 後にしか実測できない。§3 は個別関数の診断で、合成 `ActiveResolution` は作っていない (V2 だけ probe 専用 namespace)。
- §4 の 45 red は同一 tip の 1 走。(iii) 29 node の帰属は共有 memo の機序 (`_campaign_t080_value` の拒否) と receipt 解決の
  実測から導いたもので、clean な木での対照走はしていない。「G が全 test に無影響」も対照走なしでは主張しない。受入全走は
  投入していない (赤が確定しているため)。
- 三軸走査・T-080 receipt 解決・P3 はすべて wave 木 (H = `88d020466`) で測った値で、別 checkout へ一般化しない。
- hash 一致 (blob oid + sha256) は「裁定済み X2 の bytes を変更せず採用した」ことの証拠で、producer からの生成過程の証明ではない。
- 実装面の差分はゼロ (`git diff --name-only d2ebef7a4..88d020466 -- orchestrator tools hooks .github .codex external patches` = 0 件)。
  変異 matrix は免除 (DW-S04)。批准側・走査除外・hold・test・hook は 1 byte も変えていない。
- 並行 wave (a) と本 wave は旧 main `d2ebef7a4` から独立に X1' を merge しているので、後発の land は merge-base 2 つで rc=23
  になりうる (段 3 B-1)。後発は先発の fold 後 main を固定 SHA で merge してから受入を取り直す。

## 7. 検査

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff` (wave 木) / `--mode midflight` (G 用木) | rc=0 / rc=0 |
| author 自己検証 (sha256 / hash-object / bytes / mode / cmp / status) | 全一致 (§2) |
| G: `check_ai_provenance.py --message-file` (現行 checker、G 用木 checker) / `--range HEAD~1..HEAD` (G 用木、request 4992.nqsv) | rc=0 / rc=0 / rc=0 |
| merge: preflight rc=0、未解決 0、namespace clean、実装面差分 0 | ok |
| probe (`evidence/g1-gen-probe.json`) | 全項目 ok、`no-active` |
| 三軸走査 (wave 木) | rc=1、hit = X1' run_dir 3 path × 2 holdout、世代文書は非 hit (`evidence/search-projection.json`) |
| 焦点走 6 file (計算ノード request 5001.nqsv) | **45 failed / 967 passed / 11 skipped、rc=1** (§4、`evidence/focus-1-summary.txt`、`evidence/failure-table.txt`) |
| T-080 receipt 解決 (wave 木、login) | `state=invalid`、`holdout.unknownness_layer2` (407 秒) |
| runbook §2 P3 gate-check (wave 木) | rc=2、`allowed=false`、refusals 4 件 (`evidence/p3-gate-check.log`) |
| 受入全走 | **投入せず** (赤が確定。赤の受領証は取らない) |
| 三軸走査 (insight + fragment だけを files 注入) | hit 0、rc=0 (job dir `scan_insight.py`) |
| `check_docs.py` / `spool_fold.py --dry-run` (記録 commit 前) | rc=0 / rc=0 (planned、fragment 2、allocations 2)。commit 後に再走して worklog fragment 本文の値を確定 |
| 段 6 レビュー | A (正しさ) must-fix 3 / should 2、B (記録) must-fix 3 / should 3 — すべて採用して本文を訂正 (§9) |

## 8. 収録物

- `package.md` — 裁定パッケージ (択 A〜D、親の推奨は A)
- `evidence/g1-gen-probe.json` — §3 の probe 出力 (path・hash・reason のみ)
- `evidence/search-projection.json` — 三軸走査の射影 (hit path と件数のみ、検索式なし)
- `evidence/g-commit-message.txt` / `evidence/g-commit.log` — G の message と親の commit runner の log。`g-commit.log` は原文
  (job dir、sha256 `bfc3c5a0075c47e566caadf474453cc239501160466632176316d699852ba0c5`、5,779 bytes) の 62 行目 `| ` の末尾空白 1 byte を
  `git diff --check` のため除いた可逆最小正規化 (可視文字不変、5,778 bytes)。復元は 62 行目末尾に空白 1 つを戻す
- `evidence/focus-1-summary.txt` — 焦点走の FAILED 行と集計行
- `evidence/failure-table.txt` — 45 node ごとの最初の assertion 本文 (計算ノード完全出力から射影、job dir `failure_table.py`)
- `evidence/p3-gate-check.log` — P3 の JSON 出力 (hold marker 行は除いた)
- `evidence/consult-a-correctness.md` / `evidence/consult-b-sequencing.md` — 裁定相談 (ユーザー委任「codex に相談して決めて」、
  2026-09-18 09:15〜09:18 JST) の逐語。原文 (job dir `artifacts/…/s10-a.md` sha256 `9ac397471ef042f3f218d461d5095a72f5b21b2d46a4412993d045d7b36652fa`
  11,135 bytes、`s10-b.md` sha256 `d18a2fde3d1842c6f3ca21757e8b168c7be97496916eda263f219b0c256a45b7` 11,877 bytes) の行末空白
  (Markdown の強制改行 2 空白、a: 82・83 行、b: 3・8・26・33・38 行) を `git diff --check` のため除いた可逆最小正規化 (可視文字不変、
  11,131 / 11,867 bytes)。復元は当該行末に空白 2 つを戻す。裁定は `package.md` 末尾「裁定」節と decisions fragment
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-g1-gen/` — brief、裁定、prompt、子の成果物 (`artifacts/`)、
  runner script、probe script、生 log (repo には入れない)

## 9. 段 6 レビューの所見と是正

| ID | 分類 | 所見 | 是正 |
|---|---|---|---|
| RA-1 / RB-1 | must-fix | 45 red の内訳「16 / 5 / 24」が FAILED 行と合わず、(iii) の停止箇所も `_gate_check_validated` を置換した後の `_campaign_t080_value` | 計算ノード完全出力から node ごとの assertion 本文を表にし (`evidence/failure-table.txt`)、§4 を 10 / 5 / 29 / 1 の 4 経路に書き直した |
| RA-2 | must-fix | 択 A-1 の「候補または active」+ exact bytes 束縛では、未批准候補 (data) が期待集合 (authority) を定める形になりうる (規律 6) | `package.md` を書き直し、期待集合は承認済み (active) 世代の artifact から occurrence 検証で導出する (`launch_validate` と同じ規則) と限定、候補 data による gate 緩和は不採用 |
| RA-3 | must-fix | 択 A-2 は receipt の何を残し何を置換するか未定義、「設計 → author → 変異 → 新 D」は裁定を後置 | 択 A-3 (receipt の静的検証と epoch 束縛は維持し、重複する未知性層 2 だけを承認済み v2 の full launch validation へ委譲) を追加、設計案の起草 (AI) と裁定後の実装を分けた。「唯一の択」の表現を削除 |
| RA-4 | should | 「G 起因の赤は 0」は証明範囲超え。allowlist は `_CHAIN_RECORD_PATTERNS` で世代文書名を受理 | §4 を「確認した走査 refusal は X1' の 3 path 由来」に限定し、allowlist の静的根拠を追記 |
| RA-5 | should | probe は不一致で exit code を失敗にしない診断 script | §3 に明記 |
| RB-2 | must-fix | 新規 F は F862 (実 repo を読む test は登録簿にあると仮定した) と同型 | failures fragment を `再発` → `### F862` に変更、worklog の参照を F862 に |
| RB-3 | must-fix | §5 手順 6 の検証 script が実行可能な形で無い (`generation_sha256` と `sha256` の対象も明示) | 実行可能な script を掲載 |
| RB-4 | should | 「(A) の設計 wave は AI 手番で着手できる」が無条件に読める | `package.md` と worklog の新規 T を「人間が択 A 系を採った後」に条件付け |
| RB-5 | should | 前 wave の記述を「赤になるのは 2 本」と排他的に引用 | 「held 2 本を記録したが非 held と production への波及を列挙していなかった」に訂正 |
| RB-6 | should | 恒久対応 memory の所在が README に無い | §4 末尾に memory の path と作成事実を記録 |

両レビューとも G の実体照合 (親・diff・mode・blob・sha256・trailer) と、中心結論 (X1' を含む checkout では production gate が
refuse し A / X だけでは解消しない) を支持した。fix はすべて docs (README / package / fragment) で、実装面は触っていない。
