## 所見 (A-1, A-2, …)

静的検査では、P1・P2 を阻止すべき must-fix は確認しなかった。ただし、受理集合の拡張範囲と実測の射程は次のように修正すべきである。ファイル変更・pytest・検証 probe の再実行は行っていない。

以下、`F` は `orchestrator/campaign/s8b_ratified_freeze.py`、`T` は `orchestrator/tests/test_s8b_ratified_verify.py`。brief・plan・evidence は指定された `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/` 配下を指す。

**A-1 — P2 は「producer の 2 形」以上の journal を新たに受理する。**

- 対象: `codex/s2-plan.md:64`、`orchestrator/campaign/s8b_floor_campaign.py:7616`、`F:2149`。
- 問題: binding 無し reservation の重複・順序を検査しないため、producer が一度だけ campaign 前に書く形に加え、複数 reservation や campaign 後の reservation も受理対象になる。各 record の exact key 検査だけでは防げない。
- **放置時の帰結: 型が正しい余分な reservation を挿入した journal が新たに受理される一方、床値の計算や result.wall_ledger は変わらない。**
- 分類: **should**。
- 推奨: 「現物形だけ」という `verbatim/s1-brief.md:19` の説明を訂正する。producer 形への追随を目的とするなら reservation は任意・高々 1 件・campaign より前とする。診断 record として多重性を許すなら、その拡張を明記して正例で固定する。既存保証の維持だけを理由に、今回初めて許す event の多重性を無条件に許す必要はない。

**A-2 — P3 の「旧 checkout でも同じ結論しか出ない」は実測から導けない。**

- 対象: `verbatim/s1-brief.md:17`、`F:3078`、`F:3092`、`F:3304`、`F:3379`。
- 問題: reverify と live は policy・選択 identity に加え、contract resolver も異なる。identity 単独検査も historical resolver を使う。旧 checkout への適用は、コード・契約・policy・scan 対象 tree の組合せが別になる。
- **放置時の帰結: historical reverify の拒否結果が、未検証の旧 checkout における live admission の到達性の証拠として参照される。**
- 分類: **should**。
- 推奨: 旧 checkout 実測を省く判断自体は維持できるが、「同じ結論しか出ない」ではなく「本 wave の受入範囲外で未確認」と書く。`codex/s2-plan.md:211` の「live 成功を証明しない」は妥当。

**A-3 — brief 末尾の拒否原因が N1 と矛盾する。**

- 対象: `verbatim/s1-brief.md:23` と同 `:6`、`evidence/reverify-probe-journal-stage6-mutated.json:18`。
- 問題: 「旧 pin checkout でも新 main でも段階 4 (journal)」は、新 main の policy 拒否という提示実測に合わない。
- **放置時の帰結: 成果物の値・受理集合は変わらないが、完了記録が現在の拒否原因を誤って参照する。**
- 分類: **nit**。
- 推奨: 旧時点の journal 拒否と現行 main の manifest/policy 拒否を分ける。

## P1 段階 6 の受理集合の変化

**失われる保証は実在する。** 現行 `F:3536` は全 result / measurement_closure の一意導入を G に揃える。cert の `C<G` (`F:3531`) と合わせ、次を保証していた。

- 全対象 path が同じ commit G で初めて現れる。
- 各導入は cert C より厳密に後である。
- G より前の tree に当該 path は存在しない。

P1 では各 path を独立に `[C,G]` 内へ置ける。`i=C`、異なる中間 commit への分散導入、G 以前からの存在を受理する。「現物 `i=C` を足すだけ」より広い。祖先関係は半順序なので、C 後に分岐した別々の branch 上で各 artifact を導入し、G 前に合流させる形も条件を満たし得る。

一方、次は保たれる。

- H の全到達履歴で別 bytes が現れないこと: `F:490`。
- 各 path の導入が一意であること: `F:638`。
- cert の一意導入・非 merge・`C<G`: `F:3526`。
- G/H/worktree の bytes・mode 一致: `F:1765`。
- raw hash、semantic、binding、scan の既存検査。

artifact の非 merge 導入は新たに明示される。ただし、導入済み artifact が通常の merge を通ることは禁止しない。

**`C=i` は cert の条件と矛盾しない。** `C=i<G` は充足可能である。ただし従来の `C<i` は失われる。これは「cert を commit してから result を commit した」という記録上の順序の削除であり、単なる同値変形ではない。実走前発行や実時間順は、そもそも現行 docstring (`F:3161`) も保証していない。再配置時に cert と result を一緒に commit する現物について、Git 導入順と走行順を同一視すべきでない。

**G 偽装検出は保たれる。** 新検査は `_gen_path(N)` の導入集合を H の DAG から独立に導出して申告 G と比較する。artifact 導入を G の定義に使わないため、循環はない。

