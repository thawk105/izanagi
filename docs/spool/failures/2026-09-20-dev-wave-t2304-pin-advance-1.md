---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2304-pin-advance
seq: 1
---

## 新規

### {{F:land-gitlink-fold-pending-deadlock}}. gitlink を変える tip の land が、pending fragment があると D16 postcondition で `mutating` の turn ticket を残し、同一要求の再実行と全 wave の land を `unresolved mutating turn` で止めた [テスト代表性] [手順漏れ]

- 事象: 2026-09-20 18:22、ccbench pin 前進 wave の land が main を landing tip へ ff した後、設計どおり `landed-postcondition-failed` (D16 post-land submodule synchronization remains required) を返した。main checkout の submodule を新 gitlink へ同期して同一要求を再実行すると rc=27 `unresolved mutating turn: main=<landing tip>, main_before=<前 main>, landing_tip=<landing tip>` になり、以後の他 wave の land も同じ理由で止まる状態になった (18:23〜、親が peer 6 session へ advisory)。
- 根本原因: turn registry は ff の前に ticket を `mutating` にし、`_finish_land_turn` は `landed-postcondition-failed` を「未解決の mutating」として残す。`_observe_dead_land_turn` の回復は「main == main_before (rolled-back)」「main == landing_tip かつ expected_fold == noop (done)」「main^1 == landing_tip の fold commit (done)」の 3 形しか知らず、**「ff 済み・fold 未開始 (expected_fold = planned)・fold state 無し」を解決できない**。D16 経路の test (`test_gitlink_change_lands_but_cannot_report_success_before_d16_sync`) と dead mutating の test (`ff-done`) はいずれも fragment 無し (noop fold) で書かれており、pending fragment との組合せが代表されていなかった。
- 恒久対応: `tools/dev_wave_land.py` の `_observe_dead_land_turn` にこの形を「landed-fold-pending」として解決する分岐 (同一要求は `waiting` で already-landed 経路へ進み fold を行う、他要求は dead ticket を `waiting` に書き換えて election を塞がない) と、`_finish_land_turn` で同形を `mutating` に残さない分岐を足し、`orchestrator/tests/test_dev_wave_land.py` に pending fragment 付きの D16 変種と `ff-done-fold-pending` 観測 test、不明な mutating が従来どおり raise する負例を固定した (本 wave の fix commit、insight `output/insights/2026-09-20/t2304-pin-advance/README.md` §6)。
- 再発検知: 上記 test 3 本 (pending fragment 付き D16 の同一要求再実行が `landed` + fold commit、後続要求が塞がれない、不明形は raise)。
