## 所見

**S-1 — blocker：親 brief の「対象集合が同じなら被覆等価」は成立しない。**

- **根拠：** `brief.md:62–64,81`。判定へ渡る値が変わる箇所は `plan.md:17–27` の出力・改行・decode と、`:44–47,58` の格納値の注入。現行では `tools/check_ai_provenance.py:1908–1910,1926` が取得値を label と判定へ渡す。
- **構成反例：** trailer 欠落の docs commit A と `AI-Agent: none` の docs commit B を選ぶ。取得辞書が両方の OID を保持しながら、A に B の message を割り当てれば、対象集合・件数・順序・NUL 数・OID 検証はすべて一致しても A が拒否から受理へ動く。
- **区別：** これは「対象集合だけによる証明」への反例であり、plan の実装に取り違えを発見したという意味ではない。plan の **OID ごとの文字列比較**（`:92–97`）は、この穴を塞ぐために必要である。brief の自明性・証明免除の主張は撤回すべき。

**S-2 — should-fix：同じ改修後コード内の differential test は、共通の判定弱体化を検出できない。**

- **根拠：** `plan.md:150–158`、`orchestrator/tests/test_check_ai_provenance.py:6891–6900`。取得・ancestry は切り替えても、判定と集約は共有する。
- **構成反例：** 共通処理で scope findings だけを落とすと、旧取得側・一括取得側が同時に変わる。別の findings、correction、waiver が残れば、既存の非空 assertion と新旧比較は通りうる。scope 違反だけの履歴は拒否から受理へ動く。
- **限界：** これは当該比較単独の穴であり、既存テスト全体が通るとの主張ではない。単純な accept-all は `baseline.findings` の非空検査で、reject-all は既存の rc=0 固定期待値（例 `:3771–3782`）で捕捉される。
- **修正：** 正常・各違反の固定期待値を残し、比較対象の rc が実際に `{0,1,2}` を含むことを明示する。変更前コードを独立に走らせる `plan.md:175–184` は削らない。

**S-3 — should-fix：変異 #3・#4 は、記述された変更だけでは受理集合を動かすと断定できない。**

- **根拠：** `plan.md:194–204`。
- **静的反例：**
  - **#3：SOH 区切りへ変更。** 本文 SOH が framing 検査を壊しても、全件 fallback が保たれれば旧取得へ戻るため、受理集合・公開出力は維持できる。
  - **#4：検証を省いて部分結果を採用。** 欠落 OID を `.get()` で取り、`None` なら旧取得する実装では、欠落だけで違反 commit を見逃すとは限らない。
- **受理集合への影響：** 誤った message を既存 OID に注入すれば拡大・縮小しうるが、単なる検証削除とは別に、その発火を示す必要がある。
- **修正：** 「どの入力を旧実装が拒否し、変異実装が受理するか」を具体化する。fallback による意味保存、取得文字列差、公開出力差、構造 pin を分けて記録する。#2・#8・#9 の区別は妥当。

**S-4 — should-fix：`%s` の境界 fixture を具体的な bytes で固定する必要がある。**

- **根拠：** `plan.md:125–147` は複数行 subject を含むが、先頭空行、空白だけの行、先頭 TAB、message が `b"\n"` だけの場合を明記していない。
- **実測：** 現物 `a3168d8552d4…` の先頭段落は次の形だった。

  ```text
  …handoff\n  を撤去して…
  ```

  Git `%s` は `…handoff   を撤去して…` を出す。継続行の先頭2空白を保持し、連結用の1空白を加える。「空白をすべて1個へ畳む」ではない。
- **受理集合への影響：** subject の誤処理だけなら通常は label・公開出力差だが、message と共通の正規化処理にすると trailer の位置や値まで変えうる。
- **判定：** plan は Git `%s` と既存どおりの `.strip()` を使うため、現時点で不一致は反証できなかった。上記未実測形状の exact な結果を推測で期待値にしないこと。

## 親 brief への攻撃

### 「mismatch 0」は母集団を越えた証明ではない

