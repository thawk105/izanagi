## 費用経路

**「output は4 pathしか必要ない」という前提は成立しない。** 直接参照の先で、known-axes の production builder が campaign 成果物を読み、holdout の production scanner が Git-visible file 全体を読む。このため、固定集合への縮小を現行 assert だけで正当化できない。

以下、行番号は現 checkout。略称は次のファイルを指す。

- **T**: [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/tests/test_s8b_oracle_driver.py)
- **M**: [t080_freeze_migration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/t080_freeze_migration.py)
- **K**: [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s1_known_axes_freeze.py)
- **H**: [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s8b_holdout_freeze.py)

| 経路 | アンカー | 費用と成長依存 |
|---|---|---|
| base の取得・構築待ち | T:918、T:980 | 4フィールドの key ごとに構築。共有側では lock 待ちにも構築時間が載る |
| production source の配置 | T:1379 | `orchestrator/` 全体の `copytree`。output 件数には直接比例しない |
| output の可視性列挙 | T:794 | tracked regular と非 ignored untracked regular を列挙。**O(全件)** |
| source の検査・祖先集合構築 | T:834、T:842 | file/symlink 検査と祖先 path 集合構築。**O(全件)**、深さにも依存 |
| output の物理複製 | T:869、T:1385 | receipt/draft を除いた全可視 regular file。**件数・bytes に比例** |
| historical source の上書き | T:1387、T:1431 | known JSON の path/hash 閉包を実 receipt の basis blob から復元。要求集合に比例 |
| submodule の配置 | T:1443 | ccbench の追加・pin checkout。output 件数とは別の費用 |
| 初期 index・commit | T:1451、T:1452 | `git add -A` が配置済み全ファイルを処理。**件数・bytes に比例** |
| receipt 発行 | T:1572、T:1575、T:1576 | draft → validate → finalize。production 再構築・全体 scan を繰り返す |
| 発行後の検証 | T:1600、T:1601 | verifier と public gate。ここにも全体 scan がある |
| base→各テスト | T:1000 | `.git` を含む独立実体の `copytree`。**件数・bytes に比例** |
| base の削除 | T:876、T:914 | 全 tree の削除。teardown にも成長項が残る |

**144秒の解釈には留保が必要。** 計測元の `test_t080_shared_base_builds_real_builder_once_across_processes` は T:1057 で `issue_receipt=False` を渡す。したがって、その約144秒には T:1460 以降の発行 subprocess は含まれない。発行あり key の構築時間と同一視せず、親の次回計測で分離する。

## 全件複製の要求元

**1. fixture helper 自身の契約**

T:827 は「全可視 regular file、ただし receipt/draft を除外」という集合を要求する。T:1633 の小型 repo テストは、T:1703 の可視集合一致、T:1704 の production 列挙一致、T:1705 の複製集合一致を検査する。T:1707 以降は tracked file の実体欠落を拒否する。

ここで要求しているのは**path 集合と実体の存在**であり、22,976という固定件数ではない。この helper を固定 whitelist に変更すると、この契約を壊す。別 helper に置き換えて既存テストを残すだけでも、実際の e2e builder が同じ集合を使う保証にはならない。

**2. known-axes の production 再構築**

呼出しは T:1572 → M:1956 → M:1677 → K:734。

| consumer | アンカー | 要求内容 |
|---|---|---|
| P2、backoff の候補検索 | K:349、K:384 | workload ごとの glob に一致する WAL 集合と内容 |
| screening 判別 | K:255 | 各候補の `campaign.lock` の存在・JSON内容。欠落時は拒否 |
| COMMIT・genome 読取 | K:278 | WAL bytes、重複・数値・候補整合 |
| sort 本走・再測定 | K:437、K:469、K:494 | provenance/WAL。再測定候補は **exact 1件** |
| trigger・recon | K:570、K:583 | recon Markdown、main/remeasure provenance bytes |
| source 記録 | K:207、K:217 | source path と bytes の hash |

現 known JSON に含まれる output の path/hash 参照は、静的抽出で**22個の一意 path**だった。しかし、これだけでは閉じない。例えば `campaign.lock` と、glob で発見される追加候補は、この22 pathからは導出できない。

M:1697 の projected/rebuilt 完全一致は残す必要がある。候補を事前に除外すると、追加候補による不一致・非一意性を検出しなくなるため、この gate があるだけでは縮小の等価性を証明できない。

