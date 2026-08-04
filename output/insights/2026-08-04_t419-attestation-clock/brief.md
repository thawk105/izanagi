# 段 1 brief — [T-419] 実行時 attestation の effective_clock

## 裁定 (一次資料)

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-03-task-def-rulings.md` §4 (2026-08-04):
**「述語を正とし、較正を取り直す。取得時に全要素が帯内であることの受入検査を同時に入れる。」**
= D143 決定 (3) の択一 (b) + 取得時受入検査。台帳未記録なので本 wave が fragment 化して land する。

## 段 1 前提実測 (DW-S01) — 承認済み裁定の前提を覆す新事実

述語は「期待列の中央値 ±tolerance_pct に**観測列の全要素**が入ること」
(`orchestrator/campaign/execution_guard.py` `_independent_comparison_passes`)。
probe は `/proc/cpuinfo` の `cpu MHz` を論理 CPU 順に読む
(`orchestrator/campaign/env_attestation.py:434`, `method="proc-cpuinfo"`)。

**実測 1 (repo 内の全 attestation 成果物 16 件、追加計測なし)。**
Pegasus 計算ノードで取られた 16 スナップショットのうち **16 件すべてが 1〜2 個の帯外要素を持つ**。
残り 46〜47 要素は例外なく厳密に 2101.0。帯外値は 2951.7〜3080.9 MHz。
外れ位置は毎回異なる (index 0,1,5,6,8,10,11,24,28,34,38,40,43,44)。
うち registered 較正 = index 40 (3080.935)、F97 が記録した実行時 observed 列 = index 34 (3076.13)。

**実測 2 (機序の同定、ログインノードで読み取りのみ・負荷ゼロ)。**
`/proc/cpuinfo` を読むと同時に `/proc/self/stat` から自プロセスの走行 CPU を採ると、
6 回中 6 回、**自分が走っている CPU が帯外側に現れた** (self_cpu=80 が毎回 out に含まれる)。
他の帯外は共有ログインノード上の他者負荷で説明が付く。

**結論 (裁定の前提を覆す部分)。**
帯外要素は熱の都合で偶発するブーストではなく、**観測しているプロセス自身のコアが読み取り時に
turbo にいる**という観測者効果である。したがって:

1. **較正を取り直しても、取得時受入検査 (全要素が帯内) は構造的にほぼ確実に落ちる** (16/16)。
   D143 が「再びブースト混じりなら同じ穴が再発する」と書いた懸念は、確率的でなく決定的である。
2. さらに重要なこととして、**observed 側にも常に同じ観測者効果が乗る** (F97 の実行時 index 34 が
   その実測である)。よって**どれほど清潔な較正を登録しても、実行時述語は通らない**。
   裁定文が期待した効果「これが塞いでいた Pegasus 上の campaign 実行が開く」は、
   取り直しだけでは達成されない。

**実測 3 (テスト代表性)。**
`orchestrator/tests/test_s8b_floor_campaign.py:3457-3473` の `attestation_probe` fixture は、
較正サンプルを帯 `[median-delta, median+delta]` へ `min(max(...))` で**クランプ**して
runtime 観測を合成し、さらに `tolerance_pct` を 100.0 に置き換えている。
docstring 自身が「これは物理 Pegasus の実 attestation ではない」と書いている。
よって **E2E 経路は構造的に F97 の型を検出できない** — 実 probe が決して生成しない観測を
与えて guard を通しているためである。S2 の positive control はこの穴を直接撃つ。

この新事実は裁定時点で未見であり、`DW-S04` に従い親は不採用にせず、
新事実付きでユーザー再裁定へ返す (下記 U-1)。裁定の**別の半分**である取得時受入検査は、
どの再裁定でも正しさが変わらないため本 wave で実装する。

## scope (実装する)

- **S1: 取得時受入検査。** `--certify` 経路 (`orchestrator/calibrator/cli.py::_certify_main`) で、
  registered/ へ publish する候補 artifact が「**自分自身を観測値として実行時述語にかけたとき受理される**」
  ことを検査し、満たさなければ `rejected` にして publish しない。
  実装は execution_guard の consumer 側再計算を**共有せず独立に書く**
  (`_independent_comparison_passes` の「issuer の判定コードから意図的に独立」という設計を壊さないため)。
  独立 2 実装の等価性は表駆動テストで pin する。
  - **成果物影響 (DW-G05):** 放置すると、将来 Pegasus 較正を取り直したときに再び自己不整合な参照を
    registered/ へ publish でき、env 契約と proof chain が「実行時に決して通らない参照」を指したまま
    certified 選択の根拠になる。S1 は registered/ の受理集合を「自分自身の述語を通る artifact」へ狭める。
- **S2: F97 の再発検知 (positive control)。** 「取得時検査を通った artifact は実行時述語を自分自身に対して
  満たす」という不変条件テスト (合成データ) と、**現登録 Pegasus 較正が現にそれを満たさない**という
  事実 pin (probe 裁定後の wave が反転させる)。
  - **成果物影響 (DW-G05):** 放置すると F97 の型 (参照が自分の受理条件を満たさない) が無検査のままになる。
- **S3: 記録。** 新事実 (実測 1/2)、裁定の台帳化、U-1 の裁定パッケージ。

## scope 外 (実装せず裁定へ返す)

- **U-1 (ユーザー裁定): 観測者効果を観測から外す方法。** 述語も較正も直さずに済む道は無い。候補:
  - **(α) probe を「自分の走行 CPU を移しながら K 回読み、論理 CPU ごとに最小値を採る」へ変える。**
    静穏なコアは全読み取りで定格 → 全 48 要素が帯内になり、**述語は一切緩まない**。
    真に他プロセスが走るコアは全読み取りで高いままなので検出力を失わない。
    `effective_clock.method` 文字列が変わるため凍結 bytes と pin の更新 (= 較正取り直し) が同時に要る。
  - **(β) probe が自分の走行 CPU id を記録し、述語がその 1 要素だけを除外する。**
    受理集合が 47/48 へ緩む。schema に field 追加が要る。
  - **(γ) 帯外を「最大 1 個まで」許す。** 根拠が弱く β の劣化版。
  - **推奨は (α)。** 規律 1 (観測者効果の分離) の直接適用であり、受理集合を緩めない。
- **U-2: 較正の再取得ジョブ。** (α)/(β) いずれでも `method` 文字列と凍結 bytes が動くため、
  probe 是正と再取得は不可分である。`tools/pegasus/submit_certify.sh` の sanctioned 経路で行い、
  `orchestrator/campaign/env_contract.py:186-192` の path + sha256 pin、
  `orchestrator/tests/test_env_contract.py:239,649`、`orchestrator/tests/test_s8b_floor_campaign.py:3239`
  を同時に更新する。**本 wave では行わない** (裁定 U-1 が先行する)。

## 不変条件

- 規律 2: 述語を緩めない。S1 は受理集合を**狭める**方向にしか働かない。
- 規律 1: U-1 の推奨 (α) は観測者効果の除去であり、検出力を落とさない。
- `DW-O09` pin 閉包 (実測済み): 凍結 bytes を pin するのは
  `orchestrator/campaign/env_contract.py:186-192` (path + sha256)、
  `orchestrator/tests/test_env_contract.py:239-242,649-650`、
  `orchestrator/tests/test_s8b_floor_campaign.py:3239`。
  `test_frozen_artifacts.py::FROZEN_MANIFEST` (23 件) に当該 calibration は**含まれない** (実測)。
  registered/ 配下の登録済み較正は Pegasus の 1 件のみ (linux-baremetal は registered/ を使わない別 path)。
  **本 wave は凍結 bytes を変えないため `DW-O10` は不成立。**
- `DW-O13`: S1 の gate 入力 = 候補 artifact 自身の `attestation_profile.effective_clock`
  (`samples_mhz` / `tolerance_pct`)。同名識別子の二義化なし。

## provisional 裁定 (親の暫定・攻撃対象)

- **(P1)** S1 を単独で入れてよい。取り直しが当面不可能でも、S1 は「今日より悪い状態」を作らない
  (campaign は既に塞がれている) 一方、F97 の型の再発を構造的に止める。
- **(P2)** S2 の「現状は満たさない」事実 pin を landing してよい。反転を強制するので恒真ではない。
- **(P3)** probe 是正 (U-1) は受理集合と凍結 bytes に同時に触れるため本 wave で実装しない。
- **(P4)** S1 の実装は execution_guard と**共有しない**独立実装とし、等価性をテストで pin する。

## 成果物の形

- コード: `orchestrator/calibrator/` への取得時検査 + テスト (`orchestrator/tests/`)。
- docs: spool fragment (worklog / decisions / failures) + insights 逐語。
- 裁定パッケージ: U-1 (probe 是正の択一と推奨)、U-2 (再取得の実行計画)。

## 並列分割方針

- 段 2: codex read-only plan 1 本。
- 段 3: 敵対 2 レンズ (A: 新事実の反証 / B: S1・S2 の設計と受理集合)。
- 段 5: codex author 1 本 (S1 + S2 は同一ファイル群のため分割しない)。
- 段 6: 敵対レビュー 2 本。
