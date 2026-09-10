## 前提の確認

- **所見:** 必読 5 点をすべて確認した。pytest・gate probe・campaign 実走はしておらず、緑の主張はしない。
  **根拠:** `plan.md:3`、`brief.md:26-30`。
  **影響:** 本所見は静的な受理集合検査だけであり、G-A/G-B の成否は変えない。
  **提案:** 段 4 以降も静的確認と実測結果を分けて記録する。

- **所見:** D926 が固定した 4 面は現行コード上で確認できた。18 名集合は実際に以下の 18 名である。  
  `measure_fn`, `probe_fn`, `sleep_fn`, `monotonic_fn`, `prepare_fn`, `now_fn`, `host_provenance_fn`, `process_identity_fn`, `execution_receipt_fn`, `build_fn`, `repo_root`, `fetchcontent_base_dir`, `after_certificate_issued_fn`, `durable_root_policy`, `_floor_preflight_fn`, `perf_preflight_fn`, `_holdout_repo_root`, `_holdout_signature_source`。
  **根拠:** `orchestrator/campaign/s8b_floor_contract.py:40-50`、`orchestrator/campaign/s8b_holdout_admission.py:753-771`、`orchestrator/campaign/s8b_floor_campaign.py:6906-6919`、`orchestrator/campaign/floor_submit_receipt.py:13-19`。
  **影響:** プランどおり保持すれば receipt schema、6 項目 claim key、18 名集合、適格性式は変わらない。
  **提案:** 段 5 の base-to-tip 検査対象に、各 producer 側の schema/key 射影も含める。

- **所見:** `eligible_for_refreeze` は現在も producer の申告だけでは決まらない。
  **根拠:** producer の導出は `s8b_floor_campaign.py:7065-7078`、durable claim への seam 記録は同 `:7661-7671`、下流の独立再導出は `s8b_holdout_admission.py:6164-6172`、申告との不一致拒否は `s8b_floor_stats.py:1069-1077`。
  **影響:** プランがこれらを変更しなければ D488 型の受理集合拡大は起きない。
  **提案:** `confirm_official_floor` を claim、result、receipt の新しい信頼根にしないことを負例で固定する。

## must-fix 候補

1. **所見:** default `False` の確認引数を共有 public/core API に足す案は、pilot の呼出し受理集合を文字どおり広げる。従来 TypeError だった `pilot, confirm_official_floor=False` が受理される。
   **根拠:** `plan.md:104-106,125`。現行署名にはこの引数がない (`s8b_floor_campaign.py:6962-6970,7017-7026`)。
   **影響:** pilot が official 専用 control 値を新たに受け取れるため、「pilot の受理集合を 1 bit も広げない」というプラン自身の主張が成立しない。
   **提案:** default を private な未指定 sentinel にし、pilot は明示された `False`、`True`、`0`、`1`、`None` をすべて副作用前に拒否する。CLI の pilot 経路は確認 keyword 自体を転送しない。

2. **所見:** job 側の「approval env が設定済みなら検査」は fail-open な分岐であり、同じプランの unset 負例と矛盾する。
   **根拠:** `plan.md:101` は条件付き検査、`:116` は unset でも build/driver sentinel 不発を要求する。D926 は不一致を build より前に止める (`D926.md:7-9`)。
   **影響:** env 未設定の official job が shell-side build まで進み、最終受理は閉じても D926 の早期拒否契約と負例の gate 感度が失われる。
   **提案:** fixed-official job では env の存在を無条件に要求し、その後に非空、32 lowercase hex、submission nonce exact 一致を順番に検査する。unset・空・大文字・空白付き・不一致はすべて同じ早期停止面で拒否する。

3. **所見:** Python 側の負例が「gate を消すと赤でなくなる」ことをプランが保証していない。
   **根拠:** `plan.md:110` は missing/wrong-mode/exact-bool を列挙するだけで、後段入力を有効化することや直後 sentinel への到達確認を要求していない。現行 gate は protocol 検査より前にある (`s8b_floor_campaign.py:6990-7001,7088-7095`)。
   **影響:** approval guard の呼出しを削除しても、無効 protocol や後段 mock の別エラーで負例が失敗し続け、official の受理集合拡大を見逃し得る。
   **提案:** CLI/public/core ごとに有効な後段入力または直後 sentinel を用意し、負例では sentinel 不発、承認ありでは sentinel 到達を対にする。helper 単体テストだけを境界 gate の証拠にしない。

