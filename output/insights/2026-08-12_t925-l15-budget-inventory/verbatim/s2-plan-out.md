結論は、全節削除候補はゼロ、節内の削除候補は A が 3 群、B が 3 群です。提案どおり実施すると、追記後の余白は L0=2 bytes、L1=221 bytes、L1.5=263 bytes となり、不足層はありません。

`check_docs.py` が規範文の逐語を pin しているだけの箇所は、実行違反を止めないため機械代替に数えていません（`tools/check_docs.py:4035-4085`）。また、H2 節そのものは登録・dispatch 閉包が必須なので削除不可です（`tools/check_docs.py:560-578,4692-4707`）。

「発火なし」は指定された F/D と対象文書内の意味検索に限ります。範囲外の repo 全体検索を要するものは `未確定` または D としました。

## L1.5 義務棚卸し

### `docs/dev-wave/workers.md`

| 節・行 | 義務 | 機械代替 | 発火実績 | 判定 |
|---|---|---|---|---|
| preamble:3 | 指定 leaf 節を worker 起動前に読む | なし。dispatch lint は実読了を検証しない | なし | C 維持 |
| DW-S02:7 | brief と関連コードの所在を子へ渡す | なし。関連性は意味判断 | なし | C 維持 |
| DW-S02:7 | plan を `reasoning=max`・`sandbox=read-only` で起動する | なし。現 CLI は任意 reasoning と両 sandbox を受理（`tools/dev_wave_codex.py:46-55,126-146`） | D207 は採用 pin、事故記録なし | **B テスト化可** |
| DW-S02:8 | file:line 粒度でプランを書く | `check_codex_output` はサイズ・総括だけ（`tools/check_codex_output.py:100-115`） | なし | D 裁定へ。構造 field が未定義 |
| DW-S03:12 | consult を `reasoning=max`・`sandbox=read-only` で起動する | なし。同上 | D207、事故記録なし | **B テスト化可** |
| DW-S03:12 | 異なるレンズを並列起動し、plan を攻撃させる | lane 単体の妥当性だけ検査（`tools/dev_wave_codex.py:133-137`）。異なるレンズ・2 本の閉包は検証しない | なし | C 維持 |
| DW-S03:13-14 | 正しさ境界と整合・実効性を分離し、brief、前提、所有、変異帰属、親実測の一般化を攻撃する | なし。意味レビュー | F28/F29/F31/F35 が実際にこのレンズで検出（`docs/failures.md:531-597,598-679,741-750,875-896`） | C 維持 |
| DW-S03:15-16 | 新 gate が効く全層を scope に入れ、scope 外は裁定候補として返す | なし。成果物への到達性は意味判断 | なし | C 維持 |
| DW-S05-A:20-22 | 所有 path を素集合に分け、別 worktree と限定 patch で投入する | なし。patch・所有表の標準 field がない | なし | C 維持 |
| DW-S05-A:20-22 | 依存単位を先に完了し、その patch 展開後に並列投入する | なし | なし | C 維持 |
| DW-S05-A:23 | author/fix を `reasoning=high`・`sandbox=workspace-write` で起動する | なし。現 CLI は値を束縛しない（`tools/dev_wave_codex.py:46-55,126-146`） | なし | **B テスト化可** |
| DW-S05-B:27 | 実装子はコードとテストだけを編集し、docs・commit を変更しない | sandbox は docs/commit を止めない | なし | C 維持 |
| DW-S05-B:28 | 意図的な赤を xfail 化しない | なし | F27 は期待値弱体化の実例（`docs/failures.md:511-529`） | C 維持 |
| DW-S05-B:29 | 赤の内訳を完了報告へ書く | なし | なし | C 維持 |
| DW-S05-C:33 | 列挙された全義務を実装子 prompt に入れる | なし。prompt schema がない | なし | C 維持 |
| DW-S05-C:35-36 | 緑には実走 nodeid・範囲を添え、未実走を closed と書かない | なし | F27 | C 維持 |
| DW-S05-C:37 | 新設・改名テストの制約 meta-test を洗い出して走らせる | meta-test は違反を rc≠0 にするが、子が走らせたかは止めない | F42 は機械 gate 発火後も4回目あり（`docs/failures.md:1162-1206`） | D 裁定へ |
| DW-S05-C:38 | fixture の現行 hash 差し込み等でテストを甘くしない | なし | F27 | C 維持 |
| DW-S05-C:39-40 | 揮発 payload を期待値に焼かず、揮発源変更でも緑を確認する | なし | なし | C 維持 |
| DW-S05-C:41 | 所有外 caller・fixture・consumer test の波及を列挙する | なし | なし | C 維持 |
| DW-S05-C:42 | 指示外の受理集合変更をせず、現行挙動を先に書く | なし | なし | C 維持 |
| DW-S05-C:43 | docs 未 land 時の期待赤集合を事前指定し、それ以外を回帰とする | なし | なし | C 維持 |
| DW-S06-A:47 | 敵対レビューを異なるレンズで2本並列実行する | 本数・レンズは未検査 | なし | C 維持 |
| DW-S06-A:47 | review effort を `high` にする | **機械権威**。逐語 regex と receipt 束縛（`tools/dev_waves/launch_authority.py:36-39,386-417`） | なし | C 維持 |
| DW-S06-A:48 | Codex author のない実装 hunk があれば停止する | 許可範囲内では実効 checker を確認できず未確定 | なし | C 維持 |
| DW-S06-A:49 | 所見ゼロを変異裏取り前に緑と数えない | なし | F28 の無効変異群 | C 維持 |
| DW-S06-B:53 | fix 前に統合 snapshot patch を退避する | なし | なし | C 維持 |
| DW-S06-B:53-55 | 所見を所有素集合へ分割し、素集合なら並列、一枚岩なら理由を handoff に書く | なし | なし | C 維持 |
| DW-S06-B:55 | 横断所見を1 Codex 単位へ寄せ、親が直さない | なし | なし | C 維持 |
| DW-S06-B:57-58 | 実装子契約と段4規模上限を継承し、超過を差し戻す | なし | なし | C 維持 |
| DW-S06-B:60-61 | 既存期待値の反転・緩和・skip・削除を禁じ、誤期待なら実装を変えず停止する | なし | F27 | C 維持 |
| DW-S06-C:65 | focus effort を `high` にする | **機械権威**（`tools/dev_waves/launch_authority.py:40-43,393-417`） | なし | C 維持 |
| DW-S06-C:65 | 統合後の焦点レビューを全体へ1本行う | effort 以外は未検査 | なし | C 維持 |
| DW-S06-C:66 | 親が変異 matrix と受入を再走する | なし | なし | C 維持 |
| DW-S06-C:67 | 成立 operations と DW-G05 を適用し、影響不明所見を must-fix にしない | なし | なし | C 維持 |

