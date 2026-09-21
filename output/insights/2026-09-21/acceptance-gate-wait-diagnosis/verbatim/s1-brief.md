# 段 1 brief — 受入門番の待ち時間診断 (2026-09-21 07:5x JST)

## 研究前進
- 土台。止めている研究: 論文稿 wave (paper-*-ja) と B-5/B-8 など証拠 wave の壁時計 (1 wave 平均 154 分、記憶 dev-wave-wall-decomposition-facts) のうち受入門番で待った分が未測定で、8c 無人ループ (ユーザーの目標の柱) の wave 回転率を決める。完了判定 = 直近 20 wave の待ち分布・同時待ち数・開いた瞬間の leaders/load・飢餓回数が一次資料から数表になり、緩和案が効果見積り付きの裁定パッケージになる。最小差分 = 実装 0 行 (repo)。

## scope
- 母集合: `dev-wave-jobs/<wave>/` と `~/.claude/jobs/*/tmp/` にある門番 log 2 形式 (chain 型 `gate: load=… leaders=… (cond …)` / loop 型 `attempt=… leaders=… load1=… streak=…`) を持つ wave のうち、最終 log mtime が新しい 20 wave (9/20 15 時〜9/21 04 時見込み)。attempt (再投入) は wave 内の系列として全部数える。
- 出す数: (a) 待ち時間 (loop 最初の tick → GO/attempt 行) の分布 (中央値・p90・最大、attempt 別と wave 別)、(b) 待ち区間ごとの同時待ち wave 数 (他 wave の tick 時刻区間の重なり + log 内 leaders 値で下限補正)、(c) 開いた瞬間 (GO 直前の tick と recount) の leaders / load1、(d) 飢餓の回数 (P2 の定義)、(e) 条件の異なる門番の内訳 (列で示す)。
- 緩和案 (閾値 ≤2、jitter、周期の位相ずらし、優先順 FIFO) を記録 tick 列への反実仮想再適用で見積り、裁定パッケージにする。実装しない。

## 確定済みユーザー裁定
- 門番の閾値 leaders ≤ 1 ∧ load1 ≤ 60 + jitter は 2026-09-18 manager 調停 (記憶正本)。緩和は裁定事項 (2026-09-20 T-2610)。
- D2148 項 12: inbox の門番条件値・FIFO・自動再投入・追加 L2 節を丸ごと採用した裁定ではない。D662/DW-O27: lease 待ち行列は廃止、acceptance は lease を待たない。D2185: 1 wave (E/L 隣接対) だけ上限 2 へ緩めた先例。
- lease primitive (`tools/wave_land_window.py`) と待ち手 (`tools/dev_wave_wait.py`) は変えない。規律 2 不変。gate・台帳・一般化の追加は scope 外。

## 不変条件
- repo の実装面差分 0 行。集計 probe は Codex author 子が worktree 内へ書き、親が実行前に job dir へ退避 (DW-C01、記憶 probe-must-not-enter-repo-without-codex-author)。
- 数値は一次資料 (log の時刻文字列・mtime) からのみ採り、推定しない。実測 log は tee の生 stdout を逐語で別 file に置く。
- 効果見積りは反実仮想 (仮定付き模型) であり上下限として書かない。他 wave の挙動変化は 1 次近似。

## 前提実測 (brief 前)
- lease dir `dev-wave-jobs/land-lease/` は現在 ticket 1 件 (8/23、stale) のみで履歴を持たない → 「lease directory の記録」は待ち時間の一次資料にならない (依頼の前提を覆す新事実 → 段 4 で扱う)。
- `acceptance-*.wait-receipt.json` は producer receipt (dev-wave-producer-receipt/v1: artifact/done の mtime のみ)、`acceptance-receipt-*.json` (dev_wave_wait 発行) も時刻 field を持たない → 待ち時間は門番 log の tick 時刻と started.txt/finished.txt/mtime から復元する。
- `~/.claude/jobs/` は 20 dir しか残っておらず (削除で消える)、門番 file は 1 件 (rulings28) → 母集合は実質 `dev-wave-jobs/`。
- 9/17 以降の門番 log は 100 本超 (wave 約 60)。loop 型は条件値を log に出さないので script (`gate-acceptance-loop.sh`) から読む。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 待ち時間 = 門番 loop の最初の tick 時刻 → GO (loop 型) / `attempt N:` (chain 型) の時刻。post-claim merge・投入後は待ちに含めない。attempt 2 以降は前 attempt の rc 行から次の GO まで。
- (P2) 飢餓の定義 (事前登録): 待ち区間の長さ ≥ 30 分 ∧ 区間内で同時に待つ wave (自分含む) の最大 ≥ 3。T-2610 の実測 (3 本 + 走行中 2 本で 50 分) を 1 件として再現できる定義であることを確認する。
- (P3) 同時待ち数は他 wave の門番 log の tick 区間の重なりで復元する。log の無い待ち手 (門番なし直接投入・消えた job dir) は数え落とすので、log 内の leaders 値 (走行中 leader) と合わせて「待ち + 走行」の両方を出す。
- (P4) 閾値の異なる門番 (≤ 2、`l1<30`、pigz hold) も母集合から除外せず、条件を列に持つ。分布は ≤1 型だけの部分集合でも出す。
- (P5) 効果見積り: 記録 tick 列へ代替条件を再適用し「開いたであろう最初の tick」を求める。開いた wave が leader を増やす 2 次効果は、同時刻の他 wave へ +1 を伝播する 1 段だけ扱う。

## 成果物
- `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md` (数表・方法・限界・裁定パッケージ §) + `verbatim/` (生 stdout 逐語、probe の写しは .md)。
- `docs/spool/worklog/` fragment 1 本 (裁定待ちを明記)。decisions fragment は無し (裁定はユーザー)。
- job dir: probe script、生 log、集計 JSON。

## 分割方針 (軽量版、記憶 T-2243 型)
- 段 2 省略。段 3 read-only 相談 1 本 (レンズ: 母集合・定義 P1〜P5・復元の穴・見積り法の妥当性)。段 4 裁定。段 5 Codex author 1 本 (集計 probe)。段 6 read-only review 1 本 (README の数表を生 stdout と照合) + 焦点再レビュー。段 7 記録。段 8。段 9 受入 (門番経由) + land。
- 変異 matrix は実装面差分 0 で免除。受入全走は免除しない。

## 条件表 (段 1 時点)
- DW-O08/O09/O10 不成立 (freeze・凍結 bytes・producer に触れない)。DW-O11 不成立 (削除なし)。DW-O13 不成立 (gate 新設なし、緩和案は裁定パッケージ)。DW-O20 済 (startup-gate.log rc=0)。
