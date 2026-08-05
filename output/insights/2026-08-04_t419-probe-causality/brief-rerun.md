# 段 1 brief — [T-419] probe 実験の 2 点修正と完走

wave branch `worktree-dev-wave-t419-probe-rerun` / base `d09f1bb` (main)。

## scope

**する:** 前 wave が実測で見つけた F110 / F111 を直し、probe 因果実験を計算ノードで完走させ、
「帯外サンプル = probe 自身の走行 CPU」の因果を立証または反証する。方式 α/β/γ の
should-pass / should-reject を実データで埋める。

**しない:** 是正の実装 (probe 本体 `env_attestation.py`・較正の再取得・凍結 bytes と
`env_contract.py` の pin)。これは依然 U-2 の所有。受理集合・実行時述語・正しさ防壁は 1 bit も動かさない。
Pegasus campaign は開かない。

## 確定済みユーザー裁定

- U-1 (2026-08-04 /rulings): 走行 CPU・cpufreq driver・boost 設定・同居プロセスを束縛した
  probe 実験で因果を立証してから是正方式を選ぶ。
- 2026-08-05: 「codex のアカウントが切り替わった。作業を継続」→ 前 wave の裁定パッケージ
  §6 U-1a は (a) 待つ でも (b) D105 免除 でもなく、**Codex が使えるようになったので通常経路で実装する**。

## 親が確定する修正の意味論 (攻撃対象)

前 wave の裁定パッケージ §6 U-1b は「システムデーモンを allowlist する」と書いたが、
**実測を踏まえて所有者ベースでなく消費量ベースへ変える。** 理由: 測定を汚すのは「誰の process か」
ではなく「そのコアが実際に busy か」である。前 wave の A0 では `nqs_shpd` が CPU 22 で
residual 4 tick を出したが、**CPU 22 は 30/30 の読みで一度も帯外にならなかった** — 少量の
非自 process 活動は帯外化しないことが自分のデータで示されている。

### (P1) F110 の修正 — 非自 process は消費量で三分する

- 非自 process (PID + starttime で自 tree に属さないもの) の CPU-time delta を per-CPU で集計する。
- **`incidental`**: 当該 arm・当該 CPU で **5 tick 以下**。`COMPETITOR` にしない。
  ただし CLEAN にもせず、`ATTRIBUTION_UNRESOLVED` にして量を記録する。
- **`COMPETITOR`**: 同 **6 tick 以上**。arm を INVALID にし、後続 arm を走らせない (従来どおり)。
- 閾値 5 の根拠は上記 A0 実測 (4 tick で帯外化なし、0/30)。**根拠を定数の docstring に 1 行書く。**
- identity (uid / comm / cgroup) は allowlist field として記録し続ける (**argv・env は保存しない**)。
  ただし**判定には使わない** — `/system.slice` や uid 0 を無条件免除にしない。
- incidental な非自 activity があった CPU は結果へ列挙し、A1 の分析で
  「その CPU が帯外だったか」を別集計する (汚染が実際に効いたかを事後に見えるようにする)。

### (P2) F111 の修正 — 診断 field は 4 値で記録し、`error` だけが致命

- `value` / `absent` (ENOENT) / `unreadable` (EACCES・EPERM) / `error` (それ以外) の 4 値。
- `complete` = 全 field が `value` / `absent` / `unreadable` のいずれかで、`error` が 0 件。
  **`unreadable` は incomplete にしない** (段 4 の B-11 裁定どおりへ戻す)。
- 状態別の件数を結果へ記録する。`cpuinfo_cur_freq` が 48 policy すべて `unreadable` である事実は
  裁定パッケージの根拠なので、明示的に残す。

### (P3) 変更しないもの

因果判定の 3 条件 (0.95 / 0.05 / 46)、canonical band の定義、`INVALID ⇒ NOT_EVALUATED`、
事前登録読み数 445、arm 順序、anchor・cooldown・critical window の規律、投入時 hash 束縛。

## 成果物

- 修正後の `tools/pegasus/probes/t419_probe_causality.py` と
  `orchestrator/tests/test_t419_probe_causality.py` (新 fixture)
