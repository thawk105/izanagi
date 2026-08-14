---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-backlog-triage
seq: 1
title: 次の一手 657 件を全件棚卸しし、陳腐化・低価値 312 件を落として高価値 58 件へ補記する (docs のみ、branch worktree-dev-wave-backlog-triage)
---

## 本文

- ユーザー依頼は「残存タスクを確認し、現状を確認し、陳腐化していれば削除、今やる価値が非常に小さくても
  削除、今でもやる価値が高そうなら補記」。docs のみの wave で実装面の差分はゼロ。
- **母集合の確定に carry 鎖の全解決が要った。** 棚卸し開始時点 (エントリ 552) の「次の一手」は
  657 件で、作業中の main 取り込みで 664 件になった。うち本文を持つのは一部で、残りは `- [T-NNN] (N)` の carry stub である。archive 全 22 万行を遡って
  実体本文を解決したところ **全件に実体が存在**した。うち **35 件は旧形式 stub
  `変わらず (前エントリ参照)` を鎖に含む** — この形式は `tools/spool_fold.py` の `carry_re` が
  認識しないため、当該 35 件では `base:` 照合の「他 wave が先に書き換えていたら止まる」保護が
  実質的に効いていない (F190 = [T-724] の実測を全件規模で追認した)。
- **判定基準は新設せず、既存のユーザー裁定を機械的に適用した。** (1) 2026-08-12 の
  「研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り」、(2) 同「論文主張に要るのは粗い
  provenance のみ」、(3) 絶対規律 2 / 3 に効く項は価値小に分類しない、(4) 8c 無人ループと床値は
  最優先、(5) 受入・land を実際に止めている項は throughput 上の最優先。
  **AI の好みで新しい優先度を作らないことを不変条件に置いた。**
- **裁定待ち・裁定済み実装可の項は、価値判断だけを理由に落としていない。** ユーザーが
  「実装可 / 起票可」と裁定した項を AI が見送りへ移すのは裁定の反転にあたるため、落としたのは
  (a) 裁定文自体が終端 (現状維持 / 見送り / 据置 / 終端)、(b) 実測で解消、(c) 所有が別 ID へ移った、
  (d) docs 予算という機械的制約で発火しない、のいずれかが成立する項に限った。
- **実測で現状を確認した 8 点。** (i) `tools/ruleops.py inventory --repo .` は **rc=0** で、
  受入全走を止めていると主張していた [T-423] / [T-430] の赤は存在しない。
  (ii) `test_s8c_preregistration_invariant.py` + `test_t793_report.py` は **17 passed** で、
  「main が現在この 1 件で赤」と主張していた [T-1003] / [T-888] も解消済み。
  (iii) `docs/handoff/` は README のみで [T-1039] / [T-1037] / [T-234] の実体は消えている。
  (iv) `tools/dev_wave_land.py` は `--acceptance-receipt` を `required=True` で要求しており
  [T-393] は実装済み。(v) bounded local の出力が「回収不能量 = 判定占有量」を示し [T-985] (D354) は
  実装済み。(vi) 見送り台帳の item 先頭 ID 188 件と active 657 件の突き合わせで
  **二重在籍は 8 件** ([T-896] が未測定としていた数値を確定)。(vii) `output/insights` は 292 subdirectory に
  対し直近の平置き新規 1 件のみで [T-258] は運用として確立済み。(viii) 参照先として名指しされていた
  16 ID (T-276 / T-277 / T-481 / T-487 / T-454 / T-564 / T-674 / T-664 / T-207 / T-812 / T-287 /
  T-313 / T-908 / T-595 / T-472 / T-474) は**すべて既に非 active** で、「◯◯ が閉じるまで着手しない」
  型の依存が事実上解けていた。
- **結果: 664 → 352 (完了 6 / 見送り 306 / 補記して継続 58 / 無変更で継続 294)。**
  見送り 306 件の内訳は裁定終端 55・診断のみ 46・防御的堅牢化 45・docs 予算 38・
  粗い provenance 33・所有移管 27・実測で解消 21・発火条件不成立 19・ノード間分散 protocol
  (unratified) 8・二重在籍 7・単発フレーク 5・LLM routing 実験 2。
- **作業中に main が 2 度進み、判定対象がずれた。** 取り込み後に base digest を全件再計算したところ、
  最優先と補記していた [T-1092] (受入が緑でも receipt が出ない) は別 wave が既に閉じており、
  新規 8 件 ([T-1106]〜[T-1113]) が増えていた。前者は補記対象から外し、後者は同じ基準で判定に加えた
  (見送り 2 / 補記 3 / 無変更 3)。**並行 wave が多い環境では、この再計算を land 直前にもう一度行う。**
- **見送りは削除ではない。** ID 保存則 (D70) の sink である `docs/phase3.md` 見送り台帳へ、
  1 件ずつ理由と**再訪条件**を付けて移した。拾い直す判断はいつでもできる。
- **補記した 52 件の骨格。** 床値クラスタ ([T-1094] が閂、[T-971] / [T-748] / [T-1096] / [T-419] /
  [T-583] / [T-688])、8c 無人ループ ([T-324] / [T-527] / [T-238])、絶対規律 2 / 3
  ([T-396] の reward hack 経路が最優先、[T-441] / [T-493] / [T-1068] / [T-523] / [T-524] / [T-525] /
  [T-822] / [T-817] / [T-848] / [T-1025] / [T-397])、受入と land の律速
  ([T-1087] が最優先、[T-1058] / [T-1005] / [T-1059] / [T-1056] / [T-981] / [T-1105] /
  [T-1097] / [T-1101] / [T-989] / [T-932] / [T-650] / [T-826] / [T-754] / [T-1038] / [T-1090] /
  [T-894] / [T-1009])、台帳と裁定の健全性 ([T-959] / [T-724] / [T-711] / [T-351] / [T-895] /
  [T-896] / [T-612] / [T-758])、および main 取り込みで増えた 8c live pilot の閂
  ([T-1112] / [T-1109] / [T-1111]) と受入フレーク ([T-1107])。
- **[T-1009] と [T-613] が両立しないことを棚卸しで発見した。** 前者は「`--force-dispatch` 経由だと
  変異の失敗 node 抽出が壊れる」、後者は「変異 runner には `--force-dispatch` を必ず渡す」である。
  どちらを正とするかは未裁定なので、両項を残したうえで [T-1009] へその旨を補記した。
- **[T-657] が 2 つの異なる意味で参照されている。** 本項の最新本文は dev-wave docs 予算の stage0 残余だが、
  [T-805] と [T-1103] は同 ID を「権威束設計 (承認 record・失効・発効窓)」として参照している。
  同一 ID に別主題が付いている疑いがあるため、本 wave では [T-657] を docs 予算側として見送りへ移し、
  権威束設計を指す参照は [T-805] / [T-1103] 側に残した。**どちらが正本かはユーザー裁定が要る。**
- **敵対レビュー 2 本 (read-only codex、レンズ A = 落としすぎ / レンズ B = 陳腐化根拠の事実確認) を掛け、
  合計 21 件の判定を覆した。両レンズとも file:line 付きで、親の根拠より強い証拠を出した。**
- **レンズ A は「粗い provenance だから見送り」という親の分類を 6 件で覆した** —
  [T-733] (source closure に verifier / calibrator / buildcache が無く、**verifier だけを弱めても
  lock 照合を通り誤 variant が certified になる**)、[T-580] (validator identity が委譲先 reader を
  閉じず receipt 不変のまま受理集合が変わる)、[T-570] (作図系が admission を経由せず
  **topology 違反 WAL から論文図が出る**)、[T-334] (依存 bytes 非束縛で **trace build と perf build が
  別物になりうる** = 規律 1)、[T-446] (mimalloc の可動 tag と SHA pin を照合する gate が無く
  allocator 入替えが gate を通る)、[T-1095] (oracle の `config.h` を記録するだけで照合しない F46 型)。
  **親の分類基準「bytes 級 provenance の新設は見送り」は、読み手への証明と、防壁自身が束縛されて
  いない穴とを取り違えていた。** 6 件とも見送りから戻して補記した。
- **レンズ A はさらに [T-190] と [T-270] を「受入・land の現役阻害要因」として救った。**
  [T-190] は親が「エントリ 548 の production 修正で解消」としたが、548 自身が本項を持ち越し、
  F57 も「原因確定ではない」と明記していた (レンズ B も独立に同じ反証を出した)。
- **レンズ A の指摘で高価値枠から外したものもある** — [T-748] は実作業が [T-971] / [T-1094] へ
  移っており歴史的証拠への参照にすぎない、[T-895] / [T-896] は本 wave で目的を達しており
  研究・受入・land のいずれの閂でもない。
- **レンズ B は「陳腐化」の事実主張を 9 件反証した。** 内訳は「裁定は終端」と書いたが裁定文に続きの実装義務が明記されていた
  5 件 ([T-184] resource / retry、[T-520] bounded surface 比較、[T-530] 残余 package、
  [T-550] probe 規模の族制度化、[T-231] tmpfs 実消費の先行測定)、
  「所有が別 ID へ移った」と書いたが移管先がその残余を含まない 2 件
  ([T-467] merge trailer 規約は [T-938] に無い、[T-637] parser の黙殺は [T-391] に無い)、
  および [T-1055] / [T-190]。**親はすべて受け入れて見送りから外した。**
- **最も重い反証は [T-1055] である。** 親は「非帰属受理 → receipt → land の end-to-end が
  2026-08-13 12:14 JST に緑」を根拠に終端としたが、レンズ B が
  `docs/archive/worklog-phase3-0814-547.md:39-48` を示し、**再訪条件の実受入赤は既に発火しており、
  4 走中 3 走が赤・唯一の緑も rc=70 で receipt なし・land 未達**であることを突き止めた。
  親の根拠は「試験が緑」であって「実運用で成立」ではなかった。
- **「根拠が弱い」と指摘された 1 件は推論を捨てて測り直した。** [T-299] について親は
  「以後 440 を超えるエントリが緑で land した」という構造的推論を使っていたが、レンズ B が
  「当該 40 nodeid の消失を示さない」と正しく指摘した。当該 file を単独実走し
  **82 passed / 14 skipped / 赤 0** を得て、実測に置き換えた。
- **段 8 自己改善: 新しい失敗型を 1 件記録した。** `更新` は item を置換する操作なのに、
  生成器が本文の取得元を「末尾エントリの描画行」に取っていたため、main 取り込み後に
  carry stub がそのまま `更新` の本文になり、52 件の実体本文を失いかけた。
  **`base:` 照合は carry 解決後の digest で行うため通り、`check_docs` も `spool_fold --dry-run` も
  緑のままだった。** 機械化を新規 T として起票し、当面は memory で担う。
- 実装面の差分がゼロのため変異 matrix は免除 (`DW-S04`)。受入全走は免除せず実施した。

## 次の一手差分

### 完了

- [T-917] 凍結チェーン検証の保留執行は t816-step4-impl wave が実施済みと着手前実測で確定し、重複実装もしていない。
  remaining: none
  base: c6387dac574cff9b22e02b10fd162c2a36c6f2bcaa485b1c08599e6a836444df

- [T-393] 検証 receipt の LandRequest への束縛は実装済み。2026-08-15 の実測で tools/dev_wave_land.py が --acceptance-receipt を required=True で要求しており、検査を省いた tip の land は機械拒否される。
  remaining: none
  base: 915b590912fd55772108f06006063fc0659fc3a6a3a96b0c02d3980dacb37e09

- [T-798] fold transaction の phase 化・state 削除の postcondition 後移動・finalize の land 専用化を 2026-08-11 の実装 wave が実装済み。残る相は [T-889] / [T-800] / [T-801] へ切り出し済み。
  remaining: none
  base: 98639478e550e541fac726052192a45fcde249fb105e824f5f270c8010fdd44a

- [T-799] transaction state への trusted cutoff・audited digest・plan 入力 closure の束縛を 2026-08-11 の実装 wave が実装済み。
  remaining: none
  base: d939429b32b96d0f5bcdf941602d0f482a33ec9b2a46d21f4b741b65b4d8bcb5

- [T-820] _load_rotate_limit の例外囲いを BaseException へ広げる実装を 2026-08-11 の実装 wave が完了済み。
  remaining: none
  base: 8fb8c4b0cf9cd2395e654a3a4ea39e89274bd091677494fe6dd0ba29f99d1155

- [T-821] FOLDED receipt への base / tested tip / wave ref の追加を 2026-08-11 の実装 wave が完了済み。既知限界は本文に記録済み。
  remaining: none
  base: 7e41897de73ec3c98c53e5b23258115c3fb5ea7dca7585e3f7f63049c1893320

### 更新

- [T-1094] **P1・新規 (B 系)**:
  床値 build 経路に FetchContent の source 差し替えを通す。`buildcache.py` には
  `FETCHCONTENT_SOURCE_DIR_*` の配線が 0 件で、計算ノードは直結 network 不可
  (`docs/pegasus-runbook.md:744-756`)。`silo_ladder_rung1.py:1046` に先例がある。
  **これが解けない限り、oracle を直しても床値は 0 件のままである。**
  shared build path のため全 campaign へ波及する点に注意。
  **(2026-08-15 棚卸し) 今も最優先**: 床値が 1 件も取れていない直接の閂であり、oracle 側を直しても本項が解けない限り結果は 0 件のままである ([T-971] / [T-748] が実測で確認済み)。shared build path のため全 campaign へ波及する。
  base: 8cae1a758c85f7bcd7a927418503ef321c54c05d6a5333d142ca34cdef8ac5a3

- [T-971] **P1・部分完了**: 床値 sort_best の SWO oracle 不可用の原因を実測で確定し、
  診断・resolver・依存束縛・compiler 明示注入を実装した。**ただし床値は 1 件も取れていない** —
  FetchContent staging が別 blocker として残り、計算ノードでの end-to-end 確認も未実施。
  残件は (a) 計算ノードでの実測 (resolver 解決と CMake configure の可否を同時に測る短い PBS probe)、
  (b) [T-1094] の解決。
  **(2026-08-15 棚卸し) 今も高価値**: 床値クラスタの本体。残件 (a) 計算ノードでの end-to-end 実測と (b) [T-1094] のうち、(b) が閂である。
  base: 67cb7df0ebc9bb32bec1257324c0303accc3de8b69aef9fc24d31f11b060007d

- [T-1096] **P2・新規 (B 系)**:
  `p3_s4_loop_sort.py` の oracle 依存解決も使い捨て checkout 上で失敗する。
  floor 限定の解決では直らず、S5 の sort_best gate・WAL・campaign report は
  `infrastructure-unavailable` に汚染されたまま。全 consumer へ trusted dependency root と
  compiler を明示注入する共通 seam を作るか、S5 を明示的に別扱いにするかの裁定が要る。
  **(2026-08-15 棚卸し) 今も高価値**: sort 側 oracle が解けないままだと S5 の sort_best gate・WAL・campaign report が infrastructure-unavailable に汚染され続ける。床値クラスタと同じ seam の裁定を要する。
  base: eb076f79cb066295b1c00971c58359bd208b2bfd083aa68162ebb5d991305140

- [T-419] **P1・裁定済み (2026-08-12 /rulings、(b)) → 世代列照合へ**: 凍結 protocol の contract hash
  pin は世代列への照合 ([T-478] A′ 機構と同型) へ変える。実装は世代交代を実際に行う wave へ同梱
  (優先度下げ)。残る blocker (iv) 例外集合の空化の依存関係は不変。
  **(2026-08-15 棚卸し) 今も高価値**: 較正チェーンの起点であり、[T-420] / [T-443] / [T-475] / [T-506] / [T-507] / [T-531] ほか多数が本項の U-2 に従属している。本項が動かない限り certified campaign を開けない。
  base: 8583fed606dba54ccbbbaecee0b36d2d3a35fd37b12662872c389ec771897254

- [T-583] **P2・新規**: `submit_certify.sh` が `qsub` へ
  repo 外の `-o` / `-e` を渡さないため、job のたびに `.o<ID>` / `.e<ID>` が repo 直下へ返り、
  次の submit を dirty gate が、land を clean 要求が塞ぐ。repo を submit directory にする job は
  `-o` / `-e` をファイル path で渡す規範が runbook にあるのに従っていない。
  現状は毎回手で job-staging へ移して凌いでいる。
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 較正 certify を回すたびに repo 直下へ .o/.e が返り、次の submit を dirty gate が、land を clean 要求が塞ぐ。毎回手作業で凌いでいるのに、直すのは qsub へ渡す -o / -e の 1 箇所である。
  base: 1280d05c0658bf690b757bc748114b6912e010d156f204de88f227e70a8f767a

- [T-688] **P2・裁定済み (2026-08-12 /rulings) → 採用**: job wrapper 側に durable checkpoint /
  partial-log path を作り、SIGKILL・OOM・walltime 打ち切り・起動前 rc=16 の診断ゼロを塞ぐ。
  **(2026-08-15 棚卸し) 今も高価値**: 床値 job が SIGKILL・OOM・walltime で落ちたときに診断がゼロになる。[T-748] / [T-971] の実測が job artifact の手作業復元に頼っている現状の原因でもある。
  base: 70b3ee69b2757a8b20c904a900ba2ad40ed671a5cf2d7cdc8b79f5c505d25e0d

- [T-324] **P1・裁定済み → 待ち解除**: [T-244] の裁定が完了したため第 1 段が済んだ。
  順序は変わらず「複数世代・還流・標本設計の事前登録 → 実走」。budget=1 の結果を
  workload 特化合成の証拠に数えない点も従前どおり
  **(2026-08-15 棚卸し) 今も高価値**: 8c 本走 (複数世代・還流・標本設計の事前登録 → 実走) の入口であり、ユーザーが目標の柱と位置づける無人ループの本体にあたる。
  base: 7fad551afeb0869e7c1b330497724a40db9688f21e47b13ab8b0da147e12f79c

