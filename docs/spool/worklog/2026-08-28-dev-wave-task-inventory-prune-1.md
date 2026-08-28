---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-task-inventory-prune
seq: 1
title: 過剰実装・過剰ガードレール587件をactiveから除外する (docsのみ)
---

## 本文

- ユーザー裁定に従い、当初active 946件を全件棚卸しした。過剰防壁120件と開発プロセス/衛生476件を見送り対象としたが、current mainでT-2065が先に裁定・完了し、再開時の焦点監査で正しさblocker 8件をcarryへ戻した。残る587件のうち、既に見送り台帳へ存在するT-185/T-186は重複active carryを完了終端し、過剰防壁109件と開発プロセス/衛生476件、計585件を新たに見送りへ送る。
- 正しさ境界と研究速度の敵対相談を反映し、anomaly即reject、trace/perf分離、前向き事前登録、file-drawer防止、現行研究blockerは維持した。再開監査でT-1946/T-1948/T-1950/T-1955/T-1956/T-1957/T-1994/T-2005をproof chain・受理集合・正式実走のblockerと再確認した。
- 分類不能8件 (T-096/T-097/T-100/T-133/T-163/T-167/T-168/T-169) と別wave所有5件 (T-1861/T-1902/T-1933/T-1934/T-2012) は推測で処理しない。current mainで完了済みのT-1934を除く所有4件をcarryし、entry 1080のactive 937件からfold後のactive期待値を350件とした。

## 次の一手差分

### 完了

- [T-185] 見送り台帳に既存の条件付き見送りを正本とし、重複して残ったactive carryを終端する。
  remaining: none
  base: 96635f9e183be880fc07030bfdd102573925350fc952fa58c7ed487a90e55ae7

- [T-186] 見送り台帳に既存の条件付き見送りを正本とし、重複して残ったactive carryを終端する。
  remaining: none
  base: 0235b894e4162d564799b239eef8561afbc2b5610735b36aeaefbe03a5822c9c

### 見送り

#### 正しさ・防壁系

- [T-232] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: b47a58d580e334f848ba1ccdc6f895e9d2aea7c50e88b05abaf89f4acf4d883a

- [T-274] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 92eaecb0181910e1f3679559d57e52aba21d18f35be217347bda217344b89307

- [T-311] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 434057e85de9288f6a61d1296e6e0a515664dab230fa20c0fb0cad5e63274996

- [T-337] 種別宣言の機構と field 名は D528 で確定し、D162 決定 (11) の land 禁止も campaign producer に… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: cf2eb4d3d3e68a62d6bd0902d667138ef6e86de08126d2b3adcac524915340d9

