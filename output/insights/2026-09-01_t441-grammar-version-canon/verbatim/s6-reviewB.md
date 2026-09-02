## 条項 2 の充足

実装上の版束縛は identity・WAL・cache の3面を通っています。

- identity: `p3_s4_loop.py:938-942` → `ident.py:226-235` で campaign id に入り、`p3_s4_loop.py:1066-1076` と `loop.py:313-327` が実行時定数との一致を強制します。
- source/variant: `loop.py:454-463` → `pipeline.py:1087-1098` → `source_digest.py:2108-2134` と流れ、`pipeline.py:1165` の variant id に入ります。
- cache: bound token は legacy の `buildcache.py:3055-3064`、v2 の `buildcache.py:2275-2277,2459-2463` の実 cache pre-image に使われます。
- WAL: `wal.py:646-662` が versioned lock 配下の `BUILD_START` に記録し、`wal.py:1183-1199,1523-1526` が正式 admission で検証します。

**B-01 — R-8 のテストは旧 cache fallback を検査していない**

`test_p3_s4_loop.py:2526-2585` は raw/bound の `cache_key()` と `_v2_identity()` が異なることしか確認していません。旧 unbound entry を置いて実際の `build()` / `build_v2()` がそれを hit しないことは観測しておらず、fallback を追加する M12 変異が生き残ります。production code 自体に fallback は見当たりませんが、裁定 R-8 の必須検査は未充足です。

成果物影響 — fallback が再導入されても acceptance が検知せず、版導入前の binary を現行文法の試行が参照して certified 結果を汚染しえます。  
深刻度 — must-fix

## 条項 3 の充足

現在の実装経路は充足しています。`p3_s4_loop.py:321-338` で13段通過後にだけ canonicalizer を呼び、`backoff_hole_grammar.py:717-742` が十進整数1文を生成し、`p3_s4_loop.py:339-343` がその bytes を材料化します。

`20` / `0x14` / `2e1` / `20.0` はいずれも `double now_backoff = 20;` に収束することも確認しました。その後は同じ source bytes から `source_digest.py:2252-2265` の同じ digest/token、`pipeline.py:1165` の同じ variant id、前節の同じ legacy/v2 cache key になります。

**B-02 — R-11 の「一続き」テストが production 配線を通っていない**

`test_p3_s4_loop.py:437-453` は `Genome(... BACKOFF_FIXED=int(coder.value))` をテスト自身で再実装しています。production の対応箇所は `p3_s4_loop.py:1256-1264` であり、この行を誤配線してもテストは通ります。`run_one_iteration()` を通し、mock した `run_campaign()` の入口で materialized source と渡された genome を同時に検査する形が必要です。

成果物影響 — production の値配線が将来ずれても、source `20` と異なる `BACKOFF_FIXED` の試行が同じ材料として記録される回帰を検知できません。  
深刻度 — should-fix

## consumer の取り残し

正式 admission は `artifact_admission.py:1158-1177` から topology validator を通り、critic は `critic/digest.py:1586-1597` で admitted view のみを消費しています。pipeline/buildcache の v2 経路にも取り残しはありません。

機能行の除去・差し替えを差分全体で確認したところ、同型の consumer 置換は次の1件だけでした。

**B-03 — duplicate reader が既存 validator を失い、完全 topology validator に過剰接続されている**

`p3_s4_loop.py:1107-1113` は既存の `validate_commit_contract_bindings()` を `_validate_attempt_topology()` に置換しています。duplicate snapshot の部分 record は完全 topology を満たさず、親実測でも5 nodeid が `AttemptTopologyError` になっています（`s6-parent-measurement.md:18-47`）。

既存 commit validator を復旧し、duplicate 側でも版欠落を検査する必要があるなら、完全 topology ではなく `validate_backoff_grammar_bindings()` を併記するのが変更単位を保つ修正です。

成果物影響 — 既存 certified duplicate を再選択できず、試行が duplicate ではなく例外停止となり、whiteboard・試行台帳・次の critic 参照が欠落します。  
深刻度 — must-fix

