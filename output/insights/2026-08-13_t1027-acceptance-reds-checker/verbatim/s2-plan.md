## A

(P1) は修正版を採る。dispatch が使われた場合の collection 権威は relay stdout ではなく、dispatch receipt の `scheduler_logs.stdout.tail` とする。dispatch されなかったローカル実行だけは `CompletedProcess.stdout` を権威とし、後述の完全性 gate を必須にする。

実装箇所は [tools/check_acceptance_reds.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:21) 付近へ定数と receipt 型、同ファイル 52 行付近へ次の private helper を追加する。

- `_dispatch_receipt_path(stdout, returncode) -> Path | None`
- `_read_dispatch_receipt(path, worktree, expected_args, returncode)`
- `_authoritative_collection_stdout(...) -> str`
- `_cleanup_dispatch_artifacts(...)`

receipt path は `child stdout begin` 行から推測しない。[dispatch_compute.py:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/pegasus/dispatch_compute.py:1770) が出す次の非 relay 行を、行全体一致で一意に解析する。

```text
[Pegasus dispatch] receipt を <absolute-path> へ保存しました (child rc=<N>)
```

この方法を選ぶ理由は次の通り。

- child の各行は [dispatch_compute.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/pegasus/dispatch_compute.py:705) で必ず `| ` が付く。したがって、行頭から一致させれば child が receipt 告知を偽装しても候補にならない。
- receipt の nonce は subprocess 呼出側へ返されない。`output/pegasus-dispatch` の前後差分走査は並行 dispatch と競合し、fallback receipt もあるため決定的でない。
- request ID から scheduler log 名や nonce を逆算する案は、非公開命名規則へのより強い結合になる。
- exact selector だけを再 collect する案は、`@group` と literal `@`、summary detail と literal ` - ` の区別に再び推測を持ち込み、現行 [tools/check_acceptance_reds.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:108) の最長 exact-match 契約を弱める。さらに長い parameter 集合では再度 relay 上限を超えうる。
- relay の `omitted_bytes` を見て即 rc=2 にするだけでは誤診は直るが、既知赤の実ファイルを判定できず、brief の「実運用へ到達」を満たさない。

receipt path は JSON を読む前に以下をすべて検査する。

- 絶対 path であり、NFC、制御文字なし。
- `worktree/output/pegasus-dispatch` を `resolve(strict=True)` した root の内側。
- 許す形は `<root>/<nonce>/receipt.json` または `<root>/receipt-fallback-<nonce>.json` のみ。nonce は dispatcher と同じ leaf 制約とし、`.`、`..` は拒否する。
- leaf と辿る各 component に symlink がない。receipt 自体は `O_NOFOLLOW` で開き、regular file、上限内、読取中不変を確認する。
- 保存行が 0 件、複数件、child rc 不一致、dispatch 制御行があるのに保存行がない場合は、ローカル stdout へ fallback せず `InvalidInput`。

必須 schema は次に限定する。未知の将来 schema を推測受理しない。

- `schema_version == "pegasus-dispatch-receipt/v2"`
- `submission_dir`: 上記 nonce directory と一致
- `request.task == "tests"`
- `request.args`: `run_tests.py` が dispatch へ渡す正規化後 argv と完全一致。末尾 path は probe worktree 内の絶対 path
- `result.stage == "child"`、`result.child_rc == subprocess returncode`
- `outcome.kind == "child"`、`outcome.rc == subprocess returncode`、`outcome.accounting_verified is True`
- `scheduler_logs.accounting_present is True`
- `scheduler_logs.stdout.path`: 検証済み `submission_dir` 内
- `scheduler_logs.stdout.size`: bool でない非負 int
- `scheduler_logs.stdout.omitted_bytes`: bool でない int かつ collection では必ず 0
- `scheduler_logs.stdout.tail`: str。`omitted_bytes == 0` の場合は UTF-8 byte 長が `size` と一致

証拠 3 は relay 側が `omitted_bytes=8002` だが、実 receipt の `scheduler_logs.stdout` は `size=12098`、`omitted_bytes=0`、全文 tail である。この二つを混同しない。receipt 内でも `omitted_bytes>0` なら、その tail は権威に昇格させず rc=2 とする。

