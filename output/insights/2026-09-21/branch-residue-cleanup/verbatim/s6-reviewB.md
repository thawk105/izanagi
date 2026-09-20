## RB-1. DW-O28 に裁定済みの限定が欠けている

**real / must-fix。**

根拠: `s4-adjudication.md:18,27`、`dw-o28-new.md:4–6`、[dev_wave_cleanup.py:1901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1901)。

- 「不成立・不明は拒否し木と branch を残す」が**撤去開始前に限る**と書かれていない。実装は木・admin 撤去後の branch 削除失敗で rc=30 となり、木は残らない。
- 「統合証明済みの子 branch」は、裁定が要求した **manifest の現行 branch だけ**という限定が明示されていない。
- 「履歴を bundle 後」は、実装の「HEAD が main 祖先なら bundle 不要」と一致しない。

影響: 失敗後の残存状態と削除対象、証拠の必須条件を誤読させる。993 bytes に収まったことは意味保存の証拠にならない。

最小修正: 「撤去前の不成立・不明」「manifest 現行 branch」「main にない履歴を bundle」の限定を入れる。

**refuted:** 「他へ引き渡さない」への圧縮自体は、撤去義務を主語として読めば D702 の列挙を包含する。根拠は [decisions.md:27707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/decisions.md:27707)。ここは修正不要。

## RB-2. bundle の実行順は段 4 と異なるが、安全側の変更

**real / 記録修正。**

根拠: `s4-adjudication.md:18` は「detach → 木 → admin → 不在確認 → bundle → -D」。現物の [dev_wave_cleanup.py:1854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1854) は「backup → bundle → detach → 木 → admin → -D」。

影響: bundle 失敗時に木・admin が残る。テストもその挙動を固定している（[test_dev_wave_cleanup.py:2380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:2380)）。合理的な変更だが、`s5-authorA-fix2.md:17` の「処理順序…維持」を段 4 との一致として扱えない。

最小修正: 最終裁定・記録に「bundle を撤去前へ移動し、退避失敗時は木を保持」と明記する。コードを危険側の順序へ戻す必要はない。

## RB-3. 過剰実装は ref 名検証の重複が中心

**real / nit。**

根拠: [dev_wave_cleanup.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:313)、[同:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1523)。

bundle validator は Git の ref 名規則を手実装しているが、本番入力の `proof.branch` は既に `git check-ref-format --branch` を通っている。固定 argv、証拠 path、full branch ref、除外 SHA の束縛を残せば、細かな ref 文法の再検査は正常な呼出し経路では重複する。

削減候補は次のとおり。

- ref 文法の手実装と、その網羅テスト（`test_dev_wave_cleanup.py:2455`）。削減すれば validator 単体の受理集合は変わるため、「全 API の意味不変」とは言わず、内部呼出し契約で整理する。
- `deleted_branch_tip`（tool:1942）は既存 `HEAD` と同値。監査情報として重複しており、新 receipt schema を確定する前なら削減候補。
- submodule 正例の未使用 `head = _sha(case.child)`（test:531）は、そのまま削除可能。

**refuted:** docstring の追加8行、bundle digest、integration の根拠、専用削除順テストを一括して過剰とは判定しない。履歴保全と内容統合の区別、再実行、部分失敗を説明・検査しており、段4:17,48 に対応する。receipt field 数自体にも裁定上の上限はない。

## RB-4. 既存テストの期待値変更と F649 型の疑い

**refuted。**

根拠: `impl-diff-all.patch` と [test_dev_wave_cleanup.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:172)。

- `keeps_branch → deletes_branch` は今回の意味変更そのもの。bundle を別 repo へ取り込み、中間 commit の内容まで復元している。
- reflog 保持例（test:320）は現行 `other` を削除し、旧履歴を保持する `author` の不変 assertion を残している。
- already-clean（test:444）、submodule 正例（test:530）は branch の事後条件だけを変更。submodule 負例は保持されている。
- `-D` 全面禁止は、validator の固定形許可と共通 runner の実行拒否へ分割されている（test:2311）。許可の拡大に直接対応する。

新負例も、bundle を実際に壊して実 Git を呼び、branch lock file で実削除を失敗させる（test:2365,2389）。F649 の「機構を stub して一度も通さない」型ではない。

`assert receipt['history_bundle_reason']`（test:2353）は**弱い非空検査**だが恒真ではない。空文字・None への変異で落ちる。理由の正確性を契約にするなら期待値を固定し、単なる補助情報なら現状でもよい。安全機構の代替に数えないこと。