- [T-527] **P3・新規 (段 6 レンズ B-3 後半)**:
  `rr80` / `rr20` の実 projection が `WORKLOADS` に無く、正式 holdout 起動は現状 production に
  到達しない。U-4 は「拒否」側の到達性を確保済みだが、正式 H1/H2 を走らせるには projection と
  campaign / completeness consumer の追加が要る。これは配線でなく測定能力の追加であり、
  [T-295] の発効と歩調を合わせる。
  **(2026-08-15 棚卸し) 今も高価値**: 正式 H1/H2 の projection が production に存在しないため、8c 正式実験は現状「起動できない」。配線ではなく測定能力の追加であり、本走の前提になる。
  base: bd2e09d8c7c79d5b2f17060696249fb2c95fa6e4a3e5bf2e62afb8fd8e970ebd

- [T-238] **P3・新規 (本エントリ)**: driver 族 (`p3_s4_loop.py` / `p3_s4_loop_trigger_gating.py` /
  同 sort・trigger 版) の `ENV_TAG`/`CLK`/`NUMA` ハードコードを `env_contract` registry 由来へ寄せる。
  Pegasus entry は `numactl=()` / `clocks_per_us=2100` なので、現状この族は Pegasus を選べない
  **(2026-08-15 棚卸し) 今も高価値**: driver 族が ENV_TAG / CLK / NUMA をハードコードしているため、合成ループの本体である p3_s4_loop 族が主戦場の Pegasus を選べない。
  base: 7838527558a1692a2c84ff7131042542c5de95460bea1d3cac122bc3336c0ccf

- [T-396] **P1・新規**: trigger-gating の受理集合に reward hack 経路が
  ある。EVOLVE-BLOCK の hole は `TxExecutor::abort()` 内の任意 1 行で、機械 gate は識別子 5 個の
  blacklist だけである。`pro_set_` (`cc/silo/include/transaction.hh` の `std::vector<Procedure>`) は
  blacklist に無く、`makeProcedure` は `RETRY:` の前で 1 回しか呼ばれないため、`abort()` で
  `pro_set_.pop_back()` するとトランザクションが retry ごとに縮み、**serializable のまま
  throughput だけ上がる**。`mrctid_` 経由の別経路も指摘された。auditor (LLM) だけが関所である。
  AST allowlist 化を検討する。受理集合の縮小なので D96 手続が要る (規律 2 に直接効く)
  **(2026-08-15 棚卸し) 今も最優先 (規律 2 の直撃)**: EVOLVE-BLOCK の hole から pro_set_.pop_back() で「serializable のまま throughput だけ上がる」reward hack が到達可能であり、関所は LLM auditor だけである。合成の受理集合そのものの穴なので、堅牢化一般とは別格に扱う。
  base: 12197a7f708f6662456e0d0f3c8cadfd7d8235ac478dd9396de1c26c937f7d3a

- [T-441] **P2・新規**: backoff 軸の EVOLVE-BLOCK hole 受理文法を設計・実装する。
  [T-409] 択一 4 の裁定 (scope = trigger のみで閉じる) による分離。trigger 側の文法 v1
  (`output/insights/2026-08-04_t409-evolve-hole-allowlist/`) を出発点にする
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: backoff 軸の hole 受理文法は合成の受理集合そのもの。trigger 軸だけが 32 正準の閉集合を持ち、backoff 軸は無防備なまま残っている。
  base: 5ba1fe56df11b842285ffd425a3d2bf98d69ca31130ab565de778cf8d96925fa

- [T-493] **P3・新規 (T-490 U-4 の裁定で分離)**: `sort_best.comparator` に
  trigger 軸の 32 閉集合に相当する閉じた権威集合を設計する。[T-410] の witness 設計 (D146) と
  同じ面であり、合流させてよい
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: sort 軸も [T-441] と同じく閉じた権威集合を持たない。trigger 軸との非対称が受理集合の穴になる。
  base: 8bbe3b924d0206bc5a513d3e92225621a8e76c4b283a078af44aeadb9d47363b

- [T-1068] **P2・新規**: trigger 骨格の宣言側と呼出依存を凍結するか。
  R4 (prologue での `izanagi_gate_pass` 再宣言による代入・真理値の無効化)、R5 (宣言と BEGIN の間の
  制御流変更による非到達化)、R7 (`Backoff` / `FLAGS_clocks_per_us` の local shadowing) は、
  いずれも block と epilogue を逐語一致させたまま gate を無効化できる。実証差分は
  `output/insights/2026-08-13_t1048-trigger-freeze-epilogue/verbatim/consult-b.md` 所見 1、
  同 `consult-a2.md` 所見 2、同 `review-b.md` 所見 2。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: block と epilogue を逐語一致させたまま gate を無効化できる 3 経路 (R4 / R5 / R7) が実証差分つきで残っている。凍結領域の意味が破れる。
  base: 0d8f14372cc7c718254d05d62c114708bd38f360d236674ece2f469eeae97e84

- [T-523] **P1・新規 (配線 wave 段 3 レンズ A-3、親が現物で裏取り)**:
  `s8b_floor_campaign --mode pilot` は trial registry も lifecycle 台帳も通さずに
  freeze 由来の holdout セルを実測できる。U-4 が閉じたのは 8c launcher の経路だけであり、
  H1/H2 の事前観測路はこちらに残る。**同型の欠陥が独立 2 producer で再現した**ので
  (8c launcher と 8b floor campaign)、族一般化として「freeze 由来 holdout を実測へ渡す
  共通下位境界に admission と一回性台帳を置く」設計を起票する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: freeze 由来 holdout を admission も一回性台帳も通さずに実測できる経路が独立 2 producer で再現しており、holdout 漏洩の直接経路になる。
  base: ecd0fd43e4ab808c38f6c422a9eac9d00f357dbc6a175b91e33a2fe60b6acb0c

- [T-524] **P2・新規 (同レンズ A-4)**:
  trial_id ごとの一回性と manifest hash ごとの receipt では、**別々の manifest を N 個登録して
  良い receipt だけを下流に渡す** best-of-N を閉じられない。実験単位を
  `(prereg_generation, holdout, arm, replicate_slot)` にし、承認 artifact が全 slot と個数を
  固定する設計へ改める。下流は predeclared receipt の全列挙と消費を検査する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: 別々の manifest を N 個登録して良い receipt だけを下流へ渡す best-of-N を閉じられない。実験計画に対する reward hacking にあたる。
  base: f493aeb0c9d3453ea07c35cdbd0f5636d9a9945f9b914905d1813aedf1995159

- [T-525] **P2・新規 (同レンズ A-2)**:
  holdout 束縛が workload 名と `ycsb_rratio` だけで、freeze が持つ skew / rmw / records / threads を
  含まない。名前と rratio の一致だけで別条件の測定が H1 として receipt 化されうる。
  ratified freeze の完全な `HoldoutSpec` と SHA を sealed binding にし、campaign identity・
  実行引数・run-start・terminal report・受入で全 field を再照合する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: holdout 束縛が workload 名と rratio だけなので、skew / rmw / records / threads が違う測定が H1 として receipt 化されうる。
  base: a6da431c3db7209407f97d2c29701ac1e71f53b646b4cce6ae3e88e36b332dff

- [T-822] **P2・裁定済み (2026-08-11 /rulings、閉じる) → 8c 正式系列の着手前に実装 wave 起票可**:
  8c 正式受入の恒真保証 3 件 ((i) Layer-3 chain を必須経路で呼ぶ / (ii) 宣言 arm の実走認証 /
  (iii) 6 report 間の `measurement_head` 一致検査) を実装で閉じる。「意図的な限界として明文化」は
  正しさゲートの格下げのため不採用。実装順・段階分けは wave の設計に委ねる。実装面のため
  Codex author 必須
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: 8c 正式受入の恒真保証 3 件。「意図的な限界として明文化する」案は正しさゲートの格下げにあたるため不採用と既に裁定されており、実装で閉じるしかない。
  base: 10752a972b700703f6648b5c254f0e3c808b5007107a29e21b1090b5ba243f5d

- [T-817] **P1・再裁定済み (2026-08-12 /rulings、Q1 (a) 限定形・Q2 (a)・Q3 (a)・Q4 分配) →
  verifier epoch 実装 wave 起票可**: Q1 = epoch を導入し「certified を名乗る受理集合」から
  E0 (現行 policy 未検証) 記録を除外、歴史解析の生値は epoch 表示付きで残す。Q2 = 残存ログ
  突き合わせ機構は作らない (0/459 で条件節が空集合、same-run 束縛値が無く作れば規律 2 違反 +
  恒真 gate)。将来の run の再発防止は [T-859] として起票。
  Q3 = `campaign_verifier_epoch` を v2 lock の既存 authority へ束縛 (実 enforcement bytes への
  束縛)。Q4 = S8b 独立 identity 層は Q1 の専用 wave に含める、guided WAL の位置づけは
  [T-860]、歴史 campaign の admission は [T-861] として
  起票。正本 = `output/insights/2026-08-11_t817-verifier-epoch/verbatim/ruling-package.md`
  **(2026-08-15 棚卸し) 今も高価値**: 「certified を名乗る受理集合」から未検証 epoch の記録を除外する作業であり、対外主張の射程を正直に保つために要る。
  base: fbb1b24056353b0bec9f940ff28db788e8f49cb0c1e698651e776466a4e96650

- [T-848] **P1・新規**: 変異 `TIMEOUT` の意味を
  「RUN 開始を receipt で確認した後の計算ノード実行 timeout」に限定し、queue timeout を
  別 status にする。現行は dispatch subprocess 全体に timeout が掛かるため、**一度も走っていない
  変異が terminal として `registered == recorded` を満たす。**逐次経路にも存在する既存欠陥で、
  D130 決定 (3) 条件 4 の `total_deadline` と同族。既存台帳の再解釈が要る。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 一度も走っていない変異が terminal として registered == recorded を満たすため、変異台帳が偽の緑を出す。検出力の主張そのものが汚染される。
  base: 68c5f02e78de3648b6ba14823aa8943f5464e644fc23871757bd93e94c13859d

- [T-1025] **P1・新規**: `hooks/guard_bash.py` の `_is_read_only`
  allowlist に残る実 writer を閉じる。`awk 'BEGIN {print > "…"}'`・`sed -n 'w …'`・
  `git diff --output=…`・`sort -T …`・`find -fls …`・`xxd -r … …` の 6 形が、
  **現行実装で WAL 等の既存保護対象を書ける**ことを実測済み (2026-08-13、
  `probe_allowlist.py`、対照の `echo >>`・`rm` は拒否)。[T-956] land 後は同じ 6 形を
  `hooks/guard_write.py` へ向ければ guard source の上書きにも到達する。scope は hooks 特例では
  なく**全既存保護対象**に対する reader mode の実 writer 判別。受入条件 = 6 形を hooks と
  WAL の双方で拒否し、対応する純読み形 (`awk '{print}' file`・`sed -n p`・`git diff -- path`・
  `sort file`・`find -print`・`xxd file`) は維持。flag/env の逃がし道を置かない。
  **(2026-08-15 棚卸し) 今も高価値**: read-only allowlist に残る 6 形が WAL 等の既存保護対象を実際に書けることを実測済みであり、防御的堅牢化一般ではなく実測付きの防壁破りである。
  base: 479223e05516c170bd8e7ea5f392e446ba5acc14620797a30a197025ef04623e

- [T-397] **P2・新規**: sort 軸の構造化 integrity witness を新設する。
  現行の `permutation_violations` は整数 counter と自然文 notes だけで `verdict=indeterminate` /
  `anomalies=[]` になるため、「同じ理由」の同値関係を書けない。
  D138 を sort 軸へ適用する前提条件
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 現行の permutation_violations は整数 counter と自然文だけで verdict=indeterminate に落ちるため、「なぜ壊れたか」を次の一手へ渡せない。sort 軸へ D138 を適用する前提でもある。
  base: 75d2e6241c4b26fffea59f2dccaa2be59a96adc2b8c0bcc368bc6cfb013e4f11

- [T-733] **P2・新規**: source closure を**推移閉包**へ広げるか。
  現在の 8 path は閉包ではなく、`pipeline.py` が verifier / calibrator / buildcache /
  build_admission / source_digest へ、`execution_guard.py` が env_attestation / site_policy へ
  判定を委譲している。qualification 側の 37 path 集合が規模の目安。
  成果物影響 = これがない限り「certified 経路が source-bound」とは永久に名乗れず、
  委譲先の差し替えは成果物のどの値からも検出できない。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2。親の分類を敵対レビューが覆した)**: 8 path の source closure に verifier / calibrator / buildcache が入っていないため、**verifier だけを弱めても既存 lock の照合を通り、誤った variant が certified になりうる**。親は当初これを粗い provenance 基準の見送り側へ分類したが、これは「読み手への証明」ではなく正しさ防壁自身が束縛されていない穴である。
  base: 9b7a5adfaac6b3e0fa63d614546ec6360ddaf828186f45083d5af14be5926905

- [T-580] **P2・新規**: admission receipt の `validator.sha256` と
  oracle の `generator_versions` は leaf source の hash だけを記録し、判定に使う被 import module の
  意味論を閉じていない。`artifact_admission` は自分自身を hash しながら WAL の
  strict reader へ判定を委ねており、reader 側が変わっても receipt は不変のまま受理集合が変わりうる。
  T-503 とは独立に成立する穴で、versioned transitive source closure を新設するか、
  盲点を明示的な限界として記録するかの択一を含む。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2。親の分類を敵対レビューが覆した)**: admission receipt は自分自身の hash しか validator identity にせず、判定を live の WAL reader へ委譲する。reader の意味が変われば **receipt 不変のまま受理集合が変わる**。同上の理由で見送りから戻した。
  base: 95f16806f0c1716c7b12ee7151cee6ffba3fb87c69f0795e21d86587cf178e5c

- [T-570] **P3・新規**: 作図系が admission を経由せず WAL を直接読むため、
  topology 違反の WAL からも図と provenance が出る
  **(2026-08-15 棚卸し) 今も高価値 (親の分類を敵対レビューが覆した)**: 作図系は admission を経由せず WAL の bench_done / commit だけで certified 値として作図する。**偽または topology 違反の WAL が論文図へ入る経路**であり、provenance の粒度の問題ではなく図の値が誤る問題である。
  base: 70481a81dc12c5a67a3bb1e7e0ae2325d1fbb7082028c11febec78eb82f30076

- [T-334] **P3・新規 (本エントリ)**: 依存 bytes の content hash 束縛。D125 決定 (3) は dependency prefix を path 要素の配列として identity に束縛するが、**依存ライブラリの bytes 自体は hash していない**。trace/perf build の間に prefix 内容が差し替わると「trace だけが差分」と記録される
  **(2026-08-15 棚卸し) 今も高価値 (規律 1。親の分類を敵対レビューが覆した)**: build identity が dependency prefix の path だけを束縛し内容を束縛しないため、trace build と perf build の間で依存物が入れ替わると**正しさを検証したプログラムと性能を測ったプログラムが別物になる**。観測者効果の分離 (規律 1) が成立しなくなる。
  base: 97e36ad7e80e0d2b7693d632d8b29ea429ebb555e733197bdec3376a3c322164

- [T-446] **P3・新規**:
  **mimalloc の `fetchcontent_ref` は annotated tag `v2.3.2`、`pin` は commit SHA で、
  両者を照合する gate が無い** (`third_party_policy` は ref が 40-hex のときしか照合しない)。
  tag が動いても現行検査は通る。凍結 driver の変更が要る
  **(2026-08-15 棚卸し) 今も高価値 (親の分類を敵対レビューが覆した)**: mimalloc の FetchContent は可動 tag を使う一方 SHA pin との照合 gate が無い。**allocator が入れ替わると測定値が変わるのに gate は通る**。現在たまたま正しい HEAD である事実は将来の穴を閉じない。
  base: 1fd23c1a5304c0c3af7585dc4cda8c1ac418c1ac890213846c745ea908f8369f

- [T-1095] **P2・新規 (B 系)**:
  oracle の compile closure を byte で封印し、oracle receipt を floor proof chain へ耐久化する。
  現状は env が transport 兼 authority になりうる。`config.h` は Git 非管理なので
  HEAD pin だけでは閉じない。`expected config.h hash` の置き場所は D115 (identity 非束縛の
  key だけ floor policy へ) と D152 (cache root は policy から導出しない) の双方に
  抵触しうる**未解決の設計択一**であり、裁定が要る。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3。親の分類を敵対レビューが覆した)**: oracle の `config.h` は観測 hash を記録するだけで期待値と照合しない (F46 型 = 記録するだけで発火しない値)。Git HEAD が正しくても **oracle のコンパイル意味を変えられ、誤った oracle 判定が floor chain へ入る**。
  base: 6965708ee173341dd6b01857921c351eb4765578d3bb02e1365114bca661cc1c

- [T-190] **P2・新規 ((70)、F57)**: launcher normal fakeの32-worker負荷フレークを
  失敗artifact保存つきで原因分離し、production gateを緩めずfixtureをhardenする
  **(2026-08-15 棚卸し) 今も高価値 (親の判定を敵対レビュー 2 本が独立に覆した)**: 親は「エントリ 548 の production 修正で解消」と判定したが、**548 自身が本項を持ち越しており、F57 も「原因確定ではない・原因分離 task は閉じない」と明記**している。548 が直したのは終了観測と signal mask の別欠陥である。受入全走と land を現に阻害する要因として残す。**見送り台帳にも同名項があるため、正本の一本化は [T-896] で扱う。**
  base: 51676c5a3e9b750878a631d8718f5a817ccc6523e7e2dcece0b68ae83065d5d1

