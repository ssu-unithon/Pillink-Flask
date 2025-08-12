from flask import Flask, request, jsonify
from flask_cors import CORS
import os, traceback
import pandas as pd
import numpy as np
from collections import Counter
import requests, json
from urllib.parse import unquote
from sentence_transformers import SentenceTransformer, util
import re
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
CORS(app)

#파일 위치 확인
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("CWD:", os.getcwd())
print("FILE DIR:", BASE_DIR)
csv_path = os.path.join(BASE_DIR, "medicine_all.csv")
medicine_all = pd.read_csv(csv_path, encoding="utf-8")
log_path = os.path.join(BASE_DIR, "app.log")

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
if logger:
    print("logger 설정")

# 파일 핸들러 (10MB 이상이면 백업하고 새 파일 생성, 최대 5개 유지)
file_handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
if file_handler:
    print("handler 존재함")

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
if console_handler:
    print("console_handler 설정됨")

# 로그 포맷
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 핸들러 등록
logger.addHandler(file_handler)
logger.addHandler(console_handler)

<<<<<<< HEAD
model_name = 'jhgan/ko-sbert-sts'
embedder = SentenceTransformer(model_name)
=======
print("2")
#문장 유사도 평가 모델
model_name = 'jhgan/ko-sbert-sts'
embedder = SentenceTransformer(model_name)
print("2-1")
>>>>>>> b53192731531c4731de3995ff0cb4c8b06f7f03f

#API 인증키
serviceKey = unquote('0zt0FUkd5LMT9nSUvUkxnyXvIkqWli%2Bbk0ulrUNTqhSlAfcMw0a9sMwR4FrMOjdwJ8m3%2Bt9HNGzvrMv8nUB6OQ%3D%3D')
if serviceKey:
    print(serviceKey)

@app.get("/health")
def health():
    return {"ok": True}, 200


#루트(확인 용도)
@app.get("/")
def home():
    return "Flask Servre Testing...",200


