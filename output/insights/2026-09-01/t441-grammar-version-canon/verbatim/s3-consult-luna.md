## 依頼の充足

**F-01 — 正準 materialization は accepted variant を畳むが、reject 台帳の重複を残す**

plan は選択肢 (c) を採り、13 段通過後に canonical source を材料化するため、accepted な `20` / `0x14` / `2e1` / `20.0` の `src_token`・variant ID・cache key は一致する。これは `s2-plan.md:29-42,65-70` と `p3_s4_loop.py:321-333,1252-1266` から成立する。

一方、`diffq_variant_id()` は引き続き raw implementation を hash し、plan も版を足すだけで raw を維持する (`s2-plan.md:72-75`; `p3_s4_loop.py:368-398`)。したがって、独立した構造違反を伴う `20` と `0x14` は別 `diffq-*` のまま残る。D901 は「別 token として台帳に残る」こと自体を問題にしている (`rulings-verbatim.md:32-39`)。reject を対象外にする裁定はない。

修正案は、受理判定や公開 reason を変えず、diffq hash の内部 pre-image だけで initializer literal を正準値へ置換すること。reject 台帳を対象外とするなら、その scope 縮小を再裁定する必要がある。

**成果物影響:** 同じ genome/value/rejection の試行が綴りだけで複数 variant として WAL・critic 入力に残り、試行台帳の重複が解消されない。  
**深刻度:** must-fix

## consumer の取り残し

**F-02 — `include/backoff.hh` の dirty path は文法 producer の識別子にならない**

plan は `include/backoff.hh` が tracked dirty なら grammar version を `src_token` に加える (`s2-plan.md:21-25,85-98`)。しかし同じ path は hole grammar を通らない既存 producer も変更する。

- `backoff_extended_sweep.py:54-64,193-225` は固定 patch を適用して `resolve_evidence()` と build cache を使う。
- `b10_backoff_shape_sweep.py:83-89,674-746,2480-2517,2910-2914` も同じ path を材料化し、`src_token`・variant ID・cache key を生成する。
- `source_digest.py:79-82` のコメントは p3 loop の「単一 marker」を説明するだけで、同 path の他 producer が存在しない証明ではない。

これらの campaign config には grammar version が入らないため、campaign identity は不変なのに variant/cache identity だけが変わる。明示的な p3 grammar provenance/version を source identity 解決へ渡す seam、または実際の grammar-controlled canonical hole を識別する条件が必要である。

**成果物影響:** B10／extended backoff の既存 campaign 内で variant ID と cache key が突然変わり、再開時の重複評価・cache miss・台帳混在が発生する。  
**深刻度:** must-fix

**F-03 — 正式 artifact admission が新しい WAL 版検査を迂回する**

plan は新 validator を replay・repair・recovery・`records_by_stage()`・duplicate readerへ接続するが (`s2-plan.md:118-124`)、正式な admission consumer を挙げていない。

`artifact_admission._inspect_campaign()` は WAL を直接読み、`wal._validate_attempt_topology()` を呼ぶ (`artifact_admission.py:1111-1177`)。ここが新 validator を呼ばなければ、versioned lock に対して `BUILD_START.backoff_grammar_version` が欠落・異値でも `require_admitted_campaign()` が view を発行できる (`artifact_admission.py:1251-1289`)。critic はその view をそのまま消費する (`critic/digest.py:688-698`)。

validator を `_validate_attempt_topology()` 内へ置いて全 caller を閉じるか、少なくとも artifact admission に明示接続する必要がある。

**成果物影響:** 版が欠落・食い違う WAL が certified acceptance と材料レポートへ入り、版束縛を持たない試行が正式材料として参照される。  
**深刻度:** must-fix

**F-04 — campaign ID pin 閉包の分類が不足している**

`default_cfg()` の変更で更新必須なのは、plan が挙げた `test_p3_s4_loop.py:2952-2974` だけではない。現在の B4 base ID literal も更新対象である (`test_p3_b4_closed_critic.py:3064-3072`)。

一方、次は更新してはいけない legacy 参照である。

