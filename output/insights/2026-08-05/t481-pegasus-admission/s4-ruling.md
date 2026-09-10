# 段 4 裁定 — [T-481] / [T-482] / [T-483]

親が段 3 の 19 real 所見を real/refuted、採用/不採用、scope 内/外に裁定する。
**受理集合に関わる主張はすべて実 hook subprocess で裏取りしてから裁定した**
(逐語 = `artifacts/probe_lens_claims.json`)。

## 0. 裏取りで判明した最重要事実

レンズ所見の多くは「本 wave の変更が開ける穴」ではなく **現時点ですでに開いている穴** だった。

| 綴り | 現在 | 根拠 |
|---|---|---|
| `python3 -m cProfile tools/pegasus/exec_calibrate.py` | **ALLOW** | 分離形では第 1 非 option が `cProfile` になり pegasus path に当たらない |
| `python3 -m cProfile -o /tmp/p.out tools/pegasus/certify_calibration.sh` | **ALLOW** | 同上 |
| `python3 -m pytest.__main__ <tests>` / `-m _pytest.main <tests>` | **ALLOW** | pytest 判定が module 名の完全一致のみ |
| `python3 -W ignore tools/pegasus/exec_calibrate.py` | **ALLOW** | option の値を script と誤認 |
| `bash -O extglob tools/pegasus/certify_calibration.sh` | **ALLOW** | 同上 (shell 側) |
| `cd hooks && python3 ../tools/pegasus/exec_calibrate.py` | **ALLOW** | cwd を追跡せず lexical path のみ |
| `systemd-run --user --scope -- pytest -q` | **ALLOW** | `systemd-run` が wrapper 集合に無く子を解析しない |
| `bash -lc "bash -lc 'bash -lc \"pytest -q\"'"` | **ALLOW** | shell `-c` 再帰が depth<2 で打ち切り許可に倒れる |

**したがって「一律 `tools/pegasus/` 判定」は厳格な壁ではなく、1 行の綴り替えで抜けられる状態だった。**
本 wave の narrowing (blanket → 明示表) はこれらの穴を広げないが、閉じもしない。
どれを本 wave で閉じるかを下記で裁定する。

## 1. 所見の裁定

### real・採用・scope 内 (実装する)

| # | 所見 | 裁定 |
|---|---|---|
| A-R3 | `-m` の後続を一律 data にすると script 実行 module (`cProfile`/`pdb`/`trace`/`runpy`) の実行対象が消える。**しかも分離形は現在すでに ALLOW** | real。`-m` の意味規則を「module が実行体。ただし script 実行 module では後続 script も実行対象」に修正する |
| A-R4 | `pytest.__main__` / `_pytest.main` で pytest 拒否を迂回できる (現在 ALLOW) | real。module identity を閉集合で正規化する |
| A-R6 | interpreter option の値を script と誤認し表を外せる (現在 ALLOW) | real。`_script_target` に忠実な prefix parser を入れる |
| A-R9 | 悉皆 meta-test は inventory 同期しか保証しない | real。**保証名を「inventory 同期」に狭める**。恒真な保証を謳わない |
| B-R2 | 二値表では「毎回 1 件 sanctioned 化」が形を変えて残る | real。**三値 (`unknown`/`local-ok`/`dispatch-required`) + 証拠 field + 昇格 lifecycle** にする |
| B-R3 | meta-test が直下限定で nested を取りこぼす | real (ただし runtime は現在 nested も deny)。列挙を再帰にする |
| B-R7 | 二値 class は `dispatch_compute.py` の self-gate や `run_probe.py` の意味的 site を表せない | real。class とは別に `reason` / `primary_gate` / `evidence` を持たせる |
| B-R8 | DW-G03 の「3 例」は独立していない (T126 の submit と collect は同一鎖) | real。**族の定義を「文書化済み login 手順と admission registry の不整合」とし、独立例は calibration 鎖と T126 鎖の 2 workflow** と記録する |

### real・採用・scope 外 (裁定パッケージへ返す。実装しない)

