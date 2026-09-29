# [T-2872] MOCC read-heavy の stock の G2 は MOCC 本体の欠陥 — validation が「版の読み」と「lock 状態の読み」を別々に行う隙間に他の取引の書き込みと解錠が入り、両方が commit する。trace 無しの build でこの割り込みを 112 走すべてで直接観測した。G2 の witness 5 件のうち 2 件は片側の辺でこの割り込みを直接観測と一致させ、残る 3 件も順序の論証からこの割り込みと推論できる (一致なし 0 件)

authority: none
default_effect: no-state-change

- 依頼 (逐語): `verbatim/request.md`。段 1 brief: `verbatim/s1-brief.md`。段 4 裁定と本走の事前登録: `verbatim/s4-ruling.md` (追記 1 が本走の条件)。開始 gate: `verbatim/startup-gate.log` (rc=0、起点 local main `035fc11fa`)。
- 一次資料: `output/insights/2026-09-27/t2868-mocc-g2-cause/README.md`。既往: `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` §3・§7、`output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` §3・§6、`output/insights/2026-09-19/mocc-witlight-arm-run/README.md`。裁定 D2277 項 2。
- **repo のコード変更なし。** 計器 (診断 patch) と runner は Codex author が書き、repo に入れていない。job dir `/work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/` と保全先 `/work/1/SFC/tanab/izanagi-repro-archive/t2872-mocc-g2-split-20260929/` (G2 の 5 run の trace・TSV・verifier JSON と `MANIFEST.sha256`)。sha256: runner `t2872_probe.py` `50c16ab01a321487e8831bdc640c9dec292d84eb4090ba3c59957bc88ad59e42`、patch `mocc-g2-probe.patch` `ff243794b33e360eba952c552a716b1118a084cc12e31aeca5b2ac94b707cfc5`、arm 定義 `arms-t2872.json` `807c584816c0d48d0bc0c6be7277c1fed2e279832f1ba96ee0e62210a5256e19`。
- 用語: 「割り込み」は、読み手の validation の 2 つの load (版の読みと lock 状態の読み) の間に、他の取引の版の公開 (publish) と解錠が入ることを指す (OS の割り込みではない)。「cell」は測定条件、「stock」は元の設定の MOCC、「pin C」は固定した CCBench の版、「hit」は計器が記録した事象、「受理集合」は検査を通る実行の集合。
- 本文は**非 certifying の観測記録**であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。t2849・t2868 の値と判定は変えていない (規律 2・7)。verifier・判定・受理集合は変えていない。

## 0. 結論 — 切り分け表

| 分岐 | 判定 | 根拠 (節) |
|---|---|---|
| (iii) MOCC 本体の欠陥 | **本体の欠陥と判定する。** validation の read set 走査は版を読んで比べた後に、別の load で lock 状態を読む。この間に他の取引が同じ record を publish して解錠すると、古い版を読んだ取引がそのまま commit する。trace 無しの build でこの割り込みの commit を 112 走すべて・計 4,284 件観測した。trace 有りの build の G2 witness 5 件のうち 2 件は、片側の rw 辺でこの割り込みの直接観測と一致した (class A)。残る 3 件は lock 読みの後の再読でだけ一致し (class B)、§2 の順序論証からこの割り込みと推論できる。一致なし 0 件・判定不能 0 件。事前登録の R2 (全 witness が class A で一致) は満たさない | §2・§5 |
| (iv) trace hook の記録誤り | **観測した 5 件の当該辺では否定する材料を得た。全般の排除ではない。** 一致した辺の key と上書き版は、trace の書き出しと独立な validation 内の load が観測した値と一致した。ただし key と「読んだ版」は trace と同じ read set 由来で、独立ではない | §5・§6 |
| trace hook の観測者効果 | **機序を作ってはいない。** 割り込みは trace 無しで起きる。trace は割り込みの出現を commit あたり約 5 分の 1 に減らしていた (5.3×10⁻⁶ 対 9.7×10⁻⁷) | §5 |

- 5 件のうち 2 件は「版の再読 (Vmid) が相手の書いた版を見た」確実な一致 (class A)。
- 残る 3 件は「lock 読みの後の再読 (V3) で相手の版を見た」一致 (class B)。この 3 件でも、§2 の場合分けと「相手側に割り込みの観測が無い」ことから、割り込みは読み手の Vmid と lock 読みの間に入ったと推論できる (直接観測ではない)。
- 5 件とも、割り込みを受けた読み手の commit tid は「上書きした相手の版 + 1」だった。validation の最後の再読 (`max_rset_` の更新) で相手の新しい版を取り込み、相手より後ろの tid を取っている。既往の witness の「同 epoch・tid 差 1〜3」と同じ形である。

