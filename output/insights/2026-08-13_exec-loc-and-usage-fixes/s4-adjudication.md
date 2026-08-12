# 段 4 裁定 — 実行場所分類の台帳反映 + wave 使用量 collector の 2 バグ修正

親が段 2 プランと段 3 敵対 2 レンズを real/refuted で裁定し、プラン v2 と変異事前登録を確定する。

## 0. 親が独立に再現した実測 (裁定の土台)

| # | 主張 | 出所 | 親の検証 | 判定 |
|---|---|---|---|---|
| E1 | 複製 collision は 1 件でなく 30 件 | lensA | `grep -c message_id_collision ledger-1.stderr` = 30 | real |
| E2 | 終端 `parentUuid` は replica 間で一致しない | lensA | `c9d22658-...` 対 `719f7bed-...` | real |
| E3 | 同一 message.id で終端 usage が食い違う群がある | lensA | `msg_011Cd9iWwXUEMz9erCs7xbA7` の終端 `output_tokens` = 10933 対 3 | real |
| E4 | 実測最大 delta は 19.7 MiB であって 20.6 MiB ではない | lensB | 842317824−821682176 = 20,635,648 B = 19.68 MiB (= 20.6 **MB**) | real |
| E5 | class 変更だけでは段 9 収集は unblock されない | 親・lensA・lensB 一致 | `collect_wave_usage.py:198` は `site_policy.refuses_heavy_work` のみ参照 | real |
| E6 | 有効 5 走 = 19.68 / 11.64 / 11.90 / 18.13 / 11.51 MiB、負 delta 1 走除外 | 親 | run-0 / run2 の base・peak を全て検算 | real |
| E7 | E3 の 2 replica は前 3 field が完全一致し output だけ異なる | 親が追加検証 | 両者 `input=2, cache_creation=3770, cache_read=31900` | real |

**E3 と E7 により、親の段 1 provisional 裁定 (P3) の「終端 usage 全一致」規則は refuted。**
実入力には「同一 model call の部分 snapshot」が存在し、終端 usage が一致しない。

## 1. 所見の裁定

### 採用 (real・本 wave で実装)

| ID | 所見 | 出所 | 裁定 |
|---|---|---|---|
| A1 | fingerprint に `parentUuid` を入れると実データを弾く | lensA must-fix | **採用**。E2 で確認。`parentUuid` は同一性証拠に使わない |
| A2 | 終端 usage 一致だけでは同一性証明にならない | lensA must-fix | **採用**。下記 §2 の dominance 規則へ置換 |
| A3 | requestId の条件付き抑止は別 call の誤統合を隠しうる | lensA must-fix | **採用**。resolver を検証完了まで状態を書かない多相にする |
| A4 | representative 選択後では loser 側 anomaly が消える | lensA must-fix | **採用**。member-local anomaly を dedup 前に全計算し、1 件でもあれば benign 化しない |
| A5 | 外側 argv 正規化は未知 option / abbreviation / 単独 `-` を値として飲む | lensA must-fix | **採用 (プランを不採用へ)**。§3 参照 |
| A6 | rc=3 が「正当な不実行」と「site 証拠の故障」を兼ねる | lensA must-fix | **採用**。suspect は rc=1 へ分離 |
| A7 | 新規テストが実測を単純化し恒真に近い | lensA must-fix | **採用**。raw から最小化した fixture を必須にする |
| A8 | 測定は本番 helper の argv (`--max-files=1000`) を測っていない | lensA must-fix | **採用**。evidence へ「既定 ledger argv の限定観測」と明記 |
| B1 | evidence の数値が単位取り違え | lensB must-fix | **採用**。E4/E6 の実測値へ差し替え |
| B2 | registry の `reason` は test_hooks golden が固定している | lensB should-fix | **採用**。reason 変更時は golden を同時更新 |
| B3 | evidence 文字列に非 §7.0 であることを明記 | lensB should-fix | **採用**。matcher 回避に見せない |
| B4 | ID 形式・欠落の契約が無い | lensA must-fix | **採用**。cross-file 緩和に使える ID を canonical 形式へ限定し、不正 ID は緩和対象外 |

### 採用しない / 裁定パッケージへ返す (scope 外の real)

| ID | 所見 | 裁定 |
|---|---|---|
| C1 | 段 9 収集を login で実際に受理する結線 (registry × hook × site_policy × collector) | **scope 外・real。裁定パッケージへ。** 受理集合を広げる新しい admission architecture であり、本 wave の台帳反映を越える |
| C2 | class flip (`local-ok`) 用の非 Pegasus exact allowlist | **scope 外・real。裁定パッケージへ。** D175 決定 6 の単調性を変える規範変更 |
| C3 | D233「分類測定はユーザー端末の手番」の改訂要否 | **裁定パッケージへ。** ユーザーの委任は「適切な場所を選ぶ」ことであり、AI が §7.0 の専有測定を自ら実行してよいという意味に**拡大解釈しない** (F159/F160 の再裁定が要る) |
| C4 | argv 別 admission (`--max-files=25` と `1000` の同一視) | **裁定パッケージへ。** §7.0 の記録範囲を越える |
| C5 | replica provenance の別フィールド保持 / `replicated` bucket | **不採用 (backlog)。** 成果物影響を 1 行で書けない (DW-G05) |
| C6 | `DW-S09` への rc 契約の追記 | **不採用。** L1 余白 1 byte で、既存の「`DW-O23` の成功結果以外は `DW-STOP`」という量化を弱める置換しか入らない (lensA should-fix)。**安全文を削らない**。rc 契約は `--help` と `docs/README.md` へ置く |

