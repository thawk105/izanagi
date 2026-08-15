## 2026-08-15 (555) — 次の一手 657 件を全件棚卸しし、陳腐化・低価値 305 件を落として高価値 58 件へ補記する (docs のみ、branch worktree-dev-wave-backlog-triage)

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
  **二重在籍は 8 件** ([T-896] が未測定としていた数値を確定)。**さらに land 1 回目の rc=26 で、
  この 8 件は active から落とせないことが判明した** — 見送り台帳は同一 ID の重複を機械拒否し、
  active から落とす手段は `完了` か `見送り` しかないため、残作業のある二重在籍項は
  現行機構ではどちらでも落とせない。8 件は無変更で carry し、事実を [T-896] へ記録した。
  **あわせて `spool_fold.py --dry-run` の射程も実測で分かった** — dry-run は重複 ID を含む同じ
  fragment に対して rc=0 を返し、実 fold の「生成後 canonical 検証」で初めて rc=26 になった。
  **dry-run の緑は land の緑を含意しない**(受入全走 1 本を無駄にした)。(vii) `output/insights` は 292 subdirectory に
  対し直近の平置き新規 1 件のみで [T-258] は運用として確立済み。(viii) 参照先として名指しされていた
  16 ID (T-276 / T-277 / T-481 / T-487 / T-454 / T-564 / T-674 / T-664 / T-207 / T-812 / T-287 /
  T-313 / T-908 / T-595 / T-472 / T-474) は**すべて既に非 active** で、「◯◯ が閉じるまで着手しない」
  型の依存が事実上解けていた。
- **結果: 664 → 359 (完了 6 / 見送り 299 / 補記して継続 58 / 無変更で継続 301)。**
  見送り 299 件の内訳は裁定終端 54・診断のみ 45・防御的堅牢化 44・docs 予算 38・
  粗い provenance 33・所有移管 27・実測で解消 20・発火条件不成立 19・ノード間分散 protocol
  (unratified) 8・単発フレーク 5・LLM routing 実験 1。
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
- **受入 1 走目 (08:51 JST) が [T-1107] のフレークで赤になり、非帰属 checker も解除できなかった。**
  落ちたのは `test_dev_wave_wait.py::test_public_main_real_signal_releases_lease` で、
  checker の単独再走も `stage=acceptance-scheduler-attestation` の `marker-count` で rc=70 になり
  `status=attributable-red` と判定され receipt が出なかった。**親が同じ node を通常の焦点走で回すと
  1 passed / 2.16 秒で緑**であり (本 wave は docs のみの差分で当該 file に到達しない)、
  `DW-O18` に従い帰属させない。**このフレークは「赤になる」だけでなく非帰属経路でも解除できない**
  という新事実を [T-1107] へ足した。

- [T-393] 検証 receipt の LandRequest への束縛は実装済み。2026-08-15 の実測で tools/dev_wave_land.py が --acceptance-receipt を required=True で要求しており、検査を省いた tip の land は機械拒否される。

- [T-798] fold transaction の phase 化・state 削除の postcondition 後移動・finalize の land 専用化を 2026-08-11 の実装 wave が実装済み。残る相は [T-889] / [T-800] / [T-801] へ切り出し済み。

- [T-799] transaction state への trusted cutoff・audited digest・plan 入力 closure の束縛を 2026-08-11 の実装 wave が実装済み。

- [T-820] _load_rotate_limit の例外囲いを BaseException へ広げる実装を 2026-08-11 の実装 wave が完了済み。

- [T-821] FOLDED receipt への base / tested tip / wave ref の追加を 2026-08-11 の実装 wave が完了済み。既知限界は本文に記録済み。

- [T-917] 凍結チェーン検証の保留執行は t816-step4-impl wave が実施済みと着手前実測で確定し、重複実装もしていない。

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-139] (554)
- [T-337] (554)
- [T-338] (554)
- [T-339] (554)
- [T-213] (554)
- [T-318] (554)
- [T-309] (554)
- [T-307] (554)
- [T-329] (554)
- [T-244] (554)
- [T-327] (554)
- [T-295] (554)
- [T-324] **P1・裁定済み → 待ち解除**: [T-244] の裁定が完了したため第 1 段が済んだ。
  順序は変わらず「複数世代・還流・標本設計の事前登録 → 実走」。budget=1 の結果を
  workload 特化合成の証拠に数えない点も従前どおり
  **(2026-08-15 棚卸し) 今も高価値**: 8c 本走 (複数世代・還流・標本設計の事前登録 → 実走) の入口であり、ユーザーが目標の柱と位置づける無人ループの本体にあたる。
- [T-319] (554)
- [T-320] (554)
- [T-305] (554)
- [T-304] (554)
- [T-311] (554)
- [T-298] (554)
- [T-300] (554)
- [T-301] (554)
- [T-303] (554)
- [T-294] (554)
- [T-248] (554)
- [T-184] (554)
- [T-292] (554)
- [T-241] (554)
- [T-280] (554)
- [T-270] (554)
- [T-274] (554)
- [T-265] (554)
- [T-266] (554)
- [T-269] (554)
- [T-222] (554)
- [T-144] (554)
- [T-257] (554)
- [T-255] (554)
- [T-254] (554)
- [T-258] (554)
- [T-231] (554)
- [T-129] (554)
- [T-251] (554)
- [T-235] (554)
- [T-238] **P3・新規 (本エントリ)**: driver 族 (`p3_s4_loop.py` / `p3_s4_loop_trigger_gating.py` /
  同 sort・trigger 版) の `ENV_TAG`/`CLK`/`NUMA` ハードコードを `env_contract` registry 由来へ寄せる。
  Pegasus entry は `numactl=()` / `clocks_per_us=2100` なので、現状この族は Pegasus を選べない
  **(2026-08-15 棚卸し) 今も高価値**: driver 族が ENV_TAG / CLK / NUMA をハードコードしているため、合成ループの本体である p3_s4_loop 族が主戦場の Pegasus を選べない。
