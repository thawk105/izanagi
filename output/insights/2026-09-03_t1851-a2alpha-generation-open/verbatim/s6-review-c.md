## S1〜S12 の裁定照合

1. [実測] nit（適合確認）— S1 は一致する。`TransitionPolicy` と `DomainProfile` の追加 field は keyword-only で、default はそれぞれ `True` / `None` である。v1 factory と S8C constructor は追加引数なしのままである。根拠: `orchestrator/campaign/attempt_registry_core.py:168-201`; `orchestrator/campaign/s8b_attempt_profile.py:587-636`; `orchestrator/campaign/trial_registry.py:2113-2164`。  
   成果物影響: v1 台帳の既定遷移・terminal 受理集合は変わらない。

2. [実測] nit（適合確認）— S2 は一致する。terminal validator は classification equality と null matrix の後に呼ばれる。根拠: `orchestrator/campaign/attempt_registry_core.py:1300-1327`。  
   成果物影響: v1 の `None` は no-op、v2 terminal だけが追加 validator で拒否される。

3. [実測] nit（適合確認）— S3 は一致する。retryable terminal の次 ordinal 開放直前に policy が検査され、v2 factory だけが `False` を指定する。根拠: `orchestrator/campaign/attempt_registry_core.py:1115-1140`; `orchestrator/campaign/s8b_attempt_profile.py:662-683`。  
   成果物影響: v1 recovery 列は従来どおり、v2 の未承認 recovery ordinal は開かない。

4. [実測] nit（適合確認）— S4 は一致する。旧 comparator は `_assert_exact_profile()` に抽出され、schema object identity で v1/v2 factory を選び、新 2 field も exact 比較する。根拠: `orchestrator/campaign/s8b_attempt_registry.py:319-486`。  
   成果物影響: canonical v2 だけが新規受理され、偽造 profile は引き続き台帳入口へ到達しない。

5. [実測] nit（適合確認）— S5 は一致する。v2 factory の validator は指定署名で無条件拒否する。根拠: `orchestrator/campaign/s8b_attempt_profile.py:555-563,683`。  
   成果物影響: sealed evidence API が無い現段階では v2 terminal 行は台帳へ入らない。

6. [実測] nit（適合確認）— S6 は一致する。legacy terminal 2 入口はいずれも core 呼出し前に v2 を拒否する。根拠: `orchestrator/campaign/s8b_attempt_registry.py:2295-2315,2364-2374`。  
   成果物影響: 自己申告 terminal 値が v2 台帳へ混入しない。

7. [実測] nit（適合確認）— S7 は一致する。`_entry_paths()` の全 11 呼出しが protocol-aware で、handle 経路は保存済み `registry_path` も再照合する。根拠: `orchestrator/campaign/s8b_attempt_registry.py:554,568,1597,1640,1691,1918,2148,2318,2375,2434,2537`。  
   成果物影響: v1 は一段 path のまま、v2 は protocol 世代 path から逸脱しない。

8. [実測] nit（適合確認）— S8 の production 実装は一致する。64-hex 世代 path、symlink・非 directory・不完全世代・既存世代を拒否する create-only publisher がある。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1022-1092`。  
   成果物影響: 既存世代の上書きや不完全世代の補完により台帳参照がすり替わることを拒否する。

9. [実測] nit（適合確認）— S9 は一致する。claim v3 の address は binding 3 field、slot 6 fieldを含み、v3 schema・exact key set・reader/writer が分岐する。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1155-1196,1209-1269,1272-1341`。  
   成果物影響: protocol・schedule・measurement を含む世代別 claim が別 filename と参照を持つ。

10. [実測] nit（適合確認）— S10 は一致する。legacy marker の key set と比較内容は保持した rename で、v2 observation は capability 経路へ分岐する。根拠: `orchestrator/campaign/s8b_attempt_registry.py:57-69,2089-2135,2170-2225`。  
    成果物影響: v1 consumed marker の受理集合は変わらず、v2 は legacy marker では開かない。

11. [実測] nit（production 適合確認）— S11 の実装は一致する。prelock hook は lock 前に一度だけ呼ばれ、marker の lock interval 内で `_atomic_update_locked()` に入り、同関数自身も live-lock guard を持つ。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1435-1447,1532-1579`; `orchestrator/campaign/s8b_holdout_admission.py:5004-5009,5140-5172`。  
    成果物影響: v2 mutation は capability と同じ admission lock interval に束縛される。

12. [実測] nit（適合確認）— S12 は一致する。reserve/resume に keyword-only `consumption_marker=None` が追加され、v2 は必須、v1 は `None` を受理する。戻り型は従来どおりである。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1653-1670,1697-1733,2465-2504`。  
    成果物影響: v1 caller は変更不要で、v2 は marker 無しに start/resume できない。