### refuted

| ID | 所見 | 理由 |
|---|---|---|
| R1 | 親の「中間 record 数がファイル間で異なる」(段 1) | lensA が指摘のとおり、親は top-level usage と nested `usage.iterations` の文字列出現数を record 数と取り違えた。**親の誤り。撤回する** |
| R2 | プランの「`reason` は自由に変えてよい」 | test_hooks golden が固定 (B2)。「投影だけでは検出されない」に限定 |
| R3 | プランの `parentUuid` fingerprint | E2 で refuted |

## 2. プラン v2 — 単位 2 (ledger replica resolver)

**同一性の公理を明示する。** 空でない canonical な `message.id` が一致する assistant 応答は、
同一の model call である。これは API の message id が応答ごとに一意であることに依拠する
**明示的な前提**であり、report schema と docs に書く。従来の実装はこの前提を置かず、
cross-file 再利用を一律 fatal にしていた。本 wave はこの前提を置き、**受理集合を意図的に変える**。

resolver は 3 相とし、**全検証が終わるまで representative map も invalid 集合も書かない** (A3)。

- **相 1 (member-local 検証)**: 各 member の anomaly (`alias_conflict`、既存 `invalid_requests`、
  `usage_final_below_prior_max` を含む) を先に計算する。1 件でもあれば group を benign 化しない (A4)。
- **相 2 (group 検証)**: `message.id` group について次を全部満たすときだけ benign replica とする。
  1. すべての member の `message.id` が canonical (非空・ASCII・長さ上限内)。満たさない member が
     あれば緩和対象外 (B4)。
  2. すべての member が終端 usage を持つ。
  3. **usage dominance**: ある member の終端 usage vector が、他の全 member の終端 usage vector を
     `USAGE_FIELDS` の全 field で `>=` する。**支配 candidate が 1 つも存在しない (incomparable) 場合は
     従来どおり `message_id_collision` を立てて fatal** (A2 の置換)。
     **[erratum 2026-08-13 段 6]** 本項の初版は「支配 member が一意に決まらなければ fatal」と書いたが、
     これは誤り。等値 replica は全 member が相互に支配するため candidate が複数になる。
     正しくは「**支配 candidate が存在しなければ fatal。複数 candidate が同値なら決定的に tie-break**」
     である。実装はこの正しい形になっており、実測群 1 (等値 4 replica) を受理する。
  4. terminal model が全 member で一致する。
  5. tool identity 集合が、支配 member の集合に対して他 member が部分集合である
     (部分 snapshot と整合する)。
  `parentUuid` と `agentId` は**同一性証拠に使わない** (A1/E2)。
- **相 3 (適用)**: 支配 member を representative とし、その終端 usage で **1 回だけ**計上する。
  root file の member があれば root、無ければ sidechains へ計上する。
  `requestId` group は message representative へ写像し、写像後の**相異なる model call** が
  2 件以上なら従来どおり `request_id_collision` を fatal にする (A3)。
  representative が invalid なら loser も全て invalid にする。

**実データに対する成立確認 (親が検算済み)**:
- 群 1 (`msg_011Cd9iV517nAAoCVuTwcsjt`): 終端 usage が 4 replica とも
  `(2, 10258, 16679, 428)` で一致 → dominance は等値で成立 → 1 回計上。
- 群 3 (`msg_011Cd9iWwXUEMz9erCs7xbA7`): `(2, 3770, 31900, 10933)` が
  `(2, 3770, 31900, 3)` を全 field で支配 → 支配 member 一意 → 1 回計上 (usage は 10933 側)。
- 既存 negative test の fixture (`1/2/3/4` 対 `10/20/30/40`): どちらも他方を支配しない
  (incomparable) → **従来どおり fatal、rc=2、両 metric 0**。**既存期待値を弱めない。**

**残る限界 (正直に書く)**: 30 群すべてがこの規則で解けるかは、実 transcript 全走でしか確認できない。
login では hook が ledger を拒否する (正しい挙動) ため本 wave では確認しない。
段 7 の worklog へ「合成 fixture では緑、実 1,045 file 入力での全群解決は未確認」と書く。

## 3. プラン v2 — 単位 1 (collector)