## 1. 問いと範囲

- 問い: t2868 で MOCC read-heavy (48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒、pin C `68106660…`) の stock が性能構成の検査で出した G2 (3/109) を、(iii) MOCC 本体の欠陥か (iv) trace hook の記録誤りかに切り分ける (D2277 項 2)。
- 範囲外: CCBench の修理 (T-2854 の整形 commit と `cc/mocc/transaction.cc` が重なる)、pin 前進、上流への送信 (D16)。gate・検査・台帳・一般化の追加。
- 既往との差 (純増): 既往の計器 (T-1943 の witness、T-2798 の軽量 witness) は trace 有りの build 上で payload の出所を識別する形で、G2 の出た反復で一度も発火しなかった。T-2779 の診断 patch は 2 変更を束ねた受理集合の縮小で、機序そのものは観測していない。**trace 無しの build での直接観測と、witness ごとの独立な観測との突き合わせは本 wave が初めて。**

## 2. 機序の導出 (pin C の現物、行は `cc/mocc/transaction.cc`)

- validation の read set 走査は、版の load (1035-1036) → 比較 (1037-1045) → lock 状態の load (1049 `ldAcqCounter() == W_LOCKED`) → `max_rset_` の更新で版をもう一度読む (1063)。MOCC は lock を版とは別の word (読み書き lock) に持つので、1 回の load で「未施錠かつ版が同じ」を確かめられない。
- 書き手は write set を施錠 (1016-1026) してから自分の read set を検査し、writePhase で publish (1259) → 全 lock を解錠 (1271 `unlockCLL()`)。
- 2 取引の長さ 2・両辺 rw の閉路 (T1 が x を読み y を書く、T2 が y を読み x を書く、x≠y、両者とも楽観読み、読んだ key を自分では書かない) が両方 commit するには、**一方の validation の [版 load, lock load] の間に、相手の当該 key の publish と解錠が両方入る必要がある**。
  - T1 の lock load が T2 の x の施錠より前なら、T2 の y の検査は T1 の y の施錠より後になる。T2 が通るには T2 の窓に T1 の publish と解錠が要る。
  - T1 の lock load が T2 の解錠より後なら、T1 が古い版を見たことから T1 の窓に T2 の publish と解錠が要る。
  - 段 2 plan・段 3 相談 A がこの場合分けを現物で検算した。
- 被覆境界: 温度が高い record の read lock、read phase での write lock (update 460・delete 567)、自己 write、node set 検証、INSERT/DELETE を含む取引には、この論証をそのまま広げない。本 wave の witness 5 件はすべてこの前提を満たした (`verbatim/p1-applicability.txt`: 別 key を読み、読んだ key を自分では書かず、互いに相手の読んだ key を 1 つずつ書く。X/I/P 行 0)。

## 3. 計器 (観測者効果の小さい診断 patch)

- 独自 macro `IZANAGI_MOCC_G2_PROBE` (既定 0、`#if TRACE` の外) で囲み、macro off の前処理後の source は template 適用済みの pin C と一致する。実 build の compile 命令で `-P` 前処理の出力を比べ、sha256 が一致することを本走の各 job の build 前に確かめた (runner が不一致なら停止する)。
- validation の read set 走査で、版の比較を通った直後・lock 条件の前に版をもう一度 acquire load する (**Vmid**、窓の中の新規 load 1 つ)。lock 条件は既存の load を local に受ける (load 回数は同じ)。`max_rset_` の更新は元の式のまま、その後に版をもう一度読む (**V3**、窓の外)。validation・lock・publish・abort の判断と commit tid は変えない。
- **class A** = lock が未施錠で通過し、Vmid の (epoch, tid) ≠ 最初の版 V1。版の読みと lock の読みの間に他者が publish し、lock を読んだ時点で解錠済みだった確実な観測である。**class B** = Vmid = V1 だが V3 ≠ V1 (lock 読みの後の publish を含む曖昧な観測)。自己施錠の item は数えない。
- hit は validation 中は取引ごとに保留し、abort で捨て、commit 時に (thid, commit epoch, commit tid) を付けて thread ごとの固定長配列へ移す。出力はプロセス終了時 (測定区間の外)。溢れは件数で残す (本走は 0)。
- 観測者効果: 検査に到達した read item ごとに load 2 (Vmid・V3) と比較、hit 時だけ記録と key の複写。Vmid は窓の中に入るので窓を 1 load 分広げる。

