# dev-wave の land 後に worktree・branch が残る問題の原因と対策 (2026-09-29〜30)

authority: none / default_effect: no-state-change (記録。可変状態の正本は worklog 末尾と現行 phase doc)

- 依頼 (ユーザー逐語): 「dev-waveをした後に、local mainにland成功しつつワークツリーやブランチを掃除せずに終了するやつが多いせいで、ワークツリーやブランチのごみが溜まりやすい。改善してくれ」
- wave branch: `worktree-dev-wave-land-cleanup-enforce`。段構成: 段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本 + 焦点再レビュー 1 本 (撤去の受理集合を広げるので軽量版にしなかった)
- 逐語: `verbatim/` (brief、調査報告、plan、相談 2 本、段 4 裁定、実装子報告 2 本、レビュー 2 本、段 6 裁定、fix 報告、焦点再レビュー、Stop hook probe)

## 1. 実測した原因

2026-09-29 に land した wave 約 35 本の Claude Code transcript を調査子 (sonnet) が集計し、親が撤去 tool の現物 (`tools/dev_wave_cleanup.py` の統合判定) で照合した (`verbatim/investigation-report.md`)。9/27〜28 は未精査で、以下の件数はこの母集団に限る。

| 原因 | wave 数 |
|---|---|
| 子木の `remove-child` が rc=20 (fix 巡の途中版の木は所有 path が main と不一致、repo に入れない probe・作図の木は所有 path が空で、統合証明が構造的に不成立) | 約 10 |
| 撤去中に他 wave の land で main が進み rc=30 (`main changed since integration proof`) | 4 |
| wave 本体が rc=20 (amend 前 commit が branch reflog に残る) | 3 |
| 並走の land 調整役の撤去許可 (`CLEANUP OK`) を待って止まった | 2 |
| land 後に撤去を呼ばず `result:` で終了 (1 本は終了時に wave 木内、1 本は ExitWorktree で main に戻っていた) | 2 |
| manifest に登録しない補助木 (integ・run・smoke・verify、1 wave で 14 本) | 1 |
| 作業ツリー隔離のガードで撤去本体が撃てなかった | 0 |

wave 本体の木はおおむね撤去されていた。残骸の主成分は Codex 子木で、fix 巡ごとに新しい木を作る運用 (1 wave で `git worktree add` 25〜31 回) が、契約 (`DW-S05-A` の「同木で branch を切り再登録」) とも食い違っていた。

## 2. 変更

- `tools/dev_wave_cleanup.py remove-child`: 統合証明が不成立でも、wave 木が land 済み (HEAD が main 祖先)・子の reflog 上の commit がすべて main / 子 branch tip / 他の既存 branch から届く・per-worktree ref が main 非到達 commit を指さない・既存の退避検査を全部通る、のときは `integration_basis="archived-unintegrated"` で撤去する (子 branch tip が main 非祖先なら history.bundle を作り `bundle verify`)。wave の条件は証明時・削除直前・admin 再検査の 3 か所で確かめる。
- 統合証明の後に main が前進しただけなら撤去を続ける (巻戻し・分岐は拒否のまま)。
- 子 branch の削除を期待 OID 付きの `update-ref -d` にした。
- Stop hook `tools/dev_wave_cleanup_stop_hook.py` (`.claude/settings.json` に timeout 10 秒で配線)。本体を `hooks/` の外に置いた理由は `hooks/README.md` hook 5 節。
- docs: `DW-O28` (退避経路と「証拠 dir は job 後も残る所に」、996/1000 bytes)、`DW-S05-A` (補助・probe 木も登録、fix は同木・同 branch)、`hooks/README.md` hook 5 節。
- 判断の記録は decisions fragment、再発は failures の F1036。

## 3. 止まらない経路 (後送)

段 6 レビュー B2 の仕分け。wave 本体の reflog 起因 rc=20 (amend をやめ追加 commit で直すのが手順側の対策)、manifest 外の補助木 (今回 `DW-S05-A` で登録を明記したが機械検査は無い)、symlink path の manifest 指定で rc=2、調整役の撤去許可待ちで止まる運用 (repo 外の取り決めで、許可が来ないときの扱いが決まっていない)、ExitWorktree で main に戻ってから終了した session (Stop hook の cwd 判定では見えない)、main 前進以外の rc=30 と途中停止からの再開 (現行は木の削除後・受領証の前に止まると再実行で完了できない。段 2 plan の journal 案は頻度の実測後に設計する)。
焦点再レビューの should「admin 再検査への wave 引数の伝播を単独で固定する test が無い」は、現行実装の欠陥ではなく DW-G05 により追加しなかった。

## 4. 検査

- 焦点走 (login、`tools/run_tests.py`): fix 1 前 (commit 0ad743c0b) に変更 test・consumer・収集制約・inventory 4 群・`test_check_docs.py` で 2241 passed / 7 skipped (skip は template patch 未適用 4 件と growth hold 3 件。後者は `python3 tools/check_docs.py` の直接実行が違反なし)、fix 1 後 (329456b6b) に 6 file で 962 passed / 1 skipped、fix 2 後 (308091ea3) に `test_dev_wave_cleanup.py`・`test_hooks.py`・`test_pytest_collection_config.py` で 782 passed / 1 skipped。
- 変異 (`tools/mutation_worktree.py`、独立 clone、直列 dispatch、runner = `test_dev_wave_cleanup.py` 全体 + `test_hooks.py` の Stop hook 関連 11 node): spec は `verbatim/mutation-spec-final.json` (sha256 56b4b7c4bf28ae8528c7bd0d8b4ee8b632fe3a95856272c86eab78291920a57f)。
  - probe (commit 329456b6b、全件 SURVIVED 期待): M2 と M14 が SURVIVED。M2 は「未統合の子 + reflog にしか無い commit」の test が無く (既存 test の子は統合済みで手前の経路が拒否する)、M14 は上限超過 test の payload が読めても block されない形だった。どちらも real な test の穴として fix 2 で test を足した。焦点再レビューは M14 を「単一理由で落ちる」と静的に判定していたが、実測で覆った。
  - final (commit 308091ea3): baseline PASSED、M1〜M14 と M6B の 15 件が KILLED、等価変異 P0 が SURVIVED、MISMATCH 0 (16/16 が事前登録と一致)。期待 node は probe の観測に、fix 2 の 2 test を M2・M14 へ実装の読解で足したもの。所要 68 分 (直列 dispatch 17 request)。
  - 束ね経路 (`dispatch_compute.py --task mutation`、1 job) は runner に nodeid と `-k` を許さず、2 file 全体で回すと計算ノード上で撤去 test 126 件が `lexical cwd is unavailable or not absolute` で baseline 赤になった (変更と無関係の既存 test を含む)。撤去 tool の test は束ね経路で走らない。
- 規模 (`git diff --numstat 8fe87f852 308091ea3`): `tools/dev_wave_cleanup.py` +88/-21、`tools/dev_wave_cleanup_stop_hook.py` 94 行 (新規)、`orchestrator/tests/test_dev_wave_cleanup.py` +142/-11、`orchestrator/tests/test_hooks.py` +158、`.claude/settings.json` +11、pin 追随 (`tools/check_docs.py`・`test_check_docs.py`) 各 ±2〜4。裁定の上限 (tool 250・hook 120・test 各 300) 以内。
