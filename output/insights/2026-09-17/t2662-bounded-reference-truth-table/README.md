# [T-2662] path 参照の抑止判定 — helper と本番の真偽表と D248 の射程 (2026-09-17)

到達不能 commit 監査 (`tools/audit_dangling_commits.py`) の D247 条件 5「landed 内容が候補 path を
境界付きで参照している」を判定する 2 実装 — テスト専用 helper `_has_bounded_path_reference()`
(pattern 出現の左右 1 byte を見る) と本番 `_bounded_path_reference_matches()` (探索根の出現に対し、
根末尾以降の最初の境界 byte または content 末尾までを照合候補にする) — を同じ候補集合で真偽表にかけ、
実在 path を対照にして現行 2 実装の差を確認し、D248 の未規定部分と本番維持の根拠を整理した。
ユーザー裁定 D2104 項 25 (AI 実測先行、暫定は本番側) の実測手番。**実装差分ゼロ** (probe は Codex author
が書き、repo には入れない)。段 6 の敵対レビュー 2 本が親の言い過ぎを 3 点倒し、本文はその是正後
(`s6-adjudication.md`)。

## 結論 (4 点)

1. **差は一方向で、条件は 1 つ。** 862 行の真偽表で「本番だけ True」(P>H) は **0 行**、「helper だけ True」
   (H>P) は **144 行** (うち 4 行は本番の入力領域外の P11、残り 140 行が本番到達可能な差)。この表の
   pattern ごとの判定では、本番 True はすべて helper True だった。差が出るのは**探索根より下に境界 byte
   (空白・改行・tab・引用符・括弧類) を含む path** が、landed 内容に境界付きの形 (裸 + LF、引用、括り、
   content 全体、CRLF、無効出現の後の有効出現、chunk 跨ぎ) で書かれたときだけ (P1〜P7・P12・実在 P13)。
   境界 byte を含まない path (P0) は **chunk 境界を跨ぐ 42 行を含め全 72 行一致**。非 ASCII を含む path
   (P8)、探索根自身に空白を含む場合 (P9)、path 内部に根が再出現する場合 (P10)、衝突形 (右側
   `.backup`/`+backup`、左側 `/other`、非 ASCII 接尾、NUL 接尾) も全行一致。
   **本番 ⇒ helper は全入力で成り立つ** (コード上の論証、表はその裏付け): 本番が `matched.add(token)` に
   到達する token は「非空の根に一致した左境界付きの位置から、境界 byte または content 末尾まで」の実部分列で
   pattern と完全一致し、helper は全出現を `start = index + 1` で走査してその出現の左右境界を認める。
   chunk 分割 (`search_end = chunk_end + len(root) − 1`、右境界探索は content 末尾まで) もこれを破らない。
   **射程**: 表は単根 (`accepted_roots` が 1 つ) である。本番の根集合は全 match の root の集合で、結果は
   根ごとの和集合になる。入れ子の根や境界 byte を含む根 (P9、R0385 で両方 True) があれば、単根で False の
   file pattern が本番でも True になりうるが、その行でも helper は True なので P>H は増えない。
2. **D248 の逐語は候補 path 内部の探索方式を一意に定めない** (D2104 項 25 の理由の再確認)。D248 の
   「pattern の出現が path として完結しているか」「content の先頭・末尾も境界」「未知 byte は延長」は、
   helper (既知 pattern 全体の出現の左右を検査する) とも本番 (根末尾以降の最初の境界 byte で切る) とも
   整合する。helper は内部境界を含む例で本番より広く参照を認め、本番はそれを認めない。**本 wave は
   D2104 項 25 の「抑止を広げない」条件に従い本番を維持し、これを D248 の唯一の解釈の証明とは扱わない。**
   本番の方式を D248 の追加規則として明文化するかは別のユーザー裁定 (実害なし、worklog の裁定待ち項)。
3. **向きは「本番を維持し、helper 側へ揃えない」(実装差分ゼロ)。** helper は 2026-08-26 の単一走査化
   (commit 31b66034f) より前の本番の境界述語 (legacy) で、現在の本番の呼び手は無く、同値テスト
   `test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics` だけが対照に使う。同テストの
   候補 6 行はすべて境界 byte を含まない同一 pattern `/offrepo/w/a.py` なので、その同値主張の射程は
   「境界 byte を含まない path」に限られ、**その射程内では chunk 跨ぎを含めて同値**であることを本表が示す。
4. **境界 byte 入りの path が「必ず報告される」とは言えない。** file 自身の完全 path への参照は当該探索根の
   現行本番では認められないが、D247 条件 5 は探索根より真に下位の**祖先 dir** の参照も認め、
   `_reference_patterns()` は祖先を全部生成する。境界 byte を含まない祖先 (例 `/offrepo/w`) が引用されれば
   抑止されうる — 表に測定済み (R0098、R0245: 祖先 `/offrepo/w` を引用 → helper・本番とも True)。
   別候補や hardlink alias の参照でも抑止されうる。

## 帰結

