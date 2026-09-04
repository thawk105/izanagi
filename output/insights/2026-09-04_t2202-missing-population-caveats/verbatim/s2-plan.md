## 総括

編集対象は 8 file、数値主張は 35 組です。内訳は A=2、B=11、C=4、D=1、E=3、F=6、G=3、追加 I=5 です。  
brief の 19 組から有効な主張を 16 組追加し、誤った「24 反復」は対象から除外します。  
A〜G・I はすべて EOF 純追記を推奨します。F の段落直後挿入は既存の file:line 参照を壊すため採りません。  
`docs/paper-story/*.md` は該当 0 件、値の書き換え・削除・コード変更・テスト変更はありません。

## 主張一覧と挿入位置

母集団の根拠は、[一覧の正典 §4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-denominator-270/README.md:83)、[WAL 集計表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:76)、[欠測 attempt 表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:90)、[帰属表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:159)です。performance は全 238 反復中 read-heavy 18、そのうち `292d58f1dad8` の 3 反復が欠測 attempt の観測分です。完全性集計にはさらに両未完 attempt の legacy 各 1 件が入り、合計 5 観測が掛かります。

**A. [2026-08-31_t1905-b10-formal-run/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-08-31_t1905-b10-formal-run/README.md:140)**  
挿入は現 EOF 181 行の後です。

- A1 [147-148 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-08-31_t1905-b10-formal-run/README.md:147): 「中止 300 万件、commit 1690 万件、合計約 2000 万件」。read-heavy 高 commit 3 点の performance 13 反復、内訳は n=5、5、3。最後の n=3 が未 commit `constant-mu2` です。1690 万への関与は正典 97 行で明示され、300 万と約 2000 万も同じ反復の abort と commits 合計なので同じ母集団です。
- A2 [150-151 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-08-31_t1905-b10-formal-run/README.md:150): 「CPU/経過=1.0、48 コア中 47 コア遊休、5 時間で 15 点中 3 点」。request `965996` 全体の壁時計には未 commit 第4 attempt の legacy 1 と performance 3 の時間が入り、完了数は 3 変種のままです。15 点は構造数ですが、5 時間対3変種という進捗主張には欠測が掛かります。

**B. [2026-09-02_b10-trace-truncation/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:1)**  
挿入は現 EOF 279 行の後です。

- B1 [12-26、45、63-69、101、220-221 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:12): 「287 反復」「残る 197 反復」「287 回すべて一致・発火なし」。287 は legacy 49 + performance 238 で、未完 balanced の legacy 1、未完 read-heavy の legacy 1 + performance 3を含みます。197 も balanced 85 と read-heavy 22を含みます。
- B2 [148-149 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:148): 全238反復の `r=0.9991` と `r=0.4044`。
- B3 [150-152 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:150): campaign 別 `r(commits)=0.9826-0.9975` と read-heavy の `r(attempts)=0.997`。read-heavy 部分は n=18 中3が欠測 attempt 由来です。
- B4 [155-158 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:155): 回帰の切片 `-26.517`、commit 係数 `84.625`、試行係数 `-0.309`、`R²=0.998152`、試行費用「実質0」。母集団は performance 238。
- B5 [179-184 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:179): read-heavy n=18 の傾き `87.002`、切片 `-70.75`、RMSE `31.25`。n=18 中3が欠測 attempt 由来です。他3 campaign の単独行には掛かりません。
- B6 [186 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:186): 全体 `84.4 マイクロ秒/commit`。母集団は performance 238。
- B7 [189-192 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:189): 同一変種内 `r=-0.0213`、commit 振れ幅中央値 `0.93%`、所要振れ幅 `6.99%`。同節の performance 反復集計から出た統計として保守的に同じ但し書きを掛けます。
- B8 [194-195 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:194): 「read-heavy は write-heavy の約7倍」。対応3点の read-heavy は n=5、5、3で、比の再現は[一次資料 195-203 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:195)です。
- B9 [195-198 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:195): 高 commit 3変種の `16.83M-17.19M / 1346.9-1465.6秒`。3変種の一つが n=3 の未完 attempt です。adaptive と write-heavy の単独範囲には掛かりません。
- B10 [200-202 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:200): 「約2000万試行」と「1690万commit」の帰属。A1と同じ母集団です。
- B11 [235-236 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-trace-truncation/README.md:235): `5.61M / 414.6秒` と `16.90M / 1425.4秒` の比較。後者は `constant-mu2` の n=3 をまとめた値なので、比較全体に掛かります。