4. **所見:** staged dependency seam の解決を D926 実装より先に別変更として置く順序は安全でない。
   **根拠:** 現行 job は `--fetchcontent-base-dir` を必ず渡す (`floor_campaign.sh:1226-1231`) が、同引数は18名集合に入り (`s8b_floor_campaign.py:6891-6903`)、official は approval gate より先に拒否される (`:6990-6996`)。プランも blocker と認定している (`plan.md:94,148-150`)。
   **影響:** 現状維持なら official 受理集合は空のまま、先に引数を外せば現行 pilot の transport が変わり得る。
   **提案:** 段 4 で transport 方針を先に裁定する。legacy default を実測で採用できる場合も、argv 除去は fixed-official 化と同じ段 5 単位に含める。赤なら scope 拡張の裁定まで実装しない。

## nit

1. **所見 (nit):** submission receipt 不変確認が consumer ファイルの zero-diff に偏っている。
   **根拠:** `plan.md:120-123`。receipt producer は編集対象の `submit_floor.sh:348-388,679-708` にも埋め込まれている。
   **影響:** producer の key/schema が偶発変更されると既存 admission が拒否するか、承認自己申告欄が混入する。
   **提案:** shell 内の両 payload について、baseline と schema literal・key 集合の canonical projection が同一であることも比較する。

2. **所見 (nit):** D323 の固定 argv テストは、既存の実行時 argv 捕捉を残すことまで明記するとよい。
   **根拠:** 現行テストは実 argv の完全一致と `shlex.split` の両方を使っており (`test_pegasus_floor_tools.py:2108-2149`)、`--mo"de"` も shell 解釈後は `--mode` として検出できる。
   **影響:** source substring 検査だけへ弱体化すると、分割表記・変数展開・間接 argv による mode 受け口を見逃し得る。
   **提案:** hostile ambient mode と positional argv を与えても、捕捉 argv が固定 official の完全一致になる実行テストを維持する。

3. **所見 (nit):** 「実測した」と読解を混同した記述はプラン内には見当たらない。
   **根拠:** `plan.md:3` は probe 未実施、`:8` は P1-b を静的読解と明記する。`:13` の件数は read-only state snapshot、`:131` の hash は identity 確認であり、G-A/G-B の緑とは書いていない。
   **影響:** 現記述のままなら gate の実測値や成果物は変わらない。
   **提案:** 件数 snapshot と hash 確認を、今後も「G-A/G-B 実測」と呼ばない。

## 親 brief への所見

1. **所見:** (P1-c) は判定対象が古く、親 brief のままでは G-B を正しく表現しない。
   **根拠:** `brief.md:41-42` は旧 `consumed` 228 件を主対象にするが、fresh reservation は旧 effect-key claims を参照せず (`s8b_holdout_admission.py:1618-1620`)、衝突は measurement-generation claim の `O_EXCL` で決まる (`:1636-1647`)。
   **影響:** 無関係な旧 marker に基づき official を誤停止するか、現行 generation claim の衝突を検査し損なう。
   **提案:** (P1-c) を plan の measurement-generation digest/path 検査へ差し替え、read-only 判定に残る TOCTOU も明記する。

2. **所見:** (P1-d) の scope と現行 staged transport は両立していない。
   **根拠:** `brief.md:43-44,58-60` と `plan.md:148-150`。
   **影響:** 親 brief を無修正で段 5 へ渡すと、D926 を実装しても official は refreeze 適格経路へ到達しない。
   **提案:** transport を既定経路にできる根拠、または追加変更の裁定を brief に反映してから段 5 を開始する。

3. **所見:** (P1-e) の「1 単位」は正しいが、transport に触れるならその変更も producer/consumer 契約の切れ目を作らない同一単位へ含める必要がある。
   **根拠:** `brief.md:45-46`、`plan.md:94,148-150`。
   **影響:** submitter・job・CLI/core・適格性境界を途中状態で分けると、未承認 official または到達不能 official の commit が生じる。
   **提案:** probes は先行可能だが、実装の land 単位は submitter、job、両 Python 境界、transport argv、正負テスト、docs を原子的に扱う。

## 総括

現プランは D926 の不変面と D488 の下流再導出を概ね守るが、pilot への explicit-false 受理、unset env、gate 感度、transport 順序の 4 点は段 5 前の must-fix。  
特に transport 未裁定のままでは、承認 gate を直しても official 受理集合は空のままである。  
静的検査のみであり、G-A/G-B・pytest・campaign の緑は主張しない。