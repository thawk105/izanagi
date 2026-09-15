## 総括

最も強い所見は、v2 が **index にだけ残る新規ファイルを `DEL-LANDED` と誤判定する経路**を持つことです。唯一の内容を救出対象から落とします。  
`LANDED-HIST` にも、返した commit の当該 path が照合対象 blob を持たない実例が、提示資料内にあります。  
親 brief の「blob 到達性で足りる」は撤回が必要です。plan の追加条件は妥当ですが、現行スクリプトはその条件を検証していません。  
したがって、現資料から個別の撤去許可は出せません。以下は指定資料の静的読解と表の再集計であり、Git の新規実測・変更・テスト実行はしていません。

以下、`materials/` は指定 job の資料ディレクトリ、repo 相対パスは指定 worktree 基準です。

## real 所見

### 1. v2 の削除判定が index にある唯一の内容を隠す

- **主張：** `[ ! -f ]` は「削除変更」の判定ではありません。新規ファイルを stage した後、作業木側だけ削除した状態も入ります。
- **根拠（読解）：** `materials/reach2.sh:26` で XY 状態を捨て、`:28`〜`:34` で現物が通常ファイルでもディレクトリでもなく、main の path 検査が失敗すれば `DEL-LANDED` にします。たとえば `AD new.py`、main に `new.py` 不在なら、index 内の内容を一度も照合せず合格ラベルになります。
- **成果物影響：** index にしかない実装・試験・調査内容を、救出不要として失います。
- **推奨是正：** HEAD→index と index→作業木を独立に列挙し、全 index stage の OID を保存対象にする。削除は元の状態と削除操作を束縛して判定する。plan `:146`〜`:149` を必須条件として実装仕様に落とす。

### 2. `LANDED-HIST` の証拠 commit が、対象 blob を置いた tree とは限らない

- **主張：** `-m` は merge の検索漏れを直しても、「hit した commit の path に対象 blob がある」という保証を追加しません。
- **根拠（提示実測＋読解）：**
  - `materials/reach2.tsv:15` は fixture の旧 blob `a41252dfa…` を `LANDED-HIST:9f2f8d3a3` としています。
  - `materials/findobj_probe.txt:8`〜`:13` はその commit の差分を **`a41252dfa → b3d0c3794`** と示します。旧 blob を除いた変更も検索に hit しています。
  - `reach2.sh:44`〜`:46` は hit 後の tree 照合をしません。
- **成果物影響：** この SHA を復元先・採用証拠として記録すると、対象版を復元できない証拠が残ります。
- **推奨是正：** full SHA の候補 commit と必要な親 commit の tree を直接照合し、実際に対象 path・mode・OID を持つ証拠へ置き換える。`LANDED-HIST` は採用確認までは「履歴保存候補」とする。

### 3. `LANDED-CURRENT` も、作業全体の保存を証明しない

- **主張：** 同一 path の blob 一致は有用ですが、index、mode、リンク種別、変更の組み合わせを落としています。
- **根拠（読解）：** `reach2.sh:38`〜`:41` は作業木の hash と可変の `refs/heads/main:<path>` だけを比較します。実行属性だけの変更、index=A／作業木=B／main=B、複数ファイルの検査途中に main が進む場合を区別しません。`s1-brief.md:42`〜`:46` の十分条件・費用の結論は強すぎます。
- **成果物影響：** 実行属性、stage 済みの別案、再現に必要なファイル集合を失います。
- **推奨是正：** 固定した `M`、index と作業木の別 snapshot、path・type・mode・内容、採用対応を束縛する。履歴の異なる時点から集めた一致は、一式の採用と区別する。

空ファイル・定型 header の一致は hash 衝突ではありません。**bytes が同じことから、その子の変更が採用されたとは推論できない**という問題です。

### 4. エラーを「clean・削除済み・未保存」へ変換する

- **主張：** 現行計測は fail-closed ではありません。
- **根拠（読解）：**
  - `reach2.sh:21`〜`:23`、`strict.sh:11`〜`:13`：status の rc を見ず、空出力なら `CLEAN`。
  - `reach2.sh:31`〜`:34`：`cat-file` のあらゆる失敗を main の path 不在扱い。
  - `reach2.sh:44`、`:49`〜`:53`：`timeout … | head -1` の Git／timeout rc を保持せず、空なら最後は `NOWHERE`。v1 の timeout 分岐まで失っています。
