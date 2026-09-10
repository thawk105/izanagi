## 受理集合の検査

## F-01 — 判定後の正準化なら受理集合は動かない

現行は raw candidate を structural → host-effect → 13段文法の順で判定し、文法 accept は最終行でのみ成立する (`orchestrator/campaign/p3_s4_loop.py:288-328`, `orchestrator/campaign/backoff_hole_grammar.py:576-709`)。plan は accept 確定後にだけ再 materialize する (`s2-plan.md:65-70`) ため、記述どおりなら新規受理・過剰拒否はない。

**成果物影響:** certified 選択の受理集合と固定 rejection は不変で、accepted source bytes だけが収束する。  
**深刻度:** nit（修正不要の適合確認）。

## F-02 — grammar-only reject を使わない spy は前段に隠される

plan が spy の注入先として挙げる `test_p3_s4_loop.py:4630-4686` は HOLE_ESCAPE／HOST_EFFECT のみで、backoff grammar まで到達しない。直接 validator を呼ぶ corpus (`:454-489,618-767`) も `quarantine()` の配線順を証明しない。`double now_backoff = 20; (void)0;` は既存 composed path で grammar の `statement-count` に到達する (`orchestrator/tests/test_p3_s4_loop.py:735-746`) ため、これを実効注入点にすべきである。

**成果物影響:** 放置すると canonicalization を grammar 判定前へ移す変異が生き残り、現在拒否される追加文が受理され得る。  
**深刻度:** must-fix。

## 正準化の経路

## F-03 — brief の P2 は D901 の重複除去を達成しない

brief は「台帳の数値 token だけ」を正準化し、source は書き換えないとしている (`brief.md:69-70`)。しかし raw source は `quarantine()` がそのまま書き (`orchestrator/campaign/p3_s4_loop.py:288-333`)、source bytes が digest (`orchestrator/campaign/source_digest.py:1977-2003`) と cache key (`orchestrator/campaign/buildcache.py:631-634`) を分裂させる。これは D901 の「certified 選択の母集合を汚す重複を除く」という理由 (`rulings-verbatim.md:33-39`) と両立しない。plan の受理後 materialization (`s2-plan.md:29-44`) は技術的には正しいが、親 P2 を覆す裁定が未了である (`s2-plan.md:195-198`)。

**成果物影響:** P2 のままでは同値な `20`／`0x14`／`2e1` が別 variant・cache・試行台帳として残り、certified 母集合が重複する。  
**深刻度:** must-fix。

## F-04 — value・raw literal・正準形の三者は整数 production 域では一致する

production は正準化より前に `coder.value` の整数値域と raw literal の数値一致を検査する (`orchestrator/campaign/p3_s4_loop.py:966-1008,1011-1029,1192-1210`)。plan が同じ `_cpp_number_value()` と `str(int(value))` を使う限り、`1..1000` では `coder.value == raw value == canonical value` が保たれる (`s2-plan.md:57-63`)。

ただしテスト計画は attribution、quarantine、source/cache を分割しており、`value=20`＋raw `0x14`＋canonical source `20`＋`BACKOFF_FIXED=20` を一続きに固定していない。

**成果物影響:** 配線ミス時には genome の値と実際の binary source がずれ、試行台帳と性能帰属が汚染される。  
**深刻度:** should-fix。

## 帰属と identity

## F-05 — campaign/WAL と source/cache が別の版 producer を読む

campaign と reject identity は module 定数を使う計画 (`s2-plan.md:72-81`) なのに、WAL は lock 宣言値を使う (`:108-116`)。さらに `source_digest.resolve()`／`resolve_evidence()` は cfg・lock・version を引数に持たない (`orchestrator/campaign/source_digest.py:2195-2250`)。`run_one_iteration()` にも cfg の版が現行定数と一致する gate はない (`orchestrator/campaign/p3_s4_loop.py:1190-1266`)。

したがって lock/cfg が版 N、実行コード定数が版 M の場合、campaign/WAL は N、`diffq_variant_id` と cache/src token は M になり得る。

**成果物影響:** 同じ campaign identity の下に別文法版の source/cache identity が入り、「同じ identity なら同じ意味」が壊れる。  
**深刻度:** must-fix。

## F-06 — `include/backoff.hh` の dirty 判定は campaign 帰属ではない

plan は「backoff campaign だけ」を保証するとしながら、実装述語は `tracked_paths` に `include/backoff.hh` があるかだけである (`s2-plan.md:21-25,85-99`)。`source_digest` 自身は同 path を複数の汎用 EVOLVE source の一つとして扱い (`orchestrator/campaign/source_digest.py:79-95`)、resolver は campaign cfg を受け取らない。