[tools/check_acceptance_reds.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:452) と 477 行の二つの default runner は共通の receipt 検証・後始末を使う。これは追加で必要な修正である。dispatcher は [dispatch_compute.py:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/pegasus/dispatch_compute.py:1321) により probe worktree 内へ成果物を作る一方、fingerprint は [tools/check_acceptance_reds.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:364) で ignored file も検出する。このままでは selector 修正後に次の identity gate で止まる。

したがって、検証済み nonce directory と、該当時だけ exact fallback receipt を `finally` で除去する。root 全体、glob、未検証 path は削除しない。削除失敗は rc=2 とする。node rerun 側も `capture_output=True` にして同じ後始末を行い、従来表示されていた stdout/stderr は後始末後に再送する。任意の ignored artifact を拒否する既存 gate と既存テストは緩めない。

`tools/pegasus/**` と `tools/run_tests.py` は一切編集しない。

## B

(P2) は `_selector_from_collection` へ入れず、[tools/check_acceptance_reds.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:477) の `_default_collection_runner` が権威 stdout を得た直後、nodeid tuple を返す前に置く。新 helper の署名候補は次である。

```python
def _complete_collected_nodeids(stdout: str, path_text: str) -> tuple[str, ...]:
    ...
```

禁止署名は次の通りとする。

> collection footer が欠落・複数・未知書式、selected 件数が 0、deselect 算術が不整合、path に一致する nodeid が重複、または unique nodeid 件数が selected 件数と不一致なら、部分 collection を返してはならない。

証拠 3 と 4 の実書式はそれぞれ、`| ` を一度除いた後の次の形である。

```text
114 tests collected in 0.58s
8 tests collected in 0.54s
```

受理 grammar は、既存 `_DURATION` を再利用して次に閉じる。

- `1 test collected in <duration>`
- `N tests collected in <duration>`
- `S/T tests collected (D deselected) in <duration>`。`S + D == T` を必須とし、比較対象は `S`
- `no tests collected in <duration>`
- `no tests collected (D deselected) in <duration>`

footer は一意でなければならない。nodeid は現行と同じく、`line == path_text` または `line.startswith(path_text + "::")` のみを数える。ただし現在の set 内包で重複を黙って畳まず、list で抽出して重複を明示拒否してから unique tuple にする。

各場合の扱いは次の通り。

- 0 件: 実 pytest は通常 rc=5 なので先行する returncode gate でも止まる。注入 seam が rc=0 と `no tests collected` を返しても completeness gate で rc=2。
- 複数 path: `_probe_nodes` の [721-723 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:721) は赤 reference ごとに一つの `path_text` を collect する。異なる path は別 invocation、別 footer、別 gate とし、合算しない。
- deselect: footer の total ではなく selected を比較する。全件 deselect は selected=0 なので rc=2。
- skip: runtime skip 予定の test も item として collect される限り通常の nodeid として数える。collection 中に module 全体が skip され nodeid が出ない場合は 0 件として rc=2。現行 pytest の collect-only footer にない独自 `skipped` 項目を推測受理しない。
- footer に collection error 等の未知 suffix が付けば、returncode が誤って 0 でも fail-closed。

通る正例は次である。

```text
orchestrator/tests/test_example.py::test_a
orchestrator/tests/test_example.py::test_b

2 tests collected in 0.01s
```

`path_text == "orchestrator/tests/test_example.py"` なら selected=2、unique path nodeid=2 で通り、二つの nodeid を返す。`| ` が各行に付いた完全な relay と、receipt の無接頭辞 tail の双方で同じ結果になる。

## C

rc は現行どおり 2 とする。0 は green または全件 non-attributable、1 は attributable-red、2 は入力・環境・完全性を証明できない場合という既存三値契約であり、新 rc を追加すると scope 外 consumer の変更が必要になる。

打ち切り時の制御フローは次になる。

1. `_default_collection_runner` で command rc、receipt location/schema、receipt stdout の非打ち切り、footer 件数を順に検査する。
2. いずれかが不明なら `InvalidInput("pytest collection ... truncated/incomplete ...")` を送出し、nodeid tuple は返さない。
3. [tools/check_acceptance_reds.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:722) の代入が完了しないため、723 行の selector 解決、734 行の単独 rerun、740-742 行の attributable 追加へ到達しない。
4. `_probe_nodes` の 752-775 行が probe を cleanup した後に同じ `InvalidInput` を再送出する。
5. `check_acceptance_reds` は [907-923 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:907) の status 決定へ戻らず、`non-attributable-only` 分岐も checker receipt 書込も実行しない。
6. `main` の [1014-1017 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:1014) だけが `status=invalid-input` と理由を出し rc=2 を返す。

