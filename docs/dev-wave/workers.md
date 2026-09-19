# dev-wave worker 契約

plan、敵対相談、実装、レビュー・fix worker の正本。入口が指定する leaf 節を worker 起動前に読む。

## DW-S02 — 段 2 プラン起草

brief と関連コードの所在を渡し、codex `reasoning=medium`、`sandbox=read-only` で
file:line 粒度の plan を起草させる。

## DW-S03 — 段 3 敵対相談

codex `reasoning=medium`、`sandbox=read-only` で異なるレンズへ並列起動し、プランを守らせず検査させる。
正しさ境界・整合・実効性と過剰・削除（研究前進・実測欠陥への対応、削除・局所修正の可否）に分け、
親 brief 自身も検査対象だと明記する。brief の file:line、前提、
所有範囲、変異の帰属不成立、**親自身の実測値とその一般化**を探させる。
gate・検査を新設する wave では成果物が実際に効く全層が scope に入るかを必ずレンズに入れ、
scope 外の層を実装したふりにせず裁定パッケージ候補として返させる。

## DW-S05-A — 段 5 所有と投入

所有path素集合の単位ごとに別worktree。作成時job dirのmanifest(形式はtool冒頭、所有pathはrename両端込み)へ登録してから起動、fixは同木でbranchを切り再登録。依存完了後、所有path限定patch
（`git add -A`→`git diff --cached <base> --output=<f> -- <所有パス>`→`git apply`、`<base>`=子作成SHA。隔離sessionは`git -C`不可）だけ展開し並列投入。
worktreeは`-b`必須(detachedはmidflight rc=1)。
投入直前にcdせず`tools/check_wave_startup.py --repo <abs> --mode midflight`。rc≠0で停止。
乖離量は非関門。gate実測NOTE≠0ならanchor再読。
起動器はauthor/fixの全残差を終端commit、待ち手は`--commit-worktree <abs>`指定。記録のみ(D2044項16)。
codex は `reasoning=medium`、`sandbox=workspace-write` とする。

## DW-S05-B — 段 5 権限と赤

権限は入口の凍結境界に従う。親・他単位の成果物の land まで意図的に赤になるテストを
xfail 化せず、既存テストの期待値も変えない。赤の内訳を報告に明記する。

## DW-S05-C — 段 5 実装子の検査・報告

実装子のpromptに次を全部入れる。

- 緑には実走nodeid・範囲を併記。子の実走は親の全走を代替せず、実走不能なら`closed`でなく「実装済み・未実走」と書く。
- テスト新設・改名は親の名指しを網羅と見なさず、制約meta-testを自ら洗い出し走らせる（F42）。
- fixtureへの現行hash差し込み等、テストを甘くして緑にしない（F27）。
  機構の正例・負例は実体を名指しし依存先をstubしない（F649）。
- 期待値へ揮発payload(tree hash等)を焼き込まず、理由と件数を固定して揮発部分を外し、揮発源を編集しても緑か確認する。
- 報告に所有外caller・共有fixture・consumer testへの波及を静的列挙。
- 指示外の受理集合変更をせず、scope前に現行の受理・拒否挙動を明記。
- 親docs未landなら期待赤のfinding集合を事前指定し、他は回帰と報告する。

## DW-S06-A — 段 6 敵対レビュー

実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。
1 本は `DW-S03` の過剰・削除レンズに固定する。
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。

## DW-S06-B — 段 6 fix の分割と継承

real所見へfixを投じる前に統合snapshot patchを退避する。所見を編集対象file集合で分け、
所有が素集合なら`DW-S05-A`と同じworktree・所有・限定patch契約で並列投入する。
一枚岩なら理由1行をhandoffへ。横断所見も一つのCodex単位へ寄せ、親が直接直さない。
実装子契約の継承では段4の規模上限も省略せず、超過は所見が閉じても差し戻す。
fixのpromptに**既存テストの期待値を変更しない**を明記する。反転・緩和・skip・削除を禁じ、赤なら実装側が誤りとする。期待値が誤りなら実装を変えず報告して止める。

## DW-S06-C — 段 6 統合後の再検証

並列 fix の統合後、焦点再レビューは全体へ `reasoning=medium` で 1 本でよい。
親が変異 matrix と受入を再走する。
成立した条件の operations と `DW-G05` を適用する。
