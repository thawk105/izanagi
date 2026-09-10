pytest は実行していない。以下は静的レビューのみ。

[B-1] real（pin 閉包の見落とし）

`test_s8b_oracle_manifest.py:39-47` は report/judge を `generator_versions` の pin 対象にし、`:66-100` に独立した raw golden、`:1078-1093` に実 byte hash 検査がある。`s8b_oracle_spec.py:160-165` と `s8b_oracle_manifest.py:430-468` が実運用の照合経路である。親の「凍結 artifact に oracle observations が 0 件」は `test_frozen_artifacts.py:41` 以下の全体検索では支持されるが、「pin 閉包が 0 件」は不正確である。プランの `s2-plan.md:74-85,172-181` はこの検査を編集面・受入条件から落としている。

影響: reviewed-spec の generator hash と独立 golden を更新しないと `load_approved_spec` が先に拒否し、certified report、oracle verdict、台帳が生成されず、受理集合は空になる。

[B-2] real（変異帰属が汚染される。実行範囲依存）

`s2-plan.md:155-168` の M1-M5/M10 は report、M6-M9 は judge の source mutation であるため、広い受入範囲では既存の `test_s8b_oracle_manifest.py:1078-1093` が全て先に殺す。新 receipt 検査による kill と区別できない。M1 の現在の指定 test も `test_s8b_oracle_report.py:1499-1506` では receipt を検査していないため、プラン記載の assertion 追加が実際に必要である。

影響: mutation ledger が「新 receipt が受理集合を縮めた」と誤記し、certified 選択の縮小根拠と検査帰属を証明できない。

[B-3] real（M10 の指定 killer が変異箇所を通らない）

プランは `s2-plan.md:10,60` で absolute と `..` を resolve 前に拒否する一方、M10 は resolve 後の `relative_to(output_root)` を削り、killer は `:147-149,168` の `[absolute]` である。この負例は前段の literal 拒否で落ちるので、M10 の変異行を検査しない。既存 symlink が output root 外を指すケースも登録されていない。

影響: out-root 外の symlink 経由 store が読める変異が生き残り、receipt の `store_path` 参照先と certified 判定の実体が別 root になり得る。

[B-4] 疑い（現行 certified 経路では未発火）

`build_observations` の production 呼出しは `s8b_oracle_report.py:2014` の 1 件だけで、他は `test_s8b_oracle_report.py` 139 件と `test_s8b_oracle_driver.py:4667` である。したがって keyword-only default 自体は本番 bypass にならない。だが `s2-plan.md:26` は official direct API の token 省略を許し、`s8b_oracle_artifacts.py:64-68,264-268` は receipt 欠落の `OfficialObservations` をロードできる。現行 production consumer は `test_s8b_oracle_manifest_contract.py:18-29` の judge/verdict に限定されるため、現時点では実害なし。

影響: 未登録の将来 consumer が judge を経ずにこの marker を受理すると、receipt 無しの observations が certified 入力として流れ、受理集合が広がる。

[B-5] nit（親の post-run 0 件主張の表現）

`s8b_floor_campaign.py:4350-4386` の `_verify_resume_store` は store を再読し、`:6131-6139` から呼ばれる。これは resume の実走前 gate なので T-1086 の「実走終了後から report 生成まで」の主張は支持されるが、「repo 全体に 0 件」は字義どおりには誤りである。

影響: 対象時間窓を明記すれば certified 選択、report、台帳の値は変わらない。

裁定パッケージ候補（scope 外）

[B-6] real（T-1103 相当のため今回の blocker にはしない）

judge の予定 validator は `s2-plan.md:16-18,38-49` にある cell 集合・SHA 形式・state しか検査せず、`expected_sha256` を freeze の binary hash に再束縛できない。`judge_oracle` の引数は `s8b_oracle_judge.py:313-317` のままで、`s8b_verdict.py:273-295` からも binary authority は渡らない。store と observations の receipt を同時に改変し、`expected_sha256=actual_sha256`、state=`match` にすれば determinate に到達する。これは `docs/phase3.md:688-691` が T-1103 として明示的に見送った偽造耐性の問題であり、裁定 package に分離すべきである。

影響: store 差替えと receipt 同時改変では winner、certified status、受理集合が変わらず、receipt は偽の緑になる。

確認済みの非所見: `judge_oracle` の production 呼出しは `s8b_verdict.py:290-295` と judge CLI `s8b_oracle_judge.py:595-600` で、位置引数 1 + keyword 3 は維持される。n pilot は `s8b_oracle_n_pilot.py:1-6,1951-1958` で明示的に非 certified、exploration は `s8b_oracle_exploration.py:24-53` の別 marker であり、現行 certified 経路の取りこぼしではない。既存の observations exact pin は `test_s8b_oracle_report.py:4414-4434`、loader の逐語保持は `test_s8b_oracle_artifacts.py:198-204`、perf closure meta-test は `test_official_perf_closure.py:753-768,795-855` であり、後者は observations schema の二重管理ではない。

## 総括

- frozen artifact 直下の observations pin は 0 件だが、source-byte pin 閉包は非ゼロ。
- 最優先は reviewed-spec の source hash と独立 golden の更新漏れ。
- M1-M10 は既存 source pin との多重 kill を mutation ledger で分離すべき。
- M10 には symlink escape の直接 killer が必要。
- production の default 呼出し残存と judge API bypass は現時点で確認されない。
- store-only の post-run 差替え検出という wave の狙いは成立する。
- store と receipt の同時偽造は T-1103 の裁定候補として残る。