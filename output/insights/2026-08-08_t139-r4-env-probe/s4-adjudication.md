# [T-139] R4 環境 probe — 段 4 裁定・プラン v2・変異事前登録

```text
authority: none
default_effect: no-state-change
```

段 3 の 2 レンズはいずれも **NO-GO** (レンズ A = 事前登録/受理集合で blocker 8 件、
レンズ B = 実行環境/実装で blocker 8 件)。親は全 16 件を real / refuted に裁定した。
**refuted は 0 件、部分 refuted が 1 件**である。

---

## 1. 最重要の裁定 — 閾値を probe から導出しない (レンズ A B1 を採る)

**レンズ A B1 は real であり、親の P1 は誤りだった。**

`上限 = max(1.0, ceil_{0.1}(U) + 0.5)` は `U ≤ 3.5` の全域で `上限 ≥ U + 0.5` を満たす。
すなわち **probe の全観測値は、その probe が作った区間に必ず入る。**
したがって「probe が閾値を支持した」という主張は成立せず、`candidate_ready` は実質的に
「`U ≤ 3.5` か」の検査でしかない。core §14 の「実現値を必ず含む許容範囲」の禁止に、
少なくとも較正層でそのまま該当する。

**裁定 D-1: 閾値は「観測から作る」のではなく、`{1.0, 2.0}` という probe 前に凍結した
有限の梯子から選ぶ。**観測に合わせて数値を生成しないので B1 の自己充足は成立せず、
かつユーザー依頼の「実測で確定」を満たす。

**梯子の物理的意味 (恣意的な数字ではないことの根拠):**

| 候補 | 意味 | 48 core に対する割合 |
|---:|---|---:|
| `1.0` | 自 run の後始末残渣のみ。他テナントなし | 2.1% |
| `2.0` | 単一スレッドの他テナントが 1 本いる場合まで許容 | 4.2% |
| (梯子の外) | 本 study が前提とする静穏なノードが成立しない | — |

**判定規則 (probe 前に凍結。実測後の裁量ゼロ):**

| probe の終端 | 条件 | `a03` への効果 |
|---|---|---|
| `confirmed_1.0` | 13 窓すべて valid、かつすべて `≤ 1.0` | `[0, 1.0]` のまま。**支持する実測が 0 件から 13 窓へ変わる** |
| `escalated_2.0` | 13 窓すべて valid、最大が `(1.0, 2.0]` | `[0, 2.0]` へ変更。理由と観測値を逐語で残す |
| `not_feasible` | 13 窓すべて valid、最大が `> 2.0` | **数値を作らない。**観測値を添えて R4 (d) の材料としてユーザーへ返す |
| `incomplete` | 窓の malformed / 欠落、run 失敗、build・compiler witness 不成立 | 結論なし。理由を添えて返す |

**なぜ core §14 の禁止に当たらないか。** 禁止されているのは「実現値を**必ず**含む許容範囲」である。
梯子は 2 要素の有限集合であり、`> 2.0` の実現値に対しては**どの候補も選ばれない**。
したがって区間が実現値を必ず含むことはない。親の初版 P1
(`max(1.0, ceil_{0.1}(U) + 0.5)`) は `U ≤ 3.5` の全域で必ず含んだので、この点で誤りだった。

**この梯子自体が段 6 の敵対レビューの主要攻撃対象である。**倒れた場合の退避先は
「`[0, 1.0]` 固定 + feasibility の GO/NO-GO のみ」(数値を作らない) とする。

**なぜこれが裁定 R4 (a) を止めることにならないか。**
R4 (a) が要求したのは (i) probe を先に走らせること、(ii) 実測後に裁量が入らないよう
**写像を先に凍結する**ことである。D-1 はどちらも満たす — 写像は「観測 → 3 値」の決定的関数として
probe 前に凍結され、実測後の裁量はゼロである。R4 (a) の例示 (「最大値 + 0.5」) は
`例えば` と書かれた例示であり、裁定された選択肢は (a) すなわち「probe を先に走らせる」である。

**さらに、数値を fitting しても何も買えない。**本 wave の終端は裁定どおり
**段階 1 (承認待ち) 一括再提出**であり、`a03` の最終値はどのみちユーザーが承認する。
fitting した数値を出すより、`[0,1.0]` に対する実測の可否と生の観測値を添えて返す方が、
ユーザーの裁定材料として厳密に優れている。

**D-1 に伴い削除するもの:** `+0.5` の margin、cap `4.0`、`ceil_{0.1}` の丸め、
`max(1.0, ·)` の床。probe の比較は有理数の整数演算で行い、浮動小数を判定に使わない
(`48 × busy ≤ 1 × total` と `48 × busy ≤ 2 × total`、すなわち `48·busy ≤ total` と
`24·busy ≤ total`)。

## 2. 個別裁定

### レンズ A

