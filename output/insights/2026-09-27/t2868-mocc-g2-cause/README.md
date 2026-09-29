# [T-2868] MOCC read-heavy の G2 は literal を差し込まない stock でも同じ形で出る — verifier の判定は記録された trace と一致し、差し込みは待ち時間 1 行だけ。原因は MOCC 側 (本体の実装か trace の記録) に絞られた

authority: none
default_effect: no-state-change

- 依頼 (逐語): `verbatim/request.md`。段 1 brief: `verbatim/s1-brief.md`、段 4 裁定: `verbatim/s4-ruling.md` (段 2 plan と段 3 の相談 2 本の所見 12 件をすべて採用)。開始 gate: `verbatim/startup-gate.log` (rc=0、起点 local main `339d7c188`)。
- 材料: `output/insights/2026-09-27/t2849-mocc-conn/README.md` §4 と保全 trace。既往: [T-2774] [T-2779] [T-2780] と D2148 項 13、上流報告案 `output/insights/2026-09-20/t2791-mocc-upstream-report/`。
- **repo のコード変更なし。** 再検査の probe (`t2868_recheck.py`、Codex author、sha256 `ca989f99ca94fd97dd1bd1a03f366d0bb14b15951f91e792dec5957cec112a82`) は repo に入れず、branch `t2868-probe-author` (commit `d86ec8f48`) と job dir に置いた。追加走は着地済みの比較 harness をそのまま使った。
- job dir (repo 外、probe・投入 script・件ごとの全出力・submit 木): `/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/`。追加走の trace 保全: `/work/1/SFC/tanab/izanagi-repro-archive/t2868-mocc-stock-20260927/` (35 GB)。
- 本文は**非 certifying の観測記録**であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。元の 6 件の reject と t2849 の判定は変えていない (規律 2・7)。

## 0. 結論 — 切り分け表

