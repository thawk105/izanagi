# 段 4 裁定 — [T-1418] (2026-09-27 JST、base ad114fba0、main 不変を確認済み)

入力: out/s2-plan.md (plan)、out/s3-sol.md (正しさ境界、NO-GO)、out/s3-luna.md (過剰・削除、条件付き GO)。裁定 inbox: wave 開始後の main 進行 0 commit・decisions 追加なし。

## 所見の裁定

| 所見 | 裁定 | 採否・扱い |
|---|---|---|
| sol-1 clean な残留 M を fresh が H として受理 | real | 採用。file-swap の残留は dirty tree で既存検査が拒否するが、commit モードは tree が clean になりこの保護が外れる (DW-M05 同等性の欠落)。**HEAD commit の author email が harness の固定 identity なら、モード不問で fresh / resume / plan-only とも起動前 fail-closed。** |
| sol-2 runner が M を読んだ証拠 | 一部 real | 採用: runner 直前と runner 直後 (復元前) に HEAD==M・detached・touched bytes==M blob を検査し、崩れていたら fail-closed。不採用 (scope 外): 計算ノード側の観測証拠の束縛。dispatch は repo_root の path に cd するだけ (dispatch_compute.py:3755/1125/1455) で、既定 file-swap も同じ前提に立つ。実 dispatch の dogfood で到達を実測する。|
| sol-3 plan の M2 は単一理由でない | real | 採用。matrix を下記に組み直す。|
| sol-4 commit 固有の誤 KILLED | real (should) | 採用: dogfood と matrix の各赤は失敗理由 (assertion 本文) を読んで受理集合の変化到達を記録。等価対照は同一 file・同一 runner argv で置く。|
| sol-5 H / M / その他の状態判別、復旧文言 | real | 採用。下記「復元」。|
| sol-6 「残らない」の主張が強い | real | 採用: 主張は「branch ref を動かさない」に限定。dogfood は detach した非 shared 独立 clone (DW-M07) で行う。|
| sol-7 偽 runner は本物の閉包検査を通らない | real | 採用: unit test は git 注入の検査と位置づけ、閉包の実体は実 dispatch dogfood を受入条件にする。|
| sol-8 / luna-11 brief の「HEAD 以外の束縛は無い」 | real | 採用: 「新規 capture 経路は現 HEAD に束縛。既存 v2 lock の検証は lock 記録 commit に束縛 (ident.py:388) で、commit モードでも drift が残る」と限定し、insight に適用範囲として書く。|
| luna-1 復元直前にも detached を確認 | real | 採用。|
| luna-2 最小安全境界 | 同意 | 採用。|
| luna-3 v5・M SHA・object 再検証は不要 | real | 採用: **ledger は v4 のまま**。commit モードは procedure の `source_policy` / `restore_policy` を別の固定文言にし、既存の完全一致照合で resume をモードに束縛。M SHA は台帳に載せない (injection_diff_sha256 + repo_head で木は決まる)。|
| luna-4 wrapper 中継 | real | 採用: wrapper・fanout は変更しない。commit モードは harness を detached の独立 clone へ直接当てて使う。|
| luna-5/6 test・変異の二重計上 | real | 採用。下記の統合 test・matrix。|
| luna-7 同モードで通る resume、attached 拒否の対 | real | 採用。|
| luna-8 E1 の重複 | real | 採用: E1 (harness 変異としての等価) は置かない。等価対照は dogfood の閉包 file コメント変異だけ。|
| luna-9 docs 記録を削る | refuted (一部) | DW-S07 は worklog / insight / decisions の記録を必須とし、failures の恒久対応は routing 規則 (skill-self-improvement §routing 1・5) の行き先。mutation.md への追記は行わない (L1.5 予算・本題外)。記録は fragment のみ。|
| luna-10 相談・review 本数 | refuted | DW-S06-A は実装 wave に review 2 本を要求。正しさ計器の変更なので維持。|
| plan の `-c core.hooksPath=/dev/null` | 不採用 (親) | git hook は未設定。hook を無効化せず、hook が commit を変えた場合は post-commit 検査が fail-closed で止める。`-c commit.gpgsign=false` と固定 identity の `-c user.name/user.email` だけ付ける。|

## plan v2 (実装子への指示の正本)

所有 file: `tools/mutation_harness.py`、`orchestrator/tests/test_mutation_harness.py` のみ。規模上限: harness 追加・変更 350 行、test 追加 550 行。

