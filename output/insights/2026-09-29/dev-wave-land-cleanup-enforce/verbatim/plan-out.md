## 総括

段 2 の結論は、**退避撤去は「統合証明の代わりに、復元可能な証拠を撤去前に検証する」独立経路として実装する**ことです。現行の `remove-child` は dirty bytes を保存しますが、reflog の全 commit、detached 子、index の生状態を覆いません。また、木の削除後から receipt 発行前までの失敗は再実行で回復できません。P1 と P2 は同じ回復 journal を含めて実装する必要があります。

以下は指定資料の静的検査に基づく計画です。書き込み・テスト・探索は行っていません。

## P1

**変更位置:** [dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1456) の `ChildProof`、`:1578` の統合判定、`:1678–1810` の証拠と receipt、`:1812–1974` の実行順、`:236–327` の Git argv 許可、`:2028–2048` の結果表示。

現行の再利用可能部分は、manifest 束縛と保管先の repo 外検査（`:1511–1559`, `:1864–1866`）、占有・index・変換・submodule の拒否（`:1850–1855`）、patch・status・dirty tar の作成と再読照合（`:1678–1772`）、bundle verify と SHA 記録（`:1883–1899`）、receipt の SHA 照合（`:1782–1809`）です。これらの拒否条件は維持します。特に submodule の dirty・ignored・pin 外履歴（`:1634–1675`）を安易に受理せず、`git worktree remove` と `submodule deinit` も使いません。

不足は次のとおりです。

| 対象 | 現行の穴 | 必要な保存・検証 |
|---|---|---|
| HEAD／branch reflog | bundle は現在の branch から `^main` の範囲だけ（`:1878–1887`）。reflog-only commit は漏れる | HEAD と対象 branch の reflog の old/new commit、現在 HEAD、branch tip を列挙し、**各 commit が bundle 内か、存続する main/ref から到達可能**と証明 |
| detached 子 | bundle を作らない（`:1878–1879`） | detached HEAD と HEAD reflog の非到達 commit も bundle |
| 別 branch 由来履歴 | 現行は別 branch が保持すると許可（`:1594–1600`）するが、その branch が後で消えれば証拠 dir には残らない | 退避経路ではその commit も bundle。統合済み経路の従来期待値は維持 |
| index-only 変更 | `index.patch` はある（`:1732–1734`）が、index 自体と flag の復元証拠はない | admin 内の index 生 bytes と SHA、patch の適用検証。既存の特殊 flag／未解決 stage 拒否は維持 |
| ignored・未追跡・空 directory | status と dirty tar は ignored を拾う（`:1678`, `:1694–1765`）が、空 directory を省き、tar の entry と元の閉集合を照合しない | `.git` binding を除く木の全 entry inventory、tar の再読・entry 数・type・mode・bytes SHA の一致。特殊 file、読取不能、変動は拒否 |
| submodule と admin | primary store の pin 検査はある（`:1660–1673`）。admin snapshot は削除照合用で、復元 archive ではない（`:890–918`） | 許可済み submodule の木と admin の必要 bytes を証拠へ保存・照合。object の存続条件も receipt に記録 |
| stash | shared stash は子木撤去で直ちに消えないが、子由来か識別できない | 対象時点の `refs/stash` とその reflog を記録。損失ゼロを主張する退避経路では非到達 stash commit も bundle に含めるか、保存不能として拒否 |

**新規関数案:** `_collect_child_loss_set`、`_archive_child_tree_and_admin`、`_create_complete_child_bundle`、`_verify_child_archive`、`_write_child_recovery_journal`、`_resume_child_removal`。全 commit を含む bundle は、共有 repo に一時 ref を作らず、証拠 dir 内の隔離 bare repo に列挙 SHA の archive ref を作り、共通 object store を読ませて `git bundle create history.bundle --all` とします。`git bundle verify` を**空の検証 repo**で成功させ、`bundle list-heads` が列挙 SHA を指すこと、unbundle 後に全 SHA を `cat-file -e` できることまで検証します。既存の `^main` incremental bundle の verify だけでは、必要な prerequisite を持つ現 repo でしか検証できません。

擬似コード:

```text
preflight、占有・index・変換・submodule 検査
proof = 凍結した main tip／HEAD／branch／owned_paths
integrated = 従来の統合証明
if !integrated: route = archived-removal
木・admin・reflog・stash の閉じた inventory を作る
route が archived-removal なら完全 archive と全必要 commit bundle を作る
archive を再読し inventory と照合、空 repo で bundle を検証
撤去開始前に recovery journal を fsync・原子的に公開
unlock → detach → 再照合 → 木 → admin → branch
branch -D は manifest 現行 branch、tip 不変、証拠検証済みの場合だけ
不在と証拠 SHA を検査して removed.json を原子的に公開
```

