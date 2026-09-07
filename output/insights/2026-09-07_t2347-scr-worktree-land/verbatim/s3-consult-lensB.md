## 総括

結論は二段階です。

- F851 に記録された**実際の2本の `/scr/.../job-repo` 登録**については、案 (a) で fold gate の rc=31 は解消し、その後に同じ登録を理由として拒否する箇所も、読めた範囲ではありません。通常条件なら `rc=0,status=landed` まで進みます。
- ただしプランの実装は「path 不在」を判定せず、Git が `prunable` と呼んだ record を無条件に除外します。これは親 brief の不変条件1より広く、現プランのまま author へ渡すのは危険です。
- pytest は実走していません。指定された6ファイルだけの静的検査です。

## F851 が閉じるか (実行順の追跡)

| 順序 | land の処理 | F851 の `/scr` 登録への反応 |
|---:|---|---|
| 1 | `_verify_repository` | main と依頼 wave 自身の binding だけを検査。全 worktree registry は列挙しない。 |
| 2 | forward replay | `/tmp` の独立 repo で実行。共有 repo の `/scr` 登録を列挙しない。 |
| 3 | land lock | `.git/dev-wave-land.lock` のみ。worktree 登録とは無関係。 |
| 4 | locked preflight / dirt / no-touch | main/wave の status と `.claude/worktrees`・`.codex/worktrees` の実ディレクトリを検査する。`.git/worktrees` 全体や `/scr` は列挙しない。 |
| 5 | provenance | F851 の実走がこの段を通過して fold gate で落ちているため、当該2登録については通過実績あり。 |
| 6 | fold gate | 唯一の直接原因。変更後は2 record を除外し、実在する main/wave だけを `/tmp` 隔離 dir と比較するため通過する。 |
| 7 | gate 後再検査 | preflight・fingerprint を再実行するが、全 registry は列挙しない。 |
| 8 | collision / ff-only | main 内 target と untracked/ignored/control path を検査後、`git merge --ff-only`。detached の外部 `/scr` 登録を明示的に検査しない。 |
| 9 | postcondition / fold | main/wave の HEAD・status と fold 成果を検査する。`dev_wave_land.py` 内には別の `worktree list` がない。 |

1. **F851 の正確な再現状態では案 (a) は rc=31 を除去する。**

   - 根拠 (real): [dev_wave_land.py:3451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3451) が唯一の `worktree list` で、consumer は [dev_wave_land.py:3811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3811) のみ。F851 の2 record は実際に `prunable` と観測済み。
   - 放置時の land 値: 現行は `rc=31,status=fold-gate-failed`、提案実装後は `/scr` が判定要因から外れ、他条件が同じなら `rc=0,status=landed`（競合着地済みなら `already-landed`）。

2. **F851 の逐条照合は「恒久対応は満たす、再発検知の回帰固定は満たさない」。**

   - `恒久対応`: F851 が許した案 (a) を実装するため、観測済み2登録については充足。
   - `再発検知`: F851 が示す exact signature、すなわち `status=fold-gate-failed`、`[Errno 2]`、`/scr/` を、変更後に出さないことを確認する end-to-end test は計画されていない。予兆となる `/scr/` 登録の検知・記録も追加しない。
   - 根拠 (real): 計画された正例の終端は主に `_registered_worktree_paths` の返値であり、実 `land()` の status/reason まで束縛しない。
   - 放置時の land 値: 現実装案の値はおそらく rc=0 だが、将来同じ rc=31 signature が戻っても、この追加テスト群だけでは再発を直接検知できない。

## 所見 (real 候補)

3. **blocking: `prunable` と「worktree path 自体が不在」を同一視している。**

   Git の `prunable gitdir file points to non-existent location` が証明するのは、admin の `gitdir` が指す `<worktree>/.git` を追えないことです。worktree のトップディレクトリ自体が存在しないとは限りません。たとえばディレクトリと内容が残り `.git` だけ失われた登録も prunable になり得ます。

   提案コードは `is_prunable` を見た時点で decode/`resolve(strict=True)` を丸ごと省くため、従来なら解決して返していた「path は実在するが linkage が壊れた登録」も除外します。これは brief の「実在する登録は従来と1 bitも変えない」に反します。計画の helper は `shutil.rmtree(path)` で全 path を消すため、この反例を通りません。

   - 根拠 (real): [plan.md](/home/SFC/tanab/.claude/jobs/b550caea/tmp/wave-t2347/artifacts/t2347-scr-worktree-land/plan.md:12) のコードは prunable record を resolve 前に `continue` する。一方、現行 [dev_wave_land.py:3461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3461) は path 自体が存在すれば返す。
   - 放置時の land 値: 通常は変わらないが、その登録が fold 隔離領域と重なる条件では、従来の rc=31 から「検査を通過」へ変わり、意図した以上に受理集合が広がる。