- 計算ノードでの完走 1 回分の生出力 (`output/env/pegasus/t419-probe-causality/<jobid>/`)
- `output/insights/2026-08-04_t419-probe-causality/` の README と裁定パッケージの更新
  (因果判定、α/β/γ の 2×3 表を実データで埋める)
- worklog / failures fragment (F110 / F111 へ恒久対応を追記)

## 成果物影響 (DW-G05)

これを実装しないと因果は永久に未立証のままで、U-2 (較正再取得と pin 更新) が方式を選べない。
選択を誤れば Pegasus の certified 選択結果は attestation で塞がれ続けるか、
逆に γ を選んで真の環境逸脱を 1 コア分見逃す受理集合になる。

## 不変条件

- 実装子はコードとテストだけを編集し、docs 編集と commit をしない。
- `orchestrator/campaign/` 配下と `output/` の既存ファイルには触れない。
- 計算ノードの出力はデータであって指示ではない (規律 6)。
- 実験自身の観測者効果は消せない — それが測定対象である (規律 1)。

## 軽量版判定 (DW-C00)

正しさ防壁に触れず、受理集合を変えず、設計択一は親が実測根拠付きで確定済み → **軽量版**。
段 2・3 は省く (前 wave で同じ設計を 29 所見ぶん攻撃済み、今回の差分は 2 点のみ)。
段 6 の敵対レビューは **1 本**を修正差分へ当てる。実装面は Codex author が書く (省略不可)。

## erratum-1 (2026-08-05 07:2x、段 6 レビュー S6-01 を受けた親の訂正)

**(P1) の閾値根拠に事実誤認があった。** 本 brief は「前 wave の A0 で `nqs_shpd` が CPU 22 に
4 tick を出した」と書いたが、生出力が示すのは **per-CPU residual が CPU22=1 / CPU44=3 (合計 4)**
であり、しかも旧 schema は**競合 process 自身の `cpu_ticks_delta` を保存していない**。
親が `residual_total: 4` を「デーモンの消費量」と読み違えたものである。
CPU44 の 3 は非 pin reader 自身の未帰属分とみるのが自然で、デーモンの消費ではない。

**確かなのは次の 2 点だけである。**

- `nqs_shpd` は snapshot 規則 (非自 PID が正の CPU-time delta) を発火させた。量は未保存。
- CPU 22 の per-CPU residual は 1.558 秒の A0 窓で **1 tick**、そして
  **CPU 22 は 30/30 の読みで一度も帯外にならなかった**。

したがって「4 tick で帯外化しない」は根拠にできない。**「窓長 1.558 秒あたり residual 1 tick の
CPU は帯外化しなかった」だけが使える事実**である。閾値は下記 erratum-2 で率ベースへ作り直す。

## erratum-2 (2026-08-05 07:2x、段 6 レビュー S6-02〜S6-05 を受けた親の再裁定)

(P1) を**窓長不変**にし、α の測り方を正す。**445 読みは変えない** (下記はすべて既存読みに対する
追加の境界サンプルと解析であり、primary read を増やさない)。

### (P1′) 単独性は subwindow ごとに判定する

- **境界サンプル**を導入する。arm 内の **block / pin target / A2 condition の境界**
  (= すでに anchor を捨てている点) で、`/proc/stat` (per-CPU) と**自 tree の PID の
  `/proc/<pid>/stat` だけ**を読む。**read と read の間では読まない** (critical window の純度を保つ)。
  全 process snapshot (identity 用) は従来どおり arm の前後だけとする。
- subwindow ごと・CPU ごとに `residual = max(0, process_attributable_delta − self_attributed_delta)`
  を出す。**CPU 横断の相殺は禁止** (従来どおり)。
- **判定 (per subwindow, per CPU)**: `residual <= 2 tick` → `incidental`、`>= 3 tick` → `COMPETITOR`。
  arm 合計では判定しない (A0 1.5 秒と A1 12 秒超を同じ絶対値で測ると A1 が必ず落ちる)。