## RB-5. M0〜M9 の anchor と失敗 node 予測

**refuted:** anchor 不成立、および「全件 SURVIVED 指定だから不正」という疑い。

`mutation-spec-probe.json` の実 bytes を現物と静的照合した結果、**M0〜M9 の old は全て1か所**。new は M6 だけ既存1か所、他は0か所だった。M6 の new は元コードにも含まれる末尾部分であり、old の一意性を壊さない。

全件 `SURVIVED`・期待 node 空は probe として [DW-M07:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/dev-wave/mutation.md:49) に合う。以下は実走結果ではなく予測である。node 名は `test_dev_wave_cleanup.py` 内。

| 変異・tool 行 | 単一理由性と予測 |
|---|---|
| M0:13 | docstring の説明追加だけ。削除動作について等価、SURVIVED 予測。実注入・復元確認は別途必要。 |
| M1:1918 | 非祖先子の `-d` が拒否され、`test_remove_child_archives_dirty_integrated_author_and_deletes_branch` が落ちる。他の非祖先成功例にも波及する。正常受理の縮小として有効。 |
| M2:1936 | 呼出しごと省くので、関数内の削除後検査も消える。上記正例の ref 不在 assertion、`test_remove_child_ancestry_child_skips_bundle_and_deletes_branch` 等が落ちる。有効。 |
| M3:1863 | 上記正例の bundle 実在検査が落ちる。`test_remove_child_bundle_verify_failure_is_partial[create/verify]` も注入地点へ到達せず落ちる。有効だが正例の検出を主証拠にする。 |
| M4:1570 | `test_remove_child_rejects_unintegrated_author_commit` と `test_remove_child_empty_owned_paths_requires_ancestry` が落ちる予測。fixture の履歴は子 branch から到達でき、内側 history gate は代替拒否しない。再検査も同じ変異済み関数を呼ぶ。有効。 |
| M5:1334 | 共通 `_git` が `-D` を拒否する。`test_wave_cleanup_uses_only_lowercase_d` と `test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist` が落ち、他の wave 成功例にも波及。専用禁止境界の突破証拠にはならない。 |
| M6:329 | validator は固定形を受理済みなので `test_common_git_runner_rejects_force_delete` が落ちる。共通 runner の実効 gate に照準できている。 |
| M7:1875 | `[verify]` は壊れた bundle のまま削除が進み、期待例外が出ず落ちる。`[create]` は後続の directory 読込み失敗に mask される。次節参照。 |
| M8:1935 | `test_remove_child_branch_delete_failure_is_partial` の phase assertion だけが落ちる。削除拒否・rc=30・receipt 不在は不変。 |
| M9:1782 | `test_remove_child_receipt_rejects_recreated_branch` が落ちる。再出現 branch を他の receipt 検査は拒否せず、already-clean に流れる。有効。 |

影響・最小修正: M1/M2/M3/M5 は上表だけを**完全集合**として登録しない。probe で全失敗 node を確定して再登録する。DW-M08:59 が完全一致を要求しており、静的予測だけで本走 KILLED と扱えない。

## RB-6. M7 の create は mask、M8 は診断感度に留まる

**real / must-fix（変異評価）。**

根拠: `mutation-spec-probe.json:111,125`、tool:1875–1879、test:2369,2405、[DW-M03:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/dev-wave/mutation.md:18)、[DW-M08:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/dev-wave/mutation.md:61)。

- **M7/create:** create 失敗を無視しても、`history.bundle` は directory。後続 `bundle.open("rb")` が失敗し、同じ rc=30・phase・保持状態になる。単一理由性を満たさない。
- **M7/verify:** 壊れた通常 file は後続で読めるため、戻り値無視が削除許可へ直結する。この fixture は有効。
- **M8:** 段4:64 の「削除失敗でも成功／receipt」から「phase 誤表示」へ変わっている。KILLED に数えてはならない。
- **M5:** 共通 runner による防御が残る。wave の正常成功を壊す変異としては観測できるが、「wave が force 削除できる穴を検出した」とは言えない。

最小修正: M7/create を単独 gate の証拠から外し、verify を主証拠にする。M8 は diagnostic sensitivity pin へ分離し、段4で要求した fail-open 変異を別途再照準する。M5 も証明対象を正常受理の縮小と明記するか、安全境界の登録から外す。

## RB-7. decisions の対応表には漏れと引用の不正確さがある

**real / 記録の must-fix。**