- [T-239] (554)
- [T-232] (554)
- [T-233] (554)
- [T-212] (554)
- [T-211] (554)
- [T-201] (554)
- [T-202] (554)
- [T-203] (554)
- [T-189] (554)
- [T-190] **P2・新規 ((70)、F57)**: launcher normal fakeの32-worker負荷フレークを
  失敗artifact保存つきで原因分離し、production gateを緩めずfixtureをhardenする
  **(2026-08-15 棚卸し) 今も高価値 (親の判定を敵対レビュー 2 本が独立に覆した)**: 親は「エントリ 548 の production 修正で解消」と判定したが、**548 自身が本項を持ち越しており、F57 も「原因確定ではない・原因分離 task は閉じない」と明記**している。548 が直したのは終了観測と signal mask の別欠陥である。受入全走と land を現に阻害する要因として残す。**見送り台帳にも同名項があるため、正本の一本化は [T-896] で扱う。**
- [T-181] (554)
- [T-183] (554)
- [T-186] (554)
- [T-185] (554)
- [T-059] (554)
- [T-097] (554)
- [T-100] (554)
- [T-133] (554)
- [T-088] (554)
- [T-096] (554)
- [T-011] (554)
- [T-163] (554)
- [T-167] (554)
- [T-168] (554)
- [T-169] (554)
- [T-223] (554)
- [T-306] (554)
- [T-330] (554)
- [T-331] (554)
- [T-333] (554)
- [T-334] **P3・新規 (本エントリ)**: 依存 bytes の content hash 束縛。D125 決定 (3) は dependency prefix を path 要素の配列として identity に束縛するが、**依存ライブラリの bytes 自体は hash していない**。trace/perf build の間に prefix 内容が差し替わると「trace だけが差分」と記録される
  **(2026-08-15 棚卸し) 今も高価値 (規律 1。親の分類を敵対レビューが覆した)**: build identity が dependency prefix の path だけを束縛し内容を束縛しないため、trace build と perf build の間で依存物が入れ替わると**正しさを検証したプログラムと性能を測ったプログラムが別物になる**。観測者効果の分離 (規律 1) が成立しなくなる。
- [T-347] (554)
- [T-349] (554)
- [T-350] (554)
- [T-351] **P2・新規 (本エントリ)**: `/rulings` の収集経路に、現 branch の
  valid pending fragment を加える。記録先は spool へ変えたが収集側が canonical しか読まない。
  **(2026-08-15 棚卸し) 今も高価値**: 記録先を spool へ移したのに /rulings の収集が canonical しか読まないため、未 land branch 上の裁定が総ざらいの母集合から丸ごと落ちる。裁定の取りこぼしに直結する。
- [T-354] (554)
- [T-355] (554)
- [T-360] (554)
- [T-361] (554)
- [T-362] (554)
- [T-364] (554)
- [T-368] (554)
- [T-370] (554)
- [T-372] (554)
- [T-374] (554)
- [T-387] (554)
- [T-388] (554)
- [T-389] (554)
- [T-391] (554)
- [T-392] (554)
- [T-396] **P1・新規**: trigger-gating の受理集合に reward hack 経路が
  ある。EVOLVE-BLOCK の hole は `TxExecutor::abort()` 内の任意 1 行で、機械 gate は識別子 5 個の
  blacklist だけである。`pro_set_` (`cc/silo/include/transaction.hh` の `std::vector<Procedure>`) は
  blacklist に無く、`makeProcedure` は `RETRY:` の前で 1 回しか呼ばれないため、`abort()` で
  `pro_set_.pop_back()` するとトランザクションが retry ごとに縮み、**serializable のまま
  throughput だけ上がる**。`mrctid_` 経由の別経路も指摘された。auditor (LLM) だけが関所である。
  AST allowlist 化を検討する。受理集合の縮小なので D96 手続が要る (規律 2 に直接効く)
  **(2026-08-15 棚卸し) 今も最優先 (規律 2 の直撃)**: EVOLVE-BLOCK の hole から pro_set_.pop_back() で「serializable のまま throughput だけ上がる」reward hack が到達可能であり、関所は LLM auditor だけである。合成の受理集合そのものの穴なので、堅牢化一般とは別格に扱う。
- [T-397] **P2・新規**: sort 軸の構造化 integrity witness を新設する。
  現行の `permutation_violations` は整数 counter と自然文 notes だけで `verdict=indeterminate` /
  `anomalies=[]` になるため、「同じ理由」の同値関係を書けない。
  D138 を sort 軸へ適用する前提条件
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 現行の permutation_violations は整数 counter と自然文だけで verdict=indeterminate に落ちるため、「なぜ壊れたか」を次の一手へ渡せない。sort 軸へ D138 を適用する前提でもある。
- [T-398] (554)
- [T-401] (554)
- [T-402] (554)
- [T-403] (554)
- [T-405] (554)
- [T-410] (554)
- [T-411] (554)
- [T-414] (554)
- [T-415] (554)
- [T-419] **P1・裁定済み (2026-08-12 /rulings、(b)) → 世代列照合へ**: 凍結 protocol の contract hash
  pin は世代列への照合 ([T-478] A′ 機構と同型) へ変える。実装は世代交代を実際に行う wave へ同梱
  (優先度下げ)。残る blocker (iv) 例外集合の空化の依存関係は不変。
  **(2026-08-15 棚卸し) 今も高価値**: 較正チェーンの起点であり、[T-420] / [T-443] / [T-475] / [T-506] / [T-507] / [T-531] ほか多数が本項の U-2 に従属している。本項が動かない限り certified campaign を開けない。
- [T-420] (554)
- [T-424] (554)
- [T-425] (554)
- [T-426] (554)
- [T-429] (554)
- [T-434] (554)
- [T-435] (554)
- [T-437] (554)
- [T-441] **P2・新規**: backoff 軸の EVOLVE-BLOCK hole 受理文法を設計・実装する。
  [T-409] 択一 4 の裁定 (scope = trigger のみで閉じる) による分離。trigger 側の文法 v1
  (`output/insights/2026-08-04_t409-evolve-hole-allowlist/`) を出発点にする
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: backoff 軸の hole 受理文法は合成の受理集合そのもの。trigger 軸だけが 32 正準の閉集合を持ち、backoff 軸は無防備なまま残っている。
- [T-442] (554)
- [T-443] (554)
- [T-446] **P3・新規**:
  **mimalloc の `fetchcontent_ref` は annotated tag `v2.3.2`、`pin` は commit SHA で、
  両者を照合する gate が無い** (`third_party_policy` は ref が 40-hex のときしか照合しない)。
  tag が動いても現行検査は通る。凍結 driver の変更が要る
  **(2026-08-15 棚卸し) 今も高価値 (親の分類を敵対レビューが覆した)**: mimalloc の FetchContent は可動 tag を使う一方 SHA pin との照合 gate が無い。**allocator が入れ替わると測定値が変わるのに gate は通る**。現在たまたま正しい HEAD である事実は将来の穴を閉じない。