#약 정보
def get_medicine_info(entpName=None, itemName=None):
    try:
        if not entpName and not itemName:
            logger.warning("업체명과 제품명이 입력되지 않음")
            return None, {"error": "업체명과 제품명을 입력해주세요"}

        url = 'http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList'
        params = {
            'serviceKey': serviceKey, 'pageNo': '1', 'numOfRows': '3',
            'entpName': entpName or '', 'itemName': itemName or '',
            'itemSeq': '', 'efcyQesitm': '', 'useMethodQesitm': '', 'atpnWarnQesitm': '',
            'atpnQesitm': '', 'intrcQesitm': '', 'seQesitm': '', 'depositMethodQesitm': '',
            'openDe': '', 'updateDe': '', 'type': 'json'
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        payload = r.json()
        items = (payload.get('body') or {}).get('items') or []

        if not items:
            logger.info(f"검색 결과 없음: entpName={entpName}, itemName={itemName}")
            return None, {"message": "검색 결과가 없습니다."}

        item = items[0]
        result = {
            '효능': item.get('efcyQesitm'),
            '사용법': item.get('useMethodQesitm'),
            '주의사항': item.get('atpnQesitm'),
            '상호작용': item.get('intrcQesitm'),
            '부작용': item.get('seQesitm'),
            '보관법': item.get('depositMethodQesitm')
        }
        logger.debug(f"약 정보 조회 성공:{result}")
        return result,None

    #예외 처리 
    except Exception as e:
        logger.error(f"medicine_info ERROR: {repr(e)}", exc_info=True)
        return None, {"error": "server error", "detail": str(e)}

#질문_대답 
@app.get("/inquiry_answer")
def inquiry_answer():
    try:
        #문의사항
        corpus = (request.args.get('corpus') or "").strip()
        if not corpus:
            return jsonify({"error": "문의사항을 입력하세요"}), 400

        print("1")
        #질문_대답 파일
        print('1-1')
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Question_Answer.xlsx")
        print('1-2')
        if not os.path.exists(qa_path):
            return jsonify({"error": "QA file 존재하지 않음", "path": qa_path}), 500
        
        print('1-3')
        QA = pd.read_excel(qa_path)
        QA["question"] = QA["question"].fillna("")
        QA["answer"] = QA["answer"].fillna("")

        print("2")
        #문장 유사도 평가 모델
        print("2-1")
        
        #임베딩
        #corpus_emb = embedder.encode(corpus, convert_to_tensor=True)
        #query_emb = embedder.encode(QA['question'].tolist(), convert_to_tensor=True)

        
        #유사도 계산
        #cos_scores = util.pytorch_cos_sim(query_emb, corpus_emb).cpu().numpy().ravel()

        corpus_vec = embedder.encode(
            [corpus],
            convert_to_numpy=True,
            normalize_embeddings=True,  # 코사인 정규화
            batch_size=1,
            show_progress_bar=False
        )[0]

        query_vecs = embedder.encode(
            QA['question'].tolist(),
            convert_to_numpy=True,
            normalize_embeddings=True,  # 코사인 정규화
            batch_size=16,
            show_progress_bar=False
        )

        # 정규화되어 있으니 코사인 유사도 = 내적
        cos_scores = query_vecs @ corpus_vec
        print("3")
        
        #최상위 1개
        best_idx = int(np.argmax(cos_scores))
        best_score = float(cos_scores[best_idx])

        print("4")
        #유사도가 너무 낮은 경우 결과 없음 처리
        if best_score <= 0.35:
            return jsonify({"result": "결과 없음", "score": best_score})

        response = {
            "question": QA['question'].iloc[best_idx],
            "answer": QA['answer'].iloc[best_idx],
            "score": best_score
        }

        print("5")
        #약 정보 요구
        if best_idx in [7,8,9]:
            response['answer']=""
            entpName = ""
            itemName = ""
            
            #조사 목록 
            josa_list = ["은", "는", "이", "가", "과", "와", "를", "을", "에", "도", "로", "의","랑", "이랑"]

            #약에 대한 단어 추출(특수문자 제거, 토큰화)
            tokens = re.findall(r'[가-힣A-Za-z0-9]+', corpus)
            #단순 단어 '약' 제거
            tokens = [t for t in tokens if t != "약"]

            #전처리한 단어
            clean_tokens = []
            for t in tokens:
                removed = False
                for josa in josa_list:
                    if t.endswith(josa) and len(t) > len(josa):  #끝글자(문자 길이 고려)
                        clean_tokens.append(t[:-len(josa)])      #조사 제거
                        removed = True
                        break
                if not removed:
                    clean_tokens.append(t)

            print(clean_tokens,flush=True)
            print("6")
            
            find_medi = []
            for token in clean_tokens:
                find_medi.extend([name for name in medicine_all['itemName'] if token in name])
            #find_medi = list(set(find_medi)) #최종 약물 단어 추출

            print(find_medi,flush=True)
            if find_medi[0]:
                itemName=find_medi[0]
            
            itemName=clean_tokens[0]
            print("itemName", itemName,flush=True)
            medicine_result, err = get_medicine_info(entpName,itemName)
            if medicine_result:
                if best_idx == 7:
                    response['medicine_info'] = medicine_result['사용법']
                elif best_idx == 8:
                    response['medicine_info'] = medicine_result['부작용']
                elif best_idx == 9:
                    response['medicine_info'] = medicine_result['상호작용']
            else:
                response["medicine_info"] = err or {"message": "약 정보 조회 실패"}
        
        return jsonify(response)

    #예외 처리
    except Exception as e:
        print("inquiry_answer ERROR:", repr(e))
        traceback.print_exc() 
        return jsonify({"error": "server error", "detail": str(e)}), 500

#약 정보
@app.get('/medicine_info')
def medicine_info():
    entpName = request.args.get('entpName')
    itemName = request.args.get('itemName')
    if not entpName and not itemName:
        return jsonify({"error": "업체명과 제품명을 입력해주세요"}), 400

    medicine_result, med_err = get_medicine_info(entpName, itemName)
    if medicine_result:
        return jsonify(medicine_result)
    return jsonify(med_err), 500 if "error" in (med_err or {}) else 200


#충돌 성분 조회
def contrain_ingre(ingredient):
    params = {
        "serviceKey": serviceKey,
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
        "ingrKorName": ingredient,
    }

    base_url = "http://apis.data.go.kr/1471000/DURIrdntInfoService03"
    endpoint = "getUsjntTabooInfoList02"
    url = f"{base_url}/{endpoint}"
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        result=res.json()
    except Exception as e:
        return [], {"error": f"API 요청 실패"}

    body = (result or {}).get("body") or {}
    items = body.get("items")
    if items is None:
        items = body.get("item")  # 어떤 응답은 item만 있음

    flat = []
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("item"), dict):
                flat.append(it["item"])
            elif isinstance(it, dict):
                flat.append(it)
    # case 2) items: dict
    elif isinstance(items, dict):
        if isinstance(items.get("item"), list):
            for it in items["item"]:
                if isinstance(it, dict):
                    flat.append(it)
        elif isinstance(items.get("item"), dict):
            flat.append(items["item"])
        else:
            flat.append(items)
    else:
        flat = []

    # 필요한 필드만 얇게 추출 (키 명칭 변형 대비)
    cleaned = []
    for rec in flat:
        if not isinstance(rec, dict):
            continue
        cleaned.append({
            "MIXTURE_INGR_KOR_NAME": rec.get("MIXTURE_INGR_KOR_NAME") or rec.get("MIXTURE_INGR_KOR_NM"),
            "PROHBT_CONTENT": (rec.get("PROHBT_CONTENT") or "").strip(),
            "INGR_KOR_NAME": rec.get("INGR_KOR_NAME"),  # 디버깅용
        })
    return cleaned, None


