## 総括

- **real 3 件／refuted 6 件／must-fix 2 件**。real のうち 1 件は等価対照の射程に関する nit。
- 比較述語・通常の終了 rc・reject の key 集合を変える経路は、計画どおりなら認めない。
- **親 brief への異議:** 診断 I/O を加えても制御結果が不変という保証と、「live 比較なし」の一般化は強すぎる。
- P1・P2・P4 は採用可能。P3 は返ってくる書込み例外と I/O stall を分ける必要がある。
- 静的検査のみ。ファイル変更・pytest・変異実走は行っていない。

以下、`driver` は `orchestrator/qualification/t126_driver.py`、`artifacts` は同ディレクトリの `artifacts.py`。`brief`・`plan` は指定された `parent-brief.md`・`plan-out.md` を指す。

## 1. 受理集合の不変性

**所見 A1 — 型変更による通常経路の受理・拒否変更：refuted。**

- **根拠:** `driver:449–474`。typed raise は従来の `try/except Exception` の外で、非空・全行 pass の述語もそのまま。基底例外の rc=34 を継承しても、production 子は helper の返す 31 で終了し、親は従来の `AttestationError` を送出する。`driver:763–770,816–823` の evidence keys は `stage/type/message` のまま。
- 成功分岐に sidecar 書込みはなく、返ってくる書込み例外は外側の `except BaseException` で 31 に畳まれる。
- **是正案:** この配置を維持する。新しい内部例外の型名を親の evidence に直接流さない。
- **成果物への影響:** 診断が得られた拒否の message と evidence hash は意図どおり変わるが、通常経路の受理集合・成功 attestation JSON は変わらない。

**所見 A2 — I/O stall まで含めた制御結果不変の保証：real／must-fix。**

- **根拠:** `artifacts:470,480,492,527–530` は fsync を実行する。D474:8–11 はこれを明示的に避けている。`plan:286` は子の timeout を認める一方、親の reader は同期実行する計画である（`plan:203–225`）。
- 子の fsync stall は `driver:1213–1239` の timeout に入り、通常の mismatch message が timeout message に変わる。さらに、子が終了しても親の存在確認・読取りが stall すると、`fsm.reject` にまだ到達しない。例外捕捉はブロック中の I/O を止めない。
- 外側には `tools/pegasus/t126_qualification.sh:834–843` の timeout があり、「必ず rc=31・attestation reject が記録される」とは言えない。成功経路も helper 呼出し分の時間差があるため、実時間上の受理集合まで同一とは証明できない。
- **是正案:** 非 fsync の診断書込みと、親の同期読取りを拒否記録の前提にしない方法を段 4 で確定する。少なくとも「通常の例外では rc 不変」と「stall・外側 timeout は保証外」を分け、現計画を D474 完全準拠と扱わない。
- **成果物への影響:** mismatch の説明・sidecar 参照が timeout に置き換わり、親読取りの stall では attestation reject の台帳行自体が残らない可能性がある。比較上の不一致が certified に転じる経路ではない。

## 2. 規律 2・3・7 との整合

**所見 A3 — sidecar の authority 化、全行記録の過剰性：refuted。**

- **根拠:** `plan:218–230` は非ゼロ終了後の message だけを変更する。`driver:1280–1289` では拒否例外が成功 manifest 作成より前に伝播する。sidecar を読んで受理へ戻す分岐はない。
- 成功時に追加文書を作らない方針は項 15 と整合する。ただし、既存の accepted attestation JSON まで削除する意味ではない。
- 値は `env_attestation.py:882–907` の CPU・cache・NUMA・clock・visibility の固定フィールドであり、hostname は比較対象外（同:993）。秘密情報を新たに収集する経路は示せない。全行保持は失敗行だけでなく通過した前提も残す。
- ただし「21 行」はサイズ上限ではない。文字列・配列の総 bytes が固定という説明は避ける。また、比較行と hash だけで凍結 profile 全体や実行時 policy まで自己完結して再構成できるとは限らない（同:961–969、D2056 決定 5）。
- **是正案:** P2 を維持し、主張を「比較時の全行・判定値の保存」に限定する。秘匿対策やサイズ gate の新設を must-fix にしない。再計算の自己完結性は別裁定。
- **成果物への影響:** 現案では診断 bytes が増えるだけで checker authority・certified 選択は変わらない。自己完結した再計算を主張すると、レポートの保証範囲が実装を超える。

## 3. create-only 経路の衝突

**所見 A4 — accepted path との衝突・通常再試行による上書き：refuted。**

- **根拠:** `driver:1198–1201` の `.json` と計画の `.mismatch.json` は別名。`artifacts:329–355` はこの名前を拒まない。
- `run_series` は各 round の pre-round を一度呼び、post-series は終端時に一度呼ぶ（`driver:740,762,813–825`）。失敗時は再送せず例外を伝播する。再起動で非空 attempt を使うことも `artifacts:699–700` が拒否する。
- 既存 sidecar を先置きした場合は create-only が拒否し、元 bytes を保存する。通常経路で同名再試行が起きる根拠はない。
- **是正案:** 衝突時に別名を増やさない現案を維持する。既存ファイルを読めても「今回の子が公開した証明」とは扱わない。
- **成果物への影響:** 通常実行では衝突による値・参照の変更なし。先置きされた文書への参照は診断に限定され、受理根拠にならない。