- [T-338] **単位5 (writer + conformance vectors) 完了。次は単位6 (統合+4名前export)。** D574決定(… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 7149865b72d7c9234dcd2a03cd6d27828dfb97a7aabc100706cfe95c614047e6

- [T-361] bnode003/bnode004 間で /work・/home とも cross-node 6/6 BLOCKED、localflock な… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 7d868e3e23991039da1de0725df00b8be3dc350d7b4a9557ce0eb371a75b5be8

- [T-387] 択 (b) 採用・現状維持 — 受理集合は広げない。実害が無く、受理集合を広げるのは常に慎重にすべき方向である。ただし「実害がない理由は直接読… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 00a4413bd8e6783592ce90c7e7081df31eddbb25c82fead11730b2927d34468a

- [T-398] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 502564404743ff3ce61485aa63076ec022eb6b053cf1b9155c8255754a35fecb

- [T-405] 当該taskの持越し残件 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 16fdfaed21bafa6967a692a172a1ea03b49a62e033f051f6023b2517949c892c

- [T-478] 撤去採用につき床値 v2 の 発行経路は不要方向で確定した。撤去を実装する wave が最終確認して終端させる。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 29d2b16b75d920b68f5653e1b97896cc6683b23f784f59b1e5fe71196bb53a8d

- [T-500] post-policy の機械 sweep は membership 証拠なしで受理される。共有 validator は機械 lock に空の… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: da44f77d33fe34d36228105f3fb032da44761465b822417f8a543f191a2f0098

- [T-530] 読み出し境界の残件 6 問は択一の 形の裁定パッケージにしてから再提出する ([T-674] 所有)。D320 により provenance… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ae8e47ddc5d44c95eb51ee98c5dad92bf6d4d39c0113cede6ba69cf7cb344459

- [T-578] 変異 kill 判定で未固定の弱化変異が 他に無いかを、集合関係と正規化以外の軸 (rc 分類、timeout、artifact error)… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 09a7cd1ee118f52dbe506a3c4c1a823ab914e2005cf8938c93258fb4a1a758a6

- [T-582] current-only を意図として固定し、 直接テストで境界を押さえる (D1084)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 1485344243e3057e88259266000dcf2945eefbe693dbbbe94ab9b440207e5cee

- [T-696] 「審査される 側が審査する道具を書き換えられる」構造は、**協調境界として受容すると明文化する**。択 (a) の immutable tru… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 80843e09cc291cdf8814e910d7795f72b58c8c4f893c101fae4fb12eabb06abd

- [T-790] ルート A / B の択一は消滅した。 規範 compiler を site compiler へ寄せる以上、g++-13 を生むための隔離… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 73012b51050660e3d848566be857896abab9e4448540c0d016daf2e967402916

- [T-824] 択 (a) 採用 — 待ち手に呼び出し受領証 (段・wave・引数・script の指紋の束縛) を発行させ、段 7 の記録検査で照合する。待… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 708b35d858c4e6de62b8606ddf29a3bbec6d228eff6872ba93e34ae68648e300

- [T-829] _EXPECTED_FIXTURE_ENTRIES_SHA256 と _EXPECTED_ROW_IDS_SHA256 の 2 つの独立 ha… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ba4b74989a21e0d038c6d536b7e17e5e5435e978c3eaefad512acdf18e684862

- [T-847] 択 (a) 採用 — 呼び出しの権能を排他権の payload へ束縛し、release/renew で一致を要求する。同じ束の 4 点 (T… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 861a91a5374345804786fc2d0d3488711e99f6dd5dfb4c8c3fe1c8353d8815e3

- [T-923] 全面拒否を維持し、発火条件を分割先が残した権威・生成側・二相の防壁・予算台帳の解決に貼り直す。床値実測の開始とは結合しない (D915)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 6bfda1b939969e3487aca2fdc1ec280adaf2156bc340b88dc87e2eed38cdac2b

- [T-958] qualification/artifacts.py の append_jsonl と campaign/wal.py の lock prei… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 98eabdd318eca8693c1da43ee7a515eb4b6f307d54144e86c628d5d41b56d4e0

- [T-1013] 固定 literal 1〜2 変数の注入のみ可。allowlist の 一般化はしない。実装待ち。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 9417bf88cd978d73b476343044c859b1624e58eca80dd04120ca8bfbe2c8b4d4

- [T-1017] perf realpath を toolchain binding へ含める要求は、 D497 により official 化の必須依存ではない… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 5c2a080574b26babacf9d8a4df0ff0e74e49e5d75b9a3325812a266648b6294a

- [T-1018] competing_process / launch_failure の自己申告と保存 probe 証跡 (rc / stdout / std… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 7472d89578ec811449ea55cb2321beb876625fb5401e1eb12f713475fb152c58

- [T-1063] 占有の予約制は、本 rulings 第 1 束で「別枠として起票する」と裁定した占有穴の設計と同一の機構であるため、その枠で扱う。個別には決め… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 7f3c1d78862283c3d42ff1c715773299e275b6b93564f797a5b951a0bd502357

- [T-1121] 起動検査の残存限界 2 件。clean/smudge filter や EOL 変換のある path では clean-tree との連言が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 07590d9f59133982185741f1e70388405d5beff72b0245b67e9eb5835f8559c5

- [T-1122] tools/check_wave_startup.py の _git は subprocess に timeout を渡していない (既存 6… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 038bc958bba903f1eb93e6e0620b2e5b9005547e329f74e4509cf25be6b2786a

- [T-1136] 事前登録の判定器を -m で起動すると 12 条件すべてが評価器例外になる。同判定を package import 経由で呼ぶと正しく未定義を… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: aa99cc197503b00802436bdca21e29ac5e4f8fc92ee10e8573c9c89759d719aa

- [T-1158] build 中に依存 tree を差し替えて元へ戻す (ABA) 攻撃への予防を設計する。前後 snapshot の同値検査では検出できない。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 9cffc0502b1aa1c06fc66636ed5d735f5690ed030a8f0d249210d792e092f2d9

- [T-1160] 共有 FetchContent base に create-only の 所有権 token を導入する。現状は job 一意な $TMPDI… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 67c136c93dbb4bcc6de5fb79de9a0e3666980f5ffdfbeea94671986607e0a6fe

- [T-1161] 択 (b) 採用 — まず影響範囲を実測する。末端でない path を防壁の対象に含めるとビルド生成やパッチ適用と干渉して正規経路が止まりうる… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 71e2e2e684536a2db345f1b617b06c2aeee64df0e0f764e4d434abcde4fbaeca

- [T-1193] pin fast path が _verify_rollout_sha の失敗を 握り潰し、その後の全走査が同じ file を SHA 未検証… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: df4ce2e52e7cf0588481522048a0a04e6f0c1feaf51630ad72b7958fe0e70ab2

- [T-1215] 択 (b) 採用 — 当該 1 箇所の除去漏れだけ直し、族一般化は独立 2 例目を待つ。閾値を満たさないうちに族化するのは規律 5 (盛らない… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 65c0046c6de1a18e4bab2558a27a597437e3ec4ce96f3a10c2b14ea5416b58aa

- [T-1233] dispatch claim・変異 source 復元・evidence 退避・ teardown を直列化する per-checkout の… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: a99f57f629381447bb9efdc14807410563cead7ccdbdaccd9904ece7b7393df2

- [T-1236] qsub 前の永続 claim と、対象束縛された終端証拠による 解決 (tombstone)。SIGKILL・discovery 中の再 s… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: effc3a51b1687379480f1d4308920644d2cfc234625aa72018b8b289311dcfec

- [T-1238] 過剰拒否を検出する正例変異を、dispatch 署名・ dispatch 検出・worktree 検出・受入検出の 4 面へ登録する。本 wa… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 9930d17e4749b1137bcad153a3a663a0714a72beaa4c08ba0697400cad7f0d61

- [T-1242] SWO receipt を 「oracle が実際に走った」証明にする署名機構は**新設しない**。「bytes 級の凍結証拠・署名・束縛 機… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: a55ca93b01b0c24783d5f13ef411f9476fa9bb262f357b749283e3e6622824f5

- [T-1243] admission 台帳を 削除して同一 bytes で再構成する攻撃への耐性機構は**新設しない**。[T-1242] と同じ理由・同じ条件… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: c0a26df6eb7b7e5b45577657b142b0e3d4de329196e8723a440181824bb29453

- [T-1244] measurement_head は **非権威 field のまま**とし、位置づけを明記する。commit 束縛の新設は「計測は HEAD… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d665adf52e26dd5c71cbfce8821e787e401765d0251733d896f69717e3fb8e69

- [T-1258] 択 (b) 採用・当面維持 — 投入 script への外部起点の束縛は今は入れない。偽装には repo への書き込み権が要り、それを持つのは… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d02ad37d6ef4f9ce2839316b9c28c6c1a105913ce48eb3fa8f859ef5b5d06931

- [T-1266] gate の権威 (保持された authorization_contract.contract) と現行 registry がずれると、gat… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: f39e4c7e2ef95b04d6a5779b6e3a002202cc8f5eec642f6148f1ea5ec1e4f35e

- [T-1270] _cleanup_lifecycle は cleanup body の前に ownership を NONE へ消費するため、body 中に別… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 60c64d8033770c4a11fbdd1d535e090b1d73764675e293acbae08b9b670650a3

- [T-1288] -m 実行で判定器 module が二重に読み込まれ全 12 条件が evaluator-exception へ潰れる件は 直す。**呼び出し… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 528e15e340d3dc5c876b4de8af6720d3fd18a2704b2cdb63c579eb735bb4fa2d

- [T-1299] source root repository を信頼済み中核と明文化し、機械可読な限界宣言に残す。config allowlist を掛ければ… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: c34589b7d57f7a220b8b63f66517e623018e4ec94c433312b32ca9a5bfe5c00b

- [T-1305] 防御的冗長として明記して 残し、発火する保証にも検出力にも数えない (D1214)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ecd5ac2f50f1d0b9c033e79aa7028af4229674a59b7d0a1f0f8c050c2b5e337d

- [T-1317] dispatch の IZANAGI_DISPATCH_OUTCOME_V1 attestation は受入 command と同じ stdo… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: be7de1b3e986b17cb06fedf8cd34a9fcf6fe49dff2a2385b39335ae7844fc34b

- [T-1322] 床値 driver CLI の --protocol が caller 選択面のまま残っている。段 6 レビュー C / D が real と… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ee14160d901b2f0961a7ced31f673b009b420002f7e55aaf7ba207ce4d262a58

- [T-1323] official launch preflight (_PREFLIGHT_FIXED_FILES と legacy bytes 比較) が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8e475a1a68feae5da7b0403a13b31dd9fc5e66f464084b40fca41fe3b375c1ba

- [T-1324] v2 candidate producer が legacy path を固定で読む件は、予算承認の材料が揃い official floor… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: bc5c1dd3976dc43213455ba2461b7bc3d2a666d2f0d900638ff283fe5cad36b0

- [T-1325] committed-only 権威は bytes 一致を要求するが、 commit 後の chmod による作業ツリー側の mode drif… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 24fcec1ac8d9b603fb4f9dcbfda84485363b7230386bb77c7b9da6bb73fbfc46

- [T-1340] refusal 文字列と識別子に残る floor の語が、 比較の基礎という意味に誤読される。受理集合も certified 選択の値も pr… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 28410612da4f161f3101347d5acf035458568d3b6e685dd3d16484822a835abe

- [T-1369] 非機械条件 C03 / C07 / C08 の証拠契約に 実在しない関数名 accept_trial が残る (C03 の load_mani… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: bc1fc7b00ffbea7680a90039f6bc096f3e9549530da708393ba556ea2f0bb163

- [T-1370] 実走前 gate の s8b_oracle_driver._store_sha256 を no-follow / regular-file 確… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8a7bb2796cd978b3d38443556ccb3949d1942bdd99cf5c974b2c0ff20b75be9e

- [T-1375] land verifier 自身も候補コードである。D254 の provenance checker と同型に main へ束縛する。 成果… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 76e04dcae712b5f590c3ef3bc066aa050971b9f5ab1b52fae185a00c2651afc0

- [T-1377] 歴史 raw 専用の 4 ツール (s1_report.py / tools/plotting/plot_backoff.py / p2_2_… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 924be2a1b69a2ce41d8a78d3ee7cd379dfac8c2164073d2082351cc343b406e6

- [T-1386] 段 6 敵対レビューが real と判定しつつ本 wave の scope 外とした 6 件。 (a) malformed consumer… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 90a06b7ffa2b4dd980208d64d84381188c1863399a9d4565ef3c5efea2fb15be

- [T-1398] 受入待ち手の D486 attempt 2 で、self-claim 前に main がさらに進むと claim-self-unverifie… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8850d682a10f5f1ea2e295050309f8945257cc7755feb1f8d7d1b600df2c97b6

- [T-1417] _extract_latest_active/ _global_ordinal_entries (tools/spool_fold.py) は… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: fbe83efe624d2cbba87b52b9e5913c758a0a9b00226cea8ed069d2c2040106f1

- [T-1435] attempt registry の時点証明機構は「trusted launcher は誠実である」を 前提とする。この前提自体を機構的に検証… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 5aa12d41f49369d9e24192e3265a032317724c4b0c64f13b91e017c742c3c85c

- [T-1450] _receipt_schema.py:34-43の ReceiptSchema.__post_init__がdocumentの再ハッシュをせず… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: fcff0377f37833ab6caed30b96412eb800fbf056c3d806af2ce47b65458f8c39

- [T-1463] [T-287] 裁定パッケージ§3。値域検査では in-domain 改竄 (許可値の範囲内で rejected→fail+increase+… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 5368c71cad178c15a207caf4aab687e0cfb038109d8413e0914529b71aa61325

- [T-1478] journal の reservation-preflight イベントも perf-preflight と同型の resume classi… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 9f3ab0af73f7ebc7d38f10d32be2433094fcadeb747020f1629965cdef398dab

- [T-1483] D510項目6 (測定近接性ラベル) を実装する将来wave。前提条件: (a) provenance (timestamp・環境/実装/to… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 85870ccc870aab08880d70822dc23c57d6f1c13da7f8d95093fdd89a9872d910

- [T-1487] s8b_holdout_freeze.py の _blob_at_head/head 捕捉 (measurement_closure 等 4… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 14253774f80638b6d014afdf8aaae4854fa82617e17a9fd40fb0f748578f6d10

- [T-1521] 禁止を入れる前に (a) その禁止が実際に捕まえる負例 2 件と (b) 正当な用法を誤って拒まない境界の試験を実測する (D1213)。 *… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 9b188df7c23003414e4a7ff945b1ae8cf1a3abfe70d5f1a63fd273edc0d86fd4

- [T-1556] 受入環境の temp root を admission する層は作らない。発火する既存 artifact path も計測 ID も書けない段… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: cd5345a20f72c54840e9bf1d82285ef3ff4be95fd3e486d29178738ff20adae9

- [T-1570] 既定 K=2 である事実を踏まえても、受領証レベルの shard完全性証明は実害が出るまで作らない。実行器内部の完全性検査は維持する。 決定… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 520eed739e74db9b47dd2c814b53aa8237117d1eedf0803012e5020943f11e1c

- [T-1590] 適格判定の後に PYTEST_ADDOPTS を process 内で書き換える 窓が残る。これを行えるのは tools/run_tests.… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ec782646bc014d1f67bbc924542f76040674334add5210591663de29d5cdc7d1

- [T-1644] 静的に解決できない間接値の 限界は D774 の docstring 明記のまま据え置く。別の証明手段を設計する場合は [T-1642] の別… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 61b3fcf6c5b25f9d2f56ff91c54d29c8edfd136146d770648df948b91ae5b754

- [T-1654] 子が読む規範は working tree であり凍結されていない。 authority docs 2 file の 4 節だけが全文比較されて… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 82e18620080d4608593270fef0a6d7ddc74f8f67fbf2983fbc77b73767971ac8

- [T-1655] snapshot 取得から子の spawn までの間に authority docs を 書き換えられる窓が残る (現行でも同じ窓がある)。凍… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: c9e9e0ebbf9f2d6d94f3d97520dd1e57f5dce4ed608e28cfdd99d384528f4a44

- [T-1656] receipt は HEAD snapshot しか持たないため、 後日「どの merge admission で通ったか」を再検証できない。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 0f5cad3ded1c8a118e76256dd133d2845e2de925e7af596a9aa4b29ccb5c1475

- [T-1661] dangling 監査が抑止根拠に採った外部 copy を、 /cleanup-branches の削除直前に再検証する gate を検討する… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 072cb25e959eb71ac9379c18c3e31720b56b27d7787916f0341cb7d3108edf3d

- [T-1665] 最終 scan と shutil.rmtree の間に新規 process の 参入を排除する仕組みが無い。checker 自身が「走査後に始… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 69a29555f460cf8be36719266dbe8f6ed5044fda69f18a7563faa90dbff3c347

- [T-1666] cmdline 除外の invoker exe allowlist を、 祖先 edge を invoker ごとに証明する条件へ置き換える。… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 861c26e0e6bf39121e680e2d280c1c511b755bccff3fe2a3df200c55ea598f04

- [T-1673] adapter の registry 更新が共有 admission root の 排他 lock を取るため、全 worktree・全 ca… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ca2cc884f69412686e770101c8c5e14e15e522e7796d095dad09edc969144845

- [T-1679] interpreter の bytes 級同定 (実行 bytes・version・checker source bytes) は、D780… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: ab3e9bc50f1beb66b556d804cb5c0999ed7a79139627a988879bd1fb580a343b

- [T-1701] seccomp allowlist の exact 集合を固定する 検査を置く。現在の検査は hard-code した forbidden s… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 37d0dbe794e3c6f9d2ad67da3a901bfc1cfc4896b1d92ca2b4f7d7d2a9463cc4

- [T-1704] _BENCH_PAYLOAD_EXTRA_KEYS に 2 つ目の key を 足した瞬間、1 key だけ渡す既存 caller が mis… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 834a41e679652b7b6ae19002cc1e0e270946c45a233a8662a519a779963bb55c

- [T-1721] 4 問とも裁定 (D1222)。(1) 稼働 wave の land 後に一体で再設計する (2) 再開 scope の 8 項目への拡大を認… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 1c8790522a64c4dfb76bc8800912935a7935fded8acacd53840fa035b81cb76a

- [T-1723] exploration campaign root producer の discovery は**強化せず、現行の検出範囲を明記して運用する… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 97e91ffabfa632f145160077e13066e2b720e39e286f9220e595fd3893aac74e

- [T-1724] p3_autonomous_workload_trial の runtime 側 root 所在検査は**対象外と明記し、空の asserti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 76c6fdf080ac361e586ed2d35c1cf4969b1755de2bb2b52cef8e3bddfd6d80be

- [T-1729] s8c_preregistration_evidence.py の C01 は p3 の 3 関数の AST に整数リテラル 1_000_00… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 78916e1bd2b1672ca06609f28b39c0d01146562e193786afc4df108b52ca34a8

- [T-1733] tools/dev_wave_land.py の受領証に **発行元の証明と再送防止を設計する**。署名鍵と発行権限は候補および AI が書け… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 38126749e518cdf1a98f28808d835bdef7f50c18b73e8f922f5db262df704048

- [T-1750] 受入 launcher が実行器を起動する interpreter は素の python3 で PATH 解決である (tools/accep… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d5acb5d2cc58cf58a39c0574a334457f0dd391d5e2a73bcbd0e90fbf4f93f9ba

- [T-1778] A-1 の policy 束縛は同一 commit 内で しか効かない。policy・その SHA・source binding を別 com… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: aff6fd1f080acc4098619952af314c32ed3e09b2147be32061a75eb45089f1ec

- [T-1783] digest 中の間接識別子を 中立 label へ射影する型付き renderer は**採らない** (D988)。 make_criti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8d2d73d93e65b07310e4b63f4e354f159003b5817bb4983787c99b210c8d1ab8

- [T-1802] 明示共有 base を使う複数 job の間で、 oracle 判定後に別 process が prebuild を再入する経路を塞ぐ。D42… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 6d6cd60d79a0f13215258c2e243a6f75793ecae4f457e2a49f21630a6ab074c7

- [T-1808] 受入 gate 本体 (照合器・登録器・受領証) を強制ソース閉包へ **入れない**。D956 が「受入 gate を足す実装は閉包の ex… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 0d9946ca55ff23c4d54c1afb70c74260ec3155766d03f5d12c884d7924e241b1

- [T-1811] landed 参照が読む main 側 blob に size 上限が無い。修正前の git show も同じだったので回帰ではないが、mai… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: a9c44ccc4f30f709ae5e60bbf1561f5fd90f41cf754c2d9b7b01413bb866616f

- [T-1837] ambient IZANAGI_SORT_SWO_MASSTREE_ROOT から 任意の pin 適合 root を受理する product… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: a5a45f4783fb18e89a7052b99690a9a951cd0df52ea33e9f8d1ca657733764e6

- [T-1841] 択 (b) 採用 — D1099 の方針どおり偽造不能受領証の機構へ相乗りする (D1221)。同一主題の項も本裁定で終端した。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: dba7e273a69de4af9b529d207fb0e771775fc806c6b1ac783f477703bff9a465

- [T-1853] 登録しない。D1006 の条件文を 確定形へ改める (D1069)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: b710624ee4ad3d2c8b7a870ef7d05c2f52a2c69ee89a5aa5adde54c0875c2a33

- [T-1854] 分類受領証を封じた後、出力を開く前の crash で封じた bytes が復元不能になり slot が停止する。恒久解は durable な… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d0ee0da652a6aa9c182d66a329c14e374e8a603b3a8e1f7141d74fa8ba430373

- [T-1860] patchharness の共有 checkout guard は ContextVar を読むので、別 thread と subproces… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: afd1603d089f1a7992aac2ddc96a94367098955ac3190a172ce51e38fed521f8

- [T-1866] 再訪条件を「必ず通る経路に停止点ができたとき」へ改める (D1072)。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: e129d755e0e9d70bd643ad07421b57bf74770dea4a09d029831eda0c8914a4cf

- [T-1897] 変異 m08 (_evidence_sort の除去) に意味的検出器が無い。凍結 report の accepted_evidence が… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8bbcc76e3ad2092abf4d74a0dfa287909e8feb63e3b650e2e55c7783c6586796

- [T-1900] orchestrator/tests/test_check_docs.py の 共有ヘルパ _run_check は timeout=None… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 78d00045874c307ad7da8fea6a27d822dd0130dc70df849f5210fc004cb1f686

- [T-1927] 列挙した admin 名から gitdir を 開くまでの ABA 置換と、列挙後に増えた登録を現行 scan は検出しない。「矛盾のない 1… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: e4af82d1061a3be8131d04f98da8f7c9da101718cd5de28f6bab3c6e974146b2

- [T-1945] 択 (iii) 採用 — 予算だけ freeze 単位に残し、台帳を protocol 世代ごとに分ける複合形。 防壁の意味を変えずに世代を収… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8b70c8b1e7f313a4aeefc8820f342a921ad5ae4b75b776addf67c29931d53bb2

- [T-1947] FloorRetryAuthorization が公開 dataclass で、runner が isinstance しか検査しないため a… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d24cafd0b45a9679b000519ece5800184ed38c219b1cd4b3ea157896cf1949a5

- [T-1949] 案 A (pin 据え置き) を採用した (D1150)。SS2PL は既存 patch で扱い続ける。 案 C の前提 C-1 (sourc… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: d43288322ac2dae0c5bd96c72518579f75a30d5fc36d829ecd903b8d8200bcfc

- [T-1951] .gitmodules の branch = izanagi-trace を 実際の pin を含む tip へ揃える。現状 upstream… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: c833a08721bd446e521d1df8e1f062759dc4808a52b9ebb848350ccfbf71a493

- [T-1961] 同じ artifact を対象にする gate を 新設するとき、既存 gate と要求の向き (凍結か追随か) が逆でないかを機械検査する仕… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 6a04ae22f928836963f680f8e2bcbc215b1531ba7e911afcc78a5c470c1ba2d5

- [T-1988] 全史検査と履歴取得の間に履歴 view が 変わると過去の不正を取り逃す。v1 も同一構造。外部の固定実行器を要する。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 060cd65bb66778ae13434a7e56c6ae1f8f09e84e58292ee42a7b3b52395b1840

- [T-1989] qualification lane へ署名 gate を付けるかは evidence-only lane の意味を変えるため別裁定とする。 — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 18d619253ede7f051bb5d66b9ac1b780ef642b98e68cf84c1fedd085a3876d12

- [T-2026] 承認 bytes を誰が置くかの 射程衝突を裁定する。D287 は本 pin について「人間がコード diff をレビューして定数を置く」を… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 8b41b42a7e3c25c2579878f98a21c9e88b251beafe36e9c162f1319a1a782cbe

- [T-2039] 末尾 append では user site の .pth が追加する path は復元されない (site.addsitedir() を禁じ… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: 914e86cc768474382105e96b5c7d0ab2d42e5bf1be9244dbcb836d27cfcffb10

- [T-2047] s8b_attempt_registry.py は旧 consumed/ と旧 marker schema だけを読む。現在 producti… — 理由: 現行claimへの具体的影響が立証されない追加防御であり、D205/D730に従いactiveから除外する。
  再訪条件: 独立3実害、現行研究実走blocker、または既発行claimの誤りを実証したとき。
  base: c42ead267f63d11de7d849ffeaec5dae7eb7f41c52f92329c5774f00ea984dee

#### プロセス文書系

- [T-211] 択 (a) を緩い形で採用 — 完全一致ではなく「見出し文が大幅に変わったら警告」とする。carry 検査の強化 (本 rulings 第 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2838853b4a7d04a7dfd22aeb1edfa389b656bf20857fed80d92a90137ec1e2d3

- [T-212] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 47f788fce9f9fb2c9219425491f96b4d8a3e73189c873b1d4e4082dc711fe66b

- [T-213] 択 (a) 採用 — 隔離複製の置き場を共有ファイルシステムへ移す。検査の実行場所契約を変える案は受理集合と実行場所の両方を動かすため影響が広… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 642076a82b0d68182ef8180ecdf5bc15975f0b1233df5b3acac608ef9bd7fcec

- [T-223] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 779103ed748d117fbbcc3b1257e964e92f8159bf016cf34864045a7d688f43ee

- [T-231] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bd1c5e354f05aafc75cca112804a8cd5951d2376d486a87cb35fa7b5a4cc05be

- [T-233] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c3d68eed80435816a345117a7d6e4c90f59635b0327cc92ea68a41fd6adc29e8

- [T-248] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 159fc2129bef612eb45b46bc2e1255c6728ccea19d4f520da44fb5f70e9f34d4

- [T-254] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 46f8818c1e387d63a8dc85f738cee1b3eafbb9aa4d88f79669740b0fca2f14b9

- [T-255] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 72ce142591aa6392edd85c7c548507e0848de0116040dd3999ff1e398fd8a3e3

- [T-258] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bb0186b382c35e90366872fc120f86d9f6196655a6c64cfed345369371dc843c

- [T-270] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 22546064bf20cc1d73071b2f3ee551d3d26a498451cbe908bb127fab094f5413

- [T-280] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8ef011366472f08004c77bda0efa1eaab91021f4813b2ff61f76805d564ba32f

- [T-294] 択 (a) 採用 — 着地直前の再収集を手順へ入れ、収集は判定語に依存しない形にする。2026-08-25 の全件収集で、語で絞る収集が変種を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: db43a4096353dcd49f69b1f94a6dbe775493daaec9c5cfcff238d62e371db2fe

- [T-298] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 98f1efcd36e8ed268b298048da82942ff0aa7f9330708eeca583321c1ebe2dff

- [T-300] ログイン側の headroom admission gate は本 wave で実装・受入・変異まで 完了した (D209)。**残るのは本丸… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4130ac46817138e5f7b03de78f7ee6db8d24f2c8298922e41b120bf55a7e5873

- [T-301] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d799885cb25527b7bc1fa08862a021fda9a555ae42f2c33f62644f7caa7b203a

- [T-305] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5dcee5259cba9c432bf9c4a770eb1cca0ccf2da0903c67a01b58835e3a58af7c

- [T-309] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f6f8924384e77c5b7d8e37154c89a4c56b779e512354d3d90fed7e79652a2594

- [T-347] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a9a71d5120e7d2a96ea4550177172aaff7f3bf47dfa255d2df5953cf2d8feb23

- [T-349] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7bc1a7abc0c981ffaa61105bcb9f161f7b630a24547f467e264bb783e94f0690

- [T-351] /rulings の収集経路に、現 branch の valid pending fragment を加える。記録先は spool へ変えたが… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6a0589af5e6dafb3f434225ce59b9f15e0d143dbb9dd3be10b7978bcb022227c

- [T-354] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c81e3d0db9e4a519ea3ba636bdfb60047bd06d146c6284f8f2dec9267790e396

- [T-355] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d030444189eb307dfe7b5301766bd0e30945dc95af4c21e9f38f851416d8ce65

- [T-364] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 228c1cae74bc36ff231c1f68bc18d5ed6bcbf08450d8a7677ca83faca0053efc

- [T-368] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3023ee49602797d41024caa47f41ae54d9281e769aff74fc135a6e607ff67237

- [T-370] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 447c5f5bf231abd4f8004de6bb631d9aba967eae060a68a6006b7e877275b804

- [T-388] 専用の一時ツリーへ隔離する (D1217)。 **着手前に、除外集合の導出を変えた裁定 (同日着地) の後でも再現するかを確かめる。** 20… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 002fc261b45fd4407ee2552f058e5cc4fad31da726e992a33b03e40c2b639009

- [T-389] まず現状を実測する。射程の訂正 = 受入ツールが自分で main を merge する経路と、着地 tip を指定して再走を避ける経路が既に在… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cb9cffbfd669d6cd3a764cf7e7dac21a5008376267f65dd23cb56bc11e142d7a

- [T-392] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 48bbbcf7d77ebe103c6e742a957c9856425cd655354ca81a3000b167ee85b3a4

- [T-411] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fd4f4963617eac2be789e8ce6b9a2daeb54303c28310bd478a6a46fa90643d69

- [T-442] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 111c38da65bfdcf8ed25ca2f7566c1279c12eb3798ae4f59310577830eebf8e8

- [T-448] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2b909bbe00ba26e03258c4dcedc6e71503500b3e25fdac7c01cd6db16916ee72

- [T-456] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9501c80cc2887ec4eba54d4fcd02262dee687501c660ba1f6a6451cb7095bb27

- [T-464] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e3973d423a8b2264142c886b40f983a836eb41045159542879e046cf6294e78c

- [T-467] 択 (a) 採用 — 合成のみの merge の記録規則 (著者出所行 / waiver / 判定変更のいずれか) を明文化する。D770 が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 48b4de77169f0235021301ab6b443bbd9c8a87308fc995ae04315cf91a7bc5d8

- [T-491] 当該taskの持越し残件 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6a3d35760b73fb0e427d4b71441d4fe17040f06a4d1d23195d8f7a92b88e4b1c

- [T-508] docs/dev-wave 予算は機械検査・ ツール化への移管 (b) を主、陳腐化削除 (a) を従として余白を作る。(c) 予算の独立審査… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 556d33eef72fc07a1491e6926df106a377bb288fe365c4f9924d473ba8856bd9

- [T-511] 択 (b) 採用 — 任意コマンドを計算ノードへ送る汎用の投入種別を足す。初回走行の規定を足す案は「1 走目はログインノードで」を制度化する方… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8e0de3b9d39a74840dccc3d09c279e82dbc49aae13dff9559c65cbab481be38a

- [T-515] 択 (b) 採用・現状維持 — 指紋の導出は変えない。certified 選択に入らないため実害は台帳の重複だけで、導出変更は複数の利用側を持… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9f8507ab075651d667212e025ab4dcde00071b5a95aae66e298a45cf85aabd9d

- [T-518] 択 (b) 採用 — ディレクトリ移動を追跡しない穴と再帰打ち切りの穴を先に閉じ、引数形式の差と起動方式の穴は測定経路の裁定と同時に決める。後… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5851ffb978e39ebd71de670fde333178b0c22ee1f4a6192503367040e1ea726d

- [T-520] 資源分類の実測がユーザー端末の手番である ことを docs/pegasus-runbook.md §7.0 と tools/README.md… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 49c039ca2d5c080db2d8550bbd3d5a303da11a8b21e352c7cc866f44e07c1147

- [T-526] python3 -m orchestrator.campaign.s8c_preregistration check が二重 import で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fab0571ebada6f684df85de3d4fcca3280182a6d4d2d6d436876e98a84ce34be

- [T-550] 択 (a) 採用・制度化 — 使い捨て試験コードの規模上限を族として制度化する。独立 2 例で閾値を満たしている。制度化の中身は文書 1 行な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5dbfb2001e409e32af81a7286397a3679180d01b0e3829c7d49e946a648cac9b

- [T-591] tools/pegasus/fetch_third_party.py を admission registry へ local-ok として登… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 317dc892f1a985551e579a6fa1125f8a1c387f935fcdf70ed6f302235ddd29c6

- [T-599] ログインノードでの build 解禁は、**そもそも今も必要かを先に確認する**。この項が「ユーザー依頼の未達」と記録されて から時間が経ち、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 08a5ddf763cd33e3e764377f352fc20a0e8e41384514f41bf854d5bb8e83ad77

- [T-604] ログインノードの bounded scope 実行が memory.max / memory.oom.group を走行中に attest で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 346f811f4415b7e618695dd98d2cef7c5afc48d022ef9b6860004f80ac92ce5f

- [T-611] tools/mutation_worktree.py の分類 実測は、軽い複製への変更 (裁定済み) の実装後に行う — 今の重い clone… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6b087871b46f2b1f6fa48e53642da86c6a00b0a40cf2be4da875d7144f9b22a7

- [T-612] 択 (b) 採用 — 実残骸の場所を観測してから設計する。中止時の自動片付けは docs 予算に阻まれた収容として D782 の AI 側処理… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ca731efe7a345d8fb01067baa46295fee3d7ea4d83bed8281674824ab541fb09

- [T-613] tools/mutation_harness.py が run_tests.py へ D209 決定 10 の --force-dispatc… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b1b4afd833e607ce8ba0606a02f6b4be0167ba8d233e8aa83326514c33f664a6

- [T-617] orchestrator/tests/test_pegasus_tools.py:632 の _acquisition_probe_docum… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1e5cabf6c4ac3ebd8142d9cfd308daac43c26e56e1592894a117effbe74cfd7c

- [T-620] --runner-mode の経路要求と spec / out の置き場は docs 追記でなく変異ハーネス側の機械検査にする ([T-508… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f9899b3dc18d28f6583da2504b1ae61eefbdc659664ca78ad7037ab4764cf1ee

- [T-637] 条件 dispatch の parser が 3 列未満または backtick path 不一致の行を黙って無視する挙動を、無視でなく赤にす… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f80e2204ef0f4344fa8670b7eed3507e071656b9987ab5bb7fe88702b71ed70a

- [T-638] tools/claude_session_ledger.py (既定 argv) は計算ノード 2 台・有効 5 走で charged del… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3ab4a36ea89373fba459cc5ac55305b7122d1ec57e10faa9be87c4035ede89ac

- [T-650] land が到達点ごとに release_safe / retryable_same_request を宣言し、 両方成立するときだけ受入 l… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: eb8f4a9eb26335e1ef6b9d0ec92dda654b705c24d6dbb9810e9a6bfe2f2ad4ea

- [T-659] 対象は列挙できる閉集合に限り、機構は作らず手順で担う (発行 tool の head 書込み案は不採用)。 活性化専用の作業窓を手順で置き、採… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6bcfbbb90a07295d835ee7de1026aeeeb9409e3915fa64759c94711e435b53a6

- [T-669] dev-wave の子投入 preflight に local main の SHA 比較を 足す。現状は親の手検査で代替しており、並行 wa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 384a8ca58c3391edebf3947b2bf69e606e2c3051d0cc0631e894806ff0aa8c00

- [T-681] 親が実編集 probe を行う前に作業ツリーが clean で あることを機械確認する。未 commit の子成果がある状態での復元は復旧不能… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cd1d672df6bcd91aa7a4d4756a463d5666b053b58904dc7d827383c4e86a0fb0

- [T-693] tools/wave_land_window.py の claim は 非 acquired (held / queued / stale-h… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6677b47f46553ce900c494e2953a4972867cae3a4e968c5a7002e1eeaaae4fff

- [T-711] docs/spool/failures/ の fragment に **更新 節を足す** (対象 F と差し替える行を base diges… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 276f0d07a7ca23dd09d2a796853ed5f77e12f06a251ce1f63d4b0d8229cd168d

- [T-713] [T-692] R3 = (a) の裁定に基づく起票。 実 repo を読む重い git テスト群 (s8c candidate、ruleop… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e2308aea0d082ccdf83fed769135da0eb76c89ddbf98708cc7d460ac2736756e

- [T-724] tools/spool_fold.py:1151 の carry_re が 変わらず (前エントリ参照) という序数なしの旧形式 stub を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 54d035c688e5afabe5a41723577a5e621997ce4b52bec29b219397a45164757c

- [T-754] tools/check_wave_startup.py は local main との乖離と handoff の実在を見るが、**同じ wor… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 64242e66b6c15a12107c4772940bd097e345b08068bdcf8b20dec0e725595029

- [T-777] 住所構造 lint を受入経路で 走らせる形だけ入れる。偽 edge (Markdown 意味解釈) の対処は却下維持 (DW-G03 独立… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4d871fd9e37b1ac62bd8f97f5687110a427ae22e9a9f31a47c3d324d977b47ed

- [T-778] 期待 node の完全一致と走行範囲の 絞りの注意は runner 側の検査・警告にする ([T-508] (b))。DW-M08 への追記は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f69112046606815542e719ee348f5323ab2d4b25a39d6407ec99c6ff65dd943e

- [T-782] Q1 は読み替える、 Q3 は生成点で凍結し世代更新と対にする、Q4 は既存設計資産を起点にする。 Q2 は D992、Q5 は D961 で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6cd88cd124e35a59b43fb74ca5846844ac4bf4a795928608ccfb8ddc92ab7a45

- [T-826] M0 = 受入テストの分割不変性と real-repo 排他閉包を機械検査で成立させる。排他閉包の欠落は 分割と無関係に同時 dispatch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ae36731d970ed4af7e9ba0214792b18e732862d65c4b84525e609662a162bc14

- [T-830] tools/check_docs.py の fence scanner が indent を**表示 column ではなく文字数**で数えて… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f7c4c9b6f1fb46bd8931a74efa69ac3ecbadb0fd8244f2dcc19c37a745cc47a8

- [T-835] 択 (a) 採用 — 固有条件で確立した直し方 (slot + nonce の先行固定) を一般規範へも適用する。「条件を満たす方法が存在しな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 066370d9592cf5eb871c013e93aa90b6ffa9df095bf1af70621b19d2fa82265e

- [T-845] --artifact-root の親 dir 取りと <root>/<wave>/<job-id> の事前作成は dev_wave_codex… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fb0e6d958c423afae612a4d3fe80fa619eba0e03f4fba950fe866535df28b183

- [T-846] test_p3_s4_loop.py::test_checkpoint_direction_and_magnitude_domains_mat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5d4812b43dedb112d8b928eec0a7d8908228be69d71e33caa776ec01019b6379

- [T-853] 択 (a) 採用 — 文面を「実装面差分ゼロ」にする。誤分類の向きが免除拡大であり絶対規律 2 の面に当たる。「実装面」は入口が既に定義済みの… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f5fdab8a65f99bbb15688efd73a1c74c1a82f34990376ce5ee56d6dd0e069190

- [T-855] 択 (a) 採用 — 分解済みの 2 行を正規化し、非正規形を弾く機械検査も入れる。判定は 2 秒で、混入時点で止まれば子を走らせてから捨てる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0bdd8cfd2ecb5db676d261878739b1a9830ee76ea66d05db3ea3ce25df60cd50

- [T-865] test_spool_fold.py の _copy_real_canonical_family が dependency closure を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 94564b75842248db187cf798dc88165bddd63e60a3a508b7748a74c11ea9f1e3

- [T-870] dev-wave-t870-lease-timingwaveがclaim→land/release実時間を実測した (output/insig… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 25f391a645a1a52a815602d9c7301c535540004e09a1dcc6aeade8f61b8ef9ba

- [T-875] 段別 argv 契約の検証は launcher が 投入前に --dry-run 相当を自動実行して弾く形にする。DW-O01 への追記はしな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c9eb6edc994f49634508198d31ca9f8a69e6b7dde5001fb18d5614f8def48804

- [T-876] _normalize_node() で xdist の @<group> 接尾辞を剥がし、**xdist_group marker 付きテスト… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5ccc27b401cf5abf2c51a9774e4e707956ee73e0a4132e01365f31677dedce9d

- [T-878] orchestrator/tests/test_s8b_approved.py:31 の from tests.skiputil import… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4918908cc751230d18d343fbc34a0911b2e845bf6ba83ac5bb8a7c8d86a2045a

- [T-880] 択 (b) 採用 — 対象 repo の tools を import 文脈へ束縛する。現状維持は「別 repo を対象にすると誤った版を読む… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f6d54f0a4b50b7a62a3d4357b8c4feb943820959e12399c8b2b1b2462b1098b9

- [T-882] 受入全走の短縮を (a) batch 化と (b) opt-in 化へ分解する。 IZANAGI_T080_E2E=1 で同一 workloa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e8ce432a7350269def104180a52206501d9d163cf45d947840eea7c1ac1be976

- [T-884] 択 (a) 採用 — セッション記録の全件解析へ索引か上限を入れる。約 106 ファイル/日で増え約 26 日で倍になる速度は放置できない。p… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 40fcf4575f5e4743a75d13e71db2b09a60889eb256d3577ee5b876a79ee9e92c

- [T-885] 隔離の保証が変わらないことを確認の うえ --no-checkout / hardlink 等の軽量形へ変える。[T-893] と同一裁定 (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 125d5c6db0206c2d0f3edf0ded969b9c0b155927e977163dab711660ff9fac45

- [T-887] 択 (a) 採用 — 限定 group を別案として再提示可能とする。退けた根拠が D91 の逆読みだった以上再提示は正当である。実測は並列数… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 688e49833e1af5f39a22d26493064f8a47e710328df4a5ccef9080aec27a1931

- [T-889] state 無しの検証済み fold commit を already-landed と認識する経路を land へ足す。受理集合を 広げる変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bf9832011297c7e7e1df18e070f2158b8fbe86f1760e3d15fc665717f27bb1d7

- [T-890] lock-aware finalize / inspect command を作り standalone apply を封鎖する。[T-799… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cd6b7a900c451447f38eb8b04e4db0e785518313bf91830e6f64b2216c9687fb

- [T-892] 本 wave の変異 1 巡目で、 この赤が **baseline を FAILED にして harness の production wri… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4c016a12768d9a8737f34f4ba41a71a76492ecb9b12da65e7a6364939d4002e0

- [T-893] [T-885] と同一裁定。E2E の repo 全体 clone は隔離意味論の確認つきで hardlink / --no-checkout… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: db74fb9b0974c08c567cadb837b7c1fab526880a83d5c3a4989f37b24171b6ce

- [T-894] 受入待ち手の merge 競合診断に競合 path を 出させる。現状は stage=merge rc=70 だけで、親が git merge… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8ed9b3546cf00216ff4fe3653d381e772f9cdc4f7a2a25a2d7d276d5162714b2

- [T-895] 「次の一手」の項が裁定で終端したまま active に残り続ける構造を検知する。本 wave の実測では 62 件が滞留し、うち 52 件は残… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 03f83096eb3bfd380a043ec582d1c6a2d582fe1408cfd08846930bbacda69977

- [T-896] 二重在籍 8 件は **worklog の active 側を正本とし、見送り台帳側の項を消せる手段 (更新 型) を足す**。残作業が ある… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 658eb573b198d4c59c669cb815875005dccbb27a75ecc1182636112cafb3b3a0

- [T-912] [T-709] が裁定した部分集合一致の判定枠 (期待 node が実測失敗集合に含まれれば KILLED) は tools/mutation… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9db485810ca39d6f9a26c1e8c0b569782a23247756242101a807ed3933e1ab4b

- [T-928] 段 2A が挙げた残り約 40 function を 一次証拠で検証し、成長比例と確認できたものを台帳へ追加する。証拠 (file:line… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1cc0afba60a801739aaa384ca8bff6a4108dd7e6105c3d86e0f1d766dce42be8

- [T-935] submodule gitlink の前進は Git 操作の 機械的代行であって著作ではないと docs/ai-provenance.md へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 09da0fc531cfbff4087ceedc6165c21967bb654aa51bb5389cdef746d67f77ef

- [T-937] _scan_session_rows が 全 corpus の全行を parse する。現在はテストが実 corpus を渡していないため律速… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c1f55b8ac403958d72f2c26c3940108fb23d6cbb8a475d13771853be1088f530

- [T-938] provenance checker の merge 判定を path の積集合から内容へ寄せる。git diff-tree --cc が空の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 780ddc4db1a4f9fa5dd7a1cf6e3f58075c2c856457b5c75a71021afcd8832046

- [T-939] 比例項の真の除去 (session-id 索引または直接解決可能な path 契約)。本 wave は係数を下げただけで walk の線形項は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5acf9565a075f078f816779f28be13ea62849657ffd797dc39d9a9693367cb5b

- [T-952] worktree-dev-wave-testops-observation の未 land commit 3 本は、所有が曖昧なまま置くと b… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4350264c4853cfb69ea96bcb13550356eb697aecb6331a5752e92010b9a48ccc

- [T-959] L2 経路で収容する裁定は変わらない。収容対象に、entry 859 本文へ実測付きで記録されながら T 項を持たない段 8 候補 4 件を含… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3e8501be66c52cfe0d25b139c2d4c0c401a91e1710566b1a36fd03bf532ef1cb

- [T-960] tools/run_tests.py が --noconftest と suite 下を指す --confcutdir を fail-clos… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9ac992dafaf65f21e2d43608f009547345808d8965186a915989c293c784ee78

- [T-963] 残る 3 本 (backup-rulings-land-20260812-first-attempt、 backup-rulings-land… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e4908a15c48745b61a2cd4194a754516bf0fe4b25660d5c4de0b3ceb461a6afd

- [T-980] 受入成果物へ worker ID・worker 別開始終了時刻・receipt memo の cache hit/miss・ lock 取得待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: dcbd9f92a0c441167328af1ea1d71ab17f64dbdf2f51654d9627974cee3b90ab

- [T-981] 「evidence_status=invalid の理由を receipt へ記録する」は 本 wave で実装した (schema v5 の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e091e12e47b38a2a52614d3bc5d17cd92b850ec91cd024941f72041ae9784225

- [T-995] 既知違反台帳の各 entry が「実在する commit で 実際にその違反を持つ」ことを検査する positive coverage を足す… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1bd3457ca1fc4861336810a97da0491f100af33e95c4a3ef3c247c6444b4c6e1

- [T-997] 択 (a) 採用 — 拒否は維持したまま理由を出す形に直す。受理集合は変わらない。「repo 外からは走らない」ことを明示する診断は、相対パス… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1b504c843253bcb66114e7247ccd650381cbd1ba3bdb408a52cac22a5def93ce

- [T-998] claude_session_ledger.py が 並列 subagent の transcript 間で共有される message id… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 44af53d2dc509fa2e11beef3662461993b4bdcc16f7a043a43d02d77eba05a96

- [T-999] collect_wave_usage.py が 内側 collector へ --project を空白区切りで渡すため、先頭が - の実 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 47682dfb68d7faaaef94561f2ed09a36bd8e2bac2b9556140785f3c03ec54d6b

- [T-1002] codex 成果物の検証器が要求する ## 総括 見出しを dev-wave の prompt 定型へ入れる。今回 1 投入 (64 秒・mo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 34f9c4ecb6b9c6f4c22835a051773ac5900e9767f454cf523d043b938ee9cec5

- [T-1004] 択 (b) 採用 — 検査間の競合 (検査後に main が進むと緑になる) と対象 main OID の未認証の 2 件を閉じ、残りは記録に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 27e3cf507d70d51fd09003e97f896a14ed467feb969dcdc7b32398c8bf099319

- [T-1005] 裁定条件が不成立という実測は変わらない。本族の赤は D498 の実装で閉じる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5bf822cbaedd3a980c1e6f25f3fe18ac89be7ffcf95e5e13738ef6d33a9e1c40

- [T-1009] 変異 runner は **dispatch recipe (--force-dispatch) を正とする** ([T-613] の運用規約… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 19bbe7e90fad341bf5940896338fc0845a34e546f42c5b4e744c8284f7ed32c0

- [T-1010] docs/dev-wave/** と入口の圧縮が exact pin を 跨いだかを、圧縮前に機械で洗い出す手段がない。本 wave は 4… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2bcbb0109fa095428e5f0b5b215da3497f6de5ed112309d2dde4f3ad41bb93e5

- [T-1011] 変異 harness の起動前 abort 4 型 (--wrapper-attempt の型、-rf 必須、container 残骸、--o… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f0b6b3ca50b6bc09a09761ab3ca34ef197c4171194a597db04175f207279db37

- [T-1016] 実資源に触るが現 writer と path-disjoint な reader の第三分類。read path と writer path… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1977c3bd5be736d63d6d46a8e0e654ba78b866a46a66a296d817bf2b0ef1b4de

- [T-1021] tools/run_tests.py は Pegasus login の headroom が足りる経路で bounded test を先に実… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 18938f7680b895e894ccecf8aac84458de2545d350e2fb2fe2fe674234bb5941

- [T-1023] check_acceptance_reds.py の probe worktree は SIGTERM / SIGHUP / SIGINT で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ca16279fa1e66377866fcf30a7d9577e96fbd420b5b0ef56dad1a44ca0eacdab

- [T-1026] hooks/guard_bash.py の docstring (39-45 行付近) が現状と 2 点食い違う。(1)「Codex subp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5adf0e7c01fce7bb6a8d585597f6e976dcb9781e297521d81d5baa6178cd7250

- [T-1032] 択 (a) 採用・引数単位 — 同じ script が引数次第で軽い処理にも重い処理にもなるため path だけでは分類できない。測定対象を本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cc32c2def7274d2e6541fc759df8bc2cddf3e885d7f0ba74e04062afb4e34f9b

- [T-1033] 実 1,045 file 入力の 30 collision 群を 現行 resolver へ通して全群が解けることを確認する。実行場所の手番が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 84ea442fa3e08622800b41062ee5d38540a956051cb483cdd0c1ca030aad9bbf

- [T-1036] 択 (a) 採用 — 実行場所の分類に失敗したときは閉じる側 (実行拒否) に倒す。ログインノードで重い処理を走らせる事故は共有環境への外乱で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a1d4eb823d0a92101a538ef356bbd62c7db5f9cf888eaa42ba28453255bbd634

- [T-1056] tools/dev_wave_wait.py producer が、 .done も成果物も存在せず producer が生存している状態で、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b0408633a60d85486e2517cadfce9e750af1145e326737f2b3a6ac325141fb7c

- [T-1057] checker 全体の timeout (i) と checker 実行中の lease heartbeat (ii) を実装する。 (ii)… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0d63968baaf3510f8470b380c19ca866fde8f552eed04731a5a51eac1c3e2fda

- [T-1058] test_dev_wave_wait.py の signal handler 復元テストが変異 harness の走行間で揺れる。 2 巡目で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b973636793ef6d54a5ffce0ea1e09c4db67d23dd465a002f0ce61cfd3dda8687

- [T-1059] tools/codex_worker_launch.py の --evidence-grace-s 既定は 5 秒で、この時間内に codex… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2ed0e3375285f17c206e7ed5abaade18e27f264b9d42ab0072a8155a141b625a

- [T-1061] test_dev_wave_wait.py の fake effects は期待 event 列を固定するため、共有定数や共通呼び出しを変異さ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b76bac97f045039c7c29715f11664cab8f197fe1db72247a3d699f1ac75bc0ed

- [T-1064] 択 (a) 採用 — 生の worktree 削除と登録済み worktree への強制削除を防壁の破壊系集合へ入れる。防壁を強める方向であり… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4a3bf3fe0ccb03f71b39d0932a0bbe1886b82f4c252b7c0307c2813510e9d021

- [T-1079] test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 87e709aef456b03081f8d162db935f3f3c9a31d9b96eabbca0a58ede587e94ba

- [T-1080] 択 (2) 採用 — 完全なやり取りの生涯 (開始ちょうど 1 回 → 完了) を「証拠が完全」の必要条件にする。択 (3) (CLI に機械… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1e9beed24f071f6c25162e27ad95fd207a4a130c73b98b84733c77e136578822

- [T-1081] orchestrator/tests/test_codex_worker_launch.py は dispatch 走行でも走ごとに 1〜40… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7fc87425f7a3a937762a6d6d39bb4ec36f41535df5576dc66f9a8fadb69da034

- [T-1082] test_codex_worker_launch.py は計算ノード前提と明記する。1 file のために前回ピーク由来の 予算算出方式を変え… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f97d36bf192006dd0d41590cfe73b008e9b8b426ca7082b292e3bc88fb242045

- [T-1084] evidence_forced_stop が receipt に出ないため、SIGTERM が evidence deadline 由来か 外… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f699c718ce3e5533a971aa63850c3c28d029f79b8b3692c83ac74a324cf0534b

- [T-1085] 子が正しさで拒否されると output が公開されず、dev_wave_wait.py producer は それを producer-fil… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 595c2611f742568d978112f736f9c175fa540f9d678a4e9475e7d2392ba09aa6

- [T-1091] 背景の待ち手が producer 生存・.done 未生成の 状態で rc=0 復帰する事象を 1 session で複数回観測した。tool… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ec85ae5df029c4da7ebb22870d656c11fc35aa0ccc8c27b1553e8b0c48bef39b

- [T-1093] dev-wave の codex 子が成果物を書き終えた後、 producer script が .done を書く前に落ちる事象を 1 se… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: aecf3526fa886ce0677b3952ca23ee0e0013e952842c9f342ff347736697b78a

- [T-1097] 択 (a) 採用 — 3 者の順序を「診断の出力 → bytes 契約 → 本件」とする。診断が出るようになれば残り 2 件の誤診が止まるため… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9fbaaf64b4ede2bfc2afda8501cf771c33c953a91bf7ea5f4ffa079ee9095394

- [T-1098] 受入 lease の critical section の内訳は pytest 156 秒 + **親が受入成功後に lease を握ったまま… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e6a4545149ddf256fdf9f15e6ce62aebc55ecf87e32eca41168864113796780d

- [T-1101] 受入試行の終端 (成功・失敗 stage・所要秒) を機械集計する仕組みが無く、本 wave は job dir の mtime と log… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6349fea4e2a5375234229592ced8682f49008ab0304eaca825d7cff726ba6c71

- [T-1105] codex 子の sandbox から tools/run_tests.py が走らない (local 予約台帳を更新できず dispatch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d34c0bb38344b80f5f2b0ac18df5ed8b7c3b59b45550d63db1e85c164407f515

- [T-1107] 族の member に **4 つ目の file** が加わった。2026-08-16 01:38 JST の 受入で orchestrato… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d4b3ca6349dc8b2d801540104526d4e361d78484d5a0e1938e7822e376a0cb89

- [T-1114] tools/check_docs.py へ 「spool fragment の 更新 / 完了 item の本文が carry stub 形式… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 66b3a23e1e34d6ecb6e18cf838502d75f668b594c9eafba5a6ec695053de69ce

- [T-1118] 非帰属 checker は子 pytest へ渡す環境から pytest 選択系の変数しか除去せず、task-run 記録の変数を残す。これが… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fa914fe05cdbfc14ff0e91e27eb66456b4970a9a88a8d6e45b5ca96f2203ae01

- [T-1120] 択 (a) 採用 — main に着地した引き継ぎ文書の所有・寿命・回収を一体で定義する。定義が食い違ったままだと、着地した文書が「生死不明」… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2d919baed399b3905e6093fd0f536c9e665ef867f55e7679d95361fa617b9b46

- [T-1123] --forbid-worktree-handoff の help は 「README.md 以外の worktree-local handof… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8df986e206581f06330dc1d0231f813de1feddf1943162a1080e2023c53312c3

- [T-1124] DW-O20 は新規 worktree について最上位の git submodule update --init しか書いていないため、入れ子… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4c4ed44bbb2b83982abab2d57dea58636802c066c23fa0f1db2daec1d721a6bb

- [T-1126] codex 子の writable root へ job 用一時領域を明示追加して恒久化する。変異 harness 側の 「spec / ou… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 883c0ce60656a80cba57b67fd4b18c859ed0b9705226a595489cad1664d2de18

- [T-1127] run_tests.py の bounded local が前回ピークから 見積もる予算では cgroup attest が落ち rc=16… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bbc8ebf04756c3792abf65b839d76910dd95107ec54914a22ac337bba3e15c6a

- [T-1138] テスト実行器が計算ノード投入の待ち行列上限と 全体猶予を下位へ渡していないため、キューが滞留すると猶予を延ばす手段が無く基盤失敗になる。 本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a118c3cd67614832e191b3af2d498fa29c966a25612df35ca3110c474a0d30bb

- [T-1145] 変異 harness の「期待 node が pytest collection に実在しない」診断が、parametrize を持つ関数へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0d9f29d7ebbcd91761ae2045d97a40b1e8a24d063af99936e000fdc622541493

- [T-1147] land API へ段 6 の実施証拠を要求させる。ただし全証拠の一括必須化は過去形の wave を着地不能にするため、 **まず mutat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 47d5b15eaa8de2310773f6adf886514ad8924102376ba9b3f3747909b38601e4

- [T-1149] 内容が健全で digest も記録済みの attempt を、NFC 逸脱という provenance 形式だけで全損させる現行設計へ、 **… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 40f4825e7ccb6ef7434f942002302f8a3d0cd77e53c2b0a3363878402fb37e0c

- [T-1150] 変異 harness が 実行のたびに変化するファイル (dispatch receipt 等) を含む木を走査対象にすることを、 **禁じる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 02e878c8a33b4173a387934dc960c9d25307463c38341ddfb819669f2fa07bc7

- [T-1152] 読み取り専用の 計測解析 script は **repo 外なら親が書いてよい**旨を明文化する。[T-317] 裁定 (2026-08-10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 844def580658d2c6f46230f94ae2f9ea7e13cbe4cfccab7bbe93e286d5449cf2

- [T-1153] land 時の path 交差検査を tools/dev_wave_land.py の fail-closed 検査として**機械化する**。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f06879d837f3b6abe9ea4bf9c7be59ac4c620ee03400d3a8f672c5fdf3b346cd

- [T-1154] 軽量版 wave に 実装面があるときのレビュー段の要否を、**要る側で明文化する** (DW-C00 軽量版と DW-S06-A の 不整合… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f93a4fb747dbd0b848d0a177511e8a8e51e12d4153c589eb2a22cd6915d72f01

- [T-1162] 問い返しの前提だった「flock はノード跨ぎで効かない」が誤りだった。/work は lustre を flock オプションで mount… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 93c51338649cb56b087100bc2c168c4c3485746b979b97b0261809481d7ee60d

- [T-1163] tools/run_tests.py から dispatch の --queue-wait-timeout / --overall-grace… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fc2339ca183e6a05b852453004a38f51bc5e261c0beda73668c430a4149b7097

- [T-1164] test_dev_wave_wait.py の 3 node は 2da49c56 が production の mask 汚染を閉じ、_ha… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 725dd88fe1b16b40f5a6b3375160cb21e789136b87a0f1054b95773b55e9a891

- [T-1165] tools/dev_wave_wait.py producer が **pid file 不在を「producer 死亡」と解釈して即座に正常… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e016517469a4403ff933054c07adcf999e66c032474b1685a829a4c6ec2908c4

- [T-1169] 受入全走 2 回が orchestrator/tests/test_dev_wave_wait.py の**別々の nodeid**で 1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 208d087250fd047d7477cd355c6a7be4863e793a34e312bf60c86f5026dad475

- [T-1171] 択 (b) 採用 — まず発生率を既存記録から数える。発生率が未計測のまま上限を入れると正当な並行投入を切りうる。計数は既存記録から無料で得ら… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5eeb7182b2106b558118e9dc88dae32e5506c4febad6ffc7b1709879f9daf343

- [T-1173] 親 command は tools/dev_wave_wait.py acceptance で lease を release すると書くが、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bbe575c529a5becef0b9b1575614697cc1f6bb32f2fe8c1b6f6811273f3e041f

- [T-1176] role 応答の JSON parse 失敗への再試行。D936 が「D935 が入れる失敗分類の記録を先に運用へ流し、 実測を得てから再試行… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 45abdbca3bd1facbb7e5e47ed15975e091f9bbc1024fd14a89d78ebe98dc396d

- [T-1177] attestation を runbook の正規手順へ揃える schema v2 を**別 wave で起票して直す**。gate の受理集… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 90e9f54363b5ed7e63a135152dd1cb252555cedfa92901bfe48b9b9ac8022979

- [T-1189] land の採番順序は **現状維持とし、番号を参照する成果物は wave を分割して次 wave へ回す**。択 (b) 決定 fragme… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 39b024a0374e3c7f9d0247f7c40e2aca40627e0b3c5112010959f5a8c4d31fae

- [T-1190] 事前登録の例外型は理由属性を reason で持つのに、評価器側の分類は reason_code を読むため、当該例外がすべて blob 読取… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 43d34f8ba80ad58d138ab413acf715cb891f21e862f252aeb27a9374dcd5ad46

- [T-1191] session_meta 行が 複数ある rollout について、**完全一致する重複行だけを 1 行として扱う**。compaction… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: aa76d0af26f283296d577a5d6fa17d542a18e32b36d0dd81c76f0540541d9a96

- [T-1192] _session_meta_rows の decode 失敗と OSError を silent skip せず、**MATCH / NO_M… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: acb15b49626a7902950add371b8e552b44aba9d158ffcdb329ca55c80074b910

- [T-1194] F342 の恒久対応は **L2 節 (合計上限なし) へ置く**。択 (b) L1.5 の他節を縮約する案は、同族 docs で折り返しの変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 81599c9b6894095bc567e040a2dfaf9a98b22b3bf7f9a9f92ae631e3b89fd0c5

- [T-1196] **「判定不能」が 2 種類できたのに、運用者が区別できる記述が無い。** DW-O18 は「tools/check_acceptance_r… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: eef82023f5bc92ed7f5a2f1a259242158d0c6f11bdacb403d16bc739b4610b6a

- [T-1201] 評価器を持たない条件を machine_checkable: true にすると、原因は評価器 registry の欠落なのに commit-… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 96a085760cdd0d52ed227414dcd95d27c1abcb14a8ec7b733b8d9dac46b4ee38

- [T-1203] dev-wave docs の 予算は**機械検査への移送を主、別 reference の新設を従**として空ける。[T-508] の既裁定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ea7f1d5a4f2ecd8bf48108749c38b911a18c3401fba57c58b5f0cc50f17fe919

- [T-1204] 成果物を加工してから hash した pin を 機械で列挙する検査を置く。F345 の恒久対応は 現状 memory 止まりである。DW-O… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 46d2081e0a4bb49b851d256ae049476fc6ce7a4c697e60139af959f0697ede3b

- [T-1205] 受入待ち手の test_public_main_failure_restores_handler_without_release が全走 (1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7326da2ae6e675bc6a55f24a247b4904195bd758cad47fda58c7b781e2cbea4d

- [T-1206] 変異 harness の期待 node は --collect-only の空間で検査され、実際の照合は FAILED 行の空間で行われる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 151a81b3692bd37c255f84231fcc0c028bfb6aaadc0ae261b2daa7fedea648a1

- [T-1217] 変異 harness の報告 node と collection 実在検査の空間差を機構側で正規化する。詳細は F346。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 407cde1cd880c8bcc09c230c28d42975db6c5517b7fb563569ab754b499ed5be

- [T-1220] 択 (b) 採用 — 生成側にも範囲の事後条件とテストを足す。欠番を挟む同時ローテーションはまとめ処理の失敗として全 wave の land… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f80635db1e1165d486969ad07b4021581e3e90f74891592cec459f8069488aa8

- [T-1221] F347 の 恒久対応は DW-O02 へ直接書かず、**機械検査への移送 (主) と別 reference の新設 (従)** で 枠を作っ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3b485dc058d864bfe39f365a65788c42a3e20129a396fd1d5d66f9c50909c460

- [T-1224] 択 (a) 採用 — 閉包検査の判定基底を lstat へ変える。壊れた symlink を不在扱いするのは「不在の実測」を誤らせる型で、既定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d8fb24196a79673916ae3a05e4d997547627d8912763c91c0463c6066f67a8a9

- [T-1225] 変異 harness の _failed_nodes は **ERROR  行も読む**。変異検査は規律 2 の実効性を測る道具なので、mod… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ec7ffa46eecb4b658c9c53fb8cfcddfd82e44e17b9690dce616aa26dd3ba2048

- [T-1227] 「差分が 到達しえない path の赤」を構造的に非帰属へ寄せる (DW-O18 の機械化) を主とし、差分が触った file に限り 2 回… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c6e61e2712226b08ddc69d2a4b8dc3f15ba54b666e65f33432fe02507a3a3690

- [T-1237] fan-out の driver report と top-level stderr へ hold path・request ID・submi… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 21980d597be84d08e31ac385a8038f0ed0bc978f8e5bc3d49fa2b90891afbca3

- [T-1245] dev-wave docs の予算で滞留している是正は、**dev-wave 以外に正本を持つものは外の文書へ移し、 dev-wave 固有の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6f88f8963eca585ce9cc58c095539a69782b9e9a6d1b2b4763a32a5f7cdb7c35

- [T-1261] 新設した構造テストが floor_campaign.sh の unset 対象集合を「ちょうど 3 個」と固定しており、 将来 unset L… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5b5cdf9732c8cc2a67a90096d5e81d86ffee2e0f12e9f10885008b8543826dd3

- [T-1264] tuple(numactl or ()) が str を 1 文字ずつの tuple へ分解するため、numactl に list/tuple… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7d447e5e59172839452fdc688300095e79772d5f38f086ec4b786a551bfe13ed

- [T-1271] tools/mutation_harness.py の失敗 node 抽出が FAILED  行しか見ないため、fixture teardow… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9e729acc9f8aac844e90972263145f25272a304b1a79d01b1441ade51f12c4c4

- [T-1272] 同形の return-to-store gap が tools/mutation_harness.py:1076 と orchestrator… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7ee1803a18187acabc76259c8ee29d353dbcdbf24916942493169ceaa19cdeca

- [T-1273] 子への Web 検索禁止は DW-C01 へ 1 行で収容したが、 裁定が主とした機械移送は**未実施**である。tools/codex_wo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 75ca49b13a19c32afce96df0af0b74a1567cdd989675e961124e000eb580c1b0

- [T-1276] 受入 lease の claim / release / TTL 失効に監査証跡が無く、 「release が機械化されたか」「待ち時間がどれ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 74e84e12f0fd9b52f33c18466bdd7bf3415fdf3957df2f13da71646bbe973690

- [T-1277] 既知の land 再試行 script は rc を自前分類し、 終端的な赤でも lease を再取得せずに land を再実行する。自動解放… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4f93f5085f028ec484684a9a9aa56a5205b4e1ab454248d5b9a17fa5f260d0b1

- [T-1278] 走行形で結果が変わる テストは正しさシグナルに使えない (規律 3)。原因分離は諮らず進め、揃える方向が確定したら 実装まで進めてよい。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ad3c5a464effa7124bc969f26440342306e5dd61360c5c45f3999c76de44c875

- [T-1290] pipeline.evaluate を loop.run_campaign を 経ずに呼ぶ 4 経路 (screening_driver.py… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 129b29b940ce851d6dfd8181c57046bffd1d854f19f47505f8289aea3795bd08

- [T-1297] 退避 bundle の run 単位 index は index.jsonl まで作ったが、列挙・読解の CLI は作っていない。 親は初回の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 43876498a9d6f2d30729415501e88fe74c16263726c33d90c10f99dc1102809c

- [T-1304] 択 (b) 採用 — 義務を新設せず、段 3 の敵対レンズの既定項目へ「成果物が目的へ到達するか」を含める。既存項目が「成果物が実際に効く全層… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 82a8238436b6627ee4767d6b175790ffb97135b6a1e4112a8d16437d9c587da2

- [T-1308] fix 子への適用範囲指定は dev-wave 固有なので新規 L2 節へ収容する。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7fb1c60ac37b156a360e89d1a3e14ec4371e8ea4ae45ba22637a1a0710095ecb

- [T-1318] 単独再走の rc=0 に 「対象 nodeid が call phase まで実行され PASSED した」証拠を要求する。現在は rc=1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1a53188ea346a3616c3a07174e45efb6171e6bbaa0d5ffad579c46a82f46dc97

- [T-1319] 初回全走と単独再走の argv・環境変数・pytest 選択・scheduler を同形にする。現在は checker が PYTEST_DI… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8c75902fcf23899f6c9b83e2d7bc80d2a466609ff12e7583996a9afcd731aa57

- [T-1321] 「main で決定的に赤なので受入全走を必ず非緑にし、 受入は毎回 checker の非帰属判定に依存している」は**耐久受領証と矛盾する**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1610516166746e32ff9a55ebcb4be92e580164743974cd88b533d68eec3eef3a

- [T-1332] 同一タスクを扱う wave の二重着手を、docs でなく既存の起動検査ツール (tools/check_wave_startup.py) の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4dc0a030471ee6feb87a3194eb8185da16581f3bdc8c3fd3dafbd915a63a8604

- [T-1344] tools/mutation_worktree.py の receipt が local 停止の理由を分類できるようにする。現在は wrapp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5df7e2c61790519b01bf0878c8d4da4d91ae8d764bc4cf9bcf922fc8f39a7420

- [T-1345] test_s8b_floor_campaign.py と test_dev_waves_integration.py の成長比例 node を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 41e29803ca497ae747fb1a4543c7cf38534b07f63ba7a7e1142e9573f2c05ab4

- [T-1350] read-only codex 子の web 検索を **機械的に禁止する**。F217 の恒久対応は「子 prompt に web 検索禁止… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cb00ce1317f21e90381dd30a9a4486a5c0758d735ed07cd379392ff2f93ba408

- [T-1351] dev-wave 固有の作法なので新規 L2 節へ収容する。圧縮での捻出は exact pin を壊すため 引き続き採らない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cc127c1274660b46486bbf5c7c7e77a643b685a23cb73037f4fc852f0ab644c2

- [T-1359] ファイル数比例項は当面残す。(a) 恒久保留は、この検査が封印後の混入を見張る唯一の番人であり、 成長比例テストの恒久保留規律が想定していた「… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 478f1e42010ca4badc9d00d3b4067e0d202302ba3277d940b78171f612c143da

- [T-1360] 択 (a) 採用 — prompt 以外の軸 (レンズ設計・入力の射影・独立性の取り方) で多様性を回復する。モデルを増やす方向は採らない (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1c2eb33d8b1af7ee85f1b5b77c33cea759687fec52da5964e35145cbf5dd4eb5

- [T-1363] tools/check_wave_startup.py と tools/run_tests.py の診断文は今も git submodule… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: dc7a91fbe4a7f73d6f7dc4197d483529f4e9657c175737b1fa51b4cbcdd21751

- [T-1364] 層予算が読了量の上限として機能しているかの 再点検は、[T-959] の収容 wave の設計入力として扱う (単独では起こさない)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e1ef79c16859e1bacdcaec12e3174554ae348307e3e187d3c93b4db6648ec26e

- [T-1365] DW-C01 の 10 規則は予算 (残り 9 bytes) のため通る正例を添えられていない。 DW-S04 は gate の禁止に正例 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 100f6ab1d5ca7f311165525cb372703614fb1bfd974d7caafc41be9559974ae8

- [T-1366] 変異 container で test_real_repo_clean が実行されない。skipif は無い。実 repo を読む 検査を変異… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c86a388bd1bedf52e4bf2ff6319fe32c98889f41ffb85bfa84011b8c64d1af54

- [T-1368] 変異 harness の期待 node と xdist group marker の名前空間の食い違いは harness 側で解消する。 回避… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 746701ca587e638dbf7dd88aba55d1f71952fd4574c42a30902686886a0ddc85

- [T-1383] 受入全走の固定費 約 26 秒 (wall − real-repo 鎖長、 14 走で 20.6〜28.8 秒) の内訳を測り、削減可否を判定… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d37b983415586cae682e0cd547446c4ff6ffaa7ab0c4eea9dc9af58111a7c57b

- [T-1399] merge-message-provenance (tools/dev_wave_wait.py:3816-3825) は merge の 3… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d6df397a113a9f77abf293ca999d63adc878ca1994665f941647629d2b65fae5

- [T-1404] 当初案 (DW-O05 へ1文追記) を撤回し、道具側の実装へ 切替える。「症状 (usage limit/401等 exit code・ev… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5de063d73cd9c73572ff4b381f8441be87dbe1dc19586ca6d3e8a24adb1de7c1

- [T-1406] registration schema version を昇格する。 先に test_redundant_registry_duplicate… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 84687cd46b73569289e7babc2cfbcc604130f2a043e9a36eb2a268e3a0633d7a

- [T-1407] 独立予算審査を待たず、 dev-wave 作法 5 件を収容できるだけ上限を引き上げて結線してよい (D671)。個別の (a)/(b)/(c… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 44a01fdd7ef7ff864ee08e343ee166e6024b8b8218a0fc9b0677b9ed156d4671

- [T-1410] 択 (a) 採用 — 段 2/3 を飛ばす軽量経路を正式な dispatch 規則として明文化する。4 回使われた経路が未明文化なのは、次に使… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 852ef05fc86d3da745976ad71562f8f933d12088b11319dc9ebb35898361b75a

- [T-1412] 独立予算審査へ 回さず、上限引き上げを含む収容 wave でまとめて処理する (D671)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ec8e3c2b9f15bf90286f482fa151454925e6e50462cf15d8330384bab0bbd6b9

- [T-1413] (b) 採用。 分類の測定対象を本番 caller が実際に渡す argv (現行の --max-files=1000 相当) に合わせる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: dd44152dd6fb5ef36ce318127f22aee78ac5478c65efdabd9c466b1685c83f9a

- [T-1415] DW-S01 の前提実測 範囲の明文化は、上限引き上げを含む収容 wave で入れる (D671)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a7adcb027720d9c5ae0783727186179064df3a7b6cdc434548e32786fc042a7e

- [T-1424] docs/dev-wave/core.md の DW-C01「--laneは--stage consult専用。他段はrc=2で落ちる。」とい… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6d12b7b1ea3e35e08bd78dc34244830410d593eac2f88ec7d7bdfbaaf45e5240

- [T-1425] 新設テスト test_real_repo_clean (実測8.3秒、 orchestrator/・tools/ 全 .py を AST 走査… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 40bc9d69af2c4d5583795d686f0f081b8d0040dd83d02ee7d44c6f1854663215

- [T-1426] output/ のさらなる tracked bytes 削減。t419-probe-causality の path 参照対応、output/… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9c83cdb879b6f9056f7a56922aa1cebdfa0fab5159a1fc602da47a3fdb57281c

- [T-1429] job wrapper の durable checkpoint / partial-log 実装 (2026-08-18 に段3敵対相談がC… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a4f2da4e4c24ea3ee7f315ac49d378b8c51a1b59d07fd907be4bfab68a113bbe

- [T-1430] DW-S07 への 「fragment は最終受入より前に commit する」1 文と、段 8 の修正候補を次 wave の段 1 冒頭で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f9ca7ae8ca6da468072bc940da6d3cffbd3811cd28038f611eecb14668eeb4dd

- [T-1432] 択 (a) 採用 — 4 箇所に分散した会計証拠の検証を 1 つの判定へ寄せ、group name の束縛を足す。分散した検証は「1 箇所直し… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b786d2ed2d06c901403a33c9fd2b6fa386d9bd9eb937fc9fd30c955be242eb8b

- [T-1439] producer --check-only の 運用契約への結線は、既存文言の圧縮を先行させる必要はなく、上限を必要分だけ引き上げて 結線して… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 989a96a90bad3aaaec2eeb21cbfa3a33b5b9cdc85cff3750c67c0e007c49a6f1

- [T-1443] tools/mutation_worktree.py の期待node事前登録 (collection存在チェック) が @<xdist_gro… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2754196f51badf713eed9d63cbe7a6d6361afebc3c745fe67487e6d5428aa77f

- [T-1446] 予算超過で滞留して いた段 8 自己改善候補の束ねは、上限引き上げを含む収容 wave でまとめて設計し直す (D671)。候補が編集面で重な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 364e8e720f230fdb6c332d9aec67f55a1c533aa7e7c5f07e071caf7c188ff2db

- [T-1448] DW-O19 (段6の一時変異手順) の 「変異前をclean確認し」を、file 単位の差分確認でなく git status --porce… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7e2c72f0dfea993e3767d6a639f427fcd4dbf486720636218d4f042f4be045d6

- [T-1452] ## 総括 見出し必須の明示統合は [T-959] の 収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 658d9b955669c3091517186094ab6716cdebbc8d3765507a871acaae835f460f

- [T-1457] 背景 job で EnterWorktree 前に 起動した Agent fork (および再委任先) で Bash が worktree 判… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d8c19fbc71f674f89d51293212c834f8ef958c5aa84b9d324202d16a5a879f07

- [T-1459] dev-wave の codex prompt 構築 (tools/dev_wave_codex.py) が、plan/consult/aut… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8d41b2fbfadb502634ad1187fc31d24122fc02f53422bf4b1630e1619f5f82b5

- [T-1460] 変異 matrix runner の除外条件の追記は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b116b24490993089d1f045d3f2dd0ef1ad1e4cd8bdd9bf1536b2364e68c85e99

- [T-1465] docs/phase3.md 見送り台帳の [T-1090] (1 dispatch job で複数node を扱う設計、有界並列化の 不採用… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 927ccc417b4f629343451c4ad7b370ed0e5dc01256113283b1d255d592ba6207

- [T-1466] /rulings の収集 手順 2 件の是正は、上限引き上げを含む収容 wave で入れる (D671)。 収容先の .claude/comm… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e9f3883b83cb1a990ab719ac97048557ecc124f808321ada064c9c16704f64ff

- [T-1467] 択 (a) 採用・分割して実施 — 恒久保留 59 件を個別レビューするが、正しさの関門付きのものから10 件程度ずつ行う。一度に 59 件を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4988d001ed3bd76e4fad140695d8814eb06fd0aa61eb7d28d29793117b888d86

- [T-1471] 受入全走の xdist collection 固定費の 現在値を再測定する。2026-08-18時点 (12951件・単一process 4.… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8b04245471d0bfb887231a94c963dffb29f848570356b890e32408686ee9e4f1

- [T-1479] 探索目的の全走も隔離 worktree で 行う旨を DW-O20 (984/1000 bytes、空き16 bytes) へ追記する候補。d… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2be06f0a508b611fa7910f30d34fffce06006f856d65340b8e69e3b95adf8374

- [T-1485] role 呼び出しの retry=False 実装可否を判断するには、fixture provider ではなく実 provider (cla… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 35c491662d9a9866f236bdb6bd99207fe2e9e5bda427ddfb39df1583f6c5d80f

- [T-1489] reasoning-pin の authority/admission 分割、 detached mutation の実 detach、mut… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 94ffba5b99915cdd05e71238ee9316d728629a30f6d9e27557bab919e694386b

- [T-1491] _message_file_paths() (commit前preflight) が本waveと同型のpairwise-intersectio… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0103e38dbea9d581646538b1b913f5edd3d9ef1d0c726814452c6b09cd10ce82

- [T-1492] tools/dev_wave_wait.pyの producerサブコマンドへ、poll loop到達を示すreadiness marker機… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 66ef3759e2e23c01ad02dde030cf5c8415a44e7e0a7f4f6b6fe1b10f4dcc454a

- [T-1493] test_s8b_floor_campaign.pyの build_cells呼出しの区間別計測 (cache lookup/実ビルド/val… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b0e12b17f7aa803f4869a8b0e86938694e5862753e74640bcedb2e129830ddaa

- [T-1494] test_real_repo_ serialization.py::test_real_repo_priority_order_is_lite… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 452570254e15ce297106b24a1a8202bbe2eaec5245a39f29cf598f943b492c17

- [T-1496] 択 (b) 採用 — 当該テストを growth-test hold registry へ登録しない (D845)。 再訪条件 = 実 pac… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d6b33cff679cfc89c282d7dc8ab670ba7647536f0626ab5738785587c1d26ec6

- [T-1497] 恒久除外集合を task-run receipt / aggregate / acceptance launcher receipt へ証跡化… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3610f2854ab7fdfcaa183a47a2bbd1684db867d934c8809c6c57c9c67e45d973

- [T-1498] 変異 harness の 焦点走対象に、入れ子でスイート全体を subprocess 実行するメタテスト file (test_growth_… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 89ffc3e5dbde361814692b6f0fdc8832e2022e6b78fd52c54b48be2611298de1

- [T-1499] masstree の config.h 欠落が 解消したら、tools/run_tests.py の恒久除外表から該当 entry を 1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: dc9a32058ece1287cf81169e7ca84bbd63ab1bb0911429613d062659132c8fbc

- [T-1500] 共有契約 module orchestrator/test_selection_contract.py は production module… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 03ce4ea3420fa906d86574602ceab8057670c18923fb2cc1f2ed427c38fa8159

- [T-1501] F373 の恒久対応 (FORCE_COLOR/COLORTERM を外して起動する) は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0dc07c998737b5923c901f91e56dc447f8081c09bec8b4730562f1494d5b323b

- [T-1502] 自分の変更に起因しない受入の赤を dev-wave で直す。対象は 2 つの wave が独立に観測した 27 件 — test_sort_s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: daa8969a54409d247ccbd13fd2810453936027420ba91a0533f285c0bcaaf4d9

- [T-1503] 受入の親子が互いの完了を待って停止する経路 (F466) を塞ぐ。結果の読み取りから完了通知の 送出までの区間を try/finally で囲… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 915dd8532269ffafabd7f7547469f8eaa6e845df341999ba516b28eedbe800e0

- [T-1504] 赤の帰属を判定する検査 (tools/check_acceptance_reds.py) が、受入が成功した回でも 41 分以上を要する件を調… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9f9835d8b84fb89a87120caacb577b25a09bc26b92ac4d14fbf28652f509c0eb

- [T-1507] 既知赤と判定済みのテストを受入の実行対象から機械的に外す配線を入れる (D679、D678)。 現状は各 wave が実行時に個別指定して回避… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a201532ad8b99c4daf3f5d62774d868cfbf403220ec14cc669924666d8a279ac

- [T-1508] 赤の帰属判定を**全走差分方式**へ作り替える (D680)。 probe 作業ツリーを廃し、tested main 側で全走を 1 回だけ回… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5cdf22e87cf21bff96c56878934ec24f090376f868836bb6e9194ae97797573c

- [T-1509] 段 2 / 段 3 の reasoning effort を docs pin から subprocess argv へ機械強制する。現在 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 23d0fd4b986428d6db83e763240912df6c1ff32dcb99ec3da7bab3ae5fcb4674

- [T-1511] 非帰属 probe の worktree 再利用を 実現するには、まず「probe の状態隔離を何によって証明するか」の設計が要る。 work… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 229a249f84448d5597536621ba4f155632f57ad885f73b1239527509fcc7cb6c

- [T-1512] worktree 再利用を維持する。非帰属判定の並列化は同時実行数の上限機構を新設することになり規模が見合わない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4ef9c8419badeecf7dc5e777239709dc8279ad6fe33cd44346c10e85bcaf1ad8

- [T-1513] 非帰属判定の所要は **目標 3 分 (計算ノードを全力で使って)・実態許容上限 5 分**とする (D726)。畳み込み単独の 26 回 →… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 706d3e9264fdd28c5e1998a91823e5978a951f2ae46158d0f903225249ef14f6

- [T-1514] tools/check_acceptance_reds.py の _authoritative_command_stdout は、dispat… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7aaf6a23350115ca475bc795bbe6c3cabd63fec8af250d427a39ddde28c73cb1

- [T-1515] red-check receipt の schema 変更は行わない。 分割取りこぼしまたは空結果受理の実害1件で T-1570 と同時に再訪… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1b13d41e3c7039d2860e5ef0189354fd67600e437a8bae7057d434e092fb26ab

- [T-1517] 全走差分方式の R_main は tested_main の SHA だけで決まり wave に依存しないので、 <main SHA, run… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 236af5c63447334f29cde2575cacfa81aa6cf0c6ea10fa2a388f611d5cfa7525

- [T-1518] D671 の下で入れ直す 2 件も、まず [T-959] の L2 経路で収まるかを試す。収まらない分だけ D671 の引き上げを使う。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 83c17f4d2005680d1dba37b79976fd0d6f51a8ae690a27cc3c02492b53dbd279

- [T-1519] orchestrator/tests/test_dev_wave_land.py::test_exploration_external_roo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d74b9adda617891e6a99014e09bc717a5a65987f9206bc4860a948c2fc17540e

- [T-1522] 全走差分方式の tested main 側の赤集合を <main SHA, runner 内容ハッシュ> を key として repo 外へ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d3316ee3285972ece1ca7b5d478f0f16a1de28a99a82f95ef5a26d7fec22dc5c

- [T-1523] **production が pin / cache / 索引を使う経路を、テストだけが素の全走査で叩いている箇所**を 横断で洗い出し、受入… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c68bda14e5a5256c358564c098ef9aa53ae0655f691eaa5eeac96532f744c61e

- [T-1528] --attempt-out / --wrapper-attempt の runner-mode 依存の是正は [T-959] の収容 wave… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c342a7a746ff25d182f7d42afbd2706d7d1ba575f683b1136958433ee4839432

- [T-1530] 択 (b) 採用・現状維持 — 未取得経路での判定なし再試行は許さない。受入の排他は結果の意味を守る仕掛けであり、緩める側に倒す根拠が弱い。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2605909934d3eda73535f82f6bf7566be3a274716aa88a8dbd9da56d834fad6a

- [T-1531] 択 (a) 採用 — no-op になった 2 引数は稼働 wave がゼロになった時点で削除する。何もしない引数を残すと「指定すれば効く」と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0e2b5002cdcf3dde236850232ed4c315dcdc71409384793595f70bb53ee9b86f

- [T-1532] 入口 command 段 6 を、no-op フラグ名でなく 「lease の取得可否で受入投入を止めない」という条件そのもので pin し直… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9231a1d5cd8b4880569d30e538e24e3206fc6482a40a8a78a9ff30a26345cf38

- [T-1533] login node でのみ再現的に落ちる test_exploration_external_root_keeps_wave_clean を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1d43066a1f49b891b711c9b4fcce263eb5be73a8de1fe17c499d0950d57e59a2

- [T-1534] claim が holder に自己 digest を返しつつ holder_self:false を返した場合、受入は未取得として進み le… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4837ecd2e602069d5ebecf5b315ce996922dbbd11d9dfc27a4bc29111c4740ec

- [T-1535] 「変異走行中に tree へ書かない」の追記は [T-959] の収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 64b0e4a51f821068e54a35477c1766702083a51d010fc0fea600ec1032950e0e

- [T-1537] 択 (a) 採用 — 追加時点で重複を弾く関門を作る。D99 決定 1 の閉じた CLI 集合の改訂を含めて一変更単位で設計する。11 日で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bf00ea93d424f045709d8c0e7c7075b67a032132aa285e306dfea21d9cd80beb

- [T-1538] mutation.md への追記 2 件は [T-959] の 収容 wave で入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d4163d574262d2fe5848f0d12709c33b45a3b899e9abe78f9c1de513dd8526b0

- [T-1540] _validate_hold_rows を拡張し、barrier_nodes が保留集合に入っていないことを既存の import 時 enfo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ab930aa7b99037064307ee776bb3f530539af6d7d48d75869cf1ef4ed5d55662

- [T-1541] 変異期待 node の正本と 保留 registry の整合を機械検査する。本 wave では 7 件の矛盾が人手の読みでしか 見つからなかっ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cf07478e0638b935b0ad2bb28b0b7c5670f04a3d66a8cd1753401c53bb18e37c

- [T-1542] 択 (a) を警告のみで採用 — pin 無し全走査に上限は設けず警告を出す。上限は正当な走査を切りうる。同じ探索関数の伸長 (セッション記録… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9e807d94a717da97599f0c9ae9dd4c811acb887c144d034c496254f12d5985cc

- [T-1543] L1.5 満杯で入らない自己改善候補 5 件は [T-959] の L2 経路で収容する。予算値の引き上げも routing 先の変更も単独で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 2792c73bb55d114d444e03e7ac69fddbe127bcf9cd8302f2ab05b18f843e5cef

- [T-1544] 予算が空いた時点で、 親の焦点走を FORCE_COLOR / COLORTERM を外して走らせる義務と、親の実走も 終端マーカーと終了 r… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: afdb32fd98a33a87769b9d9909e6448b868a32f612d4be89ff2ceb68dfcbac75

- [T-1545] 変異まわりの手順事実 3 件は [T-959] の 収容 wave で L2 節へ入れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d13c992a3c664b7a217635375fb330488e4b393e569eaffbfc0b50cdf9b7931f

- [T-1550] 隔離集合を acceptance receipt へ束縛する。 現状は走行末尾の IZANAGI_FLAKY_HOLD_SUMMARY_V1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0db9b168a3237d5101bcde4562148c28fb00c80477d7954706691eae9f712fee

- [T-1552] 失敗 digest の byte 予算は上げず、**捨てた分の manifest 実体を記録側に残す**形にする。 予算は「記録が無限に膨らま… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 772eca16ce6e1eea4715fcd397c152bf03383aadad47f2a0d3eaadab00326f2d

- [T-1553] 準備区間に物理 hard cap を与える。 現状の準備上限は既存 wall 上限と同じ polled admission 検査であり、imp… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 03f38996ea04d89015283852607e204deef632f51506baf310c70d137bc46146

- [T-1554] 並行セッションが F57 修理で 23 node へ入れた max_wall の引き上げが、準備費の控除後も必要かを実測して戻す。 引き上げは… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4cfe394be65164e2dfea3f4e4d4885cd960d1cfdaa3029fafd7e995df07dfaba

- [T-1557] nodeid 正規化の非対称は harness 側で解消する。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f4c8b5f0684e8f37f0c8b58572eabfb81a1d1094a71eb156f10ed232173e935d

- [T-1559] 択 (a) 採用 — land 後の記録 commit を段 9 の正式な遷移として許す。中途半端な撤去の残骸は全 wave の land を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5b566d0d070316b9d8f7fcbba3fb496b812b0e1b998dfc74bc46f9c01cc457b9

- [T-1560] /cleanup-branches §3 の撤去順 (branch 削除が 2 番目) が本 wave の順 (branch 削除が最後) と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9474a9ad3c2a7ca101bd0e17ae29429281b123785c0b840cbee3f8384a2fcadb

- [T-1561] codex launcher の evidence_status=invalid が 健全な成果物を not_accepted にする条件を特… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1c859f0b84329e55632c14d8a7a93a064ea6feb8716f83fbb767a2792b0e13e7

- [T-1562] 既存の worktree 31 本・branch 114 本を 掃除する。zombie 修正で /cleanup-branches §3 の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8d3440b8e6913e3311dae6651e4d21181a0771d27b25224634cfa099c886b6fc

- [T-1564] verify_snapshot の呼出し扇形を縮約する。 1 node 内で 47 回呼ばれており、内訳は fixture 2 / super… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 57425c2d4d027d9ceaa970fecacb78bda9758e9f7a4d05ec9139700fc64dbdcb

- [T-1565] real-repo 鎖の 2〜4 位を含む test 構成を見直す。 いずれも同じ module snapshot に対する closure… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3adf591b5bd711358cf4963dd3cb4021e849fd9cd7b7339475adeb0636c3e4f7

- [T-1566] group 注釈付き node を期待 node として 扱えるようにする。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1865e7a36bcef5409d7147d195bf4e7b63e530fb0c791c83f532cea52f647549

- [T-1567] 択 (a) 採用 — 第 2 の直列鎖の内訳を測る。ただし D820 が分割数による解決を退けたため、本項に残るのは内訳の実測だけである。単独… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0fd28ef9f2dc7666d41d3bd490e9e86449f9d050c6747494d97e0f748654e563

- [T-1568] 自分が原因でない決定的な赤で 塞がれた側は、**所有者が修理中であると確認できた場合に限り一時隔離してよい**。 隔離の理由を「赤だから」にし… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 376f64491871c98a52fbe9c0a96bb511575a6cb734dc9bca288a9bfc7e07a67b

- [T-1569] orchestrator/tests/test_dev_wave_cleanup.py::test_landed_attached_workt… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c97ee29ee6b3dca98132dd357b8d2325515cc8c769a0ed9bc01ed8463c1702c8

- [T-1572] 実 tree を snapshot して不変を要求するテスト 9 関数 / 11 node と、基盤が repo 内へ書く path を突き合… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 93d31ee1ee1a9c1762c9a0d548ddaae6f9281a13627591b67928316f8bf18152

- [T-1573] shard session directory が走行後に残る。 1 走あたり約 15 MB。land への影響は無くなったが、共有 file… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9501527155f06f804eba54494e907378e34843665a95c04a257ee25a75315376

- [T-1575] 受入 lease の排他範囲を他 wave の codex 子まで広げるのは**当面行わない**。排他を広げると 並行度が落ち、それは今まさに… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1cca821bdf4ae258878310bf4e2f2b11add08a1121937c994800fbc2a842516d

- [T-1576] 使い捨て worktree に生成される「proof chain ではない campaign 形の runtime 出力」は、 **campa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a204a158fbd5c84dae2b138e815e7083cffe5c94c6b103dfdbe71fa3a011b831

- [T-1577] failures 台帳が「裁定パッケージへ送る」で止めたまま担い手の無い機械検査の新設 3 件を **1 回でまとめて設計する**。(i) F… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 54c771d6c92f8e6a1622e4c28d54defe4b8f802160ac316420bb9f5afb9bcf91

- [T-1580] tools/check_docs.pyの DEV_WAVE_WAITER_DISCLAIMER_REが英語語彙 (optional/manua… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5e0bc07ec1f696d2c01bb8cb2999787dca034768a8c51a403cb89ea07993fb7e

- [T-1581] tools/codex_worker_launch.py の _evidence_status() が invalid を返したとき、どの条件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 18e8ede91bd9c5d2772e4ad29f0eae30cab95551b2dec06f3a28b78513ae2eef

- [T-1585] collection 環境の対称化を先に試み、費用が見合わなければ非対称な走行を不適格にする。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9deb73cced9035c21457865388c7d0731501b6d9c6ba29b2384bbb48270e5156

- [T-1586] 正式なテスト母集合の権威は別 commit 由来の台帳へ置く。実行時の inventory は環境で揺れる。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b9b714b1888336796db6946c03a841fd4f0887ecbc3ddd88a3e07c7c0e0c5335

- [T-1587] 分割の片方が早期 infra failure、 もう片方が既に RUN のとき、親は worker を止めるが PBS job は継続し、回収… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 85ef59c9a1ab73d1328bb6c41e990af0969cb3fa6d74938781f61adbcd4f1924

- [T-1588] #PBS -b 2 で 1 要求 2 ノードを取れば queue 要求を 1 回にできる。現 dispatcher は 1 ノード・1 結果・… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 83f0bb741befaaed4163de81ddfda5f2aabc3c83df38aa3b15d07a52aa5b9884

- [T-1589] 負荷に応じて K を動的に選ぶ案。**2026-08-26 の実測で「K を増やす方向は 当面効かない」は失効した。** 排他鎖の細分化後に測… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5f3724a94f5d88dae30f80c367184afd50afb78cb57105dc8950918fd4bb7329

- [T-1595] 欠落 2 件の 収容も [T-1639] と同じ手順で AI が判定してよい。(ii) は独立 3 例目として例外の要件を満たす。 正本 =… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 51202ed69cd5a648a257cc22385520f47e784391918a68940de8e2d14ab74fe5

- [T-1596] orchestrator/tests/test_dev_wave_land.py::test_exploration_external_roo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b7a6c873c80f7744b61c51ef80f7b9a89125df0716ea5e81c803e4858acd1c66

- [T-1598] 段数上限ちょうどの前方取り込みを、topology 検査だけでなく land の端から端まで (再演・lock・provenance・ff-o… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 363f01636efa89ab82f8219eb83408f1d52c1a63de1fb476bf330988449daae5

- [T-1599] /rulings の land 直前に、**裁定本文が根拠にしている事実がまだ成立しているか**を照合する 手順を入れる。現行の防壁は spo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 71e2896887501b2772fc597822c8b25d1d47d896da754c1f64c529faccbc4b9b

- [T-1608] git merge --no-edit と git revert --no-edit が trailer を 1 行も持たない commit… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4838e706a952dea04397b9f8fbf036c21ea0e5d37e15ebbfb45ec0ed9669a21c

- [T-1609] output/insights/**/*.py が実装面判定に 当たるため、解析 script を insight へ置いた docs com… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: be863177d04ed585404c3ec9d823606e4757d8a31676734974ca08f3b61ed802

- [T-1610] real-corpus テストの fixture anchor に、 既に完了して archive され二度と実体更新されない task_id… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 16b0672a2cb2d0957c4a5d4b4aba1f4addac1a99a27d0ff52f6f2bfa50e22028

- [T-1612] Codex dev-wave skill の 4 命題 (.codex/worktrees/ の配置と再利用契約、隔離 codex exec… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 67f91d65b1d244cc8c5cd17502d85a092dd342684e1504e3aa69012b9782172e

- [T-1614] sandbox 化 Codex 子が .agents/ へ 書けない制約を dev-wave の reference へ収容するか判断する。本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: aa1a388b7c677748e122d306dc6db0f93612e83ce85f3b209745d7ccc6d60082

- [T-1615] workspace-write の Codex 子で evidence_status=invalid が再現し、read-only では起きな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3d8242b139ebc475140c51e14b1ea0538e9226796938021f235fae3e12fb8710

- [T-1619] 受入の高コスト側にある「同じ前置きを何度も払っている」型を共有化する。 s8c predicate 族 (test_current_repos… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7b2c07bac0cd11ad834708def4b8d55b54871fa80c759532c310e00c22434e1f

- [T-1620] 所要台帳の定期再生成の運用を決める。 被覆率 gate が 90% を下限にしているが、再生成の契機は誰も持っていない。 値の精度は要らない… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7aa558f32b36a29c28b7f3e65a51d9f43c821069abc0399bfd293383f7e71352

- [T-1624] ungrouped node (1 件 = 1 work unit) の 順序依存を測れるようにする。現状 targeted の AB/BA… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f2e244855729c465b61f9c1f8ba60f1a432a2e30d4f8c8915cc7bb68f17babfb

- [T-1625] 実 repo 利用 node の直列集合への 登録漏れを、共有 submodule の checkout 経路以外でも機械強制する。現行 gu… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 578910f318bc73fb58eeb047f97d84bd175a91fe7c2e56aaa37618d4aead2eae

- [T-1626] 43% を 現状追認しない。correctness gate 付きの growth hold 34 件を対象に所要と重複を実測し、戻せる分を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: de2ce06d6da86b77ba4e424168365f9151a23a52dc7d386ba9b222e136bf6159

- [T-1627] worker を跨ぐ overlap 依存を測る設計を立てる。 共有 submodule の apply 窓、patch lock、tmp 上… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 14643ecd58edeee8f770b3995e452aacfd8b3775dc8a22245a27e536d7960b01

- [T-1628] 受入投入前に HEAD..main が 束縛対象の実行体 (待ち手・launcher・runner) の bytes を変えるかを検査し、変え… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 135f89129fe120c931ddabc46879c267afd375b6b6dc432e8344c948fbee0835

- [T-1634] docs/handoff/ の 残骸棚卸しを本セッションで実施し、**9 件すべてが台帳で終端した死んだ wave の残置**である ことを確… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 94b725afbba43ffc422b72e81756488598c4099b76934d39c9d746fa7e129212

- [T-1637] repo 内監査が報告した到達不能 30 commit (probe・TEMP・superseded 由来が大半) と、上記 2 branch… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bade63cec993a4a0e4df8a9d31fb6163cd7491c46961badd562295c54594e606

- [T-1639] DW-O17 への 統合は D730 の手順 (既存記述の削減 → 独立 3 例の例外収容 → それでも作れない場合にだけ上限引き上げ) を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d304a1c551b8bc791a78937267066636156c83ba8264e9a3bf8635e39bec7bf1

- [T-1640] 変異 harness が xdist group 接尾辞を 正規化しないため、group を新設した wave は KILLED 判定を構造的… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7e372ac0e89724363ce671131095dc61db25c3957f88889bc450414cf528d92f

- [T-1645] DW-S05-C への 追記も同じ手順で AI が判定してよい。「予算に 137 bytes 以上の空きができたとき」という再訪条件は D73… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e91fa6ee0a6841c9bdf12cf5c7d040791f50f6738cc3840f5d548182998de408

- [T-1646] 重複測定の基点を DW-O18 へ書く案は、事故を伴わない 1 例であり D730 の原則どおり 実施しない。実体は本エントリと起票元 wav… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 08a800ce1771058432ed1d7e6f96b36fc9d8bf056d43940f0bd082e489a98a6f

- [T-1649] launcher テストの時間予算を、attempt 本体の時間で測る形か固定費を予算から除く形へ直す。 予算の一律引き上げは採らない (暴走… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a9ed645acfb5fb77f1233e835bc1153e85e5a20753b3475869a717cd4eb55ad8

- [T-1650] 着地済み branch の削除を承認する。削除直前に branch 名・先端・main 上の対応 commit の一覧を保存し、内容一致と占有… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1c7b6f4023421b82682a7359581f2c09a8193a7c56785c77b61174c47e243edf

- [T-1651] worker_collection.index() を O(1) の index map へ置き換える試作を作り、現行 K=2 の受入全走で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3f08ea051ed9e97f6433bc50bf0d85688f127599b8dd075c2bb2b7917222b8a2

- [T-1652] 同一の slot probe 数 (104,654,278) に対し collection 順で CPU が約 2 倍違う機序を特定する。 候… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3d40680839514896b6172139d46dea269fce62dd34952a0fd1f49b96d604d6c9

- [T-1653] 択 (b) 採用 — 当面は閉じたまま運用する。該当 30 commit には親が直接 merge する 1 commit 限りの例外が確立し… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d3ef413312355ed5f47e39b6de574764dc81a836eb0649a527fcbe726d85751b

- [T-1657] hooks/guard_bash.py の head 判定を是正し、直書き形と shell 変数間接形で判定が一致することを要求する posi… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ffa8a280a46292ffb7865b4502c0db702e6b73b8c238c5c738ad795b167df0fe

- [T-1662] PR 2 本を送る。内容は 2026-08-25 の択 (b) のまま変えない。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 06e2133d28d60970b65f0d4b2c9e6f485b90393e2ba21c8bfd21456e5ce8e3a3

- [T-1663] 実証済みの範囲で射程を確定し限界として明記する。一般化は需要が実測で現れた時点で再訪する (D916)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d7fef589916bb082c078366d1bac7f0a10158e14f1c7ab6d8ece82bb9c047d37

- [T-1664] D821 の 3 択のうち説明を狭める 案を当面採る (D839)。可用性を捨てて閉じる側単独は不採用。 予約制と全層同時切替は別枠で起票し、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 89b8fbdbe56a1893baa8cc0d879e8cd5bfcaea1ba272064dceb349b4323e4dde

- [T-1667] hang 変異の timeout 後に計算ノード job の終端を 確認できず orphan-hold が張られる。hang 変異用の走行だけ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 76c40a968804774cc59aab09ad3545c126961d5ef84b2ed32b87f8f6120ac1f6

- [T-1674] DW-O01 の effort 記述は plan / consult で実測と逆であり、誤記の是正なので D730 の 原則落ちには当たらない… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 921520b7588e8fa08b21c0f7b66ccf6259d81f61dfb518ab51c4082cd0e00f3f

- [T-1676] known-violation の 群別件数を受入 receipt と land result へ投影する。D800 が「群の値は rc の入… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ec47612ac36b87100667033cc8a601653525d6aeb297a28dc7a94e8bc4712b84

- [T-1681] growth-hold 側の worker 経路 stale 検査に 感度 control が無い。現実装は静的には検査しているが、_is_c… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0f4296e8b117a3acffed4a5e167e8ba7cc8f6aef0e60b6f7fb21377a6952ea75

- [T-1682] suite root に別 target を足した上位集合は 完全 collection と見なされず、stale 検査が発火しない。coll… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 294615f66289c75d98adcf6679131d6ced788f6ee0961ae8e339469cd397a769

- [T-1684] 受入 shard 経路が output/task-runs/ と output/runs/ へ書くため、_real_output_snapsh… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 30fa38885de250d994d831c2a58625761bbb7c844c9b1c9a0a96adbb624b8bbf

- [T-1685] evidence_status=invalid の第 3 の原因を 特定する。web 検索と非 NFC は本 wave で反証済みで、最終 a… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9b3e54b0bd2247bbfe440bed42523a72fc4101d2d0c3ec49d3eb15a3a938ea07

- [T-1686] 択 (a) 採用 — 繰越 fixture 5 件へ段と担当を個別に割り付け、完了判定へ配線する (D844)。射程の訂正 = 三者一致は D… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 50113b63fa377336eb4121bb668a16d82cdc89cc20eecf12c721e23c267cd9a3

- [T-1687] 繰越義務述語を段 6 候補提出の前提関門 adapter へ結線済み (D946)。残件だった operational caller 0 件に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 15587f446af9c91e23bf107be757acd1e242e9436f8ab46380a6da81006163ae

- [T-1688] 択 (b) 採用 — 未裁定側へ揃え、当該 1 件を改めて裁定へ載せる。pin が resolved であることは「誰かがそう書いた」以上の意… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d67136988e645fcd74a6513887c02b33e50f6d911412221816b215ea391b0051

- [T-1689] D752 (2026-08-24 ユーザー裁定) が定めた fold 適用後 tree の land 前関門を実装する。fold の決定的な… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0a7c229ded5d2fa516e22176571075e95e31f8fc98d460a3e46a28ccc1aa87e7

- [T-1691] K=3 の実測は行わない。D820 が分割数の増加を既定の手段から外しており、実測が良い値でも採用経路が無い。受入短縮は node 単位の費用… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: dccbb1e19ae35d7696b8cb92cfbd700dc048f910154e5ce46c16db514c058152

- [T-1692] orchestrator/tests/acceptance_duration_ledger.json を変更後の実測で再生成する。対象 nod… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9aaccfbd2c8ce5b1e4dc3d06a6190661c142a67c48d8f9cc6e1431bcda49df74

- [T-1693] shard wall のうち test phase に入らない残余 (12 session で 57.34〜93.00 秒、critical… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 48cba42b96b67831b71f58e97e77e13a01fd828fd8b85e45547524eaaaf5a13f

- [T-1695] main thread が pthread_exit() した後も 別 thread が実行中で cwd を保持する thread group… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 46e4cc02e28511bbad2dc97745ec1e1429ecae9d40d4e023e921f1a1cd9e6f84

- [T-1707] tools/mutation_worktree.py が 使い捨て worktree で外部 benchmark の submodule を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4b15ca169a660a0173df1c66057d7129cfdf1120740053e45ef905375f52ee5b

- [T-1715] 新規 worktree の初回受入全走は output/runs/pytest-launcher-failures が走行中に新規作成されるた… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e74911e245f564fe9d4a2d24b2682ab0e9b11056806e4a2fe6d4e00b0903f448

- [T-1716] docs/dev-wave/** の L1.5 予算に 安全義務の是正が入らない件は、**D782 の手順を AI が適用して閉じる**。 d… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b2cc40435d5682b50055a340adcb862f987f5d35c370d6df56a532cd499960a4

- [T-1717] 証拠が無効になった理由を受領証の attempt record へ 1 field 記録する。本セッションの author 子 1 本目がこの… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 645a5dc1a7dd684ccbfbcc7f1fcf5a702d35111444401e2e662e6d30f8eb0a6c

- [T-1720] 段 8 の自己改善 2 件 (refuted の 2 種を分けて書く / fix 子の担当所見を prompt 本文で列挙する) が byte… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7e69b28860bf20c08195df052d0b1608d28bd8ea56698c98792ef7791605218e

- [T-1725] docs/dev-wave/** の 層予算が満杯で安全義務の追記が入らない件は、D961 が 手順を定めた。予算のために安全義務を削る選択肢… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b1b4f15afac3cfd40ce98748deb6a942228d420a524e24e211fd5356d4693036

- [T-1730] DW-O01 の「採用は check_codex_output.py の rc=0」は一文だけ読むと十分条件に読め、 本 wave の親はそれ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b8dfc35c435e6421caf000878fff034422e3fd28716fd43a08bbfdd29fb953ef

- [T-1734] 新規 F を要する決定的な非帰属赤は、 **保留の登録簿が未着地 fragment を証拠に取れるようにする。ただし採番・正本化・有効化を 着… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d5f3053b201011f1327fd0b7b988500be9071fd71cccc0e473e0d111ee07f71c

- [T-1735] D690 の 5 分は **計算ノードの順番待ちを含めない。テスト実走と帰属判定の合計を 5 分以内とする。** 診断のみへ狭める形も、順番待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 33f1d21c0fad1568f1dc1288d648d28d80c4ca2695b9db9977aa19838b219218

- [T-1736] FlakyTestHold の cause は **自由記述を権威にせず、独立に検証された分類の受領証へ束縛し、受領証が無ければ 保留を発効さ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d6939d495db2097d2579e9ab6c4230058de8cd06d85cc535c350095a54067be0

- [T-1737] 「予算に張り付いた対象への変異登録では変異後 bytes も赤理由の層に数える」を DW-M01 / DW-M04 へ統合する件は、D961… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1cbe9a4f6e4bdea6befff19ad984b691594a34d94761ceba71a864777681ab3a

- [T-1740] 「実装が production 経路から到達するかをレンズに答えさせる」を dev-wave の正本へ入れる件は、 D961 の収容表へ載せる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 62f8796745992bad6fc147e788bea57a25f22132e68fddcd4fb325b026d0e3c8

- [T-1743] lane と model の束縛を外し、 旧値は読み取りのみ受理する (D1085)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cf134f06c3fe407fde5f2079b52018bfe7ff91fd4a777b0ac5ba135e168f8c1d

- [T-1744] /rulings の収集で、前回セッションが 残した索引ファイルを差集合の母集合に使わない。本実行は前回索引の 102 項から採用済み 92… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 01dd1e106e927413ed6031b84ea3667093a81080f4e4293c89ae9cd8f00e7610

- [T-1746] 受入 shard の残余 (pytest wall − pole、shard-0 で 62 秒 / shard-1 で 47 秒) のうち、w… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ea694c418aa13547211bcfb8dfae6912965650b50ce906169216ba632bfcd5b1

- [T-1747] login preflight の全史 provenance 監査 2 本の 冗長は**削らず現状維持とする**。速くするなら、取り込み差分だ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 836f71f3276bf93b00902b4663dc411b5f6b1c90189203eb7522d05a02ad3e0e

- [T-1751] landing tip の実行器が受領証の 検査対象外である件は、**取り込んだ main 側が実行器を変えている場合だけ受領証の再利用を 拒… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 704ba5590b0e250be3f9bf2781b104f6444bd5f2001f28ad267c790df8731fdb

- [T-1753] /cleanup-branches §1 へ監査の所要時間 (1 時間級・ 無出力) の注記を入れる。入口は byte 予算が満杯のため、re… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 31212bb4bcc41f19b50666ab2a3d8511738f9f021e282e5a9d6a181ce834721b

- [T-1754] 内容として着地済みだが main の祖先でない branch を /cleanup-branches の削除対象へ**入れる**。削除は -D… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 37e86dfd12facc5e36381678db9f405c137e3f0664a7e1df8d352d4885b2e66c

- [T-1755] fold receipt に無い fragment が 着地済みかを決定的に判定する本文比較器。re-home 追跡と placeholder… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 565fd883e1c1e71119b0013cdd0cfaf9fe2006cec52005e73e22d104904979f0

- [T-1757] 再生成される不透明 baseline (test_reflux_originless_compatibility.py の 1 行) の着地を… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 94c32861bbc81d4145a292feaad36571cea1cec0b43e0e63399dd1e9b8fb46c0

- [T-1758] 共有 main checkout の untracked 集合を 変える操作の直前に pgrep -af mutation_worktree.… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c749d033d41684e80579b4994f893155d50e9ff09caff6893c983af7ac46fd22

- [T-1761] 依存物の staged 運搬を driver の既定にする変更は**承認しない**。先に staged 運搬を canonical trans… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 3752fcaac947b6aec96bad13ca48ff39e661ef3cfd13bbc74c2d8ed713c19caa

- [T-1763] Pegasus の orphan hold 解除文言に、 gate を成立させた実 path を列挙させる。現在は要約 marker の pa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 755b1740e3dd46b96f98a835c52a39fcc8cc94e5901a5ebdde71b9faa1237502

- [T-1764] 非採番 archive の carry が構造的に 検査対象外である件は、**検査を拡張して母集団へ入れる**。名前で対象外を固定している 既… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a07ac111217d6fe49a0e0f02b5127f58f1d52beeeb81f3e4191682fff0fcf90a

- [T-1765] 既知違反台帳・固定総数・exact テストを 同一 patch で書き換えれば無裁定で緑にできる件は、**保護レビュー境界**で塞ぐ。 **そ… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 75add84d4470cba918efa0c85e49c947a5abc312d916f0567f217bda6813be85

- [T-1766] carry 文法を読む consumer (fold、land、rulings 収集) と checker の 2 regex が一致する保証… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 502afbb39e18a2603e416d1d9eb3c12ce05a8c481455e74ea217627f773858e5

- [T-1767] 母数の粗い下限を fold と原子的に ratchet する。凍結 entry ごとの期待件数を固定し、現行 worklog は fold の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: efa0a5b436b4ac6803091482db455449445a03759426b53913eb86f0fb6f9ead

- [T-1775] DW-M05 へ 「tools/mutation_worktree.py --source-repo には固定 commit の独立 clon… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a0d68673b3aaa706e337c3441a20fb3b4ad39823ac713cce2e95a438b3b0bf68

- [T-1776] D935 が 記録するようになった failure_phase を実運用の journal から集計し、 role / provider ごと… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4e0408c9de76d0bcac947d9cf3bccb49a8c38a73a33fb70af5a5bb76d9b1b466

- [T-1786] 自走 harness が monkeypatch / tmp_path を 取るテストを実行できず、test_calibration_free… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 04a67d94ec9b8ff155fa8e3ccb8ee688e1720054df0384bfd40214776c4c8df8

- [T-1790] 実 output/ の窓内書き手のうち output/task-runs/reports/ の書き手が未特定のまま残っている。 現行の除外は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 77467dd4d103d05e81e5a71aaa2eef9cc4d3ce05af86f4ccb28c0d870db6e5c0

- [T-1791] docs/dev-wave/** の L1.5 に 実測した手順 1 行 (150 bytes) が入らない件は、D961 の 手順で閉じる。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 236f8d969f31d978b42e795dabebdfd403700a9e8140161ee48b04c835c92629

- [T-1793] 背景 job の待機作法を dev-wave docs へ 入れる余地を作る。本 wave の段 8 は候補を 2 件出し、DW-O03 の射… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6967f70b1672f54d2a577f0349be3200c3adf8da8db2acb80c803af6a0e860aa

- [T-1796] hook が dispatch gateway の内側 argv を 綴りによって拒否したりしなかったりする件は、**D427 が定める「防護… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a457bf1a1c08e4e12099790c5b017a71c8d77276f9f5b620c48fe0f223fd3d47

- [T-1797] 変異の共有 lock 移行は task 経路についてだけ 閉じている。harness 直接起動は共有 lock を通らないため、repo 全体… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 99a4dbb0195e81067819431009d909baacded90a33934ab217ee7bce40a8b408

- [T-1801] 作り方であると明示する。 受理集合は変えない (D1089)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7231920b31eb1f2752ec24989cb8a82a62339fb34ae8b9fa614576c44aaf0baf

- [T-1809] 親が子へ渡す文書で 非 ASCII を chr(...) 表記に固定する規律を docs/dev-wave/ へ入れる件は、 D961 の収容… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 17d87d6a57b94cb80312c7978ace40494fba91b92f1b5a2c96c1063000a78e90

- [T-1810] 到達不能 commit 監査の残る律速は **古い wave 成果物の退避で探索根を縮める**運用側の変更で対処し、**所要上限は現状のまま*… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 149e4592cb26bdd7488b5a290e68ecf874a2b349a90650507d39f8a16810e66b

- [T-1812] finding path の metadata 取得は commit ごとの argv 上限つき batch なので fork 数が find… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4cd581afd72edb4c5e10a64ec1563f7f504a39f8a7539207062f42d2a04dbbc7

- [T-1813] hang する変異を dispatch 経路で 清算する件は、択 **(c) 現状維持として DW-M06 に「dispatch では han… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 43f0664750c6648a8ab655249d742a63de57c3211c501717238112375ff100e0

- [T-1823] 場所の指定は 未了のまま (D1030)。**共有 filesystem の 2 か所は同一の故障単位ではないが同一の ストレージサーバ群を指… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cdc18629e3f0c38f1bbc2aa411b678debe6f33859b8f4e40e77889bdfeb2710a

- [T-1824] repo 外に置いた救出物・退避物の恒久索引。 現在は worklog 本文だけが手掛かりで、半年後の第三者が directory 名を知らな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 908ce2b290f2f90e120b9e1566ea1ce201c9a8b3f2b2f8f8fe23c576bb83ca76

- [T-1827] 共通 base bundle と薄い rescue bundle の 保管・復元方針。現行は救出のたびに main 履歴を丸ごと複製し、1 件… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7dae2b6516c89429956bf5c7247f661ecbeb77ef713bb4e3293d5ed376e92649

- [T-1829] dev-wave の子 prompt へ Web 検索禁止を 必ず入れる義務の機械化。本 wave で子が Web 検索を始めて成果物を捨てた… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7a7b380f6fa570f53d5d63e5a22e9fe18ae02081ec0ffa4d3fabba66b9b318a7

- [T-1833] 段 8 の自己改善で DW-S01 へ 「裁定の N 箇所は実アンカーで数え直し、同名の非対象は対象外行に残す」「受理集合を変えるなら 広がる… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0b1844e650714f2710067e065b37e93a0e520952a138f2b58867fe5ab269d516

- [T-1838] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 31bd454835645ccbfe2126d816b7c0b13b332cff5a392f5b6068961bb87dd948

- [T-1839] IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT を dispatch の tests task env allowli… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cb385ead0c1f5844b2a7fe0da5458ea06f01c21407e8d83bbb10547aabfe5dcf

- [T-1845] 検査器側を直す。下書きへの検証追加は 費用を見積もってから別途判断する (D1088)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5db96f585024593b8df7576bcba3911149ae02f8c3f10ef7f56f22663f0d229e

- [T-1846] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9f6b503c603fd7e0904a41e1ab05fe3628f544ba61256b27c53122096c86e503

- [T-1849] D961 の射程内 (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 9b8187e43f385deb2544d365a4e12c68db02960bab8472817c734905c96afbb1

- [T-1857] D961 の射程内。契約文面の書き換えが未着地であることが真因である (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 266279649c9b54102a51581dda225955fbc90bd168e97dc70f32b12861ff7920

- [T-1859] 受入の固定費 56.4 秒の内訳が未分解。 本 wave 後は wall の約 27% を占める。D532 が認める 3 手のうち (c) に… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5b0553fdfbd2499c8997643dc85b471ae7ca0252a3a23ab5dcf669cdacf73929

- [T-1862] 択 (a) 採用 — 検査が要求する状態を同じ file の中で自分で作る。判定器の基準変更と明示的な skip は不採用 (D1045)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d8fc9b6ae3a5dce64e96935ccd07d84ea0d2f36543618a3dfff2026b084c50a9

- [T-1863] gen_S の混雑 (実測 RUN 31 / QUE 16) により、 受入や焦点走を計算ノードへ分散すると外側 wall が queue 待… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 474777f6280c9bf8ed0c00b393f61bf3956f566a03128ba9f4f644a59f984399

- [T-1864] D961 のとおり D782 の手順を AI が適用して閉じる。個別に裁定へ返さない (D1046)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c740c2638915c0567d7e8fcdb0a441b5950b23039d8c5239d34159360c0ab2ec

- [T-1865] 1 commit 手順へ戻す。条件 3 点付き (D1068)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 22dc69e147026e8c570d5333809d03373582d7b73023580d71f97c48d3c0ebfd

- [T-1867] 合成監査の子に安定した job 識別子を与え、 receipt 台帳から機構の工数を機械集計できるようにする。現状は wave ごとに名前が違… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 50618018a09d642e39bae366b54f76eeb2f0c4e557e59acc2044e77ecf47f542

- [T-1868] node 故障時の State Transition Reason が未観測である。共有環境で誘発できないため、 偶発事例を取りこぼさず拾う経… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b6dcca03272b569a282164138a25fe0856b15885a8826a518d1fd0539169ffbc

- [T-1877] 統合せず、 両方へ相互参照を追記する (D1091)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f6903bed2b24d520427e5091b6f4d2b52622c91b119cd31d3da161b39995ede6

- [T-1884] 占有検査は判定器を 作り替える。完全観測を表す旗を空集合判定とは別に設け、証明可能な部分集合だけを判定に使う。 除外の再投入と区分単位の保留は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b35a83fe7bcbc69a7c9ae30c77a4fe0c50668881e6b2057aec6c04ff8a0f42a1

- [T-1885] 掃除の成功時診断 retry_count に 自動の読み手を作る。本 wave は実 /proc を走査する成功 6 node を stub… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a4c8756e39fa7373c75bfdfcae4e3476638027734662b98ac3fe1ee2a69254fa

- [T-1887] 既定の分割数は ノードで揃えた対測定を取るまで据え置く (D1047)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: aae76157b3abf885d32fada240b676fa1794416b4810b816317a456415b274e5

- [T-1888] 所要台帳を重み付けに使う機構は作らない。台帳は分析用途に留める (D1052)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b5199fd36cadfbd04d7d7ebc55f41280d7a51791fbf0f6d00ed2dd509a60fb27

- [T-1890] 道具名を実在するものへ 正し、逐語 pin も同じ変更単位で更新してよい (D1048)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e81508b05063c7bfe80730c14befe5cacca01227c48c04f1f719ae7afdfcd025

- [T-1891] 同一 tip・同一選択・同一割付の 受入走で、直列総仕事量が 10585.7 対 14862.6 秒 (1.40 倍)、pytest wall… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 37a834951a8280536365a4779834ff6838eae16552deaec47a66760c1ebbdbda

- [T-1896] 限定例外を条件 3 点付きで書き足す (D1074)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f619747b16a24467a6581a2887420932cc25049a3dc2987cf16ff0a35bbf06d9

- [T-1898] 既知違反の目標指標を 「基準時点以降の新規違反 0 件」へ改める作業。既存の違反は別指標で可視のまま保持し、 残置扱いへ格下げしない (D10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: e4500e1de021acb04ece87ccebb2a7f4ef0e39762edccbb1b4520906c3d00c7d

- [T-1903] 期待値を更新する。 D1152 の形に従い**所要値は性質の述語として更新し、対象集合は基準時点に対する exact な同一性を 保つ** (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: fe640acc84269d444220cb4466f12de7b600f5dd2bb99249a423499464f5b889

- [T-1904] 静的な件数 gate は**置かない** (D1154)。 producer が commit 済みになったことは gate の必要性を作らな… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7bfa5791d79dd16bfaedb7a8fe2761fce3b27ee1c14322a2b165bf23052be974

- [T-1914] 共有 /tmp へ断続的に現れる空の .git の作成元を 特定し恒久遮断する。全 wave の受入を確率的に赤にする。repo 内に作成コー… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: cc7e82f61534cf8461f48e67edbfa4b5e3393708cb53c3b3a5a81c4bbfa6a1ea

- [T-1915] output/task-runs/ は tracked 24 file で git-visible、並行 shard が run direct… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 96a239c336d4538999777a0e98989029eafa288d55ea9a2b9a374b37a83ffa1f

- [T-1916] output/variants/*/bin/ のような wildcard 規則は有限展開できないため、実在後に git ls-files 側で… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a0e25a596d781ff6b087bc645513618eb4ae2d03bc3494f4edfa5d838f888e43

- [T-1917] test_receipt_memo_real_xdist_order_has_no_worker_payer は内側で pytest -n 1… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a4bf266ab67ba3779dbf3ea7a6fc73f97faf662b94965b9d3576c54a2947c7f3

- [T-1918] info/exclude の contract test は git init の通常 repository しか作らないので、実装を rep… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 32629f0fbe8156bd5542da3c1705abef00d6a635f30147d494bb16d567955e37

- [T-1919] 修理済み hold が黙って生き残ることを 検出する機構。DW-G04 により本 wave では設計メモに留めた (output/insigh… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c8736e144490f8c06fa828a2f00af0f676c4ca495145c27127a0924388c912bd

- [T-1920] docs/dev-wave/** の L1.5 層予算に 阻まれた収容を D782 の手順で閉じる。**裁定へ返す案件ではない** (D961… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c3ba343d7d2a4a0a8d8099072f55ccd3da906d9aa9affea8e792b1e6774ca815

- [T-1922] spool_fold.py --dry-run が 生成後 canonical の carry/universe 検査を持たないため、land… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c3ddbb0fbf8c4231803d43ac7658d0f90d052b763a842b02279400f72a25684c

- [T-1923] orchestrator/tests/acceptance_duration_ledger.json が hold#1 の node を 10… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 37392f242f5c4138893f8ab037a360b5745b7a5ce57f0e1b886dfb98935ecbbc

- [T-1926] 生きた worktree 登録を読む production の競合をどう閉じるか。有界な取り直し・missing_ok 相当・ 走行開始時 s… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7c5c51ec22605452f22a7c9d52e5616d96292e5bad8c675964d902a0a4668b6e

- [T-1928] tools/dev_wave_land.py の _worktree_snapshot と _validate_admin_binding が… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1191f3b9ca33a743546a92797eb144f5fd76b9fc5ff81e9397100962677e92c0

- [T-1929] _registered_worktree_paths の resolve 失敗は _FoldGateFailure の既定 (retryabl… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d149004fd6ab0a68271d0c8e41b34a36f417efe59cb6c0e440483420a02e313f

- [T-1930] coordinator の登録 scan には 時間上限が無い。親の実測で単一 process でも 808.553 ms の外れ値が出ており… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 77fb5ac5627ce651aef393c720d7d0279be9da271854b420a18d7b318593b6f5

- [T-1931] 変異 harness の node 抽出器は FAILED  行だけを読むため、fixture / setup で落ちる変異を rc=1 でも… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 80db4b584e6ef465d396edf77d369d343a13a262fddecbae5c6cb994e8598d6c

- [T-1932] **実行器の tip 等値要求は外さない** (D1151)。 択 B (一度きりの land 例外) は受理する authority が無く… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8a64926906f2c882a9049bc9e8be345047401904dfc3ddba9d40d4aa4bbe255b

- [T-1935] dev-wave reference の byte 予算に 余白がゼロで、実測した手順の穴を 1 行も書けない。本 wave は 4 件を候補… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d2103e6ceeb89ad330ea1f7fff8356c4a9439826ce9a30eed304c01ee667d21a

- [T-1937] orchestrator/tests/acceptance_duration_ledger.json を変更後の受入 JUnit 群から全再生… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 07d0b537966ea2332b1909b86915d2e6c432a097db6131c20e4657a0e483b89c

- [T-1938] 受入 wall の律速は総 work (7874.186 秒、W/48 = 164.046 秒) であって排他鎖ではない。work の上位は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: d5a06839471306e62c9e2aca27a5a317052fc90622d01aa27477f8cae0fe6e6e

- [T-1939] 本 wave が足した HEAD 不変 gate は、 helper の恒真化変異は殺せるが、**呼び出し行そのものを消す変異は殺せない**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c59ecd37a4f88cdc40e2176c80f62efd6d78c30e9a3a3d34fe216afb4eb2f123

- [T-1952] 定期更新の担い手を land 側に置く。**pin は 2 種へ分ける** — 所要値は性質述語へ、 node 集合は基準時点に対する exa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 793de76388dd937c50713b544afe0c2cc7681129ff87c3173bdc5917fb0679cc

- [T-1953] docs/dev-wave/** の L1.5 予算 9,566 bytes が 満杯で、実測に基づく短い注意書き (数十 bytes) すら… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 4815d21605d0efe924410814ec2eb32c3627930b3308217917c46fc351a8e84d

- [T-1954] tools/audit_dangling_commits.py の 外部控え抑止から basename 一致条件を外せるかを検討する。安全側の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 75cc49d384ab540be88c0cbe93bd04df9f84e3965bd1604683969a0e424081d1

- [T-1959] 裁定を確定する前に、同じ主題の 既裁定を主題語で全文検索して抵触を洗い出す手順を、裁定を作る側の command へ足す。 本 wave の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: bb78db4e0336cdd97f2f043107ddbd95896f270c9f58b37c7f524e77a87f14ed

- [T-1960] [T-1952] と同じ変更単位で扱う。所要値の exact pin は測定機の個体差を assert する型なので 性質述語へ緩めるが、**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b585ef189065d53cbf8f41a2bf80423216648508c9602cf0ae7b2d884de9600b

- [T-1964] 変異契約の事前登録節へ 「静的に単一理由性を確定できない変異は、登録前に一時変異と焦点走 1 回で落ちる node を実測する」を 足す。本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1e26b109e5648e413e390ff2f7acd3e9d6c8485a730fac8c26d5629d20bee4be

- [T-1972] 後継表・規則の正本・ README 導線の 3 点で充足と認める。原表だけを開いた読者へ届かない残余は限界として明記する (D1208)。本項… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0f9be45b991333fbc8f733fec50bec1ccd89b6dd8bd43cdf2cc47559c237b3bd

- [T-1976] 実行器を初めて編集し、 (i) bounded local 再入も main blob 実行へ移す、(ii) 外側の dispatcher i… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 329a3e039ccc5df2d276a4cb976fa3571bda7d0a00171a6ecf878f96e9808b84

- [T-1977] 実行器束縛の検出力不足 3 件を閉じる。 (i) blob 読取の revision 指定を殺すテストが無い — unit test は re… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1556c2406934a18cff2e6f1f43203ea3e680eb894106b4306abd89eed289e9cf

- [T-1979] docs/pegasus-runbook.md の受入節が 受理経路を 2 つとも現役として説明しているが、D690 以降 tools/che… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1a538623d64ca839e31a41c58517daaa182d0013bc3b758a95b47ba65487fa71

- [T-1982] 一回性を撤去した後、 「holdout の値を見てから選択・凍結・主張を変えない」がどこで守られているかを棚卸しする。 一回性が実質的な防壁と… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 1c58ce6c65f276ba20d053d9c13a760e5df377a814cf85be9d82771998cd5a82

- [T-1990] test_t1574_changed_suite_ledger_node_delta_is_exact の added 12 node は**… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6fd30f0167cdb718e8d203f1ca268be629502e4c1862f26d9b900cc227f74c4c

- [T-1991] flaky_test_holds.py の evidence_id は ^F[0-9]+$ かつ docs/failures.md に実在する… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 243724dc4fce8f0570ca3453d90334787a7ce615cb8ccd387fcff45cf92febdc

- [T-1992] 起動ツールが指示文へ 機械的に前置する形にする (D1216)。 **人の注意を関門にしない。** 文書量の枠は D961 / D1046 /… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c47290fef4c8f5f7a56af3b729534969ed5e9f1a53cef3be6841c1b9523fbbd3

- [T-1993] 隔離環境の codex 子は 実行場所判定が scheduler を叩くため pytest を実走できず必ず rc=16 になる。 本 wav… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: f20145cdc7199bfe8fad2e0162b5d48d6b851b81ef67693d5e581cfcd0495527

- [T-2003] 実 repo の手順書 exact pin を照合する 唯一の test が docs_bytes の growth hold で既定スイート… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 528d00116962a99bc6eb95eeb8d306c4cbbbcb87f41a768142ee6bbbc6c6335a

- [T-2007] 「批准を維持するか撤去するか」という問いの立て方自体が誤っていた。 **争点は批准ではなく、現行コードとの差を有効性の条件にしていたことである… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: ca8857d01c2e20a59fe378cc8dbf8e1eabb9cdd96bdf97c146ceb889e44080f1

- [T-2011] D1159 を実装する。land 側の到達不能な non-attributable-only 検証枝を撤去する。受理集合を縮める方向。 正本は… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6275e671bb57f4476f072436f0c27495d4f622c89a8572efe6121634ca9ebe42

- [T-2013] D1158 により D1054 の残余は閉じない。 免除路を既存の限界として docs/archive/README.md か検査器の doc… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 17e4292c111727f46e0a616e81e51f0a94b5cadad1feed2c2c4440f2673ea79a

- [T-2014] /rulings の収集に、**持ち越し項の解決本文が裁定前に書かれたまま carry されている型**を 検出する手順を足す。本 wave… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 21bf764c373dc839776e74be7fe9e36d21ea183a47868b37f0df0b92477ece16

- [T-2015] /rulings が起動する consult 子の依頼文に、check_codex_output.py が要求する出力形式 (## 総括 節)… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: a05326814dd1efde0358ff32a0105cb707c5a58f64799c6cd40e9633951435d0

- [T-2019] 択 (A) 採用 — 全 live Git 経路へ抑止を入れて閉包を広げる。reader 分類の前提を壊す書き込みが残ると D1008 の a… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b9e184f836132cf5eaf026af47be5d98f0359ffb4a1f23c1b245405338f0afa0

- [T-2020] 共有 filesystem 上の lock を採る。成立しなければ親 tree と共有ベンチマークの双方を隔離する (D1210)。 **親の… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 6c5eea073aa92d8e1e608e74c43b5c03ffb95ad16966657f1a880bdae56f0c69

- [T-2021] canonical node と共有される function scope fixture が実 repo へ触れているかを個別に監査する。 本… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 942f4284b1e952c3364a9a99721efd5a0b0a9d24e409cbd929d8e82144a05875

- [T-2023] 手順書の規則を正とし、 実測なしで登録されている 2 本を実測待ちへ戻す (D1212)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0658f95f3d7be03e4032ee1ed73067824f237f9ae98ecd236b626bd94233dec0

- [T-2040] 配線しない。 代わりに D1149 が決めた stdout telemetry と成果物 evidence の分離を実装する (D1215)。… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 0436992e934eb8a51ba942f89fddeb44f12e68da773e34ab83e5f646682e9708

- [T-2041] 択 (a) 採用 — fixture を実行時合成へ変え repo 内 bytes を NFC に保つ (D1216)。 **(b) は ev… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 33dc8684d2c0c76d07f6cdea72037c21c62474b92d6905437ee60a666901bf50

- [T-2042] DW-C01 の docs 行を旧文へ戻す変異が変異 matrix で SURVIVED した。 原因は test_normative_exa… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 17bd923ce471a278065dc7d2df32f711a0717211373be61aca5f03b82b9c5260

- [T-2054] docs/dev-wave/** の L1.5 予算の 実余裕を main 取り込み後に測り直し、収容できなかった 2 件を該当 leaf 節… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 8c13a1935befe125c48de7565f4b168221ec0e3ad2cb707eb2923d9938ce94d6

- [T-2055] DW-S06-A の reasoning=xhigh が採用 pin として exact 照合されているため、 「段 5 / 6 の effo… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: b333fc4c5f8d166230677118661351ef605bb8e17e221abfaf9186c5c8c876f0

- [T-2056] 期限付き root が保持する祖先 commit へ retention source と失効下界を伝播させる。現行は完全一致だけを見るため、… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 7a0c79429578cd103b14fcfd6f8482ee012a9354ebda9b72084b2e6dd7bba0b1

- [T-2057] merge確認後のbranch削除をexpected OID付きの最小CASにする。単独waveは立てず、次のDW-O28変更へ相乗りする (… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 5800fbfbd7f47d4858713af3720e85b64036374db1a717bffa529bf0c307e1ec

- [T-2059] 既存startupで台帳の期限接近・超過だけを非阻止通知する。daemon、全object走査、停止gateは作らない (D1250)。 — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: c8f8673d84a4f6d410839555afa2031ee76dde50961648d8af6e5bb4e03cbd06

- [T-2064] 並行 land 中の mutation wrapper を共通 main 進行で rc=125 にしない fixed-source clone… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: 214aa25a8312e55bd6533b395127ba91a30b52a6716bca80079de5f5c80719c9

- [T-2071] dispatch変異のtimeoutをqueue / Pre-runningと child実行に分離し、child開始前の混雑でsource変… — 理由: 研究実走の値・受理集合・proof参照を直接変えない開発プロセス/衛生作業であり、D205に従いactiveから除外する。
  再訪条件: 現行研究実走のblockerとなり、成果物影響を特定できたとき。
  base: eff67a617a9ce5cf6d61728eb6892885b161e96d08020f6d1fea43b68a4150a9
