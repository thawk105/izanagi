# command / skill 自己改善契約

この文書は `.claude/commands/dev-wave.md`、`.claude/commands/cleanup-branches.md`、
`.claude/commands/rulings.md` の自己改善に共通する発火 gate、routing、入口編集条件、commit 境界の正本である。
command 固有の実行手順や事故の物語はここへ置かない。

## 発火 gate

候補の記録と、本文・正本の編集を分ける。

- dev-wave は、作法の欠落・無駄・曖昧・失敗に気づいた時点で候補を記録する。
  事故や実害を伴わない手順の明確化・無駄取りも候補にできる。
- cleanup-branches は、記載と実挙動の食い違い、新しい罠、手順不足を今回の実行で実測した場合だけ、
  本文編集の gate が成立する。
- rulings は、収集漏れ、正本との食い違い、誤解を招く出力規則を今回の実行で実測した場合だけ、
  本文編集の gate が成立する。

dev-wave の候補は段 8 で一度だけ裁定する。実測のない仮想的懸念だけで failures や decisions を
変更しない。

## routing

1. 新しい失敗型・near miss・既存防壁の破れは `docs/failures.md` へ送る。
   同型再発なら新しい F を作らず、既存 F に「再発: 日付」を追記する。
2. 長期の設計、権限、正本、interface を変える採用済み判断は `docs/decisions.md` へ送る。
   未裁定または大きい変更を既成事実にせず、裁定パッケージとしてユーザーへ返す。
3. dev-wave 固有の手順は発火段に対応する `docs/dev-wave/` の既存 leaf 節へ統合し、意味を保って
   統合できない場合だけ新しい節・ファイルを候補にする。新規 L2 節の登録は鏡像の
   「発火実績あり × 義務が現に機械代替されていない × 同じ意味検索で反証も同一発火点の
   既存正本もなし」を満たす場合だけとする (D271)。L2 (条件成立時だけ読む節) の削除を裁定
   パッケージへ送れるのは「発火実績なし × テスト/機械検査で義務代替済み」の両条件を満たす
   節だけで、実施はユーザー裁定に限る。「発火実績なし」は ID 件数でなく repo 全体
   (insights・memo 含む) の意味検索で反証されないことを確認する。
4. cleanup-branches / rulings の短い手順は各 command の既存節を是正する。
   長い事故説明は F ポインタにし、裁定待ち・branch 状態・可変データを command へ書かない。
5. 同じ内容を複数の行き先へ全文複製しない。入口は命令と dispatch、reference は実行手順、
   failures は事象・原因・恒久対応、decisions は採用理由を担う。

## command 入口の編集条件

command 本文の変更を許すのは次の場合だけである。

- 実測で誤りと判明した既存命令を是正する。
- 既存命令の意味を変えず、入口内へ統合して縮約・明確化する。
- 常に読まれなければ dispatch 自体が成立しない新規命令で、既存命令にも reference にも統合できず、
  追加後も `tools/check_docs.py` の byte・最長行予算を満たす。

事故を伴わない明確化・無駄取りを入口への追記理由にしてはならず、該当 reference 節を是正する。
入口へ事故の経緯、長い例、日付付き逸話を追記しない。予算のために安全義務を削除・弱化してはならない。
予算に収まらなければ reference へ統合し、それでも意味等価にできなければ変更を止めてユーザー裁定へ返す。
予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象にする。

## command 別の終端

### dev-wave

wave 開始時に専用 handoff へ「dev-wave 改善候補」節を作る。段 7 後の段 8 で本契約を一度適用する。
自動是正できる小変更は、command 入口でなく該当 reference 節へ統合することを既定とし、
関連正本と同時に専用 commit にする。関連検査と予算検査を通した後だけ段 9 の監査済み集合へ含める。
段構成、実装子権限、正しさ防壁、裁定境界、予算の変更は実装せず裁定パッケージへ送る。
候補ゼロなら無言で段 9 へ進む。

### cleanup-branches

command と実挙動の食い違い、新しい罠、手順不足を実測した場合だけ適用する。
新しい失敗または再発は failures 台帳と同時に更新し、command / reference の是正と台帳更新を
1 commit にまとめ、worklog に残す。削除・push の権限境界は自己改善を理由に広げない。

### rulings

自己改善は現行欠落を意図的に補う能力追加である。収集漏れ、正本との食い違い、
誤解を招く出力規則を実測した場合だけ適用する。発火時点でクラス 2 に昇格し、
`CLAUDE.md` のクラス 2 起動手順を完了してから編集する。裁定待ちの実体は worklog、insights、
handoff、phase doc に残し、command や本契約を裁定台帳にしない。失敗は failures、
採用済み長期方針は decisions、既存手順の誤りは rulings の該当節へ送る。

## 検査と commit 境界

変更時は `CLAUDE.md`、`AGENTS.md`、各正本の更新契約に従い、関連テストと
`python3 tools/check_docs.py` を実行する。command と、変更理由になった failures / decisions /
reference の整合を同じ commit で保つ。AI provenance、local main、push の境界に例外を作らない。

`check_docs.py` の担保は予算と dispatch・節・孤児・逃がし・住所 (address edge) の構造 lint に限る。
whole-file SHA-256 pin も bytes 差だけを検知し、意味は敵対監査と人間レビューが担う。
