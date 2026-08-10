# 結論

`b01`〜`b03` だけを持つ草案は起草できるが、現状のまま発効可能な追補 B にはできない。個別公表 family の構成と検定統計量が、core / 追補 A で公表用として一意に固定されていないためである。草案は `authority: none` のまま承認パッケージへ返す。

以下では、数値案として `b01 = 1`、`b02 = 個別公表系列全体で 0.05 を第1候補へ不可逆に割当て`、`b03 = F を根とする別台帳＋primary 予約 digest への片方向束縛` を推奨する。ただし `b01` と `b02` の数値は governance 裁定であり、pilot raw から導出した値ではない。

## 正本から確定している境界

- core は B の field を `{b01,b02,b03}` に閉じ、欠落・余剰を解決失敗とする。[preregistration.md:311–360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:311)
- D234 も、B は候補数上限・個別公表 spending・台帳の根だけを持ち、`q` に影響する量を持たない、と再確認する。[decisions.md:10999–11015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/decisions.md:10999)
- 追補 A の grammar は、`## fields` から次の `## ` 見出しまでにある `### ` 見出しの先頭 token だけを field key とする。[addendum-a-reissue.md:52–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:52)
- 実装面は producer 実装 wave の責務であり、本件では resolver・producer・validator・台帳・schema・テストを作らない。[preregistration.md:366–370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:366)、[decisions.md:11065–11068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/decisions.md:11065)

## 1. `b01` の逐語案

予定本文は次とする。

```markdown
### b01 — 候補数上限

正規の根 `F` に属する候補数上限を `K = 1` とする。
許容される候補 ordinal は `{1}` だけである。

候補は canonical な primary 予約 entry が create-only で確保された時点で
1 件と数える。失敗・中断・未公表でも ordinal を解放、再利用、付け替えしない。
同一候補の事前登録済み予備 allocation は新しい候補には数えないが、全 attempt を保持する。

ordinal `2` 以降を同じ根の候補として投入してはならない。第 2 候補を扱うには、
本 core を変更せず、別 study の新しい core とユーザー裁定を起こす。
```

根拠と限界：

- core が固定した候補は exact bytes に束縛された `modeX` 1 本だけである。[preregistration.md:51–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:51)
- 追補 A も `modeX` の source triple・patch・macro を一意に固定している。[addendum-a-reissue.md:399–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:399)
- したがって `K=1` は、この凍結 core の受理対象を拡張しない最小の有限 cap である。ただし core 自身が数値を導出しているわけではないため、最終的には governance 裁定である。

親 brief の (P3) は採らない。`a12` の `δ_MC=0.001` は、60 simulation セルを束ねる Monte Carlo 上側信頼主張の誤り予算であり、検定可能な p 値の「解像度」ではない。[addendum-a-reissue.md:825–838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:825)、[addendum-a-reissue.md:878–892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:878)

仮に調和 spending を置けば、(P3) の式は

```text
0.05 / [6k(k+1)] >= 0.001  ⇒  k(k+1) <= 8.333…  ⇒  k <= 2
```

となるが、前提となる `δ_MC` の用途が違うため `cap=2` の根拠にはならない。

## 2. `b02` の逐語案

予定本文は次とする。

```markdown
### b02 — 個別公表系列の累積 spending 関数の数値割当て

個別公表系列に固有の累積 spending 関数を `A_pub` とし、次で固定する。

    A_pub(0) = 0
    A_pub(1) = 0.05
    domain   = {0, 1}

したがって第 1 候補の個別公表 familywise level は

    alpha_pub,1 = A_pub(1) - A_pub(0) = 0.05

である。`b01` により第 2 候補は許容されない。

予約された候補は、実行・検定・公表の成否にかかわらず当該割当てを不可逆に消費する。
未使用量の回収、別候補への再配分、失敗後の再利用は行わない。

`alpha_pub,1` は個別公表系列だけの量であり、primary 系列の有意水準、
臨界値または受理条件の入力として使用しない。
```

`0.05` は core / 追補 A から数学的に導出できない。親 brief の (P2) が置いた governance 候補にすぎず、ユーザー承認が必要である。[s1-brief.md:53–67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:53)

有効な周辺 p 値と Holm 手続きが別途すでに固定されているなら、候補内 6 セルの FWER は `0.05` 以下、候補 cap が 1 なので系列全体も `0.05` 以下となる。ただし後述のとおり、その「有効な周辺 p 値」が現文書では固定されていない。このため、この数値割当てだけでは B を発効できない。

## 3. `b03` の逐語案

予定本文は次とする。

