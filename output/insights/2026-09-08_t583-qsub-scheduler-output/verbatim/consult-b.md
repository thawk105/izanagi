## 所見 1: 計画した負例は恒真ではなく、封じ込め判定を実走で発火させる

根拠 (`plan.md:41-60,145-177`): separate-git-dir 配置から repo 内候補を導出し、事前条件を独立に確認した上で、最初の `scheduler_root_is_outside_repositories` 呼出しを撃つ。source 文字列一致ではない。対象 script では現行 `tools/pegasus/submit_certify.sh:84-100` の dirty gate と staging 作成の間に入る分岐である。

影響: 判定を無条件 true にする (m3) と rc=0、`qsub command:`、staging 作成へ進むため、負例は赤になる。候補集合から述語が自動的に真になる構造でもない。

推奨 (採用): 負例の構造を維持し、実装後も最初の containment 呼出しが staging より前にあることを確認する。

## 所見 2: 拒否に対する通る正例があり、受理集合も示されている

根拠 (`plan.md:115-138,179-182`): 正例は通常の common-dir 配置で rc=0 と qsub argv 到達を要求し、負例は repo 内候補だけを rc=2 で拒否する。`-o`、`-e` の値は argv から解析され、絶対 path、repo 外、期待 root、nonce 付き leaf を検査する。

影響: 「常に拒否すれば緑」という過剰拒否を防げる。m1、m2、m4 の主要形もこの正例で検出できる。

推奨 (採用): 正例と負例を必ず対で実装する。

## 所見 3: staging と receipt の不在は検査できるが、qsub 非実行の因果は検できない

根拠 (`plan.md:163-177`; `tools/pegasus/submit_certify.sh:99-100,130-165,181-188,213-242`): 負例は attempts root と scheduler root の不在を要求する。submission directory、`pre-submit.json`、`submit-receipt.json` は attempts root の子なので、その不在でまとめて否定できる。一方、`--dry-run` は containment の成否とは独立に `tools/pegasus/submit_certify.sh:181-185` で qsub を実行しない。`qsub command:` 不在は command 構築へ未到達という証拠であって、qsub 呼出しの spy ではない。

影響: (m5) の単純な後方移動は staging と command 表示により赤になるが、「この判定が実投入の qsub を止めた」とまではテスト結果から言えない。

推奨 (削る): 負例の保証文から「qsub 非実行を実測した」を削り、「staging と qsub command 構築より前に拒否した」と限定する。

## 所見 4: 負例入力は到達可能だが、brief の事故型との同一視は誤りである

根拠 (`plan.md:151-161,184-188`; `tools/pegasus/submit_certify.sh:27`; `brief.md:60-61`): `--repo-root` は既存 CLI であり、Git が正式に作る internal separate-git-dir から repo 内候補を導出できる。したがって入力自体は到達可能である。ただし、既存事故は `-o`、`-e` が無いことで scheduler が cwd へ既定出力した機構であり、提案された common-dir root 導出が repo 内になった機構ではない。

影響: 負例は実在する CLI と Git topology を通る有効な containment 負例だが、記録済み事故そのものを再現するテストではない。事故型の m1 は正例の argv 検査が捕捉する。

推奨 (削る): `brief.md:60-61` の「実際に今まで repo root へ返っていたのがこの型」という同一視を削る。負例は「到達可能な別の不安全 topology」と記す。

## 所見 5: brief の「qsub 実行時 cwd = repo root」は一般には成立しない

根拠 (`brief.md:19-21`; `addendum.md:16-18,26-29`; `tools/pegasus/submit_certify.sh:27,176-188`; `docs/pegasus-runbook.md:103-105,151-152`): script は `--repo-root` を解決するが、qsub 実行前にそこへ `cd` しない。現行 qsub は呼出し元 cwd で実行される。runbook も既定出力先を「投入時のディレクトリ」としている。

影響: repo root から投入した記録済み運用では事故説明が成立するが、任意の invocation へ一般化できない。別 cwd なら、未指定出力はその cwd を汚す。提案する絶対 `-o`、`-e` はこの差に依存せず修正として有効である。

推奨 (削る): `= repo root` という一般化を削り、「記録済みの repo-root cwd からの投入では repo root」と限定する。

## 所見 6: dry-run が検査するのは argv と投入前準備までで、NQSV の受理と書込みではない

