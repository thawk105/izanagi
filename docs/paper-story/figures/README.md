# docs/paper-story/figures/ — 図の凍結物と後継図

このディレクトリは論文ストーリー用の図を置く。

**この README 自身は「腐らない入口」であり、凍結物ではない。** 図が増えたり後継図が出たら更新する。
一方、**PNG / PDF / provenance JSON は凍結物**である。`docs/paper-story/README.md` の運用ルールに従い、
既存の図は上書きしない。誤りが見つかったら後継図を**別 filename**で、
**再現可能な生成器を伴うときだけ**作る。

## 図の一覧

| filename | 生成器 | 状態 |
|---|---|---|
| `fig1_phase2_negative.png` | tracked に無い | 凍結。2026-07-10 版で収録 |
| `fig2_backoff_mechanism.png` | tracked に無い | 凍結。**baseline を誤って label している** (下記) |
| `fig3_arc_status.png` | tracked に無い | 凍結。2026-07-10 版 (Phase 3 段 5 時点) の現況図 |
| `fig2b_backoff_sweep_3workload.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_backoff.py` | `fig2_` の**後継図**。本 README が再現手順を持つ |

## `fig2_backoff_mechanism.png` の何が誤っていたか

旧図は横破線に `stock adaptive backoff (Cicada-type hill-climb)` という label を付けているが、
**その線が描いている値は無 backoff のもの**である。図の中で赤い曲線の x=0 の点 (無 backoff) と、
その破線が同じ高さにある — 同じ値に 2 つの異なる label が付いていた。

さらに旧図が描いていた系列は perf record 下の診断用 profile 系列であり、D20 が
「perf 下の tps は headline 非使用」と定めているため、論文の headline 値の出所にはできない。

詳細と一次資料は `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`。

後継図 `fig2b_backoff_sweep_3workload` はこれを次のように直している。

| 論点 | 旧図 | 後継図 |
|---|---|---|
| 系列 | profile (perf record 下、headline 非適格) | sweep (headline 適格) |
| workload | write-heavy 1 件 | write-heavy / balanced / read-heavy の 3 件 |
| 基準線 | 無 backoff の値に「適応 backoff」の label | **無 backoff 対照 1 本だけ**を、そう名乗って描く |
| 基準線の不確かさ | 点推定のみ | 95% 信頼区間の帯を付ける |
| 下段の機序 | spin% を含む (profile 由来) | abort 率と IPC (sweep の集約値) |
| 生成器 | tracked に無い | `tools/plotting/plot_backoff.py` (tracked) |
| 入力の束縛 | 無し | provenance JSON が入力・生成器・出力の SHA-256 と、描いた線の label↔値 対応を記録 |

なお `fig2_backoff_mechanism.png` を参照する凍結スナップショット
(`docs/paper-story/2026-07-10.md` と `docs/paper-story/2026-08-23.md`) のキャプションも
同じ誤りを持つが、**両版は凍結物なので訂正しない**。訂正は日付なしの入口
`docs/paper-story/README.md` の erratum が担う。

## 後継図の再現

repo root から、**計測機の外**で次の 1 行を実行する (FIGURE_CONVENTIONS §7)。

```
python3 tools/plotting/plot_backoff.py --baselines no-backoff docs/paper-story/figures/fig2b_backoff_sweep_3workload output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7 output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9
```

`--baselines no-backoff` が、この図の基準線を無 backoff 対照 1 本に限定している。
この option を省くと生成器の既定 (無 backoff と適応 backoff の 2 本) になり、
**どちらの線が利得の分母かが図から決まらなくなる** — それが旧図の事故の本質である。

出力は次の 3 ファイル。

- `fig2b_backoff_sweep_3workload.png` — ラスタ
- `fig2b_backoff_sweep_3workload.pdf` — ベクター (論文投稿はこちら)
- `fig2b_backoff_sweep_3workload.provenance.json` — 入力・生成器・出力の SHA-256、
  描いた線の label↔値 対応、測定条件、図に出した主要数値

### 再現できるのは「値」であって「バイト列」ではない

同じコマンドを再実行すると同じ論理値・同じ図が得られるが、
**3 点セットの byte-for-byte 一致は保証しない。**

- provenance JSON は生成時刻 (`generated_utc`) を持つので**時刻依存**。
- PDF は matplotlib が生成日時を埋めるので**時刻依存**。
- PNG は matplotlib の版が metadata として入り、font 解決も環境に依存するので**環境依存**。

