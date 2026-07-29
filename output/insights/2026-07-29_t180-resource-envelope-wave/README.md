# T-180 job 単位 resource envelope — 材料・逐語・変異台帳

worklog 2026-07-30 (65) の一次資料。本 directory の逐語は改変しない。

## 本 wave が確定したこと

`codex-cli 0.146.0` は turn / token / wall-clock / retry の**上限 flag を持たない**
(`codex exec --help` 全文で確認)。したがって job 単位の資源封筒は wrapper 側でしか強制できない。
段 1 の実測 (`probe/`) で次の 2 つの seam が実在することを確かめ、その上に launcher を作った。

1. stdout `--json` の `thread.started.thread_id` は rollout の `session_meta.session_id` と
   ファイル名に一致する → **wave の受理集合を session_id で決定的に束縛できる**
   (T-179 が「cwd 部分一致では固定できない」として本 ID へ送った積み残し)。
2. rollout JSONL は**実行中に逐次 flush** される (`probe/liveness.tsv`: `token_count` が
   12/20/29/37/39 秒で 1→5) 。一方 stdout の usage は `turn.completed` の 1 回だけ
   → **live 停止は rollout tail、終了判定は stdout 最終 usage** の二重 metering。

`turn.completed.usage` は rollout 最終 `total_token_usage` と完全一致し、
T-179 の "CLI reported" (`input - cached + output`) がそのまま receipt に載る。

## 射程 (誇張しない)

- **hard cap は wall-clock だけ**である。`model_calls` と token は
  「観測可能な proxy による best-effort 停止 + 事後 fail-closed 判定」であり、
  usage は model call 完了後にしか観測できないため最大 1 call 分の不可視 overshoot がありうる。
  receipt は `model_calls_semantics` と `possible_unobserved_overshoot` でこれを表出する。
- `setsid()` で process group を逃れた子は killpg の射程外である。封じ込めは**行わず**、
  receipt に残存を記録するに留める (`escaped_process_containment`)。
- probe が示すのは CLI 0.146.0 の 1 実走で観測できた挙動であり、buffering や版差での
  一般性は証明していない。実装は metering evidence 欠落を非採用にすることで吸収する。

## 成果物

| path | 役割 |
|---|---|
| `tools/codex_worker_launch.py` | `run` / `check-receipt`。封筒の強制と receipt / manifest の発行 |
| `tools/codex_worker_ledger.py` | `--manifest` selector を追加 (T-179 の台帳を拡張) |
| `orchestrator/tests/test_codex_worker_launch.py` | fake codex による回帰 (実 inference なし) |
| `orchestrator/tests/test_codex_worker_ledger.py` | manifest 経路と usage 検査の回帰 |

## dogfood — 本 wave 自身の worker を launcher 経由で起動した

DW-O01 の結線は T-184 の所有 (「DW-O01 と worker 契約へ一度だけ反映する」) であり、
本 wave では docs を書き換えない。死蔵を避けるため、**段 6 のレビュー 3 本を新 launcher で起動**した。

| job | model_calls | cli_reported | wall_clock_s | outcome |
|---|---|---|---|---|
| s6-review-a | 33 | 192,930 | 1,101.5 | accepted |
| s6-review-b | 34 | 232,757 | 1,229.1 | accepted |
| s6-focus | 66 | 412,833 | 1,106.5 | accepted |
| **計** | **133** | **838,520** | — | — |

3 件とも `check-receipt` rc=0。manifest (`launcher-run/wave-manifest.json`) は
3 job の session を wave へ束縛した。**この dogfood が N-1 (後述) を捕まえた。**

`launcher-run/` に凍結するのは receipt 3 件と manifest だけである。生の
`attempt-0001.events.jsonl` / `stderr.log` / `output.md` (計 2.1MB) は repo に置かない。
receipt が各成果物の `sha256` と `bytes` を pin しているため、証拠としての検証可能性は
receipt 側で閉じている (review 本文自体は `s6-review-a.md` / `s6-review-b.md` / `s6-focus.md`
として逐語凍結済み)。

## 実データ受入 (親実測、F54 の要素単位照合)

T-179 が凍結した 10 session_id で manifest を作り (`t179-10-sessions.manifest.json`)、
親が `--manifest --json --strict` を実走した。

```
rc=0  issues={}  sessions=10  model_calls=434  cli_reported=2,757,982
```

**stage 別 6 値を逐件照合し全一致** (plan 1/39/224,150、consult 2/62/392,185、
author 1/47/171,736、review 2/87/544,553、fix 2/100/605,734、focus 2/99/819,624)。
さらに session 単位で manifest の `job_id` 束縛が 10/10 正しいこと、
distinct job_id が 10 であることを確認した。旧 `--cwd-contains` 経路も同値を返し、
既存経路の drift がないことを確認した。集約一致だけを根拠にしない (F54)。

## 段 3 / 段 6 が捕まえた実在の欠陥

- **`cli_reported` が負になりうる** (段 3 A-3、親が実コードで再現):
  `_validated_usage` は `cached_input_tokens > input_tokens` を通し、
  `_billable({input:100, cached:200, output:1})` = **-99** を返した。T-179 から継承した欠陥で、
  token 上限をこの値の上に作ると自明に破れる。本 wave で malformed として拒否する。
- **N-1 receipt schema の後方互換破壊** (焦点再レビュー、親が実測で確認):
  fix round 1 が `schema_version=1` のまま必須 field を 27→31 に増やしたため、
  **本 wave が数時間前に生成した dogfood receipt 2 件が rc=2 で拒否**された。
  fix round 2 で新規は v2 とし、checker が v1/v2 の双方を読めるようにした。
  **実運用 1 件を dogfood していなければ、この破壊は wave 内で発見できなかった。**
