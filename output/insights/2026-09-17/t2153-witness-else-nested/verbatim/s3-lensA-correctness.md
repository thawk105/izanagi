## witness の健全性

以下、`G`＝`orchestrator/campaign/condition_meaning_gate.py`、`TG`＝`orchestrator/tests/test_condition_meaning_gate.py`、`S2`＝`orchestrator/campaign/s2_verify_calibration.py`、`T5`＝`orchestrator/tests/test_s5_permutation_coverage.py`。`brief`、`plan`、`liveness_*` は指定された射影資料を指す。すべて静的点検であり、テスト・compiler・変異は実行していない。

**所見**：「元の入れ子は評価に入らない」を TU 全体の前処理成功まで一般化することはできない。  
**分類**：real  
**根拠**：brief:12,34 に対し、G:2949 の置換は元の指令・本文を残し、G:3104 は所有 TU 全体の前処理失敗を `compile-time-branch-preprocess-failed` にする；NOREAD patch:17、HIGHKEY patch:22,30 の `#if ADD_ANALYSIS` も処理対象になる。  
**影響**：marker の条件が正しくても、未定義 `ADD_ANALYSIS` と `-Wundef -Werror`、本文の前処理エラー等で red になり、無条件の green 保証は成立しない。  
**推奨**：plan v2 と brief の P1-a を「前処理が成功する場合、元の入れ子は marker の選択条件に入らない」に限定する；plan:29 の留保を brief にも反映する。

**所見**：対象 hunk がコメント・行継続・無効な外側条件の内部にあるという疑いは、S2 の現行 pin では反証された。  
**分類**：refuted  
**根拠**：`external/ccbench@dff0f1e:cc/silo/transaction.cc:362` は関数開始、:363 の `#if ADD_ANALYSIS` は :365 で閉じ、:377 のコメントは :380 で閉じる；挿入直前の :386–387 は通常の `if (...) {`。TG:1401,1440 には行継続・コメント等を拒否する既存例がある。  
**影響**：現 patch の挿入位置による false-green／false-red は確認できない；外側 `#if 0` を追加した別入力なら完了 marker も消え、閉じ忘れなら前処理自体が失敗する。  
**推奨**：この疑いに対する機構変更は不要；現 pin の構造確認と任意入力への保証を区別して記録する。

**所見**：開始指令の一意性は patch 単独では保証できないが、現行 S2 経路については stock と適用規律まで根拠がある。  
**分類**：refuted  
**根拠**：NOREAD patch:9／HIGHKEY patch:8 は各一行を追加し、`git grep` で `dff0f1e` と現 HEAD `511c9538…` の stock TU に両名の出現はなかった；S2:133 は各 patch を別々に `applied` し、`patchharness.py:257` は適用前に `assert_pinned_clean` を要求する。  
**影響**：現行 S2 で計装 patch と broken patch の積み重ねによる同一指令二重化は確認できない；別の合成入力で二重化しても G:2934 の一意性検査で red になる。  
**推奨**：plan の stock 検算を最終記録に残す；TG:253 の helper は「追加行の一意性」であり「適用後 TU の一意性」の検査とは書かない。

**所見**：親の生死実験は関数・通常の `if`・HIGHKEY 要求側の入れ子を写しており、その欠落を理由に結果を否定することはできない。  
**分類**：refuted  
**根拠**：`liveness_a_type.py:35–43` に HIGHKEY 側の `if (...) { #if ADD_ANALYSIS ... }`、:54–59 に関数と外側 `if` がある；一方、実 patch:18–20 の key 復号や実 header 群は toy に置き換わっている。  
**影響**：通常の C++ 文脈を省いたため marker 結果が変わるという反例にはならないが、実 TU の依存 header・configure 成功を裏付ける実験ではない。  
**推奨**：実測名を「実 patch の前処理構造を模した toy TU」に統一する；実 patch 適用後 TU の実測と呼ばない。

## 主張の範囲

**所見**：witness green から positive control の異常発火を導くことはできないが、現 S2 にその読み替えによる後段の緩和はない。  
**分類**：refuted  
**根拠**：G:3282–3296 が検査するのは marker 数のみ；S2:409–419 は引き続き NOREAD／HIGHKEY の `non-serializable`、cycle 数、legacy の `certified` を用いて `gate3` と `all_pass` を決める。  
**影響**：abort 処理や key 閾値を誤って変更しても枝選択 witness 自体は green になり得るが、green だけで S2 の positive control 成功にはならない。  
**推奨**：最終成果物でも「枝選択確立」と「verifier の positive control 実走成功」を別の主張として残す；後段判定の変更は不要。

## 受理集合の向き

