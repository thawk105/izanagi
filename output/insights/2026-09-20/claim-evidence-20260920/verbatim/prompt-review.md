単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/claim-evidence/2026-09-20.md
  (**レビュー対象の新稿**、203,760 bytes / 691 行、1 行が長い表。**全文 `cat` しないこと**。`grep -n "^## \|^### "` で節の位置を出し、
  `sed -n` で 20 行以内ずつ読め。表の 1 行は 2〜6 KB あるので `sed -n 'N,Np'` を 1 行ずつでもよい)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/claim-evidence/2026-08-26.md
  (**前稿。凍結物で不変**、83,074 bytes / 570 行。新稿 §7 の対応表の照合に使う。同じく節ごとに読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/README.md
  (**レビュー対象。claim-evidence 系列表に 1 行を足した**。`grep -n "claim-evidence" ` で位置を出せ。「最新スナップショット以後に
  確定したこと (stale 注記)」の 11 件が、新稿が取り込んだ 09-19 版以後の事実の一覧である)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/brief-s1.md (親の段 1 brief と段 4 の provisional 裁定 (P1)〜(P3)。
  新稿が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-claim-evidence-2026-09-20/docs/paper-story/2026-09-19.md
  (**入力の正本。凍結物で不変**、394,236 bytes / 3,325 行 — **全文 `cat` しないこと**。§3 = 1147〜1288 行、§6 = 1751〜2037 行、
  §7 = 2038〜2338 行、§8 = 2339〜3071 行、§9 = 3072〜3208 行。`sed -n` で 80 行以内ずつ読め)

新稿の各行が (b) 欄で指す一次資料 (`results/` 稿 8 本、`output/insights/` の README、`certification.json` / `result.json` /
calibration JSON、`docs/decisions.md` の D 本文) は、お前が (b) 欄の path から自分で開け。**`docs/decisions.md` は 5.6 MB /
68,000 行超、`docs/failures.md` は 2.7 MB — 全文 `cat` してはならない。** `grep -n "^## D<番号>\. "` で位置を出し `sed -n` で
60 行以内ずつ読め。`wc -c` / `wc -l` は許す。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新稿と README の 1 行を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、
下の 2 レンズを 1 本で担う。**
親が実走した検査: `tools/check_docs.py` rc=0 (2 回)、新稿が引く repo 内 path 91 件の実在 (欠 1 = `output/s8b-freeze-candidates/
holdout_freeze.v2.g1.json` で、新稿は「保存 branch にあり main に無い」と書いている)、repo 外 path 9 件の実在、
A-2 / A-6 の `certification.json` の `effects` / `status` / `source_commit` / `request_ids`、A-1 `result.json` の sha256 `372f199e…` と
`statistics` の値、between_run_noise JSON 3 本の `between_run.cv`、A-2 / A-6 policy の `scheduler.nodes` = 5、
`output/env/pegasus/calibration/registered/` の 8 file、`output/campaigns/*/reports/layer3_report.json` の 8 件、図 fig1〜fig9 の
実在 (fig10 / fig8b 無し)、ccbench gitlink `511c9538`。

新稿の作り方: 前稿の §1〜§6 の骨格を保ち、2026-09-19 版の §3 / §6 / §7 / §8 / §9 全体から行と限定を作り直した (差分改訂ではない)。
行 ID C1〜C17b は前稿から継承、C18〜C37 と C15c が新規、限定 L01〜L28 は継承 (本文に「2026-09-19 版時点の更新」を加筆)、
L29〜L50 が新規。§7 に前稿との対応表。(c) の語彙は前稿の 6 値から 7 値 (「固定条件で certified な correctness」を追加) へ広げた。

## レンズ A — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 少なくとも次を (b) 欄が指す権威 bytes / results 稿 / insight / D 本文で検算せよ:
   - C18 (A-2): median 4 値、`effects` 2 値と百分率、request / host、source commit、`a4_noise_floor_status`、日付。
   - C19 (A-6): median 2 値、`effects.rr95`、request、source commit、限定 12 件との整合、「反復 attempt は行わない」。
   - C20 (T-1998): `improvement_percent` / `ratio` / median 2 値、日付 3 つ (測定・認証・再確認)、node、sha `464e3af5…`、
     consumer 是正で受理集合が広がる変更 1 件、限定 20 件との整合。
   - C21 (A-1): 対差平均 3 値・h・B・baseline 平均・k・`floor_fraction`、job / host、`formal` / `promotion_prohibited` /
     `result_authority`、sha 3 つ、L-A1S-1〜20 との整合。C31 / L36 (attempt-0002 の gate 拒否): 時刻・rc・gate 名・commit `abff80d1b`・
     副作用なし・裁定パッケージ 3 択 (`output/insights/2026-09-19/a1-sized-attempt2/README.md`、D2156)。
   - C22 (待ち方 grid): raw p / Holm p の 6 値、36 cell の効果量の件数 (完全に出た 0、境界跨ぎ 4)、135 / 270、request `978195`、
     権威 bytes の path と sha `a4390603…`。
   - C23a / C23b (右 tail cohort 1 / 2): group id、job id、事前登録 commit 2 つ (`cad6f46d8` / `8737cacb4`)、verdict、18 区間、
     throughput と abort 率の 1000 → 9999 の値 (cohort ごとに別の値であること)、権威 bytes の sha 3 つずつ、限定 15 / 16 件、
     再現欄の規則 (D2050 / D2157、合成しない)、fig8 は cohort 1 だけ。
   - C24 (official 床値案): rr20 / rr80 と scale_ref、request `1818`、96 attempt、`wired_min_rel_floor` 0.03、g1 候補 sha `7e111406…`
     と bytes、2 度の land 不成立の理由 (entry 1640 / 1688、`output/insights/2026-09-19/t2724-chain-land-2/README.md` §0・§6)、
     branch `t2724-chain-land-2-saved` (`0a799da6c`)、D2120 項 2 の (a)〜(f)、D2154。
   - C25 (検証相): 候補 2 genome の `src_token` 2 つ、extime 3 s、30 verify / 候補、未完走 2 件 / 候補、request の範囲、時刻、
     sha `f7248a7f…`、限定 9 件、D2160 の項 1〜7 (準用・identity・extime・確定値・未完走・繰延べ・不変条件)。
   - C26 (B-7 fixed5): median 6 値、`effects` 3 値と百分率、床値 3 値、判定 (rr95 のみ退行)、outer `reject`、request / source、
     sha `b6493e4e…`、限定 14 件、D2162。
   - C27 / C28 (mocc): 5/42 と CP 区間、T-2774 の 5 arm 検出数と Fisher、T-2779 の 3 値と Fisher、T-2780 の job と結論、
     軽量 witness の 4 arm 検出数・Fisher 0.500・検出力 0.105、D2148 項 13。
   - C29: between_run.cv 3 値と JSON の `notes` (下限であること)。
   - C30 (identity): D2104 項 2、D2108 (空入力 prefix、8/8 byte 一致、受理集合が狭まる向き)、D2120 項 7 の限界 2 つ。
   - C32 (B-4): 凍結 commit `0b4fbd7a6`、窓 w1 / w2 の UTC 範囲、n = 62、w1 の request 3 つと実行 HEAD `2ba400087`、
     「terminal complete」、D2138 / D2145 / D2146、`output/insights/2026-09-19/t2288-floor-pair-w1/README.md` の「主張しないこと」。
   - C33 (B-5): D2158、事前登録 v1 が未発効であること、[T-2797] の内容。
   - C34 (mocc 準備): D2114 / D2134 / D2147 / D2159 / D2150 項 1 / D2127 の内容、wave 2 の request `11161` と 30 check、
     候補 pin `e9e477ca` の位置 (4 commit 先、差分 1 file)。
   - C35 (K2): 3 巡の値 (20 / 25 / 10)、3 巡目の job `10761`・Elapse・median 815,983・CV・`continue`・critic-3 帰属不能、
     同 job stock 対照の未達、D2148 項 2 / 項 3、D2155、[T-2795] の内容。
   - C36 / C37 / C11 / C3: g1 候補の生成 (D2077 / D2097 / D2098)、較正 record 8 件、layer3 report 8 件、loop の certified 到達 4 度
     (2026-09-10 / 09-16 / 09-18 / 09-19) の出所。
   - 継承行 C1 / C2 / C4〜C8 / C13 / C14a / C14b / C15a / C15b / C16 と前稿の対応 (§7)。C14a の raw 未特定 ([T-1878])。
   - §3.1 の L01〜L28 が前稿の趣旨を動かしていないこと (加筆は「2026-09-19 版時点の更新」の範囲か)。§3.2 の L29〜L50 が
     2026-09-19 版 §7 (76 項) の恒久・条件付き限定を落としていないか — 落とした項目があれば列挙せよ。
   - §4.2 A-1 行の「前稿 §6 の二択 (案 A / 案 B) は D1262 / D1619 により案 A の向きに解消している」という読みが正しいか
     (D1262 / D1619 の本文と policy v3-sized の arm 定義から)。
2. **母集合と射程。** 新稿が「certified」「accepted」「completed」「そろった」「再現」「解除」「承認」「取得済み」と書く箇所で、
   母集合が広すぎないか (例: A-1 attempt-0001 を「A-1 の値」「再現」と読ませていないか、検証相を B-8 の取得や性能の認証と
   読ませていないか、B-10 cohort 2 を「再現されたので飽和しない」と読ませていないか、official 床値の採用裁定を発効と読ませていないか、
   mocc の準備を第 2 成功例と読ませていないか、A-2 の取得済みを「限定も外れた」と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「N 件」「N 稿」「N 点」を原データから数え直せ。特に (c) の「7 値」、行の総数 (C1〜C37 と
   C15c の実在と重複無し)、L の総数 (L01〜L50、欠番無し)、§3 末尾の「紐づかない限定 4 つ」、§4.1 の「A-1 と A-5 の 2 つ」、
   README 行の「C1〜C37」「L29〜L50」、C11 の「8 件」、C37 の「8 件」、C28 の「4 件」、C25 の「30 verify」、C21 の「限定 20 件」。
4. **path と参照。** (b) 欄の path・D 番号・T 番号・F 番号が実在し、内容が本文の記述と合うか。**(b) 欄で `[権威 bytes]` と
   `[導出索引]` の区分が規則 (§1.3) どおりか** — results 稿を権威 bytes に置いていないか、`authority: none` の insight を
   権威 bytes に置いていないか。行番号参照が無いことも確かめよ。
5. **凍結物の不変。** `git -C <worktree> status --short` / `git -C <worktree> diff --stat` で、変更が `docs/paper-story/README.md`
   (更新) と `docs/paper-story/claim-evidence/2026-09-20.md` (新規) の 2 file だけであること、前稿・版・`results/`・`figures/`・
   `docs/paper-story-backoff/` に差分が無いこと、README の版の履歴表 (「## 版の履歴」の表) に新しい行が**無い**こと (claim-evidence は
   版ではない) を確かめよ。

## レンズ B — 主張の強さ、分類の一貫性、二重計上、前稿との差分、先取り

6. **禁止句。** 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「飽和しない」「再現した」「発効した」に相当する表現
   (短縮形・言い換えを含む) が、(a) 欄の肯定文として無いこと (✗ の禁止推論として引用しているのは可)。B-10 の言い方が事前登録
   §4.5 の固定表現「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」に限られていること。
7. **(c) 欄の一貫性と二重計上。** 同じ観測が §2.1 と §2.2 の両方に行として立っていないか。(c) の値が閉語彙 7 値の外に無いか。
   A-6 の `reject` と右 tail の `not-observed` が「測って届かなかった」に置かれていないこと (2026-09-19 版 §9 の第 2 種の規則)。
   検証相 (C25) が「固定条件で certified な correctness」に置かれ、性能の行 (C18 / C19) の (a) に染み出していないこと。
8. **(d) と (e) の規則。** 全行に ✗ の禁止推論が 1 つ以上あるか。(e) が `外せる項目:` / `後続別主張:` / `将来scope:` / `要裁定` の
   型で書かれ、`該当なし` を使っていないか。(e) の A / B 項目 ID が §4 に実在するか。`要裁定` の行に裁定待ちの T 番号があるか。
9. **前稿との差分 (§7)。** 前稿の全行 (C1〜C17b) と L01〜L28 が §7 の表で扱われているか。C12 を落とした理由と L24 の扱いが
   一貫しているか。前稿の記述で新稿と食い違うものが「当時は真で後続が古くした」型だけか (前稿の執筆時点の誤りを新稿が見落として
   いれば must-fix。逆に新稿が前稿の誤りを認定しているなら、その根拠を検算せよ)。
10. **§5 統制稿と表の整合。** §5.1〜§5.7 の各文が §2 の行と §3 の L に根拠を持つか。表に無い限定を足していれば、§5 冒頭の
    「補ったもの」表に載っているか。§5 が表より強い主張になっている箇所を列挙せよ (例: 5.2 の検証相の書き方、5.4 の cohort 2)。
11. **先取り・scope。** 稼働中で未着地の wave の内容を完成済みとして書いていないか (着地済み正典は local main `b7f970dfa`。
    fig10・cohort 2 の後継図・[T-2792] / [T-2795] / [T-2797] は裁定待ち)。新しい主張を足していないか (brief の scope)。
    裁定を先取りしていないか (例: B-8 の取得、A-1 の再認可、pin 前進の実施、chain の取り込み、B-5 の本走)。README の
    「版の履歴」表に触れていないこと。README の stale 注記 11 件のうち、新稿が取り込んでいないものがあれば列挙せよ。
12. **brief の (P1)〜(P3) を攻撃せよ。** (P1) C12 を落として C2 / C18 へ吸収したことは、前稿の読者に対して情報を失わせないか。
    (P2) 検証相の B-8 仕分けを本稿で行わないことは、B-8 の状態語を曖昧にしないか (§4.3 の書き方で足りるか)。(P3) results 稿を
    `[導出索引]` に置く区分は §1.3 の規則と整合するか。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。前稿の C12 は「本稿に無い」と明示したうえで L24 で歴史的に保持する形は許容。
- 旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 は充足と書かない。3 走行と A-1 attempt-0001 と B-7 fixed5 を pool しない (D1993 項 6)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効した」とは書かない。検証相は性能値を含まず既存判定を昇格させない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・版・figures/) の訂正・図の再生成・新しい主張の追加・
  英語化も scope 外。版の履歴表への登録は規則で禁止。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当箇所 (§番号と行 ID または L 番号)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新稿をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
