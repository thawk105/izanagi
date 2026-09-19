## 総括

**現状の plan は差し戻しを推奨します。** 特に、統合参照の自己証明、退避の完全性、manifest の世代束縛、撤去中の再起動が未解決です。一方、index／reflog 退避の追加、単一参照との tree entry 比較、既存 wave mode からの分離は妥当です。

静的検査のみ実施しました。ファイル変更・pytest・撤去・変異の実走はしていません。

以下、`plan.md` は[段2起草](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/artifacts/dev-wave-t2778-child-worktree-cleanup/plan.md)、`brief.md` は[親brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/brief.md)、`materials.md` は[射影資料](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/materials.md)を指します。

1. **対象: plan §3／brief (P1) / 重大度: must-fix / 任意 integration-ref が統合証明を恒真にする**

   **根拠:** `plan.md:91`、`:119`、`:124`、`:128`、`brief.md:58`。

   **失敗入力:** 未統合 author の現在 HEAD を `--integration-ref` に渡す。B は所有 path 全部について自己比較となり、必ず成立する。通常の直線履歴なら A も成立する。SHA 形式の検査だけでは防げない。

   **最小修正:** 追加参照を manifest の親 wave と検証済み landing 情報に束縛する。段9専用なら、追加 SHA の main 到達可能性も要求するのが単純。単に「子 HEAD と異なる」だけでは、子の子孫 SHA を渡せるため不足する。

   main のみなら land 前の未統合変更は原則拒否される。ただし既に内容が一致する子は通るので、**統合判定は land 完了判定の代用にならない**。

2. **対象: plan §3–4／brief (P1)・不変条件3 / 重大度: must-fix / patch と未追跡 tar だけでは作業木の bytes を網羅しない**

   **根拠:** `brief.md:48`、`:50`、`plan.md:141`、`:149`、`:154`、`:194`、`:196`。

   **失敗入力:** tracked file に `assume-unchanged`／`skip-worktree` を設定して内容を変更する。Git 差分だけを保存すると、その作業木内容を見落とし得る。clean filter や改行正規化がある場合も、Git 表現の patch は作業木の生 bytes と一致する保証がない。空 directory は `ls-files` に現れない。

   **最小修正:** index の path・stage・mode・OID と、filesystem の path・種別・mode・生 bytes を独立に列挙する。patch は補助とし、差分に現れない tracked 内容も復元可能な形で保存するか、その状態を拒否する。空 directory の保存／非保存も明記する。

   brief の5点退避では、さらに「stage 後に作業木だけ元へ戻した内容」「reset 前の HEAD reflog 履歴」が落ちる。plan の `index.patch`／`history.pack` 追加は必要である。通常の削除・rename・実行 bit・symlink は二つの patch で表現可能だが、未解決 stage は明示拒否を維持すること。`ls-files -o --exclude-standard` は ignored を落とすため使えない。

3. **対象: plan §3／brief (P1) / 重大度: must-fix / clean submodule にも消える履歴がある**

   **根拠:** `plan.md:150`、`:154`、`:182`、`tools/dev_wave_cleanup.py:979`、`:989`、`:998`。

   **失敗入力:** submodule 内でローカル commit を作って元の pin に reset する。superproject と submodule の作業木は clean でも、その commit は子 admin 配下の submodule reflog／object store にしか残らない場合がある。superproject の `history.pack` は gitlink の先の object graph を保存しない。submodule 内 ignored file も、superproject の未追跡列挙では網羅できない。

   **最小修正:** 「dirty submodule の拒否」だけでなく、再帰的な作業木・ignored・refs／reflog と、削除される object store の保存先を検査する。救出を実装しない範囲は rc20 で保持する。T-2777 の hardlink 許容は共有 object の unlink 安全性であり、全 object の別コピー存在証明ではない。

   所有外 committed 内容は、現在 tip が生存 branch から到達可能なら branch 残置で保持できる。しかし detached／reset 前履歴まで含む一般則にはできず、plan の追加 pack が必要になる。