`brief.md:22–23,81` は、現在の履歴・設定で一致したことを示すにとどまる。さらに、**今回の Git では、依頼文が示唆する config 由来の差も再現しなかった**。

Git **2.34.1**、実 commit `2a4b5d682997…` に対して、次を `git -c` で渡して比較した。

```text
trailer.inject.key=AI-Agent
trailer.inject.cmd=printf invalid
trailer.inject.ifexists=replace
```

`cmd` を `command` に替えた場合も、`--parse` と `%(trailers:only=true,unfold=true)` は元の AI-Agent 値を返した。`trailer.separators=%` と key の改名も、双方に同じ変化を起こした。

したがって、**「公開 option に `--only-input` 相当がない」ことから、自動追加・置換が起こると断定してはいけない**。一方、この小さい実測で全設定の等価性も証明できない。plan の parser 維持（`:64–72`）は妥当である。

差を探すための具体的な commit message 候補は次である。

```text
subject

---

AI-Agent: none
```

この bytes に対して、`interpret-trailers --parse` は空、`--parse --no-divider` は `AI-Agent: none` を返すことを実測した。**pretty 側を含む合成 commit での差は未確認**であり、完成した反例とは報告しない。親は raw object fixture で確認すべき。この形の divider と AI-Agent を持つ現物候補は HEAD 到達履歴にはなかった。

### 「commit object に NUL が入らない」は前提にできない

Git object の表現自体から message の NUL 不在は導けない。通常の commit 作成経路による制約と、raw object を扱う監査の入力域は別である。

`brief.md:75–76` の前提を採らず、`plan.md:105–111` が追加 NUL の検知・fallback と pretty の切詰め確認を要求した点は正しい。ただし、現物で NUL が0件だったことは malformed fixture の代用にならない。

## 反証できなかった点

**現物確認：** HEAD `0600887d92538b3f34d894f9674d202d0a29a578` の到達 **10,443 commits** を、raw object の長さに従って読み取り、plan の件数を独立に確認した。

| 形状 | 確認結果 |
|---|---|
| 空 message／1 MiB 以上 | ともに0件 |
| raw message の非 UTF-8／`encoding` header | ともに0件 |
| NUL／SOH／CR／CRLF | すべて0件 |
| merge／root | 3,399件／1件 |
| 複数行の先頭段落 | 1件、`a3168d8552d4…` |
| 最大 message | 6,410 bytes、`c170bee925d0…` |
| 末尾 LF | 1個が10,441件、2個が2件 |

- 現物の複数行 subject について、plan の一括コマンドと旧 `%s`・`%B` の文字列は一致した。
- 明示 LF を **decode 前**に置く設計は、末尾 CR と text mode の改行正規化の順序を考慮している。ここに静的な破綻は見つからなかった。
- 正常な各 record が必ず3個の区切り NUL を出す条件では、本文中の追加 NUL は総数を増やす。全件検証後だけ採用する設計を、単純な区切り注入では崩せなかった。
- D908 の監査回数削減、D274 の定数上限引上げ、D254 の land 関門迂回に、**現 plan が該当する証拠はない**。ただし、対象集合の維持だけで D908 の等価性要求を満たしたとは言えない。
- ファイル変更・commit・pytest・全史監査は実行していない。以上の確認を受入テストの緑とは扱わない。

## 総括

最も危険なのは、親 brief が「対象集合の一致」を「受理集合の一致」に読み替えている点である。  
現 plan はその誤りをかなり補っており、取得設計自体の確定的な blocker は発見していない。  
親は固定 HEAD・OID 列・設定の下で、**独立した変更前コードと変更後コードの OID ごとの subject/message、CommitAudit、HistoryAudit、CLI bytes・rc**を比較すべき。  
現物にない NUL・encoding・divider・空白境界は raw fixture で別に測り、fallback を含む結果を記録すること。  
変異 #3・#4 は、具体的な旧拒否→新受理の証拠なしに「受理集合差を KILLED」と報告しないこと。