## 所見

- **S1｜must-fix｜P7｜棚卸しの適用単位。** `git apply --check` は driver の素の `git apply` と同じ文脈照合を使うが、44 本すべてを単独で clean checkout に当てると、骨格 patch の上に重ねる計装・変異を誤って「不適用」と数える。policy 系には重ね順が明記されている。放置すると棚卸し表と作り直しの裁定が変わる。**推奨:** 各 patch の前提と順序を表に固定し、F と修正 tip の両方で同じ前提を当てた後に `git apply --check` と実適用を照合する。根拠: `patches/README.md:767-776,800-801`、`orchestrator/campaign/patchharness.py:204-211`。

- **S2｜must-fix｜P7｜「当たる」の意味。** V27 の現行 patch はマクロ無効側に旧コード `if (searchWriteSet...) goto` を埋め込む。修正 tip に hunk が仮に当たっても、無効時に修正を取り消す形になりうる。V26 も旧探索順を前提にした hunk であり、修正後は「修正された読みを旧値へ戻す」変異として再定義が要る。放置すると変異の検出結果と「既定 OFF は inert」という一次資料の主張が変わる。**推奨:** 44 本について適用可否に加え、マクロ無効の結果が修正 tip と一致するか、マクロ有効時に意図した差だけを作るかを diff で点検し、V26・V27 の再生成を起票する。根拠: `patches/broken-silo-repeat-update-buffer.patch:46-63`、`patches/broken-silo-stale-read-own-write.patch:42-59`、`patches/README.md:813-825`。

- **S3｜should｜P1｜修正の API 境界。** 提案どおりの `update` は既存要素の `op_` を見ずに `body_` を置き換える。INSERT 要素は `body_` を持たず、DELETE 要素に値を入れても `writePhase` は削除する。さらに `scan` は依然として読み集合を優先する。一方、通常の UPDATE 要素では既存の `rcdptr_` と書き込み集合を維持するため、施錠・読集合再確認・`max_rset_`／`max_wset_` の経路を新たに迂回する変更ではない。放置すると修正 commit を「全 API の取引内値を修復」と説明した場合、実際の値の意味と食い違う。**推奨:** 依頼どおり二か所の変更に留め、INSERT／DELETE／scan と組合せた操作は未修正の限界として一次資料と上流説明に明記する。根拠: `F-silo-transaction.cc:70-75,109,117-137,211-219,304-315,453-478,533-553,673-737`、`gen-opt-gate-liveness/README.md:149-155`。

- **S4｜should｜P3｜D297 の二つの結果の名称。** F→修正 tip は `--expect-paths cc/silo/transaction.cc` を通過してから、最初の TRACE=0 正規化出力不一致で rc=1 となる見込みである。header が差分に無いので、header 用四引数を渡しても header 判定には入らない。P′→P″ は、P′の親を pin とし、P″を P′の子で修正 tip と同じ tree にすれば祖先条件を満たす。ただしその差分は C→F と同様に header `include/trace.hh` を含むため、四引数、依存物、gitlink 照合まで必要で、`--expect-paths` を指定するなら Silo 一ファイルにはできない。放置すると D297 の意図した拒否を CI 失敗と誤読し、合成比較の pass も誤った範囲の保証として後続 wave に渡る。**推奨:** (a) を「値変更の期待拒否」、(b) を「pin＋同じ修正から F の付随変更を比較する補助証拠」として別々に記録し、後続の gitlink 前進では実際の旧新 tip に必要な判定を改めて定義する。根拠: `tools/check_trace0_preprocess_identity.py:217-237,599-603,679-721,1074-1135,1157-1189`、`t2854-ccbench-format-ci/README.md:14-18`、`s1-brief.md:14`。

- **S5｜should｜P4・P5｜事前登録と判定不能。** U0 の一秒走では F の D2b が両 workload とも赤だったが、同じ件数の再現は保証されない。照合器は D2b (i) の自分の書き後の読み、(ii) の書きがゼロなら `not-exercised` と返す。起動器の旧 `prereg` は修正側の `not-exercised` を許すため、そのままでは brief の合格条件より緩い。放置すると発生条件ゼロの走行を修正成功または対照成功と誤認する。**推奨:** 両 workload・両 D2b 条項の発生条件を結果に保存し、ゼロなら合格・不合格でなく判定不能とする。根拠: `gate_check.py:161-206`、`launch_gate_liveness.py:120-129`、`gen-opt-gate-liveness/README.md:100-110`。

