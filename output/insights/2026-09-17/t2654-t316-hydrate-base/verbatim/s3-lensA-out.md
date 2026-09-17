## 規律 2 への攻撃

[A-1] refuted — prepare による `config.h` 生成は供給側の正常化であり、提示 plan に関門の判定規則を緩める変更はない。

根拠: `s2-plan-out.md:59,100` は共有 configure から従来どおり関門へ渡し、関門例外を伝播させる。`probe.py:124,357` の exact pair、`:390` の verdict、`:1928` の関門本体は変更対象外である。prepare の `_run` が rc=0 の stderr を拒否しないことも、後続の関門の stderr 判定・`:1960` 以降の診断を置換しない。

ただし「cache 直指しと受理集合が同じ」は限定が必要。同じ完成済み入力に対する**関門の判定規則**は同じだが、生成物欠落を prepare で補うため、元の cache 状態から見た S6 全体の到達集合は変わる。また hydrate は origin・index bit 等を検査するため、旧経路より拒否が増える入力もある。両者を同一の受理集合と記述しないこと。

[A-2] refuted — 関門未到達の失敗が go になる経路はないが、hydrate と prepare では拒否理由が異なる。

根拠: `probe.py:390` の優先順位は attempted → walltime → toolchain → source identity → condition gate である。

| 失敗位置 | plan に沿った観測 | 現行 verdict |
|---|---|---|
| hydrate 失敗 | identity 未採取、`source_identity_valid` 未設定または false | `S6_SOURCE_IDENTITY_INVALID` |
| prepare 失敗 | identity=true、関門 family 空 | `S6_CONDITION_GATE_UNPROVEN` |
| 残時間不足 | `failure_stage="walltime"` | `S6_WALLTIME_RESERVE_REACHED` |

`success=False` 自体が拒否の決め手ではない。`s2-plan-out.md:49,287` の失敗テストでは、観測だけでなく `verdict_s6` の理由コードも上表どおり確認すること。hydrate 失敗まで一律に `S6_CONDITION_GATE_UNPROVEN` と説明するのは誤り。

## 裁定整合 (D2032 / D1625 / D2085)

[A-3] refuted — host 関門と sandbox build の名前空間の違いだけでは、third-party source の同一性は破れない。

根拠: `s2-plan-out.md:54,59` は同じ canonical S を共有し、`SandboxProfile.argv` (`probe.py:849`) は `--ro-bind S S` を作る。S が scratch 外なら、後続の writable scratch bind (`:851`) に覆われない。読み書き権限の違いはあっても、同じ source tree を参照する構成である。

ただし path 文字列の一致だけでは証明不足。plan の実 sandbox 内の読み取り・書込み拒否検査まで必要。D2032 の直接の指定は CCBench の patch 木であり、third-party への適用は brief が明示した追加の不変条件として説明するのが正確である。

[A-4] real — P2 は D2085 の射程を「二重検査一般の禁止」へ広げている。

根拠: `s1-brief.md:48–49` は「二重検査は D2085 の射程」とする。一方、逐語の決定は「**job body が gflags / glog を build する直前の検査**」を変更前のまま維持し、「**本 wave では実装しない**」という限定である。既存の A-2 検査を不要と判定する一般規則ではない。

是正: `_verify_pristine_floor_dependency_sources` を導入しない理由は、「今回の経路は新規 S への実 hydrate が使用前検証を既に実施し、A-2 の追加コピー経路を導入しない」「本依頼は追加 gate を scope 外としている」に置き換える。D2085 は類似する scope 判断の先例に留める。逆に、A-2 に存在するという理由だけでその検査を新設する必要もない。

[A-5] refuted — D2032 の prepare 却下欄は今回の合流を禁止していない。

根拠: D2032 の却下理由は「本 wave の本題ではないので別項へ送り」であり、D2044 項27 がその供給問題の解消を明示している。D1625 の exact pair は変更しない。

ただし `s2-plan-out.md:261–269` の S/B 分離は、先例と argv まで同じ構成ではない。「同じ準備済み source を供給する合流」と記述し、先例の緑をこの構成の実測証拠として転用しないこと。

## 変異の帰属

[A-6] refuted — (a) の cache 直指し変異には、plan が専用 killer を指定している。

該当 node は `test_t316_sandbox_probe.py::test_s6_live_offline_source_paths_and_prepare_order`。`s2-plan-out.md:277` は prepare・関門・両 configure の source path を S と exact 比較し、cache に ignored `config.h` を残す fixture を指定している。