| # | 判定 | 裁定 |
|---|---|---|
| A-B1 | **real** | D-1 で採用。閾値の導出を廃止 |
| A-B2 | **real** | 一般化しない。追補 A へ「単一割当て内の相関した 13 窓の記述的観測であり、割当て間変動は 0 点。分位点・被覆率・偽拒否率・26 割当てへの保証を主張しない」を逐語で書く (D-2) |
| A-B3 | **real (部分)** | strata を分ける (preflight / 30 秒 / 60 秒) を採用。ただし **3 arm・36 run の完全再現は採らない** — 時間予算に入らず、`DW-G01` の最安の生死確認を超える。probe preflight は build 直後に置かず、**prebuilt binary 検証後**に置いて本走の preflight を模す (D-3)。再現しない差 (13 窓 vs 36 窓、stock のみ) は追補へ逐語で書く |
| A-B4 | **real** | **測定を開始した attempt は 1 回、再走 0 回**と凍結する。窓を 1 つでも観測した時点で terminal。再 submit は「job が測定を一切開始していないことが scheduler 側証拠で確定した場合」に限り、事前上限 1 回。create-only の pre-submit 台帳へ attempt ordinal を先に予約する (D-4) |
| A-B5 | **real** | 導出契約を **Markdown 内 JSON ではなく独立 JSON blob** にする。runtime は `git cat-file blob <expected_commit>:<path>` で 1 度だけ read し、**同じ byte buffer を hash して parse** する。さらに受領証 → 再発行追補の一致 checker を親側に置く (D-5) |
| A-B6 | **real** | core §9 を検算した。「開始後の失敗は reject または判定不能。予備で置き換えない」は **core の逐語**である。したがって `a04` の「その分は `J_max` の余裕と**予備 2 本**が吸収する」は**偽** — 予備置換は開始前失敗にしか使えない。当該文を削り、`a03` 不成立の写像先を **`判定不能` 一意**に絞る (`reject` を選ばない)。§9 の分類は増やしていない (D-6) |
| A-B7 | **real** | `a08` の「唯一の差は `-DCCBENCH_TRACE`」を削除する。親も独立に実測済み (login node で `command -v gcc` = `/usr/bin/gcc`、`readlink -f` = `/usr/bin/x86_64-linux-gnu-gcc-11`)。`command_v` token・realpath token・実 CMake argv を別々に記録し、期待値には**計算ノード受領証の値だけ**を使う。stock TRACE=1 は「base stock witness」に限定し、3 arm の成立は主張しない (D-7) |
| A-B8 | **real** | 専用 namespace `output/env/pegasus/t139-r4-env-probe/<jobid>/` と、全射影行への `study_eligible=false` / `probe_series_id` / `purpose` を採用 (D-8) |

### レンズ B

| # | 判定 | 裁定 |
|---|---|---|
| B-B1 | **real** | driver cap に adjacency を算入していない。`12 × 5 = 60` 秒 + preflight 5 秒を phase 表へ明示し、cap を再計算する (D-9)。前 wave の「1500 秒 cap で後処理 60 秒」と同型 |
| B-B2 | **real** | TRACE=1 build failure を `set -e` で落とさない。捕捉して `builds[trace1].status=failed` + rc + log hash を残し、**既取得の 13 窓を理由付き成果物として保存してから**非 0 終了する (D-10) |
| B-B3 | **real** | run failure も同様。固定 schedule を最後まで走らず、**最初の run 失敗で `incomplete` 終端**とする (残り待機 540 秒を無駄にしない)。失敗行は必ず残す (D-10) |
| B-B4 | **real (主張縮小で閉じる)** | 単独性は**判定入力にしない**。`a03` はノード全体の busy を測るものであり、他テナントの負荷が入ることは仕様どおりである。hostname・`PBS_NODEFILE`・cpuset/affinity・PID 可視性 canary・foreign process snapshot は**受領証へ記録**し、feasibility の主張範囲を「このノード・この割当てで観測した node-global 負荷」に縮める (D-11) |
| B-B5 | **real** | driver の cap 判定を `time.monotonic_ns()` に統一する。epoch は記録専用 (D-12) |
| B-B6 | **real** | TRACE=1 の 180 秒 cap は未実証。configure と build の cap を分け、**TRACE=1 側は余裕 837 秒から厚く取る** (configure 90 / build 420)。elapsed を実測して受領証へ残す (D-13) |
| B-B7 | **real** | D-5 で閉じる (独立 JSON blob 化 + fence/重複 key 問題の消滅) |
| B-B8 | **real** | 出力 namespace を D-8 で固定。clean-tree 除外は**その namespace だけ**。`qsub -o/-e` は repo 外の具体ファイルへ。`s1-brief.md` を含む docs は **qsub より前に commit する** (D-14) |

## 3. プラン v2 (段 5 の実装子への指示に反映する差分)

段 2 プラン `s2-plan.md` を基礎とし、次を上書きする。

1. **D-1**: 導出写像を「観測 → `confirmed_1.0` / `escalated_2.0` / `not_feasible` / `incomplete`」の
   4 値判定へ置換。`+0.5` / cap 4.0 / 丸め / 床を削除。比較は
   `48·busy ≤ total` と `24·busy ≤ total` の整数演算。