**所見**：registry 追加は supply の実行形も変えるため、meaning の三状態だけでは wave 全体の受理集合が狭まることを証明できない。  
**分類**：real  
**根拠**：G:1879–1888 は registry 会員で requested/control の build root を共有し、G:2500 は会員に限り同一 root を許容する；G:2589 は S2 の通常 supply 呼出しからこの経路へ入る。  
**影響**：新二件の supply record・configure 証拠も変わり、供給側を固定した `unestablished → green/red` の説明だけでは旧 red 入力が admit に転じないことを示せない。  
**推奨**：plan v2 の受理集合の説明を meaning 単独と family 全体に分け、予定済み供給回帰の確認対象として両 macro の共有 root 分岐を明記する；I4 は呼出し引数不変に限定する。

**所見**：共有 build root に残る CMake cache／生成物によって旧 supply red が green に変わる可能性は、今回の資料からは排除できない。  
**分類**：plausible  
**根拠**：G:1889–1897 は同じ root に要求値、対照値の順で configure し、その後 G:2505,2520 が両方を前処理する；別 root と同一 root では configure の状態が同一とは限らない。  
**影響**：configure が cache や生成 header に依存する入力では供給観測が変わり得る；ただし現 S2 pin で red→admit になる具体例は未確認。  
**推奨**：「全入力で狭まることを実証済み」とは記載せず、既存供給テストで確認した範囲を示す；未確認の可能性だけを理由に新機構は追加しない。

**所見**：対応集合の拡張だけで旧宣言型や未確立 record が自動的に green になる経路は見つからない。  
**分類**：refuted  
**根拠**：G:622,3402,4189 は旧型／旧 CLI cases を `MACRO` に固定し、G:3944–3984 は registry 束縛と観測を検証する；G:4103 は `supply_green and meaning_not_red`、:4107 は status が `unestablished` の record だけを一覧化する。  
**影響**：正当な新 green record の受理範囲は増えるが、対応集合への所属だけでは未確立一覧から消えず、meaning red も admit されない。  
**推奨**：旧経路の追加変更は不要；受理集合の懸念は上記 supply 分岐と分けて扱う。

**所見**：要求 0／既定 0、既定 None で factory が None を返す性質は維持されるが、それを供給評価全体の不変と同一視してはならない。  
**分類**：real  
**根拠**：G:967–969 は要求 `"1"`・既定 `"0"` を要求し、G:3335–3341 は宣言 None を未確立にする；一方、G:1879 の共有条件は factory の戻り値ではなく registry 会員性と非 inert 性を見る。  
**影響**：これらの meaning は未確立のままだが、非 inert な別値要求の supply 実行形まで不変とは限らない。  
**推奨**：plan の「挙動不変」は factory／meaning の状態に限定して書く。

## 変異 matrix の帰属

**所見**：registry 逐語変異と source_rel 変異の名指し node は静的には失敗を予測できるが、後者の失敗は factory 到達前である。  
**分類**：real  
**根拠**：TG:242 は registry の逐語ではなく `f"#if {macro}"` で toy を作るため逐語変異は G:2934 または TG:988 で検出される；`source_rel=include/backoff.hh` では TG:232 の `assert macro == "BACKOFF_NOINLINE"` が先に失敗する。  
**影響**：plan:182 の KILLED 自体は予測できても、それを factory の所有 TU 検査が働いた証拠にすると帰属が誤る。  
**推奨**：plan v2 の source_rel 行に「指定 node は fixture 前提違反で失敗、factory 拒否は別の静的導出」と記す；実測では traceback の失敗位置を残す。

**所見**：S2 配線変異の検出を文字列検査だけに帰属させるのは不十分だが、現 plan は実引数検査も予定している。  
**分類**：real  
**根拠**：T5:91 は `"declare_define_runtime_meaning(request)" in gate_source` だけなので、未使用呼出しやコメントを残して `declaration=None` にしても通る；plan:164–170 は evaluator の declaration と factory request を検査する別 consumer を要求している。  
**影響**：単純な文字列置換変異は source 検査でも落ちるが、実配線の証拠になるのは consumer 側の失敗である。  
**推奨**：plan v2 では配線変異の主 killer を新 consumer node と明示し、stub が `kwargs["declaration"]` を実際に検査した失敗を記録する。

**所見**：残る三変異は既存 node による検出であり、新しい二件の検出力として数えるべきではない。  
**分類**：real  
**根拠**：TG:1360 の重複例は `!=1 → <1` で最初の一箇所だけ計装され期待 red を失う；TG:1288 の非識別例は検査除去後も G:3295 で mismatch red となり reason が変わる；TG:1507–1518 の `[0-0]` は factory 条件緩和で宣言 None の期待を失う。  
**影響**：三件とも静的には KILLED 予測だが、非識別変異は誤受理防止ではなく reason 契約の検出であり、実行順による「先に殺した node」は未実測。  
**推奨**：既存被覆、新規被覆、reason 契約を別記する；指定された変異に静的な SURVIVED は見つからないが、KILLED 実績とは書かない。

## 親 brief 自身の点検

