# 採点 reason 人間監査シート (v2 §9 — 集計後・報告前の明示の段)

**監査観点:** 採点者が「曖昧を yes に倒した」形跡の点検。各 reason が
(1) 実在の構造/診断項目を名指ししているか (2) 恒真文でないか (3) no にすべき曖昧を
yes にしていないか。判定を覆すべきものがあれば該当 score-ID をユーザー裁定で記録する。

集計値: main 20/20 適格 / c4 17/20 / c5 20/20。名目 p: S-2 (main vs c4) = 0.115 /
S-3 (main vs c5) = 1.0。棄却→再採点 5 件 (reject ファイルは scores/ に保存)。

## main-00 (score-045)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 材料1診断の「validation 中のロック競合に対する2種の待たない政策の選択」は no-wait 政策の二択を軸とし、silo-backoff-magnitude は abort 後グローバル待機。本提案は lockWriteSet() の `if (expected.lock)` 競合分岐に tuple-local な有界スピン待機を新規挿入するもので、既存の二択(no-wait同士)でも abort 後 global 待機でもない別作用点・別処理段(待機の新規導入)。軸内言い換えの域を超え構造的に別の hole。
- **c2**: stock 実在の lockWriteSet() `if (expected.lock)` 分岐・CAS 取得路を指し、diagnostics 実在項目(政策反転 abort_rate 50.8→21.0%, balanced ipc1.62; backoff ipc崩壊1.4-1.6→0.4-0.5)に接続。反証観測として workload 別 abort_rate/latency/ipc の振る舞い(write-heavy で稼ぎ側 vs balanced で ipc 崩壊側)を指定しており否定可能。
- **c3**: mutation_type=code_fragment (待機ループ挿入の構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: 診断の「コミット時ログ書込の有効化(on/off)」は logging の有無軸。本提案は wal() の flush 発火閾値 `log_set_.size() > LOGSET_SIZE/2` を可変化するもので on/off とは別の作用点(束サイズ/書込頻度)。
- **c2**: stock 実在の wal() flush 条件を指し、診断実在項目(throughput 低下が書込比率に単調比例, abort 不変・latency/llc_miss 増)に接続。反証観測として write-heavy での I/O コスト(書込回数減による latency/llc_miss/throughput 変化)を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は機械的グリッド探索で代替可能のため no。提案自身も scalar 型と明記。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: silo-backoff-magnitude は abort 後グローバル待機(スカラー軸)、no-wait 政策軸は validation lock 応答。本提案は read_internal() の `while (expected.lock)` 無限スピンに上限を与える read 路 tuple-local の別作用点・別処理段。既出軸のいずれとも別 hole。
- **c2**: stock 実在の read_internal() スピンループ・二度読み一致確認を指し、診断実在項目(backoff の ipc 崩壊 1.4-1.6→0.4-0.5, read-heavy latency5.7→25μs, -77%)に機序クラスを接続。反証観測として read-heavy でのスピン滞留比率・ipc/latency を指定し、有意でなければ恒真側に落ちると自ら明記=否定可能。
- **c3**: mutation_type=code_fragment (スピン上限化と分岐追加の構造変異)。
**round_eligible: True**

## main-01 (score-002)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal() の TID word 監視スピンループ (transaction.cc の for(;;){while(expected.lock)...} 実在) の待ち政策。診断3軸 (backoff magnitude=post-abort待機・validation no-wait政策・commit log書込) のいずれとも別の処理段 (read phase のロック解除待ち) を対象にしており、silo-writeset-sort/silo-backoff-magnitude の既開通 hole とも別作用点。
- **c2**: read_internal の busy-wait は stock に実在 (while(expected.lock) がタイトにロードを回す)。機序は post-abort 待機の IPC 崩壊 (1.4-1.6→0.4-0.5) と同型の占有機構を別位置で踏むという仮説で、IPC/latency の観測量および契機切替時の abort 増という反証可能な観測を指定している。
- **c3**: mutation_type=code_fragment (待ち方の制御フロー差替)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() の flush 閾値 (if(log_set_.size()>LOGSET_SIZE/2)) を対象とする hole。診断の『commit log書込 on/off』とは別の作用点 (書込頻度=バッチ粒度) で、閾値そのものは診断に既出でない。
- **c2**: wal() の log_set_ 蓄積・logfile_.write は stock に実在。診断項目3 (書込 I/O コストへの帰属、latency/llc_miss 増・abort不変) に接続し、閾値変化と I/O 償却/latency の地形という反証可能観測を指定。
- **c3**: mutation_type=scalar 単体 (write() 発行頻度を制御する単一スカラー)。スカラー単体は既存グリッド探索で代替可能のため no。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は abort() 内 #if BACK_OFF の待機発火箇所 (transaction.cc に実在) に『待つか否か・いつ待つか』の gate を挟む制御フロー変異。既開通 hole silo-backoff-magnitude は backoff.hh のスカラー待機量軸であり、本提案は別作用点 (abort() 制御フロー) の code_fragment で magnitude では表現不能。診断の on/off はコンパイル時大域フラグの観測だが、本提案は局所状態/abort契機による動的 gate という構造的に別の hole。
- **c2**: abort() の Backoff::backoff 呼出は stock 実在。診断項目1 の非対称 (純損は削れる再試行が無い abort にも一律待機コストを払う) に接続し、gate による相殺workload/純損workload 間の throughput 地形という反証可能観測を指定。
- **c3**: mutation_type=code_fragment (待機発火の gate 制御フロー変異)。
**round_eligible: True**

## main-02 (score-016)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の alive 軸は silo-backoff-magnitude (post-abort backoff・include/backoff.hh)、validation 内の待たない政策、コミット時ログ書込の3件と dead な writeset-sort。本提案は cc/silo/transaction.cc の read_internal 内 `while(expected.lock) loadAcquire` の read フェーズ・ビジースピンに上限を挟む別処理段の hole で、いずれの既出軸とも別位置。yes。
- **c2**: read_internal のロッククリア待ちスピン `for(;;){ while(expected.lock){...} }` は stock 抜粋 (transaction.cc) に実在。仮説は診断項目1の『待機が IPC を潰す (1.4-1.6→0.4-0.5)』機序を同型のこのスピンに適用し、上限導入で abort 率×IPC が交換されるという反証可能な観測 (最適上限の workload 依存性・IPC/abort の振る舞い) を指定。実在構造に接続。yes。
- **c3**: mutation_type=code_fragment (スピン上限カウンタと超過時 abort 分岐の構造変異)。yes。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: 診断のコミット時ログ書込軸は WAL on/off の I/O コスト帰属。本提案は wal() の flush 発火閾値 `log_set_.size() > LOGSET_SIZE/2` を変異穴にする別位置 (on/off ではなくバッチ粒度)。構造的に別 hole。yes。
- **c2**: wal() の flush 判定閾値は stock 抜粋 transaction.cc に実在。診断項目3の書込 I/O コスト帰属 (abort 不変・latency 増・llc_miss 増) を根拠に閾値上昇で write() 頻度減→latency 償却、llc_miss は逆向き悪化という符号付き反証可能観測を指定。yes。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。提案文自身も scalar とラベルしている。
**round_eligible: True**

## main-03 (score-005)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: diagnostics には silo-backoff-magnitude (include/backoff.hh の abort 後・再試行前待機) と silo-writeset-sort (dead, 施錠順序 comparator) のみ。本提案は read_internal 内のロック解放待ちスピン (別ソース transaction.cc・別処理段=read phase・別作用点) を hole 化しており、既出軸の再掲でも軸内探索の言い換えでもない。
- **c2**: stock 抜粋 transaction.cc の read_internal に実在する `for(;;){ while(expected.lock){loadAcquire...} }` 解放待ちを指しており実在構造に接続。反証可能な観測 (待機規律を変えても IPC 占有と read latency のトレードオフ・read-path 待機地形が現れなければ仮説棄却) を指定し、attribution[0] の IPC 崩壊/latency 悪化の非対称を根拠に据える。
- **c3**: mutation_type=code_fragment (構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: attribution[2] はログ書込の on/off の帰属であり、本提案の wal フラッシュ発火閾値という別作用点は診断に既出でない。transaction.cc wal 内の別 hole。
- **c2**: stock の wal 内 `if (log_set_.size() > LOGSET_SIZE/2)` に実在接続し、閾値変更で throughput が動かなければ I/O 償却仮説を棄却という反証条件を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため不適格。
**round_eligible: True**

## main-04 (score-055)
### 提案 0 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() 内の flush 発火閾値 `if (log_set_.size() > LOGSET_SIZE / 2)`。診断 silo-backoff-magnitude.attribution[2] は『コミット時ログ書込の on/off』という別 hole であり、書込量を吐く閾値（バッチ束ね量）の変異は別作用点。材料 1 の transaction.cc wal() に実在する未開通位置。
- **c2**: wal() の log_set_ 蓄積閾値超過で単発 logfile_.write する処理は stock 抜粋 transaction.cc に実在。latency/llc_miss が動くという反証可能観測を指定（abort_rate 不変と整合）。実在構造に接続。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal() (a) のロッククリア待ち無制限スピン `for(;;){ while(expected.lock){...} }`。診断 silo-backoff-magnitude.attribution[0] は abort 後の再試行前バックオフ（別 phase・別サイト）で、read phase のスピン待ちは別 hole。材料 1 transaction.cc に実在する未開通位置。
- **c2**: read_internal (a) の loadAcquire 無制限ビジースピンは stock 抜粋に実在。待ち方変異が ipc/latency の地形を持つとし、ipc が動かなければ否定される反証可能観測を指定。実在構造に接続。
- **c3**: mutation_type=code_fragment（構造変異）で待ち方の骨格差し替え。yes。
**round_eligible: True**

## main-05 (score-015)
### 提案 0 — 不適格 (c1=False c2=True c3=True)
- **c1**: hole 位置は lockWriteSet() の `if (expected.lock)` 競合応答分岐で、これは診断 attribution の実在項目「validation 中のロック競合に対する 2 種の待たない政策の選択」がまさに指す既出軸の作用点と同一。提案自身も『既存二択の離散点を内挿する骨格』と述べ、同じ処理段・同じ作用点での政策空間探索 (軸内探索) にとどまる。別の処理段・別の状態・別の作用点ではないため既存性 no。
- **c2**: mechanism は stock 実在の lockWriteSet() 分岐 (NO_WAIT_LOCKING/NO_WAIT_OF_TICTOC) を指し、診断の反転 (ipc 1.62 高発行 vs abort_rate 50.8→21.0%/latency 同時低減) に紐づく。反証可能な観測 (どの指標で勝つかが反転境界をまたぐ) を指定。恒真ではない。
- **c3**: mutation_type は code_fragment (構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() の flush 発火しきい値 `if (log_set_.size() > LOGSET_SIZE/2)`。診断の「コミット時ログ書込の有効化 (on/off)」は logging の有効化トグルであり、flush バッチ粒度という別作用点。既出軸の再掲ではない。
- **c2**: mechanism は stock 実在の wal() バッチ書込経路を指し、診断の書込 I/O 帰属 (abort 不変・latency/llc_miss 増加・書込比率に単調比例) に接続。syscall 頻度低下という反証可能観測を指定。
- **c3**: mutation_type が scalar 単体。既存の機械的グリッド探索で代替可能なため軸適格性 no。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は abort() 内 `#if BACK_OFF` 待機発火ブロックを abort 原因分類で gating するコード片。診断の silo-backoff-magnitude は backoff.hh の待機量スカラー (別作用点・別構造)。原因分類による発火判定という新たな状態・作用点を導入しており、量のスカラー探索とは構造的に別 hole。既存性 yes。
- **c2**: mechanism は stock 実在の abort() backoff ブロックを指し、診断の ipc 崩壊 (1.4-1.6→0.4-0.5) と損の abort-baseline 依存 (write-heavy -22.5% < read-heavy -77%) に紐づく。非競合由来 abort での ipc 回復という反証可能観測を指定。原因分類の伝播は未実装だが幻覚ではなく提案として追加する構造であり、機序核は実在観測に接続。
- **c3**: mutation_type は code_fragment (構造変異)。
**round_eligible: True**

## main-06 (score-043)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 対象 hole は TxExecutor::read_internal の read-phase 待機ループ (`while(expected.lock){ loadAcquire }` と (e) 再読安定チェック) で、stock 抜粋に実在。診断の既出軸は backoff.hh の再試行前待機 (silo-backoff-magnitude) と validationPhase/lockWriteSet 内のロック競合『2 種の待たない政策』(attribution[1]) だが、本提案は read-phase・別関数・別段の待機構造を作用点にしており構造的に別 hole。writeset-sort とも別。yes。
- **c2**: read_internal の無制限スピン (実在) と attribution[0] の ipc 崩壊 (1.4-1.6→0.4-0.5) / read-heavy latency 5.7→25μs を機序の根拠に接続し、bounded/no-wait 化で read-heavy の spin コストと abort コストのトレードオフ地形が現れる (latency/abort/throughput の振る舞い) と反証可能な観測を指定。恒真文ではなく実在構造に繋がる。yes。
- **c3**: mutation_type=code_fragment (待機継続 vs 早期中断の分岐構造の書換)。scalar 単体でない。yes。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: 対象 hole は wal() の flush 閾値 `if (log_set_.size() > LOGSET_SIZE/2)` で stock に実在。診断 attribution[2] は『コミット時ログ書込の on/off』であり閾値変異とは別作用点。構造的に別 hole でありこの項自体は yes だが C3 で不適格。
- **c2**: attribution[2] の書込 I/O コスト帰属 (write-heavy -13.4%・latency/llc_miss 増・abort 不変) と wal() の一括 write 構造 (sizeof(LogRecord)*logRecNum_) に接続し、閾値変化で write() あたりレコード数=syscall アモータイズ度が変わり write-heavy に latency/throughput 地形が現れると反証可能に指定。実在構造に繋がる。yes。
- **c3**: mutation_type=scalar 単体 (flush バッチ閾値の数値のみ変異、I/O 構造は不変)。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
**round_eligible: True**

## main-07 (score-018)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は cc/silo/transaction.cc の read_internal 内、ロック中タプルへの読み取り経路のタイトスピン待機 (`while (expected.lock) { ... }`) の待機規律。診断の silo-backoff-magnitude は abort 後の再試行前 backoff (別位置・別処理段)、silo-writeset-sort は施錠順序 comparator、validation の待たない政策は lockWriteSet 内の書込セット施錠待機であり、いずれも read 経路の spin とは別 hole。構造的に別作用点で既出でない。
- **c2**: read_internal の減衰なしタイトスピンは stock に実在。attribution の ipc 崩壊 (1.4-1.6→0.4-0.5) と『コアが待機で実命令を発行できない』を IPC 律速の根拠に繋げ、read-heavy latency 5.7→25μs から相対感度を示唆。反証可能な観測 (待機規律変異で abort/IPC/latency の地形が post-abort backoff と別位置で動くか) を指定。実在構造に接続し反証可能。
- **c3**: mutation_type=code_fragment、待機政策の続行/離脱判断の構造差し替え。スカラー単体でない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は wal() 内のフラッシュ発火条件 (`if (log_set_.size() > LOGSET_SIZE / 2)`) の粒度/構造。診断『コミット時ログ書込の有効化 (on/off)』は書込機能の有無への帰属であり、フラッシュ発火規律 (batching/group-commit トリガ構造) の変異は別作用点で既出でない。stock の wal() は実在。
- **c2**: attribution『コミット時ログ書込』の throughput 低下が書込比率に単調比例・純書込 I/O コスト帰属を根拠に、per-flush 償却コストがフラッシュ粒度に支配される機序を提示。wal() の固定半バッファ閾値フラッシュは stock に実在。反証可能な観測 (write-heavy で per-flush 粒度変異が throughput/latency/llc_miss をどう動かすか) を指定。実在構造に接続し反証可能。
- **c3**: mutation_type=code_fragment と明示され、skeleton は発火構造の差し替え (batching/group-commit トリガ) を記述。unknowns で scalar の可能性に触れるが提案の骨格は構造変異でスカラー単体でない。
**round_eligible: True**

## main-08 (score-034)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の locked tuple に対する常時スピン待機 `for(;;){ while(expected.lock){...} }` の待機打ち切り政策。診断の 3 軸 (abort 後バックオフ待機 in backoff.hh / validation 中の待たない政策 in lockWriteSet / コミット時ログ書込) はいずれも別の処理段。read phase のスピン待機は別の作用点で、構造的に別 hole。yes
- **c2**: 参照する read_internal の locked tuple 常時スピンは transaction.cc の stock 抜粋に実在。attribution 項目1 の IPC 崩壊 (1.4-1.6→0.4-0.5) を援用し、read phase 側でも同型のコア停止 (低 IPC) が発生しうるとし、workload 別 IPC/throughput という反証可能な観測を指定。yes
- **c3**: mutation_type は code_fragment (待機打ち切り判定の挟み込み構造変異)。yes
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() のフラッシュ発火閾値 `log_set_.size() > LOGSET_SIZE/2`。診断のログ書込軸は on/off であり、group-commit のバッチ粒度は別の作用点。構造的には別 hole。yes (ただし C3 で不適格)
- **c2**: 参照する wal() のフラッシュ閾値式は transaction.cc の stock 抜粋に実在。attribution 項目3 (書込 I/O コストへの帰属・abort 率不変) を援用し、write() 発火頻度が I/O 償却率を支配するとし、write-heavy の throughput/latency という反証可能な観測を指定。yes (ただし C3 で不適格)
- **c3**: mutation_type は scalar 単体 (閾値のみのチューナブル化)。スカラー単体は既存の機械的グリッド探索で代替可能なため no。束内でも自ら headline 非対象 scalar と明記。no
**round_eligible: True**

## main-09 (score-004)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal の読取フェーズのロック待ちスピン (for(;;){while(expected.lock){...}}) を hole 化。診断は backoff-magnitude・validation の no-wait 政策・WAL・writeset-sort(dead) を扱うが、読取フェーズのスピン待ちサイトはどれとも別の処理段・別作用点。既出でない。
- **c2**: stock の transaction.cc read_internal に実在するスピン待ちループを指す。ipc 崩壊・lock政策反転の診断に接続し、読取側スピン→即abort差替えで abort率↔ipc トレードオフが立つと予想、workload 依存の throughput 地形という反証可能な観測を指定。
- **c3**: mutation_type=code_fragment (構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() のフラッシュ発火閾値 (log_set_.size()>LOGSET_SIZE/2) を対象。WAL 診断はログ書込 on/off の I/O コストで、フラッシュ頻度という別ノブだが、C3不適格のため適格には無関係。
- **c2**: stock の wal() に実在する if(log_set_.size()>LOGSET_SIZE/2) 発火判定を指す。純I/Oコストは batching で償却可能という機序から write-heavy端 (-13.4%) で地形が最も動くという反証可能な予測を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: 既開通 silo-backoff-magnitude と同一 region (include/backoff.hh) だが、対象は Backoff::backoff の待機ループ per-iteration 本体 (_mm_pause 挙動) であり、待機量スカラー (Backoff_/update_backoff) とは別の作用点。長さでなく待機中挙動という構造的に別の hole で、軸内探索の言い換えに当たらない。
- **c2**: stock backoff.hh の for(;;){_mm_pause();stop=rdtscp();if(chkClkSpan)break;} を指す。ipc 崩壊 (待機で実命令発行不能) の帰属に接続し、待機総量固定で本体差替えると ipc 崩壊を abort率低減から切り離せるか、read-heavy 側で回収余地最大という反証可能な観測を指定。
- **c3**: mutation_type=code_fragment (構造変異)。
**round_eligible: True**

## main-10 (score-038)
### 提案 0 — 不適格 (c1=False c2=True c3=True)
- **c1**: 診断 attribution 第2項『validation 中のロック競合に対する 2 種の待たない政策の選択』は、まさに lockWriteSet() 内の `if (expected.lock)` 競合応答分岐 (NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC の択一) を既出軸として掲げている。本提案は同一作用点・同一処理段 (validation の施錠競合応答) に第3の中間政策 (有界スピン) を挟むもので、別の処理段・別の状態・別の作用点ではなく既出軸の応答形状の探索拡張 (軸内探索) に当たる。提案自身も unknowns で『既存二極の言い換えでない構造照合』『D47 必須条件 3 の対象』と重複懸念を明記しており、曖昧側は no に倒す。
- **c2**: stock 実在の lockWriteSet #if 分岐・IPC 1.62・abort 50.8→21.0% に接続し、balanced/write-heavy に地形が集中し read-heavy 0.4% は順位不能という反証可能な観測 (どの workload で感度が出れば/出なければ仮説が崩れるか) を指定している。
- **c3**: mutation_type=code_fragment、有界スピン→再取得→上限 abort の構造変異でスカラー単体ではない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断 attribution 第3項『コミット時ログ書込の有効化』は on/off トグルの軸であり、本提案は wal() 内 `if (log_set_.size() > LOGSET_SIZE / 2)` の flush 粒度・まとめ書き単位という構造的に別の作用点 (書込の有無ではなく flush 頻度・バッチ構造) を提案している。診断に載る軸の骨格再掲でも軸内探索でもなく、別 hole。
- **c2**: stock 実在の wal() flush 判定・LOGSET_SIZE/2=500・LogHeader.chkSum_・コメントアウト済み fdatasync に接続し、write-heavy に最大の地形・read-heavy 低感度という反証可能な予想を指定している。
- **c3**: mutation_type=code_fragment。skeleton は flush 閾値とまとめ書き単位 (バッチ構造改訂) を変異面に置き、構造変異とスカラーの複合。提案は scalar/code_fragment 確定不能と自己言及するが宣言値は code_fragment で構造改訂を含むため yes。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal() の `for(;;){ while(expected.lock){...} }` ロック解放待ちスピンは、診断3軸 (backoff.hh の待機量・lockWriteSet の validation 政策・log 書込) のいずれとも異なる処理段 (read phase の読取り一貫性待ち) の作用点で、診断に未掲載。validation 側 no-wait 軸とは別の処理段・別の状態 (読取り一貫性 vs 施錠) であり構造的に別 hole。提案自身が重複懸念を明記しつつも位置・状態が異なる。
- **c2**: stock 実在の read_internal スピンループに接続し、IPC 崩壊 (1.4–1.6→0.4–0.5)・latency 5.7→25μs を機序根拠に、read-heavy に地形を持つ (read 経路支配) という反証可能な予想を指定している。
- **c3**: mutation_type=code_fragment、有界スピン→abort の構造変異でスカラー単体ではない。
**round_eligible: True**

## main-11 (score-011)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断に載る軸は silo-backoff-magnitude (backoff.hh の post-abort 待機) と silo-writeset-sort (write set 施錠順序 comparator, dead)。本提案は cc/silo/transaction.cc の read_internal の read-phase スピンループ `while(expected.lock)` を有界化する hole で、別処理段 (read フェーズの待機) ・別作用点。診断の再掲でも軸内探索の言い換えでもない。
- **c2**: read_internal の `for(;;){ while(expected.lock){...} check==expected で break }` は stock 抜粋 transaction.cc に実在。attribution[0] の ipc 崩壊・latency 増と attribution[1] の read-heavy 0.4% (noise 内) を突き合わせ、read-heavy の待機感応が write 側競合経路に由来しえない余地を read 側スピンに帰す論。反証観測 (有界化で read-heavy IPC/throughput が backoff コストなしに回収されるか) を指定。恒真文でも幻覚でもない。
- **c3**: mutation_type は code_fragment (有界スピン+abort 分岐という構造変異にスカラー副パラメタ埋込の複合形)。構造変異とスカラーの複合は適格。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: attribution[2] はコミット時ログ書込の on/off (feature toggle)。本提案は wal() のフラッシュ発火水位 `if (log_set_.size() > LOGSET_SIZE/2)` の変異で、on/off とは別位置 (有効時の I/O 償却水位)。診断軸の再掲ではない。
- **c2**: wal() の `if (log_set_.size() > LOGSET_SIZE/2)` は stock 抜粋に実在。attribution[2] の書込 I/O 純コスト帰属 (latency増/llc_miss増/abort不変) に接続し、発火水位を上げて syscall を償却すれば write-heavy -13.4% の損を validation/abort に触れず狙えるとする反証可能な予想。実在構造に繋がり観測指定あり。
- **c3**: mutation_type が scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。提案自身も headline 非対象と自認。
**round_eligible: True**

## main-12 (score-050)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断3軸は backoff待機(include/backoff.hh, abort後)・validation中のロック競合政策(lockWriteSet)・コミット時ログ書込。本提案は read_internal() の施錠中スピン `while(expected.lock)` という別の処理段(読取フェーズの待機サイト)に hole を開けており、材料1のどの軸とも作用点が異なる。構造的に別 hole。
- **c2**: mechanism は stock 実在の read_internal() スピンループを指し(transaction.cc に存在)、backoff軸の ipc崩壊 indicator を機序として引用。read-heavy 中心に性能地形が出るという反証可能な観測(read-heavy で感度が出なければ否定)を指定。恒真文でなく実在構造に接続。
- **c3**: mutation_type は code_fragment。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() のフラッシュ発火閾値 `if (log_set_.size() > LOGSET_SIZE / 2)` は診断のログ書込 on/off 軸とは別の作用点(閾値)であり材料1に既出でない。
- **c2**: wal() の実在するフラッシュ判定を指し、ログ書込軸の latency/llc_miss indicator を機序に繋げ write-heavy 中心のトレードオフ地形という反証可能予想を指定。
- **c3**: mutation_type が scalar 単体。スカラー単体は機械的グリッド探索で代替可能なため不適格。提案自身も『scalar 型のため段6 headline 非対象』と記述。
### 提案 2 — 不適格 (c1=False c2=True c3=True)
- **c1**: hole 位置が lockWriteSet() の `if (expected.lock)` 競合応答分岐であり、診断 attribution 第2項『validation 中のロック競合に対する 2 種の待たない政策の選択』とまさに同一の作用点。政策の識別は射影で落とされているが、同じ処理段・同じ競合応答点で応答戦略を挟み替える提案であり既出軸の探索範囲内。提案自身も unknowns で『軸内探索でないことの確認が要る』と自認。曖昧につき no に倒す。
- **c2**: lockWriteSet の実在する競合応答分岐を指し、attribution 第2項の政策反転・ipc/abort_rate indicator を機序に接続。反転する性能地形という反証可能観測を指定。
- **c3**: mutation_type は code_fragment。
**round_eligible: True**

## main-13 (score-039)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal() の read フェーズ内ロック解放待ちスピン (while(expected.lock) loadAcquire)。診断の silo-backoff-magnitude は include/backoff.hh の abort 後 backoff、silo-writeset-sort は validationPhase の施錠順 comparator であり、いずれとも別処理段・別作用点。materials 1 の diagnostics に read フェーズのスピン構造の軸は無い。
- **c2**: read_internal の実在スピン構造 (stock 抜粋の for(;;){while(expected.lock)...(e)再確認} ) を指し、backoff attribution の IPC 崩壊 (1.4-1.6→0.4-0.5)・latency 増を同型のバスィ待機機序として引用。反証観測 (throughput 地形が出るか/単調 latency 悪化のみで地形が無い可能性) を明示。
- **c3**: mutation_type は code_fragment。有界スピン化・pause 挿入・再読上限化等の構造変異。scalar 単体ではない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は wal() のフラッシュ粒度・coalescing (log_set_ 閾値 LOGSET_SIZE/2・1 write レコード数・fdatasync)。診断第3項は WAL on/off の帰属のみで粒度は未変異と本文も指摘。同一ファイルだが writeset-sort とは別関数・別位置、write I/O 経路という別作用点。
- **c2**: stock 実在の wal() 書込ブロック (閾値判定・logfile_.write・chkSum) を指し、attribution 第3項の書込 I/O 局在 (write-heavy -13.4%・latency/llc_miss 増・abort 不変) に接続。反証観測 (write-heavy で amortize が throughput 地形を生むか/地形が乏しい可能性) を明示。
- **c3**: mutation_type は code_fragment。coalescing 戦略・同期方式の構造変異を含む。閾値のみなら scalar 化する旨を unknowns で自認しているが、提案骨格は構造変異として提示されている。
**round_eligible: True**

## main-14 (score-024)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は cc/silo/transaction.cc の TxExecutor::read_internal 内 for(;;) ループ先頭の `while (expected.lock) { ... }` という read phase のロック待ちスピン点。診断の既開通 hole は silo-backoff-magnitude (backoff.hh の abort 後再試行前待機量スカラー) と silo-writeset-sort (施錠順序 comparator) の 2 つで、いずれも read phase のスピン待機とは別の処理段・別作用点。構造的に別 hole で yes。
- **c2**: mechanism は stock 実在の read_internal スピンループ (材料1 transaction.cc に実在) を指し、待機で ipc が崩壊する機序 (診断の ipc 1.4-1.6→0.4-0.5) を read phase の idle 待機点に同型に働くと予想。反証可能な観測として read-heavy 側の ipc/latency 地形の有無を指定 (感度が read-heavy に出なければ否定) しており、実在構造への接続と反証可能観測を満たす。yes。
- **c3**: mutation_type は code_fragment (構造変異=待機構造の差替え) で yes。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は TxExecutor::wal 内 `if (log_set_.size() > LOGSET_SIZE / 2)` のフラッシュ発火閾値。診断の既開通 hole (backoff-magnitude / writeset-sort) とは別位置。コミット時ログ書込は attribution に軸として載るが、この閾値リテラルという作用点は診断骨格に既出でない。yes。
- **c2**: mechanism は stock 実在の wal 関数のフラッシュ閾値 (材料1 に実在) を指し、診断のログ書込 I/O コスト帰属 (throughput 低下が書込比率に単調比例) に対し閾値が I/O 償却度を左右すると予想。反証可能観測として write-heavy 側の地形を指定。実在構造接続と反証可能観測を満たす。yes。
- **c3**: mutation_type は scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
**round_eligible: True**

## main-15 (score-046)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: diagnostics の 3 軸は backoff 待機量 (backoff.hh)・validation の 2 待たない政策 (lockWriteSet)・WAL on/off。本提案は read_internal の for(;;) 内 `while (expected.lock) { ... }` = 読取フェーズのロック待ちスピンという別処理段の hole を提案しており、材料 1 の診断・既開通 hole いずれにも該当しない。構造的に別の作用点。
- **c2**: stock 抜粋 transaction.cc の read_internal に実在する無限スピン待機を正確に指し、attribution[0] の ipc 崩壊 (1.4–1.6→0.4–0.5) と attribution[1] の待機打ち切り政策の workload 反転という実測値に接続。反証可能な観測 (ipc・abort_rate・workload 感度) を指定しており恒真文ではない。torn read を作らず abort/retry へ倒す点も末尾 expected==check 再検査という実在構造に整合。
- **c3**: mutation_type が code_fragment (スピンを上限付き→abort 変換する分岐差替)。スカラー上限は副次パラメータで構造変異が主体のため適格。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() 内 `if (log_set_.size() > LOGSET_SIZE / 2)` のフラッシュ閾値という位置は WAL on/off とは別の作用点で、診断に閾値軸は載っていない。位置としては既出でない。
- **c2**: stock 抜粋 transaction.cc の wal() に実在する閾値条件を指し、attribution[2] の書込 I/O コスト帰属 (latency/llc_miss 増、abort 不変) に接続。反証可能な観測 (per-flush 固定費償却・latency) を指定。
- **c3**: mutation_type が scalar 単体。閾値スカラーのみを動かす提案で構造変異を伴わないため、既存の機械的グリッド探索で代替可能。提案自身も headline 非対象・探索補助限定と明記。
**round_eligible: True**

## main-16 (score-031)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断 silo-backoff-magnitude は『待機量の決定 — スカラー値軸』(include/backoff.hh の kMaxBackoff/gradient 更新)。本提案は Backoff::backoff() の待機ループ本体 (_mm_pause busy spin の消費形態) を作用点とし、待機量スカラーには触れないと明記。同一領域だが別の作用点 (量ではなく消費形態の構造) を開く構造変異で、診断骨格の再掲ではない。
- **c2**: stock の backoff.hh に実在する `for(;;){_mm_pause(); ...}` busy spin を指し、attribution の ipc 崩壊 (1.4–1.6→0.4–0.5) を『待機量過大』でなく『コア占有で実命令発行不能』に帰属。ipc がスカラー調整で回復するか否かで反証可能な観測を指定。実在構造に接続。
- **c3**: mutation_type は code_fragment (待機粒度・譲歩挟み込みの構造差替え)。
### 提案 1 — 不適格 (c1=False c2=True c3=True)
- **c1**: 診断 attribution『validation 中のロック競合に対する 2 種の待たない政策の選択』が lockWriteSet() の `if (expected.lock)` 分岐をまさに既出軸として記述している。本提案は同一の施錠競合分岐 (同じ処理段・同じ作用点) で応答方針を選ぶ hole を開いており、有界スピン等の中間形態を加えても既出軸の探索範囲内の変異 (骨格再掲) に相当する。別の作用点・別の処理段ではない。
- **c2**: lockWriteSet() の #if 二択分岐 (NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC) は stock に実在し、政策反転 (差 balanced 19.6%/write-heavy 12.7%) と abort_rate 50.8→21.0% 等の反証可能観測を指定。機序自体は実在構造に接続。
- **c3**: mutation_type は code_fragment (競合応答分岐の構造変異)。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断 attribution『コミット時ログ書込の有効化 (on/off)』は logging の on/off 切替を軸とする。本提案は wal() の `if (log_set_.size() > LOGSET_SIZE/2)` フラッシュ発火条件・バッチ粒度を作用点とし、on/off とは別の処理段 (発火閾値・まとめ書き粒度の構造) を開く。診断骨格の再掲ではない。
- **c2**: wal() の `if (log_set_.size() > LOGSET_SIZE/2)` フラッシュ経路は stock に実在し、attribution の書込 I/O コスト (throughput -13.4% / latency・llc_miss 増・abort 不変) に帰属。latency/llc_miss の振る舞いで反証可能な観測を指定。実在構造に接続。
- **c3**: mutation_type は code_fragment (フラッシュ発火条件・粒度の構造変異)。
**round_eligible: True**

## main-17 (score-033)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の (a) ロック待ちスピン `while (expected.lock) { expected.obj_ = loadAcquire(...) }`。診断3軸 (backoff-magnitude=include/backoff.hh の post-abort 待機、validation ロック競合政策=lockWriteSet、コミットログ書込) のいずれとも別の処理段 (read phase のロッククリア待ちビジースピン) を対象とし、材料1 stock (transaction.cc read_internal) に実在するが診断未収載の別作用点。
- **c2**: attribution1 の ipc 崩壊 (1.4-1.6→0.4-0.5)・read-heavy 最大損 (throughput -77%/latency 5.7→25μs) を引き、read_internal の実在する上限なしリロードスピンが read-heavy でホットタプルに当たり IPC シンクとなる仮説。反証観測として read-heavy の発行率/latency を指定。stock 実在構造に接続し反証可能。
- **c3**: mutation_type=code_fragment (スピンの形の構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() のフラッシュ閾値 `if (log_set_.size() > LOGSET_SIZE/2)`。診断 attribution3 は log 書込 on/off の帰属であり、フラッシュのバッチ粒度閾値は別の作用点で材料1 stock (transaction.cc wal) に実在。既出軸そのものの再掲ではない。
- **c2**: attribution3 の書込比率単調比例・純 I/O 帰属を引き、wal() の実在する write() バッチ発行と閾値による syscall 償却の関係を仮説化。write-heavy の latency/llc_miss で反証可能に観測指定。stock 実在構造に接続。
- **c3**: mutation_type=scalar 単体。閾値のスカラー値のみで構造変異を伴わないため no (機械的グリッド探索で代替可能)。提案束自身も『scalar 型のため段6 非対象』と記載。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は validationPhase Phase2 read_set 条件3 `if (check.lock && !searchWriteSet(...)) { aborted; unlockWriteSet(); }` の即 abort。attribution2 の『待たない政策』は lockWriteSet の書込ロック取得点 (NO_WAIT マクロ) が実在証拠であり、read-set タプルが他者施錠中という別状態・別作用点への応答は別の hole。提案自身も書込ロック取得点との構造的別位置を主張。材料1 stock に実在。
- **c2**: attribution2 の政策優劣の workload 間反転 (balanced 19.6% ipc1.62 / write-heavy 12.7% abort 50.8→21.0%) を引き、read 検証条件3 の応答可変化で workload 依存地形を予想。反証観測に workload 反転/abort 率を指定。validationPhase 条件3 は stock 実在構造で接続。
- **c3**: mutation_type=code_fragment (即 abort/再読取り待ち等の応答の構造変異)。
**round_eligible: True**

## main-18 (score-019)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal() の `while(expected.lock)` 無条件 busy-spin ループ (transaction.cc に実在)。診断の待たない政策 (attribution 項目2) は lockWriteSet の validation phase の NO_WAIT_* 分岐であり、本提案は read phase という別処理段に政策選択点を開く。別の作用点・別の状態の hole であり既出の再掲でも軸内探索の言い換えでもない。
- **c2**: mechanism は read_internal の実在する `while(expected.lock)` spin と、attribution 項目1 の IPC 1.4-1.6→0.4-0.5 崩壊・latency 5.7→25μs を指す。read 支配動作点で validation で反転が観測された政策依存の地形が現れる、という反証可能な予測 (現れなければ否定) を指定。stock 実在構造に接続。
- **c3**: mutation_type は code_fragment (待つ/待たない選択を挟む構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() の `if (log_set_.size() > LOGSET_SIZE / 2)` flush 発火閾値 (transaction.cc に実在)。診断の commit log write (attribution 項目3) は on/off であり、本提案は flush 粒度という別次元の作用点。既出骨格の再掲ではない。
- **c2**: mechanism は wal() の実在 flush 閾値と attribution 項目3 の書込 I/O コスト帰属 (latency 増・llc_miss 増・abort 不変) を指し、閾値上げで latency/llc_miss 増分が動く反証可能な予測を指定。
- **c3**: mutation_type が scalar 単体。閾値のスカラー変異は既存の機械的グリッド探索で代替可能なため不適格。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は Backoff::backoff() の `_mm_pause()` busy-spin 待機ループ本体 (backoff.hh に実在)。既開通 silo-backoff-magnitude は待機量スカラー軸だが、本提案は待機量を保ったまま待機プリミティブ (命令発行構造) を差し替える code_fragment。別次元・別作用点であり軸内探索の言い換えではない。
- **c2**: mechanism は backoff.hh 実在の _mm_pause ループと attribution 項目1 の IPC 崩壊 (待機中に命令発行ゼロ) を指し、待機量不変でプリミティブを変えれば abort 低減を残しつつ IPC 崩壊分を回収する、という反証可能な予測を指定。
- **c3**: mutation_type は code_fragment (待機プリミティブの構造変異)。
**round_eligible: True**

## main-19 (score-012)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 対象は read_internal() 内の read phase ロック解放待ちスピン `while (expected.lock)` であり、診断に載る 3 軸 (backoff.hh の abort 後待機=silo-backoff-magnitude、validation の待たない政策、コミット時ログ書込) および既開通の writeset-sort comparator とは別処理段・別作用点。材料 1 の transaction.cc に実在する別 hole を提案しており既出でない。
- **c2**: read_internal() の `for(;;){while(expected.lock){...}}` という実在スピンを指し、attribution 1 の『コアが待機で実命令を発行できない』IPC 崩壊 (1.4-1.6→0.4-0.5) を機序として read 待機点一般へ外挿。反証観測として IPC/latency/abort 率の振る舞い、および torn read の reward hack 反証手順を指定しており反証可能。恒真文でなく実構造に接続。
- **c3**: mutation_type=code_fragment (待機打ち切り/yield/短い待機挟みの構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() 内フラッシュ発火閾値 `if (log_set_.size() > LOGSET_SIZE / 2)` を対象。診断のコミット時ログ書込軸は on/off 有効化の帰属であり、バッチ境界サイズの調整という作用点自体は診断に既出でない。
- **c2**: wal() の実在フラッシュ条件と logfile_.write を指し、attribution 3 の『純粋な書込 I/O コスト』(throughput 低下が書込比率に単調比例、write-heavy -13.4%) を機序に、閾値上げで I/O 発行回数償却を予測。write-heavy throughput・syscall 回数・durability 窓の反証観測を指定。実構造接続で反証可能。
- **c3**: mutation_type=scalar 単体。閾値のスカラー値変異でありスカラー単体は既存の機械的グリッド探索で代替可能なため no。提案自身も unknowns で headline 非対象・探索補助限定と記載。
**round_eligible: True**

## c4-02 (score-049)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断 silo-backoff-magnitude attribution 3 は『コミット時ログ書込の有効化 (on/off)』という WAL on/off 軸。本提案は tpcc_silo.cc worker_init の logfile_.open(O_CREAT|O_TRUNC|O_WRONLY) の open フラグ・同期方針 (O_DSYNC/O_DIRECT/fdatasync 有無) という別の処理段・作用点を hole 化しており、on/off ではなく I/O パスの書込方式変異。構造的に別 hole で既出でない。
- **c2**: attribution 3 (書込 I/O コスト帰属・abort_rate 不変/latency 増/llc_miss 増) を根拠にし、stock 実在の open 呼出 (tpcc_silo.cc worker_init #if WAL) と wal()/log.hh の書込経路を指す。反証可能観測『open/同期方式を変えれば abort_rate を動かさず latency・llc_miss を上下でき、帰属誤りなら効果が出ない』を明示。実在構造に接続。
- **c3**: mutation_type は code_fragment (open フラグ・同期構成の構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: ftruncate(1000000000) の事前確保サイズという hole は診断にも既出軸探索範囲にも無く、別の作用点。既出でない。
- **c2**: attribution 3 の書込 I/O コスト帰属に接続し、stock 実在の ftruncate リテラルを指す。反証可能観測 (確保サイズ変更で abort_rate 不変・latency 変化、効果なければ帰属誤りまたは run 長で観測不能) を指定。実在構造に接続。
- **c3**: mutation_type が scalar 単体 (ftruncate サイズ 1 値のみ)。既存の機械的グリッド探索で代替可能なため no。提案束自身も headline 非対象と自己記載。
**round_eligible: True**

## c4-03 (score-036)
### 提案 0 — 不適格 (c1=True c2=False c3=True)
- **c1**: 診断に載る軸は silo-backoff-magnitude(backoff.hh のスカラー・validation 待たない政策・コミット時ログ書込 on/off)と silo-writeset-sort(施錠順 comparator)のみ。本提案は cc/silo/replayTest.cc の replay ループの 1レコード=1read 逐次読み出しをまとめ読み構造へ差し替える、別領域・別処理段(読み側 I/O 粒度)の hole であり、既出軸・その骨格の再掲でも軸内探索の言い換えでもない。
- **c2**: replayTest.cc の replay ループ・log.hh の computeChkSum・LogRecord は stock 抜粋に実在し接続はある。しかし反証可能な観測(どの観測量がどう振る舞えば否定されるか)が具体に特定されていない。機序は『read 粒度を変えると I/O 律速の性能地形が replay 経路上に現れる』と予想するのみで、観測量として挙げた replay/recovery 時間について提案自身が unknowns 冒頭で『この hole が効く感度を持つ計測対象が計測ハーネスに存在するか自体が機序単独では埋まらない』と明記しており、観測量の存在自体が未確定。曖昧のため no に倒す。
- **c3**: mutation_type は code_fragment(逐次読みをまとめ読み構造に差し替える構造変異)。scalar 単体ではない。
**round_eligible: False**

## c4-04 (score-017)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断には「コミット時ログ書込の有効化 (on/off)」があるが、本提案は on/off トグルではなく sbomb_silo.cc worker_init ラムダの logfile_.open のフラグ集合と ftruncate 事前確保という別の処理段・別作用点 (I/O パス設定) を hole 化しており、transaction.cc の wal() には触れないと明言。軸内探索の言い換えではなく構造的に別の hole。
- **c2**: 参照する logfile_.open / ftruncate(1000000000) は stock 抜粋 sbomb_silo.cc に実在。診断の latency 増・llc_miss 増という指標に接続し、cache 経由回避フラグで llc_miss 増分が動くはずという反証可能観測を指定 (動かなければ page cache 干渉仮説が否定)。実在構造への接続あり。
- **c3**: mutation_type は code_fragment (フラグ集合の書換え)。scalar 単体ではない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断のどの軸 (backoff-magnitude / validation 政策 / ログ書込) にも thid→core 親和性写像は現れない。setThreadAffinity(thid) の恒等写像を並べ替える別作用点で、既出軸の言い換えでない。
- **c2**: 参照する setThreadAffinity(thid) は stock 抜粋 sbomb_silo.cc の worker_init ラムダに実在。診断が llc_miss を『微増/増加』と生きた指標として示す点に接続し、写像を並べ替えると llc_miss (下流 IPC・latency) が動くという反証可能観測を指定。実在構造への接続あり。
- **c3**: mutation_type は code_fragment (thid→core 写像の書換え)。scalar 単体ではない。
**round_eligible: True**

## c4-05 (score-021)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の 3 軸 (backoff-magnitude、validation 中の待たない政策、コミット時ログ書込) と silo-writeset-sort(dead) はいずれも transaction.cc 実装ロジックまたは backoff.hh のスカラー。本提案は cc/silo/include/tuple.hh の class Tuple のメモリレイアウト (tidword_ と body_ のキャッシュライン分離) という別編集面・別作用点の hole であり既出でない。
- **c2**: stock 実在構造を指す: tuple.hh の `alignas(CACHE_LINE_SIZE) Tidword tidword_;` + `TupleBody body_;` の同一ライン共有、transaction.cc read_internal のロック spin (loadAcquire で tidword_ を連続 load)、writePhase の storeRelease(tidword_)。false sharing 仮説を提示し、反証可能観測 (分離後 llc_miss_rate/ipc が abort_rate と切り離されて動く/動かない) を指定。sizeof(Tuple) 増大の交絡も自認しており実質的。
- **c3**: mutation_type は code_fragment、メンバ順序変更/パディング挿入/alignas 付与によるレイアウト構造変異でスカラー単体ではない。
**round_eligible: True**

## c4-06 (score-044)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 材料1診断の3軸 (backoff待機量=タイミング, 待たない政策=制御フロー, ログ書込=I/O) および既開通 hole (silo-backoff-magnitude スカラー / silo-writeset-sort comparator) のいずれとも別。本提案は cc/silo/include/tuple.hh の Tuple メンバ配置 (tidword_ と body_ のライン分離) という別作用点・別状態 (メモリレイアウト) を扱い、既出軸の言い換えでない。
- **c2**: stock 実在構造に接続: transaction.cc の read_internal が tuple->tidword_.obj_ を loadAcquire スピン読み、lockWriteSet/writePhase が同 word を CAS/storeRelease、tuple.hh で tidword_ 直後に body_ が隣接という実配置。false-share でコヒーレンスミスが生じるという仮説で、反証観測として llc_miss_rate/ipc/throughput がライン分離で不変なら否定される旨を指定。恒真文でなく実構造に繋がる。
- **c3**: mutation_type が code_fragment (構造変異=メンバ配置の入れ替え)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: 診断3軸・既開通 hole のいずれとも別で、tuple.hh の alignas 粒度による隣接 Tuple 間 false sharing を扱う別作用点。既出軸の言い換えでない。
- **c2**: stock 実在の alignas(CACHE_LINE_SIZE) tidword_ と診断指標 llc_miss_rate (第1項微増/第3項増加) に接続し、隣接ライン共有量が変われば llc_miss/throughput が動くという反証可能観測を指定。実構造に繋がる。
- **c3**: mutation_type が scalar 単体 (alignas 値の {1×,2×} 切替)。スカラー単体は既存の機械的グリッド探索で代替可能なため no。束内でも自ら headline 非対象・scalar と明記。
**round_eligible: True**

## c4-07 (score-020)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断3軸(backoff待機量・validation待たない政策・コミット時ログ書込)および既開通hole(silo-backoff-magnitudeスカラー/silo-writeset-sort comparator)はいずれもtransaction.cc/backoff.hh側の処理段。本提案はcc/silo/include/tuple.hhのTupleメンバ配置(tidword_とbody_のキャッシュライン相対配置)という別領域・別のhole位置を突いており、材料1のどの軸骨格の再掲でも軸内変異でもない。
- **c2**: tuple.hhに実在するTidword tidword_/TupleBody body_、transaction.ccのread_internalスピンループ・validationPhase再チェック・writePhaseのmemcpyという実在処理に接続。反証可能観測としてllc_miss_rate(診断indicatorsに実在する生きた指標)がレイアウト変異で動くかを指定しており、動かなければ仮説否定という条件が明示されている。恒真文や幻覚構造への依存はない。
- **c3**: mutation_type=code_fragment(alignas付与/パディングメンバ挿入によるメモリレイアウト構造変異)。スカラー単体ではない。
**round_eligible: True**

## c4-08 (score-051)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の既出軸は silo-backoff-magnitude (待機量スカラー)・validation の待たない政策・コミット時ログ書込・silo-writeset-sort (施錠順序 comparator) の4つ。本提案は cc/silo/include/tuple.hh の Tuple メンバレイアウト (tidword_ と body_ の間の padding / 再アライン) という別領域・別の作用点 (レコードのメモリ配置と false sharing) の構造 hole であり、いずれの既出軸の軸内変異でもない。yes。
- **c2**: 機序は stock 実在構造を指す: tuple.hh の `alignas(CACHE_LINE_SIZE) Tidword tidword_;` と後続 `TupleBody body_;`、read_internal の spin-load・lockWriteSet の CAS・writePhase の storeRelease が同一 tidword 語に集中する点は抜粋に実在。反証可能な観測として llc_miss_rate / コヒーレンス往復・throughput の変動を指定し、動かなければ地形なしと否定できると自認 (『地形自体が小さい可能性も同じ数値から読める』)。恒真文ではなく実在レイアウトに接続。yes。
- **c3**: mutation_type は code_fragment と宣言され、padding/再アライン挿入という構造変異。unknowns に scalar 型帰属の迷いはあるが headline 宣言は code_fragment。yes。
**round_eligible: True**

## c4-09 (score-028)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 材料1の既開通 hole は include/backoff.hh の silo-backoff-magnitude (待機量=scalar 軸) のみ。本提案は Backoff::backoff() の spin ループ本体で now_backoff (長さ) を固定し、待機中の占有動作 (_mm_pause() 単発 busy-spin) の構造そのものを差し替える別作用点の code 片穴で、量の言い換えではなく構造的に別の hole。yes。
- **c2**: stock backoff.hh に実在する Backoff::backoff() の for(;;){_mm_pause();stop=rdtscp();if(chkClkSpan)break} 構造を指しており、診断 attribution の ipc『1.4–1.6→0.4–0.5 崩壊 (コアが待機で実命令発行不能)』を名指し。IPC の回復有無という反証可能な観測量を指定 (待ち方変異が IPC を回復させなければ仮説否定)。実在構造接続かつ反証可能観測あり。yes。
- **c3**: mutation_type=code_fragment (spin 本体の構造変異)。scalar 単体ではない。yes。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 既開通 hole silo-backoff-magnitude は待機量 scalar。本提案は待機ループの終了条件 (chkClkSpan による時間到達で break) に早期離脱述語を挟む構造変異で、量の上限は固定したまま『待ち切るか途中で抜けるか』の終了条件という別作用点の hole。提案0 (spin 本体) とも別位置。構造的に別 hole。yes。
- **c2**: stock の chkChlkSpan による flat な時間ベース busy-wait 構造 (実在) を指し、attribution の latency『read-heavy 5.7→25μs 増加』と throughput 全 workload 低下を参照。now_backoff 全量が latency に無条件加算される構造への帰属で、latency の回復有無という反証可能観測を指定。unknowns で信号可読性の懸念を挙げるが機序核心は幻覚でなく実在構造接続。yes。
- **c3**: mutation_type=code_fragment (終了条件構造の変異)。scalar 単体ではない。yes。
**round_eligible: True**

## c4-10 (score-026)
### 提案 0 — 不適格 (c1=True c2=True c3=False)
- **c1**: epoch 前進間隔 (siloLeaderWork 内 chkClkSpan 第三引数) の hole は diagnostics の 3 軸 (backoff-magnitude / validation lock政策 / commit log) いずれとも別の処理段・別作用点。材料1に既出でない構造。
- **c2**: common.hh の alignas(CACHE_LINE_SIZE) GlobalEpoch、util.cc の atomicAddGE、transaction.cc の atomicStoreThLocalEpoch(atomicLoadGE()) といった実在構造を指し、前進間隔短縮でコヒーレンス無効化→IPC低下という反証可能な観測 (IPC の方向) を指定している。
- **c3**: mutation_type が scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: chkEpochLoaded() 全数バリア gate の判定構造差し替えは diagnostics 3 軸のいずれとも別の処理段。epoch 前進停止条件という別状態への作用点で既出でない。
- **c2**: util.cc の chkEpochLoaded() (i=1 から全 ThLocalEpoch 確認)、transaction.cc の atomicStoreThLocalEpoch で epoch 更新される実在構造を指し、backoff空転中の worker 停滞で前進が律速→gate 緩和で epoch 進行/latency/GC 境界が変わるという反証可能な観測を指定。
- **c3**: mutation_type が code_fragment (gate 判定構造の差し替え)。構造変異につき yes。
**round_eligible: True**

## c4-11 (score-010)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の3軸 (backoff-magnitude・validation no-wait 政策・log 書込) と dead の writeset-sort のいずれとも別の hole。材料1の Tuple 定義 (`alignas(CACHE_LINE_SIZE) Tidword tidword_; TupleBody body_;`) の cache line 配置という別作用点を提案しており既出でない
- **c2**: stock 実在構造 (tuple.hh の Tuple メンバ配置、transaction.cc の read_internal spin-load/loadAcquire・lockWriteSet の CAS・writePhase の memcpy) に接続。反証可能観測として llc_miss_rate と coherence traffic の変化を指定し、動かなければ仮説否定という向きが明示される
- **c3**: mutation_type は code_fragment (メンバ順序・padding 幅の構造変異)。scalar 単体でない
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断のどの軸・骨格とも異なる。材料1の Tidword union (lock:1/tid:29/epoch:32 が単一 obj_ に同居) の lock ビットを version ビット群から別語/別 line に分離する構造変異で、別の状態・作用点を提案しており既出でない
- **c2**: stock 実在構造 (tuple.hh の Tidword ビットフィールド、lockWriteSet の lock CAS、validationPhase/read_internal の version 読取り) に接続。反証可能観測として lock-CAS/version-read の line 共有度による coherence traffic・llc_miss の変化を指定している
- **c3**: mutation_type は code_fragment (ビットフィールド語の分解・配置の構造変異)。scalar 単体でない
**round_eligible: True**

## c4-12 (score-057)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 軸は worker→物理コア割当 (tpcc_silo.cc worker_init ラムダの setThreadAffinity(thid) 引数変換) の hole。診断3軸 (backoff on/off・validation 待たない政策・ログ書込 on/off) および dead の writeset-sort のいずれとも別の処理段・別作用点。材料1に affinity 変異軸の既出なし。
- **c2**: 機序は stock 抜粋に実在する setThreadAffinity(thid) 呼出 (tpcc_silo.cc の #ifdef Linux ブロック) を指し、コア配置が LLC 共有/跨ソケットを決めると繋げる。attribution 第1項の ipc 崩壊・llc_miss 微増を根拠に llc_miss_rate/ipc 次元の地形を予想し、割当政策を変えても llc_miss/ipc が動かなければ否定される反証可能な観測を指定。実在構造への接続あり。
- **c3**: mutation_type=code_fragment (setThreadAffinity 引数を写像 f(thid) へ差し替える構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: ftruncate(1e9) のログ事前確保サイズ hole。診断第3項 (ログ書込 on/off) とは別の作用点 (確保サイズ vs 有効化) で、材料1に prealloc size 軸の既出なし。ただし c3 で失格。
- **c2**: 機序は tpcc_silo.cc 抜粋に実在する trans.logfile_.ftruncate(1000000000) を指し、確保済みブロックか割当メタデータ I/O かを分ける。attribution 第3項 (abort 不変・latency/llc_miss 増・書込比率単調比例) と繋がり、write-heavy latency 経由の地形を予想 = 反証可能。実在構造接続あり。
- **c3**: mutation_type=scalar 単体 (ftruncate 引数のバイト数リテラル変異)。スカラー単体は機械的グリッド探索で代替可能のため no。提案本文自身も headline 非対象ラベル自動付与を認めている。
**round_eligible: True**

## c4-13 (score-022)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の attribution 3『コミット時ログ書込の有効化 (on/off)』は WAL 二値の効果帰属。本提案は bomb_silo.cc の worker_init 内 logfile_.open のフラグ集合・ftruncate 前確保量という I/O 設定次元を挟む別 hole であり、on/off 二値とは別の作用点。材料 1 の diagnostics に該当軸なし。
- **c2**: stock 抜粋の bomb_silo.cc に実在する `trans.logfile_.open(logpath, O_CREAT|O_TRUNC|O_WRONLY, 0644)` と `ftruncate(1000000000)` を指しており実在構造に接続。attribution3 の latency 増加・llc 増加観測を根拠に、書込 I/O 支配 workload ほど latency 成分に地形が出ると予測し、反証可能な観測 (latency が I/O 設定変異で動かなければ否定) を指定。
- **c3**: mutation_type = code_fragment (I/O 設定コード片の差し替え)。scalar 単体でない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の 3 attribution (backoff/validation待たない政策/ログ書込) いずれもスレッド配置に触れていない。setThreadAffinity の thid→コア写像という別作用点の hole で、材料 1 の既出軸と構造的に別。
- **c2**: stock の atomic_tool.hh の atomicAddGE(GlobalEpoch)・tuple.hh の tidword という実在構造の coherence トラフィックを指し、bomb_silo.cc の setThreadAffinity(thid) 固定写像を作用点とする。attribution の llc_miss_rate 微増/増加観測を根拠に、配置変異で LLC 共有・coherence 地形 (llc_miss) が動くと予測 — 反証可能な観測 (llc_miss が配置変異で動かなければ否定) を指定。
- **c3**: mutation_type = code_fragment (コア配置写像コード片の差し替え)。scalar 単体でない。
**round_eligible: True**

## c4-14 (score-054)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の silo-backoff-magnitude 第3項は『コミット時ログ書込の有効化 (on/off)』という WAL の有無トグル。本提案は sbomb_silo.cc worker_init の open flag / 書込モード (O_CREAT|O_TRUNC|O_WRONLY の経路構成) を変異させる別位置の hole であり、on/off とは別の作用点。既開通の backoff/sort とも別。構造的に別 hole で yes。
- **c2**: sbomb_silo.cc 抜粋に実在する trans.logfile_.open(...) の flag を指しており実在構造に接続。第3項 attribution の latency 増加・llc_miss_rate 増加・書込比率単調比例を引き、open flag/書込モード変異が同じ latency/llc_miss 指標を動かすとの反証可能な観測を指定。恒真文でない。yes。
- **c3**: mutation_type=code_fragment (構造変異)。yes。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: ftruncate(1000000000) のリテラルという事前確保サイズは診断の on/off とは別次元。ただし c3 で失格。
- **c2**: 実在する ftruncate リテラルを指し、page fault 経由で llc_miss/latency に波及との反証可能観測を指定。stock 構造に接続。
- **c3**: mutation_type=scalar 単体。既存の機械的グリッド探索で代替可能なため no。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: setThreadAffinity(thid) の worker→コア写像変異は診断のどの軸 (backoff/validation政策/log書込) にも既開通の backoff/sort にも該当しない配置面。構造的に別 hole で yes。
- **c2**: sbomb_silo.cc 抜粋に実在する setThreadAffinity(thid) 呼び出しを指し実在構造に接続。llc_miss_rate が本系で応答する指標 (backoff微増/WAL増加) を根拠に、affinity 写像変異が llc_miss を動かすとの反証可能観測を指定。恒真文『改善する可能性』ではなく具体的観測量を指定。提案自体が恒真接近を懸念しているが、実在コード点と llc_miss 指定により最低限の実質性は満たす。yes。
- **c3**: mutation_type=code_fragment (写像変換のコード片)。yes。
**round_eligible: True**

## c4-15 (score-030)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断 silo-backoff-magnitude の3項目め『コミット時ログ書込の有効化 (on/off)』は WAL のオン/オフ切替。本提案は bomb_silo.cc worker_init の open(O_CREAT|O_TRUNC|O_WRONLY) 呼びと ftruncate、および wal() の sync 有無という I/O 経路パラメタ (フラグ集合・fdatasync・preallocation) を変異面とする。on/off の切替ではなく I/O 経路構成という別作用点の hole であり、軸内探索の言い換えでなく構造的に別 hole。提案自身も unknowns で重複懸念を挙げるが、作用点・骨格が診断の on/off と異なるため novel と判定。
- **c2**: 機序は stock_excerpts に実在する構造 (bomb_silo.cc の trans.logfile_.open(logpath, O_CREAT|O_TRUNC|O_WRONLY, 0644)・ftruncate、transaction.cc の wal() のコメントアウトされた fdatasync) を正確に指す。反証可能観測として『I/O 経路パラメタを変えると latency と llc_miss_rate の増分に地形が出る、write-heavy が最感度』を指定。実在構造への接続と反証可能観測ありで yes。
- **c3**: mutation_type は code_fragment (open フラグ集合・sync 呼びの挿入・preallocation の複合変異)。scalar 単体でなく構造変異。yes。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: スレッド affinity (thid→物理コア写像) は診断のどの attribution にも載っていない。llc_miss_rate の変化は backoff 待機と WAL I/O に帰属済みだが placement は独立要因として未登場。setThreadAffinity(thid) を別配置ポリシに差し替える別作用点の hole であり novel。
- **c2**: 機序は bomb_silo.cc worker_init の #ifdef Linux ガード下 setThreadAffinity(thid) という実在呼びを指す。反証可能観測として『thid→core 恒等写像を別配置に開けると llc_miss_rate に地形が出る (skew0.9/48thread の高競合下で LLC 共有トポロジを左右)』を指定。恒真文でなく特定の観測量の振る舞いを予言しており yes。
- **c3**: mutation_type は code_fragment (thid→core 割当関数の差し替え = 構造変異)。yes。
**round_eligible: True**

## c4-16 (score-035)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 軸は tuple.hh の tidword_ と body_ 間のキャッシュライン境界パディングという配置 (false sharing) 変異。診断3軸 (backoff スカラー・validation 政策・ログ書込) いずれの骨格でもなく、opened hole (backoff・writeset-sort) とも別の処理段・別領域 (tuple.hh、opened:false)。構造的に別 hole。
- **c2**: stock 実在構造 (Tuple の alignas(CACHE_LINE_SIZE) Tidword tidword_/body_、read_internal の lock spin、lockWriteSet の CAS) に繋がり、診断の llc_miss_rate『微増・cache 利得なし』を根拠にしている。反証可能観測を llc_miss_rate/coherence トラフィックとして指定 (パディングで動かなければ配置由来 miss 仮説が否定される)。
- **c3**: mutation_type=code_fragment (メモリ配置のコード片挿入/除去)。構造変異。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 軸は Tidword の lock ビットをバージョン語 (tid/epoch) と別ワードへ分離するビットフィールド構造変異。診断3軸・opened 2 hole いずれの骨格でもなく、tuple.hh の別状態・別作用点。構造的に別 hole。
- **c2**: stock 実在構造 (struct Tidword の union obj_ 単一64bit語、read_internal の (a)-(e) 再読取比較、lockWriteSet 単一語 CAS、validationPhase の check.lock) に繋がる。診断項目2の write-heavy abort 50.8→21.0% を根拠に、ロック churn とバージョン読取の結合緩和を仮説とし、反証可能観測を abort_rate/latency として指定。
- **c3**: mutation_type=code_fragment (ビットフィールド定義とその随伴コード変異)。構造変異。
**round_eligible: True**

## c4-17 (score-014)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 対象は cc/silo/include/silo_op_element.hh の WriteElement 値保持 (毎回ヒープ確保+memcpy) という別 hole。診断の既出軸は backoff (スカラー・include/backoff.hh)、validation の待たない政策、コミット時ログ書込 (WAL)、及び dead の writeset-sort (comparator)。いずれとも別の処理段・別作用点で、comparator 順序には明示的に触れないと宣言。既出でない。
- **c2**: stock 抜粋に実在する WriteElement コンストラクタの val_ptr_=make_unique+memcpy と writePhase の memcpy(get_val_ptr) を指して繋がる。反証観測を『abort 独立・書込比率比例・llc_miss に現れる throughput レバー』として指定 (診断のコミット時ログ書込項の形を援用)。この保持方式変更で throughput/llc_miss が動かなければ仮説否定 — 反証可能。
- **c3**: mutation_type は code_fragment (バッファ再利用・サイズ別分岐・遅延コピー等の構造変異)。scalar 単体でない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 対象は同ファイルの ReadElement 値保持フットプリント (val_[VAL_SIZE]・body_・memcpy(this->val_,...))。既出軸 (backoff/validation政策/ログ書込/writeset-sort) と別の処理段・別作用点で、comparator には触れない。既出でない。
- **c2**: ReadElement は stock 抜粋に実在する構造で、read_internal/validationPhase の tid 再突合経路も実在。反証観測を『read-set 保持コストが独立の throughput 効果 (llc_miss) を持つか実測』として明示。効果が無ければ否定 — 反証可能。ただし本人が構造類推止まりと認め、指定した char* val コンストラクタは現行未使用可能性 (unknowns 明記) だが構造自体は抜粋に実在するため幻覚ではない。
- **c3**: mutation_type は code_fragment (値保持を参照/圧縮/遅延に切替える構造変異)。scalar 単体でない。
**round_eligible: True**

## c4-18 (score-037)
### 提案 0 — 不適格 (c1=True c2=True c3=False)
- **c1**: 軸は ReclamationEpoch = cur_epoch - 2 の後退距離 (GC 解放境界) を振るもの。診断の 3 軸 (backoff 待機量・validation ロック政策・コミットログ書込) のいずれとも別の処理段 (siloLeaderWork の reclamation frontier / gc_records) を提案しており既出でない。
- **c2**: util.cc の siloLeaderWork 内 ReclamationEpoch 計算・transaction.cc の gc_records() の `rec->tidword_.epoch > ReclamationEpoch` 消費という実在構造を指し、lag→常駐フットプリント→llc_miss/latency 方向の地形という反証可能な観測を指定している。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。提案本文の unknowns 自身も headline 非対象 scalar と明記。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: chkEpochLoaded の全スレッド一致述語 (エポック前進ゲート) を定足数/時間上限政策に差し替える hole。診断 3 軸とも別の処理段 (GlobalEpoch 前進条件) で既出でない。
- **c2**: stock の util.cc chkEpochLoaded (全 ThLocalEpoch==nowepo 要求)・atomicStoreThLocalEpoch (validation 到達時のみ前進)・siloLeaderWork の atomicAddGE という実在構造に接続し、定足数部分化→latency 方向の地形という反証可能な観測を指定している。
- **c3**: mutation_type=code_fragment (構造変異) なので適格。
**round_eligible: True**

## c4-19 (score-040)
### 提案 0 — 不適格 (c1=True c2=True c3=False)
- **c1**: util.cc siloLeaderWork() 内の ReclamationEpoch 算出 (cur_epoch-2) と gc_records() の epoch しきい値解放は diagnostics の 3 帰属 (backoff / validation 待たない政策 / ログ書込) いずれにも無く、別の処理段 (reclamation lag) を突く新規 hole。既出軸の言い換えでない。
- **c2**: ReclamationEpoch = cur_epoch>2?cur_epoch-2:0 は util.cc に実在、gc_records() の rec->tidword_.epoch>r_epoch 解放も transaction.cc に実在。llc_miss_rate は attribution[2] の生きた indicator。write-heavy で terrain が非対称に立つ/立たないという反証可能な観測を指定。実在構造に接続。
- **c3**: mutation_type が scalar 単体。K の値をグリッド探索する機械的スカラー変異で構造変異でない → no。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: chkEpochLoaded() の all-N バリアと siloLeaderWork() の epoch 前進 gate 条件を可変合意ポリシに差し替える hole は diagnostics のどの帰属にも無く、別作用点 (epoch 前進バリア構造) を突く新規軸。既出軸の探索範囲内でない。
- **c2**: chkEpochLoaded の i=1..N 全一致走査・atomicStoreThLocalEpoch・siloLeaderWork の chkClkSpan AND gate は util.cc/atomic_tool.hh に実在。attribution[0] の ipc 崩壊 (待機で命令発行できない) に接続。遅延スレッドが epoch 前進を律速する仮説は、48thread で ThLocalEpoch 前進が均一なら否定される、という反証可能な観測を指定。因果未計測を honesty として明示しており幻覚でない。
- **c3**: mutation_type が code_fragment。バリア構造そのものの書換えで構造変異。yes。
**round_eligible: True**

## c5-00 (score-027)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal のステップ(a)施錠待ちスピンループ (`while (expected.lock) { ... }`) を変異点とする hole。診断の3軸 (backoff待機・validation中のno-wait政策・コミット時ログ書込) にも既開通2 hole (silo-writeset-sort=validationPhaseの施錠順序 / silo-backoff-magnitude=abort後待機) にも該当せず、読み取りフェーズ中の競合遭遇時点という別処理段の hole。既出でない。
- **c2**: transaction.cc 実在の read_internal スピンループ (loadAcquire でロックビットが立つ間 tidword を再ロード) を指し、『読み取り側の前進はライタの施錠保持時間に直接結合している』という反証可能な観測 (応答差替後に競合下 latency が不変なら仮説否定) に接地する。幻覚なし。
- **c3**: mutation_type は code_fragment (施錠中タプル遭遇時の応答方針差替え)。構造変異でありスカラー単体ではない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: util.cc の siloLeaderWork の epoch 前進条件 (`chkClkSpan(...)&&chkEpochLoaded()` で atomicAddGE) を変異点とする hole。診断3軸・既開通2 hole のいずれとも別の制御変数 (epoch cadence) で、別作用点。既出でない。
- **c2**: util.cc 実在の siloLeaderWork 前進条件・ReclamationEpoch=cur-2 に接地し、『epoch境界が commit 可視化・reclamation 世代を一斉に律速』という反証可能な主張 (cadence 変更で可視化/reclamation timing が不変なら否定) を示す。実在構造に繋がる。
- **c3**: mutation_type は code_fragment (前進タイミング条件の形の差替え)。構造変異。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: gc_records() の解放走査起動閾値を変異点とする hole。診断3軸・既開通2 hole のいずれにも該当せず、reclamation/gc 頻度という別作用点で既出でない。
- **c2**: transaction.cc 実在の gc_records() deque 走査と writePhase末尾・abort() の2呼出点に接地し、解放頻度が観測可能な差 (メモリ滞留 vs 一時的 throughput) を生むという反証可能な主張を示す。実在構造に繋がる。
- **c3**: mutation_type が scalar 単体 (解放走査を起動する蓄積件数のスカラー閾値)。既存の機械的グリッド探索で代替可能なため no。unknowns 内で境界事例と自認するが宣言型は scalar。
**round_eligible: True**

## c5-01 (score-056)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal 内の楽観読み lock 待ちスピンループを対象とする hole。診断の 3 軸 (backoff 待機量・validation の待たない政策・コミット時ログ書込) とも silo-writeset-sort とも別の処理段 (読み経路の楽観読み中ロック競合応答) を提案しており既出でない。
- **c2**: stock 抜粋 transaction.cc の read_internal に実在する `while (expected.lock) { expected.obj_ = loadAcquire(...) }` ループを名指しで指し、writePhase の storeRelease が立てる lock との関係に繋げている。反証は同ループの有無・形で可能と明示。
- **c3**: mutation_type は code_fragment (構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: util.cc siloLeaderWork の ReclamationEpoch = cur_epoch-2 のラグ定数を対象。診断軸・既開通 2 hole の探索範囲外の別サブシステム (回収遅延) で既出でない。
- **c2**: siloLeaderWork の実在リテラル 2 と gc_records の `rec->tidword_.epoch > r_epoch` 判定を名指しで指し反証可能。実在構造に接続。
- **c3**: mutation_type が scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: siloLeaderWork のグローバルエポック前進ゲート述語 (chkClkSpan && chkEpochLoaded) を差し替える hole。診断軸・既開通 hole と別位置・別作用点で既出でない。
- **c2**: stock に実在する siloLeaderWork のゲート述語・validationPhase Phase2 の epoch 比較 `get_tidword().epoch != check.epoch`・writePhase の commit-TID epoch 成分を指しており、前進条件変異でこれら粒度が動くと繋げ反証可能。
- **c3**: mutation_type は code_fragment (構造変異)。
**round_eligible: True**

## c5-02 (score-003)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の (a) 読取待機ループ `while (expected.lock)` の読取相スピン。診断3軸 (silo-backoff-magnitude=abort後の再試行前待機 backoff.hh / validation中の待たない政策 lockWriteSet / コミット時ログ書込) および silo-writeset-sort (validation の施錠順 comparator) のいずれとも実行相・対象状態が異なる別 hole。材料1の診断・骨格に読取相スピン待機軸は未出。
- **c2**: transaction.cc の read_internal に実在する `while (expected.lock) { ... }` 無制限スピンと外側 for での再読による local_extra_reads_ 加算構造を正しく指す。反証可能な観測として extra_reads / 読取遅延の変化を指定。実在構造への接続と反証観測あり。
- **c3**: mutation_type は code_fragment (待機の形=pause挿入・境界付きスピン・早期abort転換の構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は util.cc siloLeaderWork の `ReclamationEpoch = cur_epoch>2?cur_epoch-2:0` の回収 epoch 遅延定数。診断・既開通2 hole とは別の処理段 (epoch 回収)。材料1に該当軸は未出。
- **c2**: siloLeaderWork の ReclamationEpoch 計算と transaction.cc gc_records() の `rec->tidword_.epoch > r_epoch` break を正しく指す実在構造。回収タイミング変化として反証観測を指定。
- **c3**: mutation_type が scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
**round_eligible: True**

## c5-03 (score-029)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の for(;;) while(expected.lock){ loadAcquire } ロック待ちスピンの待機規律。材料1診断は backoff-magnitude・validation中の待たない政策・コミット時ログ書込・writeset-sort であり、読み取り相の対書き手スピン規律は別処理段・別作用点。既出軸の言い換えではない。
- **c2**: stock の read_internal スピンと writePhase の memcpy(get_val_ptr)+storeRelease(maxtid) という実在構造に接続。反証可能な観測『高 write ratio/skew 動作点でスピン規律に throughput が非感応なら仮説は誤り』を指定。
- **c3**: mutation_type=code_fragment(構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の epoch 前進スパン閾値は診断の3軸(backoff/待たない政策/ログ書込)いずれとも別位置・別処理段。ただし既存 FLAGS_epoch_time チューニングと外形が近い点は留保。
- **c2**: siloLeaderWork の chkClkSpan+chkEpochLoaded→atomicAddGE、validationPhase の atomicStoreThLocalEpoch、writePhase の commit TID epoch という実在構造に接続。反証観測『閾値に throughput 非感応なら誤り』を指定。
- **c3**: mutation_type=scalar 単体。既存グリッド探索で代替可能のため不適格。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の ReclamationEpoch ラグ量(リテラル2)と gc_records の epoch 境界は GC 回収窓であり診断3軸のいずれとも別機序・別位置。
- **c2**: siloLeaderWork の ReclamationEpoch=cur_epoch-2、gc_records() の rec->tidword_.epoch>r_epoch 判定、writePhase DELETE 経路の gc_records_.push_back という実在構造に接続。反証観測『delete を含む workload で回収ラグに throughput/メモリ非感応なら誤り』を指定。
- **c3**: mutation_type=scalar 単体。既存グリッド探索で代替可能のため不適格。
**round_eligible: True**

## c5-04 (score-009)
### 提案 0 — 不適格 (c1=False c2=True c3=True)
- **c1**: hole位置は lockWriteSet() の `if (expected.lock)` 施錠済みタプル遭遇時の応答分岐 (NO_WAIT_LOCKING_IN_VALIDATION の即abort / NO_WAIT_OF_TICTOC の unlock→goto retry)。これは診断2つ目『validation 中のロック競合に対する 2 種の待たない政策の選択』が指す作用点そのもの。同じ処理段・同じ作用点で応答政策を変異させる提案であり、既出軸の探索範囲内 (第三の有界待機オプションを足すのみ) と判定。
- **c2**: lockWriteSet の実在する二極分岐 (即abort/無限retry)・validationPhase の sort・write_set_ 走査に正しく接続し、反証可能観測『この分岐通過に起因する abort 計数』を指定している。stock 実在構造に繋がる。
- **c3**: mutation_type=code_fragment (構造変異)。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: hole位置は read_internal() の `while(expected.lock)` 施錠クリア待ちスピンの刻み方 (pause挿入・再読込間隔・有界化)。診断は backoff-magnitude・validation lock policy・commit log write・writeset-sort のみで、read フェーズのスピン規律は別の処理段・別作用点。既出軸に含まれない。
- **c2**: read_internal の実在する密スピンと writePhase の memcpy(VAL_SIZE)→storeRelease(maxtid) クリティカル区間に接続し、反証可能観測 local_extra_reads_ / read 遅延計数を指定。stock 実在構造に繋がる。
- **c3**: mutation_type=code_fragment (構造変異)。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole位置は siloLeaderWork() の ReclamationEpoch 遅延距離リテラル 2。診断のいずれの軸 (backoff・validation policy・log write・writeset-sort) にも該当せず、gc 回収エポック遅延は別作用点。既出でない。
- **c2**: siloLeaderWork の実在 `ReclamationEpoch = cur_epoch>2?cur_epoch-2:0` と gc_records() の `rec->tidword_.epoch > r_epoch` 閾判定、writePhase DELETE→gc_records_ push に正しく接続し、delete 含む workload の解放/メモリ挙動という反証可能観測を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能のため不適格。
**round_eligible: True**

## c5-05 (score-007)
### 提案 0 — 不適格 (c1=False c2=True c3=True)
- **c1**: 材料1診断 silo-backoff-magnitude の attribution 2 が『validation 中のロック競合に対する 2 種の待たない政策の選択』を既出設計選択として明示。これは stock lockWriteSet の `if (expected.lock)` 分岐（NO_WAIT_LOCKING_IN_VALIDATION=即abort / NO_WAIT_OF_TICTOC=部分解錠して goto retry）そのもの。提案 1 の hole 位置はこの同一作用点であり、code_fragment 化して政策変種を追加しても骨格・作用点は既出軸と同一の軸内探索の言い換えに当たる。
- **c2**: mechanism は stock lockWriteSet の衝突応答内側ループという実在構造を指し、『競合を上げても挙動が平坦なら地形なし』という反証可能な観測を指定している。
- **c3**: mutation_type=code_fragment（構造変異）。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: TxExecutor::read_internal() の read フェーズ無制限 busy-spin 待機ループ（`while (expected.lock) {...}`）は、診断に載る backoff・validation ロック政策・WAL のいずれとも別処理段（read phase の待機）で、材料1診断に該当なし。別作用点。
- **c2**: mechanism は stock read_internal に実在する writer ロック中の busy-spin ループを指し、『writer 混入を上げても read latency が平坦なら地形なし』という反証可能観測を指定。
- **c3**: mutation_type=code_fragment（構造変異）。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() の `if (log_set_.size() > LOGSET_SIZE/2)` フラッシュ閾値は、診断 attribution 3 の『コミット時ログ書込の有効化 (on/off)』とは別作用点（バッチ束ね量の閾値であって on/off ではない）。stock wal に実在。
- **c2**: mechanism は stock wal のフラッシュ閾値判定という実在構造を指し、『WAL 無効なら本経路が通らず地形なし』という反証可能観測を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存グリッド探索で代替可能のため no。
**round_eligible: True**

## c5-06 (score-032)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole 位置は cc/silo/transaction.cc の read_internal の読取り前ロック待ちスピン `while (expected.lock) { expected.obj_ = loadAcquire(...); }`。材料1診断の既出軸は silo-backoff-magnitude (backoff.hh の abort 後再試行待ち)・validation 中の待たない政策 (lockWriteSet)・commit 時ログ書込であり、いずれも読取り phase のスピン待ちとは別処理段・別作用点。edit_surface_map の既開通 hole (writeset-sort comparator / backoff-magnitude) とも別。構造的に別 hole。
- **c2**: read_internal の当該 while ループは stock 抜粋 (transaction.cc) に実在し、Tidword が alignas(CACHE_LINE_SIZE) である点も tuple.hh に実在。_mm_pause もバックオフも無い連続 loadAcquire がコヒーレンストラフィックを生む機序は実在構造に接続。反証可能な観測として『施錠タプルへの読取り衝突率が高い構成で待機ペーシングが llc_miss/ipc/throughput を変えるか』が指定でき、変化しなければ仮説否定 — 反証可能。
- **c3**: mutation_type は code_fragment (構造変異)。適格。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は util.cc の siloLeaderWork 内 `ReclamationEpoch = cur_epoch > 2 ? cur_epoch - 2 : 0;` のリテラル遅延幅。材料1診断・edit_surface_map の既開通 hole いずれとも別処理段 (epoch ベース回収の安全マージン)。構造的に別 hole。
- **c2**: siloLeaderWork の ReclamationEpoch 計算と gc_records() の `rec->tidword_.epoch > r_epoch` 判定はともに stock 抜粋に実在し、削除レコードの reclaim 時期がこのリテラルに直結する機序は実在構造に接続。反証可能な観測として delete/insert 比率の高い workload でアロケータ圧・性能が変わるかが指定できる。
- **c3**: mutation_type は scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため不適格。
**round_eligible: True**

## c5-07 (score-053)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal の (a) 直後のロック待ちスピンループ (`for(;;){while(expected.lock)...}`) を待機方式の hole として開ける提案。診断の alive 軸は silo-backoff-magnitude (abort 後の再試行前待機=backoff.hh) と validation 中の no-wait 政策 (lockWriteSet) とログ書込 on/off であり、read フェーズの前進待ちスピンはいずれとも別の処理段・別作用点。構造的に別 hole で既出でない。
- **c2**: stock 抜粋 transaction.cc の read_internal に実在するスピンループと writePhase の storeRelease までロック保持する構造を正しく指し、反証可能な観測 (低競合・reader がロック済み tuple にほぼ当たらない workload では throughput 差が出ないはず) を明記。恒真文でなく実在構造に接続。
- **c3**: mutation_type が code_fragment (待機方式の構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の ReclamationEpoch ラグ定数=GC/メモリ回収面で、診断の 3 軸いずれとも別機構・別作用点。既出でない。
- **c2**: util.cc の siloLeaderWork と transaction.cc の gc_records() の実在構造を指し、delete/insert チャーンが無い workload ではラグ値非感応という反証可能観測を示す。ただし c3 で失格。
- **c3**: mutation_type が scalar 単体 (ラグ定数のみ)。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() のフラッシュ発火閾 (LOGSET_SIZE/2) は WAL の IO バッチ化面で、診断のログ書込 on/off 軸 (有効化そのもの) とは別 hole (閾値による束ね方)。既出でない。
- **c2**: transaction.cc の wal() に実在する log_set_ 蓄積と閾超え一括 write の構造を指し、WAL 無効ビルドで非感応という反証可能観測を示す。ただし c3 で失格。
- **c3**: mutation_type が scalar 単体 (フラッシュ閾のみ)。スカラー単体は no。
**round_eligible: True**

## c5-08 (score-048)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 対象は read_internal の楽観読み (a) ステップの `while (expected.lock) { loadAcquire }` 純スピンの待ち方。材料1 diagnostics の3軸は abort後再試行バックオフ (silo-backoff-magnitude)・validation 中の待たない政策・コミット時ログ書込であり、dead軸は施錠順 comparator。いずれも読み位相のロック待ちスピンとは別処理段・別作用点であり、構造的に別 hole。
- **c2**: transaction.cc の read_internal の for(;;)/while(expected.lock) スピンと、writePhase UPDATE の memcpy→storeRelease によるロック保持窓、tidword_ の同一キャッシュライン loadAcquire という実在構造を正しく指しており幻覚なし。VAL_SIZE 比例の保持窓を読み手がスピン消費しキャッシュライン競合が変わるという予測で、latency/占有時間・競合という観測量の変化として反証可能 (待ち方変異で latency/競合が動かなければ否定)。
- **c3**: mutation_type は code_fragment (待機ポリシー差込の構造変異)。scalar 単体でない。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: 対象は util.cc siloLeaderWork の `cur_epoch - 2` の定数2 (回収猶予マージン)。diagnostics のどの軸 (backoff量・validation政策・ログ書込) にも既開通軸 (施錠順) にも該当せず、gc回収境界という別作用点。
- **c2**: writePhase DELETE の gc_records_.push_back、gc_records() の `epoch > r_epoch` break、siloLeaderWork の ReclamationEpoch=cur_epoch-2 という実在構造を正しく指す。deque長とfree発火時期の変化として反証可能な観測を指定。
- **c3**: mutation_type が scalar 単体 (マージン値のみ変異)。構造変異との複合でない。提案自身も「探索補助限定・scalar型」と明記。基準によりスカラー単体は no。
**round_eligible: True**

## c5-09 (score-025)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal() の (a) 段ロック待ちスピン (read phase・validation 前)。診断の 3 軸は silo-backoff-magnitude (abort 後再試行待機)、validation 中ロック競合の 2 政策、コミット時ログ書込であり、read 経路のロッククリア待ちスピンはいずれとも別の処理段・別作用点。既出でない。
- **c2**: read_internal() の `while (expected.lock) { loadAcquire(...) }` タイトスピンと writePhase の storeRelease が同一 tidword を叩き合う構造 (stock に実在) を指し、contention 下 read latency という反証可能観測を指定。
- **c3**: mutation_type=code_fragment。
### 提案 1 — 不適格 (c1=False c2=True c3=True)
- **c1**: hole は lockWriteSet() の `if (expected.lock)` 競合応答分岐 (NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC の 2 政策)。診断の attribution『validation 中のロック競合に対する 2 種の待たない政策の選択』が正にこの作用点を扱っており、同じ競合応答分岐で待機/諦めの政策を挟み替える提案は既出軸の探索範囲内の変異。既出のため no。
- **c2**: lockWriteSet() の施錠競合分岐 (stock 実在) を指し、abort 率と施錠待ち時間のトレードオフという反証可能観測を指定。ただし c1 で不適格。
- **c3**: mutation_type=code_fragment。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の ReclamationEpoch=cur_epoch-2 の遅延定数を対象とする GC 回収タイミングの hole は診断 3 軸のいずれとも別作用点で既出でない。
- **c2**: gc_records() の `epoch > ReclamationEpoch` 閾値と siloLeaderWork の遅延定数 (共に stock 実在) を指し、メモリ再利用局所性という反証可能観測を指定。ただし c3 で不適格。
- **c3**: mutation_type=scalar 単体。スカラー単体は機械的グリッド探索で代替可能のため no。
**round_eligible: True**

## c5-10 (score-001)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は cc/silo/transaction.cc の read_internal 冒頭 (a) の `for(;;){ while(expected.lock){ loadAcquire } }` スピン待機。診断の既出軸は silo-backoff-magnitude (abort後の再試行前backoff・include/backoff.hh) と silo-writeset-sort (施錠順序comparator)。read フェーズのインライン待機点は別の処理段・別の作用点で、既出軸の軸内変異ではない。
- **c2**: read_internal の while(expected.lock) loadAcquire ループと施錠側の storeRelease(tuple->tidword_) は stock (transaction.cc) に実在。機序は tidword_ の同一 cache line を読み手がタイトスピンし施錠→解放の coherence 往復に干渉するという具体的因果で、待機戦略 (pause挿入等) 差替時に throughput/ipc/llc が動くかで反証可能。実在構造に接続し観測で否定しうる。
- **c3**: mutation_type は code_fragment (構造変異) で適格。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の `ReclamationEpoch = cur_epoch>2 ? cur_epoch-2 : 0` の epoch ラグ定数。診断3軸 (backoff / validation待たない政策 / ログ書込on-off) いずれとも別の GC 猶予支配点で、gc_records の物理delete条件に繋がる別 hole。
- **c2**: gc_records() の `rec->tidword_.epoch > r_epoch` break と r_epoch=ReclamationEpoch は stock (transaction.cc/util.cc) に実在。ラグ縮小で早期解放→use-after-free/メモリ保持減という反証可能な観測を指定。実在構造に接続。
- **c3**: mutation_type が scalar 単体。既存の機械的グリッド探索で代替可能なため不適格。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: wal() の `if (log_set_.size() > LOGSET_SIZE/2)` の flush 閾値。診断のログ軸は『コミット時ログ書込の有効化 (on/off)』であり、書込頻度/滞留量のトレードオフ閾値は別 hole。silo-writeset-sort とも関数・対象量が異なる。
- **c2**: wal() の log_set_ 蓄積と logfile_.write まとめ書き、閾値判定は stock (transaction.cc) に実在。閾値変化で write回数と滞留量が動く反証可能な観測を指定。ただし #if WAL 下でのみ有効という制約も自認しており実在構造に接続。
- **c3**: mutation_type が scalar 単体。スカラー単体は不適格。
**round_eligible: True**

## c5-11 (score-052)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の (a) ステップ内 `while (expected.lock) { expected.obj_ = loadAcquire(...); }` の読み取り側スピン地点。診断の3軸 (backoff=abort後再試行待機 / validation中の待たない政策=lockWriteSet / コミット時ログ書込) のいずれとも別処理段。読み取りフェーズでのインプレース待機刻みは診断・既開通hole (silo-writeset-sort/silo-backoff-magnitude) いずれにも未出の別作用点。
- **c2**: stock の transaction.cc read_internal に実在する busy-reload ループを名指し、待機刻みが tidword_ キャッシュライン再読込頻度を決めるという実構造への接続を持つ。反証観測「read_internal 以外に読み取り側待機地点があれば偽」を明示。恒真文でなく反証可能。
- **c3**: mutation_type=code_fragment。待機ポリシをコード片で差し替える構造変異。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: ReclamationEpoch のマージンリテラル 2 は診断・既開通hole いずれにも未出。siloLeaderWork の実在減算式を指す別作用点。
- **c2**: util.cc の `ReclamationEpoch = cur_epoch > 2 ? ...` と transaction.cc gc_records() の `rec->tidword_.epoch > r_epoch` 閾値という実在構造に接続し、反証観測「回収閾値を決める他の定数があれば偽」を指定。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。提案自身も headline 非対象 scalar と自己申告。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は searchReadSet/searchWriteSet の O(n) 線形走査を補助索引に置換。診断3軸・既開通hole いずれにも未出のローカルセット探索構造という別作用点。
- **c2**: stock transaction.cc に実在する searchReadSet/searchWriteSet の線形走査ループ、read/update/insert/delete_record からの呼び出し、common.hh の batch_max_ope 既定1000 に接続。反証観測「read_set_/write_set_ の探索が他所にもあり索引化が部分的にしか効かない場合」を指定。
- **c3**: mutation_type=code_fragment。走査方式を索引探索へ置換する構造変異。
**round_eligible: True**

## c5-12 (score-000)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の読み取りフェーズ内スピン待機ループ `while (expected.lock) { ... }`（transaction.cc の read_internal に実在）。診断の既出軸は backoff.hh の abort 後再試行待機(silo-backoff-magnitude)、lockWriteSet の待たない政策(validation lock 競合)、コミット時ログ書込、writeset-sort であり、読み取りフェーズの施錠中スピン応答はいずれとも別の処理段・別作用点。既出軸の言い換えではない。
- **c2**: writePhase が lockWriteSet で tidword_.lock=1 を立て memcpy〜storeRelease まで保持する実在構造と、read_internal の pause 無し・上限無しビジースピン(共に stock 抜粋に実在)へ接続。反証可能な観測として読み取りレイテンシ/IPC/abort 率を挙げ、待機構造を差し替えた際にこれらが動かなければ仮説否定という向き。実在構造への接続と観測量指定を満たす。
- **c3**: mutation_type は code_fragment(構造変異)。スピン本体の pause 挿入・上限＋楽観再読復帰・待機構造差し替えを許すコード片軸。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は wal() の `if (log_set_.size() > LOGSET_SIZE / 2)` フラッシュ閾値(transaction.cc に実在)。診断の『コミット時ログ書込の有効化(on/off)』は WAL 有効/無効の帰属であり、バッチ蓄積閾値の量的制御点とは別 hole。既出軸の再掲ではない。
- **c2**: wal() の LogRecord append と閾値超過時の logfile_.write 一括書込(stock 抜粋に実在)、latest_log_header_.logRecNum_ 関係へ接続。I/O 償却 vs コミット遅延の観測でスループット/latency がどう振る舞えば否定されるかを示す。実在構造接続を満たす。
- **c3**: mutation_type が scalar 単体。閾値の数値選択のみで既存の機械的グリッド探索で代替可能。構造変異との複合でない。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は siloLeaderWork(util.cc)の `ReclamationEpoch = cur_epoch > 2 ? cur_epoch - 2 : 0` の lag 定数。診断の既出軸(施錠順序・再試行間隔・ログ書込)と別の処理段(GC 回収エポック窓)。既出軸内の言い換えではない。
- **c2**: gc_records() の `rec->tidword_.epoch > r_epoch` 回収停止条件と siloLeaderWork の lag 定数(共に stock 抜粋に実在)へ接続。lag を安全下限未満にすると use-after-free、メモリ保持窓 vs 回収積極性の観測で否定可能。実在構造接続を満たす。
- **c3**: mutation_type が scalar 単体。lag 定数の数値選択のみでグリッド探索代替可能、構造変異との複合でない。
**round_eligible: True**

## c5-13 (score-008)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal の step(a) スピンループ (`while (expected.lock)` / `expected == check`) を対象とする hole。既開通 hole は silo-writeset-sort (lockWriteSet の comparator) と silo-backoff-magnitude (backoff.hh の待機量)、診断の validation 待たない政策も lockWriteSet 内。本提案は read フェーズのロック待ちスピンという別処理段・別作用点で、構造的に別 hole。
- **c2**: read_internal の loadAcquire 密ループと writePhase の UPDATE 経路 `memcpy(...body_.get_val_size())` はいずれも stock 抜粋に実在。ライタが値コピー保持中の tuple にヒットしたリーダがヒントなしでスピンするという実構造への接続があり、read latency・extra_reads 計数 (local_extra_reads_) の差として反証可能な観測を指定。
- **c3**: mutation_type=code_fragment (スピン方式の構造変異)。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: searchReadSet/searchWriteSet の線形走査を補助構造化する hole。既開通 2 hole (comparator・backoff) とも診断の政策とも別位置。silo-writeset-sort が write_set 全体ソートなのに対し、これはローカルセットの key 検索経路で構造的に別 hole。
- **c2**: searchReadSet/searchWriteSet の毎操作線形走査は transaction.cc 抜粋に実在、common.hh の batch_max_ope=1000 も実在。大 Tx でセット長比例の探索コスト増という実構造に接続し、per-tx latency がセット長に対しどう伸びるかを反証可能な観測として指定。
- **c3**: mutation_type=code_fragment (探索補助構造の構造変異)。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork の epoch 前進閾値を対象とする hole。util.cc は未開通領域で既開通 2 hole とは別位置・別対象量。構造的に別 hole。
- **c2**: siloLeaderWork の閾値判定・chkEpochLoaded・ReclamationEpoch=cur-2、gc_records の `rec->tidword_.epoch > r_epoch` はいずれも stock 抜粋に実在。回収滞留量とスループット/メモリ挙動の差として反証可能な観測を指定。
- **c3**: mutation_type が scalar 単体であり、skeleton も「閾値をスカラー hole 化」と明記。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
**round_eligible: True**

## c5-14 (score-023)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 材料1診断の既出軸は silo-backoff-magnitude (backoff.hh の abort 後再試行前待機) と silo-writeset-sort (dead, comparator)。本提案は transaction.cc の read_internal() ロック待ちスピンループ (別処理段・別作用点) に待機挿入する構造的に別の hole。既出軸の言い換えではない。
- **c2**: stock 抜粋 read_internal の `while(expected.lock){ expected.obj_=loadAcquire(tuple->tidword_.obj_); }` と writePhase の storeRelease に実在的に繋がる。反証可能な観測: 競合の無い workload ではスピンに入らず差が出ない、を指定。診断非参照だが stock 実在構造への接続と反証観測があり適格。
- **c3**: mutation_type=code_fragment (構造変異)。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: siloLeaderWork() の ReclamationEpoch lag 定数 2。診断3軸のいずれにも該当せず、別位置・別状態 (GC 猶予距離) の hole。
- **c2**: stock util.cc の `ReclamationEpoch = cur_epoch>2?cur_epoch-2:0` と transaction.cc gc_records() の `rec->tidword_.epoch > r_epoch` に実在的に繋がる。反証観測 (削除/挿入がほぼ無い workload では gc_records_ が育たず無影響) を指定。ただし c3 不適格のため提案全体は不適格。
- **c3**: mutation_type=scalar 単体。既存の機械的グリッド探索で代替可能なため no。提案本文も『scalar のため段6 headline 非対象ラベルが自動付与』と自認。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: read()/scan() 冒頭のローカルセット走査順序 (searchReadSet/searchWriteSet の順・短絡)。診断3軸 (backoff/comparator/log書込) のいずれとも別の作用点で構造的に別 hole。
- **c2**: stock transaction.cc の searchReadSet/searchWriteSet 線形走査と read() の呼び出し順序に実在的に繋がる。反証観測 (read_set_/write_set_ が小さい workload では走査長差が無視でき無影響) を指定。
- **c3**: mutation_type=code_fragment (走査順・短絡の構造変異)。
**round_eligible: True**

## c5-15 (score-047)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 穴は read_internal の read フェーズのロック中 busy-reload 待機 (`while (expected.lock)`)。診断の既出軸は silo-backoff-magnitude (include/backoff.hh の abort 後再試行前待機)、コミット時ログ書込、validation 中の待たない政策 (lockWriteSet)、及び dead の writeset-sort であり、いずれも別の処理段・別の作用点。read フェーズの spin 待機は構造的に別の hole。
- **c2**: transaction.cc の read_internal に実在する `for(;;){ while(expected.lock){...} ...}` と、writePhase が UPDATE/DELETE の memcpy 区間 lock=1 を storeRelease まで保持する実構造を正しく指し、読み手 spin 時間が writer クリティカルセクション長に直結する機序を述べる。反証観測『低競合構成では変異ほぼ無効=地形なし』を指定。実在構造+反証可能で実質的。
- **c3**: mutation_type=code_fragment (待機カウンタ+応答分岐の構造変異)。scalar 単体でない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: 穴は util.cc の siloLeaderWork の epoch 前進 gate 判定条件。診断の既出 3 軸 (backoff・log 書込・validation 待たない政策) と dead の writeset-sort のいずれとも別の処理段。FLAGS_epoch_time のスカラー振りは対象外と明示し構造判定を変異範囲とする点も既存グリッド探索の言い換えでない。構造的に別の hole。
- **c2**: util.cc の siloLeaderWork に実在する `chkClkSpan(...)&&chkEpochLoaded()` の連言 gate、atomicAddGE、ReclamationEpoch=cur_epoch-2、transaction.cc の gc_records が ReclamationEpoch を参照する実構造を正しく指す。反証観測『epoch 前進が律速でない構成では差が出ない=地形なし』を指定。実在構造+反証可能で実質的。
- **c3**: mutation_type=code_fragment (前進判定の構造変異)。スカラーフラグ振りを明示的に対象外にしており scalar 単体でない。
**round_eligible: True**

## c5-16 (score-013)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は cc/silo/transaction.cc の read_internal 内、施錠中タプルに遭遇したときのリーダ側スピン応答 (`while (expected.lock) { loadAcquire }`)。材料1 diagnostics の 3 軸は abort後 backoff (backoff.hh)・validation中の待たない政策 (lockWriteSet)・コミット時ログ書込であり、いずれも read phase のスピン応答段ではない。edit_surface の既開通 hole (writeset-sort comparator・backoff-magnitude) とも別の処理段。構造的に別 hole で yes。
- **c2**: mechanism は transaction.cc の read_internal の実在するスピンループ (無制限の loadAcquire 再ロード) を正しく指し、writePhase の memcpy+storeRelease 保持区間との結合を述べる。反証可能な観測として書き込み競合下のリーダ経路サイクル/ipc の地形を指定 (待機戦略変更で throughput/サイクルが動かなければ否定)。実在構造への接続あり。yes。
- **c3**: mutation_type は code_fragment (構造変異)。yes。
### 提案 1 — 不適格 (c1=True c2=True c3=False)
- **c1**: hole は util.cc siloLeaderWork の `ReclamationEpoch = cur_epoch>2 ? cur_epoch-2 : 0` の遅延定数 2。diagnostics 3 軸・既開通 2 hole いずれも GC 再利用窓に触れておらず、構造的に別の hole。yes。
- **c2**: mechanism は transaction.cc の gc_records() `if (rec->tidword_.epoch > r_epoch) break;` と ReclamationEpoch を実在構造として正しく指し、削除/挿入下のメモリ footprint・gc_records_ deque 滞留量という反証可能観測を指定。実在構造接続あり。yes。
- **c3**: mutation_type=scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能のため no。提案自身も scalar と明記。
**round_eligible: True**

## c5-17 (score-042)
### 提案 0 — 不適格 (c1=True c2=True c3=False)
- **c1**: 材料1診断は silo-backoff-magnitude・silo-writeset-sort の2軸のみ。本提案は util.cc siloLeaderWork の ReclamationEpoch オフセット (gc reclamation 経路) という別位置の hole で既出でない。
- **c2**: transaction.cc の gc_records() の `rec->tidword_.epoch > ReclamationEpoch` と util.cc の `ReclamationEpoch = cur_epoch > 2 ? cur_epoch - 2 : 0` という実在構造に繋がり、delete/insert チャーンの無いワークロードでは N が無効という反証可能な観測を指定。
- **c3**: mutation_type が scalar 単体。スカラー単体は既存の機械的グリッド探索で代替可能なため no。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: read_internal() のロック待ちスピン (読取側の待ち点) は診断2軸 (書込側施錠順序・abort後待機) と構造的に別の作用点で既出でない。
- **c2**: transaction.cc read_internal の `while (expected.lock) { loadAcquire(...) }` スピンと (e) 再チェック `expected == check` という実在構造に接続。write比率>0・contention 構成でのみ効き read-only では不変という反証可能な観測を指定。
- **c3**: mutation_type が code_fragment (待機規律の構造変異)。
### 提案 2 — 不適格 (c1=True c2=True c3=False)
- **c1**: 診断の『ログ書込の有効化 (on/off)』とは別に、wal() の flush 閾値 `log_set_.size() > LOGSET_SIZE/2` という batch 粒度の別 hole。既出の2 hole とは別位置。
- **c2**: transaction.cc wal() の log_set_ 蓄積と `logfile_.write` 1回発行、LOGSET_SIZE/2 閾値という実在構造に接続。#if WAL 有効時のみ効くという反証可能な観測を指定。
- **c3**: mutation_type が scalar 単体。スカラー単体は no。
**round_eligible: True**

## c5-18 (score-006)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は read_internal の `while(expected.lock){...}` リロードと (e) 再チェックループ (transaction.cc の read_internal に実在)。診断の既出軸は silo-backoff-magnitude (abort後の試行間待機)・validation中のロック競合の待たない政策 (lockWriteSet)・コミットログ書込・silo-writeset-sort であり、いずれもリーダ側 read フェーズのスピン規律とは別の処理段。構造的に別 hole。
- **c2**: backoff.hh の pause 付き待機ループと対比した read_internal の無 pause 密リロード・(e) 再チェック・local_extra_reads_ (ADD_ANALYSIS) はすべて stock 抜粋に実在。反証可能な観測として『偏った write 重負荷下で read 遅延・extra-reads が待機規律に応答する地形』を指定。実在構造に接続し観測量を明示。
- **c3**: mutation_type=code_fragment (待機規律の構造変異)。scalar 単体でない。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は searchReadSet/searchWriteSet の線形 vector 走査の索引化 (transaction.cc に実在)。診断の既出軸 (backoff・validationロック政策・コミットログ・writeset-sort) はいずれも競合/順序/IO 系であり、per-tx の局所集合探索 CPU コストは別作用点。構造的に別 hole。
- **c2**: searchReadSet/searchWriteSet の線形走査と read/update/insert/delete/scan からの呼出は stock 実在。common.hh の batch_max_ope=1000 も実在。O(R^2) の per-tx CPU 仕事という機序は実在構造に接続し、反証可能な観測 (大 R batch tx で競合とは独立に per-tx 探索コストが変化) を指定。
- **c3**: mutation_type=code_fragment (索引付き探索への構造差替え・補助メンバ追加)。scalar 単体でない。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: hole は siloLeaderWork の epoch 前進述語と ReclamationEpoch 算出 (util.cc に実在)。既出軸のいずれ (backoff・ロック政策・ログ・writeset-sort) とも別 subsystem (epoch cadence / GC 回収窓)。単なる FLAGS_epoch_time チューニングと区別し論理 hole として scope。構造的に別 hole。
- **c2**: siloLeaderWork の chkClkSpan/chkEpochLoaded 二重ゲート・ReclamationEpoch=cur-2・writePhase の tid_c.epoch=ThLocalEpoch[thid_]・gc_records() はすべて stock 抜粋に実在。epoch cadence が commit-tid 粒度と GC 回収ラグを結合するという機序は実在構造に接続し、回収圧と epoch 境界バッチングの変化を反証可能な観測として指定。
- **c3**: mutation_type=code_fragment (前進述語・回収窓導出の論理変異)。scalar 単体でない。
**round_eligible: True**

## c5-19 (score-041)
### 提案 0 — 適格 (c1=True c2=True c3=True)
- **c1**: 診断の3軸は abort後バックオフ (silo-backoff-magnitude)・validation中のロック競合待たない政策・コミット時ログ書込。本提案は read_internal の (a) ロック待ちスピン (`while(expected.lock){...}`) という読み経路の別待機点を hole とする。診断のどの軸とも別処理段の作用点で、既開通 hole (writeset-sort comparator / backoff スカラー) の変異範囲にも入らない。
- **c2**: stock 抜粋 transaction.cc の read_internal に当該スピンループ (無停止 loadAcquire 再ロード) が実在し、機序はその位置のキャッシュコヒーレンス往復を指す。反証観測『変異前後で性能不変なら棄却』を明示。実在構造に接続し反証可能。
- **c3**: mutation_type は code_fragment (構造変異)。
### 提案 1 — 適格 (c1=True c2=True c3=True)
- **c1**: siloLeaderWork の epoch 前進ゲートと ReclamationEpoch 算出を hole とする。診断3軸 (backoff/validation政策/ログ書込) と既開通2 hole はいずれも epoch 制御に触れず、別処理段・別作用点。
- **c2**: stock 抜粋 util.cc の siloLeaderWork に epoch 前進条件 (chkClkSpan && chkEpochLoaded → atomicAddGE) と ReclamationEpoch = cur_epoch-2 が実在。機序はその GC 境界/validation 直列化窓への帰属を指す。反証観測『オフセット/条件を変えて計測不変なら棄却』を明示。
- **c3**: mutation_type は code_fragment。
### 提案 2 — 適格 (c1=True c2=True c3=True)
- **c1**: gc_records() の起動カデンス (毎コミット/毎 abort の無条件 deque 走査) を hole とする。診断3軸・既開通2 hole は reclamation 消費頻度に触れず、提案1 (epoch/reclamation 値決定) とも消費側で別作用点。
- **c2**: stock 抜粋 transaction.cc に gc_records() 本体 (epoch>r_epoch ガードの front 走査) と writePhase末尾・abort での無条件呼び出しが実在。機序は per-tx 固定オーバーヘッドを指し、反証観測『カデンス変更で計測不変なら棄却』を明示。
- **c3**: mutation_type は code_fragment。
**round_eligible: True**