**C. [2026-09-02_paper-story-a6-certification/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_paper-story-a6-certification/README.md:96)**  
挿入は現 EOF 212 行の後です。

- C1 [100、186-200 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_paper-story-a6-certification/README.md:100): 「1回23分」と訂正後の `1346.9-1465.6秒、22.45-24.43分`。高 commit 3点、performance n=5、5、3です。
- C2 [100-101 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_paper-story-a6-certification/README.md:100): 「5時間で15点中3点」。request 全壁時計に未 commit 第4 attempt の4観測分が入ります。
- C3 [102-103、194-206 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_paper-story-a6-certification/README.md:102): 旧 `3.83時間・約3.1倍` と訂正後 `約4.07時間・約2.95倍`。いずれもC1の帯からの外挿です。
- C4 [164-168 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_paper-story-a6-certification/README.md:164): 「287反復すべて一致」。B1と同じ5観測を含みます。

**D. [2026-09-02_t1905-b10-multinode-design/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t1905-b10-multinode-design/README.md:28)**  
挿入は現 EOF 33 行の後です。

- D1 [32 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t1905-b10-multinode-design/README.md:32): 「約25時間」。request `965996` の約5時間5分を完了3変種で15変種へ外挿していますが、壁時計には未 commit 第4 attempt の legacy 1 + performance 3が入ります。

**E. [2026-09-02_t2229-t2230-verify-cost-erratum/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:10)**  
挿入は現 EOF 111 行の後です。

- E1 [14-15、29-34 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:14): `23分` と `1346.9-1465.6秒`。高 commit 3点の performance n=5、5、3です。
- E2 [15、18、38-49 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:38): `24.43分、4.07時間、2.95倍` と比較対象の旧値 `23分、3.83時間、3.1倍`。E1からの換算です。
- E3 [69-83 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2229-t2230-verify-cost-erratum/README.md:69): 「5時間5分、15点中3変種」。全壁時計には未 commit 第4 attempt の4観測分が入ります。

**F. [docs/b10-multinode-formal-run-design.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:1)**  
段落直後ではなく現 EOF 427 行の後へ純追記します。

- F1 [16-31、227-230 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:16): 「5時間5分・15中3」「CPU/経過=1.0・47コア遊休」「残り3時間半から5時間」。request 全体に未 commit 第4 attempt の4観測分が入ります。
- F2 [115-117 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:115): balanced の「6時間・14変種から約6時間半」。6時間壁時計には未 commit `c7c331ebe662` の legacy 1が入りますが、除数は完了14変種です。performance は0件です。
- F3 [120-122 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:120): 「約17M、1346.9-1465.6秒、79.6-86.0マイクロ秒/commit」。read-heavy performance 18反復中3が未 commit attempt 由来です。「24反復」は下記のとおり除外します。
- F4 [124-127 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:124): `14.0-16.2時間、1.48-1.71倍、66-72マイクロ秒/commit、1.1-1.3倍`。F3を入力に含む read-heavy 全体の外挿です。
- F5 [129-131、420 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:129): 「3変種で5時間5分、約25時間」とその再掲。D1と同じ母集団です。
- F6 [242-248 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/docs/b10-multinode-formal-run-design.md:242): 「287反復すべて certified」。B1と同じ5観測を含みます。

**G. [2026-09-03_t1905-b10-road-and-balanced/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:1)**  
P5を退けて対象へ戻し、現 EOF 280 行の後へ追記します。

- G1 [35-44 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:35): 「adaptive は commit が1/3」。高 commit 側3変種の一つが n=3 と表内で開示されていますが、この派生比率自体には但し書きがありません。
- G2 [71-79 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:71): `総commit 1.18-1.30G、41.0-44.3us、13.4-15.6時間、合計14.0-16.2時間`。read-heavy 4変種の観測と外挿に、performance n=3 の未 commit attempt が入ります。
- G3 [81-86、274 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md:81): `閾値66-72us、並列効果1.1-1.3倍、上振れ+2%、余裕約1.5倍`。G2からの派生です。

**I. [2026-09-02_t2191-verifier-parallel/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:1)**  
brief に無い追加 file です。現 EOF 231 行の後へ追記します。

