# 段 6 fix (U1 所有分) 完了報告 — Claude opus

**pytest は 1 度も走らせていない** (ログインノード `pegasus02`)。静的検査と probe のみ。

## 変更

- **F1 (must-fix = レビュー A の MF-2)**: `orchestrator/tests/test_check_ai_provenance.py` の `_run_range` (`:260`) を
  `provenance.main(site=site_policy.OTHER)` にし、直接呼びの既存 node **27 件**も同様に固定した (計 28 箇所)。
  新規 node 2 本で挙動側と呼出規約側の両方から退行を止める。
- **F2 (nit → 親裁定で採用)**: `tools/check_ai_provenance.py:903-927`。共通 6 条件を `carrier_ready` に括り出し、
  `elif carrier_ready:` で理由 finding を 1 本出す
  (`… AI-Agent-Correction commit が AI-Agent-Waiver 行を持つため前方訂正の担い手になれない`)。
  **M4 の事前登録 literal `and not correction.waiver.exact` は逐語のまま保存** (count=1)。
  `elif` にしたので M4 変異時は理由 finding が出ず受理へ倒れる = 帰属が一意。
  **受理集合は 1 bit も動かない** — 失格経路は target 側 finding が抑止されないため変更前から rc=1 であり、finding が 1 本増えるだけ。
- **F3 (nit → 親裁定で採用)**: 新規 node 1 本。後の commit ほど速く終わる非対称遅延 (0.05s × 逆順) を入れ、
  `findings` が入力順のままであることを assert する。

## probe の実測 (repo 内には一切書いていない)

    P1 AST 不変条件:   provenance.main 呼出 = 33 件, site= 未指定 = []
    P2 F2 実 git 履歴: rc=1
       stderr: 0a19059f98ee target merge: AI-Agent trailer がない
               d40f6c83cf16 forward correction: AI-Agent-Correction commit が
                 AI-Agent-Waiver 行を持つため前方訂正の担い手になれない
               check_ai_provenance: 3 件中 2 違反
    P3 negative control (waiver 無し): rc=0 / 担い手 finding 不在: True
       stdout: forward-corrected=1 target=0a19059f... correction=41ca4433...
    P4 F3 順序: elapsed=0.32s / findings == expected (入力順): True
       実完了順 index: [5,4,3,2,1,0] = 入力順の完全な逆
    P5 逐語: 理由 finding count=1 / M4 literal count=1 / carrier_ready=3
    F1 probe: fixed rc=0 "1 件、違反なし" / 退行再現時 AssertionError 発火
       実ホスト current_site() = PEGASUS_LOGIN   ← MF-2 は生きた危険だった
    M4 変異 probe (and not correction.waiver.exact 削除):
       rc=0, forward-corrected=1 が出る → 期待 node の 3 assert が全滅 = KILL
    M8 変異 probe (pool.map → as_completed):
       findings == 逆順: True → 新 node が決定的に KILL
    git log <epoch>..72849d3 | grep -c AI-Agent-Waiver → 0

最後の 1 行が重要: **受入基準 (i) の byte 一致 range には waiver commit が 0 件**なので、
F2 の新 finding はそこでは発火しえず baseline byte 一致は保たれる。

## 新規・変更 node と KILL する変異

| nodeid | 種別 | KILL |
|---|---|---|
| `test_range_helper_pins_site_and_never_reads_the_ambient_site` | 新規 | `_run_range` の `site=` 落ち (ambient 化 = 実 qsub 退行) |
| `test_every_checker_main_call_in_this_suite_pins_the_site` | 新規 | 新設 node の `site=` 渡し忘れ (33 件走査、floor 30 で恒真化防止) |
| `test_waiver_disqualified_correction_carrier_explains_the_reason` | 新規 | 理由 finding の削除 (規律 3 の沈黙化) |
| `test_audit_history_findings_follow_input_order_under_skewed_latency` | 新規 | **M8** (決定的。逆順を実測) |
| `test_waiver_does_not_widen_forward_correction_acceptance` | 変更 | **M4** (変異 probe で rc 1→0 を実測) |

## F1 で `site=` を固定した呼出の全列挙

`grep -n "provenance\.main(site=site_policy\.OTHER)"` → **28 箇所** (helper 1 + node 27)。

- helper: `:260 _run_range` — 経由する test 関数 21 / parametrize 展開後 **29 node**
- `--range` 直接呼び 10: `:710` `:732` `:748` `:755` `:776` `:799` `:815` `:851` `:882` `:1011`
- `--message-file` 直接呼び 17: `:1037` `:1079` `:1147` `:1183` `:1214` `:1229` `:1256` `:1275`
  `:1974` `:2000` `:2041` `:2073` `:2096` `:2131` `:2154` `:2640` `:2676`

`provenance.main` へ到達する test 関数は 52 / **62 node**。site gate 専用 5 本は元から `site=` 明示済みで無改変。
**39 node (29+10) がこのホストで実 PBS job を投げる状態だった** (`current_site()` = `PEGASUS_LOGIN` を実測)。

## 所有外への波及

**なし** (`git status --short` で変更は所有 2 ファイルのみ)。F2 は stdout/stderr の出力が 1 行増える経路を新設するが、
rc を素通しする `task_run_check.py` / `dev_waves/cli.py` は rc しか見ないので影響なし。
lint 設定は repo に存在しない。

## 期待して赤くなる finding — **0 件**

`test_waiver_does_not_widen_forward_correction_acceptance` の `3 件中 2 違反` は実装に合わせた期待値の更新であり、
probe P2 で実出力を実測して一致を確認済み。

## 親への申し送りと親裁定

1. **M8 の期待 KILL node を新 node へ差し替えるべき** (旧 node は M8 に対し確率的なまま)。
   → **親裁定: 採用。** `s4-adjudication-plan-v2.md` §5 の期待 node 更新節に反映済み。
2. **M4 は期待 node が 2 本になった** (新 F2 node も落ちる。原因は一意)。
   → **親裁定: 採用。** 同上に反映済み。
3. D105 の列挙に F2 の理由 finding を書き足す判断が要る (受理集合は不変、出力のみ増える)。
   → **親裁定: 採用。** D105 の「研究状態への影響」末尾に「出力の追加であって受理集合は不変」と明記した。
