```jsonl
{"packet_id":"12aaaae318e241eb6e46a14a7f3f0072","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"3c71bea9793cab41a6305526931fb4bb","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"a27e7fbf394f28c37c75531b560d56ee","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"ae545ba70cf60de38a363b9305c0a6b6","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"b014ba613bdeb5a5d4acaa68dfca8ebf","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"b3dfad052c7ca83a02d358e1ac685a74","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"b4355e8b228d9e85c0617ee5b52f6e8d","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"bb6fbd1fc07069f915b54b347cdebcf2","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"e38e68d2a783825ba1c8124762dbca21","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"f91a3dcf8cff0979b959fdf7fae18317","r1_detected":true,"decision":"NO-GO","findings":[]}
```

## 総括

`r1_detected` は true が6件、falseが4件です。`decision` の分布は GOが4件、NO-GOが6件、不明が0件でした。R-1を検出した6件はいずれも、pre-policy commitでもcanonical CAB parser相当が実行され、その障害によって従来のrc=0がrc=2へ変わり、受理集合を縮小することをmust-fixまたはNO-GOとして明示しています。残る4件は、この実行経路がpre-policyでは遮断されると結論しているため、否定文脈としてfalseにしました。

新規 finding は0件で、root causeの一覧は「なし」です。本文に現れたbare CRを含むLF境界の問題は既知のA-1、cwd・ambient configやmutation controlの問題はA-2またはB-3、pre-policy parser回帰はR-1と意味同値です。また、反復的な`git log -S`の性能懸念は複数packetで言及されていますが、各本文自身が具体的な成果物影響を立証できないbacklogとして扱っているため、新規 findingには数えませんでした。

迷って保守側へ倒したpacketはありません。GOとNO-GOが曖昧に併記された本文や、最終判断を留保した本文もありませんでした。境界として注意したのは、R-1を「closed」「pre-policyでは呼ばれない」とする記述を検出扱いにしないこと、および既知findingの別表現を新規認定しないことです。これらはいずれもcodebookの否定文脈規定と意味同値性規定で判定でき、codebookだけでは決められない残余境界はありませんでした。