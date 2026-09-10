## P1 追試

P1 は主経路について確認できた。

- `s8b_floor_campaign.py:735-762` の `_head_blob_100644` は、指定 commit の tree entry が `100644 blob` であることを検査し、`cat-file blob` の bytes を返す。
- `s8b_floor_campaign.py:879-887` は working tree bytes も読むが、コメントどおり strict validation 専用で、権威には使わない。
- 権威 record は `s8b_floor_campaign.py:889-896` の固定 commit blob から構築される。
- `resolve_current_floor_protocol` は HEAD を一度捕捉し、固定 commit scan を行う (`s8b_floor_campaign.py:983-989`)。record の commit OID も再確認する (`:990-997`)。

`run_campaign` では、mode/seam/確認値の拒否分岐 (`s8b_floor_campaign.py:5638-5670`) はあるが、いずれも core 到達前の拒否である。成功経路では無条件に

- `_require_supplied_protocol_authority`: `s8b_floor_campaign.py:5672-5675`
- `_run_campaign_core`: `s8b_floor_campaign.py:5676-5687`

の順に進む。authority helper は resolver document、供給 bytes、SHA-256 をすべて比較する (`s8b_floor_campaign.py:5600-5625`)。

CLI は protocol を working tree から初期ロードする (`s8b_floor_campaign.py:7075-7088`) が、必ず上記 `run_campaign` gate を通る (`:7090-7097`)。authority エラーは main の例外処理で終了し、core へ進まない (`:7098-7104`)。

注意点として、resolver 単体は working tree legacy bytes と HEAD blob の一致までは要求しない。ただし確認できた production caller は、`run_campaign`、holdout admission、certified writer admission で、いずれも固定 record との比較を実施している。certified writer は SHA 比較を行う (`certified_writer_admission.py:201-218`)。

## P2 production 呼出しの分類

| 呼出し | protocol / `master_seed` の出自 | 判定 |
|---|---|---|
| `s8b_floor_campaign.py:1489`（wrapper）、実呼出し `:5850-5853` | `run_campaign` の protocol。CLI の raw load 後、`:5600-5625` で HEAD blob record と document/bytes/hash を一致させる | 固定 commit blob に束縛済み（安全） |
| `s8b_ratified_freeze.py:1881-1884` | `:3126-3130` で G/H/worktree を捕捉するが、`_capture_g_h_worktree` は G の git blob を返す (`:1666-1688`)。`:3162-3178` で strict parse/契約検証後、`:3199-3202` から manifest 検証へ渡る | 固定 generation commit の git blob／承認済み artifact 由来（安全） |
| `s8b_holdout_freeze.py:1444-1447` | `:1362-1365` で `root / FLOOR_PROTOCOL_REL` を raw working tree から読む。`:1376-1378` は canonical SHA 検査のみで、HEAD blob との比較がない | raw working tree 由来。T-646 同型の未束縛経路 |
| `s8b_holdout_admission.py:1222-1225` | `:1199-1201` の `_authority` が resolver を呼び、`:638-650` で固定 commit blob を strict parse。供給 protocol との一致も `:651-652` で検査 | 固定 commit blob 由来（安全） |

holdout freeze の caller は `build_v2_g1_candidate` (`s8b_holdout_freeze.py:1715-1718`) で、CLI production path も `:1910-1915` から同じ関数を呼ぶ。`HEAD` は `:1687-1689` で捕捉済みだが、protocol 検証には使われていない。なお result の `protocol_sha256` 照合 (`:1424-1425`) は追加防壁であり、schedule に渡す bytes の authority 置換にはなっていない。

### grep 全 production hit の分類

テストを除いた指定 grep の全 hit は次のとおり。

- `s8b_floor_campaign.py:174,263,867,889-890,895,934,1066`  
  protocol path/index。working tree bytes は scan・比較対象だが、authority record は `:889-896` の固定 blob。
- `s8b_floor_campaign.py:1288`  
  canonical JSON の検索ラベル文字列で、artifact 読み込みではない。
- `s8b_floor_campaign.py:1417,1445`  
  protocol writer の destination/path metadata。
- `s8b_floor_campaign.py:3783,3814,3816,3853`  
  preflight captured bytes と pre-oracle commit blob の hash/exact 比較。固定履歴に束縛される。
- `s8b_floor_campaign.py:5595`  
  supplied path の既定値。実 bytes は `:5606-5617` で resolver record と比較される。
- `s8b_ratified_freeze.py:77`  
  selector protocol path 定数。実使用 `:2813-2815` は pre-oracle commit blob hash。
- `s8b_prediction_runner.py:79,1548`  
  path 定数と不一致エラーメッセージ。実読み込み `:1542-1546` は固定 `pre_oracle_head` blob。
- `s8b_holdout_freeze.py:48`  
  protocol path 定数。実使用 `:1362-1378` は raw working tree 読み込みであり、今回の未修正 hit。

## Fix 要否

修正が必要。

最小案は `s8b_holdout_freeze.py:1348-1378` に、`build_v2_g1_candidate` が既に捕捉している `head` (`:1687-1689`) を渡し、既存 `_blob_at_head` (`:319-330`) で `head:FLOOR_PROTOCOL_REL` の blob を取得して、`protocol_raw` (`:1362`) と byte-exact 比較すること。

比較は protocol parse・`build_schedule` (`:1444`) より前に行い、不一致は `FreezeError` で fail-closed 拒否する。正当な protocol reseal commit では新しい captured HEAD blob と working tree bytes が一致するため通過する。

実装変更は行っていない。pytest 等の実走も段2 read-only のため未実施である。

## 総括

- P1: `run_campaign`/CLI の主経路は、固定 HEAD blob との authority 比較を core より前に必ず実施しており、主張された TOCTOU は閉じている。
- P2: production 呼出しは論理的に4経路。campaign、ratified、holdout admission は安全だが、holdout freeze `:1444` は raw working tree protocol を消費している。
- Fix: `s8b_holdout_freeze.py:1362` 直後に captured HEAD blob との byte-exact 比較を追加する案を採用すべき。