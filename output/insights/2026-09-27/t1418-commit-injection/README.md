# [T-1418] 変異 harness の commit 注入モード — contract-loader 閉包の member を値の層で変異検査する (2026-09-27)

依頼の逐語: `verbatim/request.md`。段 1 brief・段 4 裁定 (erratum 1 を含む)・段 6 裁定・Codex 子の出力はすべて `verbatim/` に置いた。
設計判断は同 wave の decisions fragment `docs/spool/decisions/2026-09-27-worktree-dev-wave-t1418-closure-mutation-2.md` (land 時の fold で `docs/decisions.md` の D になる。題「contract-loader 閉包の member を変異させるときは、変異 harness の commit 注入モード (`--inject commit`) で走らせる」)、F424 の記述訂正は同 wave の failures fragment の supersede 追記。

## 1. 何が問題だったか

`orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` (96 path。loop.py・pipeline.py・p3_s4_loop.py・wal.py・ident.py・verifier など) の file を
`tools/mutation_harness.py` の既定方式 (作業木へ未 commit で注入する file-swap) で変異させると、`orchestrator/campaign/ident.py` →
`contract_loader_binding.capture_contract_loader_binding` の一致検査 (現 HEAD の blob と disk bytes) が変異の中身と無関係に先に落ちる。
owner test の赤が「値の層で検出した」のか「drift で落ちた」のかを区別できず、各 wave は変異を commit した木を手で作って確かめていた (F424、T-2632・T-2849・T-2850)。

F424 の記述のうち「`ratified_enforcement_source` fixture が disk==HEAD blob を要求する」は古い。同 fixture は b4ff38f6b (2026-08-27) で no-op になっている。

## 2. 何を足したか (実装 commit 6d2e14cdb + fix 54d472756)

- `--inject {file-swap,commit}` (既定 file-swap)。commit モードは detached HEAD の木でだけ起動し、1 変異ごとに注入 bytes を固定 identity (`mutation-harness@invalid`) の一時 commit M にして runner を走らせ、終了後に固定 HEAD H へ戻す。branch ref は動かさない。git hook は無効化しない。
- runner の前: M の親がちょうど H、H..M の変更 path == touched、M の blob == 注入 bytes、作業木 clean、detached を検査。
- runner の後: dispatch の orphan 判定を先に行い、hold なら M を保持して停止 (復旧文言は commit 用)。hold でなければ HEAD==M・detached・bytes==M blob を再検査してから記録。
- 復元: detached を再確認し、HEAD==H なら touched を `restore --source=H`、HEAD が「親==H かつ author==harness identity」の commit なら `reset --soft H` の後に同 restore。それ以外は上書きせず停止。
- 起動時: HEAD の author email が harness identity なら、モード不問で fresh / resume / plan-only を拒否 (kill で残った M を固定 HEAD として受理しない)。
- ledger は v4 のまま。commit モードだけ `source_policy` / `restore_policy` の文言を変え、既存の完全一致照合で resume をモードに束縛。
- 変えていないもの: 閉包の一致検査・fixture・ident・contract_loader_binding・campaign_lock、既定 file-swap の挙動と ledger 文言、wrapper (`tools/mutation_worktree.py`・`tools/mutation_fanout*.py`)。

## 3. 使い方

detached の木 (主 repo に登録した worktree を `git checkout --detach`、または detach した独立 clone) へ harness を直接当てる。

```
python3 tools/mutation_harness.py --repo <detached worktree> --spec <spec> --expected-spec-sha256 <sha> \
  --out <out> --attempt-out <attempt> --wrapper-attempt 1 --runner-mode dispatch --inject commit --detached -- \
  python3 tools/run_tests.py --force-dispatch <test file> -k <expr> -q -rf
```

## 4. 実測 — dogfood probe (閉包 member の loop.py、commit 6d2e14cdb、変異用 worktree `.codex/worktrees/t1418-mut`)

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_p3_s4_loop_sort.py -k forwards_one_sort_contract -q -rf`。
E = loop.py の `source_options = {}` 行末へのコメント (等価)。V = `source_options["sort_oracle_contract_id"]` への転送の if を偽にする (値)。
owner = `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate`。両走とも全件 SURVIVED 期待の probe で、観測をそのまま書く。

| 走 | 時刻 (JST) | baseline | E | V |
|---|---|---|---|---|
| file-swap | 15:26–15:29 | PASSED | owner 赤。理由 `contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/loop.py` | owner 赤。理由は E と同じ drift |
| commit | 15:30–15:35 | PASSED | 赤 0 件 (SURVIVED) | owner だけ赤。理由 `KeyError: 'sort_oracle_contract_id'` (test_p3_s4_loop_sort.py:1485、resolver へ転送された kwargs に値が無い) |

file-swap では等価変異まで drift で owner を落とし、V の赤も drift だった (値の層が見えない)。commit モードでは等価変異が生き残り、V は値の層の assertion で落ちた。
両走の後、変異用 worktree の HEAD は 6d2e14cdb・作業木 clean だった。ledger の policy は commit 用の文言が記録された。

## 5. 実測 — harness 自身の変異 probe (commit 54d472756、file-swap で tools/mutation_harness.py を変異)

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_mutation_harness.py -q -rf`。実行した harness は wave 側の実物 (sha256 f46a9c98…、`--repo` の外なので HEAD 照合の対象外) で、変異用 worktree の同 file と同じ bytes。15:37–16:20 JST、baseline PASSED。