- 既存 overlay artifact: `test_artifact_admission.py:84-88,188-190`
- legacy critic fixture: `test_critic.py:582-590`
- 既存 backoff sweep ID 群: `test_campaign.py:337-360,685-714`
- 既存 output path/hash: `s1_expected_goldens.py:253-258,315,370,437-443`

後二者は `p3_s4_loop.default_cfg()` ではなく既存 `backoff_config()`／historical output を固定しており、D942 の非遡及 (`rulings-verbatim.md:63-66`) により維持すべきである。plan は「更新する current pin」と「維持する historical pin」を明記すべきである。

**成果物影響:** B4 の current ID が古いままだと新 campaign の参照・材料化テストが失敗し、逆に legacy IDを更新すると既存 overlay/WAL への参照が失われる。  
**深刻度:** must-fix

参照閉包として、`backoff_hole_grammar` の直接 import は `p3_s4_loop.py`、`codex_roles/policy.py`、`critic/digest.py`、`test_p3_s4_loop.py` の4本である。policy は dormant raw admission (`policy.py:485-513`)、critic は固定 rule ID 集合の検査 (`digest.py:896`) なので、正準化 producer にしない判断自体は妥当である。identity/cache の再計算側では `ident.py:196-235`、`pipeline.py:121-127`、`buildcache.py:618-636,1289-1373` は token を opaque に扱えるが、F-03 の admission 経路だけは追加接続が必要である。

## 説明と実装の食い違い

**F-05 — campaign/WAL と source/cache が異なる版を束縛できる**

campaign identity は `cfg.search_config` の値を使う (`s2-plan.md:77-83`; `ident.py:196-235`)。WAL writer/reader は lock に記録された exact integer を使う (`s2-plan.md:108-124`)。対して source/cache は `source_digest` が import した実行中モジュールの `BACKOFF_GRAMMAR_VERSION` を使う (`s2-plan.md:85-98`)。

現行 `resolve_evidence()`／`resolve()` の API には cfg/lock version が渡らない (`source_digest.py:2195-2250`)。plan のテスト自身も config の version だけを変えて identity/layout を検査する (`s2-plan.md:163-165`) ため、たとえば lock が version 2、source/cache が定数 version 1という状態を拒否しない。

最小修正は、build/WAL 前に `cfg.search_config[key] == BACKOFF_GRAMMAR_VERSION` を exact に強制し、任意差し替え cfg を拒否すること。旧版 campaign の再開も必要なら、lock-declared version を source identity producer まで明示伝播する必要がある。

**成果物影響:** WAL は grammar 2 と記録しながら variant/cache key は grammar 1で生成でき、certified 選択・cache hit・試行台帳が同じ版を指さなくなる。  
**深刻度:** must-fix

## 変更単位と盛りすぎ

**F-06 — 条項2と3を同じ実装子へまとめる方針は裁定に反する**

brief は条項2・3を「同一変更単位」、段5実装子1本とする (`brief.md:12-15,83-87`)。しかし D942 は条項2・3を同じ変更単位へ含める案を明示的に却下し (`rulings-verbatim.md:70-72`)、D1034 も両者を「独立した設計」として追認している (`rulings-verbatim.md:78-85`)。

編集面も分割できる。

- 正準化単位: `backoff_hole_grammar.py`、`p3_s4_loop.quarantine()`、accepted/rejected spelling tests
- 版束縛単位: `default_cfg()`、source identity seam、WAL、cache/identity tests

T-441という同一 wave 内で直列 landしてよいが、少なくとも二つの論理 commit／実装段に分けるべきである。

**成果物影響:** 一方の不具合だけを切り戻せず、正準化による受理済み source変更と identity/WAL/cache変更が同時に certified 選択へ入る。  
**深刻度:** must-fix

新規 framework・互換 fallback・新台帳を足していない点は妥当である。WAL reader検査は版束縛を実効化するため必要で、盛りすぎには当たらない。

## テスト計画の実効性

**F-07 — 版導入前 cache の miss を殺すテストがない**

plan の cache test は「同じ版なら同じ、versionを1変えれば別、stockは不変」までである (`s2-plan.md:171-173`)。次の誤実装はすべて通る。

