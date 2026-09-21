VERDICT: GO

検査対象は commit `5326ad4ab` です。以下の短い file 名は、すべて /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/ の下にあります (methods.md / implementation.md / README.md)。一次資料 (D・entry・insight・事前登録・結果稿・発効記録) は、repo root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/ からの相対 path で書きます。
新規の must-fix と regressed は 0 件です。新規所見は nit 6 件です。

## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| S1 | closed | methods.md:77-80 に「superproject (submit-tree `6a3e15809`) から、CCBench を driver の PIN `511c9538` へ checkout (D1777。gitlink は `e9e477ca` のまま)」とあり、:95-96 も同じ内容。implementation.md:95 の K2 行も同様。一次資料の pair-attempt insight §1 (l.45-46「D1777 / T-2407 の手順」、l.54 policy epoch、l.56 `ccbench_commit` `511c9538`)、entry 1754 (l.9)、D1777 本文と一致する。git でも確かめた: `6a3e15809` で `p3_s4_loop.PIN` = `511c9538…`、`ls-tree` の gitlink = `e9e477ca…` |
| S2 | closed | methods.md:170 (校正段)、:180 (本走段)、:195 (未確定の列挙) に反映されている。D2190 項 3 (b)、事前登録 §5、結果稿 §2 項 4 と一致する。緩い読みは塞がった |
| S3 | closed (指摘した箇所) | methods.md:206-208 の出所が「結果稿 §3、発効記録 §3〜§5、entry 1791。実施手順は D2202」になった。親は implementation.md:92 と :142-143 にも広げている。ただし同型が implementation.md:173-174 に残る (下の新規 nit 1) |
| S4 | closed | implementation.md:213 の link が `../../2026-09-20/paper-methods-ja/README.md` §5 を指すようになった。前稿 README §5 (l.86〜99) に must-fix 4 / should 3 の表があることを確かめた |
| N1 | closed | methods.md:132 が「対象の 2 案 (推奨は案 A)」になった。D2175 の表題と第 1 bullet に一致する |
| N2 | closed | methods.md:147-148 の `effective` 節の内訳が、D2202 項 1 と発効束 JSON の `effective` の key に一致する。key は decision / approval_date / approval_target / approval_record_commit / decision_numbering_fold_commit / draft_source / calibration_job_walltime / verifier_hard_timeout_s |
| N3 | closed | methods.md:157 の「許可集合で照合」は D2190 項 2 と一致する。「各 1 値」は :158-159 で D2202 項 2 に帰属させている。未確定の列挙 (:195-196) に sha 不一致と判定集合外の記録の混入が足され、D2190 項 3 (c) に一致する |
| N4 | closed | methods.md:85-86 と implementation.md:128 の stub の範囲が、D2205 の再訪条件 (build / trace / bench / … / checkout / condition gate …) と pair-repair §0「主張しない」1 に一致する |
| N5 | closed | methods.md:208「校正の未完走・bench 失敗・規約不適合はいずれも 0 件」は、結果稿 §3.3 (未完走 0、bench 失敗 0、規約不適合 0 / 0) と事前登録 §13 に一致する |
| N6 | closed | methods.md:194 は事前登録 §6.1 項 2 のほぼ逐語である |
| N7 | closed | methods.md:76-77 が「entry 1754、pair-attempt insight §1、D2187」の順になった。implementation.md:92 と :142-143 は実施記録を先頭に置いている |
| N8 | partial | README.md:68-69 に 2 行が足された。ただし 1 巡目が名指しした implementation.md:154 (「K2 の stock 対照口の追加**と修復**も」) が表に無い。implementation.md:30 (「本稿末尾」→「下の『実走・契約・未了の境界』節」「(前稿から継承)」) も、追加行の「story の項の…」の範囲に入っていない。前稿との diff で確かめた (hunk `129c154`、`27c30`) |
| N9 | 不採用が妥当 | 依頼 (request.md l.3-4) が B-8 の方法の要素として「発効束」を名指ししている。N2 の訂正で内容も正確になった。N9 は正しさの指摘ではなく、冗長さの指摘である |

