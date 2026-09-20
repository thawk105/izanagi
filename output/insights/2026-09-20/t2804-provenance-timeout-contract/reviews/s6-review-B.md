## 所見

以下は静的レビューです。行番号は実装後のファイルを指します。裁定正本は [s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/s4-ruling.md) です。

1. **real / must-fix — 終端ログの field 名が契約と異なる。** `tools/check_ai_provenance.py:2945`、`orchestrator/tests/test_check_ai_provenance.py:6987`：裁定 §2.5 の `deadline_margin_s` を `deadline_at_margin_s` に置換しており、放置すると観測成果物に契約指定 field が存在しない。

   field の追加ではなく改名である。author 報告は別の依頼本文を根拠にしているが、今回指定された正本とは一致しない。本体とログ期待値を正本へ合わせればよく、別名併記の互換層は不要。

2. **real / should — DW-O13 の厳密不等式を満たしたという説明はできない。** `orchestrator/tests/test_check_ai_provenance.py:6952`、`docs/dev-wave/operations.md:107`：実際の検査は `288+90+60+32=470` を許し、放置すると「終了余裕込みで外側未満」という未検証の保証を受入済みと記録してしまう。

   実装・テストは **裁定 §3 の指定には一致**する。`post>0` により内側期限が外側より早いことは固定するが、実際の後段時間 `h<32` は固定しない。したがって、ここで独断で予算をさらに削るべきではない。「C-2804 の予約算術を検査、DW-O13 の実時間条件は別途実測」と区別する必要がある。

   定数コメントは、60 秒の母集団・harness regime、16 秒が運用閾値であること、32 秒が代理値であることを明記している。ただし、harness regime と provenance の同等性、poll 5 秒が観測遅延の上限であることまでは証明していない。

3. **real / should — 既存 D612 テストが新 env の継承に依存する。** `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:181,206`：新 env を消していないため、放置すると正しい実装でも kwargs 不一致、残余不足の rc=16、または不正値例外でテストが赤になる。

   対象は `test_provenance_dispatch_omits_both_overrides_when_unset` **だけでなく** `test_provenance_dispatch_forwards_both_d612_overrides` も含む。両テストで新 env を `monkeypatch.delenv(..., raising=False)` すれば足りる。期待値を部分一致へ緩める必要はない。

   これはテストの環境隔離不足であり、本番の受理集合の欠陥ではない。通常の land は子へ渡す env を設定するため、これだけで呼出元のテスト環境が汚染されるわけでもない。提示ログの緑は、その実行環境での成功を示す。

4. **refuted / — 裁定外の拒否 gate・一般化・互換層はない。** `tools/check_ai_provenance.py:2892,2927`、`tools/dev_wave_land.py:3565`：有限値検査、合成 Q の下限拒否、継承期限の上書きはいずれも契約本体であり、削除すると裁定された fail-closed または期限伝播が失われる。

   新引数や注入 seam の全面変更はなく、dispatcher・D612 parser・rc 分類も差分に含まれない。削除対象となる要求外実装は認めない。

5. **refuted / — fail-closed の向きと境界は一致する。** `tools/check_ai_provenance.py:2896,2927,2956`、`orchestrator/tests/test_check_ai_provenance.py:6896,6932`：不正 env は rc=16、有限の過去期限は残余不足、合成 Q がちょうど16秒なら投入となり、無予算の既定 dispatch へ戻る穴はない。

   `test_outer_deadline_invalid_value_returns_infra` は rc と dispatcher 未呼出しを検査する。`test_outer_deadline_refuses_before_dispatch` は過去・負期限、15.9秒拒否、16秒投入を検査する。診断文字列だけの検査ではない。

6. **refuted / — テストの帰属・期待値改訂は弱体化していない。** `orchestrator/tests/test_check_ai_provenance.py:6825,6866`、`orchestrator/tests/test_dev_wave_land.py:4820,5847,10018`：実 `_default_dispatch` が末端 dispatcher に渡す値を検査しており、変更した helper を fake で迂回して緑にする構造ではない。

   `_bounded_scope_membership`、`admit_fn`、`_run_bounded_scope` は今回の予算導出の外側にある既存の経路制御 seam。cap_oom では時計を40秒進め、Q が288から248へ減ることまで固定する。ただし、これらは実 cgroup・OOM・qdel 自体の検証ではない。

   期待値1438・288・248・258は独立した literal。定数を参照する予約算術にも `==32/60/16` があり、production helper で期待値を再計算していない。land の AST 検査は定数名と480を固定し、env は追加一 key 以外 exact、timeout 文面の検査は追加されている。

