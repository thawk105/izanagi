## 所見 (real 候補)

**現 plan は「非再帰な digest と実 TU の不一致」を調べる設計としては有効ですが、「製品経路で許された variant が stock の certified 結果・cache・receipt を継承した」という完了判定には不足します。特に、現行 admission と coder 検疫が反証になります。** 以下は静的所見であり、変異の到達を実測済みとは扱いません。

**A-1 — token 衝突から cache 継承への推論は、現行コードと合わない。**

- **根拠 (file:line):** `source_digest.py:249–259` の receipt は `tracked_diff_sha256`・`tracked_clean`・root を含む。`build_admission.py:674–701` は stock admission に **token が stock、tracked-clean、現行 pin** の全条件を要求し、`:703–715` で source 全体を admission の hash に束縛する。`buildcache.py:638–641` の legacy key にも admission hash が入り、v2 は `:1319–1337` で admission と任意の source snapshot を含む。
- **real と主張する理由:** 今回の carrier 変異は tracked diff を変える。同一 root・genome・token でも admission の source が異なるため、正規に導出した cache key は原則異なる。stock receipt の使い回しも `build_admission.py:745–746` で拒否される。単なる未観測ではなく、親 brief の「直結」に対する具体的反証である。
- **是正案 (scope 内):** reference/current の `resolve_evidence()`、receipt、admission の比較を既存関数による観測として記録する。cache 継承は実際の key と `cached=True`、返却 binary hash を観測した場合に限る。**scope 外:** admission を迂回・変更して到達を作ること。

**A-2 — M3a を「許された coder variant」と呼べない。carrier が編集権限の境界を変えている。**

- **根拠 (file:line):** `p3_s4_loop.py:697–708,758–760,789–795` は coder implementation に構造検疫・effect 検査・backoff grammar を適用する。`diff_quarantine.py:492–497` は hole 内の生指令を `HOLE_ESCAPE` として拒否する。実 build 経路も `p3_s4_loop.py:1903–1906` で検疫する。top-level 挿入は `diff_quarantine.py:477–488` の領域外検査に当たる。
- **real と主張する理由:** M3a の `#undef`／`#define` を coder payload として渡せば既存検疫が止める。ところが変異 template を先に `applied()` すると、それらは検疫の比較基準となる骨格側へ移る。`resolve()` の受理は、この trust boundary の差を埋めない。M3b/M6 も正規の hole 編集面外である。
- **是正案 (scope 内):** 「変異 template を信頼して適用した後、identity gate が受理した」と記す。coder 由来の到達と template 由来の到達を分ける。**scope 外:** 検疫・grammar の緩和。

**A-3 — M6 の diff-of-diffs 通過と、perf binary の採用は別問題。**

- **根拠 (file:line):** `source_digest.py:1662,2166–2167,2196–2200` は include を除去した file 単独比較。一方、`buildcache.py:3495–3499` は cache hit でも TRACE diff と symbol 検査を行い、`:3754–3756,3782–3786` は `izanagi_trace` symbol を拒否する。実 trace header は `external/ccbench/include/trace.hh:25,35,105–110` に namespace 内の thread-local 状態を持つ。
- **real と主張する理由:** M6 が単独 file の比較を抜ける仮説には根拠がある。しかし実 TU に現れる `izanagi_trace` の状態・呼出しは、非 strip binary の symbol 検査が捕捉する対象そのもの。少なくとも「後段に止める層がない」とは言えない。最終 symbol 残存・link 成否は未実測。
- **是正案 (scope 内):** 「TRACE diff 検査通過」「実 TU への TRACE 展開」「compile/link」「最終 nm 判定」を別々に記録する。後二者を観測しない場合は「採用された perf build への混入」と書かない。

## 模擬と実の差 (F29)

**A-4 — probe が省略する製品側の分岐を、到達先ごとに明示する必要がある。**

**根拠 (file:line) と突き合わせ:**