- **S6｜should｜P4・P5｜計装の F 向け再配置。** F の writePhase は TPC-C の v3 枝と YCSB の通常 C/R/W 枝を分ける。YCSB では `tpcc_tx_type()==0` 側の txid を `last_commit_txid` に渡し、UPDATE の `memcpy` 直前に最新 `body_` の先頭八 byte を V に出せば、二度目の `update` で置換された刻印を読める。RMW の刻印は `val_` コピー後、`update` に渡す器の `id_` に置く必要がある。放置すると Q/V と C…E/W の対応、D2b の読みが変わる。**推奨:** 作り直した計装について `#if TRACE` 除去後の bytes 照合と、Q 対 C…E・V 対 W の全件一対一を実走の受入条件にする。判定器の `--ccbench-root` には、その binary を build した計装済み checkout を渡す。根拠: `F-silo-transaction.cc:605-642,673-701`、`instr-silo-gate-witness.patch:69-113,119-147`、`gate_check.py:106-139`、`orchestrator/verifier/model.py:119-125,192-200`。

- **S7｜should｜P6｜先例 script の固定値。** F の format 緑は 213 file・clang-format 14.0.0／14.0.6 の先例であり、修正 tip 自体の合格ではない。CI build script は親を C2′ に固定し、D297 script も旧 OID を pin、親を C2′、差分三ファイルに固定している。放置すると修正 tip の build・D297 が入力検査で止まり、F の結果を tip の結果と取り違える。**推奨:** 新しい bundle の head＝修正 SHA、親＝F を検査する job script を作り、format は修正 tip の clean checkout で全 213 file を再実行して F を対照として記録する。根拠: `run_ci_build.sh:4-9,34-41`、`run_judge.sh:5-18,52-79`、`t2854-ccbench-format-ci/README.md:14-18`、`s1-brief.md:17`。

- **S8｜should｜P1・成果物｜F が変わった場合と引継ぎ。** brief は F を固定しているが、依頼は F が無い・変わった場合に `[T-2854]` の実際の前進先 tip を採り、根拠を書くよう指定する。また一次資料には上流へ送る短い英語説明文、spool fragment には後続 gitlink 前進 wave の branch 名・SHA・棚卸し結果の所在が必要である。放置すると修正 commit の土台、push 依頼、後続 wave の起票が古い F に結び付く。**推奨:** 着手時と最終化前に `[T-2854]` の前進先を確認し、採用した親 OIDと分岐理由、上流説明文、後続 wave の依存条件を成果物に明記する。根拠: `md_1.txt:24-37,51`、`s1-brief.md:5,12,20`。

## brief で正しいと確認した点

- **P2:** `#line 635/658/679/700` は F が C2′と揃えた TRACE=0 の論理行番号を後続区間で保つ。修正の三行追加により、`#line 635` より前の論理行番号は三つ進むが、各マーカー以降は元の値へ戻る。`ERR` の 106 と 690 は維持される見込みである。四つの値を一律に +3 すると後続の `__LINE__` を動かすため、**値を変えない**裁定が妥当。master では F の配置を前提にできず、cherry-pick 後の行番号と CI を別に確認する。根拠: `F-silo-transaction.cc:106,666,698,728,740,752`、`t2854-ccbench-format-ci/README.md:15,39-42`、`master-probe.log:5-8`。
- **P3:** 合成比較は依頼の手順 3 を超える追加作業だが、C→F の pass と組み合わせて、修正以外の TRACE=0 変化を分離して示す材料になる。約千秒の追加費用を含めても brief の概算は二 node 時間の線内である。根拠: `s1-brief.md:14,22`、`t2854-ccbench-format-ci/README.md:18,52-60`。
- **P4・P6:** F の赤と修正 tip のゼロを別 build で取り直すこと、format を差分行だけでなく全体で測ること、push と gitlink 前進をこの wave で行わないことは依頼に沿う。根拠: `md_1.txt:26-33,48-50`、`s1-brief.md:15-19`。

## 総括

計画の中核は妥当。実施前に最も直すべき点は、44 本を一律に単独適用で数えないことと、適用可否に加えて変異の無効時・有効時の意味を検査すること。修正 commit は指定された二か所に保ち、未修正の API 境界と D297 の期待拒否を明記すれば、CI・trace 実測・棚卸しの結果を後続 wave に誤解なく渡せる。