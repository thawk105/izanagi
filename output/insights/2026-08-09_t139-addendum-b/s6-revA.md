## 1. `[blocker]` weak mean null のもとで周辺 p 値が妥当でなく、FWER 論証が閉じていない

[判定]  
spending の算術自体は条件付きで正しい。各候補について Holm が strong FWER `≤ α_pub_k` を持つなら、候補間の独立性なしに union bound で `Σ_k α_pub_k ≤ 0.05` となる。  
しかし必要条件である「各周辺 p 値の超一様性」が、cluster 代表値の非正規性を許す weak mean null では成立しない。

[根拠: `addendum-b.md:129-134`]  
> 帰無は core §7 が primary と定めた weak mean null (`E[·] ≤ 0`)  
> `p_k = 1 − T_{J−1}(T_k)`  
> Holm を 6 セルへ適用する

[根拠: `addendum-a-reissue.md:827-838`]  
> 本 field はその較正を与えない  
> 「cluster level の weak mean null における真の型 I 誤りを較正した」とは主張しない

[根拠: `addendum-a-reissue.md:958-961`]  
> Hotelling・`t`・非心 `t` の有限標本分布は cluster 代表値の iid 多変量正規 planning model に依存する。cluster 分布が非正規なら被覆も検出力下界も保証しない。

反例（推論）: ある真の帰無セルの cluster 代表値 `Z` を、確率 `0.9` で `1±η` の狭い連続分布、確率 `0.1` で `−9±η` の狭い連続分布とすれば `E[Z]=0` である。`J≤13` では全 cluster が正側になる確率が少なくとも `0.9^13≈0.254`。`η` を十分小さくすれば、その事象で標本分散は正だが `T` は任意に大きくなり、`p<0.025/6` となる。したがって Holm は真の帰無を確率少なくとも約 0.254 で棄却でき、候補内 FWER `≤0.025` は破れる。この分布は大きな正定数を各 throughput に加えることで `(S,D_g,X)` の正値制約にも埋め込める。

[成果物影響]  
個別公表表の未調整・調整済み p 値、有意セル集合、材料レポートの「有意」主張が変わる。`alpha_pub` を primary へ流さない契約が守られる限り certified 選択そのものは変わらないが、公表結果を proof chain 付き材料として受理できない。

[最小の直し方]  
`b02` からこの p 値規則を除き、別 study の新 core で、次のどちらかを事前固定する。

- iid 正規を公表推論の明示的仮定とし、結論を model-based に限定する。
- weak mean null に対して有限標本妥当性を持つために必要な boundedness・tail 条件等を追加し、それに適合する検定を定義する。

そのうえで、候補ごとの条件付き strong FWER と候補横断 union bound を別々に証明する。

## 2. `[blocker]` `a10` の planning 定義を公表手続きへ流用する裁定は飛躍している

[判定]  
`a10` に 6 成分と `T_k` の式が存在する、という親の逐語確認は正しい。だが、それが固定しているのは標本数設計用の planning 統計量であり、公表用の帰無分布・p 値・Holm 接続・区間構成まで既存契約になったとは言えない。  
段 2 の「どこにも定義されていない」は反証できても、「公表 family と統計量は固定済み」という段 4 の結論は反証しすぎである。

[根拠: `addendum-a-reissue.md:684-704`]  
> 最悪検出力の下界  
> planning model のもとで `T_k` は […] 非心 t 分布に従う

[根拠: `s4-adjudication.md:14-18`]  
> 公表 family の構成も周辺統計量も、既に発効済み文書で固定されている。

[根拠: `preregistration.md:339-343`]  
> `b02` | 個別公表系列の累積 spending 関数の数値割当て

[根拠: `preregistration.md:313-316`]  
> それ以外の変更は core の変更に当たる。  
> 新しい core を起こしてユーザー裁定へ戻す

[根拠: `preregistration.md:438-441`]  
> 6 セルすべての調整済み p 値と同時区間を […] 固定表で公表する

core は「公表する」としか定めず、p 値の分布写像と区間の作り方を定めていない。`addendum-b.md:130-138` の t p 値と `a11` 区間流用は、単なる数値 spending ではなく新しい推論規則である。

[成果物影響]  
公表表の p 値、調整済み p 値、有意判定、同時区間およびそれらの権威参照が未確定になる。材料レポートは一意に再生成できず、試行台帳から公表 proof chain を閉じられない。

[最小の直し方]  
B3(a) を承認可能な解釈として扱わない。追補 B は `b02` の数値 schedule だけに戻し、公表 family、weak-null 検定、調整済み p 値、区間と判定の対応を新 study の core で凍結する。少なくとも producer 実装 wave が推論規則を選ぶ形にはしない。