```text
version == 1: raw_digest をそのまま返す
version >= 2: version付き hashを返す
```

これは v1/v2差と stock不変を満たすが、版導入前の raw-digest cache keyを grammar v1 が再利用する。D901 条項2の初回 domain separationを満たさない。

legacy `cache_key()` (`buildcache.py:618-636`) と `_v2_identity()` (`buildcache.py:1289-1373`) の双方で、unbound raw token と bound-v1 tokenが異なること、旧 keyへの fallback lookupがないことを固定すべきである。

**成果物影響:** 版導入前に作られた非-stock binaryが grammar v1 campaignへ cache hitし、新文法で再評価されないまま certified 記録へ入る。  
**深刻度:** must-fix

**F-08 — versioned lockを後付けする既存 critic fixtureが新 validatorと矛盾する**

`_critic_view()` は record作成後に `L.default_cfg()` 由来 lockを書いている (`test_p3_s4_loop.py:159-166`)。この helper は多数の既存 reject/critic testから呼ばれる (`test_p3_s4_loop.py:1311,1450,1464,1501,2059` など)。default cfgが versionedになると、既に書かれた `BUILD_START` には version fieldがなく、新 validatorが正しく拒否する。

production-shaped testは lockを先に seedし、legacy testは version keyなし lockを明示するよう fixtureを分離する必要がある。後付け backfillで直してはいけない。

**成果物影響:** WAL→critic の受入テストが一斉に赤になるか、validatorを弱めて欠落版WALを通す圧力が生じ、正式参照の保証が落ちる。  
**深刻度:** should-fix

**F-09 — 既存 test file利用は妥当だが、import面を避ける条件がplanにない**

plan のテスト追加位置は概ね `test_p3_s4_loop.py:212` 以降で、T-1999 の 40-102 行と重ならない。既存 fileには BHG・source_digest・wal が既に import済み (`test_p3_s4_loop.py:37-51`) なので、新規 test fileやmeta test登録は不要である。

ただし cache testには現在未importの `buildcache` が必要である。top-level import群を編集するとT-1999面と重なるため、`test_p3_s4_loop.py:2041` 付近で local importする、とplanに固定すべきである。

**成果物影響:** import競合で cache key検査が欠落すると、版なし cache再利用を殺す受入防壁が落ちる。  
**深刻度:** should-fix

## 親 brief への所見

**F-10 — initializer-literal／statement-countをscopeから外した判断は妥当**

既存 validator は initializerを数値 token 1個へ限定し (`backoff_hole_grammar.py:690-705`)、statement数を1へ限定している (`backoff_hole_grammar.py:606-709`)。brief の実測行列 (`brief.md:28-45`) と一致し、残件をD901条項2・3へ組み替えた判断は正しい。

**成果物影響:** 既に狭められた受理集合を再変更せず、未実装の版束縛と表記重複だけを対象にできる。  
**深刻度:** nit（是正不要）

**F-11 — login node受入の指定は妥当**

plan の変更はPython producer/identity/WAL/cache wiringと静的・単体テストであり、性能測定や新しいC++実装を要求していない (`brief.md:79-81`; `s2-plan.md:133-177`)。`source_digest` の preprocess確認が必要でも性能測定ではない。計算ノード本走を受入条件へ足す根拠はない。

**成果物影響:** certified値や受理集合への影響はなく、受入はlogin node上の規定test runnerで完結できる。  
**深刻度:** nit（是正不要）

## 総括

最も重い欠陥は、`include/backoff.hh` のpath判定でgrammar versionを付けるため、非文法producerのvariant/cacheまで同一campaign内で変えてしまう点である。  
加えて、lock/WAL版とsource/cache版の単一性が保証されず、正式artifact admissionもWAL版検査を迂回できる。  
選択肢(c)によりaccepted表記の重複は畳めるが、raw `diffq_variant_id` はD901の台帳重複を残す。  
D942/D1034に照らし、正準化と版束縛はT-441内でも二つの論理変更単位へ分けるべきである。  
以上のmust-fixを解消するまで、このplanをそのまま通してはならない。