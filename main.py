from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Depends

from typing import Union

from emergency import predict_emergency  # emergency.py 모듈에서 필요한 함수 임포트
from emergency import recommend_hospital  # emergency.py 모듈에서 필요한 함수 임포트
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments, EarlyStoppingCallback

import os
import json
import torch
from haversine import haversine
import pandas as pd
import requests



app = FastAPI(
    title="병원 추천 시스템",
    description="응급상황별 맞춤 병원 추천 서비스",
    version="1.0.0"
)

# API 라우터 생성
router = APIRouter(
    prefix="/hospital",
    tags=["Hospital"]
)
tokenizer = None
model = None
device = None

@router.get("/")
def read_root():
    word = "Hospital_FastAPI"
    return word

@router.get("/openai")
# 0. load key file------------------
def init_openai():
    # path='C:/Users/User/project7_api/'
    path='./'
    try:
        with open(os.path.join(path+ 'module/api_key.txt'), 'r') as file:
            api_key = file.read().strip()  # 일반 텍스트로 읽기
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"OpenAI 초기화 중 오류 발생: {str(e)}")
        return None


@router.get("/summarize_text")
def summarize_text(input_text):
    client = init_openai()
    system_role = '''당신은 응급상황에 대한 텍스트에서 핵심 내용을 훌륭하게 요약해주는 어시스턴트입니다.
    응답은 다음의 형식을 지켜주세요.
    {"summary": \"텍스트 요약\",
    "keywords" : \"핵심 키워드\"}
    '''
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": input_text}
            ]
        )
            
        # 응답 내용 출력
        answer = response.choices[0].message.content.strip()
        summary_data = json.loads(answer)
            
        return {
            "summary": summary_data.get("summary", "요약 없음"),
            "keywords": summary_data.get("keywords", [])
        }
    except json.JSONDecodeError:
        print(f"JSONDecodeError: 응답이 JSON 형식이 아님")
        return "JSON ERROR"
    except Exception as e:
        print(f"요약 실패: {e}")
        return "요약 실패 ERROR"

@router.get("/load_emergency_model")
def load_emergency_model():
    global tokenizer, model, device
    # path='C:/Users/User/project7_api/'
    path='./'
    try:
        model_dir = os.path.join(path + 'module/model')
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            num_labels=5
        )
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        model.eval()
        
        # 성공 메시지만 반환
        return {"status": "success", "message": "모델이 성공적으로 로드되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"모델 로드 중 오류 발생: {str(e)}"}


@router.get("/predict_emergency")
def predict(text: str):
    global tokenizer, model, device
    
    if not all([tokenizer, model, device]):
        return {"error": "모델이 로드되지 않았습니다."}
    
    # 먼저 텍스트 요약 수행
    summary_result = summarize_text(text)
    
    # 요약 결과가 에러인 경우 처리
    if isinstance(summary_result, str):  # 에러 메시지인 경우
        return {"error": summary_result}
    
    # keywords를 추출하여 예측 수행
    predicted_class, probabilities = predict_emergency(
        summary_result["keywords"], 
        tokenizer, 
        model, 
        device
    )
    
    return {
        "summary": summary_result["summary"],
        "keywords": summary_result["keywords"],
        "predicted_class": predicted_class+1,
        "probabilities": probabilities.tolist() if probabilities is not None else None
    }



@router.get("/hospital_by_module", summary="Get Hospital")
async def get_hospital(
    request: str,
    latitude: float,
    longitude: float,
    count: int
):
    result = recommend_hospital(
        text=request,
        user_lat=latitude,
        user_lon=longitude,
        top_n=count
    )
    if result is None:
        return {"error": "병원 추천 처리 중 오류가 발생했습니다."}

    # 응급도 클래스가 3 이하일 때 병원 추천
    if result['emergency_class']+1 <= 3:
        return {
            "summary": result['summary'],
            "emergency_class": result['emergency_class']+1,
            "nearest_hospitals": result['nearest_hospitals']
        }
    else:
        return {"message": "병원 추천이 필요 없습니다."}

        


# 라우터 등록
app.include_router(router)