| ID | 外した検査 | 赤になった test (狙い以外の赤は全件 0) |
|---|---|---|
| M1 | 起動前の detached 要求 | `test_commit_attached_head_rejected_before_runner` [True] [False] |
| M2 | commit 後の変更 path 一致 | `test_commit_post_commit_boundary_rejects_single_defect[extra-path]` |
| M3 | commit 後の親 == H | 同 `[wrong-parent]` |
| M4 | commit 後の blob 一致 | 同 `[wrong-blob]` |
| M5 | 復元直前の detached 再確認 | `test_commit_restore_refuses_attached_head_without_moving_branch` |
| M6 | commit モードの orphan hold 保全 | `test_commit_dispatch_orphan_hold_precedes_post_runner_blob_check`、`test_commit_orphan_hold_preserves_m_then_manual_resume` |
| M7 | 起動前の残留 harness commit 拒否 | `test_residual_harness_commit_rejected_before_runner` の 8 組 |
| M8 | commit モードの policy 文言 (file-swap と同一にする) | `test_resume_rejects_injection_policy_mismatch` [file-swap-commit] [commit-file-swap] |
| M9 | runner 後の再検査 | `test_commit_rejects_runner_drift_before_record` [bytes] [head] |

## 5b. 実測 — final (commit 54d472756、期待 node = probe の観測集合で事前登録)

同じ変異用 worktree で直列に 3 走。spec と結果は `mutation/` (`harness-spec-final.json` → `harness-final1.json`、`dogfood-spec-final-commit.json` → `dogfood-final1c-commit.json`、`dogfood-spec-final-fileswap.json` → `dogfood-final1f-file-swap.json`)。

| 走 | 時刻 (JST) | baseline | 結果 (期待との完全一致) |
|---|---|---|---|
| harness 自身の変異 M1〜M9 (file-swap) | 16:22–16:51 | PASSED | KILLED 9、matching 9/9 |
| dogfood commit モード | 16:52–17:10 | PASSED | E SURVIVED (赤 0)、V KILLED (owner 1 node)、matching 2/2 |
| dogfood file-swap | 17:10–17:13 | PASSED | E KILLED・V KILLED (どちらも owner 1 node、drift)、matching 2/2 |

final の KILLED record は失敗本文の末尾を保存しない (harness は MISMATCH / PARSE_ERROR のときだけ保存する) ので、赤の理由は §4 の probe (同じ変異・同じ runner argv) で読んだものを根拠にする。
3 走とも走行後の変異用 worktree は HEAD 54d472756・作業木 clean。commit 走の ledger の `source_policy` は commit 用、file-swap 走 2 本は既定の文言だった。

完了判定 (brief): (a) 閉包 member のコメント変異が drift で落ちず SURVIVED、(b) 同 file の値変異が owner test だけで KILLED、を実 dispatch で満たした。

## 6. レビューと裁定

- 段 3: 正しさ境界レンズ NO-GO (must-fix: 残留 M を fresh が受理、runner が M を読んだ証拠、plan の変異案の単一理由性)、過剰・削除レンズ条件付き GO (v5 ledger・wrapper 中継・M SHA 台帳は削れる)。段 4 で採否を裁定 (`verbatim/s4-ruling.md`)。
- 段 6: レビュー 2 本とも NO-GO、共通 must-fix = runner 後の再検査が orphan 判定より先 → fix 1 巡で順序を入れ替え。runner 後検査の負例と、復元直前の検査だけに届く test を追加 (`verbatim/s6-fix-ruling.md`)。
- 焦点再レビュー: 7 所見中 closed 4・裁定で直さない nit 2・partial 1。partial は「`[head]` の負例が HEAD と bytes を同時に変えるので HEAD 照合単独の検出を示せない」(should)。親裁定で fix 巡を足さない: M9 (再検査ブロック全体) は `[head]` `[bytes]` の両方で検出され、HEAD だけが動き touched bytes が一致する状況は runner (`tools/run_tests.py`) が HEAD を動かさない以上、成果物影響を示せない (DW-G05)。backlog。
- 直さなかった nit: policy 文言・復旧文言の重複 (3 箇所)、残留検査 test の 8 組の直積。

## 7. 適用範囲と限界

- commit モードが外すのは新規 capture 経路 (現 HEAD に束縛) の drift だけ。既存の v2 campaign.lock を検証する経路は lock に記録された commit に束縛されるので (ident.py の `verify_against_lock`)、固定 commit の lock を使う test は commit モードでも drift で落ちる。
- commit モード固有の赤 (HEAD commit の SHA・author・message を読む test) は等価変異の対照で測る。本 dogfood では等価変異の赤は 0 件だった。対照は同じ file・同じ runner argv ごとに置く。
- 変異 commit object は共有 object store に gc まで残る。主張は「branch ref を動かさない」に限る。
- 計算ノードが M の木を見る根拠は、dispatch が request の repo_root path へ cd して走る実装 (tools/pegasus/dispatch_compute.py) と、上の dogfood で V が値の層で落ちた観測である。ノード側の HEAD を記録へ束縛する機構は足していない。

## 8. 逐語写しの正規化 (DW-S07)

`verbatim/codex/s6-review-b.md` だけ、`git diff --check` に当たる行末空白を除いた (可視文字は不変)。
原文 sha256 = 6dbc2df96d1f56f06633335320270bce60d8e44c38d7cdaa12c2f37b06abfb2c (6419 bytes)、正規化後 = 86947fb5f066a176ab33a33a0f59bd36317daf248e0b3a96041a0701e8c28ce1 (6407 bytes)。
除いたのは 3・6・9・12・15・18 行目の行末の半角空白 2 個ずつ (計 12 bytes、Markdown の強制改行)。復元はこの 6 行の行末へ半角空白 2 個を足す。

## 9. scope 外にしたもの

- T-458 / T-626 (D2172 項 10 で「次に同 file を触る wave で相乗り」) は、ユーザー指示「本題の実装だけ」により相乗りしていない。
- wrapper / fanout への `--inject` 中継、ledger v5、変異 commit SHA の台帳記録。
