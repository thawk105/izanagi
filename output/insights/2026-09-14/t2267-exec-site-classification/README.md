authority: none
default_effect: no-state-change

# [T-2267] 実行場所分類 — 対象・入力・実行条件の確定と、既存経路で取れた観測

`docs/pegasus-runbook.md` §7.0 の実行場所分類について、D1938 が人間専任を解除して AI へ委任した
対象を現物で確定し、既存の認可された経路で取れる範囲を観測した記録である。

**結論を先に書く。**

1. **対象の本走は分類できていない。** T-2216 model の凍結入力・本走 argv を受け取れる
   認可済みの login dedicated-scope 経路が、調査した現行実装には無い。分類は `unknown` のままとする。
2. **凍結入力は実在する。** 一時は「不在」と判断したが、それは走査範囲の誤りだった。
   range 外に完全一致 2 本があり、3 者が独立に sha256 を照合した。本走 argv は再現可能である。
3. **ここに載せたメモリ観測は §7.0 手順による実測ではない。** 既存 runner の参考観測であり、
   certified peak を計算せず、これを根拠に資源 class を変更しない。

調査 commit: `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a`。観測日: 2026-09-14 (JST)。

---

## 1. 対象・入力・実行条件

対象は `tools/t2216_backoff_walk_model.py` である
(T-2267 の初出本文 = `docs/archive/worklog-phase3-0903-1228.md:499`)。

| 項目 | 確定内容 |
| --- | --- |
| 実行体 | `tools/t2216_backoff_walk_model.py` (60,117 bytes) |
| CLI | `measured_json backoff_copy output_json [--score-h2] [--tail-json WORKLOAD=PATH]` (`:1510`-`:1522`) |
| 凍結設定 | `REPETITIONS = 8` (`:48`)、`DURATION_US = 3_000_000.0` (`:47`)。`_require_frozen_config` が変更を拒否する |
| 入力 pin | `BACKOFF_COPY_SHA256` (`:37`)、`MEASURED_INPUT_SHA256` (`:38`)、`SOURCE_PIN` (`:36`) |
| hook 上の扱い | admission registry 未登録かつ `tools/pegasus/` 外。`--help` は rc=0 で通る |
| §7.0 上の扱い | 未計測なので `unknown`。`unknown` は `dispatch-required` と同じに扱う |
| 参考実績 (非 canonical) | `generic` で計算ノードへ送った job のメモリ 101 MB・経過 733 秒。これは login cgroup の観測ピークではない |

### 明示入力 — 5 files / 297,814 bytes

| 入力 | bytes | 照合 |
| --- | ---: | --- |
| 凍結 `measured.json` | 269,108 | sha256 `f46cebdd2691e3012c4632d3d6e82a050bb262aa43a0e8dd3aa6ffd66d604931` = pin と一致 |
| `external/ccbench/include/backoff.hh` | 3,623 | sha256 `3e9f548507200532c79b14b94389abbfd4f87c7c03addde0099740f2df3d8cd7` = pin と一致 |
| `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/t2266-backoff-static-tail-write-heavy.json` | 8,359 | repo 内に実在 |
| 同 `-balanced.json` | 8,342 | repo 内に実在 |
| 同 `-read-heavy.json` | 8,382 | repo 内に実在 |

Python・numpy 等の実行環境は明示入力に数えず、別項として扱う。

### 凍結入力の所在 — 「不在」は走査範囲の誤りだった

- 親が最初に走査したのは 2 repo だけである。`izanagi-job-evidence` 配下の JSON 846 件と、
  `/work/1/SFC/tanab/izanagi` 配下 (`.git` 除外・20 MB 未満) の全 JSON を sha256 で走査し、
  **その範囲では一致 0 件**だった。この結果自体は保存する。