- **成果物影響：** 検査不能な状態を安全候補や破棄候補へ誤分類します。
- **推奨是正：** subprocess ごとに stdout・stderr・rc を保持する。非ゼロ、timeout、不完全結果は `UNKNOWN`。path 不在は、読取り成功した tree の列挙結果から確認する。

### 5. 所有 path 限定 patch は、子全体の救出にならない

- **主張：** 親への patch 移送が成功しても、所有外の編集は残り得ます。
- **根拠（読解）：** `docs/dev-wave/workers.md:20`〜`:21` の DW-S05-A は `git add -A` 後、`git diff --cached … -- <所有パス>` だけを抽出します。所有外の編集が index に入りながら移送対象から落ちる構造です。fix も `:54`〜`:55` で継承します。
- **成果物影響：** 所有外 caller・共有 fixture の修正や調査結果が、採用 patch の外で失われます。
- **推奨是正：** 所有パスによる抽出集合とは別に、子全体の変更集合を棚卸しし、その差集合を必ず「救出・明示破棄・保留」のいずれかにする。

### 6. `.codex/worktrees/` 配下という位置から子の所有権は導けない

- **主張：** Codex manager の wave 本体を「実装子」と誤認する経路を排除できていません。
- **根拠（読解）：**
  - `census.sh:12`、`reach2.sh:19` は配下を一律走査し、producer・manager/worker の役割を検査しません。
  - census の branch 接頭辞は再集計でも **7 系統**。
  - `measurements.md:14` の所有探索は背景 job を対象外とします。`owner_map.tsv` の `-` は所有者不存在の証明ではありません。
  - `operations.md:178` は Claude/Codex worktree を双方保護し、D703（`materials/d702.txt:43`〜`:47`）は exact invocation/path/ref に限定します。
- **成果物影響：** 稼働中の Codex manager 本体や別 producer の成果物を、子の撤去権限で消すおそれがあります。
- **推奨是正：** 作成記録に producer 種別・manager/worker・親 invocation・Git admin・path/ref を束縛する。全 manager の active root と照合し、所有関係が証明できない既存木は保留する。

plan `:33` の接頭辞禁止・exact 束縛は妥当です。ただし、**現在の所有表からその束縛が回復済みとは言えません（読解）**。

### 7. 自己マッチ除外と終端確認は別問題で、TOCTOU は残る

- **主張：** census の自己マッチを消すための広い PID 除外は、実占有も隠します。
- **根拠（読解）：**
  - checker `:453`〜`:464` は、自身の argv と、starttime が一致する特定の祖先 wrapper の argv を除外します。兄弟の census 用 `git -C` は除外対象とは限りません。
  - `:173`〜`:205`、`:284`〜`:302` の祖先判定は「checker path の後に対象 token」があるかを見ます。純粋な checker 呼出しか、後続で仕事を再開する shell かまでは証明しません。
  - `:553`〜`:560` は PID 集合を一度列挙し、`:586` から順次走査します。starttime 再照合は PID 再利用対策であり、同じ PID の後続 `chdir`・`exec` を防ぎません。
- **成果物影響：** 判定後に再開・新規起動した producer の書込みを、撤去と競合させます。
- **推奨是正：** census 終了後に再検査し、PID／starttime／sources を残す。`git` 全体・同一 UID・全子孫などを除外しない。所有親が再投入を止め、launcher・waiter・計算 job の終端を確認してから一件ずつ直前検査する。

**窓の範囲：** 各 PID の観測時点から directory 撤去終了までです。そこには残りの PID 走査、判定後の処理、detach・branch 操作、撤去が入ります。F26（`materials/f26.txt:10`〜`:14`）は撤去自体が分単位になり得ると記録しています。今回の表に時刻・PID がないため、実際の秒数や上限は算出できません（資料読解）。

### 8. 段階的削減には、流入を含む完了条件がない

- **主張：** 「安全なものから一件ずつ」は安全手順であって、残存数が収束する保証ではありません。
- **根拠（読解）：** plan `:236`〜`:243` は旧対象の処置順を示しますが、新規投入の制御・処置能力・打切り条件は定めません。依頼文の観測「100 分に 21 件」を使うなら流入は **12.6 件/時**です。提示 TSV 単独ではこの流入観測を再検算できません。
- **成果物影響：** 掃除負荷と所有不明物が増え続け、終端契約の目的が達成されません。
- **推奨是正：** 旧対象を固定 cohort として閉じ、新規 producer の終端契約を先行適用する。全体の残存数を減らすには、救出・裁定・撤去を含む完了率が流入率を上回ることを確認する。