- [T-448] (554)
- [T-456] (554)
- [T-464] (554)
- [T-467] (554)
- [T-469] (554)
- [T-470] (554)
- [T-473] (554)
- [T-475] (554)
- [T-478] (554)
- [T-479] (554)
- [T-484] (554)
- [T-488] (554)
- [T-489] (554)
- [T-491] (554)
- [T-493] **P3・新規 (T-490 U-4 の裁定で分離)**: `sort_best.comparator` に
  trigger 軸の 32 閉集合に相当する閉じた権威集合を設計する。[T-410] の witness 設計 (D146) と
  同じ面であり、合流させてよい
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: sort 軸も [T-441] と同じく閉じた権威集合を持たない。trigger 軸との非対称が受理集合の穴になる。
- [T-497] (554)
- [T-500] (554)
- [T-506] (554)
- [T-507] (554)
- [T-508] (554)
- [T-511] (554)
- [T-515] (554)
- [T-518] (554)
- [T-520] (554)
- [T-523] **P1・新規 (配線 wave 段 3 レンズ A-3、親が現物で裏取り)**:
  `s8b_floor_campaign --mode pilot` は trial registry も lifecycle 台帳も通さずに
  freeze 由来の holdout セルを実測できる。U-4 が閉じたのは 8c launcher の経路だけであり、
  H1/H2 の事前観測路はこちらに残る。**同型の欠陥が独立 2 producer で再現した**ので
  (8c launcher と 8b floor campaign)、族一般化として「freeze 由来 holdout を実測へ渡す
  共通下位境界に admission と一回性台帳を置く」設計を起票する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: freeze 由来 holdout を admission も一回性台帳も通さずに実測できる経路が独立 2 producer で再現しており、holdout 漏洩の直接経路になる。
- [T-524] **P2・新規 (同レンズ A-4)**:
  trial_id ごとの一回性と manifest hash ごとの receipt では、**別々の manifest を N 個登録して
  良い receipt だけを下流に渡す** best-of-N を閉じられない。実験単位を
  `(prereg_generation, holdout, arm, replicate_slot)` にし、承認 artifact が全 slot と個数を
  固定する設計へ改める。下流は predeclared receipt の全列挙と消費を検査する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: 別々の manifest を N 個登録して良い receipt だけを下流へ渡す best-of-N を閉じられない。実験計画に対する reward hacking にあたる。
- [T-525] **P2・新規 (同レンズ A-2)**:
  holdout 束縛が workload 名と `ycsb_rratio` だけで、freeze が持つ skew / rmw / records / threads を
  含まない。名前と rratio の一致だけで別条件の測定が H1 として receipt 化されうる。
  ratified freeze の完全な `HoldoutSpec` と SHA を sealed binding にし、campaign identity・
  実行引数・run-start・terminal report・受入で全 field を再照合する。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: holdout 束縛が workload 名と rratio だけなので、skew / rmw / records / threads が違う測定が H1 として receipt 化されうる。
- [T-526] (554)
- [T-527] **P3・新規 (段 6 レンズ B-3 後半)**:
  `rr80` / `rr20` の実 projection が `WORKLOADS` に無く、正式 holdout 起動は現状 production に
  到達しない。U-4 は「拒否」側の到達性を確保済みだが、正式 H1/H2 を走らせるには projection と
  campaign / completeness consumer の追加が要る。これは配線でなく測定能力の追加であり、
  [T-295] の発効と歩調を合わせる。
  **(2026-08-15 棚卸し) 今も高価値**: 正式 H1/H2 の projection が production に存在しないため、8c 正式実験は現状「起動できない」。配線ではなく測定能力の追加であり、本走の前提になる。
- [T-530] (554)
- [T-531] (554)
- [T-536] (554)
- [T-540] (554)
- [T-541] (554)
- [T-543] (554)
- [T-548] (554)
- [T-550] (554)
- [T-551] (554)
- [T-554] (554)
- [T-559] (554)
- [T-561] (554)
- [T-562] (554)
- [T-565] (554)
- [T-566] (554)
- [T-567] (554)
- [T-568] (554)
- [T-570] **P3・新規**: 作図系が admission を経由せず WAL を直接読むため、
  topology 違反の WAL からも図と provenance が出る
  **(2026-08-15 棚卸し) 今も高価値 (親の分類を敵対レビューが覆した)**: 作図系は admission を経由せず WAL の bench_done / commit だけで certified 値として作図する。**偽または topology 違反の WAL が論文図へ入る経路**であり、provenance の粒度の問題ではなく図の値が誤る問題である。
- [T-571] (554)
- [T-575] (554)
- [T-578] (554)
- [T-580] **P2・新規**: admission receipt の `validator.sha256` と
  oracle の `generator_versions` は leaf source の hash だけを記録し、判定に使う被 import module の
  意味論を閉じていない。`artifact_admission` は自分自身を hash しながら WAL の
  strict reader へ判定を委ねており、reader 側が変わっても receipt は不変のまま受理集合が変わりうる。
  T-503 とは独立に成立する穴で、versioned transitive source closure を新設するか、
  盲点を明示的な限界として記録するかの択一を含む。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2。親の分類を敵対レビューが覆した)**: admission receipt は自分自身の hash しか validator identity にせず、判定を live の WAL reader へ委譲する。reader の意味が変われば **receipt 不変のまま受理集合が変わる**。同上の理由で見送りから戻した。