- I1 [27-29 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:27): read-heavy 実測傾き `87.0`、検査器比率 `68-75%`、観測帯 `1346.9-1465.6秒`。87.0は read-heavy performance 18反復、帯は高 commit 3点 n=5、5、3です。
- I2 [28-33 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:28): `17M` への `1000-1210秒・約1213秒` 外挿。17Mという適用規模がI1の観測群から来ます。
- I3 [50-51 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:50): `17Mで約87GB`。I1の規模を使った記憶量外挿です。
- I4 [125-133 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:125): `420-500秒、検査器外240-340秒、660-840秒、13.7-17.5時間、end-to-end 1.7-2.1倍` と「12時間に入らない」。合成 trace の実測だけでなく、I1の旧 read-heavy 混合区間との差分を使います。
- I5 [184-200 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_t2191-verifier-parallel/README.md:184): `17Mは68万の25倍` と workers 別 `58.5-142GB`。17M規模をI1から取った記憶量外挿です。並列器自体の `2.2倍` など合成 trace 単独値には但し書きを掛けません。

**行参照の実測:** 対象 path に対する `README.md:<数字>` または `.md:<数字>` の参照がありました。`#L<数字>` 形は0件です。

- A: `b10-denominator-270/verbatim/{s2-plan.md,s3-lensB-quantitative-closure.md}`、`b10-missing-iterations-scope/verbatim/{s2-plan.md,s3-lensB.md}`、`b10-preflight-fixes/verbatim/s3-lens-a.md`
- B: `b10-denominator-270/verbatim/{s2-plan.md,s3-lensA-correctness-boundary.md,s3-lensB-quantitative-closure.md}`、`b10-missing-iterations-scope/verbatim/s2-plan.md`、`t2261-v8-cost-breakdown/verbatim/s2-plan.md`
- C・D: `b10-denominator-270/verbatim/{s2-plan.md,s3-lensB-quantitative-closure.md}`
- E・I: `t2261-v8-cost-breakdown/verbatim/s2-plan.md`
- F: `b10-denominator-270/verbatim/{s2-plan.md,s3-lensA-correctness-boundary.md,s3-lensB-quantitative-closure.md}`、`b10-missing-iterations-scope/verbatim/s3-lensB.md`、`b10-preflight-fixes/verbatim/s3-lens-b.md`、`t2266-backoff-static-tail/verbatim/s4-adjudication.md`
- G: 対象 path を伴う行番号参照は0件です。

このため insight への EOF 追記は妥当です。Fも段落直後へ挿すと現在の全後続行をずらすので、EOFにH2節を置き、各主張の現行節名と行を名指しする方が安全です。

## 但し書きの文面

**A**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **「中止 300 万件、commit 1690 万件、合計約 2000 万件」:** この値の母集団は read-heavy の高 commit 3 変種の performance 反復で、その一つは commit へ到達しなかった `constant-mu2` attempt (`292d58f1dad8`) の観測3反復である。値を無効にするものではなく、欠測を含まない母集団での再計算は行っていない。
- **「CPU/経過=1.0、48 コア中47コア遊休、5時間で15点中3点」:** request `965996` の壁時計には、commit へ到達しなかった第4 attempt の legacy 1反復と performance 3反復に使った時間も含まれる一方、完了数は3変種のままである。値を無効にするものではなく、その時間を除いた再計算は行っていない。
```

**B**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **「287反復」「残る197反復」「287回すべて一致・発火なし」:** 集計には、commit へ到達しなかった balanced attempt の legacy 1反復と、read-heavy `constant-mu2` attempt の legacy 1反復・performance 3反復が含まれる。値を無効にするものではなく、この5反復を除いた再計算は行っていない。
- **相関、回帰、単価の主張:** `r=0.9991 / 0.4044`、campaign別相関、回帰式と `R²=0.998152`、read-heavy の `87.002`、全体の `84.4`、同一変種内の `r=-0.0213` と振れ幅は、performance 238反復を全部または一部に使い、read-heavy 18反復中3反復が未 commit `constant-mu2` attempt 由来である。値を無効にするものではなく、その3反復を除いた再計算は行っていない。
- **「約7倍」、高 commit 帯、1690万commit、hard cap 比較:** 高 commit 3点の一つは、5反復中3反復だけが観測された未 commit `constant-mu2` attempt である。値を無効にするものではなく、この点を含まない母集団での比率・範囲・平均の再計算は行っていない。
```

