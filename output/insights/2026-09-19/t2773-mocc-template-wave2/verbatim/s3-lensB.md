## 所見 1: auditor-live の機械要件から入力隔離の検査が抜けている

**real/refuted の判定材料:** **real（plan の要件漏れ）**。設計正本:297 は「mocc 節を持つ auditor 定義と read-only・入力射影の構造」を要求する。一方、plan:318、523〜530 の JSON・consumer 要件は auditor の sha と mocc 追記までで、権限・射影の機械確認を含まない。plan:756〜767 の n=1 射影は適切だが、D38 決定4では n=1 と機械要件を分けている。

既存の `spec.py:595〜601` が tools 契約を検査するため、新たな隔離機構は不要。これを機械証拠へ接続すれば足りる。放置すると、新 JSON の緑が「auditor 定義の存在」までしか示さない。

**must-fix / should / nit:** **must-fix**

**是正案 (逐語):**

> `auditor_definition` は実ファイルの sha・項目別 mocc 記述に加え、既存 role loader による Read/Grep/Glob 契約の検査結果と、性能値・期待 verdict を除外する入力射影の構造検査結果を記録する。これらを機械 check に含める。n=1 の応答やファイル存在で代用しない。

## 所見 2: P2 は妥当。ただし sha 鎖と check 成立の検査を明確に分ける

**real/refuted の判定材料:** **P2 の不当性は refuted、検査手順の曖昧さは real**。

設計正本:348 は wave 1 の driver/test/JSON「拡張」と書くが、D2134 項5・DW-O09 は歴史的証拠の保持を支持する。新 driver が helper を再利用し、新 JSON から旧証拠を参照する案は整合的。ただし D2134 項5が直接名指す保持対象は T-2294 であり、wave 1 全ファイルの永久凍結をその逐語決定と呼ぶのは過大。

plan:316〜317 は32/14 checkの参照、526 は旧 JSON 鎖の実 sha 一致を要求している。しかし、**参照先の必要 key・真値・観測との対応まで検査するのか**が明瞭でない。既存 `test_mocc_mutation_proof.py:329〜384` は wave 1 の観測から32 checkを再導出するので再利用可能。

**must-fix / should / nit:** **should**

**是正案 (逐語):**

> 新 JSON → wave 1 JSON → T-2294 JSON の各 path/sha を検査し、参照先を実際に開いて旧32/14 checkの必要 keyと成立を確認する。wave 1 の入力由来検査は既存検査を再利用する。旧証拠に新 field は要求しない。欠落 JSON・hot 証拠欠落・check key欠落・hash不一致の拒否対照を §10 の要求として明記する。

sha 鎖は証拠の同定であり、それだけを check 成立の代用品にしなければよい。

## 所見 3: P6 の発火条件は妥当。auditor の文字列検査には項目境界が必要

**real/refuted の判定材料:** **鍵の偽陽性という懸念は refuted**。

plan:483〜501 の判定をメモリ上で照合した結果、現 HEAD の `patches/*.patch` には発火対象がなかった。既存計装・負例4本・Silo template は負例になる。提案された mocc marker の追加 hunk は正例になる。ただし新 patch 自体は未作成なので、正例は合成 hunk による確認。

鍵(b)は `axis_*.py` に限定し、SOURCE_REL・MARKER_ID・TEMPLATE_PATCHを併用する（plan:507〜515）。`axis_trigger_gating.py:24` は Silo source なので発火しない。EBS 所属も、SOURCE_RELだけの全 module 探索も使わず、D2134 項6に適合する。

auditor 検査も plan:528、819 は「各項」「項目別内容検査」としており、単なる全文中の `"mocc"` 検索を指定してはいない。ただし実装方法は未確定。

**must-fix / should / nit:** **should**

**是正案 (逐語):**

> auditor 本文をギャラリー型番号とチェックリスト番号の境界で分割し、型8/9/13/16・チェックリスト11/12/13それぞれに独立に固定した必須記述を要求する。全文中の `"mocc"` の存在や、検査対象自身から生成した期待文字列だけでは合格させない。該当追記の削除・別項目への移動を拒否対照にする。

## 所見 4: auditor の pin 3箇所と semantic_digest は閉じている