```markdown
### b03 — 累積台帳を束縛する正規の根の同定方法

個別公表系列の正規の根は、次の ordered pair とする。

    publication_family_root = (
        fold_commit = 88d68f9127b31df5aafc3d59607896626a1652e8,
        ledger_kind = individual_publication
    )

`fold_commit` と `ledger_kind` は上記の literal から導出し、
caller、receipt、親系列 ID、試行 IDの申告値を入力にしない。
新しい正規の根を作れるのは、新 study を承認する canonical なユーザー裁定だけである。

個別公表台帳は primary 台帳とは別の canonical 台帳とし、累積量を混合しない。
ただし個別公表の予約 ordinal は独立に自己申告させない。

本 study では、primary 台帳の `(F, 1)` にある一意な create-only 予約 entry を先に解決し、
個別公表台帳へ ordinal `1` の entry を create-only で予約する。
個別公表 entry は primary 予約 entry の digest を必須の親参照として持ち、
個別公表 ordinal は参照先 primary ordinal と exact 一致しなければならない。

個別公表 entry は `(publication_family_root, ordinal)` と
`primary_reservation_entry_digest` の双方について一意でなければならない。
失敗・中断・未公表でも entry を削除せず、ordinal を解放または再利用しない。

canonical な両台帳に対応する entry が無い、重複する、digest が一致しない、
または ordinal が一致しない場合は、追補 B の解決および本走投入を拒否する。
その場合も primary の有意水準または臨界値を計算し直さない。
```

この案は a13 を変更しない。a13 は primary 側について、根 `F`、本 study の `k=1`、create-only 予約、canonical 台帳、失敗時も番号を解放しないことを既に固定している。[addendum-a-reissue.md:919–938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919)

追補 A の裁定パッケージも、採用案では `a13` が primary 台帳、`b03` が個別公表台帳だけを受け持つとしている。[package.md:131–162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-addendum-a/package.md:131)

二台帳は別々のままである。公表台帳から primary の不変 entry へ foreign-key 相当の片方向参照を置くだけで、spending の合算や primary 台帳の書換えは行わない。公表 ordinal を primary ordinal から再導出させるため、別台帳を理由に `k=1` を独立主張する経路を塞げる。

## 4. pilot raw と `q` への非依存

| field | pilot raw に依存しない理由 | `q` に影響しない理由 |
|---|---|---|
| `b01` | `K=1` は凍結済みの候補 identity と governance 裁定だけから決まり、TPS、pilot 共分散、失敗率を読まない | 候補 admission の上限だけで、`J`・primary alpha・臨界値を設定しない |
| `b02` | `A_pub(0)=0`, `A_pub(1)=0.05` は事前固定定数と台帳 ordinal だけの関数 | `alpha_pub` を別 namespace に置き、primary の入力として使わない |
| `b03` | 入力は固定 commit `F` と create-only 台帳 metadata だけ。性能 raw を根・ordinal・digest 選択に使わない | primary entry は読み取り参照だけ。相違時は投入拒否し、primary 側を再計算しない |

a11 の `q` は `J` と primary の `α_k` だけの関数である。[addendum-a-reissue.md:783–797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:783)  
a13 は本 study の primary 値を `α₁=0.025` と固定し、B が `q` に影響しないことを明記している。[addendum-a-reissue.md:894–917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:894)

したがって B から primary の `q`、`α₁`、`J` を参照して数値を分岐させる文は置かない。

## 5. 個別公表 family の 6 セル

### 逐語から確定する事実

- core は「個別公表は6セル全件」とだけ書き、セル identity を同じ文では列挙していない。[preregistration.md:246–256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:246)
- §16 も「6セルすべての調整済み p 値と同時区間」とだけ書く。[preregistration.md:438–442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:438)
- 追補 A の `a10` は planning vector を `(N_W1,H_W1,G_W1,N_W2,H_W2,G_W2)` とする。[addendum-a-reissue.md:630–634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:630)
- `a12` も simulation の60セルを `10 J × 6成分 (W1/W2 × N/H/G)` とする。[addendum-a-reissue.md:858–866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:858)

### 判定

意図としては `{W1,W2}×{N,H,G}` が最有力であり、親の (P1) は自然である。しかし `a10` は標本数設計、`a12` は primary stress check の文脈であり、「これを個別公表 family とする」という逐語はない。core には `D` も定義されているため、`{N,H,G}` と `{D,N,G}` のどちらを公表セルとするかを、文面だけで形式的に排除できない。[preregistration.md:62–87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:62)

したがって厳格な exact-key 契約では「決まらない」と判定する。B で `{W1,W2}×{N,H,G}` を新規定義すると、見出し parser 上は `b02` 内に隠せても、意味上は「family 構成」という余剰 field を設定することになる。草案では既存の「core §10/§16 の6セル」とだけ参照し、構成を確定したふりをしない。

## 6. 個別公表の検定統計量

### 固定状況

固定されていない。