## 4. P1：execution_guard を変更しない根拠

**所見 A5 — 正規比較値の非 JSON 型による `TypeError`：refuted。**

- **根拠:** `execution_guard.py:618–624` は非 pass 行を JSON 化する。`env_attestation.py:875–929` は scalar、list、dict を返し、cache/NUMA は `dataclasses.asdict` を通す。
- `schema_v2.py:123–189,203–257` は文字列・整数・bool・有限数値・list を検査する。cache の CPU 集合も set/frozenset ではなく `List[int]`。正規 loader/probe 経路で非 JSON 型が混入する反例は得られなかった。
- 指定 floor test の `test_s8b_floor_campaign.py:9127–9145` は vendor 不一致と `out_root` 不在を確認する。これはその出力ディレクトリについての pin であり、全 filesystem の副作用ゼロの証明ではない。
- **是正案:** P1 は維持可能。「全不一致・全副作用を実測済み」と一般化しない。構造化属性だけを足す変更も不要。
- **成果物への影響:** 今回 P1 を維持しても、正規比較値が JSON 化で失われる経路は示せない。floor 出力を新設しないため既存参照も維持される。

## 5. P4：空 comparisons の sidecar

**所見 A6 — 空 sidecar が無意味・有害という懸念：refuted。**

- **根拠:** `driver:465` は空集合を明示的に拒否する。既存 test `test_t126_qualification_driver.py:361–367` もこれを固定している。現在の production comparator は固定フィールドから行を生成する（`env_attestation.py:1004–1015`）。
- `status="rejected", comparisons=[], failed_fields=[]` は「比較行が生成されなかった拒否」を表す。probe 例外で sidecar がない状態と区別できる。`failed_fields=[]` 単独を成功と解釈する consumer は計画にない。
- **是正案:** P4 を維持し、空比較を「全行 pass」と説明しない。独立した gate は不要。
- **成果物への影響:** 従来失われていた空比較の事実が診断に残る。拒否集合・成功成果物は変わらない。

## 6. 変異の帰属

**所見 A7 — comment-only E1 の無限定な等価扱い：real／nit。**

- **根拠:** `plan:263–276`。M1・M3・M4 は同じ主 killer を持つため、一対一の「専属」ではない。ただし plan 自身が主 killer の意味と明示しており、誤った排他性は主張していない。
- M1 は実 helper に sidecar を書かせて存在・内容を検査するため、fork なしでも殺せる。一方、closure が helper を呼ばない変異や `os._exit` の返却値変更を殺す証拠にはならない。plan:250 はこの限界を明記している。
- E1 は helper の挙動については等価だが、driver bytes を変更するので live identity について等価ではない。全 unit test 生存は矛盾しない。
- **是正案:** E1 を「対象 helper の挙動に関する等価対照」と限定する。親の fork 実測結果は helper の変異結果と分けて報告する。現段階では未検査を隠していないため must-fix にしない。
- **成果物への影響:** comment-only でも新規 live series の digest・ID は変わる。helper test 生存を「成果物全体が同一」の証拠にすると検証レポートが過大になる。

## 7. identity file と親 brief の一般化

**所見 A8 — 「歴史 snapshot のみ、live 比較なし」の適用範囲：real／must-fix。**

- **根拠:** `brief:24` に対し、`contract.py:51` は driver を identity 集合に含める。`driver:354–376` は実ファイル hash と HEAD blob を比較し、`driver:896–897` は prologue の driver hash と照合する。wrapper も実際に hash を採取する（`t126_qualification.sh:798–799`）。
- **新規実走:** 未 commit の driver を source として使えば HEAD 不一致になる。変更を含む整合した commit・source stage・submission identity が必要で、新規 series/attempt の参照も変わる。古い submission/prologue の流用を許す根拠にはならない。
- **過去 attempt:** `verify()` は `driver:1376–1380` から記録 identity を検証する。`identity.py:125–150` の対象は記録済み commit の blob であり、現在の driver bytes ではない。したがって、今回の driver 変更だけで過去 attempt が一律 invalid になるという懸念は反証できる。live schema 照合は別途存在するが、今回 schema は変更しない（同:152–160）。
- **是正案:** brief を「既存 literal hash の検索では更新対象 pin を発見しなかった。live identity 照合は存在する」と修正する。新規実走の identity 更新と過去 attempt の再検証を分離する。歴史 manifest の再発行は求めない。
- **成果物への影響:** 新規 series ID・attempt ID・prologue hash・台帳参照は変わる。旧参照を再利用すると実走開始前に拒否される。過去成果物を新しい digest に書き換える必要はない。

## 裁定パッケージ候補

1. **D474 と writer 選択:** create-only を保つ非 fsync の診断経路を認めるか。併せて親の同期読取りを拒否記録の前提から外すか。現段階では実装済み・制御結果不変とは扱わない。
2. **再計算可能性の射程:** 比較行保存で完了とするか、D2056 相当の凍結 profile・照合時 policy まで含む自己完結した再計算を別 task にするか。今回の T-2683 は前者として完了可能。
