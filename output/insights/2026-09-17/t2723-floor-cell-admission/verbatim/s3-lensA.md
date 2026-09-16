## 受理集合の差分

以下、`A`＝`orchestrator/campaign/p3_b4_admission_record.py`、`F`＝`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`、`M`＝`orchestrator/campaign/p3_b4_material_report.py`、`TA`＝`orchestrator/tests/test_p3_b4_admission_record.py`、`P`＝指定の `s2-plan.md`、`B`＝指定の `s1-brief.md` とする。pin の受理例は、参照先 artifact 自体が既存 loader の検証を通ることを前提とする。

**所見**: normalized sentinel 比較は strip 以外にも受理集合を広げ、`未記⼊`（末尾 U+2F0A）を拒否から `None` へ変える。
**分類**: real
**根拠**: F:1503 は raw の `"未記入"` と比較するが、P:125–132 の案は normalized 値と比較する；A:541 は `unicodedata.normalize("NFKC", value)` であり、読取専用の文字列確認でも `NFKC("未記⼊") == "未記入"` を確認した。
**影響**: 従来 grammar error で生成停止した文書から、floor absent の材料レポートが生成可能になり、B:26 の「stripだけ」という規律2の前提に反する。
**推奨**: plan v2 では追加緩和を明記して裁定対象にするか、strip済みrawで sentinel を比較して既承認のstripだけに限定する。

**所見**: §5外の同prefix行の無視も、stripとは独立した「拒否→受理」である。
**分類**: real
**根拠**: F:1472–1476 は文書全体で `len(matches) != 1` を拒否する一方、P:210–223 は§5外・fence内・HTML comment内の複製を無視する；P:323 自身も「§5外の重複行を無視」と記す。
**影響**: 完全な§5のfloorがsentinelなら「拒否→None」、有効pinなら「拒否→pin」となり、外側の複製が不正終端・不正値でも同じである。
**推奨**: 要求された境界修正としてこの拡大を明示し、規律2を「全体集合の単調縮小」ではなく、承認する差分を列挙した契約へ訂正する。

**所見**: 「受理→拒否」は§5外の行と責任者欠落だけでなく、共有parserの全条件によって発生する。
**分類**: real
**根拠**: A:625–666 は見出し一意性・順序、区間内block除外、12非空行、exact header、各行の両端 `|`、2セル、正規化後label重複・集合を検査し、A:538–543 は全label／valueの不可視文字を拒否する。
**影響**: 旧経路がNone／pinを返した「見出し欠落・重複・逆順」「9行表／余計な説明行」「header変更」「他行の終端破損／余分な `|`」「未知・重複label」「他セルのU+200B」「責任者空値・予約sentinel」が、新経路ではrow errorになる。
**推奨**: この条件群を縮小差分として列挙する；規律2を緩める変更ではないが、既存入力の互換性変更として省略しない。

**所見**: path中のASCII `|` と、Markdown context検査による追加拒否も差分一覧から漏れている。
**分類**: real
**根拠**: F:82–84 のpathは `[^;]+`、F:331–338 は `|` を禁止しないが、A:655–657 は `split("|")` 後の2セルを要求する；A:610–615 はliteral comment openerの過剰拒否を宣言する。
**影響**: 有効な `artifact_path=artifacts/a|b.json; sha256=…`、fence／comment内にしかfloor行がない文書、§5前の未閉鎖literal `<!--` を持つ文書は、旧pin受理から新拒否へ変わる。
**推奨**: path文字制約の縮小と既知の過剰拒否の継承をplan v2へ追記する；規律2の緩和には該当しない。

**所見**: stripの差分はsentinelだけでなくpinにも及ぶが、両版で正常終了する同一入力について `None↔pin` や参照先変更は生じない。
**分類**: real
**根拠**: F:1481 は値をそのまま返し、A:658 は `cell.strip()` を行う；P:112 のexact floor label条件により、新版が選ぶ行は旧版のprefix候補でもある。
**影響**: ` 未記入 ` は拒否→None、` artifact_path=a.json; sha256=… ` は拒否→pinとなるが、`artifact_path= a.json; sha256=…` のpath先頭空白や `a.json ;` の末尾空白は保存され、既存の参照先は変わらない。
**推奨**: Unicode外周空白も含むstripの適用範囲と「両版成功時は同じ値・参照」を明記する；行頭空白や終端 `|` の後の空白は引き続き拒否と記す。

**所見**: 「P5だけで旧floor resolverの受理集合が広がる」という疑いは成立しない。
**分類**: refuted
**根拠**: F:1497 のstrict UTF-8もBOMを正常decodeし、旧走査は後続floor行を発見する；新版で有効なfloor行は§5見出しとheaderより後なので、文書先頭BOMがそのprefixを妨げることはない（P:162）。
**影響**: BOM付き完全表は旧版でも受理可能であり、P5単独の拒否→受理はない；BOMを隠れ蓑にした先頭fence等は新版で追加拒否されうる。
**推奨**: P5を独立した緩和と報告しない；「BOMなしdecodeを使う新parser」との比較と、旧resolverとの比較を区別する。