- [T-1087] **P1・新規**: `tools/check_acceptance_reds.py` が
  自分の dispatch 受領証で自分の清浄性検査を落とし、rc=2 (判定不能) から復帰できない。
  再走・collection が probe worktree を cwd にして `run_tests.py --force-dispatch` を呼ぶため、
  `.gitignore` 記載の `output/pegasus-dispatch/` に受領証が書かれ、直後の
  `--ignored=matching` 検査が非空になる。判定器が使えないと、受入が rc=1 の wave は
  非帰属を機械的に立証できず land できない。清浄性検査から dispatch 受領証 path を
  除外するか、受領証を probe worktree の外へ出す設計が要る。
  **(2026-08-15 棚卸し) 今も高価値**: 非帰属 checker が自分の dispatch 受領証で自分の清浄性検査を落とし rc=2 から復帰できない。判定器が使えないと、受入が rc=1 の wave は非帰属を立証できず land できない。
  base: fd82c7856d3dcdcbf33e34b0add1645202c0512d8f3b5696f62bd58a68d00ec4

- [T-1058] **P2・新規 (2026-08-13 実測 2 例)**:
  `test_dev_wave_wait.py` の signal handler 復元テストが変異 harness の走行間で揺れる。
  2 巡目では `test_signal_after_core_success_uses_restored_real_handler` が
  **`tools/dev_wave_land.py` だけを変異させた N5 の失敗集合に現れ**、
  3 巡目では `test_public_main_failure_restores_handler_without_release` が N2 の集合から消えた。
  land のみの変異が待ち手の signal テストを落とすことは依存関係上ありえないので、
  変異へは帰属させずフレークとして扱った。F57 族 (受入全走フレーク) と同じ面かは未確認。
  **通算 6 例で、うち 1 例は変異 baseline を赤にして harness を停止させた** (12:17 JST)。
  受入全走でも 3 例出て、そのたびに非帰属 checker 経路へ落ちている。
  対象は `test_signal_after_core_success_uses_restored_real_handler` /
  `test_public_main_failure_restores_handler_without_release` /
  `test_public_main_real_signal_releases_lease` /
  `test_public_main_real_signal_after_success_uses_restored_handler` の 4 件。
  成果物影響 = 変異 matrix の期待完全集合が走行ごとに揺れ、exact 一致契約 (`DW-M08`) が
  フレーク由来の MISMATCH を出して検出力の判定を曇らせる。加えて受入全走を繰り返し赤にし、
  land を実質的に止める。
  **(2026-08-15 棚卸し) 今も高価値**: 通算 6 例で、変異 baseline を赤にして harness を止めた回もある。受入全走を繰り返し赤にし land を実質的に止めている ([T-1066] が「フレーク本体は未着手」と明記)。
  base: 98314a27a147ed5bf35dfe685a10392da4353ab949123eca3b0d3d8f0e17fc50

- [T-1005] **P2・新規**: `test_codex_worker_launch.py` が受入全走で
  非決定的に落ちる。2026-08-13 の受入 2 走目で 6 件が同時に落ち、同 file の単独再走は 114 passed /
  rc=0 で再現しなかった。2 tip 間の差分に同 file・その依存の変更は無い。落ちたのは receipt /
  manifest / docs authority を検査する node 群で、並行 wave の codex 子が共有する状態
  (`~/.codex/sessions`、docs authority snapshot、receipt) との競合が疑われる。48 worker の xdist で
  再現条件を切り分け、共有状態への依存を fixture 側で断つか、依存が本質なら受入での直列化を裁定する。
  **(2026-08-15 棚卸し) 今も高価値**: 受入全走で 6 件が同時に落ち、単独再走では再現しない。並行 wave の共有状態との競合が疑われ、受入の再走コストを直接押し上げている。
  base: d82094b700addb732d1979743ecad17811bd5d97d0d4de5b9e90e7987739698b

- [T-1059] **P2・新規 (2026-08-13 実測 3 例)**:
  `tools/codex_worker_launch.py` の `--evidence-grace-s` 既定は 5 秒で、この時間内に codex が
  session を作らないと `_terminate` で強制停止される。login node が混雑すると codex の起動が
  5 秒に間に合わず、`codex_exit_code=-15` / model call 0 / wall 8.6 秒 / evidence missing で
  子が死ぬ (11:15 / 11:18 / 11:37 JST)。**launcher の log は空で、receipt を開かないと理由が分からない。**
  `tools/dev_wave_codex.py` はこのノブを露出していないため、親は同 wrapper の `--dry-run` が出す
  権威ある argv をそのまま使い、非権威の観測ノブだけを広げて直接起動する回避を採った
  (`--evidence-grace-s 90`。wrapper が作る artifact directory は呼び手が `mkdir -p` する)。
  成果物影響 = 混雑時に実装子が起動できず、原因も表に出ないため、
  wave が「codex が壊れている」と誤診して停止する。
  **(2026-08-15 棚卸し) 今も高価値**: 混雑時に実装子が起動前に殺され、launcher log が空なので wave が「codex が壊れている」と誤診する。実測 3 例。
  base: c7fabbba71614d65bfd704876f211de472373fbd7538ddb9ef4ca41298c65f65

- [T-1056] **P2・新規**: `tools/dev_wave_wait.py producer` が、
  `.done` も成果物も存在せず producer が生存している状態で、出力ゼロ・rc=0 で即座に返る
  ことがある。2026-08-13 に 5 回実測 (02:44 / 03:12 / 03:55 / 03:58 / 04:14 JST)。
  親が 3 点照合 (成果物実在 + `.done` + producer 死) で検知して張り直したため実害は出ていないが、
  待ち手を信じる呼び手は「子が成功した」と誤認する。成果物影響 = 子の成果物なしで次段へ進み、
  context 無しの出力をレビュー結果と数える経路が開く。
  **回収 context でさらに 2 例 (09:12:29 / 09:17:29 JST)。通算 7 例で、うち 1 例は
  投入 31 秒後だった。**
  **(2026-08-15 棚卸し) 今も高価値**: 通算 7 例。待ち手を信じる呼び手は子の成果物なしで次段へ進み、context 無しの出力をレビュー結果と数える経路が開く。
  base: 97bf917afe4c9b9ded1e2920bb9241b60a4063d40582701776778b707f98adbc

- [T-981] **P2・新規**:
  `evidence_status=invalid` の理由を receipt へ記録する。現状は
  `codex_exit_code=0` / `validator_rc=0` のまま成果物が捨てられ、
  どの行のどの検査で落ちたかが一切残らないため、prompt や成果物の品質を疑う方向へ誤誘導される。
  併せて consult / review 段で web_search を既定無効にするか、
  stdout event の重複キー扱いを証跡検査から分離するかを決める
  (F263)。
  **(2026-08-15 棚卸し) 今も高価値**: evidence_status=invalid で子 1 本の成果が丸ごと捨てられるのに、どの行のどの検査で落ちたかが残らない。原因が prompt 品質と誤診される。
  base: ae409e961cf3e977afc375d291e73b8f288d2dc78708ad165c289c819a2e4ee3

- [T-1105] **P2・新規**: codex 子の sandbox から
  `tools/run_tests.py` が走らない (local 予約台帳を更新できず dispatch へ倒れ、
  `qstat -Q preflight rc=1` で rc=16)。本 wave で 3 回、別 wave でも同型が観測されている。
  子が実測できないと段 5・6 の「緑には実走 nodeid を併記」が常に親へ集中する
  **(2026-08-15 棚卸し) 今も高価値**: codex 子から tools/run_tests.py が走らないため、段 5・6 の実測がすべて親へ集中する。dev-wave の並列度を直接下げている。
  base: 50cce88820e44c993370f3ca1bbdacb3b37601366b503702bc1746c8a4f5c7c3

- [T-1097] **P2・新規・要裁定**:
  `check_ai_provenance.py --message-file` の合否が message 内容でなく repository 状態
  (`MERGE_HEAD`・staged path 集合) の関数であることが、受入の再走を誘発している。
  同一 message file が受入試行 1 で拒否・試行 5 で受理された実測がある。
  親は毎回「message が悪い」と誤解して message を書き直す codex 子を起動しており、
  **失敗時に checker の stdout を出さないことがこの誤解を固定している**。
  診断を出す処方は [T-1092] と同型だが、`tools/dev_wave_wait.py` を
  `dev-wave-t1092-receipt-diagnostics` と `dev-wave-t1076-waiter-bytes-contract` が
  所有しているため、3 者の順序をユーザーが決める必要がある。
  **(2026-08-15 棚卸し) 今も高価値**: 同一 message file が受入試行 1 で拒否・試行 5 で受理された実測があり、失敗時に checker の stdout を出さないことが誤診を固定している。同 file を 3 wave が所有するため順序はユーザー手番。
  base: bdf0e19c043918129eff909dfd4dd8e84869d643925d6ea7cffaf94151f8ff42

- [T-1101] **P3・新規**: 受入試行の終端 (成功・失敗 stage・所要秒)
  を機械集計する仕組みが無く、本 wave は job dir の mtime と log から手作業で復元した (約 30 分)。
  受入 receipt か task-run へ「lease 待ち秒・critical section 秒・終端 stage」を残せば、
  以後のボトルネック裁定が実測でできる。
  **(2026-08-15 棚卸し) 今も高価値**: 受入試行の終端・所要・失敗 stage を機械集計できず、ボトルネック裁定のたびに手作業復元 (約 30 分) が要る。
  base: eb8236d0dba8342b94b13a27931f91ac30f0be71972a322febca97cfbb7c814a

- [T-989] **P1・新規**: 受入 wall の最長 node
  (`test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment`、
  全走 61.6〜90.0 秒 / 単独走 6.81 秒) の実体は module fixture `benchmark_snapshots` の
  snapshot 構築 (単独走 49.80 秒) である。実 repo を hardlink なしで複製しているため
  **commit 数に比例**する。hardlink / object 共有で payer 自体を安くすれば
  「wall ≈ 最長 node + 約 30 秒」モデル上は wall が動く唯一の場所。
  検証は D357 に従い 3 走以上の中央値で行う。
  **(2026-08-15 棚卸し) 今も高価値**: 受入 wall のモデル上「wall が動く唯一の場所」であり、payer が commit 数に比例するため放置すると開発するほど遅くなる (D335 と同面)。
  base: 3dac6c94fe0cb7bbe86bc49932176ad3ab50b163fe1cb9b74c9e239e6f4875f7

- [T-932] **P1・新規**: repository の成長に比例して実行コストが増える構造の
  テストを棚卸しし、D335 に従い恒久保留 (ユーザーの
  明示命令まで実行対象外) を執行する。保留は削除でなく可視な skip 印 + 機械可読な理由の
  記録で行い、正しさゲートを担うテストが該当した場合は保留一覧でユーザーへ提示する。
  **(2026-08-15 棚卸し) 今も高価値**: 成長比例テストの棚卸しと恒久保留の執行そのもの。放置すると受入時間が repository の成長に張り付く。
  base: 0ad79752cd8e0d64f1706f05c9301311409e9b29506ba548cad4ba97acd9299d

- [T-650] **P2・新規**: claim → 受入 → land → release/通知 を 1 つの
  wrapper へ束ね、受入赤・land 失敗・例外でも必ず release する機械的な finally を作る。
  現状は入口の契約文が終端での解放を要求するだけで、取り残しは TTL 2400 秒まで他 wave を止める。
  **(2026-08-15 棚卸し) 今も高価値**: lease の取り残しが TTL 2400 秒まで他 wave を止める。claim から release までを 1 つの finally で束ねる機械的な手当てで消える。
  base: 5afc22c82dd95f7701a57bc4e51e692d7e92b6e35be3f77da82f46165660aa66

- [T-826] **P2・新規 ([T-813] (ii)、2026-08-11 裁定)**: M0 =
  受入テストの分割不変性と real-repo 排他閉包を機械検査で成立させる。排他閉包の欠落は
  分割と無関係に同時 dispatch の偽赤 (F136 族) の源であり、独立価値を持つ。
  [T-813] の再評価条件 1 の前提。正本 = `output/insights/2026-08-11_t813-acceptance-sharding/`
  **(2026-08-15 棚卸し) 今も高価値**: real-repo 排他閉包の欠落は分割と無関係に同時 dispatch の偽赤 (F136 族) を生み、受入の再走を恒常的に増やしている。
  base: efc3dd4c5cdbfc3a25601b2926e5b9943b27a036ca1ef552265a997b3246b178

- [T-754] **P3・新規**: `tools/check_wave_startup.py` は local main
  との乖離と handoff の実在を見るが、**同じ worktree を他 process が使用中かを見ない**。同一
  タスクの背景 job を 2 本起動すると slug が一致するため必ず同じ worktree へ入る
  (F203)。「同一 worktree path を argv に持つ生存 process が自分以外に
  居ない」を fails-closed で検査する。自己マッチと並行 wave の子への誤マッチを避ける照合方法
  (pid 除外、worktree path での一意化) を含めて設計する。
  **(2026-08-15 棚卸し) 今も高価値**: 同一 worktree を他 process が使用中かを見ないため、稼働中の wave の worktree を壊しうる (F203)。背景 job 運用では実害が大きい。
  base: e60a0cb2dcd866ce1b5d40e78df20289d64529541d6bfae2da59c2b127f5baa5

- [T-1038] **P2・裁定済み (第 10 回)**: (a) checker 側修正 — `_check_worktree_handoff` は
  tracked file を foreign control-plane として通し、untracked のみ残置と見なす。同 wave で
  submodule 初期化失敗時の提示文も `-c protocol.file.allow=always` 形へ直す (本文の未採番裁定)。
  実装待ち。
  **(2026-08-15 棚卸し) 今も高価値**: docs/handoff の残置が全 background job の起動検査を赤にする再発を、checker 側で構造的に止める裁定済みの修正である ([T-1039] / [T-1037] / [T-234] の恒久対応)。
  base: a32def30b6da412b22aab3bc3481f53fc6008cdc038d53e6dd1ed7b9bc2f2fe4

- [T-1090] **P3・要裁定**: 非帰属 checker は赤 n 件に対し collection と rerun で dispatch を
  2n 回行う。**本 wave が実測モデルを取り、有界並列化は不採用を推奨した**
  (低負荷で `T(n) = 15 + 63n`、P=4 の節約は受入試行あたり平均 約 26 秒。
  単独 rerun のノイズ床を上げて帰属する赤を非帰属へ倒す偏りがあり、
  `--force-dispatch` の同時投入は他 wave を遅らせうる)。
  代替として **1 dispatch job で複数 node を扱う設計** (2n qsub を n または 1 へ減らす) を推奨する。
  これは rerun の実行環境を変えないので同じ偏りを生まない。dispatcher の secure task と
  receipt schema の新設が要るため、着手可否はユーザー裁定を待つ。
  **(2026-08-15 棚卸し) 今も高価値 (ユーザー裁定待ち)**: 非帰属 checker が赤 n 件に対し dispatch を 2n 回行う。有界並列化は不採用を推奨済みで、1 dispatch job で複数 node を扱う設計の着手可否だけが残っている。
  base: c6826c40787d7e470687656b3cfcf5a551c9f34a8e1a52ba70f7ba055ae7b8b9

- [T-894] **P2・新規**: 受入待ち手の merge 競合診断に競合 path を
  出させる。現状は `stage=merge rc=70` だけで、親が `git merge` を手で再現しないと
  着手できない。待ち手が abort する前に `git diff --diff-filter=U --name-only` を
  job directory のファイルへ書き出すだけで往復が 1 つ減る。
  F231 の残余。
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 現状は stage=merge rc=70 だけが出るため、親が git merge を手で再現しないと着手できない。競合 path を job directory へ書き出すだけで往復が 1 つ減る。
  base: f0dff0e65d1eac1b1b9e44dbbbe314a977c4474d7f85716af5dac6ebc9cd7aa1

- [T-1009] **P2・新規**: 変異 harness の失敗 node 抽出が
  `--force-dispatch` 経由では壊れる。dispatch が子 stdout の中間を省略するため、
  失敗が多い変異で `PARSE_ERROR` になる (本 wave の N6)。回避策は直接 pytest を runner にすること。
  harness 側で「省略された stdout を検出したら fail-closed で別経路を促す」方が安全。
  **(2026-08-15 棚卸し) 今も高価値・要整合**: --force-dispatch 経由で失敗 node 抽出が壊れる本項と、「変異 runner には --force-dispatch を必ず渡す」という運用 ([T-613]) は現状そのままでは両立しない。どちらを正とするかを決める必要がある。
  base: 8a3c5039da6976c2454512b899ebf81ee758f0b6c7572e853113d50af5081dc7

- [T-959] **P2・新規 ([T-925] 段 7)**: `docs/dev-wave/**` の **L2 には合計上限が無く**、
  各節の空きの総和が 7,252 bytes ある (上限は L1 合計・L1.5 合計・L2 単節 1,000 bytes の 3 つだけで、
  ファイル単位の上限は存在しない)。新規 L2 節 1 つの費用は入口の条件 dispatch 表 1 行 (最短 79 bytes)。
  **L0 を 180〜280 bytes 空けるだけで堰き止め 4 件すべてを収容できる**見込みで、L1.5 / L1 を
  個別に空ける従来の枠組みより桁違いに安い。設計すべきは (i) 各契約の発火条件が既存 L2 節の条件と
  一致するか、一致しないなら新規 L2 節が `docs/skill-self-improvement.md:28-30` (D271) の
  「発火実績あり × 機械代替なし × 意味検索で反証も同一発火点の既存正本もなし」を満たすか、
  (ii) L2 化で読み込みが条件成立時だけになる意味変化が許容できるか、(iii) 入口 1 行の原資。
  registry (`tools/check_docs.py` の `REQUIRED_REFERENCE_SECTIONS`) と Codex 側 skill の
  同時更新を伴うため実装面で、Codex author が要る (D95)。
  **(2026-08-15 棚卸し) 今も高価値**: docs 予算クラスタ全体の解錠鍵。本棚卸しでは docs 予算だけを理由に見送った項が 38 件あり、L2 の空き 7,252 bytes と L0 の 180〜280 bytes が唯一の現実的な収容経路である。
  base: 66da5514dd61ccf3c988a0df19345a3cedd172f0c6ed0eac5212c6819b0b147b

