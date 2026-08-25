# 段 6 レビュー裁定 — [T-1697]

review A (裁定契約の充足と gate の実効性) 12 件、review B (テスト検出力と報酬ハック面) 10 件。
**20 件を real、2 件を「閉じられない性質」として非採用**とする。両レビューとも「採用不可」。
fix 1 単位を Codex `role=fix` へ投じる (編集面が同じ 2 file なので一枚岩。理由はこの行)。

もっとも重いのは review B の所見 1 である。**off controller の `reflux` を `True` にする 1 行変異が
全 test をすり抜ける。** 本 wave が閉じようとしている当の性質が、テストで固定されていない。
私が段 4 で登録した M1〜M15 にもこの変異が無かった。登録の穴でもある。

---

## 採用する fix (R1〜R12)

### R1 — pair 検査は terminal receipt の bytes を読んで再検証する (A2, A4, B2)

現状の `assert_b4_arm_pair` は自由に構築できる dataclass を受け取り、`evidence_class=="certified"` の
**文字列だけ**を出自の証明に使っている。test 自身が `replace(..., evidence_class="certified")` で
test-only receipt を昇格させ、それを正例 P4 にしている。

- pair 検査の入力は **terminal receipt の file path** とし、bytes を読んで schema・`status`・
  各 hash を再計算・再照合してから比較する。
- sealed factory は `pair_id` を生成して両 receipt へ焼き、pair 検査で equality を要求する。
  別 factory 由来の on/off 混成を拒否する。
- test-only receipt の certified 昇格を**負例**にする。P4 の正例は certified pair 実体で作る。

**成果物影響:** 未是正なら捏造 receipt と別 block の混成が certified 受理集合へ入る。

### R2 — certified mode は executable を呼び手に選ばせない (A1, B3)

certified mode では caller の `executable` を**無視**し、固定名 `claude` を PATH から解決する。
解決後の絶対 path と sha256 は receipt の evidence へ残す。CLI の `--claude-executable` は
certified 経路から外す (test-only 経路にだけ残すか、削除する)。

**非保証として明記する:** PATH に置かれた binary の同一性は認証していない。
同一 process 内のコードが Python レベルの検査を無効化できることも同様に閉じられない
(review A 所見 1 後段の module global 書換えはこの型であり、**閉じられない性質として非採用**)。

**成果物影響:** 未是正なら critic を一度も実行していない block が certified になる。

### R3 — off アームが赤を受け取らないことをテストで固定する (B1) ★最重要

pair を実際に invoke する test で、**実際に送られた payload を捕捉**し、各 admitted view から
独立に再計算した on / off digest と **byte 比較**する。off payload に fixture 固有の赤 marker
(`b4-fixture-reject` 等) が現れないこと、on には現れることを対で固定する。

段 4 の変異登録に **M16「off controller の `reflux` を `True` に変える」** を追加する。期待は KILLED。

**成果物影響:** 未是正なら off 汚染 block が certified 受理集合へ入り、アーム帰属が偽になる。

### R4 — tool-surface の負例を 3 本へ分ける (A10, B4)

現状の負例は `permission_denials` 非空・`num_turns=2`・`server_tool_use>0` を**同時に**壊しており、
provider の検査順のせいで後ろ 2 つの検査を削除しても緑のままになる。
1 field だけを壊し他は正常値の負例を 3 本に分け、例外の理由まで固定する。
複合負例は裁定どおり別に残してよい。空 `server_tool_use` dict が `all()` で真になる件も明示する。

**成果物影響:** 未是正なら後ろ 2 gate の退行が無検出になり、tool 使用のある block が certified になる。

### R5 — hash chain を独立に再計算して exact 比較する (B5)

現状は「長さ 64」や「両アームで異なる」しか見ていない。fixture の WAL bytes・loop state bytes・
捕捉した argv・送信 digest・start receipt bytes から**期待 hash を test 側で独立再計算**し、
receipt の値と exact 比較せよ。

**成果物影響:** 未是正なら別 snapshot・別 digest が同じ block に束縛される。

### R6 — 「fold しない」の検査を実経路で行う (B6)

test 内で作った `LoopState` は controller に渡らないので、現在の不変 assert は恒真である。
invoke 前後の**実 loop state bytes** を比較し、campaign root と artifact root に proposal や
checkpoint が新設されないことを確認せよ。`co_names` の blacklist は補助へ降格する。

**成果物影響:** 未是正なら `prior_critic_reverse` と停止理由が変わり、標本数が変わる。

### R7 — CLI を実際に駆動する test にする (B7)

現状は callable であることと文字列 `def main(` しか見ていないため、`main()` 冒頭を `return 0` に
する変異が生存する。factory を差し替え可能な seam にして `main()` を呼び、2 回の invoke・
pair 検査・terminal receipt path を含む stdout・失敗時 rc=1 を検査せよ。