- [T-581] (554)
- [T-582] (554)
- [T-583] **P2・新規**: `submit_certify.sh` が `qsub` へ
  repo 外の `-o` / `-e` を渡さないため、job のたびに `.o<ID>` / `.e<ID>` が repo 直下へ返り、
  次の submit を dirty gate が、land を clean 要求が塞ぐ。repo を submit directory にする job は
  `-o` / `-e` をファイル path で渡す規範が runbook にあるのに従っていない。
  現状は毎回手で job-staging へ移して凌いでいる。
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 較正 certify を回すたびに repo 直下へ .o/.e が返り、次の submit を dirty gate が、land を clean 要求が塞ぐ。毎回手作業で凌いでいるのに、直すのは qsub へ渡す -o / -e の 1 箇所である。
- [T-584] (554)
- [T-585] (554)
- [T-591] (554)
- [T-599] (554)
- [T-604] (554)
- [T-607] (554)
- [T-611] (554)
- [T-612] **P3・裁定済み (2026-08-07 委任) → 実残骸観測後に設計**: 未完了 container の自動回収は
  手動削除 / `--resume` のまま、`DW-G04` に従い実残骸 path を観測してから設計する (wave 記載の
  追認)
  **(2026-08-15 棚卸し) 発火条件が成立した**: DW-G04 が求めた実残骸 path の観測は、エントリ 552 で得られている (変異 scratch を rm -rf した結果、git の worktree 登録に実体なし残骸が残り、次の変異走が rc=125 で起動前に落ちた)。設計へ進んでよい。
- [T-613] (554)
- [T-617] (554)
- [T-619] (554)
- [T-620] (554)
- [T-623] (554)
- [T-637] (554)
- [T-638] (554)
- [T-646] (554)
- [T-650] **P2・新規**: claim → 受入 → land → release/通知 を 1 つの
  wrapper へ束ね、受入赤・land 失敗・例外でも必ず release する機械的な finally を作る。
  現状は入口の契約文が終端での解放を要求するだけで、取り残しは TTL 2400 秒まで他 wave を止める。
  **(2026-08-15 棚卸し) 今も高価値**: lease の取り残しが TTL 2400 秒まで他 wave を止める。claim から release までを 1 つの finally で束ねる機械的な手当てで消える。
- [T-659] (554)
- [T-669] (554)
- [T-681] (554)
- [T-688] **P2・裁定済み (2026-08-12 /rulings) → 採用**: job wrapper 側に durable checkpoint /
  partial-log path を作り、SIGKILL・OOM・walltime 打ち切り・起動前 rc=16 の診断ゼロを塞ぐ。
  **(2026-08-15 棚卸し) 今も高価値**: 床値 job が SIGKILL・OOM・walltime で落ちたときに診断がゼロになる。[T-748] / [T-971] の実測が job artifact の手作業復元に頼っている現状の原因でもある。
- [T-693] (554)
- [T-696] (554)
- [T-699] (554)
- [T-711] **P2・新規**:
  `docs/spool/failures/` の fragment は「新規」「再発」しか持たず、**既存 F の恒久対応欄を
  更新する経路が無い**。現在 `docs/failures.md` の 10 件が「恒久対応: 未実施」のままで、
  そのうち F176 は本 wave で実装済みだが台帳上は未実施に見える。
  wave が canonical を直接編集するのは禁止されているため迂回できない。
  選択肢は (a) fragment に「更新」節を足す (対象 F と差し替える行を base digest 付きで書く)、
  (b) 恒久対応の状態を F 本文でなく別の索引に持つ、(c) fold 後に人手で直す運用を明文化する。
  **(2026-08-15 棚卸し) 今も高価値**: failures 台帳の 10 件が「恒久対応: 未実施」のままで、うち少なくとも F176 は実装済みである。canonical 台帳が事実と食い違う状態を wave 側からは直せない。
- [T-713] (554)
- [T-715] (554)
- [T-724] **P2・新規 (本エントリ)**: `tools/spool_fold.py:1151` の
  `carry_re` が `変わらず (前エントリ参照)` という序数なしの旧形式 stub を carry と認識せず、
  `substantive_digest` がそこで停止する。carry 鎖にこの形式を含む item では、fragment の
  `base:` 照合が実本文でなく stub の digest と突き合わされ、「他 wave が先に書き換えていたら
  止まる」保護が実質的に効かない。本 wave の [T-201] で実測した (F190)。
  閉じ方は `carry_re` の拡張か旧形式を carry として解決する経路の追加、および
  一致しない `変わらず` 形式の存在を検査する meta-test。
  **(2026-08-15 棚卸し) 今も高価値**: 本 wave の実測で、active 657 件のうち 35 件が旧形式 stub (変わらず (前エントリ参照)) を carry 鎖に含んでおり、その全件で base 照合の「他 wave が先に書き換えていたら止まる」保護が効いていない。
- [T-733] **P2・新規**: source closure を**推移閉包**へ広げるか。
  現在の 8 path は閉包ではなく、`pipeline.py` が verifier / calibrator / buildcache /
  build_admission / source_digest へ、`execution_guard.py` が env_attestation / site_policy へ
  判定を委譲している。qualification 側の 37 path 集合が規模の目安。
  成果物影響 = これがない限り「certified 経路が source-bound」とは永久に名乗れず、
  委譲先の差し替えは成果物のどの値からも検出できない。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2。親の分類を敵対レビューが覆した)**: 8 path の source closure に verifier / calibrator / buildcache が入っていないため、**verifier だけを弱めても既存 lock の照合を通り、誤った variant が certified になりうる**。親は当初これを粗い provenance 基準の見送り側へ分類したが、これは「読み手への証明」ではなく正しさ防壁自身が束縛されていない穴である。
- [T-734] (554)
- [T-750] (554)
- [T-754] **P3・新規**: `tools/check_wave_startup.py` は local main
  との乖離と handoff の実在を見るが、**同じ worktree を他 process が使用中かを見ない**。同一
  タスクの背景 job を 2 本起動すると slug が一致するため必ず同じ worktree へ入る
  (F203)。「同一 worktree path を argv に持つ生存 process が自分以外に
  居ない」を fails-closed で検査する。自己マッチと並行 wave の子への誤マッチを避ける照合方法
  (pid 除外、worktree path での一意化) を含めて設計する。
  **(2026-08-15 棚卸し) 今も高価値**: 同一 worktree を他 process が使用中かを見ないため、稼働中の wave の worktree を壊しうる (F203)。背景 job 運用では実害が大きい。