plan 自身もこの代用の妥当性を未決としている (`s2-plan.md:197-200`)。版 key を持たない別 campaign が同 path を変更した場合にも token が version-bound になる構造で、P1 の campaign 限定を証明できない。

**成果物影響:** 非対象 campaign の variant/cache key が予告なく動くか、逆に対象 campaign の明示的帰属を検査できない。  
**深刻度:** must-fix。

## F-07 — 固定 ID は「再導出 4件」と「歴史記録」に分かれる

| 固定値 | 分類 | 根拠 | 扱い |
|---|---|---|---|
| `2cd75697`, `9f43a5b8` | 現行 `default_cfg()` 再導出 | `orchestrator/tests/test_p3_s4_loop.py:2952-2967` | 版導入で更新してよい |
| `ad0444da`, `8700ee8e` | B4-marked `default_cfg()` 再導出 | `orchestrator/campaign/p3_b4_closed_critic.py:1984-1991,2025-2032`; `orchestrator/tests/test_p3_b4_closed_critic.py:3064-3112` | 版導入で更新してよい。plan が脱落 |
| `0b53a387` と `LEDGER_RAW_SHA256` | 過去 campaign／overlay ledger | `orchestrator/tests/test_artifact_admission.py:81-89,188-189,814-824`; `orchestrator/tests/test_critic.py:582-590` | 更新禁止 |
| `backoff-sweep-*` の campaign ID | 別 driver の現行／歴史 pre-image | `orchestrator/campaign/backoff_sweep.py:100-120`; `orchestrator/tests/test_campaign.py:661-716` | p3版導入では不変 |
| `s1_expected_goldens.py` の3 path＋3 SHA | 過去 campaign bytes | `orchestrator/tests/s1_expected_goldens.py:253-258,315-320,370-375,437-440` | 更新禁止 |

plan は通常 on/off の2件だけを挙げ (`s2-plan.md:167-169`)、B4 の2件を落としている。歴史値を動かさず現行4件だけを更新することは D942 と両立する。

**成果物影響:** B4 golden が赤になる一方、機械的な一括更新をすると過去台帳・overlay ledger・参照 SHA を遡及改変する危険がある。  
**深刻度:** must-fix。

## F-08 — identity の双方向性は F-05/F-06 解消後なら成立する

同値 literal は canonical source に収束し、異なる値は `BACKOFF_FIXED` と canonical source の双方で分離される (`s2-plan.md:33-44`)。異なる raw sourceも raw digestを版 pre-imageに残す計画で分離される (`:85-92`)。stock は cache tokenを維持しても campaign ID側に版が入るため、full identity は分離される (`:21-25,77-83`)。

**成果物影響:** F-05/F-06 を直せば、同義候補の重複を除きつつ意味差・文法版差を identity に反映できる。  
**深刻度:** should-fix（F-05/F-06 に従属）。

## 恒真な保証と拒否射影

## F-09 — raw digest 保持を殺す変異に対応テストがない

plan は raw digestを pre-imageへ残すと保証する (`s2-plan.md:85-92`) が、テスト計画は「同じ digest は同じ」「version変更で変わる」だけである (`:171-173`)。異なる raw digest A/B が同じ版でも異なる token になる検査がないため、`source=<raw_digest>` を落とす変異 (`:189`) が生き残る。

実効注入点は `_bind_backoff_grammar_version(digest_a, ("include/backoff.hh",)) != ...digest_b...` の helper-level 検査である。

**成果物影響:** 異なる source が同一 cache keyへ aliasし、別 binary の結果を certified 候補へ誤帰属し得る。  
**深刻度:** must-fix。

## F-10 — WAL 欠落検査は恒真ではなく実効性がある

versioned lockに対する欠落／異値レコードを手作りして validator と duplicate readerへ入れる計画 (`s2-plan.md:155-157,175-177`) は、正常 writer の自己 oracleに閉じない。lockに版がない場合の即 returnも歴史 WAL を遡及拒否しない (`:118-124`)。

**成果物影響:** versioned WAL の版欠落は拒否され、既存 WAL bytes と歴史参照は維持される。  
**深刻度:** nit（修正不要の適合確認）。

## F-11 — 新しい拒否射影に candidate bytes の漏出はない

rejection は固定 rule/reason/stage のみを投影する (`orchestrator/campaign/backoff_hole_grammar.py:76-145`; `orchestrator/campaign/p3_s4_loop.py:336-363`)。plan の raw implementation は hash pre-image内だけ、WAL追加値は固定整数版だけである (`s2-plan.md:72-75,108-116`)。accepted source の canonical valueは拒否経路には出ない。

`quarantine()` が rejected raw `edited_text` を戻す既存 API (`orchestrator/campaign/p3_s4_loop.py:288-333`) は残るが、plan が新設する漏出ではない。