根拠: `frag-decisions-draft.md:38–41`、[decisions.md:68183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/decisions.md:68183)、[同:62028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/decisions.md:62028)。

- D2163 が却下したのは「登録専用 CLI、**履歴 pack**、子 branch の `-d`」。今回 bundle を採用するのに、表は履歴退避の却下を supersede する対応を落としている。
- D2042 本文には表が引用する「`ahead=0` のみ `-d`、`-D` 禁止」という逐語文はない。それは現行 command §2:46 の文。D2042 の直接の変更対象は「削除の述語の連言と閾値は変えない」という決定である。

影響: どの既存制約を更新したか追跡できない。

最小修正: D2163 の履歴 pack 却下を、子 branch 削除に必要な bundle に限って更新すると追記。D2042 の行は本文の実際の決定と command の実文を区別する。D204・D703 の狭い例外と wave 本体 `-d` 維持の整理は整合している。

## RB-8. 数値は母集団の混同が残る

**real / 記録修正。**

根拠: `frag-decisions-draft.md:44–50,65`、`frag-failures-draft.md:13–18`、`s4-adjudication.md:21–23,28`。

「165 本のうち4本削除、**残る155本**」は算術上も母集団上も成立しない。155 は指示時の数であり、140 は削除実績、24 は除外内訳である。時点の異なる観測を差引きとして接続している。さらに全155本の原因を patch 統合と断定するのは、段4が認めた「原因別比率・被覆割合は未確定」を超える。

最小修正: 各数字を独立した観測として書き、「patch 統合で非祖先 branch が残る経路がある」と機構に限定する。

**refuted／確認限界:**

- 227+21=248、161+66=227 は整合する。161を landed としていない点も裁定に従う。
- 除外24の内訳11+7+1+5は整合する。
- 約40 wave は概算と明示されている。
- **1,721 は指定された brief・裁定・fragment に登場しない。** 正誤を確定する資料がない。
- 00:20〜00:46、00:40頃、00:46 は brief・裁定との相互整合はある。ただし26分全体を「手作業の裁定」の純所要とする分解は示されていない。「cleanup session 約26分」とするのが適切。
- 段3原文と削除実測 TSV は指定資料に含まれず、今回は原文までの独立照合をしていない。

「Git object は延命しない」は段4:17 が明示的に要求した区別であり、不要な「言わないこと」の混入とは判定しない。

## RB-9. failures の恒久対応は一部がまだ実体化していない

**real / 完了扱いの留保。**

根拠: `frag-failures-draft.md:20–26`、[cleanup-branches.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/.claude/commands/cleanup-branches.md:12)、[同:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/.claude/commands/cleanup-branches.md:46)。

経路1の tool と名指しテストは存在する。一方、現在の command は `-d` のみで `-D` 禁止のまま。経路2と新 DW-O28 の pin は、下書きが述べる完成状態の実体ではない。

影響: author B 待ちの下書きとしては理解できるが、この状態で「恒久対応完了」として取り込めない。最小修正は、最終差分で command・overlay・pin の実在を確認してから完了形へ確定すること。

**refuted:** `[手順漏れ]` は、生成に対応する撤去経路が欠けたという記述に合う。F747 の越権とは異なる型であり、新 F 自体は段4:34でも採用済み。証明不能な子を経路2の候補に含める記述は、別実行で条件を満たす場合の回収と限定すれば、段9からの名指し引渡し禁止と矛盾しない。

## RB-10. f2 に分類すべき FAILED はない

**refuted。**

根拠: `focus-f2.log:10,30,38,58–60,66`。

集計は **1011 passed / 5 skipped / child rc=0**。FAILED 一覧は存在しない。

- 本 wave 起因のテスト赤: 0
- 非帰属のテスト赤: 0
- 偽赤として除外する FAILED: 0

末尾の `recording-unavailable:series-invalid` は計測記録の診断で、pytest failure ではない。開始02:26:50、終了02:28:57。ログ自身が受入形ではないと警告しており、受入全走の代用にはならない。

最小修正: 赤の分類を捏造せず、この集計と検証範囲だけを記録する。本レビューでは pytest・変異を実走していない。

## 総括

**NO-GO。**
must-fix: DW-O28 の限定、M7/M8 の評価と段4の削除失敗変異、decisions の supersede 対応・母集団表現。
完了条件: 経路2・文書 pin の実体化と、probe 後の期待 node 完全集合の確定。
nit: ref 文法の重複、receipt の重複 field、未使用変数。f2 自体は緑。