現行 fixture の空 cache (`test_t316_sandbox_probe.py:1845–1850`) のままでは成立しないが、plan `:169–175` は**5 本の実 Git repository**へ置き換える。したがって「空 cache の hydrate 失敗だけで殺す計画」という攻撃は反証される。事前登録では、正常系と変異系の双方で hydrate 成功を確認し、path assertion の失敗を KILL 根拠にすること。

[A-7] real — (g) は JSON 解読失敗に遮られ、rc 無視へ帰属できない。

根拠: `fetch_third_party.py:629` は clone 前に全 cache を検証する。glog origin 不一致なら `main:764–766` が stderr を出して rc=1 を返し、成功 JSON (`:752–762`) は出ない。

そのため rc 判定だけを消しても、plan `:49` の JSON 解読失敗処理で停止できる。`s2-plan-out.md:283` の「次段 `_git_head` 到達時 assertion」は発火せず、同じ失敗 stage のまま変異が生存し得る。

是正: 実 CLI origin 不一致テストは統合失敗系として残す。rc 判定の変異は、正常 JSON を持つ非0 rc の記録を使う局所テストへ再照準するか、実 rc=1 の観測後に JSON 解読へ進むこと自体を禁止する observer を設ける。後段 identity の監視だけでは足りない。

[A-8] real — (d)/(e)/(i) は assertion の実行時点を固定しないと、別の失敗が先行する。

根拠: `s2-plan-out.md:280–285` は配置・bind・argv の assertion を挙げるが、いつ実施するかが未指定。現行 `_observe_s6_wiring` は `observe_s6` 終了後に結果を返す (`test_t316_sandbox_probe.py:1951–1969`)。

- **(d)** S が writable scratch 内に入っても build は成功し得る。S 配置を build 前に直接検査し、書込み成功は別の証拠にする。
- **(e)** S の bind 欠落では inside configure の source 不在が先に発火し得る。最初の build 呼出し時に profile/bwrap argv を検査する。
- **(i)** `BASE_DIR=S` では host 関門が S 内に binary directory を作り、inside configure で書込み拒否になり得る。関門入口と configure 実行直前に argv を検査する。

是正: 事前登録で「最初に失敗させる assertion」を指定する。単なる inside build 失敗を、それぞれの狙った防壁の KILL と数えない。

[A-9] refuted — (b)/(c)/(f)/(h) は、plan の専用観測を用いれば帰属先を分離できる。

| 候補 | 帰属先・条件 |
|---|---|
| (b) prepare 省略 | `:278` の関門入口で「実 prepare return 済み」を確認する。header 欠落は別の統合証拠。 |
| (c) 関門だけ S | `:279` の実 build configure argv と S の exact 比較。関門成功だけを根拠にしない。 |
| (f) 束縛脱落 | `:160,282` の独立 literal 集合比較。両一覧から同時脱落しても検出可能。dirty 拒否とは証拠を分ける。 |
| (h) inside prepare | `:284` の実 call 数 exact 1。helper は host 実行なので、ro-bind による自然失敗を期待しない。 |

これらも結果の成功/失敗だけでは不十分。特に prepare 周辺の `except Exception` (`:98`) が observer の `AssertionError` を通常失敗へ変換し得るため、call 数等は記録して捕捉範囲外で検査する。

## 親の実測の一般化

[A-10] real — `/scr` の所要時間と予算内完了には、異なる処理・環境の測定を外挿している箇所がある。

根拠: `facts-offline-supply.md:35–36` の85秒は login→NFS の **`cp -a`**。job 内 hydrate CLI の測定ではない。`timeout 20` という設定値も、完了時間の観測ではない。`:38–41` の15.75秒は login→Lustre、`:55` の13秒は別 runner の warm-up である。

是正: brief P6 (`:67–69`) の「内側」「/scr 数秒〜十数秒」は見積りに降格する。plan `:92,259,316` が未実走・deadline 厳密保証なしと限定した点は妥当。1200秒の設定に余裕があることと、実経路がその予算内で完了することを分ける。

[A-11] real — network・過去受領証・先例の緑には、射影資料だけでは一次証拠を検算できない主張が残る。

対象は次のとおり。