## 新規所見

[nit] implementation.md:173-174 — 「B-8 の発効と 3 値判定 `pass` (D2194 項 1、D2202、entry 1791)」は、S3 と同じ型 (D2202 を `pass` の出所に並べる) で、fix の対象から漏れている。README §4 の S3 行は implementation にも反映したと書いている / 根拠: D2202 本文に判定値 `pass` は無い。`pass` は結果稿 §3.3 と発効記録 §5 にある。request.md l.7-9 の出所規則 / 直し方: 「(発効は D2194 項 1。判定は結果稿 §3・発効記録 §5・entry 1791、手順は D2202)」に置き換える。

[nit] methods.md:158-159 — 「B-8 の集計では、受理する sha256 を各 1 値で明示して渡した (D2202 項 2)」は過去形の実施事実だが、出所が D だけである (N7 / S3 と同じ型)。D2202 項 2 は「明示する」という手順を定めた文である / 根拠: 渡したことは発効記録 §3.1 と §5 (`--accept-ruling-sha 6ccb18c7…` / `--accept-bundle-sha 059536a7…`) が示す / 直し方: 「(手順は D2202 項 2、実施は発効記録 §3.1・§5)」とする。

[nit] methods.md:170 (と :180) — D2190 項 3 (b) の限定「開始して失敗した bench に適用する (打ち切りの `not_run` は失敗でない)」が抜けている。また :180 は「校正・本走を問わず」の出所を (§3.2、§5) にしており、解釈を固定した D2190 項 3 (b) を挙げていない。これで生じうる誤読は厳しい側 (打ち切りを失敗に数える) なので、規律 2 を緩める問題ではない / 根拠: D2190 項 3 (b)。結果稿 §3.3 は `not_run` を bench 失敗と別に数えている / 直し方: :170 に「(開始して失敗した bench に限り、打ち切りで走らせなかった extime は数えない)」を足し、:180 の括弧に「D2190 項 3 (b)」を足す。

[nit] implementation.md:92 — B-8 行は判定集合 30 枠と `pass` という数値主張を書いているが、事前登録 §13 が添えることを求める「校正の未完走件数・規約不適合件数」(いずれも 0) が無い。N5 の反映は methods だけだった / 根拠: 事前登録 §13 の第 2 bullet、結果稿 §3.3 / 直し方: 「再検証・再開・再投入は 0 回」の前に「校正の未完走・bench 失敗・規約不適合は 0 件」を足す。

[nit] README.md:58-69 (§3) — N8 が partial である件。implementation.md:154 の「と修復」(K2 の範囲の書換えで、型は後の着地 = D2205) と :30 の書換えが表に無い / 根拠: 前稿との `diff` の hunk `129c154` と `27c30` / 直し方: K2 行の「箇所」に「implementation 境界節の B-4 段落末」を足し、追加行の正本の優先関係に「stale 注記の項の参照先と (前稿から継承)」を足す。

[nit] README.md:84, :86 (§4 の裁定表の「反映」列) — S3 行の「methods と implementation の 2 箇所」は、実際に直したのが 3 箇所 (methods.md:206-208、implementation.md:92、:142-143) である。S1 行は「(D1777)」を 3 箇所に書いたように読めるが、D1777 があるのは methods.md:78 だけで、:95-96 と implementation.md:95 には無い / 根拠: `git diff 784db3f02 5326ad4ab` / 直し方: 「3 箇所」に直し、S1 行を「D1777 は methods §2 の K2 段落に明記」と書く。

### 項目 4 (規律 2 の向き) の再確認

fix で足した規則文は、どれも一次資料にたどれる。

- bench 失敗は校正・本走を問わず pass を妨げ、校正で出れば本走を投入しない (D2190 項 3 (b))
- 校正の未完走は pass を妨げないが開示する (事前登録 §6.1 項 2)
- sha の不一致と混入は未確定に落とす (D2190 項 3 (c))

