from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from emergency import recommend_hospital  # emergency.py 모듈에서 필요한 함수 임포트

# API 라우터 생성
router = APIRouter(
    prefix="/hospital",
    tags=["Hospital"]
)

app = FastAPI(
    title="병원 추천 시스템",
    description="응급상황별 맞춤 병원 추천 서비스",
    version="1.0.0"
)

# 정적 파일 디렉토리 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>병원 추천 시스템</title>
    <style>
        body {
            font-family: 'Noto Sans KR', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-image: url('/static/background.png');
            background-size: 2200px;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            width: 400px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #34495e;
            font-weight: bold;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        input:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            width: 100%;
            padding: 14px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #2980b9;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <h1>병원 추천 시스템</h1>
        <form action="/hospital/hospital_by_module" method="get">
            <div class="form-group">
                <label>응급상황</label>
                <input type="text" name="request" placeholder="응급상황을 입력하세요" required>
            </div>
            <div class="form-group">
                <label>위도</label>
                <input type="number" step="any" name="latitude" placeholder="위도를 입력하세요" required>
            </div>
            <div class="form-group">
                <label>경도</label>
                <input type="number" step="any" name="longitude" placeholder="경도를 입력하세요" required>
            </div>
            <div class="form-group">
                <label>몇 개의 응급실 추천을 원하시나요?</label>
                <input type="number" step="any" name="count" placeholder="응급실 추천 개수를 입력하세요" required>
            </div>
            <button type="submit">병원 찾기</button>
        </form>
    </div>
</body>
</html>
"""


@router.get("/hospital_by_module", summary="Get Hospital")
async def get_hospital(
    request: str,
    latitude: float,
    longitude: float,
    count: int,
    
):
    result = recommend_hospital(
        text=request,
        user_lat=latitude,
        user_lon=longitude,
        top_n=count
    )
    
    html_result = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>병원 추천 결과</title>
        <style>
            body {{
                font-family: 'Noto Sans KR', sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }}
            .result-container {{
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
            }}
            .summary-box {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .keywords {{
                color: #1976d2;
                margin-top: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            tr:hover {{
                background-color: #f1f3f5;
            }}
            .distance, .duration {{
                color: #3498db;
                font-weight: bold;
            }}
            .arrival-time {{
                color: #e74c3c;
                font-weight: bold;
            }}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="result-container">
            <div class="summary-box">
                <h3>응급 상황 요약</h3>
                <p>{result['summary']['summary']}</p>
                <p class="keywords">키워드: {result['summary']['keywords']}</p>
            </div>
            <h2>추천 병원 목록</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>병원명</th>
                    <th>주소</th>
                    <th>전화번호</th>
                    <th>거리</th>
                    <th>소요시간</th>
                    <th>도착예정시간</th>
                </tr>
    """
    
    for i, hospital in enumerate(result['nearest_hospitals'], 1):
        html_result += f"""
                <tr>
                    <td>{i}</td>
                    <td>{hospital['hospital_name']}</td>
                    <td>{hospital['address']}</td>
                    <td>{hospital['tel1']}</td>
                    <td class="distance">{hospital['distance_km']} km</td>
                    <td class="duration">{hospital['duration']}</td>
                    <td class="arrival-time">{hospital['arrival_time']}</td>
                </tr>
        """
    
    html_result += """
            </table>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_result)



@app.get("/", response_class=HTMLResponse)
async def root():
    return html_content

# 라우터 등록
app.include_router(router)