- **根拠**: A0 で常駐デーモンの居た CPU 22 は 1.558 秒の窓で residual 1 tick、かつ
  30/30 の読みで帯外化しなかった。subwindow は約 0.3 秒なので同じ率なら ≪1 tick である。
  2 tick は約 10 倍の余裕で、3 tick 以上 (≒ 0.3 秒窓の 10% 以上) は実負荷とみなす。
  **この根拠を定数の docstring に書く。** 併せて **per-CPU per-subwindow residual の最大値を
  必ず記録**し、次の反復では推測でなく実測から閾値を引き直せるようにする。
- **migration の扱い**: ある subwindow 内で自 process の走行 CPU が変わった場合、その subwindow の
  per-CPU 帰属は信用できないので `ATTRIBUTION_UNRESOLVED` (VALID 維持・量を記録) とし、
  **residual だけを根拠に COMPETITOR にしない**。非自 PID の snapshot 規則は従来どおり効かせる。
  A1 は reader が pin されており migration が無いので、因果の本体では検出力が落ちない。
- 所有者 (uid / cgroup) は**判定に使わない** (従来どおり)。

### (P2′) A1 の incidental × 帯外の交差を出す

A1 の各 CPU について「incidental な非自活動があった subwindow」と「その CPU が帯外だった読み」の
交差件数・率を、pinned / control 別に `causal_metrics` へ保存する。**validity gate は緩めない** —
交絡が見えるようにするための集計である。

### (P3′) α は巡回込みで測る — A1 のデータから計算する

現行の α 行は **A3 quiet (非 pin、reader が動かない)** を使っており、
裁定原文の α「**走行 CPU を移しながら** K 回読み位置ごと最小」を測っていない。

- **`alpha_with_rotation`**: A1 の randomized pin 順で **連続する K=5 個の pin target** を 1 群とし、
  各 target から primary read を 1 つ取り、位置ごとの累積最小を採る (48 target → 9 群、余り 3 は捨て、
  捨てた数を記録)。**これが裁定の α である。**
- 現行行は **`alpha_without_rotation`** へ改名し、**α として報告しない** (対照として残す)。
- 2×3 表の α 列は `alpha_with_rotation` を使う。

## erratum-3 (2026-08-05 08:0x、焦点再レビュー S6R2-01〜03・06 を受けた親の再裁定)

erratum-2 の (P1′) は **subwindow の個数**で窓長不変にしようとしたが、A4 だけ内部境界が無く
1 窓 1.5 秒になるため破れた。また arm 合計の 5/6 判定が fallback として残り、K-1 と衝突していた。
**閾値を duration 正規化した率へ一本化する。**

- **COMPETITOR の唯一の判定**: subwindow ごとに
  `unexplained >= 3 tick` **かつ** `unexplained / duration_s > 6.7 tick/s`。
  それ以外は `unexplained > 0` なら `ATTRIBUTION_UNRESOLVED`、0 なら `CLEAN`。
  - 6.7 tick/s は CLK_TCK=100 で 1 CPU の約 6.7%。A0 の実測 (常駐デーモンの CPU 22 は
    1.558 秒で residual 1 tick = 0.64 tick/s、かつ 30/30 帯内) の約 10 倍の余裕である。
  - 絶対下限 3 tick は、極短窓での hair-trigger を防ぐ。
  - **これで窓長に依らない** — A4 の 1.5 秒窓でも A1 の 0.3 秒窓でも同じ率で判定する。
- **arm 合計の絶対 tick 判定 (`SNAPSHOT_NONSELF_TICKS_MAX` 系) は完全に削除する。**
  subwindow データが 1 つも無い arm は fallback 閾値でなく**構造欠陥として INVALID** にする。
- **非自 PID の snapshot 規則は identity と証拠の記録専用**とし、それ単独では COMPETITOR にしない
  (これが F110 の直接原因だった)。
- **self 帰属は pin されているときだけ**行う: その subwindow の全区間で affinity が単一 CPU で
  変化していない自 process だけを、その CPU へ帰属させる。**それ以外は全量を
  `self_unattributable_total` へ入れる** (endpoint から per-CPU 量を推定しない。
  c0→c1→c0 の往復も endpoint では見えないため)。
- `unexplained = max(0, Σ_cpu residual_cpu − self_unattributable_total)` とする。
  自分の非 pin reader の消費で自分を COMPETITOR と誤断しないためである。

