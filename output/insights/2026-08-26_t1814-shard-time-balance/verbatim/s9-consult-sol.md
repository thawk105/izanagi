## 原因の同定

`scan_worktree_occupancy()` が `indeterminate` になる総則は、「占有者がゼロで、1 件以上の `issues` がある」です。占有者がいれば issue の有無にかかわらず `occupied` が優先されます（`tools/check_worktree_occupancy.py:613-621`）。

`issues` の全生成経路は次のとおりです。

1. `/proc` が directory でない、列挙・PID 数値化に失敗する（同 `:550-570`）。
2. PID の最初の `stat` が読めず、PID directory がまだ存在すると判定された場合、または `stat` が不正・読取エラー（同 `:384-391`）。
3. `cwd` の `readlink` が失敗し、PID が残る非 zombie だった場合。`PermissionError` は非阻害診断だが、それ以外は issue（同 `:401-416`）。
4. 読めた cwd の `resolve(strict=True)` が失敗した場合。permission は非阻害、正確な `" (deleted)"` suffix を持つ対象外 cwd は非阻害、それ以外は issue（同 `:420-447`）。
5. self/zombie 以外の `cmdline` が読めず、PID が残っている場合。cmdline の permission も issue（同 `:453-476`）。
6. 走査末尾の `stat` 再読が失敗し、PID directory がまだ存在すると判定された場合（同 `:478-499`）。
7. 前後の `starttime` が違い、PID 再利用と判定された場合（同 `:501-509`）。

対象 worktree 自体が解決不能・非 directory の場合は `indeterminate` ではなく `invalid-target` ですが、CLI の rc は同じ 2 です（同 `:533-547`, `:698-703`）。今回の tmp repo は `_make_repo()` が実在 directory を作るため、この経路ではありません（`orchestrator/tests/test_dev_wave_cleanup.py:56-87`）。

48 worker の process churn から直接到達し得るのは、PID の初回/末尾 `stat` race、cwd/cmdline 消滅 race、PID 再利用です（上記 2、3、5、6、7）。proc policy や一時 I/O 異常が重なれば cmdline permission・その他 OS error も起こり得ます。各 PID の issue は対象との関係を問わず global `issues` に集約され（`tools/check_worktree_occupancy.py:586-611`）、1 件でも全体を不定にします。

D793 が閉じたのは、「readlink は成功、raw 値が正確に `" (deleted)"` で終わり、strict resolve のみ失敗し、PID が存続し、両 spelling が対象外」という一点です（`docs/decisions.md:30422-30437`、実装 `tools/check_worktree_occupancy.py:427-445`）。zombie は別の D705 経路で閉じています（同 `:408-414`）。

今回の拒否は `attempts=1 retry_count=0` です。一方、`missing/{stat,cwd,cmdline}` だけなら最大 3 scan の retry 対象です（`tools/dev_wave_cleanup.py:29-30`, `:488-496`）。したがって、純粋な D793 型 `missing/cwd` の閉じ残しならこの本文にはなりません。少なくとも一つ、`pid-reused`、permission、invalid/os-error、proc-root 等の非 retryable issue が混じっています。**今回の拒否原因は D793 の exact 射程外です**。ただし issue payload がエラー出力から捨てられているため、どの射程外経路かまでは未同定です。

テスト側については、実装が machine-wide `/proc` を走査すること自体は本来の契約です。対象 path を参照する process は機械のどこにでもいるためです。しかし、stat/cwd/cmdline が読めない process は「対象外」と証明できず、fail-closed の global issue に倒れるため、実際には無関係な短命 process も判定を不定にできます。

一方、この file の cleanup 状態遷移テストを uncontrolled な `/proc` に結合した点には、テスト隔離上の欠陥があります。`_make_repo()` は `_REPO` しか差し替えず、`_run()` は production `cleanup.main()` を直接呼びます（`orchestrator/tests/test_dev_wave_cleanup.py:56-87`, `:110-113`）。ただしこれはテストだけの偽赤ではなく、同じ環境で実 cleanup も rc=22 になる実装上の liveness defect です。