弱めた記述は無い。一次資料に無い規則の追加も無い。唯一ずれがあるのは `not_run` の限定の欠落で、誤読されるとしても厳しい側である (上の nit)。

D2190 項 3 (f) (校正は anomaly を理由に残りの extime を止めない) は methods に無い。ただし fix 前から無い記述で、規律 2 を弱めるものではないので、所見にはしていない。

### 項目 5 (1 巡目の refuted) の再確認

- 判定集合 30 枠の帰属: grep で確かめた。methods.md:205-206、implementation.md:92・:123・:190-191、phase3 の l.22-24 はすべて「本走 24 + 校正の完走 6」の形で、違反は 0 件。
- K2 の D2187 / D2205 の区別: 2 段落は分かれたままである (methods.md:73-80 / :82-87)。fix は各段落の中に文を足しただけで、両者を混ぜていない。
- B-5: 本文は不変。implementation.md:142-143 で変わったのは B-8 の出所の括弧だけである。
- scope: fix は三つの対象と wave 記録の中に収まっている。
- `git diff --check 784db3f02 5326ad4ab` の出力は空だった。

## 再計算した派生値

| 値 | 数え方 | 結果 |
|---|---|---|
| README §4: must-fix 0 / should-fix 4 / nit 9 / refuted 24 | s6-review.md を数えた。should は l.3・5・7・9。nit は l.11〜27 の奇数行で 9。refuted は l.29〜52 で 24。must-fix の行は無い | 一致 |
| README §2「B-8 の 9 段落と判定の 3 項」 | methods.md の段落の開始行: :130、143、154、165、177、186、199、203、212 で 9。判定の項: :189、192、195 で 3。fix で足した :170 と :194 は既存の段落の中にあり、空行を足していない | 一致 |
| README §3 の「型」(10 行) | git で確かめた。`482f19b88` (09-20 17:56) は `6a3e15809` (19:03) の祖先。`7baf3f375` (20:42)、`7c0a1c63a` (22:54)、`c41cfb09f` (20:34) は、いずれも `482f19b88` の祖先ではない。`624c84986` は 2026-09-21 08:42:12。entry 1779 と D2200 は 09-21。追加の 2 行 (表記の修正と追加、link の修正) も中身と合っている | 一致 (網羅性は N8 のとおり partial) |
| implementation の確認点「should-fix 4 件と nit 8 件を反映」 | 採用は S1〜S4 と N1〜N8、N9 は不採用 | 件数は一致 (N8 の中身は partial) |
| methods 冒頭「本稿の時点」2 箇所 | 前稿 methods の継承部分: l.24-25 (行をまたいで「本稿の\n時点」) と l.201。l.67 (K2) と l.74 (pin) は改稿の対象の中なので除く | 一致 |
| implementation と README §3 の「4 箇所」 | 上の 2 箇所に、前稿 implementation の l.72 (A-1 行「本稿の時点で 0 件」) と l.145 (兄弟 wave の文) を足して 4 | 件数は一致。ただし l.145 の字面は「本稿は稼働中の兄弟 wave」で、「本稿の時点」ではない (時点を指す表現としては同類) |
| README §4 S3「methods と implementation の 2 箇所」 | fix の diff で数えた | 不一致 (3 箇所) |
| methods.md:208 の件数 0 (校正の未完走・bench 失敗・規約不適合) | 結果稿 §3.3 の表、発効記録 §5 | 一致 |
| 発効束の sha256 `059536a7…807c1b` と事前登録の `6ccb18c7…` | `sha256sum` で再計算 | 一致 |
| K2 の submit-tree と PIN | `6a3e15809` の `p3_s4_loop.py:115` が `PIN = 511c9538…`、gitlink が `e9e477ca…` | 一致 |

### Critical Files for Implementation
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/implementation.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/methods.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/t2807-b8-effective/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/docs/decisions.md (D2190 項 3 (b)、D2202)
