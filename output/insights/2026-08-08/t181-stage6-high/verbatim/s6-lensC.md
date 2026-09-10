## C-01

- ID: C-01
- 主張: raw HTML block 内へ必須 H2 を移す迂回が残っており、可視化先行の目的を満たしていない。
- 根拠: [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:847) には raw HTML も除去する `_visible_dispatch_inventory_text()` がある一方、pin は `tools/check_docs.py:3399`、H2 inventory は `:3662` で fence/comment しか除去しない `_visible_markdown_text()` を使用している。`workers.md` の `DW-S06-A` 直前へ `<x>\n` の4 bytesだけを挿入した probe は、通常可視化で H2=1、dispatch 用可視化で H2=0、pin findings=`[]`、inventory findings=`[]`。さらに `_safe_read_text` をメモリ上で差し替えて production `_check_command_docs_guard()` を走らせても `PRODUCTION_RAW_HTML_FINDINGS []` だった。
- 判定: real / must-fix
- 成果物影響: rendered Markdown では存在しない `DW-S06-A` 契約を checker が受理し、段6 reviewer の reasoning 契約と dispatch 台帳が黙って蒸発できる。

## C-02

- ID: C-02
- 主張: `visible_section.count(literal) == 1` は literal の文脈を拘束せず、規範文を visible な例示・他 key の値へ置換しても通る。
- 根拠: `tools/check_docs.py:3430-3436` は節全体で値列と単純 substring 件数だけを見る。S06-A の規範文1行を `参考リンク: [例: \`reasoning=high\`](...)` または `参考値: outer=\`reasoning=high\`` に置換した production-path probe は、どちらも `_check_command_docs_guard()` findings=`[]`。regex 入力は values=`['high']`、literal_count=`1`。
- 判定: real / must-fix
- 成果物影響: `reasoning=high` を指定する命令を削除して単なる例示だけ残しても land 差分が受理され、docs drift pin が実質的に発火しない。

## C-03

- ID: C-03
- 主張: 新 regex は旧 regex が無視した無関係な URL/path/句読点境界の値を新たに effort として拾い、受理集合を縮小する。
- 根拠: `tools/check_docs.py:286-293`。canonical S06-A にそれぞれ追記した probe は次のとおり。

  - `https://e.invalid/?reasoning=日本語`: old=`['high']`、new=`['high','日本語']`
  - `/path/reasoning=/tmp`: old=`['high']`、new=`['high','/tmp']`
  - `note.reasoning=💥`: old=`['high']`、new=`['high','💥']`

  いずれも新 pin は S06-A finding を返した。前方境界は英数字・`_`・`-` しか拒まず、`.`・`/`・`?` を許す。
- 判定: real / nit
- 成果物影響: pin 自体が弱まる方向ではないが、無関係な URL/path を含む正当な reference 文書が新たに拒否される。

## C-04

- ID: C-04
- 主張: 新 regex が旧 regex の検出を完全に失い、pin が黙って通る回帰は確認できなかった。U+3000 と lazy quantifier も fail-open にはならない。
- 根拠: 行末・文書末・tab・空白・U+3000・`: / - _ .`・両引用符・裸値を旧新へ投入した。代表結果は行末/doc末/tab=`max→max`、`max-next`/`max_next` は同値、`max:next` は old=`max`, new=`max:next`、`max/next` は old=`max`, new=`max/next`、`max　次` は old=`max`, new=`max　次`。列挙した suffix 全体で `OLD_MATCH_NEW_NO_MATCH=[]`。裸値と引用値は regex が拾っても canonical backtick literal count=0 のため拒否された。正規の `` `reasoning=high`　次 `` は values=`['high']`, count=1, findings=`[]`。`+?` は次文字が終端 allowlist のときしか止まれず、`reasoning="hi"gh"` は `hi"gh` 全体となって拒否された。
- 判定: refuted / nit（修正不要）
- 成果物影響: 曖昧 suffix は値全体として拒否され、検出欠落による受理集合の拡大は観測されない。

## C-05

- ID: C-05
- 主張: fence/comment の空文字置換による節境界ずれと未閉鎖 fence は、今回確認した形では fail-closed である。既存4 reference に正当な fenced H2 もない。
- 根拠: `_visible_markdown_text()` は `tools/check_docs.py:969-1022` で不可視行を空文字へ置換し、元改行を保存する。S03 H2 を fence 内へ隠す probe では後続本文がS02へ混ざったが、S02は値重複、S03は節0件となり両 pin finding。S02後に未閉鎖 fence を置くと S03/S06-A/S06-C がすべて節0件となり3 finding。全4文書の実査では fence opener は各0件で、raw/visible H2集合は完全一致した。
- 判定: refuted / nit（修正不要）
- 成果物影響: fence/comment 経路では欠落節が受理されず、現行 reference に新しい偽赤も生じない。

## C-06

- ID: C-06
- 主張: 指定された既存 pin 挙動は保存されている。
- 根拠: current workers の pin findings=`[]`。S02をhighへ変えると既存S02 findingだけ、S03 literal削除では既存S03 findingだけが逐語で返った。S05-Aをmaxへ変えても findings=`[]`、S06-B節の抽出値は`[]`。S06-Aの comment decoy と、closing fenceを独立行にした fence decoy は values=`['high']`, findings=`[]`。
- 判定: refuted / nit（修正不要）
- 成果物影響: DW-S02/S03、S05-A、S06-B、および節内不可視 decoy の現行受理・拒否値は変わらない。

## C-07

- ID: C-07
- 主張: 追加テストは主要な finding 集合を検査しているが、実装と同じ可視性仮定を共有し、production の S06-C 被覆も不足している。
- 根拠: [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/orchestrator/tests/test_check_docs.py:5194) は S06-A max、`:5217` は hidden S06-A の production finding 集合を exact 比較する。一方、whole-section wrappers は `:5153` / `:5230` の fence/comment のみで raw HTML がない。S06-C は direct max (`:4985`) と direct hidden (`:5145`) だけで、`rg` 上 production-path test は0件。既存コードベースには raw HTML を別扱いすべきことを示す test が `:2007-2023` に既にある。
- 判定: real / must-fix
- 成果物影響: C-01 の迂回をテストが緑のまま許し、将来 S06-C だけ production 配線から脱落する回帰も検出できない。

## 総括

NO-GO。

停止点は C-01 の raw HTML H2 不可視化漏れと、C-02 の visible decoy による規範文置換である。
H2/pin の節抽出を raw HTML 対応の可視化へ揃え、両経路の production exact test が必要。
canonical literal は節内 substring ではなく、規範文または許可された行構造へ束縛すべき。
C-03 は fail-closed の過剰拒否だが、意図した受理集合か裁定を明記する必要がある。
pytest は実行していない。結論は静的実読と Python のメモリ上 probe に基づく。