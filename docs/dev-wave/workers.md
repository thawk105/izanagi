# dev-wave worker 契約

plan、敵対相談、実装、レビュー・fix worker の正本。入口が指定する leaf 節を worker 起動前に読む。

## DW-S02 — 段 2 プラン起草

brief と関連コードの所在を渡し、codex `reasoning=medium`、`sandbox=read-only` で
file:line 粒度の plan を起草させる。

## DW-S03 — 段 3 敵対相談

codex `reasoning=medium`、`sandbox=read-only` で異なるレンズへ並列起動し、プランを守らせず検査させる。
正しさ境界と整合・実効性を分け、親 brief 自身も検査対象だと明記する。brief の file:line、前提、
所有範囲、変異の帰属不成立、**親自身の実測値とその一般化**を探させる。
gate・検査を新設する wave では成果物が実際に効く全層が scope に入るかを必ずレンズに入れ、
scope 外の層を実装したふりにせず裁定パッケージ候補として返させる。

## DW-S05-A — 段 5 所有と投入

所有 path が素集合の単位ごとに別 worktree。依存完了後、所有 path 限定 patch
（`git add -A`→`git diff --cached <base> --output=<f> -- <所有パス>`→`git apply`、`<base>`=子作成 SHA。隔離 session は `git -C` 不可）だけ展開し並列投入。
worktree は`-b`必須(detachedは midflight rc=1)。
投入先へ cd せず直前に `tools/check_wave_startup.py --repo <abs> --mode midflight`。rc≠0 で停止。
乖離量は非関門。gate 実測 NOTE≠0 なら anchor 再読。
起動器は author/fix の投入先全残差を終端 commit、待ち手は呼出側指定 `--commit-worktree <abs>`。記録のみ (D2044 項 16)。
codex は `reasoning=medium`、`sandbox=workspace-write` とする。

## DW-S05-B — 段 5 権限と赤

権限は入口の凍結境界に従う。親・他単位の成果物の land まで意図的に赤になるテストを
xfail 化せず、既存テストの期待値も変えない。赤の内訳を報告に明記する。

## DW-S05-C — 段 5 実装子の検査・報告

実装子の prompt に次を全部入れる。

- 緑には実走 nodeid・範囲を併記。子の実走は親の全走を代替せず、実走不能なら
  `closed` でなく「実装済み・未実走」と書く。
- テスト新設・改名は親の名指しを網羅と見なさず、制約 meta-test を自ら洗い出し走らせる（F42）。
- fixture への現行 hash 差し込み等、テストを甘くして緑にしない（F27）。
  機構の正例・負例は実体を名指しし依存先を stub しない（F649）。
- 期待値へ揮発 payload (tree hash 等) を焼き込まず、理由と件数を固定して揮発部分を
  外し、揮発源を編集しても緑か確認する。
- 報告に所有外 caller・共有 fixture・consumer test への波及を静的列挙。
- 指示外の受理集合変更をせず、scope 前に現行の受理・拒否挙動を明記。
- 親 docs 未 land なら期待赤の finding 集合を事前指定し、他は回帰と報告する。

## DW-S06-A — 段 6 敵対レビュー

実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
所見ゼロの扱いは `DW-M02`。

## DW-S06-B — 段 6 fix の分割と継承

real 所見へ fix を投じる前に統合 snapshot patch を退避する。所見を編集対象 file 集合で分け、
所有が素集合なら `DW-S05-A` と同じ worktree・所有・限定 patch 契約で並列投入する。
一枚岩なら理由 1 行を handoff へ残す。横断所見も一つの Codex 単位へ寄せ、親が直接直さない。

実装子契約の継承では権限、reasoning/sandbox、テスト弱体化禁止、受理集合、期待赤、波及報告、段 4 の
規模上限を省略せず、超過は所見が閉じても差し戻す。

fix の prompt に**既存テストの期待値を変更しない**を明記する。反転・緩和・skip・削除を禁じ、
赤なら実装側が誤りとする。期待値が誤りなら実装を変えず報告して止める。

## DW-S06-C — 段 6 統合後の再検証

並列 fix の統合後、焦点再レビューは全体へ `reasoning=medium` で 1 本でよい。
親が変異 matrix と受入を再走する。
成立した条件の operations と `DW-G05` を適用し、成果物影響を書けない所見を must-fix にしない。