4. **対象: plan §2／brief (P2)・(P4) / 重大度: must-fix / exact path は作成世代を識別しない**

   **根拠:** `plan.md:42`、`:44`、`:77`、`:107`、`tools/dev_wave_cleanup.py:374`、`:404`。

   **失敗入力:** 旧子木を撤去した後、同じ path・branch 名で別用途の worktree を作る。旧 manifest を回収 wave が渡すと、現在の実体との照合は通り得る。既存 `_assert_identity` は今回の preflight 以降の交換を検出するもので、登録時の実体との同一性は証明しない。

   **最小修正:** entry に登録世代と admin／directory の identity を束縛し、同 path の再登録は同一世代の更新か、新世代への明示切替かを区別する。旧 branch・旧証拠の所在も残す。単純な entry 置換では、旧 entry の所有情報が消え、旧 branch と証拠だけが取り残される。

5. **対象: plan §2・§3／brief (P1)・(P2) / 重大度: must-fix / 所有集合の完全性が機械的条件になっていない**

   **根拠:** `plan.md:74`、`:75`、`:77`、`:126`、`:131`、`materials.md:308`。

   **失敗入力:** 所有 file `old.py` を `new.py` に rename したのに、owned_paths は `old.py` のみ。親側が `old.py` の削除だけ取り込むと、双方不存在で B が成立し、`new.py` の採用を検査しない。同様に、不一致 file を再登録時に所有集合から外せば判定を弱められる。

   **最小修正:** 所有契約の変更を単なる再登録と分離し、rename の旧新両端、削除 path を所有集合に含める。前世代からの縮小は通常 CLI では拒否する。

   `base_sha` は「HEAD の祖先」だけでは作成 base の証明にならない。登録時 HEAD／所有抽出の base と束縛すること。ただし、親の統合後には現在の merge-base が進み得るため、現在の merge-base との無条件一致を要求する修正も誤りである。

6. **対象: plan §2／brief (P2)・(P4) / 重大度: should / manifest の整合性と所有権限を混同している**

   **根拠:** `plan.md:38`、`:70`、`:81`、`:86`、`brief.md:65`。

   **失敗入力:** 同じ common gitdir の別 wave の有効な manifest と、その登録子 path を渡す。remove CLI には期待する所有 wave がなく、「誤った manifest」なのか「意図した旧 wave 回収」なのかを区別できない。header の wave path を別の有効 worktree に変更すれば、元 wave 本体も「header の wave ではない」対象になる。

   **最小修正:** caller が期待する owner/job identity を明示し、通常の自己撤去と旧 wave 回収で照合する。manifest 全体を整合的に偽造する同一権限主体への防御は署名なしでは成立しないため、manifest の信頼境界を明文化する。「手書き変更なら拒否」という一般化は削る。

   相対 path・末尾 slash・symlink component は既存 `tools/dev_wave_cleanup.py:165` の検査で拒否可能。別 common、primary、header の wave も設計上拒否される。大文字小文字は勝手に同一視せず exact record と照合し、case-insensitive filesystem を支援するなら inode による別名重複検査も必要。

7. **対象: plan §3／brief (P4) / 重大度: must-fix / 占有再検査は再起動を排他しない**

   **根拠:** `plan.md:79`、`:109`、`:154`、`:168`、`tools/check_worktree_occupancy.py:4`、`:8`、`tools/dev_wave_cleanup.py:1230`。

   **失敗入力:** 最後の occupancy／内容再照合直後に launcher が子を再起動し、`shutil.rmtree` 中に新しい file を書く。その bytes は退避に含まれず削除され得る。manifest の flock と admin の flock は、それを取得しない launcher を止めない。

   **最小修正:** 段9の前提を「現在の job が終端した」から「当該世代の producer が終端し、再投入を止めた」へ具体化する。協調する起動経路と撤去経路で同じ排他を保持するか、排他を保証できない対象は保持する。再走査だけで TOCTOU 解消とは書かない。

   D705 の継承自体は妥当。既存 scanner は消滅 PID／zombie を区別し、`_assert_unoccupied` は最大3回の再試行と payload 整合検査を持つ（`check_worktree_occupancy.py:408`、`dev_wave_cleanup.py:484`、`:521`、`:529`）。子 mode でもこの関数をそのまま使い、mutation 後の失敗は rc30 に包むこと。