## 4. 実走

- build 3 本 (比較 harness の stock と同じ configure argv: Release・sanitizer OFF・gcc-11/g++-11・`-DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_KEY_SORT=0 -DCCBENCH_TEMPERATURE_RESET_OPT=1`、template `patches/silo-backoff-fixed.patch`):
  - **T** = TRACE=1 + probe (verifier で検査)
  - **N** = TRACE=0 + probe (trace 無しで割り込みを数える)
  - **P** = TRACE=0 の素 (probe の観測者効果の対照)
- workload: `-ycsb_tuple_num=1000000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=95 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。
- batch = T 4・N 4・P 2 の benchmark を順番を回して直列に走らせた後、T の 4 trace を並列に verify (benchmark と verifier は重ねない)。verifier の argv は t2868 の保全 inventory と同じ形。
- 本走は結果を見る前に固定した 2 job × 14 batch (`verbatim/s4-ruling.md` 追記 1)。2 job とも全 batch を完走した (欠測 0)。
- smoke (`35579.nqsv`) は本走に合算しない (T 4・N 4・P 2、G2 0/4、N の class A 156)。その前の smoke 3 回は runner の欠陥で build 前後に止まった (§8)。
- 計算: Elapse は smoke `35474` 28 s・`35492` 29 s・`35505` 34 s・`35579` 267 s、本走 `35594` 3,179 s・`35595` 3,149 s。計 6,686 s = **1.86 node 時間** (ユーザー確認の線 2 node 時間の内側)。

## 5. 結果

- **R0 (判定不能):** T・N・P の全 280 走で 0 (溢れ 0、TSV の欠落・不整合 0、hit の C 行の欠落 0、benchmark・verifier の失敗 0)。

| arm | 走 | commit 平均 (範囲) | 検査した read item | class A | class B | A / commit | A が出た走 | G2 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| T (TRACE=1 + probe) | 112 | 5,650,766 (5,534,149〜5,766,297) | 6,042,813,966 | 616 | 945 | 9.7×10⁻⁷ | 112 / 112 | **5 / 112** |
| N (TRACE=0 + probe) | 112 | 7,175,519 (6,932,282〜7,389,505) | 7,670,748,800 | **4,284** | 14,252 | 5.3×10⁻⁶ | **112 / 112** | — |
| P (TRACE=0 素) | 56 | 7,233,623 (6,994,782〜7,449,379) | — | — | — | — | — | — |

- **R1:** trace 無しの build (N) で class A が 112 走すべてに出た (計 4,284 件)。trace 無しの build で、validation の版の読みと lock の読みの間に他者の publish と解錠が入り、その取引が commit した実例がある。
- **G2:** T で 5/112 走 = 4.5% (Clopper–Pearson 95% 区間 1.5〜10.1%)。各走の cycle は 1 件、witness は長さ 2・両辺 rw。t2868 の harness 走 (同 pin・同 argv・同 cell、probe 無し) の 3/74 とは同時刻の対照ではなく、比べない。
- **R2・R3 (witness ごとの突き合わせ、`verbatim/witness-detail.txt`):**

| run | 2 取引の commit 版 | 割り込みを受けた読み手の辺: key、読んだ版 → 上書き版 | probe の観測 (V1 / Vmid / V3) | 一致 | 逆向きの辺 |
|---|---|---|---|---|---|
| main-a 0034 | T5092734 (67,4821)・T5092727 (67,4820) | T5092734 が key 0: (67,4806) → (67,4820) | (67,4806) / (67,4806) / (67,4820) | class B | key 2: hit なし |
| main-a 0050 | T971187 (14,715)・T971176 (14,714) | T971187 が key 1: (14,704) → (14,714) | (14,704) / **(14,714)** / (14,714) | **class A** | key 0x40: hit なし |
| main-a 0054 | T2819245 (38,2170)・T2819239 (38,2167) | T2819245 が key 0: (38,2164) → (38,2167) | (38,2164) / **(38,2167)** / (38,2167) | **class A** | key 1: hit なし |
| main-a 0062 | T4385819 (58,298)・T4385811 (58,297) | T4385819 が key 5: (58,290) → (58,297) | (58,290) / (58,290) / (58,297) | class B | key 0: hit なし |
| main-b 0079 | T3857485 (52,4397)・T3857483 (52,4396) | T3857485 が key 0: (52,4393) → (52,4396) | (52,4393) / (52,4393) / (52,4396) | class B | key 0xb: hit なし |

  - 5 件すべてで片側の辺に一致がある。class A 2 件、class B だけ 3 件、一致なし 0 件、判定不能 0 件。事前登録の R2 の「全 witness が class A で一致」は満たさない (`R2_all_witnesses_status = not_all_A`)。
  - class B だけの 3 件: 逆向きの辺の読み手に hit が無い。割り込みは必ず lock 読みより前の publish なので、そこで起きていれば V3 ≠ V1 として A か B に記録されたはずである (溢れ 0)。したがって §2 の場合分けでは、割り込みは class B 側の読み手の窓にあり、Vmid = V1 なので **Vmid と lock 読みの間** (load 2 つの間) に publish と解錠が入ったことになる。これは §2 の論証と probe が漏れなく記録したことを前提にした推論で、直接観測ではない。
  - 割り込みを受けた読み手の commit tid はどれも上書き版 + 1 だった (0034: 相手 (67,4820) → 読み手 (67,4821) など)。
- **観測者効果:**
  - probe: commit 平均 N 7,175,519 対 P 7,233,623 (N が 0.8% 少ない、標準偏差は N 86,617・P 104,987)。窓の中の load が割り込みの頻度をどれだけ変えたかは、この比較からは分からない (P は割り込みを数えられない)。
  - trace: class A は commit あたり T 9.7×10⁻⁷ 対 N 5.3×10⁻⁶。trace 有りの build は write phase で全 write lock を持ったまま C/R/W 行を書くので、lock の保持が延び、割り込みの代わりに lock 検査での abort が増える方向に働くと考えられる (T-2774 §1 の観測者効果の仮説と同じ向き、機序は未検証)。

## 6. 解釈の上限

- **言えること:** pin C の MOCC は、この cell で、validation の版の読みと lock の読みの間に他の取引が publish と解錠を終える割り込みを、trace 無しの build で頻繁に許して commit する。観測した G2 の 5 件のうち 2 件は片側の辺でこの割り込みの直接観測と一致し (class A)、3 件は class B の一致と §2 の場合分けからの推論でこの割り込みに帰着する。一致しない witness は無かった。事前登録の R2 (全件 class A) は満たさず、R3 の区分 (class B だけ 3 件) に当たる。静的な順序論証 (§2)、trace 無しでの直接観測 (R1)、witness との突き合わせ (class A 2 件の直接一致と class B 3 件の推論) が同じ機序を指すので、本体の欠陥と判定する。
- **言えないこと:**
  - (iv) の全般の排除。key と読んだ版は trace と同じ read set 由来である。
  - class B だけの 3 件の割り込みの位置の直接観測 (推論に留まる)。
  - trace 無しの build で G2 (閉路) が起きていること。N は閉路を検査しない。割り込みは閉路の必要条件で、十分条件ではない (他方の取引が相手の書く key を読んでいなければ閉路にならない)。
  - torn read の経路 (read phase の cold 読み、T-2774 §3 (i)) の有無。版の閉路は validation の窓だけで説明がつき、本計器は torn read を検査しない。
  - verifier の版順序の仮定 ((epoch, tid) の辞書順) の検証。witness の辺は verifier と同じ仮定で読んでいる。
  - probe の窓の中の load が割り込みの頻度をどれだけ増やしたか。
- 陰性・非有意の扱い: 本 wave に陰性の主張は無い。

## 7. CCBench (MOCC) 側の所見 (`output/README.md` の形式)

- **発見:** pin C (`68106660…`、e9e477ca + X/P 計装) の MOCC (RWLOCK) の validation は、read set の各 item について版の比較と lock 状態の検査を別の load で行う。この間に他の取引が同じ record を publish して解錠すると、読み手は古い版を読んだまま commit し、さらに `max_rset_` の再読で相手の新しい版を取り込んで相手より後ろの commit tid を取る。2 取引がこれを片側で起こすと、長さ 2・両辺 rw の G2 (write skew) が commit される。観測した G2 5 件のうち 2 件はこの割り込みの直接観測と一致し、3 件は推論で帰着した。trace の記録誤り (iv) は当該辺では観測と矛盾しないが、全般には排除していない。
- **再現条件:** 48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒、stock genome (`BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`)、Release・gcc-11。trace 無しの build で割り込みの commit は 1 走 (約 718 万 commit) あたり平均約 38 件。trace 有りの build の性能構成の検査で G2 は 5/112 走。
- **該当コード (pin C の `cc/mocc/transaction.cc`):** validation の read set 走査 1033〜1063 行 (版 load 1035、比較 1037、lock load 1049、`max_rset_` 1063)。書き手の publish 1259、解錠 1271。
- **仮説 (機序):** Silo は版と lock bit を同じ word に持つので 1 回の load で「未施錠かつ版が同じ」を確かめられる。MOCC は lock を別の word (読み書き lock) に移したが、検査は「版 → lock」の 2 回の load のままで、その間の変化を見ない。§2 の場合分けのとおり、この隙間が閉路の必要条件になる。
- **修理方針 (次の一手、本 wave では実装しない):**
  - 最小の修理は、read set の各 item で lock 状態を読んだ後に版を読み直し、最初の版と違えば abort すること (既往 T-2779 の診断 patch の validation 側と同じ形。T-2779 では cold 側 abort と束ねて 5/120 → 0/120)。lock を先に読んでから版を比べる順序の入れ替えも同値の候補で、どちらを採るかは修理 wave で上流 Silo の検査と照らして決める。`max_rset_` は再読でなく検査した版から取る。
  - いずれも受理集合を縮める方向の変更であり、正しさゲートは緩めない (規律 2)。
  - 検証: 本 wave の計器と cell を修理版で走らせ、commit 側の class A が 0 になること、T で同じ反復数 (112) の G2 が 0 件であることを確かめる (112 走で 0 件なら率 4.5% の帰無は片側で強く棄却される)。
  - CCBench の変更は Codex author、CCBench の CI (build・clang-format 14) を通す (D2277 項 1・2)。T-2854 の整形 commit と同じ file に触れるので、その後 (C2' 系) に乗せる。pin 前進は D2277 項 1 の順序に従い、修理後の版で測り直すかは修理が pin に入る時点で示す (D2277 項 2)。
- **CCBench 論文・既往との関係:** 既往の stock MOCC の G2 (T-1892・T-2774・T-2779、10,000 record・rr50) と同じ形の witness である。上流報告 (T-2791) は送信済み (D2272 項 8)。本 wave の機序の特定を追加で報告するかは人間の判断。
- **還元判断: ユーザー確認待ち。** 上流への報告・PR は人間の判断 (D16、D2148 項 13)。AI は構造化までとした。

## 8. 段の経過と所見

- 段 2 plan (read-only 1 本) → 段 3 相談 2 本 (A 機序と判定規則、B 過剰・費用) → 段 4 で所見をすべて real と裁定した。主な修正は次のとおり。
  - 親 brief の計器は、`max_rset_` の再読 (lock 読みの後) を窓の観測に使っていた。窓の外の publish も拾うので、窓の中に Vmid を足した (相談 A)。
  - 判定規則の「(iv) を否定」を「当該辺で独立な観測と一致、全般は排除しない」に弱め、判定不能 (R0) を先に分けた (相談 A・B)。
  - verify を batch ごとにし、反復数を結果の前に固定した (相談 B)。
- 段 5: Codex author 1 本 (1 回目は model の混雑で途中終了、継続で完成)。
- 段 6: 親の監査で must-fix 4 件 (`#line` のファイル名と行番号、verify の時期、C 行索引の大きさ、ccbench の作業木) → fix1。read-only レビュー 1 本の must-fix 3・should 2 (class A/B に lock 未施錠を要求、benchmark 失敗等を R0 に、verifier の判定不能と報告上限超えを別会計、並列上限、失敗時の trace 保全) と smoke の実測欠陥 3 件 (compile 命令が 4 target 分ある、前処理の比較が空行を含む、`-Werror=sign-compare`) → fix2〜fix4。smoke は 1 投入で 1 欠陥ずつ見つかり 4 回目で完走した。
- 変異 matrix: repo の実装面の差分が 0 なので免除 (DW-S04)。計器の機構は selftest 34 項目 (結合・一致判定・判定不能の正例と負例、実 `g++-11` での前処理比較の正例と負例) と、本走の各 job の build 前の前処理一致検査で確かめた。
- 段 6 の事実の再抽出レビュー (read-only 1 本): 各 arm の数値・区間・Elapse・witness 表 5 行・smoke の値は一次資料と一致した。所見 5 件 (`max_rset_` の行番号 1062→1063、§6 の R2 表記が未達を隠す、題名・§0・§6・§7 で class A の直接一致と class B の推論を分ける、用語の説明、裁定原文の照合) をすべて real とし、本文を直した。裁定原文 (D2272 項 8・D2277 項 1・2) は親が decisions で照合した。
