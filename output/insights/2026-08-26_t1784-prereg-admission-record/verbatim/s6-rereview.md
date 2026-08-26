## 総括

FIX-2、3、4、6、7 は実コード上で `closed` と判定しました。  
FIX-1 は ASCII 限定の語境界に過剰拒否が残るため `partial`、FIX-8 は既存負例の削除があるため `partial` です。  
FIX-5 は指定された回避を拒否しますが、fence でない行を fence と誤認する新しい拒否を作ったため `regressed` です。  
success receipt `/v2` の dataclass は 40 field のままで、増減はありません。  
pytest は指示どおり再実走していません。

## 対応表

|項目|判定|実コードによる根拠|
|---|---|---|
|FIX-1|`partial`|NFKC 後に sentinel を検査する順序は正しく、`snapshot`、`final`、`internal`、`signature` は通り、独立した `TBD`、`N/A` は拒否される (`orchestrator/campaign/p3_b4_admission_record.py:75-79`, `:464-470`, `:551-557`)。ただし境界が ASCII 限定なので、`担当者=NA太郎` の `NA` も独立 sentinel と誤認する。|
|FIX-2|`closed`|sidecar は record path/hash、検証 HEAD、文書 path/commit/hash、3期待値を持つ (`orchestrator/campaign/p3_b4_closed_critic.py:332-360`)。新規 artifact root 内へ `O_EXCL` で書かれ (`:309-329`, `:1141-1159`)、provider 構築 `:1163` と query `:857` より前。CLI は path/hash を出す (`:1764-1771`)。success dataclass は不変 (`:214-254`)。|
|FIX-3|`closed`|certified gate は exact live pair、production seal、実際の terminal path、再検証した record、sidecar bytes/hash、pair_id、receipt の3期待値を必須にする (`orchestrator/campaign/p3_b4_closed_critic.py:1017-1048`, `:1651-1731`)。両腕 JSON を整合的に昇格しても test-only pair には seal がなく拒否される (`orchestrator/tests/test_p3_b4_closed_critic.py:1786-1817`)。|
|FIX-4|`closed`|Git 子環境は親環境の複製ではなく、値も固定された5変数だけ (`orchestrator/campaign/p3_b4_admission_record.py:245-252`)。`LD_PRELOAD`、`LD_LIBRARY_PATH`、`HOME`、`XDG_CONFIG_HOME`、locale、任意の `GIT_*` は渡らない。テストも exact allowlist を固定している (`orchestrator/tests/test_p3_b4_admission_record.py:364-397`)。|
|FIX-5|`regressed`|NFKC 前後の format/default-ignorable 拒否は有効 (`orchestrator/campaign/p3_b4_admission_record.py:453-470`)。backtick/tilde、長さ、同種 marker を追跡するため、入れ子、tilde、途中終了は拒否され、4-space indented heading は heading と認識されない (`:473-530`)。一方、CommonMark では fence にならない backtick 入り info 文字列も opener と誤認する新しい過剰拒否がある (`:100`, `:489-495`)。|
|FIX-6|`closed`|署名の出力域は既知 admission 署名、unclassified admission、timeout、unclassified closed critic の閉じた列挙 (`orchestrator/campaign/p3_b4_closed_critic.py:120-140`, `:363-374`)。failure terminal と CLI は同じ関数を使う (`:967-980`, `:1778-1780`)。success receipt dataclass は変更されていない (`:214-254`)。|
|FIX-7|`closed`|module docstring、関数名、docstring、例外文言は「固定表、非空 source cell、閉じた sentinel、3値」に限定し、型・意味・render 後の非空を検査しないと明記する (`orchestrator/campaign/p3_b4_admission_record.py:18-20`, `:48-52`, `:499-506`)。新しい名称は実検査以上を主張していない。|
|FIX-8|`partial`|schema、文書 path、§5 labels はテスト内 literal (`orchestrator/tests/test_p3_b4_admission_record.py:20-40`)。receipt exact keys も40 fieldと `finished_at_ns` の literal (`orchestrator/tests/test_p3_b4_closed_critic.py:890-933`)。正例名/docstring も fake runner、3期待値、残り9欄の非検査を明示 (`:831-859`)。ただし既存の片腕昇格負例が実差分で削除されている。|