### `docs/dev-wave/mutation.md` の L1.5 節

| 節・行 | 義務 | 機械代替 | 発火実績 | 判定 |
|---|---|---|---|---|
| DW-M02:14 | 所見ゼロを変異なしで緑と数えない | なし | F28 | C 維持 |
| DW-M02:14 | 生存時に mask・等価性を疑い実効 gate へ再照準する | なし。semantic 判断 | F28 | C 維持 |
| DW-M02:14 | 初回結果を消さず erratum に残す | なし | F28 | C 維持 |
| DW-M03:18-20 | 受理集合/fail-closed が変わった場合だけ kill と数える | rc/node 一致は検査するが受理集合の意味は判定しない（`tools/mutation_harness.py:1434-1450`） | F28 | C 維持 |
| DW-M03:18-20 | 診断文字列だけの赤を kill にしない | なし | F28 | C 維持 |
| DW-M03:19-20 | fixture の単一理由性を確認し、過剰決定を単独証拠から外す | なし | F28 | C 維持 |
| DW-M04:24-25 | anchor を累積 source 上で exact 1 件にし、空注入を拒否する | **あり**。違反は `HarnessError`→rc=2（`tools/mutation_harness.py:803-835,2401-2412`） | F33 は機械化前。現 entry に機械化後再発なし（`docs/failures.md:829-854`） | **A 削除可** |
| DW-M04:24-25 | 同一 file の複数置換を累積適用する | **あり**（`tools/mutation_harness.py:806-820`） | F33、機械化後再発なし | **A 削除可** |
| DW-M04:25-26 | SURVIVED を equivalent とする前に diff で注入を確認する | diff は束縛するが、equivalent という意味判断は止めない（`tools/mutation_harness.py:843-853,1532-1538`） | F33 | D 裁定へ |
| DW-M04:26 | 両層変異の kill 期待を事前登録する | `expected_status` は必須だが「両層」の識別はしない（`tools/mutation_harness.py:301-347`） | F33 | D 裁定へ |
| DW-M05:30-32 | official harness を使い、独自 harness なら同等検査を事前登録する | official tool 外の起動を止める gate はない | F32 | C 維持 |
| DW-M05:33-34 | 起動前に総所要を見積もる | tool は計算・表示するだけ（`tools/mutation_harness.py:2259-2269`） | F32 | D 裁定へ |
| DW-M05:33-34 | 外側上限に掛からない経路で起動する | `--detached` は自己申告 flag で、実 detachment を証明しない（`tools/mutation_harness.py:2143-2149,2181-2182`） | F32 | D 裁定へ |
| DW-M05:34-35 | `pgrep` は ERE/literal とし、自己・他 wave を path で排除する | official harness は `pgrep` 不使用だが、外部 waiter は止めない | F32 の再発（`docs/failures.md:806-828`） | C 維持 |
| DW-M06:39 | hang 対象を正しく `hang_risk` と分類する | field の型だけ検査。分類の正しさは自己申告（`tools/mutation_harness.py:328-332`） | F32 | C 維持 |
| DW-M06:39-40 | timeout を TIMEOUT 証拠として記録し、次の変異へ継続する | **あり**。個別 timeout→record→次 loop、期待不一致は最終 rc≠0（`tools/mutation_harness.py:1434-1450,1551-1588,2355-2396`） | F32 の機械化前事故後、指定 entry に同義再発なし | **A 削除可** |
| DW-M07:44 | final commit の anchor と期待 node を再検証してから本走する | HEAD/spec/collection は束縛するが、「final commit である」ことは自己申告（`tools/mutation_harness.py:2200-2215,2273-2307`） | F28/F71 | D 裁定へ |
| DW-M07:45 | mask 再照準と erratum を台帳へ残す | なし | F28 | C 維持 |
| DW-M08:49-52 | rc・failed node を正本 stdout から解析し、rc≠0/0 node を停止する | あり（`tools/mutation_harness.py:974-989,1017-1066,1434-1450,2387-2391`） | F71 はこの gate の発火・再発を記録（`docs/failures.md:2176-2218`） | D 裁定へ |
| DW-M08:52 | 期待 node 完全集合との完全一致だけを KILLED とする | あり（`tools/mutation_harness.py:1103-1147,1448-1450`） | F33/F71 | D 裁定へ |
| DW-M08:53 | 不確定時だけ probe→erratum→再登録→再走する | なし | F71 | C 維持 |
| DW-M08:54-55 | diagnostic sensitivity を kill と別枠記録する | category field はあるが意味区分は自己申告 | F28 | C 維持 |
| DW-M08:55-56 | テスト強化 wave は新旧双方へ走らせ差分を示す | なし | なし | C 維持 |

