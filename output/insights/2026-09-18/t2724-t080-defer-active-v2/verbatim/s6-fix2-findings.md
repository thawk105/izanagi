# 段 6 fix-2 の指示 (親、2026-09-18 12:55 JST)

fix-1 統合 commit `02a43dd58` の焦点走 (chain 無し木、29 file、request 5622): **2663 passed / 8 failed / 36 skipped、305 秒**。disk-swap 退行・sink pin・consumer 回帰はすべて緑。残る赤は接続系 8 node で、fixture 構築が 1 段進み (build seam は解消)、次の障害で止まる:

```
FloorCampaignError: holdout admission reservation failed: cannot resolve current floor protocol:
AI reseal が人間専有 field を変更した: ['env_tag', 'master_seed', 'wired_min_rel_floor']
```

位置: `test_s8b_ratified_freeze.py:1082 build_production_emitter_g1` → `_run_official_fixture_campaign` → `s8b_floor_campaign._run_campaign_core:7940` → `s8b_holdout_admission._authority:824` → `s8b_floor_campaign.resolve_current_floor_protocol`。

## G1. 原因 (親の判定、現物で確かめよ)

接続 fixture の base は `_build_t080_stub_free_e2e_repo(active_v2_base=True)` (`test_s8b_oracle_driver.py:1392〜1403`) で実 root の output を複製し、g1 / budget input / `selector_predictions.json` / `selector-runs/` だけを除いている。しかし main の freeze namespace には **`output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json` (人間が封印した protocol) と `output/s8b-freeze/floor_protocol.json`** が tracked で残り、emitter が自分の合成 protocol を `_FLOOR_PROTOCOL_REL` (= `output/s8b-freeze/floor_protocol.json`) に書くと、`resolve_current_floor_protocol` が封印済み protocol からの「AI reseal」と解釈して人間専有 field の変更を拒否する。

## G2. 直し方 (test 側のみ、S は不変)

`active_v2_base=True` の除外集合を「**`output/s8b-freeze/` 配下で `holdout_freeze.json` (v1、T-080 が要る) 以外の全 file/dir**」と「`output/s8b-freeze-budget-inputs/` 配下の全 file」に広げる (宣言集合として列挙し、走査結果や試行錯誤で増やさない)。除外は basis commit の**前**に行う (履歴に入れない)。T-080 側が要る `output/s1-freeze/known_axes_freeze.json`、`output/s8b-freeze/holdout_freeze.json`、`orchestrator/tests/data/freeze_holdout_positive_control_v1.txt`、`orchestrator/` 配下は残す。45 node 用の削除集合 S (official namespace + `V2_CANDIDATE_REL`) は 0 byte。

そのうえで、emitter 側が読む残りの複製 output (`output/env/pegasus/...` の calibration ref、env contract、claims 等) を静的に列挙し、`_run_official_fixture_campaign` / `launch_validate` / `_authority` / `_active_chain_exempt_exact` / `_selector_evidence_exempt_exact` が「実 root 由来の残骸」を人間封印物として読む経路が他に無いかを確かめる。あれば同じ宣言集合に足す (理由を comment に)。

## G3. 自己検証

接続 fixture は sandbox で直接呼出しできない (growth-hold guard / site 拒否) ので、fixture 構築の各段を静的検算し、特に `resolve_current_floor_protocol` が emitter の protocol を「初回封印」として受理する条件 (floor-protocols namespace が空、`floor_protocol.json` 不在) を現物の関数で確認する。さらに、次に来る可能性のある障害 (certificate 発行、C commit、G の `frozen_at_head`、A / X、`load_ratified_freeze` の namespace clean 検査、`launch_validate` の closure / selector 祖先 / exempt) を順に読み、実 root 由来の複製が干渉しうる箇所を報告する。

## G4. 変えないもの

fix-1 までの production 差分 (driver の campaign-start 形、predicate、型 field)、S、既存 tracked test の期待値、走査除外・hold・allowlist。sink pin は行番号が動かない限り不変。

## 対応表

G1〜G4 と、fix-1 の対応表で partial だった項目 (F1〜F9) のうち本巡で状態が変わるものを closed / partial / regressed で書く。
