# [T-316] 段 4 裁定 + plan v2 + 変異事前登録 (親)

## 1. 親 provisional 裁定の自己裁定

| # | 親の provisional | 裁定 | 根拠 |
|---|---|---|---|
| P1 | 本 wave は gate 本体を実装せず test-only まで | **refuted・撤回** | `_site_admits_measurement()` は `site_policy.OTHER` を受理する (`p3_s4_loop_trigger_gating.py:278-280`、`site_policy.py:45`)。任意 C++ 経路は Pegasus 以外の site で**今日すでに開いている**。さらに site 判定を持つのは trigger-gating だけで、backoff / sort は `site_policy` の参照が 0 件。「T-277 前だから安全」という前提が事実に反する |
| P2 | (b) sandbox が load-bearing、(a) は defense-in-depth | **refuted・撤回** | `docs/pegasus-runbook.md` に rootless sandbox backend (bwrap/unshare/seccomp/landlock/namespace) の記載が 0 件。DW-G04 (発火条件を満たす artifact path か計測 ID を brief に書けること) を満たさない。実装可能性が未証明の案を主柱に据えていた |
| P3 | auditor を独立防壁として数えない | **real・採用 (レンズ C の限定を追加)** | 3 レンズとも同意。ただし「security credit 0 の advisory / detective control」として残す。価値ゼロと混同しない (`claude_projected_provider.py:91,221,295` が role ごとに fresh・tool-less context を作る) |
| P4 | text 検査で C++ 意味論の完全性を主張しない | **real・維持** | D33 の既決と整合 |

## 2. 3 レンズ所見の裁定 (real / refuted、採否)

**real・本 wave で採用:**
- B-2 / A2-1: gate を 3 driver の `run_one_iteration()` 内に置くと `pipeline.evaluate()`、
  sort/trigger sweep、screening、preview、手動 patch が素通しになる。**共通隘路へ寄せる**
- C-3: 最小集合は「全 site・全 driver の role-derived build 既定拒否」
- C-6: `diff_quarantine.py:17-20` の docstring が、存在しない防壁 (source_digest + auditor が
  意味的逸脱の完全性を担う) を数えている。**恒真な保証の記述を訂正する**
- s2-plan 2: `quarantine()` が検疫**前**にファイルへ書く (`p3_s4_loop.py:207-213`)

**real・本 wave では実装しない (別 wave へ、裁定パッケージで返す):**
- (a) 軸別 typed IR / grammar (A2-2,3,4、B-6、A2-7): role 契約と 4 台帳 pin・manifest・adapter・
  unattended supervisor の二重契約に触るため、人間レビュー付きの独立 wave が要る
- (b) sandbox 一式 (B-1、C-1、C-8): Pegasus capability probe が先。DW-G04 未充足
- copy-out 境界 (symlink/FIFO、B-3、C-1): sandbox wave と一体
- template patch SHA 台帳 (A2-6): 独立の小 wave
- 局所欠陥: `*/` 未検査、backoff `value` の int 契約 (A2-2)、legacy build の timeout 欠落、
  `nm` の無隔離読み

**refuted:**
- なし (親の P1/P2 を除く)。3 レンズは互いに矛盾せず収束した

## 3. plan v2 — 本 wave の scope

**方針: 表現を狭めるのでも隔離するのでもなく、「分類されていない source は build させない」。**
D122 の先例 (明示 opt-in + exact policy admission) と同型にする。

1. **`orchestrator/campaign/build_admission.py` を新設。** provenance class を閉じた enum で定義する:
   `STOCK_OR_PINNED` / `MACHINE_SWEEP` / `HUMAN_REVIEWED` / `CODER_DERIVED`。
   `CODER_DERIVED` は明示 opt-in が無ければ `BuildAdmissionError` で fail-closed。
   opt-in は ambient な環境変数でなく、driver の CLI 引数から明示的に組み立てた値だけを受ける。
2. **`pipeline.evaluate()` に admission を必須引数として追加。** 既定値を持たせない
   (未指定は TypeError = fail-closed)。非テスト呼出しは 3 箇所だけである
   (`loop.py:145`、`screening_driver.py:148`、`t126_driver.py:519`)。