receipt には `schema/version`, `route`（`integrated`／`archived-removal`）, `path`, `manifest_sha256`, `branch`, `HEAD`, `admin_gitdir`, `proof_main_tip`, `final_main_tip`, `owned_paths`, `inventory_sha256`, 各 archive の path・SHA・entry 数、reflog/stash の commit 集合、bundle の path・SHA・head 対応・空 repo verify 結果、`branch_deleted`, `deleted_branch_tip`, `completed_at` を記録します。`CleanupResult` に route を加え、既存 stdout の `removed` は維持しつつ、明示的な JSON 出力オプションと stderr の `route=...` 診断を追加します。

**正例テスト:** 未統合で owned path 不一致、空 owned_paths、detached HEAD、reset で reflog-only commit、別 branch 由来 commit、index-only 変更、ignored file と未追跡原本をそれぞれ退避・復元し `-D` または detached の branch 無しまで確認するテスト。**負例:** tar entry 欠落／空、bundle に SHA 一つ欠落、verify 失敗、特殊 file、submodule 不一致、index flag、占有、manifest 不一致では木・admin・branch が残るテスト。

## P2

「main changed」の明示的な rc=30 は [dev_wave_cleanup.py:1578–1580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1578) と `:1930–1935` の二箇所です。前者は preflight（`:1859–1860`）では rc=20、木削除後の `_recheck_admin`（`:1062–1065`, `:1921–1925`）では rc=30 になります。後者は branch 削除直前の rc=30 です。

両方とも `proof.main_tip == current_main_tip` を、`merge-base --is-ancestor proof.main_tip current_main_tip` に緩めてよいです。**比較の基準となる proof 時 tip と、その tip に対する owned path の tree 比較（`:1583–1587`）、子 branch／HEAD の不変条件は緩めません。** main の巻戻し・分岐、Git 判定不能は拒否します。wave 本体には同文言の比較はなく、`:664–672`, `:741–764`, `:1061–1065`, `:1425–1429` は「現 main からの到達性」を調べています。前進なら成立し続け、巻戻し時は拒否するので変更しません。`_child_payload` の merge-base（`:1728`）も proof 時 tip に固定します。

現行 rc=30 の再実行は冪等ではありません。木を削除した時点（`:1920–1923`）で receipt はまだ無く（`:1957–1971`）、`_child_receipt` は false。再実行は record の branch が detached のため `:1830–1832` で拒否し、admin が消えた後なら `_directory_identity`（`:1833`）でも拒否します。branch 削除後・receipt 前も同様です。wave 側には admin recovery journal（`:973–1006`, `:1105–1155`）がありますが、子の入口はそれを使いません。

P1 の recovery journal を**木を消す前**に公開し、子入口で receipt より先に確認します。journal が固定する manifest、元 HEAD／branch tip、証拠 SHA、admin snapshot と現在状態を照合して、`attached → detached → dir 無し・admin 有り → admin 無し・branch 有り → branch 無し` の各状態から残工程だけを進めます。食い違いは rc=20／30 で停止し、別の木や branch を推測削除しません。

**正例テスト:** proof 後に main が fast-forward した各注入点（admin recheck、branch delete）で完走。各 mutation 境界で中断後、同 argv で完了。**負例:** main 巻戻し・分岐、子 tip 変化、証拠改変、journal と admin inode の不一致は拒否。既存 `test_remove_child_main_advance_during_removal_is_partial`（[test_dev_wave_cleanup.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:476)）の期待値は新仕様と衝突するため、前進成功例へ置き換え、分岐拒否を別テストにします。

## P3

**新 file:** `hooks/guard_dev_wave_cleanup_stop.py`。配線は [.claude/settings.json:8–47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/.claude/settings.json:8) の `hooks` に `Stop` command を追加。規約説明は [hooks/README.md:467–474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/hooks/README.md:467)。これは注意喚起の衛生 hook と明記し、PreToolUse の正しさ防壁や Codex 配線の証拠と混同しません。実測入力では EnterWorktree 後の `cwd` と `stop_hook_active`、`background_tasks` が確認されています。

`decide(payload, git_runner)` の判定手順:

