## 総括

P1 を前提に、**再投入せず、既存 cohort の判定・証拠の所在・今回の確認範囲を記録する 3 ファイル**を作る。実装差分はゼロでよい。  
最大の異議は、brief が「初回の束縛記録」を「2 回目の投入禁止」まで拡大解釈している点である。再投入しない判断と、その根拠の強さは分ける。  
2026-09-15 の結果は既存結果として扱い、今回新たに測定・認証したとは書かない。T-2647 の図表・主張への採用判断は残す。  
insight は現行規約に従い日付ディレクトリへ置く。以下は静的調査による plan であり、ファイル変更・commit・テスト実行は行っていない。

## 書く file と主張

**1. `output/insights/2026-09-16/b10-tail-formal-submit.md` — 新規**

今回は単一の文書なので、この配置を採る。根拠は [output/README.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-formal-submit/output/README.md:73) の単一資料の例と同 :82–85 の日付ディレクトリ規約。複数ファイルを保存する場合だけ、`2026-09-16/b10-tail-formal-submit/README.md` とその配下へ変更する。

本文は次の順で書く。

| 挿入箇所 | 書く内容・主張 | 根拠 |
|---|---|---|
| 新規ファイル冒頭 | 題「B-10 静的 backoff 右 tail — 既存本走の確認と再投入しない判断」。`authority: none`、`default_effect: no-state-change`。確認日・wave・親が確認した HEAD を記す | `output/README.md:89` |
| §1 結論 | 09-15 cohort が既に集団判定を持つため、本 wave は新しい cohort を投入しない。判定は `not-observed-in-any-workload`、性能は未認証 | 既存 insight `:82–103`、親の射影 |
| §2 証拠の所在 | group、3 job、外部 root、報告 3 ファイル、commit/blob/spec、complete manifest に記録された JSON/DAT の digest を転記する | 既存 insight `:82–88`、親の射影 |
| §3 確認表 | submission §1 の 5 条件と事前登録 §8.1 の 5 条件を**別表**にする。今回の確認、過去の実測記録、未確認を区別する | submission `:15–25`、事前登録 `:1034–1047` |
| §4 再投入しない理由 | 依頼の測定・集団報告は既に存在する。追加 cohort の目的・合成・選択規則はこの wave では定めない。既存結果を取り直す根拠も今回示されていない | brief `:19–21`、事前登録 `:29–36`、`:1052–1053` |
| §5 下流への引渡し | 下記 consumer 棚卸しと、T-2647 が未了であることを記す | archive `:692–701` |
| §6 限界・検査 | 「飽和が存在しない」「機序を説明した」「性能を認証した」「B-10/T-2266/T-2647 を閉じた」とは主張しない。実施した静的調査だけを記す | 事前登録 `:129–140`、既存 insight `:29–36` |

証拠の記載では、次を明示する。

- 外部ファイルの実在・scalar 値・hash は**親の 2026-09-16 11:20 JST 実測の射影**。この段の独立再測定ではない。
- complete manifest の digest は「manifest に記録された値」。JSON/DAT の現物との再照合を済ませたとは書かない。
- `completion.json` 3/3 は完走の証拠であり、valid の単独の根拠ではない。submission `:74–77` が明示している。
- 24 cell・120 correctness 記録・anomaly 0・失敗 0 は、既存 insight `:93–103` の記録に基づく。今回 WAL 全件を再監査したとは書かない。

submission 条件表の結論は以下とする。

1. repo root からの投入：**今回は投入しないため非該当**。過去の実績は既存 insight `:165–168`。
2. 祖先性：親の現 worktree における確認は成立。新しい計算ノード checkout の確認とは区別。
3. 文書 bytes：親の照合で一致。
4. 探索 campaign：射影された v1 の 3 directory は実在。formal driver は mode を歴史的 WAL から読む（driver `:351–358`）。
5. 出力親：親の実測では repo 外の絶対 path。今回は出力を作らない。

§8.1 の各条件には、先行実装の実測表 `output/insights/2026-09-14_t2566-tail-formal-driver/README.md:24–30` をそれぞれ対応づける。**過去の実測根拠を確認したことを、今回の発火試験の成功へ言い換えない。**

**2. `docs/spool/worklog/2026-09-16-dev-wave-b10-tail-formal-submit-1.md` — 新規**

骨格：

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-b10-tail-formal-submit
seq: 1
title: B-10 右 tail の既存本走を確認し再投入しない (docs + insight、branch worktree-dev-wave-b10-tail-formal-submit)
---

## 本文