**成果物影響:** rejection rule/reason、材料レポート、WALに literal・正準値・統計が新規露出することはない。  
**深刻度:** nit（修正不要の適合確認）。

## 親 brief への所見

## F-12 — validator 実測だけでは「台帳に別 token が残る」まで証明しない

brief の実測は `validate_backoff_implementation()` の結果だけである (`brief.md:28-42`)。それだけで証明できるのは grammar acceptance までで、production は別途 value/literal 一致を要求する (`orchestrator/campaign/p3_s4_loop.py:966-1029`)。matched `coder.value=20` なら実際に通ることは既存テストが補強している (`orchestrator/tests/test_p3_s4_loop.py:332-352`) が、brief の「実測から」の一般化は一段広い。

**成果物影響:** scope 結論は変わらないが、実測証拠と静的制御流の区別が監査記録で曖昧になる。  
**深刻度:** nit。

## F-13 — T-1999 との test file 重複検査が不足している

brief は T-1999 が `test_p3_s4_loop.py` に未commit差分を持つと認識しているが、hunk位置を示していない (`brief.md:91-99`)。plan は同ファイルの `:129-138` を含む多数箇所を編集する (`s2-plan.md:135-177`)。production側の2領域を避けるだけでは test file の衝突を排除できない。

**成果物影響:** merge時に version/WAL/受理順テストの片方が落ち、certified 選択の防壁が未検査になる。  
**深刻度:** must-fix。

## F-14 — FROZEN_MANIFEST 根拠は「直接破壊」にだけ十分

`FROZEN_MANIFEST` に backoff campaign記録がないこと (`orchestrator/tests/test_frozen_artifacts.py:29-70`) は、plan のコード／テスト編集がその23件を直接書き換えない根拠としては十分である。しかし `s1_expected_goldens.py` や overlay ledger の歴史 pin は別の保護面であり、brief の記述 (`brief.md:61-63`) だけでは全 pin 閉包を覆わない。

**成果物影響:** 凍結23件は守れても、過去 campaign path・WAL SHA・overlay ledger参照を誤更新する余地が残る。  
**深刻度:** should-fix。

## F-15 — `test_campaign.py:337-360` の backoff ID は16件ではなく15件

該当範囲は5集合×3 workloadで15 literalである (`orchestrator/tests/test_campaign.py:337-360`)。分類は F-07 のとおりで、結論には影響しない。

**成果物影響:** 成果物値は変わらず、pin inventory の件数表記だけが不正確。  
**深刻度:** nit。

## 変異候補の帰属

## F-16 — 変異 matrix は3候補を補強する必要がある

`s2-plan.md:181-193` の候補を制御流に照らした結果は次のとおり。

| 変異 | 現計画の帰属 | 必要な注入点 |
|---|---|---|
| 定数だけ定義し `default_cfg` 未配線 | 実効 | exact key＋campaign ID検査 |
| campaign IDだけ変更し source/cache未束縛 | 実効だが版 skew未検査 | cfg/lock版とmodule版を意図的にずらす |
| WAL field欠落／wrong stage | 実効 | versioned writer E2E |
| writerのみ、reader欠落許容 | 実効 | handcrafted missing field＋replay/duplicate |
| helperのみで quarantine未配線 | 実効 | returned/written canonical bytes |
| WALだけ正準化し raw source維持 | 実効 | canonical file bytes＋source token |
| raw digestを版 pre-imageから削除 | **隠れる** | 異なる2 digestをhelperへ直接注入 |
| path条件を削除し全非-stockへ版付与 | 条件付き実効 | non-backoff tracked pathを明示注入 |
| STOCKにも版付与 | 実効 | exact `STOCK` token/cache golden |
| rule IDをgrammar版に連動 | 既存固定 rule corpusで実効 | 既存期待値を維持 |
| canonicalizationを13段前へ移動 | **前段rejectに隠れる** | grammar-only `statement-count` 候補を使用 |

**成果物影響:** 隠れた3系統を放置すると、受理集合の緩和、異ソースcache alias、campaign/WAL/cacheの版不整合を検出できない。  
**深刻度:** must-fix。

## 総括

- 最重所見は F-05 で、cfg/lock版と source/cache が別 producerを読むため、版束縛が一貫した identity 契約になっていない。
- F-03 の source materialization 方針は D901 の目的には必要だが、親 P2 を覆す裁定を得てから実装すべきである。
- 現行4件の再導出 goldenだけを更新し、`0b53a387`、backoff-sweep、s1 SHA、overlay ledgerは動かしてはならない。
- F-02、F-09、F-13、F-16 のテスト／重複検査不足も land 前に解消が必要である。
- したがって、このプランは現状のまま通してはならない。