## must-fix

- `s2-plan.md:109-120,212-224` — 正例がすべて mask 7・nonce `"a"*64`・`source=None` なので、「その nonce だけ許す」「source 付き binding を拒否する」consumer 変異が生き残る。producer 実走正例を少なくとも `(mask=18, nonce="b"*64, source=SourceBinding(...))` でも通し、ledger と provenance の commitment を同じ binding に合わせること。
- `brief.md:28-29` / `test_reflux_formal_consumer.py:540-552` — 親 brief は旧形状へ直接依存する FC06 test を列挙していない。放置すると `wal[0]["trigger_binding"]` が KeyError になり、FC06 の検出力を失う。段 2 プラン `:195` の donor raw binding コピーを brief にも反映すること。
- `test_reflux_formal_consumer.py:284-290` — `_rewrite_wal()` が production record に root `build_attempt_id` を追加すると、payload の古い attempt を root 値で覆い隠す非 production 形状になる。放置すると producer 実走テストが実際の record 形状を検査しない。段 2 プラン `:193` どおり既存の格納位置だけを書き換えること。
- `brief.md:105-108` / `orchestrator/tests/README.md:114-127,144` — `test_reflux_formal_consumer.py` は pytest-only allowlist 上のファイルで、自走 harness を持たない。`python3 file.py` 型では 0 件 exit 0 になり得るため、焦点走は `tools/run_tests.py` 経由へ訂正すること。
- `test_reflux_origin_fixture_builder.py:301-325` — 現行検査は projection と source bytes の自己整合しか見ない。放置すると余分な root keyを持つ疑似 production fixture でも通るため、trigger outer keys、payload keys、raw binding keysを exact set で固定すること。

意図した consumer＋builder の原子的な差分に対する、9 file の静的波及は次のとおり。

| file:line | 静的な赤・追随 |
|---|---|
| `test_p3_autonomous_workload_trial.py:10347-10385,10622-10629,10710-10780` | 最終差分では編集不要。`10778` は consumer 未追随なら `FC05C` となる既存 E2E 検出点 |
| `test_reflux_origin_topology.py:12-35` | WAL 不参照。赤なし |
| `test_reflux_source_closure.py:18-22,102-160` | authority/artifact のみ。赤なし |
| `test_reflux_origin_binding.py:22,187-256` | authority/artifact のみ。赤なし |
| `test_reflux_origin_artifacts.py:12-54` | record を opaque JSON として扱う。赤なし |
| `test_reflux_formal_consumer.py:525-532` | `wal[0]["trigger_binding"]` が KeyError。raw nonce mutation へ変更必須 |
| `test_reflux_formal_consumer.py:540-560` | `wal[0]["trigger_binding"]` が KeyError。donor の production raw binding へ変更必須 |
| `test_reflux_formal_consumer.py:583-602` | 手書き旧形状が FC05C に先取され、期待 FC07 と不一致。production trigger を保存して terminal だけ差し替える |
| `test_reflux_origin_client.py:54,82-93` | launch/authority のみ。赤なし |
| `test_trial_registry.py:43,849-852` | launch admission のみ。赤なし |
| `test_reflux_origin_fixture_builder.py:107-119` | baseline exact 一致が赤。計画どおり provenance、WAL projection、result evidence の3 entryを更新 |
| `test_reflux_origin_fixture_builder.py:301-330` | 自己整合検査はそのまま通るため、新形状を証明する assertion が別途必要 |

したがって、段 2 プラン `:175-196` の最終差分向け列挙に file 漏れはない。漏れは親 brief の FC06 直接参照である。

builder または consumer の片方だけを先に置く非原子的状態では、さらに `test_reflux_formal_consumer.py:336-342,535-580,605-612,626-664,667-694,720-813` が FC05C の先取または P6 不到達で赤となり、`test_p3_autonomous_workload_trial.py:10710-10780` も赤となる。この中間状態を焦点結果として評価してはいけない。

変異帰属は次のとおり。

| 事前登録変異 | 既存か新規か | 殺すテスト |
|---|---|---|
| 旧 root 形状を再受理 | 新規だけ | 同値の旧形状を FC05C とする test。値を不一致にすると恒真になる |
| mask 比較脱落 | 新規だけ | ledger＋provenance の mask だけを変える mask-only test。変異時は FC06 へ進むため reason 固定で殺す |
| commitment 比較脱落 | 更新既存＋新規 | `test_fc05c_rejects_wal_trigger_binding_mismatch():525` の valid nonce 差、および commitment-only test |
| 2 binding の先頭を返す | 新規だけ | 同値の valid binding 2件を置く duplicate test |
| wire ビット順反転 | 既存も殺す | `test_exact_fixture_contract_reaches_only_p6_unavailable():336` と `test_origin_public_path...:10710`。新規2正例も殺す |
| `validate_record` 不呼出 | 新規だけ | raw binding に余分な key を加える test |