**C**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **「1回23分」、1346.9-1465.6秒、22.45-24.43分、3.83時間・3.1倍と訂正後の4.07時間・2.95倍:** 高 commit 3変種の一つは、commit へ到達しなかった `constant-mu2` attempt の観測3反復である。値を無効にするものではなく、その3反復を除いた再計算は行っていない。
- **「5時間で15点中3点」:** 壁時計には未 commit 第4 attempt の legacy 1反復と performance 3反復の時間も含まれる一方、完了数は3変種のままである。値を無効にするものではなく、その時間を除いた再計算は行っていない。
- **「287反復すべて一致」:** 287反復には、未完 balanced attempt の legacy 1反復と、未完 read-heavy attempt の legacy 1反復・performance 3反復が含まれる。値を無効にするものではなく、この5反復を除いた再計算は行っていない。
```

**D**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **read-heavy の「約25時間」:** 元の約5時間5分の壁時計には、commit へ到達しなかった第4 attempt の legacy 1反復と performance 3反復に使った時間も含まれる一方、外挿の除数は完了3変種のままである。値を無効にするものではなく、その時間を除いた再計算は行っていない。
```

**E**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **23分、1346.9-1465.6秒、および24.43分・4.07時間・2.95倍への積み直し:** 高 commit 3変種の一つは、commit へ到達しなかった `constant-mu2` attempt の観測3反復である。値を無効にするものではなく、その3反復を除いた再計算は行っていない。
- **「5時間5分で15点中3変種」:** 壁時計には未 commit 第4 attempt の legacy 1反復と performance 3反復の時間も含まれる一方、完了数は3変種のままである。値を無効にするものではなく、その時間を除いた再計算は行っていない。
```

**F**

```markdown
## 欠測 attempt を含む母集団から出た数値主張の但し書き (2026-09-04、D1529)

> **§1・§5.1の「5時間5分・15中3」「CPU/経過=1.0」「47コア遊休」「残り3時間半から5時間」:** request `965996` の壁時計には、commit へ到達しなかった第4 attempt の legacy 1反復と performance 3反復に使った時間も含まれる。値を無効にするものではなく、その時間を除いた再計算は行っていない。

> **§4の balanced「約6時間半」:** 6時間壁時計には、commit へ到達しなかった `c7c331ebe662` attempt の legacy 1反復に使った時間も含まれる一方、外挿の除数は完了14変種である。値を無効にするものではなく、その時間を除いた再計算は行っていない。

> **§4追記の「約17M、1346.9-1465.6秒、79.6-86.0マイクロ秒/commit」と、そこから出した14.0-16.2時間・余裕・閾値:** read-heavy performance 18反復のうち3反復は、commit へ到達しなかった `constant-mu2` attempt の観測分である。値を無効にするものではなく、その3反復を除いた再計算は行っていない。

> **§4と§10の「3変種で5時間5分、約25時間」:** 元の壁時計には未 commit 第4 attempt の legacy 1反復と performance 3反復の時間も含まれる一方、外挿の除数は完了3変種である。値を無効にするものではなく、その時間を除いた再計算は行っていない。

> **§5.1の「287反復すべて certified」:** 287反復には、未完 balanced attempt の legacy 1反復と、未完 read-heavy attempt の legacy 1反復・performance 3反復が含まれる。値を無効にするものではなく、この5反復を除いた再計算は行っていない。
```

**G**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **「adaptive は commit が1/3」:** 比較対象となる高 commit 3変種の一つは、commit へ到達しなかった `constant-mu2` attempt の観測3反復である。値を無効にするものではなく、この点を含まない母集団での再計算は行っていない。
- **read-heavy の1.18-1.30G、41.0-44.3us、13.4-15.6時間、14.0-16.2時間、閾値・余裕の主張:** 外挿の入力には、performance 5反復中3反復だけが観測された未 commit `constant-mu2` attempt が含まれる。値を無効にするものではなく、その3反復を除いた再計算は行っていない。
```

**I**