**3. holdout の全体 scan――全件要求の主要な根拠**

発行時には次の全経路がある。

- M:1727 の `search_repository(root)`。
- M:1731 の production `verify_document` 内での再 scan。
- M:1750 の validate/finalize による再構築。
- M:1889 の draft/receipt 追加後の汚染検査。呼出しは M:1985、M:2023、M:2048。

発行後も、M:2343 → M:2191 → **M:2201** が `search_repository(root)` を呼ぶ。static adapter も M:2490 から同経路へ入る。

H:370 は tracked regular、非 ignored untracked regular、ccbench tracked regular を列挙する。H:608 からその全体を処理し、既定では H:45 の `output/s8b-freeze/` だけを prefix 除外する。残りは H:618、H:482 で**実際に bytes を読む**。

要求は次のとおり。

- 非除外 path 全体の存在・可読性・bytes。
- rr80/rr20 conjunction が0件、rr50陽性対照が正数であること：H:714。
- draft の再検証では、軸別件数・hit path を含む semantic scan hash の一致：M:1741、M:1761。
- 一方、総 `file_count` 自体はこの hash に含めない。凍結時の軸別件数と現在値の完全一致も要求しない：H:1000。

したがって、**「固定件数を要求しない」から「任意の file を落としてよい」は導けない。** 除外予定の file に conjunction を追加すると、現行経路は拒否し、縮小 fixture はそれを見なくなる。

**4. builder が組む repo に対する Git 操作**

- T:1451 の全体 add、T:1452 の basis commit。
- M:1790 の全体 status。M:1833 は clean、M:2013 は「指定 draft 1件だけ dirty」を要求。
- M:1301、M:1365、M:1384、M:1399 は basis 内の source/artifact blob を検査。
- M:2055 は receipt の履歴・worktree bytes、M:1253 は introduction の diff が receipt 1件だけであることを要求。
- M:883 は recorded commit の**object 存在と ancestry**を観測する。tree が同じでも object store を増やせば観測は変わり得る。

Git は全件を業務上の固定件数として要求してはいないが、配置された集合の clean 性と履歴を検査する。未配置 file の検出を代替するものではない。

**5. e2e の各 consumer と assert**

T:1285 の AST 検査が固定する通常 consumer は6関数・展開11 node。親の「t080群38 node」とは別の集合である。

| consumer | アンカー | output に関わる保証 |
|---|---|---|
| 正常発行・public gate | T:1735 | source/metadata golden、active-valid、17 observations、fixture Git blob 由来の期待値、exact floor/budget 拒否 |
| 単一 defect | T:1835 | freeze bytes、ccbench pin、未知性違反の exact reason。未知性負例は T:1892 の root直下 file |
| 残りの defect | T:1924 | closure、schema、pairing、reconstruction、陽性対照の exact reason |
| 履歴 defect | T:2156 | trailer、extra path、modify/revert の単一 reason |
| 発行後削除 | T:2182 | receipt 削除履歴、subprocess の再発行拒否、historical source bytes 不変 |
| never-issued gate | T:4753 | copied freeze/source、実 verifier 呼出し、held/released の exact refusal 集合 |

正常発行テストの report consumer は [s8b_oracle_report.py:251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s8b_oracle_report.py:251) から historical receipt、basis blob、ancestry を再導出し、同 :317 で envelope を完全一致させる。これは output 全体を scan しない。

public gate は [s8b_oracle_driver.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/campaign/s8b_oracle_driver.py:467) の adapter、同 :482 の legacy holdout verifier、同 :518 の known verifierを通る。後者は K:903 で copied source を読み、K:948 で再構築する経路も持つ。

**6. snapshot・隔離の検査**

T:571 → [output_snapshot_ignores.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/tests/output_snapshot_ignores.py:636) は、渡された tree の path・mode・size・mtime・ctime を読む。T:1720 の対象は**実 repo の output**であり、fixture に同じ全 tree を複製する要求ではない。

T:37 は temp root の配置境界、T:1540・T:1554 は subprocess の loader/module root、T:1087 はテスト間の独立実体を検査する。それぞれ別の隔離条件である。

以上から、複製全件がすべて必要とは断定しないものの、**非除外 output 全体の bytes を要求する consumer は実在する**。親のP1はそのままでは採用できない。

## 候補案

**A. consumer の要求集合へ限定――固定 whitelist は採らない**

差分骨格：