**real/refuted の判定材料:** **漏れという懸念は refuted**。

plan:581〜609 は次を全部含む。

- `review_ledger.SOURCE_FILE_SHA256["auditor"]` 更新。
- 更新後の `load_role_specs` → `render_adapter` による adapter 再生成。
- originless baselineへの literal shaを使った extension追記。

`spec.py:837` で `render_adapter` が `semantic_digest(spec)` を呼ぶため、semantic_digestの手動更新漏れもない。description不変はplan:579、`--write`不使用は609に明記。後者は `check_codex_agents.py:352〜360` と一致する。

完全な旧shaの出現先は機械側3ファイルと歴史 insight 1ファイル。短縮値 `a0912ebb` の検索では歴史 insight がさらに1ファイル増える。

**must-fix / should / nit:** **nit（手順変更不要）**

**是正案 (逐語):**

> renderer の出力全体を採用し、semantic_digestを含む派生値を個別編集しない。歴史 insight と既存 extension 内の旧shaは保持する。

## 所見 5: 主要な pin・inventory 閉包は plan に既に入っている

**real/refuted の判定材料:** **新たな必須更新漏れは確認できず、主要な疑いは refuted**。

| 検査面 | 現物と判定 |
|---|---|
| patch define inventory | `test_ccbench_spawn_sites.py:662〜666` が cache→TU mappingを拾う。`MOCC_TEMP_PREDICATE` は対象。plan:691〜698がCounter更新を列挙済み |
| subprocess allowlist | plan:687の既存 helper再利用なら新直接siteなし。`_DIRECT_SAFE_ALLOWLIST`への架空entry追加は不要 |
| manual build一覧 | `test_p3_build_authority_cli.py:159〜190` の2集合をplan:673が更新 |
| materializer閉包 | `test_s8b_floor_campaign.py:8014` の走査対象。plan:663〜683に登録と確認nodeあり |
| condition gate件数・fixture | plan:640〜650に39→40、15→16、cache22→23、fixture供給行まで記載 |
| IZANAGI_走査 | `test_p3_s4_loop.py:7936〜7969` はpatch全文を走査。新tokenを入れない案なら追加登録不要 |
| 軸SOURCE_REL表 | plan:456〜462に追記案あり |
| B-4 module数 | `test_p3_b4_wiring_probe.py:327` は47。走査はimport閉包（`p3_b4_wiring_probe.py:1083〜1101`）なので、新moduleの存在だけでは増えない |
| duration ledger | 未登録nodeは `conftest.py:1739〜1759` で未計測扱い。新test追加だけで全件pin更新は不要 |
| docs checker | `check_docs.py`にauditor.md・patches/README.mdの内容sha pinは確認できない |

**must-fix / should / nit:** **should**

**是正案 (逐語):**

> `test_axis_driver_source_rel_within_edit_surface` への追記は「追加してよい」ではなく実施対象にする。subprocess helperを複製した場合だけ、その実装差分に応じてsite inventoryを再点検する。B-4件数やduration ledgerを新ファイル数に合わせて機械的に更新しない。

## 所見 6: P5 は将来 consumer の実使用を証明しないが、plan はその限界を認めている

**real/refuted の判定材料:** **過大保証という懸念は plan について refuted、親 brief の表現には realな曖昧さ**。

plan:442は束縛関数と完成proof gateを分離し、454は「将来consumer導入時には実checkoutのOIDを渡すテストが別途必要」と明記。D2134 項6に適合する。

三対照の主体も異なる。別名template・別OIDは束縛関数が拒否し、literal定数は正しい値なら受理、patch検出はgate側の責務（plan:448〜452）。親brief:51の「直書きPIN→拒否」を表記形式の禁止と読むのは誤り。

**must-fix / should / nit:** **should**

**是正案 (逐語):**

> 本waveは束縛APIと対照を実証する。将来consumerが実際のcheckout・template・PINを渡してこのAPIを通ることは、consumer導入時に別途検査する。正しいOIDのliteral表記自体は拒否しない。任意の直書き経路の閉鎖は主張しない。

## 所見 7: P9 の cache route は mocc ownerで評価できる

