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

編集 path 所有が素集合の単位に分け各単位を別 worktree へ置く。依存先を完了させ、所有 path 限定 patch
（`git add -A`→`git diff --cached --output=<f> -- <所有パス>`→`git apply`。隔離 session は `git -C` 不可）だけ展開し並列投入。
投入先 root へ cd せず直前に `tools/check_wave_startup.py --repo <abs> --mode midflight`。rc 非 0 で停止。
乖離量は非関門。fail-open の INFO でなく gate 実測値の NOTE が非 0 なら anchor を読み直す。
codex は `reasoning=medium`、`sandbox=workspace-write` とする。

## DW-S05-B — 段 5 権限と赤

権限は入口の凍結境界に従う。親・他単位の成果物が land するまで意図的に赤になるテストを
xfail 化せず、既存テストの期待値も変えない。赤の内訳を完了報告に明記する。

## DW-S05-C — 段 5 実装子の検査・報告

実装子の prompt に次をすべて入れる。

- 緑には実走 nodeid・範囲を併記する。子の実走は親の全走を代替せず、実走不能な子は
  `closed` と申告せず「実装済み・未実走」と書く。
- テスト新設・改名の単位は、親の名指しを網羅と見なさず制約 meta-test を自ら洗い出して走らせる（F42）。
- fixture への現行 hash 差し込みなど、テストを甘くして緑にしない（F27）。
  機構の正例・負例は実体を名指しし依存先を stub しない（F649）。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。理由と件数を固定して揮発部分を
  外し、揮発源を編集しても緑か確認する。
- 完了報告に所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。
- 指示外の受理集合変更をせず、scope 前に現行の受理・拒否挙動を明記する。
- 親 docs が未 land なら期待赤の finding 集合を事前指定し、他は回帰として報告する。

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
射程は main 既存分に限ると書く。

## DW-S06-C — 段 6 統合後の再検証

並列 fix の統合後、焦点再レビューは全体へ `reasoning=medium` で 1 本でよい。
親が変異 matrix と受入を再走する。
成立した条件の operations と `DW-G05` を適用し、成果物影響を書けない所見を must-fix にしない。
