## レンズ A

### must-fix

**M1 — 候補追加時の属性消失で、新実装だけが finding を取り落とす反例が残っています。**

- **根拠:** checker L2341–2350、L2503–2509、L2616、および段4裁定「論証」の「残る差」。D2045 は findings・rc・公開 record の等価性を要求しています。
- **成果物への影響:** 旧形と受領証なし oracle が rc=1 とする履歴を、新形が成功 prefix として再利用し、finding を欠落させて rc=0 にできます。
- **是正案:** 以下を実 Git の回帰テストにし、候補追加を許す条件を再設計してください。保証できるまでは候補集合一致へ戻す必要があります。履歴上の path を使った候補列挙の拡張は、scope 外の**裁定パッケージ候補**です。

静的に構成した反例は次のとおりです。実走はしていません。

1. `_attribute_merge_repo` と同じ、離れた行の変更を統合した Claude author の merge M を、`tools/retired/shared_lines.py` に作る。
2. Codex author の commit A で、その directory の最後の tracked path を削除する。
3. A の監査前に、以下の untracked 属性を置く。
   - root `.gitattributes`: `tools/retired/shared_lines.py -diff`
   - `tools/retired/.gitattributes`: `shared_lines.py diff`
4. directory 内の属性が root の指定を上書きするため、M の combined patch は既存 fixture と同じ空の text diff になる。A の全史監査は成功し、受領証を発行できる。しかし nested 属性は候補外なので fingerprint に保存されない。
5. 子 commit B で `tools/retired/README.md` を追加し、nested `.gitattributes` を削除する。root 属性は保持する。

この遷移では、保存候補 ⊂ 現在候補、新候補の現在状態は absent、実在 entry の digest は一致します。したがって新実装は A を再利用します。一方、B の全史監査では root の `-diff` が M に作用し、既存負例と同じ Codex author 欠落を検出します。旧形は候補追加によって失効し、この違反を検出します。

段4の集合論証が証明するのは「**列挙された状態表の差**が absent 候補の追加だけ」ということです。「Git が読む属性入力も同一」は導けません。段4自身が記載するこの差を「既存限界」と分類しても、旧実装との判定差は解消しません。

### should

なし。

### nit

なし。

### その他の検査結果

- **実装と patch:** 適用済み2ファイルの blob hash は patch の適用後 hash と一致しました。変更関数・7テスト関数・破損20ケースは author 報告と一致します。
- **除外条件:** L2345 は `{"kind": "absent"}` との厳密比較です。unreadable、directory、symlink、regular の読取失敗は残ります。
- **候補の復号:** 文字列型、base64、zlib、空要素、重複、sorted、末尾形、包含を検査しています。指定された不正形式は再利用されません。
- **相談AのM1:** `test_attribute_retired_directory_falls_back`（L8296以降）は候補脱落＋untracked 属性出現を再現し、digest 同一・候補減少・merge finding・全史1回を検査しています。oracle helper は受領証を削除し、rc と stdout／stderr を比較します。今回の逆方向の反例は未被覆です。
- **schema／保存:** schema=2、key 集合、候補保存は追従済みです。旧 schema は通常別 partition になり、現 partition に残っていても再利用検査で拒否されます。prune は schema を見ないため残留・有効受領証の淘汰はありえますが、誤受理にはなりません。通常の保存失敗から全史を追加実行する経路もありません。
- **全 caller:** `rg -n --hidden -g '!.git' '_receipt_bindings' .` の結果、実呼出しは **2箇所**（L2446、L2593）で、双方3値へ追従済みです。ほかは定義1箇所、例外を投げるテスト stub 1箇所、文書・計測記録3箇所。land／wait を含め、取り残された caller は見つかりません。
- **不変部分:** 属性候補取得に監査 tip の tree 読取りは追加されていません。dispatch 判定、partition の構成方法、公開出力の生成コードは変更されていません。ただし、上記M1によって出力内容の等価性は崩れます。
- **報告と実走:** author の「pytest 未実走」と、後続の親 log の **2738 passed／5 skipped、rc=0** は矛盾しません。変異対応表は静的予測として整合しますが、log は変異 kill の証拠ではありません。probe は所有 path 限定 patch に含まれず、その実装内容は本検査では未確認です。

## 総括

**NO-GO — must-fix 1件。**

plan v2 への実装追従は確認できましたが、plan v2 自体に旧実装との判定差が残っています。静的検査のみで、pytest・変異実走は行っていません。