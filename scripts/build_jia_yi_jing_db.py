from __future__ import annotations

import csv
import json
import sqlite3
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "jia_yi_jing_acupuncture.db"
JSON_PATH = DATA_DIR / "jia_yi_jing_acupuncture.json"
CSV_PATH = DATA_DIR / "jia_yi_jing_acupuncture.csv"

MERIDIANS = [
    (1, "手太陰肺經", "LU", "手太陰", "肺經主氣、司呼吸與津液運化。"),
    (2, "手陽明大腸經", "LI", "手陽明", "大腸經主傳導糟粕，與表裡相合。"),
    (3, "足陽明胃經", "ST", "足陽明", "胃經主受納腐熟，與消化相關。"),
    (4, "足太陰脾經", "SP", "足太陰", "脾經主運化、統血與水濕代謝。"),
    (5, "手少陰心經", "HT", "手少陰", "心經主神志與血脈。"),
    (6, "手厥陰心包經", "PC", "手厥陰", "心包經與心主血脈、神志相關。"),
    (7, "足少陰腎經", "KI", "足少陰", "腎經主藏精與生長發育。"),
    (8, "足厥陰肝經", "LR", "足厥陰", "肝經主疏泄與氣血調節。"),
    (9, "手少陽三焦經", "SJ", "手少陽", "三焦經主通調水道與氣化。"),
    (10, "足少陽膽經", "GB", "足少陽", "膽經主決斷與肢節病機。"),
    (11, "足太陽膀胱經", "BL", "足太陽", "膀胱經主背腰與表裡相合。"),
    (12, "督脈", "GV", "督脈", "督脈主一身陽氣總匯。"),
    (13, "任脈", "CV", "任脈", "任脈主陰脈總匯與胞宮。"),
]

DISEASES = [
    (1, "頭痛", "疼痛", "以頭部疼痛為主。"),
    (2, "牙痛", "疼痛", "口腔與牙齒疼痛。"),
    (3, "目赤", "眼部", "目睛紅赤、疼澀。"),
    (4, "便秘", "腸胃", "大便乾結難下。"),
    (5, "咳嗽", "呼吸", "反覆咳嗽、咳痰。"),
    (6, "氣喘", "呼吸", "呼吸短促、喘促。"),
    (7, "心悸", "心血管", "心中悸動、胸悶。"),
    (8, "失眠", "神志", "難以入睡或易醒。"),
    (9, "胃痛", "胃腸", "胃脘部疼痛。"),
    (10, "嘔吐", "胃腸", "反胃、噯氣、吐逆。"),
    (11, "腹痛", "腹部", "腹部脹痛或絞痛。"),
    (12, "腹脹", "腹部", "腹部脹滿、腸鳴。"),
    (13, "月經不調", "婦科", "經期、經量、經色异常。"),
    (14, "腰痛", "腰背", "腰背疼痛、僵硬。"),
    (15, "眩暈", "頭部", "頭暈目眩、站立不穩。"),
    (16, "肩痛", "肩頸", "肩背疼痛或牽涉痛。"),
    (17, "鼻炎", "耳鼻喉", "鼻塞、流涕、鼻瘡。"),
    (18, "耳鳴", "耳鼻喉", "耳中作響、聽力異常。"),
    (19, "水腫", "水濕", "體表或四肢浮腫。"),
    (20, "痰多", "呼吸", "痰濃、痰黏、痰量多。"),
    (21, "遺尿", "泌尿", "夜尿或尿失禁。"),
    (22, "胸悶", "胸部", "胸中不暢、悶脹。"),
    (23, "膝痛", "關節", "膝部疼痛、腫痛。"),
    (24, "落枕", "肩頸", "頸項痠痛、轉頭不利。"),
    (25, "膽病", "肝膽", "膽氣不舒引起的病機。"),
    (26, "經痛", "婦科", "經行腹痛、痛經。"),
]

