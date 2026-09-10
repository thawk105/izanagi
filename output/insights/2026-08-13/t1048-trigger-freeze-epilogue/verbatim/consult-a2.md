### 所見 1 — `axis_trigger_gating.py` は凍結閉包の外ではない

- 主張: brief の「`FROZEN_MANIFEST` に対象 path がないので pin 閉包の再発行不要」は誤り。直接 key ではないだけで、3 系統の凍結成果物から source SHA で間接 pin されている。
- 根拠: plan は `axis_trigger_gating.py` への定数追加を指定する（`plan.md:7-21`）。一方 `known_axes_freeze.json` は同 path の SHA を記録し（`output/s1-freeze/known_axes_freeze.json:46-48`）、`measurement_freeze.json:41-43` と `holdout_freeze.json:224-226` にも同じ pin がある。`verify_document` は現行 file bytes を再計算して不一致を拒否する（`orchestrator/campaign/s1_known_axes_freeze.py:845-857`）。現行 SHA も既に記録値 `47507d9b…` ではなく `72371560…` だった。
- 影響: 正当な S-1 freeze consumer が build admission より前に `source sha256 不一致` で止まる。T-1048 がさらに同 file を変更すると、この既存不整合を見えなくしたまま「過剰拒否なし」と記録することになる。
- 推奨: **must-fix**。`axis_trigger_gating.py` を編集する案を一旦外し、epilogue 定数を admission 側の未 pin 面へ置く案と、既存 source-pin 不整合の裁定パッケージを分離する。凍結 JSON の再発行は本 wave で既成事実化しない。

### 所見 2 — P1 の「hole が必ず上書き」は到達可能性を仮定している

- 主張: hole は構文上無条件代入でも、実行されるとは限らない。BEGIN 前を自由にしたままでは P1 の一般化は成立しない。
- 根拠: 宣言と BEGIN の間は `patches/silo-backoff-trigger-gating-variant.patch:84-86`。ここへ `return;` を挿入しても、BEGIN..END と epilogue は逐語一致したままで、新 gate は受理する。現行検査も BEGIN より前を読まない（`orchestrator/campaign/build_admission.py:169-199`）。plan 自身も凍結対象を END 以後に限定する（`plan.md:48-55`, `plan.md:219`）。
- 影響: report は mask M を主張するが、hole も gated call も実行されず backoff が消える。quarantine 経由では外部改変として拒否されるが、review/generator evidence を直接束縛する gateway 経路では単独では拒否されない。
- 推奨: **scope 外**。P1 を「BEGIN 前の再代入は、hole に到達した場合に限り上書きされる」へ狭め、制御流変更を残存限界へ追加する。これを閉じるための C++ 制御流解析を本 wave に混ぜない。

### 所見 3 — P4 の `#endif` は C++ の `if` を構文的に閉じない

- 主張: `#endif\n` まで逐語一致しても、その直後の `else` は epilogue 内の `if` に結合できる。したがって「`#endif` までで R2 が閉じる」は偽。
- 根拠: epilogue は `if (...) { ... }` の直後に preprocessing directive で閉じるだけである（`patches/silo-backoff-trigger-gating-variant.patch:107-111`）。次をその直後へ置くと、gate-on の preprocessing 後には正当な `if ... else` になる。

```cpp
#if BACKOFF_TRIGGER_GATING
else {
  Backoff::backoff(FLAGS_clocks_per_us);
}
#endif
```

plan は正しい E より後をほぼ任意として受理する（`plan.md:101-104`, `plan.md:222`）。この追加は E の完全重複でもないため、新しい重複検査にも掛からない。

- 影響: `izanagi_gate_pass == false` でも else 枝が backoff し、実バイナリは全要因 backoff に戻る。brief が挙げる成果物偽装そのものが残る（`brief.md:68-70`）。
- 推奨: **must-fix（封鎖実装は scope 外）**。P4 の根拠を撤回し、dangling-else 型を残存限界へ明記する。後続空行を凍結しても空白は else を遮断しない。真に閉じるには skeleton に構文的 terminator を追加するなど patch migration が必要で、patch 不変条件と衝突するため裁定へ返す。

### 所見 4 — fresh build の外に admission 非通過層が残る

- 主張: 新 gate は fresh build gateway には効くが、全成果物層を閉じない。
- 根拠: repository inventory は手動 CMake build 6 file のうち admitted を `s8a_trigger_coverage.py` だけとし、broken coverage・rung1・T152 を明示的 non-admissible とする（`orchestrator/tests/test_p3_build_authority_cli.py:144-161`）。さらに S8b resume は `store_path` の存在と binary SHA だけを再検証し、admission receipt を要求しない（`orchestrator/campaign/s8b_floor_campaign.py:2220-2239`）。receipt replay も live source 検査を行わない方針である（`plan.md:210-212`）。
- 影響: fresh S8b floor/oracle と S-1 build は守られるが、既存 portable binary の resume、任意 executable、non-admissible materializer には新 gate の保証が伝播しない。
- 推奨: **scope 外**。S8b binary と admission receipt の束縛を既知 RP-4 として裁定パッケージに残す。直接 materializer closure も別件とし、本 wave で実装したふりをしない。

### 所見 5 — 現行の正当な materialized producer には byte 過剰拒否を再現しなかった