| 分岐 | 判定 | 根拠 (節) |
|---|---|---|
| (i) verifier の誤検出 | **記録された trace を前提とする限り排除。** 候補 6 件と stock 3 件の計 9 件すべてで、保全時と同じ版の verifier を同じ引数で再実行して同じ witness が出た。verifier を使わない生の行の照合でも 2 本の rw 辺が成立した | §2・§3 |
| (ii) literal 差し込みによる source の直接変更 | **排除。** 候補 6 件の保全 patch は、変更 file が `cmake/Options.cmake` と `include/backoff.hh` の 2 つだけで、template との差は hole 内の `double now_backoff = <値>;` の 1 行だけ。validation・lock・trace 記録の source には触れていない。**待ち時間の変化が並行実行の結果 (G2 の起き方) を変える経路は、この照合では排除していない** | §2 |
| (ii') literal (待ち時間の変更) が G2 の必要条件 | **この cell では排除。** literal を差し込まない stock (適応 backoff) の 16 slot で、性能構成 74 反復中 3 件に同じ形の G2 が出た | §3 |
| (ii'') literal が G2 の率を上げる | **差は検出されない。** 候補 6/119 (5.0%) 対 stock 3/109 (2.8%、t2849 の 0/35 を含む)、両側 Fisher p = 0.50 | §3 |
| (iii) MOCC 本体の欠陥 | **実装側で排除されずに残る候補 ((iv) とは未分離)。** 実測は本体欠陥を hook の誤記録より選り分けていない。witness の形は既往の stock MOCC の G2 (T-1892・T-2774・T-2779) と同じで、既往の静的候補 (a) の順序 (validation が版と lock 状態を別の load で読む) は pin C の現物にも残る。**ただし根因は確定していない** | §4 |
| (iv) trace hook の記録誤り | **未検証。** 生の行の照合は trace の中の整合だけを言う。hook が実際に読んだ版を書いたかは trace からは分からない (既往の三分岐の「hook」と同じ未達) | §2・§4 |

要するに、**MOCC の stock 自体がこの cell (48 thread・1,000,000 record・rr95・zipf 0.9) で、性能構成の検査に同じ形の G2 で落ちる** (観測 3/109)。
6 件の G2 を起こすのに literal は必要でなかった。ただし候補での literal の寄与の有無や、率が stock と同等かは示していない (率の差が非有意なだけで、同等性の証明ではない)。
**論文への使い方は未決** (§6)。「正しさゲートが合成候補の誤りを捕まえた」例には使えない。

## 1. 問いと範囲

- 問い: t2849 read-heavy の literal 候補 6 slot の G2 を、(i) verifier の誤検出 / (ii) literal 差し込みの影響 / (iii) MOCC 本体の欠陥に切り分ける。
- 順序: 段 A (保全 trace の再検査、計算ノード 1 job) → 段 B (literal を差し込まない stock の追加走、既存 harness) → 段 B の anomaly の再検査。
- 範囲外: verifier・判定・受理集合の変更、gate・検査・台帳の追加、CCBench の改変、診断 patch、上流への送信 (D16・D2148 項 13)。

## 2. 段 A — 保全 trace の再検査 (候補 6 件)

計算ノード 1 job (`31813.nqsv`、Elapse 1,242 s)。probe が件ごとに次を行った。件ごとの全出力は job dir `recheck-output/` (各 23〜48 MB、sha256 は `recheck-output.sha256`)、要点は `verbatim/stageA-recheck-compact.json`・`verbatim/stageA-summary.md`。

1. **同定**: campaign の WAL で性能構成の non-serializable な `verify_done` の commit 数と、保全 inventory の `--expected-commits` が一致する反復を 1 つ採った (6 件とも一意)。
2. **展開と検算**: 48 file を展開し、inventory の sha256・bytes・行数と照合した (6 件とも一致)。
3. **verifier の再実行**: 保全時の verifier module の sha256 (inventory) と、実行した木の `orchestrator/verifier/*.py` は 6 件とも一致した (同じ版)。pin C の checkout に保全 patch を当てて `--ccbench-root` にし、保全時の argv の trace dir と ccbench root だけを置き換えて走らせた。6 件とも rc=1 (non-serializable) で、出力の witness (取引 2 つ・key・読んだ版・上書きした版) は digest と一致した。verify 1 回 116〜168 s。
4. **verifier を使わない照合**: 生の C/R/W/E 行だけを読み、次を確かめた。
   - 2 取引の frame が閉じていて、R/W の件数が宣言と一致し、W の版が C の commit 版と一致する。
   - 各辺 A→B について、A が読んだ版を書いた取引が trace に実在する。同じ key でその版の直後の版を書いたのは B である。同じ版の重複は無い。
   - 結果は 6 件とも 2 辺が成立し、frame の異常は 0。2 取引は常に別の thread で、lock 被覆違反などの X/I/P 行は 6 件とも 0 件だった。
   - **共有する前提:** C/R/W 行の意味と、版を (epoch, tid) の辞書順に並べることは verifier と同じである。独立なのは parser と判定の実装だけで、trace が実際の実行を正しく写していることは証明しない。
5. **patch の照合**: 6 件とも `patch_only_template_plus_literal = true`。hole 外の差は 0 行で、literal は 5・135・10・651・5・20。

| 件 | literal (µs) | 保全 dir | commits | 2 取引 (thread) | 辺 1: key 読み版 → 上書き版 (書き手) | 辺 2 |
|---|---:|---|---:|---|---|---|
| bo 初期点 | 5 | `__lxnjdt6` | 6,896,260 | T5765376 (42)・T5765402 (37) | key 2: (63,591) → (63,593) T5765402 | key 0: (63,590) → (63,592) T5765376 |
| bo 終点再計測 | 135 | `6xdft5np` | 6,981,597 | T5165685 (46)・T5165697 (44) | key 0: (56,757) → (56,760) | key 3: (56,756) → (56,759) |
| random 初期点 | 10 | `61cpczdc` | 6,831,437 | T6007074 (15)・T6007082 (22) | key 0: (66,3531) → (66,3538) | key 1: (66,3528) → (66,3535) |
| random 探索 | 651 | `zpjkgz3a` | 5,132,965 | T4826866 (22)・T4826870 (0) | key 0x61: (71,685) → (71,918) | key 0: (71,915) → (71,917) |
| sweep 初期点 | 5 | `yd20yjdp` | 6,950,679 | T4654192 (42)・T4654200 (27) | key 1: (50,4066) → (50,4071) | key 2: (50,4066) → (50,4070) |
| sweep 終点再計測 | 20 | `3ad6bb3s` | 6,953,353 | T9480 (38)・T9487 (20) | key 0: (1,325) → (1,329) | key 1: (1,324) → (1,328) |

## 3. 段 B — literal を差し込まない stock の追加走

- **設計 (段 4 裁定):** 着地済みの比較 harness の block 対照 (`p3_s4_loop_pegasus.sh` の harness mode、`IZANAGI_S4_T2849_MODE=block-controls`、`IZANAGI_S4_T2849_BLOCK_STOCK_SESSIONS=4`) を 4 job 同時に投入した (新規コード 0)。
  - 条件は t2849 と同じ cell・pin C `68106660…`・stock genome `mocc|BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1` (template 適用後も preprocess 後の source は原本と同一)。検査は同じ verifier、性能構成の直列検査。
  - cohort `t2868-mocc-stock-v1`、block 1〜4、submit 木は `339d7c188`。
  - 段 2 plan の `BACK_OFF=0` 案は既存 harness で指定できず leader の処理も変えるので削った。T-2779 runner の改造も不要と裁定した。
- **ユーザー確認:** 見積り (1 slot 800〜935 s、16 slot で 3.6〜4.2 node 時間) を示し、回答は「64 反復 (推奨)」(`verbatim/user-compute-confirmation.md`)。
  - 反復数の見積りの訂正: 1 slot は legacy 1 回 + 性能構成**最大 5 反復** (anomaly で打ち切り) で、「性能 4 反復」は親の誤読だった。実際の性能構成の反復は 74。費用は slot 単位の見積りのとおり。
- **結果:** 16 slot 中 3 slot が non-serializable。性能構成の反復では 74 中 3。

| block | slot | campaign | 判定 |
|---|---|---|---|
| 1 | 1〜4 | `8fbbe1d5`・**`b76a41da`**・`df70bfb6`・`79922deb` | certified・**G2**・certified・certified |
| 2 | 1〜4 | `070e66b3`・`37580c0d`・`dff8128b`・**`28361e07`** | certified ×3・**G2** |
| 3 | 1〜4 | `cda942b3`・`0720fbab`・`45916435`・`996a8735` | certified ×4 |
| 4 | 1〜4 | **`e82a4f9b`**・`5d4feb10`・`df2b3009`・`746f971e` | **G2**・certified ×3 |

- **stock の 3 件の再検査** (`32027.nqsv`、Elapse 1,100 s。段 A と同じ probe、候補 3 件の再実行を同梱。要点 `verbatim/stageB-recheck-compact.json`・`verbatim/stageB-recheck-summary.md`):
  - 3 件とも verifier は同じ版で rc=1、witness は digest と一致し、生の行で 2 辺が成立した。X/I/P は 0 件。
  - patch は template そのまま (hole 外の差 0)。
  - 候補 3 件の再実行は段 A と同じ結果になった。

| 件 | commits | 2 取引 (thread) | 辺 1 | 辺 2 |
|---|---:|---|---|---|
| block 1 slot 2 | 5,597,962 | T4741103 (37)・T4741112 (2) | key 8: (63,3028) → (63,3054) T4741112 | key 0: (63,3043) → (63,3053) T4741103 |
| block 2 slot 4 | 5,640,790 | T2031996 (1)・T2032003 (9) | key 3: (27,3116) → (27,3131) | key 0: (27,3127) → (27,3129) |
| block 4 slot 1 | 5,525,130 | T3517220 (31)・T3517226 (18) | key 5: (48,1155) → (48,1162) | key 0: (48,1158) → (48,1160) |

- **率の比較** (性能構成の反復単位、95% は Clopper–Pearson):

| 群 | G2 反復 / 反復 | 率 | 95% 区間 | trace 有効走の commit 数 |
|---|---|---:|---|---|
| 候補 (t2849、literal 3〜1000 µs の合算) | 6 / 119 | 5.0% | 1.9〜10.7% | 4.28M〜7.20M |
| stock (本 wave) | 3 / 74 | 4.1% | 0.8〜11.4% | 5.46M〜5.67M |
| stock (t2849、単価実測 1 + block 1 + 系列開始 5 slot) | 0 / 35 | — | — | 5.47M〜5.66M (単価実測を除く 30 反復) |
| stock 合計 | 3 / 109 | 2.8% | 0.6〜7.8% | — |

- 候補対 stock 合計の両側 Fisher は p = 0.50 で、率の差は検出されない。
  - stock の率を 3/109 とすると、t2849 の 0/35 は確率約 38% で起こる。t2849 で stock が 0 件だったのは、この率で説明できる。
  - 候補の率は値の違う候補の合算であり、「stock と同等」を示したものではない (非有意は同等性の証明ではない)。
- commit 数は曝露量の目安であり、性能主張に使わない (規律 1)。t2849 で anomaly が出た 651 µs の反復 (5.13M) は stock の域より低い。「高 throughput のときだけ出る」とは言えない。
- 計算: 段 B 4 job の Elapse 計 11,450 s (31863: 2,648・31864: 3,087・31865: 3,079・31866: 2,636)。段 A 1,242 s、再検査 1,100 s と合わせて **13,792 s = 3.83 node 時間**。

## 4. CCBench (MOCC) 側の所見の構造化 (`output/README.md` の形式)

- **発見:** pin C (`68106660…` = e9e477ca + X/P 計装、`cc/mocc/transaction.cc` の差は `#if TRACE` 内だけ) の MOCC の stock (`BACK_OFF=1`、適応 backoff、`KEY_SORT=0`、`TEMPERATURE_RESET_OPT=1`) が、性能構成の trace 検査で長さ 2・両辺 rw の G2 (write skew) を commit する。74 反復中 3 件。literal の固定 backoff の候補でも同じ形が 119 反復中 6 件。
- **再現条件:** 48 thread・1,000,000 record・rr95 (read 95%)・rmw 0・max_ope 10・zipf 0.9 (保全 inventory の `workload_flags`。比較 harness の read-heavy、pin C の較正 `calibration-7f00a49f493e1015.json` の動作点)・3 秒・trace-enabled build (TRACE=1、X/P 計装あり、T-1943 の witness なし)・GCC は harness の既定。性能構成の反復あたりの観測は stock 3/109 (2.8%、95% 区間 0.6〜7.8%)、候補 6/119 (5.0%)。
- **witness の共通形 (9 件):** 2 取引が互いの読んだ版を上書きして両方 commit する。commit 版は同 epoch で tid 差 1〜3 (9 件で 1 が 6 件・2 が 2 件・3 が 1 件)。関わる key は 0・1・2・3・5・8・0x61 (zipf の上位)。2 取引は常に別の thread。読んだ版を書いた取引はいずれも trace に実在する。
- **該当コード (pin C の行):** validation の read set 走査 `cc/mocc/transaction.cc` 1033〜1063 行。版の読み (1035〜1036) と比較 (1037〜1038) の後に、別の load で lock 状態を読む (1049、`ldAcqCounter() == W_LOCKED`)。writer 側の publish (tidword の atomic store) は 1259〜1260 行 (`#line 1195` 指令の下)、unlock は 1271 行 (`unlockCLL()`)。
- **仮説 (未確定):** T-2774 §3 の静的候補 (a) と同じ順序で両方が validation を通る可能性がある。すなわち、R が x の版を読む → W が x を publish して unlock する → R が x の lock 状態を読む、の順。既往では、診断 patch (validation の版再読 + cold 側 abort) で通常 5/120 が 0/120 に下がった ([T-2779]、2 変更を束ねた介入)。本 wave では診断 patch を走らせていない。**hook の記録誤り (iv) と区別できていない**ので、根因とは書かない。
- **CCBench 論文・既往との関係:** 既往の stock MOCC の G2 (T-1892 5/42、T-2774 7/120、T-2779 通常 5/120・BACK_OFF=1 2/120) は 10,000 record・rr50 の小さな cell だった。本件は比較 harness の read-heavy 動作点 (100 万 record・rr95) でも、stock が同じ形の G2 を出すことを示した新しい条件である。上流報告案 [T-2791] の送信前なら、この条件を追記する材料になる。
- **還元判断: ユーザー確認待ち。** 上流への報告・PR は人間の判断 (D16、D2148 項 13)。AI は構造化までとした。

## 5. t2849-mocc-conn §4 の記述への追記 (元の記述は変えない)

- §4 の「検査走行の abort 率」列 (19.70% など) は、digest の abort 統計の値で、legacy workload (4 thread・200 record・1 秒・rr50・rmw あり、保全 inventory の `workload_flags`) の検査走行のものだった。anomaly が出た性能構成の反復の abort 率は、bo 初期点で 6.8% (468,814 / 6,896,260)。
- 「stock slot 7 件は 0」は性能構成の反復では 0/35。1 slot は legacy 1 回 + 性能構成最大 5 反復で、anomaly の反復で打ち切る。digest の「rep 5」は legacy を 1 回目と数えた番号 (bo 初期点は性能構成の 4 反復目)。
- 本 wave の段 B で、同じ構成の stock が 74 反復中 3 件の G2 を出した。§3 の read-heavy の stock 比が分母に使う block 対照の stock も、同じ性質を持つ実装である。

## 6. 論文への使い方と残り (裁定の材料)

- **使えないこと:** 「正しさゲートが合成候補の誤りを捕まえた」例として 6 件を使うこと。literal なしの stock でも同じ形の G2 が出るので、6 件を合成が持ち込んだ誤りとは言えない。候補での literal の寄与の有無は決まっていない。
- **言えること (非 certifying、主張に使うかは未決):**
  - ゲートは候補と stock を同じ基準で検査し、同じ形の G2 を両方で検出した (候補 6/119、stock 3/109。率の差は検出されないが同等性も示していない)。
  - 1 slot の certified (性能構成 5 反復) は、この cell では安全の強い証拠にならない。
- **影響 (未決の事項):** MOCC の read-heavy では、比較の基準である stock 自体が性能構成の検査に落ちる反復がある (観測 本 wave 3/74 = 4.1%、t2849 を含め 3/109 = 2.8%、95% 区間 0.6〜7.8%。母率は精度よく決まっていない)。t2849 の read-heavy の stock 比・終点選択 (`_disqualified`)・certified な終点 (evolution 13 µs、llm 80 µs) は、いずれもこの性質を持つ実装の上で得られた。
- 扱いの択一 (起票して裁定を待つ):
  - (a) MOCC の read-heavy を比較から外す。
  - (b) 「基準プロトコル自体が非直列化可能な cell」として注記して残す。
  - (c) 反復を増やして率を推定したうえで扱いを決める。
- **未達 (本 wave で閉じない):**
  - (iii) と (iv) の分離。実行順序の直接観測か、観測者効果の小さい計器が要る (既往 T-2774 §7・T-2779 §3)。
  - 診断 patch の再走。
  - 上流報告案への追記。

## 7. 段の経過と所見

- 段 2 plan (read-only 1 本) → 段 3 相談 2 本 (A 正しさ境界・B 過剰と削除) → 段 4 で所見 12 件をすべて採用した。主な修正は次のとおり。
  - 段 B の対照を stock 適応に一本化し、BACK_OFF=0 と runner 改造を削った。
  - 親の検出力の計算の誤りを撤回した (既観測の 0/30 を未観測として「計 90 で 99%」と数えていた)。
  - 段 A の結論を「記録された trace の中の整合」に限定した。
- 段 5: Codex author 1 本が probe 1 file (465 行) を unit 木に書いた。親は内容を読んで監査し、selftest 6 項目 (正例: write skew の 2 辺成立・template + literal の合格。負例: 直列の辺不成立・書き手不明・transaction.cc の hunk の不合格・hole 外 1 行変更の不合格) を実走した。
- 変異 matrix: repo の実装面の差分が 0 なので免除 (DW-S04)。probe の機構は selftest の正例・負例で確かめた。
- 段 6: read-only レビュー 1 本 (事実の再抽出)。件数・witness・統計値・Elapse・該当コードの行 (1 件を除く) は一次資料と一致した。所見 5 件 (patch 照合からの「意味の変更」の排除が広すぎた、非有意な率比較から候補の原因を断定していた、publish の行番号、(iii) の判定語、率の書き方) をすべて real とし、本文を修正した。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が名指す branch `t2868-probe-author` (commit `d86ec8f48`、probe の repo 側の保存先) と unit 木、job dir の submit 木 `/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/trees/sb1`〜`sb4` は、2026-09-30 の掃除 wave で回収せずに撤去する。probe は branch 束 bundle `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/backup/branches.bundle` から復元でき、job dir の `probe/`・`recheck-output/` は撤去しない。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