#중복 성분, 충돌 성분, 위험치 지수
@app.post('/ingredient_risk')
def ingredient_risk():
    data = request.get_json(silent=True) or {}  #Body 추출
    raw_ing = data.get("ingredients") or []     #키 값 추출(사용자 복용 약들)
    
    #전처리
    ing = [str(x).strip() for x in raw_ing if str(x).strip()]
    if not ing:
        return jsonify({"error": "사용자의 복용 약 정보가 필요합니다"}), 400

    #입력 중복(동일 성분이 2회 이상 등장)
    cnt = Counter(ing)
    duplicates = sorted([k for k, v in cnt.items() if v > 1])

    #병용금기 충돌 성분
    ing_set = set(ing)
    pair_map = {} 
    errors = []

    for a in ing_set:
        items, res = contrain_ingre(a)
        try:
            body = res.get("body", {})
            items = body.get("items") or []
            if isinstance(items, dict):
                items = items.get("item", [])
            if not isinstance(items, list):
                items = []
        except Exception as e:
            errors.append({"ingredient": a, "error": f"응답 파싱 실패: {e}"})
            continue
        
        
        for it in items:
            if not isinstance(it, dict):
                continue
            rec = it.get("item", it)
            mix_name = rec.get("MIXTURE_INGR_KOR_NAME")
            reason = (rec.get("PROHBT_CONTENT") or "").strip()
            if mix_name and mix_name in ing_set and mix_name != a:
                key = frozenset((a, mix_name))
                if key not in pair_map:
                    pair_map[key] = reason
        

    # 충돌 리스트로 변환
    collisions = []
    for key, reason in pair_map.items():
        a, b = sorted(list(key))
        collisions.append({"a": a, "b": b, "reason": reason})

    n = len(ing)
    pair_count = max(n * (n - 1) // 2, 0)
    collision_count = len(collisions)
    duplicate_count = len(duplicates)

    if pair_count > 0:
        risk_rate = int(((collision_count + duplicate_count) / pair_count) * 100)
    else:
        risk_rate = 0
    
    # 경고 모음
    warnings = []
    for d in duplicates:
        warnings.append({"type": "[중복 성분]", "ingredient": d, "reason": ""})
    for c in collisions:
        warnings.append({"type": "[충돌 성분]", "a": c["a"], "b": c["b"], "reason": c["reason"]})

    return jsonify({
        "count": n,
        "pairCount": pair_count,
        "duplicateCount": duplicate_count,
        "collisionCount": collision_count,
        "riskRate": risk_rate,
        "duplicates": duplicates,
        "collisions": collisions,
        "warnings": warnings,
        "errors": errors,   # 외부 API 실패 항목이 있으면 참고용
    })

print('complete init')

port = 8000
print("[LOG] >> 0.0.0.0:5000 flask start")

#localhost
if __name__ == '__main__':
    port = 5000
    print(f"[LOG] >> 0.0.0.0:{port} flask start")
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print("local error")