- core §7 は、統計量が cluster 間の標本平均・標本共分散だけから作られることを要求するが、式は一意にしない。[preregistration.md:198–221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:198)
- `a10` の `T_k=√J·μ̂_k/s_k` は sample-size planning と primary 受理確率のための定義である。[addendum-a-reissue.md:684–704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:684)
- `a11` は primary の同時領域と `q` を固定するが、個別公表の未調整 p 値、帰無仮説の向き、closed testing の局所検定、同時区間の inversion を固定しない。
- brief が述べる「Holm / closed testing」は adjustment の名前にすぎず、入力となる周辺 p 値を定めない。[s1-brief.md:28–29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:28)

### 解決選択肢と成果物影響

| 選択肢 | 判定 | 成果物影響 |
|---|---|---|
| `b02` 内に `T_k`、片側 p 値、Holm、区間 inversion を書く | 不可 | 見出しは3個でも意味上の余剰 field。B は exact-key 解決失敗 |
| 別の publication protocol / Addendum C を足す | 不可 | core が委譲していない第3の推論権威になる。B の閉集合違反 |
| producer 実装 waveで統計量を選ばせる | 不可 | pilot/raw を見た後の実装裁量となり、事前登録が完結しない。本走 gate は閉じたまま |
| 6セルを記述値だけにして inferential claim を捨てる | 現 core では不可 | core §16 の調整済み p 値・同時区間要求を変更するため、別 study が必要 |
| `a10` の `T_k` が公表にも適用される、と解釈裁定だけで補う | 不十分 | family、周辺 p 値、局所 intersection test、同時区間がなお未定。canonical decision が core 外の推論規則になる risk も残る |
| 新しい core で family・null・統計量・p 値・adjustment・区間を明記する | 唯一の clean な解 | 別 study、新 core、新 A/B、再承認が必要。既存 core を書き換えない |

したがって、数値案を持つ B 草案は作成してよいが、現 study の「完結した追補」として承認・発効してはならない。

## 7. 草案文書の節構成

予定する行配置は次のとおり。

| 予定箇所 | 内容 |
|---|---|
| `addendum-b.md:1–8` | title、`authority: none`、`default_effect: no-state-change`、study label、document kind |
| `:10–32` | `## 0. 本書の位置づけ`、発効条件、自己 digest 禁止、core の path/commit/SHA-256 三つ組 |
| `:34–44` | envelope grammar と exact-key 宣言 `{b01,b02,b03}` |
| `:46` | `## fields` |
| `:48–59` | `### b01` と上記逐語 |
| `:61–78` | `### b02` と上記逐語 |
| `:80–108` | `### b03` と上記逐語 |
| `:110` | 次の `## ` 見出しで fields 範囲を終了 |
| `:112–125` | `## 本書が主張しないこと` — 未実装、未発効、family/statistic gap、pilot raw 非依存 |

`## fields` の直下には、空行を除き次の順で置く。

```markdown
## fields

### b01 — 候補数上限
...
### b02 — 個別公表系列の累積 spending 関数の数値割当て
...
### b03 — 累積台帳を束縛する正規の根の同定方法
...

## 本書が主張しないこと
```

fields 範囲内に他の `###` 見出しを置かず、小節は太字ラベルで書く。したがって grammar が得る key は、順序を無視しても厳密に `{b01,b02,b03}` の1集合となる。metadata、`core_ref`、末尾 disclaimer に現れる `bNN` は field key にならない。

## 8. 承認パッケージへ返す裁定

1. `b01` を `K=1` とし、この凍結 core に第2候補を入れないことを承認するか。
2. 個別公表系列の総 FWER budget を governance 値 `0.05` とし、cap 1 の第1候補へ全額を不可逆に割り当てるか。
3. 親 (P3) の `δ_MC` 根拠を棄却することを確認するか。
4. 公表6セルを `{W1,W2}×{N,H,G}` と読む意図はあるか。ただし現 core の逐語では固定不足であり、B に書く案は余剰 field になることを受け入れるか。
5. 公表用の null、検定統計量、未調整 p 値、closed-testing 局所検定、同時区間が未固定であるため、新 core の別 study へ戻すか。
6. `b03` を、同じ `F` に domain-separated した別公表台帳とし、primary 予約 entry digest・同一 ordinal へ片方向束縛する案を承認するか。
7. 上記が未解決の間、`addendum-b.md`・`package.md`・`README.md` をすべて `authority: none` とし、凍結・発効・本走 admission を行わないことを確認するか。

## 総括

推奨値: `b01=1`、`b02: A_pub(0)=0, A_pub(1)=0.05`、`b03: (F, individual_publication)`＋primary予約digest・同一ordinalへのcreate-only束縛。  
裁定へ返す論点: `K=1` と公表alpha `0.05` のgovernance承認、6セル identity、公表用検定統計量、新coreへ戻す可否、b03の片方向束縛。  
最大の risk: family と検定統計量が未固定のまま、見出しだけexact-keyの B を発効させて `b02` に適用先があると誤認すること。