8. **対象: plan §6–7／brief (P3) / 重大度: should / node 名はあるが、単独で変異を殺す入力条件が不足している**

   **根拠:** `plan.md:230`、`:241`、`:249`、`:260`、`:268`、`:274`、`:275`。

   **失敗入力:** 正例は wave へだけ取り込む説明で、main への land または有効な追加参照が明示されていない。判定不能負例も、何を実体として判定不能にするか未定義。realpath 検査の変異は、別の path 検査や record 不一致で引き続き拒否されれば生き残る。

   **最小修正:** 各 node に、実 repo 状態、唯一の拒否理由、到達 phase、非変更 assertion を記載する。正例は land と参照を明示する。履歴退避は同じ common に依存せず、独立 repo へ pack を復元して検査する。backup 全省略だけでなく、index・ignored・reflog の各省略を個別に殺す node を足す。

   F649 に沿った実 CLI／実 Git の方針はよい。ただし「実 scanner の node を別に用意」だけでは、主正例自体の占有経路が stub でない証明にはならない。hardlink／admin binding の負例も子経路へ追加する必要がある。

9. **対象: plan §3・§9／brief (P4) / 重大度: should / 回収時の欠落 entry と partial の扱いが未完**

   **根拠:** `plan.md:102`、`:154`、`:168`、`:298`、`brief.md:65`。

   **失敗入力:** 子 A 撤去成功後、子 B の backup 中に中断。次回 manifest 順に再実行すると、A は record 不在で拒否、B は証拠 dir 非空で拒否する。rc30 を報告する契約はあるが、回収 wave がどう先へ進むか未定義。

   **最小修正:** 世代に束縛した成功記録から既撤去 entry を識別するか、回収対象を明示選択する手順を記す。partial は証拠を上書きせず、停止 phase と残存物を照合する。退避不能 submodule 等は backup 開始前に検査し、「rc20 保持」と「書込み後 rc30」の境界も揃える。

   子→wave の順序自体は正しい。通常は wave branch が子撤去中に残る。旧 manifest 回収では既に wave branch がない場合があるため、旧 branch 名ではなく main 到達可能な固定 SHA と残存 job dir が必要になる。

10. **対象: plan §9／brief (P6) / 重大度: must-fix / D2148 の不整合指摘は誤り**

    **根拠:** `plan.md:300`、`:314`、`:320` に対し、`materials.md:35` と `docs/decisions.md:67496` はともに「残置領域の恒久的な削除権限は広げない」、対象 T-2778 と記す。

    **失敗入力:** plan を信じて親が supersede 先を T-2051 関連へ変更する。

    **最小修正:** この所見と総括の「D2148参照が不整合」を撤回する。brief の参照と P6 の遅延採番方針を維持する。

11. **対象: brief (P5)／plan §4・§8 / 重大度: should / 既存契約維持の条件を brief へ戻す**

    **根拠:** `brief.md:66`、`plan.md:177`、`:183`、`:282`、`orchestrator/tests/test_check_docs.py:9488`、`:9686`。

    **失敗入力:** DW-O28 を「1000 bytes 以下」で書き直すが、989 bytes ではない。既存 assertion が赤になる。

    **最小修正:** P5 を「989 bytes と既存置換文字列を維持」へ修正する。既存 `_parse_argv` の8/10固定、`_classify`、`_mutate` を残して手前で dispatch する方針は成立可能。allowlist の追加も既存禁止形とは衝突しないが、新 pack helper は旧 `_git` spy の外なので専用検査を足す。

    旧 collection node 名は `test_pytest_collection_config.py:388`、file path は `test_selection_contract.py:40` に固定されており、維持が必要。

**裁定パッケージ候補（scope 外）:** 所見7の一般的な lease／起動排他は、既存 scanner 自身が scope 外と明記する未解決面です（`tools/check_worktree_occupancy.py:10`）。本 wave では producer 終端・再投入禁止という運用前提を具体化し、全起動経路を覆う恒久 lease は別裁定に分けるべきです。

`-s ours` の代案については plan の比較が妥当です。子 tip の履歴を main に保持でき、blob 判定と branch 残置を減らせますが、内容採用は証明せず、不採用履歴まで main に残します。reset 前 reflog、index、dirty、submodule の救出も別途必要で、今回の退避問題を単独では解決しません。