バイト一致を要求したいなら `SOURCE_DATE_EPOCH`・依存版・font を pin する別の仕組みが要る。
本図はそこまでしていない。**着地したバイト列の同一性は provenance JSON が記録した SHA-256 と
`orchestrator/tests/test_backoff_figure_provenance.py` が守る** — 再生成の決定性には依存しない。

## 入力

3 つとも `output/campaigns/` の tracked な既存 campaign であり、本図のために新規計測は行っていない。

| workload | campaign | read 比率 |
|---|---|---:|
| write-heavy | `backoff-sweep-silo-write-heavy-sweep-493813a7` | 5% |
| balanced | `backoff-sweep-silo-balanced-sweep-484c663e` | 50% |
| read-heavy | `backoff-sweep-silo-read-heavy-sweep-610004b9` | 95% |

各 campaign から読むのは反復ごとの生スループット値と genome を持つ WAL、abort 率と IPC の
集約値を持つ dat、CCBench commit を持つ lock file の 3 種である。
3 種の SHA-256 は provenance JSON にある。

read-heavy の campaign が 3 つあるうち `610004b9` が正典である理由 (他の 2 つは screening の
positive control と build 失敗) は、上記 insight の該当節にある。

## キャプション正文

> **図2b.** 旧 `linux-baremetal` 環境における Silo の静的 backoff sweep (3 workload)。
> 上段は各設定 5 反復の標本平均スループット (M tps = 毎秒 100 万トランザクション) と、
> t 分布による 95% 信頼区間。灰色の破線と帯は、**同じ sweep の中の無 backoff 対照**
> (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) の標本平均と 95% 信頼区間である。
> **この対照が利得の分母であり、図中の基準線はこれ 1 本だけである。**
> 上段の `peak` 注釈は、曲線の最大が両端でなく内側にある workload だけに付く。
> read-heavy は単調減少で最大が左端なので注釈は付かない。
> 下段は abort 率と IPC (instructions per cycle = 1 サイクルあたりの命令数)。
> 下段は集約 1 点なので信頼区間を付けない。
> 測定条件は 3 workload 共通で、レコード数 1,000,000、48 スレッド、Zipf skew 0.9、
> read-modify-write 無効、実行時間 3 秒、`clocks_per_us` = 1,800 TSC tick/µs、トレース無効、
> `numactl --interleave=all`、環境タグ `linux-baremetal`、CCBench commit `6656e93`。
> **記録された実行フラグの上では** read 比率だけが workload ごとに異なる
> (write-heavy 5%、balanced 50%、read-heavy 95%)。ただし測定日は同一ではない
> (write-heavy と balanced は 2026-06-22、read-heavy は 2026-06-28)。
> 縦軸は workload ごとに独立なので、パネル間で線の高さや傾きを直接比べてはならない。
> データは verifier epoch E0 (この campaign を撮った時点で verifier の同一性を束縛する権威が
> まだ無かったことを示す印) の `HISTORICAL_RAW` 読み出しであり、現行の paired campaign 契約
> (`docs/decisions.md` の D496) より前の記述的結果である。
> **本図は論文の利得率の出所ではない。** 論文値 (write-heavy +38.3%、balanced +11.3%、
> read-heavy -6.6%) は同じ WAL の各側 **median** の比であり、本図の点推定は**標本平均**である
> (平均から計算すると +38.1% / +11.4% / -6.9%)。両者は同じ生値の別の要約であって、
> 一方が他方の丸め違いではない。
> 旧図 `fig2_backoff_mechanism.png` が示していた spin 希釈の機序は**本図の射程外**である
> (spin% は perf record 下の診断系列にしかない)。

## proof chain

- 図に描いた線 → provenance JSON の `baselines[]` (label・値・95% CI 半幅・genome)
- 図の主要数値 → provenance JSON の `facts`
- provenance JSON → 入力 WAL / dat / lock file / 生成器 / 出力 PNG・PDF の SHA-256
- それらが着地後もずれないこと → `orchestrator/tests/test_backoff_figure_provenance.py`
- 図中の label と実際に描いた線の一致 → `orchestrator/tests/test_plot_backoff_ci.py`
- 利得率の一次資料と条件表 → `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`
- 作図規約の正本 → `tools/plotting/FIGURE_CONVENTIONS.md`
