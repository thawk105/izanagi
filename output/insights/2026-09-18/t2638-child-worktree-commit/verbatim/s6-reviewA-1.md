## 所見一覧 (番号、real/refuted/unverified、must-fix/nit、根拠、再現条件、成果物影響)

指定資料に限定した静的レビュー。pytest・変更操作は行っていない。**must-fix は 3 件**。主要な発火条件・rc 合成・待ち手の fail-closed 配線は裁定に一致する。

1. **real / must-fix — 死亡後 commit テストが既存診断で赤になり、M13 の基準走が成立していない。**
   根拠: `orchestrator/tests/test_dev_wave_wait.py:5155`（追加 hunk `@@ -5087,6 +5087,136 @@`）、`tools/dev_wave_wait.py` の `_derive_producer_state` → `_initial_start_time`、`s5-focus-run.log`。producer を `communicate()` で回収した後、receipt 公開前の再観測が消滅済み `/proc/<pid>/stat` を読むため診断が出る。ログでも rc・stdout の assert を通過後、空 stderr 期待で失敗している。
   **再現条件・成果物影響:** 実 producer 回収後に receipt を公開する既存経路で再現し、正しい実装も赤になるため、検査レポートと M13 の KILLED 判定を受理証拠にできない。

2. **real / must-fix — docs が裁定で必要とされた運用境界を省いている。**
   根拠: `docs/dev-wave/workers.md:26` 相当（`s6-docs.diff` の DW-S05-A hunk）、裁定 A1・A10・B-不足2・§2.4。追加文は「実装子の残差は起動器/待ち手 (`--commit-worktree`) が終端 commit」のみ。「投入先 worktree **全体**」「記録であり採用・land・撤去とは別」「待ち手の対象を呼出側が正しく指定する」がない。待ち手は receipt の sandbox/stage を検証しない設計なので、最後の条件は実効的な境界である。
   **再現条件・成果物影響:** read-only 子の worktree に誤って flag を付けると残差が commit され、誤った対象の HEAD・保存対象集合が変わる。commit を採用証拠と誤読すると台帳の参照・受理判断も変わり得る。

3. **real / must-fix — `NamedTemporaryFile(dir=None)` は repo 外を保証しない。**
   根拠: `tools/dev_waves/git_state.py:313`、helper 追加 hunk。`dir=None` は裁定の指定コードには一致するが、Python 側の一時ディレクトリ選択は `TMPDIR` 等に依存する。`_git_env()` の制限はこの Python 側選択に作用しない。`finally` の削除は実装済みだが、配置の保証とは別である。
   **再現条件・成果物影響:** 新規プロセスで `TMPDIR` を worker 内の書込み可能ディレクトリにすると本文を含む一時ファイルが repo 内にできる。通常完了時の commit tree は変わらないが、中断時に残ると後続の `add -A` により成果物・所有 path patch へ混入し得る。

4. **real / nit — `<base>` の比較テストは実 Git だが、DW-S05-A の操作列全体を固定していない。**
   根拠: `orchestrator/tests/test_dev_waves_git_state.py:1341` の `test_commit_worker_worktree_records_residue_then_noop`。前処理は `git add tracked`、比較対象も `tracked` だけ。追加・削除は commit tree で別途検査されるが、`git add -A` 後の全所有 path patch の前後一致ではない。
   **再現条件・成果物影響:** 所有 patch に追加・削除も含む場合の抽出回帰を、この bytes 比較だけでは検出できず、展開 patch の受理証拠が狭い。現実装の patch 欠落は確認していない。

5. **refuted / nit — 通常の拒否・延期・失敗分類、および launcher rc 合成に抜けがあるという疑い。**
   根拠: `tools/dev_waves/git_state.py:247` 以降、`tools/dev_wave_codex.py:348` 以降。root 不一致・主 checkout・detached・main/master は `refused`、5 marker は `deferred`、Git 非0・timeout・stdout 非UTF-8 は `failed`。追加 allowlist は指定の5操作だけで、全 Git 呼出しが既存 `_run`・hardening・`_git_env` を通る。add/commit は120秒。launcher 非0は維持し、0かつ refused/failed のみ3になる。
   **再現条件・成果物影響:** 裁定表の各通常ケースでは予定どおり成功集合が制限され、保存失敗を成功として受理する分岐は見つからない。

6. **refuted / nit — 対象外経路と待ち手の終端配線が契約を破るという疑い。ただし非 author/fix の stdout は明示的例外。**
   根拠: `tools/dev_wave_codex.py:347`・`:354`、`tools/dev_wave_wait.py:1975`・`:1989`・`:2007`・`:4484`。read-only・dry-run は helper に入らず、flag 無しの待ち手は旧成功判定を保つ。DEAD の break 後に一度だけ helper を呼び、refused/failed なら成功 receipt の公開経路へ進まない。check-only に helper 呼出しは追加されていない。workspace-write の非 author/fix は **stdout に skipped 行を追加する**が、これは裁定 §2.2 の明示要求である。
   **再現条件・成果物影響:** 非 author/fix の workspace-write では stdout bytes は変わるが、Git・rc・receipt はこの変更から影響を受けない。「stdout も完全不変」という依頼文の一般表現とは区別が必要。