### `docs/dev-wave/operations.md` の L1.5 節

| 節・行 | 義務 | 機械代替 | 発火実績 | 判定 |
|---|---|---|---|---|
| DW-O01:8 | canonical launcher を使い、model を caller 指定しない | launcher に `--model` はなく docs から導出。ただし raw 起動の全面禁止までは未確認 | なし | C 維持 |
| DW-O01:8,14 | model と review/focus effort を docs 権威から導く | **機械権威**（`tools/dev_waves/launch_authority.py:17-43,386-417`） | なし | C 維持 |
| DW-O01:9 | background job を指定 wrapper で detach する | なし | F23/F24 | C 維持 |
| DW-O01:10 | prompt 非空を確認し、既存 `.done` を再利用しない | prompt は job-id 自動生成時だけ非空検査（`tools/dev_wave_codex.py:160-170`）。`.done` は未検査 | F23/F24 | D 裁定へ |
| DW-O01:11 | canonical waiter と producer 自身の pid-file を使う | waiter は pid-file を検査する（`tools/dev_wave_wait.py:258-265,318-332`）が、誰が書いたかは証明しない | F32/F24 | D 裁定へ |
| DW-O01:12 | producer 死後、artifact・`.done`・exit code だけで完了判定する | waiter は producer 死と2 file を検査するが `.done` 内容を読まない（`tools/dev_wave_wait.py:400-430`） | F24 に機械化後の多数再発（`docs/failures.md:371-415`） | D 裁定へ |
| DW-O01:12 | 成果物を最終メッセージから読む | なし | F43 | C 維持 |
| DW-O01:13 | `check_codex_output.py` rc=0 の成果だけ採用する | size・UTF-8・総括を rc=1 で拒否（`tools/check_codex_output.py:67-115,142-150`） | F43 | D 裁定へ。意味整合は未検査 |
| DW-O02:18-19 | artifact を wave 専用 subdirectory に隔離する | launcher は wave/job dir を生成するが prompt/output は任意 absolute path（`tools/dev_wave_codex.py:149-175`） | なし | D 裁定へ |
| DW-O02:19 | 専用場所を確保できなければ停止する | 生成 directory エラーは非0（`tools/dev_wave_codex.py:227-247`） | なし | D 裁定へ。全 artifact 閉包ではない |
| DW-O02:20-22 | brief・前段成果を file 化して絶対 path で渡し、読めなければ停止させる | なし。prompt 内容の schema がない | なし | C 維持 |
| DW-O02:21-22 | context 無し出力をレビュー結果に数えない | なし | なし | C 維持 |
| DW-O03:26-27 | 防護 path を含む prompt は Write で作り、heredoc/substitution を使わない | hooks は一部 Bash を拒否するが script・変数等は開いている（`hooks/README.md:93-102,265-294`） | なし | D 裁定へ |
| DW-O03:27 | guard を迂回しない | hooks は第二防壁で sandbox ではない（`hooks/README.md:265-294`） | なし | C 維持 |
| DW-O05:36 | read-only 子へ「pytest 緑不要・静的検査可」と明記する | なし | なし | C 維持 |
| DW-O05:37 | 親が実測し、子の未実走を緑と記録しない | なし | F36 近縁 | C 維持 |
| DW-O13:79 | gate 設計前に入力が実成果物のどの field にあるか確認する | なし。設計者の一次資料照合 | D75 | C 維持 |
| DW-O13:79 | 同名識別子を二義化しない | なし | D75 | C 維持 |

