## 所見 (real)

B1. 親の「consumer 8 箇所」は実在する call graph ではない。

`test_p3_b4_closed_critic.py:180` は定義であり、直接の `_driver_configs` 呼び出しは同ファイルの `:185`、`:532`、`:2702` の3箇所だけである。一方、次が列挙から落ちている。

- production 本体: `p3_b4_launcher.py:547`
- `_marked_driver_configs` 経由: `test_p3_b4_closed_critic.py:819,1002,1029,2322`
- `launch_bootstrap` 経由: 同 `:170`。この helper 自体に15箇所の caller がある
- `launch_continuation` 経由: 同 `:2810` → `p3_b4_launcher.py:593` → `:547`
- `test_p3_b4_launcher.py` にも `launch_bootstrap` の直接 caller が `:338,365,429`、さらに共通 bootstrap helper の wrapper caller が `:154,177,190,209,255,562,568,608,634,811` にある

親の8行は「定義、直接呼び出し、helper 呼び出し」を混ぜた occurrence 一覧であり、波及 inventory としては不正確。ただし後述のとおり、追加で見つかった pytest caller に静的な破綻は見つからない。

B2. plan の未射影拒否 test は、記述どおりでは目的の境界へ到達しない。

`s2-plan.md:111-116` は、修正後に `_production_context(unprojected_cfg)` で旧 launcher 相当の未射影 production context を作るとしている。しかし実体の helper は、渡された `cfg` を context 作成に使わず、実 launcher を呼んだ後に campaign ID を assert するだけである（`test_p3_b4_closed_critic.py:148-150,170-177`）。修正後の launcher は `_driver_configs` の射影済み ID を context に束縛する（`p3_b4_launcher.py:547-550`）。

したがって PEGASUS_COMPUTE では helper 内の `assert` が先に失敗し、予定した `require_b4_production_context(..., expected_campaign_id=projected_id)` の `"campaign id differs"` を検査できない。production seal を弱めず、test-local に旧 `_driver_configs` の戻り値を差し替えて旧 context を発行させるなど、fixture 構成を直す必要がある。

B3. base 専用の挙動変更でも、proof closure bytes は3 driverすべてに波及する。

`projection_closure_manifest` は driver 分岐より前に `p3_b4_launcher.py` を全 driver 共通で含める（`p3_b4_closed_critic.py:632-650,658-670`）。そのため launcher の1 byte変更で base、sort、trigger の `projection_sha256` がすべて変わる。production 検査も3値すべてを比較する（同 `:687-706`）し、receipt は選択 driver の値を記録する（同 `:998-1016`）。

PEGASUS_COMPUTE の base ではさらに campaign ID が変わり、start receipt と terminal receipt の `campaign_id` bytes も変わる（同 `:896-906,998-1006`）。`campaign_lock.py:49-113` の enforcement source closure にも launcher が `:93` で含まれる。従って「sort の挙動は不変」は正しいが、「sort/trigger の proof bytes も不変」ではない。

B4. brief の OTHER 不変条件は D261 の読み違い。

brief は OTHER で ID を変えないことを現行不変条件としている（`brief.md:23-25,63`）。しかし D261 は、その文だけを明示的に前向き失効させ、「以後、有効な不変条件として引いてはならない」とする（`docs/decisions.md:12062-12077`）。

今回の限定変更が実際に OTHER ID を維持すること自体は問題ない。また本依頼の禁止事項としても維持すべきである。ただし、test や説明を「D125/D261 が要求する恒久保証」と位置づけるのは誤りである。

## 所見 (refuted)

B5. 既存 `test_p3_b4_closed_critic.py` が Pegasus login hostname を拾って赤になる懸念は refuted。

`conftest.py:239-255` の fixture は既定 function scope、`autouse=True` で、canonical `site_policy.socket` と `_has_nqsv` を中立化する。対象 module は import 時に `site_policy` を読み込む（`test_p3_b4_closed_critic.py:31-39`）ため fixture setup 時には確実に `sys.modules` に存在する。同 test file は opt-out fixture `_detect_site_under_test` を一度も要求していない。

また `p3_s4_loop._current_site` は `site_policy.current_site` の alias だが（`p3_s4_loop.py:123`）、resolver 本体ではなくその入力 `site_policy.socket` を差し替える方式なので有効である。既存 caller は OTHER に解決され、`measurement_env` は追加されない（同 `:153-161`）。

B6. `_marked_driver_configs` consumer が frozen ID/hash literal と衝突する懸念は refuted。

固定された base ID は `test_p3_b4_closed_critic.py:3081-3129` にあるが、ここは `B4L._driver_configs` ではなく `C.B4_DRIVER_CONFIG_FACTORIES["base"]` を直接呼ぶ（`:3118`）。その factory は raw `default_cfg` のままである（`p3_b4_closed_critic.py:1984-1991`）。OTHER と同じ IDなので今回の変更では literal は変わらない。

