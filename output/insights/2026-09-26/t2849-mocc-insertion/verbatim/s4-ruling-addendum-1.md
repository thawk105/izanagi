# 段 4 追補裁定 1 — MOCC slot の campaign pin (2026-09-26 15:2x JST、親)

## 新事実 (生死確認 2 回目で判明)
- 生死確認 29487 (series)・29488 (block) は driver 起動前に job body の `refuse "CCBench P3 S4 campaign pin mismatch"` で止まった (Elapse 7 s・9 s)。
- 原因: `orchestrator/campaign/p3_s4_loop.py:118` の `PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"` は D1936 項 1 (ユーザー裁定「新しい試行の CCBench pin を 511c953 に固定する」) の campaign pin で、pin C への前進 (D2227 項 1・D2236) は D2150 項 1 の ①④⑦ (定数 `pin.CURRENT_PIN`・`CCBENCH_FULL_SHA`・gitlink、buildcache の生成物、現行 pin を期待する test) に限られ、driver の campaign pin を動かしていない。job body (`tools/pegasus/p3_s4_loop_pegasus.sh:352-373`) は submodule の HEAD がこの PIN と完全一致することを要求する。T-2850 の submit-tree は ccbench を 511c9538 に checkout して走っていた (実測)。
- 511c9538 の mocc には X/P 計装が無く (C = 68106660 がそれを足す commit)、D2236 のとおり現行 verifier は旧 pin の mocc trace を certified にできない。今回の較正 3 件も pin C で取った。

## 裁定
- D2150 項 1 は「③ 移行する driver … は各新系列の着手時」と定め、D2227 項 1 は C の承認理由に「第 2 プロトコルの口 S2 ([T-2849]) の X/P 前提は C の計装で足りる」を挙げる。したがって **MOCC の slot だけ campaign pin を C (`68106660686232781bca3be792a750d3e19d7a8a`) に移す**のは承認済みの範囲 (新系列の着手時の driver 移行) であり、ユーザー再裁定は要らない。
- **silo の campaign pin は 511c9538 のまま** (D1936 項 1、T-2850 の試走の登録と整合)。silo 既定の挙動・campaign identity・job body の argv / env 契約は変えない。
- 実装 (fix 2、Codex author):
  1. `p3_s4_loop.py`: protocol → campaign pin の対応 (silo = 既存 `PIN`、mocc = C の 40 桁 literal。gitlink の値から導出しない = gitlink が将来動いても MOCC の campaign pin が黙って動かない)。campaign 設定 (`ccbench_commit=`)・template patch の適用 (`applied(..., PIN, sub)` 3 箇所)・`checkout(PIN, ...)` 3 箇所・`assert_pinned_clean(fixed_sub, PIN)` を、その campaign / 実行の protocol の pin にする。silo では現行と同じ値・同じ呼出し。
  2. job body: harness mode で `IZANAGI_S4_T2849_PROTOCOL=mocc` のときだけ、照合する campaign pin を mocc の pin にする。silo・未設定は現行どおり `PIN`。
  3. 試験: mocc の campaign pin が C・silo が 511c9538 のまま (campaign 設定・job body の照合の両方)。
- 変異の追加登録 (fix 前): M11 = mocc の campaign pin を silo の PIN に戻す (p3_s4_loop 側) → 新試験。M12 = job body で mocc でも silo の PIN を照合する → job contract の新試験。期待 node は probe で観測した完全集合 (drift 層を含む) を登録し、p3_s4_loop.py の変異は drift 7 件を引いた残差で帰属を判定する。
- 生死確認は fix 2 の統合後の HEAD で submit-tree を作り直して再投入する (submit-tree の ccbench は gitlink = C のまま)。これまでの 4 job は計 4+4+7+9 = 24 秒 (driver 未起動)。
