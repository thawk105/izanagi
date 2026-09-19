## 実装と保存値の経路

指定の7ファイルを `tools/t_witlight/` に作成し、untracked のまま残しました。

正常完走・同じ採取結果について、witness on のとき S 行は unlock 後に同順・同値・同件数で出ます。
witness off のとき TLS vector の構築・clear・reserve・decode・push・S 出力は実行されません（ポインタ初期化と分岐は残ります）。

[W.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/witlight-author/tools/t_witlight/W.patch:39) の保存値の鎖は次のとおりです。引用は順に patch の39〜41行、54〜56行、13行です。

```diff
+      if (!izanagi_mocc_g2_decode((*itr).rcdptr_->body_, stored_producer))
+        std::abort();
+      izanagi_stored_producers->push_back(stored_producer);
```

```diff
+      izanagi_mocc_g2_emit_post_store(
+          thid_, izanagi_txid, we, maxtid,
+          (*izanagi_stored_producers)[stored_index++]);
```

```diff
+                                     std::uint64_t stored_producer) {
```

helper は、その引数を既存の不変行で出力します。この行は変更していないため、`+` 行ではありません。

```cpp
      << version.tid << ' ' << stored_producer << '\n';
```

共有 body の decode → vector → unlock 後の添字読出し → helper 引数 → S の第5値、という経路であり、writer txid へ置換する経路はありません。これは静的確認で、runtime 不一致注入は未実施です。

通る正例は、smoke の on arm で実在する write に対し **S 件数＝W 件数**、identity Counter 一致、各 identity 1件、保存 producer 一致となる場合です。実 smoke は未実走です。verifier／discriminator の受理・拒否条件は変更していません。

## 配置上の限定

測定 patch の `#line` は plan §3 の指定位置に置きました。`1136` は TRACE 内ですが、`115/1201/1208` は TRACE 外です。そのため「4指令すべて TRACE=0 で inactive」とは報告できません。X/P の既存指令は保持しています。

合成 source は TRACE=1 の観測専用で、性能値には使用しません。異常終了時の出力 prefix 同一性、旧 off binary との同一性は保証していません。

## 総括

成果物の行数・SHA256 は以下です。検査用資材は同ディレクトリの `scratch/` に残しています。

| ファイル | 行数 | SHA256 |
|---|---:|---|
| `W.patch` | 63 | `4ef9c387068abf9dcdd123ba87691b4d613cdb36fff9c541448c147367095aff` |
| `witlight.patch` | 76 | `0648e2c6de46319da02056cb516d706ff9f09c3c0ffb2cadb6c94ee069473363` |
| `arms-witlight-node1.json` | 50 | `ba74088785f3ffcaf708166608c04d5f087b00cd28018f50587566022f9bcd30` |
| `arms-witlight-node2.json` | 50 | `f5e802236d0047125548490553cd34ffc06153f89ef5b85219cb5da94d146245` |
| `arms-witlight-node3.json` | 50 | `8db96f217db2f84af10b7fd3490df01cdd45e7ffc3115d2e851c80af5818b355` |
| `arms-witlight-node4.json` | 50 | `ab0e84b28b7d9db402ddfbc4d183c362687cd7f6fc9f671d20749a9bcf1fefca` |
| `smoke_capture.py` | 109 | `65017778972c7dcab6b5bdd0da801da11fb7e923e1075d9755101ff90446bc55` |

実走結果：

- **4系列すべて成功**：W 単独、X/P 単独、X/P → witlight、W → X/P。各段の `git apply --check` と適用は rc=0。
- **同内容性**：両辺から `^#line` 行だけを除いた `cmp` は rc=0。
- **touch set**：各 patch は `cc/mocc/transaction.cc` 1本。X/P SHA256 は指定値 `e9e65b78…` のまま。
- **W の境界**：`grep -n '^#include'` 完全一致。全変更を目視確認し、TRACE ブロック外の bytes 一致も確認。include 追加・`#line`・X/P 混入なし。
- **JSON**：Python 3.10 で4本とも読込み成功。object 集合一致、順序は ABCD／BCDA／CDAB／DABC。
- **wrapper**：`--help` rc=0。偽 command による verifier 限定複製、witness 有無、原本保持、manifest 追記・件数・bytes・SHA、引数・返値・例外の維持、一度だけの委譲、複製失敗時の例外を確認。CLI 委譲と runner `__file__` 維持も確認。
- **runner**：無変更・指定 SHA 一致。`selftest: PASS 21/21 cases`。
- **未実走**：pytest、compute、build、実 smoke／本走、OID identity 2本、binary identity、runtime 保存値不一致注入。
- **所有外への波及**：無し。tracked／index 差分なし。submodule 非接触、add／commit 等は未実行。
