## 総括

推奨は **C を通常経路、B を明示裁定された不採用物の例外経路**とし、終端所有者を子を投入した wave 親に固定する案である。  
段 9 の `DW-O28` に子の処置・解錠・撤去まで含め、子が未処置なら親も撤去完了としない。  
A 単独では commit によって ahead>0 の障壁を作り、一時 probe を履歴へ残す問題も解けない。  
最も強い反対理由は、C の blob 到達性が「採用された変更」の証明には足りず、B の誤裁定は唯一の内容を失わせる点である。  
以下は指定 13 ファイルの読解と親の実測に基づく裁定案であり、編集・Git 状態変更・撤去・テスト実行はしていない。

## 現況の所有グラフ

以下、repo 内の `file:line` は指定 worktree を基準とし、`materials/` は `/home/SFC/tanab/.claude/jobs/2b4c302e/wave/materials/` を指す。

| 所有の段階 | 現行契約・根拠 | 途切れている点 |
|---|---|---|
| 親が編集単位を分割し、子用 worktree を用意する | `docs/dev-wave/workers.md:18`、`:20`。fix も同契約を継承する（`:54`） | 作成・投入と撤去の対応が書かれていない |
| 子が編集し、親が patch を取り込む | **DW-S05-A**、`workers.md:21`。所有 path 限定の staged patch を抽出・適用する | 内容の移送であり、子 branch の commit を main の祖先にする処理ではない。子の index・作業木が残る |
| 起動中の木を保護する | **DW-O20**、`docs/dev-wave/operations.md:169` が `git worktree lock` を要求 | 子を終端へ移す所有者・解錠条件が明記されていない |
| 親の成果物を main へ land する | **DW-O23**、`operations.md:173`。`:178` は Claude/Codex worktree への非接触を規定 | land に子の掃除を期待できない。非接触は維持すべき |
| 親が自分を撤去する | **DW-O28**、`operations.md:214`、`:217` | 指定されるのは wave 自身。子集合を処置する契約がない |
| 残存物を明示 cleanup で調べる | **`/cleanup-branches` §2**、`.claude/commands/cleanup-branches.md:41` | ahead=0、status 空、非占有、所有確認などが必要。dirty・locked・所有不明を救済する経路ではない |
| 所有記録を引き継ぐ | `materials/measurements.md:73` の manifest、`docs/handoff/README.md:19` の永続成果物への退避 | 調査対象 manifest との一致は 2 件。branch 名は探索の手掛かりであり、所有権の証明ではない |

**親 brief への訂正・留保**

- **解錠機構は既にある。** [`tools/dev_wave_cleanup.py:946`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-codex-worktree-retirement/tools/dev_wave_cleanup.py:946) は preflight 後に対象を unlock する。「解錠機構がない」ではなく「子への適用契約がない」が読解による結論である。
- D703 は自動削除の対象を **同一 invocation の exact な wave path/ref** に限定する（`materials/d702.txt:43`）。子への拡張は既存許可の解釈だけでは成立せず、ユーザー裁定が必要。
- `.claude/worktrees/` は 04:20 に 9 件、04:55 に 17 件であり、67 対 9 を原因説明に使わない（`measurements.md:20`）。
- brief の「13 件中 11 MAIN＋1 CLEAN＋1 OTHERREF＋1 NOWHERE」は合計 14。採用可能率の根拠にしない。
- 所有調査は背景 job 内を対象外としている（`measurements.md:13`）。「65 件の所有記録が存在しない」までは証明されていない。

**全案共通の終端契約案**

発火点は `landed / already-landed` 後の段 9。責任者は投入した親、再開時は明示的に引継ぎを受けた親とする。対象は記録に束縛した子の exact path・Git admin・branch・起動 ID に限る。接頭辞による一括収集は禁止する。

`operations.md:214` と `:217` の置換案：

> 親は land 成功と投入した全子・launcher・待ち手・計算 job の終端を確認し、対象外 cwd から、所有記録に束縛した子 worktree を一件ずつ処置する。子の撤去または承認済み保留記録を確定してから自 wave を撤去する。未承認の残存・判定不能・部分撤去は撤去完了と報告せず、同じ親の再開事項として残す。

`operations.md:169` の置換案：

> 子を走らせる worktree は lock し、親・起動 ID・exact path/ref・Git admin の束縛を所有記録に残す。解錠は DW-O28 の終端検査を満たした所有親だけが行う。lock の古さ、親 directory の不在、占有 rc0 単独を解錠理由にしない。

