## 1. real: 歴史 decoder の通過を lock 全体の真正性と取り違えている

**成果物への影響:** 135 件の正規 recordを残したまま、campaign identity や authority を改変した偽造 lock で report を発行でき、受理集合と report の参照 identity が変わる。

根拠:

- プランが lock から検査するのは `workload`、path、binding、spec の4投影だけである。`s2-plan.md:14-29`
- `HistoricalSeriesIdentity` には authority commit を格納する一方、その値の exact 検証は計画されていない。`s2-plan.md:80`
- fixture も「relevant fields」だけを複製し、全 identity を固定しない。`s2-plan.md:112-121`
- `campaign_lock._validate_identity()` は `search_config` が dict であることしか検査せず、その内部は任意である。`orchestrator/campaign/campaign_lock.py:304-316`
- pre-T733 authority の検査も key grammar、正整数、hex 形式までで、記録 commit の実 blob との照合はない。`orchestrator/campaign/campaign_lock.py:382-424`
- これは「記録 commit blob との digest 照合を全24 pathで維持する」という D1653 の必須条件に届かない。`verbatim-D1653.md:20-27`

具体的な反例は、write-heavy の現物 lock を基に次のどちらかを行い、inner と outer を再 canonical 化するものになる。

- `search_tag` を `trial`、`trial` を `forged`、`ccbench_commit` を別値へ変更する。検査対象の4投影は一切変わらないため、計画どおりなら通る。
- authority の `contract_loader_commit` を `ffff...ffff`、24個の blob digest を全て `0000...0000` へ変更する。形式と exact-24 grammar は満たすため歴史 codec を通り、偽造 commit が report identity に入る。

いずれも現行コードでは、現物と同じ exact-24 grammar が `decode_campaign_lock()` の exact-63 gateで拒否されるため、プラン適用後に初めて受理される入力である。`orchestrator/campaign/campaign_lock.py:328-347`, `:508-528`

最小の直し方: 既存 `_assert_report_lock_binding()` の中で、4投影だけでなく系列別の完全な campaign identity を exact 比較し、authority は D1653 どおり記録 commit の24 blobを再照合する。通常 decoder の変更や汎用 gate の新設は不要である。

## 2. nit: cross-series の path 比較は恒真で、spec 比較も独立した保護になっていない

**成果物への影響:** この冗長述語を壊しても受理集合、判定値、report 参照は変わらない。

各系列で先に `preregistration_path == PREREG_REL` を要求した後、3系列の path を相互比較しているため、後者は決して発火しない。`s2-plan.md:26-29`

spec も各系列で canonical digest が同じ固定 literal `9c594114...` と一致することを先に要求する。したがって、その後の cross-series canonical JSON 比較は通常の SHA-256 前提では独立した mutation gateにならない。現物3本の spec は実際に同一だった。各 `campaign.lock:1`

最小の直し方: path の相互比較は削除する。spec の相互比較を残すなら防御 gateではなく診断用整合確認と記述し、変異保護件数へ数えない。

## 3. nit: binding 変異テストの一部は exact literal 比較へ帰属しない

**成果物への影響:** 実装の受理集合は変わらないが、変異 matrix が誤って「literal exact 比較を保護した」と報告しうる。

`test_report_lock_identity_rejects_recanonicalized_binding_drift` は「各key」を変異するとしている。`s2-plan.md:129-130`

しかし `spec_sha256` を変更または削除する変異は、module literal 比較を削除しても、直後の locked spec digest 比較または key access が先に赤にする。`s2-plan.md:27-28`  
同様に schema v4 検査を壊しても固定 spec digest が残る限り、通常の schema 変異は digest gateで赤になる。`s2-plan.md:35-37`

最小の直し方: literal 比較の帰属変異には、別 gateが消費しない `analysis_code_sha256` の変更または系列 binding の交換を使う。`spec_sha256` 変異は binding-spec 鎖の別テストとして扱う。

一方、次の変異候補は帰属が成立する。

- 歴史 decoder を通常 decoderへ戻す変異は exact-24 正例だけが直接赤になる。`s2-plan.md:151-152`
- live parserを reportへ戻す変異は fail stub 正例が直接赤になる。`s2-plan.md:157-158`
- record digest 比較の削除は、既存 content mutation が semantic gateで検査していない値まで変えるため検出できる。`orchestrator/tests/test_b10_backoff_shape_sweep.py:1898-1944`, `:2039-2054`, `:2273-2288`

## 4. refuted: binding の key 欠落、系列交換、record 改変は計画上は通らない

**成果物への影響:** 指定された反例では受理集合は広がらない。

- binding は系列別 module literal と dict 全体を比較するため、key 1個の欠落、追加、値変更を拒否する。`s2-plan.md:25-28`
- write-heavy、balanced、read-heavy の helper は分離されたままである。`s2-plan.md:86-92`
- workload も固定 dispatch と exact 比較するため、現物 lock の系列交換は workload と binding の両方で落ちる。`s2-plan.md:25`, `:87`
- spec 改変は outer lock を再 canonical 化しても、固定 `9c594114...` との canonical digest 比較で落ちる。`s2-plan.md:28`
- record 改変は自己 hashを再計算しても、系列別45件の digest literal 集合から外れる。`orchestrator/campaign/b10_backoff_shape_sweep.py:2876-2896`, `:2993-2997`, `:3096-3100`, `:3201-3205`