- その範囲外に完全一致が 2 本ある。参照鎖は
  `output/insights/2026-09-07/t2313-13pt-audit/README.md:35`-`:36` が挙げる外部 model 出力の
  `provenance.measured_input` である。

  | 発見した原本 | bytes | 照合 |
  | --- | ---: | --- |
  | `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2216-backoff-mechanism/proj/measured.json` | 269,108 | pin と完全一致 |
  | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/proj/measured.json` | 269,108 | pin と完全一致 |

- 照合は親・段 2・段 3 の 3 者が独立に行い、いずれも同じ sha256 を得た。
- **repo へ複製していない。** 複製先の provenance 規約を新設せずに置くと由来不明の凍結 bytes が
  増えるためで、保全先の決定は下記の裁定パッケージへ回す。
  **これらの job ディレクトリは使い捨てであり、消えれば path と hash から 269,108 bytes は
  復元できない。** 入力の発見は、実行環境まで含めた再現の成功を意味しない。

---

## 2. 既存 pytest scope の参考観測 (正式分類には不使用)

> 以下は既存 `tools/run_tests.py` による専用 bounded scope の `memory.current` 観測値である。
> sampler は scope 起動後に開始し、各ループで 5 ms 待機するため、§7.0 の先行 sampler・
> 間隔 ≪1 ms の手順による実測ではない。開始直後およびサンプル間のピークの取り落とし量は
> 未評価であり、規定 margin で吸収できることも確認していない。正式な certified peak は未確定で、
> この値から資源 class を変更しない。観測対象は記載した pytest argv・fixture の実行であり、
> 凍結入力による model 本走は未実測、`unknown` のままである。

runner は `python3 <worktree>/tools/run_tests.py`。commit `75bea8e5f`、2026-09-14 (JST)。
「提示 cap」は runner が stderr に出す**付与予算**であり、実効 `memory.max` の逐語観測ではない
(`tools/run_tests.py:1754` が予算を表示し、`:1818`-`:1832` は kernel 値のページ切下げも受理する。
3,940,686,240 は 4,096 の倍数ではない)。**実効 `memory.max` は未取得である。**

| 走行 | argv | 提示 cap (bytes) | 観測ピーク (bytes) | rc |
| --- | --- | ---: | ---: | ---: |
| xdist 32 worker | `orchestrator/tests/test_t2216_backoff_walk_model.py` | 3,940,686,240 | 2,834,767,872 | 0 |
| serial A | `-n 0 <絶対 path>/orchestrator/tests/test_t2216_backoff_walk_model.py` | 3,940,686,240 | 159,653,888 | 0 |
| serial B (1 走目) | 同上 | 1,073,741,824 | 156,565,504 | 0 |
| serial B (2 走目) | 同上 | 1,073,741,824 | 161,529,856 | 0 |

- **「3 反復」とは書けない。** §7.0 は cap 変更時の再測定を要求する。cap 別では 1 走と 2 走である。
- 53 test がすべて緑。32 worker 版では `IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:series-invalid`
  が出た。serial 版では admission の peak 台帳が生きており、2 走目の stderr に
  「前回ピーク=159653888 bytes」「次回見積もり=199567360」が出た。
- **この値は対象 model の footprint を bound しない。** test は合成入力を使い
  (`orchestrator/tests/test_t2216_backoff_walk_model.py:97`)、pin を差し替え (`:502`)、
  `predict_all` を fake 化する (`:529`)。32 worker 版の 2.64 GiB は pytest の fan-out が支配的である。
- 32 worker 版と serial 版で入力・実行内容が違うので、比で割って model のメモリ量を導く操作はしない。

---

## 3. §7.0 の記録 7 項目 — 本走はどこが埋まっていないか

| 項目 | 既存 pytest scope の参考観測 | 対象 model 本走 |
| --- | --- | --- |
| commit | `75bea8e5f` | 未実行 |
| argv | 上表のとおり | `python3 tools/t2216_backoff_walk_model.py <measured.json> <backoff.hh> <out> --tail-json write-heavy=… --tail-json balanced=… --tail-json read-heavy=…` (**予定 argv。実行していない**) |
| 入力の総 bytes と件数 | test file 55,271 bytes 1 件と合成 fixture (動的分は未集計) | 5 files / 297,814 bytes (確定) |
| `memory.max` | 提示予算のみ。実効値**未取得** | 未取得 (経路なし) |
| 観測ピーク | 上表。ただし §7.0 手順ではない | **未測定** |
| 繰り返し数 | cap 別に 1 走 / 2 走 | 0 |
| 測定日 | 2026-09-14 (JST) | — |

model の `REPETITIONS = 8` は model 内部の反復であって、§7.0 の「繰り返し数」ではない。

---

## 4. 経路の有無 — 実測と現物

**認可済みの login bounded scope は存在する。** 存在しないのは、対象の本走を渡せる経路である。

| 経路 | 現物 | 判定 |
| --- | --- | --- |
| `tools/run_tests.py` | `:2397` で runner 引数を処理し、`:1895` `_scope_command` が専用 unit・`MemoryMax`・`MemorySwapMax=0` を構築する | 認可済み。ただし **pytest しか渡せない** |
| 同 `script_path` 引数 | `:1897` に内部 seam があるが、実呼出し `:2015` は指定せず `:1899` で自己再 exec。CLI からの配線はゼロ | 経路に数えない |
| `tools/check_ai_provenance.py` | `:2731` `_scope_command` は自己再 exec 固定。CLI は `:2978` の `--force-dispatch` 等で任意実行引数を持たない | 認可済み。ただし履歴監査専用 |
| `tools/mutation_fanout.py` | `:1360` で自己再 exec。`:401` が生存 cgroup の `memory.peak` を要求し、この kernel (5.15) に同 file は無い (D433 が本走不能を確定済み) | 測定の入口にならない |
| `tools/pegasus/dispatch_compute.py` の `generic` | `:1623` で任意 argv を実行するが、job script (`:851` 付近) と `_job_run` (`:1582` 付近) の二重 hostname gate が `bnode[0-9]+` を要求する。`_run_isolated_child` の隔離は user/mount namespace であって専用 memory cgroup ではない | **計算ノード専用。login scope の反例にならない** |
| raw `systemd-run` | `hooks/guard_bash.py:1191` が、LOGIN/SUSPECT で解析された head が `systemd-run` のとき拒否する。`:1192` に非実行の command-reader の例外がある | 親の Bash tool から実際に拒否された |

### 親が実測した hook の拒否 2 件 (2026-09-14 JST、login node)

1. `systemd-run --user --scope -q --unit=izmeas-probe-$$ -p MemoryAccounting=yes -- /bin/true`
   → `[guard_bash] 拒否: systemd-run を拒否します`。
2. argv に `tools/pegasus/admission_registry.json` を含む python heredoc の**読み取り**
   → `[guard_bash] 拒否: 未登録 Pegasus 実行体 … を拒否します`。実行ではなく data file 参照である。

拒否はその呼出し・その綴りの発火証拠であって、それ自体が経路の不在の証明ではない。
**静的検索も全実行面の不在証明にはしない。** 本節の判定は「調査した現行実装には無い」である。

**迂回は経路に数えなかった。** 別綴り、Codex 子、subprocess 越し、内部 seam の転用、
`systemctl --user` / D-Bus、cgroup の直接 mkdir、hook の未解析面、過去の非 canonical 測定 script
(`output/insights/2026-08-13_exec-loc-and-usage-fixes/measure-evidence/measure2.sh`) はいずれも使っていない。
共有 cgroup の差分と per-process RSS も正式分類の根拠にしていない。

---

## 5. 不足している実行経路 — 成立条件と裁定衝突

§7.0 は「実行可能な経路が無ければ、その不足を AI の実装課題として特定する」と定める。
以下は**成立条件の仕様であって実装許可ではない。**

1. 対象を現行 `tools/t2216_backoff_walk_model.py` の本走に限定し、凍結 bytes・3 tail・argv・
   commit・依存版を記録できること。
2. 対象と同時に生きる全子孫を専用 cgroup に収め、実効 `memory.max` と swap 制約を確認できること。
3. 対象の開始を取り逃さずに専用 cgroup の charged memory を観測し、測定範囲・sampling 条件・
   失敗を記録できること。
4. §7.0 の 7 項目を同じ 1 回の実行へ結び付けられること。0・欠測・cap 到達を軽量成功としないこと。
5. 資源分類と性能測定を混同せず、hook 拒否や未解析面を経由しないこと。

### 既存裁定との衝突

- **D180** は「測定専用の bounded surface の即時新設」を却下し、admission registry の族再設計へ
  同梱すると定めた。対象限定であってもこの論点に触れる。
- **D210** は上限付き実行を entry point の内側に閉じ、**汎用 launcher を作らない**と定めた。
  `script_path` の CLI 公開や任意 argv を bounded に流す launcher は、同決定が取り下げた設計と同型である。
- **D1938** は実行担当の変更であって、これらの実装変更を一括承認したものとは読めない。

したがって**親の裁量では実装しない。** 下記の裁定パッケージへ返す。

### 本 wave の scope 外の層

| 層 | 扱い |
| --- | --- |
| `hooks/guard_bash.py` の admission | 拒否条件・受理集合・配線の変更は scope 外 |
| `tools/pegasus/admission_registry.json` 正本 | 登録変更・class 昇格は scope 外 |
| runbook §7.0 の投影表 | 分類変更の反映は scope 外 |
| `tools/check_docs.py` の集合完全一致検査 | 既存検査の実行は親が行う。検査の変更は scope 外 |
| 新経路の受入全走 | 未実装なので未実施 |

**docs-only の受入が緑であることを、「対象本走が認可済み bounded 経路で動く」と読み替えない。**

---

## 6. 裁定パッケージ (ユーザー手番)

1. 対象限定の測定実行経路を作ってよいか。D180 の「即時新設は却下・族再設計へ同梱」と、
   D210 の「entry point 内に閉じる・汎用 launcher を作らない」の双方に触れる。
2. 非 `tools/pegasus/` path の `local-ok` 登録が loader と hook の双方で拒否される制約の下で、
   対象を測れたとして class をどう扱うか。
3. 凍結入力 bytes の保全先。使い捨ての job ディレクトリ外へ置くか、置くならどの provenance 規約か。

---

## 7. 逐語資料

`verbatim/` に段 1 brief・段 2 プラン・段 3 の敵対 2 レンズ・段 4 裁定を凍結した。
段 3 は親 brief 自身も攻撃対象とし、親の無限定な「経路は存在しない」と「凍結入力は不在」を
どちらも refuted にした。本文はその訂正後の形だけを使っている。
