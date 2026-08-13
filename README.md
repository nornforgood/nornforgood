# 甲乙經穴位-經絡-病症關聯資料庫

這個專案提供一份可直接使用的中醫經穴知識庫，整理「穴位、經絡、病症」三者的關聯，並同時提供可訪問的網頁介面與 HTTP API。

## 主要功能

- 穴位查詢
- 經絡查詢
- 病症查詢
- 按病症尋找對應穴位
- 按經絡尋找對應穴位
- 直接瀏覽器使用的前端頁面
- JSON API 供外部系統存取

## 目錄

- [data](data)：資料庫與匯出檔
- [scripts/build_jia_yi_jing_db.py](scripts/build_jia_yi_jing_db.py)：資料生成腳本
- [scripts/query_jia_yi_jing.py](scripts/query_jia_yi_jing.py)：命令列查詢工具
- [server.py](server.py)：Web UI 與 API 服務
- [README.md](README.md)：說明文檔

## 啟動方式

### 1) 建立資料庫

```bash
py -3 scripts/build_jia_yi_jing_db.py
```

### 2) 啟動前端與 API

```bash
py -3 server.py
```

### 3) 打開瀏覽器

```text
http://localhost:8000
```

## API 範例

- 健康檢查： `http://localhost:8000/api/health`
- 病症列表： `http://localhost:8000/api/diseases`
- 穴位列表： `http://localhost:8000/api/acupoints`
- 經絡列表： `http://localhost:8000/api/meridians`
- 按病症查穴位： `http://localhost:8000/api/by-disease?keyword=頭痛`
- 按經絡查穴位： `http://localhost:8000/api/by-meridian?keyword=手陽明`

## 資料結構

### meridians

| 欄位 | 說明 |
| --- | --- |
| id | 經絡 ID |
| name | 經絡名稱 |
| code | 經脈縮寫 |
| category | 經脈類型 |
| description | 經絡簡介 |

### acupoints

| 欄位 | 說明 |
| --- | --- |
| id | 穴位 ID |
| name | 穴位名稱 |
| pinyin | 拼音 |
| meridian_id | 所屬經絡 ID |
| location | 定位描述 |
| note | 穴位說明 |
| classic_code | 經典編碼 |
| meridian_name | 所屬經絡名稱 |

### diseases

| 欄位 | 說明 |
| --- | --- |
| id | 病症 ID |
| name | 病症名稱 |
| category | 病症分類 |
| description | 病症簡介 |

### point_disease

| 欄位 | 說明 |
| --- | --- |
| point_id | 穴位 ID |
| disease_id | 病症 ID |
| relation_type | 關聯類型 |
| evidence | 關聯說明 |

## 資料範圍

- 經絡：13 個（含任脈、督脈）
- 穴位：25 個代表性穴位
- 病症：26 類常見病證
- 關聯：49 筆穴位-病症對應

## 可部署方式

這個專案可直接部署成單機 Web 服務。最簡單的方式是：

1. 在目標伺服器安裝 Python 3
2. 將整個專案資料夾上傳
3. 執行：

```bash
py -3 server.py
```

4. 使用 Nginx / reverse proxy 包一層即可對外發布

## 後續擴充

1. 補齊更多穴位、經絡與病症資料
2. 增加「主治」「禁忌」「治法」欄位
3. 擴充成更完整的知識圖譜
4. 接上前端篩選、分頁、搜尋與圖表展示