`workers.md:20` への統合案：

> 親は投入前に子の所有情報を専用 handoff に記録し、終了後に採用・不採用・未判定の差分一覧を追記する。段 7 で既存 insights 成果物へ吸収し、未撤去対象の記録を含む job artifact を先に廃棄しない。

占有検査の rc0 に加え、親による全 producer の終端確認と再投入禁止が必要である。観測不能 PID、別 namespace、FD、走査後の新規 process は rc0 で排除されない（`tools/check_worktree_occupancy.py:4`）。終端を確定できなければ停止する。

**新しい L2 節・新 tool は提案しない。** 指定資料で「撤去・掃除・畳む・cleanup・unlock・到達・破棄・manifest・recorded_cwd」を検索した。発火実績は T-2638、機械処理は既存 cleanup の解錠・ancestry 検査、同一発火点の正本は DW-O28 に hit した。D271 の新設条件を満たすとは言えず、`docs/skill-self-improvement.md:27` に従い既存節・既存 tool への統合案とする。

## 案 A — 子の作業木を branch へ commit する

**発火点・所有者：** 子の終了・patch 採用内容の確定時。commit は親が行う。現行も `docs/dev-wave/core.md:31` は commit を親に割り当てている。

**手順案**

1. 子の変更を採用分・不採用分・未判定分に分ける。
2. 採用分だけを子 branch に commit し、親がその **commit 自体を祖先として保持する統合**を行う。
3. 通常の受入・監査・land を経る。
4. 子 HEAD と branch/HEAD reflog の全 commit が main 到達可能で、status 空になったものだけ終端処理する。

**ahead>0 の検査結果：成立上の核心**

読解によると、`/cleanup-branches` §1 は ahead>0 の内容調査を求めるが、§2 は依然 **ahead=0 のみ削除**である（command `:31`、`:41`）。`git cherry` が patch 相当性を示しても削除条件は満たさない。

したがって、**子へ commit して従来どおり patch だけ取り込む A は撤去を塞いだまま**になる。`git branch -d` の拒否も停止条件であり、`-D` は使えない。子 commit を main の祖先にする統合方式への変更が必要である。

**必要な正本変更・文面案**

`workers.md:21` の置換：

> 採用差分は親が子 branch に commit し、その commit を祖先として保持する形で wave へ統合する。patch の適用だけを branch 着地証明にしない。不採用・未判定内容を cleanup のために commit しない。

これに共通の DW-O28・DW-O20 改訂を組み合わせる。`/cleanup-branches` §2、既存 cleanup の ancestry/reflog 検査は維持する。

**一時 probe 問題**

`t1643-impl` の probe を commit して後から削除しても、履歴には残る。probe commit を別 branch にだけ保存すれば、今度は ahead/reflog 検査で止まる。**A 単独では「probe を歴史へ焼き付けず、木も撤去する」を満たせない。** commit 前の B による明示破棄、または保留が必要である。

**成果物影響・費用・副作用：** 統合履歴、commit provenance、受入対象 tip が変わる。commit・merge・競合解消・監査の費用が増える。全内容 commit は研究成果物に不要な probe 履歴を持ち込むため採用しない。

## 案 B — 破棄を記録して撤去可能にする

**発火点・所有者：** 親が採用差分を確定する段階で破棄候補を作り、段 7 で記録、land 後に同じ親が実施する。**不明だから破棄、は認めない。**

**記録の所在・書式・読者**

既存の wave 用 `output/insights/<日付>/<wave>/` にある裁定・完了成果物へ「子 worktree 終端」項目を統合する。専用台帳や新 tool は作らない。作業中の handoff はそのポインタと進捗を持ち、worklog は通常の spool 経由で参照を残す（`core.md:106`、`docs/handoff/README.md:19`）。

記録単位は子一件。最低限の項目案：

```text
owner: wave invocation ID / 引継ぎ記録
target: absolute path / Git admin / branch / HEAD
producer-terminal: session・launcher・waiter・job の終端証拠
snapshot: index と作業木を区別した全対象一覧の digest
entries:
  path / 種別 / mode / index OID / raw bytes hash / byte数
  disposition: landed | discard-approved | hold
  reason: 不採用理由と採用成果物への影響
  evidence: 採用・不採用判断の出典
  authorization: ユーザー裁定の参照と対象 digest
```