なお、提示された 15 node のうち machine-wide `/proc` に本当に依存するのは 6 nodeだけです。

- landed attached の 2 node（同 `:191-199`）
- forward-merged の 2 node（同 `:202-230`）
- reentry の `[a]` / `[b]`。`[c]`〜`[e]` は directory 不在で occupancy を呼びません（同 `:180-188`, `:242-266`）。

残る 9 node は `_occupancy_payload` を stub しているか、occupancy phase がありません（同 `:538-556`, `:625-667`, `:972-987`）。したがって「`_assert_success_output` を呼ぶ 15 node」は脆弱 class の正確な定義ではありません。

## 3 択の比較

| 案 | 受理集合・失う検出力 | 絶対規律 2 | 実装量・戻し方 | 次の同型への持続性 |
|---|---|---|---|---|
| (a) file 除外 94 node | 実効集合は `A - 94`。占有時の拒否、indeterminate の fail-closed、branch/reflog 安全性、path 検証、Git allowlist、再入状態、partial mutation 後の停止をまとめて失う。除外は実際に `--ignore=<file>` になる（`orchestrator/test_selection_contract.py:121-124`）。 | **抵触する。** 既知 flaky 以外の約 88 node まで無条件に受理判定から外す。さらに旧 reason は誤っていた「消滅 pid 型」のままで（同 `:43-50`）、旧 release condition は D793 land と明示 file 走で既に成立済み。単に tuple を戻すのは証拠も期限も stale。 | 機械的には 1 行だが、正当に行うなら新 reason/version/release condition と新しい直接裁定が必要。戻すときは空 tuple に戻して明示 file 走＋全走。 | file 内の node が動いても赤は消えるが、それは file 全体を見ないため。別 file の同型や新しい cleanup consumer には効かない。 |
| (b) 15 node hold | 実効集合は `A - 15`（collection 上は exact node を skip、`orchestrator/tests/conftest.py:1128-1132`, `:1335-1351`）。negative safety tests は残るが、正常撤去、forward-merge、再入、retry、診断受理、allowlist の統合正例を失う。しかも 9 node は今回の `/proc` churn と無関係。 | **現案は抵触する。** 実測のない 13 node を「既知失敗」として外すため。観測済み 2 nodeだけの正直な hold は registry 方針には沿い得るが、次走で node が移るため解決にならない。 | 15 個の完全 node row、canonical failures 証拠、再導入 task が必要。削除は各 row を外すだけだが、registry digest・collection 契約も検査対象。 | exact node 一致だけで class fallback はない。新 node、別 parameter、別 file には自動追随しない。今回 node が動いた事実と相性が悪い。 |
| (c) 実装修理 | `A` は不変。94 node をすべて実行し、cleanup の安全防壁も維持する。修理は「正体不明の stable process は indeterminate のまま」「消滅・PID 再利用・zombie・証明済み対象外だけ無害化」が条件。 | **抵触しない。** 不明 process を一律無視せず、同一 PID/starttime の再検証で非占有を証明できた lifecycle race だけ issue から除けるため。 | 中程度以上。まず issue の `error/source` を拒否診断へ出し、synthetic churn 回帰を追加し、exact PID の再検証または snapshot 安定化を実装する。失敗時は checker 差分を戻せば従来の fail-closed に戻る。 | 個別 node ではなく lifecycle class を直せば、node が移動しても効く。新しい issue class には別修理が必要。 |
| 第 4 案: composite acceptance | 高並列 shard ではこの file を外すが、全 worker 終了後に同 file 94 node を serial child で必須実行し、両 child-green の合成だけを受理する。全体の集合は `A` のまま。 | 両 phase の receipt と「片方欠落時は拒否」を機械化すれば抵触しない。94 node の安全検出は残る。ただし高並列下での cleanup liveness signal は失う。 | runner・receipt・欠落検査の変更が必要。戻すときは特別 lane を削除して通常全走へ戻す。 | 同 file 内の新 nodeにも効くが、他 file の real-`/proc` consumer や実 cleanup の liveness defect は直らない。暫定策に限る。 |