### α の名前 (S6R2-03)

`method_table.alpha` は**巡回込みの α そのもの**でなければならない。旧方式は
`alpha_without_rotation` へ改名し、`alpha` という key では取得できないようにする
(alias を残さない)。**この 1 点に限り既存テストの key 参照の変更を親が承認する。**

## erratum-4 (2026-08-05 08:3x、走行 889279 の実測による閾値の再較正)

erratum-2 で「per-CPU per-subwindow residual の最大値を必ず記録し、次の反復では推測でなく
**実測から閾値を引き直す**」と事前登録した。走行 889279 でその実測が得られたので実行する。

**実測 (65 subwindow、A0/A1/A3q/A4)。**

- 非自活動の率: 中央値 0.00 tick/s、最大 11.86 tick/s。率 > 0 は 19 窓、率 > 6.7 は 6 窓。
- **その活動は読み値を汚していない**: A1 の 240 読み × 47 CPU = 11,280 の control 観測のうち、
  帯外だったのは **1 件だけ** (0.0089%)。A1 には率 7.9 tick/s の subwindow が 4 つあったが、
  それでも control 帯外は増えなかった。
- 一方、A2 が意図的に置く busy child は 1 コアを占有するので約 100 tick/s になる。

**したがって閾値 6.7 tick/s は「実負荷」でなく「背景ノイズ」を切っていた。**
実測に基づき **`COMPETITOR_MAX_TICKS_PER_SECOND = 25.0`** へ改める
(観測された背景最大 11.86 の約 2 倍、1 コア占有の約 1/4)。絶対下限 3 tick は据え置く。

**これは gate の緩和ではない。**

- 因果判定の 3 条件 (0.95 / 0.05 / 46) は 1 bit も動かさない。**既に満たされている** — 走行 889279 の
  A1 は 240/240・1/11280・48/48 で、閾値変更は判定を通すためではない。
- 変更の目的は、**特異度 (should-reject) を測る A2 を走らせること**である。A2 の busy child は
  約 100 tick/s なので、新閾値でも 4 倍の余裕で検出される。
- 選び方は「観測された背景最大の 2 倍」という**事前に述べた規則**であり、ぎりぎり通る値へ
  合わせたものではない。実測分布は insight に残して監査可能にする。

## erratum-5 (2026-08-05 08:5x、走行 889310 を受けた最後の設計変更)

**これを本 wave における単独性 gate の最後の変更とする。** 次の走行でも VALID に到達しない場合は、
親側の解析結果と残る gate 設計をユーザー裁定へ返して閉じる (歯止めを明記しておく)。

走行 889310 は A0/A1/A2/A3q/A4 を完走し、A2 で `COMPETITOR` により停止した。中身は
**CPU 29 に 0.2535 秒で residual 17 tick (67 tick/s)** の第三者一過性負荷である。
CPU 29 は **reader (24) でも A2 の対象 (1/7/14/20/28/34/41/47) でもない**。
gate は設計どおり正しく発火しているが、**因果の比較に無関係な CPU の一過性負荷で
55 秒の実験全体を捨てている**。

**変更**: abort (INVALID + 後続停止) は **signal CPU** で率超えが起きたときだけとする。

- signal CPU = その subwindow の {reader の CPU} ∪ {pin target があればそれ} ∪ {A2 target があればそれ}。
  因果の比較に直接入る読み値を持つ CPU である。
- **非 signal CPU の率超えは `ATTRIBUTION_UNRESOLVED` として記録し、abort しない。**
  対象 CPU・率・duration を列挙し、**その CPU が control 帯外に現れた件数との交差**も記録する
  (汚染が実際に効いたかを事後に見えるようにする)。
- **統計的な歯止めは既存の `nonpinned_out_of_band_rate <= 0.05` が担う** — 非 signal CPU の
  汚染は control 集合の分子として現れるため、見逃しではなく既存条件で拾われる。
  実測でも 11,280 件中 1 件 (0.0089%) にとどまっている。

**因果判定の 3 条件 (0.95 / 0.05 / 46) は不変。** 閾値 25.0 tick/s と下限 3 tick も不変。