## F423 型 decoy

**所見**: 真正§5の見出しが保たれている限り、floor行だけを壊して§5外のcanonical行で補う攻撃は閉じる。
**分類**: refuted
**根拠**: A:645–666 は選択区間内だけで固定表を構成し、行欠落・未知label・重複を拒否する；P:112 はfloor labelの元表記一致も要求する。
**影響**: floor labelの外周空白・全角化・U+200B・非NFKC-foldable homoglyphによる破損を、§5外の単独行で救済してpinを採ることはできない。
**推奨**: この限定された攻撃について変更不要；「F423全般を閉じる」と一般化しない。

**所見**: 本物の両見出しを軽微に壊して別所に完全なcanonical §5を置くF423型は残る。
**分類**: real
**根拠**: A:630、637 はraw見出しのexact正規表現だけを文書全体で探索する；例えば本物の `## 5.`／`### 5.1` を全角数字またはゼロ幅文字付きにし、別所へ正常な見出し・完全表を置けば、探索対象は複製だけになる。
**影響**: 本物の見た目の表が未充足でも、別所の完全表のpinが材料レポートのfloor出所になる；セル内の不可視文字拒否は未選択区間に及ばない。
**推奨**: plan v2に見出し探索の残存限界を明記する；全面的な対策は今回のmust-fixへ混ぜず裁定パッケージへ分離する。

**所見**: fence／comment／インデントの扱いは一律の「Markdown上の本物判定」ではない。
**分類**: real
**根拠**: A:547–599 はfenceとHTML commentだけを追跡し、A:630、637 は行頭からの見出し一致を要求する；TA:747 は4空白付き開始見出しを拒否し、TA:811–829 はliteral `<!--` の過剰拒否を固定する。
**影響**: 通常のfence／comment内複製は無視され、4空白・tab付き偽見出しも一致しない一方、raw HTML blockは非保証で、literal comment openerによる正常floorの拒否も継承される。
**推奨**: 除外できる構文と非保証を区別して記載する；なお過剰拒否のdocstringは `_markdown_block_context` 自身ではなくA:31–36、610–615にある。

## 責任者行の述語

**所見**: P3の切り出しは指定5例で同一受理集合を保ち、「責任者指名の意味検証」にはならない。
**分類**: refuted
**根拠**: A:668–686 とP:42の「`continue`だけを`return`へ置換」に従えば、①`実行責任者 = alice、開始時刻 = 2026-09-17T10:00+09:00`＝両方受理、②両値未記入＝両方拒否、③`hello`＝両方受理、④label欠落＝両方parser拒否、⑤空値＝両方述語拒否となる。
**影響**: `hello`でもfloorの権威化は可能だが、新たな述語緩和ではなくD2079決定2が維持した非保証である；比較は他セルの条件を揃えた責任者述語について成立する。
**推奨**: P3の実装変更は不要；briefの「責任者未指名を拒否」を「既存責任者セル述語に違反する場合を拒否」へ狭める。

## strip と grammar の掛け先

**所見**: NFKC済みpinをloaderへ渡すと参照先が変わるためraw保持は必要だが、sentinelのNFKC適用は別の受理変更である。
**分類**: real
**根拠**: F:331–338 の `_relative_path` はASCII限定ではなく、`artifacts/Ａ.json`、`artifacts/ﬀ.json` 等をUnicodeのまま受理しうる；NFKCはそれぞれ `A.json`、`ff.json` に変える（P:164）。
**影響**: normalized pinを渡す実装では別artifactを参照するかhash不一致で停止する；raw pinならpath内の互換文字・空白を保持し、全角hash／全角構文は従来どおり拒否される。
**推奨**: loaderにはstrip済みrawから抽出したpath/hashを渡す；sentinelについては先述の `未記⼊` 差分を独立して決着させる。

## sentinel と absence の意味

**所見**: planのdocstring更新指示は「strip後」だけでは不足し、実装案のNFKCと事前の責任者検査を表現できていない。
**分類**: real
**根拠**: P:166 は「strip後のsentinel」とするが、P:125–132 はnormalized比較、P:151 は責任者検査をNone返却より先に置く；A:681–686 はadmissionにおける `未記入` を拒否する。
**影響**: 同じ `未記入` でも完全admissionでは未充足、floor resolverでは条件付きabsenceとなり、責任者不正ならabsenceへfallbackせずrow errorになる。
**推奨**: docstringに正規化の実際の順序、absence返却の前提、完全admission成立を証明しないことを書く；error code写像の新設は不要。

**所見**: 他欄が未記入でもfloor pinを権威化する残存は成果物に影響するが、今回導入する緩和ではない。
**分類**: real
**根拠**: F:1503–1517 は現状でも他欄を見ずpinをloadし、P:320もこれを維持する；M:267–271 はfloorを評価器へ渡し、M:977–989 は `availability="present"` として `authoritative_floor_artifact` を非保証一覧から除く。
**影響**: 他欄未記入のまま有効pinを置くと旧版・新版ともfloor欄はpresentになり、`p3_b4_analysis_path.py:349–352` のfloor欠如によるinvalidを回避するが、それだけでcertifiedは保証されない。
**推奨**: scope外の既存残存として明記し、「事前登録の発効条件へ完全接続した」という完了主張を避ける；他欄検査の追加は今回のmust-fixにしない。

