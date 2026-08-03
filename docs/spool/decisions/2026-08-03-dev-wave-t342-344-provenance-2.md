---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-t342-344-provenance
seq: 2
---

## {{D:provenance-capability}}. build provenance を source 由来 capability にし、admission を cache / replay / 選択の identity へ束縛する — 閉じていない層は security credit を与えずに列挙する

**背景:** D127 は「分類されていない source は build させない」を入れたが、決定 (4)(5) で
「検査するのは caller が自己申告した enum と bool の整合だけ」「cache と replay の class 束縛は
入れない」と限界を明記していた。同一 bytes を別 class と申告すれば certified 受理集合へ入れられ、
cache hit と WAL replay は class を跨いで過去の binary と terminal を再利用できた。
ユーザーは 3 件を**一体で**塞ぐよう裁定した。分割すると片方が迂回路になるためである。

**決定 (1): class は caller が選ぶ値でなく evidence から導出する。** 導出順序は
(a) `src_token` が stock かつ tracked-clean かつ宣言 commit が repo 正本 pin と一致、
(b) 対象 source に束縛された review receipt、(c) registered generator に束縛された generator receipt、
(d) 同一 run context の parser 発行 token、(e) 該当なしと曖昧な組は拒否、とする。
caller が class を宣言する場合は evidence と exact 一致しなければ拒否する。
**stock 判定に repo 正本 pin の照合を入れた**のは、caller が checkout と宣言 commit を一緒に選べる
以上、自己整合だけでは「承認済み pin」を意味しないためである。

**決定 (2): CLI authority は parser の private action だけが発行する run-scoped token にする。**
plain bool・偽 dataclass・別 run の token を拒否する。nonce は永続化しない (再起動 resume を
壊さないため)。permanent identity には安定した authority-kind だけを入れる。

**決定 (3): legacy cache key は stock を含む全 class で receipt digest を織り込む。** 段 2 プランと
段 3 の敵対レンズがいずれも「stock だけ例外にすると receipt を持たない旧 stock cache が受理され続け、
`旧 entry は拒否` というユーザー裁定と両立しない」と指摘した。あわせて legacy entry に
exact-schema の sidecar を必須化し、hit 時の欠落・不一致を明示拒否する。preimage 変更だけでは
旧 entry に検査が到達せず「拒否した」証拠にならないためである。

**決定 (4): v2 は preimage と completion manifest の両方に admission を必須 field で入れる。**
preimage・manifest・現在の source evidence を exact equality で照合する。

**決定 (5): campaign は canonical preimage へ policy を入れる (campaign ID が変わる)。**
起票時の親案は「ID を保ったまま lock へ焼く」だったが、canonical preimage は ID の材料そのものであり、
ID と lock を別 identity へ分裂させることになる。さらに旧 loop 成果物は official namespace にあり、
現行 driver は D123 で exploration namespace へ前向き移行済みなので、ID を保っても通常 resume で
旧 directory を踏まない。**可聴な拒否は overlay と consumer 側が担う**と整理した。

**決定 (6): replay で要求するのは receipt canonicality・policy 一致・attempt topology までとする。**
過去 attempt の source を現在 worktree と一致させる検査は入れない。receipt は source の hash しか
持たず bytes を持たないため、その検査は恒真化するか、正当な過去 iteration を一律拒否するかの
どちらかにしかならない。現在 source との一致は現在候補と cache 再利用の境界だけで要求する。
`BUILD_START` / `BUILD_DONE` / `COMMIT` は attempt ID で束ね、source 解決前に止まった
pre-build rejection は receipt 無しを許すが、その attempt から `BUILD_DONE` / `COMMIT` が出ていたら拒否する。

**決定 (7): 旧成果物は deny-only overlay で `legacy-unclassified` と宣言し、2 次元で持つ。**
`verification_status` (当時の verifier 判定) と `admission_status` を別 field にする。
実 WAL は `certified: true` を持っており、歴史的地位まで否定しては事実に反するためである。
台帳は campaign ID と path だけでなく **lock SHA・WAL SHA・`build_start` 件数の不変 tuple** でも
membership を照合する。ID/path だけでは、同じ bytes を別 directory へ置くだけで迂回できたためである。
reader は exact ledger SHA を decision receipt として返す。

**決定 (8): positive receipt 要求の射程は新 schema 以後の成果物に限る。** 歴史性は
「lock の key が無いこと」ではなく **pre-policy snapshot の exact path と bytes** で証明する。
key の有無で判定すると、receipt を欠く新成果物ほど歴史扱いで通る循環定義になるためである。
素性を証明できない receiptless artifact は selection へ通さない。全歴史成果物の遡及再分類は
本決定に含めない。

**決定 (9): non-admissible materializer は単一の registry を正本とし、producer への埋め込みは
一律にしない。** 埋め込みは producer によっては committed evidence の exact-key schema と
driver sha 束縛を壊し、修復に凍結・committed 成果物の再 pin を要求する。registry 自身が閉包を担う。
docstring はこの実態どおりに書き、例外とその理由を明記する。

**決定 (10): 閉じていない層に security credit を与えない。** D127 決定 (4) と同じ扱いで、
docstring と本決定に次を明記する — 同一 process 内発行器の真正性、shell materializer と
calibrator の任意 binary path、ABA / 混在 snapshot、freeze を経由した推移的 provenance、
全歴史成果物の遡及再分類、T126 control の再測定、S8b の refreeze 適格性が mode 由来であること、
成功する no-build 試行の正規形が無いこと。これらは検出できているのに閉じていない事実として残す。

**研究状態への影響:** 受理集合は狭まる方向にだけ変わる。同一 bytes を別 class と申告する経路、
class を跨いだ cache hit と terminal replay、receipt を持たない旧 loop 成果物の材料流入がいずれも
止まる。cache と campaign identity は一度 cold になり、旧 checkpoint は自動継続しない。
凍結成果物 23 件の bytes と `s1_known_axes_freeze.py` は不変である。

**却下した選択肢:**
- legacy cache key で stock を例外にする — receipt を持たない旧 stock cache が受理され続ける。
- campaign ID を保ったまま lock へ policy を焼く — ID と lock が別 identity へ分裂し、
  かつ旧 namespace が前向き移行済みのため通常 resume で発火しない。
- 3 campaign の denylist だけで既定除外する — 未掲載の receiptless artifact が通る。
- 全歴史成果物を遡及再分類する — 3 件の overlay 実装ではなく repository 全体の再分類であり、
  全 artifact と全 consumer の inventory を要する別 wave の仕事になる。