`wrong_g=A` では artifact の導入は `[C,A]` に入るが、世代文書の導入は真の G のままなので新検査が拒否する。さらに既存の段階 7 も active chain の再解決結果と `generation_commit` を比較する (`F:3034`、`F:3040`)。新検査は唯一の偽装防壁ではなく、段階 6 の拒否帰属を維持する追加防壁である。

production の直接構築は検索上 **loader 内の `F:1478` のみ**。loader は `F:1473` で active chain を解決し、世代導入を `F:1231` で一意導出して、`F:1477` の V1 等を通す。代表的 consumer は `orchestrator/campaign/s8b_oracle_driver.py:639`、同 `:1324` で loader を呼ぶ。直接構築禁止の静的テストは `orchestrator/tests/test_s8b_ratified_freeze.py:3070` にある。ただし文字列検索による規約検査であり、任意 Python からの偽造不能性ではないことは `F:797` が明記している。

**H-pure と追加 ancestor 検査は整合する。** 捕捉済み H から導出した full commit OID を `_git_ok` に渡すなら、新しい HEAD や worktree の内容を参照しない。shallow は `F:341`、replace/grafts は `F:347` で先に拒否される。複数 root は一律拒否ではなく、H の全 DAG を検査し、別 root の同 path 導入は複数導入または祖先区間違反として落ちる。

`_git_ok` は exit 1 と Git エラーをともに False にする (`F:337`)。受理方向には倒れないが、Git エラーが祖先違反として記録される診断上の限界は残る。

## P2 journal の受理集合の変化

新しい受理形は次のとおり。

| campaign | reservation | P2 の受理 |
|---|---|---|
| binding 無し | 無し | 維持 |
| binding 無し | binding 無し | 新規受理。plan では複数も許容 |
| binding 付き | 同じ値の binding 付き 1 件 | 新規受理 |
| 片方だけ claim | 任意 | 拒否 |
| key 片欠け・型不正・値不一致 | 任意 | 拒否 |

plan が加える **値の一致** (`codex/s2-plan.md:62`) は、brief の claim 状態一致より強い。producer が同じ `external_checkpoint_binding` から両 record を作るため妥当である。

binding 無し reservation は `s8b_floor_campaign.py:7616` と `:7634` の独立した条件分岐で生成可能なので、受理してよい。「official だから binding 必須」とする根拠は提示資料からは得られない。

ただし binding は、ここでは **記録内の整合情報**である。非空文字列と record 間一致だけでは、実在 PBS job や nonce の外部認証にはならない。両方を同じ別文字列へ変更すれば、この追加述語自体は通る。これを job 身元の証明と表現してはならない。成果物側では campaign 全体の mirror 比較 (`F:2536`、`F:2554`) 等を保つ必要がある。

`floor_liveness._validate_journal_binding` との役割差は明確である。

- liveness は照会対象の外部 job/nonce に照合する (`floor_liveness.py:394`)。開始途中の journal も扱い、両 event の存在を常に要求しない。
- launch は completed journal の既存状態機械・receipt・result 整合を検査する。campaign の cert/receipt key も必須である。
- liveness は reservation の型検査を claim 時だけ行う (`floor_liveness.py:259`)。plan は binding 無しにも型を要求する。
- liveness は event 重複を常に拒否する (`floor_liveness.py:386`)。plan は binding 無し reservation を例外にする。

したがって、validator 全体を共有すべきではない。一方、reservation の key・型という共通文法は将来の乖離源になる。共通部分の契約テストで両者を照合し、外部認証・途中状態・完了状態の差を明記するのが適切である。

## 変異の帰属

新述語は未実装なので、以下は現行コードと plan から確認できる到達経路であり、実測結果ではない。

| 負例 | 新述語まで届かせる条件と拒否点 |
|---|---|
| 導入が C より前 | 同 bytes の closure を base に導入する。`F:3235` の G/H 一致、段階 4・5 を維持し、`F:3536` の置換箇所で下限検査へ。plan `:177` は妥当 |
| G の祖先でない | public 経路では `F:1769` の G-tree 検査が先に拒否する。一意導入で G に存在する path は G の祖先に導入点を持つため、新上限述語への到達は構造的に困難。plan `:198` の helper 単体分離は正しい |
| merge 初導入 | 両 parent が path を持たない merge M で追加。`F:511` が M を導入点とし、C≤M≤G を満たして新非 merge 検査で拒否。plan `:179` |
| 同 bytes の複数導入 | 導入・削除・再導入し、G/H は一致させる。`F:490` は通り、`F:638` の一意性で拒否。plan `:180` |
| wrong_g=A | `T:2842` の直接構築で G だけ交換。新 artifact 区間を通り、世代文書導入比較で `generation-introduction`。`T:2848` の reason/cause 固定を維持 |
| C=G | `T:2828` から `F:3531` の既存 `cert-lineage`。新 artifact 述語の検証とは別 |
| 未知 event | commit 前に挿入し、`F:2052` の `journal-event`。plan `:194` の手前落ち回避が必要 |
| binding key 片欠け | `F:2057` に置く exact key 検査。型・claim 検査まで届かないのが正しい |
| binding 型不正 | key 集合を完全に保ち、`F:2057` 直後の新型検査へ |
| 片側 claim | 各 record は合法な 2 形のどちらかにし、`F:2167` 付近の新整合検査へ |
| binding 値不一致 | 両側を非空 str に保ち、新値比較へ。型検査で落とさない |
| reservation 型不正 | exact key 集合を保ち、追加する field 型検査へ |
| wall_ledger の binding 欠落 | journal 自体は合法にし、`F:2554` の `result-wall_ledger`。journal 新述語の負例とは別 |