## 3. `[must-fix]` Holm の棄却と `a11` 同時区間は双対でなく、同じ表で矛盾する

[判定]  
`alpha_pub_1=0.025` の Holm と、workload ごとに `α₁=0.025` を使う `C_w(q)` は別の手続きである。同じ数値 `0.025` でも family と被覆対象が異なり、棄却セルの区間が 0 を含む事象が起こる。

[根拠: `addendum-b.md:132-139`]  
> Holm の閾値列は […] `0.0041666…`, […] `0.025`  
> 同時区間は […] `C_w(q(J, α₁))` をそのまま用いる  
> 2 workload の union bound は `0.05` 以下

[根拠: `addendum-a-reissue.md:783-792`]  
> `[Hotelling の失敗確率] + [1 − T_{J−1}(q)] ≤ α_k`

Hotelling 項が正なので `1−T(q)<0.025`、したがって `q` は片側 0.025 の t 臨界値より大きい。ほかの 5 p 値が各 Holm 閾値を十分下回り、第 6 セルの `p` が `1−T(q)<p<0.025` なら、Holm は全セルを棄却する一方、第 6 セルは `T<q` なので `a11` 区間が 0 を含む。

逆方向が実際の `J=4..13` で排除されるかについても、草案には `1−T(q)≤0.025/6` の証明がない。少なくとも両手続きが常に整合するという契約は存在しない。

[成果物影響]  
同じ公表行に「Holm 有意」と「同時区間は 0 を含む」が並び、材料レポートがどちらを有意性の権威とするか一意でなくなる。certified 選択は primary `C_w` のままだが、公表表の有意セル集合と説明文が食い違う。

[最小の直し方]  
公表区間を Holm 手続きの反転として定義するか、両者を明確に別ラベルにして「区間と Holm 判定は一致を要求しない」「有意セルは Holm 列だけで決める」と固定する。前者が推奨。

## 4. `[nit]` `alpha_pub` から primary `q` への直接経路は見つからないが、主張の射程が広すぎる

[判定]  
現在の文面上、`alpha_pub_k` を `q(J,α_k)` の入力にする直接経路はない。この点の狭い主張は成立する。  
ただし追補 B 自身が「公表区間にどの `q` を使うか」を規定しており、「`q` に一切触れない」という説明は不正確である。

[根拠: `docs/decisions.md:11007-11010`]  
> 追補 B は […] `q` に影響する量を一切持たない

[根拠: `addendum-b.md:136-138`]  
> 同時区間は […] `C_w(q(J, α₁))` をそのまま用いる  
> `alpha_pub_1` を `q` へ入れる経路は存在しない

[根拠: `addendum-b.md:146-147`]  
> `alpha_pub_k` は […] primary 系列の […] 入力として使用してはならない

[成果物影響]  
現 study の certified 選択値は変わらない。ただし将来 ordinal で primary と publication の schedule が異なる場合、consumer が同名の alpha を alias すると primary の受理集合を誤って変えうる。

[最小の直し方]  
`affects_q: false` を `affects_primary_q: false` に狭め、`alpha_primary_k` と `alpha_pub_k` は数値が一致しても別 namespace・別入力であることを明記する。

## 5. `[must-fix]` `b01=1` と無限 schedule は矛盾しないが、「引き上げ」の版管理が未定義

[判定]  
exact-key は field 名の閉集合であり、`b02` の domain が無限であること自体は `b01=1` と矛盾しない。現在は ordinal 2 以降を admission deny し、schedule の tail を予約しているだけである。  
問題は、発効済みの `b01=1` をどの正規手続きで引き上げるかが書かれていないことにある。

[根拠: `addendum-b.md:65-78`]  
> `candidate_cap: 1`  
> `admissible_ordinals: [1]`  
> ordinal `2` 以降を投入してはならない

[根拠: `addendum-b.md:90-94`]  
> 上限の引き上げはユーザー裁定によってのみ可能  
> 上限を超える ordinal の投入要求は […] admission deny

[根拠: `addendum-b.md:99-102`]  
> `domain: k = 1, 2, 3, …`

ユーザー裁定だけで既存の凍結 blob を上書きするのか、新 study・新 addendum を作るのか、resolver がどの blob を effective とするのかが閉じていない。

[成果物影響]  
ordinal 2 の投入について、実装により「永久 deny」「既存追補を書換え」「新追補を採用」が分岐する。試行台帳の受理集合、参照する addendum digest、publication ordinal が一意でなくなる。