fixture は `_record_for_query():584-621,657-660` で mask 0〜31をすべて生成する。0 と31は反転不変だが、7の `"11100"` を含む多数の非対称 mask が同じ full evaluation を通るため、ビット順反転変異は既存 test だけでも生き残らない。

## nit

- producer 実走経路は実現可能。`CampaignLayout.ensure()` は `layout.py:226-230` で6 directoryを作るだけで `campaign.lock` は作らない。trigger stage は `wal.py:89-91` の既知 stageであり、`_append_record():1194-1198` の lock 読取り対象でもないため、trigger 1行だけなら lock 不在でよい。
- `wal.log_trigger_binding():1595-1611` の副作用は `runs/wal.jsonl` の作成・追記、WAL flock、file fsync、`runs/` directory fsync (`wal.py:1266-1276,1282,1340-1359`)。他の file は生成しない。`tmp_path` ごとの layout なら隔離上の問題はない。
- duration ledger は file 単位ではなく nodeid 単位 (`acceptance_duration_ledger.json:2`)。既存 formal consumer file は52 node合計6.516秒なので、提案した負例と2〜3正例を足しても静的見積りは約8秒、5分上限には十分収まる。新規 nodeは既存 fileへの追加でも実測後の ledger 登録が必要。
- 新規 file は ledger に加え、自走 harnessまたは README allowlist 登録も必要 (`README.md:114-127`)。既に pytest-only 登録済みの `test_reflux_formal_consumer.py` に足す方が変更面は小さい。
- literal test は attempt idを書き換えるので、厳密には byte-for-byte の逐語ではなく「逐語から attempt だけ移植した record」である。名称と説明をそう合わせると誤解がない。
- producer の将来変更で live producer test と literal test が同時に赤なら、先に新形状が裁定済みか確認する。裁定済みなら consumer と literal を更新し、旧 literal の互換受理を足してはいけない。未裁定の drift なら producer 側の回帰であり、この wave の consumer を追随させる根拠にはならない。

## 親 brief への所見

- (P1): 条件付き支持。stage 数を先に数え、raw を `validate_record` し、独立 `_wire()` と commitment を exact 比較する設計は正しい。ただし source 付き・非固定 nonce の正例追加が必要。
- (P2): 支持。同値の旧形状を使えば、無視して `None` の実装は FC05C、旧形状を読む変異は P6Unavailableとなり、恒真ではない。
- (P3): 支持。terminal の root `kind` は既知の別不整合だが、本件で同時修理すると FC07 の受理集合まで変わる。
- (P4): 支持。nested raw extra-key test が `validate_record` 不呼出変異を殺し、例外漏出も FC05C への閉包も検査できる。
- (P5): 部分支持。live producer＋literal の二経路は有効だが、同じ binding から ledger commitment を導く正例単独では commitment 比較脱落を殺せない。計画済み nonce差・commitment-only負例が必須で、source付き正例も追加すべき。
- (b): 実測された1例の逐語として支持するが、sourceなし・固定 nonce・mask 7を一般化してはいけない。mask は33-record fixtureで補えているが、sourceとnonceは未補完。
- (c): 支持。ledger exact 3 keys と production projection未実装という限界は明記どおりで、ledger値は実測値ではなく契約由来である。
- (d): 支持。root/payload両対応の attempt helperがあるが、root追加でpayload不一致を隠さないよう `_rewrite_wal` 修正が必要。terminal `kind` は別 carry。
- (e): 9 file の集合は支持。最終差分で直接編集が要るのは formal consumer test、fixture builder test、baselineだけ。ただし brief の個別列挙には FC06 test が欠けている。

## 総括

- 段 2 の修理方針と主要な変異 matrix は支持する。
- 必須追加は source付き・非固定 nonce の producer 正例、FC06 の brief反映、正しい pytest実行経路である。
- 最終差分で静的に赤となる既存 test は formal consumer 3件と fixture baseline 1件。
- pytest は実走しておらず、以上はすべて静的検査結果である。