| # | 所見 | 理由 |
|---|---|---|
| A-R7 | cwd / 相対 / symlink で exact-path 表を外せる (現在 ALLOW) | 重量判定経路に cwd 追跡を新設する別設計。防護 tree 側には既に cd 追跡があり、そこへ寄せるか否かは択一 |
| A-R5 | `env -S` の GNU grammar と `shlex.split` の差 (現在 ALLOW) | 専用 parser かfail-closed かの択一。本 wave の面と独立 |
| A-R10 | shell `-c` 3 段ネストで解析打ち切り→許可 (現在 ALLOW) | 深さ上限の意味 (DoS 対策 vs fail-closed) の択一 |
| A-R8 | `systemd-run` 等の未解析 launcher (現在 ALLOW) | wrapper 集合の拡張は受理集合を広く動かす。**runbook の計測手順自身がこの経路である**ため、閉じ方は裁定が要る |
| A-R2 / B-R1 | `collect_receipt.py` の入力 cap は stderr だけでは足りない (JSON 全読み・`rglob` 全件・path 総 bytes) | [T-482] 択 (c) の実装本体。6 種の cap + 境界テスト + cap 下実測が要る独立単位 |
| B-R5 | 現行 sanctioned 5 本のうち `submit_silo_ladder_rung1.sh` は runbook が `unknown` と明記、`dispatch_compute.py` / `fetch_third_party.py` も任意 argv・無 cap の出力保持を持つ | **規範を厳格適用すると現在 ALLOW の 5 本を落とす**。grandfather か厳格かはユーザー裁定 |
| B-R4 | hook を分類の正本にすると runbook 実測・README 手順とのドリフトが機械停止されない | registry の所在 (hook 内 / pegasus 側 registry を hook が投影) は正本配置の択一 |
| A-R11 | `pytest -h` / `--co` / `-c` payload の過剰拒否 | 受理集合を広げる変更。族と独立 |

### refuted / 縮小

| # | 判定 |
|---|---|
| A-R1 / B-R6 の「プランが追記を反映していない」 | real だが**プランの落ち度ではなく親の追記が段 2 起草後に出たため**。plan v2 で解消する |
| brief の「族欠陥 4 例」 | **refuted**。`make_acquisition_receipt.py` は `certify_calibration.sh:633` から呼ばれる compute 側 helper であり、拒否が正しい (親が call site を実測確認) |
| A-R11 の「compute-only entry の `--help` を許すべき」 | 不採用。`run_probe.py --help` の拒否は設計どおりで、可用性の実害が実測されていない |
| B-R3 の「nested が runtime で通る」 | **refuted**。`python3 tools/pegasus/probes/anything.py` は現在 DENY。所見は meta-test の列挙漏れに縮小 |
| N1 「2〜3 倍」の増幅率 | nit。追記から倍率表現を落とし「入力比例・上限なし」に直す |

## 2. plan v2 (段 5 で実装するもの)

**単位は 1 つ。** 所有 = `hooks/guard_bash.py` + `orchestrator/tests/test_hooks.py`。docs は親が書く。

1. **admission registry (三値 + 証拠)**: `tools/pegasus/` の全実行体を
   `path → {class, reason, primary_gate, evidence}` で持つ。class は
   `local-ok` / `dispatch-required` / `unknown`。**hook が許可するのは `local-ok` だけ**とし、
   `unknown` と `dispatch-required` と未登録 (nested を含む) はすべて deny。
   現行 sanctioned 5 本は `local-ok` + `evidence: legacy-admitted` として**現状を正直に記録**し、
   実測済みの `fetch_third_party.py` だけ `evidence: runbook-§7.0-measured` とする。
   `_SANCTIONED_PATHS` は registry の `local-ok` から導出し二重表にしない。
2. **`-m` 実行体の意味規則**: module が実行体。位置引数は原則 data。ただし
   **script 実行 module の閉集合** (`cProfile` / `pdb` / `trace` / `runpy` / `timeit` / `coverage` 等)
   では後続 script を実行対象として分類する。module identity は `pytest` / `pytest.__main__` /
   `_pytest.main` を同一視する閉集合で正規化する。