POINTS = [
    (1, "合谷", "HEGU", 2, "手背第一、二掌骨之間，橫紋端", "原穴，主治頭痛、牙痛、目赤、便秘。", "LI4", "手陽明大腸經"),
    (2, "曲池", "QUCHI", 2, "肘橫紋外端，屈肘時凹陷處", "大腸經要穴，治肩臂疼痛與熱證。", "LI11", "手陽明大腸經"),
    (3, "少商", "SHAOSHANG", 1, "拇指末節外側，指甲角旁0.1寸", "肺經井穴，主治咳嗽、喉痛。", "LU11", "手太陰肺經"),
    (4, "列缺", "LIEQUE", 1, "前臂桡骨茎突上1.5寸，橈骨中間", "肺經絡穴，主治頭痛、咽喉痛與鼻炎。", "LU7", "手太陰肺經"),
    (5, "足三里", "ZUSANLI", 3, "膝下一寸，犢鼻下三寸", "胃經合穴，治胃痛、腹痛、便秘。", "ST36", "足陽明胃經"),
    (6, "豐隆", "FENGLONG", 3, "外踝上8寸，腓骨前緣", "胃經絡穴，治痰多、咳嗽與便秘。", "ST40", "足陽明胃經"),
    (7, "中脘", "ZHONGWAN", 13, "臍上4寸，胸腹正中線", "任脈要穴，主治胃痛、嘔吐、腹脹。", "CV12", "任脈"),
    (8, "關元", "GUANYUAN", 13, "臍下3寸，任脈中線", "任脈要穴，主治腹痛、遺尿與月經病。", "CV4", "任脈"),
    (9, "氣海", "QIHAI", 13, "臍下一寸半，任脈中線", "補益元氣，治氣虛腹脹乏力。", "CV6", "任脈"),
    (10, "三陰交", "SANYINJIAO", 4, "內踝上3寸，脛骨內側後緣", "脾經合穴，治月經不調、痛經、腹痛。", "SP6", "足太陰脾經"),
    (11, "陰陵泉", "YINLINGQUAN", 4, "膝內側髕骨下緣", "脾經穴，治腹脹、食滯與水腫。", "SP9", "足太陰脾經"),
    (12, "公孫", "GONGSUN", 8, "第一蹠骨大頭內側前緣", "肝經絡穴，治胃痛、胸悶、嘔吐。", "LR4", "足厥陰肝經"),
    (13, "太沖", "TAICHONG", 8, "足背第一、二蹠骨縫際", "肝經原穴，治頭痛、眩暈、月經不調。", "LR3", "足厥陰肝經"),
    (14, "章門", "ZHANGMEN", 8, "側胸部第九肋間隙", "肝經俞募穴，治胸脅脹痛。", "LR13", "足厥陰肝經"),
    (15, "神門", "SHENMEN", 5, "小指尺側，腕橫紋尺側端", "心經穴，治失眠、心悸與神志不安。", "HT7", "手少陰心經"),
    (16, "內關", "NEIGUAN", 6, "前臂掌側，腕橫紋上2寸", "心包經絡穴，治心悸、胃痛、嘔吐。", "PC6", "手厥陰心包經"),
    (17, "太溪", "TAIXI", 7, "內踝後方，跟腱前緣", "腎經原穴，治腰痛、耳鳴與遺尿。", "KI3", "足少陰腎經"),
    (18, "湧泉", "YONGQUAN", 7, "足底前部，足心凹陷處", "腎經井穴，治眩暈與失眠。", "KI1", "足少陰腎經"),
    (19, "百會", "BAIHUI", 12, "頭頂正中，前發際後1寸", "督脈要穴，治頭痛、眩暈與昏厥。", "GV20", "督脈"),
    (20, "風池", "FENGCHI", 10, "項部胸鎖乳突肌與斜方肌間", "膽經穴，治頭痛、目眩與風寒外感。", "GB20", "足少陽膽經"),
    (21, "肩井", "JIANJING", 10, "肩部，肩峰與第七頸椎連線交點", "膽經穴，治肩痛、落枕與頸項強。", "GB21", "足少陽膽經"),
    (22, "外關", "WAIGUAN", 9, "前臂尺骨與橈骨間，腕後2寸", "三焦經絡穴，治耳鳴、頭痛、肩頸痛。", "SJ5", "手少陽三焦經"),
    (23, "肝俞", "GANYU", 11, "第七胸椎旁開1.5寸", "膀胱經穴，治肝膽病變及目部不適。", "BL18", "足太陽膀胱經"),
    (24, "脾俞", "PIYU", 11, "第十一胸椎旁開1.5寸", "膀胱經穴，治消化不良和水腫。", "BL20", "足太陽膀胱經"),
    (25, "照海", "ZHAOHAI", 7, "內踝下方，踝尖後方", "腎經穴，治頭痛、月經病與失眠。", "KI6", "足少陰腎經"),
]