- 親が外部成果物を確認した日時・方法・結果と、その確認範囲。
- 再投入しない判断は {{D:tail-formal-no-second-cohort}}。
- brief の訂正、協議で採否を決めた論点、実際に行った検査を記録する。
- 証拠の整理先は output/insights/2026-09-16/b10-tail-formal-submit.md。

## 次の一手差分

### carry

- [T-2647]
```

**base digest：不要、付けない。** この plan は既存項目を更新・完了・見送りにせず carry する。根拠は `docs/spool/worklog/README.md:58–66`、`:81–91`。T-2647 は「どの図表・主張へ載せるか」が未定なので、今回の完了へ振り替えない。

親が T-2647 の本文更新まで追加する場合だけ、land 先 local main で `python3 tools/spool_fold.py --base-digest '[T-2647]'` を実行し、その値を使う。archive 本文や carry stub を手計算した digest で代用しない。

**3. `docs/spool/decisions/2026-09-16-dev-wave-b10-tail-formal-submit-1.md` — 新規**

骨格：

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-b10-tail-formal-submit
seq: 1
---

## {{D:tail-formal-no-second-cohort}}. 既存の右 tail 本走結果を参照し本 wave では再投入しない

**決定:** 2026-09-15 の cohort と集団報告を既存結果として参照し、
本 wave は第 2 cohort を投入しない。図表・論文主張への採用は別作業に残す。

**理由:**
- 依頼された測定と集団判定は既に存在する。
- 今回、取り直しを必要とする根拠は示されていない。
- 追加 cohort の目的・合成・選択規則を結果観測後の本 wave で補わない。

**却下した選択肢:**
- 同じ依頼を未実施とみなして再投入する。
- 事前登録本文や既存成果物を更新して現在の状態へ合わせる。
- この確認だけで性能認証や B-10 全体の完了を宣言する。
```

**title：上記 H2 に置く。frontmatter の `title:` は禁止。base digest：不要。** 根拠は `docs/spool/README.md:39–49`、`docs/spool/decisions/README.md:5–34`。この判断を「ユーザーが永久に再実験を禁止した」とは記録しない。

## 触ってはならない file

| 対象 | 理由・根拠 |
|---|---|
| `docs/b10-backoff-static-tail-preregistration.md` 全文 | raw bytes が束縛対象（同 `:1058–1062`）。結果後の変更は事前登録に数えない（`:17–21`）。過去時点の記述も書き換えない |
| 過去の探索・本走 campaign の `campaign.lock`、`runs/wal.jsonl`、report、completion、外部集団報告 3 ファイル | 事前登録 `:1097–1100`、`output/README.md:53–64`。report は create-only（driver `:645–660`）。再生成・移動・上書きしない |
| `orchestrator/campaign/backoff_extended_sweep.py` と既存格子の pin | 事前登録 `:1067–1068`。具体的な pin は `orchestrator/tests/test_backoff_extended_sweep.py:441`、`:514–515`、`:556–561` |
| `orchestrator/tests/test_b10_backoff_static_tail_formal.py` の spec hash・格子・反復数 pin | 同 `:49–59`。今回の結論のために期待値を変更する必要はない |
| 本走 driver、submit/job script、その他コード・テスト・機械設定 | 新しい測定も実装も要求しない plan。brief `:64–68` の実装差分ゼロと整合する |
| `docs/worklog.md`、`docs/decisions.md`、`docs/failures.md` | wave の直接編集禁止。`docs/spool/README.md:3–5` |
| `docs/spool/FOLDED.md`、既存 fragment の削除 | fold 所有。`docs/spool/README.md:91–98` |
| 09-15 insight、過去 worklog、既存図表・較正入力 | 過去の記録を今回の確認で改変しない。`output/README.md:63–64`。図表への採用は archive `:699–701` の未決事項 |

submission 文書も本 plan では変更しない。`:84` の作成時点の記述は保存し、新 insight から現在の実績を案内すれば足りる。

## 下流 consumer の棚卸し

参照文字列として cohort ID、報告 directory、verdict、run kind、driver 名、T-2647、既存 insight path を追った。**09-15 の実測 verdict を読み込む実行 consumer は、調査した repo 範囲で 0 件。文書上の引渡し先は存在する。**

