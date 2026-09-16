## 所見 RB-1: literal・宣言順・wire 順の取り違えは反証

主張：新 literal が歴史 grammar と異なり、decode または epoch を壊す疑いは成立しない。

根拠 (file:line)：`campaign_lock.py:146,505,511`、`artifact_admission.py:1083`。`git show 2a9ba783f^:orchestrator/campaign/campaign_lock.py` を独立取得し、production と両テストの literal が全 62 要素・順序とも一致することを確認した。wire は sorted 順で照合し、blob map と epoch preimage は宣言順で構築している。

real / refuted：**refuted**。  
must-fix か nit か：nit 相当、修正不要。  
成果物影響：歴史 epoch の順序由来の値ずれは認められない。

## 所見 RB-2: 実 3 本の記録 commit と全 blob は現在の repo に存在する

主張：commit 欠落や記録 digest 不一致で必達 B が阻まれる疑いは成立しない。必達 A／B は静的に成立すると判断する。

根拠 (file:line)：`artifact_admission.py:1034,1077,1160`、`contract_loader_binding.py:577`。実ファイルを独立に読み、以下を確認した。

- rr5／rr50：記録 commit は `31ec382a7841e188e46f93e8de4261c964facfb2`。
- rr95：記録 commit は `ae8a767eb60118c3f9791141603fa01ad4f28406`。
- 両 commit は Git commit object として存在する。各 lock の全 62 digest が commit blob と一致し、当該 commit の宣言順も新 literal と一致する。
- 3 本とも wire 順・内外 canonical JSON が一致する。

独立計算した epoch は rr5／rr50 が `E1:c560b2cac50f5b389ac8f20cf9a1400c26a1a99fd6564f46c64e6724212edb74`、rr95 が `E1:bd9418227bc080d2f3f70e48cad7d1518a7141df0323c6d08f7e83f277bc68cd`。公開 API の実走結果ではない。

real / refuted：**refuted**。  
must-fix か nit か：nit 相当、実装修正不要。  
成果物影響：中央歴史 API が 3 本に歴史 E1 を返すための記録データと Git 参照は揃っている。

## 所見 RB-3: 新設テストは decoder と committed blob 検査を実際に通す構造である

主張：dataclass の直接構築だけで正例を成立させている疑いは成立しない。

根拠 (file:line)：`test_campaign_lock_codec.py:575,634`、`test_artifact_admission.py:549,2994,3013,3089`。codec 正例は文字列／bytes decoder を呼ぶ。admission 正例は合成 Git repo に実 blob を commit する fixture を用い、`require_admitted_campaign` と `require_campaign_verifier_epoch` を呼ぶ。差し替えるのは repository root であり、decoder／validator の stub ではない。62 件の不一致負例も両 API を通し、例外に対象 path が含まれることを検査する。直接構築の node は型・scope・順序の局所不変条件を検査する補助である。

real / refuted：**refuted**。  
must-fix か nit か：nit 相当、修正不要。  
成果物影響：歴史型への分類と blob 真正性を失う変更を、公開 API の検査で検出する構造になっている。

## 所見 RB-4: 固定期待値への揮発値の焼き込みは認められない

主張：別 commit・時刻・PID によって固定期待 epoch が変わる疑いは成立しない。

根拠 (file:line)：`test_artifact_admission.py:375,549,3005,3021`。固定 epoch は宣言順と `epoch closure fixture {index}\n` の固定 bytes から独立再計算して一致した。固定 path hash も一致する。fixture の commit ID 自体は変動し得るが、epoch preimage に commit ID は入らない。

real / refuted：**refuted**。  
must-fix か nit か：nit 相当、修正不要。  
成果物影響：checkout の HEAD や実行時刻の変化による期待 epoch の不安定化はない。

## 所見 RB-5: consumer の挙動を一律に「不変」とは言えないが、裁定外の変更ではない

主張：`load_explore_correctness_mode` の到達可能入力は中央歴史 API の拡張に伴って増える。

根拠 (file:line)：`b10_backoff_static_tail_formal.py:351` は歴史 admission／decoder 後に既存の `run_kind`・workload 条件を検査するため、条件を満たす exact-62 がそこへ到達可能になる。一方、`b10_backoff_shape_sweep.py:3131,3135` は exact-24 条件を維持し、exact-62 の拒否位置だけが変わり得る。`layer3_report.py:116` は通常 decoder のまま。3 consumer のソースは基準 commit と完全一致した。

real / refuted：**real**（波及の説明）。  
must-fix か nit か：**nit**。裁定が認めた歴史 grammar 拡張の帰結である。  
成果物影響：exploration mode の参照候補は増えるが、shape report の受理集合と certified 選択は維持され、layer3 材料レポートは依然 exact-62 を拒否する。

## 所見 RB-6: 実装の過不足は見当たらないが、受入実走の証拠は残っている

主張：裁定 §2 の実装項目は揃っている。ただし静的レビューを受入実走済みと扱ってはならない。

根拠 (file:line)：`campaign_lock.py:449,494,680`、`artifact_admission.py:242,287,1034,1099`、`s5-impl.md:53`。exact-24 validator、通常 decoder／encoder、既存テスト関数は基準 commit とソース一致。未知 grammar は最後に exact-24 validator へ渡るが、その厳密照合で拒否され、無条件受理にはならない。変更は指定 production 2・test 2 ファイルに限られる。実装報告では実 3 本の A／B・測定 C・前後 hash 確認は未実施である。

real / refuted：**real**（検証証跡の未完了）。  
must-fix か nit か：**nit**。具体的な受理集合の欠陥は示せず、実装差し戻し理由にはしない。  
成果物影響：台帳では静的確認と実走確認を区別し、測定 C の後段拒否を未確認のまま成功扱いしないこと。

## 総括

最も危険な残件は RB-6：静的成立を実 3 本の受入実走成功へ読み替えること。  
採否判定：**実装は採用可。must-fix は検出しなかった。**  
literal・記録 commit・全 186 blob の一致を独立確認した。pytest／公開 API は実走していない。