dict 比較が key 順序非依存である点も欠陥ではない。JSON object の順序は identity 値ではなく、lock codec が inner/outer の canonical bytesを別途要求している。`orchestrator/campaign/campaign_lock.py:597-605`

最小の直し方: なし。ただし所見1のとおり、比較していない campaign identity と authority の改変は別である。

## 5. 親 brief の実測

**B1は refuted as defect、実測を肯定。** 現在の blob は `cdd715c9e01050bea00f2b670e0d42d83f97a71f`、発効 commit の blob は `ea910de32df83c1bb320cbe62344dc5fb3b94684` だった。`load_preregistration()` は bytes 不一致を `prereg-blob` で拒否する。`orchestrator/campaign/b10_backoff_shape_sweep.py:1578-1586`

**B2は nit。** 「HEADなら現行 era identity で発行しうる」は decoder 障害を除いた条件付きデータフローとしては正しいが、現物3本では B3 が必ず後段で止めるため、実際の発行可能性へ一般化してはいけない。プラン自身はこの条件を正しく補っている。`s1-brief.md:14-19`, `s2-plan.md:5-8`

**B3は refuted as defect、現物で肯定。** 3本とも `campaign-lock/v2`、authority blob map は24 pathだった。通常 decoder は現行63 pathの exact集合を要求する。`orchestrator/campaign/campaign_lock.py:49-113`, `:328-347`  
歴史 decoder の pre-T733 tuple は現物の24 keyと一致する。`orchestrator/campaign/campaign_lock.py:118-143`, `:382-424`, `:568-612`  
これは現物 JSON とコードの静的照合であり、decoder や pytest の実走ではない。

**M3からM5は refuted as defect、実測を肯定。** helper は引数を無視して系列別 literal を返す。`orchestrator/campaign/b10_backoff_shape_sweep.py:2863-2873`, `:3001-3010`, `:3104-3113`  
現物3本は v4 spec 全体を持ち、write-heavy bindingだけに `analysis_commit` がある。3本の spec、path、block projection、means projectionも一致した。各 `campaign.lock:1`

**M6の前半は refuted as defect、現物で肯定。** 発効版 blob の machine spec は v4だが、現行 parser は v5 exactを要求するため拒否される。`77b33e37...:docs/b10-backoff-shape-preregistration.md:284`, `orchestrator/campaign/b10_backoff_shape_sweep.py:352`, `:1037-1056`

**M6の「lock が唯一の源」は nit。** Git blob自体は現在も読めるうえ、プランが新設する report専用 v4復元器は理論上その blobにも適用できる。唯一なのは技術的な sourceではなく、D1771 が裁定した authority である。`s1-brief.md:25-26`, `s2-plan.md:35-37`

最小の直し方: brief の B2を「lock gateを除いたデータフロー」、M6を「D1771上の唯一の採用 authority」と言い換える。

## 6. refuted: 凍結入力の書換えと WAL 所有範囲逸脱はない

**成果物への影響:** 既存 lock、block record、receipt の bytesと参照は変わらない。

プランはそれらを読み取るだけで、report writerだけを変更する。`s2-plan.md:87-97`  
既存 writerも `report_root.mkdir(..., exist_ok=False)` と `"x"` openなので既存 reportを上書きしない。`orchestrator/campaign/b10_backoff_shape_sweep.py:3692-3696`, `:3803-3805`

新規 report の bytesと格納先は、v2から推奨v3への schema変更、3 bindingの記録、root segment変更により意図的に変わる。これは凍結 report の改変ではなく、新規発行物である。`s2-plan.md:63`, `:96`, `:139-142`

WAL 読取側 `_verification_source_disclosure()` は `:3359-3438` のまま残し、プランは後続 `_verification_completeness()` の引数型だけを変更すると明記している。`s2-plan.md:93`, `orchestrator/campaign/b10_backoff_shape_sweep.py:3359-3515`

最小の直し方: 「既存 reportも上書きしない。v3は別 rootの新規成果物」とプランに1行明記するだけでよい。

## 総括

1. **real 所見は1件。** 最重は、歴史 codecを通した後に4投影しか比較せず、偽造 campaign identity と未検証 authorityを持つ exact-24 lockまで受理する点である。
2. **プランは現状のまま採ってはいけない。** `_assert_report_lock_binding()` を完全な系列 identity と D1653 authority検証へ閉じれば、残りの設計は採用可能である。
3. 親が段4で裁定すべき論点は、第一に「4投影だけでよいか、系列別の完全な lock identityと24 blob authorityまで exact に束縛するか」であり、後者を推奨する。第二に、予定どおり provenanceをv3へ上げて「共通spec、3系列binding、現在の analyzer」を分離するかを確定すべきである。

pytest、decoder実行、file編集は行っていない。現物確認は read-only の JSON、Git blob、コードの静的照合だけである。