## 新規 must-fix

### CommonMark 上の非 fence 行を opener と誤認し、正当な文書を拒否する

- 根拠: `_FENCE_OPEN_RE` は marker 後を無条件で `.*` として受理し、backtick fence の info 文字列に backtick を許している (`orchestrator/campaign/p3_b4_admission_record.py:100`, `:489-495`)。
- 具体的な破り方: `b"\x60\x60\x60meta\x60tag\n\n"` の後に正常な §5 を置く。この先頭行は CommonMark の backtick fence opener ではないが、現実装は EOF まで fenced と扱い、`starts` を空にして `:527-530` で拒否する。
- 成果物影響: 正当な commit 済み事前登録文書が admission を通れず、certified 実走を開始できない。
- 修正案: opener の marker と info 部を分離し、marker が backtick の場合は info 部に backtick があれば opener と認識しない。上記 bytes＋正常な §5 は通し、通常の backtick fence または tilde fence 内の §5 は引き続き拒否する。

## nit / backlog

- FIX-1 の境界は Unicode-aware にする余地がある。`(?<!\w)...(?!\w)` 相当なら `担当者=NA太郎` を通し、独立した `N/A` や `status: TBD` を拒否できる。現テストは通常語を固定するが、独立 `N/A` の負例と非 ASCII 隣接の正例がない (`orchestrator/tests/test_p3_b4_admission_record.py:236-240`, `:314-333`)。
- FIX-8 は「既存期待値を削除しない」指示に違反している。最終テストは直ちに両腕を昇格するため (`orchestrator/tests/test_p3_b4_closed_critic.py:1786-1807`)、旧来の「terminal だけ昇格すると start/terminal 不一致」「片腕だけ完全昇格すると evidence class 不一致」の2検査が消えた。現在の実装はなお拒否するため成果物欠陥ではないが、両検査を復元してから両腕昇格を追加すべき。
- fence の新テストは基本 backtick fence、全角 sentinel、format 文字だけ (`orchestrator/tests/test_p3_b4_admission_record.py:336-361`)。tilde、短い内側 marker、長い外側 marker、途中の開閉、4-space indented block を literal 負例として追加すると状態機械を固定できる。
- §5 全体を HTML comment または raw HTML block 内に置く既存の誤受理は残る。検査は fence 状態しか除外しない (`orchestrator/campaign/p3_b4_admission_record.py:514-530`)。これは今回指定された fence 修正が新設した欠陥ではないため、新規 must-fix には数えていない。
- sidecar は生成後も通常の owner-writable file である。ただし現 gate は fresh record から canonical bytes を再構築し、bytes/hash の双方を照合する (`orchestrator/campaign/p3_b4_closed_critic.py:1683-1704`)。改竄後の sidecar 単体では gate を通らない。将来の consumer は CLI が出す hash の照合を必須にすべき。

## 恒真監査の結果

偽入力を挙げられなかった新規 assert: **無し**。

代表例として、sidecar の query 後生成、receipt key の増減、signature の欠落、Git 親環境の継承、両腕昇格の certified gate 通過は、それぞれ対応する新規 assert／`_raises` を偽にする具体入力になる。

## 攻撃できなかった面

- sidecar の初回上書きは `O_EXCL` で拒否され、provider query 前に完成する。
- sidecar の1 byte 改変、末尾改行、別 record の sidecar への交換はいずれも certified gate の再構築比較で拒否される。
- test-only 両腕の start/terminal JSON を整合的に `certified` へ変更しても、production seal がないため正式関門を通らない。
- 同一 process では `_PAIR_SEAL`、`_PRODUCTION_PAIR_SEAL` や module globals を参照・差し替えできるが、これは既存の明記済み trust non-guarantee の範囲内 (`orchestrator/campaign/p3_b4_closed_critic.py:145-148`)。今回の seal はその保証範囲を越えて主張していない。
- Git 子 process へ loader、home/config、locale、親由来の任意環境を残す経路は見つからなかった。
- success receipt `/v2` の schema version と40 fieldに増減はなく、failure 専用の `error_signature` だけが追加されている。