これは書式案であり、値を埋めた記録を作成したものではない。削除は不在状態と削除前の情報、rename は両 path、submodule は別の保存対象として扱う。

**誰が読むか：** 採用を裁定する親、段 3/6 の検証者、再開親、段 9 の終端処理が読む。cleanup は既存 §1 の調査資料として参照するだけで、この記録から新たな破棄を実行しない。

**手順案**

1. 終了した子の全内容を棚卸しし、各項目の処置を決める。
2. 不採用理由を採用成果物・scope 判断と照合する。唯一の内容の破棄は対象 digest を特定した裁定に束縛する。
3. 記録が main へ land した後、対象状態が記録と同一であることを再確認する。
4. **cleanup に入る前の所有親の処置**として、承認された項目だけを破棄・復元する。包括的な `reset --hard` や一括 clean を契約にしない。
5. status 空、HEAD・reflog ancestry、所有・終端・占有などの既存条件を満たしてから解錠・撤去する。

**必要な正本変更・文面案**

`operations.md:216` への統合：

> 不採用内容は、親が対象の完全な状態を束縛した破棄記録を land し、その対象への明示裁定を照合した後に限り、cleanup 前処置として破棄できる。未記載項目・状態変化・理由不明・権限不明は停止する。破棄記録は commit ancestry の代替にならない。

`core.md:106` への統合：

> 子の採否と終端記録は既存 insights 成果物へ含め、実施前の承認と実施済み結果を混同しない。

`/cleanup-branches` §0 の編集・commit 禁止、§2 の status 空条件は変えない。

**正当性の担保：** 「不要」という自己申告や署名だけでは足りない。内容を特定し、元の採用判断・成果物影響・ユーザー裁定を照合する。`t1643` の「docs のみ着地」は破棄候補の根拠だが、それだけで今の 475 行を削除する権限にはしない。

**成果物影響・費用・副作用：** 採用成果物の bytes を変えず、不採用理由を監査可能にする。人による内容確認費用がある。記録が hash だけなら破棄内容の復元はできない。復元性を求める場合は別途内容保存が必要で、C を満たしたふりをしてはならない。

## 案 C — 着地証明を条件にした撤去

**発火点・所有者：** land 後、子を処置する直前。所有親が固定した main commit `M` に対して証明する。

**契約案**

「変更 file の内容 blob が着地 main から到達可能」を**必要条件**にする。ただし、それだけで撤去可にしない。

追加して必要なのは、対象集合の完全性、path・mode・index と作業木双方の保存、採用内容との対応、HEAD/reflog ancestry、所有・終端・占有、証明後の状態不変である。**異なる時点に各 file が存在したことは、変更一式が採用された証明ではない。**

**手順案**

1. main を full SHA `M` に固定し、所有・終端を確認する。
2. NUL 区切りで staged/unstaged/untracked を列挙し、削除・rename・mode・symlink・submodule を落とさない。ignored file も撤去で失われるので別途棚卸しする。
3. 通常 file は、index と作業木に異なる内容があれば双方を対象にする。
4. 採用記録にある commit を先に照合し、必要な場合だけ履歴を検索する。証拠 commit `c` が `M` の祖先であることと、その tree の literal path・mode・blob を直接確認する。
5. blob を持たない削除、未解決 index、submodule 内変更などを未検証のまま通さない。対応する証明が未実装なら保留する。
6. 証拠と現物の一致を再確認した後、承認された親の前処置として保存済み差分を取り除き、**status 空を改めて検査**する。
7. 既存の全 gate を満たして一件ずつ撤去する。

C の証明ができない内容を B で処置する場合は、**「C 合格」ではなく「B の裁定による処置」**と記録する。

**必要な正本変更・文面案**

`operations.md:216` への統合：

> 子の未コミット内容を解消する前に、固定した着地 main からの到達性と採用差分への対応を、全対象の path・種別・mode・内容に束縛して検証する。blob 存在、履歴検索の hit、占有 rc0 のいずれも単独で撤去許可にしない。証明できない項目が一つでもあれば処置を停止する。

既存 `tools/dev_wave_cleanup.py:562` の clean 検査は維持し、その前段に子専用の証明・状態再照合・限定処置を統合する案とする。`:646` の branch/HEAD reflog ancestry を blob 証明で置換しない。子の HEAD を親の tested tip と偽って既存 CLI へ渡す設計にはしない。