1. `stop_hook_active is True` は通す。payload 欠落・型不正・git 外は通す。
2. cwd を検査し、各 Git 呼出しは `subprocess.run(["git", "-C", cwd, ...], shell=False, stdin=DEVNULL, timeout=0.5)`。hook 全体を約 3 秒で打ち切る。
3. argv は順に `rev-parse --is-inside-work-tree`、`rev-parse --is-bare-repository`、`rev-parse --show-superproject-working-tree`、`rev-parse --show-toplevel`、`rev-parse --git-dir`、`rev-parse --git-common-dir`、`symbolic-ref --quiet HEAD`、`rev-parse --verify refs/heads/main^{commit}`、`rev-parse --verify HEAD^{commit}`。primary checkout（git-dir＝common-dir）、detached、bare、submodule は通す。cwd が linked 木の内部でも top-level を基準にする。
4. `git reflog show --reverse --format=%H refs/heads/<current-branch>` の最古 entry を作成時 tip 候補とする。reflog 不在・曖昧なら通す。`creation_tip != HEAD` を必須にして、作成直後の commit 0 件を block しない。さらに `merge-base --is-ancestor creation_tip HEAD` と `merge-base --is-ancestor HEAD refs/heads/main` がともに rc=0、木が存在するときだけ block。rc=1 は通し、その他・timeout は通す。reflog 最古 entry が本当の作成 entry か確かめるため、可能なら branch reflog の初行 old SHA が全ゼロであることを読む。reflog が期限切れなら推定しない。
5. block は `{"decision":"block","reason":"local main への land 済み子 worktree が残っています。DW-O28 に従い、この wave が作った manifest 登録木と branch を撤去してください。撤去できない場合は対象 path と理由を最終報告に記してください。"}` を stdout に出す。許可と内部失敗は exit 0、出力無し。実測どおり再 Stop の `stop_hook_active=true` は通す。

`background_tasks` が非空というだけで通すと、完了済み task や別用途の task で残骸を見逃します。active 状態の schema が実測で確定するまでは抑制に使わず、調整役の OK 待ちでは turn ごとに一度の追加モデル応答が生じる費用を README に明記します。後で active と確実に判定できる field が証明された場合にだけ skip を加えます。

**正例テスト:** `decide` 直叩きで linked 木の branch が作成 tip から前進して main 祖先の場合に block、stdin JSON→stdout JSON の subprocess 煙テスト、settings の `Stop` command と file path を確かめる配線テスト。**負例:** commit 0 件、未 land、main checkout、detached、submodule、bare、git 外、reflog 欠落、Git timeout、`stop_hook_active=true` は通す。テスト追加位置は [test_hooks.py:4998以降](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_hooks.py:4998)。

## P4

[operations.md:216–222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/docs/dev-wave/operations.md:216) の `DW-O28` に、退避撤去・receipt・rc=30 再開・全子木の先行撤去を短く記述します。[workers.md:17–24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/docs/dev-wave/workers.md:17) の `DW-S05-A` は作成時登録を補助・計測・probe 木まで明示し、fix は**同じ木と branch を原則再利用**へ修正します。現文は「同木で branch を切り再登録」で、古い fix branch を増やすため矛盾します。`DW-S06-B`（`:50–56`）にも fix 投入時の同木再利用を参照させます。`hooks/README.md` に Stop の発火面と fail-open を記載します。D2163 の非祖先退避案却下と D2197 の統合済み限定は、今回のユーザー裁定を根拠に明示的に部分 supersede する decision fragment が必要です。F1034・F1036 との対応も failure fragment に記録します。

pin と予算は次を同時更新します。

| 面 | 現在値・検査箇所 | 実装時の扱い |
|---|---|---|
| `DW-O28` exact pin | [check_docs.py:631–638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/check_docs.py:631)、[test_check_docs.py:189–196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_check_docs.py:189)。現行 **997 bytes**、L2 単節上限 **1,000 bytes**（check_docs `:363`、test `:9503`, `:9700`） | 文を圧縮して 1,000 bytes 内に収め、両 literal と長さ assertion を同時更新 |
| workers の層予算 | L1.5 上限 **9,696 bytes**（check_docs `:362`, `:5391–5394`、test `:2769`, `:3473`） | 現在の実使用値は定数ではなく `:5324–5370` で算出。変更後に checker の報告値を測り、上限内で既存文を統合 |
| settings／hooks README | `check_docs.py` に両 file の byte 上限・全文 pin は見当たらず。settings 配線は [test_hooks.py:5229–5254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_hooks.py:5229) | `Stop` matcher の専用 pin を追加し、既存 PreToolUse の期待は保持 |

