# 逐語: output/insights/2026-09-20/t2810-g1-launch-validation/README.md §5・§8 (base 5efd69367、見出しで切り出し)

## 5. 実 repo の実測 (統合 commit 後、無変異、login node、`evidence/`)

| # | 経路 | 結果 | 証明範囲 |
|---|---|---|---|
| (e) | `load_ratified_freeze(root)` | generation 1、sha `7e1114…`、G `32ba8cae4` | 批准 loader は成功 (T-2724 と同じ) |
| (a) | `reverify_published_freeze` (policy 照合なしの正規 public 経路、`_resolve_historical_contract_sha256`) | `closure-hit-mismatch` (rr80 未申告 = 候補 path)、75.8 s | **段階 4 semantic・5 binding・6 lineage・7 exemption を通過して段階 8 に到達**。歴史 reverify の成功ではない (候補 hit で止まる、rr20 側は未到達) |
| (b) | `launch_validate` (live) | `manifest-invalid` / `binary-admission` (現行 policy 不一致)、0.3 s | D2184 のとおり段階 4 で止まる。journal / 段階 6 には到達しない |
| (c) | runbook §2 P3 gate-check、g1 path | rc=2、`allowed: false`、拒否 2 件 = layer-2 hit + (b) の文字列 | 更新後 `_ACTIVATED_G1_REFUSALS` と集合 exact 一致 (`compare_refusals.py`)。held checks 3 件は不変 |
| (c') | 同、v1 path | rc=2、既知 4 件 | T-2724 の `after-v1.json` と集合 exact 一致 (不変) |
| (d) | `assert_g1_floor_selection_identity` | None (0.02 s) | live 経路だけが持つ選択 identity 検査は通る |

(a) の時間は login node の値で一般化しない。

**fix2 後の再実測 (HEAD `083a45ee9`、`evidence/reverify-after-fix2.json`、`p3-after-fix2-g1.json`):** (e) loader 成功 (activation_head `083a45ee9`)、
(a) `closure-hit-mismatch` (同じ候補 path、92.2 s)、(b) `manifest-invalid` (0.27 s)、(c) rc=2、拒否 2 件が更新後 `_ACTIVATED_G1_REFUSALS` と集合 exact 一致 —
統合 commit 後と同じ (fix2 は段階 6 の世代文書検査だけを変え、現物 G は世代文書 1 file を追加する commit なので観測は変わらない)。


## 8. scope 外 (実装しない、裁定パッケージ候補)

1. **N1 / [T-2812]:** 新 main の live 経路は段階 4 の policy 照合で止まる。policy 照合の除去・`expected_policy=None` の live 導入・receipt 張り替えは D2184 で却下済み。
   移行は T-2812 (② 登録・identity、③ driver pin、⑤ successor protocol、admission の整合)。
2. **N3 候補文書の scan hit:** 第一候補 = 候補 file `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` だけを削除する commit。scan 除外は広げず、B-10 freeze-tree pin
   (`output/s1-freeze` + `output/s8b-freeze`) の対象外、G/A/X・floor_source bytes は不変、`_active_chain_exempt_exact` 不変。帰結: `V2_CANDIDATE_REL` の create-only
   存在拒否が消える (再生成されれば hit が復活)、`_ACTIVATED_G1_REFUSALS` の候補を含む hit 列挙が変わる、削除後に load / reverify をやり直す、候補 bytes と来歴は X2 の
   履歴 blob と世代文書で保持。D2077「痕跡を消してよかったことの証明ではない」に照らし、削除の根拠は別裁定 (候補 path の役割終了を認めるか)。
   **裁定 (第 27 回 /rulings、2026-09-21 00:5x JST「推奨通り」、一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md` 項 5、
   台帳の D は記録 wave `rulings-all-20260921` の fold 後):** (a) 候補 file だけを削除する commit を本 wave の land 後に別 commit で (scan 除外不変、削除後に load / reverify を
   再実測)。根拠 = 候補 path の役割が批准済み世代 (D2180) へ移って終了。本 wave では実施しない (worklog の新規 T へ AI 手番として起票)。
3. **旧 pin 固定 checkout への修正の移植:** 歴史再開に本修正を使うなら移植した別 checkout の検証が要る。
4. **W-4 spec 承認、W-5 実走・certified 選択:** 不変。