他の `_driver_configs` consumer は ID、layout、receipt hash を渡された config や現在の source bytes から導出している。projection test も live bytes をその場で hash する（`test_p3_b4_closed_critic.py:2025-2042`）。静的には既存 test の期待値修正は不要。

B7. 現在の repo に更新必須の frozen B4 projection 値がある、という懸念は refuted。

実 preregistration の該当欄はまだ `未記入`（`docs/phase3-b4-reflux-ablation-preregistration.md:166`）。production admission record JSON も存在しない。文書契約は、値を記入した後に closure member が変われば3値すべてが無効になる、と明記している（同 `:253-257`）が、今回はまだその状態ではない。

test 用 admission は live hash を毎回生成している（`test_p3_b4_closed_critic.py:714-740,766-777`）。従って B3 の proof-byte波及は実在するが、今回同時更新すべき既存の frozen record は見つからない。

B8. sort に同等の campaign site 射影があり、今回巻き込まれるという懸念は refuted。

`p3_s4_loop_sort.py:120` には `buildcache.compilers_for_current_site()` があるため、「site に関する helper が皆無」という広い表現は正確でない。ただしこれは condition gate の compiler 選択だけで、campaign config の site 射影ではない。sort config は固定の `linux-baremetal` contract を直接束縛する（同 `:300-328`）。

plan の `if base / elif trigger` なら sort は新分岐を通らず、sort の挙動は変わらない。

B9. T-2317 の layout helper を移植しないことで正式 base launcher に新しい分裂が生じる懸念は refuted。

launcher は射影後 config から context と layout を作る（`p3_b4_launcher.py:547-550,567-569,620-624`）。base main も先に同じ site 射影を行い（`p3_s4_loop.py:2589-2599`）、`drive_iteration` は冪等に再射影して、layout 未指定時は最終 ID から layout を作る（同 `:2335-2342`）。正式経路では layout 注入がないため、trigger の `_assert_layout_matches_campaign` / `_with_campaign_location` を移植しなくても今回新たな不一致は生じない。

B10. import、変更 footprint、受入台帳の時期に追加 blocker はない。

launcher には `p3_s4_loop` module import が既にある（`p3_b4_launcher.py:29-31`）。test 側にも `L` alias がある（`test_p3_b4_launcher.py:21`）ので、plan 記載どおり `site_policy` import だけを追加すれば参照は解決する。B2 の test fixture 修正も同じ test file 内で閉じる。

受入台帳は未知 node を correctness failure にせず、既知 unit の順位から fallback cost を与える（`conftest.py:1571-1591,1631-1664`）。正本 producer は `tools/update_acceptance_duration_ledger.py` で、JUnit から値を生成し（`:57-95,235-282`）、`--add-only` は既存 entry を保ったまま未登録 node だけを追加する（`:362-441`、対応 test `test_update_acceptance_duration_ledger.py:515-604`）。`test_p3_b4_launcher.py` は frozen suite 一覧にも含まれない（producer `:21-30`）。

従って、実測 JUnit を得た後、最新 main の台帳を base に producer の `--add-only` で追記する方針で足りる。手作業で JSON を編集する意味なら不足だが、plan の「運用追記」を正本 producer 実行と読む限り問題ない。

## scope 外だが real (裁定へ返す候補)

B11. 公開 `p3_s4_loop.run_one_iteration` は「将来の直接 API caller」ではなく、現在すでに直接呼ばれている。

repo-wide 検索では `orchestrator/tests/test_p3_s4_loop.py:205,296,995,2921,4714,6482,6520,6582,6625` の9箇所が直接 caller。特に `:4695-4724` は B4 marker 付き config を公開関数へ直接渡す明示的な負例である。`tools/` と production module に base 公開関数の直接 caller は見つからなかった。

従って `s2-plan.md:88-92` の「直接 caller は将来正式化された場合だけ」という説明は事実と異なる。ただし現存する B4 caller は test-only context が境界で拒否されることを検査する負例であり、T-2316 で `p3_s4_loop.py` や授権境界を変更する理由にはならない。実装せず、scope 説明の訂正または別裁定へ返す候補である。

## 総括

helper の base 射影そのものは成立し、既存 pytest consumer、sort、正式 base layout に静的な破綻は見つからない。ただし plan はそのまま author へ渡せない。

必須修正は、未射影 production context を作れない拒否 test の fixture 設計を直すこと。併せて、consumer inventory、全3 driverへ及ぶ proof hash、D261 による OTHER 不変条件の失効を説明へ反映すべきである。公開 `run_one_iteration` の既存 test caller は scope 外として裁定候補に残す。

pytest は実走しておらず、以上は静的検査結果である。