したがって、「判定不能なのに rerun_rc がないため attributable が空で、non-attributable-only へ落ちる」という新経路はない。`non-attributable-only` へ行けるのは、全 reference が完全な collection から exact selector を得て、全単独 rerun が明示的に rc=1 を返した場合だけである。

診断は三つに分ける。

- relay は打ち切られたが完全 receipt を回収できた: エラーにせず処理継続。
- relay が打ち切られ、receipt が欠落・複数・範囲外・schema 不正: `collection relay is truncated and no complete dispatch receipt is available`
- receipt tail 自体の打ち切り、または footer 不一致: `dispatch receipt collection is truncated`、あるいは `collection footer count mismatch: selected=N nodeids=M path=...`

完全性を通った後に本当に reference が存在しない場合だけ、現行の `logged pytest nodeid has no exact collected selector` を残す。

## D

既存期待値は変更しない。fixture の入力だけを実 pytest の collect 出力へ合わせる。

- [test_check_acceptance_reds.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:50): fixture の 7 nodeid 後へ `7 tests collected in 0.01s` を追加する。
- 同 888-890 行の `test_default_seam_forces_dispatch_for_collection_and_rerun` と、998-1000 行の infrastructure fixture に `1 test collected in 0.01s` を追加する。既存の rc、command、receipt expectation はそのまま。
- 同 186 行付近へ、動的 probe cwd 内に実 schema 相当の receipt、scheduler log、relay transcript を作る `_fake_dispatch_result` helper を置く。

新規 nodeid 候補と殺す欠陥は次の通り。

- `test_truncated_relay_uses_complete_dispatch_receipt`
  - 証拠 3 と同様に relay から目的 nodeidを落とし、receipt tail には残す。旧 `result.stdout.splitlines()` 経路を殺す正例。
- `test_truncated_relay_without_receipt_fails_closed_before_rerun`
  - `omitted_bytes>0` の relay header と部分 footerだけを返す。receipt 不在時の relay fallback と誤 selector 診断を殺す。
- `test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun`
  - 外部 path の内容は他 field をすべて有効にする。location gate 無効化時だけ rc=0 へ反転させる。
- `test_dispatch_collection_receipt_requires_bound_request_args`
  - 別 path の collect receipt を差し込む。stale/foreign receipt の流用を殺す。
- `test_dispatch_collection_receipt_requires_v2_child_outcome`
  - schema、child rc、accounting の欠落を parameter 化する。field 欠落を黙って補う実装を殺す。
- `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed`
  - receipt 自体の `omitted_bytes>0` を再現し、relay 打ち切りとの取り違えを殺す。
- `test_collection_footer_count_mismatch_fails_closed_before_rerun`
  - path nodeid 1 件、footer 2 件、目的 selector は存在する入力にする。件数 gate を落とすと non-attributable-only まで進むため単一理由になる。
- `test_single_test_collection_footer_is_accepted`
  - `1 test collected` の正例。過剰拒否と singular grammar 退行を殺す。
- `test_deselected_collection_footer_uses_selected_count`
  - 1 nodeid と `1/3 tests collected (2 deselected)` を通す。total と selected の取り違えを殺す。
- `test_zero_or_all_deselected_collection_fails_closed`
  - `no tests collected` と `no tests collected (3 deselected)` を parameter 化し、空 collection の受理を殺す。
- `test_each_logged_path_has_an_independent_complete_collection_gate`
  - 二つの赤 path に別 transcript を返し、path 間の footer 合算や collection 再利用を殺す。
- `test_injected_collection_failure_cannot_reach_rerun_or_status`
  - 既存 `collection_runner` が `InvalidInput` を送出する注入を用い、`node_runner=_unexpected_runner` として `_probe_nodes` から rc=2 までの制御フローを固定する。
- `test_default_dispatched_rerun_removes_verified_dispatch_artifacts`
  - node rerun も fake receipt を生成し、厳密な後始末後に fingerprint を通ることを確認する。
- 既存 `test_ignored_artifact_from_node_fails_closed` は無変更で残し、dispatcher 固有成果物の限定 cleanup が任意の ignored artifact 無視へ広がっていないことを保証する。

