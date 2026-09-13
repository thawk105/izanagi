# [T-1948] attempt registry の読取失敗を旧経路の認可へ変換しない — 変異 matrix の逐語

- authority: none
- default_effect: no-state-change
- wave: `dev-wave-t1948-registry-parse-fallback`
- 実装 commit (変異の固定 HEAD): `335e582b146fe2a9b66959e2509c6b7597982335`
- 本走 spec: `mutation-spec-final.json`
  (sha256 `bf6a21213677a96d35e7b51cc81550be01a69c16878efee0b505d18275037c06`)
- probe spec: `mutation-spec-probe.json`
  (sha256 `05ddac1d6ec41acd46df9f6d5032b8142d8d98d657d0ea441f3659a760928a92`)
- harness: `tools/mutation_harness.py`
  (sha256 `735a01dbe32997c4db617e9dbc21d7083e1b8a7384be6df4b3b8817e738538d0`)、
  `--runner-mode dispatch --detached`
- runner: `python3 tools/run_tests.py --force-dispatch
  orchestrator/tests/test_s8b_holdout_admission.py -q -rf`
  (harness が `-p no:cacheprovider` を付す。runner sha256
  `0eb713c571e3724ae01b571d9a7521fcbbe0fa8d0d0f5e0f954d380a7859e046`)
- **本走結果: baseline PASSED、KILLED 4 / 4、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0**
  (所要 284 秒)

## 何を塞いだか

床値 campaign の再試行認可 gate には、attempt registry の読取が失敗したとき旧
`valid=False` 経路の候補 1 件を受理して正常復帰する fallback が 2 箇所あった。読取が失敗すると
recovery 候補の**件数を数えられない**ので、D880 が要求する「候補 evidence の件数による排他」を
件数を確かめないまま通していた。本 wave が作った穴ではなく既存の穴である。

塞ぐ範囲は「候補読取・導出が失敗した事実を legacy 認可へ変換しない」であって、
「壊れた registry 全般を拒否する」ではない。`b"{}\n"` のように framing・strict JSON・canonical
検査を通る入力は従来どおり通り、recovery 候補 0 件として扱われる。D977 の版境界と旧経路の
全廃は scope 外で、本 wave はその不整合を増やしていない。

## 本走の内訳

| ID | 撃つ不変条件 | 期待 node (完全集合) |
|---|---|---|
| `MUT-T1948-QUERY-PARSE-FALLBACK` | query は候補件数が判定不能なとき認可しない | `test_malformed_registry_rejects_existing_failed_session_retry_query` |
| `MUT-T1948-SHARED-PARSE-FALLBACK` | ticket 発行と最終 evidence 検査の両文脈で、判定不能を認可へ変換しない | `..._consumption`, `..._inspection` |
| `MUT-T1948-READ-ENOENT-AS-ABSENT` | 存在を確認した後に読めなかったことを候補 0 件へ化けさせない | `test_dangling_registry_symlink_is_not_treated_as_absent` |
| `MUT-T1948-ABSENT-AS-UNREADABLE` | **過剰拒否の正例 (DW-M01)**: registry 不在の legacy 経路を壊さない | 下表の 7 件 |

node の prefix はすべて `orchestrator/tests/test_s8b_holdout_admission.py::`。

`MUT-T1948-ABSENT-AS-UNREADABLE` の期待 node 7 件:

- `test_existing_failed_planned_session_retry_still_passes`
- `test_floor_marker_capability_accepts_nonzero_retry_ordinal_on_use`
- `test_floor_marker_capability_rejects_wrong_nonzero_retry_ordinal_on_use`
- `test_legacy_retry_rejects_extra_completion_for_same_trigger`
- `test_malformed_registry_rejects_existing_failed_session_retry_inspection`
- `test_missing_registry_preserves_existing_failed_session_retry`
- `test_retry_ticket_without_failed_planned_trigger_is_rejected`

## probe 相 — 期待 node 集合を実測で確定した

`DW-M02` に従い初回結果を消さずに残す。

- probe 結果: baseline PASSED、**MISMATCH 4 / KILLED 0**。全件を
  `expected_status: SURVIVED` / `expected_nodes: []` で登録したので、これは設計どおりの不一致であり
  「変異が生き残った」という意味ではない。probe の目的は観測 node の収集である (`DW-M07`)。
- 4 件とも失敗 node が非空で、注入は実在した。

**なぜ probe が要ったか。** 段 6 の敵対レビュー A が、過剰拒否の正例
`MUT-T1948-ABSENT-AS-UNREADABLE` について「登録 1 件に対し**静的には最低 6 件**が落ちる。
完全一致方式のままでは受入材料が成立しない」と指摘した。レビュー自身が
「上記を最終的な完全集合と断定せず、親の matrix で確定する必要がある」と限定していたので、
親が probe を走らせて実測した。**実測は 7 件**で、静的予測に無かった
`test_retry_ticket_without_failed_planned_trigger_is_rejected` が加わった。
静的レビューだけで完全集合を確定していたら、本走が MISMATCH で止まっていた。