| consumer／参照先 | 参照関係と判定 |
|---|---|
| T-2647 | `docs/archive/worklog-phase3-0915-1512.md:692–701` が実測 verdict と insight を直接参照し、図表・主張への反映を要求。現行 `docs/worklog.md:1543` でも carry。今回閉じない |
| 09-15 insight | `output/insights/2026-09-15/t2266-tail-band/README.md:103–146` が集団判定・区間表・24 cell 表を掲載。既存の報告文書であり、新しい下流採用ではない |
| 論文 B-10 | 事前登録 `:3–8` → `docs/paper-story/2026-08-26.md:848–851`。関連する主張の候補だが、当該節は機序の未了を述べており、この verdict の入力を要求していない |
| walk model | 09-15 insight `:178–179` → `tools/t2216_backoff_walk_model.py:53–56`。`t2266-tail`、旧 6 点、report/v1 固定。本走 verdict の consumer ではない |
| tail 図生成 | 同参照 → `tools/plotting/plot_t2266_tail_mechanism.py:35–39`、`:142–181`、`:227–231`。固定された旧系列入力を読む。本走 JSON を差し替えない |
| 本走 driver | `orchestrator/campaign/b10_backoff_static_tail_formal.py:800–803` は campaign と探索 mode を入力に report を生成。既存 verdict を取り込む下流 consumer ではない |
| job script | `tools/pegasus/b10_backoff_grid.sh:616–626`、`:694–707` は driver 起動と実行成果物の存在確認。集団 verdict は入力にしない |
| formal テスト | `orchestrator/tests/test_b10_backoff_static_tail_formal.py:33–59`、`:324–362` は spec と試験 cohort を使用。09-15 verdict を期待値として要求しない |
| submission テスト | `orchestrator/tests/test_b10_backoff_grid_submit.py:305–373` は文書の argv と mock verdict の終了コードを検査。実測報告には依存しない |
| driver の登録・閉包テスト | `test_campaign.py:5362`、`test_p3_build_authority_cli.py:148`、`test_official_perf_closure.py:129`、`test_ccbench_spawn_sites.py:54` はコード経路への参照。実測 verdict の consumer ではない |
| D2027 | `docs/decisions.md:61519–61555` は帯測定と本走の scope を区別する既存判断。今回の verdict によって帯の裁定を変更する経路ではない |

これは参照調査の結果であり、「将来 consumer が不要」の証明ではない。

## 親 brief の誤り

1. **成果物の配置が規約と不一致。** brief `:72` の `2026-09-16_b10-tail-formal-submit/README.md` は、新規資料を日付ディレクトリへまとめる `output/README.md:82–85` と合わない。

2. **歴史的記述を「現在は偽」としている。** brief `:36–37`。submission `:84` は明示的に「本書の作成時点では」と限定している。現在の未投入を意味しない。

3. **「初回」から投入禁止を導いている。** brief `:54–57`。事前登録 `:1052–1053` は初回投入時の hash 記録要求であって、2 回目の投入禁止条項ではない。複数 cohort の選択規則が無いことから、再実験が必ず不正な結果選択になるとも断定できない。**今回再投入しない判断**として記録するのが適切。

4. **現在の前提確認と過去の実行条件が混在。** brief `:38–41`。条件 1 が未判定なら「全条件成立」と同義に扱えない。条件 2 も submission `:18` の対象は計算ノードから見える checkout。今回の worktree の祖先性確認とは区別する。

5. **hash 一致から変更履歴まで断定。** brief `:35` の「当時から 1 bit も動いていない」は、提示された照合だけでは過剰。証明されているのは、記録された blob と現在の bytes の同一性。中間履歴に変更が一度も無かったことではない。

6. **探索走の日付の時区が欠落。** brief `:9` は「2026-09-08 完走」。事前登録 `:59` は投入 09-09。提示された directory の `20260908T193601Z` は JST では 09-09 04:36:01 であり、完了日時でもない。日付は時区と投入／完了を分けて記す。

7. **v1 実在と v2 要件の関係を省略。** brief `:39` の括弧だけでは不足。追補 `:1087–1095` の対象は T-2418 の新走で、formal の mode 読出しは driver `:351–358` の historical 経路である。v2 directory が深さ 4 まで見つからないことだけで、既存本走を無効にしたり探索再走を要求したりしない。

## 未解決・親へ返す判断

- 親の最終裁定で P1 を確定してから decisions fragment を書く。理由は「既存結果で今回の測定依頼を満たす」に置き、永久的な再実験禁止へ広げない。
- **T-2647 は carry。** どの図表・主張へ採用するか、帯 901〜998 をどうするか、B-10 全体を閉じるかは今回決めない。
- 外部報告の digest を「照合済み」と記載するなら、親が現物との一致を確認する必要がある。確認しない場合も、manifest 記載値と既存記録の引用として本 plan は成立する。
- 親は fragment 作成後に `check_docs.py` と `spool_fold.py --dry-run --show-diff` を実行する。後者の land 前 rc=0 は `docs/spool/README.md:74–89` の要求。この段ではどちらも実行しておらず、緑とは報告しない。