- `facts:7–8`：9月9日の2ノードと DNS capability unavailable から、「計算ノードは外部 network 不在」全般は導けない。DNS 不可と全外向き通信不可も同義ではない。
- `facts:10–12,17–18`：9月17日の cache 生成物と status は、9月15日の受領証がその生成物を使った機序の直接証拠ではない。
- `facts:27–28`：9月10日の「header 無し・object 0」は当時の観測。今回の出力については9月17日の記録と現行 hydrate 検証を根拠にする。
- `facts:55`：13秒に対応する job・測定ログの識別がない。
- `facts:61–70`：コード経路の説明と「緑だった」という実測は別。9月7日の insight は現在の S/B 分離案の成功を証明しない。

是正: これらは虚偽と断定せず、「親報告・本相談では一次記録未検算」と区別する。特に network と時間の環境一般化を削る。hydrate の `reject_ignored=True` と prepare API の契約自体は、指定コードで裏づけられる。

## 規律 7

[A-12] refuted — 提示 plan に過去5受領証を無効化する処理はない。

根拠: `probe.py:2356–2420` の束縛は実行時の worktree と runtime hash を記録する処理で、過去受領証を再判定する reader ではない。`s2-plan-out.md:142–153` の二件追加は新実行の束縛対象拡張である。

過去受領証と新受領証の hash 集合が異なるのは当然で、旧集合に新しい二件がないことを「旧実行の不一致」と扱ってはいけない。比較時は各受領証の実行 commit と当時の束縛集合を使う。指定資料には consumer 全体も5受領証本文もないため、それらの互換性を検算済みとはしない。

[A-13] real — brief の「追加は S6 内だけ」と P4 の runtime 束縛拡張は、字義どおりには両立しない。

根拠: `s1-brief.md:34` は「追加は S6 観測内の新 key に限る」。しかし P4 (`:61–63`) は S6 外の `runtime_sha256` map に二件を加える。

是正: 「S6 観測二件に加え、既存 runtime 束縛 map の対象二件を拡張する。旧受領証への遡及要求はしない」と例外を明記する。コードの新機構は不要で、親 brief の整合修正で足りる。

## scope 判定

[A-14] refuted — plan の実装項目は既存機構への接続であり、新しい production gate・台帳の新設は見当たらない。

| 項目 | 判定 |
|---|---|
| P1：job 内 hydrate | 合流。既存 CLI の呼出し。 |
| P2：S の寿命・配置・ro-bind | 合流。既存一時 directory と sandbox bind の適用。 |
| P3：outside prepare 一回 | 合流。既存 helper の接続。S/B 分離は先例との差として明記が必要。 |
| P4：二件の束縛追加 | 合流。既存検査の対象拡張。A-13 の文言修正が必要。 |
| P5：観測追加・identity 採取先変更 | 合流。今回使用する入力の記録。使用直前までの pristine 保証にはしない。 |
| P6：残時間から timeout 算出 | 合流。既存 deadline/budget の適用。 |
| fixture・専用 assertion | 検証の追加。production gate の新設ではない。 |
| hydrate/prepare の失敗記録 | 既存 fail-closed 制御への接続。verdict は変更しない。 |

新設として実装案から外すべき項目は、提示 plan 内にはない。使用直前の hydrate 同等再検証や推移的 import 全体の束縛を追加提案するなら、それは別の裁定パッケージ候補であり、本実装に混ぜない。

[A-15] refuted — prepare 呼出しが現行 sink scanner に追加検出されないという説明は正しいが、安全性の証明にはならない。

根拠: `test_ccbench_spawn_sites.py:805` の検出は `.build/.build_v2` 等または `--build/--target` literal に依存し、`:598` では `buildcache.py` 自体を除外する。prepare 呼出しはこの構文検出に該当しない。

採用理由は「必要な依存準備を既存 helper で行う」に置くこと。「scanner が検出しないから被覆不要」を一般的な正しさの根拠にはしない。

## 総括

1. **[A-7]** hydrate rc 無視変異は JSON 解読失敗に遮られるため、killer を再照準する。
2. **[A-8]** 配置・bind・BASE_DIR 変異は、後段失敗より前に専用 assertion を発火させる。
3. **[A-4]** D2085 を二重検査一般の禁止へ広げた引用を修正する。
4. **[A-10]** NFS コピー時間・別 runner の時間から `/scr` の完了予算を保証しない。
5. **[A-13]** S6 内だけの追加制約に、runtime 束縛二件の拡張を明記する。

静的検査のみ。ファイル変更・テスト実走・PBS 操作は行っていない。