(b) の現行 registry は row ごとに singleton node ID を要求し（`orchestrator/tests/flaky_test_holds.py:105-112`）、green/red observation を非空で要求します（同 `:115-126`）。さらに canonical `docs/failures.md` の該当節が test function と failure signature を逐語的に含まなければ拒否します（同 `:146-161`）。spool は直接参照されません（同 `:23`, `:48-69`）。

したがって、残り 13 nodeを赤の実測なしに**正直に登録する成立形はありません**。validator 自体は observation の真偽を機械検証できないため文字列を捏造すれば通せますが、それは「不完全登録で赤を緑にしない」という契約（同 `:87-91`）と絶対規律 2 の違反です。観測済み 2 nodeも、現在の canonical F489 に今回の node/signature が fold されてから初めて登録可能です。

land の順序は「(a)/(b) で一旦 land」ではなく、原則として **(c) を終えるまで待つ**のが妥当です。遅延の実害は、docs-only wave の「duration 重みへ変えない」という結論が main の canonical 状態にならず、後続作業が古い前提で進む・同じ調査を重複すること、wave worktree/branch の滞留が続くことです。ただし runtime 修正や correctness 成果物が未配備になる遅延ではなく、94 node の破壊安全性検出を消す害より小さいです。待機を短くする必要があるなら、(a)/(b) ではなく第4案を別 task で先に入れるのが許容可能です。

## 推奨

(c)  
まず rc=22 に issue の `error/source` 集約を安全に出し、今回の非 retryable signature を確定する。  
その signature を synthetic `/proc` で再現し、同一 PID/starttime の再検証で transient と証明できる場合だけ無害化する。  
stable な非 zombie missing-cwd、対象内 deleted-cwd、実 occupant は従来どおり拒否して防壁を保つ。  
本 wave はその修理の child-green まで land を待ち、急ぐ場合だけ「94 node 必須 serial child」の第4案を使う。

## この推奨の穴

- 現在の stderr に issue payload がないため、修理対象が PID reuse、cmdline permission、別 OS error のどれかはまだ確定していません。
- exact-PID 再検証にも race はあり、lease なしでは「走査後に始まる process」を排除できません。既存契約どおり必要条件に留まります。
- (c) が runner の composite serial 化より大きい場合、docs-only 結論の canonical 化を不必要に長く止める可能性があります。
- 原因が compute node 固有の `/proc` policy なら、一般的な churn 修理ではなく環境契約の明示が必要になる可能性があります。

## 未確認事項

- 2 回の失敗時の `issues` 本体、PID、`error/source` はログに出ておらず未確認です。
- process が stat/cwd/cmdline のどの段階で変化したかは未確認です。
- 第4案について、現行 acceptance receipt に二段 child-green を合成する既成 seam があるかは全経路を監査していません。
- 指示どおり pytest・実 `/proc` probe は実行しておらず、本回答は静的検査です。資料記載の `94 passed` を独自に再確認してはいません。

## 総括

D793 は deleted-cwd の exact case を閉じており、今回の `attempts=1` は少なくとも別の非 retryable issue を示します。  
machine-wide `/proc` 走査は実装契約ですが、無関係な PID issue を global に集約するため liveness が process churn に支配されています。  
15 node hold は証拠契約上成立せず、実際の real-`/proc` 依存 node も 6 件だけです。  
file 除外は cleanup の破壊安全性検出 94 件を失うため採るべきではありません。  
受理集合を維持した (c) を優先し、land を急ぐ場合だけ全 94 node を別 child で必須実行する第4案が妥当です。