全流入を直列一担当で処理する仮定なら、平均 **約4.76分/件未満**が必要です。これは条件計算であり実測性能ではありません。

## 計測スクリプトの盲点

### 表の検算結果

| 表 | 再集計 | 数字が実際に表す範囲 |
|---|---|---|
| `census.tsv` | 67 行、変更数列173、untracked列6、present列173、missing列0、ancestor65／非祖先2 | `census.sh:21`〜`:46` の除外・正規表現・通常ファイル判定を通ったもの。全内容の保存率ではない |
| `reach_all.tsv` | 180 行＝MAIN170＋OTHERREF1＋NOWHERE6＋CLEAN1＋NOT-A-FILE2 | **取り下げ済み v1 の出力ラベルの検算だけ**。救出結論には使用しない |
| `occ_all.tsv` | free64／occupied3。対象は資料記載と一致 | rc・JSON・PID・時刻がないため、CLI結果からラベルへの変換と自己マッチ説は再検証不能 |
| `owner_map.tsv` | 名前付き2／`-`65 | 限定探索の照合結果。65件の所有記録不存在を意味しない |

`reach2.tsv`・`strict.tsv` は途中値として扱い、件数・成功率を結論に使っていません。`strict.sh:19` の `external/ccbench` 文字列検索も、submodule 全体の判定ではありません。

### 取り直す測定

以下は**親向けの未実行コマンド**です。`W` は所有確認した対象、`R` は共有 repo、`M` は固定 main SHA。各コマンドは個別に rc を保存し、非ゼロなら停止してください。NUL 出力は shell 変数や行単位 `sed` を通さず、bytes 対応の parser で処理します。

```bash
git --no-optional-locks -C "$R" rev-parse --verify 'refs/heads/main^{commit}'

git --no-optional-locks -C "$W" status --porcelain=v2 -z \
  --untracked-files=all --ignore-submodules=none

git --no-optional-locks -C "$W" diff --cached --raw -z \
  --no-abbrev --no-renames --ignore-submodules=none HEAD --

git --no-optional-locks -C "$W" diff --raw -z \
  --no-abbrev --no-renames --ignore-submodules=none --

git --no-optional-locks -C "$W" ls-files --stage -z
git --no-optional-locks -C "$W" ls-files -v -z
git --no-optional-locks -C "$W" ls-files --others --exclude-standard -z
git --no-optional-locks -C "$W" ls-files --others --ignored --exclude-standard -z

git --no-optional-locks -C "$R" ls-tree -r -z --full-tree "$M"
```

| 見落としの型 | 実物の根拠 | 取り直しで必要な処理 |
|---|---|---|
| submodule 内変更 | census `:21`、v1 `:11` は `--ignore-submodules=all` | 上記 strict status に加え、各初期化済み submodule 内で index・作業木・未追跡・ignored を同様に列挙。gitlink 一致だけでは内部保存にならない |
| 削除 `D` | census `:41`〜`:44` は内容検査から除外。v1 `:18` は NOT-A-FILE。v2 は不在を削除と混同 | 二つの raw diff で削除側を特定し、元 OID・mode と削除意図を保存 |
| rename の旧 path | 三スクリプトの `sed 's/.* -> //'` | `--no-renames` で旧側削除と新側追加をともに検査。必要なら別途 rename 対応を記録 |
| ignored 生成物 | 全 status が ignored を列挙しない | `ls-files --others --ignored --exclude-standard -z` とファイルシステム棚卸しを照合。生成物という名称だけで不要扱いしない |
| index 独自内容・未解決 stage | hash は現物だけ。strict の変更数正規表現は `UU` などを落とす | `ls-files --stage -z` で stage 0〜3 を保持し、OID の内容を検査 |
| quote・改行・` -> ` を含む path | census `:28`、v1 `:16`、v2 `:26` | NUL parser。rename は仕様上の追加レコードを読む。履歴検索時は literal pathspec を使用 |
| mode・symlink・型変更 | `[ -f ]` はリンク先を辿り、hash 比較は mode を見ない。`T` は件数正規表現から落ちる | `lstat`・`readlink` と tree/index mode を比較。通常ファイルとリンクを別処理 |
| assume-unchanged・skip-worktree | status ベースの列挙のみ | `ls-files -v -z` と全 tracked path の現物照合。非表示フラグ・sparse 不在を削除と混同しない |
| filter・LFS 等の外部内容 | v2 `:38` は子でなく WAVE の文脈で hash | 通常ファイルは `git hash-object --no-filters -- "$W/$p"` も測り、raw bytes と Git 正規化内容を区別。pointer blob 一致で外部実体の保存を断定しない |
| 入れ子 repo・未登録 directory | `*/` glob は worktree 登録・admin 同一性を検証しない | `git worktree list --porcelain -z` の登録集合と対象の Git admin を照合。入れ子 repo は別保存単位 |
| 作業途中の状態変化 | main・HEAD・現物を別時刻に読む | producer 終端後に固定 SHA と全対象 snapshot を取得し、処置直前に同一性を再確認 |

