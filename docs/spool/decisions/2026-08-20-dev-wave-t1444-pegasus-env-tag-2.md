---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1444-pegasus-env-tag
seq: 2
---

## {{D:s8b-machine-pin-site-derived}}. S8b machine-pinはsite_policy.current_site()起点で解決し、contract引数からは解決しない

**決定:** `s8b_floor_campaign.py`/`s8b_oracle_driver.py`の`assert_machine_pin`呼び出しにおける
`machine_env_tag`の解決を、`p2_2.ENV_TAG`直接importから、両driver共通の
`_machine_env_tag_for_site(site)`ヘルパーへ分離する。入力は`site_policy.current_site()`
(実機観測) であり、`contract` (これから使おうとしている契約) からは解決しない。
`site==PEGASUS_COMPUTE`は`env_contract.lookup_required_attestation_contract().env_tag`、
`site==OTHER`は`env_contract.REGISTRY`から`attestation_mode=="none"`のcontractを一意検索、
それ以外の site は fail-closed で拒否する。

**理由:**
- machine-pin は本来「実際にこのプロセスがどの機で動いているか」という物理環境の独立検査で
  あるべきである。入力 `contract` (これから使おうとしている契約) だけから機体タグを導出すると、
  同じ registry から両辺を作る自己検証になり恒真になりうる。
- `env_contract.lookup_required_attestation_contract()`は既に`execution_guard.py`の
  Pegasus compute 認可構造 (`require_certified_writer_authorization`) が使う確立された
  registry-derived パターンであり、docstring も「env literal を重複させず registry property
  を使う」設計と明記している。同じパターンを machine-pin 側にも適用した。
- `s8b_floor_campaign.py`/`s8b_oracle_driver.py`は env 固有 literal を持たない env-neutral
  module (γ-16 の AST 検査対象) であり、site 起点の解決はこの契約と両立する。

**却下した選択肢:**
- ローカル定数 `_LEGACY_MACHINE_ENV_TAG="linux-baremetal"` を S8b 側に新設する案。
  `s8b_oracle_driver.py`は attestation_mode 判定前に無条件で machine-pin を呼ぶ構造
  (`s8b_floor_campaign.py`の mode=none 分岐限定とは異なる) のため、Linux literal 固定だと
  Pegasus required 実行が拒否される。また env-neutral module の AST 検査 (env literal 禁止)
  に抵触する設計だった。
- 入力 `contract` から `env_contract.REGISTRY`/`GENERATIONS` を再検索するだけの設計
  (`_machine_env_tag_for_contract(contract)`) — 実行機の独立検査にならず恒真になりうる。

## {{D:screening-required-attestation-parity}}. Pegasus screening 経路に通常経路と同じ強度の attestation を課す

**決定:** `screening_driver.py`に`_attest_required_contract()`/`attest_runtime_contract()`を
新設し、`prepare_screening_campaign()`が required contract (attestation_mode=="required") の
場合、build/評価より前に hash-bound verification と strict attestation
(`execution_guard.attest_and_build_receipt`) を完了させる。floor calibration の既定
directory 解決も、固定 Linux path から resolved contract の env_tag 経由
(`env_scope_dir(contract.env_tag)`) へ変更する。

**理由:**
- 通常経路 (`loop.run_campaign`) は required calibration のロードと attestation receipt
  作成を実行するが、screening 経路は `require_certified_writer_authorization()` のみで
  attestation を経由しなかった。Pegasus (required) contract を screening に通せるようにした
  ことで、通常経路と screening 経路の admission 強度が非対称になっていた。
- screening の floor calibration が常に Linux 固定 directory を読んでいたため、Pegasus
  screening が誤った (Linux の) between-run noise floor と比較していた。

**却下した選択肢:**
- screening を Pegasus 対応 scope から外し、通常経路だけを site-aware 化する — D58 ablation
  (bench-first screening v2 の初回適用対象がまさに screening 経路) を Pegasus で動かすという
  本 wave の目的に反する。
