# 段 1 brief の addendum — 親が自分の誤りを訂正する

**brief.md の「repo 外束縛の全数 (実測、3 件)」は誤りである。実際は 5 file・3 外部 root ある。**
親は最初 `git grep` で `/home/` と `expanduser` を引いただけだったので、`/work/` 配下の束縛を
取り逃していた。段 2 のプラン起草後に、AST で全 string literal を集めて「実在する repo 外 path で
system prefix (`/usr /proc /dev /tmp /bin /sbin /lib /etc /var /sys /opt`) でないもの」へ絞る
走査を独立に書いて測り直した。

## 走査の実測

- `orchestrator/tests/*.py` の string literal のうち絶対 path・home 相対に見えるもの: **1796 件**。
  **字句だけの走査は gate として成立しない。**
- そこから「実在する repo 外 path、system prefix を除く」へ絞ると: **195 件**。
  ただし大半は `/`、`//`、`/./`、`/run`、`/work` のような断片 (path 結合の右辺) である。
- 断片を除いた意味のある distinct な束縛先:

| 束縛先 | 出現 |
|---|---|
| `/work/1/SFC/tanab/dev-wave-jobs` | 2 |
| `/work/1/SFC/tanab/b10-backoff-grid-runs5` | 2 |
| `/home/SFC/tanab/.codex/sessions` | 1 |
| `/work/SFC/tanab/github/glog`, `/work/SFC/tanab/github/gflags` | 各 1 |
| `~/.claude/projects` | 1 |

## 更新した全数表

| # | file:line | 束縛先 | 防護 | 実際に外部を読むか |
|---|---|---|---|---|
| 1 | `test_codex_reasoning_ab.py:128` | `~/.codex/sessions` | `_require_pinned_rollouts` が**内容単位**で skip (`:800-806`) | 読む。**適切に防護されている唯一の先例** |
| 2 | `test_t189_oracle_wiring_slice.py:38,84` | `/work/1/SFC/tanab/dev-wave-jobs` | `skipif(not _JOBS_ROOT.is_dir())` の**根 directory の有無だけ** | 読む |
| 3 | `test_t1434_t1222_science_slice.py:21` | 同上 | **無し** | 読む (`:55,83,126,217,244,295,316,340,378`) |
| 4 | `test_b10_extended_figure_provenance.py:21-23,287` | `/work/1/SFC/tanab/b10-backoff-grid-runs5` | **無し** | 読む。`_sha256(MEASUREMENT_ROOT / relative)` を 22 件 |
| 5 | `test_plot_b10_extended_backoff.py:15-17,148` | 同上 | **無し** | 読む。`plot.load_measurements(MEASUREMENT_ROOT)` |

`test_pegasus_tools.py:427,461` の `/work/SFC/tanab/github/{gflags,glog}` と
`test_claude_session_ledger.py:1773` の `~/.claude/projects` は、**値としての文字列を assert して
いるだけで filesystem を読んでいない。** したがって本族には入らない。
**この区別が gate 設計の要点である** — 「literal に repo 外 path が現れる」ではなく
「実行時にその path を読む」が族の条件でなければならない。

4 と 5 は `os.environ.get("IZANAGI_B10_MEASUREMENT_ROOT", "<repo 外の既定>")` の形で、
環境変数で上書きできるが**既定値が repo 外**である。上書きしない通常の受入では既定が効く。

## `DW-G03` への帰結

親は brief で 2 と 3 を「独立 2 例」と数えたが、両者は同じ `dev-wave-jobs` を見ており
「異なる producer/consumer」と言えるかは弱かった。**4 と 5 は別の外部 root・別の系統
(論文図の provenance と作図) であり、これで独立 2 系統が揃う。** 族としての一般化は正当化される。

## `DW-G05` 成果物影響

4 と 5 が束縛する `/work/1/SFC/tanab/b10-backoff-grid-runs5` は、
`docs/paper-story/figures/fig2c_b10_extended_backoff.{png,pdf}` の provenance を検証するための
外部測定 root である。ここが剪定されると、**論文図の provenance 検査が hard red になり、
その時点で全 wave の受入が同時に落ちて land が止まる。** 2026-09-01 に
`~/.codex/sessions` の 2026/07 消失で起きたのと同じ形である (同時刻の別 wave 3 本が同数で落ちた)。

## 段 2 プランへの含意

段 2 のプランは 3 件を前提に書かれている。**設計 (登録簿 + 内容単位 guard + メタ gate) は
変わらないが、対象集合が 2 file 増える。** 段 4 の裁定でこれを取り込む。