## L1 義務棚卸し

### `docs/dev-wave/core.md`

| 節・行 | 義務 | 機械代替 | 発火実績 | 判定 |
|---|---|---|---|---|
| preamble:1-3 | 本書を親段・plan gate・停止条件の正本として扱う | 構造 lint のみ | なし | C 維持 |
| DW-C00:7-9 | 入口の scope・言語・起動手順に従い、引数を候補より優先し、読了を記憶で代用しない | 実読了・優先判断の gate なし | なし | C 維持 |
| DW-C00:8-9 | 読了 trigger から L0/L1/L1.5/L2 を分類する | byte 分類自体は lint（`tools/check_docs.py:3724-3823`）、実行時の読了は未検査 | なし | C 維持 |
| DW-C00:11-12 | 設計択一・正しさ防壁・受理集合のいずれかなら敵対検証子を省かず、変更面確定時に再評価する | なし | F28/F29 | C 維持 |
| DW-C00:12-15 | 非該当だけ軽量版とし、実装面の author/fix は省かず親が編集しない | なし | なし | C 維持 |
| DW-C00:14-15 | docs-only は子ゼロ可、実測は省かず、9段全走はユーザー明示時に使う | なし | なし | C 維持 |
| DW-C00:17 | 待ち手を1条件1本とし canonical waiter を使う | prose literal と target 実在だけ lint（`tools/check_docs.py:3924-4032`） | F32 の汎用 waiter 再発 | D 裁定へ |
| DW-C00:17-18 | producer 停止時に waiter も落とし、producer 死を待ち条件へ含める | waiter は死を検査するが停止連動は親操作（`tools/dev_wave_wait.py:378-430`） | F32 | D 裁定へ |
| DW-STOP:22-24 | 不在・未読・赤・権限不整合・未見新事実・裁定待ちのいずれかなら停止する | なし。複数成果物の統合判断 | 多数 F の終端 | C 維持 |
| DW-STOP:24 | 期限後成立なら巻き戻し、旧成果物を流用しない | command 構造 lint はあるが実 invalidation は未検査（`tools/check_docs.py:4714-4718`） | なし | C 維持 |
| DW-STOP:25 | 弱体化・権限拡大・rebase・force・未監査差分で迂回しない | land tool 内だけ一部拒否 | F27/F37 | C 維持 |
| DW-S01:29-33 | brief を10〜30行とし、scope・裁定・不変条件・成果物・分割方針だけを書く | canonical brief parser/field がない | なし | D 裁定へ |
| DW-S01:30-31 | provisional 前提を P 採番し、攻撃対象と明記する | なし | F29/F31 | C 維持 |
| DW-S01:31-32 | テスト wave は既存被覆を性質で検索し、純増検出力だけ書く | なし | F42 近縁 | C 維持 |
| DW-S01:32-33 | 未確認で子を起動せず、受入・実測環境を確定する | なし | なし | C 維持 |
| DW-S01:35-39 | 承認前提を実測し、模擬差を明記し、自己 hash/pin では模擬を根拠にしない | なし | F29（`docs/failures.md:598-679`） | C 維持 |
| DW-S01:37-39 | コード前提は実編集・復元で測り、不能なら拒否事実と差を書く | なし | F29 | C 維持 |
| DW-S01:38-39 | 別 program の build・env・外部 command・注入 seam を棚卸しする | なし | F29 | C 維持 |
| DW-S01:41 | decision 本文と archive worklog を開き、本文を優先する | なし | F31 | C 維持 |
| DW-S01:41-42 | 人間手番を git・成果物で照合し、済なら stale として繰り上げる | なし | F35 | C 維持 |
| DW-S01:42-43 | 日付・hash・件数を一次 field から取得する | なし | F1/F35（`docs/failures.md:26-80,897-901`） | C 維持 |
| DW-G01:47-48 | 大型実装前に既存または100行以内 driver で生死確認する | driver 行数は測れるが、実効生死・着手前時点は未検査 | なし | C 維持 |
| DW-G01:48 | 確認前の専用機構・LLM driver を brief で却下する | なし | なし | C 維持 |
| DW-G02:52-53 | 初 cycle 前 blocker を成果物値を変える欠陥に限定する | なし。意味判断 | なし | C 維持 |
| DW-G03:57-58 | 族一般化は異なる producer/consumer の独立2例後だけ許す | なし。台帳の意味照合 | F71 は3例で実際に発火 | C 維持 |
| DW-G04:62-63 | 条件付き機能は既存 artifact path/measurement ID を brief に書ける場合だけ実装する | brief field が未標準化 | なし | D 裁定へ |
| DW-G05:67-68 | scope/must-fix ごとに未実装時の成果物影響を1行書く | なし。値・受理集合・参照の意味判断 | なし | C 維持 |
| DW-G05:69 | 影響を書けない所見を nit/backlog とする | なし | なし | C 維持 |
| DW-G05:70 | 段1で書けなければ子を起動せず1 cycle 後へ送る | なし | なし | C 維持 |
| DW-S04:74 | real/refuted・採否・scope を裁定し plan v2 を確定する | なし | なし | C 維持 |
| DW-S04:75 | scope 外 real 所見を実装せず裁定パッケージへ返す | なし | なし | C 維持 |
| DW-S04:76 | 変異を DW-M01 に従い事前登録する | spec SHA は後で束縛するが登録時点は未検査 | F28 | D 裁定へ |
| DW-S04:77 | gate 禁止を署名で書き、通る正例を添える | なし | なし | C 維持 |
| DW-S04:79-80 | 実装差分ゼロ裁定以外は変異免除せず、実 repo test を段7前に走らせる | なし | なし | C 維持 |
| DW-S04:82-85 | 未見新事実だけが承認済み裁定を止め、親が不採用化せず再裁定へ戻す | なし | F31/F35 | C 維持 |
| DW-S04:84-85 | 裁定済み方向を非同値案へ戻す前にコードで等価性確認する | なし | F31 | C 維持 |
| DW-S07:89-93 | canonical 3台帳を直接編集せず spool fragment とし、fold は land lock 内だけで行う | spool schema/fold は検査するが、wave 側の直接台帳編集を全面的に拒否する根拠は未確定 | なし | D 裁定へ |
| DW-S07:94-96 | 検出語を走査し、hit/末尾空白は hash・byte・復元法付き可逆修正だけにする | なし | F34/D88 | C 維持 |
| DW-S07:97 | docs commit 後に repo scan invariant と影響 test を再走する | 自動起動 gate なし | F34 | C 維持 |
| DW-S07:97-98 | 実測前に結果欄を作らず、未実施を明記する | exact placeholder の一部だけ lint（`tools/check_docs.py:124-167,1427-1470`） | F36 は予測値先書きも再発 | D 裁定へ |
| DW-S07:98 | 値なし前方参照を禁じ、再走値を amend する | なし | F36 | C 維持 |
| DW-S07:99 | hash 自己参照を禁止する | 許可範囲内で実効 gate を確認できず未確定 | F36 | C 維持 |
| DW-S07:99-100 | provenance・worklog・push の正本に従う | なし | F25/F37 | C 維持 |
| DW-S08:104-105 | 段7後に自己改善契約を一度だけ適用する | dispatch 文の存在は lint、適用回数は未検査 | なし | C 維持 |
| DW-S09:109 | commit・受入・tested main/tip・監査列を固定して O23 を行う | land tool は渡された値を検査するが、受入完了自体は証明しない | F37 | D 裁定へ |
| DW-S09:110 | local main は canonical land tool だけで変更する | docs の alternate route lint はあるが、手動 git 自体は止めない | F37 | C 維持 |
| DW-S09:111 | land 成功以外は停止・報告する | tool は非成功を非0で返す（`tools/dev_wave_land.py:2666-2676`）が、報告は親義務 | なし | D 裁定へ |
| DW-S09:112 | 段9後に usage collector を実行する | なし | なし | C 維持 |
| DW-CTX:116-117 | 対話 wave 後は人間が clear、新 context から次 wave を起動する | なし | D69 | C 維持 |
| DW-CTX:119-120 | 無人継続は外部 supervisor が wave ごとに新 process を使い、組込 loop を使わない | supervisor 実装は許可範囲外で未確定 | なし | D 裁定へ |
| DW-CTX:120-121 | max-waves、金額/token、deadline を必須にする | 同上 | なし | D 裁定へ |
| DW-CTX:121-124 | 列挙した赤・dirty・timeout 等で fail-closed 停止する | 同上 | なし | D 裁定へ |
| DW-CTX:123-124 | 自然言語完了だけで継続せず HEAD・cleanliness・検査・task-run を照合する | 同上 | なし | D 裁定へ |