| 境界 | 製品経路 | plan の probe と差 |
|---|---|---|
| 適用 | `patchharness.py:247–263`：pin・clean・apply・復元 | 同じ関数。適用機構は実物 |
| identity | `loop.py:634`、`pipeline.py:1805`：`resolve_evidence()` | plan は `resolve()`。tracked diff／runtime snapshot の採取がない |
| terminal skip | `loop.py:695–706`：variant ID が `done` にあれば skip | 呼ばない。admission より前の分岐 |
| build admission | `pipeline.py:1840–1857` | 呼ばない。dirty な stock-token source は無条件に stock 扱いされない |
| source pin | `pipeline.py:1987–1991`：指定時に canonical source 検査 | 呼ばない。通常の clean 要求は `:1137–1142` |
| A1 pin | `paper_story_a1_source.py:25–28,45–52,58–66`：patch hash と materialization の束縛 | 変異 patch はこの契約と一致しない。`applied()` に hash 検査がないことは A1 通過を意味しない |
| build 出口 | `buildcache.py:3645–3666`：full evidence 再照合、その後 TRACE 検査 | TRACE diff は別途観測予定。full evidence 再照合・binary 検査は対象外 |
| verification | `pipeline.py:614–624`、`verifier/core.py:226–234` | verifier・receipt 発行を呼ばない |

**real と主張する理由:** 省略した各層の役割が異なる。

- `_recheck_source_evidence` は **resolve 後の変化**を止める。最初から変異した木を解決し、そのまま維持すれば、それだけでは変異を拒否しない。
- `proof_source_snapshot` は一般的な再帰前処理検査ではない。`verifier/model.py:119–177,192–200` は CMake の compiled source を字句正規化して採取し、`:238–240` は条件評価・動的到達を保証しないと明記する。backoff header の macro 漏れをこれだけで封じたとは言えない。
- hooks は payload 検査を削除済みで、意味的逸脱は auditor／人間領域である（`hooks/README.md:164–167`）。一方、A-2 の coder 検疫は実際の機械拒否であり、両者を混同してはいけない。
- local clone が共有 checkout guard の対象外なのは妥当（`patchharness.py:315–323`）。ただし同 commit が保証するのは source の出発点であり、root を含む receipt や製品全経路の同一性ではない。
- masstree `config.h` は source cache 内を読む（`ThirdParty.cmake:58,85`）。生成は build custom command（`:66–78`）なので、既存生成物を使う probe と、必要なら再生成する build の同等性には条件が付く。

**是正案 (scope 内):** insight にこの経路表と「通過／拒否／未観測」を残す。使用した compiler・dependency・`config.h` の bytes と argv を固定した観測として報告する。新しい gate や恒久台帳は不要。

## 消費側の継承の実体

**A-5 — 継承候補は「skip キー」「cache binary」「verification receipt」で強さが違う。**

- **根拠 (file:line):** `pipeline.py:137–143` と `source_digest.py:111–116` は stock token の suffix を省き、**同じ genome** の variant ID を維持する。`loop.py:695–706` はその ID で terminal skip する。cache は A-1 の admission を追加する。verification は `pipeline.py:614–624` で実 verifier を呼び、`verifier/core.py:226–234` で source・admission・variant・snapshot を照合する。
- **real と主張する理由:** loop の skip は admission より前なので、後段の cache 分離では守れない候補である。ただし `done` は certified 成功だけとは限らず、skip 分岐自体は新しい certified 結果や receipt を発行しない。`result_evidence_context` がある場合は再発行拒否にもなる（`loop.py:697–702`）。また stock token は「全 stock genome と同じ ID」ではない。
- **是正案 (scope 内):** 継承を実測したと書くための追加観測を分ける。

| 主張 | 必要な観測 |
|---|---|
| stock と同じ skip キーになった | 同一 genome の ID 一致 |
| 既存 stock terminal により実際に skip された | 元 terminal の種類・ID と、実 loop の skip 結果 |
| stock cache binary を再利用した | admission、cache key、`cached=True`、binary hash |
| certified 結果・receipt が変異側へ帰属した | 元の certified 証拠と、それを変異側として消費・帰属させた実 downstream 結果 |

M3a は同一 genome・異なる payload の非 stock token 衝突候補であり、stock 継承例ではない。コメント・空白などの意図した同値化との差は、**同じ実条件で意味に関わる差が残るか**にある。`sleepTics(1)` の追加は有力な source-level の反証だが、任意の TU bytes 差だけで runtime の別挙動まで確定してはいけない。

## 主張の限定 (書いてよい / 書いてはいけない)

**A-6 — N2 の差と正例の赤は、原因まで確認して初めて証拠になる。**

