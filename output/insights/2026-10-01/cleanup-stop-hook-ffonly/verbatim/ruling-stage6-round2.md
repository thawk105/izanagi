# 段 6 裁定 (2 巡目) — 焦点再レビュー C の所見

再レビュー C の対応表: A-2・A-3・B-2・B-4 closed、A-1・A-4・B-1 partial (C-1〜C-3 による)、B-3 nit 見送り。件数の検算 (統合 hook +31/−4、
test +220/−0、cleanup_stop 21 関数 28 ケース、settings_json 2、焦点走 30 passed = 28 + 2) は親・子の記載と一致。

DW-O16 に従い、NO-GO が続く所見へは fix を重ねず (fix は 1 巡)、親が変異で裏取りして閉じる。判断の軸は D2314 項 4
(この hook は注意喚起で正しさ防壁ではなく、AI が書き換えても防壁は弱まらない) と hooks/README.md hook 5 の既知の限界
(「reflog が期限切れ・`branch -f` 済みなら作成点を誤りうる」= 旧 hook も git の記録の改変には元々負ける)、DW-G05 (要求外の仮想リスクに防壁を足さない)。

| 所見 | 裁定 | 理由 |
|---|---|---|
| C-1 main を C から B へ巻き戻し、tag `main` を C に置いて wave が ff、後で land すると、main reflog の古い C@100 で免除 | real (構成は正しい)・scope 外 | main の巻き戻しと branch と同名の tag の作成という 2 つの git の記録の改変が要る。dev-wave の通常操作には現れない (repo に tag main は無い、実測)。既知の限界として記録 |
| C-2 `GIT_COMMITTER_DATE` で reflog の記録時刻を操作順と逆にすると、land 済みの見逃しと ff だけの木の誤 block の両方が起きる | real・scope 外 | 記録時刻の改変が要る。通常運用では操作順と記録時刻は一致する。誤 block 側は旧来の誤検出に戻るだけ |
| C-3 `GIT_REFLOG_ACTION=branch` で作成項に見せかけた commit を作り、本物の作成項を消すと免除 | real・scope 外 | reflog action の偽装と reflog 項の削除の 2 つが要る。旧 hook も reflog 項の削除で同様に騙せる (README の既知の限界) |
| C-4 main の reflog が期限切れ・部分失効だと、ff だけの木の誤 block が残る | real・scope 外 (安全側) | 旧来の誤検出に戻るだけで、land 済みの木の促しは消えない。この repo の main は日々進み、ff 先の tip の reflog 項は新しい |
| C-5 main reflog の読み取りが時間切れになると、祖先判定の予算が無くなり fail-open で通る | real (経路は存在)・不採用 | この経路に入るのは作成後の全項が `merge main: Fast-forward` の木だけで、記録の改変が無ければ自分の commit を持たない木なので、通すのが正しい答え。main reflog 3,732 項の読み取りは 0.15 秒 (1 点の実測、巨大化の保証ではない) |
| C 付記: 段 5 の ff helper は実時計・継承環境 (GIT_REFLOG_ACTION) に依存 | nit・不採用 | 受入の実行環境はこの変数を設定しない |

## 残る既知の限界 (insight・worklog・hooks/README 更新の持ち越しへ書く)
- 免除は reflog の文言・記録時刻・main の reflog の過去の出現を根拠にするので、これらを改変・偽装した木では land 済みでも通りうる
  (C-1〜C-3、A-4 の残り)。改変が無い通常運用では、免除される木は自分の commit を持たない。
- main の reflog が失効していると、ff だけの木で従来の誤検出が残る (C-4)。
- 直したのは DW-O20 の `merge --ff-only main` (と `refs/heads/main`) による誤検出だけ。sha 指定の ff・`pull --ff-only`・`reset --hard main`・
  `-m` 付きの ff は従来どおり促しが出る。

## 変異
段 4 と段 6 (1 巡目) で登録した M0〜M10 に、F4 の層が M3・M4 を覆う可能性があるので単独 (m3-alone・m4-alone) と両層 (m3m9・m4m9) の
両方を probe へ入れ、観測で kill 期待を確定する (DW-M01・DW-M02)。