### L1 の mutation / operations

| 節・行 | 義務 | 機械代替 | 発火実績 | 判定 |
|---|---|---|---|---|
| mutation preamble:1-3 | 本書を変異契約の正本として扱う | 構造 lint のみ | なし | C 維持 |
| DW-M01:7-9 | 変異を実装前に登録し、前後の同一拒否層と単一赤理由をコードで確認する | spec SHA は束縛するが、時点・意味は検査しない（`tools/mutation_harness.py:2200-2208`） | F28 | C 維持 |
| DW-M01:8-9 | 確認不能な変異を登録せず実効 gate へ再照準する | なし | F28 | C 維持 |
| DW-M01:9-10 | 受理集合縮小 wave は過剰拒否の正例も登録する | spec に正例種別 field がない | F28 | D 裁定へ |
| DW-M01:10 | テスト強化 wave は新旧両走も登録する | なし | なし | C 維持 |
| operations preamble:1-4 | 成立 operation の節を操作直前に読み、停止条件を迂回しない | 実読了 gate なし | なし | C 維持 |
| DW-O23:134 | canonical land tool へ absolute worktree、tested SHA、監査列を渡す | path・SHA・閉包違反は非0（`tools/dev_wave_land.py:394-406,486-533,1079-1112`） | なし | C 維持。呼出し route 自体 |
| DW-O23:135 | lock 内で再照合し ff-only だけを行う | **あり**（`tools/dev_wave_land.py:1273-1363,2600-2614`） | 指定 corpus に機械化後事故なし | **A 削除可** |
| DW-O23:135-137 | 同じ lock 内で fragment を一度だけ foldし、赤なら landed を返さず、0件を no-op にする | **あり**（`tools/dev_wave_land.py:1931-1970,2027-2064`） | 指定 corpus に機械化後事故なし | **A 削除可** |
| DW-O23:138-139 | wave 側で fold せず、dirty・衝突 untracked を拒否する | dirty/衝突は機械拒否（`tools/dev_wave_land.py:833-890`）。事前 wave-side fold の全面検出は未確定 | なし | D 裁定へ |
| DW-O23:139 | handoff と worktree を非接触にする | identity/許容 path は検査するが全外部変更は未確定 | なし | D 裁定へ |
| DW-O23:141 | 成功を landed/already-landed だけとする | tool の rc/status が強制（`tools/dev_wave_land.py:2244-2251,2535-2544,2666-2676`） | なし | D 裁定へ。親の解釈義務が残る |
| DW-O23:141-143 | stale/busy は fresh context で再監査・再受入し、他所有物/rebase/force/remote/push で解消しない | tool は stale/busy を返すが再開行動は親義務 | なし | C 維持 |

