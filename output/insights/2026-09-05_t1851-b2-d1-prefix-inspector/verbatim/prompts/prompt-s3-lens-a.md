単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md` — 親 brief。**これ自身も検査対象である。**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md` — 段 2 plan。**守らずに攻撃する対象である。**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/s4-adjudication-r2.md` — 設計 wave の 13 blocker と 6 段分割
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/t1946-proof-chain-s4-adjudication.md` — proof chain の設計凍結
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a2alpha-s4-adjudication.md` と `refs/a2beta-README.md` — 直前 2 wave の状態と裁定

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD `50dbf9158`。コードはすべてこの worktree の中を読む。

## レンズ A — 正しさ境界と裁定整合

plan と親 brief を、**正しさゲートの意味論と確定裁定への整合**の観点で攻撃せよ。plan の推奨を採用するかどうかは問わない。次を必ず検査する。

1. **D1337 の prefix 証明の意味論。** plan の verifier inspection が「live 全行を replay した後だけ `len(rows) >= N` と `rows[N-1].event_sha256 == reported head` を比較する」を満たすか。N 行以後の壊れた tail (parse 失敗・chain 切断・genesis 改竄) を拒否し、正当な append を許すか。N 行内の改竄が chain の再計算で必ず露出するか (event_sha256 の計算に何が入り、何が入らないか — `attempt_registry_core.py:240-258` を現物で読め)。「reported が無ければ skip」「N > len(rows) を receipt 不在と読む」など恒真化の形が無いか。
2. **proof の binding。** proof の freeze / protocol / schedule digest が、artifact 側の自己申告と live 世代の genesis の**両方**と照合されるか。片方だけなら、別 campaign の台帳を指す proof が通る経路を具体的に示せ。current protocol generation の解決 (`_registry_generation_paths_locked`) が「別世代の台帳を prefix として受理する」余地を残さないか。
3. **v4 の受理面不変。** plan の D1-a / D1-c / D1-d が、既存 v4 artifact の受理集合を 1 bit も変えないか。v4 に `attempt_registry` が現れたとき exact key で拒否されるか、それは既存の経路で既に拒否されているか (既存なら新設の検査は恒真 — D1522 の「下層の実体を名指しする直接検査」が要る)。
4. **A2α の S5 / S6 (v2 terminal の二層拒否) との整合。** 本 wave の inspector が v2 terminal を必要としないこと、E1 / E2 (単位 C) の契約を先取りしていないこと。terminal に依存する部分 (coverage、`finished_at`) が実装に混入していないか。
5. **read-only の保証。** inspector が台帳 bytes・claim・marker を 1 byte も書かないか。`_locked_readonly` と write lock の選択が recovery reader (単位 B1 / A の resume 経路) の意味を変えないか。B2-7 (既存 recovery reader を壊さず別 API) を満たすか。
6. **親 brief の (P1)〜(P6) を独立に評価せよ。** 特に (P1) (producer は v4 のまま、v5 は別名定数) が D1341 の同時 land 要件を満たしつつ、単位 C が切り替えるときに supersede すべき pin を今のうちに名指しできるか。(P3) の「到達可能な値域」が現物 (v2 世代に積める行) と一致するか。
7. **親の実測値とその一般化。** brief の DW-O09 節 (pin 閉包の件数、`output/` の v4 bytes 0 件)、DW-O13 節、実アンカー表の行番号を現物で検算し、誤りを全件列挙せよ。
8. **成果物が実際に効く全層。** 本 wave の gate が production で発火しない (D1114 / D1341) ことを前提に、それでも「効いている」と誤読させる記述が plan / brief に無いか。scope 外の層 (単位 C / D2) を実装したふりにしていないか。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案、(e) 親 brief の (P) 番号との対応、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。scope 外だが real な所見は「裁定パッケージ候補」として別節にまとめろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数、must-fix 件数、(P1)〜(P6) の独立評価 (採用 / 却下 / 条件付き) を 10 行以内で書け。