**real/refuted の判定材料:** **Silo専用で評価不能という懸念は refuted（静的判断）**。

`condition_meaning_gate.py:862` のrequest生成、1696以降のconfigure処理、1795〜1815のowner/target選択はrequest由来。Silo固定定数を新経路へ持ち込む必要はない。plan:298の判断は妥当。

一意witnessも `condition_meaning_gate.py:2941` が要求しており、plan:630のcomment付き外側guardで重複を避ける。fixture追加もplan:650にある。

**must-fix / should / nit:** **nit（変更不要）**

**是正案 (逐語):**

> ROUTE_CMAKE_CACHEを維持する。実行失敗時にCXX_FLAGS経路への変更やmeaning省略で緑にせず、mocc owner・target・fixture・一意witnessの不整合を修正する。

## 所見 8: compute範囲は妥当だが、時間と生死確認のbuild数は区別する

**real/refuted の判定材料:** **1 jobで不可能という根拠はなく、保証扱いへの異議は real**。

wave 1 README:141はverifier合計607.6秒、最大54.8秒。完全JSONのstock12走を集計すると、benchmark約12.0秒、verifier約255.1秒だった。これは親brief:47の400〜600秒を否定しないが、新build・condition gate・identityを含む上限ではない。plan:324は適切に不確実としている。

plan:277〜285のcomputeは5 build。一方、731〜732の生死確認は記述どおりなら6 buildで、同じ数ではない。

DQ・consumer対照をcomputeでJSONへ記録し、pytestで独立期待値を検査する分担（plan:328）は妥当。追加benchmark走は不要。

**must-fix / should / nit:** **should**

**是正案 (逐語):**

> 3600秒はjob枠、600〜1200秒は未実測の計画値とする。生死確認6 buildと受入compute5 buildを区別し、生死確認は必要な組合せへ絞る。DQ・consumer・auditor定義はcomputeで実結果を記録し、pytestでは独立期待と拒否対照を検査する。

## 所見 9: 親の件数と plan の親批判に小さな事実誤認がある

**real/refuted の判定材料:** **real**。

- 親brief:14、27の「旧計装shaが12 fileにpin」は、HEAD `657e1e5a7` では短縮sha検索が**15ファイル**に一致した。ログ・README・receiptも含み、全部を機械pinと呼べない。旧bytes保持の結論自体は妥当。
- 旧計装sha `e9e65b78…`、auditor sha `a0912ebb…`、wave 1 JSON sha `c99aedb9…` は実bytesと一致。
- plan:829が訂正対象とする「親P4の七hunk」は、今回の親brief:50には書かれていない。
- scope外の探索driver・汎用台帳・broken-template版・verifier編集等はplanに見当たらない。設計§12の7成果物、§7末尾の6 check種、§9.2の3候補も対応している。欠落は所見1の機械要件の接続。

**must-fix / should / nit:** **nit**

**是正案 (逐語):**

> sha検索結果はHEAD・検索文字列・出現種別を付して記録し、歴史記録の出現数を機械pin数と呼ばない。「親P4の七hunkを訂正」は削除し、「計装版は六hunk・七復元点」と事実だけを書く。

## 総括

- **must-fix:** auditor-liveの機械証拠に、read-only契約と入力射影の構造検査を接続する。
- **pin閉包の漏れ:** planに新たな必須漏れは確認できない。親briefから漏れていた `condition_gate_test_support.py` はplanで補完済み。軸SOURCE_REL表の追記は実施対象として確定する。
- **P2:** 妥当。旧bytes保持と新JSONによる参照でよい。ただしsha鎖と旧check成立を別々に検査する。
- **P5:** planの限定つきで妥当。実consumer導入時の配線検査は未完であり、別途必要。
- **P6:** 発火条件は妥当。auditor検査は項目境界を持たせ、所見1の機械要件を補う。
- **親briefへの異議:** pin出現件数の一般化、literal PINを拒否するという表現、400〜600秒の扱いを修正する。P7・P9は妥当、P10はplan:738のrunner経由という限定を維持する。

HEAD確認と静的読解・メモリ上の照合のみ実施。ファイル変更、pytest、build、computeは実行していない。