## 説明と実装の食い違い

実装子は pytest を実走していないことを明記しており、偽の緑申告はありません。

**B-04 — 予見赤を1件と報告したが、既存 oracle は2件未更新**

`s5-author.md:68-72` は `test_quarantine_passes_clean_backoff_value` だけを予見しています。しかし以下の2箇所が裁定後の正しい観測量と衝突しています。

- `test_p3_s4_loop.py:230-236`: canonical source に `20.0` を要求。
- `test_p3_s4_loop.py:2647-2659`: versioned `BUILD_START` に追加される `backoff_grammar_version` を key 集合に含めていない。

親実測もこの2件を特定しています（`s6-parent-measurement.md:49-60`）。許可された literal と1 keyだけを更新し、その他の assert は維持すべきです。

成果物影響 — runtime の材料値は正しい一方、焦点走が赤のままとなり、この変更を検査済み成果として着地できません。  
深刻度 — must-fix

## 盛りすぎ

B-03 の duplicate reader への完全 topology gate が唯一の過剰変更です。

R-12 は実装されていません。拒否候補は `p3_s4_loop.py:393-397` で raw implementation を引き続き hash しており、別表記の拒否 token は統合されません。R-13の分割、新 framework、互換層、新台帳もありません。

## 呼び出し規約

追加引数は `loop.py:243-255`、`pipeline.py:1790-1796`、`source_digest.py:2137-2139,2225-2232,2269-2271` で keyword-only・既定 `None` です。production の p3 呼出しは `p3_s4_loop.py:1323-1328` だけが版を明示し、他 campaign は既定経路を維持しています。

**B-05 — `resolve_evidence` の実 call 集計に文字列リテラルを含めている**

`s5-author.md:40-41` の `run_campaign=73 calls / 23 files` は正しい一方、`resolve_evidence=28 / 23` は不正確です。AST上は27 calls / 22 filesで、余分な1件は `test_paper_story_a2_certification.py:2497` の source文字列 assertionです。`source_digest.resolve(...)` の35出現は一致します。

成果物影響 — なし。呼び出し漏れではなく監査件数の誤記なので nit です。  
深刻度 — nit

## fixture と波及

`_seed_legacy_lock()` は版 key を除いた別 lock を作るだけで、既存 WAL payload を書き換えていません（`test_p3_s4_loop.py:159-169`）。versioned fixture も WAL より先に lock を seed します（`test_p3_s4_loop.py:180-184,1524,1544,1598`）。したがって backfill ではありません。

新規 test file・改名はなく、plain-runner 登録は不要です。duration ledger は網羅登録ではなく90% gateです（`test_acceptance_schedule_order.py:704-713`）ので、新設12 nodeidの個別登録も必須ではありません。

**B-06 — shared fixture の既存利用先が完一覧として報告されていない**

実装子報告は `_critic_view()` を legacy 化したことだけを記しています（`s5-author.md:65`）。実際には `test_p3_s4_loop.py:1089,1133,1412,1644,1658,1695,1714,2069,2096,2122,2264,2294,2400,4039,4059,4069,4087,4108,4135,4325` の20 call siteへ波及します。親実測ではこれらに赤は出ておらず、実装内容も妥当ですが、「漏れなく列挙」は満たしていません。

成果物影響 — なし。fixture は明示 legacy のまま正常に admission され、報告の網羅性だけの問題です。  
深刻度 — nit

## 総括

条項2・3のproduction配線自体は達成されています。追加で見つかった既存 consumer の差し替えは、親既知の duplicate reader 1件だけです。

受入前の修正対象は次の3点です。

- duplicate reader の既存 validator 復旧。
- 既存2テストの許可範囲内の期待値更新。
- legacy/v2 cache の旧 key fallback 不使用を実 lookup で固定するテスト。

加えて、R-11テストはproduction経路へ接続するのが望まれます。R-12・R-13のscope逸脱、WAL backfill、meta-test登録漏れはありません。