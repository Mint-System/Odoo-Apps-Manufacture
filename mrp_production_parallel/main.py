from fastapi import FastAPI
import uvicorn

import odoo
from api import productions


app = FastAPI(title="FastAPI-Odoo18 App",
              description="Make Odoo APIs")

app.include_router(productions.router)


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)