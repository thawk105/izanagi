## 所見

以下、行番号は現 checkout。略記は次のファイルを指す。

- **T**: [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/tests/test_s8b_oracle_driver.py)
- **M**: [t080_freeze_migration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/t080_freeze_migration.py)
- **H**: [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s8b_holdout_freeze.py)
- **K**: [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s1_known_axes_freeze.py)
- **P**: [stage2-plan.md](/home/SFC/tanab/.claude/jobs/54ef49c2/tmp/wave-artifacts/dev-wave-t2559-accept-floor/stage2-plan.md)

必読ファイルはすべて読取可能。静的検査のみで、編集・commit・pytest・性能測定はしていない。

### 所見1 — 固定 whitelist は、既存 node を全部残しても入力に対する検出力を失う

**根拠:** T:1385、T:1628、T:1705–1714、T:1892–1921、M:1727–1731、M:2201、H:608–637、H:714–734。

現行では、非除外 output の任意の可視ファイルに rr80 三軸 conjunction が入ると、それを fixture に複製し、発行 subprocess の production scan が拒否する。最終的に **T:1628 の subprocess 成功 assert が落ちる**。whitelist がそのファイルを落とすと、この拒否経路自体が消える。

一方、既存の未知性負例は **fixture 作成後に root 直下へ** `rr80-known.txt` を置く（T:1892）。そのため T:1914–1921 は引き続き通り、output の脱落を検出しない。

known-axes 側にも同種の経路がある。追加の remeasure campaign が K:471 の glob に一致すると、K:479–480 は候補数が複数であることを拒否する。既存 JSON に記録された source だけを複製すれば、追加候補を隠してこの拒否を消せる。

**影響:** 現行では発行失敗する入力から、候補版では有効 receipt を作れる。node 集合・parametrize・assert の文字列が同じでも、受理集合は拡大する。

**提案:** A の固定 whitelist は採らない。helper 自体を縮小すれば T:1705–1707 が落ちるが、helper を残して builder だけ別経路へ変えると、その保護も届かない。P:219 の対照 probe は、この具体的な受理集合変化を確認する用途に限定する。

### 所見2 — 全 object store の借用は、report の観測値を静かに変える

**根拠:** M:883–901、M:2266–2271、T:1782–1785、T:1810–1811。

実 repo に recorded commit があり、fixture にない場合、現行の ancestry は `missing-commit`。実 repo 全体を alternates にすると、その commit が見えるため、fixture の独立履歴に対して `not-ancestor` へ変わり得る。`observed` も `None` から validation HEAD に変わる。

T:1782 が独立期待値と比較するのは **17 件中の先頭15件だけ**。残り2件の ancestry は比較対象外である。T:1811 は report と verifier が同じ object store を見るため、この変更後も一致し得る。

**影響:** gate の可否が変わらなくても、report envelope の ancestry の値が変わる。「同一 tree」「同じテストが緑」では観測保存を証明できない。

**提案:** B は採らない。C でも「refs を移さない」だけでは不足し、**不要な commit object 自体を移さない**条件が必要。P:173 の blob 限定を実装で維持する。新しい常設 gate は不要。

### 所見3 — plan の数値モデルは、144秒の誤帰属を残している

**根拠:** T:1000、T:1047–1067、T:1460–1461、P:27、P:185–197。

144秒の出所とされるテストは、次を実行する。

1. 最初の子で `issue_receipt=False` の base を構築し、first repo へコピー。
2. 次の子で cache hit し、second repo へコピー。
3. 各 repo の設定検査、process 起動・通信など。

したがって、その node の junit 時間を **「base 構築1回」には帰属できない**。P:27 は発行 subprocess を含まない点だけ留保しており、**2回のコピーを含む点を落としている**。

さらに P:185 の `144 + 8.47 + 70` における「本体70秒」の出所は示されていない。射影された D1708 の70秒は、別時点の **base構築**で、本体は4秒である。

**影響:** 222.51秒との近似一致は成分モデルの検証にならず、118.54秒という base 目標や145.68秒という候補値に実測上の根拠がない。

**提案:** これらの数値目標は撤回し、親が予定する同条件の成分測定で置き換える。放置すると、効果未確認の変更を数値上の達成として記録する経路になる。

### 所見4 — 推奨 C は、brief が求める「成長比例を断つ」を満たさない

**根拠:** brief:8–9、38、P:164–177、203–210、234–236。

C は全件列挙・全件の実体配置・scan・base→test コピーを残す。これは係数削減候補であり、件数増加への依存を除く案ではない。plan 自身も最後にこの不達を認めている。

**影響:** A/B で速くなっても、それだけで brief の構造的な完了条件を達成したことにはならない。

**提案:** C を比較実験候補として扱うことと、wave の完了判定を分ける。「成長比例を断った」という成果物記載は不可。恒久的な検査・台帳の追加は必要ない。

## 反証した攻め筋

**C が blob を再利用するだけで恒真化する、という攻撃は成立しなかった。**

T:1782 は「fixture と実 repo が一致する」assert ではなく、production が生成した observation と、fixture の Git blob から独立導出した期待値を比較する。T:1435–1440 は descriptor に fixture 固有の bytes を加え、T:1737 がその分岐を使う。これと通常の add を保持する限り、実 repo の固定値を返す退化は引き続き検出される。