- [T-724] **P2・新規 (本エントリ)**: `tools/spool_fold.py:1151` の
  `carry_re` が `変わらず (前エントリ参照)` という序数なしの旧形式 stub を carry と認識せず、
  `substantive_digest` がそこで停止する。carry 鎖にこの形式を含む item では、fragment の
  `base:` 照合が実本文でなく stub の digest と突き合わされ、「他 wave が先に書き換えていたら
  止まる」保護が実質的に効かない。本 wave の [T-201] で実測した (F190)。
  閉じ方は `carry_re` の拡張か旧形式を carry として解決する経路の追加、および
  一致しない `変わらず` 形式の存在を検査する meta-test。
  **(2026-08-15 棚卸し) 今も高価値**: 本 wave の実測で、active 657 件のうち 35 件が旧形式 stub (変わらず (前エントリ参照)) を carry 鎖に含んでおり、その全件で base 照合の「他 wave が先に書き換えていたら止まる」保護が効いていない。
  base: b481182dfc4e096767f6889b245f8d8afdf25d59dab03e359a7628b814d88828

- [T-711] **P2・新規**:
  `docs/spool/failures/` の fragment は「新規」「再発」しか持たず、**既存 F の恒久対応欄を
  更新する経路が無い**。現在 `docs/failures.md` の 10 件が「恒久対応: 未実施」のままで、
  そのうち F176 は本 wave で実装済みだが台帳上は未実施に見える。
  wave が canonical を直接編集するのは禁止されているため迂回できない。
  選択肢は (a) fragment に「更新」節を足す (対象 F と差し替える行を base digest 付きで書く)、
  (b) 恒久対応の状態を F 本文でなく別の索引に持つ、(c) fold 後に人手で直す運用を明文化する。
  **(2026-08-15 棚卸し) 今も高価値**: failures 台帳の 10 件が「恒久対応: 未実施」のままで、うち少なくとも F176 は実装済みである。canonical 台帳が事実と食い違う状態を wave 側からは直せない。
  base: a3f60d9be2c4431122737a122660af1049ad8e9b2cdc0853d62246284b175f6a

- [T-351] **P2・新規 (本エントリ)**: `/rulings` の収集経路に、現 branch の
  valid pending fragment を加える。記録先は spool へ変えたが収集側が canonical しか読まない。
  **(2026-08-15 棚卸し) 今も高価値**: 記録先を spool へ移したのに /rulings の収集が canonical しか読まないため、未 land branch 上の裁定が総ざらいの母集合から丸ごと落ちる。裁定の取りこぼしに直結する。
  base: 79da9d60037273b9c159920612bac3bd8643311f6cd21c31e9f9a909b9d25135

- [T-895] **P2・新規**: 「次の一手」の項が裁定で終端したまま
  active に残り続ける構造を検知する。本 wave の実測では 62 件が滞留し、うち 52 件は残件ゼロ
  だった。先頭行の終端語 (終端 / 見送り / 受容 / 現状追認) による抽出は誤検出率が約 16%
  (10/62 は生きた項) なので、**gate ではなく定期報告**にする。受理集合を変えないため
  `DW-G05` の影響は「報告の有無」だけで、実装しなければ backlog の単調増加が続く。
  **(2026-08-15 棚卸し) 本 wave が手作業で 1 回実施した (高価値枠からは外す)**: 2026-08-15 の全件棚卸しで active 664 件を判定し、陳腐化 + 価値小として 305 件を見送りへ移した。定期報告として機械化する価値は残る (今回の手作業は 1 wave 分の丸ごとを要した)。
  base: 4bd34e04e72b7cf3f799846923e510a545f1ed79e75ac43446b4d3d2f55ca1e3

- [T-896] **P3・新規**: [T-186] が見送り台帳 (`docs/phase3.md`) と
  worklog の「次の一手」に二重在籍している。台帳側が残余 3 件の正本で、active 側は重複。
  ID 保存則は両方が sink を満たすため機械検査に当たらない。同型が他にないかの棚卸しと、
  どちらを正本にするかの規約化を行う。
  **(2026-08-15 棚卸し) 実測した (高価値枠からは外す)**: 見送り台帳の item 先頭 ID 188 件と active 657 件を突き合わせ、二重在籍は 8 件 ([T-059] [T-181] [T-183] [T-184] [T-185] [T-186] [T-189] [T-190]) と確定した。うち 7 件は active 側から落として台帳側を正本にし、[T-190] だけは受入・land を現に阻害しているため active に残した (正本の一本化は未了)。残るのは「どちらを正本にするか」の規約化である。
  base: 46d6a3e85cbc58c82eca7634739c481378f9efa019e91aab293fcc267e29c041

- [T-612] **P3・裁定済み (2026-08-07 委任) → 実残骸観測後に設計**: 未完了 container の自動回収は
  手動削除 / `--resume` のまま、`DW-G04` に従い実残骸 path を観測してから設計する (wave 記載の
  追認)
  **(2026-08-15 棚卸し) 発火条件が成立した**: DW-G04 が求めた実残骸 path の観測は、エントリ 552 で得られている (変異 scratch を rm -rf した結果、git の worktree 登録に実体なし残骸が残り、次の変異走が rc=125 で起動前に落ちた)。設計へ進んでよい。
  base: 30633abf55cc2f5df7e7d56a5fa1e6e65cb3a4c051bb8ca371c57cf6be445cec

- [T-758] **P2**: 既存 docs の誤り 3 件の訂正 —
  `ccbench-anatomy.md:211` (ermia active は raw cstamp)、同 `:126` (mocc の自由軸は 2 つ)、
  `phase3.md:269` (si の trace-hook 既存)。1 件目は S1 着手時の必須知識として書かれており、
  従うと誤実装するため優先する
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 3 行の訂正だが、1 件目は S1 着手時の必須知識として書かれており、従うと誤実装する。protocol 移植 ([T-755]) の前に片付ける価値がある。
  base: 8cb2d974b48971d557500bb5faf718751f32b28ece2f8631fe6730e1e126ecfc

- [T-1107] **P2・新規・フレーク**:
  `test_public_main_real_signal_releases_lease` は 48 worker の受入全走でだけ赤になる。
  子へ SIGTERM を送り rc=143 を期待するが、負荷下では signal 到達より先に
  `acceptance-scheduler-attestation` の `marker-count` が発火して rc=70 になる
  (テスト用 tmp repo の child argv は scheduler marker を出さない)。単独走・焦点走では緑。
  受入を止める帰属赤として観測されるため、期待を「143 または attestation 失敗」に広げるのでなく、
  marker を出す child か attestation を待たせる seam を設ける方向で直す。
  **(2026-08-15 棚卸し) 今も高価値**: 48 worker の受入全走でだけ赤になり、帰属赤として観測されるため受入を止める。機序 (marker-count が signal 到達より先に発火) と直す方向 (期待を広げるのでなく marker を出す child か seam) まで特定済みで、着手可能である。
  base: 5d7b11b224e95d58d0dcd6a5fffba5ecb0148eabef096c524ba0530dfeb28525

- [T-1109] **P1・新規・ユーザー裁定待ち**:
  D122 決定 (2)(ii) の `PBS_JOBID` 受理文法が実機で充足不能である。
  択 (a) transport 側を `(?:0:)?<request-id>` へ拡げる (collector と同形。負例集合の更新を伴う)、
  択 (b) job script が request ID を切り出して渡す (**gate が検査する env の書き換えであり親は迂回と判定**)、
  択 (c) witness を `PBS_JOBID` 以外の実在証拠へ替える。
  **親の推奨は択 (a)** — repo 内に既に `(?:0:)?` を許す consumer があり、D122 決定 (7) は
  witness を attestation でないと明言済みなので防護の主張は減らない。受理集合の変更なので D96 手続。
  **(2026-08-15 棚卸し) 今も高価値 (ユーザー裁定待ち)**: 実機の `PBS_JOBID` が gate を通らないため 8c live pilot が起動できない。親推奨 (a) の根拠 (同形の consumer が既に repo 内にあり、D122 決定 (7) が witness を attestation でないと明言) まで揃っており、裁定 1 つで [T-1112] が動く。
  base: 22fb5fff93adb9c579ab62548fd5f9263c0eac5b4de27de6cc05d736f14039ef

- [T-1112] **P1・新規**: 上 2 件が閉じた後に 8c A/B/C live pilot を再投入する。
  job script と依存 staging は保全済みで、単独性検査と gflags/glog build はそのまま再利用できる。
  **(2026-08-15 棚卸し) 今も高価値**: 8c A/B/C live pilot の再投入そのものであり、ユーザーが目標の柱と位置づける無人ループの実走にあたる。job script と依存 staging は保全済みで、閂は [T-1109] / [T-1110] の裁定 2 件だけである。
  base: c06e27b6aa807951e48f05aa83655d5c8877ddb307ff51f1fee9f35bc1b037de

- [T-1111] **P1・新規・ユーザー裁定待ち**:
  fail-closed admission 述語に「実在の production 値を自分の述語へ通す positive control」を
  族として義務づけるか。F97 (登録済み較正が自分の attestation 述語を通らない) と
  本 wave の [T-1109] (実機 `PBS_JOBID` が transport 述語を通らない) は
  別 producer / 別 consumer の独立 2 例で、`DW-G03` の族一般化閾値を満たす。
  どちらも「誰かが実際に走らせるまで発見されない」型である。
  検査義務の新設なので親は実装せず裁定へ返す。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 「fail-closed の述語が、実在の production 値を実際には通さない」型は F97 と [T-1109] の独立 2 例が揃い `DW-G03` の閾値を満たす。誰かが実走するまで発見されない型なので、族として positive control を義務づける価値がある。
  base: 1055bb6d5affb151aca69401aeffa96d7c26f9d189694686d8650971adcca882

### 新規

- {{T:update-item-stub-lint}} **P2・新規 (段 8 自己改善)**: `tools/check_docs.py` へ
  「spool fragment の `更新` / `完了` item の本文が carry stub 形式 (`- [T-NNN] (N)` または
  `- [T-NNN] 変わらず ...`) に一致したら赤」を足す。{{F:update-item-carry-stub}} の機械化であり、
  現状は `base:` 照合も `check_docs` も `spool_fold --dry-run` も緑のまま素通りする
  (本 wave で実測)。実装面のため Codex author が要る。成果物影響 = 未実装なら、
  main 取り込みを挟む wave が `更新` のたびに元本文を失う経路が開いたままになる。

### 見送り

#### 正しさ・防壁系

- [T-390] **D122 の opt-in 経路の残置** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (a) で「既定拒否のまま残し使わないを運用規律とする」が確定し撤去もしないと決まった。再訪条件 = opt-in 経路が実際に使われた 1 件。
  base: 659778e6a512d4fe0889107188c8ed9ce5b18c1147fccd06c0bd6e1446de713f

- [T-408] **symlink 解決の食い違いの調査** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (c) で食い違いを残すと確定し、調査 5 点も完了して実損 0 と実測済み。再訪条件 = 現行挙動を pin するテストを足す wave。
  base: 06f13ee2e1dd69dea516918462a5d696b56d1f36557993f1c70e21054a3880cf

- [T-460] **compile 中の source 差し替え ABA 対策** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。単独 wave を立てず P3+P4 実装 wave の設計入力に含めると裁定され、入力としては記録済み。再訪条件 = P3+P4 実装 wave の設計段。
  base: 3ceeaa1ee37338c0de311d2da5ba2e8e93d34fe7d2738fc3273cb525f081d35d

- [T-462] **formal report schema の binding receipt と recipient 閉集合** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。単独で決めず D121 P2 面の wave の設計入力に含めると裁定され、入力としては記録済み。再訪条件 = D121 P2 面の wave の設計段。
  base: 5d4aaf9021957f4c0958cff273c22efdf3dd95f0f084046506a954944398a296

- [T-673] **本番 guard D の採用** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。D は不採用で終端と裁定済み。残余の運用義務の所在も probe clone 削除で決着した。再訪条件 = 同族の CI 検出が既存テストで担えなくなったとき。
  base: e5d9f4b4c59fd0693d82b4437b08b20876c7fcd3874bb488fbcad05f993f9f99

- [T-745] **静的検査の走査対象を Makefile / CMake / qsub script へ広げる** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。両レンズと親が独立に全走査し、現 repo に該当する legacy module 名は 1 件も無いと実測して DW-G04 で見送り済み。再訪条件 = それらの経路に module 名が実際に現れたとき。
  base: 09b3b00dacbf35a36770c989da69d2110624aed223a70464b2fc7f9a3413aa6a

- [T-957] **被覆外 3 経路** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。scope 外で終端と裁定済み。再訪条件 = 実害 1 件、または同面を塞ぐ変更への相乗り。
  base: 6e1fde50443ff882fc8a51f28443d250eb8b6f79bf2ff44915b740c8d7df7863

- [T-964] **symlink 経路の閉鎖** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (現行 built-in spec から到達不能・実害ゼロ・塞ぐと正常系も狭める)。再訪条件 = custom spec 経路の実需。
  base: 9abd8e082320fd6acc3b3d429510c994cc8d8af3b1ba6612416572aa38c39123

- [T-321] **guard_bash の realpath 非解決・cd 追跡なし・hardlink alias の硬化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。実測された迂回を伴わない一般硬化。実測付きの writer 迂回は [T-1025] が P1 で所有する。再訪条件 = 同型の実害 1 件。
  base: 589ca7b82fc4b893fa115f1e7282412a4ecdba8a7b481502fa245b976e451c23

- [T-289] **8c freshness 検査と state 生成の TOCTOU** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。並行実行は計測規律が既に禁じ、build 経路は competing_bench_pids() が部分的に覆う。再訪条件 = 同型の実害 1 件。
  base: 5fab4586953205bb8e7c0df70413ae3e86ca29a247861ed77f6dbd8920085ff0

- [T-284] **重複 key の扱いが submit と job で非対称** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。非対称の事実は D113 に記録済みで、実害の観測はない。再訪条件 = 同型の実害 1 件。
  base: a634d59dfb898c2b431ec8bae6fb9c89febd5ecf3efbfa98762475ffbfd9f068

- [T-256] **_read_regular_at の未捕捉 OSError** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。handoff 経路からは D108 で到達不能。DW-G03 の独立 2 例目が出ていない。再訪条件 = 同型の実害 1 件。
  base: 3723b250e6aa5d3dbac780e99f309b0fca0bc0a630233310ad10a7923cf7255c

- [T-418] **state_from_dict のエラーが未信頼 checkpoint 文字列を再掲** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本 wave 由来でない既存挙動で、修正は既存テストの期待値変更を伴う。再訪条件 = 同型の実害 1 件。
  base: 66e91237fe3745f79b2bae58c3100e7d90e0953c66ca837f2df6a6d9667ed530

- [T-1024] **hook 検証と spawn の間の窓 / worker 存続中の再検証** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本文自身が「粗い provenance 基準では既定で見送り側」と結論している。再訪条件 = 同型の実害 1 件。
  base: 00f30dd6e5116540bd0c34fe56a99ad6495b117c8b807edbd49b9852c8201879

#### 研究・計測系

- [T-316] **R2-b-1 の (a) 追認 (native comparator 干渉残余の受容)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。干渉残余は台帳・runbook への明示記録で受容すると追認済みで、本項に残作業がない。再訪条件 = 同一 process 内 comparator 干渉の実害 1 件。
  base: 93bf88d748fe0381dde2a940f7e62240a8f78d3d8b6859cd92c6bca2cadaa0fc

- [T-126] **逐次停止 v2 の attempt staging 回収順序** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。実装・main 統合・land まで完了済み。live qualification は本項の scope 外と明記されている。再訪条件 = live qualification を実施するとき。
  base: 553468cd195856c44187934bcd23eac02fc37456e863ede2341f8900f481ddd5

- [T-433] **意味的充足契約 v1 の採用 (D156 発効)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。U1〜U4 が全問採用されて D156 として発効済み。機械実装は [T-941] P6 実装 wave の所有。再訪条件 = なし ([T-941] が所有)。
  base: 92467bfd22db8403def77e4c52879359906f5364db60faf486795ce9f7937d3e

- [T-463] **予算・新鮮性を cell key で数える方向** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。方向は裁定済みで、詳細設計は P3 台帳面の実装 wave の設計入力に含めると決着した。再訪条件 = P3 台帳面の実装 wave の設計段。
  base: f602b95e658282036993faf6e86755fe35c0bbf08cbc7b53108c9c2589acb31d

- [T-499] **Q1/Q4 の保留と (A) 承認手番** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。Q1 = (b) 保留 / Q4 = (b) 保留で確定し、承認手番は前提 (active ratified freeze v2) が揃うまで保留のまま。再訪条件 = active ratified freeze v2 が揃ったとき。
  base: 08edf035d4a14aebc557847af2a282d2187dba71c8bd778ad7bfb9fbc02e59d4

- [T-517] **壁 1 の非認証 probe lane** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。設計項として保持し実装しないと裁定済み。要否の再評価も [T-419] U-2 の完了に従属する。再訪条件 = [T-419] U-2 の完了時。
  base: 489f9f4778a344a1d6a088c542a8cfa0b7bd2b260c00817893f2b48d5d72eea4

- [T-606] **v2 oracle manifest の production producer** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。v2 manifest を要する consumer の実需が出るまで作らないと裁定済み (プロトタイプ基準 D205)。再訪条件 = v2 manifest を要する consumer が現れたとき。
  base: 8e03c9ec0d47fbbd870d2c93c93e1f4ffdfd602932a8a90dc9b0e11379e4d74b

