---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2304-pin-advance
seq: 1
---

## {{D:pin-advance-policy-epoch}}. ccbench pin 前進 (D2150 項 1) の実装で判明した波及を事実として追記し、「主経路は影響を受けない」の射程を固定 checkout での継続と旧証拠の保持に限定する — 承認対象・実装範囲・②③⑤の時期は変えない

**決定 (親の実施判断、2026-09-20。ユーザーの再裁定ではない):** D2150 項 1 の承認対象 (候補 `e9e477ca1b55348ab4530de0b1cf663ce4555290` を新 pin とする)、実装範囲 (材料 §4.1 の ①④⑦)、② 登録・identity / ③ driver 移行 / ⑤ floor protocol の新版 / ⑥ 較正 / ⑧ 性能事前登録を「各新系列の着手時」とする順序は変更しない。同項の理由欄「主経路の現行 pin 系列 (K2 次巡・A-1 sized・凍結 g1) は独立 full OID の driver と旧凍結の保持で影響を受けない」は、**pin 前進前の superproject と対応する submodule・旧契約を固定した checkout (submit-tree) で系列を継続すること、および旧証拠 (較正 record・凍結 protocol・凍結 binary・lock・登録) の bytes を保持すること**についてだけ成立し、**新 main の code でそれらを live 消費すること**には成立しない。次の 2 点を新事実として記録する。

1. `orchestrator/campaign/build_admission.py` の admission policy preimage は `repo_stock_pin = pin.CURRENT_PIN` を含むため、pin 前進で policy sha が `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44` から `db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a` へ移る。現行 policy を要求する経路 (`s8b_binary_admission` の receipt 照合、`s8b_ratified_freeze` の launch 検証 (`LaunchValidatedFreeze`)、`s8b_floor_campaign` の旧 binary 再利用・resume、`ident` の旧 lock 拒否、`p3_s4_loop` / `paper_story_a1_paired` の policy 束縛) は、旧 policy で admission された binary・lock を新 main から消費できない。独立 full OID (`p3_s4_loop.PIN` 等) は source pin を固定するだけで policy 束縛を免れない。現行 policy に束縛された test の golden (campaign ID・cache key・builder canonical bytes・synthetic receipt) は前回の pin 前進 (T-816) と同型で epoch を 1 段進めた。
2. `s8b_floor_campaign.resolve_current_floor_protocol()` は新 gitlink の checkout で現行 env 契約の候補が 2 件 (legacy anchor `d706650…` と versioned `511c9538…`) あり head gitlink exact が 0 件になるため fail-closed で raise する。新 pin の successor protocol は AI reseal 経路で発行できる (材料 ⑤、新系列の着手時)。

帰結の書き方は次に固定する: **旧系列 (K2 の巡、A-1 sized v3、凍結 v2 g1 の chain、B-4 床値の旧 binary) を続けるときは、pin 前進前の superproject commit と対応する submodule・旧契約の固定 checkout から走る。新 main へ移行するときは系列ごとに ② (新登録・新 identity) ③ (driver の pin) ⑤ (successor protocol) と source / admission の整合を揃える。** 旧 binary の再 admission だけでは、旧 lock の継続 (identity に policy が入る) も source pin の不一致 (receipt の source commit 照合) も解消しない。

land の順序: 本 wave は tested tip まで完成させ、並行 wave (凍結 v2 g1 の承認 A と active pointer X) の land 完了 tip が local main に含まれることを確認してから、その main を取り込んだ tip の受入を経て land する。待機は policy 問題の解決ではなく「旧 pin + A/X を含む pin 前進前の commit を歴史再開の起点として先に確定する」ための順序である。

**理由:**
- 相談 2 本 (設計・決定 / 最強の反論、いずれも read-only) が独立に同じ結論に達した: 候補の正しさは否定されていない、稼働中 attempt (固定 submit-tree) は止まらない、今日〜数日で新 main を必要とする測定は名指しできない、一方で並行 wave の残工程 (実 repo の真値・gate-check・受入) に新しい拒否原因を持ち込む危険は具体的。
- 「裁定へ返す」で止めない (ユーザーの恒久指示 2026-09-14)。新事実は real と認め、承認範囲を維持して続行する理由を明示し、D2150 の逐語は書き換えない。
- 規律 7: 旧測定・凍結 bytes・当時の判定を保持し、新 main での拒否を過去測定の無効化と読まない。規律 2: policy 照合の除去、resolver の曖昧 fallback、receipt の張り替え、live 経路への `expected_policy=None` の導入は行わない。

**却下した選択肢:**
- 停止してユーザー再裁定へ返す — DW-S04 / DW-STOP の文面では最も保守的だが、恒久指示の下では事実訂正と順序調整で処理でき、pin 前進を待つ mocc の certified 系列を遅らせる。
- 並行 wave を待たず今すぐ land — 待ち時間は無くなるが、並行 wave の統合後検証に protocol 解決不能と policy 不一致が加わり、既存の lineage 矛盾との切り分けが増える。
- policy preimage から `repo_stock_pin` を切り離す — 受理集合と identity の設計変更で、本 wave の範囲外。必要なら別の裁定。