4. **計画した実 Git test は分類器までは本物だが、F851 の land 経路を最後まで通さない。**

   `_make_prunable_worktree` は本物の `git worktree add`、path 削除、本物の porcelain を使っており、この点は良い設計です。しかし prunable 正例は `_registered_worktree_paths` の返値で止まり、同じ実 registry を保持したまま `_execute_fold_gate`、まして `land()` の ff/fold 完了まで通しません。既存の `_execute_fold_gate` 実機構テストは prunable 登録を作らず、別の2テストは関数全体を monkeypatch しています。

   - 根拠 (real): 既存 [test_dev_wave_land.py:9213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9213) は通常 registry、[test_dev_wave_land.py:9329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9329) と [test_dev_wave_land.py:9380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9380) は `_registered_worktree_paths` を置換する。計画にも prunable registry を伴う `land()` test はない。
   - 放置時の land 値: 現コードの静的追跡では rc=0 へ進むが、テスト成果物は「旧 rc=31 が end-to-end で消えた」ことを証明しない。

5. **a5 の異常終了残骸は、共有 repo に長期間残り得る。**

   script は EXIT cleanup を持ち、通常の `fail`/ERR では remove を試します。ただし SIGKILL、cleanup timeout、CCBench remove が期限を消費した場合などは superproject 登録が残ります。さらに cleanup は `CCBENCH_BASE worktree prune` だけを行い、`REPO_BASE worktree prune` は実行しません。

   残った admin の `gitdir` は、通常の `worktree add` の契約上 `/scr/.../job-repo/.git` を指し、script は `worktree lock` も admin `locked` file の作成も行いません。したがって login node、または scratch 消滅後には `detached`＋`prunable` の残骸として見え続けます。

   - 根拠 (real): add は [a5_second_boot_backoff_sweep.sh:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:467)、remove は [同:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:148)、prune は CCBench に対する [同:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:161) だけ。
   - 放置時の land 値: 案 (a) なら unlocked/prunable 残骸は rc=0 側へ進む。外部から lock された残骸、または login から path が見える環境では prunable にならず、従来どおり rc=31 が残る。

## 反証した懸念 (refuted)

6. **現在の a5 が自分で worktree を lock する懸念は反証された。**

   script 内の `lock` は campaign WAL 用などで、`git worktree lock` ではありません。worktree は `add --detach` だけで、admin の `locked` file を操作する処理もありません。加えて F851 自身が実 `/scr` 2登録を prunable と記録しています。

   - 根拠 (refuted): [a5_second_boot_backoff_sweep.sh:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/pegasus/a5_second_boot_backoff_sweep.sh:467) と [f851-verbatim.md](/home/SFC/tanab/.claude/jobs/b550caea/tmp/wave-t2347/f851-verbatim.md:3) の実観測が一致する。
   - 放置時の land 値: 現在の2 job について locked が原因で案 (a) が効かず rc=31 のままになることはない。

7. **同じ `/scr` 登録が fold gate 後の別の明示的 worktree 検査で再び赤になる懸念は反証された。**

   `dev_wave_land.py` 内の `("worktree", "list", "--porcelain")` は1回だけです。後段の control snapshot は共有 admin 全体でなく main 配下の `.claude/worktrees` と `.codex/worktrees` を見るため、外部 `/scr` 登録は対象外です。

   - 根拠 (refuted): [dev_wave_land.py:1604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:1604)、[同:3449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449)、[同:5492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:5492)。
   - 放置時の land 値: fold gate を通過した後、同じ2登録だけを理由に rc=31や別 rcへ戻る経路はない。

8. **Git 版差が silent fail-open を生む懸念は反証された。ただし availability の再発条件ではある。**

   将来の Git が prunable marker を出さなくなれば、提案 parser は record を通常登録として扱い、`resolve(strict=True)` が失敗します。つまり黙って通すのでなく rc=31 へ倒れます。

   - 根拠 (refuted): plan の分岐は marker がある場合だけ `continue` し、marker 不在なら現行の strict resolve を維持する。
   - 放置時の land 値: silent rc=0 にはならない。代わりに F851 型の `rc=31` が再発する。