**成果物影響:** 未是正なら閉じた route が到達不能でも「利用可能」と扱われる。

### R8 — closure manifest に実依存を足す (A7, B9)

manifest が裁定の列挙 6 項だけで、payload や閉鎖挙動を変える直接依存が外にある。
少なくとも `artifact_admission.py`、`s8b_prediction_runner.py`、`role_session_isolation.py` を足す。
test 側は expected key から実 path/contract bytes への対応表を**独立に定義**し、
全 entry を再計算して exact 比較する (末尾の「変えた dict の hash は違う」という数学的恒真検査を
それに置き換える)。

**成果物影響:** 未是正なら意味の違う projection が同じ群へ併合される。

### R9 — path tokenizer の偽陰性と escape view の偽陽性を直す (A8)

`_PATH_TOKEN_RE` が空白で path を分断するため、引用された path 中に除去可能な空白 component を
入れた alias が正規化を免れる。逆に、JSON decode 済み leaf 中の文字どおりの `\uXXXX` を再 decode
するため、escape を説明しているだけの digest を誤って拒否しうる。
JSON string leaf 全体を引用符込みで扱う tokenizer にし、残存 escape の扱いを明文化せよ。
空白 alias の負例と、「escape を説明するだけ」の正例を対で足せ。

**成果物影響:** 前者は開示 block を受理し、後者は正当な digest を受理集合から落とす。

### R10 — exact schema の型・値 gate に 1 field ずつの負例を足す (B10)

`reverse_recommended=1`、各文字列 field の非 str、空 digest、未知 `result` を 1 field ずつ変えた
負例を足し、例外メッセージも固定せよ。

**成果物影響:** 未是正なら malformed な decision/outcome が成功 receipt に束縛される。

### R11 — terminal receipt の必須性 (A9)

start receipt の書込みを `try` の内側へ入れ、terminal slot を query の**前に**排他予約する形にせよ。
storage failure まで保証できないなら、**その限界を非保証として明記**せよ (恒真な保証にしない)。

**成果物影響:** 未是正なら失敗 query が台帳から欠落する。

### R12 — 表示を実装に合わせて縮小する (A11, B8)

- module docstring の "seals" と "same stable snapshot" は R1〜R5 を入れた後の実力に合わせて書く。
- 「report されない・local な tool 使用を証明しない」ことを非保証 field に足す。
- fixture の呼称を「real admitted fixture」から **policy-admitted synthetic WAL fixture** へ縮小する。
  `# rejections` の見出しは赤が空でも renderer が常に出すので、赤到達の証拠に数えない
  (fixture 固有 marker の on 出現 / off 不出現で固定する — R3 と同じ検査)。
- 親 brief の成果物影響を裁定 A12 の文へ更新する (**親がやる**)。

**成果物影響:** 未是正なら材料レポートの参照説明が実装以上の証明を主張する。

---

## 非採用 (2 件)

- **A1 後段の module global 書換え** (`_CERTIFIED_RUNNER` / `REPOSITORY_ROOT` を同一 process から
  差し替えられる)。**閉じられない性質**である。同一 process の Python コードは任意の検査を
  無効化できる。R2 の非保証文で正直に書き、gate の根拠にしない。
- **A5 の WAL / loop state の論理世代束縛。** 実現には `p3_s4_loop.py` の loop state へ epoch か
  WAL prefix hash を書き込む必要があり、本 wave が「切替点と venue を触らない」と定めた
  不変条件に反する。**scope 外 → 裁定パッケージ (B6 として追加)。**
  本 wave では「byte 安定性は読取中の不変性しか示さず、進んだ WAL と一世代古い loop state の
  組合せは受理されうる」ことを非保証として明記する。

---

## 変異事前登録の改訂 (DW-M01 の再照準)

review A 所見 12 のとおり、**M6 / M7 / M8 / M9 / M11 は単一理由でない** (後段 pair gate、
前段 tracker/factory、構築側 exact schema、別 view に mask される)。
DW-M01 の「確認できなければ登録せず実効 gate へ再照準する」に従い、**この 5 件を登録から外す。**

**追加する変異:**

|#|変異|期待|
|---|---|---|
|M16|off controller の digest 生成を `reflux=True` にする|KILLED (R3 の byte 比較 test)|
|M17|pair 検査から `pair_id` equality を外す|KILLED (混成 pair 負例)|
|M18|certified mode の executable 固定解決を caller 値に戻す|KILLED (偽 executable 負例)|
|M19|pair 検査を terminal receipt 再読でなく dataclass 受理に戻す|KILLED (昇格 receipt 負例)|
|M20|closure manifest から `artifact_admission` entry を落とす|KILLED (対応表 exact 比較)|

改訂後の登録集合は M1〜M5、M10、M12〜M20 の 15 件。正例は P1〜P4 (P4 は R1 に合わせて
certified pair 実体で作り直す)。