3. **忠実な interpreter prefix parser**: `-W` / `-X` / `-c` 等の値を消費し、`--` と最初の script で
   停止する。shell 側も `-O` / `-o` / `--rcfile` の値を消費する。
4. **テスト**: 全 entry の LOGIN/SUSPECT 挙動、OTHER/COMPUTE の受理 bit 不変 (全 entry)、
   `-m` matrix (分離/密着/bundle/版付き)、registry 悉皆 meta-test (**再帰列挙**、保証名は
   「inventory 同期」に限定)、既存 pin (`test_hooks.py:915` / `:977`) は削除せず維持。

**本 wave で ALLOW へ反転させる entry は無い。** 族の症状 (`collect_receipt.py` の拒否) は
入力 cap と実測が揃うまで解かない。これは規律 2 の適用であって先送りではない —
無界入力の entry を実測なしに `local-ok` と記録することは、防壁を緩める方向の変異にあたる。

**意図した受理集合の縮小** (現在 ALLOW → 実装後 DENY):
`-m pytest.__main__` / `-m _pytest.main` 系、`-m cProfile|pdb|trace|runpy <重量 path>` 系、
`-W ignore|<option 値> <重量 path>` 系、`-mpytest <sanctioned path>` の借用系。
**過剰拒否の正例**も同時に登録する (`-m py_compile <path>`、`--collect-only`、`--message-file`、
`--help`、compute site の全形、非 Pegasus の全形)。

## 3. 変異事前登録 (DW-M01)

| ID | 変異 | 期待赤 (単一理由) |
|---|---|---|
| M1 | script 実行 module の閉集合を空にする | `-m cProfile <compute-only>` の DENY テスト。他層は当該入力を拒否しない (裏取り済: 現在 ALLOW) |
| M2 | `-m` 検出時に位置引数を候補へ戻す | `-mpytest tools/run_tests.py` の借用テスト。前段 provenance は非該当 |
| M3 | registry の `exec_calibrate.py` を `local-ok` にする | 既存 anti-glob control (`test_hooks.py:977`)。分類分岐だけが理由 |
| M4 | interpreter option の値消費を外す | `-W ignore <compute-only>` の DENY テスト |
| M5 | registry から 1 行削除する | 悉皆 meta-test のみ (runtime は未登録 deny のままなので挙動不変) = **diagnostic sensitivity pin** として別枠記録 (DW-M08) |
| M6 | registry を全 `dispatch-required` にする | `local-ok` 正例群 (fetch / dispatch / submit 3 本) が赤 = 過剰拒否の検出力 |

## 4. ユーザーへ返す裁定パッケージ (段 9 で worklog へ)

1. **grandfather か厳格か** (B-R5)。現行 `local-ok` 5 本のうち §7.0 実測があるのは
   `fetch_third_party.py` だけ。厳格適用は現在 ALLOW の 4 本を落とす。
2. **registry の正本配置** (B-R4)。hook 内に置くか、`tools/pegasus/` 側の
   machine-readable registry を hook と `check_docs.py` が投影するか。
3. **[T-482] 択 (c) の実装単位**。`collect_receipt.py` の 6 種 cap + 境界テスト + cap 下実測。
   実測はユーザー端末でしか行えない (下記 5)。
4. **現在開いている 4 経路をどう閉じるか** (A-R7 cwd/symlink、A-R5 `env -S`、A-R10 ネスト深さ、
   A-R8 未解析 launcher)。いずれも実測済みの live bypass。
5. **分類の bootstrap**。§7.0 の測定手順は計算ノードで動かず (実測: `artifacts/feasibility.txt`)、
   wave の Bash 面は main checkout の hook に支配される (実測済み・即復元)。
   したがって分類の実測はユーザー端末でしか行えない。恒久的な measurement surface を
   決める必要がある。