変異を「殺す」の意味にも注意が必要である。例えば新世代文書検査を削除しても、wrong_g は段階 7 の `F:3040` で拒否され得る。**例外が出たことだけでは新検査の実効性を証明しない。** plan `:192` の exact reason/cause assertion が失敗することを変異検出と記録すればよい。

また、独立 fixture は `T:676` で直接構築し loader を通らない。public `launch_validate` 成功は core の証拠であり、V1 を含む loader→launch 全体の成功証拠ではない。production-emitter fixture と実 repo loader の観測を別に保持すべきである。

## 親の実測とその一般化への疑義

**N1:** 提示 JSON の `launch_validate` は `manifest-invalid` / `binary-admission` であり、`F:3308` が journal 呼出し `F:3318` に先行するため説明と整合する。ただし、提示 JSON 単独では driver の拒否「2 件 exact」までは証明しない。plan `:209` の gate-check 再実測が必要。

**N2:** `evidence/journal-keys-probe.txt:4` と `:8` は、reservation 未登録と campaign の追加 2 key を直接示す。これは key 集合の観測であり、値の型・binding 相互一致・全 journal semantic の成功証拠ではない。producer の両形はコードの分岐で別途裏付けられる。

**N3:** `evidence/reverify-probe-journal-stage6-mutated.json:13` は candidate path の未申告 hit を示す。段階 8 到達という説明は現行検査順と整合する。ただし JSON には一時変異の正確な patch が含まれないので、**今回提案する P1・P2 そのものが通った証拠ではない**。plan `:205` の最終実装・無変異 reverify が必要である。

「semantic / binding に別の不整合は無い」は、その H・変異版・historical 経路で到達した範囲に限定すべきである。live 固有の相違は次の 3 点。

1. current contract 照合: `F:3078`。
2. current admission policy: `F:3304`。
3. floor selection identity: `F:3379`。

N1 は同じ実測で current contract を通過したことは示すが、policy より後の live 検査は未到達。identity 単独成功を足しても live 全体成功にはならない。

N3 の「validator では解けない」は、**現行の許容設計を維持する範囲では正しい**。`F:3048` の active-chain exemption は path を列挙し、その path の hash を固定する。世代文書と同 bytes でも、別 candidate path に免除は伝播しない。candidate を追加免除する変更は技術的には可能だが、`verbatim/D2120-item2.md:14` の「走査除外は広げない」に反する。単なる allowlist 追随として本 wave に入れてはならない。candidate 削除が十分な解決かは本レビューでは未確認であり、別件に留める判断は妥当。

なお `F:3548` には selector evidence exemption もある。「4 path のみ」は active-chain 部分についての説明であり、一般の全 exemption 集合の説明としては不正確である。

**N4:** Git の追加履歴では cert と result が `cc82edc8c` に現れ、G の差分は世代文書 1 件だった。提示された topology と整合する。ただし `git log --diff-filter=A` だけでは全 DAG の一意導入・不変 bytes は証明しない。最終実装の `_immutable_introductions` を通す必要がある。また、この観測は `i=C` の必要性を支持するが、全中間 commit を許す `[C,G]` を唯一の設計として導くものではない。

## 総括

P1 は従来の「全 artifact が G に同時導入され、C より厳密に後」という保証を緩和する。その代わりに一意性・不変 bytes・非 merge・祖先区間を維持し、G の根拠を世代文書自身の導入へ移す設計は整合しており、信頼の根の循環は見つからなかった。

P2 も妥当だが、binding 無し reservation の多重性・順序まで広がる点は明示的に決めるべきである。binding の記録内一致を外部 job 認証と扱ってはならない。

推奨は **A-1・A-2 を修正して実装へ進む**。完了の主張は validator の修復と限定した到達証拠までとし、live launch 成功や W-4 / W-5 の開始許可へ一般化しない。