```text
T:1385  全可視 output の複製を、要求集合 R の個別複製に置換
T:1387  known の source closure を複製前に抽出
T:1400  operational と builder の WAL/lock/provenance 要求を R に加える
T:1451  配置した R と既存 source/submodule を index 化
```

ただし、安全な `R` は少なくとも次を含む。

```text
historical source closure
∪ operational artifacts
∪ known builder が探索する候補・付随ファイル
∪ holdout scanner の非除外 Git-visible output 全体
```

これでは要求集合自体が repo とともに増える。逆に、最後の集合を省いて22 source path等に限定すると受理集合が変わる。

T:1892 の未知性負例は root直下への追加しか検査しない。**この assert が緑でも、複製対象外の output による拒否を失っていない保証にはならない。** T:1704 も helper の小型 repo 契約であり、別経路に置き換えた e2e の閉包証明にはならない。

既存 scan 除外 prefix 内で、直接参照・closure にも使われない file だけを除く余地はある。ただし削減量は未確定で、成長比例は断てない。固定 whitelist 案は検出力維持を担保できないため採らない。

**B. 実 repo の SHA と alternates を利用――採らない**

差分骨格：

```text
T:794   ls-files -s の mode/OID/path を保持
T:1373  fixture の object lookup に実 repo の object store を接続
T:1385  update-index --index-info と checkout-index で output を配置
T:1431  historical source の上書きは維持
T:1451  上書き分・untracked 等だけ add
```

問題は三つある。

1. **index SHA は現行 worktree bytes と同義ではない。** 現行 helper は unstaged変更・非 ignored untracked を複製する。SHAだけを使えば、それらを落とし得る。
2. `checkout-index` は独立 worktree の実体を作る処理を残す。全体 scan があるため、indexだけ作って materializeしない案も成立しない。
3. 全 object store の alternates は M:883 の `missing-commit` を `not-ancestor` 等に変え得る。T:1782 は最初の15 observationしか独立期待値と比較せず、T:1811 の report一致も双方が同じ追加 object を見れば通る。**既存 assert はこの変化を必ず検出しない。**

T:37 の配置境界や subprocess import隔離には、read-onlyな object参照自体を禁止する文言はない。しかし、それらは object lookup の隔離を保証もしない。host の object保全への継続依存と ancestry観測の変更を含む案を、同一treeだけを根拠に等価とは判定できない。

**C. 必要 blob だけを fixture 内へ移送し、独立 index を組む――比較実験の候補**

Bから、hostへの継続依存と不要なcommit objectの可視化を除いた案。

```text
T:794   全可視 path の列挙契約を維持し、再利用可能な blob OID を得る
T:1385  同じ path/bytes/mode の独立 worktree を作る
         対象 blob だけを self-contained pack 等で fixture .git 内へ移送
T:1431  historical basis による上書きを従来どおり維持
T:1451  再利用対象を update-index --index-info で登録
         dirty/untracked・上書き対象・その他 source は通常の add
T:1452以降、T:1000、production code、既存 assert は維持
```

実装条件は、再利用判定でworktree変更を隠さないこと、既存のGit変換・modeと同じtreeを作ること、packを外部base objectに依存させないこと。commit履歴全体やrefsは移送しない。

受理集合維持の根拠は、**同じ可視path・bytes・modeを供給し、同じfixture内履歴を構築すること**。T:1703–1705、T:1758、T:1782、T:1903、T:2173、T:2296、T:4830の保証をそのまま残せる。T:1087の実体独立性、T:1540以降のimport隔離とも両立する。

ただし、既存assertだけでは「全outputの旧新tree一致」や「packの完全自立」を保証しない。親の比較probeで確認する必要があり、未確認なら採らない。**これは再ハッシュ等の係数削減案であり、成長比例を断つ完成案ではない。**

いずれもテスト削除・assert緩和・保留追加は行わない。D747の「削除0件」、D2001の欠落検出維持、項35の「効果を先に測り、未確認のまま実装しない」を維持する。

## 効果見積り

親の値を使った**条件付き算術**と、実証済み効果を区別する。

- 基準：`144 + 8.47 + 70 = 222.47秒`。最長nodeの222.51秒と概ね一致する。
- shard-0の超過25.5秒を、そのnodeから同量削れるモデルなら、必要条件は  
  **`222.51 − 25.5 = 197.01秒` 未満**。
- copyと本体が不変なら、baseは  
  **`197.01 − 8.47 − 70 = 118.54秒` 未満**が目安。

