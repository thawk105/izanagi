## 総括

静的レビュー上、exact 62 path 実装に correctness 上の fix は不要です。5 変異はすべて KILL され、正例 P1・P2 も通ります。  
24 path 前提の取り残しによる黙示的な偽緑は見つかりませんでした。親による実測緑を条件に統合可能です。  
ただし acceptance は 190 case 増え、主要 4 群の `git cat-file` 起動数は約 6.62 倍になる見積りです。  
pytest は実行していません。固定 SHA と tuple のみ独立に静的再計算しました。

## 変異 5 件の KILL 判定

- M1: KILL する。`runner.py` を production tuple から除くと、`orchestrator/tests/test_t671_source_binding.py:239` の exact tuple assert が落ちます。`len == 62` も同 file `:244` で落ちます。

- M2: KILL する。`buildcache.py` case は `orchestrator/tests/test_t671_source_binding.py:576` の 62-path parametrize に含まれ、clean capture 後の変更を `:595` の `pytest.raises` が検出します。例外が出なければそこで失敗し、誤った例外なら `:600-601` の reason/path assert が落ちます。

- M3: KILL する。exact-2 は `orchestrator/tests/test_campaign_lock_codec.py:219`、exact-12 は `:247` の `pytest.raises(CampaignLockCodecError, match=...)` が落ちます。subset を許しても後段の全 path 参照で `KeyError` になるだけなら、期待例外型不一致として同じく KILL されます。さらに各欠落 key の 62 case が `:193-206` にあります。

- M4: KILL する。末尾は `orchestrator/qualification/series.py` (`test_t671_source_binding.py:101`)。loop を `[:-1]` にすると末尾 case の `verify_live_contract_loader_binding()` が正常終了し、`:595-598` の「例外が必要」という assert が落ちます。

- M5: KILL する。任意の新規 2 path の交換は `test_t671_source_binding.py:239-241` の ordered exact tuple assert で落ちます。また synthetic lock の実 E1 が変わり、`test_artifact_admission.py:1245-1247` の固定 E1 assert も落ちます。`:1233-1236` の ordered-list SHA は test literal 自体の交換を防ぐ assert であり、production-only 交換の直接検出は前記 2 assert です。

## 正例 2 件の判定

- P1: 通る。production tuple、独立 test literal、確定 suffix はすべて同じ ordered 62 path でした。`test_artifact_admission.py:1231-1236` の固定値を独立再計算し、E1 は `E1:78920e...04e9`、ordered-list SHA は `b27438...067a` と一致しました。exact-62 decode は `:1217-1225`、E1 発行と certified view は `:1228-1251` で検査されます。

- P2: 通る。対象の tracked lock は `schema_version` と `authority` を持たない v1 bytes です。decoder は `campaign_lock.py:401-411` で `authority=None`、epoch は `artifact_admission.py:911-920` で E0、`HISTORICAL_RAW` は `:963-966` で current closure を参照せず通します。実 lock を使う正例は `test_artifact_admission.py:1110-1119` です。

## real な所見

なし。

## refuted な所見

1. 「名前が exact twenty four のままなので検査も 24 本だけ」は refuted。名前は古いものの、tuple assert は 62、本数 assert は 24+38=62、全 member の 4 parametrize 群も 62 case です。

2. 「共有 fixture が production tuple に追随するため M1/M5 が偽緑になる」は refuted。`test_t671_source_binding.py:37-106` と `test_artifact_admission.py:46-115` に独立 literal があり、後者には固定 known-answer もあります。

3. 「未編集 consumer が旧 24 map を作って壊れる」は refuted。`campaign_lock_test_support.py:10-20` などは recorded HEAD の 62 blobへ動的追随します。受理 grammar は意図どおり exact-24 から exact-62 へ置換されます。

4. 実装報告の実走主張に偽装はありません。「pytest 実走なし」「child_started=false」「判定不能」と明記され、closed や green を主張していません。6 file の変更という記述も commit `a94ba713b` の差分と一致します。

## 受入への影響見積り

path-driven parametrize は次の 5 群で各 24 から 62、合計で **120 case から 310 case、190 case 増**です。

- `test_campaign_lock_codec.py:193`
- `test_t671_source_binding.py:528`
- `test_t671_source_binding.py:576`
- `test_t671_source_binding.py:604`
- `test_t671_source_binding.py:705`

1 回の全 map 走査に伴う `git cat-file blob` は 24 回から62回、**2.583 倍**です。新規 lock 作成の capture+live verify、certified read の committed verify+current capture は各 48 回から124回になります。

T671 の Git を使う 4 parametrize 群だけでは、fixture 構築と失敗位置までの走査を含め、静的見積りで **4,380 回から28,985回、約6.62倍、24,605 subprocess 増**です。既存 duration ledger の4群合計10.962秒を単純比例すると約72.5秒、serial で約61.5秒増です。全走の実時間は親の実測が必要です。

## nit / 裁定パッケージ候補

- `test_t671_source_binding.py:235,413` などの `twenty_four` 名は実体と不一致です。動作には影響しませんが、将来の nodeid移行時に exact-62 へ改名候補です。
- `acceptance_duration_ledger.json:1953` および `:16535` 付近は旧24 caseのままです。basename 重複による ID 改名も含め、5群の current 310 node中200 nodeが未登録、旧10 keyが stale になります。unknown-cost fallback があるため blocker ではありませんが、親の実走後に実測値で更新する候補です。
- 実装報告の波及一覧から、直接 binding を取得して62-key lockを発行する `orchestrator/campaign/p3_b4_wiring_probe.py:1219,1463-1473` が漏れています。挙動は正しいものの一覧へ追記候補です。
- 固定値は実装子が計算したと報告しており、裁定の「親が独立計算」に対する手続上の差があります。本レビューでは別経路で一致を確認済みです。