- [T-755] (554)
- [T-758] **P2**: 既存 docs の誤り 3 件の訂正 —
  `ccbench-anatomy.md:211` (ermia active は raw cstamp)、同 `:126` (mocc の自由軸は 2 つ)、
  `phase3.md:269` (si の trace-hook 既存)。1 件目は S1 着手時の必須知識として書かれており、
  従うと誤実装するため優先する
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 3 行の訂正だが、1 件目は S1 着手時の必須知識として書かれており、従うと誤実装する。protocol 移植 ([T-755]) の前に片付ける価値がある。
- [T-762] (554)
- [T-776] (554)
- [T-777] (554)
- [T-778] (554)
- [T-782] (554)
- [T-785] (554)
- [T-790] (554)
- [T-793] (554)
- [T-805] (554)
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
- [T-818] (554)
- [T-822] **P2・裁定済み (2026-08-11 /rulings、閉じる) → 8c 正式系列の着手前に実装 wave 起票可**:
  8c 正式受入の恒真保証 3 件 ((i) Layer-3 chain を必須経路で呼ぶ / (ii) 宣言 arm の実走認証 /
  (iii) 6 report 間の `measurement_head` 一致検査) を実装で閉じる。「意図的な限界として明文化」は
  正しさゲートの格下げのため不採用。実装順・段階分けは wave の設計に委ねる。実装面のため
  Codex author 必須
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: 8c 正式受入の恒真保証 3 件。「意図的な限界として明文化する」案は正しさゲートの格下げにあたるため不採用と既に裁定されており、実装で閉じるしかない。
- [T-823] (554)
- [T-824] (554)
- [T-826] **P2・新規 ([T-813] (ii)、2026-08-11 裁定)**: M0 =
  受入テストの分割不変性と real-repo 排他閉包を機械検査で成立させる。排他閉包の欠落は
  分割と無関係に同時 dispatch の偽赤 (F136 族) の源であり、独立価値を持つ。
  [T-813] の再評価条件 1 の前提。正本 = `output/insights/2026-08-11_t813-acceptance-sharding/`
  **(2026-08-15 棚卸し) 今も高価値**: real-repo 排他閉包の欠落は分割と無関係に同時 dispatch の偽赤 (F136 族) を生み、受入の再走を恒常的に増やしている。
- [T-828] (554)
- [T-829] (554)
- [T-830] (554)
- [T-834] (554)
- [T-835] (554)
- [T-839] (554)
- [T-841] (554)
- [T-842] (554)
- [T-843] (554)
- [T-845] (554)
- [T-846] (554)
- [T-847] (554)
- [T-848] **P1・新規**: 変異 `TIMEOUT` の意味を
  「RUN 開始を receipt で確認した後の計算ノード実行 timeout」に限定し、queue timeout を
  別 status にする。現行は dispatch subprocess 全体に timeout が掛かるため、**一度も走っていない
  変異が terminal として `registered == recorded` を満たす。**逐次経路にも存在する既存欠陥で、
  D130 決定 (3) 条件 4 の `total_deadline` と同族。既存台帳の再解釈が要る。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 一度も走っていない変異が terminal として registered == recorded を満たすため、変異台帳が偽の緑を出す。検出力の主張そのものが汚染される。
- [T-850] (554)
- [T-851] (554)
- [T-853] (554)
- [T-855] (554)
- [T-859] (554)
- [T-860] (554)
- [T-861] (554)
- [T-863] (554)
- [T-865] (554)
- [T-870] (554)
- [T-875] (554)
- [T-876] (554)
- [T-878] (554)
- [T-880] (554)
- [T-882] (554)
- [T-884] (554)
- [T-885] (554)
- [T-887] (554)
- [T-889] (554)
- [T-890] (554)
- [T-892] (554)
- [T-893] (554)
- [T-894] **P2・新規**: 受入待ち手の merge 競合診断に競合 path を
  出させる。現状は `stage=merge rc=70` だけで、親が `git merge` を手で再現しないと
  着手できない。待ち手が abort する前に `git diff --diff-filter=U --name-only` を
  job directory のファイルへ書き出すだけで往復が 1 つ減る。
  F231 の残余。
  **(2026-08-15 棚卸し) 今も高価値 (低コスト)**: 現状は stage=merge rc=70 だけが出るため、親が git merge を手で再現しないと着手できない。競合 path を job directory へ書き出すだけで往復が 1 つ減る。
- [T-895] **P2・新規**: 「次の一手」の項が裁定で終端したまま
  active に残り続ける構造を検知する。本 wave の実測では 62 件が滞留し、うち 52 件は残件ゼロ
  だった。先頭行の終端語 (終端 / 見送り / 受容 / 現状追認) による抽出は誤検出率が約 16%
  (10/62 は生きた項) なので、**gate ではなく定期報告**にする。受理集合を変えないため
  `DW-G05` の影響は「報告の有無」だけで、実装しなければ backlog の単調増加が続く。
  **(2026-08-15 棚卸し) 本 wave が手作業で 1 回実施した (高価値枠からは外す)**: 2026-08-15 の全件棚卸しで active 664 件を判定し、陳腐化 + 価値小として 305 件を見送りへ移した。定期報告として機械化する価値は残る (今回の手作業は 1 wave 分の丸ごとを要した)。
- [T-896] **P3・新規**: [T-186] が見送り台帳 (`docs/phase3.md`) と
  worklog の「次の一手」に二重在籍している。台帳側が残余 3 件の正本で、active 側は重複。
  ID 保存則は両方が sink を満たすため機械検査に当たらない。同型が他にないかの棚卸しと、
  どちらを正本にするかの規約化を行う。
  **(2026-08-15 棚卸し) 実測した (高価値枠からは外す)**: 見送り台帳の item 先頭 ID 188 件と active 657 件を突き合わせ、二重在籍は 8 件 ([T-059] [T-181] [T-183] [T-184] [T-185] [T-186] [T-189] [T-190]) と確定した。**8 件とも active から落とせないことを land で実測した** — 見送り台帳は同一 ID の重複を機械拒否するため、既に台帳へ項を持つ ID を新たな見送り item として追加すると fold が rc=26 で止まる (2026-08-15 の land 1 回目)。active から落とす手段は `完了` か `見送り` しかないので、**残作業のある二重在籍項は現行機構ではどちらの手段でも落とせない**。したがって 8 件は無変更で carry した。本項の残作業は「どちらを正本にするか」の規約化に加えて、**この落とせなさ自体を解く手段** (台帳側の項を消せるようにするか、`更新` で台帳側へ寄せるか) を含む。残るのは「どちらを正本にするか」の規約化である。