## 削除候補と実測 bytes

全節削除はありません。以下は節内の逐語削除です。

### A 削除可

L1.5 `DW-M04`、201 bytes。末尾 LF は含みません。

```text
置換対象が一箇所でなければ停止し、注入なしを緑と報告しない。同一ファイルの複数置換は累積適用し、
置換ごとに累積後の一意性を assert する。
```

L1.5 `DW-M06`、139 bytes。内部 LF 1 byte、末尾 LF なし。

```text
timeout は当該変異が
fail-closed から fail-open へ倒れた証拠として記録し、harness 全体を落とさない（F32）。
```

L1 `DW-O23`、333 bytes。末尾 LF を含みます。

```text
協調wave lock内で再照合し、tipへのff-onlyだけ行う。ff-only成功後は**同じlockを保持したまま**
`docs/spool/`のfragmentをfoldし、T/D/Fの採番・canonical3台帳への追記・worklogローテーションを
一度だけ行う。foldが赤なら`landed`を返さない。fragment0件のfoldはno-op。
```

A 合計:

- L1.5: 340 bytes
- L1: 333 bytes

### B テスト化可

`tools/dev_wave_codex.py:126-146` に stage policy gate を設け、実在する CLI field を検査します。

- 入力 field: `args.stage`、`args.reasoning`、`args.sandbox`（`tools/dev_wave_codex.py:46-55`）
- 拒否条件:
  - `plan|consult`: `reasoning=max`, `sandbox=read-only`
  - `author|fix`: `reasoning=high`, `sandbox=workspace-write`
