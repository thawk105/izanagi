## 攻撃面 1〜7 の所見

以下の略記は repo root 相対です。

- **HF**：`orchestrator/campaign/s8b_holdout_freeze.py`
- **T**：`orchestrator/tests/test_s8b_holdout_freeze.py`
- **FX**：`orchestrator/tests/s8b_v2_freeze_fixture.py`
- **FC**：`orchestrator/campaign/s8b_floor_campaign.py`
- **CT**：`orchestrator/campaign/s8b_floor_contract.py`
- **HA**：`orchestrator/campaign/s8b_holdout_admission.py`
- **FS**：`orchestrator/campaign/s8b_floor_stats.py`

**攻撃面1：新規3 test**

**RB-1 — 新規 worktree 改変負例は検査対象に到達しない。**

- **対象**：T:1895、CT:433、CT:500。
- **主張**：`protocol["master_seed"] += 1` は文字列への整数加算であり、`TypeError` になる。
- **根拠**：protocol validator は `master_seed` に空でない文字列を要求する。fixture はこの validator を通過した文書を使う。
- **反例または入力**：現在の `versioned_protocol=True` fixture 自体。T:1897 の `pytest.raises` に入る前に失敗する。
- **是正案**：既存ヘルパー T:1726 と同様に文字列の接尾辞を追加する。変更前後の bytes 不一致も確認する。
- **重大度**：**must-fix**。

**RB-2 — 新正例は版付き参照の配線を検出するが、すべての assert が独立した検出力を持つわけではない。**

- **対象**：T:1844–1865、HF:2000–2020。
- **主張**：既存正例との本質的な違いは、anchor と異なる現行 protocol を実際に選ばせる点。期待値を同じ resolver から取得しているため、resolver 自体の選択仕様を独立には検証しない。
- **根拠**：
  - T:1845：anchor 以外を選択したこと。
  - T:1850：出力の path と raw bytes hash。
  - T:1854：source path の proto8 と選択文書の canonical hash の対応。
  - T:1857：closure 出力からの除外。ただし、除外前の検索結果に当該 path が存在することは確認していない。
  - T:1864–1865：build/generate の一致と生成 bytes。両経路共通の誤りはこれだけでは検出しない。
- **反例または入力**：`floor_protocol_rel` を dedicated 集合から削除しても、検索結果に元々含まれなければ closure assert は通る。
- **是正案**：除外前の hit を実データで成立させられない場合、この assert を専用除外の独立した検出力として数えない。resolver 正否と producer 配線の検証範囲も分けて記録する。
- **重大度**：**should**。

**RB-3 — hash 不一致の診断が旧 authority を示唆する。**

- **対象**：HF:1488、T:1879。
- **主張**：「固定 protocol hash」は解決後の現行 protocol hash を指すようになり、旧 literal anchor の意味から変化している。
- **根拠**：新版負例は、まさに固定 anchor の hash を result に入れて拒否させる。
- **反例または入力**：当該負例の入力では、result は旧固定 protocol hash と一致している。
- **是正案**：「解決済み protocol hash と不一致」等へ変更し、対応する match も更新する。
- **重大度**：**should**。

**攻撃面2：stub・期待値の弱化 — 破れず。** 新規3 test の monkeypatch は `BUDGET_APPROVAL_SHA256` のみ。FX:785 は synthetic ccbench の実 HEAD を入力へ束縛し、FX:914–915 で実際に commit する。resolver・manifest・admission の成功を stub していない。raw hash の期待値は解決 record の bytes から独立に計算しており、揮発 hash の literal 化や凍結承認値の現行 hash への置換はない。

**攻撃面3：変異の単一理由性**

**RB-4 — M3 は既存負例で診断差として殺せても、新しい拒否能力の証拠にならない。**

- **対象**：HF:1411–1416、FC:927–946、FC:984–988、T:1827、T:1897。
- **主張**：producer の HEAD bytes 比較は到達不能ではないが、現在の入力では後続の record bytes 比較と拒否能力が重なる。
- **根拠**：anchor は resolver 内で worktree の構文検証と HEAD 文書の読取りを別々に行うため、既存 seed 改変負例は HF:1411 に到達する。そこを削除すると HF:1416 が拒否し、T:1827 の文言 match が赤になる。版付きは FC:984 で先に拒否される。
- **反例または入力**：既存 anchor seed 改変、または RB-1 修正後の新版 seed 改変。
- **是正案**：M3 を「拒否能力について冗長 gate」と明記する。新版でも producer 比較への到達を示したければ、実 resolver を呼んだ直後に worktree を変更する委譲 wrapper で時点差を作る。ただし、後続 record 比較も拒否するため、これを単独の受理集合防御とは数えない。架空 record を返す stub で単一理由を作らない。
- **重大度**：**must-fix**（変異評価・登録）。

**RB-5 — M5 の期待 node は未成立。早期拒否の契約なら実データで検証できる。**

- **対象**：HF:1432–1441、CT:502–509、HA:857–866。
- **主張**：指定された既存 `protocol.freeze` 不一致 node は確認できず、後段にも同種の拒否がある。
- **根拠**：CT は freeze 参照の形式を検査し、固定参照との一致までは要求しない。一方 HA は固定 path と実 freeze bytes hash を要求する。
- **反例または入力**：synthetic anchor の `freeze.path` または形式上有効な `freeze.sha256` を変更し、canonical bytes を commit した入力。
- **是正案**：`_validate_floor_inputs` を直接呼ぶ新規 test を追加し、実 `_load_repo_object` への委譲 spy で result 読取り回数を記録する。固定参照不一致に対して「result を一度も読まない」を先に assert し、その後に例外を確認する。M5 削除時は読取り境界を越えるため、この assert で検出できる。これは早期拒否の検証であり、拒否能力の唯一性とは区別する。
- **重大度**：**must-fix**（変異評価・登録）。

