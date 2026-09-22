## 所見

**推奨は adopt_with_conditions。** 骨格の基本方針は成立しますが、検査の接続、試験の合格条件、変異の帰属を実装前に固定する必要があります。以下は静的レビューであり、build・pytest・patch 適用は実施していません。

参照略号は次のとおりです。repo path はすべて指定 worktree 配下です。

- `B`：親 `brief.md`
- `P`：親 job の `codex/s2-plan.md`
- `D`：`output/insights/2026-09-21/silo-function-synthesis-space/README.md`
- `T`：`external/ccbench/cc/silo/transaction.cc`
- `C/`：`orchestrator/campaign/`
- `Q/`：`orchestrator/tests/`

1. **must-fix — norw の期待判定が現行 driver と完全一致していない。**

   根拠：`P:280,429` は `non-serializable && total_cycles>=1` とするが、`C/s2_verify_calibration.py:411–412` はさらに `exit_code == 1` を要求する。

   反例入力：`{"verdict":"non-serializable","total_cycles":1,"exit_code":2}`。計画の二条件なら合格し、現行判定では不合格になる。lockskip の両 X reason、early-unlock の保持欠落のみという修正は `C/s3_lock_coverage.py:299–312` と一致している。

   **影響：** verifier 異常終了を norw の検出成功としてレポートへ計上しうる。

   **代案：** exit code を含む判定を逐語で事前登録する。欠損・型違い・異常終了を別途拒否し、この反例を checker の負例にする。

2. **must-fix — 結果集計に空集合・ケース欠落を拒否する条件がない。**

   根拠：`P:379` は `all_pass=all(checks.values())` を採用する。`P:310` の欠損拒否は probe record の規則であり、必要な走行・check 自体が生成されなかった場合の規則ではない。

   反例入力：`runs={}`, `checks={}` なら `all([])` は真。三負例の片方の方策だけを落として、残った checks がすべて真でも同じ問題になる。

   **影響：** 未実施の試験を含む C 段出口が合格として保存される。

   **代案：** ケースごとに必須 run/check の集合を先に固定し、実結果との完全一致、値が実際の bool であること、必要な発火数が正であることを確認してから集計する。空入力、片方策欠落、commit が一件もない入力を負例にする。

3. **must-fix — 「最大待機」方策と、機構変異ごとの適用試験が未固定。**

   根拠：`P:278–282` は即 abort／最大待機を要求する一方、所有成果物は四方策だけ（`:261`）。その定義（`:355–359`）には、abort 1000 µs・lock 50 µs の最大待機方策がない。clamp 変異用の UINT32_MAX 方策も、この四本とは別物である。

   また `P:305` は holder を維持して limit-abort を要求するが、`:324,434` は上限削除を非検出対照とする。同じ焦点試験へ上限削除を投入すれば、終了条件を失って timeout し、「非検出対照」と両立しない。

   **反例入力：** 四方策しかない状態で `static10` を「最大待機」として代用する／no-limit に holder 永続の limit 試験を適用する。

   **影響：** 二方策の検出力、八変異の生存・検出分類、必要計算量が宣言と異なる。

   **代案：** 最大待機、clamp 超過、焦点試験用方策を本文 digest 付きで別登録する。八変異それぞれについて workload・方策・probe 有無・期待する最初の拒否層を表にする。no-limit は限定した正しさ検査での非検出対照とし、上限の焦点試験との関係を明記する。

4. **must-fix — hook 配線解除の変異と「実呼出し計数」の関係がまだ曖昧。**

   根拠：`P:294` は呼出し直前／直後から emit、`:326–328` は wrapper 内の呼出しだけを置換・削除、`:331` は実方策呼出しを数える、としている。

   反例となる実装形：

   ```cpp
   emit_call_before();
   auto r = policy_on_lock_conflict(s, c);
   emit_call_after();
   ```

   中央だけを固定応答に置換しても、両 event は残る。計数一致だけなら wiring check は緑のままである。逆に変異が計数も同時に削除すると、「方策を呼ばないこと」と「計数を消したこと」の帰属が混ざる。

   **影響：** 呼ばれない hook を発火済みとして報告しうる。

   **代案：** 焦点方策自身が `PolicyState` の専用 field を更新し、独立した呼出し site 数と照合するなど、呼出しを消すだけで観測差が出る構成を固定する。変異位置、event の残存範囲、期待 node 全集合を実装後に確認する。`docs/dev-wave/mutation.md:7–20` と F820（`docs/failures.md:23422`）が直接該当する。