3. **`loop.run_campaign()` にも admission を必須で通す。** 全 caller (16 箇所) が自分の
   provenance class を明示する。これが所見 B-2 が要求した census そのものになる。
4. **`quarantine()` の順序反転** — structural validation 後にだけ file write する
   (`p3_s4_loop.py:207-213`)。
5. **docstring 訂正** — `diff_quarantine.py:14-20` の「意味的逸脱の完全性は source_digest +
   auditor が担う」を、実態 (structural containment のみ / source_digest は identity のみ /
   auditor は advisory / 意味 admission は未実装で build_admission が既定拒否する) へ改める。
6. **negative / positive integration test** — 各入口 (loop、screening、qualification、
   sort sweep、trigger sweep、preview) から `CODER_DERIVED` が opt-in なしで build へ到達しないこと
   (build spy で到達回数 0)、opt-in 時のみ到達すること、`STOCK_OR_PINNED` が過剰拒否されないこと。

**受理集合の変化:** 縮小のみ。`CODER_DERIVED` の既定が拒否になる。他 class は現行どおり。
opt-in 経路で従来の能力は保たれるため、Phase 3 の合成能力は失われない。

## 4. 成果物影響 (DW-G05)

| scope 項目 | 実装しない場合の成果物影響 |
|---|---|
| build_admission + evaluate/run_campaign 必須化 | certified 選択の受理集合が「LLM が書いた任意 C++」のまま。非 Pegasus site では今日すでに到達可能で、その run 由来の `median_tps`・変異台帳・材料レポートの全数値が非信頼コードの実行結果に格下げされる |
| 全入口の census | gate を入れても sweep / screening / preview から同じ bytes が build へ回り、受理集合は実質不変のまま「実装済み」と誤認される |
| quarantine 順序反転 | 検疫前 bytes が共有 tree の別 reader から観測可能なまま残る (reject された候補の source が一時的に実在する) |
| docstring 訂正 | 設計正本が存在しない防壁を二重計上し続け、proof chain の保証説明が誤ったまま参照される |
| integration test | 拒否集合の回帰検出力が 0 のまま。変異台帳に T-316 防壁が歯を持つ証拠を残せない |

## 5. 変異事前登録 (DW-M01)

受理集合を**縮小**する wave のため、承認外の過剰拒否を検出する正例を必ず含める。
各変異は、手前に同じ入力を拒否する検査が無いこと・赤理由が一つに絞れることを実装後に確認する。

| ID | 変異位置 | 変異内容 | 期待 kill (赤くなる test) |
|---|---|---|---|
| M1 | `build_admission.py` の `CODER_DERIVED` 拒否分岐 | 拒否を `pass` へ (常に許可) | 既定拒否 negative test (loop 入口) |
| M2 | 同 opt-in 判定 | 判定を `True` 固定 (恒真) | opt-in 無しで到達しないことを見る test |
| M3 | `pipeline.evaluate()` の admission 必須検査 | 既定値 `None` を許可へ | 未分類 caller の fail-closed test |
| M4 | sweep 入口の class 指定 | `CODER_DERIVED` → `MACHINE_SWEEP` へ差し替え | sweep 入口の bypass negative test |
| M5 (正例) | `build_admission.py` の `STOCK_OR_PINNED` 分岐 | 拒否側へ倒す | stock 計測が通ることを見る positive test が赤 = 過剰拒否検出力あり |

harness は `tools/mutation_harness.py` を使う (DW-M05)。本走は統合 commit 後。
他 wave が `flock` を保持していて取れない場合は、本走未実施を正直に記録する。

## 6. 段 5 の分割

実装単位は 1 本 (Codex `role=author`、`reasoning=high`、`sandbox=workspace-write`)。
`build_admission.py` 新設・`pipeline.py`・`loop.py`・全 caller・`p3_s4_loop.py` の順序反転・
`diff_quarantine.py` docstring・test が相互依存するため分割しない (DW-S06-B の単一化理由)。
docs 編集と commit は行わせない (凍結境界)。