1. CLI `--inject {file-swap,commit}` 既定 file-swap。既定の挙動・ledger bytes・既存 test の期待値は不変。
2. 起動前 (lock 取得後、source 読取り前): (a) モード不問で HEAD commit の author email が harness identity (`mutation-harness@invalid`) なら拒否。(b) commit モードは `git symbolic-ref -q HEAD` が「非 0 かつ git エラーでない」(= detached) を要求。plan-only も同じ検査まで。
3. 1 変異 (commit): 既存の注入・read-back・pycache purge・`_assert_only_expected_dirt(H)` → `git -c user.name=izanagi-mutation-harness -c user.email=mutation-harness@invalid -c commit.gpgsign=false commit --quiet --only -m "mutation-harness: <id>" -- <touched>` → M を取得し、親がちょうど H、`diff --name-only H M` == touched、`M:<rel>` の bytes == 注入 bytes、status porcelain (untracked・submodule 含む) 空、detached、を検査 → runner → 直後に HEAD==M・detached・bytes==M blob を検査 → 復元。
4. 復元 (`_defer_cleanup_signals` の内側): HEAD を読み直し、detached でなければ ref を動かさず fail-closed。HEAD==H なら touched を `restore --source=H --staged --worktree`。HEAD が「親==H かつ author==harness identity」の commit なら `reset --soft H` の後に同 restore。それ以外は上書きせず fail-closed (手動復旧の報告)。最後に `_verify_originals`、H blob との bytes 一致、index/作業木 clean、`_assert_head(H)`。
5. dispatch orphan hold (既存 `_dispatch_orphan_stop` / hold 検出): commit モードは HEAD=M・bytes=M blob・clean を保持して停止。sidecar の source_state は commit 専用値、復旧文言は「job 終端確認 → HEAD と bytes の確認 → reset --soft H + restore → clean/HEAD 確認 → hold と sidecar 削除」。hold 除去後に M のまま起動すると 2(a) で拒否される。
6. ledger: v4 のまま、commit モードだけ `source_policy` / `restore_policy` を commit 用固定文言にする。resume は既存の完全一致でモードを束縛。

## test (統合版、所有 file に追加)

- T1 commit 注入の対照: 偽 runner が「作業木 bytes == HEAD blob」でなければ赤 (drift 模擬)。file-swap の等価変異は赤、commit の等価変異は SURVIVED、commit の値変異は狙いの node だけ KILLED。
- T2 attached HEAD は plan-only・実走とも runner 前に拒否、branch ref 不変。
- T3 post-commit 境界: commit 手順を差し替えて作った M を、(i) 余分な path を含む (tree clean)、(ii) 親が H でない (tree は同一)、(iii) touched の blob が注入 bytes と違う、の 3 例で runner 前に拒否。各例は他の 2 条件を満たす単一理由 fixture。
- T4 復元: 正常・非 0 rc・local timeout で HEAD==H、bytes==H blob、index/作業木 clean、detached 維持、branch ref 不変。
- T5 復元直前に HEAD が attached になっていたら ref を動かさず停止。
- T6 runner 中の signal で復元。
- T7 dispatch orphan hold で HEAD=M を保持、以後の fresh/resume は拒否、手動復元後の同モード resume は通る。
- T8 resume のモード不一致 (file-swap ledger を commit で、その逆) は拒否。
- T9 残留 M (HEAD が harness identity の commit、tree clean) で fresh 起動を拒否 (モード不問)。

## 変異事前登録 (DW-M01。anchor の逐語と期待 node は実装後に probe で確定し spec 化)

| ID | 位置 (新コード) | 期待する赤 |
|---|---|---|
| M1 | 起動前の detached 要求を外す | T2 |
| M2 | post-commit の changed-path 一致検査を外す | T3(i) |
| M3 | post-commit の親 == H 検査を外す | T3(ii) |
| M4 | post-commit の blob 一致検査を外す | T3(iii) |
| M5 | 復元直前の detached 再確認を外す | T5 |
| M6 | commit モードの orphan hold を通常復元へ倒す | T7 |
| M7 | 起動前の harness identity 検査を外す | T9 |
| M8 | commit モードの policy 文言を file-swap と同一にする | T8 |

category は全件 negative。単一理由性は probe で確認し、崩れたら DW-M01 に従い再照準。

## dogfood (完了判定、実 dispatch)

- 置き場: 最終実装 commit を main にした独立 clone を `checkout --detach` (DW-M07・D1009)。
- 対象: `orchestrator/campaign/loop.py` (閉包 member)。V = `source_options["sort_oracle_contract_id"]` への転送を止める (loop.py:811-814 の if を偽にする)。E = 同 file へのコメント 1 行。
- runner: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_p3_s4_loop_sort.py -k forwards_one_sort_contract -q -rf`。
- 期待: file-swap の E は drift 赤 (mask の実測)、commit の E は SURVIVED、commit の V は owner `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate` だけで KILLED。各赤は assertion 本文を読んで理由を記録。probe (全件 SURVIVED 期待) → final の順。

## erratum 1 (段 5 走行中、実行前に訂正。DW-O12)

dogfood と変異 matrix の置き場を「独立 clone」から **主 repo に登録した detached worktree** (`.codex/worktrees/t1418-mut`、統合 commit を `worktree add --detach`、`dev_wave_submodule_init.py` で初期化) へ変える。
理由: 新規 clone は submodule の URL が非 local で初期化 tool に拒否される (memory mutation-discipline 2026-09-20 節)。wrapper は並行 churn で共有木検査が破れるので使わず、harness を `--repo <mut-tree>` へ直接当てる (DW-M05 の正本経路)。
harness は wave worktree 側の実物 (`python3 <wave>/tools/mutation_harness.py`) を使う。`_tool_identity` は `--repo` 外の harness を HEAD 照合しないので、mut-tree 側の harness file を変異させても実行中の harness は変わらない。
これに伴い sol-6 の主張の限定は「branch ref を動かさない」だけにする (変異 commit object は共有 object store に gc まで残る。reflog は mut-tree の HEAD reflog に残り、木の撤去で消える)。

## 研究前進・成果物影響 (再確認)

閉包 member (loop / pipeline / p3_s4_loop / verifier) を変える wave の変異台帳で、値の層を見ない KILLED が正しさ gate の歯の証拠に数えられる状態を解く。