- **内側 argv を全て等号 1 token 形にする** (P5 の内側部分。プラン `:11-20` を採用)。
- **外側 argv の正規化は採らない** (A5)。外側 CLI では先頭 `-` の slug は `--project=<slug>` を
  要求し、`--help` と `docs/README.md` に明記する。理由: 正規化は未知 option・argparse
  abbreviation・単独 `-` を値として飲み、**受理集合を広げる**。ユーザー指示の欠陥
  (「内側 parser へ空白区切りで渡す」) は内側の等号化だけで閉じる。
- **rc 契約**:

  | status / 事象 | rc | 意味 |
  |---|---:|---|
  | `complete` | 0 | 収集できた |
  | `blocked` (site が `PEGASUS_LOGIN` と**確証**できた) | 3 | 実行場所規律により正当に走らなかった |
  | `blocked` (site が `PEGASUS_SUSPECT` = 証拠不足) | 1 | 分類の証拠が壊れている (A6) |
  | `incomplete` / `missing` / `error` | 1 | 収集が壊れた |
  | 外側 argparse 拒否 | 2 | argv が不正 |
  | `--help` | 0 | |
  | 未知 status | 1 | 成功へ倒さない |

- artifact は現行どおり**先に**保存し、rc だけを変える。`KeyboardInterrupt` は握り潰さない。
- `docs/dev-wave/core.md` は**変更しない** (C6)。

## 4. プラン v2 — 単位 3 (admission metadata)

- `class` は **`unknown` 据置**。理由は 2 つで、防壁の存在は主理由ではない。
  1. 実測は §7.0 の canonical 手順 (専有 scope) ではなく共有 service cgroup の delta である。
  2. 測ったのは ledger 既定 argv (25 file) であり、本番 helper が渡す `--max-files=1000` の
     cap 境界を測っていない (A8)。
- `reason` を実装に合わせて是正する (hard cap は存在する)。**test_hooks golden を同時更新** (B2)。
- `evidence` は E4/E6 の実測値へ差し替え、非 §7.0 であることを明記する (B1/B3)。
  数値: 有効 5 走、最大 +19.7 MiB、margin +128 MiB、certified 147.7 MiB、負 delta 1 走除外、
  対象 argv = 既定 `--json` / 25 file、入力母集団 1,045 file / 1.40 GB。
- `docs/pegasus-runbook.md:460` の投影行を同じ evidence へ揃える (親が書く)。
- `tools/check_docs.py` の production は**変更しない**。実測表へ行を足さない。

## 5. 変異事前登録 (DW-M01)

各変異は単一理由性を満たす位置に置く。受理集合を**変える** wave なので、
過剰拒否を検出する正例も登録する。

| # | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | `_collector_argv` の `--project=` を分離 2 token へ戻す | KILLED | 内側 argv の形だけを固定する node がある |
| M2 | `_run` の rc 写像を全 status 0 へ戻す | KILLED | rc 契約 node のみが落ちる |
| M3 | `main()` の `except Exception: return 0` を復活 | KILLED | 例外経路 node のみ |
| M4 | resolver の dominance 検査を外し message.id 一致で常に dedup | KILLED (negative) | 既存 negative fixture が incomparable |
| M5 | dominance を「全 field 等値のみ」へ狭める | KILLED (**正例**) | 部分 snapshot fixture が過剰拒否される |
| M6 | requestId 抑止を無条件にする | KILLED (negative) | requestId 再利用 fixture のみ |
| M7 | 相 1 の member-local anomaly 先行計算を外す | KILLED (negative) | loser 側 anomaly 隠蔽 fixture のみ |
| M8 | registry の evidence を旧文字列へ戻す | KILLED | check_docs 投影 + test_hooks golden |
| M9 | `_NON_PEGASUS_ADMISSION_FALLBACK_PATHS` から ledger を外す | KILLED | fallback 集合一致 node のみ |

期待 node は fix 後の最終 commit で再導出する (DW-M07)。

## 6. 成果物影響 (DW-G05)

- 単位 1 を実装しないと、実 slug で収集が静かに失敗し rc=0 で成功に見える → 工数台帳が全 wave 欠測。
- 単位 2 を実装しないと、並列 subagent を使った全 wave で rc=2 となり使用量が 1 件も記録されない。
  誤った方向 (単純 dedup) で実装すると token を最大 4 重計上し台帳の値が壊れる。
- 単位 3 を実装しないと、registry の `reason` が実装と食い違ったまま残り、
  evidence に非 canonical 測定の事実が残らない → 後続の分類判断が誤った前提を引く。
- C1/C2 を返さずに実装すると、hook の受理集合が本 wave の裁定外で広がる。

## 7. 所有分割 (段 5)

- **単位 A**: `tools/collect_wave_usage.py` + `orchestrator/tests/test_collect_wave_usage.py`
- **単位 B**: `tools/claude_session_ledger.py` + `orchestrator/tests/test_claude_session_ledger.py`
- **単位 C**: `tools/pegasus/admission_registry.json` + `orchestrator/tests/test_hooks.py`
  (+ 必要なら `orchestrator/tests/test_check_docs.py`)
- **親専有 (docs)**: `docs/pegasus-runbook.md`、`docs/README.md`、spool fragment、insights、裁定パッケージ