- **manifest 追記位置** (F-P1、親が独立に発見): `_append_manifest` が attempt 完了後に
  呼ばれており、launcher が途中で殺されると費消済み session が台帳から消えた。
  rollout 相関直後へ移した。

## 変異台帳 (統合 commit `24d2672` の後に本走、DW-O19)

harness は親の監査計器であり repo に commit しない (実装子が自分を採点する構図を避ける)。
`flock` 単一走行 guard、置換の一意性 assert、内容比較での復元検査、
`FAILED <node>` の正規化記録を持つ (DW-M04 / M05 / M08)。

**初回 10 本: KILLED 7 / SURVIVED 1 / 別理由赤 2。**
DW-M02 に従い初回結果を消さず erratum として残し、実効 gate へ再照準した。

| ID | 初回 | 原因 | 再照準後 |
|---|---|---|---|
| M18 | SURVIVED | 変異位置が terminate 路で、期待 node は `_normal_reap` 路 (F28 の誤照準) | `_normal_reap` へ再照準し **KILLED** |
| M19 | 別理由赤 | fix2 が新設した単一理由 node が kill していた。spec が旧 node 名を登録していた記帳誤り | 期待 node を訂正し **KILLED** |
| M14 | 別理由赤 | 空 manifest は schema の `1..1024` 検査で先に落ちる。records 検査は T-179 の M10 に mask される | schema 検査へ再照準し **KILLED** |

**最終: 10/10 KILLED。** 復元後、対象 2 ファイルは commit 済み内容と byte 一致。

## scope 外として裁定パッケージへ返すもの

1. **DW-O01 の結線と stage 別の上限値** → T-184 の明示所有。
   `docs/dev-wave/**` の残予算 38 bytes で二度書き換えるのは不経済でもある。
   本 wave は「全 worker が launcher を通る」ことを**主張しない**。
2. manifest の seal ceremony と foreign entry 後追記の検出。
3. `setsid()` 脱出子の完全封じ込め (cgroup / bwrap)。
4. stdout / artifact bytes の上限 (`max_artifact_bytes`)。射程を compute-usage に限定した。
5. 失敗型分類・safety-filter 判定・回復経路 → T-183 の所有。
   本 wave の retry は分類なしの機械的上限のみで、workspace-write では 1 回に固定した
   (非採用 attempt の filesystem 変異が次 attempt の入力を変えるため)。

## 凍結しないもの (退避先と hash)

先行 wave の慣行 (逐語 `.md` + 機械台帳を凍結) に合わせ、生 log (計 19MB) と patch は
repo に置かない。DW-S06-B が求める fix 前 snapshot の**退避義務は果たしており**、
同一性は次の sha256 で監査できる。

| patch | sha256 |
|---|---|
| `s6-pre-fix-integrated.patch` (fix round 1 前) | `89ce3c9af2f80d21645516ade6ab243e683bd537972d87ae4906e7f26a2dcca2` |
| `s6-round2-pre-fix.patch` (fix round 2 前) | `da7b58e75eb4b134c986ea9698bdc679bbd67c3dfdb3466024daedb4b467de44` |
| `s5-unit-a.patch` | `ddedecba2b367d8557c98a707651279e289b4e9a563e1661e77375f0dfdf3db8` |
| `s5-unit-b.patch` | `5d4dbc936e591be3005cd7ca0552167e21aafa1d5b1fda8dc4cffef7d32656f7` |
| `s6-fix-unit-a.patch` | `61dbd9b695502cd925ced94a97159726387ae870fd5658e90ef7fe3f42a1070d` |
| `s6-fix-unit-b.patch` | `8c0416dc75e068eb26baa051b79c0e9b59205077b2e143b3815b291d6da5a35e` |
| `s6-fix2-unit-a.patch` | `9b834ada2fe56cb09ca8fcdab2a0db5260c081aec7d06762387ac40c9d5f5f07` |
| `s6-fix3-unit-a.patch` | `7f8305ecae8ff9df5bc44ad762b9d8f9ea62a1065fbbb2540965063621c160f5` |

各 patch の内容は最終的にすべて commit `24d2672` と `de0a9ad` に landed しており、
patch 自体は中間の統合手段である。

## 逐語

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (前提実測を含む) |
| `s2-plan.md` | 段 2 codex プラン |
| `s3-consult-a.md` / `s3-consult-b.md` | 段 3 敵対相談 (両 NO-GO) |
| `s4-adjudication-plan-v2.md` | 段 4 裁定 + plan v2 + 変異事前登録 |
| `s5-author-a.md` / `s5-author-b.md` | 段 5 実装子の完了報告 |
| `s6-review-a.md` / `s6-review-b.md` | 段 6 敵対レビュー (両 NO-GO、must-fix 17) |
| `s6-review-adjudication.md` | 段 6 裁定 |
| `s6-fix-a.md` / `s6-fix-b.md` / `s6-fix2.md` / `s6-fix3.md` | fix の完了報告 |
| `s6-focus.md` | 焦点再レビュー (closed/partial/regressed 表) |
| `probe/` | 段 1 前提実測の一次資料 |
| `launcher-run/` | dogfood の実 receipt と manifest |
| `mutation-spec*.json` / `mutation-ledger-*.json` | 変異の事前登録 spec と本走結果 (機械台帳) |
| `t179-10-sessions.manifest.json` | R17 実データ受入に使った manifest |
| `VERBATIM-SHA256.md` | 逐語の hash pin |
