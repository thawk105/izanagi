## 一次資料との照合結果

以下の主張は実物と一致した。

- 登録済み calibration は2件で、`bnode011` と `bnode048`。平均はそれぞれ `3,918,457.8` と `3,848,941.0 TPS`、前者を分母にした差は `1.7740857%`。
- 2件の build argv は26要素中4要素だけが異なり、すべて `/scr/0_<job>.nqsv/...` 配下の source/build/CMake prefix の違い。
- staging/configure 記録は `libgflags.a` と `libglog.a` を指し、binary symbol にも内部 gflags symbol が存在する。
- `certify` は受理後、`registered/calibration-<digest16>.json` へ自動 publish する。
- durable root の既定許可先は repo の `output/` だけで、policy オブジェクトは注入可能。
- 保存済みの実 `qstat_queue_detail.stdout` は `Exclusive submit = OFF`。
- raw record から NumPy で再計算した反復番号との Pearson 相関は `bnode011=-0.2985375143`、`bnode048=-0.6589512241`。文書の `−0.30 / −0.66` と一致する。

---

### 1

**severity:** blocker

**主張:** `N=12, R=12` は、文書が primary とする同時保守的な `τ_U` に対して「1ノード欠落後も80% assurance」を満たさない。

**根拠:** 文書の設計式が用いる κ の片側95% F 上限だけなら assurance は、12ノードで `0.876883`、11ノードで `0.838506` だった。一方、primary analysis が要求する κ の97.5% F 上限と `σ_e` の97.5% χ²上限を組み合わせ、NumPyで帰無分布を2,000,000回生成したところ、`τ_U < 0.006` の確率は12ノードで `0.618141`、11ノードで `0.553109` だった（Monte Carlo SE 約 `0.000344`）。これは μ を既知とした楽観的な計算である。

**成果物影響:** 80% assurance を満たすと称した本走が、実際には約55%の欠落後 assurance しか持たず、失敗しても設計根拠を満たした測定とは言えない。

**提案:** primary の正確な `τ_U` 定義そのもので N/R を再探索し、κ・`σ_e`・必要なら μ の不確実性まで含めた再現可能な設計計算を protocol に固定する。

---

### 2

**severity:** blocker

**主張:** `12×12` を「minimum design」とする主張は偽であり、目的関数も定義されていない。

**根拠:** 文書と同じ κ-only assurance 条件を列挙すると、`10×14` は full=`0.860726`、drop-one=`0.807814`、総反復140であり、`12×12` の総反復144より少なく、ノード数も少ない。`14×10` も総反復140、drop-one=`0.830942` である。正のノード固定費を `P`、1反復費を `s` とすれば、`10(P+14s) < 12(P+12s)` が常に成り立つ。

**成果物影響:** 不要なノードと計算時間を投入しながら、「最小」という誤った設計根拠が記録される。

**提案:** 最小化対象を「総CPU時間」「PBSノード占有時間」「wall time」「ノード数」などから明示し、その目的関数と primary `τ_U` assurance に基づいて再最適化する。

---

### 3

**severity:** blocker

**主張:** dropout robustness は、欠測時に全 attempt を無効化する規則のため実際の解析に使えない。

**根拠:** 設計節は「1ノード欠落後」の assurance を採用理由にしているが、解析規則は `12 nodes × 12 repetitions` の完全行列を必須とし、complete-case、補完、部分推定を禁止している。1ノードでも欠ければ11ノード解析へ移らず attempt 全体が invalid になる。

**成果物影響:** dropout のために余分な能力を買っても、dropout 発生時には成果物を一切生成できず、設計上の保証が死んだ要件になる。

**提案:** 11ノードでの terminal analysis を事前登録して欠測規則と整合させるか、全欠測を invalid とするなら dropout assurance を要件から外して設計し直す。

---

### 4

**severity:** blocker

**主張:** `DurableRootPolicy` は repo への書込み能力を遮断せず、非流入の機械的防壁として記述するのは事実誤認である。

**根拠:** `DurableRootPolicy` と `WriteCapability` は、それを明示的に呼ぶコードの path validation にすぎない。通常の `open()`、`os.open()`、shell redirect、PBS stdout/stderr は迂回できる。実際、certify の publish 実装自身も raw `os.open` / `os.makedirs` を使用する。job process から repo が書込み可能なままなら、policy を外部 root に注入しても capability は残る。

**成果物影響:** 未較正値やログを repo 内の ignored/untracked path に書け、後続 consumer や人手操作を通じて certified 名前空間へ混入し得る。

**提案:** 本走 checkout を read-only mount、sandbox、またはACLで物理的に不可書込みにし、唯一の writable mount を外部 artifact root に限定する。そこまで実装しない場合は「能力遮断」ではなく協調的 allowlist と detector であると明記する。

---

### 5

**severity:** blocker

**主張:** 「canonical preconditions」のチェックリストを閉じても、文書自身が要求する非流入検査が実装されていないまま投入できる。

**根拠:** チェックリストには、ignored file を含む filesystem scan、success/presence matrix、FROZEN path の内容 hash、forbidden registry/receipt inventory、selector/freeze namespace の比較を実行する validator が必須条件として現れない。既存の repo scan は `git ls-files --others --exclude-standard` を使うため ignored files を除外し、pytest も `output/` を収集対象外にする。`test_frozen_artifacts.py` は固定23 path だけを検査し、新規 calibration record は対象外である。

**成果物影響:** 手順上は投入可能でも、ignored な測定ファイルや registry/receipt 汚染を検出できず、非流入保証が言葉だけになる。