2. **D-5**: 契約は `tools/pegasus/probes/t139_r4_env_probe_contract.json` (独立 blob)。
   `derivation-map.md` は説明文とし、その digest を指すだけにする。
   runtime は blob を 1 度 read → 同じ buffer を hash → parse。
3. **D-3**: preflight 窓は prebuilt binary 検証の後、TRACE=0 build の**直後ではない**位置へ置く。
   窓を strata (`preflight` / `wait30` / `wait60`) で分けて記録する。
4. **D-9**: phase 表へ adjacency (`12 × 5 + 5 = 65` 秒) を明示し driver cap を再計算。
5. **D-10**: build / run の失敗を捕捉し、全期待行を保存してから非 0 終了する finalizer。
   最初の run 失敗で `incomplete` 終端。
6. **D-12**: driver の cap 判定は monotonic。
7. **D-13**: TRACE=1 は configure 90 / build 420 の別 cap。
8. **D-8**: 出力は `output/env/pegasus/t139-r4-env-probe/<jobid>/`。
   全 TSV 行と JSON object に `study_eligible=false` / `probe_series_id` / `purpose`。
9. **D-11**: 単独性は診断のみ。判定関数へ渡さない (変異 M8 で機械検査)。
10. **D-4**: pre-submit 台帳 (create-only) と「測定開始後は再走 0 回」を契約 JSON に持たせる。
11. 変更なし: admission registry 3 entry (`dispatch-required`)、`_PEGASUS_EXPECTED_CLASSES` と
    `_PEGASUS_EXPECTED_ENTRIES` の両方更新、`/proc/stat` の集計行・8 列・負差分・窓長検査、
    compiler の三つ組 + 再照合、CMakeCache exact 照合。

**scope 外へ出すもの (裁定パッケージへ返す。実装しない):**

- 複数割当てによる上側許容限界の構成 (レンズ A B1 / B2 の本来の解)。
- 3 arm × TRACE=1 の完全な build witness (レンズ A B7 / レンズ B の候補)。
- producer の `attempts[].environment_observations[]` と probe の byte 契約の統一 (レンズ B)。
- pilot consumer 側の probe raw hard reject (レンズ A B8 の consumer 契約)。

## 4. 変異事前登録 (`DW-M01`)

実装後に無効化して**赤の理由が 1 つに絞れる**ことを確認する。前後に同じ入力を拒否する層が無いことを
コードで確認してから登録する。

| # | 変異位置 | 期待する赤 (単一理由) |
|---|---|---|
| M1 | 窓長 `10.000 ± 0.100` 秒の検査を外す | 窓長逸脱 fixture が `valid` になる |
| M2 | 列差分の負値検出を外す | 負差分 fixture が `valid` になる |
| M3 | 集計 `cpu` 行の 8 列要求を外す | 7 列 fixture が `valid` になる |
| M4 | `total ≤ 0` の検査を外す | `total=0` fixture が `valid` / 除算 |
| M5a | 境界 `48·busy ≤ total` を `<` へ変える | ちょうど `1.0` の fixture が `escalated_2.0` になる |
| M5b | 境界 `24·busy ≤ total` を `<` へ変える | ちょうど `2.0` の fixture が `not_feasible` になる |
| M5c | 梯子へ第 3 候補 (例 `4.0`) を足す | `> 2.0` fixture が `not_feasible` にならない |
| M6 | 「13 窓すべて valid」の要求を「valid 行だけで判定」へ変える | malformed 混在 fixture で結論が出る |
| M7 | 契約 blob の hash-then-parse を「hash 後に再 open」へ変える | 差し替え fixture が検出されない |
| M8 | 診断値 (`load1` / foreign count / cgroup) を判定関数へ渡す | **正例**: 診断値だけを変えた fixture で判定が変わる (変えてはならない) |
| M9 | `admission_registry.json` の 3 entry を 1 つ落とす | hook の未登録拒否と inventory 同期の**どちらか一方**に絞れることを確認してから登録 |
| M10 | TRACE=1 の `CMakeCache` exact 照合を緩める | `TRACE:STRING=0` の cache が TRACE=1 witness として通る |
| M11 | compiler identity の build 前再照合を外す | path/version/hash drift fixture が通る |
| M12 | 「測定開始後は再走 0 回」の terminal 判定を外す | 窓観測済み attempt が `resubmittable` になる |

M9 は `DW-M01` の「前後に同じ入力を拒否する層が無い」に抵触する可能性がある
(hook と inventory test の二重防壁)。**実装後に確認し、絞れなければ登録を取り下げて実効 gate へ再照準する。**

## 5. 段 5 の分割

実装子 1 本 (Codex `role=author`)。所有: `tools/pegasus/probes/t139_r4_env_probe.{pbs,sh,py}`、
`t139_r4_env_probe_contract.json`、`tools/pegasus/admission_registry.json`、
`orchestrator/tests/test_hooks.py` の 2 定数、`orchestrator/tests/test_t139_r4_env_probe.py`。
docs (`derivation-map.md`、追補 A 再発行、package) は**親が書く**。実装子は docs と commit をしない。