**攻撃面4：nodeid の ASCII 性 — 破れず。** 新規3 node と既存 seed 改変 node は全て ASCII、parametrize なし。表の提案 node も ASCII。M5 は現状 node が存在しないため、追加前には登録できない。

**攻撃面5：消費者への波及 — 静的には破れず。ただし RB-1 の新規 node は赤になる。** `candidate_repository` の呼び手は T 内に限定され、既定 False は従来入力を維持する。`_validate_floor_inputs`／`_measurement_closure` の呼び手は HF:2082／2100 の各1件で更新済み。`test_s8b_protocol_builder.py:1228` の historical anchor 検査が要求する代入は保持されている。他の `FLOOR_PROTOCOL_REL` 利用 test が依存する固定 path は変更されていない。perf closure の必須3呼出しも保持され、新しい subprocess 呼出し構文はない。実走の成功は未確認。

**攻撃面6：M0 の等価性 — 破れず。** HF:1390 のコメント前に通常の `#` コメントを追加する案について、位置属性を除いた AST の一致を確認した。docstring・呼出し・述語は変化しない。source bytes と generator hash は変わり得るが、既存 candidate test はその hash を固定 literal と照合していない。SURVIVED は予測であり実測ではない。

**攻撃面7：実装子の報告**

**RB-6 — 差分範囲の報告は正しいが、新版負例の到達性評価は訂正が必要。**

- **対象**：`s5-author.md` の「変異 M0〜M5 の単一理由性」、T:1895。
- **主張**：「解決器の前段検査で引き続き成功」は現コードについて成立しない。
- **根拠**：RB-1 の準備段階 `TypeError`。一方、提供された3 diff と現在の `git diff` は hunk 見出しを除く内容が一致し、tracked 差分は所有3 file のみ。test 差分は68行の追加のみ。
- **反例または入力**：現行新版負例。
- **是正案**：RB-1 修正後の静的予測と修正前の欠陥を区別して報告する。未実走の KILLED／SURVIVED を確定しない。
- **重大度**：**should**。

## 変異 M0〜M5 の再照準表

期待 node の共通接頭辞は `orchestrator/tests/test_s8b_holdout_freeze.py::`。以下はすべて静的予測です。

| ID | 位置 | old→new の骨子 | 期待 node | 単一理由の根拠 |
|---|---|---|---|---|
| M0 | HF:1390 | 通常コメント1行を追加 | なし、SURVIVED 期待 | AST・docstring 不変。実走前には確定しない。 |
| M1 | HF:1393–1416 | resolver 選択→旧 literal 読取りへ復帰 | `test_v2_candidate_build_and_generate_versioned_protocol` | 完整な旧動作への復帰なら、最初の赤は T:1846 の build、原因は HF:1487。後段にも proto8（1492）、header（1499）、manifest（1582）、admission（HA:854）の拒否があり、拒否理由は一意でない。再照準は実 `_capture_regular_nofollow` への委譲 spy を新正例に足し、protocol 読取り時の path を最初に assert する配線検証。record bytes 比較を残した部分的復帰なら HF:1416 が先に落ちるため、変異の正確な範囲を登録する。 |
| M2 | HF:2121 | 解決 path→`FLOOR_PROTOCOL_REL` | `test_v2_candidate_build_and_generate_versioned_protocol` | 最初の赤は T:1850 の辞書一致。入力は正常で、build 内に生成済み出力 path の重複照合はない。新規検出力として計上可能。 |
| M3 | HF:1411–1414 | HEAD bytes 不一致拒否を削除 | 既存 `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation` | 最初の赤は T:1827 の match。HF:1416 が引き続き拒否する。新版は修正後も FC:984 が先行する。**冗長 gate／診断差の検出**として登録し、新規拒否能力に数えない。 |
| M4 | HF:1487–1488 | result hash 比較を削除 | `test_v2_candidate_rejects_legacy_hash_for_versioned_protocol` | 最初の赤は T:1879 の `DID NOT RAISE` 予測。v4 入力で変更するのは result の hash だけ。proto8・manifest・証明書は解決 protocol と一致したままで、その result フィールドの再照合ではない。v5 は FS:803 に重複照合があるので対象外。 |
| M5 | HF:1432–1436 | 固定 freeze 参照検査を削除 | 提案：`test_v2_candidate_rejects_protocol_freeze_before_result_read` | RB-5 の committed 不一致入力で、result 読取り回数ゼロを最初に assert。削除時は HF:1438 を越えて赤になる。後段の result hash・manifest・HA:857–866 による拒否より前に、既存の早期検査の効果を測る。受理集合については冗長性が残る。 |

M1・M5 の提案は、依存先を成功させる stub ではなく、実処理へ委譲して境界を観測する test です。M3 は既存 node の診断差による赤を、新規 test の検出力へ転記してはいけません。

## GO / NO-GO と条件

**現状は NO-GO。**

1. RB-1 の文字列型誤りを修正する。
2. M1 の置換範囲を確定し、M3 を冗長 gate と分類する。M5 は実在する期待 node を追加・再登録する。
3. 親が通常版の焦点走を先に成功させ、その後で変異を実走する。準備段階の `TypeError` を KILLED と集計しない。
4. M2・M4 の新規検出力、M3 の診断差、M5 の早期拒否を別々に報告する。

## 総括

確実な欠陥は、新規負例の `master_seed += 1` です。差分範囲と既存期待値不変更の報告は裏付けられました。M3 は拒否能力が重複し、M5 は期待 node が未成立です。ファイル変更・pytest・変異実走は行っていません。