RELATIONS = [
    (1, 1, "主治", "頭痛、目赤、牙痛。"),
    (1, 4, "主治", "大便不通、便秘。"),
    (2, 4, "主治", "腸胃實熱所致便秘。"),
    (2, 16, "主治", "肩痛、臂痛及局部熱痛。"),
    (3, 5, "主治", "咳嗽、咳痰、喉痛。"),
    (4, 17, "主治", "鼻炎、鼻塞、頭痛。"),
    (4, 1, "主治", "頭痛、咽痛。"),
    (5, 9, "主治", "胃痛、嘔吐。"),
    (5, 11, "主治", "腹痛、腸鳴、便秘。"),
    (6, 20, "主治", "痰多、咳嗽及胸悶。"),
    (6, 11, "主治", "脹滿、食滯。"),
    (7, 9, "主治", "胃痛、嘔吐。"),
    (7, 12, "主治", "腹脹、脹滿。"),
    (8, 21, "主治", "遺尿、月經不調。"),
    (8, 11, "主治", "小腹冷痛。"),
    (9, 12, "主治", "腹脹、脾胃虛弱。"),
    (9, 19, "主治", "水腫與氣虛乏力。"),
    (10, 13, "主治", "月經不調、痛經。"),
    (10, 26, "主治", "經行腹痛、痛經。"),
    (11, 19, "主治", "水腫、脹滿。"),
    (11, 12, "主治", "腹脹、食滯。"),
    (12, 9, "主治", "胃痛、嘔吐。"),
    (12, 22, "主治", "胸悶、脅痛。"),
    (13, 15, "主治", "眩暈、頭痛。"),
    (13, 13, "主治", "經期不調。"),
    (14, 22, "主治", "胸脅脹痛。"),
    (14, 12, "主治", "脹滿與胸悶。"),
    (15, 8, "主治", "失眠、心悸。"),
    (15, 1, "主治", "心神不安。"),
    (16, 7, "主治", "心悸、胸悶。"),
    (16, 9, "主治", "胃痛、嘔吐。"),
    (17, 14, "主治", "腰痛、腎虛。"),
    (17, 18, "主治", "耳鳴、耳聾。"),
    (18, 15, "主治", "眩暈、耳鳴。"),
    (18, 8, "主治", "失眠、心神不寧。"),
    (19, 1, "主治", "頭痛、眩暈。"),
    (19, 15, "主治", "眩暈與昏厥。"),
    (20, 1, "主治", "頭痛、目眩。"),
    (20, 17, "主治", "風寒外感、鼻塞。"),
    (21, 16, "主治", "肩痛、頸項強。"),
    (21, 24, "主治", "落枕與肩背疼痛。"),
    (22, 18, "主治", "耳鳴、耳閉。"),
    (22, 1, "主治", "頭痛、肩頸痛。"),
    (23, 25, "主治", "肝膽不舒、目痛。"),
    (23, 15, "主治", "眩暈、目眩。"),
    (24, 19, "主治", "脾虛水腫。"),
    (24, 12, "主治", "腹脹、脹滿。"),
    (25, 20, "主治", "痰多、咳嗽。"),
    (25, 4, "主治", "便秘、痰滯。"),
]