- 不一致は `parser.error` で rc≠0。
- `tools/check_docs.py:4035-4085` の S02/S03 prose pin は削除し、S06-A/S06-C の機械権威 pin は残す。

削除逐語:

`DW-S02`、48 bytes。末尾 LF を含みます。

```text
codex `reasoning=max`、`sandbox=read-only` で
```

`DW-S03`、47 bytes。LF なし。

```text
codex `reasoning=max`、`sandbox=read-only` で
```

`DW-S05-A`、68 bytes。末尾 LF を含みます。

```text
codex は `reasoning=high`、`sandbox=workspace-write` とする。
```

B 合計は L1.5 163 bytesです。

## 堰き止められた4系統の追記逐語

### `DW-O01` — L1.5

`docs/dev-wave/operations.md:13` の後、機械権威行 `:14` の前へ置きます。

128 bytes:

```text
中断子の部分成果物は `job-id`・stage・base commit・未完を明記して保全し、次の子に監査させる。
```

114 bytes:

```text
編集量の大きい fix 巡は model call 数を見積もり、起動時に `--max-model-calls` を上げる。
```

必要量: **242 bytes**。

### `DW-S01` — L1

`docs/dev-wave/core.md:33` の後へ置きます。

113 bytes:

```text
親 brief は分類文と実アンカー表を二重管理せず、子には実アンカー表だけを渡す。
```