E1、E2、sealed terminal API 2 本、launcher 変更は差分に入っていない。v2 retryable 集合も空である。根拠: `orchestrator/campaign/s8b_attempt_profile.py:532-533,555-563`; `orchestrator/campaign/s8b_attempt_registry.py:2295-2300`。

## v1 受理集合

13. [実測] nit（不変確認）— v1 の受理集合を広げる変更は見つからなかった。

   根拠:

   - `assert_registry_rows()` / `load_attempt_registry()` の signature・戻り型は不変: `orchestrator/campaign/attempt_registry_core.py:1374-1383,1454-1462`
   - legacy `record_attempt_terminal()` の signature・`None` 戻りは不変: `orchestrator/campaign/s8b_attempt_registry.py:2303-2311`
   - resume の戻り union は不変で、追加引数だけが default `None`: `orchestrator/campaign/s8b_attempt_registry.py:2465-2484`
   - v1 claim address payload と claim v2 key setは不変: `orchestrator/campaign/s8b_attempt_registry.py:1141-1152,1173-1176,1245-1263`
   - legacy marker exact key setは不変: `orchestrator/campaign/s8b_attempt_registry.py:57-69,2089-2135`
   - v1 は `_profile_protocol_sha256()` から常に `None` が返り、一段 path を使う: `orchestrator/campaign/s8b_attempt_registry.py:489-495,498-517`

   成果物影響: 既存 v1 registry、claim filename digest、legacy marker、resume handle の値・参照に変更はない。

## D1522 の三組

14. [実測] nit（充足）— S2/S5/S6 は充足する。core replay の直接検査、validator 差し替えの呼出し assertion、v1 terminal 正例が同じ node にある。adapter→core の差し替え呼出しと正例も別 node で固定されている。根拠: `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2251-2380`; `orchestrator/tests/test_s8b_attempt_registry.py:2726-2758`。  
    成果物影響: 両 terminal 層を同時に失えば v2 自己申告 terminal が受理され、当該検査がそれを検出する。

15. [推測] must-fix — S7/S8 の symlink 四層は D1522 を満たさない。新設 test の symlink は publisher 自身の既存-generation 分岐で拒否され、`_read_regular_bytes`、generation に対する `_ensure_durable_directory`、`_write_staging`、admission guarded writer まで到達しない。stub の呼出し assertion も最上位 publisher にしかない。根拠: `orchestrator/campaign/s8b_attempt_registry.py:582-599,887-967,984-1019,1052-1092`; `orchestrator/tests/test_s8b_attempt_registry.py:2508-2595`。  
    成果物影響: 四層を落とした変異が既存 destination / incomplete-generation 拒否にマスクされ、symlink alias による台帳参照変更・予算二重計上を誤って防御済みと認証しうる。

16. [推測] must-fix — S11 の下層 `_atomic_update_locked()` guard は直接検査されていない。唯一の直接呼出しは正常 lock の正例だけであり、高位 test の差し替えは `marker.use()` 側の先行 guard で停止する。`s8b_attempt_registry.py:1447` を消しても現行 node は赤にならない。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1435-1447`; `orchestrator/campaign/s8b_holdout_admission.py:5172`; `orchestrator/tests/test_s8b_attempt_registry.py:2372-2407,2622-2645`。  
    成果物影響: 下層 guard の退行を見逃すと、将来の直接 consumer から lock 外更新が可能になり、試行台帳の順序・chain head が競合で変わりうる。

## 恒真な保証・到達不能 guard

17. [推測] nit — v2/v1 profile が選んだ exact slot codec で parse した直後の slot-type guard は production から発火不能である。該当するのは reserve、observation、resume の型再検査で、これらを消して赤になる test node は見当たらない。根拠: `orchestrator/campaign/s8b_attempt_registry.py:462-465,1710-1714,2170-2176,2581-2587,2838-2847`。  
    成果物影響: 現行成果物の値・受理集合は変わらないため nit。防壁ではなく内部型 assertion として扱うべきである。

意図された mask は、adapter terminal guard 単独の M4a、symlink 上層単独の M7a、`_atomic_update_locked` guard 単独の M10a である。このうち M4b は core 直接検査で実体がある。M7b は所見15、S11 の直接性は所見16の不足が残る。

## v2 terminal の暫定 fail-closed

18. [実測] nit（裁定を維持）— 暫定拒否は単なる診断文字列 test ではない。core replay は exact error class と anchored signature で拒否され、同じ test 内で v1 terminal が成功する。公開 adapter 経路でも v2 lifecycle が実際に `CapturedObservation` まで進んだ後に exact signature で拒否される。根拠: `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2271-2318`; `orchestrator/tests/test_s8b_attempt_registry.py:2643-2703`。  
    成果物影響: 現 wave では v2 terminal 行をゼロに保ち、v1 terminal 行は維持する。

A2β で supersede すべき pin は次の二箇所である。

- `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` の v2 拒否部分: `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2281-2297`
- `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` の adapter 拒否部分: `orchestrator/tests/test_s8b_attempt_registry.py:2694-2703`

v1 正例、forged `terminal_row_validator=None` の exact-profile 拒否、validator が non-`None` である pin は supersede 対象ではない。

## 既存テストの期待値変更

19. [実測] nit — `profile=v2_profile` から `replace(v2_profile, terminal_row_validator=None)` への変更は、E3 により canonical v2 が正当に受理されることの必然的帰結であり、テストを甘くした変更ではない。失われた性質は「canonical v2 を public mutation が拒否する」の一件だけで、これは意図的に supersede されている。canonical v2 の create/read 正例と、新 2 field の exact gate が新 node にある。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:2410-2490`。  
    成果物影響: canonical v2 世代が新規受理される一方、validator を除去した偽造 profile は引き続き拒否される。