- 主張: freeze 間接 pin を除けば、調べた現行 producer は新しい E を逐語で保つ。CRLF・末尾空白・行継続を作る実 producer は見つからなかった。
- 根拠:
  - S8a characterization は skeleton を適用後、tally と misattr を重ねる（`orchestrator/campaign/s8a_trigger_coverage.py:255-268`）。両 patch の hunk は abort 冒頭または lock-conflict store で、END/E に触れない（`patches/instr-silo-backoff-trigger-gating-tally.patch:5-35`, `patches/broken-silo-trigger-misattr.patch:5-24`）。
  - S-1 extime は skeleton 適用後に quarantine で hole だけを書き換え、derive/buildcache へ渡す（`orchestrator/campaign/s1_verify_extime_calibration.py:340-364`）。
  - S8b floor と oracle は同じ `prepare_cell` を使う（`orchestrator/campaign/s1_direct_comparison.py:530-640`, `orchestrator/campaign/s8b_floor_campaign.py:1354-1377`, `orchestrator/campaign/s8b_oracle_driver.py:1437-1495`）。
  - `quarantine` は canonical emitter に正規化し、hole 置換後の全文を書くだけである（`orchestrator/campaign/p3_s4_loop.py:193-275`）。emitter は単一行代入だけを返す（`orchestrator/campaign/reflux_ir.py:131-141`）。
  - `s6_canary_rename` は marker と両 skeleton token を rename し、追加コメント行も除去する（`orchestrator/campaign/s6_canary_rename.py:46-62`, `:93-117`）。現行三分岐では意図どおり axis 不在側へ落ちる。
  - stock submodule と唯一の `orchestrator/tests/fixtures/**/cc/silo/transaction.cc` は marker/token とも 0 hit だった。
  - 32 golden は全件 `izanagi_gate_pass = ...;` の代入形だった（`orchestrator/tests/reflux_ir_expected_goldens.py:25-56`）。
- 影響: plan の fixture 更新 2 file と、32 mask・pristine の正例方針は妥当。実 producer由来の CRLF 偽拒否は確認できない。
- 推奨: **nit**。正例を「32 mask・pristine・E 後の既存空行/ADD_ANALYSIS」に固定する。CRLF/CR は引き続き意図的負例とし、実 producer の仕様とは書かない。

### 所見 6 — 独立変異として数えられない検査がある

- 主張: BEGIN/END の順序 arm は後段 frame 比較と冗長である。また deleted/modified/gap は別 gate ではなく、同じ E slice 不一致分岐の入力違いにすぎない。
- 根拠: 現行の順序拒否後、block は frozen block または prefix/hole/suffix と一致しなければ拒否される（`orchestrator/campaign/build_admission.py:185-199`）。順序条件だけを削除しても reversed input は後段で拒否される。T-897 自身も M4-prime をこの理由で変異対象から除外済み（`output/insights/2026-08-13_t897-trigger-admission/README.md:78-84`）。新 plan の deleted/modified/gap はすべて `raw[start:end] != E` 一つで拒否される（`plan.md:48-50`）。
- 影響: これらを個別 mutation kill と数えると、検出力を水増しする。原因が別 gate へ退化した負例も緑に見える。
- 推奨: **must-fix**。順序 arm を独立変異へ登録しない。deleted/modified/gap は一つの gate に対する複数入力として集計する。derive と require の二重呼出しは時間差再検査なので冗長扱いしない。

### 所見 7 — 直結完全重複の拒否は採るべき

- 主張: 親の疑いは理解できるが、`END + E + E` の拒否は残すべきである。ただし tail integrity の保証には数えない。
- 根拠: 最初の E slice 比較だけでは `E + E` を受理する。二本目は gate-pass 時の backoff を確実に二重実行し、同じ axis の正当な実装とはいえない。現行 producer はいずれも E を一本だけ生成し、後続は空行と `ADD_ANALYSIS` である（`patches/silo-backoff-trigger-gating-variant.patch:107-114`）。一方、空白違い・別表記・dangling else はこの検査で拒否されない。
- 影響: concrete な既知不正形への純増検出力はあるが、「E より後も保護した」という一般保証は得られない。
- 推奨: **nit（採用）**。検査と単独負例を残し、記録では「直結した exact duplicate 一形だけの sanity guard」と明記する。post-E 全体の凍結、出現回数唯一性、C++ 意味論の保証とは表現しない。

P1〜P5 の結論は、P1 refuted、P2 採用、P3 現行 producer に限り採用、P4 の空行非凍結自体は妥当だが「R2 が閉じる」という根拠は refuted、P5 採用である。

## 総括

- 最重要は、`axis_trigger_gating.py` が凍結 JSON から間接 pin され、現行 SHA も既に記録値と不一致な点である。
- plan の「FROZEN_MANIFEST に直接ないので再発行不要」は pin 閉包の一般化として成立しない。
- exact epilogue は END 直後の再代入を止めるが、BEGIN 前の `return` と post-E の dangling `else` を受理する。
- 特に dangling `else` は mask と実バイナリを再び乖離させるため、「R2 を閉じた」とは記録できない。
- 現行の S8a、S-1、S8b fresh materializer、overlay patch、stock fixture には byte 過剰拒否を確認しなかった。
- S8b resume と non-admissible materializer は依然 scope 外であり、別裁定として残す必要がある。
- 直結 E 重複拒否は採用してよいが、tail 全体の保証ではなく一つの既知不正形への限定防壁である。