7. **real / should — M12 の「赤理由は ==480 だけ」という登録説明は広すぎる。** `s4-ruling.md:92`、`orchestrator/tests/test_dev_wave_land.py:5848,10018,12160`：481への変更は期限範囲・実 timeout・診断にも波及し、放置すると診断だけの赤まで単一理由の検出証拠に混ぜ得る。

   `test_cumulative_wait_budget_arithmetic_uses_production_timeouts` の `==480` を代表証拠にすれば単一理由を示せる。他の赤は別途分類し、`after 480 seconds` の不一致だけを kill に数えない。複数テストが赤になること自体は欠陥ではない。

8. **real / should — 延長案(b)の総時間説明が不正確。** `s4-ruling.md:111`：5130秒は85分30秒の provenance 予算であり、放置すると lock 待ち・他検査を含む land 全体の最長時間を過小に伝える。

   区間和と同額への延長だけでは厳密な終了余裕もない。(a)の480・累積lock待ち・harness算術維持、(c)の全区間未充足とharness改訂、(d)の固定 `subprocess.run` 構造変更という帰結は妥当。

9. **判定不能 / — 推奨(a)を支える本 wave の実時間証拠は未提示。** `s4-ruling.md:114`、`codex/s5-author.md`「未実装・未実走」：85件と旧checkerの6点は参考材料であり、放置すると未提示の L1〜L3・h 実測まで確認済みの根拠として扱われ得る。

   提示された `focus-1.log` は3893 passed・7 skipped・rc=0の焦点走であり、C-2804 の L1〜L3や後段 h の実測を代替しない。推奨(a)は暫定的な選択としては理解できるが、根拠が本 wave の実測だけで閉じているとはいえない。

### 受理集合の照合

| 条件 | 実装後の変化 | 裁定との一致 |
|---|---|---|
| 新 env 未設定／local scope | kwargs／local 経路は不変 | 一致 |
| Q 超過だが旧480秒内に完了可能 | checker rc=16 → land rc=29 retryable に移り得る | 一致 |
| 完了が `(deadline_at, K]` | 早期打切り・hold latch が生じ得る | 一致 |
| 不正 env・残余不足・D612 Q=0併用 | 投入前 rc=16、新規job/holdなし | 契約に一致。§2末尾の二帯だけではこの縮小を尽くさない |
| queue超過で取消成功 | pending hold/job残留を減らす | 条件付きで一致 |
| RUN/collection期限到達 | hold latchが残り得る | 一致。残留集合全体の単純な縮小ではない |

`(deadline_at,K]` で以前は正常完了した要求について、旧挙動まで一律「SIGKILL残留」とすることはできない。裁定 §2 の括弧書きは、旧外側期限にも達する場合に限定して読む必要がある。

固定しているテストは次のとおり。

- **env未設定の恒等**：`test_outer_deadline_unset_preserves_dispatch_kwargs`。D612有無の両方を exact 検査。
- **D612 Q=0併用の投入前拒否**：`test_outer_deadline_composes_d612_with_min[0-None]`。rc=16と末端未呼出し。
- **checkerの返却rc維持**：`test_outer_deadline_terminal_line_reports_observable_values`。mainの0・1・16を直接検査。
- **landの同じrcに対する写像**：`test_provenance_gate_accepts_tip_zero_and_lands`、`test_provenance_checker_violation_rc_is_release_safe_and_releases`、`test_provenance_checker_infrastructure_rc_is_retryable_and_retains`、signal／timeoutの対応テスト。
- **rc=1判定不変**：上記 violation テストが rc=29・release_safe=true・retryable=false・lease解放・main不変を固定。

「同じ返却rcの写像が不変」と「同じ監査入力が同じrcまで到達する」は別であり、後者は期限短縮で変わる。

## 分類表

「過剰」は要求外の仮想リスク向け実装を指す。

| 差分要素 | 分類 | 削除・不足の判定 |
|---|---|---|
| checker定数4つ | 本体 | 契約の識別子・予約・閾値。削除不可 |
| 有限値parser | 本体 | 不正値を未設定扱いにしないため必要 |
| D/Q導出・D612とのmin合成 | 本体 | 主目的そのもの |
| 投入前拒否 | 本体 | 明示された運用閾値。追加の仮想gateではない |
| 終端1行・finally | 本体 | 要求された観測。field名修正が必要 |
| land定数・env上書き・timeout文面 | 本体 | 外側480維持と絶対期限伝播 |
| unset 2 case | 検査 | 未設定恒等 |
| derives 1 case | 検査 | 独立期待値でD/Q固定 |
| all_entries 3 case | 検査 | force／headroom／cap_oom |
| refuses 5 case | 検査 | 拒否方向・過去期限・等号 |
| composes 4 case | 検査 | D612小／大／同値／0 |
| invalid 6 case | 検査 | fail-closed |
| reserved_intervals 1 case | 検査 | C-2804算術。厳密終了保証とは区別が必要 |
| dispatcher_defaults 2 case | 検査 | 既定値複製を防ぐ |
| terminal_line 5 case | 検査 | rc維持と観測。field名期待値を修正 |
| local_scope 2 case | 検査 | 適用範囲の不変 |
| land AST改訂 | 検査 | 定数名・480・1280算術を維持 |
| land subprocess/env改訂 | 検査 | 実引数・期限範囲を固定 |
| land非権威rcのstderr追加 | 検査 | stderr非転送・既存分類を固定 |
| land TimeoutExpired改訂 | 検査 | 定数参照と従来文面を固定 |
| land継承env上書き追加 | 検査 | setdefaultへの退行を検出 |
| 要求外gate・一般化・互換層 | 過剰 | 該当なし |