5. **must-fix — 四段検査から実 build までの接続試験を、C の所有成果物に明記する必要がある。**

   根拠：`P:361` に接続順はあるが、B の試験は検査器単体（`:166–172`）、C の試験は parse・判定・積み重ね（`:262`）が中心で、smoke 入口の接続試験が明示されていない。現行 `C/pipeline.py:2585–2626` に新しい policy 検査の契約はなく、`evaluate` を呼ぶだけでは新検査の実行証拠にならない。

   反例入力：U32 戻り値関数の `return true;`。これは合法な C++ だが policy-C++ v1 では拒否対象（`D:247`）。grammar 呼出しを落とした smoke 入口は、TU compile だけではこれを拒否できない。

   **影響：** 単体検査器が正しくても、実際に評価される候補の受理集合が広がる。

   **代案：** C の smoke 入口を通して、合法方策が全検査を経て build へ進む正例と、上の入力が build 前に止まる負例を追加する。検査結果と materialize する本文の digest を一致させる。候補拒否、内部例外、compiler 不在・timeout のいずれでも evaluate へ進まない条件を固定する。将来の一般 pipeline 接続は E 段として分離してよい。

6. **should — 構文規則は網羅されているが、負例・境界正例の登録がその網羅性に追いついていない。**

   根拠：`P:195–207` は要求された字句・名前解決・自己初期化・部分式代入・return・switch・型規則を覆っている。一方、`:410–446` の事前登録には、switch、`?:`、min/max、shadowing の具体的な組が不足する。

   追加すべき合法 C++ の反例は、例えば次である。

   - `return b ? 1u : 1ul;`：枝の型不一致。
   - `return std::min<uint64_t>(1u, 2ul);`：明示 template 引数。
   - `switch (x) { case 0u: x=1u; default: break; }`：fallthrough。
   - `uint32_t x=1u; { uint32_t x=x; }`：外側同名変数があっても自己初期化。
   - `constexpr uint32_t x=1ull;`：禁止 suffix。
   - `return ::uint32_t(1u);`：先頭 `::` と許可外 cast。

   **影響：** 規則の実装漏れによる過剰受理・過剰拒否が、列挙済みの試験だけでは残る。

   **代案：** 各規則に正例・負例・最初の拒否段を対応させる。全経路試験と段単独試験を分離する現在の方針は維持する。特に外部名負例を TU 単独で試す案（`P:234–239`）は妥当で、全経路で TU だけが効いたとは数えない。

7. **should — P5 の登録は可能だが、ON 経路・変異内容の証明と同一視してはいけない。**

   根拠：`C/condition_meaning_gate.py:12–25` は conditional の選択だけを保証し、body の意味・動的到達性・期待 anomaly を保証しない。`P:318,343` は八変異へ共通 macro と代表 patch を使う。

   反例入力：同じ `#if IZANAGI_BREAK_SILO_POLICY` を持つ別 body。branch witness は同じ条件選択を証明できるが、clamp 削除か hook 削除かは判定しない。通常の `break;` の存在検索も `T:181` に元からあるため証拠にならない。

   **影響：** 別の変異、または無効な変異に、期待する破壊動作の証明を誤って付与しうる。

   **代案：** `P:351` の限定を必須条件にする。実 materialize 後の TU、軸 ON、負例 ON/OFF、case/patch/source digest に束縛し、対象箇所の意味ある差を保存する。代表 patch の receipt を八変異共通の意味証明にしない。

   閉集合 test の三 macro 追加、22→25／23→26 は、それ自体では test の弱体化ではない。旧集合・未知 macro 拒否・runtime witness の限定を保ち、docstring の件数も更新する必要がある（`Q/test_condition_meaning_gate.py:3380–3419`）。

8. **should — 裸 macro という命名だけから「pipeline から定義不能」全体へ一般化しない。**

   根拠：`P:24` が確認するのは `Genome` の名前写像であり、`C/model.py:92,146–152` は確かに `CCBENCH_` を付ける。一方、診断 macro は意図的に CXX flags 経由で供給する計画（`P:342–343`）で、build 経路には環境を引き継ぐ箇所もある（`C/buildcache.py:2838–2854`）。

   反例候補：`CXXFLAGS=-DIZANAGI_SILO_POLICY_PROBE=1` を持つ通常 build。ここから到達可能と断定はしないが、Genome の写像だけではこの経路の遮断は証明できない。

   **影響：** 診断用計数の混入を排除できた範囲より、性能 build の非計装性を広く主張してしまう。

   **代案：** 通常 build の実 compile command と preprocess 出力で、probe・負例・変異の非発火を確認する。TRACE=0 で既存 trace が消えることと、probe が消えることは別々に確認する。環境経路への新しい一般 gate が必要なら scope 外の裁定へ返す。

9. **should — 骨格は成立するが、保持する stock 挙動と追加境界を明文化する。**

   根拠：`P:114–125` の配置なら、CAS 失敗も計数し、待機後は再読込し、上限／abort／未知 action で `[begin,itr)` を解放できる。CAS による expected 更新は `external/ccbench/include/atomic_wrapper.hh:67–69` と一致する。

   `T:185–191` の absent 検査と `max_wset_` 更新は成功後に保持すべきである。ただし stock の absent 出口も `unlockWriteSet(itr)` であり、現在の tuple は解放範囲に含まれない（`T:371`）。これを「全 abort 出口で取得済み lock を全解放」と一般化してはいけない。

   flag では `BACK_OFF != 1` への修正は正しい。一方、`SILO_POLICY_VARIANT=2` は計画の `#if` では ON と同義になる。`NO_WAIT_OF_TICTOC` 未定義も前処理上は 0 と扱われる。

   **影響：** stock 保持の範囲、flag の受理集合、lock 解放の保証が文書上ずれる。

   **代案：** absent・max 更新・TRACE の位置を OFF/ON の構造試験へ含める。軸値を 0/1 に閉じる担当と、前提 macro の definedness を確定する。既存 absent 出口を変更するなら、本件へ黙って混ぜず別裁定にする。

   ON では no-wait 固定により `T:165–167` の `goto retry` 枝を選ばず、OFF ではその枝を含む元コードを保存する。`clear_shadow`（`:152`）、`record_lock`（`:179`）、prefix 解放時の shadow reset（`:379`）を保持する計画に、静的に明白な直列化条件の弱化は見つからなかった。