**所見**：(b)(c) の到達不能理由は支持されるが、親ログが四つの実 patch を直接実測したわけではない。  
**分類**：real  
**根拠**：`liveness_a_type.py:93–126` は NOREAD の重複 toy と二種類の MISATTR toy を実行し、`.out:9–11` がその red を記録する；MISATTR patch:6,8 には二段の外側条件、RUNG1 patch:9,31、REQUESTED_US patch:60,178、TRIGGER_GATING patch:41–193 には所有 TU の重複指令がある。  
**影響**：実 patch の四件について得た証拠は、toy 実測と実 patch の静的対応付けであり、「四件を実 compiler で確認済み」とすると実測範囲を超える。  
**推奨**：brief:18–19 と insight で実測／静的導出を分け、MISATTR の外側有効時 `(1,1)`、無効時 `(0,0)` を条件付きで記す。

**所見**：「変更配線先は S2」と「registry 追加の効果が S2 に限られる」は別であり、後者は CLI により反証される。  
**分類**：real  
**根拠**：G:4163 は供給 domain 全体を CLI の macro 候補にし、G:4196–4197 は cases 未指定時に factory を呼ぶ；S2:130–134,399–403 は現行の二 macro の具体的な campaign 呼出しである。  
**影響**：CLI から同じ二 macro を要求する入力にも自動的に witness が有効になる；旧 `--meaning-case` の BACKOFF_FIXED 限定は変わらない。  
**推奨**：plan v2 に CLI 自動追随を影響範囲として追記し、brief の「CLI 固定」は「旧 cases 経路固定」と書き直す；将来要求し得るだけの driver への追加配線は不要。

**所見**：brief の変更表には既存未登録テストの変更が漏れ、parametrize の行番号にも小さいずれがある。  
**分類**：real  
**根拠**：brief:48 は TG:1488 の NOREAD 未登録期待を列挙していない；TG:1195 が decorator、:1196 が関数であり、plan:131 は前者のテスト漏れを補正済み。  
**影響**：未登録期待をそのまま残すと baseline が失敗する；行番号のずれ自体は nit。  
**推奨**：brief のアンカー表へ TG:1488 を追加し、plan の修正を実装・記録に反映する。

## scope 外の層

**所見**：予定された S2 consumer の stub テストだけでは、実 admission の未確立一覧が二件減ったことは検証できない。  
**分類**：real  
**根拠**：brief:26 は「S2 の admission の未確立一覧が 2 件縮む」を完了条件にするが、plan:164 は meaning と family も stub 化する；実一覧の計算は G:4104–4108、実 JSON への格納は S2:363,424–425。  
**影響**：配線の正しさ、toy witness の green、実機 JSON の変化を一つの達成実績として報告すると過大主張になる。  
**推奨**：完了条件を「配線を単体検証、一覧縮小は実 family の規則から導出、実機 JSON 更新は未実施」に分けるか、既存テスト内で実 family の一覧も確認する。

**所見**：supply と meaning が同じ前処理 helper を使う事実だけでは、meaning 側の masstree `config.h` 欠落を否定できない。  
**分類**：plausible  
**根拠**：S2:105–110 は二 arm を別々に呼び、G:1868 と :3207 以降は別 temporary build を用いる；`external/ccbench@dff0f1e:cmake/ThirdParty.cmake:66–78` は `config.h` 生成を build custom command に置くが、G:1703–1720 は configure と compile database 取得のみ。  
**影響**：依存先が build ごとに展開されれば、別 build の供給成功は meaning 成功の証拠にならず、実機では前処理 red で S2 が停止し得る。  
**推奨**：plan の未検証事項として維持する；T-2650 の着地だけでこの S2 呼出しへの供給を保証せず、実機未走なら成功を報告しない。

## 裁定パッケージ候補

**所見**：共有 root の受理集合問題や実機 header 供給を解消するための新 gate・一般機構の追加は、本点検では正当化できない。  
**分類**：plausible  
**根拠**：確認できた実行形変更は G:1879 と :2500、実機依存の未確認点は G:1703 と S2:105–110 であり、今回 red→admit の具体的再現や実機失敗は得ていない。  
**影響**：未確認の可能性から機構変更へ進むと、本 wave の witness 追加を超える。  
**推奨**：候補は留保する；後段で具体的な失敗入力が確認された場合に、その入力・成果物影響・最小変更を裁定パッケージとして分離する。

## 総括

実 patch の位置と親の toy 実験から、二件の追加を妨げる枝選択上の反例は確認できなかった。ただし、**wave 全体で受理集合が狭まるという説明は、supply の共有 root 分岐変更を含める必要がある**。

plan v2 の修正点は、無条件 green の表現、CLI 自動追随、source_rel 変異の失敗帰属、toy・配線・実機 JSON の達成範囲の区別。baseline、KILLED、実機 S2 成功はいずれも本点検では未実測である。