新規checkerテストは **10種31 case**。削るべきテスト群は認めない。不足は既存D612テストのenv隔離と、静的テストでは代替できない実時間証拠である。

## 変異登録の判定

以下は**静的な検出見込み**であり、変異実走のKILLED／SURVIVED結果ではない。テスト名の `test_outer_deadline_` を `OD_` と略記する。

| 変異 | 殺すtest／期待方向 | 単一理由の判定 | 既存検出 |
|---|---|---|---|
| M1：post控除なし | `OD_derives_deadline_and_queue_wait`、`OD_reserved_intervals_fit_outer`／Dが1438→1470 | 可。実引数の期限延長で検出。ログ差だけは除外 | 指定既存テストでは確認できず |
| M2：C控除なし | `OD_derives_deadline_and_queue_wait`／Qが288→378 | 可。cleanup予約の欠落 | 同上 |
| M3：pre控除なし | `OD_derives_deadline_and_queue_wait`／Qが288→348 | 可。前段予約の欠落 | 同上 |
| M4：min→max | `OD_composes_d612_with_min`／Q=100が288へ、Q=900が900へ | 可。明示上限または導出上限を破る | 同上 |
| M5：`<`→`>=` | `OD_refuses_before_dispatch`、`OD_derives_deadline_and_queue_wait`／正常投入を拒否、不足を投入 | 可。rc・呼出し有無が反転 | 同上 |
| M6：`<`→`<=` | `OD_refuses_before_dispatch` の198秒残余／Q=16正例 | 可。承認済み境界を過剰拒否 | 同上 |
| M7：未設定でもkwargs追加 | `OD_unset_preserves_dispatch_kwargs`／恒等性破壊 | **具体的編集は判定不能**。実際にkwargs追加へ到達させること。None演算例外だけの赤は不可 | 既存 `test_provenance_dispatch_omits_both_overrides_when_unset` でも検出。新規検出力ではない。これは登録matrixの2 file外 |
| M8：deadline_at削除 | `OD_derives_deadline_and_queue_wait`、`OD_applies_to_all_dispatch_entries`／外側由来期限が届かない | 可。末端引数欠落で検出 | 指定既存テストでは確認できず |
| M9：不正値→None | `OD_invalid_value_returns_infra`／rc=16・未投入からrc=0・投入へ | 可。ただしfloat変換失敗と非有限値の両方を変異対象として明記 | 同上 |
| M10：land env設定削除 | `test_provenance_subprocess_contract_and_exception_mapping`、`test_provenance_outer_deadline_overwrites_inherited_value` | 可。期限伝播の欠落。前者は新env未継承を固定すると明確 | env期限の検出は今回追加 |
| M11：setdefault化 | `test_provenance_outer_deadline_overwrites_inherited_value`／9999が残る | 可。継承値ありの入力で上書き失敗だけを狙う | 専用検出は今回追加 |
| M12：480→481 | `test_cumulative_wait_budget_arithmetic_uses_production_timeouts` の `==480`、subprocess契約testのtimeout検査 | 代表node内では可。全赤が単一assert由来ではない。診断のみの赤は除外 | 実timeout==480は既存検査。新規検出力ではない |
| E0：min引数交換 | 対応する全ODテストが通る見込み | 可。入力は有限値で、数値として同じmin。SURVIVED期待 | 等価対照であり検出力の主張なし |

M1〜M4・M8・M10〜M12の引数検査は、今回変更する境界そのものを観測しているため、単なる診断文字列検査ではない。ただし、それをPBS取消・hold解消の実測証拠に拡張してはならない。

## 判定

**NO-GO** — 正本が要求する終端field名を本体・テストで一致させる必要がある。予算導出と拒否条件の再設計は不要。

## 総括

C-2804の機構、拒否方向、D612合成、rc分類維持は静的に整合する。修正必須は終端field名の契約不一致。併せて、既存テストのenv隔離、DW-O13の保証範囲、変異の赤理由、延長案の総時間説明を修正すべきである。

書込み・pytest・変異実走は行っていない。提示された焦点走は3893 passed・7 skippedだが、L1〜L3と後段hの証拠は確認できない。

NO-GO