根拠 (`plan.md:224-233`; `tools/pegasus/submit_certify.sh:115-128,181-195`; `docs/pegasus-runbook.md:1585-1590`; `addendum.md:37-49`): dry-run は root 導出、正規化、mkdir、leaf path 構築、argv 表示を通るが qsub を起動しない。外部 file path が実際に動いた precedent は addendum にあるものの、新しい exact path の投入ではない。

影響: dry-run では次を観測できない。

- directory path に対する `NQScrereq: [BSV EINVAL] Not a regular file.`
- qsub 時点での親 directory 消失
- scheduler 側から見た親 directory の権限と filesystem 可視性
- leaf が既存 directory、symlink、非 regular file だった場合の扱い
- 相対 `-o`、`-e` の scheduler による解決基準
- qsub が argv を受理した後、指定 leaf に実際に stdout、stderr を作ること

正例の絶対 path、leaf basename、非 directory という argv 主張は m2、m4、相対 path 変異を静的に捕捉するが、scheduler の挙動を実測したことにはならない。

推奨 (不採用): dry-run 緑を実投入成功の証明として扱うことは不採用。テストは argv 契約の証拠として採用する。

## 所見 7: pin 閉包不在は実測ではなく、説明不足の静的探索である

根拠 (`brief.md:45-55`): 現在の `submit_certify.sh` の SHA-256 は brief 記載値と一致する。一方、閉包不在の根拠として示されるのは current hash literal と path consumer の探索結果だけで、探索 command、対象 revision、directory-level consumer の扱いは示されていない。

影響: current hash や exact path を持たず、`tools/pegasus/*.sh` のような集合を走査して aggregate hash を作る consumer は反例になり得る。したがって「literal pin は見つからなかった」は支持されるが、「pin 閉包は不在」までは支持されない。

推奨 (削る): 閉包不在という全称否定を削り、「報告した静的探索では exact path/current SHA の pin を発見しなかった」に狭める。

## 所見 8: 重複編集面の否定は瞬間的な実測だが、稼働 wave 不在までは証明しない

根拠 (`brief.md:56-59`; `docs/pegasus-runbook.md:842-846`): worktree の dirt と `main...HEAD` の走査は、その時点の編集差分についての実測である。しかし runbook は稼働 wave の正本を repo 外 handoff としている。clean だが同じ file を担当している wave、または走査後に編集を始める wave は diff 走査だけでは見えない。

影響: 「走査時点で既存差分なし」は成立し得るが、「触っている稼働 wave は無い」という一般化には反例があり得る。今回の plan の正否とは独立した、brief の証拠範囲の問題である。

推奨 (削る): 稼働 wave 不在という全称否定を削り、時刻付きの「走査時点で既存 dirt/commit 差分なし」に限定する。

## 変異対応表

| 変異 | 赤になる計画テスト | 赤になる理由 | 穴 |
|---|---|---|---|
| (m1) `-o` / `-e` を削る | `test_submitter_dry_run_routes_scheduler_files_outside_repo` | argv から両 option と直後の値を取得できない | なし |
| (m2) 値を repo 内へ差し替える | 同上 | fixture repo/common repo 外という assertion に違反 | なし |
| (m3) containment を常に true | `test_submitter_rejects_repo_internal_derived_scheduler_root_before_side_effects` | rc=2 にならず、staging と command 表示へ進む | なし |
| (m4) directory path を渡す | 正例テスト | root 自体なら非一致と leaf basename が失敗し、既存 leaf directory なら「leaf 不在」が失敗する | 計画どおり全 assertion を実装することが条件 |
| (m5) 判定を qsub 後へ移す | 負例テスト | delayed 判定より前に attempts root、staging、`qsub command:` が現れる | 単純移動は殺せるが、dry-run なので実 qsub 非実行の因果は観測しない |

## 総括

- 最重: 負例は分岐を実走するが、dry-run のため containment が実 qsub を止めたとは証明できない。
- 次点: brief の「qsub cwd = repo root」と DW-O13 の事故型同一視は、現行 script の制御と一致しない。
- 次点: pin 閉包不在と稼働 wave 不在は、報告された探索範囲を超えた全称否定である。
- 指定された (m1) から (m5) には全て赤になる計画テストがある。静的検査のみで、書き込みとテスト実行は行っていない。