- **根拠 (file:line):** `s2-plan-out.md:324–331` は独立採取・非空・位置差分類を要求する。`condition_meaning_gate.py:2076–2109` は compile argv を前処理 argv に変換するが、compile/link は実行しない。D1490 も所有 TU の枝選択を動的到達と分ける（`docs/decisions.md:46520–46526`）。
- **real と主張する理由:** 同一 root でも挿入による `__LINE__` 差は残る。M1 の N2 赤が位置差や configure エラーだけなら、意味差を拾う検出力の証拠にならない。M2 は resolve 拒否の対照なので、N2 の比較処理自体を検証しない。M0 は CMake コメント編集であり、C++ の行位置変化への対照ではない。
- **是正案 (scope 内):** 各赤に rc・例外段階・raw diff を結び付け、M1 では追加演算、M3 では `sleepTics(1)`、M6 では trace 展開という対応差を確認する。出力共有 helper でも reference/current の実行記録を別に残す。plan の「object 比較は should」は維持できるが、未実施なら主張も source-level に留める。

| 書いてよい文〔該当観測が得られた場合〕 | 書いてはいけない文 |
|---|---|
| 「変異 template 適用木を `resolve()` が受理し、同じ token を返した」 | 「製品経路が許可した coder variant である」 |
| 「同一 genome の reference/current で、digest は一致し、実 TU に `sleepTics(1)` の追加があった」 | 「実 workload の結果が変化した」 |
| 「stock genome と同じ variant ID になった」 | 「stock の certified 結果を継承した」 |
| 「TRACE diff gate は通過した」 | 「perf binary の symbol 検査まで通過した」 |
| 「M3a は同一 genome の source identity 衝突を示した」 | 「M3a は stock 継承を示した」 |
| 「M4 は前処理差を示すが、重複宣言により compile 不能だった」 | 「M4 は実行可能な別プログラムへの到達例である」 |
| 「この変異・compiler・依存条件では拒否／未到達だった」 | 「非再帰境界に穴は存在しない」 |

## 親 brief への反論

**A-7 — stdin 断片の実測は仮説を支持するが、全文 gate 通過や新規性を確定しない。**

- **根拠 (file:line):** `s1-brief.md:8,13–18`。現物では `_dump_macros` は値でなく最終定義済みの**名前集合**を返す（`source_digest.py:1702–1726`）。macro coverage は define 本体の token paste／include probe と条件指令の未知名を調べる（`:1842–1879`）。`_worktree_defines` は CMake から各 file の定義を独立に作る（`:2071–2082`）。
- **real と主張する理由:** 今回の `SLEEP_READ_PHASE`／`TRACE` の単純な再定義には、これらの検査で一律拒否する実装は見当たらない。synthetic 枝内の define も同じ規則で走査され、別 file へ漏れた macro 値は後続 file の digest へ伝播しない。一方、`#undef` は `_dump_macros` に反映されるため「完全に未モデル」とするのも不正確。未知条件名や前処理失敗を伴う別の全文入力まで一般化できない。
- **是正案 (scope 内):** stdin 結果は動機として残し、判定は実 file 全文と実 gate の結果に置く。「既存記録にない純増」は限定し、D1490 の既存 `#undef` 問題との違いを「source identity の file 間伝播と消費側への影響」に絞る。

親 brief の修正点は次のとおりです。

- **`:15–18` の cache・certified・receipt 継承の断定を撤回する。** A-1／A-5 の消費側別の条件が必要。
- **P1 は限定付き支持。** clone は実 source の実験場所として妥当だが、製品経路全体の同一性は保証しない。
- **P2 は plan の留保を採る。** 「build しない → cache は汚れない」は強すぎる。生成条件・依存 bytes・前後観測に限定する。
- **P3/P4 は維持可能。** node 署名には失敗原因を添え、carrier が信頼済み template 側を変えていることを明記する。
- **P5 は scope 内。** `s1-brief.md:25` が一時 probe branch を明示している。既存 harness 用の probe と実験証拠だけで足り、恒久 gate・検査・台帳の追加は不要。

## 総括

**identity 層の盲点を測る計画は続行可能です。ただし、現在の plan のまま製品全体の「許された variant／stock 継承」の実証として閉じるべきではありません。**

最優先は、A-1 の admission による cache 分離と、A-2 の coder 検疫による拒否を報告へ反映することです。そのうえで、M3a/M3b の digest–TU 不一致、admission 前の terminal skip、M6 の TRACE 後段拒否を個別に判定してください。

本 consult は読み取りと静的検査のみです。file 書き込み・commit・push・pytest・configure・前処理・compile/link は実行していません。