7. **refuted / nit — provenance の順序・正規化・trailer 混入防止が欠けるという疑い。**
   根拠: `tools/dev_waves/git_state.py:279` 以降、provenance テスト追加 hunk。非空文字列の recorded → requested → unknown、正規化後の `none` → unknown、本文の改行・`;` 除去、最終段落の固定 trailer が実装されている。テストは実 commit message を読み、実 checker の `AGENT_VALUE.fullmatch` と `none` 不在を検査する。
   **再現条件・成果物影響:** 登録された欠落・空白・NONE・混入ケースでは形式違反や偽 trailer による provenance 受理集合の拡大は見つからない。一時ファイル配置は所見3。

8. **unverified / must-fix（受入完了判定）— 全走・変異実走の成立は未証明。**
   根拠: `s5-author-1.md` は pytest・M0〜M14 未実走と明記。親の `s5-focus-run.log` は **461 passed / 1 failed、child rc=1、focus rc=1** で、受入全走ではないと明記する。追加テストは実 repo・実 dispatcher・実 producer を使っており、fake launcher は裁定で許容された入力生成役。対象 helper の代役化や揮発 SHA の焼込みは見つからない。
   **再現条件・成果物影響:** この焦点走や以下の静的予測を全受入・変異通過と記録すると、検査レポート・台帳の証拠範囲が実測を超える。これは追加の実装欠陥件数には含めない。

## 変異 M0〜M14 の静的検証

以下は**実走結果ではなく予測**。テスト名は裁定 §3 の登録名を指す。

| 変異 | 静的判定 | 殺す根拠・再照準 |
|---|---|---|
| M0 | SURVIVED 期待 | 真に docstring/comment の等価変更なら観測値は不変。ただし現在の焦点走全体の赤を対照成功とは扱えない。 |
| M1 | KILLED 期待 | `test_read_only_and_non_author_never_commit` の read-only author が commit され、空 stdout・HEAD/index 不変に違反。 |
| M2 | KILLED 期待 | 同テストの workspace-write plan が commit され、skipped 行・HEAD/index 不変に違反。 |
| M3 | KILLED 期待 | 拒否テストの実 detached repo が `refused detached-head` を返さなくなる。 |
| M4 | KILLED 期待 | 同テストの main/master が commit 可能となり、status・HEAD 不変に違反。 |
| M5 | KILLED 期待 | primary 判定反転で期待理由が変わるか、主 checkout を commit し、拒否テストが失敗。複数ケースが落ち得るため expected node は較正が必要。 |
| M6 | KILLED 期待 | 実 merge conflict のテストが `deferred operation-in-progress` を要求。marker を空にすると add へ進み、status または unmerged index 保持に違反。 |
| M7 | KILLED 期待 | 初回の staged 差分を clean と判断すれば、records テストの最初の `committed` assert で失敗。 |
| M8 | KILLED 期待 | author/fix × launcher rc=7 の実 dispatcher テストが returncode=7 を要求。 |
| M9 | KILLED 期待 | identity 欠落による実 commit 失敗で `test_terminal_commit_failure_rc` が3を要求。 |
| M10 | KILLED 期待 | records テスト内 `_worker_trailer` の「AI-Agent 行が1本」で失敗。 |
| M11 | 両変異とも KILLED 期待 | requested 優先は最初の recorded 優先ケース、none 写像除去は NONE ケースと明示的 none 拒否で失敗。**2つの独立した anchor に分けて較正する。** |
| M12 | KILLED 期待／anchor 要確定 | 無条件に有効 repo を渡せば空 stdout または HEAD 不変に違反。単に guard を削除して `None` を渡す変異でも落ちるが、それは型エラーであり保存境界の証明として弱い。flag 無しで実 cwd repo を対象にする実行可能な変異へ再照準。 |
| M13 | **現状は有効な KILLED 判定不可** | 生存中 sleep seam の HEAD=base assert と最終 residue 検査は早期 commit を検出できる設計。ただし元実装が空 stderr assert で赤。所見1を修正後、前倒しした helper だけを理由に落ちることを確認する。 |
| M14 | KILLED 期待 | dirty worker の dry-run テストが HEAD/index 不変・commit 行なしを要求し、helper 呼出しを検出する。 |

## 推奨する fix

1. 死亡後テストの stderr 期待を、実 PID から生成した既存診断の**文言・件数**に合わせる。生存中の HEAD 不変、最終 residue、commit 数、receipt 成功の assert は維持する。無条件の stderr 無視や PID 観測の stub 化は不要。
2. DW-S05-A に「worktree 全体の残差」「保存は採用・land・撤去と別」「`--commit-worktree <絶対パス>` は呼出側が workspace-write author/fix の対象に限って指定」を明記する。
3. 一時メッセージの配置先を resolve して repo 外と保証する。repo 内 TMPDIR を与える別プロセスの検査を追加し、成功・commit 失敗時の削除も確認する。
4. patch 比較は所有する tracked 編集・追加・削除を `add -A` 後の固定 `<base>` から抽出し、helper 前後で bytes を比較する。
5. 基準走を緑にしてから M0〜M14 を較正する。M11 は二変異、M12 は型エラー回避、M13 は所見1の赤との分離を明示する。

## 総括

**現状は受入保留。** 修正対象は死亡後テスト、docs の運用境界、一時ファイルの repo 外保証の3件。発火条件、拒否・延期・失敗分類、launcher rc 合成、待ち手の死亡後一回実行と receipt 公開抑止、provenance 生成は静的には裁定に一致する。

実測済み証拠は焦点走の **461 passed / 1 failed**。M0〜M14 の結果は未実証であり、特に M13 は基準走の赤を解消するまで有効な変異判定に使えない。