## 変異 matrix の帰属

**所見**: 「境界検査を外す変異は新規負例(i)以外では殺されない」という帰属は成立しない。
**分類**: real
**根拠**: P:251のM1は旧全文prefix走査への復帰であり、P:223のblocked decoy入力にも真正floor行と複製floor行の2本があるため、F:1473の `exact 1` 違反で同nodeも赤になる。
**影響**: M1は指定の `test_resolver_ignores_pin_outside_section5` で殺せるが、専属killerではなく、境界検査だけの独立した欠落とも同義でない。
**推奨**: M1の置換範囲を具体化し、主killerと追加killerを分けて登録する；他nodeが殺すことをSURVIVEDと扱わず、専属性不成立として記録する。

**所見**: M0〜M9の机上判定では機能変異のSURVIVEDは見つからないが、未作成のテストとpatchに対する予測である。
**分類**: plausible
**根拠**: P:250–259の指定nodeに対し、M0＝機能上SURVIVED、M1＝外側複製で件数エラー、M2＝責任者拒否消失、M3＝未知の無関係labelが通過、M4＝padded sentinel拒否、M5＝TA:672–677のNBSP expectationが通過、M6/M7＝偽見出しが探索対象となり一意性違反、M8＝全角pathの参照変更、M9＝非exact floor label通過、となる。
**影響**: M1〜M9はいずれも指定nodeが赤になる設計だが、M5はraw pinテスト、M6/M7は既存admissionのblockテストもkillerになりうる；実行順による「最初」は未確定である。
**推奨**: nodeを個別に実行したassertion失敗を帰属根拠にする；M2はloader未呼出しも必ず観測し、missing artifactによる別エラーを責任者検査の成功証拠にしない。

## 親 brief 自身の点検

**所見**: 「floor含む6欄が未記入」とP4の検索結果には、確認した範囲で反証はない。
**分類**: refuted
**根拠**: 実文書 `docs/phase3-b4-reflux-ablation-preregistration.md:159,162–166` の6値セルがexact `未記入`、167の責任者行は部分文字列として含む；B:21／P:309–311に対し、読取専用の `sha256sum` と `git grep -F` は3moduleとも一致0件、`git ls-files` とファイル列挙も対象record0件だった。
**影響**: 現行tracked登録対象についてpin更新・record再発行対象は見つからないが、履歴や外部成果物まで不存在とは言えない。
**推奨**: 「6欄」はexact値セル数と明記し、P4の結論を現行tracked対象へ限定する；検索値はadmission=`9e32cd6f…`、issuer=`6e9a08c4…`、report=`4a1b0e26…`として再現可能に残す。

**所見**: briefの「縮小＋stripだけ」は誤りで、planの「strip以外の緩和を防ぐ」という補正文にも同じ誤りが残る。
**分類**: real
**根拠**: B:26とP:323に対し、外側重複の無視と `未記⼊` のNFKC sentinel受理が反例になる；B:22のP5はdecode方針だけを記し拡大とは書かないが、P5単独の拡大自体が前述のとおり反証される。
**影響**: 差分を縮小と誤記したまま規律2適合を宣言すると、正常化によって新たにabsenceへ落ちる入力の審査が抜ける。
**推奨**: briefとplanの両方を同じ差分一覧で修正し、BOMを誤って追加緩和に数えず、実在する2系統の拡大を記載する。

## 裁定パッケージ候補

**所見**: 見出しdecoyの残存と、完全admission未成立でもfloorを権威化する既存仕様は、今回の述語切り出しとは別の裁定対象である。
**分類**: real
**根拠**: A:625–639の見出し探索は文書全体のraw一致、P:320は他欄sentinelとexpectationを検査しないと明記し、指定 `rulings-verbatim.md` のF423「既知の残存」とD2079決定2は保証の限界を区別している。
**影響**: 別所のcanonical完全表や他欄未充足の文書でもfloorがpresentになる余地は残り、今回の完了だけでは事前登録全体の発効を証明できない。
**推奨**: 必要なら「真正§5の同定保証」と「floor権威化に要求する発効条件」を別裁定として扱う；新しいgate・他欄sentinel検査・一般validatorを本waveへ追加しない。

## 総括

**所見**: plan v2のmust-fixは、NFKC sentinel拡大の決着、受理集合の差分記述、F423残存の明示、M1の帰属修正である。
**分類**: real
**根拠**: F:1470–1517とA:538–701の静的照合により、P:323の一般化を反証し、P3の指定5例の同一性とP5単独拡大の不成立を確認した。
**影響**: 現案を無修正で実装すると、`未記⼊` が生成停止からfloor absentへ変わる追加緩和を、規律2適合の説明から落としたまま導入する。
**推奨**: 上記を修正してauthorへ渡す；ファイル変更・pytest・変異実走は行っておらず、KILLED／テスト緑の実測結果は報告しない。