他の 3 件の期待 node は、事前登録の値と probe の実測値が一致した。

## 単一理由性 (DW-M01)

4 件とも受理集合を変える変異であり、診断文字列だけを変える変異は登録していない (`DW-M03`)。

`MUT-T1948-SHARED-PARSE-FALLBACK` が 2 node、`MUT-T1948-ABSENT-AS-UNREADABLE` が 7 node を
落とすのは、1 つの fallback / 1 つの不在判定が複数の文脈と fixture から使われるためで、
赤の理由はそれぞれ 1 つである。

登録を見送った変異が 1 件ある。「読取前に regular-file 検査を足す」案は、本走の実装では
採用しなかった (下記「reader の修正を最小形にした理由」)。仮に採用していても、読取後の検査が
残る限り受理集合は変わらず**拒否 message だけが変わる**ので、`DW-M03` により kill として
数えられない。

## reader の修正を最小形にした理由

段 2 のプランは `_read_floor_registry_candidate_rows` について
「非 regular / symlink 検査を読取前へ移す」を提案した。段 3 のレンズ A がこれを
**受理集合を広げる**として拒否し、親が採用した。反例は次の順序である。

1. `lstat()` と移動後の `is_symlink()` は通常ファイルを観測する。
2. `read_bytes()` の前または途中で path が symlink へ差し替わる。
3. 読取は正準 registry bytes を返し、symlink が残る。
4. 現行 reader は読取後の検査で拒否する。プランの reader は返却してしまう。

採用したのは `try` を 2 つに割るだけの形である。不在扱いは `lstat()` の `FileNotFoundError`
だけに限定し、`read_bytes()` の `FileNotFoundError` は他の `OSError` と同じ読取拒否へ送る。
**読取後の `if not stat.S_ISREG(mode) or path.is_symlink():` は位置も内容も変えていない。**

これで存在しない対象への symlink は「候補 0 件 (判定可能)」へ化けなくなり、
既存の読取後 symlink 拒否も失われない。

## 段 3・段 6 の所見のうち scope 外と裁定したもの

いずれも real だが本 wave では実装せず、次の一手へ起票した。

- **query 側 legacy 集合の非対称**: query は使用済み trigger を recovery 収集から除外するが、
  legacy 集合からは除外しない。その trigger の recovery 候補を数えずに legacy 認可を返しうる。
  本 wave が作った穴ではなく、consume と最終 inspection は対象 trigger を再取得して両候補を
  拒否するため、certified 受理集合の拡大ではない。
- **非 certified campaign 経路の例外握り潰し**: `CampaignAbort` は `FloorCampaignError` 経由で
  `RuntimeError` を継承するため、非 certified 測定経路の `except` に捕まり
  `launch_failure` の session へ変換される。certified 経路と最終 inspection は
  この catch を通らないので certified 受理は塞がる。変わるのは journal の試行行・retry 枠・
  terminal 診断であって受理集合ではない。

## 証明範囲の限定 (敵対レビュー B の所見、採用)

- `test_dangling_registry_symlink_is_not_treated_as_absent` は reader を直接呼ぶ。
  reader 自体の判定境界を固定する負例としては有効だが、
  `_floor_registry_path` の path 導出を含む統合検査の証明には使えない。
- `floor_attempt_requires_cut6_replay` も共通 gate へ到達するので、registry が壊れた後の
  cut6 replay も従来の正常復帰から拒否へ変わる。波及先として記録する。

## 旧テスト名の参照残り (編集していない)

穴を正例として固定していた
`test_malformed_registry_does_not_disable_existing_failed_session_retry` を反転・改名した。
旧名は次に残るが、いずれも現行の検査を赤にしないので本 wave では編集していない。

- `orchestrator/tests/acceptance_duration_ledger.json` — 未知 node は所要不明として扱われるだけ。
  exact node 集合 pin は 8 suite だけを束縛し、この suite を含まない。
- `output/insights/2026-08-27/t1981-holdout-oneshot-removal/mutation-spec-final.json` —
  現 checkout で再走する場合だけ期待 node が解決できない。過去の実走結果は無効化されない。
- `output/insights/2026-09-02_t2107-t1851-b1-capability/` の収集出力 2 本 — 過去の観測記録。

## 一次資料

- 変異 spec: 本 directory の `mutation-spec-probe.json` / `mutation-spec-final.json`
- 段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装報告、段 6 敵対レビュー 2 本の逐語は
  本 wave の job dir に残る (repo 外)。結論と裁定は本書と worklog に射影した。
