# [T-276] 段 4 親裁定 + plan v2

段 3 の敵対レビュー 2 本はいずれも **NO-GO**。所見を real/refuted、採用/不採用、scope 内/外で裁定する。

## 1. 所見裁定表

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 「既定 trust root」は証明されない。`PATH`/`HOME` は子へ渡り、実行体は ambient PATH 解決 + hash のみ (既知 T-242) | real | **主張を狭める形で採用**。T-242 の統合は不採用 | 内 (表現) / 外 (T-242 実装) |
| A2 | endpoint/policy pin は自己整合検査で proxy の真正性を pin しない | real | **採用 (脅威モデルを D に明記)**。TLS/SPKI pin・attestation は不採用 | 内 (記述) / 外 (実装) |
| A3 | `tools=[]` と JSON schema は valid-schema な一行 C++ 注入と虚偽 auditor pass を止めない | real | **不採用 → 裁定パッケージ**。封じ込め事実を記録 | 外 |
| A4/B2 | receipt が成功 attempt にしか残らず、失敗行・init 失敗に transport identity が無い | real | **採用** | 内 |
| A5/B1 | production CLI が opt-in を渡さないので「解禁」が発火しない保証になる。T-236 ではない | real | **採用** | 内 |
| A6 | `bnode[0-9]+` の hostname 偽陽性で site 判定が fail-open | real | **transport 専用の追加 witness だけ採用**。site_policy 本体の変更は不採用 | 内 (leaf) / 外 (分類器) |
| A7/B8 | probe は 1 node・1 profile・1 CLI 版の証拠。一般化不可 | real | **採用 (記述の限定)** | 内 |
| A8 | 能力純増の会計が不足 | real | **採用 (D へ列挙)** | 内 |
| A9 | 新 gate の全層閉包表 | real | **採用 (D と worklog へ)** | 内 |
| B3 | 4 role が同じ transport を使う保証が無い (provider ごとに読む) | real | **採用 (run 単位 snapshot で解消)** | 内 |
| B4 | 固定 SHA vector が退化入力 (両 endpoint 同値・既に sorted) | real | **採用** | 内 |
| B5 | 拒否条件の positive control 不足 (列挙どおり) | real | **採用** | 内 |
| B6 | D96 が leaf API にしか掛からない。新 test の自走 harness / allowlist 登録漏れ | real | **採用** | 内 |
| B7 | 「既定は 1 bit も変わらない」の射程が広すぎる | real | **採用 (不変条件を限定)** | 内 |
| B-凍結 | s8b 除外は正当 (親境界を反証できず) | — | 親境界を維持 | — |

## 2. 裁定条件 ①②③ に対する親の立場 (worklog へそのまま書く)

- **① は「(96) が指摘した形」で閉じる。** (96) の所見は「proxy 値が**無検査の外部制御面**になる」であり、
  本 wave はその値を宣言済み policy との exact 一致・compute site・scheduler job witness・
  TLS override 不在で検査する。**閉じないのは「固定 proxy そのものが侵害された場合」と
  「実行体 trust root (T-242)」と「valid-schema な意味注入 (A3)」**であり、これらは
  「MITM を防止した」と書かない形で残余として明記する。
- **② は run 単位 receipt で閉じる。** endpoint 実値・その sha256・policy bytes sha256・site・
  job id を、成功/失敗/init 失敗の全 attempt へ同一 immutable copy で残す。
- **③ は独立 literal + 異値/逆順 synthetic vector で閉じる。** 期待値を実行時 env・production 定数・
  戻り値自身・policy loader から作らない。

## 3. plan v2 (段 2 プランからの差分だけを書く。それ以外は plan.md をそのまま採用)

1. **admission は run 単位で 1 回**。`_provider_set()` の**前**に 1 回だけ解決し、
   immutable な receipt を 4 provider すべてへ同一 object として渡す (B3)。
   provider ごとに `current_site()`・policy read を行わない。
2. **CLI flag を配線する** (A5/B1)。`--allow-pegasus-compute-transport` (store_true、既定 False) を
   `main → run_trial → _provider_set → ClaudeProjectedRoleProvider` へ通す。
   flag 省略時は leaf を一切呼ばない (site 判定も policy read もしない)。
3. **receipt を全 outcome へ残す** (A4/B2)。opt-in 時は
   - run 開始イベント (journal の先頭に `transport-admission` レコード) に receipt 全体、
   - 成功 attempt の `provenance.transport_receipt`、
   - **invalid attempt と provider-init エラーの event にも同じ receipt**
   を書く。既定 (flag 省略) 時は 1 byte も足さない。
4. **transport 専用の追加 witness** (A6)。leaf は `site_policy.current_site() == PEGASUS_COMPUTE` に加え、
   `source_env` に非空の `PBS_JOBID` があることを要求する。**`site_policy.py` は変更しない** —
   これは transport 固有の述語であり、site 分類の裁定 (`classify_site` の docstring) を変えない。
5. **consumer 側 exact gate** (B2/B6)。trial 側に receipt の exact schema 検査を置き、
   missing/extra/型不一致/hash 不一致を fail-closed で拒否する。
6. **退化しない test vector** (B4)。committed policy に加え、
   - http と https を**異なる値**にした synthetic policy、
   - endpoint key を**逆順**に持つ synthetic policy
   の 2 vector を足し、key 取り違え・片値複製・`sort_keys` 削除を検出できるようにする。
7. **positive control を B5 の列挙どおり足す**。エラー文言に proxy 実値・credential が
   含まれないこと (sentinel 不在) まで検査する。