- [T-902] (554)
- [T-912] (554)
- [T-919] (554)
- [T-923] (554)
- [T-928] (554)
- [T-929] (554)
- [T-932] **P1・新規**: repository の成長に比例して実行コストが増える構造の
  テストを棚卸しし、D335 に従い恒久保留 (ユーザーの
  明示命令まで実行対象外) を執行する。保留は削除でなく可視な skip 印 + 機械可読な理由の
  記録で行い、正しさゲートを担うテストが該当した場合は保留一覧でユーザーへ提示する。
  **(2026-08-15 棚卸し) 今も高価値**: 成長比例テストの棚卸しと恒久保留の執行そのもの。放置すると受入時間が repository の成長に張り付く。
- [T-935] (554)
- [T-936] (554)
- [T-937] (554)
- [T-938] (554)
- [T-939] (554)
- [T-941] (554)
- [T-944] (554)
- [T-949] (554)
- [T-952] (554)
- [T-958] (554)
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
- [T-960] (554)
- [T-963] (554)
- [T-967] (554)
- [T-971] **P1・部分完了**: 床値 sort_best の SWO oracle 不可用の原因を実測で確定し、
  診断・resolver・依存束縛・compiler 明示注入を実装した。**ただし床値は 1 件も取れていない** —
  FetchContent staging が別 blocker として残り、計算ノードでの end-to-end 確認も未実施。
  残件は (a) 計算ノードでの実測 (resolver 解決と CMake configure の可否を同時に測る短い PBS probe)、
  (b) [T-1094] の解決。
  **(2026-08-15 棚卸し) 今も高価値**: 床値クラスタの本体。残件 (a) 計算ノードでの end-to-end 実測と (b) [T-1094] のうち、(b) が閂である。
- [T-972] (554)
- [T-980] (554)
- [T-981] **P2・新規**:
  `evidence_status=invalid` の理由を receipt へ記録する。現状は
  `codex_exit_code=0` / `validator_rc=0` のまま成果物が捨てられ、
  どの行のどの検査で落ちたかが一切残らないため、prompt や成果物の品質を疑う方向へ誤誘導される。
  併せて consult / review 段で web_search を既定無効にするか、
  stdout event の重複キー扱いを証跡検査から分離するかを決める
  (F263)。
  **(2026-08-15 棚卸し) 今も高価値**: evidence_status=invalid で子 1 本の成果が丸ごと捨てられるのに、どの行のどの検査で落ちたかが残らない。原因が prompt 品質と誤診される。
- [T-986] (554)
- [T-987] (554)
- [T-989] **P1・新規**: 受入 wall の最長 node
  (`test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment`、
  全走 61.6〜90.0 秒 / 単独走 6.81 秒) の実体は module fixture `benchmark_snapshots` の
  snapshot 構築 (単独走 49.80 秒) である。実 repo を hardlink なしで複製しているため
  **commit 数に比例**する。hardlink / object 共有で payer 自体を安くすれば
  「wall ≈ 最長 node + 約 30 秒」モデル上は wall が動く唯一の場所。
  検証は D357 に従い 3 走以上の中央値で行う。
  **(2026-08-15 棚卸し) 今も高価値**: 受入 wall のモデル上「wall が動く唯一の場所」であり、payer が commit 数に比例するため放置すると開発するほど遅くなる (D335 と同面)。
- [T-995] (554)
- [T-997] (554)
- [T-998] (554)
- [T-999] (554)
- [T-1002] (554)
- [T-1004] (554)
- [T-1005] **P2・新規**: `test_codex_worker_launch.py` が受入全走で
  非決定的に落ちる。2026-08-13 の受入 2 走目で 6 件が同時に落ち、同 file の単独再走は 114 passed /
  rc=0 で再現しなかった。2 tip 間の差分に同 file・その依存の変更は無い。落ちたのは receipt /
  manifest / docs authority を検査する node 群で、並行 wave の codex 子が共有する状態
  (`~/.codex/sessions`、docs authority snapshot、receipt) との競合が疑われる。48 worker の xdist で
  再現条件を切り分け、共有状態への依存を fixture 側で断つか、依存が本質なら受入での直列化を裁定する。
  **(2026-08-15 棚卸し) 今も高価値**: 受入全走で 6 件が同時に落ち、単独再走では再現しない。並行 wave の共有状態との競合が疑われ、受入の再走コストを直接押し上げている。
- [T-1009] **P2・新規**: 変異 harness の失敗 node 抽出が
  `--force-dispatch` 経由では壊れる。dispatch が子 stdout の中間を省略するため、
  失敗が多い変異で `PARSE_ERROR` になる (本 wave の N6)。回避策は直接 pytest を runner にすること。
  harness 側で「省略された stdout を検出したら fail-closed で別経路を促す」方が安全。
  **(2026-08-15 棚卸し) 今も高価値・要整合**: --force-dispatch 経由で失敗 node 抽出が壊れる本項と、「変異 runner には --force-dispatch を必ず渡す」という運用 ([T-613]) は現状そのままでは両立しない。どちらを正とするかを決める必要がある。
- [T-1010] (554)
- [T-1011] (554)
- [T-1012] (554)
- [T-1013] (554)
- [T-1016] (554)
- [T-1017] (554)
- [T-1018] (554)
- [T-1021] (554)
- [T-1023] (554)
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
- [T-1026] (554)
- [T-1028] (554)
- [T-1029] (554)
- [T-1031] (554)
- [T-1032] (554)
- [T-1033] (554)
- [T-1036] (554)
- [T-1038] **P2・裁定済み (第 10 回)**: (a) checker 側修正 — `_check_worktree_handoff` は
  tracked file を foreign control-plane として通し、untracked のみ残置と見なす。同 wave で
  submodule 初期化失敗時の提示文も `-c protocol.file.allow=always` 形へ直す (本文の未採番裁定)。
  実装待ち。
  **(2026-08-15 棚卸し) 今も高価値**: docs/handoff の残置が全 background job の起動検査を赤にする再発を、checker 側で構造的に止める裁定済みの修正である ([T-1039] / [T-1037] / [T-234] の恒久対応)。