9. **テストが全面的に合成 stdout だけ、という懸念は反証された。**

   計画 helper は実 worktree add、実削除、実 porcelain を通し、さらに prunable 行の存在を assert します。分類器の正例としては production Git の機構を通ります。

   - 根拠 (refuted): [plan.md](/home/SFC/tanab/.claude/jobs/b550caea/tmp/wave-t2347/artifacts/t2347-scr-worktree-land/plan.md:59) の `_make_prunable_worktree`。
   - 放置時の land 値: Git が当該環境で marker を出さなければテスト自身が赤になるため、誤って rc=0 を保証したことにはならない。ただし所見4の end-to-end 欠落は残る。

## 案 (a) と案 (b) の独立評価

10. **理由 (i): 案 (a) は未来の job に一般化できる、は条件付きで real。**

   中央の land を直すため、将来の script が共有 repo に作った**unlocked かつ Git が prunable と分類する**登録には効きます。一方、portable worktree を prune から守るため正しく `worktree lock` する future job には効かず、案 (a) の strict resolve が再び rc=31 を返します。

   - 根拠 (real/限定): a5 固有 path を見ず marker で判断する点は一般的だが、locked missing record は marker 対象外。
   - 放置時の land 値: unlocked/prunable は rc=0 側、locked/non-prunable は rc=31 のまま。

11. **理由 (ii): job 専用 clone のコスト懸念は plausible だが、選択根拠としては未立証。**

   superproject と CCBench の双方を用意する必要は実在します。しかし親自身が実測しておらず、clone が walltime を破る、あるいは現在の worktree setup より許容不能に高い、とは言えません。

   - 根拠 (real/未立証): script は superproject と CCBench の2 checkoutを必要とするが、brief に clone 時間・容量の測定値がない。
   - 放置時の land 値: 案 (b) なら共有 registry が汚れず、この型の rc=31 は発生しない。コスト未計測それ自体は land 判定を変えない。

12. **理由 (iii): 案 (b) が現在登録済みの2本に効かない、は immediate remediation として real。**

   script を変更しても既存 admin は消えません。ただしこれは案 (b) の将来再発防止能力への反証ではなく、現在 RUN の2本を即時 unblock する理由としてだけ有効です。

   - 根拠 (real/限定): コード変更は既存 `.git/worktrees/*` を遡及削除せず、F851 の運用手順にも job 終了後の prune が記載されている。
   - 放置時の land 値: 現在の2登録が残る間は案 (b) 単独だと rc=31、終了・適正 cleanup 後は将来 job 由来の rc=31 を防ぐ。

13. **総合評価: exact F851 には案 (a) で足りるが、共有 registry の cross-node 不整合そのものを閉じるのは案 (b)。**

   案 (a) は land の可用性だけを回復し、RUN 中 worktree が login から prunable に見える状態や、第三者 prune、将来の locked registration を残します。案 (b) はこの共有 admin 依存を切ります。ただし F851 の狭い受入条件は「(a) または (b)」なので、案 (b) が必須とまでは言えません。

   - 根拠 (real): (a) は表示結果に基づく例外化、(b) は登録先そのものの分離であり、解消する層が異なる。
   - 放置時の land 値: 現在の F851 は (a) で rc=0 側へ進むが、locked/format-change 条件では再び rc=31。適用後の新規 job に対する (b) にはその残余がない。

## 裁定パッケージ候補 (scope 外の所見)

14. **他 tool の同型箇所は、指定された読み取り射影だけでは行番号・操作を検証できない。**

   `tools/mutation_worktree.py`、`tools/mutation_fanout.py`、`tools/check_acceptance_reds.py` は必読射影に含まれておらず、「次の絶対パスだけを読む」という制約に従って未読です。brief/plan は名前を scope 外として列挙するだけで、該当行や失敗操作を示していません。このため、どの行がどの操作で壊れるかを推測で候補化はできません。

   - 根拠 (real): 許可された6ファイルには各 tool の実装本文がなく、直接検査不能。
   - 放置時の land 値: `dev_wave_land.py` の land 判定は変わらない。他 tool の値は未判定であり、緑・赤のどちらとも報告できない。