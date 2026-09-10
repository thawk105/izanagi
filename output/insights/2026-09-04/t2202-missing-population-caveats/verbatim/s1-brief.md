# 段 1 brief — [T-2202] 欠測母集団由来の数値主張に但し書きを付ける (親、2026-09-04)

## scope と確定裁定
- D1529 (ユーザー裁定 2026-09-03、逐語は同 dir の `d1529.md`) の実装。欠測 attempt を母集団に含む派生数値主張へ、**主張ごとに**但し書きを付ける。単位は文書でなく「数値主張とその母集団」。
- 欠測 attempt の実体: read-heavy 変種 `292d58f1dad8` (`constant-mu2`)。commit へ到達しなかった attempt の観測分 legacy 1 + performance 3 反復が集計に入っている。balanced は `c7c331ebe662` の legacy 1 件だけ (238 回帰には 0 件)。一覧の正典は worktree の `output/insights/2026-09-02_b10-denominator-270/README.md` §4。
- 対象 (command 引数): `docs/paper-story/` と材料レポート (`output/insights/*/README.md`。`verbatim/` は凍結逐語で対象外)。
- 実測: `docs/paper-story/*.md` に該当主張は 0 件 (grep `70.0-87.0|23 分|1690 万|25 時間|約 7 倍|84.4|0.9991|6 時間半|23 時間|マイクロ秒/commit`)。paper-story は「変更 0」を記録するだけ。
- 成果物影響 (DW-G05): 放置すると、欠測を含む母集団の値が含まない値と同じ顔で材料レポート → paper へ入り、読み手が根拠の強さを区別できない。値そのものは変わらない。
- 不変条件: 規律 2 を緩めない。過去の値・判定を書き換えない (規律 7、削除 0 行)。gate・検査・台帳・一般化を足さない。実装面 0 → docs-only、親が本文を編集 (D95)。変異 matrix は実装面 0 で免除。

## 変更面の実アンカー表 (file → 主張 → 母集団 → 欠測の掛かり方)
- A. `output/insights/2026-08-31_t1905-b10-formal-run/README.md` 節「所要時間の内訳 (実測)」: 「commit が 1690 万件」 (read-heavy 飽和 3 点の performance 反復、うち constant-mu2 は n=3)、「5 時間走って 15 点中 3 点」 (壁時計には未 commit 4 変種目の時間を含む)。
- B. `output/insights/2026-09-02_b10-trace-truncation/README.md` 節「所要は commit 数に…」以下と「所要の内訳と、並列化への入力」: r=0.9991 / r=0.4044、回帰 `-26.517 + 84.625 × commit − 0.309 × 試行` (238 反復)、campaign 別回帰表の read-heavy 18 反復 87.002、「84.4 マイクロ秒/commit」、「約 7 倍」、「3 変種 16.83M-17.19M / 1346.9-1465.6 秒」、「16.90M commits / 1425.4 秒」。母集団は performance 238 反復 = read-heavy 18 (うち 3 が欠測 attempt の観測分)。
- C. `output/insights/2026-09-02_paper-story-a6-certification/README.md` 節「walltime を 06:00:00 から 12:00:00 へ変えた理由」: 「1 回 23 分」「5 時間で 15 点中 3 点」「max 23 分で 3.83 時間」。同 file 追記訂正 (2026-09-03) の「3 変種 1346.9-1465.6 秒」「約 4.07 時間」「約 2.95 倍」も同じ母集団。
- D. `output/insights/2026-09-02_t1905-b10-multinode-design/README.md` 節「この wave が主張しないこと」: 「約 25 時間」 (壁時計 5 時間 5 分 = 未 commit 4 変種目の時間込み、除数は完了 3 変種)。
- E. `output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md` §2: 「3 変種 16.83M-17.19M / 1346.9-1465.6 秒」と積み直し値 (24.43 分 / 4.07 時間 / 2.95 倍)。
- F. (P1) `docs/b10-multinode-formal-run-design.md` §4 付近: 「約 6 時間半」 (balanced、未完 attempt の legacy 1 回を含む 6 時間壁時計を 14 変種で外挿)、「3 変種で 5 時間 5 分 / 約 25 時間」、2026-09-03 blockquote の「24 反復ぶん / 1346.9-1465.6 秒 / 79.6-86.0 / 約 14.0-16.2 時間」 (24 反復に欠測 attempt の 3 反復を含む)、末尾「主張しないこと」の「約 25 時間」。
- G. `output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md` 節「read-heavy の実規模の所要」: 表が行ごとに「3 (打ち切り)」を明示。「全 24 反復」。
- H. `output/insights/2026-09-02_b10-missing-iterations-scope/README.md`: 「約 7 倍」再現表が n=3 と「3 点のうち 1 点は欠測 attempt の 3 反復から出ている」を既に明記。

## 親の provisional 裁定 (攻撃対象)
- (P1) 設計文書 F は引数の「材料レポート」に字義では入らないが、生きた非 archive 文書で、D1529 の単位は主張なので対象に含める。
- (P2) 形: insight README (A〜E) は既存本文を 1 byte も変えず、EOF に「但し書き (2026-09-04、D1529) — 欠測 attempt を含む母集団から出た数値主張」節を純追記し、主張ごとに 1 項 (位置は節名、母集団、欠測の掛かり方、値は無効でない) を書く。理由: C の追記訂正が示す先例 (規律 7)、行範囲参照の保全。設計文書 F は既存 blockquote 様式で当該段落の直後に inline。
- (P3) `docs/decisions.md` (D1480/D1485/D1489/D1509)、archive worklog 1186/1187/1189/1190、現行 worklog は本 wave の scope 外 (引数の対象指定)。残る担い手として段 7 に列挙する。
- (P4) H は既に但し書き済みとして追記しない。(P5) G は行単位で「打ち切り」を開示済みとして追記しない。
- (P6) 「15 認証単位」は構造数で対象外 (D1529)。
- (P7) 但し書きの定型 (案): 「但し書き (D1529): この値の母集団には、commit へ到達しなかった read-heavy `constant-mu2` attempt (`292d58f1dad8`) の performance 3 反復が含まれる。値を無効にするものではなく、欠測を含まない母集団での再計算は行っていない。」 主張ごとに母集団の差 (壁時計、legacy、balanced) を書き分ける。

## 分割方針・受入
- docs-only、親が編集。段 2 plan 1 本 (read-only codex)。段 3 敵対 2 本 (レンズ A: 母集団帰属の正しさと閉包、レンズ B: 但し書きの形・規律 7・参照保全・scope)。段 6 は焦点レビュー 1 本。
- 受入: worktree で `python3 tools/check_docs.py` と docs 関連テストを親が実走。