## brief と plan の前提の判定

| 項目 | 判定 | 判断 |
|---|---|---|
| P1 | 要修正 | A→B/C の依存分割は妥当。C に smoke 接続試験を明示し、B/C 共通の拒否・障害契約を先に固定する。 |
| P2 | real | 専用 grammar と API 単一正本は妥当。適用後 bytes を比較する `P:158` の案を採る。無名仮引数も固定が必要。 |
| P3 | real | 二 file の patch、PIN 不動で成立する。submodule HEAD は `e9e477ca1b55348ab4530de0b1cf663ce4555290` と確認した。 |
| P4 | 要修正 | brief の lockskip「ループ内側」は誤り。実 patch はループ直前。norw/lockskip の新版と early-unlock の再適用確認という plan は妥当。 |
| P5 | 要修正 | 登録は必要。ただし site 数・周辺 registry・限定された証明の意味まで含める。三 macro 増加だけで ON の破壊動作は証明できない。 |
| P6 | 要修正 | 八変異の分類は設計と一致するが、no-limit の試験選択、hook 解除の観測、timeout の到達条件を固定する必要がある。 |
| P7 | 要修正 | evaluate 利用は妥当。100 行以内を優先条件にせず、四段検査、実 authority、両 verify、同 job stock を実経路で接続する。 |
| P8 | 要修正 | 旧 job 単価から新ケース単価への換算は暫定。`P:464–476` の未包含費用を含む総額で投入前確認が必要。 |

brief の主要な T 行番号は現コードと一致する。worktree HEAD は `4c0eb08b98749580416d030a98fa2ddfc26c799a`、現在環境の g++ は 11.4.0 と確認した。ただし、この確認は将来の計算ノード toolchain の証明ではない。旧 job の Elapse 原ログは今回の指定資料では確認できない。

`B:26` の「login の build は hook が拒否」は実効発火を未確認であり、安全境界の証拠には数えない。

## 再発しうる失敗の型

- **[恒真ゲート]** 空 checks、hook 呼出しと独立して残る計数、検査器単体だけが緑で実入口には未接続。
- **[ドリフト]** norw の exit code 脱落、最大待機の別方策への置換、API・本文・実 build 間の不一致。
- **[捏造/幻覚]** branch witness を破壊動作の証明へ一般化、未発火要因を測定済みとする、旧単価を新 workload の上限とする。
- **[権限逸脱]** P5 を契機に一般 gate や E 段の role／pipeline を無裁定で拡張する。
- **[セッション死・救出]** no-limit と holder 維持試験の組合せ、timeout 変異の内外予算不整合。

変異については、`docs/dev-wave/mutation.md:7–20,55–60` に従い、実装後に前段・後段・内側の拒否を確認する。計画段階の期待 node を検出実績として扱わない。

## scope 外の層 (裁定パッケージ候補)

- **E 段の候補生成・一般 pipeline 接続。** C の smoke 入口で四段検査を実証することは本件内。任意の将来候補が同じ検査を必ず通る保証、p3_s4_loop、coder／auditor role は別段。
- **環境を含む診断 macro の全面遮断。** 既存経路の検証は本件内。新しい一般的な build 環境 gate が必要と判明した場合は別裁定。
- **stock の absent 出口の lock 解放。** 現状維持と追加保証を区別し、変更するなら別件として扱う。
- **七要因の動的実証範囲。** `P:314` の静的写像＋未測定表示を C 出口として認めるか、全七経路の実 CC fixture を要求するかを固定する。静的検査を動的発火と呼ばない。
- **producer 接続仕様の固定先。** `D:500` は C 前に producer／consumer の契約一致を要求する。role 実装を E に残しても、無名引数等を含む接続仕様の文書と所有者は C 着手前に決める。

## 総括

**adopt_with_conditions。** 骨格の基本配置と型付き部分言語の方針は採用できる。
must-fix は以下の五点。
1. norw 判定へ現行の `exit_code == 1` を戻す。
2. 必須 run/check 集合を固定し、空集合・ケース欠落を拒否する。
3. 最大待機方策と八変異それぞれの試験・期待層を固定する。
4. hook 呼出しだけを除去した変異を検出できる観測を固定する。
5. 四段検査から実 build までの接続を、C の入口試験で証明する。
本レビューは静的所見であり、実装・検出力・C 段出口の合格を報告するものではない。