**例外 2 型による非恒真性**

| 入力 | C の結果 |
|---|---|
| 稼働中 `prov-incr-impl` の OTHERREF | main 証明を満たさず停止。仮に同じ bytes が main にあっても稼働中条件で停止 |
| `t1643-impl` の未 commit probe | main 到達証明がなく停止。B の明示破棄または救出へ |

親の観測結果として両型は負例になる。ただし、下記の理由で `--find-object` の無 hit だけから「どの commit にもない」を一般には断定できない。実装前に直接 tree 照合で負例を確定する必要がある。

**`git log --find-object` の正しさの限界**

以下は静的検討であり、この環境で Git の挙動を再実測していない。

- `--find-object` は object の出現数が変わる差分を探す機能であり、commit tree の単純な包含検査ではない。
- **削除 commit も hit 候補になる。** hit した commit の `path` にその blob が存在するとは限らず、該当 tree または親 tree の直接照合が要る。
- merge の差分表示・履歴簡略化、rename、path 限定によって候補を拾えない場合がある。無 hit は到達不能証明として扱わない。
- `--all` は参照可能な ref の範囲であり、失効した ref や dangling commit を含む「過去の全 commit」ではない。
- Git エラー、欠損 object、shallow history、timeout を「見つからなかった」と混ぜない。すべて判定不能で停止する。
- path は literal として照合し、quote・空白・改行・pathspec 記号を誤解釈しない。

したがって親資料の `MAIN:<sha>` は候補証拠として有用だが、`measurements.md:48` の「親が patch を抜いて着地させ済み」までを検索 hit だけで保証することはできない。

**偽陰性・偽陽性の条件**

| 種別 | 具体的条件 |
|---|---|
| 偽陰性 | 着地時の競合解消・整形・追記で file 全体の blob が変わった |
| 偽陰性 | rename 後の path だけに存在、または spool fold で配置・内容が変わった |
| 偽陰性 | CRLF、clean/smudge filter などにより raw bytes と Git blob が異なる |
| 偽陰性 | merge の検索漏れ、shallow/欠損履歴、特殊 path の誤解析 |
| 偽陽性 | 同じ bytes が過去に存在しただけで、今回の変更は未採用・撤回済み |
| 偽陽性 | file ごとの証拠 commit がばらばらで、変更一式が同時に採用されていない |
| 偽陽性 | blob だけ照合して executable bit、symlink、rename 元削除を失う |
| 偽陽性 | index の独自内容、削除、untracked/ignored、submodule 内変更を列挙から落とす |
| 偽陽性 | filter 後の blob 一致を raw bytes の保存と誤認する |
| 偽陽性 | 証明後の再編集、path 再利用、main/ref 変化を見逃す |

偽陰性は自動撤去を止め、別途検証する。偽陽性を避けるため、履歴内の内容保存と採用判断を別々に確認する。

**性能・費用・成果物影響**

親実測は 2 file の標本で数秒、67 件全体で数十分（`measurements.md:121`）。一件ごとの履歴検索は同じ履歴走査を繰り返すため、`-1` や path 限定だけで安価とは言えない。射影にない TSV は読まず、平均時間は算出していない。

新規 wave は採用 commit を記録して直接照合し、履歴検索を旧 67 件の補助に限定する。timeout は保留とする。成果物 bytes は維持できるが、証明記録と終端処理の費用が増える。

## 案の比較

「掃除を実際に塞ぐか」は、条件不成立の対象を本当に停止できるかを指す。

| 軸 | A：commit | B：明示破棄 | C：着地証明 |
|---|---|---|---|
| 掃除を実際に塞ぐか | ahead>0・未到達 reflog で止まる | 承認なし・対象不一致で止まる | 未到達・列挙不能・証明不一致で止まる |
| 流入を止めるか | commit 単独では止まらない。統合方式の変更が必要 | 所有親の処置義務と組み合わせれば、不採用物の残置を減らす | 証明可能な子の残置を減らす。例外は残る |
| 失う可能性のあるもの | commit 対象外の一時物。全 commit なら不要物が履歴に残る | 裁定された唯一の内容。hash 記録だけでは復元不可 | 不完全な証明なら mode・index・削除意図・一時物 |
| 絶対規律との整合 | ancestry 維持なら整合。強制削除による解決は不可 | 内容特定と明示裁定が必須。理由不明は停止 | 必要条件として整合。blob 一致を十分条件にすると不整合 |
| 必要な正本変更の大きさ | 大：patch 中心の統合契約も変更 | 中：破棄権限・記録・限定前処置 | 中〜大：完全な対象列挙・証明・再照合 |
| 主な費用 | commit・merge・監査 | 内容審査・裁定 | 内容照合・旧履歴検索 |
| 推奨用途 | commit 自体を採用する子に限定 | 意図的な不採用物の例外 | 通常の採用済み差分 |