20. [実測] nit — test 名は実態とずれている。`test_v2_profile_is_rejected_by_public_mutation...` が実際に拒否しているのは canonical v2 profile ではなく validator を除去した forged profile である。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:2410-2445`。  
    成果物影響: 台帳値は変わらないが、node 選定時に「canonical v2 拒否が残る」と誤読させる。

## 絶対規律 2

21. [実測] nit（違反なし）— v1 validator の緩和、現行 hash の fixture 焼き込み、揮発 payload の期待値化は見つからなかった。v2 capability test は既存 admission issuer から claim/marker を取得し、adapter が claim payloadを検証して generation digest を導出する。公開 API はその digest を別引数として受け取らない。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:240-318`; `orchestrator/campaign/s8b_attempt_registry.py:1344-1375,1697-1727`。  
    成果物影響: 呼び手が別の generation authority 値を直接選んで試行台帳を開く受理拡大はない。

22. [実測] nit — runtime は v2 create/read を受理するが、その二つの public annotation はまだ v1 slot/profile 型のままである。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1582-1591,1628-1635`; runtime 正例 `orchestrator/tests/test_s8b_attempt_registry.py:2449-2465`。  
    成果物影響: runtime 成果物は変わらないが、将来の型検査付き production caller が正当な v2 呼出しを表現できない。

## 未 land 前提

現 checkpoint だけで許される不完全さは、v2 terminal の全拒否、空の retryable 集合、sealed API・E1/E2・launcher carrier・production marker handoff・proof-chain consumer の不在である。これらは `land しない` という D1341 の前提がある場合だけ許される。

land 前に必ず閉じる必要がある穴は次のとおりである。

- 所見15、16の D1522 直接検査。
- A2β の raw-facts carrier、E1 validator、E2 の4語、sealed terminal API。classified-failure API は具体的 production callerを付けるか削除する。
- launcher から v2 marker を渡す production handoffと、D1194/D1337 の proof-chain 束縛を同じ land 単位に入れる。
- 未裁定の evidence-bound handle、pre/post probe、`expected_use_perf` authority、および持ち越し裁定を閉じる。
- pytest、変異 matrix、受入全走を実走して確認する。現在の `rc=16` は緑でも赤でもない。

## 総括

- blocker の一覧: 非 land の A2α checkpoint としての blocker はなし。ただし、現状態を land すること自体は D1341 により blocker。
- v1 受理集合の不変性: 静的には不変。広がる変更は見つからなかった。
- D1522:
  - S2/S5/S6: 充足。
  - S7/S8: 不充足。四層の直接到達・差し替え assertion がない。
  - S11: 不充足。`_atomic_update_locked` の下層 guard を直接拒否検査していない。
- 恒真・到達不能:
  - M4a/M7a/M10a の単層 mask は意図どおり。
  - M7b の KILLED 根拠は既存-generation拒否にマスクされる。
  - codec 選択後の slot-type guard 4箇所は production 到達不能。
- 既存テスト変更: E3 の必然的帰結。失われた canonical-v2 拒否は意図的で、canonical-v2 正例と forged-profile 拒否へ置換済み。test 名だけ不正確。
- land 前の必須穴: D1522 2組、A2β、unit C handoff＋proof-chain 同時 land、未裁定事項、全 test/mutation/acceptance 実走。
- 読めなかった資料: なし。指定5資料を順番どおり全文読了した。
- 確かめられなかった事実: pytest結果、mutation実走結果、受入全走、再投入中のD612結果。テストは実行しておらず、別 worktree・親 repoも読んでいない。