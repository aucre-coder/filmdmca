from fastapi import FastAPI

app = FastAPI()


@app.get("/api/receive-data")
async def receive_data(url: str):
    stored_data = url
    print(stored_data)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)