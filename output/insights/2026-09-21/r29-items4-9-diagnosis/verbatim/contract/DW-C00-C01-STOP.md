## DW-C00 — manager の範囲

範囲・言語・起動は入口、引数優先。読了トリガ別:
L0=入口、L1=常時段U、L1.5=クラス依存段U、L2=C。

設計択一が割れる・正しさ防壁に触る・受理集合が変わる段は独立の敵対検証子必須。変更面確定時も再評価する。
非該当は**既定の軽量版**：段2・3と段6 review子を省ける。ただし一次資料から事実を再調査・再抽出する
docs-onlyは段6の独立read-onlyレビュー1本を残す。他のdocs-onlyは子ゼロ可。
実装面があれば段 5 の Codex 実装子と fix 子は軽量版でも必須、親は直接編集しない。
実測必須、全9段はユーザー明示時に使う。

待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。停止時は生産者・待ち手を止めて死を待つ。
`ps`全cmdlineで対象worktreeの0件実測後に投入。完了は`.done`非空。同一worktreeのdispatchは全種直列（並行はorphan
holdでrc=16、`DW-O26`）。`qdel`前に`docs/pegasus-runbook.md`§7.6を読む

## DW-C01 — 実測で是正した作法

`DW-O01/O08/O17/O20`より優先。
- `--lane`はconsult、`--reasoning`はplan/consultで必須。他段指定/必須段無指定はrc=2。
- 待ち手はpid file実在後に張る。先行は子の生存中も即戻る。
- 隔離worktreeのdetachは`.sh`2枚(launcher/detach)へ。直に叩くとguard拒否。
- 複数起点は全隣接区間の異なる正値で判別。
- 変異harnessはbaseline緑必須。既存赤は根拠を台帳へ書き`--deselect`。
- 全新規worktreeを`python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>`で再帰初期化する。
- 呼出し規約変更取込は、両親の変更行が非競合でも全呼出しを数える。
- 段6fixも受理・拒否の含意を2文に分け、通る正例を添える。
- merge/`add`/commitは親、子は競合解決だけ。
- 子の成果物はrepo内に書かせ、親が実行後repo外へ退避。
- Web検索は必要な段だけ明示して使う。

## DW-STOP — fail-closed 停止条件

参照契約/検査/権限/scope/所有違反は次段を止め、調査・修正・再検証する。
同一目的の修復は次waveでない。同一要求の再試行不可≠修復不可 (F946)。
正式停止は承認前提を覆す新事実・裁定/権限待ち・許可範囲で復旧不能な場合だけ。直せる赤で終了しない。
テスト弱体化・権限拡大・rebase・force・未監査差分で迂回しない。