- [T-1047] (554)
- [T-1049] (554)
- [T-1055] (554)
- [T-1056] **P2・新規**: `tools/dev_wave_wait.py producer` が、
  `.done` も成果物も存在せず producer が生存している状態で、出力ゼロ・rc=0 で即座に返る
  ことがある。2026-08-13 に 5 回実測 (02:44 / 03:12 / 03:55 / 03:58 / 04:14 JST)。
  親が 3 点照合 (成果物実在 + `.done` + producer 死) で検知して張り直したため実害は出ていないが、
  待ち手を信じる呼び手は「子が成功した」と誤認する。成果物影響 = 子の成果物なしで次段へ進み、
  context 無しの出力をレビュー結果と数える経路が開く。
  **回収 context でさらに 2 例 (09:12:29 / 09:17:29 JST)。通算 7 例で、うち 1 例は
  投入 31 秒後だった。**
  **(2026-08-15 棚卸し) 今も高価値**: 通算 7 例。待ち手を信じる呼び手は子の成果物なしで次段へ進み、context 無しの出力をレビュー結果と数える経路が開く。
- [T-1057] (554)
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
- [T-1061] (554)
- [T-1063] (554)
- [T-1064] (554)
- [T-1065] (554)
- [T-1066] (554)
- [T-1068] **P2・新規**: trigger 骨格の宣言側と呼出依存を凍結するか。
  R4 (prologue での `izanagi_gate_pass` 再宣言による代入・真理値の無効化)、R5 (宣言と BEGIN の間の
  制御流変更による非到達化)、R7 (`Backoff` / `FLAGS_clocks_per_us` の local shadowing) は、
  いずれも block と epilogue を逐語一致させたまま gate を無効化できる。実証差分は
  `output/insights/2026-08-13_t1048-trigger-freeze-epilogue/verbatim/consult-b.md` 所見 1、
  同 `consult-a2.md` 所見 2、同 `review-b.md` 所見 2。
  **(2026-08-15 棚卸し) 今も高価値 (規律 2)**: block と epilogue を逐語一致させたまま gate を無効化できる 3 経路 (R4 / R5 / R7) が実証差分つきで残っている。凍結領域の意味が破れる。
- [T-1069] (554)
- [T-1071] (554)
- [T-1072] (554)
- [T-1073] (554)
- [T-1074] (554)
- [T-1075] (554)
- [T-1077] (554)
- [T-1079] (554)
- [T-1080] (554)
- [T-1081] (554)
- [T-1082] (554)
- [T-1084] (554)
- [T-1085] (554)
- [T-1086] (554)
- [T-1087] **P1・新規**: `tools/check_acceptance_reds.py` が
  自分の dispatch 受領証で自分の清浄性検査を落とし、rc=2 (判定不能) から復帰できない。
  再走・collection が probe worktree を cwd にして `run_tests.py --force-dispatch` を呼ぶため、
  `.gitignore` 記載の `output/pegasus-dispatch/` に受領証が書かれ、直後の
  `--ignored=matching` 検査が非空になる。判定器が使えないと、受入が rc=1 の wave は
  非帰属を機械的に立証できず land できない。清浄性検査から dispatch 受領証 path を
  除外するか、受領証を probe worktree の外へ出す設計が要る。
  **(2026-08-15 棚卸し) 今も高価値**: 非帰属 checker が自分の dispatch 受領証で自分の清浄性検査を落とし rc=2 から復帰できない。判定器が使えないと、受入が rc=1 の wave は非帰属を立証できず land できない。
- [T-1090] **P3・要裁定**: 非帰属 checker は赤 n 件に対し collection と rerun で dispatch を
  2n 回行う。**本 wave が実測モデルを取り、有界並列化は不採用を推奨した**
  (低負荷で `T(n) = 15 + 63n`、P=4 の節約は受入試行あたり平均 約 26 秒。
  単独 rerun のノイズ床を上げて帰属する赤を非帰属へ倒す偏りがあり、
  `--force-dispatch` の同時投入は他 wave を遅らせうる)。
  代替として **1 dispatch job で複数 node を扱う設計** (2n qsub を n または 1 へ減らす) を推奨する。
  これは rerun の実行環境を変えないので同じ偏りを生まない。dispatcher の secure task と
  receipt schema の新設が要るため、着手可否はユーザー裁定を待つ。
  **(2026-08-15 棚卸し) 今も高価値 (ユーザー裁定待ち)**: 非帰属 checker が赤 n 件に対し dispatch を 2n 回行う。有界並列化は不採用を推奨済みで、1 dispatch job で複数 node を扱う設計の着手可否だけが残っている。
- [T-1091] (554)
- [T-1093] (554)
- [T-1094] **P1・新規 (B 系)**:
  床値 build 経路に FetchContent の source 差し替えを通す。`buildcache.py` には
  `FETCHCONTENT_SOURCE_DIR_*` の配線が 0 件で、計算ノードは直結 network 不可
  (`docs/pegasus-runbook.md:744-756`)。`silo_ladder_rung1.py:1046` に先例がある。
  **これが解けない限り、oracle を直しても床値は 0 件のままである。**
  shared build path のため全 campaign へ波及する点に注意。
  **(2026-08-15 棚卸し) 今も最優先**: 床値が 1 件も取れていない直接の閂であり、oracle 側を直しても本項が解けない限り結果は 0 件のままである ([T-971] / [T-748] が実測で確認済み)。shared build path のため全 campaign へ波及する。
- [T-1095] **P2・新規 (B 系)**:
  oracle の compile closure を byte で封印し、oracle receipt を floor proof chain へ耐久化する。
  現状は env が transport 兼 authority になりうる。`config.h` は Git 非管理なので
  HEAD pin だけでは閉じない。`expected config.h hash` の置き場所は D115 (identity 非束縛の
  key だけ floor policy へ) と D152 (cache root は policy から導出しない) の双方に
  抵触しうる**未解決の設計択一**であり、裁定が要る。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3。親の分類を敵対レビューが覆した)**: oracle の `config.h` は観測 hash を記録するだけで期待値と照合しない (F46 型 = 記録するだけで発火しない値)。Git HEAD が正しくても **oracle のコンパイル意味を変えられ、誤った oracle 判定が floor chain へ入る**。