- [T-747] **床値 build の toolchain 束縛** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(B) を実装し混用不可を機械検査で固定済み。残る非束縛量は手順書 §5 R-4 に明記して終端した。再訪条件 = 非束縛量 (cxx version / cmake path / module_list) が実害を出した 1 件。
  base: 27402a7bb39629b7fc68b26ef179a0cf5d2e8cfc3cae9d81b4b203e33aacc2fd

- [T-763] **65 env x 2 世代の合成 calibration 成果物** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。作らないで確定済み (段階導入の原則に反する)。再訪条件 = 同層の受理集合を変える変更時。
  base: 02cca0c6f5e30b4c3613752b1a464ca3aa6103c2fe55c305c064fd028ad8e88b

- [T-803] **pinned literal を人間承認の恒久形として承認** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。承認済みで、記入時点は将来の実凍結手番と決着した (署名方式は不採用維持)。再訪条件 = なし。
  base: b012b046b8cffd7314d4bfa09311fa13a69846a122e860b466eaf533724dbc68

- [T-816] **凍結チェーンが gitlink 前進を塞ぐ件** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。手順 4 を完了し、D328 の保留執行で閂を外して受入も赤ゼロにした。再訪条件 = 凍結チェーン検証の保留を解除するとき。
  base: 0e968486dcf210b8da2acee7a4f7c213187d975b3fe976d2a79e0d281e786b7d

- [T-838] **hard block (凍結 v1 raw trace と歴史 pin 再現経路)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-816] の裁定へ吸収され、実体 (bytes 据置での trace 再検証退役と歴史再現 driver の記録) も処理済み。再訪条件 = なし。
  base: 703e90111233697c00f6831f016a1d69f6d28ca6dd4478551eb716557d36a7ad

- [T-840] **copyout 系 Q1〜Q5** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。全問親推奨どおり裁定済みで、Q4 は既存 cache entry の拒否・再発行をしないと決着した。再訪条件 = なし。
  base: 1aaafa5c35d072e1b8cf06adc633f21d98f4e56df91d0a6341c902e273970c7b

- [T-857] **legacy manifest 由来 observations の位置づけ** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。明文化のみで終端と裁定済み。certified への到達は [T-804]/[T-856] 側が閉じた。再訪条件 = なし。
  base: f172ec4c35c8d9aa46c5ffd081d8bea8a584036ed15070da465d748f297704d7

- [T-913] **公表台帳 R2 番人 4 function の保留可否** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置を追認済み。保留したい場合は D320 とは別の個別裁定を新たに取ると決着した。再訪条件 = 個別裁定を取るとき。
  base: 1b7ec12815c1dad1cea463cc9dd65771976e4192d948ba0d84f9f08b4eec25f5

- [T-915] **holdout live scan の保留可否** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。保留対象外で確定し、ファイル数比例をやめる最適化として [T-902] 実装側が扱うと決着した。再訪条件 = なし ([T-902] が所有)。
  base: a35aa3188c6c32236d6caad062a7fe661dff4cfabda3354a9b16941e45a22a78

- [T-942] **材料レポート renderer の結線 (V-12)** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。P6 実装 wave へ同梱すると確定済み。残は V-8 のみで別 ID が保持する。再訪条件 = なし ([T-941] が所有)。
  base: 7e686d1089d41d4031425bae76542de8b5596fc163061f65a496dc81c553fcb3

- [T-955] **guard bytes 期待値の trust root** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置で確定済み。独立 trust root・launch receipt 化はいずれも作らないと決着した (粗い provenance 基準)。再訪条件 = なし。
  base: ba7374622454ab84386e6e40a3a0e062584660f1352bb34e916b67d658c8499d

- [T-962] **B4 の第 5 案** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(c) 今は足さないで確定済み。再訪条件 = manifest R1 (Q-D の同一 land 再解釈) の裁定後。
  base: b0ed953790ad5142089bfc7b1060d48a50839fa6b78873d36403d85ac5e5a430

- [T-965] **PRNG byte grammar の事前登録文書への昇格** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。据置で確定済み (段 4 裁定 + transcript で足り、grammar 選択は結論を左右しないと感度実測済み)。再訪条件 = なし。
  base: 131a23140bd87eb52568dc98d479279879ccd8842ca7d95f948170bfefa93798

- [T-969] **予約式の見直し** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (全滅系は journal 早期停止で有界化済み)。再訪条件 = 予約超過の実測 1 件。
  base: 7e56d6215ee74470b6f53ae9d7bd6aebb8e48c98f8549dd8975fb6c2fa09a852

- [T-970] **perf_candidates の採用** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (「使わないが evidence として記録」の現状維持)。再訪条件 = F89 の裁定時。
  base: bda7885fb221dd0cc6b1c1f83cb9c7ef7318ccaf8bc4f4d0bd2f9f01944fe0e1

- [T-988] **Q1/Q4 保留下の機構状態** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。裁定済みで、実装項目は別タスク・機構は fail-closed 維持と決着した ([T-499] と同束)。再訪条件 = [T-499] の保留が解けたとき。
  base: 5492de59a0a13216388f35ec5e3086d6e8f54bb1b970cb133d839bd866e3c6f4

- [T-468] **registry の canonical authority** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。詳細は確定し、実装は [T-470] の配線 wave に同梱すると決着した。同 wave は完了済み。再訪条件 = registry authority の実害 1 件。
  base: 14a70ce15fa10ab89eff2fcdec8ca898dae8940aff51eacf77f59118263812c4

- [T-409] **EVOLVE hole 文法 v1 の実装** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(a) land せず破棄が確定し、残余 3 点は別 T へ分離済み。うち 2 件は既に非 active で、残りは [T-473] が保持する。再訪条件 = なし ([T-473] が所有)。
  base: 16bd7c6c4b794c35b1f9e7098d7d41f870d8ad310453f07098938f414e459331

- [T-416] **in-domain 改竄 (rejected -> fail 等)** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。値域検査では防げず、閉じるには entry 件数上限と origin 束縛が要る同一 UID 敵対者前提の面。再訪条件 = 同型の実害 1 件。
  base: 470594b262bbfdc6d4637176a469da2ac4d861659e8d6c22bccfee3d02485e06

- [T-704] **receipt atomic create 後の例外で受理主張と実在が食い違う** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。既存欠陥で悪化させておらず、構成が必要な稀な組合せ。再訪条件 = 同型の実害 1 件。
  base: d93c5f44a6c050b651f15534ff9ac83de15218b8e0848445814b89bd42369c28

- [T-705] **_atomic_publish が例外時に rollback しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同上。再訪条件 = 同型の実害 1 件。
  base: cdc85bc493c9f639093e55265751957307aa40d8373773ad504635d80029b68e

- [T-706] **KeyboardInterrupt / SystemExit で receipt rc と process rc が分離** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同上 (診断の一貫性のみ)。再訪条件 = 同型の実害 1 件。
  base: 601cc0f1162888b3a2f21a31ddcea899a7daebee817fcee6acf42b80347a7ac0

- [T-707] **staged temp の同一 UID 別 process による置換** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提。再訪条件 = 同型の実害 1 件。
  base: 2ca6d908588c19924b733802918dd4111c891f115677cb2b88e5db35ebd87bb1

- [T-708] **os.replace 経路の staged temp 同一性の回帰固定** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。os.link 経路は固定済みで、片側のみの欠落。再訪条件 = 同型の実害 1 件。
  base: c30bf305357d5ea84fbba6c8c0ed06d5752739f004336b88b0cacc53b4b09d16

- [T-1104] **_write_create_only の truncated JSON 残留** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。共有 helper のため consumer 全体の受理集合に触れる割に、書き込み途中失敗の観測がない。再訪条件 = 同型の実害 1 件。
  base: 6c2827460a16cd21586513730c7fda8f78cd15e975d15a8e46e676e25afc5532

- [T-1006] **_durable_json の read-back 検証** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。short-write ループと fsync は既に持ち、欠けるのは read-back のみ。再訪条件 = 同型の実害 1 件。
  base: 932a0ddd1d34194d8f67d72393d970838dbaf790c7408646652e3f53b71ba4f3

- [T-378] **capability 発行器の同一 process 内 caller からの隔離** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。別 process / OS capability / 署名鍵への移設が必要で、信頼境界は docstring に明記済み。再訪条件 = 同型の実害 1 件。
  base: 11241e668025f7949086570e9e74aeaa9aa64864fdd775ed36857dadf7e8a8f3