ただし、最適化でこの上書きを古い OID に戻し、worktree と index の双方を同じ古い内容にそろえると、その負例の意味が消える。P:165 の「同じ bytes」は、**歴史 blob の復元後かつ `distinct_basis_blob` 適用後**について成立する必要がある。

**alternates が通常の fixture 書込みを実 repo へ転送する、という攻撃も成立しなかった。**

alternates は object の検索先であり、新規 object の書込み先ではない。通常の fixture 内 commit や gc が、それだけで貸出元へ書き戻すわけではない。ただし OS の書込み権限を制限する仕組みでもない。[Git公式仕様](https://git-scm.com/docs/git#Documentation/git.txt-GITALTERNATEOBJECTDIRECTORIES)

成立する問題は逆方向である。貸出元で不要 object が prune されると、借り手が必要とする object を失う場合がある。fixture の `gc.auto=0` は貸出元の保全を保証しない。[Git clone公式仕様](https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---shared)

**temp 配置・import 隔離から、blob 読取り一般の禁止は導けない。**

T:37–46 は実 output 内への temp 配置を拒否する。T:1541–1557、T:1617–1625 は限定 loader・fixture 内 module root・隔離起動を検査する。独立した blob pack の配置は、これらを直ちに破らない。反対に、これらの assert は object store の独立性を検査していない。

**既裁定からの過大な禁止も成立しない。**

| 裁定の逐語 | 今回への適用 |
|---|---|
| D747「削除 0 件で閉じる」 | C に node 削除の提案はない。ただし削除ゼロは判定保存の証明ではない。 |
| D1620「最遅 shard の wall (collection 開始から teardown 終了まで)」 | junit の代表 node や総和だけによる完了判定は不可。 |
| D1708「消費者が時間的に散っていることを先に示せた場合だけ採る」 | worker 跨ぎ共有案の条件。base 内部の構築費削減一般を禁じてはいない。 |
| D1728「各 shard が同一の全 collection」 | output fixture の集合を直接固定する裁定ではない。ただし同じ縮小集合による自己証明の問題は共通する。 |
| D1918「観測 9 走で shard-2 が一度も 300 秒を切らなかった」 | 過去の観測。今後の t080 最適化を永久に禁じる文言ではない。 |
| D2001「受入自身が検査を黙って落とすのを防ぐ検査には適用しない」 | 毎走から外す検査の境界。全 output ファイルの複製を直接命じた裁定ではない。 |
| D2046「`pre` は短縮しない」 | C はこの変更面に入らない。 |
| 項35「効果を先に測り、未確認のまま実装しない」 | C の効果は未確認。比較候補をそのまま採用済み実装へ進める根拠にはならない。 |

T:1332–1361 は通常 consumer 6関数・展開11 node と parametrize を固定する。plan にその増減はない。ただし、この集合保存と、所見1・2の入力感度／観測値保存は別問題である。

## 親 brief への指摘

- **アンカー訂正:** brief:30 の orchestrator コピーは T:1373 ではなく **T:1380**。T:1373 は `git init`。brief:31 の helper 定義は T:963 ではなく **T:964**。T:827、794、576、1385 は該当する。plan も可視集合 assert を T:1703–1705 とするが、実際は **T:1705–1707**。
- **「output は4 pathだけ」は誤り。** M:37–40 は4定数の宣言にすぎない。`verify_receipt` は M:2343→2201→H:608 で全体列挙へ入り、発行時には K の campaign 探索も走る。
- **144秒の帰属は誤り。** 所見3のとおり、発行なし base、2回のコピー等を含む node 時間である。
- **1,852→22,976件と15〜22→144秒の対応は証明されていない。** T:865–868 の古いコメントは、ignored な1.8GB・36,158 files を巻き込んだ際の121.7秒との比較である。15〜22秒が現在の「発行なし共有cache検査 node」と同じ測定区間だった証拠はない。また tracked 件数は、非 ignored untracked を含む現 helper の入力件数そのものでもない。
- **成長項の存在と、時間増加の原因同定を混同している。** 全件処理があることはコードから確認できる。しかし二時点の件数比から、7〜9倍の時間差の主因や比例則は確定できない。P3 の「固定費に埋もれた」も未検証の説明である。
- **「単独走でも遅いので混雑でなく固有費用」は強すぎる。** login の単独テストも共有資源の混雑から独立ではない。brief:52 自身が login 単独測定を根拠にしないとしており、brief:23 の断定と整合しない。
- **325.5秒の測定面を明示すべき。** brief は junit 中央値を掲げるが、D1620 の達成判定は canonical receipt の最遅 shard wall。一次成果物を今回再集計していないため、この両者の一致や直近7走の選定妥当性は未確認である。

## 総括

**plan は条件つき採用。**
C の比較実験に限る。固定 whitelist と全 object store 借用は判定・観測を変える。
144秒の帰属と数値モデルを訂正し、旧新入力・tree・fixture固有負例の保存を確認する必要がある。
C の短縮が実測されても、「成長比例を断つ」という brief の完了条件は未達のままである。