打ち切りの production parser は `command_runner` へ `subprocess.CompletedProcess` と receipt ファイルを注入して検査する。外側の例外伝播は `collection_runner` 注入で検査する。いずれも実 dispatch は不要で、semantic test は private helper 直呼びではなく `CAR.main(...)` を通す。

この段では pytest を実行していない。静的に injection seam、現行制御フロー、実 receipt schema、footer 書式を確認しただけである。

## E

行番号は現行 anchor。実装後、段 4 で逐語 anchor の一意性と最終行番号を再固定する。

1. **M0: wave 前 collection source への忠実回帰**
   - 位置: 現行 [tools/check_acceptance_reds.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:505)
   - 変異: 新しい `authoritative_stdout.splitlines()` を、wave 前の実コードが使う `result.stdout.splitlines()` へ戻す。
   - 期待 node: `test_truncated_relay_uses_complete_dispatch_receipt`
   - 単一理由: receipt/schema は有効で前段を通るが、relay には nodeid がなく footer 件数との一つの不一致で赤になる。元実装では receipt tail により同じ外部入力が通る。selector 以降には到達しない。

2. **M1: footer 件数 gate の無効化**
   - 変異: `if len(nodeids) != selected_count:` を恒偽化。
   - 期待 node: `test_collection_footer_count_mismatch_fails_closed_before_rerun`
   - 単一理由: source、footer grammar、nodeid、selector はすべて有効。gate を落とすと rerun rc=1 から rc=0 になる。前後に同じ件数を検査する層は置かない。

3. **M2: receipt stdout 完全性 gate の無効化**
   - 変異: `omitted_bytes != 0 or size != len(tail.encode("utf-8"))` の結合条件を恒偽化。
   - 期待 node: `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed`
   - 単一理由: fixture は location、schema、request、outcome、footer、selector を有効にし、欠陥を receipt stdout の不完全性だけにする。後段 footer は完全に見える tail を通すため mask しない。

4. **M3: request binding の無効化**
   - 変異: `request.task/args` と期待 argv の不一致条件を恒偽化。
   - 期待 node: `test_dispatch_collection_receipt_requires_bound_request_args`
   - 単一理由: receipt location と残りの schema は正しく、別 path の request だけが不正。無効化後は完全 tail と selector が通り rc=0 になる。後段で request を再検査しない。

5. **M4: receipt location gate の無効化**
   - 変異: receipt 保存 path の許可形判定を恒偽化。
   - 期待 node: `test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun`
   - 単一理由: 外部 receipt は内容上の `submission_dir`、stdout path、request、tail をすべて有効にする。location 検査は一つの helper に集約し、schema 層で同じ receipt-file location を重複拒否しない。

6. **M5: singular 正例の過剰拒否**
   - 変異: count=1 の期待 noun を `test` から `tests` にする。
   - 期待 node: `test_single_test_collection_footer_is_accepted`
   - 単一理由: 1 件正例は source、件数、selector、rerun がすべて有効で、noun 検査だけが赤になる。新 gate による受理集合縮小の positive control とする。

登録候補から外すものは次の通り。

- 現行 511 行の `if not nodeids` 単独無効化: 新しい selected=0 と件数 gate が後段で同じ入力を拒否するため等価変異。
- relay header の `omitted_bytes` 検出だけの無効化: receipt 欠落・schema・footer gate が同じ入力を拒否し続け、受理集合が変わらない。
- P3 の診断文字列を旧メッセージへ戻す変異: rc と分類集合が変わらない。B-057 の semantic kill ではなく diagnostic sensitivity pin として別枠にする。
- `scheduler_logs.stdout.size` と `omitted_bytes` を別々に無効化する変異: 相互に mask しうる。M2 の一つの「完全な stdout record」条件へ再照準する。
- `_selector_from_collection` の no-match gate 無効化: 完全性 gate より後ろであり、今回の打ち切り入力には到達しない。既存 selector 契約の別 wave 変異であって、本 wave の新 gate の証明にならない。

## 総括

- dispatch 時は一意な receipt 保存行から v2 receipt を特定し、完全な `scheduler_logs.stdout.tail` だけを権威にする。
- footer の selected 件数と unique path nodeid 件数を一致させ、0・欠落・複数・未知書式は rc=2 とする。
- 不完全性は rerun・status 決定より前に `InvalidInput` となるため、判定不能を non-attributable と報告する経路はない。
- 実 dispatch は行わず、静的検査だけを実施した。