- [T-379] **pegasus/*.sh と calibrator の任意 binary path の閉包** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提で、正常系を狭める。再訪条件 = 同型の実害 1 件。
  base: e095f6e252efe42235537b18262188a6de0b169e68f77fb2ef2583a03d49f66c

- [T-384] **evidence 発行と build の間の ABA / 混在 snapshot** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。source root の同一束縛と記録までは実施済み。再訪条件 = 同型の実害 1 件。
  base: cb0b999d4a79d1630fc1db74a2ba125eb30571d1dab548f51abed84bbb01ebfa

- [T-501] **admission validator の WAL 側 ABA** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。lock 側は D170 で閉じており、残るのは bytes 同一性の保証という provenance 面。再訪条件 = 同型の実害 1 件。
  base: 9f09f87e7ecc6168da8470317800ea656ac16ae47bf31031d74f8e9f9340c827

- [T-465] **duplicate-key parser が raw key 名を例外へ反射** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。journal に残る診断面で、受理集合は変わらない。再訪条件 = 同型の実害 1 件。
  base: 5b2c6c42c46eccf4c9090298a3723633c27c0da89b81a714c48ec8f487550883

- [T-322] **campaign-id / lock preimage への namespace 束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 84827456480026a6a1d2b36fd716b7fb806f6d6729e43f59202569f8b1746394

- [T-310] **DW-O09 のファイル集合 pin digest (F39)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 5feb7c362963ac1c4600da404d350116683d511173af5a2a3727a13e73ab1a57

- [T-252] **dispatcher receipt への request SHA / repo commit / driver SHA の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 775f9d670628859c74c3e914522343549d133cd1939e64f7ad8d8e7cccac1e54

- [T-273] **toolchain version に floor を課す** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: b09f8a7de323866ffd87187965bf3fe02124f0b9fcb2ae95614c533a8759e33b

- [T-380] **旧 campaign 値を内包する freeze 経由の laundering** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 9c39caaee836fe90af0fa107cb1c45d7c8c098b26e08996e9d7c850c321846ce

- [T-381] **全 receiptless 歴史成果物の遡及再分類** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 47db843ae544d93ce29cfefd87463e3b5a9eb40fcde0dc4727a2070b7d1c18a7

- [T-382] **T126 control の receiptless 旧 campaign pin の張り替え** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 970c980012989ad89b90e057ea9c8cac8878d0fb26974959567e2eee0a012e45

- [T-383] **eligible_for_refreeze を receipt chain から決める** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 160b79511f26a6988ccb3daf5f29fec14e6e24404f74f6ba592ac34789628911

- [T-444] **取得経路の proof chain 束縛 (acquisition receipt 新設)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 6000e5ec65ffe271386feecadac23b67349c135aa3dbc3195579bbf9489f9a6b

- [T-477] **content-addressed path の強制と publish receipt 束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 91f49f1469f23678e6347bda3aaf389e9aac41326be1adb2a0848bc0c57f0f25

- [T-502] **implementation field の build source への束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 8f62013a58264d262c3a695508b25873585f40a7bd8d0fff73eb9ea99ee8f27f

- [T-535] **trust root を Python module origin と制御ファイルの閉集合へ** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: acd1861d15f9aa471de6fd5981070e8df2d2faa438ed8ee7699570f189212c9e

- [T-722] **lock/WAL の外側への authority digest 固定** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: de552da87d7c396a725484d457683a954bf089d2366f6eca58ee48af5a50b352

- [T-723] **非偽造の lane marker の設計** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 535e32977f2c589e1350f0a2d300a5417f40ea1354237839563479128f71a31a

- [T-735] **contract_loader_* の wire key 改名** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 7f3ee71e37b9fb7f56559b275bb47c724b77259f74f889aa86c9a9eb1b151931

- [T-783] **S-3 (a) attempt 脚と成果物への binding report 追記** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: f851af2cc9e4e66565d3c50e7405732bb405828a189ab7f888ff59add0af6b07

- [T-1070] **axis_trigger_gating.py の sha256 と記録値の不一致の整理** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: a9a821572d5d97851224f40ab46a4e4875dbc11aaab0f172eea28203d2597e7d

- [T-1088] **receipt を持たない旧 portable artifact の棚卸し** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 5f441c4711db35310050ead1219f695031131099512fdf3552b65f2b7acdc7bd

- [T-883] **性能値主張時の dispatch receipt の worktree 外退避** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 7e469450931775c73d7bb636c3cbf4f2e04fdb29d8b9754b29c1a759d7238c71

- [T-249] **凍結 file に残る共有・サイト値の移設** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-293] の D96 手続を要し、共有・サイト値の更新実需が出ていない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 5a51a4b0b26bc3d79ad351802c88764b186629083cc5125cf582d1dd4f26fb56

- [T-099] **凍結成果物に placeholder が入った場合の waiver 契約** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。凍結成果物への placeholder 混入が一度も観測されていない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 41d16f3f871cd828dacd305a3a3d60a015d8fa5c9b4699e76624ee70a23a254a

- [T-421] **numactl prefix の代理条件の置き換え** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。Pegasus entry は numactl=() で当該分岐が発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 7ed5364d6014c612d8c9bf2c45cf59d68baf8793dee9842a6d4ef9d26c4008ef

- [T-457] **exploration campaign の resume root drift** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本文自身が「発火 artifact が無い間は設計メモ (DW-G04)」と結論している。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 76186ca5e0bb61a485a26b0cf58fd9c185b456163813b4f8ada83fa294b3cf42

- [T-660] **末尾巻き戻し検査の検出力確認** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。chain が 1 record の間は空 chain 拒否に mask され観測できない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 6cde23c9936be6325596675ddadb7959e49c5e3002e69d5afb8f0c8dae0ec70b

- [T-862] **公表台帳の予約 writer を land lock 内へ** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。着手条件の R2 は [T-793] で保留終端となり発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 52770ee473e47a0117f009c33c2f25c3cccfabee5a5af3f24bb6a3385cc75d57

- [T-315] **陳腐化した停止理由メッセージの訂正** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 118ce27118b905af0e413d93dcf4336a53eaddbc973039c03ee4f148d3e5ead4

- [T-961] **strict extension 保証の直接テスト** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: b6968c8fd8e374539443b83656dd13555fb965efbbceccebfbc6da898a1bc0b0

- [T-286] **未参照の予約 policy key の削除** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 9d3e7b19ad7e54dffebea392275ba820198afc89222b8952d6c9279a88658f2a

- [T-436] **cap-lift 記述への実 D 番号の反映** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: b565feb044035590828b99899d79a8a43fc4a95c89bc20adfe69d80c0f58e56d

- [T-797] **設計正本 §11.2 の row 抽出が表形式を取りこぼす** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 154ae79c680f77e8006801bf130c2978200fdea5bfabacba617e6524f750330b

- [T-466] **auditor nits producer schema の閉形化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 8c183a03cac61e523818c69236fb4cc3e9c50664e9731f36dab5ccc5ae5d75bc

- [T-159] **重複解決が汚染した過去成果物の救済** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: f18d953098b93d61946ca76b2d3f8cf2fa5551481a8dd766eee7824267dddfc4

- [T-308] **百分率の固定桁 round の role 契約化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 5f16c2268b978fc16fb840c2744e9d2e5fce6c18f641ca0b878640854a8723b8

- [T-336] **候補 2 件の現行版での有効性確認** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 65d3eab30aba2e94a0eb8a6631d319b5dd4151fb6456b70287594d732ae1030a

- [T-569] **guided の no-build pseudo-WAL の attempt schema** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 106a9dce8a274e29a9c64d0067a7012c942c51ac808c383630e1ad4355112284

- [T-060] **WAL 記述から改竄耐性 / 証明可能を外す明文化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 23ad98450dc363e960223410cbf42b96ac8601f8f32f685e605ef7d4d1a62e5a

- [T-533] **holdout 凍結の known 直接読み** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-531] の世代移行統合に同梱すると裁定済みで、統合先が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 038b5a11c21ff7e6f2eb750da8ad5b768780b087d9f8d501b2e391ef30774a7d

- [T-534] **受理集合の権威の凍結 proof chain への帰属** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: d0cb3f2341408e5d8f2e2a9059ca713d5e28374cb80babe9af3988e3fc8966d0

- [T-544] **name<->mask 束縛の迂回** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-531] の受入条件として同項に反映済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 094c4e7c8d29e812642e141dd7a5f43f3b97058a7c6c15f45dc0599566291bc0

- [T-748] **W-2 投入と SWO oracle 停止点の特定** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。実作業の所有は [T-971] (原因と診断) と [T-1094] (FetchContent の閂) へ移り、本項は W-2 の歴史的証拠への参照になっている (敵対レビュー A の指摘を親が受け入れた)。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 4fbfa3ff82005de8ae9fc20b0aaf051705ae3bafc00f8c21dbd9bca159b0e4ba

- [T-833] **WAL と stdout への共通 execution nonce** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。[T-859] が同一内容を裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 5161fdab365ab3f3d7be18a90d2ce78b2048ad07d9403b117325327883d2da95

- [T-109] **クロスプロトコル対応の裁定パッケージ** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。protocol 移植は [T-755] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 9f6195269c89a45a0491b18d482cc89490552984119b70a7023900c2e905b288

- [T-181] **reasoning routing の限定 A/B (認証済み台帳 + erratum)** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 81d0935ed247d9fa9777ac0a98ea1cfaed5ffc0478c596cb021daa2769c8cac5

- [T-186] **resource envelope の残余 3 件** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 0235b894e4162d564799b239eef8561afbc2b5610735b36aeaefbe03a5822c9c

#### プロセス文書系

- [T-365] **fold 署名 2 条件を heuristic と明記して現状維持** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (b) で現状維持が確定し、意味検証は [T-347] の単独所有と決まっている。再訪条件 = なし ([T-347] が所有)。
  base: d783460c28939adec6ad459761945e817754b4698dd007254441cf7f3d1a34f7

- [T-413] **記録誤りの検出を入口へ書き足すか** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。択 (d) で書き足さないと確定し、検出は稼働 wave の前提実測と収集経路が担うと決着した。再訪条件 = なし。
  base: 82a4c92db27c40ea44411a570d85380d49875c1324e9f4c95df926c3a80eb79b

- [T-557] **過去 commit checkout での防壁の版** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状是認で裁定済み。外部の最新 hook を維持する設計は起こさないと決着した。再訪条件 = なし。
  base: 8d23a6926c7827bfa7c28d9ad54908513d6e10ecf0b6df8e67088a53650be955

- [T-680] **不在の証明の表現規約** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。「N 回連続緑。不在は主張しない」の正直形に固定すると裁定済み (規律 3 整合)。再訪条件 = なし。
  base: 89af599b4c217388d81b50a66295cf8f316cf3e59699d69d3140b03d591eb8b3

- [T-891] **fold commit への transaction ID 刻印** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状維持で終端と裁定済み (D320 の見送り側 — commit 級 provenance)。再訪条件 = なし。
  base: 0f912c1fe3eef36027d24f66166255b800de6ae14e785c38964d258370fa7d19

- [T-245] **codex/p3-autonomous-trial branch の残務** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起票時に本文が途中で切れており内容を復元できない。branch 自体は取り込み済みと本文が述べている。再訪条件 = 同 branch 由来の未回収成果が具体的に判明したとき。
  base: 709c643bf4217da50504e0f8ea54ea92c313d31ec0907cacbe0cfb8bcc534dcf

- [T-836] **受入数値の正本を insights + land 報告にする** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(c) で裁定され運用としては確立済み。docs への正本化は [T-791] と同じ予算制約下にある。再訪条件 = docs 予算に余白が出たとき ([T-959])。
  base: 0ca3139f96a52d7d0bf006e567986aabe852cd1359a18ffa529759ec0c885d1b

- [T-791] **DW-S07 へ正本化する規則の差し替え** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。内容は [T-836] (c) と同一で、収容は docs 予算に従属する。再訪条件 = docs 予算に余白が出たとき ([T-959])。
  base: 7546bee175c1b418693c3e455c6922d7e2d0ae43ffff3b3fa096147c96f5218e

- [T-1039] **docs/handoff 滞留による起動検査の恒常赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。952fd45d で滞留 handoff を撤去済みで、2026-08-15 の check_wave_startup.py は rc=0。構造的な再発防止は [T-1038] が所有。再訪条件 = なし ([T-1038] が所有)。
  base: 6160db6a007333e8796d265ea6841eb2543a35603309e0b38dd957f974710d20

- [T-1037] **land 済みで撤去不能な docs/handoff 残置** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。現行 main の docs/handoff は README のみ。checker 側の恒久修正は [T-1038] が裁定済みで所有。再訪条件 = なし ([T-1038] が所有)。
  base: 25b89bc5a98f2e32f86ff11f7465c7006420148d8eca13c08ea89d9e3255e8a9

- [T-234] **完了 wave の handoff 3 件の残置と削除責任者** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。現行 main の docs/handoff は README のみで残置ゼロ。削除契機の恒久化は [T-1038] が所有。再訪条件 = なし ([T-1038] が所有)。
  base: 4916ef8d79aae07c784c39ee5a0b0f0dc6c201b1e3ffcb5562e7d1179eda8194

- [T-598] **前向き収集の律速** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。収集の login 結線は作らないと [T-1029] (b) で裁定され、残る修正は [T-999] が所有する。再訪条件 = なし ([T-999] が所有)。
  base: 7e8dfff7ee0ef5f7337d89baffbbf8ee4f07ae89aa472a46d93a262c18a39fc9

- [T-348] **fold 適用後 git add 前の SIGKILL からの自動 rollback** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。fail-closed で止まり false green にはならない。手動回復で足りている。再訪条件 = 同型の実害 1 件。
  base: b653cbd8243915cc2185306dd988a6642186a45d76e9b77631364f91dca1ed96

- [T-353] **FOLDED receipt の canonicalized body digest 化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同じ本文を別 seq で再投入する攻撃者を前提とする面。再訪条件 = 同型の実害 1 件。
  base: c2d3c0194b1ebef0b1209fd28a68a567a40108d3112e15420acb225f42be5116

- [T-801] **rollback lifecycle の 3 細部欠陥** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。いずれも同一 UID 敵対者または稀な例外時の窓で、実害の観測がない。再訪条件 = 同型の実害 1 件。
  base: 0f5825b8408d67b4fd57476a77dcd16f85f9b9ea33bdde6fdd69c7e0db6d2e5e

- [T-800] **_rollback_fold の state 型検査を復元 try/except の後の独立 phase へ置く** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。rollback 途中失敗という稀な窓の堅牢化で、実害の観測がない ([T-801] と同面)。再訪条件 = 同型の実害 1 件。
  base: eb8e8980755d03ac9b31f27beaf44237287e93242e9c606ae91a6dc39ea5a674

- [T-1099] **受入 waiter が checker receipt を再検証しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。checker 側が壊れた場合の二重防壁で、倒れる向きは fail-closed。再訪条件 = 同型の実害 1 件。
  base: 04542625eb11d843a4ae41bca0036e2aeb18412be1453068a65cb95f9798613a

- [T-1108] **acceptance-scheduler-attestation 段の detail が絶対 path と repr を載せる** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID の受入 log を読める者にしか届かず、非漏洩規律の拡張は正常系の診断を狭める。再訪条件 = 同型の実害 1 件。
  base: 79bd34ee2d7a61d89265c9f98cf86f80dcbcf97ec59e7b41ed08751294f7fe00

- [T-261] **provenance scope / Codex-author epoch の per-lineage 判定** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: cfdc905d934923eb8da253621bc89c8974088cb1823096e8d9df5d4dd1af1ed4

- [T-262] **--message-file preflight への exact waiver 排他** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 3fe0de3661f2b018f8b3991fdf3e51ae062c09ac99f4fa94d1602f1e4d0c49af

- [T-263] **provenance dispatch の data row 束縛の fail-closed 化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: af80db15e787197a64da0e0c63bbd054205d40e278c844a83fc2ff41aa2aa9c2

- [T-366] **receipt schema への tested main cutoff の永続化・binding** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 1ea22c99aebd17794b59fe0711af613a57d08b715b16e51d6d7f67c029d145a8

- [T-621] **監査結果を消費しない層 (land が full-history を強制しない)** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 295c74aa04a533d1f732e2018d74282951935d9e2ecaa5078f0856ce3e0537ae

- [T-1008] **index 意味比較が index extensions を見ない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 94b3428622ac28b6309e3984dd2c8de93a8585311c949c83cbaa8e0f1ea96475

- [T-1106] **receipt 本体生成の例外がどの段か分からない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: dd38fb14730f55089afcf22b7d28044dbc59ada8ffd4a3841d888a0fbbb7ec6e

- [T-590] **競合なし auto-merge の実装面 path の扱い** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。恒久策 (merge 判定を path から内容へ寄せる) は [T-938] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 6fee8466daf72f73216de20ee028b7f80f87f7a88168e50edc9f06814f8b1c01

- [T-825] **制御 byte 混入の機械検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。NFC 検査の追加は [T-855] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 68dee66eb6f8ed275c6830149984b7d74aa267131a1bdf79936293a975538daa

#### 外部環境系

- [T-486] **probe leg の実施** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-503] の設計採用により deferred で確定済み。再訪条件 = 実機受入 (生死確認実験) を実施するとき。
  base: 144957eb2b53cd37c4b49529c417850e9693ae36c4de79fa97dc62a474bf59b6

- [T-538] **本番 α 取得手続きの静穏ノード事前実測** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。実測は行わず運用へ回すと裁定済み (計算ノード job は scheduler が占有を保証)。再訪条件 = 運用中に過剰拒否が観測されたとき。
  base: f00002fd96f55a354d9ee8076ca4efe0ac9b9a28ddb7986c77da5adcc8e9efcc

- [T-547] **dispatch の非許可 key を黙って落とす件** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起票者推奨どおり落とすと裁定され、専用 wave は立てず次の dispatch 面 wave へ同梱と決着した。再訪条件 = dispatch 面を触る wave。
  base: 8f926950c0765d83edfc0d3128a60b5a48b0bcddc3840f384a4abbfe9f7fc219

- [T-920] **計算ノードへの linux-tools 導入** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。閂ではなくなり、ユーザーが「今はやらない」と裁定済み (perf があれば使い無ければ無しで測る)。再訪条件 = perf counters を要する主張を立てるとき。
  base: 2dcd3e64c91ff11da78dcbedf7663a030eff3ca5c05122dcbe2fe93e3547215e

- [T-966] **admission registry への登録** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。見送りで確定済み (本走完走済みで再走の実需がなく、登録には 2 同期が付随する)。再訪条件 = 再走の実需が生じたとき。
  base: d478fa3302e92be4194dddc17801bcb817d35f7ae6686c4ed9fcfec99fff0d0a

- [T-985] **login headroom の判定占有量を回収不能量へ** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。実測で確認 — 本 wave の bounded local が「回収不能量=5415566904 bytes、判定占有量=5415566904 bytes」を出力しており D354 は実装済み。再訪条件 = 上限付近での過剰拒否・過剰許可が観測されたとき。
  base: b0857bae17db9e080109a45cf3078392c21f35d23bf021b83d9551bf7b29147b

- [T-600] **判定量から reclaim 可能な file cache を差し引くか** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。[T-985] (D354) が回収不能量への変更として裁定・実装済みで本項の問いは決着した。再訪条件 = なし。
  base: 8ff577eefe66d11903f298e1d35520425c1c6849b6746d32dc74930b65b698d7

- [T-268] **pegasus を本軸の runnable env にするか** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。Pegasus は既に主戦場で、env_contract registry へ登録済み ([T-296] が実測)。問い自体が事後的になった。再訪条件 = 別の機械を本軸へ据えるとき。
  base: fa6d45fbbf87c9634a03cb36913d136cbceab441ee982c4d264d5eea1e298a0c

- [T-296] **roadmap §5 未達 (1) 専用 env-tag** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。既に閉じている (pegasus は env_contract registry へ登録済み)。残る層 C の floor 取得は [T-088] が所有。再訪条件 = なし ([T-088] が所有)。
  base: 46140f0296e1eccc6b7b1fe2891dca22ada0b791a79e186d24f436ee3ba76b3d

- [T-278] **transport 断の同型経路 (env 継承の非対称)** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。provider 2 本の非対称は記録済みで、秘密境界を破った実測はない。再訪条件 = 同型の実害 1 件。
  base: 4eb4d74acd81c7413b4b7055f68a035690dc815fcf186237ecdd6bc66713a988

- [T-275] **dispatch 成果物 root の owner / mode / symlink 検査** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。脅威モデル自体が未定義で、同一 UID 前提では得られる保証が小さい。再訪条件 = 同型の実害 1 件。
  base: aafd9f0eed794634ef3a9cf4327c5f8949d2e6f381de036cfc1fc0f21a14c51e

- [T-267] **linux-baremetal の正の machine attestation** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。未知の第三の機械での実行は運用上起きない (Pegasus 専用運用)。再訪条件 = 同型の実害 1 件。
  base: c5e3976b64bbd9d57ce3d376b66089891d5016036d5197f62851bc5230463bd8

- [T-250] **_job_run が env allowlist を子側で強制しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。単発事故で局所修復が既定。値契約の設計は [T-1089] と同面で、そちらも同じ基準で見送る。再訪条件 = 同型の実害 1 件。
  base: 5f665f24d5bcc4b71696a27053a74fbe64444812f12529a26f891bd33d2ddb89

- [T-1089] **dispatch request environment の値契約と receipt 束縛** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現行 key は全て単調で、非単調な key を足す予定がない。再訪条件 = 同型の実害 1 件。
  base: d74ac5f4ddd84186ab8c5a85436df50031cd2c5bba9b32c857b9fe891f0a350f

- [T-404] **request ID discovery の部分一致** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同じ nonce 接頭辞を持つ旧 job を掴む実害の観測がない。再訪条件 = 同型の実害 1 件。
  base: 9243e10ff04bc4f43ec4d1f825bbb9d0cceacc1111625fc9c0c642d9458b701c

- [T-406] **receipt 永続化中に到着した signal の競合窓** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。閉じるには receipt 永続化の atomicity が要り、費用に対し得られる保証が小さい。再訪条件 = 同型の実害 1 件。
  base: f5db9ac65f8340bf0f0c1be7dcd013331969fd0d21788843b1a207eff07ff187

- [T-519] **collect_receipt.py の入力有界化** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。cap 上限入力での §7.0 実測が前提で、費用に対し得られる保証が小さい。再訪条件 = 同型の実害 1 件。
  base: d7fe82d067456aec9faaaf3f7f58601e4799d9f485f8e8759bf74ab6ef931d0a

- [T-602] **user systemd 経由で cap の外へ逃げられる** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。任意 argv launcher を作らない設計のため現実的射程が小さく、閉じるには実行 sandbox が要る。再訪条件 = 同型の実害 1 件。
  base: 7be3dcf0d607e324f3437dcc0710fdf27e19cebbcdd7c438caee3d5658b806bb

- [T-552] **未改名 .e を受理する終端実証第 3 経路の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 2259b64a99d3bae7eea5870351cb635eb8891d0fb4e17c4862c565b544471d34

- [T-573] **crash receipt への scheduler 側独立 anchor の束縛** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: b5454763ab16613401941bc9d0a4543ebc124cf5eb46c88f6769c62a7fa80225

- [T-601] **local 完了 / cap 到達 / 余裕不足 / dispatcher 失敗の 4 値の永続化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 89957387005211d40d943ade7b7124e8744b80ad6b87af5b5d89e5a759d36922

- [T-445] **hydrate の機械的強制** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。呼び忘れても悪化はせず、強制には凍結 submitter の書き換えが要る。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 4b42d018d66bef78f1fe98e9a94a64c6265ac40d1e11bca6b4b696a3aa4127d4

- [T-655] **runbook §7.0 実測表 parser の一般化** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本文自身が「それまでは着手しない」と再訪条件を定めている。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: e4f5ec3835b733205f126786e80c4510e4ee06f7551e86ea2b87a9bbd9e40d3f

- [T-670] **elapstim_req 増加による queue 待ちへの影響** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。既存 receipt の比較で測れるが、40 分化で待ちが伸びた実測がない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 409dd1febbb7999b264e1667588f787f4d20b3c39320ec0c45d6a0c855af245d

- [T-1035] **local 予算 peak record への metric / schema 版の付与** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 1aaf94944df87d33647254db9f3455a6a867f1e050ee06e8fe89dd874d623cf9

- [T-1078] **dispatch relay framing の wire 契約化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 5ddc5c1411755d6ca3519cf90b85db2e8f9cc1c780f195dd78393ee0aef2ae39

- [T-332] **site_policy の fail-open** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。分類失敗時の既定の裁定は [T-1036] が所有する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 7e320d096c6d42e0decb9cfe50858b835eac3047c09eb00de92522f8ee5542b0

- [T-196] **silo_ladder_rung1 / t152 の site gate 通し** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同一対象の site gate 欠落は [T-303] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 2d845317e4b987b44d58945fcd2eccfb3bd9e6201f103944d74a61f3e19ef908

- [T-810] **測定装置の第 1 slice と実測投入** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: c70a57978e878212c503a5c1321013f13b70df00d5eecb2d91d0ccc3c1c24fec

- [T-831] **走行前提 (N-job barrier ほか) の実装** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: 65b2a5e2882711878cff729f68c03cabb163c43f60516ba3a2ab586e132ff742

- [T-866] **§9.1 item 1 の残余と production 正例経路** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: 8bc938f8da96522aa15377700570569d89c285f70688d7ba4173df2edb212a48

- [T-867] **並走ガードと投入 admission の実効化** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: 3dba23a13826f9d1d10f27b6d591043bdbba26da6fbce151212674fb7ebdfd63

- [T-922] **caller 外 authority を要する残余** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: 90f3c43d5add5d81cff0bc99c43b0d23918721f83342669095339bf8a91eccb1

- [T-974] **staged package の依存 file manifest 化** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: e1dcbab6d6a52b11becb3ac4c3df18cbb4d13acb307300d227bcb458b5568199

- [T-975] **qsub 直前 bytes 一致と node 実読 bytes の乖離** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: d376ff5197148d5cf77c2876a2361ce140368dc4ae95fe3f2825f6cee6e5a804

- [T-832] **pegasus-node-variance-protocol の LIVING_DOCS 登録** — 理由: 2026-08-15 棚卸し (価値小 = 発火しない)。ノード間分散 protocol の投入経路は [T-923] で全面 deny のままで、policy は unratified、依存する判定はすべて deny される。ratification が無い限りどの実装も実効化しない。再訪条件 = [T-923] の投入規約が承認されたとき。
  base: a04eb2ba129965c29389985c0058cb25c80e3d8f3b7a857f1f175a7c3848d50a

#### テスト衛生

- [T-423] **非 UTF-8 probe file による受入全走の赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 の実測で python3 tools/ruleops.py inventory --repo . が rc=0。受入を止める赤は存在しない。再訪条件 = 同型の inventory 拒否が再発したとき。
  base: bdf2aec4b474bf547dc41db76076bbf5a757d436ce63e8c32e78440233652156

- [T-430] **ruleops inventory の rc=2** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同上の実測で rc=0。[T-423] と同一事象。再訪条件 = 同上。
  base: cd19c000acc1b8d21b18461d05f91b629b68425b00ea33adcbeb3b984053af02

- [T-299] **test_s8b_oracle_driver の 40 件が local main で赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 に当該 file を単独実走し **82 passed / 14 skipped / 赤 0** を実測した (敵対レビューが「440 件の緑受入は当該 nodeid の消失を示さない」と指摘したため、推論でなく直接測り直した)。再訪条件 = 同 file の系統的な gate 拒否が再発したとき。
  base: 527044c8252b4c949fc97533e7e210bb49308b596ed294b8169276dcbe3008c0

- [T-1003] **_assert_history_transition の n 親一般化と main の赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。2026-08-15 の実測で test_s8c_preregistration_invariant.py + test_t793_report.py が 17 passed。赤は解消済み。残る「3 親以上の merge を禁じるか」は防御的堅牢化の既定見送り側。再訪条件 = octopus merge 由来の赤が再発したとき。
  base: d6688ebe345212ba300be375312f404f409cc555b3e3b5440f3cdec37371dd8a

- [T-888] **test_t793_report の supersession 走査が D305 で赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同実測で緑。main を止める赤は解消済み。再訪条件 = 同 file の supersession 固定が再び破れたとき。
  base: 233b31c517b7d62a3a484ee0300e7e1c1ac69742a6987ec523b562350524847e

- [T-844] **launcher 終了検査の受入フレーク** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。エントリ 548 が production 欠陥 (/proc 全走査中の一過性読取失敗で residual=None) を特定して修正し、永続 unknown と一過性の双方を検査する試験を新設した。再訪条件 = 同 2 述語の余剰が再発したとき。
  base: dde6ff3014e0988f5be02ab9a9624bfddb26bbdeeda1898fa62690f94607bc9b

- [T-772] **launcher 終了観測フレークの帰属** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。帰属先の production 欠陥はエントリ 548 で修正済み。再訪条件 = 同上。
  base: 57d83d9f990f3930c47d93c7abe40e9b10433cf1d46974b95952062aa25c7c7c

- [T-663] **受入全走限定フレークの自己申告計装** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。計装は済み、残りは実負荷で artifact を 1 件得るだけの受動待ち。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: fefa6520ec925d41cae1e7e293b876d34a8541f19d76a25a72a849d4c165ca12

- [T-218] **中継まわりのテスト衛生 3 件** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 0c8a702924db577ff525cbedf42752adae8685378beb9a695e003e45ad388817

- [T-736] **local 実行モードで常に赤くなる exploration output root 系 5 件** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 6977a1231f6e70040c755a57c07d1c922ec5b8cbfe744f1b068e8ffcc61c1d6e

- [T-996] **保留の import 時拒否が session 印の残留で無効化される** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 05c143cfbcefb5981b0ac165f8a7d2ff2f377810226808ca1f74bbf9dc1c4af0

- [T-123] **daemon.py の _atomic_json (デッドコード) の削除** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 3cce44c45f0d3be1cc2a83d16062470a86b4cc637761d3d60aeae4c3203c7fc8

- [T-764] **発行 tool test の sys.path 復元漏れ** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 6db95806d6b4225f25b7111967565e935eff801db0832f3236abc18380b95f79

- [T-771] **依存物ガードが CalledProcessError / UnicodeError まで skip に落とす** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: c118d66390128d9cad1318a4cc5807ef5790a67cd59f78506c1454bf6789baad

- [T-509] **standalone entry point への import root 挿入の横断確認** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 04cd460bd78ac78ef9a92f9cc81b924bdbe51cceea5c55fe26b4ed0c5ffce280

- [T-1007] **benchmark_snapshots の worker 跨ぎ共有** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: aebc352b2b387515d9b7ba7a820577e65facdadd10af906fa3ec0aeda5cf7357

- [T-992] **real_repo_receipt_memo の flock 待ち 950 node 秒** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: f4db9c61f92e392001f48915961496533ba896828ab56667386a8a5b6e507441

- [T-993] **benchmark_snapshots の worker 跨ぎ重複構築 165 node 秒** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: e980ac03c37f64d208a020d0f9e5bccd59c4a400e8680882ccd61c796f82df0e

- [T-113] **source_resolver root-isolation 変異を殺す control** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: c88129bdd58057016a605aa3e54cf902200fd16042054c9ebb811d5998e03912

- [T-281] **テスト側の素の mkdtemp 60 箇所** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 0e577db6586891066b3c448710a9a806f161291fe5bd776c7383592264c01fe1

- [T-427] **test_check_receipt_rejects_impossible_truth_table の 16 並列時の赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
  base: 286315f1a8211e0c7abdfc90f8e68bfcb9401fef01f60130789cc71d6c09a408

- [T-431] **test_check_receipt_rechecks_all_manifest_header_fields の 1 回だけの赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
  base: 8e59b54909e6d1bdd81dcfdacc03decfbcf78a0d0f6d3e5b5585beb8625b255e

- [T-447] **test_agent_sandbox_binds_exclude_attempt_receipt_directory の setup error** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
  base: 21084979a79144902b31e984d24f1fb1da8dde7b17292a5b461c30acadbfaf8e

- [T-603] **check_docs の command 文書 guard positive control の 1 回だけの偽赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
  base: 9ee2e2db11d75e5670d1debe7928940fdd371d9e4f6d41a4121566f2f5568949

- [T-377] **変異本走 V9 の xhigh node の無関係な赤** — 理由: 2026-08-15 棚卸し (価値小 = 単発フレークの起票で以後の再発記録がない)。再訪条件 = 同一 node の再発 1 件 (2 例目で調査する既定に従う)。
  base: 862b32e165e53a4b65aad9ea5ccffeaa47ca7fe52692647be1ab87f5929b3647

- [T-118] **provider neutral tree の残留の再測定** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。残留の帰属は [T-280] (production 例外経路) が持つ。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 48c2b0d407f9e5960489a9e5714568d35b6958455e2acedb50ac0f959db51fb9

- [T-698] **test_exploration_external_root_keeps_wave_clean の両ノードでの赤** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。決定的な再現条件を特定した [T-1079] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 6262779845dc47a8a647703322b5bd897f44f7f71f81f781c5d529235a889508

- [T-731] **同 test の走行範囲依存の赤 (3 例目)** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-1079] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: ddc1a0bdc62c0f165b1a762f2c198113395362e42a5ad8acfccb184c276101e4

- [T-480] **real-repo テストが並列全走で落ちる構造** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。族一般化は [T-826] (M0 = 分割不変性と real-repo 排他閉包) が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: f8fd61b26ca1969f28725babf55c6e70742225a63ea1e997f60644b910c384e3

- [T-134] **xdist 並列度の再最適化** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。受入 wall の実測最適化は [T-989] 系が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 7b7ecd15625c299f839273ee03fba176281d9aa84c63f117cf3996d3e1428b8a

- [T-130] **_uses_real_build_v2 のビルド時間短縮** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-989] 系が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 08a64b6b3fd59bab84a04ba2e352690517e4d62d622374a76e5853d1c70291ab

#### Codex dev-wave 資源効率化 (P1、2026-07-29 監査)

- [T-503] **使い捨て専有 worktree の活性化** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。第一 slice は land 済みで、活性化は [T-610] が shadow 凍結の継続を裁定済み。再訪条件 = なし ([T-610] の再訪条件に従う)。
  base: 2e6ba32bfa63194885fcd92560841bfda8e8e0104121a986694dbc08e5fe2ded

- [T-572] **DW-G01 への driver 使い捨て既定の明文化** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。[T-577] の 207 bytes 優先列に入らなければ見送りと裁定され、実際に入らなかった。再訪条件 = docs 予算に余白が出たとき ([T-959])。
  base: f25268ce92d91b45b6ce5edbc91238af3e8fc063e441718e66009dcb040bae75

- [T-577] **回収 207 bytes の配分** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。上位のみ採録し残りは見送りで確定済み。再発防止は failures 台帳と inbox 控え義務が担うと決着した。再訪条件 = なし。
  base: 1dfbe8f9695cebc1408e1bc8ccb7db337c0742208af208e93da254440df3fd91

- [T-579] **L2 削除候補の棚卸しを delta 監査へ変える** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。3 度とも候補ゼロと実測され、以後の独立 2 wave も同じ結論に達して棚卸し経路は尽きた。代替は [T-959] の L2 空き枠。再訪条件 = L2 節の membership が大きく増えたとき。
  base: e677716356e89266e34f82378f7e04e04ae91db8ef68e377413d0b6c5fd64bc8

- [T-610] **隔離実装の activation package** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。shadow 凍結の継続で裁定済み。独立 wave は D205 基準で現時点では起こさないと決着した。再訪条件 = L-B 実機受入の成立、または隔離を実運用で要する実害 1 件。
  base: 303417a8c687c31c44271808060f760f7007da85c54c6a34085f4d4701179711

- [T-662] **model 実引数の権威行からの導出** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。land 済みで、残余は [T-665]/[T-759] と同一束として別途裁定済み。再訪条件 = なし。
  base: 40c0e7d0fa6aa0907ef5b49c31f7f0620f5c19675e935288e454bb879ff08f55

- [T-665] **effort 束縛の残余** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。(b) 延期で裁定済み。発火条件と内容は [T-759] の項が保持する。再訪条件 = [T-759] の発火条件が成立したとき。
  base: 57b4d1342d67c08311ea08ac4ecca7b6564559a3240869fdc7b8a5a2b312cf6f

- [T-909] **lease 残留の窓** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。現状維持 + 既知限界の明記で確定済み (窓はマイクロ秒で TTL 有界、実害実測 0 件)。再訪条件 = lease 残留の実測 1 件。
  base: 137d7e0eb7789dd6e71997b77db059b22873914caf0d1338f63751531c041a0d

- [T-505] **docs 予算の恒久 3 機構** — 理由: 2026-08-15 棚卸し (陳腐化 = 裁定が終端し残件ゼロ)。起草を担う [T-454] は既に非 active で、docs 予算方針の正本は [T-508] の (b) 主 (a) 従へ移った。再訪条件 = なし ([T-508] が所有)。
  base: 979074ff2df1b22a0597e8439ad8124051f1b50a87cf305b4a5a8e1e9ae71092

- [T-746] **wave worktree に残った untracked campaign dir** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。当該 wave worktree は既に存在せず、撤去対象そのものが消えた。再訪条件 = 同型の campaign dir 残留が再発したとき。
  base: ab449215af129567066d929cb8ddade97ab7879aaba548c83fcb10371c80dca4

- [T-335] **DW-O09 の pin 閉包列挙が凍結文書のソース sha256 pin を拾えない** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同型は failures 台帳に F301 として型で記録済みで、手順側は「編集面 path も検索する」として実務に定着した。再訪条件 = 同型の再発 1 件。
  base: 22da8dae214cb20fa8dccb5d5a189f0104a0b4503f9d762346c07bde3719070c

- [T-312] **新 gate 群への事前登録変異の dogfood** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。tools/mutation_harness.py は以後ほぼ全 wave の本走で使われており dogfood は実績で満たされた。併記された機械化余地は個別 ID が保持する。再訪条件 = harness 自身の検出力を疑う事象が出たとき。
  base: fcd6e542643a5eb970ed704382fac4c2cbecaf78a926649c23516be8c4c32a64

- [T-984] **docs/dev-wave L1.5 層の棚卸し wave** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。独立 2 wave が「削除可能な節ゼロ件」を実証し、[T-579] と同じ結論に達した。空きは [T-959] の L2 枠が持つ。再訪条件 = なし ([T-959] が所有)。
  base: 050c7bae24e0f825d23529e7cea7dfea7ab5245dc7d9b0c093eb8a9189087169

- [T-204] **未使用 L2 節を削って docs 予算を空ける** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。削除候補の洗い出しは 3 度とも候補ゼロ。空きは [T-959] が実測した L2 の 7,252 bytes が持つ。再訪条件 = なし ([T-959] が所有)。
  base: a61a8ae7e18c1242072ac850bd08f09fd94bdbc8e5202529cfc3dbcea9b4e4ea

- [T-177] **未使用 L2 節削除による DW-O02 統合** — 理由: 2026-08-15 棚卸し (陳腐化 = 実測で解消)。同上 — 削除経路は尽きており、収容先は [T-959] の L2 枠設計が持つ。再訪条件 = なし ([T-959] が所有)。
  base: 51b103eb462c17f1e4f9a021f4d5ae08fc95f1b4c96fc1fb19f40aac4fffca32

- [T-849] **fan-out merge index の偽造耐性** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 Unix user 前提で、プロトタイプ基準で既に見送り済みの面。再訪条件 = 同型の実害 1 件。
  base: 4e75e01e3c8909bca31ebdad974db7205c1ad573ef382bfca1f19b47b0177ae9

- [T-373] **requested_reasoning と validity の分離記録** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 4bc7e9515aca25bd2a85d9a2c63328c7d13bf2d0e2342ad40ec603745065f713

- [T-633] **待ち手 3 条の遵守を後から確認できる field** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: a9783fe0f95f6995d26d115736e9ff7c6724e509ae72bd85e5f3b8bff7055071

- [T-1083] **evidence_grace_s の receipt v4 での封印** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 86f1c6fe08e839cf7806fe9e9dc4aa25921e36276ee3f209d81a9f1b05dbdb0f

- [T-174] **渡した prompt bytes の保存による事後監査** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: fa34b7acc309f2027da2cc43b565d2bcba339ea0c22b8b40f2f9e4abe7cc6f93

- [T-175] **射影入力の人可読記録** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: cb761101334c1f8c287f023ec1b71e02919ce83933aac462464efec26a02a4f0

- [T-345] **敵対レンズ prompt の書き分け (DW-S03)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: c32674829e5d7765ce22e59b0eba4e949232e01ba3246bb211972343640182ae

- [T-346] **完了済みタスクを引数に受けた場合の作法 (DW-S01)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 216975f94dfc3c2c1c1af7bba9efe39a61a5241eeddd8fbbabf51db0c10a4f92

- [T-341] **consumer 不在の粒度規律 (DW-S01)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 213e7cf08e6b1e87e0d353f74e2a34eaa55cf664432fa9f14c2ff6bc5f976bbd

- [T-328] **従属 4 件の収容先の確定** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 7253ef7175ab61b29455c5927222eb0348b6e3116a4cb709cc08ad63ab02dccd

- [T-279] **テストを実走できない子に緑を主張させない** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 3f379b6790d3fb526be7c5f0f2aaffe8b1325d3b9862de9c77dc0df7bf09b5c2

- [T-264] **実装子 prompt への「テスト実走は親」の明記** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: f4cca66460ef913057d321a8b0ce3029669c4d06046d140dd2718fd2e4ead05f

- [T-219] **dev-wave 改善候補 4 件の枠づくり** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: fe4a3b3643b1afbb6cae28eb12bfd2f7de7bcbaebb1b0becc0356f6fd8780e5f

- [T-214] **分割 commit の gate 通過確認義務** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 2131a7b75f4eabad3c304276d1c99525a6754578066c2ff929e38ed96dce9d1a

- [T-224] **DW-S06-A への親の実測主張の義務ほか 3 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 16408e9665de691bb20fd30db975ef2cae80943b7e2d9c65a68438bba93991dc

- [T-208] **cleanup-branches.md への F26 / F63 の運用則** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 5b5b81f5087f1e031934750fd6ac08844bc7cff2b7ce7e8993535defa7e23aa0

- [T-160] **DW-CTX への背景 job handoff 置き場ポインタ** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 5e0d466a5d65546964f56c420cdd833bf089857783de4979422c586ecc983fbd

- [T-199] **dev-wave 改善候補 3 件 (親の実装面境界ほか)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 53bd26c471609c1648a35c334fd0425a0c2f5b48d00280b9040adf500d8506ab

- [T-009] **実装子が負う規律の所在の明文化** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: bdf31133d983060df481fe98c23578be754485fa1b3f745e9c1c384211bdc5ba

- [T-359] **運用の穴 3 件の外出し** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: cb32e1f13096412179f205d7387fa289ed2d6c887b5074e338cd7f0291b9b8e0

- [T-369] **条件読み層への 2 件の統合** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 5eac7cdaa1c23699cf566abe73208cb75c2c25a2defb2e8c206d86b45b1404c6

- [T-386] **条件読み層への 2 件の統合 (同型)** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 8b1def3fe764204df37534b6315988f8edff37185c4d5dcaef689807e044c08f

- [T-375] **DW-M01 への受理集合縮小変異の literal 機械検索** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: d0610c3a6c92b2efb9944b4dc9561d110af60af427f09a542aa9a973aa6ff6b5

- [T-376] **DW-S01 への「(Pn) には最も安い反証実測を併記」** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: a7d19a0092bb25e38f1e1b1178c810dba64491ce6ff8c90b7ce63ba356a127c8

- [T-395] **DW-O18 への計算ノード pytest の正規経路** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: ac8fe7d12edcfe3226f1a461ea52922e2dd4137494d8dfd852f52910dfd0b6a0

- [T-412] **剪定の発火実績観点での再開** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 5860c245f2c31dd7dd071f12107e81b2052c5836ee766dd2f38b34d5585a8608

- [T-432] **予算残に阻まれた是正 7 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: e05755d58c11a2adf863926d2b24f5629465aea4375f489e04a7e22459a144a1

- [T-521] **DW-S06-B への F112 / F124 恒久対応** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 5558fb309f35d2962dfbc6122f26367e43b41c7fa98cf48b6dc502ab6eda4493

- [T-594] **DW-O01 系の記載を実挙動へ合わせる** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 6b52471c23933cac36744c4e87b184168cf6a088f81f320f539a9e19a121f36f

- [T-631] **DW-M01 の単一理由性の読み違え対策** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 32d01d9650b462280371f32c96854110e18303dd317cbb99342deb52943c48e4

- [T-636] **DW-M08 の両走が定義できない場合の代替証拠** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: e16af1f60bae695d95d673d28d1cbddfd11f12b62254be9a3d83af37b83c185c

- [T-652] **受信側規則と release 義務の JIT 正本節への移設** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: c6b52baa4f18741001a5ba83c7c672e83093e287cfa8133992f4df7e9556f79b

- [T-657] **stage0 残余 2 件の機械検査への移管** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 1cb1f143d1b879dee82dd8b8d44a96190d0581215711fadcfb46493f85166abe

- [T-690] **DW-S05-C / DW-S01 への追記 2 行** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 09879b0e3787f38e3250e29cee80d037d6e1487b397c3d4c6c498b8ff693840d

- [T-753] **DW-M08 への過小予測 MISMATCH の扱い** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: ce36de0f25f7a17236348401999627025a62378821901ea07d0eb61be0c3448f

- [T-779] **段 5 実装子投入直前の local main 確認** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: c2a974b7944b9c5f95a28b3b9a5333b46f690b011cf97788180c7de984f1db71

- [T-780] **裁定文の数値は手段であって義務ではない** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: f7e0e82a5c092796c273dfb873764265f223b3092ba2740decfbbbaf558f730b

- [T-806] **DW-O01 / DW-O02 への手順欠落 3 件** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: bf61b9bbcb3ee335599d6d5f4e67b897b13a0bf649fc5077b0d4fce7a61fa95b

- [T-811] **DW-O01 への「lane は段 3 だけ」** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 52765c512711f3fc06d67781b14aea49c04241be50258ea42e4ada528f4a517d

- [T-814] **DW-G05 への scope 分割時の受理集合の問い** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: d4ae9145e5ae723972f142e29febf65744cb7955bf7c454fdf6af46b7853873d

- [T-854] **機械 gate 不在時の代替証拠の明文化** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: f9b11724af38af6df3943b6c8fc607310a18041c3e755c0b766848e70324cf12

- [T-918] **DW-M03 への実行ごとに変わる生成物の除外** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 103788f8c5eb79ba67e7135f82a7c19251f5415b3e161be5a8712dfa9c8a9b35

- [T-1060] **DW-** への [T-908] land 契約の収容** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: a3486209f6bcfd565c3d2a603e6dba302e13b893fa1c3ec255d61313e5898499

- [T-1100] **受入試行の一次資料の所在 2 行** — 理由: 2026-08-15 棚卸し (価値小 = docs 予算で機械的に発火しない)。docs/dev-wave/** の削除経路は 3 度の棚卸しと独立 2 wave が候補ゼロを実証しており、予算上限の引き上げは既裁定で不可。再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
  base: 01a0529aba3ef196f7e0482cd1368b0ac2e6256f9c89dcc516a270a1166561d6

- [T-394] **外部 supervisor の DW-CTX 読了の結線** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。supervisor は現在 fake-only で runtime blocked。無人継続を実運用に入れるまで発火しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: d6f2a4e20ecc7b2ce3f326c900b4f61a75c3594409382d6781903477569d2293

- [T-702] **supervisor の DW-CTX 実読取の結線** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-394] と同一内容の重複起票。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: f0de110ff50961c331a18e3cfbc998ec626d65c9422bde34c96b75d41d256b98

- [T-759] **段 7 集合等価 gate と期待 job 台帳の freeze** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。本項自身が (b) 延期で裁定済みで、発火条件の canonical stage matrix は現時点で発行されていない (matrix が発行されれば見送り台帳から拾い直す)。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 25ea272ebdb9be2fdc1fc4462700955bd9fcd7540036ab0e39a975a5d6015143

- [T-1000] **audit_dangling_commits の実行時間と rc=124 の手順** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同監査は login で 3300 秒でも完走せず、branch 掃除自体がユーザー手番で稀。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 13da40cc9bd53bda78ba1a0e189e814fe9f7da006240be8089250c3f9c7a324b

- [T-494] **到達不能 commit 検出の Codex 再著述と land** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。監査本体が実用時間で完走せず ([T-1000])、branch 削除はユーザー手番で稀。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: fdf8d2787354fdfb1b99851c7b81fa5bc5da115cc7ed2485787caeb60656a2c0

- [T-589] **到達不能 commit 検出の再著述** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。[T-494] と同一内容の重複起票。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: aacbb998900ee84066d8ddeaee0dd13ecb12fc1eea0ea737a8afb7fd960000c4

- [T-516] **audit_dangling_commits への第 2 警告カテゴリ** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同上 — 監査本体が実用時間で完走しない。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 769953a7aec3f30595a2de451ed18f5c8dc68094862be29a5f9a79658a842f47

- [T-593] **audit_dangling_commits の 3 事項** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。同上。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: 11248247363a503618eace3b590ecbc9ddec07af5d391cfa35ac55cb3866078d

- [T-498] **campaign 固定 prompt prefix の byte-identical cache** — 理由: 2026-08-15 棚卸し (価値小 = 発火条件が成立していない、DW-G04)。LLM 実行はサブスク経路で従量課金されないため、得られるのは待ち時間だけ。再訪条件 = 発火条件を満たす artifact path または計測 ID を書けるようになったとき。
  base: a8eaac2478cc0596b6e1ec59197e7dfd353f5b6247066d94c385bb51b34cf679

- [T-216] **_bounded_log の省略注記が literal 2 文字** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 7a0d2861dd996ff42c8f4b4b296742929f953329603aa4d873b53044be4e947b

- [T-217] **中継中シグナルの複合副作用のテスト** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 6b4f47120399be0fb24cdfa217ee2b8c06d1341d5739941855e17f2ced60cfae

- [T-215] **試行台帳の collected_node_digest が空 (sidecar 還送)** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: b5e09db0211608aedf7723d240beaab43288c22f335f534b76e44e0a76dd1f22

- [T-166] **隔離 checkout への modules cache 複製と rc 13/14 の粒度** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 46f8be0989d12a809a7f8e1def7dc52f414636233aeb54ffdcd1163e91245196

- [T-712] **相反決定と冒頭 grammar 不良の failure reason の区別** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: feb3e7759e6cc6ea439da533de3789bc0d1438bc1e1cd48d5e8d7a395b8ed915

- [T-982] **3 scan の containment 走査の共有** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: de4e2d515c4219c67e596249f3f6e795e2f3af0b9566e4b05af16d22439352e0

- [T-931] **変異台帳の measured_seconds の記入** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 2b28e9815cabb3d1f362b2b225f4e6de0b72d5a1da65869218004876d92478ec

- [T-651] **lease 効果の 2 wave 実運用計測** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: c065d1e9a91befd963a19520a543817d86a97aab80edde8e8baeebaf180611a3

- [T-458] **変異 category への diagnostic sensitivity pin 別枠** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: bcdda0b44a6d2c9523f90d1787ac08f0ec789136fcef23f461cc32d612a5c1c2

- [T-626] **-rf 検査が後勝ちの -rs を防がない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 6d914047542cf344ba74ac31dc5695bb975c21e41183341617e5a86586c097c8

- [T-819] **enforcement source closure 変異の runner 作法** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: a1f670a244faad01eab1a1002414fc0009b31b54d69f7eac555135b3509614fd

- [T-761] **U+2028 / U+2029 拒否分岐の要否** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: d6169c3cca306682db6c3a2b23ab3c9362dab6362af82839f474d507d2fa371f

- [T-852] **legacy 単発経路が reservation を取らない** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 372df44ca39981dff41c11173304c3c0c73f3b9ce33f42ffaa65e797e8139e77

- [T-1015] **新設 detector の edge を 1 本ずつ撃つ変異 matrix** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: c28de5ba334193e9c1f75aa599cf2adb8a9befb88e043f2f9c3e29f7f9a2f0c9

- [T-943] **本走に載せられなかった変異 15 点の再照準** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 881d7da60dc1970e85a18cf5c6a5dc628197aa0accf4ef75b9cdb793b17c9cdb

- [T-954] **未走の変異 6 件と正例 2 件の消化** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 6430c5fac6d7afaa4c7c314fe6ce8e5bd6d685fcb0f20be0e1b77acff1d44673

- [T-924] **M6 (terminal_reduced 誤判定) の再照準** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 7cbadae818b9c42248f619c3f1ddc21c2ecd99670155445b673ab8b78b9b879b

- [T-926] **M7 (retry 表) の単一理由化か冗長確定か** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 9cbe8a4c220fbc63ee19a45f3c5fb4f9e276d4a7df6b3fa4eeba03a0481873b7

- [T-385] **M02 / M08 の帰属不成立と M11 の未説明 2 node** — 理由: 2026-08-15 棚卸し (価値小 = 診断・体裁のみで受理集合も成果物の値も変えない)。再訪条件 = 同一ファイルを触る wave への相乗り、または実害 1 件。
  base: 9068c638909a0ef560a366c2150611afcf32a2caaa7b960d02c5d87f9bfa1605

- [T-417] **real-repo 直列化 node の期待表現 (F95)** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。node ID 正規化の設計は [T-876] が所有する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 658c04cd70cf288ffb188377a68940b7ba5b67468333d5a2c5ad8c1a8d207161

- [T-512] **loadgroup marker 付き node の事前登録** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同上 — [T-876] と同一の正規化問題。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 345a0b21ed1e92871a8c0dec7f3ef445716ef96bdf36e6a05fb4679f42a95b2d

- [T-719] **expected_nodes 完全一致による MISMATCH の量産** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。部分集合一致の判定枠は [T-709] が裁定し [T-912] が実装を持つ。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: bb300f9a29d71245854f5bf3ef6ec2151643ca090c284bb1754648e1c3a3e1b0

- [T-877] **--artifact-root の親 dir 未作成による rc=2** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。自動作成への移管は [T-845] が裁定済みで保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 8f5eca411b488f10ab1d521cef6f19cc02d47a53ca65722ba0b67d0b2f92f1e2

- [T-451] **run_tests の queue 待ち timeout の指定経路** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同 file の timeout flag 通し口は [T-870] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: b1adb4df3a97e3aea1db9fadf3c19518062ba3ba078fb211cfaa09e0da3fa61c

- [T-1054] **帰属 checker の dispatch 2n 回** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。設計案と裁定待ちは [T-1090] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 2bbc209491311e1bc56d4c3aa394831c59fbe1a201f0306ef5a7c650aaaa7600

- [T-504] **_assert_clean_tracked の ignored / skip-worktree 盲点** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同一の盲点を [T-581] が実装可能な形で保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 84ca2574b4f30271ddd47456b81e34226354dcdd899d13a13f7cb8409fa61443

- [T-634] **条件 dispatch 表の文言の機械検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。同面は [T-391] が P1 で保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: d2e6101f2297fb75d66db133c58fc929eb49f24280814ffc0f328fb119855719

- [T-927] **待ち手の偽の完了通知** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。通算 7 例を持つ [T-1056] が保持する。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: bf09f7d794083f7b19b85f4f8832548cc90b3d836425736a109282ee9b35a2b8

- [T-709] **部分集合一致の判定枠の新設** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。未実装分は [T-912] へ分離済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 249bfe8a9d352c21dcc62899fef4f405d69e3e7b9b0153b2fb6be744deae356f

- [T-371] **model x reasoning 非対応組の事前検査** — 理由: 2026-08-15 棚卸し (陳腐化 = 所有が別 ID へ移り本項は参照のみ)。許可リスト機構が所有し、同機構は実装済み。再訪条件 = 所有 ID が終端し残余が宙に浮いたとき。
  base: 75fb03dc1d5257d4c382911b849de4a880a0df21cfdece96d7bf1a9034b21b1a

- [T-622] **codex_reasoning_ab の case family 一般化と protocol 凍結** — 理由: 2026-08-15 棚卸し (価値小 = 研究の本筋から外れる)。本プロジェクトの主張は workload 特化 CC の合成であり、LLM の model routing の優劣は主張に要らない。LLM 実行はサブスク経路で従量課金もされない。再訪条件 = routing 選択が結論を左右する主張を立てるとき。
  base: 7d0849852d2f3d63c3b9b69405532890443f0dea32373180936529818fa7b419

- [T-710] **codex_reasoning_ab の決定 grammar の限界 3 面** — 理由: 2026-08-15 棚卸し (価値小 = 研究の本筋から外れる)。本プロジェクトの主張は workload 特化 CC の合成であり、LLM の model routing の優劣は主張に要らない。LLM 実行はサブスク経路で従量課金もされない。再訪条件 = routing 選択が結論を左右する主張を立てるとき。
  base: e050993435dafa90d53470705495b84c3e9f14716184b58178c3fe319f716526

- [T-059] **survey #7 差分 mutation 標準化 (X5 派生)** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 0edc20d5b523472990fa2da5cac5a37a88391221dfb5d964905e66d7d675c430

- [T-183] **F43 / F45 型の早期停止と回復** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 72a3732e19231ef094307a36dd084b089be4041072faa9143cfe145ba5513765

- [T-184] **証拠に基づく既定上限 (reasoning 面は採用済み、resource / retry は残)** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 377ed41302ca0e9421d44b92b39283932e394ad69736825486d8586cde045898

- [T-189] **妥当な model routing 比較実験の設計** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 0a7903d128351c3133843a2e38c45fca85c00be6173d552d398dc4bfc9ea290f

#### RuleOps hardening (P3、T-143 残余)

- [T-1051] **_git が PATH 上の git を起動する** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。絶対 path 固定は運用を狭め、PATH を差し替えられる敵対者を前提とする。再訪条件 = 同型の実害 1 件。
  base: 59648c41620579d22595f2b9c8bc5a35b06d7831213f46ea8bd335bbfb2cce20

- [T-1052] **_git の timeout と stdout 上限** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。受入台帳が欠測または infra red になる診断面で、受理集合は緩まない。再訪条件 = 同型の実害 1 件。
  base: b0aff316fe1a8f3f30426ada135c55fc4740f50a55763a5e871d83b57a2cded2

- [T-752] **info/grafts による偽 topology** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。同一 UID 敵対者前提。DW-G02 に従い 1 cycle 後へ送られたまま。再訪条件 = 同型の実害 1 件。
  base: 745d49313b6df6c209e282b322e27f6f9245ce8860b5e8429f64a223ca6a5a46

- [T-728] **_default_controls が git-timeout を握り潰す** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。既存挙動で、握り潰しが誤った受理を生んだ観測がない。再訪条件 = 同型の実害 1 件。
  base: 4800e8b9748b608528258968b591bd0b3d4a2c3568559811c6e8300bcec9e001

- [T-729] **cat-file --batch の返却 bytes を予算に入れていない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現状 6,494 要求 / 95 MiB の実測で収まっており上限に遠い。再訪条件 = 同型の実害 1 件。
  base: 0516981751c3c24e4622bc42508408f34958ae928d0f8899560e49f34bbc17ca

- [T-630] **_build_ancestry の ARG_MAX 限界** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。現行 1,702 commit に対し約 49,000 commit の余裕がある既存 scale 限界。再訪条件 = 同型の実害 1 件。
  base: b3fcc1b4aa69e8fb04a33a17c20cabdd14d18947c4b71a0bb94aeee403ba19ae

- [T-727] **receipt range log の走行全体 deadline** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。本番 ledger は候補 0 件で発火せず、DW-G02 に従い送られたまま。再訪条件 = 同型の実害 1 件。
  base: 3fb17eba8e500aee7cb21fe6b260157f4ecd468a12b1dedb4c6c90f1a5171a72

- [T-439] **許可 rc の Git stderr を strict decode しない** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。非ゼロ rc の分岐でしか検査せず、任意 bytes が素通りする経路の実害観測がない。再訪条件 = 同型の実害 1 件。
  base: c3c6fee10853d03d2d1d4a14e7284aac3271f19e9b47dba63715a3d3e89492cd

- [T-440] **validate_candidate_ledger の decode 非対称** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。inspect が拒否する target を check が受理しうるが、実例の観測がない。再訪条件 = 同型の実害 1 件。
  base: 028977bb8e31dbad5cc0b8fbebc2fff5b29a96afca235b4146208ca85122dd72

- [T-994] **既知違反台帳の exact type 固定** — 理由: 2026-08-15 棚卸し (価値小 = 防御的堅牢化)。2026-08-12 ユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化は既定で見送り) に従う。str 派生型で SHA をすり替える同一 UID 敵対者前提。段 4 でも wave 前から存在する穴として scope 外裁定済み。再訪条件 = 同型の実害 1 件。
  base: 09dfe2ff6dce633dcfb84ea5b70721ff3a65bb30011fb5cc9970b5ecce64e752

- [T-629] **_scope_policy_commit の -S "scope=" の一意化** — 理由: 2026-08-15 棚卸し (価値小 = bytes 級 provenance)。2026-08-12 ユーザー方針 (論文主張に要るのは粗い provenance のみ、bytes 級の pin・署名・束縛機構の新設は既定で見送り) に従う。再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: 0e75a20f63be42e73524c71a43ff59822c042cdb680b6dc7b201519e19eeabb7

- [T-185] **receipt range 出力量の明示上限** — 理由: 2026-08-15 棚卸し (陳腐化 = 二重在籍の解消)。本項は見送り台帳に同名の項を既に持ち、active 側は重複である ([T-896] の実測で二重在籍はこの 8 件と確定)。**残作業の有無にかかわらず、記述は台帳側が保持する**。再訪条件 = 台帳側の項を昇格させるとき。
  base: 96635f9e183be880fc07030bfdd102573925350fc952fa58c7ed487a90e55ae7