8. **新 test file の自走契約** (B6)。`orchestrator/tests/README.md:107` の要求と
   `test_plain_runner_coverage.py:60` の meta-test を満たす形にする。
9. **主張を狭める** (A1/A2/A7/B7)。コード・docs のどこにも「MITM を防いだ」「CONNECT metadata しか
   見えない」と書かない。不変条件は「flag 省略時の child argv/env、既存 17-key response provenance、
   journal/report bytes が不変」に限定する。

## 4. scope 外 (実装しない。裁定パッケージへ回す)

- **A3**: coder 出力の boolean-expression AST/DSL 化と build/run の sandbox 化。
  **封じ込め事実**: `_site_admits_measurement` が Pegasus を拒否している間 (T-277 未着手)、
  計算ノードでは変異の build/run へ到達しない。**A3 は T-277 を開ける前の blocker として登録する。**
- **A1/T-242**: 実行体 digest の承認・起動直前再照合・固定 PATH/HOME。
- **A2**: TLS/SPKI pin、署名済み policy manifest、proxy attestation。
- **A6 (分類器側)**: `site_policy.classify_site` の強化 (job receipt/allocation identity)。
- **B2 (campaign 側)**: campaign WAL / proof chain への receipt digest 束縛。
  本 wave の provider を呼ぶ driver は `p3_autonomous_workload_trial.py` だけであり、
  `p3_s4_loop_trigger_gating.py` は role provider を呼ばない。
- T-236 (campaign dispatch task)、T-277 (measurement admission / build identity)、
  T-278 (`s6_proposal_rounds` の transport 非対称)。

## 5. 変異事前登録 (DW-M01。実装前に登録)

負例 (kill 期待。無効化すると受理集合が危険側へ広がる):

| ID | 変異 | kill 期待 |
|---|---|---|
| M1 | leaf の site 検査を常時 True 化 | 非 compute site 拒否 test |
| M2 | TLS override deny 検査を削除 | TLS 7 key 拒否 test |
| M3 | 未受理 proxy 名 (uppercase/no_proxy/all_proxy/ftp_proxy) の拒否を削除 | 未受理名拒否 test |
| M4 | endpoint 値の exact 一致を「key 存在のみ」に緩める | 値 drift 拒否 test |
| M5 | `https_proxy` へ `http_proxy` の値を複製 | 異値 synthetic vector |
| M6 | canonical JSON から `sort_keys=True` を削除 | 逆順 key synthetic vector |
| M7 | `PBS_JOBID` witness 検査を削除 | witness 欠落拒否 test |
| M8 | CLI flag の既定を True にする | 既定 off 境界 test |
| M9 | CLI flag を provider へ渡さない (配線切断) | CLI 配線 test |
| M10 | run 単位 snapshot を provider ごとの解決へ戻す | 4 role 一致 test |
| M11 | invalid attempt / init 失敗への receipt 付与を削除 | 失敗行 receipt test |
| M12 | policy path の symlink / regular file 検査を削除 | policy surface 拒否 test |
| M13 | エラー文言の redaction を外し proxy 実値を含める | sentinel 不在 test |
| M14 | consumer 側 receipt exact schema gate を削除 | missing/extra receipt 拒否 test |
| M15 | registry から transport policy 登録を外す | policy registry 閉集合 test |

正例 (過剰拒否検出。kill してはならない = 緑のままであるべき):

| ID | 正例 | 期待 |
|---|---|---|
| P1 | flag 省略の既定経路 | leaf 非呼出しで従来どおり成功 |
| P2 | compute + flag + 宣言一致 env + PBS_JOBID | admission 成立 (拒否しない) |

## 6. 実装単位

**1 単位 (単一 codex 実装子)**。理由: leaf・provider・trial (CLI/run-level snapshot/attempt receipt/
consumer gate)・policy・registry・tests が相互依存し、所有を素集合に切ると先行単位の land 待ちが
連鎖するため。docs と commit は親が行う。

## 7. 追記裁定 (段 5 投入後に親が確定。段 6 の must-fix)

**従量経路の遮断を transport leaf の受理条件へ入れる。** ユーザーの恒久指示は
「LLM 実行はすべてサブスクのログインで行い、従量 (使った分だけ支払う) 経路へ入る設定を作らない」
であり、「サブスクのログインが無いホスト (計算ノード等) から LLM を呼ぶ設計は裁定へ上げる」である。

本 wave の実測はこの条件を満たしている — 計算ノードは HOME を共有しており、
probe (request `877155`) は `env -i` で `PATH/HOME/LANG/LC_ALL/TERM` + proxy 2 key だけを渡して
rc=0 を得た。**キーを 1 本も置かずにサブスクのログインで通っている。**
したがって計算ノードは「サブスクのログインが無いホスト」ではなく、新たな裁定は要らない。

ただし解禁は「キーを置きたくなる場所」を 1 つ増やす。よって leaf の deny 検査へ次を追加する。

- `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`、
  `CLAUDE_CODE_USE_BEDROCK`、`CLAUDE_CODE_USE_VERTEX` が `source_env` に 1 つでも在れば
  **fail-closed で拒否する** (空文字でも拒否)。これらは子へ forward もしない。
- 変異 **M16** = この deny 検査を削除する。kill 期待 = 従量 env 拒否 test。
- 正例 **P3** = これらが 1 つも無い env では admission が成立する (過剰拒否しない)。

D116 には「本解禁はサブスクのログイン経路だけを使い、従量経路の env を機械的に拒否する」と書く。