必要量: **113 bytes**。

### 入口 — L0

`.claude/commands/dev-wave.md:123` の後へ置きます。

172 bytes:

```text
裁定停止時は、結論だけを変え変更面の骨格を保つと確認した場合だけ branch を再開し、変更面の再検査を段 6 review へ寄せる。
```

必要量: **172 bytes**。

L0 の原資は `.claude/commands/dev-wave.md:116-117` の重複規律 174 bytesです。

```text
各条件の詳細は参照節だけを正本とし、事故の物語は `docs/failures.md` の F 番号へ置く。
同じ物語を入口や reference へ再掲しない。
```

この義務は wave 開始時に必読の routing（入口 `:14-15`、`docs/skill-self-improvement.md:36-37`）に既にあります。新規外出しではなく、常時読まれる既存正本との重複削除です。

## 層別収支

| 層 | 現在 | 空く | 要る | 変更後 | 上限 | 最終余白 |
|---|---:|---:|---:|---:|---:|---:|
| L0 | 9,500 | 174 | 172 | 9,498 | 9,500 | **2** |
| L1 | 10,624 | 333 | 113 | 10,404 | 10,625 | **221** |
| L1.5 | 9,564 | 340 A + 163 B = 503 | 242 | 9,303 | 9,566 | **263** |

不足層はありません。予算定数は変更しません（`tools/check_docs.py:256-258`）。

## 実施順序

1. 現在の authority commit のまま、段2成果の検収と段3の2子を完了する（入口 `:68-69`）。`check_codex_output.py` の rc=0 もここで確定する（`operations.md:13`）。

2. `operations.md` / `workers.md` に触れる前に、Codex author 子で B gate と負制御テストを実装する。変更先は `tools/dev_wave_codex.py:126-146` と既存テスト、`tools/check_docs.py:4035-4085`。段6 review/fix もこの時点で終える。

3. 実装面を commit する。これにより、まだ旧 bytes の `operations.md` / `workers.md` を使ったまま必要な子を追加投入できる。

4. 親が非 authority 文書を先に編集する。

   - `.claude/commands/dev-wave.md:116-117,123`
   - `docs/dev-wave/core.md:33`
   - `docs/dev-wave/mutation.md:24-25,39-40`

5. 最後に `workers.md` と `operations.md` を編集する。

   - `workers.md:7-8,12,23`
   - `operations.md:13-14,135-137`

   この瞬間から `snapshot_authority(commit=None)` の byte 比較が失敗し、Codex 子は起動不能になる（`tools/dev_waves/launch_authority.py:377-384`）。機械権威3行は逐語を保つ（同 `:31-43,386-417`）。

6. 子を起動しない窓で関連 test、`check_codex_agents.py`、`check_docs.py`、byte 収支を確認し、docs と phase 完了を commit する。commit 後は working tree と authority commit が一致し、子起動が再び可能になる。

7. commit 後に追加 review/fix が必要なら、新しい authority digest を使って子を起動する。再編集した場合も、`編集 → 子起動禁止 → 検査 → commit → 子起動再開` の順序を崩さない。

8. 最後に provenance 監査と段9 land を行う。push は人間に残す。

テスト、`check_docs.py`、provenance 監査はこの read-only 作業では**未実走**です。

## 総括

削除対象は、L1.5 の `DW-M04` 201 bytes、`DW-M06` 139 bytes、B gate 化する worker 設定 163 bytes、L1 の `DW-O23` 333 bytes、L0 の既存重複 174 bytesです。追記後の余白は L0=2、L1=221、L1.5=263 bytesで、不足層はありません。

実施は、すべての既存-authority 子を先に完了し、B gate の実装・review/fix を終えた後、`operations.md` / `workers.md` を最後に編集して直ちに検査・commitする順序です。機械権威3行と節見出しは変更しません。