[最小の直し方]  
`b01=1` はこの addendum では不変とする。引き上げ時は、同じ `publication_family_root` と `b02` schedule を継承する新 study・新 addendum をデータ投入前に承認し、旧 blob と結果を不変に保つ、と版選択規則まで定める。

## 6. `[must-fix]` pilot 非依存は文面・通常の commit 時刻だけでは検証できない

[判定]  
草案の自己評価どおり、文面だけでは検証不能である。fold commit と pilot 投入時刻の比較も、双方に信頼できる外部時刻と pilot 投入の完全捕捉がなければ証明力を持たない。ordinal の予約 commit だけでは、追補 B の承認 blob が pilot 前に固定されたことも証明しない。

[根拠: `addendum-b.md:242-244`]  
> 本書の文面からは検証できない。  
> fold commit と pilot 1 本目の投入時刻の前後関係、および公表側 ordinal の予約 commit によって行う。

[根拠: `package.md:25`]  
> pilot の結果は 1 点も使っていない。

[根拠: `preregistration.md:433-436`]  
> 台帳の外で走らせた投入は見えない。  
> 外部の時刻根拠なしには検出できない。

[成果物影響]  
前後関係を証明できなければ、pilot 非依存を要件とする preregistration binding を認証できず、試行台帳の pilot/main entry、材料レポートの事前登録参照、最終 certified 結果の受理可否が変わる。

[最小の直し方]  
package の断定を「未検証の設計意図」に下げる。受理条件として、信頼された canonical fold 時刻、scheduler の外部 submission receipt、pilot 台帳の完全性証拠、公表予約 entry が承認済み addendum B の commit/path/digest を束縛することを要求する。

## 7. `[must-fix]` 26 割当ての内訳が発効済み追補 A と一致しない

[判定]  
総数 26 は一致するが単位の内訳が誤っている。package と草案は「本走予備 3」とし、検証割当て 1 を落としている。追補 A は「検証 1・本走予備 2」と固定している。

[根拠: `package.md:29-30`; `addendum-b.md:85-86`]  
> pilot 8 + 予備 2 + 本走 13 + 予備 3

[根拠: `addendum-a-reissue.md:611-619`]  
> 検証割当て […] 1  
> pilot […] 8  
> pilot […] 予備 2  
> 本走 […] 13  
> 本走 […] 予備 2  
> 合計 26

[成果物影響]  
このまま producer が package を実装根拠にすると、必須の検証割当てを落とすか、本走予備を 3 本受理して追補 A の試行台帳閉集合を破る。`b01=1` の根拠説明も誤った内訳を引用する。

[最小の直し方]  
`addendum-b.md` と `package.md` の双方を、`検証1 + pilot8 + pilot予備2 + 本走13 + 本走予備2 = 26` に訂正する。

## 8. `[must-fix]` `package.md` は現状の選択肢では第三者が安全に裁定できない

[判定]  
文章自体は概ね平易だが、B2/B3 の推奨が「t p 値は妥当」「planning の `T_k` は公表へ流用可能」という未証明の前提に依存している。全体を承認保留または棄却する選択肢も明示されていない。  
B6(a) の「producer 実装 wave で集約」も、実装 wave に推論規則の権威を与えるのか、単なる非権威の索引なのか不明である。

[根拠: `package.md:60-68`]  
> `0.05 / (k(k+1))` を採り […] 推奨  
> 上限を上げても誤り率は壊れない

[根拠: `package.md:84-92`]  
> 既存契約の参照と読む (推奨)  
> (a) なら公表表の p 値・区間・有意判定が一意に決まる

[根拠: `package.md:123-134`]  
> どれ 1 つも「公表手続きの正本」ではない  
> producer 実装 wave が […] 1 本へ集約する (推奨)

[成果物影響]  
ユーザーが推奨どおり承認すると、妥当性と権威が閉じていない p 値・区間・有意判定を公表表へ載せることになる。材料レポートと試行台帳の参照先が非一意になる。

[最小の直し方]  
全体選択肢に「承認保留／NO-GO：weak-null 公表手続きと権威文書を新 core で凍結する」を追加する。B2 は「schedule の算術」と「候補内検定の妥当性」を分離し、B3 は「identity/T の式は存在するが、公表への流用は未承認」と書き直す。

## 総括

blocker 件数: **2 件**

最も重い 1 件: **weak mean null・非正規 cluster のもとで t p 値が超一様でなく、`b02` の FWER 主張が反例で破れること。**

GO / NO-GO: **NO-GO — 現状の追補 B を承認・発効させてはならない。**

実走・build・テストは行っていない。read-only sandbox で指定文書を静的読解しただけであり、pytest 緑は主張しない。