```markdown
## 但し書き (2026-09-04、D1529) - 欠測 attempt を含む母集団から出た数値主張

- **read-heavy実測傾き87.0、検査器比率68-75%、17Mで1000-1213秒、および13.7-17.5時間・end-to-end 1.7-2.1倍:** 入力となる read-heavy performance 18反復のうち3反復は、commit へ到達しなかった `constant-mu2` attempt の観測分である。値を無効にするものではなく、その3反復を除いた再計算は行っていない。
- **17Mで約87GBとworkers別58.5-142GB:** 17Mという適用規模は、上記の欠測 attempt を含む read-heavy 観測から採った値である。値を無効にするものではなく、欠測を含まない母集団から規模を取り直した再計算は行っていない。
```

## brief への異議

- **A〜Fだけでは閉じません。** Gの表中 `3 (打ち切り)` は元観測の開示として有効ですが、そこから離れた1/3比、全体所要、閾値、余裕には主張単位の但し書きがありません。P5はD1529の「主張ごと」と両立しないため退けます。
- **Iが完全に抜けています。** T-2191 report は欠測を含む87.0、1346.9-1465.6秒、17Mを、費用比、所要、記憶量へ流しています。材料 report なので対象です。
- **「24反復」は誤りです。** F 121行とG 29・42行にありますが、Gの表は performance `5+5+5+3=18`、一次資料は read-heavy `verify_done=22` と明記しています。legacy 4を足しても22であり24にはなりません。この値へ「無効ではない」というD1529但し書きは付けず、値の訂正を行わない本waveでは未解決誤りとして残します。
- **briefはBの閉包が不足しています。** 287/197の完全性主張、campaign別相関、同一変種内統計、1690万と約2000万の再掲も同じ母集団です。C・Fの287主張、Eの5時間5分、FのCPU比と残時間も追加が必要です。
- **P1には同意します。** 本依頼自身がFをA〜Fへ明示しており、対象化の根拠は十分です。
- **P2はinsightについて妥当、Fについて修正が必要です。** Fにも多数の外部file:line参照があるため、FもEOF純追記に統一します。
- **P3、P4、P6は妥当です。** Hは[約7倍の直後](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:191)と[利用条件表](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:249)ですでに明示済みです。「15認証単位」は[構造数と確定済み](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/output/insights/2026-09-02_b10-denominator-270/README.md:99)なので除外します。
- **P7は基本形として採用します。** ただしperformance、全job壁時計、balanced legacy、287完全性を同じ定型へ押し込まず、上記のように母集団を書き分けます。

## scope 外に残る担い手

- `docs/decisions.md`: D1480、D1485、D1489、D1509、D1529、D1554。D1554にも `1346.9-1465.6秒、4.07時間、2.95倍` が残ります。
- archive worklog: `worklog-phase3-0902-1186.md`、`1187.md`、`1189.md`、`1190.md`、`1197-1198.md`、`1211.md`、`worklog-phase3-0903-1223.md`。
- `docs/worklog.md`: 現在はT-2202の持ち越しポインタを担いますが、検索した数値主張本体はありません。
- `output/insights/**/verbatim/`: A〜F・Iへの行番号参照を多数持ちますが、凍結逐語なので編集しません。
- `docs/paper-story/*.md`: 指定語の静的検索で該当0件なので変更しません。
- `2026-09-02_b10-denominator-270/README.md`とHはscope内の材料ですが、すでに母集団と欠測の掛かり方を主張単位で明示しているため変更0です。

P3との矛盾はありません。D1529は対象文書内で但し書きを切る単位を定めるもので、今回の明示対象を全履歴文書へ拡張する裁定ではありません。Fは今回の依頼が直接A〜Fに含めた例外です。

## 受入

親が編集後に実走するものは次です。

- `python3 tools/check_docs.py`
- `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py`
- `python3 tools/run_tests.py orchestrator/tests/test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command`

根拠は、`test_check_docs.py` の [`test_real_repo_clean`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/orchestrator/tests/test_check_docs.py:12475)が実repoへ無引数checkerを掛けること、`test_campaign_import_invariant.py` が[非archiveのdocs Markdownを列挙](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/orchestrator/tests/test_campaign_import_invariant.py:994)し、[実文書の禁止された旧commandを検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2202-missing-population-caveats/orchestrator/tests/test_campaign_import_invariant.py:1233)することです。後者はFの変更に対応します。こちらではread-only指定に従い、テストは実走していません。