- 31b66034f の commit message「既存の境界付き token 照合が同じ抑止集合へ落とす」は、境界 byte を含む
  path で有効な祖先参照が無い例では成り立たず、**本番の述語は legacy より狭い** (抑止が減る = 報告が増える)。
  同 message の「安全条件は 1 つも緩めていない」は、この述語変更の縮小方向に限れば成り立つ。D2039 の指摘と
  整合する。legacy の本番 (31b66034f の親) は `git grep -F -l -z -e <pattern>` で content を絞ってから helper を
  掛けていた。固定文字列の部分一致は境界付き出現の上位集合なので前段は helper True の content を落とさず、
  legacy の end-to-end 判定は helper と一致する (helper = legacy の境界述語)。
- 本番探索根 `/work/1/SFC/tanab/dev-wave-jobs` には今日、名前に境界 byte を含む実在 entry が 6 件
  (空白入り dir 4 件 = 配下 467 file、`[?]*` と `:(glob)` を含む file 2 件、いずれも pytest tmp 残骸) ある。
  各 dir から 1 file ずつ選んだ 6 file を引用 3 形で書いた合成 content 18 行で差が発火した (18 file ではない)。
  これらが到達不能 blob と bytes 一致して候補になっているか、実監査の findings が変わるかは**測っていない**。
  467 file 全体の発火件数にも外挿しない。
- 本番コードのコメント (`_bounded_path_reference_matches` 内「token の set 一致は pattern の境界付き出現と
  同値」) は無条件では誤り (反例 R0075: 引用符で囲んだ空白入り pattern が helper True・本番 False)。
  実装面なので本 wave では触らず、次の一手に含める。
- 監査の抑止集合・findings・rc 契約・D247 の 5 条件・D248 の境界 byte 列挙はいずれも変えない。

## 真偽表が否定しえたこと (実測の情報量)

- P>H が出ていれば「本番は常に狭い」が崩れ、本番維持を安全側と単純に説明できなくなり、根・pattern 集合・
  chunk 処理の調査が要った。
- 実在 path で差が出なければ「現在存在する名前でも発火する」と言えなかった。18 行がその隔たりを埋める。
- chunk 跨ぎで予期しない差が出れば、差を境界 byte だけに帰せず、探索の欠落を別問題として扱う必要があった。
- 否定しえなかったのは「本番維持」という運用判断であり、それは裁定の不変条件が先に決めている。

## 次の一手 (本 wave の scope 外、worklog fragment の項)

- **テスト強化 (新規、Codex author)**: 同値テストの射程 (境界 byte を含まない path) を docstring と id に
  明記し、境界 byte を含む path の差分 (helper True・本番 False) を「現行挙動と legacy との差の記録」として
  pin する。あわせて本番コードのコメントの無条件な同値主張を射程付きに直す。抑止集合は変えない。
- **裁定待ち (P3、実害なし)**: 本番の方式 (候補 path 内部の境界 byte は終端として扱う) を D248 の追加規則
  として明文化するか。現状維持で挙動は変わらず、明文化は将来の意味変更の基準になるだけ。
- 採らない案: helper を本番の意味へ揃える (legacy との比較能力を失う)、helper と同値テストを削除する
  (比較資料を失う)。いずれも恒久的な禁止ではなく現時点の選択。

## 成果物と一次資料

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (研究前進・scope・裁定・割れうる前提 P1〜P5) |
| `s4-adjudication.md` | 段 4 裁定 (probe 契約 = 候補集合の事前登録、wave の形) |
| `s5-author-report.md` | Codex author 子の最終報告 (逐語) |
| `s5-probe-audit.md` | 親の probe 監査、本走の事実 (rc・SHA-256・byte 数)、実在 path の対照、P型×C型×向きの集計 |
| `verbatim/truth-table.md` | 本走の真偽表 862 行 (byte 同一、SHA-256 `07600bc5…`) |
| `verbatim/realpath-hits.txt` | 探索根の境界 byte 入り実在 entry 6 件 (4 dir + 2 file) |
| `s6-review-a.md` / `s6-review-b.md` | 段 6 敵対レビュー (逐語。レンズ A: 候補集合と対照、レンズ B: D248 解釈と向き) |
| `s6-adjudication.md` | 段 6 所見の裁定 (real / refuted、closed / partial) と是正後の結論 |

probe 本体 (314 行、SHA-256 `799d9140…`) と JSON (89,389,377 bytes、SHA-256 `780e1b3d…`) は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2662-bounded-reference-truth-table/` に保全し repo へは入れない。

## 割れうる前提 (brief) の判定

| 前提 | 判定 | 根拠 |
|---|---|---|
| (P1) 差は一方向 (helper ⊇ 本番) | **支持** | P>H 0 / 862 + コード上の論証 (結論 1) |
| (P2) D248 の意味は本番側 | **未確定** | 本番維持の運用判断は支持するが、D248 の唯一の解釈とは立証していない (結論 2、レビュー B) |
| (P3) 実在 path での発火は今日 0 件だが構造的に 0 ではない | **修正** | 実在 path 6 file の合成 content で差は発火する (18 行)。「候補になるか」は未測定 |
| (P4) chunk 境界も同じ表で潰す | **支持** | P0 × C11 42 行一致、P1 × C11 は境界 byte 由来の H>P のみ |
| (P5) 本 wave は実装しない | **支持** | 実装差分ゼロ |
