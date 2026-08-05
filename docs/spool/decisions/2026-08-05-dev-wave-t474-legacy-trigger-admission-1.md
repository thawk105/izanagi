---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t474-legacy-trigger-admission
seq: 1
---

## {{D:legacy-trigger-raw-view-denial}}. 歴史枝の trigger 系 campaign へ raw admitted view を発行しない — D160 決定 5 の遡及結果だけを後発裁定で限定 supersede し、既存の凍結派生は grandfather する

**決定 (D96 手続。境界テストと同一変更単位):** admission validator の歴史枝
(`historical-pre-admission-schema` = pre-policy かつ Git snapshot 三点照合を通った artifact) に
おいて、`campaign.lock` の `search_config.axis` が trigger 軸であれば `admission_status` を
`legacy-unclassified` とし、raw view を発行しない。適用面は次のとおり。

1. **判定は軸だけで行う。** 機械 sweep 形状 (generator / space の連言) で限定しない。
   未知形の歴史 trigger artifact も fail-closed 側へ倒す。判定は純関数として切り出し、
   合成 lock の真理値表で固定する — 実 artifact だけを見るテストは、判定を広げる変異も
   狭める変異も corpus に反例が無い限り検出できないためである。
2. **適用範囲は歴史枝に限る。** post-policy の分類・binding 要求・overlay 台帳の 3 件・
   非 trigger の歴史 campaign はいずれも不変とし、過剰拒否を検出する正例で固定する。
3. **既存の exact-hash 凍結派生は grandfather する。** 凍結台帳が当該 campaign の付随レポートを
   admission gate を通さず直接読む経路は、そのまま権威として残す。凍結 bytes を再発行しない。
   本決定が拒否するのは新しい raw view の発行と、そこから新規に材料レポートを起こすことだけである。
4. **lock の権威となる読み取りを一回にする。** hash・parse・分類・snapshot 照合・receipt を
   すべて同一 bytes に由来させる。従来は hash の後に読み直していたため、A→B→A の書き換えで
   「hash は A・分類は B」の decision を合成できた。本決定が足す判定はその parse 済み lock を
   読むため、閉じずに置くと新しい gate 自身の回避路になる。
   **終端では live の lock / WAL hash を拒否専用に再照合する**。再照合で読んだ bytes は
   分類にも receipt にも使わない。これは物理的な一回読みではなく、権威の一意化である。
5. **supersede の範囲を逐語で限定する。** 置換するのは D160 決定 5 のうち
   「機械 sweep 6 件は proposal 経路を持たないため遡及被害ゼロを実測した」という
   raw admission の結果だけである。D160 が却下した「全 trigger campaign への binding 遡及要求」は
   **却下のまま維持する** — 本決定は旧 artifact へ binding/v1 の遡及証拠を要求せず、
   歴史枝の status だけで拒否する。D160 決定 1〜4、post-policy の marker/binding 規則、
   「将来発見される正当な pre-cutover artifact は exact hash の個別 grandfather 登録だけを許す」
   規則、既存凍結 bytes はいずれも置換しない。

**理由:**
- 後発のユーザー裁定 (2026-08-05) が、旧 trigger artifact に admitted view を名乗らせない
  縮小版再検査を選んでいる。D160 は前日の判断であり、後発裁定が結果を上書きする。
- 歴史枝は trigger 束縛検証を一切通らない。分類値による識別自体は従来から可能だったが、
  raw view を発行する capability は `admission_status` が `legacy-unclassified` 以外であることだけで
  決まり、消費側に分類分岐を強制していなかった。つまり「binding 証明済み」と「歴史的無証明」は
  同じ型の view として渡されていた。
- 当該 artifact の付随レポートに残る述語は実測上すべて正準集合に属するが、それは
  **付随レポート文字列の membership** であって、実際に build された source の membership ではない。
  述語は WAL の source token へ束縛されておらず、歴史 evidence だけでは証明できない。
  証明できないものを「受理済み」と名乗らせないことが本決定の趣旨である。

**主張の範囲 (正直な非主張):**
(a) post-policy の機械 sweep は依然として membership 証拠なしで受理される。共有 validator は
機械 lock に対し空の束縛集合を返し、producer も汎用検疫へ membership 証明を渡さない。
この層は本決定の射程外で、別途起票する。
(b) WAL 側の同型 ABA は残る。record 読み出し API が bytes を返さないため、hash した bytes と
parse した bytes の同一性を保証できない。
(c) 付随レポートの `implementation` field は述語と説明文の双方を保持しており、二義化したまま
build された source へ束縛されていない。
(d) validator 実装の sha256 は decision receipt に載るため、本決定の実装変更により
**全 campaign の receipt で validator sha が変わる**。分類と status が変わるのは旧 trigger 6 件だけだが、
receipt の値はそうではない。持続化済み decision receipt を持つ artifact は、実測した範囲
(repo 内および `/work/1/SFC/tanab` 配下) では 0 件だった。他 filesystem の run-root は未探索であり、
そこに旧 validator sha の材料レポートが存在すれば、campaign bytes が不変でも完全一致照合で
落ちる。棚卸しの範囲と結果をこのとおり限定して記録する。

**却下した選択肢:**
- **証拠 field を足し、受理集合を変えずに掲載だけ義務付ける** — raw view を発行し続けるため
  「admitted view を名乗らせない」を満たさない。field は admission の capability へ結線されず、
  raw consumer の大半はそれを読まずに commit だけで材料を作るため、掲載は gate にならない。加えて decision と材料レポートの
  schema version を同一のまま必須 field を足すことになり、persisted contract の in-place 変更になる。
- **機械 sweep 形状の連言で拒否対象を限定する** — 未知形の歴史 trigger を受理側に残し、
  かつ実 artifact だけのテストでは判定条件への帰属が成立しない。
- **再検査台帳を新設する** — Git snapshot の path / lock / WAL 三点照合が既に exact な台帳として
  機能しており、二重の権威を作る。
- **拒否を post-policy まで広げる** — 本裁定の射程を超え、既存の受理集合を追加で縮小する。
