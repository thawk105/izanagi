## 固定 seed の policy=2 は pre-state と交換可能ではない

深刻度: blocker

根拠: `plan-v2.md:187-212` は全 run で同じ seed と系列 `0111001000100110` を使い、`plan-v2.md:555-559` も長期統計品質と複数 instance の同一 seed を未検査とする。例えば勾配 0、commit parity は常に偶数、step=1、初期 `Backoff_=100` なら、`cicada-adaptive-dynamic.patch:315-347` により推奨差分は常に −1 となり、上記割当から pre-state は `100,99,100,101,102,101,100,101,100,99,98,99,98,97,98,99` と推移する。割当は更新番号の決定関数であり、全 run の同じ更新番号で同じ処置となる。さらに更新番号は throughput と負荷が決め、勾配 0 時の推奨方向は commit parity が決めるため、高負荷の K 発火、低負荷の cap 発火、偶奇 overshoot、起動過渡と固定 bit 列が系統的に重なり得る。更新番号で厳密に層別すると一方の処置しかなく positivity が消え、粗い時間層では残余交絡が残る。救えるのは、run ごとに独立に無作為抽出して事前固定した複数 seed を使い、各主要層で両割当が現れ、現在までの履歴と次の bit の独立性を設計として保証した場合だけである。

成果物影響: 現設計の policy=2 は「同じ pre-state で逆の一歩」の因果対照ではなく、固定時系列に沿った観察比較しか生成しない。

## directional success の層別は反実仮想効果を推定していない

深刻度: blocker

根拠: 現行推定器は action の符号と次窓 throughput 差の符号が一致した件数だけを数える (`t2187_adaptive_const_probe.py:843-865`)。v2 もこれを割当別に分けるだけである (`plan-v2.md:252-260`)。具体的に推奨差分が +1、真の局所応答が `+1 -> throughput +c`、`−1 -> throughput −c` なら、forward も inverted も action と outcome の符号が一致して成功率 1 になるが、二つの潜在 outcome の差は `2c` で最大である。逆に無効果で対称ノイズなら両方 0.5 になる。必要な主推定量は、割当についての ITT、例えば pre-state 層内の `log(T_next/T_current)` の `assigned_forward − assigned_invert` 平均差であり、成功率の差ではない。

成果物影響: 大きな反実仮想差を「差なし」と判定できるため、次 wave の中心命題が推定量に接続していない。

## inversion_realized と action 0 の除外は処置後選択になる

深刻度: blocker

根拠: `inversion_realized=1` は定義上 `assigned_invert=1` を含む (`plan-v2.md:164-172,224-238`) ため、この層には forward 対照が一件も入らない。下限 0、step=1 では、推奨 −1 のとき forward は clamp で action 0 として除外され、invert は +1 で realized になる。一方、推奨 +1 なら forward は +1 で残り、invert は clamp で action 0、realized 0 となる。推奨符号と境界状態は outcome と関係するので、`plan-v2.md:260` の action 0 除外も同じ偏りを加える。偏らない条件は、採否が割当前の履歴だけで決まり、両潜在割当に同じ確率で適用され、各層に両割当が存在することだが、現定義は構造的に満たさない。主解析は clamp を含む全割当の ITT とし、必要なら割当前に両方向が clamp されない `both_actions_feasible` を計算して副解析するべきである。

成果物影響: 境界で都合のよい inverted 更新だけが残り、推定対象集団と効果の向きが処置によって変わる。

## 「差なし」を支持へ変える等価設計と検出力が存在しない

深刻度: blocker

根拠: 旧事前登録の ±3% は旧 7 腕の run-level throughput 比用である (`dynamic-backoff-preregistration.md:91-104`)。新しい更新単位 ITT の等価域ではない。診断は exact 1 job であり (`dynamic-backoff-preregistration.md:132-144`)、過去実績も n=1、CI なしだった (`output/insights/2026-09-05_dynamic-backoff-mechanism/README.md:141-144`)。数百更新を独立反復として数えることは、時系列依存と carryover のため不可である。結果を見る前に、少なくとも次を新規事前登録で固定する必要がある。

- 数値の等価域とその実用根拠。旧 ±3% を使うなら更新単位 outcome へ移せる理由。
- 主推定量、CI または TOST、alpha、多重性、集約方向。
- workload、threads、推奨符号、割当前の境界可否、時間 block の層。
- warm-up、末尾 event、overflow、timeout、再投入の除外規則。処置後の clamp、action 0、outcome を見た除外は禁止。
- 独立 seed/run 数、run を cluster とする分散、自己相関を含む有効標本数、目標 power。
- seed 一覧、停止規則、p0/p1 の役割、探索解析と確認解析の境界。

成果物影響: 現状で得られる「非有意」は低検出力または系列依存と区別できず、機序の支持にはならない。

## 診断 build の throughput は限定された機序 outcome としてのみ使用できる

深刻度: must-fix

根拠: 絶対規律 1 は性能 build から診断計装を除去する契約であり (`brief-v2.md:20,29`)、診断 build 内で throughput 由来の応答を計算すること自体は禁止していない。driver も `headline_eligible=False`、`throughput_scope=diagnostic_only` を付ける (`t2187_adaptive_const_probe.py:3002-3015,3165-3174`)。ただし比を取っても性能値である性質は消えない。許される境界は、同じ policy=2 診断 build 内の割当 ITT だけを「計装された系の機序指標」として示し、絶対 TPS、trace-off との性能比較、腕の順位、production build への外挿を行わないこと。計装量が更新頻度と相互作用し得るため、この限定は必須である。