## 既存 67 件の扱い

**現在の資料だけで「撤去可」と確定できる件数は出せない。** dirty 66 件の判定には submodule 等の除外があり、clean 1 件も所有・占有の再確認が残る。

分類は次の優先順とする。

| 分類 | 判定規則 | 境界例 |
|---|---|---|
| **触るな** | 稼働中・終端不明・所有不明・foreign/primary・未解放 lock・占有/判定不能・状態変化がある | `prov-incr-impl`、`t2293-impl`。親 directory 不在でも locked のままなら該当 |
| **救出要** | 所有と終端は確定したが、独自 commit/内容・未証明差分・不採用裁定待ちがある | `t1643` probe。救出要は「main へ実装として取り込め」を意味せず、保全か明示破棄の判断が必要という分類 |
| **撤去可** | 所有・終端・権限が確定し、内容処置済み、strict status 空、HEAD と必要な reflog が main 到達、非占有、解錠済みなど全 gate を満たす | MAIN 判定の dirty 木はまだ該当しない。clean 木も rc0 だけでは該当しない |

branch 名一致、mtime の古さ、wave 本体の不在、object DB 内の blob 存在は単独で分類を繰り上げない。

**段階的に減らす手順**

1. 別途承認された migration として、旧 67 件の担当者と対象を定める。D703 の将来の子向け拡張を旧対象への自動許可にしない。
2. 背景 job 側も含む所有証拠を回復する。回復できない対象は触らない。
3. 最初は所有・終端の明確な clean/unlocked 一件で全 gate と事後検査を確認する。
4. 次に C で直接照合できる一件を処置し、status 空を作ってから撤去する。
5. B 対象、locked 対象、未到達 commit 対象はそれぞれの裁定・証拠が揃ってから扱う。
6. 毎回 **一件ずつ**、対象外 cwd、終端確認、占有再検査、許可された解錠、detach、directory 撤去、限定された prune、branch `-d`、事後検査へ進む。部分失敗なら次へ進まない。

**実装前に塞ぐべき既存 tool の差異がある。** `tools/dev_wave_cleanup.py:981` は prune 候補 directory が存在しないことを調べるが、今回の所有確認済み対象との完全一致は検査していない。`:986` はその後 real prune を行う。一方 command `:55` は完全一致を要求する。読解上、既存 tool をそのまま子へ反復適用する案は採れない。

また command `:14` は **Codex の real prune を禁止**する。完結した撤去は許可された実行主体が担い、Codex に禁止操作を代行させる設計にはしない。

## 未解決・親へ返す論点

- **通常経路は C＋限定 B ／ A 中心**：推奨は前者。後者は patch 統合から commit ancestry を保持する統合へ変更する。
- **自動撤去権限を記録済みの子へ拡張する ／ 現行 wave 本体だけに保つ**：D703 の exact invocation/path/ref の対象範囲が変わる。
- **不採用物は毎件ユーザー裁定 ／ 事前に限定された破棄権限を親へ与える**：B の人間手番と誤破棄リスクが変わる。未判定物はどちらでも停止する。
- **不採用物は理由・hash だけ残す ／ 内容も保存する**：前者は bytes を失い、後者は保存費用と一時 probe の恒久化を受け入れる。
- **C は履歴内の保存に加えて採用対応を必須にする ／ 履歴内保存だけを意味する契約にする**：推奨は前者。後者を「着地証明」と呼ぶのは不正確になる。
- **例外が残れば親を保留する ／ 承認済みの担当者へ引継いで親を畳む**：異常終端後の責任の所在と記録寿命が変わる。
- **旧 67 件は個別対象を指定した migration ／ 将来分だけ先に閉じる**：既存 backlog を減らす権限と実施範囲が変わる。

親の再検証事項は、`--find-object` 候補の直接 tree 照合、厳密な全差分列挙、占有の取り直し、所有探索範囲の補完、prune 対象一致の確認である。本回答ではこれらを実走済み・合格とは扱っていない。