def init_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("DROP TABLE IF EXISTS point_disease")
    conn.execute("DROP TABLE IF EXISTS acupoints")
    conn.execute("DROP TABLE IF EXISTS diseases")
    conn.execute("DROP TABLE IF EXISTS meridians")

    conn.execute(
        """
        CREATE TABLE meridians (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE acupoints (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            meridian_id INTEGER NOT NULL,
            location TEXT,
            note TEXT,
            classic_code TEXT,
            meridian_name TEXT,
            FOREIGN KEY (meridian_id) REFERENCES meridians(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE diseases (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE point_disease (
            point_id INTEGER NOT NULL,
            disease_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            evidence TEXT,
            PRIMARY KEY (point_id, disease_id, relation_type),
            FOREIGN KEY (point_id) REFERENCES acupoints(id),
            FOREIGN KEY (disease_id) REFERENCES diseases(id)
        )
        """
    )

    conn.executemany(
        "INSERT INTO meridians(id, name, code, category, description) VALUES (?, ?, ?, ?, ?)",
        MERIDIANS,
    )
    conn.executemany(
        "INSERT INTO acupoints(id, name, pinyin, meridian_id, location, note, classic_code, meridian_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]) for p in POINTS],
    )
    conn.executemany(
        "INSERT INTO diseases(id, name, category, description) VALUES (?, ?, ?, ?)",
        DISEASES,
    )
    conn.executemany(
        "INSERT INTO point_disease(point_id, disease_id, relation_type, evidence) VALUES (?, ?, ?, ?)",
        RELATIONS,
    )
    conn.commit()
    return conn


def export_json(conn: sqlite3.Connection) -> None:
    data = OrderedDict()
    data["meridians"] = [dict(row) for row in conn.execute("SELECT * FROM meridians ORDER BY id").fetchall()]
    data["acupoints"] = [dict(row) for row in conn.execute("SELECT * FROM acupoints ORDER BY id").fetchall()]
    data["diseases"] = [dict(row) for row in conn.execute("SELECT * FROM diseases ORDER BY id").fetchall()]
    data["relations"] = [dict(row) for row in conn.execute("SELECT * FROM point_disease ORDER BY point_id, disease_id").fetchall()]
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(conn: sqlite3.Connection) -> None:
    tables = [
        ("meridians", ["id", "name", "code", "category", "description"]),
        ("acupoints", ["id", "name", "pinyin", "meridian_id", "location", "note", "classic_code", "meridian_name"]),
        ("diseases", ["id", "name", "category", "description"]),
        ("point_disease", ["point_id", "disease_id", "relation_type", "evidence"]),
    ]
    for table_name, columns in tables:
        with CSV_PATH.with_name(f"{CSV_PATH.stem}_{table_name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table_name}").fetchall()
            for row in rows:
                writer.writerow({key: row[key] for key in columns})


def print_summary(conn: sqlite3.Connection) -> None:
    point_count = conn.execute("SELECT COUNT(*) FROM acupoints").fetchone()[0]
    disease_count = conn.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    relation_count = conn.execute("SELECT COUNT(*) FROM point_disease").fetchone()[0]
    print(f"穴位數：{point_count}")
    print(f"病症數：{disease_count}")
    print(f"關聯數：{relation_count}")
    print(f"資料庫路徑：{DB_PATH}")
    print(f"JSON 路徑：{JSON_PATH}")
    print(f"CSV 路徑：{CSV_PATH.parent}")

    sample = conn.execute(
        """
        SELECT a.name, m.name, d.name, p.relation_type, p.evidence
        FROM point_disease p
        JOIN acupoints a ON a.id = p.point_id
        JOIN meridians m ON m.id = a.meridian_id
        JOIN diseases d ON d.id = p.disease_id
        ORDER BY a.id, d.id
        LIMIT 5
        """
    ).fetchall()
    print("範例資料：")
    for row in sample:
        print(tuple(row))


if __name__ == "__main__":
    conn = init_db()
    export_json(conn)
    export_csv(conn)
    print_summary(conn)
    conn.close()