- [T-1096] **P2・新規 (B 系)**:
  `p3_s4_loop_sort.py` の oracle 依存解決も使い捨て checkout 上で失敗する。
  floor 限定の解決では直らず、S5 の sort_best gate・WAL・campaign report は
  `infrastructure-unavailable` に汚染されたまま。全 consumer へ trusted dependency root と
  compiler を明示注入する共通 seam を作るか、S5 を明示的に別扱いにするかの裁定が要る。
  **(2026-08-15 棚卸し) 今も高価値**: sort 側 oracle が解けないままだと S5 の sort_best gate・WAL・campaign report が infrastructure-unavailable に汚染され続ける。床値クラスタと同じ seam の裁定を要する。
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
- [T-1098] (554)
- [T-1101] **P3・新規**: 受入試行の終端 (成功・失敗 stage・所要秒)
  を機械集計する仕組みが無く、本 wave は job dir の mtime と log から手作業で復元した (約 30 分)。
  受入 receipt か task-run へ「lease 待ち秒・critical section 秒・終端 stage」を残せば、
  以後のボトルネック裁定が実測でできる。
  **(2026-08-15 棚卸し) 今も高価値**: 受入試行の終端・所要・失敗 stage を機械集計できず、ボトルネック裁定のたびに手作業復元 (約 30 分) が要る。
- [T-1102] (554)
- [T-1103] (554)
- [T-1105] **P2・新規**: codex 子の sandbox から
  `tools/run_tests.py` が走らない (local 予約台帳を更新できず dispatch へ倒れ、
  `qstat -Q preflight rc=1` で rc=16)。本 wave で 3 回、別 wave でも同型が観測されている。
  子が実測できないと段 5・6 の「緑には実走 nodeid を併記」が常に親へ集中する
  **(2026-08-15 棚卸し) 今も高価値**: codex 子から tools/run_tests.py が走らないため、段 5・6 の実測がすべて親へ集中する。dev-wave の並列度を直接下げている。
- [T-1107] **P2・新規・フレーク**:
  `test_public_main_real_signal_releases_lease` は 48 worker の受入全走でだけ赤になる。
  子へ SIGTERM を送り rc=143 を期待するが、負荷下では signal 到達より先に
  `acceptance-scheduler-attestation` の `marker-count` が発火して rc=70 になる
  (テスト用 tmp repo の child argv は scheduler marker を出さない)。単独走・焦点走では緑。
  受入を止める帰属赤として観測されるため、期待を「143 または attestation 失敗」に広げるのでなく、
  marker を出す child か attestation を待たせる seam を設ける方向で直す。
  **(2026-08-15 棚卸し) 今も高価値。本 wave の受入 1 走目で実際に発火し、新事実を 1 つ足す**: 08:51 JST の受入全走が本 node で赤になり land できなかった。**重要なのは、非帰属 checker の単独再走も同じ rc=70 (`stage=acceptance-scheduler-attestation`、`detail={"observed":[],"reason":"marker-count"}`) で落ちたため `status=attributable-red` と判定され、receipt が出なかったことである。** 一方で親が同じ node を通常の焦点走で回すと **1 passed / 2.16 秒**で緑になる (docs のみの差分は当該 file に到達しない)。つまり本フレークは「赤になる」だけでなく **非帰属経路でも解除できない**種類であり、踏んだ wave は受入をやり直す以外に道がない。checker の再走環境が scheduler marker を出さないことが原因側にあるため、[T-1087] とも同じ面である。
- [T-1109] **P1・新規・ユーザー裁定待ち**:
  D122 決定 (2)(ii) の `PBS_JOBID` 受理文法が実機で充足不能である。
  択 (a) transport 側を `(?:0:)?<request-id>` へ拡げる (collector と同形。負例集合の更新を伴う)、
  択 (b) job script が request ID を切り出して渡す (**gate が検査する env の書き換えであり親は迂回と判定**)、
  択 (c) witness を `PBS_JOBID` 以外の実在証拠へ替える。
  **親の推奨は択 (a)** — repo 内に既に `(?:0:)?` を許す consumer があり、D122 決定 (7) は
  witness を attestation でないと明言済みなので防護の主張は減らない。受理集合の変更なので D96 手続。
  **(2026-08-15 棚卸し) 今も高価値 (ユーザー裁定待ち)**: 実機の `PBS_JOBID` が gate を通らないため 8c live pilot が起動できない。親推奨 (a) の根拠 (同形の consumer が既に repo 内にあり、D122 決定 (7) が witness を attestation でないと明言) まで揃っており、裁定 1 つで [T-1112] が動く。
- [T-1110] (554)
- [T-1111] **P1・新規・ユーザー裁定待ち**:
  fail-closed admission 述語に「実在の production 値を自分の述語へ通す positive control」を
  族として義務づけるか。F97 (登録済み較正が自分の attestation 述語を通らない) と
  本 wave の [T-1109] (実機 `PBS_JOBID` が transport 述語を通らない) は
  別 producer / 別 consumer の独立 2 例で、`DW-G03` の族一般化閾値を満たす。
  どちらも「誰かが実際に走らせるまで発見されない」型である。
  検査義務の新設なので親は実装せず裁定へ返す。
  **(2026-08-15 棚卸し) 今も高価値 (規律 3)**: 「fail-closed の述語が、実在の production 値を実際には通さない」型は F97 と [T-1109] の独立 2 例が揃い `DW-G03` の閾値を満たす。誰かが実走するまで発見されない型なので、族として positive control を義務づける価値がある。
- [T-1112] **P1・新規**: 上 2 件が閉じた後に 8c A/B/C live pilot を再投入する。
  job script と依存 staging は保全済みで、単独性検査と gflags/glog build はそのまま再利用できる。
  **(2026-08-15 棚卸し) 今も高価値**: 8c A/B/C live pilot の再投入そのものであり、ユーザーが目標の柱と位置づける無人ループの実走にあたる。job script と依存 staging は保全済みで、閂は [T-1109] / [T-1110] の裁定 2 件だけである。
- [T-1113] (554)
- [T-1114] **P2・新規 (段 8 自己改善)**: `tools/check_docs.py` へ
  「spool fragment の `更新` / `完了` item の本文が carry stub 形式 (`- [T-NNN] (N)` または
  `- [T-NNN] 変わらず ...`) に一致したら赤」を足す。F313 の機械化であり、
  現状は `base:` 照合も `check_docs` も `spool_fold --dry-run` も緑のまま素通りする
  (本 wave で実測)。実装面のため Codex author が要る。成果物影響 = 未実装なら、
  main 取り込みを挟む wave が `更新` のたびに元本文を失う経路が開いたままになる。