成果物影響: 境界を明記しないと、診断系の処置差が trace-off 性能の証拠へ昇格して絶対規律 1 の射程を越える。

## policy=1 は逆方策の総効果だけを答え、D1515 の直接確認にはならない

深刻度: must-fix

根拠: policy=1 対 policy=0 が厳密に推定するのは「各腕自身が到達した履歴で、毎回の clamp 前推奨差分を反転する制御方策へ置換したときの run 全体 throughput 差」である。初回から状態分布、境界滞在、後続勾配、刻み、更新時刻が分岐するため、一歩の効果ではない。brief 自身もこれを認める (`brief-v2.md:35-44,79-81`)。D1515 は非単調性の機序の直接確認を要求する (`decisions.md:47160-47177`) が、policy=1 単独では満たさない。policy=2 も上記三 blocker のままでは補完にならない。足す案は一つ、新規事前登録した複数独立 seed の sequential randomized trial とし、割当前 eligibility 上の ITT を主解析にして、同じ exact policy=2 腕の正しさ認証も結果解釈の前提にすることである。

成果物影響: policy=1/2 を実装しただけ、または現推定器で走らせただけでは D1515 の再訪条件を充足した成果物として受理できない。

## Backoff 境界は維持されるが「exact literal 追加は緩和でない」は集合論的に誤りである

深刻度: must-fix

根拠: policy の反転後にも既存 clamp が必ず実行されてから `Backoff_.store` されるため (`cicada-adaptive-dynamic.patch:349-358`、`plan-v2.md:129-173`)、静的には永続化された `Backoff_` が下限または固定・動的上限を越える新経路は見つからない。policy 0 は前処理で落ち、trace 項目も `BACKOFF_TRACE` 内なので、既存二つの serializability certification cell の受理集合も現行 `_certification_contract` のまま変わらない (`t2187_adaptive_const_probe.py:986-1000`)。一方、現行 trace gate は一 literal だけを受理する (`t2187_adaptive_const_probe.py:2495-2515`) のに、計画は二本目を OR する (`plan-v2.md:292-314`)。`gate-input-measurement.md:8-9` 自身が「受理形を増やす」と正しく述べ、同文書 `:43-48` と brief `:32` の「受理域を緩めない」と矛盾する。12 field と trace v2 の追加も診断入力言語の制御された拡張であって、非拡張ではない。規律 2 が correctness gate に限定されるなら違反ではないが、「非緩和」とは呼べない。別の明示 submode に分けるか、診断 gate の承認済み拡張として記録すべきである。

成果物影響: 現表現のままでは受理集合拡大を非拡大として検査し、規律 2 の監査結果を誤表示する。

## patch B の凍結と 12 field 到達不能は正しいが、新反実仮想は未登録である

深刻度: must-fix

根拠: patch B は実際に「本書を含む commit で凍結」と記載され (`dynamic-backoff-preregistration.md:82`)、現物 SHA-256 `f3fe6b7e...` は insight の束縛値 (`README.md:199`) と一致した。12 field の到達不能も `parse_cells` が 5/11 field 以外を拒否するため正しい (`t2187_adaptive_const_probe.py:313-325`)。反証された事実主張は exact literal の非拡張性だけである。ただし旧事前登録の腕は 7 cell、診断は旧 3 腕だけ (`dynamic-backoff-preregistration.md:42-59,132-144`) で、C、policy=1/2、seed、ITT、等価域を凍結していない。計画は事前登録を編集しない (`plan-v2.md:553-564,588`) のに、新 artifact は旧文書の `prereg_sha256` を記録する (`t2187_adaptive_const_probe.py:68,3024`)。これは旧事前登録が新試験を覆うように見せる。

成果物影響: 新しい counterfactual artifact が未登録実験なのに旧 preregistration へ束縛されたような provenance になる。

## 「実測なし」と診断経路の実装は両立するが、現 wave は問いへ回答したと書けない

深刻度: must-fix

根拠: brief は成果を patch、driver、test までとし実測を明示的に scope 外にする (`brief-v2.md:12-16`)。したがって policy=2 の診断走行経路を実装することとは両立する。しかし `brief-v2.md:77-83` と `plan-v2.md:599-607` の「答える」は、現 wave では「次 wave の適切に事前登録された試験を可能にする」に弱める必要がある。また plotting consumer を A+B+C 固定へ無条件変更する計画 (`plan-v2.md:444-450`) は、既存 A+B artifact (`README.md:197-203`) の再生成を拒否し得るため、schema または stack identity ごとの versioned 受理が必要である。

成果物影響: 放置すると未測定の実装成果が機序回答として受理され、同時に既存 A+B 証拠の再現経路を壊す。

## 総括

blocker あり。最重は、固定 seed の policy=2 に交換可能性がなく、既存 directional success が処置効果を推定せず、`inversion_realized` が処置後選択になる三重の不成立である。  
policy=1 は総方策効果に限られ、現 policy=2 と合わせても D1515 の直接確認にはならない。  
patch B の凍結と 12 field 到達不能は裏取りできたが、「二本目の exact literal は緩和でない」は誤りである。  
本 wave は実装 capability までなら scope 内だが、新規事前登録と複数独立 seed の ITT 試験なしに機序結論を受理してはならない。