通常ファイルの blob や index 内容の検査例：

```bash
git --no-optional-locks -C "$W" hash-object --no-filters -- "$W/$p"
git --no-optional-locks -C "$W" cat-file blob "$index_oid"
git --no-optional-locks -C "$R" ls-tree -r -z --full-tree "$candidate_full_sha"
```

履歴 tree の一覧から literal path を bytes として照合します。**OID があるだけで保存済みとはしません**。census の `cat-file -e` は、stage によって作られただけの未 commit blob でも成功します。

占有は census 完了後、対象外 cwd から取り直します：

```bash
python3 "$R/tools/check_worktree_occupancy.py" "$W"
```

JSON 全体と rc・開始終了時刻を保存し、撤去時には同じ検査を再実行します。

## refuted — 攻撃したが立たなかったもの

- **「v2 も submodule・削除を一律無視する」：refuted（読解）。** `reach2.sh:21` は `--ignore-submodules=none`、`:28`〜`:35` は削除候補を出します。問題は内部内容の未検査と削除判定の誤りです。
- **「空白入り path はすべて `sed 's/^...//'` で壊れる」：refuted（読解）。** 単純な空白は `IFS= read -r` と引用付き展開で保持されます。壊れるのは Git の quote 表現、改行、rename 表現・` -> ` の誤解釈などです。
- **「削除 hit は blob の履歴到達性まで否定する」：refuted（読解）。** 正常な履歴なら、変更前 blob が main の祖先である親 tree に残る場合があります。否定できるのは「返した commit の tree にある」「今回採用された」という強い結論です。
- **「direct 比較にも merge 検索漏れが残る」：refuted（提示実測）。** `hashcmp.txt:1`〜`:4`、`findobj_probe.txt:1`〜`:8` は直接比較がこの偽陰性を解消したことを示します。
- **「checker は親と自身を全面的に無視する」：refuted（読解）。** argv 除外でも cwd の占有判定は `:401`〜`:451` に残ります。祖先除外にも実行ファイルと starttime の条件があります。
- **「plan 自体が blob 一致だけで撤去を許す」：refuted（読解）。** plan `:139`〜`:159`、`:224`〜`:234` は追加条件と保留を明記しています。主な是正対象は親 brief、計測結果の意味付け、実装前の証明仕様です。
- **「一件ずつ削除する方針そのものが誤り」：refuted（提示実測）。** F26 は一括処理の timeout による中途撤去を記録しています。一件ずつを維持し、流入対策を別途設けるべきです。

## 裁定パッケージへ送るべき論点

1. **C の保証範囲：採用対応まで必須／復元可能な履歴保存まで。** 推奨は前者。後者なら「着地証明」という名称を変更する。
2. **不採用物：対象ごとの破棄裁定／対象種別と digest に限定した親の事前権限。** どちらでも未判定・所有不明は保留。
3. **破棄記録：理由・hash のみ／内容と組み合わせも保存。** 前者は復元性を放棄する選択。
4. **撤去権限：D703 を記録済みの子へ拡張／現行の自 wave 限定を維持。** 拡張する場合も Codex manager 本体・他 producer・旧対象への権限を自動的に含めない。
5. **移行順序：新規 producer の終端契約を先行し旧対象を固定して削減／新規投入を一時停止して旧対象を処置。** 流入を続けたまま全体件数の収束を目標にするなら、処置能力の条件を付ける。