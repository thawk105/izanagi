## 所見

### [severity: must-fix] job-local base の変更だけで正当な cache hit が必ず postflight 拒否される

攻撃シナリオ: job A が base A と内容 receipt R で sort binary を完成 cache へ保存する。job B は `mkdtemp()` により別の base B を得るが、内容が同じなので receipt は同じ R になる。V4 に従い base path は preimage に入らないため同じ digest を hit する一方、cache entry は A の source root hash を返す。postflight は B の root hashを期待するため `effective-root-mismatch` となる。内容が同じでも job が変わるだけで拒否される。

[根拠 orchestrator/campaign/buildcache.py:826] preimage は内容 receipt のみ、[根拠 orchestrator/campaign/buildcache.py:1071] cache hit は過去の absolute source root hash を返す、[根拠 orchestrator/campaign/buildcache.py:1559] hit 経路がそれを現在の base と組み合わせる、[根拠 orchestrator/campaign/s8b_floor_campaign.py:2049] 現在の base path hash と完全一致させる。追加テストも同一 base でしか hit させておらず、この経路を隠している。[根拠 orchestrator/tests/test_buildcache_v2.py:293]

提案: fresh build では実効 root を現在の base と照合する一方、cache hit は absolute root の再一致を要求せず、completion に束縛された内容 receipt を権威にする。base A で fresh、同内容の base B で hit して通る正例を追加する。F82・F161 の `[受理集合の過剰縮小]`、F89 の経路間受理集合不一致の再発である。

**成果物影響:** 2 回目以降の production run で正当な `sort_best` binary が `UNAVAILABLE` となり、certified 選択の `sort_best` 受理集合が空へ縮む。

### [severity: must-fix] postflight 拒否より先に未検証 binary を完成 cache へ publish している

攻撃シナリオ: receipt R を取得後、cell build 中に `config.h` または archive が R′へ変化し、binary が R′を使う。`build_v2` は内容を再照合せず completion を publish する。その後 campaign postflight は drift を検出して停止するが、完成 cache entry は残る。内容を R に戻して同じ entry を hit すると、cache validator は pre-build receipt と root hashしか見ず、binary が R′で作られた事実を検出できない。現状は前所見の過剰拒否が production の再利用を mask するが、それを正しく直すと顕在化する。F126 の「後段安全弁による mask」の型である。

[根拠 orchestrator/campaign/buildcache.py:1631] build 後に取得するのは root path hashだけ、[根拠 orchestrator/campaign/buildcache.py:1663] completion は post-build HEAD/config/archive を再照合せず作られる、[根拠 orchestrator/campaign/buildcache.py:1691] cache publish が完了する、[根拠 orchestrator/campaign/s8b_floor_campaign.py:2497] 内容 drift 検査は `build_v2` が返った後である。

提案: completion publish 前に buildcache 内で HEAD・`config.h`・archive を再取得して入力 receipt と比較するか、buildcache を二相 publish にして campaign postflight 成功後だけ完成 entry を公開する。drift→拒否→内容復元→再呼出しで、拒否済み binary が hit されない統合テストを置く。

**成果物影響:** mask を外した後、異なる masstree 内容で作られた binary に admission receipt が発行され、certified 選択とレポートの binary 参照が誤った依存 identity を指しうる。

### [severity: must-fix] FetchContent private field の受理集合が非 sort cell にも拡張されている

攻撃シナリオ: stock 等の runtime record に `_fetchcontent_base_dir` と base define を追加すると、store と portable projection の exact-key gateが受理する。実際、新規通しテストは `configuration_id="configuration"` の generic recordへ同 field を加え、正常通過させている。producer の `build_cells` が現在は sort のみに付与していても、V7 の consumer gate は非 sort 汚染を拒否しない。

[根拠 orchestrator/campaign/s8b_floor_campaign.py:2709] projection は configuration を見ず両 key 集合を受理、[根拠 orchestrator/campaign/s8b_floor_campaign.py:3392] store gate も同様、[根拠 orchestrator/campaign/s8b_floor_campaign.py:3443] field 検証に sort 限定がない、[根拠 orchestrator/tests/test_s8b_floor_campaign.py:6418] generic configuration fixture、[根拠 orchestrator/tests/test_s8b_floor_campaign.py:6430] その fixture が FetchContent field 付きで通る。

提案: `_fetchcontent_base_dir` の存在を `configuration_id == "sort_best"` と同値にし、store と projection の双方で強制する。stock record に field を加える負例と、sort record の正例を分離する。F157 の項目別照合漏れと F255 の consumer 追随漏れの型である。

**成果物影響:** 非 sort cell のレポートに無許可の `${FETCHCONTENT_BASE_DIR}` provenance が入り、裁定が不変とした非 sort の受理集合と binary 参照説明が変わる。

## 判定

**NO-GO** — repeat run の正当な cache hit を拒否し、同時に postflight 不合格 entry を publishする cache lifecycle 欠陥と、非 sort consumer の scope 拡張が残っている。

## 総括

- 差分は裁定 §2.1 の 7 ファイルだけで、`FETCHCONTENT_FULLY_DISCONNECTED` と T-1129 は未実装だった。
- V1〜V3、V6、V8 の主要経路は裁定どおり確認できた。
- V4 の既定値は条件付き key 追加で、`pipeline.py` 等の既定 preimage・argv はコード上不変だった。
- V4/V5 の cache hit と postflight の組合せに、過剰拒否と publish 順序の 2 欠陥がある。
- V7 は producer では sort 限定だが、store/project consumer の受理集合が非 sort に広がっている。
- 禁止 1 は SOURCE_DIR token、禁止 2 は実効 root、禁止 3 は HEAD/config/archive drift で具体的に発火可能だった。
- base-only の正例、同じ base の正例、`st_dev`/`st_ino` だけ変えて内容を保つ正例はいずれも実在する。
- 既存テストの skip・xfail 追加、fixture への現行 code hash 差し込み、禁止された主張は認めなかった。
- pytest は実行しておらず、緑とは判定していない。