## 分割と所有

所有 path は次の素集合にします。今回の単独段では子 agent を起動しません。

| 単位 | 所有 path | 新テスト |
|---|---|---|
| U1 退避・再開 | `tools/dev_wave_cleanup.py`, `orchestrator/tests/test_dev_wave_cleanup.py` | `test_remove_child_archived_unintegrated_roundtrip`, `test_remove_child_archived_reflog_closure`, `test_remove_child_archived_detached`, `test_remove_child_archive_missing_entry_rejected`, `test_remove_child_reenters_each_partial_state`, `test_remove_child_main_fast_forward_after_proof`, `test_remove_child_main_diverged_rejected` |
| U2 Stop | 新 hook、`.claude/settings.json`, `orchestrator/tests/test_hooks.py` | `test_stop_blocks_landed_linked_branch`, `test_stop_allows_zero_commit_and_uncertain_contexts`, `test_stop_subprocess_json`, `test_settings_wires_cleanup_stop` |
| U3 規範・pin | `docs/dev-wave/operations.md`, `docs/dev-wave/workers.md`, `hooks/README.md`, `tools/check_docs.py`, `orchestrator/tests/test_check_docs.py`, decisions／failures の追記 fragment | `test_dw_o28_exact_section_pin_accepts_synthetic_fixture` の新 literal、既存の予算・節 pin テスト |

既存期待値の変更が必要なのは、統合不成立を固定する `test_remove_child_rejects_unintegrated_author_commit`、`test_remove_child_empty_owned_paths_requires_ancestry`、`test_remove_child_rejects_unreachable_reflog_history`（[test_dev_wave_cleanup.py:335–410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:335)）と、main 前進を rc=30 とする同 `:476–495` です。いずれも今回**意図して広げる受理集合**に直接衝突します。その他の既存テスト、とくに bundle verify 失敗、submodule、index flag、占有、wave branch `-d` の期待は変えません。

## 変異候補

| 殺す変異 | 落とすテスト |
|---|---|
| bundle 対象から HEAD reflog の old SHA を一つ除く | `test_remove_child_archived_reflog_closure` |
| detached 子の bundle を省く | `test_remove_child_archived_detached` |
| tar entry 数・SHA 照合を外す | `test_remove_child_archive_missing_entry_rejected` |
| index 生 bytes／index.patch を保存しない | `test_remove_child_archived_unintegrated_roundtrip` の staged 内容復元 |
| `bundle verify` の非 0 を無視する | 既存 `test_remove_child_bundle_verify_failure_is_partial` と新 archive 負例 |
| main の祖先判定を無条件 true にする | `test_remove_child_main_diverged_rejected` |
| journal 無しで木を消す／再開時に branch を推測削除する | `test_remove_child_reenters_each_partial_state` と journal 不一致負例 |
| Stop の `creation_tip != HEAD` を消す | `test_stop_allows_zero_commit_and_uncertain_contexts` |
| Stop の `stop_hook_active` を無視する | 同テストの再 Stop 例 |
| settings の Stop 配線を消す | `test_settings_wires_cleanup_stop` |
| DW-O28 の退避条件を一文削る | exact pin とその mutation 負例 |

## brief への異議

- **P1 の列挙だけでは損失ゼロを証明できません。** 現行 bundle は reflog 全 commit を含まず、detached 子は bundle 無しです。完全 archive の再読検証と空 repo での bundle 検証を撤去前条件に加える必要があります。F1034 の空 tar 事故を直接防ぐ箇所です。
- **P2 は比較二箇所の変更だけでは未完です。** rc=30 後の子経路は現行では再入不能です。証拠 dir の事前 journal と段階別再開を P1/P2 共通の必須実装にします。
- **P3 の `merge-base` を branch 作成点とみなす案は不適切です。** 作成点は reflog の初期 entry で確かめ、初期 entry を確定できなければ fail-open にします。commit 0 件の誤 block を防ぐ条件も必要です。
- **P4 の「fix は同じ子木を再利用」だけでは branch 残骸を抑えられません。** 現行 `DW-S05-A` は同木で新 branch を切るため、古い branch の所有と撤去方法を規範に含めるか、同一 branch を再利用する必要があります。
- Stop hook は終了時の案内であり、manifest 外の木、途中終了、調整役待ちの残骸を完全には回収しません。D2163 の対象限定を保ち、他 wave の木への自動 sweep へ広げない計画です。