| 案 | 削減対象 | 算術上の見積り・限界 |
|---|---|---|
| A | 対象外fileの列挙後処理・copy・add・後続scan | 安全な除外集合の件数・bytes・時間が未測定なので秒数は見積れない。`4/22,976`による比例計算は閉包が誤っているため不可 |
| B | 再利用対象のadd処理 | 仮に76.83秒を丸ごと消せれば、base67.17秒、node145.68秒。ただしcheckout・index・dirty処理をゼロとした反実仮想であり、案自体も不採用 |
| C | 再利用blobの再ハッシュ・圧縮・object書込み | 同じ反実仮想では145.68秒。実際の短縮は `76.83 − 移送/index費 − 残存add費 − 配置方式の追加費`。各費用は未測定で、短縮の符号も未確定 |

**`144 − 76.83 = 67.17秒`をcopy費用とは呼べない。** 144秒と76.83秒は同条件の成分計測ではなく、前者のkeyにも留保がある。8.47秒はbase→testの別操作であり、source→baseのcopy費用へ流用しない。

197秒条件も十分条件ではない。他workerへの律速移動、非重複tail、teardown、他shardを含め、同一canonical commandのreceiptで最遅shard wallが下がる必要がある。D1620に従い、junit単体や所要総和だけでは完了判定しない。

## 成長比例の判定

| 案 | output件数に対する費用 | 判定 |
|---|---|---|
| A：固定whitelist | コピー・indexはO(要求集合) | 検出力維持を証明できず不採用 |
| A：実consumerの閉包を維持 | 要求集合に全非除外outputが入るため **O(全件)** | 安全な部分削減にとどまる |
| B | 全件列挙・checkout・scanが残り **O(全件)** | 隔離・観測の問題もあり不採用 |
| C | 全件列挙・移送・配置・scanが残り **O(全件)** | 係数削減のみ |

**現行の入力感度を保存したまま、今回の変更面だけでO(1)または固定の要求集合へ落とす案は成立確認できていない。** 全件のbytesに依存するconsumerを残しながら、その入力を無検査で省くことはできない。

## 変異事前登録の候補

既存node/assertの増減を避け、親が実行する独立probeとして登録する。

| 変異点 | 変異 | 殺す観測 |
|---|---|---|
| T:1451 | Cのindex再利用を無効化し、従来の全面addへ戻す | 同一条件のbase構築・canonical receiptのA/B。緑だけでは効果を判定しない |
| T:1385 | 非除外outputの任意fileを複製から落とす。対照入力には三軸conjunctionを置く | 現行のM:1728／M:2229による拒否を候補も維持すること。固定whitelistの盲点を殺す |
| T:794／T:1451 | unstaged変更fileに古いindex SHAを使う、またはuntrackedを落とす | 旧新のpath/mode/blob一致probeとproduction scan結果。不正な「SHA＝現物」を殺す |
| T:1373付近 | fixtureに実repo全体のalternatesを残す | host参照なしでのblob可読性と、M:883のancestry結果の旧新一致。既存report一致だけでは不足 |
| T:1385／T:1431 | 必須campaign lockを落とす、またはhistorical上書きを現行bytesへ置換 | K:265の欠落拒否、M:1323の12/51閉包、M:1697の完全再構築一致、T:1782のfixture由来期待値 |

## 未確定事項

- 発行あり／なしの各keyについて、144秒の成分分解が必要。submodule費用も未分離。
- Cのblob移送が再addより安いか、配置時のGit変換・modeを等価に扱えるかは未確認。
- 現行assertには、任意outputの脱落、host object可視化、全面的な旧新tree一致を直接捕まえない部分がある。全走が緑でも、それらの等価性証明にはならない。
- [growth_test_holds.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2559-accept-floor/orchestrator/tests/growth_test_holds.py:201) では実repoのscan検査が保留登録されている。その検査が毎走で補完すると仮定できない。保留の追加・解除・迂回は行わない。
- 射影ファイルは読取可能だった。編集・commit・pytest・性能測定は行っていない。

## 総括

比較実験へ進める1案としては **C：必要blobのfixture内移送＋独立index構築**を推す。全入力と隔離を保ちながら、再addの費用を削る余地がある。
ただしCもO(全件)であり、「成長比例を断つ」という完了条件は満たさない。
その条件まで満たす採用案は現時点ではない。親のP1を全体scan・builder閉包込みに修正する必要がある。