**提案:** 単一の fail-closed preflight/postflight validator を投入必須条件にし、filesystem walkによる ignored file 検査、完全な presence/hash matrix、registry・receipt・freeze・selector の前後 inventory を含める。

---

### 6

**severity:** blocker

**主張:** 別ノードの monotonic clock を直接比較して start spread を判定する手順は成立しない。

**根拠:** monotonic clock は各ホストの boot-relative なローカル時計であり、ノード間で共通 epoch も共通 offset も持たない。既存の monotonic clock 使用箇所も同一プロセス内の経過時間測定で、クロスノード同期 helper は見つからなかった。また protocol は start-spread の数値閾値と timeout を固定していない。

**成果物影響:** 同時開始していても失敗、ずれていても成功と判定でき、barrier が node-order/time-order bias を防げない。

**提案:** coordinator が release を記録し、各 worker の応答を同一 coordinator clock 上で測る handshake にするか、PTP/NTP の誤差上限を実測した共通 realtime clock を使う。spread閾値、timeout、失敗規則を事前登録する。

---

### 7

**severity:** blocker

**主張:** 実験を同一 workload に固定するための重要な測定 literal と運用閾値が未確定である。

**根拠:** 実 calibration は `rratio=50`、`skew=0.9`、`rmw=0`、48 threads に加え、`extime=3`、`clocks_per_us=2100`、multi-NUMA 時の `numactl --interleave=all` を使うが、protocol の固定パラメータ表は後三者を欠く。既存 quiet gate は load1 `≤1.0`、30秒間隔で3回、最大20分だが、protocol は「閾値を固定する」とだけ書く。retry 上限、barrier timeout、start-spread、bootstrap seed/resamples も未固定である。

**成果物影響:** 実装者が投入時に値を選べ、ノード分散と実行時間・NUMA配置・静穏判定の差を混同するほか、結果を見た後の自由度が残る。

**提案:** 実行 argv、NUMA policy、quiet gate、retry、timeout、spread、bootstrap method/seed/resamples を値まで preregistration に列挙し、runner が完全一致を検証する。

---

### 8

**severity:** must-fix

**主張:** runbook の「common factor は相殺される」「差と比だけが相殺する」という説明は、加法効果と乗法効果を混同している。

**根拠:** 共通加法効果 `a` では `X-D_g`、`S-D_g`、`S-X` は相殺するが、`H=D-κS` は `H_0+(1-κ)a` となり残る。共通乗法効果 `q` では各差は `q` 倍され、相殺されない。一方 `D/S-κ` は `q` を相殺する。したがって「差と比」は同じ種類の共通効果を消していない。編集後も直前の「node is a common factor and cancels」と矛盾する。

**成果物影響:** node effect が消える量を誤認し、水準依存の node variance を対照差から除去できたと過大評価する。

**提案:** 「差は共通加法 offset、比は共通乗法 scale を相殺する」と分け、`D-κS` など混合量にはどの効果が残るか式で明記する。

---

### 9

**severity:** must-fix

**主張:** 投入手順は Pegasus 上で必要な interpreter 固定と `qsub -o/-e` の外部配置を必須化していない。

**根拠:** runbook は raw qsub で明示的な Python 3.10/PATH shim と repo 外の `-o <file> -e <file>` を要求する。protocol は interpreter/version の確認に留まり、投入節に `-o/-e` がない。既存 `submit_certify.sh` も単一 qsub で `-o/-e` を指定せず、`dispatch_compute.py` は tests/provenance 専用で、N-node barrier helper ではない。

**成果物影響:** child process が Python 3.9 を解決したり、PBSログが repo 内へ生成され、実行失敗または非流入違反になる。

**提案:** qsub argv の正規形に Python 3.10 shim、外部 absolute `-o/-e`、外部 working/output root を必須項目として固定し、preflight が argv を検証する。

---

### 10

**severity:** nit

**主張:** 新しい operational protocol が docs lint の対象外で、かつ可変な進捗状態を本文と地図に保持している。

**根拠:** `tools/check_docs.py` の `LIVING_DOCS` に `pegasus-node-variance-protocol.md` は含まれない。protocol と `docs/README.md` には「設計のみ・未実装」「未着手」など、実装後に陳腐化する状態表現がある。変更部分に docs 間の行番号参照はなく、Pegasus 固有情報の配置と README 上の地図位置自体は妥当だった。

**成果物影響:** 実装後も「未実装」が残り、path/reference 規律の回帰を checker が検出しない。

**提案:** 文書を `LIVING_DOCS` に追加し、可変状態は worklog 末尾へ移す。本文は「これらの制御が存在し合格するまで実行を許可しない」という不変条件にする。

## 総括

**NO-GO。blocker 7件、must-fix 2件、nit 1件。**

最重要なのは、primary `τ_U` に対する実 assurance が公称80%を大幅に下回ることと、durable-root policy が実際の書込み能力を遮断しないこと。このままでは計算時間を投入しても設計根拠を満たさず、未較正成果物の非流入も保証できない。

未検査・制約事項:

- 現在の scheduler 状態を live `qstat` で再確認しようとしたが、`pegasus02` で `NQSconnect: [API EACCTAUTH] Unknown user-id` となった。`Exclusive submit = OFF` は保存済み実機出力による確認であり、2026-08-11現在の live 状態ではない。
- 実ジョブの投入、barrier の動作試験、filesystem sandbox/ACL の実効試験は行っていない。
- read-only の段6レビュー契約に従い、pytest・build・文書編集は実施していない。